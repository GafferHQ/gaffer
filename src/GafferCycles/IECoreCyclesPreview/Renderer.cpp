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
#include "SceneAlgo.h"

#include "IECoreScene/Camera.h"
#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/Shader.h"

#include "IECore/Interpolator.h"
#include "IECore/MessageHandler.h"
#include "IECore/ObjectVector.h"
#include "IECore/SearchPath.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/StringAlgo.h"
#include "IECore/VectorTypedData.h"

#include "Imath/ImathMatrixAlgo.h"

#include "boost/algorithm/string.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/container/flat_map.hpp"

#include "tbb/concurrent_unordered_map.h"
#include "tbb/concurrent_hash_map.h"
#include "tbb/concurrent_vector.h"

#include "fmt/format.h"

#include <tuple>
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
#include "util/log.h"
#include "util/murmurhash.h"
#include "util/path.h"
#include "util/time.h"
#include "util/types.h"
#include "util/vector.h"
#include "util/version.h"
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
std::optional<T> optionalAttribute( const IECore::InternedString &name, const IECore::CompoundObject *attributes )
{
	using DataType = IECore::TypedData<T>;
	const DataType *data = attribute<DataType>( name, attributes );
	return data ? data->readable() : std::optional<T>();
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

} // namespace

//////////////////////////////////////////////////////////////////////////
// NodeDeleter
//////////////////////////////////////////////////////////////////////////

namespace
{

// `ccl::Scene::delete_node()` is the official way of removing a node from the
// scene and deleting it. It is specialised for each node type so that it also
// tags the appropriate object manager for update. In an ideal world we would
// just call it whenever we need to delete a node.
//
// But a single call to `delete_node()` is `O(n)` in the number of nodes in the
// scene, making deletion of all nodes `O(n^2)`, which is unacceptable for large
// scenes. The NodeDeleter class allows us to batch up deletions and use a single
// call to the more performant `ccl::Scene::delete_nodes()` method to delete
// multiple nodes at once.
struct NodeDeleter
{

	NodeDeleter( ccl::Scene *scene )
		:	m_scene( scene )
	{
	}

	// Deleter for use with `std::shared_ptr` and `std::unique_ptr`.
	template<typename T>
	struct Deleter
	{

		Deleter( NodeDeleter *nodeDeleter = nullptr )
			:	m_nodeDeleter( nodeDeleter )
		{
		}

		void operator()( T *node ) const
		{
			if( m_nodeDeleter )
			{
				m_nodeDeleter->scheduleDeletion( node );
			}
		}

		private :

			NodeDeleter *m_nodeDeleter;

	};

	using LightDeleter = Deleter<ccl::Light>;
	using GeometryDeleter = Deleter<ccl::Geometry>;
	using ObjectDeleter = Deleter<ccl::Object>;

	void doPendingDeletions()
	{
		std::lock_guard lock( m_mutex );
		std::lock_guard sceneLock( m_scene->mutex );

		if( m_pendingLightDeletions.size() )
		{
			m_scene->delete_nodes( m_pendingLightDeletions );
			m_pendingLightDeletions.clear();
		}
		if( m_pendingObjectDeletions.size() )
		{
			m_scene->delete_nodes( m_pendingObjectDeletions );
			m_pendingObjectDeletions.clear();
		}
		if( m_pendingGeometryDeletions.size() )
		{
			m_scene->delete_nodes( m_pendingGeometryDeletions );
			m_pendingGeometryDeletions.clear();
		}
	}

	private :

		void scheduleDeletion( ccl::Light *light )
		{
			std::lock_guard lock( m_mutex );
			m_pendingLightDeletions.insert( light );
		}

		void scheduleDeletion( ccl::Object *object )
		{
			std::lock_guard lock( m_mutex );
			m_pendingObjectDeletions.insert( object );
		}

		void scheduleDeletion( ccl::Geometry *geometry )
		{
			std::lock_guard lock( m_mutex );
			m_pendingGeometryDeletions.insert( geometry );
		}

		ccl::Scene *m_scene;

		std::mutex m_mutex;
		std::set<ccl::Light *> m_pendingLightDeletions;
		std::set<ccl::Object *> m_pendingObjectDeletions;
		std::set<ccl::Geometry *> m_pendingGeometryDeletions;

};

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
			: m_passType( ccl::PASS_NONE ), m_denoise( false ), m_useIEDisplay( output->getType() == "ieDisplay" ), m_lightgroup( false )
		{
			m_parameters = output->parametersData()->copy();
			CompoundDataMap &p = m_parameters->writable();

			p["path"] = new StringData( output->getName() );

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
				else if( tokens[0] == "float" && tokens[1] == "id" )
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
		bool m_useIEDisplay;
		bool m_lightgroup;
};

IE_CORE_DECLAREPTR( CyclesOutput )

using OutputMap = std::map<IECore::InternedString, CyclesOutputPtr>;

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
			std::unique_ptr<ccl::ShaderGraph> graph = ShaderNetworkAlgo::convertGraph(
				surfaceShader, displacementShader, volumeShader,
				scene->shader_manager.get(),
				name
			);
			if( surfaceShader && singleSided )
			{
				ShaderNetworkAlgo::setSingleSided( graph.get() );
			}

			for( const IECoreScene::ShaderNetwork *aovShader : aovShaders )
			{
				ShaderNetworkAlgo::convertAOV(
					aovShader, graph.get(),
					scene->shader_manager.get(),
					name
				);
			}

			m_shader = SceneAlgo::createNodeWithLock<ccl::Shader>( scene );
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
			m_shader->set_graph( std::move( graph ) );

			SceneAlgo::tagUpdateWithLock( m_shader, scene );
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

	private :

		/// Note : `ccl::Scene::delete_nodes()` doesn't actually delete shader
		/// nodes, and `ShaderCache::clearUnused()` is a no-op, so we don't
		/// bother managing them via a NodeDeleter.
		ccl::Shader *m_shader;
		const IECore::MurmurHash m_hash;

};

IE_CORE_DECLAREPTR( CyclesShader )

//////////////////////////////////////////////////////////////////////////
// ShaderCache
//////////////////////////////////////////////////////////////////////////

class ShaderCache
{

	public :

		ShaderCache( ccl::Scene *scene )
			: m_scene( scene )
		{
		}

		void update()
		{
			updateShaders();
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

		// Must not be called concurrently with anything.
		void clearUnused()
		{
			// TODO: Cycles currently doesn't delete unused shaders anyways and it's problematic
			// to delete them in a live render, so we just retain all shaders created, Cycles
			// will delete them all once the session is finished.
			return;
		}

	private :

		void updateShaders()
		{
			std::lock_guard sceneLock( m_scene->mutex );
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
		}

		ccl::Scene *m_scene;
		using Cache = tbb::concurrent_hash_map<IECore::MurmurHash, CyclesShaderPtr>;
		Cache m_cache;

};

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
// Shader Assignment
IECore::InternedString g_cyclesSurfaceShaderAttributeName( "cycles:surface" );
IECore::InternedString g_oslSurfaceShaderAttributeName( "osl:surface" );
IECore::InternedString g_oslShaderAttributeName( "osl:shader" );
IECore::InternedString g_cyclesVolumeShaderAttributeName( "cycles:volume" );
IECore::InternedString g_surfaceShaderAttributeName( "surface" );
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
IECore::InternedString g_volumeVelocityScaleAttributeName( "cycles:volume_velocity_scale");
IECore::InternedString g_volumePrecisionAttributeName( "cycles:volume_precision" );

std::array<IECore::InternedString, 2> g_volumePrecisionEnumNames = { {
	"full",
	"half",
} };

int nameToVolumePrecisionEnum( const IECore::InternedString &name )
{
#define MAP_NAME(enumName, enum) if(name == enumName) return enum;
	MAP_NAME(g_volumePrecisionEnumNames[0], 0);
	MAP_NAME(g_volumePrecisionEnumNames[1], 16);
#undef MAP_NAME

	return 0;
}

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

IECoreScene::ConstShaderNetworkPtr g_facingRatio = []() {

	ShaderNetworkPtr result = new ShaderNetwork;

	const InternedString geometryHandle = result->addShader(
		"geometry", new Shader( "geometry" )
	);
	const InternedString vectorMathHandle = result->addShader(
		"vectorMath", new Shader(
			"vector_math", "shader",
			{
				{ "math_type", new StringData( "dot_product" ) }
			}
		)
	);

	result->addConnection( { { geometryHandle, "normal" }, { vectorMathHandle, "vector1" } } );
	result->addConnection( { { geometryHandle, "incoming" }, { vectorMathHandle, "vector2" } } );
	result->setOutput( { vectorMathHandle, "value" } );

	return result;

} ();

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
				m_volume( attributes ),
				m_shaderAttributes( attributes ),
				m_assetName( "" ),
				m_lightGroup( "" ),
				m_isCausticsCaster( false ),
				m_isCausticsReceiver( false )
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
			m_lightGroup = attributeValue<std::string>( g_lightGroupAttributeName, attributes, m_lightGroup );
			m_assetName = attributeValue<std::string>( g_cryptomatteAssetAttributeName, attributes, m_assetName );
			m_isCausticsCaster = attributeValue<bool>( g_isCausticsCasterAttributeName, attributes, m_isCausticsCaster );
			m_isCausticsReceiver = attributeValue<bool>( g_isCausticsReceiverAttributeName, attributes, m_isCausticsReceiver );

			// Surface shader
			const IECoreScene::ShaderNetwork *volumeShaderAttribute = attribute<IECoreScene::ShaderNetwork>( g_cyclesVolumeShaderAttributeName, attributes );
			const IECoreScene::ShaderNetwork *surfaceShaderAttribute = attribute<IECoreScene::ShaderNetwork>( g_cyclesSurfaceShaderAttributeName, attributes );
			surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<IECoreScene::ShaderNetwork>( g_oslSurfaceShaderAttributeName, attributes );
			surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<IECoreScene::ShaderNetwork>( g_oslShaderAttributeName, attributes );
			surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<IECoreScene::ShaderNetwork>( g_surfaceShaderAttributeName, attributes );
			if( !surfaceShaderAttribute && !volumeShaderAttribute )
			{
				surfaceShaderAttribute = g_facingRatio.get();
			}
			const IECoreScene::ShaderNetwork *displacementShaderAttribute = attribute<IECoreScene::ShaderNetwork>( g_cyclesDisplacementShaderAttributeName, attributes );

			// Hash shader attributes first
			m_shaderAttributes.hash( m_shaderHash, attributes );
			// Create the shader
			m_shader = shaderCache->get( surfaceShaderAttribute, displacementShaderAttribute, volumeShaderAttribute, attributes, m_shaderHash );
			// Then apply the shader attributes
			/// \todo Why not let ShaderCache handle this for us?
			m_shaderAttributes.apply( m_shader->shader() );

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
				m_lightShader = shaderCache->get( lightShader.get(), nullptr, nullptr, attributes, h );
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

		bool applyObject( ccl::Object *object, const CyclesAttributes *previousAttributes, ccl::Scene *scene ) const
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

				if( object->get_geometry()->is_mesh() )
				{
					auto mesh = static_cast<ccl::Mesh *>( object->get_geometry() );
					if( mesh->get_num_subd_faces() )
					{
						if( ( previousAttributes->m_maxLevel != m_maxLevel ) || ( previousAttributes->m_dicingRate != m_dicingRate ) )
						{
							// Get a new mesh
							return false;
						}
					}
				}
				else if( object->get_geometry()->is_volume() )
				{
					IECore::MurmurHash previousVolumeHash;
					previousAttributes->m_volume.hash( previousVolumeHash );

					IECore::MurmurHash currentVolumeHash;
					m_volume.hash( currentVolumeHash );
					if( previousVolumeHash != currentVolumeHash )
					{
						return false;
					}
				}
			}

			object->set_visibility( m_visibility );
			object->set_use_holdout( m_useHoldout );
			object->set_is_shadow_catcher( m_isShadowCatcher );
			object->set_shadow_terminator_shading_offset( m_shadowTerminatorShadingOffset );
			object->set_shadow_terminator_geometry_offset( m_shadowTerminatorGeometryOffset );
			object->set_color( SocketAlgo::setColor( m_color ) );
			object->set_asset_name( ccl::ustring( m_assetName.c_str() ) );
			object->set_is_caustics_caster( m_isCausticsCaster );
			object->set_is_caustics_receiver( m_isCausticsReceiver );

			if( object->get_geometry()->is_mesh() )
			{
				auto mesh = static_cast<ccl::Mesh *>( object->get_geometry() );
				if( mesh->get_num_subd_faces() )
				{
					mesh->set_subd_dicing_rate( m_dicingRate );
					mesh->set_subd_max_level( m_maxLevel );
				}
			}

			if( !previousAttributes || m_shader != previousAttributes->m_shader )
			{
				ccl::array<ccl::Node *> shaders;
				shaders.push_back_slow( m_shader->shader() );
				{
					// We need the scene lock because `tag_used()` will modify the
					// scene.
					std::scoped_lock sceneLock( scene->mutex );
					m_shader->shader()->tag_used( scene );
					// But we also use the lock for `set_used_shaders()`, to protect
					// the non-atomic increment made in `ccl::Node::reference()`.
					// > Note : because we instance geometry, two objects
					// > might be fighting over what shader the geometry should have.
					// > This needs fixing in its own right, but until then, the lock
					// > at least prevents concurrent access.
					object->get_geometry()->set_used_shaders( shaders );

					if( object->get_geometry()->is_mesh() )
					{
						auto mesh = static_cast<ccl::Mesh *>( object->get_geometry() );
						/// \todo I don't know why this is necessary, but without it the new
						/// assignment doesn't seem to be transferred to the render device.
						mesh->tag_shader_modified();
					}
					else if(
						object->get_geometry()->is_volume() &&
						object->get_geometry()->is_modified() &&
						static_cast<ccl::Volume*>( object->get_geometry() )->get_triangles().size()
					)
					{
						// We've replaced an existing shader on a volume
						// from which Cycles has already built a mesh, so
						// we cheekily clear the modified tag to prevent
						// the volume from disappearing.
						/// \todo I suspect we need something similar for meshes,
						/// to prevent unnecessary BVH rebuilds.
						object->get_geometry()->clear_modified();
					}
				}
			}

			m_volume.apply( object );

			object->set_lightgroup( ccl::ustring( m_lightGroup.c_str() ) );

			// Custom attributes.
			object->attributes = m_custom;

			SceneAlgo::tagUpdateWithLock( object, scene );

			return true;
		}

		bool applyLight( ccl::Light *light, const CyclesAttributes *previousAttributes, ccl::Scene *scene ) const
		{
			if( m_lightAttribute )
			{
				ShaderNetworkAlgo::convertLight( m_lightAttribute.get(), light );
				{
					// We need the scene lock because `tag_used()` will modify the
					// scene.
					std::scoped_lock sceneLock( scene->mutex );
					m_lightShader->shader()->tag_used( scene );
					// But we also use the lock for `set_shader()`, to protect the
					// non-atomic increment made in `ccl::Node::reference()`.
					light->set_shader( m_lightShader->shader() );
				}
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
				case IECoreVDB::VDBObjectTypeId :
					m_volume.hash( h );
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

		int getVolumePrecision() const
		{
			return m_volume.precision ? nameToVolumePrecisionEnum( m_volume.precision.value() ) : 0;
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
				velocityScale = optionalAttribute<float>( g_volumeVelocityScaleAttributeName, attributes );
				precision = optionalAttribute<string>( g_volumePrecisionAttributeName, attributes );
			}

			std::optional<float> clipping;
			std::optional<float> stepSize;
			std::optional<bool> objectSpace;
			std::optional<float> velocityScale;
			std::optional<string> precision;

			void hash( IECore::MurmurHash &h ) const
			{
				if( clipping && clipping.value() != 0.001f )
				{
					h.append( clipping.value() );
				}
				if( stepSize && stepSize.value() != 0.0f )
				{
					h.append( stepSize.value() );
				}
				if( objectSpace && objectSpace.value() != false )
				{
					h.append( objectSpace.value() );
				}
				if( velocityScale && velocityScale.value() != 1.0f )
				{
					h.append( velocityScale.value() );
				}
				if( precision && precision.value() != g_volumePrecisionEnumNames[0].c_str() )
				{
					h.append( precision.value() );
				}
			}

			void apply( ccl::Object *object ) const
			{
				if( !object->get_geometry()->is_volume() )
				{
					return;
				}

				auto volume = static_cast<ccl::Volume *>( object->get_geometry() );
				if( clipping )
				{
					volume->set_clipping( clipping.value() );
				}
				if( stepSize )
				{
					volume->set_step_size( stepSize.value() );
				}
				if( objectSpace )
				{
					volume->set_object_space( objectSpace.value() );
				}
				if( velocityScale )
				{
					volume->set_velocity_scale( velocityScale.value() );
				}
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
			std::optional<bool> useTransparentShadow;
			std::optional<bool> heterogeneousVolume;
			ConstDataPtr volumeSamplingMethod;
			ConstDataPtr volumeInterpolationMethod;
			std::optional<float> volumeStepRate;

			void hash( IECore::MurmurHash &h, const IECore::CompoundObject *attributes ) const
			{
				emissionSamplingMethod->hash( h );

				// Volume-related attributes hash
				auto it = attributes->members().find( g_cyclesVolumeShaderAttributeName );
				if( it != attributes->members().end() )
				{
					if( heterogeneousVolume && !heterogeneousVolume.value() )
						h.append( "homogeneous_volume" );
					volumeSamplingMethod->hash( h );
					volumeInterpolationMethod->hash( h );
					if( volumeStepRate && volumeStepRate.value() != 1.0f )
						h.append( volumeStepRate.value() );
				}
			}

			bool apply( ccl::Shader *shader ) const
			{
				SocketAlgo::setSocket( shader, shader->get_emission_sampling_method_socket(), emissionSamplingMethod.get() );
				shader->set_use_transparent_shadow( useTransparentShadow ? useTransparentShadow.value() : true );
				shader->set_heterogeneous_volume( heterogeneousVolume ? heterogeneousVolume.value() : true );
				SocketAlgo::setSocket( shader, shader->get_volume_sampling_method_socket(), volumeSamplingMethod.get() );
				SocketAlgo::setSocket( shader, shader->get_volume_interpolation_method_socket(), volumeInterpolationMethod.get() );
				shader->set_volume_step_rate( volumeStepRate ? volumeStepRate.value() : 1.0f );

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
		Volume m_volume;
		ShaderAttributes m_shaderAttributes;
		InternedString m_assetName;
		InternedString m_lightGroup;
		bool m_isCausticsCaster;
		bool m_isCausticsReceiver;
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

class AttributesCache
{

	public :

		AttributesCache( ShaderCache *shaderCache )
			:	m_shaderCache( shaderCache )
		{
		}

		// Can be called concurrently with other get() calls.
		CyclesAttributesPtr get( const IECore::CompoundObject *attributes )
		{
			Cache::accessor a;
			m_cache.insert( a, attributes->Object::hash() );
			if( !a->second )
			{
				a->second = new CyclesAttributes( attributes, m_shaderCache );
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

		ShaderCache *m_shaderCache;

		using Cache = tbb::concurrent_hash_map<IECore::MurmurHash, CyclesAttributesPtr>;
		Cache m_cache;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// GeometryCache
//////////////////////////////////////////////////////////////////////////

namespace
{

/// \todo Make this point to `const ccl::Geometry`, since shared
/// geometry should be immutable.
using SharedGeometryPtr = std::shared_ptr<ccl::Geometry>;

class GeometryCache
{

	public :

		GeometryCache( ccl::Scene *scene, NodeDeleter *nodeDeleter )
			: m_scene( scene ), m_nodeDeleter( nodeDeleter )
		{
		}

		// Can be called concurrently with other get() calls.
		SharedGeometryPtr get( const IECore::Object *object, const IECoreScenePreview::Renderer::AttributesInterface *attributes, const std::string &nodeName )
		{
			const CyclesAttributes *cyclesAttributes = static_cast<const CyclesAttributes *>( attributes );

			if( !cyclesAttributes->canInstanceGeometry( object ) )
			{
				return convert( object, cyclesAttributes, nodeName );
			}

			IECore::MurmurHash h = object->hash();
			cyclesAttributes->hashGeometry( object, h );

			Geometry::const_accessor readAccessor;
			if( m_geometry.find( readAccessor, h ) )
			{
				return readAccessor->second;
			}
			else
			{
				Geometry::accessor writeAccessor;
				if( m_geometry.insert( writeAccessor, h ) )
				{
					writeAccessor->second = convert( object, cyclesAttributes, nodeName );
				}
				return writeAccessor->second;
			}
		}

		// Can be called concurrently with other get() calls.
		SharedGeometryPtr get(
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
				return convert( samples, times, frameIdx, cyclesAttributes, nodeName );
			}

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

			Geometry::const_accessor readAccessor;
			if( m_geometry.find( readAccessor, h ) )
			{
				return readAccessor->second;
			}
			else
			{
				Geometry::accessor writeAccessor;
				if( m_geometry.insert( writeAccessor, h ) )
				{
					writeAccessor->second = convert( samples, times, frameIdx, cyclesAttributes, nodeName );
				}
				return writeAccessor->second;
			}
		}

		// Must not be called concurrently with anything.
		void clearUnused()
		{
			vector<IECore::MurmurHash> toErase;
			for( Geometry::iterator it = m_geometry.begin(), eIt = m_geometry.end(); it != eIt; ++it )
			{
				if( it->second.use_count() == 1 )
				{
					// Only one reference - this is ours, so
					// nothing outside of the cache is using the
					// node.
					toErase.push_back( it->first );
				}
			}
			for( vector<IECore::MurmurHash>::const_iterator it = toErase.begin(), eIt = toErase.end(); it != eIt; ++it )
			{
				m_geometry.erase( *it );
			}
		}

	private :

		SharedGeometryPtr convert( const IECore::Object *object, const CyclesAttributes *attributes, const std::string &nodeName )
		{
			auto geometry = SharedGeometryPtr( GeometryAlgo::convert( object, nodeName, m_scene ), NodeDeleter::GeometryDeleter( m_nodeDeleter ) );

			if( auto vdb = IECore::runTimeCast<const IECoreVDB::VDBObject>( object ) )
			{
				// It's a pity we can't do this in VolumeAlgo in the first place. It is here instead because
				// the precision is provided by the attributes, and we don't want to pass attributes
				// to `GeometryAlgo`.
				assert( geometry->is_volume() );
				GeometryAlgo::convertVoxelGrids( vdb, static_cast<ccl::Volume*>( geometry.get() ), m_scene, attributes->getVolumePrecision() );
			}

			return geometry;
		}

		SharedGeometryPtr convert(
			const std::vector<const IECore::Object *> &samples,
			const std::vector<float> &times,
			const int frame,
			const CyclesAttributes *attributes,
			const std::string &nodeName
		)
		{
			auto geometry = SharedGeometryPtr( GeometryAlgo::convert( samples, times, frame, nodeName, m_scene ), NodeDeleter::GeometryDeleter( m_nodeDeleter ) );

			if( auto vdb = IECore::runTimeCast<const IECoreVDB::VDBObject>( samples.front() ) )
			{
				assert( geometry->is_volume() );
				GeometryAlgo::convertVoxelGrids( vdb, static_cast<ccl::Volume*>( geometry.get() ), m_scene, attributes->getVolumePrecision() );
			}

			return geometry;
		}

		ccl::Scene *m_scene;
		NodeDeleter *m_nodeDeleter;
		using Geometry = tbb::concurrent_hash_map<IECore::MurmurHash, SharedGeometryPtr>;
		Geometry m_geometry;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// LightLinker definition
//////////////////////////////////////////////////////////////////////////

namespace
{

class LightLinker
{

	public :

		LightLinker( IECoreScenePreview::Renderer::RenderType renderType );

		enum class SetType
		{
			Light = 0,
			Shadow = 1
		};

		uint32_t registerLightSet( SetType setType, const IECoreScenePreview::Renderer::ConstObjectSetPtr &lights );
		void deregisterLightSet( SetType setType, const IECoreScenePreview::Renderer::ConstObjectSetPtr &lights );

	private :

		const IECoreScenePreview::Renderer::RenderType m_renderType;

		using WeakObjectSetPtr = std::weak_ptr<const IECoreScenePreview::Renderer::ObjectSet>;

		struct LightSet
		{
			size_t useCount = 0;
			uint32_t index;
		};

		struct LightSets
		{
			/// \todo Use `unordered_map` (or `concurrent_unordered_map`) when `std::owner_hash()`
			/// becomes available (in C++26).
			using Map = std::map<WeakObjectSetPtr, LightSet, std::owner_less<WeakObjectSetPtr>>;
			Map map;
			uint64_t usedIndices = 1;
		};

		std::mutex m_mutex;
		LightSets m_lightSets;
		LightSets m_shadowSets;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesObject
//////////////////////////////////////////////////////////////////////////

namespace
{

const IECore::InternedString g_lights( "lights" );
const IECore::InternedString g_shadowedLights( "shadowedLights" );

class CyclesObject : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		CyclesObject( ccl::Scene *scene, const SharedGeometryPtr &geometry, const std::string &name, const float frame, LightLinker *lightLinker, NodeDeleter *nodeDeleter )
			:	m_scene( scene ),
				m_object( SceneAlgo::createNodeWithLock<ccl::Object>( scene ), NodeDeleter::ObjectDeleter( nodeDeleter ) ),
				m_geometry( geometry ), m_frame( frame ), m_attributes( nullptr ), m_lightLinker( lightLinker )
		{
			assert( m_geometry );
			m_object->name = ccl::ustring( name.c_str() );
			m_object->set_random_id( std::hash<string>()( name ) );
			{
				// We're not accessing the scene here, but we use the lock to
				// protect against concurrent calls with the same `geometry` on
				// other objects, because `set_geometry()` manipulates the
				// reference count on `geometry` in a non-threadsafe way.
				/// \todo Would the Cycles project accept a patch to make the
				/// reference count atomic?
				std::scoped_lock sceneLock( scene->mutex );
				m_object->set_geometry( geometry.get() );
			}
		}

		~CyclesObject() override
		{
			if( m_linkedLights )
			{
				m_lightLinker->deregisterLightSet( LightLinker::SetType::Light, m_linkedLights );
			}
			if( m_shadowedLights )
			{
				m_lightLinker->deregisterLightSet( LightLinker::SetType::Shadow, m_shadowedLights );
			}
		}

		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override
		{
			IECoreScenePreview::Renderer::ConstObjectSetPtr *setMemberData;
			LightLinker::SetType setType;
			if( type == g_lights )
			{
				setMemberData = &m_linkedLights;
				setType = LightLinker::SetType::Light;
			}
			else if( type == g_shadowedLights )
			{
				setMemberData = &m_shadowedLights;
				setType = LightLinker::SetType::Shadow;
			}
			else
			{
				return;
			}

			if( *setMemberData )
			{
				m_lightLinker->deregisterLightSet( setType, *setMemberData );
			}
			*setMemberData = objects;

			uint32_t lightSet = 0;
			if( *setMemberData )
			{
				lightSet = m_lightLinker->registerLightSet( setType, *setMemberData );
			}

			if( setType == LightLinker::SetType::Light )
			{
				m_object->set_receiver_light_set( lightSet );
			}
			else
			{
				m_object->set_blocker_shadow_set( lightSet );
			}

			SceneAlgo::tagUpdateWithLock( m_object.get(), m_scene );
		}

		void transform( const Imath::M44f &transform ) override
		{
			m_object->set_tfm( SocketAlgo::setTransform( transform ) );
			if( m_object->get_geometry()->is_mesh() )
			{
				auto mesh = static_cast<ccl::Mesh *>( m_object->get_geometry() );
				if( mesh->get_num_subd_faces() )
				{
					mesh->set_subd_objecttoworld( m_object->get_tfm() );
				}
			}

			ccl::array<ccl::Transform> motion;
			if( m_object->get_geometry()->get_use_motion_blur() )
			{
				motion.resize( m_object->get_geometry()->get_motion_steps(), ccl::transform_empty() );
				for( size_t i = 0; i < motion.size(); ++i )
				{
					motion[i] = m_object->get_tfm();
				}
			}

			m_object->set_motion( motion );

			SceneAlgo::tagUpdateWithLock( m_object.get(), m_scene );
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			ccl::array<ccl::Transform> motion;
			ccl::Geometry *geo = m_object->get_geometry();
			if( geo->get_use_motion_blur() && geo->get_motion_steps() != samples.size() )
			{
				IECore::msg(
					IECore::Msg::Error, "IECoreCycles::Renderer",
					fmt::format( "Transform step size on \"{}\" must match deformation step size.", m_object->name.c_str() )
				);
				m_object->set_tfm( SocketAlgo::setTransform( samples.front() ) );
				motion.resize( geo->get_motion_steps(), ccl::transform_empty() );
				for( size_t i = 0; i < motion.size(); ++i )
				{
					motion[i] = m_object->get_tfm();
					m_object->set_motion( motion );
				}
				SceneAlgo::tagUpdateWithLock( m_object.get(), m_scene );
				return;
			}

			const size_t numSamples = samples.size();

			if( numSamples == 1 )
			{
				m_object->set_tfm( SocketAlgo::setTransform( samples.front() ) );
				SceneAlgo::tagUpdateWithLock( m_object.get(), m_scene );
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
						m_object->set_tfm( SocketAlgo::setTransform( samples[i] ) );
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
					m_object->set_tfm( SocketAlgo::setTransform( matrix ) );
				}
				else if( frameIdx == 0 ) // Start frame
				{
					m_object->set_tfm( SocketAlgo::setTransform( samples[0] ) );
				}
				else // End frame
				{
					m_object->set_tfm( SocketAlgo::setTransform( samples[1] ) );
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
					m_object->set_tfm( SocketAlgo::setTransform( matrix ) );
				}
				else if( frameIdx == 0 ) // Start frame
				{
					m_object->set_tfm( SocketAlgo::setTransform( samples[0] ) );
				}
				else // End frame
				{
					m_object->set_tfm( SocketAlgo::setTransform( samples[numSamples-1] ) );
				}

				for( size_t i = 0; i < numSamples; ++i )
				{
					motion[i] = SocketAlgo::setTransform( samples[i] );
				}
			}

			m_object->set_motion( motion );
			if( !geo->get_use_motion_blur() )
			{
				/// \todo This is not thread-safe, nor is it compatible
				/// with instancing.
				geo->set_motion_steps( motion.size() );
			}

			if( geo->is_mesh() )
			{
				auto mesh = static_cast<ccl::Mesh *>( geo );
				if( mesh->get_num_subd_faces() )
				{
					mesh->set_subd_objecttoworld( m_object->get_tfm() );
				}
			}

			SceneAlgo::tagUpdateWithLock( m_object.get(), m_scene );
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			const CyclesAttributes *cyclesAttributes = static_cast<const CyclesAttributes *>( attributes );
			if( cyclesAttributes->applyObject( m_object.get(), m_attributes.get(), m_scene ) )
			{
				m_attributes = cyclesAttributes;
				SceneAlgo::tagUpdateWithLock( m_object.get(), m_scene );
				return true;
			}

			return false;
		}

		void assignID( uint32_t id ) override
		{
			m_object->set_pass_id( id );
		}

		void assignInstanceID( uint32_t id ) override
		{
			// Instance IDs not needed in Cycles, because encapsulated instancers aren't supported.
		}

	private :

		ccl::Scene *m_scene;
		using UniqueObjectPtr = std::unique_ptr<ccl::Object, NodeDeleter::ObjectDeleter>;
		UniqueObjectPtr m_object;
		SharedGeometryPtr m_geometry;
		const float m_frame;
		ConstCyclesAttributesPtr m_attributes;
		LightLinker *m_lightLinker;
		IECoreScenePreview::Renderer::ConstObjectSetPtr m_linkedLights;
		IECoreScenePreview::Renderer::ConstObjectSetPtr m_shadowedLights;

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

		CyclesLight( ccl::Scene *scene, ccl::ustring name, NodeDeleter *nodeDeleter )
			:	m_scene( scene ), m_light( SceneAlgo::createNodeWithLock<ccl::Light>( scene ), NodeDeleter::LightDeleter( nodeDeleter ) )
		{
			m_light->name = name;
			// All lights are always in the first set, which we use for objects
			// which don't have any linking applied. But we only add lights to
			// other sets as they are created by the LightLinker in response to
			// calls to `CyclesObject::link()`.
			m_light->set_light_set_membership( 1 );
			m_light->set_shadow_set_membership( 1 );
		}

		~CyclesLight() override
		{
		}

		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override
		{
		}

		void transform( const Imath::M44f &transform ) override
		{
			m_light->set_tfm( SocketAlgo::setTransform( transform ) );
			SceneAlgo::tagUpdateWithLock( m_light.get(), m_scene );
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			// Cycles doesn't support motion samples on lights (yet)
			transform( samples[0] );
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			const CyclesAttributes *cyclesAttributes = static_cast<const CyclesAttributes *>( attributes );
			if( cyclesAttributes->applyLight( m_light.get(), m_attributes.get(), m_scene ) )
			{
				m_attributes = cyclesAttributes;
				SceneAlgo::tagUpdateWithLock( m_light.get(), m_scene );
				return true;
			}

			return false;
		}

		void assignID( uint32_t id ) override
		{
			/// \todo Implement me
		}

		void assignInstanceID( uint32_t instanceID ) override
		{
		}

		// Used by LightLinker
		// ===================

		uint64_t getLightSetMembership( LightLinker::SetType setType ) const
		{
			return setType == LightLinker::SetType::Light ? m_light->get_light_set_membership() : m_light->get_shadow_set_membership();
		}

		void setLightSetMembership( LightLinker::SetType setType, uint64_t membership )
		{
			if( setType == LightLinker::SetType::Light )
			{
				m_light->set_light_set_membership( membership );
			}
			else
			{
				m_light->set_shadow_set_membership( membership );
			}

			SceneAlgo::tagUpdateWithLock( m_light.get(), m_scene );
		}

	private :

		ccl::Scene *m_scene;
		using UniqueLightPtr = std::unique_ptr<ccl::Light, NodeDeleter::LightDeleter>;
		UniqueLightPtr m_light;
		ConstCyclesAttributesPtr m_attributes;

};

IE_CORE_DECLAREPTR( CyclesLight )

} // namespace


//////////////////////////////////////////////////////////////////////////
// LightLinker definition
//////////////////////////////////////////////////////////////////////////

namespace
{

uint64_t indexToMask( int index )
{
	return uint64_t( 1 ) << index;
}

LightLinker::LightLinker( IECoreScenePreview::Renderer::RenderType renderType )
	:	m_renderType( renderType )
{
}

uint32_t LightLinker::registerLightSet( SetType setType, const IECoreScenePreview::Renderer::ConstObjectSetPtr &lights )
{
	std::lock_guard lock( m_mutex );
	LightSets &lightSets = setType == SetType::Light ? m_lightSets : m_shadowSets;

	LightSet &lightSet = lightSets.map[lights];
	lightSet.useCount++;
	if( lightSet.useCount == 1 )
	{
		// First usage of this set. Find an unused index.
		for( int i = 1; i < LIGHT_LINK_SET_MAX; ++i )
		{
			if( ( lightSets.usedIndices & indexToMask( i ) ) == 0 )
			{
				lightSet.index = i;
				lightSets.usedIndices = lightSets.usedIndices | indexToMask( i );
				break;
			}
		}

		if( lightSet.index != 0 )
		{
			// Assign membership to lights. Note that we rely on `lock` here to
			// prevent concurrent modification to the lights from multiple calls
			// to `registerLightSet()`.
			for( const auto &object : *lights )
			{
				auto light = static_cast<CyclesLight *>( object.get() );
				light->setLightSetMembership(
					setType,
					light->getLightSetMembership( setType ) | indexToMask( lightSet.index )
				);
			}
		}
		else
		{
			// We ran out of indices.
			IECore::msg(
				IECore::Msg::Level::Warning, "CyclesRenderer",
				fmt::format(
					"{} linking failed because the maximum number of unique light groups ({}) was exceeded.",
					setType == SetType::Light ? "Light" : "Shadow",
					LIGHT_LINK_SET_MAX
				)
			);
		}
	}
	return lightSet.index;
}

void LightLinker::deregisterLightSet( SetType setType, const IECoreScenePreview::Renderer::ConstObjectSetPtr &lights )
{
	if( m_renderType != IECoreScenePreview::Renderer::RenderType::Interactive )
	{
		// `~CyclesObject` always deregisters links, but in a batch render
		// that doesn't mean they are no longer wanted.
		return;
	}

	std::lock_guard lock( m_mutex );
	LightSets &lightSets = setType == SetType::Light ? m_lightSets : m_shadowSets;

	auto it = lightSets.map.find( lights );
	assert( it != lightSets.map.end() );
	assert( it->second.useCount );
	it->second.useCount--;
	if( it->second.useCount )
	{
		return;
	}

	// Set no longer in use.

	lightSets.usedIndices = lightSets.usedIndices & ~indexToMask( it->second.index );
	for( const auto &object : *lights )
	{
		auto light = static_cast<CyclesLight *>( object.get() );
		light->setLightSetMembership(
			setType,
			light->getLightSetMembership( setType ) & ~indexToMask( it->second.index )
		);
	}

	lightSets.map.erase( it );
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// CyclesCamera
//////////////////////////////////////////////////////////////////////////

namespace
{

class CyclesCamera : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		IE_CORE_DECLAREMEMBERPTR( CyclesCamera );

		CyclesCamera( const IECoreScene::ConstCameraPtr &camera )
			:	m_camera( camera ),
				m_transformSamples( { M44f() } )
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
			m_transformSamples = { transform };
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			m_transformSamples = samples;
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			// Attributes don't affect the camera, so the edit always "succeeds".
			return true;
		}

		void assignID( uint32_t id ) override
		{
		}

		void assignInstanceID( uint32_t instanceID ) override
		{
		}

		void apply( ccl::Camera *destination ) const
		{
			CameraAlgo::convert( m_camera.get(), destination );

			const size_t numSamples = m_transformSamples.size();

			ccl::array<ccl::Transform> motion;

			const Imath::V3f scale = Imath::V3f( 1.0f, -1.0f, -1.0f );
			Imath::M44f matrix;

			if( destination->get_motion_position() == ccl::MOTION_POSITION_START )
			{
				matrix = m_transformSamples.front();
				matrix.scale( scale );
				destination->set_matrix( SocketAlgo::setTransform( matrix ) );
				if( numSamples != 1 )
				{
					motion = ccl::array<ccl::Transform>( 3 );
					motion[0] = destination->get_matrix();
					IECore::LinearInterpolator<Imath::M44f>()( m_transformSamples.front(), m_transformSamples.back(), 0.5f, matrix );
					matrix.scale( scale );
					motion[1] = SocketAlgo::setTransform( matrix );
					matrix = m_transformSamples.back();
					matrix.scale( scale );
					motion[2] = SocketAlgo::setTransform( matrix );
				}
			}
			else if( destination->get_motion_position() == ccl::MOTION_POSITION_END )
			{
				matrix = m_transformSamples.back();
				matrix.scale( scale );
				destination->set_matrix( SocketAlgo::setTransform( matrix ) );
				if( numSamples != 1 )
				{
					motion = ccl::array<ccl::Transform>( 3 );
					motion[0] = destination->get_matrix();
					IECore::LinearInterpolator<Imath::M44f>()( m_transformSamples.back(), m_transformSamples.front(), 0.5f, matrix );
					matrix.scale( scale );
					motion[1] = SocketAlgo::setTransform( matrix );
					matrix = m_transformSamples.front();
					matrix.scale( scale );
					motion[2] = SocketAlgo::setTransform( matrix );
				}
			}
			else // ccl::Camera::MOTION_POSITION_CENTER
			{
				if( numSamples == 1 ) // One sample
				{
					matrix = m_transformSamples.front();
					matrix.scale( scale );
					destination->set_matrix( SocketAlgo::setTransform( matrix ) );
				}
				else
				{
					IECore::LinearInterpolator<Imath::M44f>()( m_transformSamples.front(), m_transformSamples.back(), 0.5f, matrix );
					matrix.scale( scale );
					destination->set_matrix( SocketAlgo::setTransform( matrix ) );

					motion = ccl::array<ccl::Transform>( 3 );
					matrix = m_transformSamples.front();
					matrix.scale( scale );
					motion[0] = SocketAlgo::setTransform( matrix );
					motion[1] = destination->get_matrix();
					matrix = m_transformSamples.back();
					matrix.scale( scale );
					motion[2] = SocketAlgo::setTransform( matrix );
				}
			}
			destination->set_motion( motion );
		}

	private :

		IECoreScene::ConstCameraPtr m_camera;
		std::vector<Imath::M44f> m_transformSamples;

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

ccl::DeviceInfo matchingDevices( const std::string &pattern, int threads, bool background, ccl::DenoiserType denoiser = ccl::DenoiserType::DENOISER_NONE )
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
			// If a denoiser is specified, only match devices that support it.
			if( denoiser != ccl::DenoiserType::DENOISER_NONE && !( device.denoisers & denoiser ) )
			{
				continue;
			}
			devices.push_back( device );
		}
	}

	if( devices.empty() )
	{
		if( denoiser != ccl::DenoiserType::DENOISER_NONE )
		{
			IECore::msg( IECore::Msg::Warning, "CyclesRenderer", fmt::format( "No compatible {} denoise device matching \"{}\" found, reverting to CPU denoising if available.", ccl::denoiserTypeToHumanReadable( denoiser ), pattern ) );
		}
		else
		{
			IECore::msg( IECore::Msg::Warning, "CyclesRenderer", fmt::format( "No devices matching \"{}\" found, reverting to CPU.", pattern ) );
		}
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
	result->writable()["samples"] = new BoolData( params.samples );
	result->writable()["threads"] = new IntData( params.threads );
	return result;
}

ccl::SessionParams defaultSessionParams( IECoreScenePreview::Renderer::RenderType renderType )
{
	ccl::SessionParams params;
	params.device = firstCPUDevice();
	params.shadingsystem = ccl::SHADINGSYSTEM_OSL;
	params.use_resolution_divider = false;

	if( renderType == IECoreScenePreview::Renderer::RenderType::Interactive )
	{
		params.headless = false;
		params.background = false;
		params.use_auto_tile = false;
	}
	else
	{
		params.headless = true;
		params.background = true;
	}

	return params;
}

ccl::SceneParams defaultSceneParams( IECoreScenePreview::Renderer::RenderType renderType )
{
	ccl::SceneParams params;
	params.shadingsystem = ccl::SHADINGSYSTEM_OSL;
	params.bvh_layout = ccl::BVH_LAYOUT_AUTO;

	if( renderType == IECoreScenePreview::Renderer::RenderType::Interactive )
	{
		params.bvh_type = ccl::BVH_TYPE_DYNAMIC;
	}
	else
	{
		params.bvh_type = ccl::BVH_TYPE_STATIC;
	}

	return params;
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

// Denoisers
IECore::InternedString g_denoiseOptix( "optix" );
IECore::InternedString g_denoiseOpenImageDenoise( "openimagedenoise" );

ccl::DenoiserType nameToDenoiseTypeEnum( const IECore::InternedString &name )
{
#define MAP_NAME(enumName, enum) if(name == enumName) return enum;
	if( IECoreCycles::optixDenoiseSupported() )
	{
		MAP_NAME(g_denoiseOptix, ccl::DenoiserType::DENOISER_OPTIX);
	}
	if( IECoreCycles::openImageDenoiseSupported() )
	{
		MAP_NAME(g_denoiseOpenImageDenoise, ccl::DenoiserType::DENOISER_OPENIMAGEDENOISE);
	}
#undef MAP_NAME

	return ccl::DenoiserType::DENOISER_NONE;
}

// Core
IECore::InternedString g_frameOptionName( "frame" );
IECore::InternedString g_cameraOptionName( "camera" );
IECore::InternedString g_sampleMotionOptionName( "sampleMotion" );
IECore::InternedString g_deviceOptionName( "cycles:device" );
IECore::InternedString g_denoiseDeviceOptionName( "cycles:denoise_device" );
IECore::InternedString g_shadingsystemOptionName( "cycles:shadingsystem" );
IECore::InternedString g_squareSamplesOptionName( "cycles:square_samples" );
// Logging
IECore::InternedString g_logLevelOptionName( "cycles:log_level" );
IECore::InternedString g_progressLevelOptionName( "cycles:progress_level" );
// Session
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
// Integrator
IECore::InternedString g_seedOptionName( "cycles:integrator:seed" );
IECore::InternedString g_denoiserTypeOptionName( "cycles:integrator:denoiser_type" );

const boost::container::flat_map<std::string, ccl::PathRayFlag> g_rayTypes = {
	{ "camera", ccl::PATH_RAY_CAMERA },
	{ "diffuse", ccl::PATH_RAY_DIFFUSE },
	{ "glossy", ccl::PATH_RAY_GLOSSY },
	{ "transmission", ccl::PATH_RAY_TRANSMIT },
	{ "shadow", ccl::PATH_RAY_SHADOW },
	{ "scatter", ccl::PATH_RAY_VOLUME_SCATTER }
};

const boost::container::flat_map<int, ccl::LogLevel> g_logLevels = {
	{ 0, ccl::LOG_LEVEL_ERROR },
	{ 1, ccl::LOG_LEVEL_WARNING },
	{ 2, ccl::LOG_LEVEL_INFO }
};

// Dicing camera
IECore::InternedString g_dicingCameraOptionName( "cycles:dicing_camera" );

// Cryptomatte
IECore::InternedString g_cryptomatteDepthOptionName( "cycles:film:cryptomatte_depth");

IE_CORE_FORWARDDECLARE( CyclesRenderer )

class CyclesRenderer final : public IECoreScenePreview::Renderer
{

	public :

		CyclesRenderer( RenderType renderType, const std::string &fileName, const IECore::MessageHandlerPtr &messageHandler )
			:	m_optionsChanged( true ),
				m_scene( nullptr ),
				m_bufferParams( ccl::BufferParams() ),
				m_renderType( renderType ),
				m_rendering( false ),
				m_outputsChanged( true ),
				m_messageHandler( messageHandler ),
				m_lightLinker( renderType )

		{
			m_cameras["ieCoreCycles:defaultCamera"] =  new CyclesCamera( new IECoreScene::Camera() );
		}

		~CyclesRenderer() override
		{
			// Cancel session before destruction of anything else. `~Session` actually
			// calls `cancel()` internally, but the session can emit progress updates
			// on other threads during cancellation, and our `progress()` method accesses
			// member data that needs to be intact when that happens.
			if( m_session )
			{
				m_session->cancel();
			}
		}

		IECore::InternedString name() const override
		{
			return "Cycles";
		}

		void option( const IECore::InternedString &name, const IECore::Object *value ) override
		{
			// Store for use in `acquireSession()` and `updateOptions()`.
			Option &option = m_options[name];
			if( option.value && value )
			{
				option.modified = value->isNotEqualTo( option.value.get() );
			}
			else
			{
				option.modified = (bool)value != (bool)option.value;
			}
			option.value = value;
			m_optionsChanged = m_optionsChanged || option.modified;
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
			acquireSession();
			return m_attributesCache->get( attributes );
		}

		ObjectInterfacePtr camera( const std::string &name, const IECoreScene::Camera *camera, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			// No need to acquire session because we don't need it to make a camera.
			// This is important for certain clients (SceneGadget and RenderController)
			// because they make a camera before calling `option()` to set the device.
			CyclesCameraPtr result = new CyclesCamera( camera );
			m_cameras[name] = result;
			if( attributes )
			{
				result->attributes( attributes );
			}
			return result;
		}

		ObjectInterfacePtr light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			acquireSession();

			CyclesLightPtr result = new CyclesLight( m_scene, ccl::ustring( name.c_str() ), m_nodeDeleter.get() );
			result->attributes( attributes );
			return result;
		}

		ObjectInterfacePtr lightFilter( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			acquireSession();

			IECore::msg( IECore::Msg::Warning, "CyclesRenderer", "lightFilter() unimplemented" );
			return nullptr;
		}

		ObjectInterfacePtr object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			acquireSession();

			SharedGeometryPtr geometry = m_geometryCache->get( object, attributes, name );
			if( !geometry )
			{
				return nullptr;
			}

			ObjectInterfacePtr result = new CyclesObject( m_scene, geometry, name, frame(), &m_lightLinker, m_nodeDeleter.get() );
			result->attributes( attributes );
			return result;
		}

		ObjectInterfacePtr object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const AttributesInterface *attributes ) override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			acquireSession();

			int frameIdx = -1;
			if( m_scene->camera->get_motion_position() == ccl::MOTION_POSITION_START )
			{
				frameIdx = 0;
			}
			else if( m_scene->camera->get_motion_position() == ccl::MOTION_POSITION_END )
			{
				frameIdx = times.size()-1;
			}
			SharedGeometryPtr geometry = m_geometryCache->get( samples, times, frameIdx, attributes, name );
			if( !geometry )
			{
				return nullptr;
			}

			ObjectInterfacePtr result = new CyclesObject( m_scene, geometry, name, frame(), &m_lightLinker, m_nodeDeleter.get() );
			result->attributes( attributes );
			return result;
		}

		void render() override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			acquireSession();

			if( m_rendering && m_renderType == Interactive )
			{
				clearUnused();
			}

			if( m_nodeDeleter )
			{
				m_nodeDeleter->doPendingDeletions();
			}

			updateOptions();
			updateSceneObjects();
			updateBackground();

			{
				std::lock_guard sceneLock( m_scene->mutex );
				const std::string cameraName = optionValue<string>( g_cameraOptionName, "" );
				updateCamera( cameraName, m_scene->camera );
				updateCamera( optionValue<string>( g_dicingCameraOptionName, cameraName ), m_scene->dicing_camera );
			}

			updateOutputs();
			warnForUnusedOptions();

			if( m_rendering )
			{
				std::lock_guard sceneLock( m_scene->mutex );
				if( m_scene->need_reset() )
				{
					m_session->reset( m_session->params, m_bufferParams );
				}
			}

			if( m_rendering )
			{
				m_session->set_pause( false );
				return;
			}

			m_session->start();

			m_rendering = true;

			if( m_renderType == Interactive )
			{
				return;
			}

			// Free up caches, Cycles now owns the data.
			resetCaches();
			m_session->wait();
			m_rendering = false;
		}

		void pause() override
		{
			const IECore::MessageHandler::Scope s( m_messageHandler.get() );
			if( m_rendering )
			{
				m_session->set_pause( true );
			}
		}

		IECore::DataPtr command( const IECore::InternedString name, const IECore::CompoundDataMap &parameters ) override
		{
			if( name == "cycles:queryIntegrator" )
			{
				acquireSession();
				updateOptions();
				return SocketAlgo::getSockets( m_scene->integrator );
			}
			else if( name == "cycles:queryFilm" )
			{
				acquireSession();
				updateOptions();
				return SocketAlgo::getSockets( m_scene->film );
			}
			else if( name == "cycles:querySession" )
			{
				acquireSession();
				updateOptions();
				return sessionParamsAsData( m_session->params );
			}
			else if( boost::starts_with( name.string(), "cycles:" ) || name.string().find( ":" ) == string::npos )
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::command", fmt::format( "Unknown command \"{}\"", name.c_str() ) );
			}

			return nullptr;
		}

	private :

		int frame() const
		{
			return optionValue<int>( g_frameOptionName, 1 );
		}

		// Returns the value of an option, falling back to the default provided.
		// If the value was modified since the previous call, sets `*modified = true`.
		template<typename T>
		T optionValue( const IECore::InternedString &name, const T &defaultValue, bool *modified = nullptr ) const
		{
			auto it = m_options.find( name );
			if( it == m_options.end() )
			{
				return defaultValue;
			}
			if( it->second.modified )
			{
				if( modified )
				{
					*modified = true;
				}
				it->second.modified = false;
			}

			if( !it->second.value )
			{
				return defaultValue;
			}
			using DataType = IECore::TypedData<T>;
			const DataType *data = reportedCast<const DataType>( it->second.value.get(), "option", name );
			return data ? data->readable() : defaultValue;
		}

		ccl::SessionParams sessionParamsFromOptions( bool *modified = nullptr )
		{
			ccl::SessionParams params = defaultSessionParams( m_renderType );

			params.samples = optionValue<int>( g_samplesOptionName, params.samples, modified );
			params.pixel_size = optionValue<int>( g_pixelSizeOptionName, params.pixel_size, modified );
			params.time_limit = optionValue<float>( g_timeLimitOptionName, params.time_limit, modified );
			params.use_profiling = optionValue<bool>( g_useProfilingOptionName, params.use_profiling, modified );
			params.use_auto_tile = optionValue<bool>( g_useAutoTileOptionName, params.use_auto_tile, modified );
			params.tile_size = optionValue<int>( g_tileSizeOptionName, params.tile_size, modified );
			params.shadingsystem = nameToShadingSystemEnum( optionValue<string>( g_shadingsystemOptionName, "OSL", modified ) );
			const int threads = optionValue<int>( g_threadsOptionName, 0, modified );
			params.threads = threads > 0 ? threads : std::max( (int)std::thread::hardware_concurrency() + threads, 1 );
			// Device depends on threads, so do that last.
			params.device = matchingDevices( optionValue<string>( g_deviceOptionName, "CPU", modified ), params.threads, params.background );
			// Denoise device depends on the chosen denoiser.
			const ccl::DenoiserType denoiser = nameToDenoiseTypeEnum( optionValue<string>( g_denoiserTypeOptionName, "openimagedenoise", modified ) );
			params.denoise_device = matchingDevices( optionValue<string>( g_denoiseDeviceOptionName, "*", modified ), params.threads, params.background, denoiser );

			return params;
		}

		ccl::SceneParams sceneParamsFromOptions( bool *modified = nullptr )
		{
			ccl::SceneParams params = defaultSceneParams( m_renderType );
			params.bvh_layout = nameToBvhLayoutEnum( optionValue<string>( g_bvhLayoutOptionName, "auto", modified ) );
			params.hair_shape = nameToCurveShapeTypeEnum( optionValue<string>( g_hairShapeOptionName, "ribbon", modified ) );
			params.use_bvh_spatial_split = optionValue<bool>( g_useBvhSpatialSplitOptionName, params.use_bvh_spatial_split, modified );
			params.use_bvh_unaligned_nodes = optionValue<bool>( g_useBvhUnalignedNodesOptionName, params.use_bvh_unaligned_nodes, modified );
			params.num_bvh_time_steps = optionValue<int>( g_numBvhTimeStepsOptionName, params.num_bvh_time_steps, modified );
			params.hair_subdivisions = optionValue<int>( g_hairSubdivisionsOptionName, params.hair_subdivisions, modified );
			params.texture_limit = optionValue<int>( g_textureLimitOptionName, params.texture_limit, modified );
			params.shadingsystem = nameToShadingSystemEnum( optionValue<string>( g_shadingsystemOptionName, "OSL", modified ) );
			return params;
		}

		void acquireSession()
		{
			// Lock is needed because `acquireSession()` can be called from multiple
			// threads. `spin_mutex` is appropriate because after initialisation we
			// are only doing a single check on `m_session`, and we want to return as
			// fast as possible.
			tbb::spin_mutex::scoped_lock lock( m_sessionAcquireMutex );
			if( m_session )
			{
				return;
			}

			ccl::SessionParams sessionParams = sessionParamsFromOptions();
			ccl::SceneParams sceneParams = sceneParamsFromOptions();

			if( sessionParams.shadingsystem == ccl::SHADINGSYSTEM_OSL && !sessionParams.device.has_osl )
			{
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer", "Device doesn't support OSL, reverting to CPU." );
				sessionParams.device = firstCPUDevice();
			}

			m_session = std::make_unique<ccl::Session>( sessionParams, sceneParams );
			m_session->progress.set_update_callback( std::bind( &CyclesRenderer::progress, this ) );
			m_scene = m_session->scene.get();

			/// \todo Determine why this is here, or remove it.
			m_scene->camera->need_flags_update = true;
			m_scene->camera->update( m_scene );

			m_scene->background->set_transparent( true );

			if( m_renderType == RenderType::Interactive )
			{
				m_nodeDeleter = std::make_unique<NodeDeleter>( m_scene );
			}

			m_shaderCache = std::make_unique<ShaderCache>( m_scene );
			m_geometryCache = std::make_unique<GeometryCache>( m_scene, m_nodeDeleter.get() );
			m_attributesCache = std::make_unique<AttributesCache>( m_shaderCache.get() );
		}

		void clearUnused()
		{
			m_geometryCache->clearUnused();
			m_attributesCache->clearUnused();
		}

		void updateSceneObjects()
		{
			m_shaderCache->update();
		}

		void updateOptions()
		{
			if( !m_optionsChanged )
			{
				return;
			}

			std::unique_lock sceneLock( m_scene->mutex );

			// Options that map directly to sockets.

			for( auto &[name, option] : m_options )
			{
				if( boost::starts_with( name.string(), "cycles:film:" ) )
				{
					SocketAlgo::setSocket(
						m_scene->film, name.string().c_str() + 12,
						option.value ? reportedCast<const Data>( option.value.get(), "option", name ) : nullptr
					);
					option.modified = false;
				}
				else if( boost::starts_with( name.string(), "cycles:integrator:" ) )
				{
					SocketAlgo::setSocket(
						m_scene->integrator, name.string().c_str() + 18,
						option.value ? reportedCast<const Data>( option.value.get(), "option", name ) : nullptr
					);
					option.modified = false;
				}
				else if(
					boost::starts_with( name.string(), "cycles:background:" ) &&
					!boost::starts_with( name.string(), "cycles:background:visibility:" ) &&
					name.string() != "cycles:background:shader"
				)
				{
					SocketAlgo::setSocket(
						m_scene->background, name.string().c_str() + 18,
						option.value ? reportedCast<const Data>( option.value.get(), "option", name ) : nullptr
					);
					option.modified = false;
				}
			}

			// Integrator

			ccl::Integrator *integrator = m_scene->integrator;
			integrator->set_seed( optionValue<int>( g_seedOptionName, frame() ) );
			integrator->set_motion_blur( optionValue<bool>( g_sampleMotionOptionName, true ) );
			integrator->set_sampling_pattern( m_session->params.background ? ccl::SAMPLING_PATTERN_BLUE_NOISE_PURE : ccl::SAMPLING_PATTERN_BLUE_NOISE_FIRST );

			if( integrator->is_modified() )
			{
				integrator->tag_update( m_scene, ccl::Integrator::UPDATE_ALL );
			}

			// Background. Here we just deal with _options_ that affect
			// the background. Lights that affect the background are dealt
			// with in `updateBackground()`, which is where the final
			// modification check and `tag_update()` is done.

			ccl::Background *background = m_scene->background;

			auto it = m_options.find( g_backgroundShaderOptionName );
			if( it != m_options.end() && it->second.modified )
			{
				m_backgroundShader = nullptr;
				if( it->second.value )
				{
					if( const IECoreScene::ShaderNetwork *d = reportedCast<const IECoreScene::ShaderNetwork>( it->second.value.get(), "option", g_backgroundShaderOptionName ) )
					{
						// Need to release scene mutex temporarily, so that
						// `ShaderCache::get()` can acquire it.
						sceneLock.unlock();
						m_backgroundShader = m_shaderCache->get( d );
						sceneLock.lock();
					}
				}

				if( m_backgroundShader )
				{
					m_backgroundShader->shader()->tag_used( m_scene );
					background->set_shader( m_backgroundShader->shader() );
				}

				it->second.modified = false;
			}

			uint32_t backgroundVisibility = ccl::PATH_RAY_ALL_VISIBILITY;
			for( const auto &[name, rayType] : g_rayTypes )
			{
				if( !optionValue<bool>( "cycles:background:visibility:" + name, true ) )
				{
					backgroundVisibility = backgroundVisibility & ~rayType;
				}
			}
			background->set_visibility( backgroundVisibility );

			// Session and scene

			bool optionsModified = false;
			const ccl::SessionParams sessionParams = sessionParamsFromOptions( &optionsModified );
			const ccl::SceneParams sceneParams = sceneParamsFromOptions( &optionsModified);
			if( optionsModified && ( sessionParams.modified( m_session->params ) || sceneParams.modified( m_session->scene->params ) ) )
			{
				// Here `modified()` actually means "modified in a way that can't be changed
				// after constructing the session".
				IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", "Option edit requires a manual render restart" );
			}
			m_session->set_samples( sessionParams.samples );

			// Misc

			ccl::log_level_set( g_logLevels.at( optionValue<int>( g_logLevelOptionName, 0 ) ) );
			optionValue<int>( g_cryptomatteDepthOptionName, 0, &m_outputsChanged );

			m_optionsChanged = false;
		}

		void warnForUnusedOptions()
		{
			for( auto &[name, option] : m_options )
			{
				if( option.modified )
				{
					if( name.string().find( ':' ) == string::npos || boost::starts_with( name.string(), "user:" ) || boost::starts_with( name.string(), "cycles:" ) )
					{
						IECore::msg( IECore::Msg::Warning, "CyclesRenderer::option", fmt::format( "Unknown option \"{}\".", name.string() ) );
					}
					option.modified = false;
				}
			}
		}

		void updateBackground()
		{
			// Note : `updateOptions()` must be called prior to
			// `updateBackground()` so that `m_backgroundShader` is up to date.
			// This function is separate because background lights can be
			// modified without setting `m_optionsChanged`.

			std::lock_guard sceneLock( m_scene->mutex );

			if( !m_backgroundShader )
			{
				/// \todo Figure out how we can avoid repeating this check for
				/// every render. This might be much easier if attribute edits
				/// were performed by a renderer method instead of an ObjectInterface
				/// method. Or can we use `scene->light_manager->need_update()`?
				ccl::Light *backgroundLight = nullptr;
				for( ccl::Light *light : m_scene->lights )
				{
					if( light->get_light_type() == ccl::LIGHT_BACKGROUND )
					{
						backgroundLight = light;
						break;
					}
				}
				m_scene->background->set_shader( backgroundLight ? backgroundLight->get_shader() : m_scene->default_background );
				m_scene->background->set_lightgroup( backgroundLight ? backgroundLight->get_lightgroup() : ccl::ustring( "" ) );
			}

			// Note : this is also responsible for tagging any changes
			// made in `updateOptions()`.
			if( m_scene->background->is_modified() )
			{
				m_scene->background->tag_update( m_scene );
			}
		}

		void updateOutputs()
		{
			std::lock_guard sceneLock( m_scene->mutex );

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

			ccl::set<ccl::Pass *> passesToDelete;
			for( const auto &p : m_scene->passes )
			{
				passesToDelete.insert( p );
			}
			m_scene->delete_nodes( passesToDelete );

			ccl::CryptomatteType crypto = ccl::CRYPT_NONE;

			CompoundDataPtr layersData = new CompoundData();
			InternedString cryptoAsset;
			InternedString cryptoObject;
			InternedString cryptoMaterial;
			bool hasShadowCatcher = false;
			bool hasDenoise = false;
			const bool useIEDisplay = std::any_of(
				m_outputs.begin(), m_outputs.end(),
				[] ( const auto &output ) { return output.second->m_useIEDisplay; }
			);
			for( auto &coutput : m_outputs )
			{
				if( coutput.second->m_useIEDisplay != useIEDisplay )
				{
					/// \todo Support a mix of IEDisplay and file outputs. To do
					/// this we'd make a single `ccl::OutputDriver` subclass
					/// that could cope with both types.
					IECore::msg(
						IECore::Msg::Warning, "CyclesRenderer",
						fmt::format(
							"Ignoring output \"{}\" because it is not compatible with ieDisplay-based outputs",
							coutput.first.string()
						)
					);
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
			else
			{
				const int cryptomatteDepth = optionValue( g_cryptomatteDepthOptionName, 0 );
				film->set_cryptomatte_depth(
					// At least have 1 depth if there are crypto passes
					cryptomatteDepth ? ccl::divide_up( std::min( 16, cryptomatteDepth ), 2 ) : 1
				);
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
				if( coutput.second->m_useIEDisplay != useIEDisplay )
				{
					IECore::msg(
						IECore::Msg::Warning, "CyclesRenderer",
						fmt::format(
							"Ignoring output \"{}\" because it is not compatible with ieDisplay-based outputs",
							coutput.first.string()
						)
					);
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

			// When we reset the session, it cancels the internal PathTrace and
			// waits for it to finish. We need to do this _before_ calling
			// `set_output_driver()`, because otherwise the rendering threads
			// may try to send data to an output driver that was just destroyed
			// on the main thread.
			/// \todo `Renderer::pause()` really shouldn't return until after
			/// the PathTrace has been cancelled, so we shouldn't need to worry
			/// about that here.
			m_session->reset( m_session->params, m_bufferParams );

			film->set_cryptomatte_passes( crypto );
			film->set_use_approximate_shadow_catcher( !hasShadowCatcher );
			m_scene->integrator->set_use_denoise( hasDenoise );

			if( useIEDisplay )
			{
				m_session->set_output_driver( ccl::make_unique<IEDisplayOutputDriver>( displayWindow, dataWindow, layersData->readable() ) );
			}
			else
			{
				m_session->set_output_driver( ccl::make_unique<OIIOOutputDriver>( displayWindow, dataWindow, layersData->readable() ) );
			}

			m_outputsChanged = false;
		}

		void updateCamera( const std::string &sourceName, ccl::Camera *destination )
		{
			auto cameraIt = m_cameras.find( sourceName );
			if( cameraIt == m_cameras.end() )
			{
				if( !sourceName.empty() )
				{
					IECore::msg(
						IECore::Msg::Warning, "CyclesRenderer",
						fmt::format( "Camera \"{}\" does not exist", sourceName )
					);
				}
				cameraIt = m_cameras.find( "ieCoreCycles:defaultCamera" );
			}

			cameraIt->second->apply( destination );
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
				m_rendering = false;
			}
		}

		void resetCaches()
		{
			m_geometryCache.reset();
			m_shaderCache.reset();
			m_attributesCache.reset();
		}

		// Most `ccl::SessionParams` and `ccl::SceneParams` cannot be modified
		// after construction of the `ccl::Session`. And we are given those params
		// via `option()` after we ourselves have been constructed. So we can't create
		// the session in our constructor. Furthermore, _other_ options pertain to
		// properties of the `ccl::Scene`, and we can't have a scene without constructing a
		// session. Likewise, we can't implement `object()` until we have a scene.
		//
		// We deal with this as follows :
		//
		// 1. Implement `option()` to buffer everything into `m_options`. This is
		//    our "source of truth" for what the options should be.
		// 2. At the first point we _need_ a session (typically in a call to `object()`),
		//    we use `acquireSession()` to construct the session using the SessionParams
		//    defined by the options to date.
		// 3. In `updateOptions()` we apply all other options to their associated Cycles
		//    objects, just prior to rendering.
		// 4. In subsequent `render()` calls, transfer any further option edits to Cycles,
		//    warning if we encounter an edit that can't be applied to the SessionParams.
		//
		// This relies on clients to send all initial options before creating an object,
		// which fortunately is the case.
		struct Option { IECore::ConstObjectPtr value = nullptr; mutable bool modified = false; };
		std::unordered_map<IECore::InternedString, Option> m_options;
		bool m_optionsChanged;

		// Session.
		tbb::spin_mutex m_sessionAcquireMutex;
		std::unique_ptr<ccl::Session> m_session;
		ccl::Scene *m_scene;
		ccl::BufferParams m_bufferParams;
		std::unique_ptr<NodeDeleter> m_nodeDeleter;

		// Background shader
		CyclesShaderPtr m_backgroundShader;

		// IECoreScene::Renderer
		RenderType m_renderType;
		bool m_rendering;
		bool m_outputsChanged;

		// Logging
		IECore::MessageHandlerPtr m_messageHandler;
		string m_lastError;
		string m_lastStatus;
		double m_lastStatusTime;

		// Caches
		std::unique_ptr<ShaderCache> m_shaderCache;
		std::unique_ptr<GeometryCache> m_geometryCache;
		std::unique_ptr<AttributesCache> m_attributesCache;
		LightLinker m_lightLinker;

		// Outputs
		OutputMap m_outputs;

		// Cameras. We store these in Cortex form, and apply them to the scene's
		// camera in `updateCamera()`.
		using CameraMap = tbb::concurrent_unordered_map<std::string, ConstCyclesCameraPtr>;
		CameraMap m_cameras;

		// Registration with factory
		static Renderer::TypeDescription<CyclesRenderer> g_typeDescription;

};

IECoreScenePreview::Renderer::TypeDescription<CyclesRenderer> CyclesRenderer::g_typeDescription( "Cycles" );

} // namespace
