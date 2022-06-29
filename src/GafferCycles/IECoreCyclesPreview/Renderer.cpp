//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Alex Fuller. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//      * Neither the name of Alex Fuller nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "GafferCycles/IECoreCyclesPreview/VDBAlgo.h"

#include "GafferCycles/IECoreCyclesPreview/AttributeAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/CameraAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/CurvesAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/IECoreCycles.h"
#include "GafferCycles/IECoreCyclesPreview/MeshAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/ObjectAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/ParticleAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/ShaderNetworkAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

#include "outputDriver/IEDisplayOutputDriver.h"
#include "outputDriver/OIIOOutputDriver.h"

#include "IECoreScene/Camera.h"
#include "IECoreScene/CurvesPrimitive.h"
#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/Shader.h"
#include "IECoreScene/SpherePrimitive.h"
#include "IECoreScene/Transform.h"

#include "IECore/CompoundParameter.h"
#include "IECore/LRUCache.h"
#include "IECore/FileNameParameter.h"
#include "IECore/Interpolator.h"
#include "IECore/MessageHandler.h"
#include "IECore/ObjectVector.h"
#include "IECore/SearchPath.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/StringAlgo.h"
#include "IECore/VectorTypedData.h"

#include "OpenEXR/ImathMatrixAlgo.h"

#include "boost/algorithm/string.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/optional.hpp"

#include "tbb/concurrent_unordered_map.h"
#include "tbb/concurrent_hash_map.h"
#include "tbb/concurrent_vector.h"

#include <unordered_map>

// Cycles
#include "bvh/params.h"
#include "device/device.h"
#include "graph/node.h"
#include "graph/node_type.h"
#include "kernel/types.h"
#include "scene/background.h"
#include "session/buffers.h"
#include "scene/curves.h"
#include "scene/film.h"
#include "scene/geometry.h"
#include "scene/shader_graph.h"
#include "scene/hair.h"
#include "scene/integrator.h"
#include "scene/light.h"
#include "scene/mesh.h"
#include "scene/shader_nodes.h"
#include "scene/object.h"
#include "scene/osl.h"
#include "scene/scene.h"
#include "session/session.h"
#include "scene/volume.h"
#include "subd/dice.h"
#include "util/array.h"
#include "util/function.h"
#include "util/log.h"
#include "util/murmurhash.h"
#include "util/path.h"
#include "util/time.h"
#include "util/vector.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreImage;
using namespace IECoreScene;
using namespace IECoreScenePreview;
using namespace IECoreCycles;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

//typedef std::unique_ptr<ccl::Camera> CCameraPtr;
using CIntegratorPtr = std::unique_ptr<ccl::Integrator>;
using CBackgroundPtr = std::unique_ptr<ccl::Background>;
using CFilmPtr = std::unique_ptr<ccl::Film>;
using CLightPtr = std::unique_ptr<ccl::Light>;
using SharedCCameraPtr = std::shared_ptr<ccl::Camera>;
using SharedCObjectPtr = std::shared_ptr<ccl::Object>;
using SharedCLightPtr = std::shared_ptr<ccl::Light>;
using SharedCGeometryPtr = std::shared_ptr<ccl::Geometry>;
using SharedCParticleSystemPtr = std::shared_ptr<ccl::ParticleSystem>;
// Need to defer shader assignments to the scene lock
typedef std::pair<ccl::Node*, ccl::array<ccl::Node*>> ShaderAssignPair;
// Defer adding the created nodes to the scene lock
using NodesCreated = tbb::concurrent_vector<ccl::Node *>;

// The shared pointer never deletes, we leave that up to Cycles to do the final delete
using NodeDeleter = bool (*)( ccl::Node * );
bool nullNodeDeleter( ccl::Node *node )
{
	return false;
}

// Helper to swap the node to delete to the front of the vector, then pop off
template<typename T, typename U>
static void removeNodesInSet( const ccl::set<T *> &nodesSet, tbb::concurrent_vector<U> &nodesArray )
{
	size_t newSize = nodesArray.size();

	for (size_t i = 0; i < newSize; ++i)
	{
		U node = nodesArray[i];

		if( nodesSet.find( node.get() ) != nodesSet.end() )
		{
			std::swap(nodesArray[i], nodesArray[newSize - 1]);
			i -= 1;
			newSize -= 1;
		}
	}

	nodesArray.resize(newSize);
}

template<typename T>
T *reportedCast( const IECore::RunTimeTyped *v, const char *type, const IECore::InternedString &name )
{
	T *t = IECore::runTimeCast<T>( v );
	if( t )
	{
		return t;
	}

	IECore::msg( IECore::Msg::Warning, "IECoreCycles::Renderer", boost::format( "Expected %s but got %s for %s \"%s\"." ) % T::staticTypeName() % v->typeName() % type % name.c_str() );
	return nullptr;
}

template<typename T>
T parameter( const IECore::CompoundDataMap &parameters, const IECore::InternedString &name, const T &defaultValue )
{
	IECore::CompoundDataMap::const_iterator it = parameters.find( name );
	if( it == parameters.end() )
	{
		return defaultValue;
	}

	using DataType = IECore::TypedData<T>;
	if( const DataType *d = reportedCast<const DataType>( it->second.get(), "parameter", name ) )
	{
		return d->readable();
	}
	else
	{
		return defaultValue;
	}
}

template<typename T>
inline const T *dataCast( const char *name, const IECore::Data *data )
{
	const T *result = runTimeCast<const T>( data );
	if( result )
	{
		return result;
	}
	msg( Msg::Warning, "setParameter", boost::format( "Unsupported value type \"%s\" for parameter \"%s\" (expected %s)." ) % data->typeName() % name % T::staticTypeName() );
	return nullptr;
}

#define OPTION(TYPE, CATEGORY, OPTIONNAME, OPTION) if( name == OPTIONNAME ) { \
	if( value == nullptr ) { \
		CATEGORY.OPTION = CATEGORY ## Default.OPTION; \
		return; } \
	if ( const IECore::TypedData<TYPE> *data = reportedCast<const IECore::TypedData<TYPE>>( value, "option", name ) ) { \
		CATEGORY.OPTION = data->readable(); } \
	return; }

#define OPTION_STR(CATEGORY, OPTIONNAME, OPTION) if( name == OPTIONNAME ) { \
	if( value == nullptr ) { \
		CATEGORY.OPTION = CATEGORY ## Default.OPTION; \
		return; } \
	if ( const StringData *data = reportedCast<const StringData>( value, "option", name ) ) { \
		CATEGORY.OPTION = data->readable().c_str(); } \
	return; }

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesOutput
//////////////////////////////////////////////////////////////////////////

namespace
{

void updateCryptomatteMetadata( IECore::CompoundData *metadata, std::string &name, ccl::Scene *scene = nullptr )
{
	std::string identifier = ccl::string_printf( "%08x", ccl::util_murmur_hash3( name.c_str(), name.length(), 0 ) );
	std::string prefix = "cryptomatte/" + identifier.substr( 0, 7 ) + "/";
	metadata->member<IECore::StringData>( prefix + "name", false, true )->writable() = name;
	metadata->member<IECore::StringData>( prefix + "hash", false, true )->writable() = "MurmurHash3_32";
	metadata->member<IECore::StringData>( prefix + "conversion", false, true )->writable() = "uint32_to_float32";

	if( scene )
	{
		if( name == "cryptomatte_object" )
			metadata->member<IECore::StringData>( prefix + "manifest", false, true )->writable() = scene->object_manager->get_cryptomatte_objects( scene );
		else if( name == "cryptomatte_material" )
			metadata->member<IECore::StringData>( prefix + "manifest", false, true )->writable() = scene->shader_manager->get_cryptomatte_materials( scene );
		else if( name == "cryptomatte_asset" )
			metadata->member<IECore::StringData>( prefix + "manifest", false, true )->writable() = scene->object_manager->get_cryptomatte_assets( scene );
	}
}

class CyclesOutput : public IECore::RefCounted
{

	public :

		CyclesOutput( const ccl::Session *session, const IECore::InternedString &name, const IECoreScene::Output *output )
			: m_passType( ccl::PASS_NONE ), m_denoise( false ), m_interactive( false ), m_lightgroup( false )
		{
			m_parameters = output->parametersData()->copy();
			CompoundDataMap &p = m_parameters->writable();

			p["path"] = new StringData( output->getName() );
			p["driver"] = new StringData( output->getType() );

			if( output->getType() == "ieDisplay" )
				m_interactive = true;

			m_denoise = parameter<bool>( output->parameters(), "denoise", false );

			const ccl::NodeEnum &typeEnum = *ccl::Pass::get_type_enum();
			ccl::ustring passType;

			vector<string> tokens;
			IECore::StringAlgo::tokenize( output->getData(), ' ', tokens );
			if( tokens.size() == 1 )
			{
				if( tokens[0] == "rgb" || tokens[0] == "rgba" )
				{
					p["name"] = m_denoise ? new StringData( ccl::string_printf( "%s_denoised", tokens[0].c_str() ) ) : new StringData( tokens[0] );
					p["type"] = new StringData( "combined" );
					passType = "combined";
				}
				else
				{
					p["name"] = m_denoise ? new StringData( ccl::string_printf( "%s_denoised", tokens[0].c_str() ) ) : new StringData( tokens[0] );
					p["type"] = new StringData( tokens[0] );
					passType = tokens[0];
				}
				m_data = tokens[0];
			}
			else if( tokens.size() == 2 )
			{
				if( tokens[0] == "aovv" )
				{
					p["name"] = m_denoise ? new StringData( ccl::string_printf( "%s_denoised", tokens[1].c_str() ) ) : new StringData( tokens[1] );
					p["type"] = new StringData( "aov_value" );
					passType = tokens[1];
					m_data = tokens[1];
				}
				else if( tokens[0] == "aovc" )
				{
					p["name"] = m_denoise ? new StringData( ccl::string_printf( "%s_denoised", tokens[1].c_str() ) ) : new StringData( tokens[1] );
					p["type"] = new StringData( "aov_color" );
					passType = tokens[1];
					m_data = tokens[1];
				}
				else if( tokens[0] == "lg" )
				{
					p["name"] = m_denoise ? new StringData( ccl::string_printf( "%s_denoised", tokens[1].c_str() ) ) : new StringData( tokens[1] );
					p["type"] = new StringData( "lightgroup" );
					passType = "combined";
					m_data = tokens[1];
					m_lightgroup = true;
				}
				else if( tokens[0] == "cryptomatte" )
				{
					m_data = ccl::string_printf( "%s_%s", tokens[0].c_str(), tokens[1].c_str() );
					p["name"] = new StringData( m_data );
					p["type"] = new StringData( tokens[0] );
					passType = tokens[0];
				}
			}

			if( typeEnum.exists( passType ) )
			{
				m_passType = static_cast<ccl::PassType>( typeEnum[passType] );
			}
		}

		CompoundDataPtr m_parameters;
		ccl::PassType m_passType;
		std::string m_data;
		bool m_denoise;
		bool m_interactive;
		bool m_lightgroup;
};

IE_CORE_DECLAREPTR( CyclesOutput )

typedef std::map<IECore::InternedString, CyclesOutputPtr> OutputMap;

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesShader
//////////////////////////////////////////////////////////////////////////

namespace
{

// Needs to be placed here as it's an attribute to be set at the shader level
IECore::InternedString g_doubleSidedAttributeName( "doubleSided" );
IECore::InternedString g_cyclesDisplacementShaderAttributeName( "ccl:displacement" );
IECore::InternedString g_shaderDisplacementMethodAttributeName( "ccl:shader:displacement_method" );
std::array<IECore::InternedString, ccl::DISPLACE_NUM_METHODS> g_displacementMethodEnumNames = { {
	"bump",
	"true",
	"both"
} };

ccl::DisplacementMethod nameToDisplacementMethodEnum( const IECore::InternedString &name )
{
#define MAP_NAME(enumName, enum) if(name == enumName) return enum;
	MAP_NAME(g_displacementMethodEnumNames[0], ccl::DISPLACE_BUMP);
	MAP_NAME(g_displacementMethodEnumNames[1], ccl::DISPLACE_TRUE);
	MAP_NAME(g_displacementMethodEnumNames[1], ccl::DISPLACE_BOTH);
#undef MAP_NAME

	return ccl::DISPLACE_BUMP;
}

IECore::InternedString g_shaderUseMisAttributeName( "ccl:shader:use_mis" );
IECore::InternedString g_shaderUseTransparentShadowAttributeName( "ccl:shader:use_transparent_shadow" );
IECore::InternedString g_shaderHeterogeneousVolumeAttributeName( "ccl:shader:heterogeneous_volume" );
IECore::InternedString g_shaderVolumeSamplingMethodAttributeName( "ccl:shader:volume_sampling_method" );
IECore::InternedString g_shaderVolumeInterpolationMethodAttributeName( "ccl:shader:volume_interpolation_method" );
IECore::InternedString g_shaderVolumeStepRateAttributeName( "ccl:shader:volume_step_rate" );

std::array<IECore::InternedString, ccl::VOLUME_NUM_SAMPLING> g_volumeSamplingEnumNames = { {
	"distance",
	"equiangular",
	"multiple_importance"
} };
ccl::VolumeSampling nameToVolumeSamplingMethodEnum( const IECore::InternedString &name )
{
#define MAP_NAME(enumName, enum) if(name == enumName) return enum;
	MAP_NAME(g_volumeSamplingEnumNames[0], ccl::VOLUME_SAMPLING_DISTANCE);
	MAP_NAME(g_volumeSamplingEnumNames[1], ccl::VOLUME_SAMPLING_EQUIANGULAR);
	MAP_NAME(g_volumeSamplingEnumNames[1], ccl::VOLUME_SAMPLING_MULTIPLE_IMPORTANCE);
#undef MAP_NAME

	return ccl::VOLUME_SAMPLING_MULTIPLE_IMPORTANCE;
}

std::array<IECore::InternedString, ccl::VOLUME_NUM_INTERPOLATION> g_volumeInterpolationEnumNames = { {
	"linear",
	"cubic"
} };
ccl::VolumeInterpolation nameToVolumeInterpolationMethodEnum( const IECore::InternedString &name )
{
#define MAP_NAME(enumName, enum) if(name == enumName) return enum;
	MAP_NAME(g_volumeInterpolationEnumNames[0], ccl::VOLUME_INTERPOLATION_LINEAR);
	MAP_NAME(g_volumeInterpolationEnumNames[1], ccl::VOLUME_INTERPOLATION_CUBIC);
#undef MAP_NAME

	return ccl::VOLUME_INTERPOLATION_LINEAR;
}

class CyclesShader : public IECore::RefCounted
{

	public :

		// Default shader
		CyclesShader( ccl::Scene *scene )
			:	m_shader( ShaderNetworkAlgo::createDefaultShader() ),
				m_hash( IECore::MurmurHash() )
		{
			m_shader->set_owner( scene );
		}

		CyclesShader( const IECoreScene::ShaderNetwork *surfaceShader,
					  const IECoreScene::ShaderNetwork *displacementShader,
					  const IECoreScene::ShaderNetwork *volumeShader,
					  ccl::Scene *scene,
					  const std::string &name,
					  const IECore::MurmurHash &h,
					  const bool singleSided,
					  const IECore::InternedString displacementMethod,
					  vector<const IECoreScene::ShaderNetwork *> &aovShaders )
			:	m_hash( h )
		{
			ccl::ShaderGraph *graph = ShaderNetworkAlgo::convertGraph( surfaceShader, displacementShader, volumeShader, scene->shader_manager, name );
			if( surfaceShader && singleSided )
			{
				ShaderNetworkAlgo::setSingleSided( graph );
			}

			for( const IECoreScene::ShaderNetwork *aovShader : aovShaders )
			{
				ShaderNetworkAlgo::convertAOV( aovShader, graph, scene->shader_manager, name );
			}

			m_shader = new ccl::Shader();
			if( surfaceShader )
			{
				string shaderName( name + surfaceShader->getOutput().shader.string() );
				m_shader->name = ccl::ustring( shaderName.c_str() );
			}
			else
			{
				string shaderName( name + volumeShader->getOutput().shader.string() );
				m_shader->name = ccl::ustring( shaderName.c_str() );
			}
			m_shader->set_displacement_method( nameToDisplacementMethodEnum( displacementMethod ) );
			m_shader->set_owner( scene );
			m_shader->set_graph( graph );
			m_shader->tag_update( scene );
		}

		~CyclesShader() override
		{
			// Cycles will delete the shader
		}

		void hash( IECore::MurmurHash &h ) const
		{
			h.append( m_hash );
		}

		ccl::Shader *shader() const
		{
			return m_shader;
		}

		void nodesCreated( NodesCreated &nodes )
		{
			// Only get the first instance
			if( this->refCount() == 2 )
			{
				nodes.push_back( m_shader );
			}
		}

	private :

		ccl::Shader *m_shader;
		const IECore::MurmurHash m_hash;

};

IE_CORE_DECLAREPTR( CyclesShader )

//////////////////////////////////////////////////////////////////////////
// ShaderCache
//////////////////////////////////////////////////////////////////////////

class ShaderCache : public IECore::RefCounted
{

	public :

		ShaderCache( ccl::Scene *scene )
			: m_scene( scene )
		{
			m_numDefaultShaders = m_scene->shaders.size();
			m_defaultSurface = new CyclesShader( m_scene );
		}

		~ShaderCache() override
		{
		}

		void update( ccl::Scene *scene, NodesCreated &shaders )
		{
			m_scene = scene;
			updateShaders( shaders );
		}

		CyclesShaderPtr get( const IECoreScene::ShaderNetwork *surfaceShader )
		{
			IECore::MurmurHash h = IECore::MurmurHash();
			return get( surfaceShader, nullptr, nullptr, nullptr, h );
		}

		// Can be called concurrently with other get() calls.
		CyclesShaderPtr get( const IECoreScene::ShaderNetwork *surfaceShader,
							 const IECoreScene::ShaderNetwork *displacementShader,
							 const IECoreScene::ShaderNetwork *volumeShader,
							 const IECore::CompoundObject *attributes,
							 IECore::MurmurHash &h )
		{
			IECore::MurmurHash hSubst;
			IECore::MurmurHash hSubstDisp;
			IECore::MurmurHash hSubstVol;
			bool singleSided = false;
			InternedString displacementMethod( "bump" );
			vector<IECore::MurmurHash> hSubstAovs;
			vector<const IECoreScene::ShaderNetwork*> aovShaders;

			// Surface hash
			if( surfaceShader )
			{
				h.append( surfaceShader->Object::hash() );
				if( attributes )
				{
					surfaceShader->hashSubstitutions( attributes, hSubst );
					h.append( hSubst );

					// Sidedness hash
					IECore::CompoundObject::ObjectMap::const_iterator it = attributes->members().find( g_doubleSidedAttributeName );
					if( it != attributes->members().end() )
					{
						bool doubleSided = reportedCast<const BoolData>( it->second.get(), "attribute", g_doubleSidedAttributeName )->readable();
						if( !doubleSided )
						{
							h.append( "singleSided" );
							singleSided = true;
						}
					}
				}
			}

			// Displacement hash
			if( displacementShader )
			{
				IECore::MurmurHash disph = displacementShader->Object::hash();
				if( attributes )
				{
					displacementShader->hashSubstitutions( attributes, hSubstDisp );
					disph.append( hSubstDisp );

					// Displacement method hash
					IECore::CompoundObject::ObjectMap::const_iterator it = attributes->members().find( g_shaderDisplacementMethodAttributeName );
					if( it != attributes->members().end() )
					{
						InternedString displacementMethodStr( reportedCast<const StringData>( it->second.get(), "attribute", g_shaderDisplacementMethodAttributeName )->readable() );
						if( displacementMethodStr != displacementMethod )
						{
							disph.append( displacementMethodStr );
							displacementMethod = displacementMethodStr;
						}
					}
				}
				h.append( disph );
			}

			// Volume hash
			if( volumeShader )
			{
				IECore::MurmurHash volh = volumeShader->Object::hash();
				if( attributes )
				{
					volumeShader->hashSubstitutions( attributes, hSubstVol );
					volh.append( hSubstVol );
				}
				h.append( volh );
			}

			// AOV hash
			if( attributes && ( surfaceShader || volumeShader ) )
			{
				for( const auto &member : attributes->members() )
				{
					if( boost::starts_with( member.first.string(), "ccl:aov:" ) )
					{
						const IECoreScene::ShaderNetwork *aovShader = runTimeCast<IECoreScene::ShaderNetwork>( member.second.get() );
						if( aovShader )
						{
							IECore::MurmurHash aovh = aovShader->Object::hash();
							IECore::MurmurHash hSubstAov;
							aovShader->hashSubstitutions( attributes, hSubstAov );
							aovh.append( hSubstAov );
							h.append( aovh );
							hSubstAovs.push_back( hSubstAov );
							aovShaders.push_back( aovShader );
						}
					}
				}
			}

			Cache::const_accessor readAccessor;
			if( m_cache.find( readAccessor, h ) )
			{
				return readAccessor->second;
			}

			Cache::accessor writeAccessor;
			if( m_cache.insert( writeAccessor, h) )
			{
				const std::string namePrefix = "shader:" + writeAccessor->first.toString() + ":";

				if( surfaceShader || volumeShader )
				{
					// Substitute surface (if needed)
					IECoreScene::ShaderNetworkPtr substitutedSurfaceShader;
					if( surfaceShader && hSubstDisp != IECore::MurmurHash() )
					{
						IECoreScene::ShaderNetworkPtr substitutedSurfaceShader = surfaceShader->copy();
						substitutedSurfaceShader->applySubstitutions( attributes );
						surfaceShader = substitutedSurfaceShader.get();
					}
					// Substitute displacement (if needed)
					IECoreScene::ShaderNetworkPtr substitutedDisplacementShader;
					if( displacementShader && hSubstDisp != IECore::MurmurHash() )
					{
						IECoreScene::ShaderNetworkPtr substitutedDisplacementShader = displacementShader->copy();
						substitutedDisplacementShader->applySubstitutions( attributes );
						displacementShader = substitutedDisplacementShader.get();
					}
					// Substitute volume (if needed)
					IECoreScene::ShaderNetworkPtr substitutedVolumeShader;
					if( volumeShader && hSubstVol != IECore::MurmurHash() )
					{
						IECoreScene::ShaderNetworkPtr substitutedVolumeShader = volumeShader->copy();
						substitutedVolumeShader->applySubstitutions( attributes );
						volumeShader = substitutedVolumeShader.get();
					}
					// Get all the possible AOV shaders
					vector<IECoreScene::ShaderNetworkPtr> substitutedAOVShaders;
					for( size_t i = 0; i < hSubstAovs.size(); ++i )
					{
						if( hSubstAovs[i] != IECore::MurmurHash() )
						{
							substitutedAOVShaders.push_back( aovShaders[i]->copy() );
							substitutedAOVShaders.back()->applySubstitutions( attributes );
							aovShaders[i] = substitutedAOVShaders.back().get();
						}
					}

					writeAccessor->second = new CyclesShader( surfaceShader, displacementShader, volumeShader, m_scene, namePrefix, h, singleSided, displacementMethod, aovShaders );
				}
			}

			return writeAccessor->second;
		}

		CyclesShaderPtr defaultSurface()
		{
			return m_defaultSurface;
		}

		// Must not be called concurrently with anything.
		void clearUnused()
		{
			// TODO: Cycles currently doesn't delete unused shaders anyways and it's problematic
			// to delete them in a live render, so we just retain all shaders created, Cycles
			// will delete them all once the session is finished.
			return;
		}

		// Must not be called concurrently with anything.
		void nodesCreated( NodesCreated &nodes )
		{
			nodes.push_back( m_defaultSurface->shader() );
			for( Cache::const_iterator it = m_cache.begin(), eIt = m_cache.end(); it != eIt; ++it )
			{
				if( it->second->shader() )
				{
					nodes.push_back( it->second->shader() );
				}
			}
		}

		void addShaderAssignment( ShaderAssignPair shaderAssign )
		{
			m_shaderAssignPairs.push_back( shaderAssign );
		}

		bool hasOSLShader()
		{
			for( ccl::Shader *shader : m_scene->shaders )
			{
				if( IECoreCycles::ShaderNetworkAlgo::hasOSL( shader ) )
					return true;
			}
			return false;
		}

		uint32_t numDefaultShaders()
		{
			return m_numDefaultShaders;
		}

		void flushTextures()
		{
			for( ccl::Shader *shader : m_scene->shaders )
			{
				for( ccl::ShaderNode *node : shader->graph->nodes )
				{
					if( node->special_type == ccl::SHADER_SPECIAL_TYPE_IMAGE_SLOT )
					{
						static_cast<ccl::ImageSlotTextureNode*>( node )->handle.clear();
					}
					else if( node->type == ccl::SkyTextureNode::get_node_type() )
					{
						static_cast<ccl::SkyTextureNode*>( node )->handle.clear();
					}
					else if( node->type == ccl::PointDensityTextureNode::get_node_type() )
					{
						static_cast<ccl::PointDensityTextureNode*>( node )->handle.clear();
					}
					//else if( node->type == ccl::VolumeTextureNode::get_node_type() )
					//{
					//	static_cast<ccl::VolumeTextureNode*>( node )->handle.clear();
					//}
				}
			}
		}

		void removeOSLShaders()
		{
			ccl::set<ccl::Shader *> remove;
			for( ccl::Shader *shader : m_scene->shaders )
			{
				if( IECoreCycles::ShaderNetworkAlgo::hasOSL( shader ) )
				{
					remove.insert( shader );
				}
			}
			m_scene->delete_nodes( remove, m_scene );
		}

	private :

		void updateShaders( NodesCreated &nodes )
		{
			// We need to update all of these, it seems as though being fine-grained causes
			// graphical glitches unfortunately.
			if( m_shaderAssignPairs.size() )
			{
				m_scene->light_manager->tag_update( m_scene, ccl::LightManager::UPDATE_ALL );
				m_scene->geometry_manager->tag_update( m_scene, ccl::GeometryManager::UPDATE_ALL );
			}
			// Do the shader assignment here
			for( ShaderAssignPair shaderAssignPair : m_shaderAssignPairs )
			{
				if( shaderAssignPair.first->is_a( ccl::Geometry::get_node_base_type() ) )
				{
					for( ccl::Node *node : shaderAssignPair.second )
					{
						ccl::Shader *shader = static_cast<ccl::Shader *>( node );
						shader->tag_used( m_scene );
					}
					ccl::Geometry *geo = static_cast<ccl::Geometry*>( shaderAssignPair.first );
					geo->set_used_shaders( shaderAssignPair.second );
				}
				else if( shaderAssignPair.first->is_a( ccl::Light::get_node_type() ) )
				{
					ccl::Light *light = static_cast<ccl::Light*>( shaderAssignPair.first );
					if( shaderAssignPair.second[0] )
					{
						ccl::Shader *shader = static_cast<ccl::Shader *>( shaderAssignPair.second[0] );
						shader->tag_used( m_scene );
						light->set_shader( shader );
					}
					else
					{
						light->set_shader( m_scene->default_light );
					}
				}
			}
			m_shaderAssignPairs.clear();

			// TODO: Optimise
			for( ccl::Light *light : m_scene->lights )
			{
				if( light->get_light_type() == ccl::LIGHT_BACKGROUND )
				{
					// Set environment map rotation
					Imath::M44f transform =  SocketAlgo::getTransform( light->get_tfm() );
					Imath::Eulerf euler( transform, Imath::Eulerf::Order::XZY );

					for( ccl::ShaderNode *node : light->get_shader()->graph->nodes )
					{
						if ( node->type == ccl::EnvironmentTextureNode::node_type )
						{
							ccl::EnvironmentTextureNode *env = (ccl::EnvironmentTextureNode *)node;
							env->tex_mapping.rotation = ccl::make_float3( -euler.x, -euler.y, -euler.z );
							light->get_shader()->tag_update( m_scene );
							break;
						}
					}
				}
			}

			ccl::vector<ccl::Shader *> &shaders = m_scene->shaders;
			if( nodes.size() + m_numDefaultShaders > shaders.size() )
			{
				shaders.resize( m_numDefaultShaders );
				for( ccl::Node *node : nodes )
				{
					ccl::Shader *shader = static_cast<ccl::Shader *>( node );
					shaders.push_back( shader );
				}
				m_scene->shader_manager->tag_update( m_scene, ccl::ShaderManager::SHADER_ADDED );
				// TODO: Optimise
				m_scene->background->tag_update( m_scene );
			}
			nodes.clear();
		}

		ccl::Scene *m_scene;
		int m_numDefaultShaders;
		typedef tbb::concurrent_hash_map<IECore::MurmurHash, CyclesShaderPtr> Cache;
		Cache m_cache;
		CyclesShaderPtr m_defaultSurface;
		// Need to assign shaders in a deferred manner
		using ShaderAssignVector = tbb::concurrent_vector<ShaderAssignPair>;
		ShaderAssignVector m_shaderAssignPairs;

};

IE_CORE_DECLAREPTR( ShaderCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesAttributes
//////////////////////////////////////////////////////////////////////////

namespace
{

// Standard Attributes
IECore::InternedString g_visibilityAttributeName( "visibility" );
IECore::InternedString g_transformBlurAttributeName( "transformBlur" );
IECore::InternedString g_transformBlurSegmentsAttributeName( "transformBlurSegments" );
IECore::InternedString g_deformationBlurAttributeName( "deformationBlur" );
IECore::InternedString g_deformationBlurSegmentsAttributeName( "deformationBlurSegments" );
// Cycles Attributes
IECore::InternedString g_cclVisibilityAttributeName( "ccl:visibility" );
IECore::InternedString g_useHoldoutAttributeName( "ccl:use_holdout" );
IECore::InternedString g_isShadowCatcherAttributeName( "ccl:is_shadow_catcher" );
IECore::InternedString g_shadowTerminatorShadingOffsetAttributeName( "ccl:shadow_terminator_shading_offset" );
IECore::InternedString g_shadowTerminatorGeometryOffsetAttributeName( "ccl:shadow_terminator_geometry_offset" );
IECore::InternedString g_maxLevelAttributeName( "ccl:max_level" );
IECore::InternedString g_dicingRateAttributeName( "ccl:dicing_rate" );
// Per-object color
IECore::InternedString g_colorAttributeName( "Cs" );
// Cycles Light
IECore::InternedString g_lightAttributeName( "ccl:light" );
// Dupli
IECore::InternedString g_dupliGeneratedAttributeName( "ccl:dupli_generated" );
IECore::InternedString g_dupliUVAttributeName( "ccl:dupli_uv" );
// Particle
std::array<IECore::InternedString, 2> g_particleIndexAttributeNames = { {
	"index",
	"instanceIndex",
} };
IECore::InternedString g_particleAgeAttributeName( "age" );
IECore::InternedString g_particleLifetimeAttributeName( "lifetime" );
std::array<IECore::InternedString, 2> g_particleLocationAttributeNames = { {
	"location",
	"P",
} };
IECore::InternedString g_particleRotationAttributeName( "rotation" );
std::array<IECore::InternedString, 2> g_particleRotationAttributeNames = { {
	"rotation",
	"orientation",
} };
std::array<IECore::InternedString, 2> g_particleSizeAttributeNames = { {
	"size",
	"width",
} };
IECore::InternedString g_particleVelocityAttributeName( "velocity" );
IECore::InternedString g_particleAngularVelocityAttributeName( "angular_velocity" );

// Shader Assignment
IECore::InternedString g_cyclesSurfaceShaderAttributeName( "ccl:surface" );
IECore::InternedString g_oslSurfaceShaderAttributeName( "osl:surface" );
IECore::InternedString g_oslShaderAttributeName( "osl:shader" );
IECore::InternedString g_cyclesVolumeShaderAttributeName( "ccl:volume" );
// Ray visibility
IECore::InternedString g_cameraVisibilityAttributeName( "ccl:visibility:camera" );
IECore::InternedString g_diffuseVisibilityAttributeName( "ccl:visibility:diffuse" );
IECore::InternedString g_glossyVisibilityAttributeName( "ccl:visibility:glossy" );
IECore::InternedString g_transmissionVisibilityAttributeName( "ccl:visibility:transmission" );
IECore::InternedString g_shadowVisibilityAttributeName( "ccl:visibility:shadow" );
IECore::InternedString g_scatterVisibilityAttributeName( "ccl:visibility:scatter" );

// Cryptomatte asset
IECore::InternedString g_cryptomatteAssetAttributeName( "ccl:asset_name" );

// Light-group
IECore::InternedString g_lightGroupAttributeName( "ccl:lightgroup" );

// Volume
IECore::InternedString g_volumeClippingAttributeName( "ccl:volume_clipping" );
IECore::InternedString g_volumeStepSizeAttributeName( "ccl:volume_step_size" );
IECore::InternedString g_volumeObjectSpaceAttributeName( "ccl:volume_object_space" );

class CyclesAttributes : public IECoreScenePreview::Renderer::AttributesInterface
{

	public :

		CyclesAttributes( const IECore::CompoundObject *attributes, ShaderCache *shaderCache )
			:	m_shaderHash( IECore::MurmurHash() ),
				m_visibility( ~0 ),
				m_useHoldout( false ),
				m_isShadowCatcher( false ),
				m_shadowTerminatorShadingOffset( 0.0f ),
				m_shadowTerminatorGeometryOffset( 0.0f ),
				m_maxLevel( 1 ),
				m_dicingRate( 1.0f ),
				m_color( Color3f( 0.0f ) ),
				m_dupliGenerated( V3f( 0.0f ) ),
				m_dupliUV( V2f( 0.0f) ),
				m_particle( attributes ),
				m_volume( attributes ),
				m_shaderAttributes( attributes ),
				m_assetName( "" ),
				m_lightGroup( "" ),
				m_shaderCache( shaderCache )
		{
			updateVisibility( g_cameraVisibilityAttributeName,       (int)ccl::PATH_RAY_CAMERA,         attributes );
			updateVisibility( g_diffuseVisibilityAttributeName,      (int)ccl::PATH_RAY_DIFFUSE,        attributes );
			updateVisibility( g_glossyVisibilityAttributeName,       (int)ccl::PATH_RAY_GLOSSY,         attributes );
			updateVisibility( g_transmissionVisibilityAttributeName, (int)ccl::PATH_RAY_TRANSMIT,       attributes );
			updateVisibility( g_shadowVisibilityAttributeName,       (int)ccl::PATH_RAY_SHADOW,         attributes );
			updateVisibility( g_scatterVisibilityAttributeName,      (int)ccl::PATH_RAY_VOLUME_SCATTER, attributes );

			m_useHoldout = attributeValue<bool>( g_useHoldoutAttributeName, attributes, m_useHoldout );
			m_isShadowCatcher = attributeValue<bool>( g_isShadowCatcherAttributeName, attributes, m_isShadowCatcher );
			m_shadowTerminatorShadingOffset = attributeValue<float>( g_shadowTerminatorShadingOffsetAttributeName, attributes, m_shadowTerminatorShadingOffset );
			m_shadowTerminatorGeometryOffset = attributeValue<float>( g_shadowTerminatorGeometryOffsetAttributeName, attributes, m_shadowTerminatorGeometryOffset );
			m_maxLevel = attributeValue<int>( g_maxLevelAttributeName, attributes, m_maxLevel );
			m_dicingRate = attributeValue<float>( g_dicingRateAttributeName, attributes, m_dicingRate );
			m_color = attributeValue<Color3f>( g_colorAttributeName, attributes, m_color );
			m_dupliGenerated = attributeValue<V3f>( g_dupliGeneratedAttributeName, attributes, m_dupliGenerated );
			m_dupliUV = attributeValue<V2f>( g_dupliUVAttributeName, attributes, m_dupliUV );
			m_lightGroup = attributeValue<std::string>( g_lightGroupAttributeName, attributes, m_lightGroup );
			m_assetName = attributeValue<std::string>( g_cryptomatteAssetAttributeName, attributes, m_assetName );

			// Surface shader
			const IECoreScene::ShaderNetwork *surfaceShaderAttribute = attribute<IECoreScene::ShaderNetwork>( g_cyclesSurfaceShaderAttributeName, attributes );
			surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<IECoreScene::ShaderNetwork>( g_oslSurfaceShaderAttributeName, attributes );
			surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<IECoreScene::ShaderNetwork>( g_oslShaderAttributeName, attributes );
			const IECoreScene::ShaderNetwork *displacementShaderAttribute = attribute<IECoreScene::ShaderNetwork>( g_cyclesDisplacementShaderAttributeName, attributes );
			const IECoreScene::ShaderNetwork *volumeShaderAttribute = attribute<IECoreScene::ShaderNetwork>( g_cyclesVolumeShaderAttributeName, attributes );
			if( surfaceShaderAttribute || volumeShaderAttribute )
			{
				// Hash shader attributes first
				m_shaderAttributes.hash( m_shaderHash, attributes );
				// Create the shader
				m_shader = m_shaderCache->get( surfaceShaderAttribute, displacementShaderAttribute, volumeShaderAttribute, attributes, m_shaderHash );
				// Then apply the shader attributes
				m_shaderAttributes.apply( m_shader->shader() );
			}
			else
			{
				// Revert back to the default surface
				m_shader = m_shaderCache->defaultSurface();
			}

			// Light shader

			const IECoreScene::ShaderNetwork *lightShaderAttribute = attribute<IECoreScene::ShaderNetwork>( g_lightAttributeName, attributes );
			if( lightShaderAttribute )
			{
				IECore::MurmurHash h;
				m_lightShader = m_shaderCache->get( lightShaderAttribute, nullptr, nullptr, attributes, h );
				// This is just to store data that is attached to the lights.
				/// \todo Not sure there's any benefit to using a `ccl:light` just as a container here?
				/// Can't we just store the CompoundData?
				m_light = CLightPtr( IECoreCycles::ShaderNetworkAlgo::convert( lightShaderAttribute ) );
			}
		}

		bool applyObject( ccl::Object *object, const CyclesAttributes *previousAttributes ) const
		{
			// Re-issue a new object if displacement or subdivision has changed
			if( previousAttributes )
			{
				if( previousAttributes->m_shader && m_shader )
				{
					ccl::Shader *shader = m_shader->shader();
					ccl::Shader *prevShader = previousAttributes->m_shader->shader();
					if( prevShader->has_displacement && prevShader->get_displacement_method() != ccl::DISPLACE_BUMP )
					{
						const char *oldHash = (prevShader->graph) ? prevShader->graph->displacement_hash.c_str() : "";
						const char *newHash = (shader->graph) ? shader->graph->displacement_hash.c_str() : "";

						if( strcmp( oldHash, newHash ) != 0 )
						{
							//m_shader->need_update_uvs = true;
							//m_shader->need_update_attribute = true;
							shader->need_update_displacement = true;
							// Returning false will make Gaffer re-issue a fresh mesh
							return false;
						}
						else
						{
							// In Blender a shader->set_graph(graph); is called which handles the hashing similar to the code above. In GafferCycles
							// we re-create a fresh shader which is easier to manage, however it misses this call to set need_update_mesh to false.
							// We set false here, but we also need to make sure all the attribute requests are the same to prevent the flag to be set
							// to true in another place of the code inside of Cycles. If we have made it this far in this area, we are just updating
							// the same shader so this should be safe.
							shader->attributes = prevShader->attributes;
							//m_shader->need_update_uvs = false;
							//m_shader->need_update_attribute = false;
							shader->need_update_displacement = false;
						}
					}
				}

				if( ccl::Mesh *mesh = (ccl::Mesh*)object->get_geometry() )
				{
					if( mesh->geometry_type == ccl::Geometry::MESH )
					{
						if( mesh->get_subd_params() )
						{
							if( ( previousAttributes->m_maxLevel != m_maxLevel ) || ( previousAttributes->m_dicingRate != m_dicingRate ) )
							{
								// Get a new mesh
								return false;
							}
						}
					}
				}
			}

			object->set_visibility( m_visibility );
			object->set_use_holdout( m_useHoldout );
			object->set_is_shadow_catcher( m_isShadowCatcher );
			object->set_shadow_terminator_shading_offset( m_shadowTerminatorShadingOffset );
			object->set_shadow_terminator_geometry_offset( m_shadowTerminatorGeometryOffset );
			object->set_color( SocketAlgo::setColor( m_color ) );
			object->set_dupli_generated( SocketAlgo::setVector( m_dupliGenerated ) );
			object->set_dupli_uv( SocketAlgo::setVector( m_dupliUV ) );
			object->set_asset_name( ccl::ustring( m_assetName.c_str() ) );

			if( object->get_geometry() )
			{
				ccl::Mesh *mesh = nullptr;
				if( object->get_geometry()->geometry_type == ccl::Geometry::MESH )
					mesh = (ccl::Mesh*)object->get_geometry();

				if( mesh )
				{
					if( mesh->get_subd_params() )
					{
						mesh->set_subd_dicing_rate( m_dicingRate );
						mesh->set_subd_max_level( m_maxLevel );
					}

					if( m_shader )
					{
						ccl::Shader *shader = m_shader->shader();
						if( shader->attributes.find( ccl::ATTR_STD_UV_TANGENT ) )
						{
							if( !mesh->attributes.find( ccl::ATTR_STD_UV_TANGENT ) )
							{
								// Re-issue new mesh with tangents
								return false;
							}
						}
						if( shader->attributes.find( ccl::ATTR_STD_UV_TANGENT_SIGN ) )
						{
							if( !mesh->attributes.find( ccl::ATTR_STD_UV_TANGENT_SIGN ) )
							{
								// Re-issue new mesh with tangent-sign
								return false;
							}
						}
					}
				}

				if( m_shader->shader() )
				{
					ShaderAssignPair pair = ShaderAssignPair( object->get_geometry(), ccl::array<ccl::Node*>() );
					pair.second.push_back_slow( m_shader->shader() );
					m_shaderCache->addShaderAssignment( pair );
				}
			}

			if( !m_particle.apply( object ) )
				return false;

			if( !m_volume.apply( object ) )
				return false;

#ifdef WITH_CYCLES_LIGHTGROUPS
			object->set_lightgroup( ccl::ustring( m_lightGroup.c_str() ) );
#endif

			return true;
		}

		void applyGeometry( const IECore::Object *object, ccl::Object *cobject ) const
		{
			if( needTangents() )
			{
				if( const IECoreScene::MeshPrimitive *mesh = IECore::runTimeCast<const IECoreScene::MeshPrimitive>( object ) )
				{
					MeshAlgo::computeTangents( static_cast<ccl::Mesh*>( cobject->get_geometry() ), mesh, needTangentSign() );
				}
			}
		}

		bool applyLight( ccl::Light *light, const CyclesAttributes *previousAttributes ) const
		{
			if( ccl::Light *clight = m_light.get() )
			{
				light->set_light_type( clight->get_light_type() );
				light->set_size( clight->get_size() );
				light->set_map_resolution( clight->get_map_resolution() );
				light->set_spot_angle( clight->get_spot_angle() );
				light->set_spot_smooth( clight->get_spot_smooth() );
				light->set_cast_shadow( clight->get_cast_shadow() );
				light->set_use_mis( clight->get_use_mis() );
				light->set_use_diffuse( clight->get_use_diffuse() );
				light->set_use_glossy( clight->get_use_glossy() );
				light->set_use_transmission( clight->get_use_transmission() );
				light->set_use_scatter( clight->get_use_scatter() );
				light->set_max_bounces( clight->get_max_bounces() );
				light->set_is_portal( clight->get_is_portal() );
				light->set_is_enabled( clight->get_is_enabled() );
				light->set_strength( clight->get_strength() );
				light->set_angle( clight->get_angle() );
#ifdef WITH_CYCLES_LIGHTGROUPS
				light->set_lightgroup( clight->get_lightgroup() );
#endif
			}
			if( m_lightShader )
			{
				ShaderAssignPair pair = ShaderAssignPair( light, ccl::array<ccl::Node*>() );
				pair.second.push_back_slow( m_lightShader->shader() );
				m_shaderCache->addShaderAssignment( pair );
			}
			else
			{
				// Use default shader
				/// \todo If we don't have a light shader, then shouldn't we be disabling the
				/// light completely, rather than assigning an emissive facing-ratio shader to it?
				ShaderAssignPair pair = ShaderAssignPair( light, ccl::array<ccl::Node*>() );
				pair.second.push_back_slow( nullptr );
				m_shaderCache->addShaderAssignment( pair );
			}

			return true;
		}

		// Generates a signature for the work done by applyGeometry.
		void hashGeometry( const IECore::Object *object, IECore::MurmurHash &h ) const
		{
			// Currently Cycles can only have a shader assigned uniquely and not instanced...
			//h.append( m_shaderHash );
			const IECore::TypeId objectType = object->typeId();
			switch( (int)objectType )
			{
				case IECoreScene::MeshPrimitiveTypeId :
					if( static_cast<const IECoreScene::MeshPrimitive *>( object )->interpolation() == "catmullClark" )
					{
						h.append( m_dicingRate );
						h.append( m_maxLevel );
					}
					if( m_shader )
					{
						if( needTangents() )
							h.append( "tangent" );
						if( needTangentSign() )
							h.append( "tangent_sign" );
					}
					break;
				case IECoreScene::CurvesPrimitiveTypeId :
					break;
				case IECoreScene::SpherePrimitiveTypeId :
					break;
				case IECoreScene::ExternalProceduralTypeId :
					break;
				case IECoreVDB::VDBObjectTypeId :
					break;
				default :
					// No geometry attributes for this type.
					break;
			}
		}

		// Returns true if the given geometry can be instanced.
		bool canInstanceGeometry( const IECore::Object *object ) const
		{
			if( !IECore::runTimeCast<const IECoreScene::VisibleRenderable>( object ) )
			{
				return false;
			}

			if( const IECoreScene::MeshPrimitive *mesh = IECore::runTimeCast<const IECoreScene::MeshPrimitive>( object ) )
			{
				if( mesh->interpolation() == "catmullClark" )
				{
					// For now we treat all subdiv surfaces as unique because they are all treated as adaptive.
					return false;
				}
				else
				{
					return true;
				}
			}

			return true;
		}

		bool hasParticleInfo() const
		{
			return m_particle.hasParticleInfo();
		}

		bool needTangents() const
		{
			if( !m_shader )
				return false;
			return m_shader->shader()->attributes.find( ccl::ATTR_STD_UV_TANGENT );
		}

		bool needTangentSign() const
		{
			if( !m_shader )
				return false;
			return m_shader->shader()->attributes.find( ccl::ATTR_STD_UV_TANGENT_SIGN );
		}

		void nodesCreated( NodesCreated &nodes )
		{
			m_shader->nodesCreated( nodes );
		}

	private :

		template<typename T>
		static const T *attribute( const IECore::InternedString &name, const IECore::CompoundObject *attributes )
		{
			IECore::CompoundObject::ObjectMap::const_iterator it = attributes->members().find( name );
			if( it == attributes->members().end() )
			{
				return nullptr;
			}
			return reportedCast<const T>( it->second.get(), "attribute", name );
		}

		template<typename T>
		static T attributeValue( const IECore::InternedString &name, const IECore::CompoundObject *attributes, const T &defaultValue )
		{
			using DataType = IECore::TypedData<T>;
			const DataType *data = attribute<DataType>( name, attributes );
			return data ? data->readable() : defaultValue;
		}

		template<typename T>
		static boost::optional<T> optionalAttribute( const IECore::InternedString &name, const IECore::CompoundObject *attributes )
		{
			using DataType = IECore::TypedData<T>;
			const DataType *data = attribute<DataType>( name, attributes );
			return data ? data->readable() : boost::optional<T>();
		}

		void updateVisibility( const IECore::InternedString &name, int rayType, const IECore::CompoundObject *attributes )
		{
			if( const IECore::BoolData *d = attribute<IECore::BoolData>( name, attributes ) )
			{
				if( d->readable() )
				{
					m_visibility |= rayType;
				}
				else
				{
					m_visibility = m_visibility & ~rayType;
				}
			}
		}

		struct Particle
		{
			Particle( const IECore::CompoundObject *attributes )
			{
				for( const auto &name : g_particleIndexAttributeNames )
				{
					index = optionalAttribute<int>( name, attributes );
					if( index )
						break;
				}
				age = optionalAttribute<float>( g_particleAgeAttributeName, attributes );
				lifetime = optionalAttribute<float>( g_particleLifetimeAttributeName, attributes );
				for( const auto &name : g_particleLocationAttributeNames )
				{
					location = optionalAttribute<V3f>( name, attributes );
					if( location )
						break;
				}
				for( const auto &name : g_particleRotationAttributeNames )
				{
					rotation = optionalAttribute<Quatf>( name, attributes );
					if( rotation )
						break;
				}
				for( const auto &name : g_particleSizeAttributeNames )
				{
					size = optionalAttribute<float>( name, attributes );
					if( size )
						break;
				}
				velocity = optionalAttribute<V3f>( g_particleVelocityAttributeName, attributes );
				angular_velocity = optionalAttribute<V3f>( g_particleAngularVelocityAttributeName, attributes );
			}

			boost::optional<int> index;
			boost::optional<float> age;
			boost::optional<float> lifetime;
			boost::optional<V3f> location;
			boost::optional<Quatf> rotation;
			boost::optional<float> size;
			boost::optional<V3f> velocity;
			boost::optional<V3f> angular_velocity;

			bool hasParticleInfo() const
			{
				if( index || age || lifetime || location || rotation || size || velocity || angular_velocity )
				{
					return true;
				}
				else
				{
					return false;
				}
			}

			bool apply( ccl::Object *object ) const
			{
				if( !hasParticleInfo() )
				{
					return true;
				}
				else if( ccl::ParticleSystem *psys = object->get_particle_system() )
				{
					size_t idx = object->get_particle_index();
					if( idx < psys->particles.size() )
					{
						if( index )
							psys->particles[idx].index = index.get();
						if( age )
							psys->particles[idx].age = age.get();
						if( lifetime )
							psys->particles[idx].lifetime = lifetime.get();
						if( location )
							psys->particles[idx].location = SocketAlgo::setVector( location.get() );
						if( rotation )
							psys->particles[idx].rotation = SocketAlgo::setQuaternion( rotation.get() );
						if( size )
							psys->particles[idx].size = size.get();
						if( velocity )
							psys->particles[idx].velocity = SocketAlgo::setVector( velocity.get() );
						if( angular_velocity )
							psys->particles[idx].angular_velocity = SocketAlgo::setVector( angular_velocity.get() );
					}
					return true;
				}
				else
				{
					return false;
				}
			}
		};

		struct Volume
		{
			Volume( const IECore::CompoundObject *attributes )
			{
				clipping = optionalAttribute<float>( g_volumeClippingAttributeName, attributes );
				stepSize = optionalAttribute<float>( g_volumeStepSizeAttributeName, attributes );
				objectSpace = optionalAttribute<bool>( g_volumeObjectSpaceAttributeName, attributes );
			}

			boost::optional<float> clipping;
			boost::optional<float> stepSize;
			boost::optional<bool> objectSpace;

			bool apply( ccl::Object *object ) const
			{
				if( object->get_geometry()->geometry_type == ccl::Geometry::VOLUME )
				{
					ccl::Volume *volume = (ccl::Volume*)object->get_geometry();
					if( clipping )
						volume->set_clipping( clipping.get() );
					if( stepSize )
						volume->set_step_size( stepSize.get() );
					if( objectSpace )
						volume->set_object_space( objectSpace.get() );
				}
				return true;
			}

		};

		struct ShaderAttributes
		{
			ShaderAttributes( const IECore::CompoundObject *attributes )
			{
				useMIS = optionalAttribute<bool>( g_shaderUseMisAttributeName, attributes );
				useTransparentShadow = optionalAttribute<bool>( g_shaderUseTransparentShadowAttributeName, attributes );
				heterogeneousVolume = optionalAttribute<bool>( g_shaderHeterogeneousVolumeAttributeName, attributes );
				volumeSamplingMethod = optionalAttribute<InternedString>( g_shaderVolumeSamplingMethodAttributeName, attributes );
				volumeInterpolationMethod = optionalAttribute<InternedString>( g_shaderVolumeInterpolationMethodAttributeName, attributes );
				volumeStepRate = optionalAttribute<float>( g_shaderVolumeStepRateAttributeName, attributes );
				displacementMethod = optionalAttribute<InternedString>( g_shaderDisplacementMethodAttributeName, attributes );
			}

			boost::optional<bool> useMIS;
			boost::optional<bool> useTransparentShadow;
			boost::optional<bool> heterogeneousVolume;
			boost::optional<InternedString> volumeSamplingMethod;
			boost::optional<InternedString> volumeInterpolationMethod;
			boost::optional<float> volumeStepRate;
			boost::optional<InternedString> displacementMethod;

			void hash( IECore::MurmurHash &h, const IECore::CompoundObject *attributes ) const
			{
				if( useMIS && !useMIS.get() )
					h.append( "no_mis" );

				IECore::CompoundObject::ObjectMap::const_iterator it = attributes->members().find( g_cyclesDisplacementShaderAttributeName );
				if( it != attributes->members().end() )
				{
					if( displacementMethod && displacementMethod.get() != "bump" )
						h.append( displacementMethod.get() );
				}
				// Volume-related attributes hash
				it = attributes->members().find( g_cyclesVolumeShaderAttributeName );
				if( it != attributes->members().end() )
				{
					if( heterogeneousVolume && !heterogeneousVolume.get() )
						h.append( "homogeneous_volume" );
					if( volumeSamplingMethod && volumeSamplingMethod.get() != "multiple_importance" )
						h.append( volumeSamplingMethod.get() );
					if( volumeInterpolationMethod && volumeInterpolationMethod.get() != "linear" )
						h.append( volumeInterpolationMethod.get() );
					if( volumeStepRate && volumeStepRate.get() != 1.0f )
						h.append( volumeStepRate.get() );
				}
			}

			bool apply( ccl::Shader *shader ) const
			{
				shader->set_use_mis( useMIS ? useMIS.get() : true );
				shader->set_use_transparent_shadow(useTransparentShadow ? useTransparentShadow.get() : true );
				shader->set_heterogeneous_volume( heterogeneousVolume ? heterogeneousVolume.get() : true );
				shader->set_volume_sampling_method( volumeSamplingMethod ? nameToVolumeSamplingMethodEnum( volumeSamplingMethod.get() ) : ccl::VOLUME_SAMPLING_MULTIPLE_IMPORTANCE );
				shader->set_volume_interpolation_method( volumeInterpolationMethod ? nameToVolumeInterpolationMethodEnum( volumeInterpolationMethod.get() ) : ccl::VOLUME_INTERPOLATION_LINEAR );
				shader->set_volume_step_rate( volumeStepRate ? volumeStepRate.get() : 1.0f );
				shader->set_displacement_method( displacementMethod ? nameToDisplacementMethodEnum( displacementMethod.get() ) : ccl::DISPLACE_BUMP );

				return true;
			}
		};

		CLightPtr m_light;
		CyclesShaderPtr m_lightShader;
		CyclesShaderPtr m_shader;
		IECore::MurmurHash m_shaderHash;
		int m_visibility;
		bool m_useHoldout;
		bool m_isShadowCatcher;
		float m_shadowTerminatorShadingOffset;
		float m_shadowTerminatorGeometryOffset;
		int m_maxLevel;
		float m_dicingRate;
		Color3f m_color;
		V3f m_dupliGenerated;
		V2f m_dupliUV;
		Particle m_particle;
		Volume m_volume;
		ShaderAttributes m_shaderAttributes;
		InternedString m_assetName;
		InternedString m_lightGroup;
		// Need to assign shaders in a deferred manner
		ShaderCache *m_shaderCache;

};

IE_CORE_DECLAREPTR( CyclesAttributes )

} // namespace

//////////////////////////////////////////////////////////////////////////
// AttributesCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class AttributesCache : public IECore::RefCounted
{

	public :

		AttributesCache( ShaderCachePtr shaderCache )
			: m_shaderCache( shaderCache )
		{
		}

		// Can be called concurrently with other get() calls.
		CyclesAttributesPtr get( const IECore::CompoundObject *attributes )
		{
			Cache::accessor a;
			m_cache.insert( a, attributes->Object::hash() );
			if( !a->second )
			{
				a->second = new CyclesAttributes( attributes, m_shaderCache.get() );
			}
			return a->second;
		}

		// Must not be called concurrently with anything.
		void clearUnused()
		{
			vector<IECore::MurmurHash> toErase;
			for( Cache::iterator it = m_cache.begin(), eIt = m_cache.end(); it != eIt; ++it )
			{
				if( it->second->refCount() == 1 )
				{
					// Only one reference - this is ours, so
					// nothing outside of the cache is using the
					// attributes.
					toErase.push_back( it->first );
				}
			}
			for( vector<IECore::MurmurHash>::const_iterator it = toErase.begin(), eIt = toErase.end(); it != eIt; ++it )
			{
				m_cache.erase( *it );
			}

			m_shaderCache->clearUnused();
		}

	private :

		ShaderCachePtr m_shaderCache;

		typedef tbb::concurrent_hash_map<IECore::MurmurHash, CyclesAttributesPtr> Cache;
		Cache m_cache;

};

IE_CORE_DECLAREPTR( AttributesCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// ParticleSystemCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class ParticleSystemsCache : public IECore::RefCounted
{

	public :

		ParticleSystemsCache( ccl::Scene *scene ) : m_scene( scene )
		{
		}

		void update( ccl::Scene *scene, NodesCreated &psys )
		{
			m_scene = scene;
			updateParticleSystems( psys );
		}

		// Can be called concurrently with other get() calls.
		SharedCParticleSystemPtr get( const IECoreScene::PointsPrimitive *points )
		{
			const IECore::MurmurHash hash = points->Object::hash();

			Cache::accessor a;
			m_cache.insert( a, hash );

			if( !a->second )
			{
				a->second = SharedCParticleSystemPtr( ParticleAlgo::convert( points ), nullNodeDeleter );
			}

			return a->second;
		}

		// For unique attributes on instanced meshes.
		SharedCParticleSystemPtr get( const IECore::MurmurHash hash )
		{
			Cache::accessor a;
			m_cache.insert( a, hash );
			ccl::Particle particle = {};

			if( !a->second )
			{
				ccl::ParticleSystem *pSys = new ccl::ParticleSystem();
				pSys->particles.push_back_slow( particle );
				a->second = SharedCParticleSystemPtr( pSys, nullNodeDeleter );
			}
			else
			{
				a->second->particles.push_back_slow( particle );
			}

			a->second->tag_update( m_scene );

			return a->second;
		}

		// Must not be called concurrently with anything.
		void clearUnused()
		{
			vector<IECore::MurmurHash> toErase;
			for( Cache::iterator it = m_cache.begin(), eIt = m_cache.end(); it != eIt; ++it )
			{
				if( it->second.unique() )
				{
					// Only one reference - this is ours, so
					// nothing outside of the cache is using the
					// camera.
					toErase.push_back( it->first );
				}
			}
			for( vector<IECore::MurmurHash>::const_iterator it = toErase.begin(), eIt = toErase.end(); it != eIt; ++it )
			{
				m_cache.erase( *it );
			}

			if( toErase.size() )
			{
				m_scene->particle_system_manager->tag_update( m_scene );
			}
		}

		void nodesCreated( NodesCreated &nodes ) const
		{
			for( Cache::const_iterator it = m_cache.begin(), eIt = m_cache.end(); it != eIt; ++it )
			{
				if( it->second.get() )
				{
					nodes.push_back( it->second.get() );
				}
			}
		}

	private :

		void updateParticleSystems( NodesCreated &nodes )
		{
			if( nodes.size() )
			{
				ccl::vector<ccl::ParticleSystem *> &particleSystems = m_scene->particle_systems;
				for( ccl::Node *node : nodes )
				{
					particleSystems.push_back( static_cast<ccl::ParticleSystem *>( node ) );
				}
				m_scene->particle_system_manager->tag_update( m_scene );
				nodes.clear();
			}
		}

		ccl::Scene *m_scene;
		typedef tbb::concurrent_hash_map<IECore::MurmurHash, SharedCParticleSystemPtr> Cache;
		Cache m_cache;

};

IE_CORE_DECLAREPTR( ParticleSystemsCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// InstanceCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class Instance
{

	public :

		ccl::Object *object()
		{
			return m_object.get();
		}

		ccl::Geometry *geometry()
		{
			return m_geometry.get();
		}

		ccl::ParticleSystem *particleSystem()
		{
			return m_particleSystem.get();
		}

		void objectsCreated( NodesCreated &nodes ) const
		{
			nodes.push_back( m_object.get() );
		}

		void geometryCreated( NodesCreated &nodes ) const
		{
			if( m_prototype )
			{
				nodes.push_back( m_geometry.get() );
			}
		}

		void particleSystemsCreated( NodesCreated &nodes ) const
		{
			if( m_prototype && m_particleSystem )
			{
				nodes.push_back( m_particleSystem.get() );
			}
		}

	private :

		// Constructors are private as they are only intended for use in
		// `InstanceCache::get()`. See comment in `nodesCreated()`.
		friend class InstanceCache;

		Instance( const SharedCObjectPtr &object, const SharedCGeometryPtr &geometry, const bool prototype )
			:	m_object( object ), m_geometry( geometry ), m_prototype( prototype )
		{
		}

		Instance( const SharedCObjectPtr &object, const SharedCGeometryPtr &geometry, const SharedCParticleSystemPtr &particleSystem, const bool prototype )
			:	m_object( object ), m_geometry( geometry ), m_particleSystem( particleSystem ), m_prototype( prototype )
		{
		}

		SharedCObjectPtr m_object;
		SharedCGeometryPtr m_geometry;
		SharedCParticleSystemPtr m_particleSystem;
		bool m_prototype;

};

class InstanceCache : public IECore::RefCounted
{

	public :

		InstanceCache( ccl::Scene *scene, ParticleSystemsCachePtr particleSystemsCache )
			: m_scene( scene ), m_particleSystemsCache( particleSystemsCache )
		{
		}

		void update( ccl::Scene *scene, NodesCreated &object, NodesCreated &geometry )
		{
			m_scene = scene;
			updateObjects( object );
			updateGeometry( geometry );
		}

		// Can be called concurrently with other get() calls.
		Instance get( const IECore::Object *object, const IECoreScenePreview::Renderer::AttributesInterface *attributes, const std::string &nodeName )
		{
			const CyclesAttributes *cyclesAttributes = static_cast<const CyclesAttributes *>( attributes );

			if( !cyclesAttributes->canInstanceGeometry( object ) )
			{
				SharedCParticleSystemPtr cpsysPtr;
				SharedCObjectPtr cobject = convert( object, cyclesAttributes, nodeName, cpsysPtr );
				m_objects.push_back( cobject );
				SharedCGeometryPtr cgeo = SharedCGeometryPtr( cobject.get()->get_geometry(), nullNodeDeleter );
				m_uniqueGeometry.push_back( cgeo );
				return Instance( cobject, cgeo, cpsysPtr, true );
			}

			bool isPrototype = false;

			IECore::MurmurHash h = object->hash();
			cyclesAttributes->hashGeometry( object, h );

			SharedCObjectPtr cobject;
			SharedCGeometryPtr cgeo;
			SharedCParticleSystemPtr cpsysPtr;
			Geometry::const_accessor readAccessor;
			if( m_geometry.find( readAccessor, h ) )
			{
				cgeo = readAccessor->second;
				cobject = convert( object, cyclesAttributes, nodeName, cpsysPtr, cgeo.get() );
				readAccessor.release();
			}
			else
			{
				Geometry::accessor writeAccessor;
				if( m_geometry.insert( writeAccessor, h ) )
				{
					cobject = convert( object, cyclesAttributes, nodeName, cpsysPtr );
					writeAccessor->second = SharedCGeometryPtr( cobject->get_geometry(), nullNodeDeleter );
					cgeo = writeAccessor->second;
					cgeo->name = h.toString();
					isPrototype = true;
				}
				else
				{
					cgeo = writeAccessor->second;
					cobject = convert( object, cyclesAttributes, nodeName, cpsysPtr, cgeo.get() );
				}
				writeAccessor.release();
			}

			m_objects.push_back( cobject );

			return Instance( cobject, cgeo, cpsysPtr, isPrototype );
		}

		// Can be called concurrently with other get() calls.
		Instance get( const std::vector<const IECore::Object *> &samples,
					  const std::vector<float> &times,
					  const int frameIdx,
					  const IECoreScenePreview::Renderer::AttributesInterface *attributes,
					  const std::string &nodeName )
		{
			const CyclesAttributes *cyclesAttributes = static_cast<const CyclesAttributes *>( attributes );

			if( !cyclesAttributes->canInstanceGeometry( samples.front() ) )
			{
				SharedCParticleSystemPtr cpsysPtr;
				SharedCObjectPtr cobject = convert( samples, times, frameIdx, cyclesAttributes, nodeName, cpsysPtr );
				m_objects.push_back( cobject );
				SharedCGeometryPtr cgeo = SharedCGeometryPtr( cobject.get()->get_geometry(), nullNodeDeleter );
				m_uniqueGeometry.push_back( cgeo );
				return Instance( cobject, cgeo, cpsysPtr, true );
			}

			bool isPrototype = false;

			IECore::MurmurHash h;
			for( std::vector<const IECore::Object *>::const_iterator it = samples.begin(), eIt = samples.end(); it != eIt; ++it )
			{
				(*it)->hash( h );
			}
			for( std::vector<float>::const_iterator it = times.begin(), eIt = times.end(); it != eIt; ++it )
			{
				h.append( *it );
			}
			cyclesAttributes->hashGeometry( samples.front(), h );

			SharedCObjectPtr cobject;
			SharedCGeometryPtr cgeo;
			SharedCParticleSystemPtr cpsysPtr;
			Geometry::const_accessor readAccessor;
			if( m_geometry.find( readAccessor, h ) )
			{
				cgeo = readAccessor->second;
				cobject = convert( samples, times, frameIdx, cyclesAttributes, nodeName, cpsysPtr, cgeo.get() );
				readAccessor.release();
			}
			else
			{
				Geometry::accessor writeAccessor;
				if( m_geometry.insert( writeAccessor, h ) )
				{
					cobject = convert( samples, times, frameIdx, cyclesAttributes, nodeName, cpsysPtr );
					writeAccessor->second = SharedCGeometryPtr( cobject->get_geometry(), nullNodeDeleter );
					cgeo = writeAccessor->second;
					cgeo->name = h.toString();
					isPrototype = true;
				}
				else
				{
					cgeo = writeAccessor->second;
					cobject = convert( samples, times, frameIdx, cyclesAttributes, nodeName, cpsysPtr, cgeo.get() );
				}
				writeAccessor.release();
			}

			m_objects.push_back( cobject );

			return Instance( cobject, cgeo, cpsysPtr, isPrototype );
		}

		// Must not be called concurrently with anything.
		void clearUnused()
		{
			ccl::set<ccl::Object*> toEraseObjs;

			for( Objects::iterator it = m_objects.begin(), eIt = m_objects.end(); it != eIt; ++it )
			{
				if( it->unique() )
				{
					// Only one reference - this is ours, so
					// nothing outside of the cache is using the
					// node.
					//toErase.push_back( it->first );
					toEraseObjs.insert( it->get() );
				}
			}

			removeNodesInSet( toEraseObjs, m_objects );
			m_scene->delete_nodes( toEraseObjs, m_scene );

			ccl::set<ccl::Geometry*> toEraseGeos;

			for( UniqueGeometry::iterator it = m_uniqueGeometry.begin(), eIt = m_uniqueGeometry.end(); it != eIt; ++it )
			{
				if( it->unique() )
				{
					// Only one reference - this is ours, so
					// nothing outside of the cache is using the
					// node.
					//toErase.push_back( it->first );
					toEraseGeos.insert( it->get() );
				}
			}

			removeNodesInSet( toEraseGeos, m_uniqueGeometry );

			vector<IECore::MurmurHash> toErase;

			for( Geometry::iterator it = m_geometry.begin(), eIt = m_geometry.end(); it != eIt; ++it )
			{
				if( it->second.unique() )
				{
					// Only one reference - this is ours, so
					// nothing outside of the cache is using the
					// node.
					toErase.push_back( it->first );
					toEraseGeos.insert( it->second.get() );
				}
			}

			for( vector<IECore::MurmurHash>::const_iterator it = toErase.begin(), eIt = toErase.end(); it != eIt; ++it )
			{
				m_geometry.erase( *it );
			}

			m_scene->delete_nodes( toEraseGeos, m_scene );
		}

		void nodesCreated( NodesCreated &objects, NodesCreated &geometry )
		{
			objectsCreated( objects );
			geometryCreated( geometry );
		}

	private :

		SharedCObjectPtr convert( const IECore::Object *object,
								  const CyclesAttributes *attributes,
								  const std::string &nodeName,
								  SharedCParticleSystemPtr &cpsysPtr,
								  ccl::Geometry *cgeo = nullptr )
		{
			ccl::Object *cobject = nullptr;

			if( !cgeo )
			{
				cobject = ObjectAlgo::convert( object, nodeName, m_scene );
				attributes->applyGeometry( object, cobject );
				ccl::Geometry *cgeo = cobject->get_geometry();
				cgeo->set_owner( m_scene );
			}
			else
			{
				cobject = new ccl::Object();
				cobject->name = ccl::ustring( nodeName.c_str() );
				cobject->set_geometry( cgeo );
			}

			IECore::MurmurHash rh;
			rh.append( nodeName );
			cobject->set_random_id( (unsigned)IECore::hash_value( rh ) );
			cobject->set_owner( m_scene );

			if( attributes->hasParticleInfo() )
			{
				ParticlesMutex::scoped_lock lock( m_particlesMutex );
				cpsysPtr = m_particleSystemsCache->get( rh );
				cobject->set_particle_system( cpsysPtr.get() );
				cobject->set_particle_index( cpsysPtr.get()->particles.size() - 1 );
			}

			return SharedCObjectPtr( cobject, nullNodeDeleter );
		}

		SharedCObjectPtr convert( const std::vector<const IECore::Object *> &samples,
								  const std::vector<float> &times,
								  const int frame,
								  const CyclesAttributes *attributes,
								  const std::string &nodeName,
								  SharedCParticleSystemPtr &cpsysPtr,
								  ccl::Geometry *cgeo = nullptr )
		{
			ccl::Object *cobject = nullptr;

			if( !cgeo )
			{
				cobject = ObjectAlgo::convert( samples, times, frame, nodeName, m_scene );
				attributes->applyGeometry( samples.front(), cobject );
				ccl::Geometry *cgeo = cobject->get_geometry();
				cgeo->set_owner( m_scene );
			}
			else
			{
				cobject = new ccl::Object();
				cobject->name = ccl::ustring( nodeName.c_str() );
				cobject->set_geometry( cgeo );
			}

			IECore::MurmurHash rh;
			rh.append( nodeName );
			cobject->set_random_id( (unsigned)IECore::hash_value( rh ) );
			cobject->set_owner( m_scene );

			if( attributes->hasParticleInfo() )
			{
				ParticlesMutex::scoped_lock lock( m_particlesMutex );
				cpsysPtr = m_particleSystemsCache->get( rh );
				cobject->set_particle_system( cpsysPtr.get() );
				cobject->set_particle_index( cpsysPtr.get()->particles.size() - 1 );
			}

			return SharedCObjectPtr( cobject, nullNodeDeleter );
		}

		void updateObjects( NodesCreated &nodes )
		{
			if( nodes.size() )
			{
				ccl::vector<ccl::Object *> &objects = m_scene->objects;
				for( ccl::Node *node : nodes )
				{
					ccl::Object *obj = static_cast<ccl::Object *>( node );
					objects.push_back( obj );
					obj->tag_update( m_scene );
				}
				m_scene->object_manager->tag_update( m_scene, ccl::ObjectManager::OBJECT_ADDED );
				nodes.clear();
			}
		}

		void updateGeometry( NodesCreated &nodes )
		{
			if( nodes.size() )
			{
				ccl::vector<ccl::Geometry *> &geometry = m_scene->geometry;
				for( ccl::Node *node : nodes )
				{
					ccl::Geometry *geo = static_cast<ccl::Geometry *>( node );
					geometry.push_back( geo );
					geo->tag_update( m_scene, true );
				}
				m_scene->object_manager->tag_update( m_scene, ccl::GeometryManager::GEOMETRY_ADDED );
				nodes.clear();
			}
		}

		void objectsCreated( NodesCreated &nodes ) const
		{
			for( Objects::const_iterator it = m_objects.begin(), eIt = m_objects.end(); it != eIt; ++it )
			{
				if( it->get() )
				{
					nodes.push_back( it->get() );
				}
			}
		}

		void geometryCreated( NodesCreated &nodes ) const
		{
			for( UniqueGeometry::const_iterator it = m_uniqueGeometry.begin(), eIt = m_uniqueGeometry.end(); it != eIt; ++it )
			{
				if( it->get() )
				{
					nodes.push_back( it->get() );
				}
			}
			for( Geometry::const_iterator it = m_geometry.begin(), eIt = m_geometry.end(); it != eIt; ++it )
			{
				if( it->second )
				{
					nodes.push_back( it->second.get() );
				}
			}
		}

		ccl::Scene *m_scene;
		using Objects = tbb::concurrent_vector<SharedCObjectPtr>;
		Objects m_objects;
		typedef tbb::concurrent_hash_map<IECore::MurmurHash, SharedCGeometryPtr> Geometry;
		Geometry m_geometry;
		using UniqueGeometry = tbb::concurrent_vector<SharedCGeometryPtr>;
		UniqueGeometry m_uniqueGeometry;
		ParticleSystemsCachePtr m_particleSystemsCache;
		using ParticlesMutex = tbb::spin_mutex;
		ParticlesMutex m_particlesMutex;


};

IE_CORE_DECLAREPTR( InstanceCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// LightCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class LightCache : public IECore::RefCounted
{

	public :

		LightCache( ccl::Scene *scene )
			: m_scene( scene )
		{
		}

		void update( ccl::Scene *scene, NodesCreated &nodes )
		{
			m_scene = scene;
			updateLights( nodes );
		}

		// Can be called concurrently with other get() calls.
		SharedCLightPtr get( const std::string &nodeName )
		{
			ccl::Light *light = new ccl::Light();
			light->name = nodeName.c_str();
			light->tag_update( m_scene );
			auto clight = SharedCLightPtr( light, nullNodeDeleter );

			m_lights.push_back( clight );

			return clight;
		}

		// Must not be called concurrently with anything.
		void clearUnused()
		{
			ccl::set<ccl::Light*> toErase;

			for( Lights::iterator it = m_lights.begin(), eIt = m_lights.end(); it != eIt; ++it )
			{
				if( it->unique() )
				{
					// Only one reference - this is ours, so
					// nothing outside of the cache is using the
					// node.
					//toErase.push_back( it->first );
					toErase.insert( it->get() );
				}
			}

			removeNodesInSet( toErase, m_lights );
			m_scene->delete_nodes( toErase, m_scene );
		}

		void nodesCreated( NodesCreated &nodes ) const
		{
			for( Lights::const_iterator it = m_lights.begin(), eIt = m_lights.end(); it != eIt; ++it )
			{
				if( it->get() )
				{
					nodes.push_back( it->get() );
				}
			}
		}

	private :

		void updateLights( NodesCreated &nodes )
		{
			if( nodes.size() )
			{
				ccl::vector<ccl::Light *> &lights = m_scene->lights;
				for( ccl::Node *node : nodes )
				{
					lights.push_back( static_cast<ccl::Light *>( node ) );
				}
				m_scene->light_manager->tag_update( m_scene, ccl::LightManager::LIGHT_ADDED );
				nodes.clear();
			}
		}

		ccl::Scene *m_scene;
		using Lights = tbb::concurrent_vector<SharedCLightPtr>;
		Lights m_lights;

};

IE_CORE_DECLAREPTR( LightCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// CameraCache
//////////////////////////////////////////////////////////////////////////

namespace
{

class CameraCache : public IECore::RefCounted
{

	public :

		CameraCache()
		{
		}

		// Can be called concurrently with other get() calls.
		SharedCCameraPtr get( const IECoreScene::Camera *camera, const std::string &name )
		{
			const IECore::MurmurHash hash = camera->Object::hash();

			Cache::accessor a;
			m_cache.insert( a, hash );

			if( !a->second )
			{
				a->second = SharedCCameraPtr( CameraAlgo::convert( camera, name ) );
			}

			return a->second;
		}

		// Must not be called concurrently with anything.
		void clearUnused()
		{
			vector<IECore::MurmurHash> toErase;
			for( Cache::iterator it = m_cache.begin(), eIt = m_cache.end(); it != eIt; ++it )
			{
				if( it->second.unique() )
				{
					// Only one reference - this is ours, so
					// nothing outside of the cache is using the
					// camera.
					toErase.push_back( it->first );
				}
			}
			for( vector<IECore::MurmurHash>::const_iterator it = toErase.begin(), eIt = toErase.end(); it != eIt; ++it )
			{
				m_cache.erase( *it );
			}
		}

	private :

		typedef tbb::concurrent_hash_map<IECore::MurmurHash, SharedCCameraPtr> Cache;
		Cache m_cache;

};

IE_CORE_DECLAREPTR( CameraCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesObject
//////////////////////////////////////////////////////////////////////////

namespace
{

class CyclesObject : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		CyclesObject( ccl::Session *session, const Instance &instance, const float frame )
			:	m_session( session ), m_instance( instance ), m_frame( frame ), m_attributes( nullptr )
		{
		}

		~CyclesObject() override
		{
		}

		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override
		{
		}

		void transform( const Imath::M44f &transform ) override
		{
			ccl::Object *object = m_instance.object();
			if( !object )
				return;

			object->set_tfm( SocketAlgo::setTransform( transform ) );
			if( ccl::Mesh *mesh = (ccl::Mesh*)object->get_geometry() )
			{
				if( mesh->geometry_type == ccl::Geometry::MESH )
				{
					if( mesh->get_subd_params() )
						mesh->set_subd_objecttoworld( object->get_tfm() );
				}
			}

			ccl::array<ccl::Transform> motion;
			if( object->get_geometry()->get_use_motion_blur() )
			{
				motion.resize( object->get_geometry()->get_motion_steps(), ccl::transform_empty() );
				for( size_t i = 0; i < motion.size(); ++i )
				{
					motion[i] = object->get_tfm();
				}
			}

			object->set_motion( motion );

			object->tag_update( m_session->scene );
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			ccl::Object *object = m_instance.object();
			if( !object )
				return;

			ccl::array<ccl::Transform> motion;
			ccl::Geometry *geo = object->get_geometry();
			if( geo && geo->get_use_motion_blur() && geo->get_motion_steps() != samples.size() )
			{
				IECore::msg( IECore::Msg::Error, "IECoreCycles::Renderer", boost::format( "Transform step size on \"%s\" must match deformation step size." ) % object->name.c_str() );
				object->set_tfm( SocketAlgo::setTransform( samples.front() ) );
				motion.resize( geo->get_motion_steps(), ccl::transform_empty() );
				for( size_t i = 0; i < motion.size(); ++i )
				{
					motion[i] = object->get_tfm();
					object->set_motion( motion );
				}
				object->tag_update( m_session->scene );
				return;
			}

			const size_t numSamples = samples.size();

			if( numSamples == 1 )
			{
				object->set_tfm( SocketAlgo::setTransform( samples.front() ) );
				object->tag_update( m_session->scene );
				return;
			}

			int frameIdx = -1;
			for( size_t i = 0; i < numSamples; ++i )
			{
				if( times[i] == m_frame )
				{
					frameIdx = i;
				}
			}

			if( numSamples % 2 ) // Odd numSamples
			{
				motion.resize( numSamples, ccl::transform_empty() );

				for( int i = 0; i < (int)numSamples; ++i )
				{
					if( i == frameIdx )
					{
						object->set_tfm( SocketAlgo::setTransform( samples[i] ) );
					}

					motion[i] = SocketAlgo::setTransform( samples[i] );
				}
			}
			else if( numSamples == 2 )
			{
				Imath::M44f matrix;
				motion.resize( numSamples+1, ccl::transform_empty() );
				IECore::LinearInterpolator<Imath::M44f>()( samples[0], samples[1], 0.5f, matrix );

				if( frameIdx == -1 ) // Center frame
				{
					object->set_tfm( SocketAlgo::setTransform( matrix ) );
				}
				else if( frameIdx == 0 ) // Start frame
				{
					object->set_tfm( SocketAlgo::setTransform( samples[0] ) );
				}
				else // End frame
				{
					object->set_tfm( SocketAlgo::setTransform( samples[1] ) );
				}
				motion[0] = SocketAlgo::setTransform( samples[0] );
				motion[1] = SocketAlgo::setTransform( matrix );
				motion[2] = SocketAlgo::setTransform( samples[1] );
			}
			else // Even numSamples
			{
				motion.resize( numSamples, ccl::transform_empty() );

				if( frameIdx == -1 ) // Center frame
				{
					const int mid = numSamples / 2 - 1;
					Imath::M44f matrix;
					IECore::LinearInterpolator<Imath::M44f>()( samples[mid], samples[mid+1], 0.5f, matrix );
					object->set_tfm( SocketAlgo::setTransform( matrix ) );
				}
				else if( frameIdx == 0 ) // Start frame
				{
					object->set_tfm( SocketAlgo::setTransform( samples[0] ) );
				}
				else // End frame
				{
					object->set_tfm( SocketAlgo::setTransform( samples[numSamples-1] ) );
				}

				for( size_t i = 0; i < numSamples; ++i )
				{
					motion[i] = SocketAlgo::setTransform( samples[i] );
				}
			}

			object->set_motion( motion );
			if( !geo->get_use_motion_blur() )
			{
				geo->set_motion_steps( motion.size() );
			}

			if( ccl::Mesh *mesh = (ccl::Mesh*)object->get_geometry() )
			{
				if( mesh->geometry_type == ccl::Geometry::MESH )
				{
					if( mesh->get_subd_params() )
						mesh->set_subd_objecttoworld( object->get_tfm() );
				}
			}

			object->tag_update( m_session->scene );
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			const CyclesAttributes *cyclesAttributes = static_cast<const CyclesAttributes *>( attributes );

			ccl::Object *object = m_instance.object();
			if( !object || cyclesAttributes->applyObject( object, m_attributes.get() ) )
			{
				m_attributes = cyclesAttributes;
				object->tag_update( m_session->scene );
				return true;
			}

			return false;
		}

		void assignID( uint32_t id ) override
		{
			/// \todo Implement me
		}

	private :

		ccl::Session *m_session;
		Instance m_instance;
		const float m_frame;
		ConstCyclesAttributesPtr m_attributes;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesLight
//////////////////////////////////////////////////////////////////////////

namespace
{

class CyclesLight : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		CyclesLight( ccl::Session *session, SharedCLightPtr &light )
			: m_session( session ), m_light( light ), m_attributes( nullptr )
		{
		}

		~CyclesLight() override
		{
		}

		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override
		{
		}

		void transform( const Imath::M44f &transform ) override
		{
			ccl::Light *light = m_light.get();
			if( !light )
				return;
			ccl::Transform tfm = SocketAlgo::setTransform( transform );
			light->set_tfm( tfm );
			// To feed into area lights
			light->set_axisu( ccl::transform_get_column(&tfm, 0) );
			light->set_axisv( ccl::transform_get_column(&tfm, 1) );
			light->set_co( ccl::transform_get_column(&tfm, 3) );
			light->set_dir( -ccl::transform_get_column(&tfm, 2) );

			light->tag_update( m_session->scene );
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			// Cycles doesn't support motion samples on lights (yet)
			transform( samples[0] );
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			const CyclesAttributes *cyclesAttributes = static_cast<const CyclesAttributes *>( attributes );

			ccl::Light *light = m_light.get();
			if( !light || cyclesAttributes->applyLight( light, m_attributes.get() ) )
			{
				m_attributes = cyclesAttributes;
				light->tag_update( m_session->scene );
				return true;
			}

			return false;
		}

		void nodesCreated( NodesCreated &nodes ) const
		{
			nodes.push_back( m_light.get() );
		}

		void assignID( uint32_t id ) override
		{
			/// \todo Implement me
		}

	private :

		ccl::Session *m_session;
		SharedCLightPtr m_light;
		ConstCyclesAttributesPtr m_attributes;

};

IE_CORE_DECLAREPTR( CyclesLight )

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesCamera
//////////////////////////////////////////////////////////////////////////

namespace
{

class CyclesCamera : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		CyclesCamera( SharedCCameraPtr camera )
			: m_camera( camera )
		{
		}

		~CyclesCamera() override
		{
		}

		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override
		{
		}

		void transform( const Imath::M44f &transform ) override
		{
			ccl::Camera *camera = m_camera.get();
			if( !camera )
				return;
			Imath::M44f ctransform = transform;
			ctransform.scale( Imath::V3f( 1.0f, -1.0f, -1.0f ) );
			camera->set_matrix( SocketAlgo::setTransform( ctransform ) );
			camera->tag_modified();
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			ccl::Camera *camera = m_camera.get();
			if( !camera )
				return;
			const size_t numSamples = samples.size();

			ccl::array<ccl::Transform> motion;

			const Imath::V3f scale = Imath::V3f( 1.0f, -1.0f, -1.0f );
			Imath::M44f matrix;

			if( m_camera->get_motion_position() == ccl::MOTION_POSITION_START )
			{
				matrix = samples.front();
				matrix.scale( scale );
				camera->set_matrix( SocketAlgo::setTransform( matrix ) );
				if( numSamples != 1 )
				{
					motion = ccl::array<ccl::Transform>( 3 );
					motion[0] = camera->get_matrix();
					IECore::LinearInterpolator<Imath::M44f>()( samples.front(), samples.back(), 0.5f, matrix );
					matrix.scale( scale );
					motion[1] = SocketAlgo::setTransform( matrix );
					matrix = samples.back();
					matrix.scale( scale );
					motion[2] = SocketAlgo::setTransform( matrix );
				}
			}
			else if( m_camera->get_motion_position() == ccl::MOTION_POSITION_END )
			{
				matrix = samples.back();
				matrix.scale( scale );
				camera->set_matrix( SocketAlgo::setTransform( matrix ) );
				if( numSamples != 1 )
				{
					motion = ccl::array<ccl::Transform>( 3 );
					motion[0] = camera->get_matrix();
					IECore::LinearInterpolator<Imath::M44f>()( samples.back(), samples.front(), 0.5f, matrix );
					matrix.scale( scale );
					motion[1] = SocketAlgo::setTransform( matrix );
					matrix = samples.front();
					matrix.scale( scale );
					motion[2] = SocketAlgo::setTransform( matrix );
				}
			}
			else // ccl::Camera::MOTION_POSITION_CENTER
			{
				if( numSamples == 1 ) // One sample
				{
					matrix = samples.front();
					matrix.scale( scale );
					camera->set_matrix( SocketAlgo::setTransform( matrix ) );
				}
				else
				{
					IECore::LinearInterpolator<Imath::M44f>()( samples.front(), samples.back(), 0.5f, matrix );
					matrix.scale( scale );
					camera->set_matrix( SocketAlgo::setTransform( matrix ) );

					motion = ccl::array<ccl::Transform>( 3 );
					matrix = samples.front();
					matrix.scale( scale );
					motion[0] = SocketAlgo::setTransform( matrix );
					motion[1] = camera->get_matrix();
					matrix = samples.back();
					matrix.scale( scale );
					motion[2] = SocketAlgo::setTransform( matrix );
				}
			}
			camera->set_motion( motion );
			camera->tag_modified();
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			return false;
		}

		void assignID( uint32_t id ) override
		{
			/// \todo Implement me
		}

	private :

		SharedCCameraPtr m_camera;
		//ConstCyclesAttributesPtr m_attributes;

};

IE_CORE_DECLAREPTR( CyclesCamera )

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesRenderer
//////////////////////////////////////////////////////////////////////////

namespace
{

std::array<IECore::InternedString, 2> g_bvhLayoutEnumNames = { {
	"embree",
	"bvh2"
} };

ccl::BVHLayout nameToBvhLayoutEnum( const IECore::InternedString &name )
{
#define MAP_NAME(enumName, enum) if(name == enumName) return enum;
	MAP_NAME(g_bvhLayoutEnumNames[0], ccl::BVHLayout::BVH_LAYOUT_EMBREE);
	MAP_NAME(g_bvhLayoutEnumNames[1], ccl::BVHLayout::BVH_LAYOUT_BVH2);
#undef MAP_NAME

	return ccl::BVHLayout::BVH_LAYOUT_AUTO;
}

std::array<IECore::InternedString, 2> g_curveShapeTypeEnumNames = { {
	"ribbon",
	"thick"
} };

ccl::CurveShapeType nameToCurveShapeTypeEnum( const IECore::InternedString &name )
{
#define MAP_NAME(enumName, enum) if(name == enumName) return enum;
	MAP_NAME(g_curveShapeTypeEnumNames[0], ccl::CurveShapeType::CURVE_RIBBON);
	MAP_NAME(g_curveShapeTypeEnumNames[1], ccl::CurveShapeType::CURVE_THICK);
#undef MAP_NAME

	return ccl::CurveShapeType::CURVE_THICK;
}

// Shading-Systems
IECore::InternedString g_shadingsystemOSL( "OSL" );
IECore::InternedString g_shadingsystemSVM( "SVM" );

ccl::ShadingSystem nameToShadingSystemEnum( const IECore::InternedString &name )
{
#define MAP_NAME(enumName, enum) if(name == enumName) return enum;
	MAP_NAME(g_shadingsystemOSL, ccl::ShadingSystem::SHADINGSYSTEM_OSL);
	MAP_NAME(g_shadingsystemSVM, ccl::ShadingSystem::SHADINGSYSTEM_SVM);
#undef MAP_NAME

	return ccl::ShadingSystem::SHADINGSYSTEM_SVM;
}

// Default device
IECore::InternedString g_defaultDeviceName( "CPU" );

// Core
IECore::InternedString g_frameOptionName( "frame" );
IECore::InternedString g_cameraOptionName( "camera" );
IECore::InternedString g_sampleMotionOptionName( "sampleMotion" );
IECore::InternedString g_deviceOptionName( "ccl:device" );
IECore::InternedString g_shadingsystemOptionName( "ccl:shadingsystem" );
IECore::InternedString g_squareSamplesOptionName( "ccl:square_samples" );
// Logging
IECore::InternedString g_logLevelOptionName( "ccl:log_level" );
IECore::InternedString g_progressLevelOptionName( "ccl:progress_level" );
// Session
IECore::InternedString g_featureSetOptionName( "ccl:session:experimental" );
IECore::InternedString g_samplesOptionName( "ccl:session:samples" );
IECore::InternedString g_pixelSizeOptionName( "ccl:session:pixel_size" );
IECore::InternedString g_threadsOptionName( "ccl:session:threads" );
IECore::InternedString g_timeLimitOptionName( "ccl:session:time_limit" );
IECore::InternedString g_useProfilingOptionName( "ccl:session:use_profiling" );
IECore::InternedString g_useAutoTileOptionName( "ccl:session:use_auto_tile" );
IECore::InternedString g_tileSizeOptionName( "ccl:session:tile_size" );
// Scene
IECore::InternedString g_bvhTypeOptionName( "ccl:scene:bvh_type" );
IECore::InternedString g_bvhLayoutOptionName( "ccl:scene:bvh_layout" );
IECore::InternedString g_useBvhSpatialSplitOptionName( "ccl:scene:use_bvh_spatial_split" );
IECore::InternedString g_useBvhUnalignedNodesOptionName( "ccl:scene:use_bvh_unaligned_nodes" );
IECore::InternedString g_numBvhTimeStepsOptionName( "ccl:scene:num_bvh_time_steps" );
IECore::InternedString g_hairSubdivisionsOptionName( "ccl:scene:hair_subdivisions" );
IECore::InternedString g_hairShapeOptionName( "ccl:scene:hair_shape" );
IECore::InternedString g_textureLimitOptionName( "ccl:scene:texture_limit" );
// Background shader
IECore::InternedString g_backgroundShaderOptionName( "ccl:background:shader" );
//
IECore::InternedString g_useFrameAsSeedOptionName( "ccl:integrator:useFrameAsSeed" );
IECore::InternedString g_seedOptionName( "ccl:integrator:seed" );

ccl::PathRayFlag nameToRayType( const std::string &name )
{
#define MAP_RAY(rayname, raytype) if(name == rayname) return raytype;
	MAP_RAY( "camera", ccl::PATH_RAY_CAMERA );
	MAP_RAY( "diffuse", ccl::PATH_RAY_DIFFUSE );
	MAP_RAY( "glossy", ccl::PATH_RAY_GLOSSY );
	MAP_RAY( "transmission", ccl::PATH_RAY_TRANSMIT );
	MAP_RAY( "shadow", ccl::PATH_RAY_SHADOW );
	MAP_RAY( "scatter", ccl::PATH_RAY_VOLUME_SCATTER );
#undef MAP_RAY

	return (ccl::PathRayFlag)0;
}

// Dicing camera
IECore::InternedString g_dicingCameraOptionName( "ccl:dicing_camera" );

// Cryptomatte
IECore::InternedString g_cryptomatteAccurateOptionName( "ccl:film:cryptomatte_accurate" );
IECore::InternedString g_cryptomatteDepthOptionName( "ccl:film:cryptomatte_depth");

// Texture cache
IECore::InternedString g_useTextureCacheOptionName( "ccl:texture:use_texture_cache" );
IECore::InternedString g_textureCacheSizeOptionName( "ccl:texture:cache_size" );
IECore::InternedString g_textureAutoConvertOptionName( "ccl:texture:auto_convert" );
IECore::InternedString g_textureAcceptUnmippedOptionName( "ccl:texture:accept_unmipped" );
IECore::InternedString g_textureAcceptUntiledOptionName( "ccl:texture:accept_untiled" );
IECore::InternedString g_textureAutoTileOptionName( "ccl:texture:auto_tile" );
IECore::InternedString g_textureAutoMipOptionName( "ccl:texture:auto_mip" );
IECore::InternedString g_textureTileSizeOptionName( "ccl:texture:tile_size" );
IECore::InternedString g_textureBlurDiffuseOptionName( "ccl:texture:blur_diffuse" );
IECore::InternedString g_textureBlurGlossyOptionName( "ccl:texture:blur_glossy" );
IECore::InternedString g_textureUseCustomCachePathOptionName( "ccl:texture:use_custom_cache_path" );
IECore::InternedString g_textureCustomCachePathOptionName( "ccl:texture:custom_cache_path" );

IE_CORE_FORWARDDECLARE( CyclesRenderer )

class CyclesRenderer final : public IECoreScenePreview::Renderer
{

	public :

		enum RenderState
		{
			RENDERSTATE_READY = 0,
			RENDERSTATE_RENDERING = 1,
			RENDERSTATE_STOPPED = 3,
			RENDERSTATE_NUM_STATES
		};

		CyclesRenderer( RenderType renderType, const std::string &fileName, const IECore::MessageHandlerPtr &messageHandler )
			:	m_session( nullptr ),
				m_scene( nullptr ),
				m_sessionParams( ccl::SessionParams() ),
				m_sceneParams( ccl::SceneParams() ),
				m_bufferParams( ccl::BufferParams() ),
#ifdef WITH_CYCLES_TEXTURE_CACHE
				m_textureCacheParams( ccl::TextureCacheParams() ),
#endif
				m_deviceName( g_defaultDeviceName ),
				m_renderType( renderType ),
				m_frame( 1 ),
				m_renderState( RENDERSTATE_READY ),
				m_sceneChanged( true ),
				m_sessionReset( false ),
				m_outputsChanged( true ),
				m_pause( false ),
				m_cryptomatteAccurate( true ),
				m_cryptomatteDepth( 0 ),
				m_seed( 0 ),
				m_useFrameAsSeed( true ),
				m_messageHandler( messageHandler )
		{
			// Define internal device names
			getCyclesDevices();
			// Session Defaults
			m_bufferParamsModified = m_bufferParams;

			m_sessionParams.shadingsystem = ccl::SHADINGSYSTEM_OSL;
			m_sceneParams.shadingsystem = m_sessionParams.shadingsystem;
			m_sceneParams.bvh_layout = ccl::BVH_LAYOUT_AUTO;

			if( m_renderType != Interactive )
			{
				m_sessionParams.headless = true;
				m_sessionParams.background = true;
				m_sceneParams.bvh_type = ccl::BVH_TYPE_STATIC;
			}
			else
			{
				m_sessionParams.headless = false;
				m_sessionParams.background = false;
				m_sceneParams.bvh_type = ccl::BVH_TYPE_DYNAMIC;
			}

			m_sessionParamsDefault = m_sessionParams;
			m_sceneParamsDefault = m_sceneParams;
#ifdef WITH_CYCLES_TEXTURE_CACHE
			m_textureCacheParamsDefault = m_textureCacheParams;
#endif

			init();

			// CyclesOptions will set some values to these.
			m_integrator = *(m_scene->integrator);
			m_background = *(m_scene->background);
			m_scene->background->set_transparent( true );
			m_film = *(m_scene->film);

			m_cameraCache = new CameraCache();
			m_lightCache = new LightCache( m_scene );
			m_shaderCache = new ShaderCache( m_scene );
			m_particleSystemsCache = new ParticleSystemsCache( m_scene );
			m_instanceCache = new InstanceCache( m_scene, m_particleSystemsCache );
			m_attributesCache = new AttributesCache( m_shaderCache );

		}

		~CyclesRenderer() override
		{
			m_session->cancel();
			delete m_session;
		}

		IECore::InternedString name() const override
		{
			return "Cycles";
		}

		void option( const IECore::InternedString &name, const IECore::Object *value ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			m_sceneChanged = true;

			auto *integrator = m_scene->integrator;
			auto *background = m_scene->background;
			auto *film = m_scene->film;

			// Error about options that cannot be set while interactive rendering.
			if( m_renderState == RENDERSTATE_RENDERING )
			{
				if( name == g_deviceOptionName ||
					name == g_shadingsystemOptionName ||
					boost::starts_with( name.string(), "ccl:session:" ) ||
					boost::starts_with( name.string(), "ccl:scene:" ) ||
					boost::starts_with( name.string(), "ccl:texture:" ) )
				{
					IECore::msg( IECore::Msg::Error, "CyclesRenderer::option", boost::format( "\"%s\" requires a manual render restart." ) % name );
				}
			}

			if( name == g_frameOptionName )
			{
				if( value == nullptr )
				{
					m_frame = 0;
				}
				else if( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
				{
					m_frame = data->readable();
				}
				return;
			}
			else if( name == g_cameraOptionName )
			{
				if( value == nullptr )
				{
					m_camera = "";
				}
				else if( const StringData *data = reportedCast<const StringData>( value, "option", name ) )
				{
					m_camera = data->readable();
				}
				return;
			}
			else if( name == g_dicingCameraOptionName )
			{
				if( value == nullptr )
				{
					m_dicingCamera = "";
				}
				else if( const StringData *data = reportedCast<const StringData>( value, "option", name ) )
				{
					m_dicingCamera = data->readable();
				}
				return;
			}
			else if( name == g_sampleMotionOptionName )
			{
				const ccl::SocketType *input = integrator->node_type->find_input( ccl::ustring( "motion_blur" ) );
				if( value && input )
				{
					if( const Data *data = reportedCast<const Data>( value, "option", name ) )
					{
						SocketAlgo::setSocket( (ccl::Node*)integrator, input, data );
					}
					else
					{
						integrator->set_default_value( *input );
					}
				}
				else if( input )
				{
					integrator->set_default_value( *input );
				}
				return;
			}
			else if( name == g_deviceOptionName )
			{
				if( value == nullptr )
				{
					m_multiDevices.clear();
					const auto device = m_deviceMap.find( g_defaultDeviceName );
					if( device != m_deviceMap.end() )
					{
						m_multiDevices.push_back( device->second );
					}
					m_deviceName = g_defaultDeviceName;
				}
				else if( const StringData *data = reportedCast<const StringData>( value, "option", name ) )
				{
					m_multiDevices.clear();
					auto deviceName = data->readable();
					m_deviceName = "MULTI";

					std::vector<std::string> split;
					if( boost::contains( deviceName, " " ) )
					{
						boost::split( split, deviceName, boost::is_any_of( " " ) );
					}
					else
					{
						split.push_back( deviceName );
					}

					for( std::string &deviceStr : split )
					{
						if( deviceStr == g_defaultDeviceName.c_str() )
						{
							const auto device = m_deviceMap.find( g_defaultDeviceName );
							if( device != m_deviceMap.end() )
							{
								m_multiDevices.push_back( device->second );

								if( split.size() == 1 )
								{
									m_deviceName = g_defaultDeviceName;
									break;
								}
								continue;
							}
						}
						else if( boost::contains( deviceStr, ":" ) )
						{
							std::vector<std::string> _split;
							boost::split( _split, deviceStr, boost::is_any_of( ":" ) );
							ccl::DeviceType deviceType = ccl::Device::type_from_string( _split[0].c_str() );

							if( _split[1] == "*" )
							{
								for( const auto &device : m_deviceMap )
								{
									if( deviceType == device.second.type )
									{
										m_multiDevices.push_back( device.second );
									}
								}
							}
							else
							{
								const auto device = m_deviceMap.find( deviceStr );
								if( device != m_deviceMap.end() )
								{
									m_multiDevices.push_back( device->second );

									if( split.size() == 1 )
									{
										m_deviceName = device->second.id;
										break;
									}
									continue;
								}
								else
								{
									IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Cannot find device \"%s\" for option \"%s\"." ) % deviceStr % name.string() );
								}
							}
						}
						else
						{
							IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Cannot find device \"%s\" for option \"%s\"." ) % deviceStr % name.string() );
						}
					}
				}
				else
				{
					m_multiDevices.clear();
					const auto device = m_deviceMap.find( g_defaultDeviceName );
					if( device != m_deviceMap.end() )
					{
						m_multiDevices.push_back( device->second );
					}
					m_deviceName = g_defaultDeviceName;
					IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown value for option \"%s\"." ) % name.string() );
				}
				m_sessionReset = true;
				return;
			}
			else if( name == g_threadsOptionName )
			{
				if( value == nullptr )
				{
					m_sessionParams.threads = 0;
				}
				else if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
				{
					auto threads = data->readable();
					if( threads < 0 )
					{
						threads = max( (int)std::thread::hardware_concurrency() + threads, 1 );
					}
					m_sessionParams.threads = threads;
				}
				return;
			}
			else if( name == g_shadingsystemOptionName )
			{
				if( value == nullptr )
				{
					m_sessionParams.shadingsystem = ccl::SHADINGSYSTEM_OSL;
					m_sceneParams.shadingsystem   = ccl::SHADINGSYSTEM_OSL;
				}
				else if( const StringData *data = reportedCast<const StringData>( value, "option", name ) )
				{
					auto shadingsystemName = data->readable();

					m_sessionParams.shadingsystem = nameToShadingSystemEnum( shadingsystemName );
					m_sceneParams.shadingsystem   = nameToShadingSystemEnum( shadingsystemName );
				}
				else
				{
					IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown value for option \"%s\"." ) % name.string() );
				}
				return;
			}
			else if( name == g_logLevelOptionName )
			{
				if( value == nullptr )
				{
					ccl::util_logging_verbosity_set( 0 );
					return;
				}
				else
				{
					if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
					{
						ccl::util_logging_verbosity_set( data->readable() );
					}
					return;
				}
			}
			else if( name == g_useFrameAsSeedOptionName )
			{
				if( value == nullptr )
				{
					m_useFrameAsSeed = true;
					return;
				}
				else
				{
					if ( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
					{
						m_useFrameAsSeed = data->readable();
					}
					return;
				}
			}
			else if( name == g_seedOptionName )
			{
				if( value == nullptr )
				{
					m_seed = 0;
					return;
				}
				else
				{
					if ( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
					{
						m_seed = data->readable();
					}
					return;
				}
			}
			else if( boost::starts_with( name.string(), "ccl:session:" ) )
			{
				OPTION(bool,  m_sessionParams, g_featureSetOptionName,   experimental);
				OPTION(int,   m_sessionParams, g_samplesOptionName,      samples);
				OPTION(int,   m_sessionParams, g_pixelSizeOptionName,    pixel_size);
				OPTION(float, m_sessionParams, g_timeLimitOptionName,    time_limit);
				OPTION(bool,  m_sessionParams, g_useProfilingOptionName, use_profiling);
				OPTION(bool,  m_sessionParams, g_useAutoTileOptionName,  use_auto_tile);
				OPTION(int,   m_sessionParams, g_tileSizeOptionName,     tile_size);

				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
				return;
			}
			else if( boost::starts_with( name.string(), "ccl:scene:" ) )
			{
				if( name == g_bvhLayoutOptionName )
				{
					if( value == nullptr )
					{
						m_sceneParams.bvh_layout = ccl::BVHLayout::BVH_LAYOUT_AUTO;
					}
					else if ( const StringData *data = reportedCast<const StringData>( value, "option", name ) )
					{
						m_sceneParams.bvh_layout = nameToBvhLayoutEnum( data->readable() );
					}
					return;
				}
				if( name == g_hairShapeOptionName )
				{
					if( value == nullptr )
					{
						m_sceneParams.hair_shape = ccl::CurveShapeType::CURVE_THICK;
					}
					else if ( const StringData *data = reportedCast<const StringData>( value, "option", name ) )
					{
						m_sceneParams.hair_shape = nameToCurveShapeTypeEnum( data->readable() );
					}
					return;
				}
				OPTION(bool, m_sceneParams, g_useBvhSpatialSplitOptionName,   use_bvh_spatial_split);
				OPTION(bool, m_sceneParams, g_useBvhUnalignedNodesOptionName, use_bvh_unaligned_nodes);
				OPTION(int,  m_sceneParams, g_numBvhTimeStepsOptionName,      num_bvh_time_steps);
				OPTION(int,  m_sceneParams, g_hairSubdivisionsOptionName,     hair_subdivisions);
				OPTION(int,  m_sceneParams, g_textureLimitOptionName,         texture_limit);

				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
				return;
			}
			else if( boost::starts_with( name.string(), "ccl:texture:" ) )
			{
#ifdef WITH_CYCLES_TEXTURE_CACHE
				OPTION(bool,  m_textureCacheParams, g_useTextureCacheOptionName,           use_cache );
				OPTION(int,   m_textureCacheParams, g_textureCacheSizeOptionName,          cache_size );
				OPTION(bool,  m_textureCacheParams, g_textureAutoConvertOptionName,        auto_convert );
				OPTION(bool,  m_textureCacheParams, g_textureAcceptUnmippedOptionName,     accept_unmipped );
				OPTION(bool,  m_textureCacheParams, g_textureAcceptUntiledOptionName,      accept_untiled );
				OPTION(bool,  m_textureCacheParams, g_textureAutoTileOptionName,           auto_tile );
				OPTION(bool,  m_textureCacheParams, g_textureAutoMipOptionName,            auto_mip );
				OPTION(int,   m_textureCacheParams, g_textureTileSizeOptionName,           tile_size );
				OPTION(float, m_textureCacheParams, g_textureBlurDiffuseOptionName,        diffuse_blur );
				OPTION(float, m_textureCacheParams, g_textureBlurGlossyOptionName,         glossy_blur );
				OPTION(bool,  m_textureCacheParams, g_textureUseCustomCachePathOptionName, use_custom_cache_path );
				OPTION_STR(   m_textureCacheParams, g_textureCustomCachePathOptionName,    custom_cache_path );
#endif

				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
				return;
			}
			// The last 3 are subclassed internally from ccl::Node so treat their params like Cycles sockets
			else if( boost::starts_with( name.string(), "ccl:background:" ) )
			{
				const ccl::SocketType *input = background->node_type->find_input( ccl::ustring( name.string().c_str() + 15 ) );
				if( value && input )
				{
					if( boost::starts_with( name.string(), "ccl:background:visibility:" ) )
					{
						if( const Data *d = reportedCast<const IECore::Data>( value, "option", name ) )
						{
							if( const IntData *data = static_cast<const IntData *>( d ) )
							{
								auto &vis = data->readable();
								auto ray = nameToRayType( name.string().c_str() + 26 );
								uint prevVis = background->get_visibility();
								background->set_visibility( vis ? prevVis |= ray : prevVis & ~ray );
							}
						}
					}
					else if( name == g_backgroundShaderOptionName )
					{
						m_backgroundShader = nullptr;
						if( const IECoreScene::ShaderNetwork *d = reportedCast<const IECoreScene::ShaderNetwork>( value, "option", name ) )
						{
							m_backgroundShader = m_shaderCache->get( d );
						}
						else
						{
							m_backgroundShader = nullptr;
						}
					}
					else if( const Data *data = reportedCast<const Data>( value, "option", name ) )
					{
						SocketAlgo::setSocket( (ccl::Node*)background, input, data );
					}
					else
					{
						background->set_default_value( *input );
					}
				}
				else if( input )
				{
					background->set_default_value( *input );
				}
				return;
			}
			else if( boost::starts_with( name.string(), "ccl:film:" ) )
			{
				if( name == g_cryptomatteAccurateOptionName )
				{
					m_outputsChanged = true;
					if( value == nullptr )
					{
						m_cryptomatteAccurate = false;
						return;
					}
					if( const BoolData *data = reportedCast<const BoolData>( value, "option", name ) )
					{
						m_cryptomatteAccurate = data->readable();
						return;
					}
				}

				if( name == g_cryptomatteDepthOptionName )
				{
					m_outputsChanged = true;
					if( value == nullptr )
					{
						m_cryptomatteDepth = 0;
						return;
					}
					if( const IntData *data = reportedCast<const IntData>( value, "option", name ) )
					{
						m_cryptomatteDepth = data->readable();
						return;
					}
				}

				const ccl::SocketType *input = film->node_type->find_input( ccl::ustring( name.string().c_str() + 9 ) );
				if( value && input )
				{
					if( const Data *data = reportedCast<const Data>( value, "option", name ) )
					{
						SocketAlgo::setSocket( (ccl::Node*)film, input, data );
					}
					else
					{
						film->set_default_value( *input );
					}
				}
				else if( input )
				{
					film->set_default_value( *input );
				}
				return;
			}
			else if( boost::starts_with( name.string(), "ccl:integrator:" ) )
			{
				const ccl::SocketType *input = integrator->node_type->find_input( ccl::ustring( name.string().c_str() + 15 ) );
				if( value && input )
				{
					if( const Data *data = reportedCast<const Data>( value, "option", name ) )
					{
						SocketAlgo::setSocket( (ccl::Node*)integrator, input, data );
					}
					else
					{
						integrator->set_default_value( *input );
					}
				}
				else if( input )
				{
					integrator->set_default_value( *input );
				}
				return;
			}
			else if( boost::starts_with( name.string(), "ccl:" ) )
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
				return;
			}
			else if( boost::starts_with( name.string(), "user:" ) )
			{
				IECore::msg( Msg::Warning, "CyclesRenderer::option", boost::format( "User option \"%s\" not supported" ) % name.string() );
				return;
			}
			else if( boost::contains( name.c_str(), ":" ) )
			{
				// Ignore options prefixed for some other renderer.
				return;
			}
			else
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.string() );
				return;
			}
		}

		void output( const IECore::InternedString &name, const Output *output ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			if( !output )
			{
				// Remove output pass
				const auto coutput = m_outputs.find( name );
				if( coutput != m_outputs.end() )
				{
					m_outputs.erase( name );
					m_outputsChanged = true;
				}
			}
			else
			{
				const auto coutput = m_outputs.find( name );
				if( coutput == m_outputs.end() )
				{
					m_outputs[name] = new CyclesOutput( m_session, name, output );
					m_outputsChanged = true;
				}
			}
		}

		Renderer::AttributesInterfacePtr attributes( const IECore::CompoundObject *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			return m_attributesCache->get( attributes );
		}

		ObjectInterfacePtr camera( const std::string &name, const IECoreScene::Camera *camera, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			SharedCCameraPtr ccamera = m_cameraCache->get( camera, name );
			if( !ccamera )
			{
				return nullptr;
			}

			// Store the camera for later use in updateCamera().
			m_cameras[name] = camera;

			ObjectInterfacePtr result = new CyclesCamera( ccamera );
			result->attributes( attributes );
			return result;
		}

		ObjectInterfacePtr light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			SharedCLightPtr clight = m_lightCache->get( name );
			if( !clight )
			{
				return nullptr;
			}

			CyclesLightPtr result = new CyclesLight( m_session, clight );
			result->attributes( attributes );

			result->nodesCreated( m_lightsCreated );

			return result;
		}

		ObjectInterfacePtr lightFilter( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			IECore::msg( IECore::Msg::Warning, "CyclesRenderer", "lightFilter() unimplemented" );
			return nullptr;
		}

		ObjectInterfacePtr object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			if( object->typeId() == IECoreScene::Camera::staticTypeId() )
			{
				return nullptr;
			}

			Instance instance = m_instanceCache->get( object, attributes, name );

			ObjectInterfacePtr result = new CyclesObject( m_session, instance, m_frame );
			result->attributes( attributes );

			instance.objectsCreated( m_objectsCreated );
			// These will only accumulate if it's the prototype
			instance.geometryCreated( m_geometryCreated );
			instance.particleSystemsCreated( m_particleSystemsCreated );

			return result;
		}

		ObjectInterfacePtr object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			if( samples.front()->typeId() == IECoreScene::Camera::staticTypeId() )
			{
				return nullptr;
			}

			int frameIdx = -1;
			if( m_scene->camera->get_motion_position() == ccl::MOTION_POSITION_START )
			{
				frameIdx = 0;
			}
			else if( m_scene->camera->get_motion_position() == ccl::MOTION_POSITION_END )
			{
				frameIdx = times.size()-1;
			}
			Instance instance = m_instanceCache->get( samples, times, frameIdx, attributes, name );

			ObjectInterfacePtr result = new CyclesObject( m_session, instance, m_frame );
			result->attributes( attributes );

			instance.objectsCreated( m_objectsCreated );
			// These will only accumulate if it's the prototype
			instance.geometryCreated( m_geometryCreated );
			instance.particleSystemsCreated( m_particleSystemsCreated );

			return result;
		}

		void render() override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			m_scene->mutex.lock();
			{
				if( m_renderState == RENDERSTATE_RENDERING && m_renderType == Interactive )
				{
					clearUnused();
				}

				updateSceneObjects();
				updateOptions();
				updateCamera();
				updateOutputs();

				if( m_renderState == RENDERSTATE_RENDERING )
				{
					if( m_scene->need_reset() )
					{
						m_session->reset( m_sessionParams, m_bufferParams );
					}
				}

				// Dirty flag here is so that we don't unlock on a re-created scene if a reset happened
				if( !m_sessionReset )
				{
					m_scene->mutex.unlock();
				}
				else
				{
					m_sessionReset = false;
				}

				if( m_renderState == RENDERSTATE_RENDERING )
				{
					m_session->start();
				}

				m_sceneChanged = false;
			}
			m_scene->mutex.unlock();

			if( m_renderState == RENDERSTATE_RENDERING )
			{
				m_pause = false;
				m_session->set_pause( m_pause );
				return;
			}

			m_session->start();

			m_renderState = RENDERSTATE_RENDERING;

			if( m_renderType == Interactive )
			{
				return;
			}

			// Free up caches, Cycles now owns the data.
			resetCaches();
			m_session->wait();
			m_renderState = RENDERSTATE_STOPPED;
		}

		void pause() override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			if( m_renderState == RENDERSTATE_RENDERING )
			{
				m_pause = true;
				m_session->set_pause( m_pause );
			}
		}

	private :

		void init()
		{
			// Fallback
			ccl::DeviceType deviceTypeFallback = ccl::DEVICE_CPU;
			ccl::DeviceInfo deviceFallback;

			bool deviceAvailable = false;
			for( const ccl::DeviceInfo& device : IECoreCycles::devices() )
			{
				if( deviceTypeFallback == device.type )
				{
					deviceFallback = device;
					break;
				}
			}

			if( m_multiDevices.size() == 0 )
			{
				m_deviceName = g_defaultDeviceName;
			}

			if( m_deviceName == "MULTI" )
			{
				ccl::DeviceInfo multidevice = ccl::Device::get_multi_device( m_multiDevices, m_sessionParams.threads, m_sessionParams.background );
				m_sessionParams.device = multidevice;
				deviceAvailable = true;
			}
			else
			{
				for( const ccl::DeviceInfo& device : IECoreCycles::devices() )
				{
					if( m_deviceName ==  device.id )
					{
						m_sessionParams.device = device;
						deviceAvailable = true;
						break;
					}
				}
			}

			if( !deviceAvailable )
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer", boost::format( "Cannot find the device \"%s\" requested, reverting to CPU." ) % m_deviceName );
				m_sessionParams.device = deviceFallback;
			}

			if( m_sessionParams.device.type != ccl::DEVICE_CPU && m_sessionParams.shadingsystem == ccl::SHADINGSYSTEM_OSL )
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer", "Shading system set to OSL, reverting to CPU." );
				m_sessionParams.device = deviceFallback;
			}

			if( m_session )
			{
				// A trick to retain the same pointer when re-creating a session.
				m_session->~Session();
				new ( m_session ) ccl::Session( m_sessionParams, m_sceneParams );
			}
			else
			{
				m_session = new ccl::Session( m_sessionParams, m_sceneParams );
			}

			m_session->progress.set_update_callback( function_bind( &CyclesRenderer::progress, this ) );

			m_scene = m_session->scene;

			m_scene->camera->need_flags_update = true;
			m_scene->camera->update( m_scene );

			// Set a more sane default than the arbitrary 0.8f
			m_scene->film->set_exposure( 1.0f );
		}

		void clearUnused()
		{
			m_cameraCache->clearUnused();
			m_instanceCache->clearUnused();
			m_particleSystemsCache->clearUnused();
			m_lightCache->clearUnused();
			m_attributesCache->clearUnused();
		}

		void updateSceneObjects( bool newScene = false )
		{
			if( newScene )
			{
				// Get all objects held by Gaffer
				m_instanceCache->nodesCreated( m_objectsCreated, m_geometryCreated );
				m_lightCache->nodesCreated( m_lightsCreated );
				m_particleSystemsCache->nodesCreated( m_particleSystemsCreated );
			}

			// Add every shader each time, less issues
			m_shaderCache->nodesCreated( m_shadersCreated );

			m_lightCache->update( m_scene, m_lightsCreated );
			m_particleSystemsCache->update( m_scene, m_particleSystemsCreated );
			m_instanceCache->update( m_scene, m_objectsCreated, m_geometryCreated );
			m_shaderCache->update( m_scene, m_shadersCreated );
		}

		void updateOptions()
		{
#ifdef WITH_CYCLES_TEXTURE_CACHE
			m_sceneParams.texture = m_textureCacheParams;
#endif

			ccl::Integrator *integrator = m_scene->integrator;
			ccl::Background *background = m_scene->background;

			if( m_useFrameAsSeed )
			{
				integrator->set_seed( m_frame );
			}
			else
			{
				integrator->set_seed( m_seed );
			}

			ccl::Shader *lightShader = nullptr;
			for( ccl::Light *light : m_scene->lights )
			{
				if( light->get_light_type() == ccl::LIGHT_BACKGROUND )
				{
					lightShader = light->get_shader();
					break;
				}
			}

			ccl::Film *film = m_scene->film;

			m_session->set_samples( m_sessionParams.samples );

			if( m_backgroundShader )
			{
				background->set_shader( m_backgroundShader->shader() );
			}
			else if( lightShader )
			{
				background->set_shader( lightShader );
			}
			else
			{
				background->set_shader( m_scene->default_empty );
			}

			if( integrator->is_modified() )
			{
				integrator->tag_update( m_scene, ccl::Integrator::UPDATE_ALL );
				m_integrator = *integrator;
			}

			if( background->is_modified() )
			{
				background->tag_update( m_scene );
				m_background = *background;
			}

			if( film->is_modified() )
			{
				//film->tag_update( m_scene );
				integrator->tag_update( m_scene, ccl::Integrator::UPDATE_ALL );
				m_film = *film;
			}

			// Check if an OSL shader exists & set the shadingsystem
			if( m_sessionParams.shadingsystem == ccl::SHADINGSYSTEM_SVM && m_shaderCache->hasOSLShader() )
			{
				if( m_renderState != RENDERSTATE_RENDERING )
				{
					IECore::msg( IECore::Msg::Warning, "CyclesRenderer", "OSL Shader detected, forcing OSL shading-system (CPU-only)" );
					m_sessionParams.shadingsystem = ccl::SHADINGSYSTEM_OSL;
					m_sceneParams.shadingsystem = ccl::SHADINGSYSTEM_OSL;
				}
				else
				{
					IECore::msg( IECore::Msg::Error, "CyclesRenderer", "OSL Shader detected, this will cause problems in a running interactive render" );
					m_shaderCache->removeOSLShaders();
				}
			}

			// If anything changes in scene or session, we reset.
			if( m_scene->params.modified( m_sceneParams ) ||
				m_session->params.modified( m_sessionParams ) ||
				m_sessionReset )
			{
				// Flag it true here so that we never mutex unlock a different scene pointer due to the reset
				if( m_renderState != RENDERSTATE_RENDERING )
				{
					m_sessionReset = true;
					reset();
				}
			}
		}

		void updateOutputs()
		{
			ccl::Camera *camera = m_scene->camera;
			int width = camera->get_full_width();
			int height = camera->get_full_height();
			m_bufferParamsModified.full_width = width;
			m_bufferParamsModified.full_height = height;
			m_bufferParamsModified.full_x = (int)(camera->get_border_left() * (float)width);
			m_bufferParamsModified.full_y = (int)(camera->get_border_bottom() * (float)height);
			m_bufferParamsModified.width =  (int)(camera->get_border_right() * (float)width) - m_bufferParamsModified.full_x;
			m_bufferParamsModified.height = (int)(camera->get_border_top() * (float)height) - m_bufferParamsModified.full_y;

			if( m_bufferParams.modified( m_bufferParamsModified ) )
			{
				m_outputsChanged = true;
				m_bufferParams = m_bufferParamsModified;
			}

			if( !m_outputsChanged )
				return;

			Box2i displayWindow(
				V2i( 0, 0 ),
				V2i( width - 1, height - 1 )
				);
			Box2i dataWindow(
				V2i( (int)(camera->get_border_left()   * (float)width ),
					 (int)(camera->get_border_bottom() * (float)height ) ),
				V2i( (int)(camera->get_border_right()  * (float)width ) - 1,
					 (int)(camera->get_border_top()    * (float)height - 1 ) )
				);

			ccl::set<ccl::Pass *> clearPasses( m_scene->passes.begin(), m_scene->passes.end() );
			m_scene->delete_nodes( clearPasses );

			CompoundDataPtr paramData = new CompoundData();

			paramData->writable()["default"] = new StringData( "rgba" );

			ccl::CryptomatteType crypto = ccl::CRYPT_NONE;
			if( m_cryptomatteAccurate )
			{
				crypto = static_cast<ccl::CryptomatteType>( crypto | ccl::CRYPT_ACCURATE );
			}

			CompoundDataPtr layersData = new CompoundData();
			InternedString cryptoAsset;
			InternedString cryptoObject;
			InternedString cryptoMaterial;
			bool hasShadowCatcher = false;
			bool hasDenoise = false;
			for( auto &coutput : m_outputs )
			{
				if( ( m_renderType != Interactive && coutput.second->m_interactive ) ||
					( m_renderType == Interactive && !coutput.second->m_interactive ) )
				{
					continue;
				}

				ccl::PassType passType = coutput.second->m_passType;

				// We need to add all lightgroup passes in-order
				if( coutput.second->m_lightgroup )
					continue;

				if( passType == ccl::PASS_CRYPTOMATTE )
				{
					if( coutput.second->m_data == "cryptomatte_asset" )
					{
						crypto = static_cast<ccl::CryptomatteType>( crypto | ccl::CRYPT_ASSET );
						cryptoAsset = coutput.first;
					}
					else if( coutput.second->m_data == "cryptomatte_object" )
					{
						crypto = static_cast<ccl::CryptomatteType>( crypto | ccl::CRYPT_OBJECT );
						cryptoObject = coutput.first;
					}
					else if( coutput.second->m_data == "cryptomatte_material" )
					{
						crypto = static_cast<ccl::CryptomatteType>( crypto | ccl::CRYPT_MATERIAL );
						cryptoMaterial = coutput.first;
					}
					continue;
				}

				if( passType == ccl::PASS_SHADOW_CATCHER )
				{
					hasShadowCatcher = true;
				}

				bool denoise = coutput.second->m_denoise;
				hasDenoise |= denoise;
				std::string name = denoise ? ccl::string_printf( "%s_denoised", coutput.second->m_data.c_str() ) : coutput.second->m_data;
				ccl::Pass *pass = m_scene->create_node<ccl::Pass>();
				pass->set_type( passType );
				pass->set_name( ccl::ustring( name ) );
				pass->set_mode( denoise ? ccl::PassMode::DENOISED : ccl::PassMode::NOISY );

				const IECore::CompoundDataPtr layer = coutput.second->m_parameters->copy();
				layersData->writable()[name] = layer;
			}

			// Adding cryptomattes in-order matters
			ccl::Film *film = m_scene->film;
			if( crypto == ccl::CRYPT_NONE || crypto == ( ccl::CRYPT_NONE | ccl::CRYPT_ACCURATE ) )
			{
				// If there's no crypto, we must set depth to 0 otherwise bugs appear
				film->set_cryptomatte_depth( 0 );
			}
			else if( !m_cryptomatteDepth )
			{
				// At least have 1 depth if there are crypto passes
				film->set_cryptomatte_depth( 1 );
			}
			else
			{
				film->set_cryptomatte_depth( ccl::divide_up( std::min( 16, m_cryptomatteDepth ), 2 ) );
			}
			int depth = film->get_cryptomatte_depth();
			if( crypto & ccl::CRYPT_OBJECT )
			{
				std::string name( "cryptomatte_object" );
				IECore::CompoundDataPtr layer = m_outputs[cryptoObject]->m_parameters->copy();
				updateCryptomatteMetadata( layer.get(), name, m_scene );
				for( int i = 0; i < depth; ++i )
				{
					ccl::Pass *pass = m_scene->create_node<ccl::Pass>();
					pass->set_type( ccl::PASS_CRYPTOMATTE );
					pass->set_name( ccl::ustring( ccl::string_printf( "%s%02d", name.c_str(), i ) ) );
					pass->set_mode( ccl::PassMode::NOISY );
					layersData->writable()[pass->get_name().c_str()] = layer;
				}
			}
			if( crypto & ccl::CRYPT_MATERIAL )
			{
				std::string name( "cryptomatte_material" );
				IECore::CompoundDataPtr layer = m_outputs[cryptoMaterial]->m_parameters->copy();
				updateCryptomatteMetadata( layer.get(), name, m_scene );
				for( int i = 0; i < depth; ++i )
				{
					ccl::Pass *pass = m_scene->create_node<ccl::Pass>();
					pass->set_type( ccl::PASS_CRYPTOMATTE );
					pass->set_name( ccl::ustring( ccl::string_printf( "%s%02d", name.c_str(), i ) ) );
					pass->set_mode( ccl::PassMode::NOISY );
					layersData->writable()[pass->get_name().c_str()] = layer;
				}
			}
			if( crypto & ccl::CRYPT_ASSET )
			{
				std::string name( "cryptomatte_asset" );
				IECore::CompoundDataPtr layer = m_outputs[cryptoAsset]->m_parameters->copy();
				updateCryptomatteMetadata( layer.get(), name, m_scene );
				for( int i = 0; i < depth; ++i )
				{
					ccl::Pass *pass = m_scene->create_node<ccl::Pass>();
					pass->set_type( ccl::PASS_CRYPTOMATTE );
					pass->set_name( ccl::ustring( ccl::string_printf( "%s%02d", name.c_str(), i ) ) );
					pass->set_mode( ccl::PassMode::NOISY );
					layersData->writable()[pass->get_name().c_str()] = layer;
				}
			}

#ifdef WITH_CYCLES_LIGHTGROUPS
			// Add lightgroups on the end
			for( auto &coutput : m_outputs )
			{
				if( ( m_renderType != Interactive && coutput.second->m_interactive ) ||
					( m_renderType == Interactive && !coutput.second->m_interactive ) )
				{
					continue;
				}

				ccl::PassType passType = coutput.second->m_passType;

				if( !coutput.second->m_lightgroup )
					continue;

				bool denoise = coutput.second->m_denoise;
				hasDenoise |= denoise;
				std::string name = denoise ? ccl::string_printf( "%s_denoised", coutput.second->m_data.c_str() ) : coutput.second->m_data;
				ccl::Pass *pass = m_scene->create_node<ccl::Pass>();
				pass->set_type( passType );
				pass->set_name( ccl::ustring( name ) );
				pass->set_mode( denoise ? ccl::PassMode::DENOISED : ccl::PassMode::NOISY );
				pass->set_lightgroup( ccl::ustring( coutput.second->m_data ) );

				const IECore::CompoundDataPtr layer = coutput.second->m_parameters->copy();
				layersData->writable()[name] = layer;
			}
#endif

			paramData->writable()["layers"] = layersData;

			film->set_cryptomatte_passes( crypto );
			film->set_use_approximate_shadow_catcher( !hasShadowCatcher );
			m_scene->integrator->set_use_denoise( hasDenoise );
			if( m_renderType == Interactive )
				m_session->set_output_driver( ccl::make_unique<IEDisplayOutputDriver>( displayWindow, dataWindow, paramData ) );
			else
				m_session->set_output_driver( ccl::make_unique<OIIOOutputDriver>( displayWindow, dataWindow, paramData ) );
			m_session->reset( m_sessionParams, m_bufferParams );

			m_outputsChanged = false;
		}

		void reset()
		{
			m_session->cancel();
			m_renderState = RENDERSTATE_READY;
			// This is so cycles doesn't delete the objects that Gaffer manages.
			m_scene->objects.clear();
			m_scene->geometry.clear();
			m_shaderCache->flushTextures();
			m_scene->shaders.resize( m_shaderCache->numDefaultShaders() );
			m_scene->lights.clear();
			m_scene->particle_systems.clear();

			init();

			// Re-apply the settings for these.
			for( const ccl::SocketType &socketType : m_scene->integrator->type->inputs )
			{
				m_scene->integrator->copy_value(socketType, m_integrator, *m_integrator.type->find_input( socketType.name ) );
			}
			for( const ccl::SocketType &socketType : m_scene->background->type->inputs )
			{
				m_scene->background->copy_value(socketType, m_background, *m_background.type->find_input( socketType.name ) );
			}
			for( const ccl::SocketType &socketType : m_scene->film->type->inputs )
			{
				m_scene->film->copy_value(socketType, m_film, *m_film.type->find_input( socketType.name ) );
			}

			m_scene->shader_manager->tag_update( m_scene, ccl::ShaderManager::UPDATE_ALL );
			m_scene->integrator->tag_update( m_scene, ccl::Integrator::UPDATE_ALL );
			m_scene->background->tag_update( m_scene );

			m_session->stats.mem_peak = m_session->stats.mem_used;
			// Make sure the instance cache points to the right scene.
			updateSceneObjects( true );
			m_scene->geometry_manager->tag_update( m_scene, ccl::GeometryManager::UPDATE_ALL );
		}

		void updateCamera()
		{
			// Check that the camera we want to use exists,
			// and if not, create a default one.
			{
				const auto cameraIt = m_cameras.find( m_camera );
				if( cameraIt == m_cameras.end() )
				{
					if( !m_camera.empty() )
					{
						IECore::msg(
							IECore::Msg::Warning, "CyclesRenderer",
							boost::format( "Camera \"%s\" does not exist" ) % m_camera
						);
					}

					if( m_scene->camera->name != m_camera || m_cameraDefault.is_modified() )
					{
						ccl::Camera prevcam = *m_scene->camera;
						*m_scene->camera = m_cameraDefault;
						m_scene->camera->shutter_table_offset = prevcam.shutter_table_offset;
						m_scene->camera->need_flags_update = prevcam.need_flags_update;
						m_scene->camera->update( m_scene );
						m_cameraDefault = *m_scene->camera;
					}
				}
				else
				{
					ccl::Camera *ccamera = m_cameraCache->get( cameraIt->second.get(), cameraIt->first ).get();
					if( m_scene->camera->name != m_camera || ccamera->is_modified() )
					{
						ccl::Camera prevcam = *m_scene->camera;
						*m_scene->camera = *ccamera;
						m_scene->camera->shutter_table_offset = prevcam.shutter_table_offset;
						m_scene->camera->need_flags_update = prevcam.need_flags_update;
						m_scene->camera->update( m_scene );
						*ccamera = *m_scene->camera;
					}
				}
			}

			// Dicing camera update
			{
				const auto cameraIt = m_cameras.find( m_dicingCamera );
				if( cameraIt == m_cameras.end() )
				{
					if( !m_camera.empty() && ( m_dicingCamera != "" ) )
					{
						IECore::msg(
							IECore::Msg::Warning, "CyclesRenderer",
							boost::format( "Dicing camera \"%s\" does not exist" ) % m_dicingCamera
						);
					}
					*m_scene->dicing_camera = *m_scene->camera;
				}
				else
				{
					ccl::Camera *ccamera = m_cameraCache->get( cameraIt->second.get(), cameraIt->first ).get();
					if( m_scene->camera->name != m_dicingCamera || ccamera->is_modified() )
					{
						*m_scene->dicing_camera = *ccamera;
						m_scene->dicing_camera->update( m_scene );
						*ccamera = *m_scene->camera;
					}
				}
			}
		}

		void progress()
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			string status, subStatus, memStatus;
			double totalTime, renderTime;
			float memUsed = (float)m_session->stats.mem_used / 1024.0f / 1024.0f / 1024.0f;
			float memPeak = (float)m_session->stats.mem_peak / 1024.0f / 1024.0f / 1024.0f;

			m_session->progress.get_status( status, subStatus );
			m_session->progress.get_time( totalTime, renderTime );

			if( subStatus != "" )
				status += ": " + subStatus;

			memStatus = ccl::string_printf( "Mem:%.3fG, Peak:%.3fG", (double)memUsed, (double)memPeak );

			double currentTime = ccl::time_dt();
			if( status != m_lastStatus )// || ( m_renderType == Interactive && ( currentTime - m_lastStatusTime ) > 1.0 ) )
			{
				IECore::msg( IECore::MessageHandler::Level::Info, "Cycles", memStatus + " | " + status );
				m_lastStatus = status;
				m_lastStatusTime = currentTime;
			}

			if( m_session->progress.get_error() )
			{
				string error = m_session->progress.get_error_message();
				if (error != m_lastError)
				{
					IECore::msg( IECore::MessageHandler::Level::Error, "Cycles", error );
					m_lastError = error;
				}
			}

			// Not sure what the best way is to inform that an interactive render has stopped other than this.
			// No way that I know of to inform Gaffer that the render has stopped either.
			if( m_lastStatus == "Finished" )
			{
				m_renderState = RENDERSTATE_STOPPED;
			}
		}

		void getCyclesDevices()
		{
			int indexCuda = 0;
			int indexHIP = 0;
			int indexOptiX = 0;
			int indexMetal = 0;
			for( const ccl::DeviceInfo &device : IECoreCycles::devices() )
			{
				if( device.type == ccl::DEVICE_CPU )
				{
					m_deviceMap[g_defaultDeviceName] = device;
					continue;
				}
				string deviceName = ccl::Device::string_from_type( device.type ).c_str();
				if( device.type == ccl::DEVICE_CUDA )
				{
					auto optionName = boost::format( "CUDA:%02i" ) % indexCuda;
					m_deviceMap[optionName.str()] = device;
					++indexCuda;
					continue;
				}
				if( device.type == ccl::DEVICE_HIP )
				{
					auto optionName = boost::format( "HIP:%02i" ) % indexHIP;
					m_deviceMap[optionName.str()] = device;
					++indexHIP;
					continue;
				}
				if( device.type == ccl::DEVICE_OPTIX )
				{
					auto optionName = boost::format( "OPTIX:%02i" ) % indexOptiX;
					m_deviceMap[optionName.str()] = device;
					++indexOptiX;
					continue;
				}
				if( device.type == ccl::DEVICE_METAL )
				{
					auto optionName = boost::format( "METAL:%02i" ) % indexMetal;
					m_deviceMap[optionName.str()] = device;
					++indexMetal;
					continue;
				}
			}
		}

		void resetCaches()
		{
			m_cameraCache.reset();
			m_instanceCache.reset();
			m_lightCache.reset();
			m_particleSystemsCache.reset();
			m_shaderCache.reset();
			m_attributesCache.reset();
		}

		// Cycles core objects.
		ccl::Session *m_session;
		ccl::Scene *m_scene;
		ccl::SessionParams m_sessionParams;
		ccl::SceneParams m_sceneParams;
		ccl::BufferParams m_bufferParams;
		ccl::BufferParams m_bufferParamsModified;
#ifdef WITH_CYCLES_TEXTURE_CACHE
		ccl::TextureCacheParams m_textureCacheParams;
#endif
		ccl::Integrator m_integrator;
		ccl::Background m_background;
		ccl::Film m_film;

		// Background shader
		CyclesShaderPtr m_backgroundShader;

		// Defaults
		ccl::Camera m_cameraDefault;
		ccl::SessionParams m_sessionParamsDefault;
		ccl::SceneParams m_sceneParamsDefault;
#ifdef WITH_CYCLES_TEXTURE_CACHE
		ccl::TextureCacheParams m_textureCacheParamsDefault;
#endif

		// IECoreScene::Renderer
		string m_deviceName;
		RenderType m_renderType;
		int m_frame;
		string m_camera;
		RenderState m_renderState;
		bool m_sceneChanged;
		bool m_sessionReset;
		bool m_outputsChanged;
		bool m_pause;
		bool m_cryptomatteAccurate;
		int m_cryptomatteDepth;
		int m_seed;
		bool m_useFrameAsSeed;

		// Logging
		IECore::MessageHandlerPtr m_messageHandler;
		string m_lastError;
		string m_lastStatus;
		double m_lastStatusTime;

		// Caches
		CameraCachePtr m_cameraCache;
		ShaderCachePtr m_shaderCache;
		LightCachePtr m_lightCache;
		InstanceCachePtr m_instanceCache;
		ParticleSystemsCachePtr m_particleSystemsCache;
		AttributesCachePtr m_attributesCache;

		// Nodes created to update to Cycles
		NodesCreated m_objectsCreated;
		NodesCreated m_lightsCreated;
		NodesCreated m_geometryCreated;
		NodesCreated m_particleSystemsCreated;
		NodesCreated m_shadersCreated;

		// Outputs
		OutputMap m_outputs;

		// Multi-Devices
		typedef unordered_map<string, ccl::DeviceInfo> DeviceMap;
		DeviceMap m_deviceMap;
		ccl::vector<ccl::DeviceInfo> m_multiDevices;

		// Cameras (Cycles can only know of one camera at a time)
		typedef tbb::concurrent_unordered_map<std::string, IECoreScene::ConstCameraPtr> CameraMap;
		CameraMap m_cameras;
		string m_dicingCamera;

		// Registration with factory
		static Renderer::TypeDescription<CyclesRenderer> g_typeDescription;

};

IECoreScenePreview::Renderer::TypeDescription<CyclesRenderer> CyclesRenderer::g_typeDescription( "Cycles" );

} // namespace
