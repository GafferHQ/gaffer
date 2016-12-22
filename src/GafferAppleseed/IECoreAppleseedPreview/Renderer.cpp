//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Esteban Tovagliari. All rights reserved.
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
//      * Neither the name of John Haddon nor the names of
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

#include "tbb/atomic.h"
#include "tbb/concurrent_unordered_map.h"

#include "boost/algorithm/string.hpp"
#include "boost/filesystem/convenience.hpp"
#include "boost/filesystem/operations.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/smart_ptr/scoped_ptr.hpp"
#include "boost/thread.hpp"

#include "foundation/platform/timers.h"
#include "foundation/utility/log.h"
#include "foundation/utility/searchpaths.h"
#include "foundation/utility/stopwatch.h"
#include "foundation/utility/string.h"

#include "renderer/api/bsdf.h"
#include "renderer/api/camera.h"
#include "renderer/api/color.h"
#include "renderer/api/display.h"
#include "renderer/api/environment.h"
#include "renderer/api/environmentedf.h"
#include "renderer/api/environmentshader.h"
#include "renderer/api/frame.h"
#include "renderer/api/light.h"
#include "renderer/api/material.h"
#include "renderer/api/object.h"
#include "renderer/api/project.h"
#include "renderer/api/rendering.h"
#include "renderer/api/scene.h"
#include "renderer/api/shadergroup.h"
#include "renderer/api/surfaceshader.h"
#include "renderer/api/texture.h"
#include "renderer/api/utility.h"

#include "IECore/Camera.h"
#include "IECore/Light.h"
#include "IECore/MessageHandler.h"
#include "IECore/Shader.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/ObjectInterpolator.h"
#include "IECore/ObjectVector.h"

#include "IECoreAppleseed/CameraAlgo.h"
#include "IECoreAppleseed/ColorAlgo.h"
#include "IECoreAppleseed/EntityAlgo.h"
#include "IECoreAppleseed/MeshAlgo.h"
#include "IECoreAppleseed/MotionAlgo.h"
#include "IECoreAppleseed/ObjectAlgo.h"
#include "IECoreAppleseed/ParameterAlgo.h"
#include "IECoreAppleseed/ProgressTileCallback.h"
#include "IECoreAppleseed/RendererController.h"
#include "IECoreAppleseed/ShaderAlgo.h"
#include "IECoreAppleseed/TransformAlgo.h"

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"


namespace asf = foundation;
namespace asr = renderer;

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreAppleseed;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

const char *g_defaultMaterialName = "__defaultMaterial";

template<typename T>
T *reportedCast( const RunTimeTyped *v, const char *type, const InternedString &name )
{
	if( T *t = runTimeCast<T>( v ) )
	{
		return t;
	}

	msg( Msg::Warning, "AppleseedRenderer", boost::format( "Expected %s but got %s for %s \"%s\"." ) % T::staticTypeName() % v->typeName() % type % name.c_str() );
	return NULL;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// AppleseedEntity
//////////////////////////////////////////////////////////////////////////

namespace
{

// appleseed projects are not thread-safe.
// We need to protect project edits with locks.
typedef boost::mutex MutexType;
typedef boost::lock_guard<boost::mutex> LockGuardType;

MutexType g_projectMutex;
MutexType g_sceneMutex;
MutexType g_assembliesMutex;
MutexType g_assemblyInstancesMutex;
MutexType g_objectsMutex;
MutexType g_objectsInstancesMutex;
MutexType g_materialsMutex;
MutexType g_surfaceShadersMutex;
MutexType g_shaderGroupsMutex;
MutexType g_environmentMutex;
MutexType g_lightsMutex;
MutexType g_texturesMutex;
MutexType g_textureInstancesMutex;
MutexType g_colorsMutex;
MutexType g_camerasMutex;

/// Base class for all appleseed object handles.
class AppleseedEntity : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		const string &name() const
		{
			return m_name;
		}

	protected :

		AppleseedEntity( asr::Project &project, const string &name, bool interactiveRender )
			:	m_project( project ), m_name( name ), m_interactiveRender( interactiveRender )
		{
			m_mainAssembly = scene().assemblies().get_by_name( "assembly" );
		}

		bool isInteractiveRender() const
		{
			return m_interactiveRender;
		}

		const asr::Project &project() const
		{
			return m_project;
		}

		const asr::Scene &scene() const
		{
			return *m_project.get_scene();
		}

		const asr::Assembly &mainAssembly() const
		{
			return *m_mainAssembly;
		}

		void bumpMainAssemblyVersionId()
		{
			m_mainAssembly->bump_version_id();
		}

		void insertCamera( asf::auto_release_ptr<asr::Camera> camera )
		{
			LockGuardType lock( g_camerasMutex );
			m_project.get_scene()->cameras().insert( camera );
		}

		void removeCamera( asr::Camera *camera )
		{
			LockGuardType lock( g_camerasMutex );
			m_project.get_scene()->cameras().remove( camera );
		}

		void insertEnvironmentEDF( asf::auto_release_ptr<asr::EnvironmentEDF> environment )
		{
			LockGuardType lock( g_environmentMutex );

			const string envShaderName = string( environment->get_name() ) + "_shader";
			asr::EnvironmentShaderFactoryRegistrar factoryRegistrar;
			const asr::IEnvironmentShaderFactory *factory = factoryRegistrar.lookup( "edf_environment_shader" );
			asf::auto_release_ptr<asr::EnvironmentShader> envShader( factory->create( envShaderName.c_str(), asr::ParamArray() ) );
			envShader->get_parameters().insert( "environment_edf", environment->get_name() );
			m_project.get_scene()->environment_shaders().insert( envShader );

			m_project.get_scene()->environment_edfs().insert( environment );
		}

		void removeEnvironmentEDF( asr::EnvironmentEDF *environment )
		{
			LockGuardType lock( g_environmentMutex );

			const string envShaderName = string( environment->get_name() ) + "_shader";
			asr::EnvironmentShader *envShader = m_project.get_scene()->environment_shaders().get_by_name( envShaderName.c_str() );
			m_project.get_scene()->environment_shaders().remove( envShader );

			m_project.get_scene()->environment_edfs().remove( environment );
		}

		void insertAssembly( asf::auto_release_ptr<asr::Assembly> assembly )
		{
			LockGuardType lock( g_assembliesMutex );
			m_mainAssembly->assemblies().insert( assembly );
		}

		void removeAssembly( asr::Assembly *assembly )
		{
			LockGuardType lock( g_assembliesMutex );
			m_mainAssembly->assemblies().remove( assembly );
		}

		void insertAssemblyInstance( asf::auto_release_ptr<asr::AssemblyInstance> assemblyInstance )
		{
			LockGuardType lock( g_assemblyInstancesMutex );
			m_mainAssembly->assembly_instances().insert( assemblyInstance );
			bumpMainAssemblyVersionId();
		}

		void removeAssemblyInstance( asr::AssemblyInstance *assemblyInstance )
		{
			LockGuardType lock( g_assemblyInstancesMutex );
			m_mainAssembly->assembly_instances().remove( assemblyInstance );
			bumpMainAssemblyVersionId();
		}

		void insertObject( asf::auto_release_ptr<asr::Object> object )
		{
			LockGuardType lock( g_objectsMutex );
			m_mainAssembly->objects().insert( object );
		}

		void insertObjectInstance( asf::auto_release_ptr<asr::ObjectInstance> objectInstance )
		{
			LockGuardType lock( g_objectsInstancesMutex );
			m_mainAssembly->object_instances().insert( objectInstance );
		}

		void insertLight( asf::auto_release_ptr<asr::Light> light )
		{
			LockGuardType lock( g_lightsMutex );
			m_mainAssembly->lights().insert( light );
		}

		void removeLight( asr::Light *light )
		{
			LockGuardType lock( g_lightsMutex );
			m_mainAssembly->lights().remove( light );
		}

		void insertMaterial( asf::auto_release_ptr<asr::Material> material )
		{
			LockGuardType lock( g_materialsMutex );
			m_mainAssembly->materials().insert( material );
		}

		void removeMaterial( asr::Material *material )
		{
			LockGuardType lock( g_materialsMutex );
			m_mainAssembly->materials().remove( material );
		}

		void insertSurfaceShader( asf::auto_release_ptr<asr::SurfaceShader> surfaceShader )
		{
			LockGuardType lock( g_surfaceShadersMutex );
			m_mainAssembly->surface_shaders().insert( surfaceShader );
		}

		void removeSurfaceShader( asr::SurfaceShader *surfaceShader )
		{
			LockGuardType lock( g_surfaceShadersMutex );
			m_mainAssembly->surface_shaders().remove( surfaceShader );
		}

		void insertShaderGroup( asf::auto_release_ptr<asr::ShaderGroup> shaderGroup )
		{
			LockGuardType lock( g_shaderGroupsMutex );
			m_mainAssembly->shader_groups().insert( shaderGroup );
		}

		void removeShaderGroup( asr::ShaderGroup *shaderGroup )
		{
			LockGuardType lock( g_shaderGroupsMutex );
			m_mainAssembly->shader_groups().remove( shaderGroup );
		}

		string createSceneTexture( const string &name, const string &fileName, bool alphaMap = false )
		{
			return doCreateTextureEntity( *m_project.get_scene(), name, fileName, alphaMap );
		}

		void removeSceneTextures()
		{
			{
				LockGuardType lock( g_texturesMutex );
				doRemoveEntities( m_textures, m_project.get_scene()->textures() );
			}

			{
				LockGuardType lock( g_textureInstancesMutex );
				doRemoveEntities( m_textureInstances, m_project.get_scene()->texture_instances() );
			}
		}

		string createMainAssemblyTexture( const string &name, const string &fileName, bool alphaMap = false )
		{
			return doCreateTextureEntity( *m_mainAssembly, name, fileName, alphaMap );
		}

		void removeMainAssemblyTextures()
		{
			{
				LockGuardType lock( g_texturesMutex );
				doRemoveEntities( m_textures, m_mainAssembly->textures() );
			}

			{
				LockGuardType lock( g_textureInstancesMutex );
				doRemoveEntities( m_textureInstances, m_mainAssembly->texture_instances() );
			}
		}

		string createSceneColor( const string &name, const C3f &color )
		{
			return doCreateColorEntity( m_project.get_scene()->colors(), name, color );
		}

		void removeSceneColors()
		{
			LockGuardType lock( g_colorsMutex );
			doRemoveEntities( m_colors, m_project.get_scene()->colors() );
		}

		string createMainAssemblyColor( const string &name, const C3f &color )
		{
			return doCreateColorEntity( m_mainAssembly->colors(), name, color );
		}

		void removeMainAssemblyColors()
		{
			LockGuardType lock( g_colorsMutex );
			doRemoveEntities( m_colors, m_mainAssembly->colors() );
		}

		void resetFrame( const string &cameraName, const CompoundData *cameraParams )
		{
			assert( cameraParams );
			asr::ParamArray &params = m_project.get_frame()->get_parameters();

			// Resolution
			const V2iData *resolution = cameraParams->member<V2iData>( "resolution" );
			asf::Vector2i res( resolution->readable().x, resolution->readable().y );
			params.insert( "resolution", res );

			// Render region.
			if( const Box2iData *renderRegion = cameraParams->member<Box2iData>( "renderRegion" ) )
			{
				// For now, we don't do overscan.
				// We keep only the crop part of the render region.
				asf::AABB2u crop;
				crop.min[0] = asf::clamp( (int) renderRegion->readable().min.x, 0, res[0] - 1 );
				crop.min[1] = asf::clamp( (int) renderRegion->readable().min.y, 0, res[1] - 1 );
				crop.max[0] = asf::clamp( (int) renderRegion->readable().max.x, 0, res[0] - 1 );
				crop.max[1] = asf::clamp( (int) renderRegion->readable().max.y, 0, res[1] - 1 );
				params.insert( "crop_window", crop );
			}
			else
			{
				params.remove_path( "crop_window" );
			}

			// Choose the active camera.
			params.insert( "camera", cameraName.c_str() );

			// Replace the frame.
			m_project.set_frame( asr::FrameFactory().create( "beauty", params ) );
		}

		void resetFrame()
		{
			// Reset the frame to default values.
			asr::ParamArray &params = m_project.get_frame()->get_parameters();
			params.remove_path( "camera" );
			params.insert( "resolution", "640 480" );
			params.remove_path( "crop_window" );

			// Replace the frame.
			m_project.set_frame( asr::FrameFactory().create( "beauty", params ) );
		}

	private :

		template <typename EntityType, typename EntityContainer>
		void doRemoveEntities( vector<EntityType*> &entities, EntityContainer &container )
		{
			for( size_t i = 0, e = entities.size(); i < e; ++i )
			{
				container.remove( entities[i] );
			}

			entities.clear();
		}

		string doCreateTextureEntity( asr::BaseGroup &baseContainer, const string &name, const string &fileName, bool alphaMap )
		{
			string textureName;
			string textureInstanceName;

			// Create the texture.
			{
				asr::ParamArray params;
				params.insert( "filename", fileName.c_str() );
				params.insert( "color_space", "linear_rgb" );

				if( alphaMap )
				{
					params.insert( "alpha_mode", "detect" );
				}

				asf::auto_release_ptr<asr::Texture> texture;
				texture = asr::DiskTexture2dFactory().create( name.c_str(), params, m_project.search_paths() );

				LockGuardType lock( g_texturesMutex );
				textureName = EntityAlgo::insertEntityWithUniqueName( baseContainer.textures(), texture, name );
				m_textures.push_back( baseContainer.textures().get_by_index( baseContainer.textures().size() - 1 ) );
			}

			// Create the texture instance.
			{
				textureInstanceName = textureName + "_instance";
				asf::auto_release_ptr<asr::TextureInstance> textureInstance;
				textureInstance = asr::TextureInstanceFactory().create( textureInstanceName.c_str(), asr::ParamArray(), textureName.c_str() );

				LockGuardType lock( g_textureInstancesMutex );
				textureInstanceName = EntityAlgo::insertEntityWithUniqueName( baseContainer.texture_instances(), textureInstance, textureInstanceName.c_str() );
				m_textureInstances.push_back( baseContainer.texture_instances().get_by_index( baseContainer.texture_instances().size() - 1 ) );
			}

			return textureInstanceName;
		}

		string doCreateColorEntity( asr::ColorContainer &container, const string &name, const C3f &color )
		{
			LockGuardType lock( g_colorsMutex );
			pair<string, renderer::ColorEntity*> c = ColorAlgo::createColorEntity( container, color, name );

			if( c.second != NULL )
			{
				m_colors.push_back( c.second );
			}

			return c.first;
		}

		asr::Project &m_project;
		string m_name;
		bool m_interactiveRender;
		asr::Assembly *m_mainAssembly;

		// Containers to keep track of entities created by this entity
		// so that they can be removed when the main entity is destroyed.
		vector<asr::ColorEntity*> m_colors;
		vector<asr::Texture*> m_textures;
		vector<asr::TextureInstance*> m_textureInstances;
};

/// Appleseed object handle for unsupported objects.
class AppleseedNullObject : public AppleseedEntity
{

	public :

		AppleseedNullObject( asr::Project &project, const string &name, bool interactiveRender )
			:	AppleseedEntity( project, name, interactiveRender )
		{
		}

		virtual ~AppleseedNullObject()
		{
		}

		virtual void transform( const M44f &transform )
		{
		}

		virtual void transform( const vector<M44f> &samples, const vector<float> &times )
		{
		}

		virtual bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes )
		{
			return true;
		}

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// AppleseedShader
//////////////////////////////////////////////////////////////////////////

namespace
{

/// Appleseed shader handle.
class AppleseedShader : public AppleseedEntity
{

	public :

		AppleseedShader( asr::Project &project, const string &name, const ObjectVector *shader, bool interactiveRender )
			:	AppleseedEntity( project, name, interactiveRender )
		{
			asf::auto_release_ptr<asr::ShaderGroup> shaderGroup( ShaderAlgo::convert( shader ) );
			shaderGroup->set_name( name.c_str() );
			m_shaderGroup = shaderGroup.get();
			insertShaderGroup( shaderGroup );
		}

		virtual ~AppleseedShader()
		{
			if( isInteractiveRender() )
			{
				removeShaderGroup( m_shaderGroup );
			}
		}

		virtual void transform( const M44f &transform )
		{
		}

		virtual void transform( const vector<M44f> &samples, const vector<float> &times )
		{
		}

		virtual bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes )
		{
			return true;
		}

		const char *shaderGroupName() const
		{
			return m_shaderGroup->get_name();
		}

	private :

		asr::ShaderGroup *m_shaderGroup;
};

IE_CORE_DECLAREPTR( AppleseedShader )

class ShaderCache : public RefCounted
{
	public :

		ShaderCache( asr::Project &project, bool interactiveRender )
			: m_project( project )
			, m_isInteractive( interactiveRender )
		{
		}

		// Can be called concurrently with other get() calls.
		AppleseedShaderPtr get( const ObjectVector *shader )
		{
			Cache::accessor a;
			m_cache.insert( a, shader->Object::hash() );
			if( !a->second )
			{
				a->second = new AppleseedShader( m_project, shader->Object::hash().toString() + "_shadergroup", shader, m_isInteractive );
			}
			return a->second;
		}

		// Must not be called concurrently with anything.
		void clearUnused()
		{
			vector<MurmurHash> toErase;
			for( Cache::iterator it = m_cache.begin(), eIt = m_cache.end(); it != eIt; ++it )
			{
				if( it->second->refCount() == 1 )
				{
					// Only one reference - this is ours, so
					// nothing outside of the cache is using the
					// shader.
					toErase.push_back( it->first );
				}
			}
			for( vector<MurmurHash>::const_iterator it = toErase.begin(), eIt = toErase.end(); it != eIt; ++it )
			{
				m_cache.erase( *it );
			}
		}

	private :

		typedef tbb::concurrent_hash_map<MurmurHash, AppleseedShaderPtr> Cache;
		Cache m_cache;
		asr::Project &m_project;
		bool m_isInteractive;
};

IE_CORE_DECLAREPTR( ShaderCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// AppleseedAttributes
//////////////////////////////////////////////////////////////////////////

namespace
{

InternedString g_cameraVisibilityAttributeName( "as:visibility:camera" );
InternedString g_lightVisibilityAttributeName( "as:visibility:light" );
InternedString g_shadowVisibilityAttributeName( "as:visibility:shadow" );
InternedString g_diffuseVisibilityAttributeName( "as:visibility:diffuse" );
InternedString g_specularVisibilityAttributeName( "as:visibility:specular" );
InternedString g_glossyVisibilityAttributeName( "as:visibility:glossy" );

InternedString g_shadingSamplesAttributeName( "as:shading_samples" );
InternedString g_mediumPriorityAttributeName( "as:medium_priority" );
InternedString g_alphaMapAttributeName( "as:alpha_map" );

InternedString g_lightShaderAttributeName( "light" );
InternedString g_appleseedLightShaderAttributeName( "as:light" );

InternedString g_surfaceShaderAttributeName( "surface" );
InternedString g_oslSurfaceShaderAttributeName( "osl:surface" );
InternedString g_appleseedSurfaceShaderAttributeName( "as:surface" );

InternedString g_meshSmoothNormals( "as:smooth_normals" );
InternedString g_meshSmoothTangents( "as:smooth_tangents" );

class AppleseedAttributes : public IECoreScenePreview::Renderer::AttributesInterface
{

	public :

		explicit AppleseedAttributes( const CompoundObject *attributes, ShaderCache *shaderCache )
			:	m_shadingSamples( 1 ), m_mediumPriority( 0 ), m_meshSmoothNormals( false ), m_meshSmoothTangents( false )
		{
			updateVisibilityDictionary( g_cameraVisibilityAttributeName, attributes );
			updateVisibilityDictionary( g_lightVisibilityAttributeName, attributes );
			updateVisibilityDictionary( g_shadowVisibilityAttributeName, attributes );
			updateVisibilityDictionary( g_diffuseVisibilityAttributeName, attributes );
			updateVisibilityDictionary( g_specularVisibilityAttributeName, attributes );
			updateVisibilityDictionary( g_glossyVisibilityAttributeName, attributes );

			if( const IntData *d = attribute<IntData>( g_mediumPriorityAttributeName, attributes ) )
			{
				m_mediumPriority = d->readable();
			}

			if( const IntData *d = attribute<IntData>( g_shadingSamplesAttributeName, attributes ) )
			{
				m_shadingSamples = d->readable();
			}

			if( const StringData *d = attribute<StringData>( g_alphaMapAttributeName, attributes ) )
			{
				m_alphaMap = d->readable();
			}

			if( const BoolData *d = attribute<BoolData>( g_meshSmoothNormals, attributes ) )
			{
				m_meshSmoothNormals = d->readable();
			}

			if( const BoolData *d = attribute<BoolData>( g_meshSmoothTangents, attributes ) )
			{
				m_meshSmoothTangents = d->readable();
			}

			m_lightShader = attribute<ObjectVector>( g_appleseedLightShaderAttributeName, attributes );
			m_lightShader = m_lightShader ? m_lightShader : attribute<ObjectVector>( g_lightShaderAttributeName, attributes );

			const ObjectVector *surfaceShaderAttribute = attribute<ObjectVector>( g_appleseedSurfaceShaderAttributeName, attributes );
			surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<ObjectVector>( g_oslSurfaceShaderAttributeName, attributes );
			surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<ObjectVector>( g_surfaceShaderAttributeName, attributes );

			if( surfaceShaderAttribute )
			{
				m_shaderGroup = shaderCache->get( surfaceShaderAttribute );
			}
		}

		void appendToHash( MurmurHash &hash ) const
		{
			hash.append( m_shadingSamples );
			hash.append( m_mediumPriority );
			hash.append( m_alphaMap );

			asf::StringDictionary::const_iterator it( m_visibilityDictionary.strings().begin() );
			asf::StringDictionary::const_iterator e( m_visibilityDictionary.strings().end() );
			for( ; it != e; ++it )
			{
				hash.append( it.key() );
				hash.append( it.value() );
			}

			hash.append( m_meshSmoothNormals );
			hash.append( m_meshSmoothTangents );

			if( m_shaderGroup )
			{
				hash.append( m_shaderGroup->name() );
			}
		}

		int m_shadingSamples;
		int m_mediumPriority;
		string m_alphaMap;
		asf::Dictionary m_visibilityDictionary;
		bool m_meshSmoothNormals;
		bool m_meshSmoothTangents;
		ConstObjectVectorPtr m_lightShader;
		AppleseedShaderPtr m_shaderGroup;

	private :

		template<typename T>
		const T *attribute( const InternedString &name, const CompoundObject *attributes )
		{
			CompoundObject::ObjectMap::const_iterator it = attributes->members().find( name );
			if( it == attributes->members().end() )
			{
				return NULL;
			}
			return reportedCast<const T>( it->second.get(), "attribute", name );
		}

		void updateVisibilityDictionary( const InternedString &name, const CompoundObject *attributes )
		{
			string flag_name( name, 14, string::npos );
			if( const BoolData *f = attribute<BoolData>( name, attributes ) )
			{
				m_visibilityDictionary.insert( flag_name.c_str(), f->readable() ? "true" : "false" );
			}
			else
			{
				m_visibilityDictionary.insert( flag_name.c_str(), "true");
			}
		}
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// AppleseedCamera
//////////////////////////////////////////////////////////////////////////

namespace
{

/// Appleseed camera handle.
class AppleseedCamera : public AppleseedEntity
{

	public :

		AppleseedCamera( asr::Project &project, const string &name, Camera *camera, const IECoreScenePreview::Renderer::AttributesInterface *attributes, bool activeCamera, bool interactive )
			:	AppleseedEntity( project, name, interactive ), m_activeCamera( activeCamera )
		{
			asf::auto_release_ptr<asr::Camera> appleseedCamera( CameraAlgo::convert( camera ) );
			appleseedCamera->set_name( name.c_str() );
			m_camera = appleseedCamera.get();
			insertCamera( appleseedCamera );

			if( m_activeCamera )
			{
				resetFrame( name, camera->parametersData() );
			}
		}

		virtual ~AppleseedCamera()
		{
			if( isInteractiveRender() )
			{
				removeCamera( m_camera );

				if( m_activeCamera )
				{
					resetFrame();
				}
			}
		}

		virtual void transform( const M44f &transform )
		{
			TransformAlgo::makeTransformSequence( transform, m_camera->transform_sequence() );
		}

		virtual void transform( const vector<M44f> &samples, const vector<float> &times )
		{
			TransformAlgo::makeTransformSequence( times, samples, m_camera->transform_sequence() );
		}

		virtual bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes )
		{
			// todo: check if this has to be implemented...
			return true;
		}

	private :

		asr::Camera *m_camera;
		bool m_activeCamera;
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// InstanceCache
//////////////////////////////////////////////////////////////////////////

namespace
{

/// A primitive that can be instanced.
class InstanceMaster : public IECore::RefCounted
{
	public :

		InstanceMaster(const string &name, asr::Assembly *mainAssembly ) : m_name( name ), m_mainAssembly( mainAssembly )
		{
			assert( m_mainAssembly );
			m_numInstances = 0;
		}

		void movePrimitiveToAssembly()
		{
			assert( m_numInstances > 0 );

			// Move the object into its own assembly if needed, so that it can be instanced.
			const string assemblyName = m_name + "_assembly";
			if( m_mainAssembly->assemblies().get_by_name( assemblyName.c_str() ) == 0 )
			{
				// Create an assembly for the object.
				asf::auto_release_ptr<asr::Assembly> ass( asr::AssemblyFactory().create( assemblyName.c_str() ) );

				// Move the object to the assembly.
				asr::Object *obj = m_mainAssembly->objects().get_by_name( m_name.c_str() );
				asf::auto_release_ptr<asr::Object> o = m_mainAssembly->objects().remove( obj );
				ass->objects().insert( o );

				// Move the object instance, minus the transform, to the object assembly.
				string objectInstanceName = m_name + "_instance";
				asr::ObjectInstance *objI = m_mainAssembly->object_instances().get_by_name( objectInstanceName.c_str() );
				asf::auto_release_ptr<asr::ObjectInstance> oi = m_mainAssembly->object_instances().remove( objI );
				const asf::Transformd transform = oi->get_transform();

				// To remove the transform, we have to create a new object instance.
				oi = asr::ObjectInstanceFactory::create( oi->get_name(), oi->get_parameters(), oi->get_object_name(), asf::Transformd::identity(), oi->get_front_material_mappings(), oi->get_back_material_mappings() );
				ass->object_instances().insert( oi );

				// Create an instance of the object assembly, with the transform from the object instance.
				string assemblyInstanceName = assemblyName + "_instance";
				asf::auto_release_ptr<asr::AssemblyInstance> assInstance( asr::AssemblyInstanceFactory::create( assemblyInstanceName.c_str(), asr::ParamArray(), assemblyName.c_str() ) );
				assInstance->transform_sequence().set_transform( 0.0f, transform );

				// Add the assembly and assembly instance to the main assembly.
				m_mainAssembly->assemblies().insert( ass );
				m_mainAssembly->assembly_instances().insert( assInstance );
			}
		}

		const string m_name;
		asr::Assembly *m_mainAssembly;
		tbb::atomic<int> m_numInstances;

};

IE_CORE_DECLAREPTR( InstanceMaster )

/// Appleseed primitive instance handle.
class AppleseedInstance : public AppleseedEntity
{

	public :

		AppleseedInstance( asr::Project &project, const string &name, const string &masterName )
			:	AppleseedEntity( project, name, false ), m_masterName( masterName )
		{
		}

		virtual ~AppleseedInstance()
		{
			// Create an instance of the master primitive assembly and add it to the main assembly.
			string assemblyName = m_masterName + "_assembly";
			string assemblyInstanceName = name() + "_assembly_instance";
			asf::auto_release_ptr<asr::AssemblyInstance> assInstance( asr::AssemblyInstanceFactory::create( assemblyInstanceName.c_str(), asr::ParamArray(), assemblyName.c_str() ) );
			assInstance->transform_sequence() = m_transformSequence;
			insertAssemblyInstance( assInstance );
		}

		virtual void transform( const M44f &transform )
		{
			TransformAlgo::makeTransformSequence( transform, m_transformSequence );
		}

		virtual void transform( const vector<M44f> &samples, const vector<float> &times )
		{
			TransformAlgo::makeTransformSequence( times, samples, m_transformSequence );
		}

		virtual bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes )
		{
			// We reuse the attributes of the master primitive.
			return true;
		}

	private :

		const string m_masterName;
		asr::TransformSequence m_transformSequence;

};

class InstanceMasterCache : public IECore::RefCounted
{

	public :

		void movePrimitivesToAssemblies()
		{
			for( Cache::iterator it = m_cache.begin(), eIt = m_cache.end(); it != eIt; ++it )
			{
				if( it->second->m_numInstances > 0 )
				{
					it->second->movePrimitiveToAssembly();
				}
			}
		}

		InstanceMasterPtr get( const MurmurHash &hash, const string &name, asr::Assembly *mainAssembly )
		{
			Cache::accessor a;
			m_cache.insert( a, hash );
			if( !a->second )
			{
				a->second = new InstanceMaster( name, mainAssembly );
			}
			else
			{
				a->second->m_numInstances++;
			}

			return a->second;
		}

	private :

		typedef tbb::concurrent_hash_map<IECore::MurmurHash, InstanceMasterPtr> Cache;
		Cache m_cache;
};

IE_CORE_DECLAREPTR( InstanceMasterCache )

} // namespace

//////////////////////////////////////////////////////////////////////////
// AppleseedPrimitive
//////////////////////////////////////////////////////////////////////////

namespace
{

/// Appleseed mesh primitive handle.
class AppleseedPrimitive : public AppleseedEntity
{

	public :

		AppleseedPrimitive( asr::Project &project, const string &name, const Object *object, const IECoreScenePreview::Renderer::AttributesInterface *attributes, bool interactiveRender )
			:	AppleseedEntity( project, name, interactiveRender )
		{
			init();

			// Create the object.
			m_object = ObjectAlgo::convert( object );
			m_object->set_name( name.c_str() );

			// Compute smooth normals and tangents if needed.
			const AppleseedAttributes *appleseedAttributes = static_cast<const AppleseedAttributes*>( attributes );
			computeSmoothNormalsAndTangents( appleseedAttributes->m_meshSmoothNormals, appleseedAttributes->m_meshSmoothTangents);

			// Create the object instance.
			createObjectInstance( name );

			// When doing interactive rendering, we put objects into its own assembly
			// to allow editing the object transform.
			if( isInteractiveRender() )
			{
				createObjectAssembly();
			}

			AppleseedPrimitive::attributes( attributes );
		}

		AppleseedPrimitive( asr::Project &project, const string &name, const vector<const Object *> &samples, const vector<float> &times, float shutterOpenTime, float shutterCloseTime, const IECoreScenePreview::Renderer::AttributesInterface *attributes, bool interactiveRender )
			:	AppleseedEntity( project, name, interactiveRender )
		{
			init();

			// Create the object.
			m_object = ObjectAlgo::convert( samples, times, shutterOpenTime, shutterCloseTime );
			m_object->set_name( name.c_str() );

			// Compute smooth normals and tangents if needed.
			const AppleseedAttributes *appleseedAttributes = static_cast<const AppleseedAttributes*>( attributes );
			computeSmoothNormalsAndTangents( appleseedAttributes->m_meshSmoothNormals, appleseedAttributes->m_meshSmoothTangents );

			// Create the object instance.
			createObjectInstance( name );

			// When doing interactive rendering, we put objects into its own assembly
			// to allow editing the object transform.
			if( isInteractiveRender() )
			{
				createObjectAssembly();
			}

			AppleseedPrimitive::attributes( attributes );
		}

		AppleseedPrimitive( asr::Project &project, const string &name, const Object *object, const IECoreScenePreview::Renderer::AttributesInterface *attributes, const boost::filesystem::path &projectPath )
			:	AppleseedEntity( project, name, false )
		{
			init();

			vector<const Object *> samples;
			samples.push_back( object );
			createSceneDescriptionObject( samples, projectPath, attributes );
		}

		AppleseedPrimitive( asr::Project &project, const string &name, const vector<const Object *> &samples, const vector<float> &times, float shutterOpenTime, float shutterCloseTime, const IECoreScenePreview::Renderer::AttributesInterface *attributes, const boost::filesystem::path &projectPath )
			:	AppleseedEntity( project, name, false )
		{
			init();

			// Check if we need to resample the shape keys.
			if( MotionAlgo::checkTimeSamples( times, shutterOpenTime, shutterCloseTime ) )
			{
				vector<ObjectPtr> resampled;
				MotionAlgo::resamplePrimitiveKeys( samples, times, shutterOpenTime, shutterCloseTime, resampled );
				createSceneDescriptionObject( resampled, projectPath, attributes );
			}
			else
			{
				createSceneDescriptionObject( samples, projectPath, attributes );
			}
		}

		virtual ~AppleseedPrimitive()
		{
			if( isInteractiveRender() )
			{
				removeAssemblyInstance( m_objectAssemblyInstance );
				removeAssembly( m_objectAssembly );
				clearMaterial();
				return;
			}

			// Check if the object has transformation motion blur.
			m_transformSequence.optimize();
			if( m_transformSequence.size() > 1 )
			{
				// The object has transformation motion blur.
				// We have to create an assembly for it.
				string assemblyName = name() + "_assembly";
				asf::auto_release_ptr<asr::Assembly> ass( asr::AssemblyFactory().create( assemblyName.c_str() ) );

				// Add the object to the object assembly.
				ass->objects().insert( asf::auto_release_ptr<asr::Object>( m_object ) );

				// Add the object instance to the object assembly.
				ass->object_instances().insert( asf::auto_release_ptr<asr::ObjectInstance>( m_objectInstance ) );

				// Add the object assembly to the main assembly.
				insertAssembly( ass );

				// Create an instance of the object assembly and add it to the main assembly.
				string assemblyInstanceName = assemblyName + "_instance";
				asf::auto_release_ptr<asr::AssemblyInstance> assInstance( asr::AssemblyInstanceFactory::create( assemblyInstanceName.c_str(), asr::ParamArray(), assemblyName.c_str() ) );
				assInstance->transform_sequence() = m_transformSequence;
				insertAssemblyInstance( assInstance );
			}
			else
			{
				// The object does not have transformation motion blur.
				// In this case, it's more efficient to put it in the main assembly.
				insertObject( asf::auto_release_ptr<asr::Object>( m_object ) );

				// To update the transform, we have to create a new object instance.
				asf::auto_release_ptr<asr::ObjectInstance> newObjInstance;
				newObjInstance = asr::ObjectInstanceFactory::create( m_objectInstance->get_name(), m_objectInstance->get_parameters(), m_objectInstance->get_object_name(), m_transformSequence.get_earliest_transform(), m_objectInstance->get_front_material_mappings(), m_objectInstance->get_back_material_mappings() );
				m_objectInstance->release();
				m_objectInstance = newObjInstance.get();
				insertObjectInstance( newObjInstance );
			}
		}

		virtual void transform( const M44f &transform )
		{
			if( isInteractiveRender() )
			{
				TransformAlgo::makeTransformSequence( transform, m_objectAssemblyInstance->transform_sequence() );
				bumpMainAssemblyVersionId();
			}
			else
			{
				TransformAlgo::makeTransformSequence( transform, m_transformSequence );
			}
		}

		virtual void transform( const vector<M44f> &samples, const vector<float> &times )
		{
			if( isInteractiveRender() )
			{
				TransformAlgo::makeTransformSequence( times, samples, m_objectAssemblyInstance->transform_sequence() );
				bumpMainAssemblyVersionId();
			}
			else
			{
				TransformAlgo::makeTransformSequence( times, samples, m_transformSequence );
			}
		}

		virtual bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes )
		{
			if( isInteractiveRender() )
			{
				// Remove any previous material.
				clearMaterial();
			}

			const AppleseedAttributes *appleseedAttributes = static_cast<const AppleseedAttributes*>( attributes );

			if( appleseedAttributes->m_shaderGroup )
			{
				// Save a reference to the OSL shader group.
				m_shaderGroup = appleseedAttributes->m_shaderGroup;

				// Create a surface shader.
				string surfaceShaderName = name() + "_surface_shader";
				asr::ParamArray params;
				params.insert( "front_lighting_samples", appleseedAttributes->m_shadingSamples );
				params.insert( "back_lighting_samples", appleseedAttributes->m_shadingSamples );

				asf::auto_release_ptr<asr::SurfaceShader> surfaceShader;
				surfaceShader = asr::PhysicalSurfaceShaderFactory().create( surfaceShaderName.c_str(), params );
				m_surfaceShader = surfaceShader.get();
				insertSurfaceShader( surfaceShader );

				// Create a material.
				string materialName = name() + "_material";
				params.clear();
				params.insert( "surface_shader", surfaceShaderName.c_str() );
				params.insert( "osl_surface", appleseedAttributes->m_shaderGroup->shaderGroupName() );

				asf::auto_release_ptr<asr::Material> material;
				material = asr::OSLMaterialFactory().create( materialName.c_str(), params );
				m_material = material.get();
				insertMaterial( material );

				// Assign the material to the object instance.
				m_objectInstance->assign_material( "default", asr::ObjectInstance::FrontSide, materialName.c_str() );
				m_objectInstance->assign_material( "default", asr::ObjectInstance::BackSide, materialName.c_str() );
			}
			else
			{
				// No shader assigned. Assign the default material to the object instance.
				m_objectInstance->assign_material( "default", asr::ObjectInstance::FrontSide, g_defaultMaterialName );
				m_objectInstance->assign_material( "default", asr::ObjectInstance::BackSide, g_defaultMaterialName );
			}

			if( !appleseedAttributes->m_alphaMap.empty() )
			{
				string alphaMapTexture = createMainAssemblyTexture( name() + "_alpha_map", appleseedAttributes->m_alphaMap, true );
				m_object->get_parameters().insert( "alpha_map", alphaMapTexture.c_str() );
			}

			// Set the object instance params.
			m_objectInstance->get_parameters().insert( "medium_priority", appleseedAttributes->m_mediumPriority );
			m_objectInstance->get_parameters().insert( "visibility", appleseedAttributes->m_visibilityDictionary );

			// todo: support edits of smooth normals and tangents attribute.
			return true;
		}

	private :

		void init()
		{
			m_objectAssembly = NULL;
			m_objectAssemblyInstance = NULL;
			m_object = NULL;
			m_objectInstance = NULL;
			m_surfaceShader = NULL;
			m_material = NULL;
		}

		void clearMaterial()
		{
			removeMainAssemblyTextures();

			if( m_surfaceShader )
			{
				removeSurfaceShader( m_surfaceShader );
				m_surfaceShader = NULL;
			}

			m_shaderGroup.reset();

			if( m_material )
			{
				removeMaterial( m_material );
				m_material = NULL;
			}
		}

		void computeSmoothNormalsAndTangents( bool normals, bool tangents )
		{
			asr::MeshObject *meshObject = static_cast<asr::MeshObject*>( m_object );

			if( normals && meshObject->get_vertex_normal_count() == 0 )
			{
				asr::compute_smooth_vertex_normals( *meshObject );
			}

			if( tangents && meshObject->get_vertex_tangent_count() == 0 )
			{
				asr::compute_smooth_vertex_tangents( *meshObject );
			}
		}

		void createObjectInstance( const string &objectName )
		{
			string objectInstanceName = name() + "_instance";
			asf::StringDictionary materials;
			materials.insert( "default", g_defaultMaterialName );
			m_objectInstance = asr::ObjectInstanceFactory::create( objectInstanceName.c_str(), asr::ParamArray(), objectName.c_str(), asf::Transformd::identity(), materials, materials ).release();
		}

		void createObjectAssembly()
		{
			// Create an assembly for the object.
			string assemblyName = name() + "_assembly";
			asf::auto_release_ptr<asr::Assembly> ass( asr::AssemblyFactory().create( assemblyName.c_str() ) );

			// Add the object to the object assembly.
			ass->objects().insert( asf::auto_release_ptr<asr::Object>( m_object ) );

			// Add the object instance to the object assembly.
			ass->object_instances().insert( asf::auto_release_ptr<asr::ObjectInstance>( m_objectInstance ) );

			// Add the object assembly to the main assembly.
			m_objectAssembly = ass.get();
			insertAssembly( ass );

			// Create an instance of the object assembly and
			// add it to the main assembly.
			string assemblyInstanceName = assemblyName + "_instance";
			asf::auto_release_ptr<asr::AssemblyInstance> assInstance( asr::AssemblyInstanceFactory::create( assemblyInstanceName.c_str(), asr::ParamArray(), m_objectAssembly->get_name() ) );
			m_objectAssemblyInstance = assInstance.get();
			insertAssemblyInstance( assInstance );
		}

		const char *filenameExtensionForObject( const Object *object ) const
		{
			return ".binarymesh";
		}

		void writeGeomFile( const Object *object, const boost::filesystem::path &path ) const
		{
			asf::auto_release_ptr<asr::Object> obj( ObjectAlgo::convert( object ) );

			// Write the mesh to a binarymesh file.
			const asr::MeshObject *meshObj = static_cast<const asr::MeshObject *>( obj.get() );
			if( !asr::MeshObjectWriter::write( *meshObj, "mesh", path.string().c_str() ) )
			{
				msg( Msg::Warning, "AppleseedRenderer::object", "Couldn't save mesh primitive." );
			}
		}

		template<class ObjectType>
		void createSceneDescriptionObject( const vector<ObjectType> &samples, const boost::filesystem::path &projectPath, const IECoreScenePreview::Renderer::AttributesInterface *attributes )
		{
			const AppleseedAttributes *appleseedAttributes = static_cast<const AppleseedAttributes*>( attributes );

			asr::ParamArray params;
			asf::Dictionary fileNames;

			for( size_t i = 0, e = samples.size() ; i < e; ++i )
			{
				const Object &object = *samples[i];
				MurmurHash hash = object.hash();

				string fileName = string( "_geometry/" ) + hash.toString() + filenameExtensionForObject( &object );
				boost::filesystem::path p = projectPath / fileName;

				// todo: can we do something better than locking here?
				{
					boost::lock_guard<boost::mutex> lock( g_geomFilesMutex );

					// Write a geom file for the object if needed.
					if( !boost::filesystem::exists( p ) )
					{
						writeGeomFile( &object, p );
					}
				}

				// Store the filename into the object params.
				if( samples.size() > 1 )
				{
					// Deforming: add the key to filename dictionary.
					fileNames.insert( boost::lexical_cast<string>( i ), fileName );
				}
				else
				{
					// Static: add the filename directly to the params.
					params.insert( "filename", fileName );
				}
			}

			// Add the keyframes dictionary to the params if needed.
			if( samples.size() > 1 )
			{
				params.insert( "filename", fileNames );
			}

			// Add params to compute smooth normals and tangents if needed.
			if( appleseedAttributes->m_meshSmoothNormals )
			{
				params.insert( "compute_smooth_normals", ".*" );
			}

			if( appleseedAttributes->m_meshSmoothTangents )
			{
				params.insert( "compute_smooth_tangents", ".*" );
			}

			// Create a mesh object referencing the geom file.
			m_object = asr::MeshObjectFactory().create( name().c_str(), params ).release();

			// Create the object instance.
			createObjectInstance( name() + ".mesh" );

			AppleseedPrimitive::attributes( attributes );
		}

		// Used to protect mesh file writting for scene description renders.
		static boost::mutex g_geomFilesMutex;

		asr::TransformSequence m_transformSequence;

		asr::Assembly *m_objectAssembly;
		asr::AssemblyInstance *m_objectAssemblyInstance;

		asr::Object *m_object;
		asr::ObjectInstance *m_objectInstance;

		AppleseedShaderPtr m_shaderGroup;
		asr::SurfaceShader *m_surfaceShader;
		asr::Material *m_material;

};

boost::mutex AppleseedPrimitive::g_geomFilesMutex;

} // namespace

//////////////////////////////////////////////////////////////////////////
// AppleseedLight
//////////////////////////////////////////////////////////////////////////

namespace
{

bool isEnvironmentLight( const string &lightModel )
{
	asr::EnvironmentEDFFactoryRegistrar envFactoryRegistrar;
	return envFactoryRegistrar.lookup( lightModel.c_str() ) != NULL;
}

bool isDeltaLight( const string &lightModel )
{
	asr::LightFactoryRegistrar lightFactoryRegistrar;
	return lightFactoryRegistrar.lookup( lightModel.c_str() ) != NULL;
}

string getLightModel( const ObjectVector* lightShader )
{
	for( ObjectVector::MemberContainer::const_iterator it = lightShader->members().begin(), eIt = lightShader->members().end(); it != eIt; ++it )
	{
		if( const Shader *shader = runTimeCast<const Shader>( it->get() ) )
		{
			return shader->getName();
		}
		else if( const Light *light = runTimeCast<const Light>( it->get() ) )
		{
			string lightModel = light->getName();
			if( boost::starts_with( lightModel, "as:" ) )
			{
				return string( lightModel, 3, string::npos );
			}
		}
	}

	return string();
}

const CompoundDataMap *getLightParameters( const ObjectVector* lightShader )
{
	for( ObjectVector::MemberContainer::const_iterator it = lightShader->members().begin(), eIt = lightShader->members().end(); it != eIt; ++it )
	{
		if( const Shader *shader = runTimeCast<const Shader>( it->get() ) )
		{
			return &shader->parameters();
		}
		else if( const Light *light = runTimeCast<const Light>( it->get() ) )
		{
			return &light->parameters();
		}
	}

	return NULL;
}

/// Appleseed light handle base class.
class AppleseedLight : public AppleseedEntity
{
	protected :

		AppleseedLight( asr::Project &project, const string &name, const IECoreScenePreview::Renderer::AttributesInterface *attributes, bool interactive )
			:	AppleseedEntity( project, name, interactive )
		{
		}

		void convertLightParams( const CompoundDataMap *parameters, asr::ParamArray &params, bool isEnvironment )
		{
			for( CompoundDataMap::const_iterator it( parameters->begin() ), eIt( parameters->end() ); it != eIt; ++it )
			{
				string paramName = it->first.value();
				ConstDataPtr paramValue = it->second;

				// for environment lights convert the radiance_map parameter to a texture, instead of a color.
				if( isEnvironment && paramName == "radiance_map" )
				{
					if( paramValue->typeId() != StringDataTypeId )
					{
						msg( MessageHandler::Warning, "AppleseedRenderer::light", "Expected radianceMap parameter to be a string" );
						continue;
					}

					string textureName = name() + "." + paramName;
					const string &fileName = static_cast<const StringData*>( paramValue.get() )->readable();
					string textureInstanceName = createSceneTexture( textureName, fileName );
					params.insert( "radiance", textureInstanceName.c_str() );
				}
				else
				{
					if( paramValue->typeId() == Color3fDataTypeId )
					{
						string colorName = name() + "." + paramName;
						const Color3f &color = static_cast<const Color3fData*>( paramValue.get() )->readable();
						colorName = createSceneColor( colorName, color );
						params.insert( paramName.c_str(), colorName.c_str() );
					}
					else
					{
						params.insert( paramName.c_str(), ParameterAlgo::dataToString( paramValue ) );
					}
				}
			}
		}
};

/// Appleseed environment light handle.
class AppleseedEnvironmentLight : public AppleseedLight
{
	public :

		AppleseedEnvironmentLight( asr::Project &project, const string &name,  const IECoreScenePreview::Renderer::AttributesInterface *attributes, bool interactive )
			:	AppleseedLight( project, name, attributes, interactive )
			,	m_environment( NULL )
		{
			AppleseedEnvironmentLight::attributes( attributes );
		}

		virtual ~AppleseedEnvironmentLight()
		{
			if( isInteractiveRender() )
			{
				removeEnvironmentEntities();
			}
		}

		virtual void transform( const M44f &transform )
		{
			TransformAlgo::makeTransformSequence( transform, m_transformSequence );

			if( m_environment )
			{
				m_environment->transform_sequence() = m_transformSequence;
			}
		}

		virtual void transform( const vector<M44f> &samples, const vector<float> &times )
		{
			TransformAlgo::makeTransformSequence( times, samples, m_transformSequence );

			if( m_environment )
			{
				m_environment->transform_sequence() = m_transformSequence;
			}
		}

		virtual bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes )
		{
			// Remove any previously created environment.
			removeEnvironmentEntities();

			// Create a new environment.
			const AppleseedAttributes *appleseedAttributes = static_cast<const AppleseedAttributes*>( attributes );
			if( appleseedAttributes && appleseedAttributes->m_lightShader )
			{
				string lightModel = getLightModel( appleseedAttributes->m_lightShader.get() );
				asr::EnvironmentEDFFactoryRegistrar envFactoryRegistrar;
				if( const asr::IEnvironmentEDFFactory *factory = envFactoryRegistrar.lookup( lightModel.c_str() ) )
				{
					asf::auto_release_ptr<asr::EnvironmentEDF> envLight( factory->create( name().c_str(), asr::ParamArray() ) );
					envLight->transform_sequence() = m_transformSequence;

					const CompoundDataMap *lightParams = getLightParameters( appleseedAttributes->m_lightShader.get() );
					assert( lightParams );
					convertLightParams( lightParams, envLight->get_parameters(), true );

					m_environment = envLight.get();
					insertEnvironmentEDF( envLight );
				}
			}

			return true;
		}

	private :

		void removeEnvironmentEntities()
		{
			if( m_environment )
			{
				removeEnvironmentEDF( m_environment );
				removeSceneTextures();
				removeSceneColors();
				m_environment = 0;
			}
		}

		asr::EnvironmentEDF *m_environment;
		asr::TransformSequence m_transformSequence;
};

/// Appleseed light handle.
class AppleseedDeltaLight : public AppleseedLight
{
	public :

		AppleseedDeltaLight( asr::Project &project, const string &name, const IECoreScenePreview::Renderer::AttributesInterface *attributes, bool interactive )
			:	AppleseedLight( project, name, attributes, interactive ) , m_light( NULL ) , m_transform( asf::Transformd::identity() )
		{
			AppleseedDeltaLight::attributes( attributes );
		}

		virtual ~AppleseedDeltaLight()
		{
			if( isInteractiveRender() )
			{
				removeLightEntities();
			}
		}

		virtual void transform( const M44f &transform )
		{
			TransformAlgo::makeTransform( transform, m_transform );

			if( m_light )
			{
				m_light->set_transform( m_transform );
			}
		}

		virtual void transform( const vector<M44f> &samples, const vector<float> &times )
		{
			// appleseed does not support light transform motion blur yet.
			transform(samples[0]);
		}

		virtual bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes )
		{
			// Remove any previously created light.
			removeLightEntities();

			// Create a new light.
			const AppleseedAttributes *appleseedAttributes = static_cast<const AppleseedAttributes*>( attributes );

			if( appleseedAttributes && appleseedAttributes->m_lightShader )
			{
				string lightModel = getLightModel( appleseedAttributes->m_lightShader.get() );

				asr::LightFactoryRegistrar lightFactoryRegistrar;
				if( const asr::ILightFactory *factory = lightFactoryRegistrar.lookup( lightModel.c_str() ) )
				{
					asf::auto_release_ptr<asr::Light> light( factory->create( name().c_str(), asr::ParamArray() ) );
					light->set_transform( m_transform );

					const CompoundDataMap *lightParams = getLightParameters( appleseedAttributes->m_lightShader.get() );
					convertLightParams( lightParams, light->get_parameters(), false );

					m_light = light.get();
					insertLight( light );
				}
			}

			return true;
		}

	private :

		void removeLightEntities()
		{
			if( m_light )
			{
				removeLight( m_light );
				removeSceneTextures();
				removeSceneColors();
				m_light = NULL;
			}
		}

		asr::Light *m_light;
		asf::Transformd m_transform;
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// AppleseedRenderer
//////////////////////////////////////////////////////////////////////////

namespace
{

InternedString g_cameraOptionName( "camera" );
InternedString g_frameOptionName( "frame" );
InternedString g_environmentEDFName( "as:environment_edf" );
InternedString g_environmentEDFBackground( "as:environment_edf_background" );
InternedString g_logLevelOptionName( "as:log:level" );
InternedString g_logFileNameOptionName( "as:log:filename" );
InternedString g_renderPasses( "as:cfg:generic_frame_renderer:passes" );
InternedString g_ptMaxRayIntensity( "as:cfg:pt:max_ray_intensity" );
InternedString g_overrideShadingMode( "as:cfg:shading_engine:override_shading:mode" );
InternedString g_searchPath( "as:searchpath" );
InternedString g_maxInteractiveRenderSamples( "as:cfg:progressive_frame_renderer:max_samples" );

/// Helper class to manage log targets in an exception safe way.
class ScopedLogTarget
{

	public :

		ScopedLogTarget()
		{
		}

		~ScopedLogTarget()
		{
			if( m_logTarget.get() != NULL )
			{
				asr::global_logger().remove_target( m_logTarget.get() );
			}
		}

		void setLogTarget( asf::auto_release_ptr<asf::ILogTarget> logTarget )
		{
			assert( m_logTarget.get() == NULL );
			assert( logTarget.get() != NULL );

			asr::global_logger().add_target( logTarget.get() );
			m_logTarget = logTarget;
		}

	private :

		asf::auto_release_ptr<asf::ILogTarget> m_logTarget;
};

class AppleseedRenderer : public IECoreScenePreview::Renderer
{

	public :

		AppleseedRenderer( RenderType renderType, const string &fileName )
			:	m_renderType( renderType ), m_shutterOpenTime( 0.0f ), m_shutterCloseTime( 0.0f ), m_environmentEDFVisible( false ), m_maxInteractiveRenderSamples( 0 ), m_appleseedFileName( fileName )
		{
			// Create the renderer controller and the project.
			m_rendererController = new RendererController();
			createProject();

			// Create the shader cache.
			m_shaderCache.reset( new ShaderCache( *m_project, isInteractiveRender() ) );

			// Create the instance master cache for non-interactive renders.
			if( !isInteractiveRender() )
			{
				m_instanceMasterCache.reset( new InstanceMasterCache() );
			}
		}

		virtual ~AppleseedRenderer()
		{
			pause();
			delete m_rendererController;
		}

		virtual void option( const InternedString &name, const Data *value )
		{
			if( name == g_cameraOptionName )
			{
				if( value == NULL )
				{
					m_cameraName = "";
				}
				else if( const StringData *d = reportedCast<const StringData>( value, "option", name ) )
				{
					m_cameraName = d->readable();
				}
				return;
			}

			if( name == g_frameOptionName )
			{
				/// \todo Does this have a meaning in Appleseed?
				return;
			}

			// appleseed render settings.
			if( boost::starts_with( name.c_str(), "as:cfg:" ) )
			{
				// remove the prefix and replace colons by dots.
				string optName( name.string(), 7, string::npos );
				replace( optName.begin(), optName.end(), ':', '.' );

				// special cases.
				if( name == g_renderPasses )
				{
					if( value == NULL )
					{
						// Reset number of render passes to 1.
						m_project->configurations().get_by_name( "final" )->get_parameters().insert_path( "shading_result_framebuffer", "ephemeral" );
						m_project->configurations().get_by_name( "final" )->get_parameters().insert_path( "uniform_pixel_renderer.decorrelate_pixels", "false" );
						m_project->configurations().get_by_name( "final" )->get_parameters().insert_path( optName.c_str(), 1 );
					}
					else if( const IntData *d = reportedCast<const IntData>( value, "option", name ) )
					{
						int numPasses = d->readable();

						// if the number of passes is greater than one, we need to
						// switch the shading result framebuffer in the final rendering config.
						m_project->configurations().get_by_name( "final" )->get_parameters().insert( "shading_result_framebuffer", numPasses > 1 ? "permanent" : "ephemeral" );

						// enable decorrelate pixels if the number of render passes is greater than one.
						m_project->configurations().get_by_name( "final" )->get_parameters().insert_path( "uniform_pixel_renderer.decorrelate_pixels", numPasses > 1 ? "true" : "false" );
						m_project->configurations().get_by_name( "final" )->get_parameters().insert_path( optName.c_str(), numPasses );
					}
					return;
				}

				if( name == g_overrideShadingMode )
				{
					if( value == NULL )
					{
						// Remove diagnostic shader override.
						m_project->configurations().get_by_name( "final" )->get_parameters().remove_path( "shading_engine.override_shading" );
						m_project->configurations().get_by_name( "interactive" )->get_parameters().remove_path( "shading_engine.override_shading" );
					}
					else if( const StringData *d = reportedCast<const StringData>( value, "option", name ) )
					{
						string overrideMode = d->readable();
						if( overrideMode == "no_override" )
						{
							// Remove diagnostic shader override.
							m_project->configurations().get_by_name( "final" )->get_parameters().remove_path( "shading_engine.override_shading" );
							m_project->configurations().get_by_name( "interactive" )->get_parameters().remove_path( "shading_engine.override_shading" );
						}
						else
						{
							m_project->configurations().get_by_name( "final" )->get_parameters().insert_path( optName.c_str(), overrideMode );
							m_project->configurations().get_by_name( "interactive" )->get_parameters().insert_path( optName.c_str(), overrideMode );
						}
					}
					return;
				}

				if( name == g_ptMaxRayIntensity )
				{
					if( value == NULL )
					{
						m_project->configurations().get_by_name( "final" )->get_parameters().remove_path( optName.c_str() );
						m_project->configurations().get_by_name( "interactive" )->get_parameters().remove_path( optName.c_str() );
					}
					else if( const FloatData *d = reportedCast<const FloatData>( value, "option", name ) )
					{
						float maxRayIntensity = d->readable();
						if( maxRayIntensity == 0.0f )
						{
							// if maxRayIntensity is 0 disable it.
							m_project->configurations().get_by_name( "final" )->get_parameters().remove_path( optName.c_str() );
							m_project->configurations().get_by_name( "interactive" )->get_parameters().remove_path( optName.c_str() );
						}
						else
						{
							m_project->configurations().get_by_name( "final" )->get_parameters().insert_path( optName.c_str(), maxRayIntensity );
							m_project->configurations().get_by_name( "interactive" )->get_parameters().insert_path( optName.c_str(), maxRayIntensity );
						}
					}
					return;
				}

				if( name == g_maxInteractiveRenderSamples )
				{
					// We cannot set this config now because appleseed
					// expects the total number of samples, not samples per pixels.
					// We save the value and set it later in the render() method,
					// where we have all the information we need.
					if( value == NULL )
					{
						m_maxInteractiveRenderSamples = 0;
					}
					else if( const IntData *d = reportedCast<const IntData>( value, "option", name ) )
					{
						m_maxInteractiveRenderSamples = d->readable();
					}
					return;
				}

				if( boost::algorithm::ends_with( optName, "max_path_length" ) )
				{
					if( value == NULL )
					{
						m_project->configurations().get_by_name( "final" )->get_parameters().remove_path( optName.c_str() );
						m_project->configurations().get_by_name( "interactive" )->get_parameters().remove_path( optName.c_str() );
					}
					else if( const IntData *d = reportedCast<const IntData>( value, "option", name ) )
					{
						int maxPathLength = d->readable();
						if( maxPathLength == 0 )
						{
							// if maxPathLength is 0 disable it.
							m_project->configurations().get_by_name( "final" )->get_parameters().remove_path( optName.c_str() );
							m_project->configurations().get_by_name( "interactive" )->get_parameters().remove_path( optName.c_str() );
						}
						else
						{
							m_project->configurations().get_by_name( "final" )->get_parameters().insert_path( optName.c_str(), maxPathLength );
							m_project->configurations().get_by_name( "interactive" )->get_parameters().insert_path( optName.c_str(), maxPathLength );
						}
					}
					return;
				}

				// general case.
				if( value == NULL )
				{
					m_project->configurations().get_by_name( "final" )->get_parameters().remove_path( optName.c_str() );
					m_project->configurations().get_by_name( "interactive" )->get_parameters().remove_path( optName.c_str() );
				}
				else
				{
					string valueStr = ParameterAlgo::dataToString( value );
					if( !valueStr.empty() )
					{
						m_project->configurations().get_by_name( "final" )->get_parameters().insert_path( optName.c_str(), valueStr.c_str() );
						m_project->configurations().get_by_name( "interactive" )->get_parameters().insert_path( optName.c_str(), valueStr.c_str() );
					}
				}

				return;
			}

			// other appleseed options.
			if( boost::starts_with( name.c_str(), "as:" ) )
			{
				if( name == g_searchPath )
				{
					if( value == NULL )
					{
						m_project->search_paths().reset();
					}
					else if( const StringData *d = reportedCast<const StringData>( value, "option", name ) )
					{
						m_project->search_paths().reset();
						m_project->search_paths().split_and_push_back(d->readable().c_str(), ':');
					}
					return;
				}

				if( name == g_environmentEDFName )
				{
					if( value == NULL )
					{
						m_environmentEDFName = "";
					}
					else if( const StringData *d = reportedCast<const StringData>( value, "option", name ) )
					{
						m_environmentEDFName = d->readable();
					}
					return;
				}

				if( name == g_environmentEDFBackground )
				{
					if( value == NULL )
					{
						m_environmentEDFVisible = false;
					}
					else if( const BoolData *d = reportedCast<const BoolData>( value, "option", name ) )
					{
						m_environmentEDFVisible = d->readable();
					}
					return;
				}

				if( name == g_logLevelOptionName )
				{
					if( value == NULL )
					{
						asr::global_logger().set_verbosity_level( asf::LogMessage::Info );
					}
					else if( const StringData *d = reportedCast<const StringData>( value, "option", name ) )
					{
						const asf::LogMessage::Category logCategory = asf::LogMessage::get_category_value( d->readable().c_str() );
						asr::global_logger().set_verbosity_level( logCategory );
					}
					return;
				}

				if( name == g_logFileNameOptionName )
				{
					if( value == NULL )
					{
						m_logFileName.clear();
					}
					else if( const StringData *d = reportedCast<const StringData>( value, "option", name ) )
					{
						m_logFileName = d->readable();
					}
					return;
				}

				msg( Msg::Warning, "AppleseedRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.c_str() );
				return;
			}

			// Write directly user options to the configs.
			if( boost::starts_with( name.c_str(), "user:" ) )
			{
				string optName( name.c_str() );
				replace( optName.begin(), optName.end(), ':', '.' );

				if( value == NULL )
				{
					m_project->configurations().get_by_name( "final" )->get_parameters().remove_path( optName.c_str() );
					m_project->configurations().get_by_name( "interactive" )->get_parameters().remove_path( optName.c_str() );
				}
				else
				{
					string valueStr = ParameterAlgo::dataToString( value );
					if( !valueStr.empty() )
					{
						m_project->configurations().get_by_name( "final" )->get_parameters().insert_path( optName.c_str(), valueStr.c_str() );
						m_project->configurations().get_by_name( "interactive" )->get_parameters().insert_path( optName.c_str(), valueStr.c_str() );
					}
				}
				return;
			}

			if( boost::contains( name.c_str(), ":" ) )
			{
				// Ignore options prefixed for some other renderer.
				return;
			}

			msg( Msg::Warning, "AppleseedRenderer::option", boost::format( "Unknown option \"%s\"." ) % name.c_str() );
		}

		virtual void output( const InternedString &name, const Output *output )
		{
			if( output == NULL )
			{
				// Reset display / image output related params.
				m_project->get_frame()->get_parameters().remove_path( "output_filename" );
				m_project->get_frame()->get_parameters().remove_path( "output_aovs" );
				m_project->get_frame()->get_parameters().remove_path( "color_space" );
				m_project->set_display( asf::auto_release_ptr<asr::Display>() );
				return;
			}

			if( output->getType() == "exr" || output->getType() == "png" )
			{
				// Output render directly to a file.
				m_project->get_frame()->get_parameters().insert( "output_filename", output->getName().c_str() );
				m_project->get_frame()->get_parameters().insert( "output_aovs", false );

				if( output->getType() == "png" )
				{
					m_project->get_frame()->get_parameters().insert( "color_space", "srgb" );
				}
				else
				{
					m_project->get_frame()->get_parameters().insert( "color_space", "linear_rgb" );
				}
			}
			else
			{
				// Create a display.
				asr::ParamArray params = ParameterAlgo::convertParams( output->parameters() );
				params.insert( "displayName", name.c_str() );
				params.insert( "type", output->getType().c_str() );
				params.insert( "data", output->getData().c_str() );
				params.insert( "plugin_name", output->getType().c_str() );
				asf::auto_release_ptr<asr::Display> dpy( asr::DisplayFactory::create( name.c_str(), params ) );
				m_project->set_display( dpy );
			}
		}

		virtual Renderer::AttributesInterfacePtr attributes( const CompoundObject *attributes )
		{
			return new AppleseedAttributes( attributes, m_shaderCache.get() );
		}

		virtual ObjectInterfacePtr camera( const string &name, const Camera *camera, const AttributesInterface *attributes )
		{
			CameraPtr cameraCopy = camera->copy();
			cameraCopy->addStandardParameters();
			bool activeCamera = false;

			// Check if this is the active camera.
			if( name == m_cameraName )
			{
				// Save the shutter times for later use.
				const V2f &shutter = cameraCopy->parametersData()->member<V2fData>( "shutter", true )->readable();
				m_shutterOpenTime = shutter.x;
				m_shutterCloseTime = shutter.y;

				activeCamera = true;
			}

			return new AppleseedCamera( *m_project, name, cameraCopy.get(), attributes, activeCamera, isInteractiveRender() );
		}

		virtual ObjectInterfacePtr light( const string &name, const Object *object, const AttributesInterface *attributes )
		{
			// For now we only do area lights using OSL emission().
			if( object == NULL )
			{
				const AppleseedAttributes *appleseedAttributes = static_cast<const AppleseedAttributes*>( attributes );
				if( appleseedAttributes && appleseedAttributes->m_lightShader )
				{
					string lightModel = getLightModel( appleseedAttributes->m_lightShader.get() );
					if( isEnvironmentLight( lightModel ) )
					{
						return new AppleseedEnvironmentLight( *m_project, name, attributes, isInteractiveRender() );
					}
					else if( isDeltaLight( lightModel ) )
					{
						return new AppleseedDeltaLight( *m_project, name, attributes, isInteractiveRender() );
					}
				}
			}

			return new AppleseedNullObject( *m_project, name, isInteractiveRender() );
		}

		virtual ObjectInterfacePtr object( const string &name, const Object *object, const AttributesInterface *attributes )
		{
			if( !ObjectAlgo::isPrimitiveSupported( object ) )
			{
				return new AppleseedNullObject( *m_project, name, m_renderType == Interactive );
			}

			if( m_instanceMasterCache )
			{
				MurmurHash primitiveHash;
				object->hash( primitiveHash );

				const AppleseedAttributes *appleseedAttributes = static_cast<const AppleseedAttributes*>( attributes );
				appleseedAttributes->appendToHash( primitiveHash );

				InstanceMasterPtr master = m_instanceMasterCache->get( primitiveHash, name, m_mainAssembly );
				if( master->m_numInstances > 0 )
				{
					return new AppleseedInstance( *m_project, name, master->m_name );
				}
			}

			if( m_renderType == SceneDescription )
			{
				return new AppleseedPrimitive( *m_project, name, object, attributes, m_projectPath );
			}
			else
			{
				return new AppleseedPrimitive( *m_project, name, object, attributes, m_renderType == Interactive );
			}
		}

		virtual ObjectInterfacePtr object( const string &name, const vector<const Object *> &samples, const vector<float> &times, const AttributesInterface *attributes )
		{
			if( !ObjectAlgo::isPrimitiveSupported( samples[0] ) )
			{
				return new AppleseedNullObject( *m_project, name, m_renderType == Interactive );
			}

			if( m_instanceMasterCache )
			{
				MurmurHash primitiveHash;
				for( int i = 0, e = samples.size(); i < e; ++i)
				{
					primitiveHash.append( times[i] );
					samples[i]->hash( primitiveHash );
				}

				const AppleseedAttributes *appleseedAttributes = static_cast<const AppleseedAttributes*>( attributes );
				appleseedAttributes->appendToHash( primitiveHash );

				InstanceMasterPtr master = m_instanceMasterCache->get( primitiveHash, name, m_mainAssembly );
				if( master->m_numInstances > 0 )
				{
					return new AppleseedInstance( *m_project, name, master->m_name );
				}
			}

			if( m_renderType == SceneDescription )
			{
				return new AppleseedPrimitive( *m_project, name, samples, times, m_shutterOpenTime, m_shutterCloseTime, attributes, m_projectPath );
			}
			else
			{
				return new AppleseedPrimitive( *m_project, name, samples, times, m_shutterOpenTime, m_shutterCloseTime, attributes, m_renderType == Interactive );
			}
		}

		virtual void render()
		{
			// Create a default camera if needed.
			if( m_project->get_uncached_active_camera() == NULL )
			{
				asf::auto_release_ptr<asr::Camera> camera = asr::PinholeCameraFactory().create( "__default_camera", asr::ParamArray() );
				m_project->get_scene()->cameras().insert( camera );
				m_project->get_frame()->get_parameters().insert( "camera", "__default_camera" );
			}

			// Setup the environment.
			asf::auto_release_ptr<asr::Environment> environment( asr::EnvironmentFactory().create( "environment", asr::ParamArray() ) );

			if( !m_environmentEDFName.empty() )
			{
				// Enable the environment light.
				environment->get_parameters().insert( "environment_edf", m_environmentEDFName.c_str() );

				if( m_environmentEDFVisible )
				{
					// Enable the environment shader.
					const string envShaderName = m_environmentEDFName + "_shader";
					environment->get_parameters().insert( "environment_shader", envShaderName );
					asr::EnvironmentShader *envShader = m_project->get_scene()->environment_shaders().get_by_name( envShaderName.c_str() );
					envShader->bump_version_id();
				}
			}

			m_project->get_scene()->set_environment( environment );

			// Set the max number of interactive render samples.
			if( m_maxInteractiveRenderSamples <= 0 )
			{
				// if maxInteractiveRenderSamples is 0 or negative, disable it.
				m_project->configurations().get_by_name( "interactive" )->get_parameters().remove_path( "progressive_frame_renderer.max_samples" );
			}
			else
			{
				asr::Frame *frame = m_project->get_frame();
				size_t numPixels = frame->get_pixel_count();
				m_project->configurations().get_by_name( "interactive" )->get_parameters().insert_path( "progressive_frame_renderer.max_samples", numPixels * m_maxInteractiveRenderSamples );
			}

			// Clear unused shaders.
			m_shaderCache->clearUnused();

			// Convert instanced primitives into assemblies.
			if( m_instanceMasterCache )
			{
				m_instanceMasterCache->movePrimitivesToAssemblies();
			}

			// Launch render.
			if( m_renderType == SceneDescription )
			{
				// Export the project and exit.
				asr::ProjectFileWriter::write( *m_project, m_appleseedFileName.c_str(), asr::ProjectFileWriter::OmitHandlingAssetFiles | asr::ProjectFileWriter::OmitWritingGeometryFiles );
			}
			else if( m_renderType == Batch )
			{
				batchRender();
			}
			else
			{
				interactiveRender();
			}
		}

		virtual void pause()
		{
			m_rendererController->set_status( asr::IRendererController::AbortRendering );

			if( m_renderThread.joinable() )
			{
				m_renderThread.join();
			}
		}

	private :

		bool isInteractiveRender() const
		{
			return m_renderType == Interactive;
		}

		void createProject()
		{
			assert( m_project.get() == NULL );

			m_project = asr::ProjectFactory::create( "project" );
			m_project->add_default_configurations();

			// Insert some config params needed by the interactive renderer.
			asr::Configuration *cfg = m_project->configurations().get_by_name( "interactive" );
			asr::ParamArray *cfg_params = &cfg->get_parameters();
			cfg_params->insert( "sample_renderer", "generic" );
			cfg_params->insert( "sample_generator", "generic" );
			cfg_params->insert( "tile_renderer", "generic" );
			cfg_params->insert( "frame_renderer", "progressive" );
			cfg_params->insert( "lighting_engine", "pt" );
			cfg_params->insert( "pixel_renderer", "uniform" );
			cfg_params->insert( "sampling_mode", "rng" );
			cfg_params->insert_path( "progressive_frame_renderer.max_fps", "5" );

			// Insert some config params needed by the final renderer.
			cfg = m_project->configurations().get_by_name( "final" );
			cfg_params = &cfg->get_parameters();
			cfg_params->insert( "sample_renderer", "generic" );
			cfg_params->insert( "sample_generator", "generic" );
			cfg_params->insert( "tile_renderer", "generic" );
			cfg_params->insert( "frame_renderer", "generic" );
			cfg_params->insert( "lighting_engine", "pt" );
			cfg_params->insert( "pixel_renderer", "uniform" );
			cfg_params->insert( "sampling_mode", "rng" );
			cfg_params->insert_path( "uniform_pixel_renderer.samples", "64" );

			// Create some basic project entities.
			asf::auto_release_ptr<asr::Frame> frame( asr::FrameFactory::create( "beauty", asr::ParamArray().insert( "resolution", "640 480" ) ) );
			m_project->set_frame( frame );

			// 16 bits float (half) is the default pixel format in appleseed.
			// Force the pixel format to float to avoid half -> float conversions in the display driver.
			m_project->get_frame()->get_parameters().insert( "pixel_format", "float" );

			// Create the scene
			asf::auto_release_ptr<asr::Scene> scene = asr::SceneFactory::create();
			m_project->set_scene( scene );

			// Create the main assembly
			asf::auto_release_ptr<asr::Assembly> assembly = asr::AssemblyFactory().create( "assembly", asr::ParamArray() );
			m_mainAssembly = assembly.get();
			m_project->get_scene()->assemblies().insert( assembly );

			// Create the default facing ratio diagnostic surface shader.
			const char *surfaceShaderName = "__default_facing_ratio_shader";
			asr::ParamArray params;
			params.insert( "mode", "facing_ratio" );
			asf::auto_release_ptr<asr::SurfaceShader> surfaceShader = asr::DiagnosticSurfaceShaderFactory().create( surfaceShaderName, params );
			m_mainAssembly->surface_shaders().insert( surfaceShader );

			// Create the default facing ratio material.
			params.clear();
			params.insert( "surface_shader", surfaceShaderName );
			asf::auto_release_ptr<asr::Material> material = asr::GenericMaterialFactory().create( g_defaultMaterialName, params );
			m_mainAssembly->materials().insert( material );

			// Instance the main assembly
			asf::auto_release_ptr<asr::AssemblyInstance> assemblyInstance = asr::AssemblyInstanceFactory::create( "assembly_inst", asr::ParamArray(), "assembly" );
			m_project->get_scene()->assembly_instances().insert( assemblyInstance );

			if( m_renderType == SceneDescription )
			{
				if( m_appleseedFileName.empty() )
				{
					msg( MessageHandler::Error, "AppleseedRenderer", "Empty project filename" );
				}

				m_projectPath = boost::filesystem::path( m_appleseedFileName ).parent_path();

				// Create a dir to store the mesh files if it does not exist yet.
				boost::filesystem::path geomPath = m_projectPath / "_geometry";
				if( !boost::filesystem::exists( geomPath ) )
				{
					if( !boost::filesystem::create_directory( geomPath ) )
					{
						msg( MessageHandler::Error, "AppleseedRenderer", "Couldn't create _geometry directory." );
					}
				}

				// Set the project filename and add the project directory
				// to the search paths.
				m_project->set_path( m_appleseedFileName.c_str() );
				m_project->search_paths().set_root_path( m_projectPath.string().c_str() );
			}
		}

		void batchRender()
		{
			// Reset the renderer controller.
			m_rendererController->set_status( asr::IRendererController::ContinueRendering );

			// Logging.
			ScopedLogTarget logTarget;
			if( !m_logFileName.empty() )
			{
				// Create the file log target and make sure it's open.
				asf::auto_release_ptr<asf::FileLogTarget> l( asf::create_file_log_target() );
				l->open( m_logFileName.c_str() );

				if( !l->is_open() )
				{
					msg( MessageHandler::Error, "AppleseedRenderer", "Couldn't open log file" );
					return;
				}

				logTarget.setLogTarget( asf::auto_release_ptr<asf::ILogTarget>( l.release() ) );
			}

			// Render progress logging.
			ProgressTileCallbackFactory tileCallbackFactory;
			asr::ITileCallbackFactory *tileCallbackFactoryPtr = 0;

			if( m_project->get_display() == NULL )
			{
				// If we don't have a display, because we are rendering
				// directly to an image file, use a progress reporting
				// tile callback to log render progress.
				tileCallbackFactoryPtr = &tileCallbackFactory;
			}

			// Create the master renderer.
			asr::Configuration *cfg = m_project->configurations().get_by_name( "final" );
			const asr::ParamArray &params = cfg->get_parameters();
			m_renderer.reset( new asr::MasterRenderer( *m_project, params, m_rendererController, tileCallbackFactoryPtr ) );

			// Render!.
			RENDERER_LOG_INFO( "rendering frame..." );
			asf::Stopwatch<asf::DefaultWallclockTimer> stopwatch;
			stopwatch.start();

			try
			{
				m_renderer->render();
			}
			catch( const exception &e )
			{
				msg( MessageHandler::Error, "AppleseedRenderer", boost::format( "Exception in render thread, what = %s" ) % e.what() );
			}
			catch( ... )
			{
				msg( MessageHandler::Error, "AppleseedRenderer", "Unknown exception in render thread" );
			}

			stopwatch.measure();

			// Log the total rendering time.
			const double seconds = stopwatch.get_seconds();
			RENDERER_LOG_INFO( "rendering finished in %s.", asf::pretty_time( seconds, 3 ).c_str() );

			// Save the frame to disk if needed.
			const asr::Frame* frame = m_project->get_frame();
			const string output_filename = frame->get_parameters().get_optional<string>("output_filename");

			if( !output_filename.empty() )
			{
				RENDERER_LOG_INFO("writing frame to disk...");
				frame->write_main_image(output_filename.c_str());
			}
		}

		void interactiveRender()
		{
			// Reset the renderer controller.
			m_rendererController->set_status( asr::IRendererController::ContinueRendering );

			// Create or update the master renderer.
			asr::Configuration *cfg = m_project->configurations().get_by_name( "interactive" );
			const asr::ParamArray &params = cfg->get_parameters();

			if( !m_renderer.get() )
			{
				m_renderer.reset( new asr::MasterRenderer( *m_project, params, m_rendererController ) );
			}
			else
			{
				m_renderer->get_parameters() = params;
			}

			// Render!.
			boost::thread thread( &AppleseedRenderer::interactiveRenderThreadFun, this );
			m_renderThread.swap( thread );
		}

		void interactiveRenderThreadFun()
		{
			try
			{
				m_renderer->render();
			}
			catch( const exception &e )
			{
				msg( MessageHandler::Error, "AppleseedRenderer", boost::format( "Exception in render thread, what = %s" ) % e.what() );
			}
			catch( ... )
			{
				msg( MessageHandler::Error, "AppleseedRenderer", "Unknown exception in render thread" );
			}
		}

		// Members used by all render types.

		RenderType m_renderType;

		asf::auto_release_ptr<asr::Project> m_project;
		asr::Assembly *m_mainAssembly;

		string m_cameraName;
		float m_shutterOpenTime;
		float m_shutterCloseTime;

		string m_environmentEDFName;
		bool m_environmentEDFVisible;

		ShaderCachePtr m_shaderCache;

		// Members used by batch and project generation renders

		InstanceMasterCachePtr m_instanceMasterCache;

		// Members used by interactive and batch renders

		RendererController *m_rendererController;
		boost::scoped_ptr<asr::MasterRenderer> m_renderer;

		// Members used by batch renders
		std::string m_logFileName;

		// Members used by interactive renders

		int m_maxInteractiveRenderSamples;
		boost::thread m_renderThread;

		// Members used by project generation renderer

		string m_appleseedFileName;
		boost::filesystem::path m_projectPath;

		// Registration with factory

		static IECoreScenePreview::Renderer::TypeDescription<AppleseedRenderer> g_typeDescription;

};

IECoreScenePreview::Renderer::TypeDescription<AppleseedRenderer> AppleseedRenderer::g_typeDescription( "IECoreAppleseed::Renderer" );

} // namespace
