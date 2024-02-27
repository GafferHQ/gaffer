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

#include "GafferCycles/IECoreCyclesPreview/CameraAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/GeometryAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/IECoreCycles.h"
#include "GafferCycles/IECoreCyclesPreview/ShaderNetworkAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

#include "IEDisplayOutputDriver.h"
#include "OIIOOutputDriver.h"

#include "IECoreScene/Camera.h"
#include "IECoreScene/CurvesPrimitive.h"
#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/Shader.h"
#include "IECoreScene/SpherePrimitive.h"

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

#include "OpenEXR/OpenEXRConfig.h"
#if OPENEXR_VERSION_MAJOR < 3
#include "OpenEXR/ImathMatrixAlgo.h"
#else
#include "Imath/ImathMatrixAlgo.h"
#endif

#include "boost/algorithm/string.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/container/flat_map.hpp"
#include "boost/optional.hpp"

#include "tbb/concurrent_unordered_map.h"
#include "tbb/concurrent_hash_map.h"
#include "tbb/concurrent_vector.h"

#include "fmt/format.h"

#include <unordered_map>

// Cycles
IECORE_PUSH_DEFAULT_VISIBILITY
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
#include "util/types.h"
#include "util/vector.h"
IECORE_POP_DEFAULT_VISIBILITY

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

	IECore::msg( IECore::Msg::Warning, "IECoreCycles::Renderer",
		fmt::format(
			"Expected {} but got {} for {} \"{}\".",
			T::staticTypeName(), v->typeName(), type, name.c_str()
		)
	);
	return nullptr;
}

template<typename T>
const T *attribute( const IECore::InternedString &name, const IECore::CompoundObject *attributes, const T *defaultValue = nullptr )
{
	if( !attributes )
	{
		return defaultValue;
	}

	IECore::CompoundObject::ObjectMap::const_iterator it = attributes->members().find( name );
	if( it == attributes->members().end() )
	{
		return defaultValue;
	}

	if( auto r = reportedCast<const T>( it->second.get(), "attribute", name ) )
	{
		return r;
	}

	return defaultValue;
}

template<typename T>
T attributeValue( const IECore::InternedString &name, const IECore::CompoundObject *attributes, const T &defaultValue )
{
	using DataType = IECore::TypedData<T>;
	const DataType *data = attribute<DataType>( name, attributes );
	return data ? data->readable() : defaultValue;
}

template<typename T>
boost::optional<T> optionalAttribute( const IECore::InternedString &name, const IECore::CompoundObject *attributes )
{
	using DataType = IECore::TypedData<T>;
	const DataType *data = attribute<DataType>( name, attributes );
	return data ? data->readable() : boost::optional<T>();
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

#define OPTION(TYPE, CATEGORY, OPTIONNAME, OPTION) if( name == OPTIONNAME ) { \
	if( value == nullptr ) { \
		CATEGORY.OPTION = CATEGORY ## Default.OPTION; \
		return; } \
	if ( const IECore::TypedData<TYPE> *data = reportedCast<const IECore::TypedData<TYPE>>( value, "option", name ) ) { \
		CATEGORY.OPTION = data->readable(); } \
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

		CyclesOutput( const IECore::InternedString &name, const IECoreScene::Output *output )
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
				if( tokens[0] == "float" && tokens[1] == "Z" )
				{
					m_data = tokens[1];
					p["name"] = new StringData( tokens[1] );
					p["type"] = new StringData( "depth" );
					passType = "depth";
				}
				else if( tokens[0] == "uint" && tokens[1] == "id" )
				{
					m_data = tokens[1];
					p["name"] = new StringData( tokens[1] );
					p["type"] = new StringData( "object_id" );
					passType = "object_id";
				}
				else if( tokens[0] == "float" )
				{
					p["name"] = m_denoise ? new StringData( ccl::string_printf( "%s_denoised", tokens[1].c_str() ) ) : new StringData( tokens[1] );
					p["type"] = new StringData( "aov_value" );
					passType = "aov_value";
					m_data = tokens[1];
				}
				else if( tokens[0] == "color" )
				{
					p["name"] = m_denoise ? new StringData( ccl::string_printf( "%s_denoised", tokens[1].c_str() ) ) : new StringData( tokens[1] );
					p["type"] = new StringData( "aov_color" );
					passType = "aov_color";
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
IECore::InternedString g_cyclesDisplacementShaderAttributeName( "cycles:displacement" );
IECore::InternedString g_shaderDisplacementMethodAttributeName( "cycles:shader:displacement_method" );

ccl::DisplacementMethod displacementMethodFromString( const string &name )
{
	if( name == "bump" )
	{
		return ccl::DisplacementMethod::DISPLACE_BUMP;
	}
	else if( name == "both" )
	{
		return ccl::DisplacementMethod::DISPLACE_BOTH;
	}
	return ccl::DisplacementMethod::DISPLACE_TRUE;
}

IECore::InternedString g_shaderEmissionSamplingMethodAttributeName( "cycles:shader:emission_sampling_method" );
IECore::ConstStringDataPtr g_shaderEmissionSamplingMethodAttributeDefault = new StringData( "auto" );
IECore::InternedString g_shaderUseTransparentShadowAttributeName( "cycles:shader:use_transparent_shadow" );
IECore::InternedString g_shaderHeterogeneousVolumeAttributeName( "cycles:shader:heterogeneous_volume" );
IECore::InternedString g_shaderVolumeSamplingMethodAttributeName( "cycles:shader:volume_sampling_method" );
IECore::ConstStringDataPtr g_shaderVolumeSamplingMethodAttributeDefault = new StringData( "multiple_importance" );
IECore::InternedString g_shaderVolumeInterpolationMethodAttributeName( "cycles:shader:volume_interpolation_method" );
IECore::ConstStringDataPtr g_shaderVolumeInterpolationMethodAttributeDefault = new StringData( "linear" );
IECore::InternedString g_shaderVolumeStepRateAttributeName( "cycles:shader:volume_step_rate" );

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

		CyclesShader(
			const IECoreScene::ShaderNetwork *surfaceShader,
			const IECoreScene::ShaderNetwork *displacementShader,
			const IECoreScene::ShaderNetwork *volumeShader,
			ccl::Scene *scene,
			const std::string &name,
			const IECore::MurmurHash &h,
			const bool singleSided,
			ccl::DisplacementMethod displacementMethod,
			vector<const IECoreScene::ShaderNetwork *> &aovShaders
		)
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
			m_shader->set_displacement_method( displacementMethod );
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
		CyclesShaderPtr get(
			const IECoreScene::ShaderNetwork *surfaceShader,
			const IECoreScene::ShaderNetwork *displacementShader,
			const IECoreScene::ShaderNetwork *volumeShader,
			const IECore::CompoundObject *attributes,
			IECore::MurmurHash &h
		)
		{
			IECore::MurmurHash hSubst;
			IECore::MurmurHash hSubstDisp;
			IECore::MurmurHash hSubstVol;
			vector<IECore::MurmurHash> hSubstAovs;
			vector<const IECoreScene::ShaderNetwork*> aovShaders;

			// Surface hash

			const bool singleSided = !attributeValue<bool>( g_doubleSidedAttributeName, attributes, true );

			if( surfaceShader )
			{
				h.append( surfaceShader->Object::hash() );
				h.append( singleSided );
				if( attributes )
				{
					surfaceShader->hashSubstitutions( attributes, hSubst );
					h.append( hSubst );
				}
			}

			// Displacement hash

			ccl::DisplacementMethod displacementMethod = ccl::DisplacementMethod::DISPLACE_BUMP;
			if( displacementShader )
			{
				displacementShader->hash( h );
				if( attributes )
				{
					displacementShader->hashSubstitutions( attributes, hSubstDisp );
					h.append( hSubstDisp );
				}
				// Only look up the displacement shader attribute when we have a displacement shader,
				// so that differences in the attribute don't needlessly change our hash when they're
				// not relevant to the final shader.
				displacementMethod = displacementMethodFromString(
					attributeValue<string>( g_shaderDisplacementMethodAttributeName, attributes, "bump" )
				);
				h.append( displacementMethod );
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
					if( boost::starts_with( member.first.string(), "cycles:aov:" ) )
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
					if( surfaceShader && hSubst != IECore::MurmurHash() )
					{
						substitutedSurfaceShader = surfaceShader->copy();
						substitutedSurfaceShader->applySubstitutions( attributes );
						surfaceShader = substitutedSurfaceShader.get();
					}
					// Substitute displacement (if needed)
					IECoreScene::ShaderNetworkPtr substitutedDisplacementShader;
					if( displacementShader && hSubstDisp != IECore::MurmurHash() )
					{
						substitutedDisplacementShader = displacementShader->copy();
						substitutedDisplacementShader->applySubstitutions( attributes );
						displacementShader = substitutedDisplacementShader.get();
					}
					// Substitute volume (if needed)
					IECoreScene::ShaderNetworkPtr substitutedVolumeShader;
					if( volumeShader && hSubstVol != IECore::MurmurHash() )
					{
						substitutedVolumeShader = volumeShader->copy();
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

			/// \todo There are several problems here :
			///
			/// - We're clobbering the `tex_mapping.rotation` parameter, which is exposed to users
			///   but now has no effect for them. This also prevents us getting the orientation of USD
			///   DomeLights correct - see ShaderNetworkAlgo.
			/// - We're iterating through all N lights just to find the background light, and we're
			///   doing it even when the transform hasn't changed. Can't we just do this in `CyclesLight::transform()`?
			/// - The light shader was created via `ShaderCache::get()`, and could therefore be shared
			///   between several lights, so we're not at liberty to clobber the shader anyway.
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
IECore::InternedString g_displayColorAttributeName( "render:displayColor" );
IECore::InternedString g_lightAttributeName( "light" );
IECore::InternedString g_muteLightAttributeName( "light:mute" );
// Cycles Attributes
IECore::InternedString g_cclVisibilityAttributeName( "cycles:visibility" );
IECore::InternedString g_useHoldoutAttributeName( "cycles:use_holdout" );
IECore::InternedString g_isShadowCatcherAttributeName( "cycles:is_shadow_catcher" );
IECore::InternedString g_shadowTerminatorShadingOffsetAttributeName( "cycles:shadow_terminator_shading_offset" );
IECore::InternedString g_shadowTerminatorGeometryOffsetAttributeName( "cycles:shadow_terminator_geometry_offset" );
IECore::InternedString g_maxLevelAttributeName( "cycles:max_level" );
IECore::InternedString g_dicingRateAttributeName( "cycles:dicing_rate" );
// Cycles Light
IECore::InternedString g_cyclesLightAttributeName( "cycles:light" );
// Dupli
IECore::InternedString g_dupliGeneratedAttributeName( "cycles:dupli_generated" );
IECore::InternedString g_dupliUVAttributeName( "cycles:dupli_uv" );
// Shader Assignment
IECore::InternedString g_cyclesSurfaceShaderAttributeName( "cycles:surface" );
IECore::InternedString g_oslSurfaceShaderAttributeName( "osl:surface" );
IECore::InternedString g_oslShaderAttributeName( "osl:shader" );
IECore::InternedString g_cyclesVolumeShaderAttributeName( "cycles:volume" );
// Ray visibility
IECore::InternedString g_cameraVisibilityAttributeName( "cycles:visibility:camera" );
IECore::InternedString g_diffuseVisibilityAttributeName( "cycles:visibility:diffuse" );
IECore::InternedString g_glossyVisibilityAttributeName( "cycles:visibility:glossy" );
IECore::InternedString g_transmissionVisibilityAttributeName( "cycles:visibility:transmission" );
IECore::InternedString g_shadowVisibilityAttributeName( "cycles:visibility:shadow" );
IECore::InternedString g_scatterVisibilityAttributeName( "cycles:visibility:scatter" );
// Caustics
IECore::InternedString g_isCausticsCasterAttributeName( "cycles:is_caustics_caster" );
IECore::InternedString g_isCausticsReceiverAttributeName( "cycles:is_caustics_receiver" );

// Cryptomatte asset
IECore::InternedString g_cryptomatteAssetAttributeName( "cycles:asset_name" );

// Light-group
IECore::InternedString g_lightGroupAttributeName( "cycles:lightgroup" );

// Volume
IECore::InternedString g_volumeClippingAttributeName( "cycles:volume_clipping" );
IECore::InternedString g_volumeStepSizeAttributeName( "cycles:volume_step_size" );
IECore::InternedString g_volumeObjectSpaceAttributeName( "cycles:volume_object_space" );

const char *customAttributeName( const std::string &attributeName, bool &hasPrecedence )
{
	if( boost::starts_with( attributeName, "user:" ) )
	{
		hasPrecedence = false;
		return attributeName.c_str();
	}
	else if( boost::starts_with( attributeName, "render:" ) )
	{
		hasPrecedence = true;
		return attributeName.c_str() + 7;
	}

	// Not a custom attribute
	return nullptr;
}

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
				m_color( Color3f( 1.0f ) ),
				m_dupliGenerated( V3f( 0.0f ) ),
				m_dupliUV( V2f( 0.0f) ),
				m_volume( attributes ),
				m_shaderAttributes( attributes ),
				m_assetName( "" ),
				m_lightGroup( "" ),
				m_isCausticsCaster( false ),
				m_isCausticsReceiver( false ),
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
			m_color = attributeValue<Color3f>( g_displayColorAttributeName, attributes, m_color );
			m_dupliGenerated = attributeValue<V3f>( g_dupliGeneratedAttributeName, attributes, m_dupliGenerated );
			m_dupliUV = attributeValue<V2f>( g_dupliUVAttributeName, attributes, m_dupliUV );
			m_lightGroup = attributeValue<std::string>( g_lightGroupAttributeName, attributes, m_lightGroup );
			m_assetName = attributeValue<std::string>( g_cryptomatteAssetAttributeName, attributes, m_assetName );
			m_isCausticsCaster = attributeValue<bool>( g_isCausticsCasterAttributeName, attributes, m_isCausticsCaster );
			m_isCausticsReceiver = attributeValue<bool>( g_isCausticsReceiverAttributeName, attributes, m_isCausticsReceiver );

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

			m_muteLight = attributeValue<bool>( g_muteLightAttributeName, attributes, false );
			m_lightAttribute = attribute<IECoreScene::ShaderNetwork>( g_cyclesLightAttributeName, attributes );
			m_lightAttribute = m_lightAttribute ? m_lightAttribute : attribute<IECoreScene::ShaderNetwork>( g_lightAttributeName, attributes );
			if( m_lightAttribute )
			{
				ShaderNetworkPtr converted = m_lightAttribute->copy();
				ShaderNetworkAlgo::convertUSDShaders( converted.get() );
				m_lightAttribute = converted;

				ShaderNetworkPtr lightShader = ShaderNetworkAlgo::convertLightShader( m_lightAttribute.get() );
				IECore::MurmurHash h;
				m_lightShader = m_shaderCache->get( lightShader.get(), nullptr, nullptr, attributes, h );
			}

			// Custom attributes

			using CustomAttributesMap = boost::container::flat_map<InternedString, IECore::ConstDataPtr>;
			CustomAttributesMap customMap;

			for( IECore::CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; ++it )
			{
				bool hasPrecedence = false;
				if( const char *name = customAttributeName( it->first.string(), hasPrecedence ) )
				{
					if( const IECore::Data *data = IECore::runTimeCast<const IECore::Data>( it->second.get() ) )
					{
						auto inserted = customMap.insert( CustomAttributesMap::value_type( name, nullptr ) );
						if( hasPrecedence || inserted.second )
						{
							inserted.first->second = data;
						}
					}
				}
			}

			for( const auto &attr : customMap )
			{
				ccl::ParamValue paramValue = SocketAlgo::setParamValue( attr.first, attr.second.get() );
				if( paramValue.data() )
				{
					m_custom.push_back( paramValue );
				}
				else
				{
					msg(
						Msg::Warning, "IECoreCycles::Renderer",
						fmt::format(
							"Custom attribute \"{}\" has unsupported type \"{}\".",
							attr.first.string(), attr.second->typeName()
						)
					);
				}
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
			object->set_is_caustics_caster( m_isCausticsCaster );
			object->set_is_caustics_receiver( m_isCausticsReceiver );

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
				}

				if( m_shader->shader() )
				{
					ShaderAssignPair pair = ShaderAssignPair( object->get_geometry(), ccl::array<ccl::Node*>() );
					pair.second.push_back_slow( m_shader->shader() );
					m_shaderCache->addShaderAssignment( pair );
				}
			}

			if( !m_volume.apply( object ) )
				return false;

			object->set_lightgroup( ccl::ustring( m_lightGroup.c_str() ) );

			// Custom attributes.
			object->attributes = m_custom;

			return true;
		}

		bool applyLight( ccl::Light *light, const CyclesAttributes *previousAttributes ) const
		{
			if( m_lightAttribute )
			{
				ShaderNetworkAlgo::convertLight( m_lightAttribute.get(), light );
				ShaderAssignPair pair = ShaderAssignPair( light, ccl::array<ccl::Node*>() );
				pair.second.push_back_slow( m_lightShader->shader() );
				m_shaderCache->addShaderAssignment( pair );

				light->set_is_enabled( !m_muteLight );
			}
			else
			{
				// No `cycles:light` shader assignment. Most likely a light
				// intended for another renderer, so we turn off the Cycles
				// light.
				light->set_is_enabled( false );
			}

			if( !light->get_is_enabled() )
			{
				// Alas, `ccl::LightManager::test_enabled_lights()` will
				// re-enable the light unless we also set its strength to zero.
				light->set_strength( ccl::zero_float3() );
			}

			return true;
		}

		// Generates a signature for the work done by applyGeometry.
		/// \todo This description is inaccurate. There used to be a method called `applyGeometry()`,
		/// but it was removed. We didn't remove `hashGeometry()` at the same time because it hashes
		/// things that were never used by `applyGeometry()` in the first place. Figure out why there
		/// was this mismatch, and if this function is really needed or not.
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

		void nodesCreated( NodesCreated &nodes )
		{
			m_shader->nodesCreated( nodes );
		}

	private :

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

		/// \todo Implementing this functionality here prevents us from properly
		/// encapsulating the work of `ShaderCache::get()`, forcing us to pass an
		/// extra hash for the things that we'll do to the shader _after_ we get
		/// it from the cache. Instead, `ShaderCache` should apply these attributes
		/// itself internally, and afterwards there should only be const access to
		/// the `ccl::Shader`.
		struct ShaderAttributes
		{
			ShaderAttributes( const IECore::CompoundObject *attributes )
			{
				emissionSamplingMethod = attribute<StringData>( g_shaderEmissionSamplingMethodAttributeName, attributes, g_shaderEmissionSamplingMethodAttributeDefault.get() );
				useTransparentShadow = optionalAttribute<bool>( g_shaderUseTransparentShadowAttributeName, attributes );
				heterogeneousVolume = optionalAttribute<bool>( g_shaderHeterogeneousVolumeAttributeName, attributes );
				volumeSamplingMethod = attribute<StringData>( g_shaderVolumeSamplingMethodAttributeName, attributes, g_shaderVolumeSamplingMethodAttributeDefault.get() );
				volumeInterpolationMethod = attribute<StringData>( g_shaderVolumeInterpolationMethodAttributeName, attributes, g_shaderVolumeInterpolationMethodAttributeDefault.get() );
				volumeStepRate = optionalAttribute<float>( g_shaderVolumeStepRateAttributeName, attributes );
			}

			ConstDataPtr emissionSamplingMethod;
			boost::optional<bool> useTransparentShadow;
			boost::optional<bool> heterogeneousVolume;
			ConstDataPtr volumeSamplingMethod;
			ConstDataPtr volumeInterpolationMethod;
			boost::optional<float> volumeStepRate;

			void hash( IECore::MurmurHash &h, const IECore::CompoundObject *attributes ) const
			{
				emissionSamplingMethod->hash( h );

				// Volume-related attributes hash
				auto it = attributes->members().find( g_cyclesVolumeShaderAttributeName );
				if( it != attributes->members().end() )
				{
					if( heterogeneousVolume && !heterogeneousVolume.get() )
						h.append( "homogeneous_volume" );
					volumeSamplingMethod->hash( h );
					volumeInterpolationMethod->hash( h );
					if( volumeStepRate && volumeStepRate.get() != 1.0f )
						h.append( volumeStepRate.get() );
				}
			}

			bool apply( ccl::Shader *shader ) const
			{
				SocketAlgo::setSocket( shader, shader->get_emission_sampling_method_socket(), emissionSamplingMethod.get() );
				shader->set_use_transparent_shadow(useTransparentShadow ? useTransparentShadow.get() : true );
				shader->set_heterogeneous_volume( heterogeneousVolume ? heterogeneousVolume.get() : true );
				SocketAlgo::setSocket( shader, shader->get_volume_sampling_method_socket(), volumeSamplingMethod.get() );
				SocketAlgo::setSocket( shader, shader->get_volume_interpolation_method_socket(), volumeInterpolationMethod.get() );
				shader->set_volume_step_rate( volumeStepRate ? volumeStepRate.get() : 1.0f );

				return true;
			}
		};

		IECoreScene::ConstShaderNetworkPtr m_lightAttribute;
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
		Volume m_volume;
		ShaderAttributes m_shaderAttributes;
		InternedString m_assetName;
		InternedString m_lightGroup;
		bool m_isCausticsCaster;
		bool m_isCausticsReceiver;
		// Need to assign shaders in a deferred manner
		ShaderCache *m_shaderCache;
		bool m_muteLight;

		using CustomAttributes = ccl::vector<ccl::ParamValue>;
		CustomAttributes m_custom;

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

	private :

		// Constructors are private as they are only intended for use in
		// `InstanceCache::get()`. See comment in `nodesCreated()`.
		friend class InstanceCache;

		Instance( const SharedCObjectPtr &object, const SharedCGeometryPtr &geometry, const bool prototype )
			:	m_object( object ), m_geometry( geometry ), m_prototype( prototype )
		{
		}

		SharedCObjectPtr m_object;
		SharedCGeometryPtr m_geometry;
		bool m_prototype;

};

class InstanceCache : public IECore::RefCounted
{

	public :

		InstanceCache( ccl::Scene *scene )
			: m_scene( scene )
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
				SharedCGeometryPtr geometry = convert( object, cyclesAttributes, nodeName );
				m_uniqueGeometry.push_back( geometry );
				return makeInstance( geometry, nodeName, /* prototype = */ true );
			}

			bool isPrototype = false;

			IECore::MurmurHash h = object->hash();
			cyclesAttributes->hashGeometry( object, h );

			SharedCGeometryPtr cgeo;
			Geometry::const_accessor readAccessor;
			if( m_geometry.find( readAccessor, h ) )
			{
				cgeo = readAccessor->second;
				readAccessor.release();
			}
			else
			{
				Geometry::accessor writeAccessor;
				if( m_geometry.insert( writeAccessor, h ) )
				{
					isPrototype = true;
					writeAccessor->second = convert( object, cyclesAttributes, nodeName );
				}
				cgeo = writeAccessor->second;
			}

			return makeInstance( cgeo, nodeName, isPrototype );
		}

		// Can be called concurrently with other get() calls.
		Instance get(
			const std::vector<const IECore::Object *> &samples,
			const std::vector<float> &times,
			const int frameIdx,
			const IECoreScenePreview::Renderer::AttributesInterface *attributes,
			const std::string &nodeName
		)
		{
			const CyclesAttributes *cyclesAttributes = static_cast<const CyclesAttributes *>( attributes );

			if( !cyclesAttributes->canInstanceGeometry( samples.front() ) )
			{
				SharedCGeometryPtr geometry = convert( samples, times, frameIdx, cyclesAttributes, nodeName );
				m_uniqueGeometry.push_back( geometry );
				return makeInstance( geometry, nodeName, true );
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

			SharedCGeometryPtr cgeo;
			Geometry::const_accessor readAccessor;
			if( m_geometry.find( readAccessor, h ) )
			{
				cgeo = readAccessor->second;
				readAccessor.release();
			}
			else
			{
				Geometry::accessor writeAccessor;
				if( m_geometry.insert( writeAccessor, h ) )
				{
					isPrototype = true;
					writeAccessor->second = convert( samples, times, frameIdx, cyclesAttributes, nodeName );
				}
				cgeo = writeAccessor->second;
			}

			return makeInstance( cgeo, nodeName, isPrototype );
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

		SharedCGeometryPtr convert( const IECore::Object *object, const CyclesAttributes *attributes, const std::string &nodeName ) const
		{
			ccl::Geometry *geometry = GeometryAlgo::convert( object, nodeName, m_scene );
			if( geometry )
			{
				geometry->set_owner( m_scene );
			}
			return SharedCGeometryPtr( geometry, nullNodeDeleter );
		}

		SharedCGeometryPtr convert(
			const std::vector<const IECore::Object *> &samples,
			const std::vector<float> &times,
			const int frame,
			const CyclesAttributes *attributes,
			const std::string &nodeName
		) const
		{
			ccl::Geometry *geometry = GeometryAlgo::convert( samples, times, frame, nodeName, m_scene );
			if( geometry )
			{
				geometry->set_owner( m_scene );
			}
			return SharedCGeometryPtr( geometry, nullNodeDeleter );
		}

		Instance makeInstance( const SharedCGeometryPtr &geometry, const std::string &name, bool prototype )
		{
			SharedCObjectPtr object;
			if( geometry )
			{
				object = SharedCObjectPtr( new ccl::Object(), nullNodeDeleter );
				object->name = ccl::ustring( name.c_str() );
				object->set_random_id( std::hash<string>()( name ) );
				object->set_owner( m_scene );
				object->set_geometry( geometry.get() );
				m_objects.push_back( object );
			}

			return Instance( object, geometry, prototype );
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
			light->set_owner( m_scene );
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
				IECore::msg(
					IECore::Msg::Error, "IECoreCycles::Renderer",
					fmt::format( "Transform step size on \"{}\" must match deformation step size.", object->name.c_str() )
				);
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
				if( object )
				{
					object->tag_update( m_session->scene );
				}
				return true;
			}

			return false;
		}

		void assignID( uint32_t id ) override
		{
			if( m_instance.object() )
			{
				m_instance.object()->set_pass_id( id );
			}
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
			// Attributes don't affect the camera, so the edit always "succeeds".
			return true;
		}

		void assignID( uint32_t id ) override
		{
			/// \todo Implement me
		}

	private :

		SharedCCameraPtr m_camera;

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

ccl::DeviceInfo firstCPUDevice()
{
	for( const auto &device : ccl::Device::available_devices() )
	{
		if( device.type == ccl::DEVICE_CPU )
		{
			return device;
		}
	}
	assert( false );
	return ccl::DeviceInfo();
}

ccl::DeviceInfo matchingDevices( const std::string &pattern, int threads, bool background )
{
	ccl::vector<ccl::DeviceInfo> devices;
	std::unordered_map<ccl::DeviceType, int> typeIndices;
	for( const auto &device : ccl::Device::available_devices() )
	{
		const string typeString = ccl::Device::string_from_type( device.type );
		const int typeIndex = typeIndices[device.type]++;
		const string name = fmt::format( "{}:{:02}", typeString, typeIndex );
		if(
			// e.g. "CPU" matches the first CPU device.
			( typeIndex == 0 && StringAlgo::matchMultiple( typeString, pattern ) ) ||
			// e.g. "CUDA:*" matches all CUDA devices, or `OPTIX:00` matches the first Optix device.
			StringAlgo::matchMultiple( name, pattern )
		)
		{
			devices.push_back( device );
		}
	}

	if( devices.empty() )
	{
		IECore::msg( IECore::Msg::Warning, "CyclesRenderer", fmt::format( "No devices matching \"{}\" found, reverting to CPU.", pattern ) );
		devices.push_back( firstCPUDevice() );
	}

	// Note : if there's only one device, `get_multi_device()` just
	// returns it directly, rather than wrapping it.
	return ccl::Device::get_multi_device( devices, threads, background );
}

IECore::CompoundDataPtr sessionParamsAsData( const ccl::SessionParams params )
{
	IECore::CompoundDataPtr result = new IECore::CompoundData;
	result->writable()["device"] = new StringData( params.device.id );
	result->writable()["headless"] = new BoolData( params.headless );
	result->writable()["background"] = new BoolData( params.background );
	result->writable()["experimental"] = new BoolData( params.experimental );
	result->writable()["samples"] = new BoolData( params.samples );
	result->writable()["threads"] = new IntData( params.threads );
	return result;
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

template<typename T>
T optionValue( const IECore::InternedString &name, const IECore::Object *value, const T &defaultValue )
{
	if( !value )
	{
		return defaultValue;
	}
	using DataType = IECore::TypedData<T>;
	const DataType *data = reportedCast<const DataType>( value, "option", name );
	return data ? data->readable() : defaultValue;
}

// Core
IECore::InternedString g_frameOptionName( "frame" );
IECore::InternedString g_cameraOptionName( "camera" );
IECore::InternedString g_sampleMotionOptionName( "sampleMotion" );
IECore::InternedString g_deviceOptionName( "cycles:device" );
IECore::InternedString g_shadingsystemOptionName( "cycles:shadingsystem" );
IECore::InternedString g_squareSamplesOptionName( "cycles:square_samples" );
// Logging
IECore::InternedString g_logLevelOptionName( "cycles:log_level" );
IECore::InternedString g_progressLevelOptionName( "cycles:progress_level" );
// Session
IECore::InternedString g_experimentalOptionName( "cycles:session:experimental" );
IECore::InternedString g_samplesOptionName( "cycles:session:samples" );
IECore::InternedString g_pixelSizeOptionName( "cycles:session:pixel_size" );
IECore::InternedString g_threadsOptionName( "cycles:session:threads" );
IECore::InternedString g_timeLimitOptionName( "cycles:session:time_limit" );
IECore::InternedString g_useProfilingOptionName( "cycles:session:use_profiling" );
IECore::InternedString g_useAutoTileOptionName( "cycles:session:use_auto_tile" );
IECore::InternedString g_tileSizeOptionName( "cycles:session:tile_size" );
// Scene
IECore::InternedString g_bvhTypeOptionName( "cycles:scene:bvh_type" );
IECore::InternedString g_bvhLayoutOptionName( "cycles:scene:bvh_layout" );
IECore::InternedString g_useBvhSpatialSplitOptionName( "cycles:scene:use_bvh_spatial_split" );
IECore::InternedString g_useBvhUnalignedNodesOptionName( "cycles:scene:use_bvh_unaligned_nodes" );
IECore::InternedString g_numBvhTimeStepsOptionName( "cycles:scene:num_bvh_time_steps" );
IECore::InternedString g_hairSubdivisionsOptionName( "cycles:scene:hair_subdivisions" );
IECore::InternedString g_hairShapeOptionName( "cycles:scene:hair_shape" );
IECore::InternedString g_textureLimitOptionName( "cycles:scene:texture_limit" );
// Background shader
IECore::InternedString g_backgroundShaderOptionName( "cycles:background:shader" );
//
IECore::InternedString g_seedOptionName( "cycles:integrator:seed" );

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
IECore::InternedString g_dicingCameraOptionName( "cycles:dicing_camera" );

// Cryptomatte
IECore::InternedString g_cryptomatteDepthOptionName( "cycles:film:cryptomatte_depth");

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
				m_renderType( renderType ),
				m_frame( 1 ),
				m_renderState( RENDERSTATE_READY ),
				m_outputsChanged( true ),
				m_cryptomatteDepth( 0 ),
				m_messageHandler( messageHandler )
		{
			// Session Defaults
			m_sessionParams.device = firstCPUDevice();
			m_sessionParams.shadingsystem = ccl::SHADINGSYSTEM_OSL;
			m_sessionParams.use_resolution_divider = false;
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
				m_sessionParams.use_auto_tile = false;
				m_sceneParams.bvh_type = ccl::BVH_TYPE_DYNAMIC;
			}

			m_sessionParamsDefault = m_sessionParams;
			m_sceneParamsDefault = m_sceneParams;

			init();

			m_scene->background->set_transparent( true );

			m_cameraCache = new CameraCache();
			m_lightCache = new LightCache( m_scene );
			m_shaderCache = new ShaderCache( m_scene );
			m_instanceCache = new InstanceCache( m_scene );
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

			// Error about options that cannot be set while interactive rendering.
			if( m_renderState == RENDERSTATE_RENDERING )
			{
				if( name == g_deviceOptionName ||
					name == g_shadingsystemOptionName ||
					boost::starts_with( name.string(), "cycles:session:" ) ||
					boost::starts_with( name.string(), "cycles:scene:" )
				)
				{
					IECore::msg( IECore::Msg::Error, "CyclesRenderer::option", fmt::format( "\"{}\" requires a manual render restart.", name ) );
				}
			}

			if( name == g_frameOptionName )
			{
				m_frame = optionValue<int>( name, value, 1 );
				return;
			}
			else if( name == g_cameraOptionName )
			{
				m_camera = optionValue<string>( name, value, "" );
				return;
			}
			else if( name == g_dicingCameraOptionName )
			{
				m_dicingCamera = optionValue<string>( name, value, "" );
				return;
			}
			else if( name == g_sampleMotionOptionName )
			{
				m_scene->integrator->set_motion_blur( optionValue<bool>( name, value, true ) );
				return;
			}
			else if( name == g_deviceOptionName )
			{
				m_sessionParams.device = matchingDevices( optionValue<string>( name, value, "CPU" ), /* threads = */ 0, /* background = */ true );
				return;
			}
			else if( name == g_threadsOptionName )
			{
				const int threads = optionValue<int>( name, value, 0 );
				m_sessionParams.threads = threads > 0 ? threads : std::max( (int)std::thread::hardware_concurrency() + threads, 1 );
				return;
			}
			else if( name == g_shadingsystemOptionName )
			{
				m_sessionParams.shadingsystem = m_sceneParams.shadingsystem = nameToShadingSystemEnum(
					optionValue<string>( name, value, "OSL" )
				);
				return;
			}
			else if( name == g_logLevelOptionName )
			{
				ccl::util_logging_verbosity_set( optionValue<int>( name, value, 0 ) );
				return;
			}
			else if( name == g_seedOptionName )
			{
				m_seed = value ? optional<int>( optionValue<int>( name, value, 0 ) ) : std::nullopt;
				return;
			}
			else if( boost::starts_with( name.string(), "cycles:session:" ) )
			{
				OPTION(bool,  m_sessionParams, g_experimentalOptionName,   experimental);
				OPTION(int,   m_sessionParams, g_samplesOptionName,      samples);
				OPTION(int,   m_sessionParams, g_pixelSizeOptionName,    pixel_size);
				OPTION(float, m_sessionParams, g_timeLimitOptionName,    time_limit);
				OPTION(bool,  m_sessionParams, g_useProfilingOptionName, use_profiling);
				OPTION(bool,  m_sessionParams, g_useAutoTileOptionName,  use_auto_tile);
				OPTION(int,   m_sessionParams, g_tileSizeOptionName,     tile_size);
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", fmt::format( "Unknown option \"{}\".", name.string() ) );
				return;
			}
			else if( name == g_bvhLayoutOptionName )
			{
				m_sceneParams.bvh_layout = nameToBvhLayoutEnum( optionValue<string>( name, value, "auto" ) );
				return;
			}
			else if( name == g_hairShapeOptionName )
			{
				m_sceneParams.hair_shape = nameToCurveShapeTypeEnum( optionValue<string>( name, value, "thick" ) );
				return;
			}
			else if( boost::starts_with( name.string(), "cycles:scene:" ) )
			{
				OPTION(bool, m_sceneParams, g_useBvhSpatialSplitOptionName,   use_bvh_spatial_split);
				OPTION(bool, m_sceneParams, g_useBvhUnalignedNodesOptionName, use_bvh_unaligned_nodes);
				OPTION(int,  m_sceneParams, g_numBvhTimeStepsOptionName,      num_bvh_time_steps);
				OPTION(int,  m_sceneParams, g_hairSubdivisionsOptionName,     hair_subdivisions);
				OPTION(int,  m_sceneParams, g_textureLimitOptionName,         texture_limit);
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", fmt::format( "Unknown option \"{}\".", name.string() ) );
				return;
			}
			else if( name == g_backgroundShaderOptionName )
			{
				/// \todo Why is this assignment here? Is it bogus or do we need to destroy the old shader before getting the new one?
				m_backgroundShader = nullptr;
				if( const IECoreScene::ShaderNetwork *d = value ? reportedCast<const IECoreScene::ShaderNetwork>( value, "option", name ) : nullptr )
				{
					m_backgroundShader = m_shaderCache->get( d );
				}
				else
				{
					m_backgroundShader = nullptr;
				}
				return;
			}
			else if( boost::starts_with( name.string(), "cycles:background:visibility:" ) )
			{
				const int vis = optionValue<int>( name, value, 1 );
				auto ray = nameToRayType( name.string().c_str() + 29 );
				const uint32_t prevVis = m_scene->background->get_visibility();
				m_scene->background->set_visibility( vis ? prevVis | ray : prevVis & ~ray );
				return;
			}
			else if( boost::starts_with( name.string(), "cycles:background:" ) )
			{
				SocketAlgo::setSocket(
					m_scene->background, name.string().c_str() + 18,
					value ? reportedCast<const Data>( value, "option", name ) : nullptr
				);
				return;
			}
			else if( name == g_cryptomatteDepthOptionName )
			{
				m_cryptomatteDepth = optionValue<int>( name, value, 0 );
				m_outputsChanged = true;
				return;
			}
			else if( boost::starts_with( name.string(), "cycles:film:" ) )
			{
				SocketAlgo::setSocket(
					m_scene->film, name.string().c_str() + 12,
					value ? reportedCast<const Data>( value, "option", name ) : nullptr
				);
				return;
			}
			else if( boost::starts_with( name.string(), "cycles:integrator:" ) )
			{
				SocketAlgo::setSocket(
					m_scene->integrator, name.string().c_str() + 18,
					value ? reportedCast<const Data>( value, "option", name ) : nullptr
				);
				return;
			}
			else if( boost::starts_with( name.string(), "cycles:" ) )
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", fmt::format( "Unknown option \"{}\".", name.string() ) );
				return;
			}
			else if( boost::starts_with( name.string(), "user:" ) )
			{
				IECore::msg( Msg::Warning, "CyclesRenderer::option", fmt::format( "User option \"{}\" not supported", name.string() ) );
				return;
			}
			else if( boost::contains( name.c_str(), ":" ) )
			{
				// Ignore options prefixed for some other renderer.
				return;
			}
			else
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", fmt::format( "Unknown option \"{}\".", name.string() ) );
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
					m_outputs[name] = new CyclesOutput( name, output );
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
			if( !instance.object() )
			{
				return nullptr;
			}

			ObjectInterfacePtr result = new CyclesObject( m_session, instance, m_frame );
			result->attributes( attributes );

			instance.objectsCreated( m_objectsCreated );
			// These will only accumulate if it's the prototype
			instance.geometryCreated( m_geometryCreated );

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
			if( !instance.object() )
			{
				return nullptr;
			}

			ObjectInterfacePtr result = new CyclesObject( m_session, instance, m_frame );
			result->attributes( attributes );

			instance.objectsCreated( m_objectsCreated );
			// These will only accumulate if it's the prototype
			instance.geometryCreated( m_geometryCreated );

			return result;
		}

		void render() override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );

			{
				std::scoped_lock sceneLock( m_scene->mutex );
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
			}

			if( m_renderState == RENDERSTATE_RENDERING )
			{
				m_session->set_pause( false );
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
				m_session->set_pause( true );
			}
		}

		IECore::DataPtr command( const IECore::InternedString name, const IECore::CompoundDataMap &parameters ) override
		{
			if( name == "cycles:queryIntegrator" )
			{
				return SocketAlgo::getSockets( m_scene->integrator );
			}
			else if( name == "cycles:queryFilm" )
			{
				return SocketAlgo::getSockets( m_scene->film );
			}
			else if( name == "cycles:querySession" )
			{
				return sessionParamsAsData( m_session->params );
			}
			else if( boost::starts_with( name.string(), "cycles:" ) || name.string().find( ":" ) == string::npos )
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::command", fmt::format( "Unknown command \"{}\"", name.c_str() ) );
			}

			return nullptr;
		}

	private :

		void init()
		{
			if( m_sessionParams.device.multi_devices.size() )
			{
				// When we first made this in `option()`, we didn't have the
				// final values for `threads` and `background`. Apply those now.
				m_sessionParams.device = ccl::Device::get_multi_device( m_sessionParams.device.multi_devices, m_sessionParams.threads, m_sessionParams.background );
			}

			if( m_sessionParams.shadingsystem == ccl::SHADINGSYSTEM_OSL && !m_sessionParams.device.has_osl )
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer", "Device doesn't support OSL, reverting to CPU." );
				m_sessionParams.device = firstCPUDevice();
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
		}

		void clearUnused()
		{
			m_cameraCache->clearUnused();
			m_instanceCache->clearUnused();
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
			}

			// Add every shader each time, less issues
			m_shaderCache->nodesCreated( m_shadersCreated );

			m_lightCache->update( m_scene, m_lightsCreated );
			m_instanceCache->update( m_scene, m_objectsCreated, m_geometryCreated );
			m_shaderCache->update( m_scene, m_shadersCreated );
		}

		void updateOptions()
		{
			ccl::Integrator *integrator = m_scene->integrator;
			ccl::Background *background = m_scene->background;

			integrator->set_seed( m_seed.value_or( m_frame ) );

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
				background->set_shader( m_scene->default_background );
			}

			if( integrator->is_modified() )
			{
				integrator->tag_update( m_scene, ccl::Integrator::UPDATE_ALL );
			}

			if( background->is_modified() )
			{
				background->tag_update( m_scene );
			}

			if( film->is_modified() )
			{
				//film->tag_update( m_scene );
				integrator->tag_update( m_scene, ccl::Integrator::UPDATE_ALL );
			}

			// If anything changes in scene or session, we reset.
			if( m_scene->params.modified( m_sceneParams ) ||
				m_session->params.modified( m_sessionParams )
			)
			{
				// Flag it true here so that we never mutex unlock a different scene pointer due to the reset
				if( m_renderState != RENDERSTATE_RENDERING )
				{
					reset();
				}
			}
		}

		void updateOutputs()
		{
			ccl::Camera *camera = m_scene->camera;
			int width = camera->get_full_width();
			int height = camera->get_full_height();

			ccl::BufferParams updatedBufferParams = m_bufferParams;
			updatedBufferParams.full_width = width;
			updatedBufferParams.full_height = height;
			updatedBufferParams.full_x = (int)(camera->get_border_left() * (float)width);
			updatedBufferParams.full_y = (int)(camera->get_border_bottom() * (float)height);
			updatedBufferParams.width =  (int)(camera->get_border_right() * (float)width) - updatedBufferParams.full_x;
			updatedBufferParams.height = (int)(camera->get_border_top() * (float)height) - updatedBufferParams.full_y;

			if( m_bufferParams.modified( updatedBufferParams ) )
			{
				// Set `m_outputsChanged` so we call `m_session->reset()` below
				// with the new buffer params, and so we update the display driver
				// with the new resolution.
				m_outputsChanged = true;
				m_bufferParams = updatedBufferParams;
			}

			if( !m_outputsChanged )
				return;

			Box2i displayWindow(
				V2i( 0, 0 ),
				V2i( width - 1, height - 1 )
			);
			Box2i dataWindow(
				V2i(
					(int)(camera->get_border_left()   * (float)width ),
					(int)(camera->get_border_bottom() * (float)height )
				),
				V2i(
					(int)(camera->get_border_right()  * (float)width ) - 1,
					(int)(camera->get_border_top()    * (float)height - 1 )
				)
			);

			ccl::set<ccl::Pass *> clearPasses( m_scene->passes.begin(), m_scene->passes.end() );
			m_scene->delete_nodes( clearPasses );

			CompoundDataPtr paramData = new CompoundData();

			paramData->writable()["default"] = new StringData( "rgba" );

			ccl::CryptomatteType crypto = ccl::CRYPT_NONE;

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
			if( crypto == ccl::CRYPT_NONE )
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

			paramData->writable()["layers"] = layersData;

			// When we reset the session, it cancels the internal PathTrace and
			// waits for it to finish. We need to do this _before_ calling
			// `set_output_driver()`, because otherwise the rendering threads
			// may try to send data to an output driver that was just destroyed
			// on the main thread.
			/// \todo `Renderer::pause()` really shouldn't return until after
			/// the PathTrace has been cancelled, so we shouldn't need to worry
			/// about that here.
			m_session->reset( m_sessionParams, m_bufferParams );

			film->set_cryptomatte_passes( crypto );
			film->set_use_approximate_shadow_catcher( !hasShadowCatcher );
			m_scene->integrator->set_use_denoise( hasDenoise );
			if( m_renderType == Interactive )
				m_session->set_output_driver( ccl::make_unique<IEDisplayOutputDriver>( displayWindow, dataWindow, paramData ) );
			else
				m_session->set_output_driver( ccl::make_unique<OIIOOutputDriver>( displayWindow, dataWindow, paramData ) );

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

			const ccl::Integrator integratorCopy = *m_scene->integrator;
			const ccl::Background backgroundCopy = *m_scene->background;
			const ccl::Film filmCopy = *m_scene->film;

			init();

			// Re-apply the settings for these.
			for( const ccl::SocketType &socketType : m_scene->integrator->type->inputs )
			{
				m_scene->integrator->copy_value(socketType, integratorCopy, *integratorCopy.type->find_input( socketType.name ) );
			}
			for( const ccl::SocketType &socketType : m_scene->background->type->inputs )
			{
				m_scene->background->copy_value(socketType, backgroundCopy, *backgroundCopy.type->find_input( socketType.name ) );
			}
			for( const ccl::SocketType &socketType : m_scene->film->type->inputs )
			{
				m_scene->film->copy_value(socketType, filmCopy, *filmCopy.type->find_input( socketType.name ) );
			}

			m_scene->background->set_shader( m_scene->default_background );

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
							fmt::format( "Camera \"{}\" does not exist", m_camera )
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
							fmt::format( "Dicing camera \"{}\" does not exist", m_dicingCamera )
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

		void resetCaches()
		{
			m_cameraCache.reset();
			m_instanceCache.reset();
			m_lightCache.reset();
			m_shaderCache.reset();
			m_attributesCache.reset();
		}

		// Cycles core objects.
		ccl::Session *m_session;
		ccl::Scene *m_scene;
		ccl::SessionParams m_sessionParams;
		ccl::SceneParams m_sceneParams;
		ccl::BufferParams m_bufferParams;

		// Background shader
		CyclesShaderPtr m_backgroundShader;

		// Defaults
		ccl::Camera m_cameraDefault;
		ccl::SessionParams m_sessionParamsDefault;
		ccl::SceneParams m_sceneParamsDefault;

		// IECoreScene::Renderer
		RenderType m_renderType;
		int m_frame;
		string m_camera;
		RenderState m_renderState;
		bool m_outputsChanged;
		int m_cryptomatteDepth;
		std::optional<int> m_seed;

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
		AttributesCachePtr m_attributesCache;

		// Nodes created to update to Cycles
		/// \todo I don't see why these need to be state on the Renderer.
		/// I think they could either be private data within `InstanceCache`
		/// etc, or we could just stop deferring the addition of objects to
		/// the `ccl::Scene`.
		NodesCreated m_objectsCreated;
		NodesCreated m_lightsCreated;
		NodesCreated m_geometryCreated;
		NodesCreated m_shadersCreated;

		// Outputs
		OutputMap m_outputs;

		// Cameras (Cycles can only know of one camera at a time)
		typedef tbb::concurrent_unordered_map<std::string, IECoreScene::ConstCameraPtr> CameraMap;
		CameraMap m_cameras;
		string m_dicingCamera;

		// Registration with factory
		static Renderer::TypeDescription<CyclesRenderer> g_typeDescription;

};

IECoreScenePreview::Renderer::TypeDescription<CyclesRenderer> CyclesRenderer::g_typeDescription( "Cycles" );

} // namespace
