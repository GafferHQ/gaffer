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

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "GafferScene/Private/IECoreScenePreview/Procedural.h"

#include "IECoreAppleseed/CameraAlgo.h"
#include "IECoreAppleseed/ColorAlgo.h"
#include "IECoreAppleseed/EntityAlgo.h"
#include "IECoreAppleseed/EntityPtr.h"
#include "IECoreAppleseed/MeshAlgo.h"
#include "IECoreAppleseed/MotionAlgo.h"
#include "IECoreAppleseed/ObjectAlgo.h"
#include "IECoreAppleseed/ParameterAlgo.h"
#include "IECoreAppleseed/ProgressTileCallback.h"
#include "IECoreAppleseed/RendererController.h"
#include "IECoreAppleseed/ShaderNetworkAlgo.h"
#include "IECoreAppleseed/TransformAlgo.h"

#include "IECoreScene/Camera.h"
#include "IECoreScene/Shader.h"

#include "IECore/MessageHandler.h"
#include "IECore/ObjectInterpolator.h"
#include "IECore/SimpleTypedData.h"

#include "foundation/core/version.h"
#include "foundation/platform/timers.h"
#include "foundation/utility/log.h"
#include "foundation/utility/searchpaths.h"
#include "foundation/utility/stopwatch.h"
#include "foundation/utility/string.h"
#include "renderer/api/aov.h"
#include "renderer/api/bsdf.h"
#include "renderer/api/camera.h"
#include "renderer/api/color.h"
#include "renderer/api/display.h"
#include "renderer/api/edf.h"
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

#include "boost/algorithm/string.hpp"
#include "boost/filesystem/convenience.hpp"
#include "boost/filesystem/operations.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/smart_ptr/scoped_ptr.hpp"
#include "boost/thread.hpp"

#include "tbb/atomic.h"
#include "tbb/concurrent_hash_map.h"

namespace asf = foundation;
namespace asr = renderer;

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreAppleseed;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

const char *g_defaultSurfaceShaderlName = "__default_facing_ratio_shader";
const char *g_defaultMaterialName = "__defaultMaterial";
const char *g_nullMaterialName = "__nullMaterial";

template<typename T>
T *reportedCast( const RunTimeTyped *v, const char *type, const InternedString &name )
{
	if( T *t = runTimeCast<T>( v ) )
	{
		return t;
	}

	msg( Msg::Warning, "AppleseedRenderer", boost::format( "Expected %s but got %s for %s \"%s\"." ) % T::staticTypeName() % v->typeName() % type % name.c_str() );
	return nullptr;
}

/// Helper class to manage appleseed log targets in an exception safe way.
class ScopedLogTarget
{

	public :

		ScopedLogTarget()
		{
		}

		~ScopedLogTarget()
		{
			if( m_logTarget.get() != nullptr )
			{
				asr::global_logger().remove_target( m_logTarget.get() );
			}
		}

		void setLogTarget( asf::auto_release_ptr<asf::ILogTarget> logTarget )
		{
			assert( m_logTarget.get() == nullptr );
			assert( logTarget.get() != nullptr );

			asr::global_logger().add_target( logTarget.get() );
			m_logTarget = logTarget;
		}

	private :

		asf::auto_release_ptr<asf::ILogTarget> m_logTarget;
};

const std::vector<IECore::MessageHandler::Level> g_ieMsgLevels = {
	IECore::MessageHandler::Level::Debug,
	IECore::MessageHandler::Level::Info,
	IECore::MessageHandler::Level::Warning,
	IECore::MessageHandler::Level::Error,
	IECore::MessageHandler::Level::Error
};

class CortexLogTarget : public asf::ILogTarget
{

	public :

		CortexLogTarget( IECore::MessageHandler *messageHandler ) : m_messageHandler( messageHandler ) {};

		void write( const asf::LogMessage::Category category, const char* file, const size_t line, const char* header, const char* message ) override
		{
			m_messageHandler->handle( g_ieMsgLevels[ min( int(category), 4 ) ], "Appleseed", message );
		}

		void release() override {};

	private :

		IECore::MessageHandlerPtr m_messageHandler;
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// AppleseedRendererBase forward declaration
//////////////////////////////////////////////////////////////////////////

namespace
{

IE_CORE_FORWARDDECLARE( ShaderCache );
IE_CORE_FORWARDDECLARE( InstanceMasterCache );

/// This class implements the basics of outputting attributes
/// and objects to appleseed, but is not a complete implementation
/// of the renderer interface. It is subclassed to provide concrete
/// implementations suitable for use as the master renderer or
/// for use in procedurals.
class AppleseedRendererBase : public IECoreScenePreview::Renderer
{

	public :

		~AppleseedRendererBase() override;

		IECore::InternedString name() const override
		{
			return "Appleseed";
		}

		AttributesInterfacePtr attributes( const CompoundObject *attributes ) override;

		ObjectInterfacePtr object( const string &name, const Object *object, const AttributesInterface *attributes ) override;
		ObjectInterfacePtr object( const string &name, const vector<const Object *> &samples, const vector<float> &times, const AttributesInterface *attributes ) override;

	protected :

		AppleseedRendererBase( RenderType renderType, const string &fileName, const float shutterOpen, const float shutterClose );

		bool isInteractiveRender() const
		{
			return m_renderType == Interactive;
		}

		void createProject();

		ObjectInterfacePtr procedural( const string &name, const IECoreScenePreview::Procedural* procedural, const AttributesInterface *attributes );

		RenderType m_renderType;

		asf::auto_release_ptr<asr::Project> m_project;
		asr::Assembly *m_mainAssembly;

		ShaderCachePtr m_shaderCache;
		InstanceMasterCachePtr m_instanceMasterCache;

		typedef tbb::concurrent_hash_map<IECore::MurmurHash, string> ProceduralCache;
		ProceduralCache m_proceduralCache;

		float m_shutterOpenTime;
		float m_shutterCloseTime;

		string m_appleseedFileName;
		boost::filesystem::path m_projectPath;
};

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
MutexType g_edfMutex;
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

		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override
		{
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

		void insertCamera( EntityPtr<asr::Camera> &camera )
		{
			LockGuardType lock( g_camerasMutex );
			m_project.get_scene()->cameras().insert( camera.release() );
		}

		void removeCamera( EntityPtr<asr::Camera> &camera )
		{
			LockGuardType lock( g_camerasMutex );
			m_project.get_scene()->cameras().remove( camera.get() );
			camera.reset();
		}

		void insertEnvironmentEDF( EntityPtr<asr::EnvironmentEDF> &environment )
		{
			LockGuardType lock( g_environmentMutex );

			const string envShaderName = string( environment->get_name() ) + "_shader";
			asr::EnvironmentShaderFactoryRegistrar factoryRegistrar;
			const asr::IEnvironmentShaderFactory *factory = factoryRegistrar.lookup( "edf_environment_shader" );
			asf::auto_release_ptr<asr::EnvironmentShader> envShader( factory->create( envShaderName.c_str(), asr::ParamArray() ) );
			envShader->get_parameters().insert( "environment_edf", environment->get_name() );
			m_project.get_scene()->environment_shaders().insert( envShader );

			m_project.get_scene()->environment_edfs().insert( environment.release() );
		}

		void removeEnvironmentEDF( EntityPtr<asr::EnvironmentEDF> &environment )
		{
			LockGuardType lock( g_environmentMutex );

			const string envShaderName = string( environment->get_name() ) + "_shader";
			asr::EnvironmentShader *envShader = m_project.get_scene()->environment_shaders().get_by_name( envShaderName.c_str() );
			m_project.get_scene()->environment_shaders().remove( envShader );

			m_project.get_scene()->environment_edfs().remove( environment.get() );
			environment.reset();
		}

		void insertAssembly( EntityPtr<asr::Assembly> &assembly )
		{
			LockGuardType lock( g_assembliesMutex );
			m_mainAssembly->assemblies().insert( assembly.release() );
		}

		void removeAssembly( EntityPtr<asr::Assembly> &assembly )
		{
			LockGuardType lock( g_assembliesMutex );
			m_mainAssembly->assemblies().remove( assembly.get() );
			assembly.reset();
		}

		void insertAssemblyInstance( EntityPtr<asr::AssemblyInstance> &assemblyInstance )
		{
			LockGuardType lock( g_assemblyInstancesMutex );
			m_mainAssembly->assembly_instances().insert( assemblyInstance.release() );
			bumpMainAssemblyVersionId();
		}

		void removeAssemblyInstance( EntityPtr<asr::AssemblyInstance> &assemblyInstance )
		{
			LockGuardType lock( g_assemblyInstancesMutex );
			m_mainAssembly->assembly_instances().remove( assemblyInstance.get() );
			bumpMainAssemblyVersionId();
			assemblyInstance.reset();
		}

		void insertObject( EntityPtr<asr::Object> &object )
		{
			LockGuardType lock( g_objectsMutex );
			m_mainAssembly->objects().insert( object.release() );
		}

		void insertObjectInstance( EntityPtr<asr::ObjectInstance> &objectInstance )
		{
			LockGuardType lock( g_objectsInstancesMutex );
			m_mainAssembly->object_instances().insert( objectInstance.release() );
		}

		void insertLight( EntityPtr<asr::Light>& light )
		{
			LockGuardType lock( g_lightsMutex );
			m_mainAssembly->lights().insert( light.release() );
		}

		void removeLight( EntityPtr<asr::Light> &light )
		{
			LockGuardType lock( g_lightsMutex );
			m_mainAssembly->lights().remove( light.get() );
			light.reset();
		}

		void insertEDF( EntityPtr<asr::EDF> &edf )
		{
			LockGuardType lock( g_edfMutex );
			m_mainAssembly->edfs().insert( edf.release() );
		}

		void removeEDF( EntityPtr<asr::EDF> &edf )
		{
			LockGuardType lock( g_edfMutex );
			m_mainAssembly->edfs().remove( edf.get() );
			edf.reset();
		}

		void insertMaterial( EntityPtr<asr::Material> &material )
		{
			LockGuardType lock( g_materialsMutex );
			m_mainAssembly->materials().insert( material.release() );
		}

		void removeMaterial( EntityPtr<asr::Material> &material )
		{
			LockGuardType lock( g_materialsMutex );
			m_mainAssembly->materials().remove( material.get() );
			material.reset();
		}

		void insertSurfaceShader( EntityPtr<asr::SurfaceShader> &surfaceShader )
		{
			LockGuardType lock( g_surfaceShadersMutex );
			m_mainAssembly->surface_shaders().insert( surfaceShader.release() );
		}

		void removeSurfaceShader( EntityPtr<asr::SurfaceShader> &surfaceShader )
		{
			LockGuardType lock( g_surfaceShadersMutex );
			m_mainAssembly->surface_shaders().remove( surfaceShader.get() );
			surfaceShader.reset();
		}

		void insertShaderGroup( EntityPtr<asr::ShaderGroup> &shaderGroup )
		{
			LockGuardType lock( g_shaderGroupsMutex );
			m_mainAssembly->shader_groups().insert( shaderGroup.release() );
		}

		void removeShaderGroup( EntityPtr<asr::ShaderGroup> &shaderGroup )
		{
			LockGuardType lock( g_shaderGroupsMutex );
			m_mainAssembly->shader_groups().remove( shaderGroup.get() );
			shaderGroup.reset();
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

			if( c.second != nullptr )
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

		~AppleseedNullObject() override
		{
		}

		void transform( const M44f &transform ) override
		{
		}

		void transform( const vector<M44f> &samples, const vector<float> &times ) override
		{
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
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

		AppleseedShader( asr::Project &project, const string &name, const ShaderNetwork *shader, bool interactiveRender )
			:	AppleseedEntity( project, name, interactiveRender )
		{
			m_shaderGroup.reset( ShaderNetworkAlgo::convert( shader ), true );
			m_shaderGroup->set_name( name.c_str() );
			insertShaderGroup( m_shaderGroup );
		}

		~AppleseedShader() override
		{
			if( isInteractiveRender() )
			{
				removeShaderGroup( m_shaderGroup );
			}
		}

		void transform( const M44f &transform ) override
		{
		}

		void transform( const vector<M44f> &samples, const vector<float> &times ) override
		{
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			return true;
		}

		const char *shaderGroupName() const
		{
			return m_shaderGroup->get_name();
		}

	private :

		EntityPtr<asr::ShaderGroup> m_shaderGroup;
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
		AppleseedShaderPtr get( const ShaderNetwork *shader, const IECore::CompoundObject *attributes )
		{
			IECore::MurmurHash h = shader->Object::hash();
			IECore::MurmurHash hSubst;
			if( attributes )
			{
				shader->hashSubstitutions( attributes, hSubst );
				h.append( hSubst );
			}

			Cache::accessor a;
			m_cache.insert( a, h );
			if( !a->second )
			{
				std::string name = h.toString() + "_shadergroup";
				if( hSubst != IECore::MurmurHash() )
				{
					IECoreScene::ShaderNetworkPtr substitutedShader = shader->copy();
					substitutedShader->applySubstitutions( attributes );
					a->second = new AppleseedShader( m_project, name, substitutedShader.get(), m_isInteractive );
				}
				else
				{
					a->second = new AppleseedShader( m_project, name, shader, m_isInteractive );
				}
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
InternedString g_doubleSidedAttributeName( "as:double_sided" );
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
			:	m_shadingSamples( 1 ), m_doubleSided( true ), m_mediumPriority( 0 ), m_meshSmoothNormals( false ), m_meshSmoothTangents( false )
		{
			updateVisibilityDictionary( g_cameraVisibilityAttributeName, attributes );
			updateVisibilityDictionary( g_lightVisibilityAttributeName, attributes );
			updateVisibilityDictionary( g_shadowVisibilityAttributeName, attributes );
			updateVisibilityDictionary( g_diffuseVisibilityAttributeName, attributes );
			updateVisibilityDictionary( g_specularVisibilityAttributeName, attributes );
			updateVisibilityDictionary( g_glossyVisibilityAttributeName, attributes );

			if( const IntData *d = attribute<IntData>( g_shadingSamplesAttributeName, attributes ) )
			{
				m_shadingSamples = d->readable();
			}

			if( const BoolData *d = attribute<BoolData>( g_doubleSidedAttributeName, attributes ) )
			{
				m_doubleSided = d->readable();
			}

			if( const IntData *d = attribute<IntData>( g_mediumPriorityAttributeName, attributes ) )
			{
				m_mediumPriority = d->readable();
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

			m_lightShader = attribute<ShaderNetwork>( g_appleseedLightShaderAttributeName, attributes );
			m_lightShader = m_lightShader ? m_lightShader : attribute<ShaderNetwork>( g_lightShaderAttributeName, attributes );

			const ShaderNetwork *surfaceShaderAttribute = attribute<ShaderNetwork>( g_appleseedSurfaceShaderAttributeName, attributes );
			surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<ShaderNetwork>( g_oslSurfaceShaderAttributeName, attributes );
			surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<ShaderNetwork>( g_surfaceShaderAttributeName, attributes );

			if( surfaceShaderAttribute )
			{
				m_shaderGroup = shaderCache->get( surfaceShaderAttribute, attributes );
			}
		}

		void appendToHash( MurmurHash &hash ) const
		{
			hash.append( m_shadingSamples );
			hash.append( m_doubleSided );
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
		bool m_doubleSided;
		int m_mediumPriority;
		string m_alphaMap;
		asf::Dictionary m_visibilityDictionary;
		bool m_meshSmoothNormals;
		bool m_meshSmoothTangents;
		ConstShaderNetworkPtr m_lightShader;
		AppleseedShaderPtr m_shaderGroup;

	private :

		template<typename T>
		const T *attribute( const InternedString &name, const CompoundObject *attributes )
		{
			CompoundObject::ObjectMap::const_iterator it = attributes->members().find( name );
			if( it == attributes->members().end() )
			{
				return nullptr;
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

		AppleseedCamera( asr::Project &project, const string &name, const Camera *camera, const IECoreScenePreview::Renderer::AttributesInterface *attributes, bool interactive )
			:	AppleseedEntity( project, name, interactive )
		{
			m_camera.reset( CameraAlgo::convert( camera ), true );
			m_camera->set_name( name.c_str() );
			insertCamera( m_camera );
		}

		~AppleseedCamera() override
		{
			if( isInteractiveRender() )
			{
				removeCamera( m_camera );
			}
		}

		void transform( const M44f &transform ) override
		{
			TransformAlgo::makeTransformSequence( transform, m_camera->transform_sequence() );
		}

		void transform( const vector<M44f> &samples, const vector<float> &times ) override
		{
			TransformAlgo::makeTransformSequence( times, samples, m_camera->transform_sequence() );
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			// todo: check if this has to be implemented...
			return true;
		}

	private :

		EntityPtr<asr::Camera> m_camera;
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

		InstanceMaster( const string &name, asr::Assembly *mainAssembly )
			:	m_name( name )
			,	m_mainAssembly( mainAssembly )
		{
			assert( m_mainAssembly );
			m_numInstances = 0;
		}

		void movePrimitiveToAssembly()
		{
			assert( m_numInstances > 0 );

			// Move the object into its own assembly if needed, so that it can be instanced.
			const string assemblyName = m_name + "_assembly";
			if( m_mainAssembly->assemblies().get_by_name( assemblyName.c_str() ) == nullptr )
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
			:	AppleseedEntity( project, name, false )
			,	m_masterName( masterName )
		{
		}

		~AppleseedInstance() override
		{
			// Create an instance of the master primitive assembly and add it to the main assembly.
			string assemblyName = m_masterName + "_assembly";
			string assemblyInstanceName = name() + "_assembly_instance";
			EntityPtr<asr::AssemblyInstance> assInstance( asr::AssemblyInstanceFactory::create( assemblyInstanceName.c_str(), asr::ParamArray(), assemblyName.c_str() ) );
			assInstance->transform_sequence() = m_transformSequence;
			insertAssemblyInstance( assInstance );
		}

		void transform( const M44f &transform ) override
		{
			TransformAlgo::makeTransformSequence( transform, m_transformSequence );
		}

		void transform( const vector<M44f> &samples, const vector<float> &times ) override
		{
			TransformAlgo::makeTransformSequence( times, samples, m_transformSequence );
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
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
			m_object.reset( ObjectAlgo::convert( object ), true );
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
			m_object.reset( ObjectAlgo::convert( samples, times, shutterOpenTime, shutterCloseTime ), true );
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

		~AppleseedPrimitive() override
		{
			if( isInteractiveRender() )
			{
				clearMaterial();
				removeAssemblyInstance( m_objectAssemblyInstance );
				removeAssembly( m_objectAssembly );
				return;
			}

			// Check if the object has transformation motion blur.
			m_transformSequence.optimize();
			if( m_transformSequence.size() > 1 )
			{
				// The object has transformation motion blur.
				// We have to create an assembly for it.
				string assemblyName = name() + "_assembly";
				EntityPtr<asr::Assembly> ass( asr::AssemblyFactory().create( assemblyName.c_str() ) );

				// Add the object to the object assembly.
				ass->objects().insert( m_object.release() );

				// Add the object instance to the object assembly.
				ass->object_instances().insert( m_objectInstance.release() );

				// Add the object assembly to the main assembly.
				insertAssembly( ass );

				// Create an instance of the object assembly and add it to the main assembly.
				string assemblyInstanceName = assemblyName + "_instance";
				EntityPtr<asr::AssemblyInstance> assInstance( asr::AssemblyInstanceFactory::create( assemblyInstanceName.c_str(), asr::ParamArray(), assemblyName.c_str() ) );
				assInstance->transform_sequence() = m_transformSequence;
				insertAssemblyInstance( assInstance );
			}
			else
			{
				// The object does not have transformation motion blur.
				// In this case, it's more efficient to put it in the main assembly.
				insertObject( m_object );

				// To update the transform, we have to create a new object instance.
				m_objectInstance.reset( asr::ObjectInstanceFactory::create( m_objectInstance->get_name(), m_objectInstance->get_parameters(), m_objectInstance->get_object_name(), m_transformSequence.get_earliest_transform(), m_objectInstance->get_front_material_mappings(), m_objectInstance->get_back_material_mappings() ) );
				insertObjectInstance( m_objectInstance );
			}
		}

		void transform( const M44f &transform ) override
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

		void transform( const vector<M44f> &samples, const vector<float> &times ) override
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

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
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
				params.insert( "lighting_samples", appleseedAttributes->m_shadingSamples );

				m_surfaceShader.reset( asr::PhysicalSurfaceShaderFactory().create( surfaceShaderName.c_str(), params ) );
				insertSurfaceShader( m_surfaceShader );

				// Create a material.
				string materialName = name() + "_material";
				params.clear();
				params.insert( "surface_shader", surfaceShaderName.c_str() );
				params.insert( "osl_surface", appleseedAttributes->m_shaderGroup->shaderGroupName() );

				m_material.reset( asr::OSLMaterialFactory().create( materialName.c_str(), params ) );
				insertMaterial( m_material );

				// Assign the material to the object instance.
				m_objectInstance->assign_material( "default", asr::ObjectInstance::FrontSide, materialName.c_str() );

				if( appleseedAttributes->m_doubleSided )
				{
					m_objectInstance->assign_material( "default", asr::ObjectInstance::BackSide, materialName.c_str() );
				}
				else
				{
					m_objectInstance->assign_material( "default", asr::ObjectInstance::BackSide, g_nullMaterialName );
				}
			}
			else
			{
				// No shader assigned. Assign the default material to the object instance.
				m_objectInstance->assign_material( "default", asr::ObjectInstance::FrontSide, g_defaultMaterialName );
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

			if( isInteractiveRender() )
			{
				// We need to re-create object instances after edits.
				asf::auto_release_ptr<asr::ObjectInstance> oi = m_objectAssembly->object_instances().remove( m_objectInstance.get() );

				m_objectInstance.reset( asr::ObjectInstanceFactory::create( oi->get_name(), oi->get_parameters(), oi->get_object_name(), oi->get_transform(), oi->get_front_material_mappings(), oi->get_back_material_mappings() ) );
				m_objectAssembly->object_instances().insert( m_objectInstance.release() );

				// Tell appleseed that we updated the contents of the object assembly.
				m_objectAssembly->bump_version_id();
			}

			return true;
		}

	private :

		void init()
		{
			m_objectAssembly.reset();
			m_objectAssemblyInstance.reset();
			m_object.reset();
			m_objectInstance.reset();
			m_surfaceShader.reset();
			m_material.reset();
		}

		void clearMaterial()
		{
			removeMainAssemblyTextures();

			if( m_surfaceShader.get() )
			{
				removeSurfaceShader( m_surfaceShader );
			}

			m_shaderGroup.reset();

			if( m_material.get() )
			{
				removeMaterial( m_material );
			}

			m_objectInstance->clear_front_materials();
			m_objectInstance->clear_back_materials();
		}

		void computeSmoothNormalsAndTangents( bool normals, bool tangents )
		{
			asr::MeshObject *meshObject = static_cast<asr::MeshObject*>( m_object.get() );

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
			m_objectInstance.reset( asr::ObjectInstanceFactory::create( objectInstanceName.c_str(), asr::ParamArray(), objectName.c_str(), asf::Transformd::identity(), materials, materials ) );
		}

		void createObjectAssembly()
		{
			// Create an assembly for the object.
			string assemblyName = name() + "_assembly";
			m_objectAssembly.reset( asr::AssemblyFactory().create( assemblyName.c_str() ) );

			// Add the object to the object assembly.
			m_objectAssembly->objects().insert( m_object.release() );

			// Add the object instance to the object assembly.
			m_objectAssembly->object_instances().insert( m_objectInstance.release() );

			// Add the object assembly to the main assembly.
			insertAssembly( m_objectAssembly );

			// Create an instance of the object assembly and
			// add it to the main assembly.
			string assemblyInstanceName = assemblyName + "_instance";
			m_objectAssemblyInstance.reset( asr::AssemblyInstanceFactory::create( assemblyInstanceName.c_str(), asr::ParamArray(), m_objectAssembly->get_name() ) );
			insertAssemblyInstance( m_objectAssemblyInstance );
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
			m_object.reset( asr::MeshObjectFactory().create( name().c_str(), params ) );

			// Create the object instance.
			createObjectInstance( name() + ".mesh" );

			AppleseedPrimitive::attributes( attributes );
		}

		// Used to protect mesh file writting for scene description renders.
		static boost::mutex g_geomFilesMutex;

		asr::TransformSequence m_transformSequence;

		EntityPtr<asr::Assembly> m_objectAssembly;
		EntityPtr<asr::AssemblyInstance> m_objectAssemblyInstance;

		EntityPtr<asr::Object> m_object;
		EntityPtr<asr::ObjectInstance> m_objectInstance;

		AppleseedShaderPtr m_shaderGroup;
		EntityPtr<asr::SurfaceShader> m_surfaceShader;
		EntityPtr<asr::Material> m_material;

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
	return envFactoryRegistrar.lookup( lightModel.c_str() ) != nullptr;
}

bool isDeltaLight( const string &lightModel )
{
	asr::LightFactoryRegistrar lightFactoryRegistrar;
	return lightFactoryRegistrar.lookup( lightModel.c_str() ) != nullptr;
}

bool isAreaLight( const string &lightModel )
{
	asr::EDFFactoryRegistrar edfFactoryRegistrar;
	return edfFactoryRegistrar.lookup( lightModel.c_str() ) != nullptr;
}

string getLightModel( const ShaderNetwork *lightShader )
{
	return lightShader->outputShader()->getName();
}

const CompoundDataMap *getLightParameters( const ShaderNetwork *lightShader )
{
	return &(lightShader->outputShader()->parameters());
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
		{
			AppleseedEnvironmentLight::attributes( attributes );
		}

		~AppleseedEnvironmentLight() override
		{
			if( isInteractiveRender() )
			{
				removeEnvironmentEntities();
			}
		}

		void transform( const M44f &transform ) override
		{
			TransformAlgo::makeTransformSequence( transform, m_transformSequence );

			if( m_environment.get() )
			{
				m_environment->transform_sequence() = m_transformSequence;
			}
		}

		void transform( const vector<M44f> &samples, const vector<float> &times ) override
		{
			TransformAlgo::makeTransformSequence( times, samples, m_transformSequence );

			if( m_environment.get() )
			{
				m_environment->transform_sequence() = m_transformSequence;
			}
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
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
					m_environment.reset( factory->create( name().c_str(), asr::ParamArray() ) );
					m_environment->transform_sequence() = m_transformSequence;

					const CompoundDataMap *lightParams = getLightParameters( appleseedAttributes->m_lightShader.get() );
					assert( lightParams );
					convertLightParams( lightParams, m_environment->get_parameters(), true );

					insertEnvironmentEDF( m_environment );
				}
			}

			return true;
		}

	private :

		void removeEnvironmentEntities()
		{
			if( m_environment.get() )
			{
				removeEnvironmentEDF( m_environment );
				removeSceneTextures();
				removeSceneColors();
			}
		}

		EntityPtr<asr::EnvironmentEDF> m_environment;
		asr::TransformSequence m_transformSequence;
};

/// Appleseed delta light handle.
class AppleseedDeltaLight : public AppleseedLight
{
	public :

		AppleseedDeltaLight( asr::Project &project, const string &name, const IECoreScenePreview::Renderer::AttributesInterface *attributes, bool interactive )
			:	AppleseedLight( project, name, attributes, interactive ) , m_transform( asf::Transformd::identity() )
		{
			AppleseedDeltaLight::attributes( attributes );
		}

		~AppleseedDeltaLight() override
		{
			if( isInteractiveRender() )
			{
				removeLightEntities();
			}
		}

		void transform( const M44f &transform ) override
		{
			TransformAlgo::makeTransform( transform, m_transform );

			if( m_light.get() )
			{
				m_light->set_transform( m_transform );
			}
		}

		void transform( const vector<M44f> &samples, const vector<float> &times ) override
		{
			// appleseed does not support light transform motion blur yet.
			transform(samples[0]);
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
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
					m_light.reset( factory->create( name().c_str(), asr::ParamArray() ) );
					m_light->set_transform( m_transform );

					const CompoundDataMap *lightParams = getLightParameters( appleseedAttributes->m_lightShader.get() );
					convertLightParams( lightParams, m_light->get_parameters(), false );

					insertLight( m_light );
				}
			}

			return true;
		}

	private :

		void removeLightEntities()
		{
			if( m_light.get() )
			{
				removeLight( m_light );
				removeSceneTextures();
				removeSceneColors();
			}
		}

		EntityPtr<asr::Light> m_light;
		asf::Transformd m_transform;
};

/// Appleseed area light handle.
class AppleseedAreaLight : public AppleseedLight
{
	public :

		AppleseedAreaLight( asr::Project &project, const string &name, const IECoreScenePreview::Renderer::AttributesInterface *attributes, IECoreScenePreview::Renderer::RenderType renderType )
			:	AppleseedLight( project, name, attributes, renderType == IECoreScenePreview::Renderer::Interactive ) , m_renderType( renderType ), m_transform( asf::Transformd::identity() )
		{
			init();
			AppleseedAreaLight::attributes( attributes );
		}

		~AppleseedAreaLight() override
		{
			if( isInteractiveRender() )
			{
				removeAreaLightEntities();
			}
			else
			{
				// Create the material assignments.
				asf::StringDictionary frontMaterialMappings;
				frontMaterialMappings.insert( "default", m_material->get_name() );

				asf::StringDictionary backMaterialMappings;
				backMaterialMappings.insert( "default", g_nullMaterialName );

				// Create an object instance for the light.
				string objectInstanceName = name() + "_instance";

				asr::ParamArray params;
				params.insert( "visibility", m_visibilityDictionary );

				EntityPtr<asr::ObjectInstance> objectInstance( asr::ObjectInstanceFactory::create( objectInstanceName.c_str(), params, name().c_str(), m_transform, frontMaterialMappings, backMaterialMappings ) );
				insertObjectInstance( objectInstance );
			}
		}

		void transform( const M44f &transform ) override
		{
			M44d md( transform );
			asf::Matrix4d m( md );

			// Rotate 90 degrees around X to match Gaffer's default light orientation.
			m = m * asf::Matrix4d::make_rotation_x( asf::deg_to_rad( -90.0 ) );
			m_transform = asf::Transformd( m );

			if( isInteractiveRender() )
			{
				m_assemblyInstance->transform_sequence().clear();
				m_assemblyInstance->transform_sequence().set_transform( 0.0f, m_transform );
				bumpMainAssemblyVersionId();
			}
		}

		void transform( const vector<M44f> &samples, const vector<float> &times ) override
		{
			// appleseed does not support light transform motion blur yet.
			transform(samples[0]);
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			// Remove any previously created area light.
			removeAreaLightEntities();

			// Create a new light.
			const AppleseedAttributes *appleseedAttributes = static_cast<const AppleseedAttributes*>( attributes );
			m_visibilityDictionary = appleseedAttributes->m_visibilityDictionary;

			if( appleseedAttributes && appleseedAttributes->m_lightShader )
			{
				// Create the EDF.
				string edfName = name() + "_edf";
				asr::EDFFactoryRegistrar edfFactoryRegistrar;
				string lightModel = getLightModel( appleseedAttributes->m_lightShader.get() );
				const asr::IEDFFactory *factory = edfFactoryRegistrar.lookup( lightModel.c_str() );

				m_edf.reset( factory->create( edfName.c_str(), asr::ParamArray() ) );
				const CompoundDataMap *lightParams = getLightParameters( appleseedAttributes->m_lightShader.get() );
				convertLightParams( lightParams, m_edf->get_parameters(), false );
				insertEDF( m_edf );

				// Create a material for each side of the light.
				string materialName = name() + "_front_material";
				asr::ParamArray params;
				params.insert( "edf", m_edf->get_name() );
				m_material.reset( asr::GenericMaterialFactory().create( materialName.c_str(), params ) );
				insertMaterial( m_material );

				// Create the geometry for the area light.
				params.clear();
				params.insert("primitive", "grid");
				params.insert("resolution_u", 1);
				params.insert("resolution_v", 1);
				params.insert("width", 2.0f);
				params.insert("height", 2.0f);

				EntityPtr<asr::Object> object;
				if( m_renderType == IECoreScenePreview::Renderer::SceneDescription )
				{
					object.reset( asr::MeshObjectFactory().create( name().c_str(), params ) );
				}
				else
				{
					object.reset( asr::create_primitive_mesh( name().c_str(), params ) );
				}

				if( isInteractiveRender() )
				{
					// Create an assembly and an assembly instance to allow quick transform updating.
					string assemblyName = name() + "_assembly";
					m_assembly.reset( asr::AssemblyFactory().create( assemblyName.c_str() ) );
					insertAssembly( m_assembly );

					string assemblyInstanceName = assemblyName + "_instance";
					m_assemblyInstance.reset( asr::AssemblyInstanceFactory::create( assemblyInstanceName.c_str(), asr::ParamArray(), assemblyName.c_str() ) );
					m_assemblyInstance->transform_sequence().set_transform( 0.0f, m_transform );
					insertAssemblyInstance( m_assemblyInstance );

					// Add the geometry to the light assembly.
					m_assembly->objects().insert( object.release() );

					// Create the material assignments.
					asf::StringDictionary frontMaterialMappings;
					frontMaterialMappings.insert( "default", m_material->get_name() );

					asf::StringDictionary backMaterialMappings;
					backMaterialMappings.insert( "default", g_nullMaterialName );

					// Create an object instance for the light.
					string objectInstanceName = name() + "_instance";

					asr::ParamArray params;
					params.insert( "visibility", m_visibilityDictionary );

					asf::auto_release_ptr<asr::ObjectInstance> objectInstance;
					objectInstance = asr::ObjectInstanceFactory::create( objectInstanceName.c_str(), params, name().c_str(), asf::Transformd::identity(), frontMaterialMappings, backMaterialMappings );
					m_assembly->object_instances().insert( objectInstance );
				}
				else
				{
					// Add the object to the main assembly.
					insertObject( object );
				}
			}

			return true;
		}

	private :

		void init()
		{
			m_edf.reset();
			m_material.reset();
			m_assembly.reset();
			m_assemblyInstance.reset();
		}

		void removeAreaLightEntities()
		{
			if( m_edf.get() )
			{
				removeEDF( m_edf );
			}

			if( m_material.get() )
			{
				removeMaterial( m_material );
			}

			if( m_assembly.get() )
			{
				removeAssembly( m_assembly );
			}

			if( m_assemblyInstance.get() )
			{
				removeAssemblyInstance( m_assemblyInstance );
			}

			removeSceneColors();
			removeSceneTextures();
		}

		IECoreScenePreview::Renderer::RenderType m_renderType;
		asf::Transformd m_transform;
		asr::ParamArray m_visibilityDictionary;

		EntityPtr<asr::EDF> m_edf;
		EntityPtr<asr::Material> m_material;
		EntityPtr<asr::Assembly> m_assembly;
		EntityPtr<asr::AssemblyInstance> m_assemblyInstance;
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Procedurals
//////////////////////////////////////////////////////////////////////////

namespace
{

class ProceduralRenderer : public AppleseedRendererBase
{

	public :

		/// \todo The base class currently makes a new shader cache
		/// and a new instance cache. Can we share with the parent
		/// renderer instead?
		ProceduralRenderer( RenderType renderType, const string &fileName, const float shutterOpen, const float shutterClose )
			: AppleseedRendererBase( renderType, fileName, shutterOpen, shutterClose )
		{
			assert( renderType != Interactive );
		}

		void option( const IECore::InternedString &name, const IECore::Object *value ) override
		{
			IECore::msg( IECore::Msg::Warning, "AppleseedRenderer", "Procedurals can not call option()" );
		}

		void output( const IECore::InternedString &name, const Output *output ) override
		{
			IECore::msg( IECore::Msg::Warning, "AppleseedRenderer", "Procedurals can not call output()" );
		}

		ObjectInterfacePtr camera( const std::string &name, const IECoreScene::Camera *camera, const AttributesInterface *attributes ) override
		{
			IECore::msg( IECore::Msg::Warning, "AppleseedRenderer", "Procedurals can not call camera()" );
			return nullptr;
		}

		ObjectInterfacePtr light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			IECore::msg( IECore::Msg::Warning, "AppleseedRenderer", "Procedurals can not call light()" );
			return nullptr;
		}


		ObjectInterfacePtr lightFilter( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			IECore::msg( IECore::Msg::Warning, "AppleseedRenderer", "Procedurals can not call lightFilter()" );
			return nullptr;
		}


		void render() override
		{
			IECore::msg( IECore::Msg::Warning, "AppleseedRenderer", "Procedurals can not call render()" );
		}

		void pause() override
		{
			IECore::msg( IECore::Msg::Warning, "AppleseedRenderer", "Procedurals can not call pause()" );
		}

		asf::auto_release_ptr<asr::Assembly> releaseMainAssembly()
		{
			// Clear unused shaders.
			m_shaderCache->clearUnused();

			// Convert instanced primitives into assemblies.
			if( m_instanceMasterCache )
			{
				m_instanceMasterCache->movePrimitivesToAssemblies();
			}

			// Remove the main assembly from the project and return it.
			asr::Scene* scene = m_project->get_scene();
			asf::auto_release_ptr<asr::Assembly> assembly = scene->assemblies().remove( m_mainAssembly );
			return assembly;
		}
};

IE_CORE_DECLAREPTR( ProceduralRenderer )

/// Appleseed procedural handle.
class AppleseedProcedural : public AppleseedEntity
{

	public :

		AppleseedProcedural( asr::Project &project, const string &name, const IECoreScenePreview::Procedural *procedural, ProceduralRenderer* renderer , bool interactiveRender )
			:	AppleseedEntity( project, name, interactiveRender )
		{
			// Expand the procedural into the renderer's project.
			procedural->render( renderer );

			// Remove the main assembly from the renderer's project.
			m_assembly.reset( renderer->releaseMainAssembly() );

			// Remove the default surface shader and materials from the assembly.
			m_assembly->surface_shaders().remove(m_assembly->surface_shaders().get_by_name(g_defaultSurfaceShaderlName));
			m_assembly->materials().remove(m_assembly->materials().get_by_name(g_defaultMaterialName));
			m_assembly->materials().remove(m_assembly->materials().get_by_name(g_nullMaterialName));

			// Rename the assembly and insert it into out main assembly.
			string assemblyName = name + "_assembly";
			m_assembly->set_name( assemblyName.c_str() );
			mainAssembly().assemblies().insert( m_assembly.release() );

			if( isInteractiveRender() )
			{
				createAssemblyInstance();
			}
		}

		~AppleseedProcedural() override
		{
			if( isInteractiveRender() )
			{
				removeAssemblyInstance( m_assemblyInstance );
				removeAssembly( m_assembly );
			}
			else
			{
				// Create an instance of the procedural assembly and add it to the main assembly.
				createAssemblyInstance();
			}
		}

		void transform( const M44f &transform ) override
		{
			if( isInteractiveRender() )
			{
				TransformAlgo::makeTransformSequence( transform, m_assemblyInstance->transform_sequence() );
				bumpMainAssemblyVersionId();
			}
			else
			{
				TransformAlgo::makeTransformSequence( transform, m_transformSequence );
			}
		}

		void transform( const vector<M44f> &samples, const vector<float> &times ) override
		{
			if( isInteractiveRender() )
			{
				TransformAlgo::makeTransformSequence( times, samples, m_assemblyInstance->transform_sequence() );
				bumpMainAssemblyVersionId();
			}
			else
			{
				TransformAlgo::makeTransformSequence( times, samples, m_transformSequence );
			}
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			// We don't support attributes inside procedurals.
			return true;
		}

	private :

		void createAssemblyInstance()
		{
			string assemblyName = name() + "_assembly";
			string assemblyInstanceName = assemblyName + "_instance";
			m_assemblyInstance.reset( asr::AssemblyInstanceFactory::create( assemblyInstanceName.c_str(), asr::ParamArray(), assemblyName.c_str() ) );
			m_assemblyInstance->transform_sequence() = m_transformSequence;
			insertAssemblyInstance( m_assemblyInstance );
		}

		EntityPtr<asr::Assembly> m_assembly;
		EntityPtr<asr::AssemblyInstance> m_assemblyInstance;
		asr::TransformSequence m_transformSequence;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// AppleseedRendererBase definition
//////////////////////////////////////////////////////////////////////////

namespace
{

AppleseedRendererBase::AppleseedRendererBase( RenderType renderType, const string &fileName, const float shutterOpen, const float shutterClose )
	:	m_renderType( renderType )
	,	m_shutterOpenTime( shutterOpen )
	,	m_shutterCloseTime( shutterClose )
	,	m_appleseedFileName( fileName )
{
	// Create the project.
	createProject();

	// Create the shader cache.
	m_shaderCache.reset( new ShaderCache( *m_project, isInteractiveRender() ) );

	// Create the instance master cache for non-interactive renders.
	if( !isInteractiveRender() )
	{
		m_instanceMasterCache.reset( new InstanceMasterCache() );
	}
}

AppleseedRendererBase::~AppleseedRendererBase()
{
}

AppleseedRendererBase::AttributesInterfacePtr AppleseedRendererBase::attributes( const CompoundObject *attributes )
{
	return new AppleseedAttributes( attributes, m_shaderCache.get() );
}

AppleseedRendererBase::ObjectInterfacePtr AppleseedRendererBase::object( const string &name, const Object *object, const AttributesInterface *attributes )
{
	if( const IECoreScenePreview::Procedural *p = IECore::runTimeCast<const IECoreScenePreview::Procedural>( object ) )
	{
		return procedural( name, p, attributes );
	}

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

AppleseedRendererBase::ObjectInterfacePtr AppleseedRendererBase::object( const string &name, const vector<const Object *> &samples, const vector<float> &times, const AttributesInterface *attributes )
{
	if( const IECoreScenePreview::Procedural *p = IECore::runTimeCast<const IECoreScenePreview::Procedural>( samples.front() ) )
	{
		return procedural( name, p, attributes );
	}

	if( !ObjectAlgo::isPrimitiveSupported( samples[0] ) )
	{
		return new AppleseedNullObject( *m_project, name, m_renderType == Interactive );
	}

	if( m_instanceMasterCache )
	{
		MurmurHash primitiveHash;
		for( size_t i = 0, e = samples.size(); i < e; ++i)
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

AppleseedRendererBase::ObjectInterfacePtr AppleseedRendererBase::procedural( const string &name, const IECoreScenePreview::Procedural* p, const AttributesInterface *attributes )
{
	if( !isInteractiveRender() )
	{
		// Check if we have seen this procedural before.
		MurmurHash hash;
		p->hash(hash);

		ProceduralCache::accessor a;
		m_proceduralCache.insert( a, hash );

		if( a->second.empty() )
		{
			a->second = name;
		}
		else
		{
			// Return a handle to an instance of the procedural.
			return new AppleseedInstance( *m_project, name, a->second );
		}
	}

	// Create a procedural renderer. Disable scene edits and enable auto-instancing.
	RenderType procRenderType = m_renderType == Interactive ? Batch : m_renderType;
	ProceduralRendererPtr renderer = new ProceduralRenderer( procRenderType, m_appleseedFileName, m_shutterOpenTime, m_shutterCloseTime );

	// Expand the procedural and return a handle to it.
	return new AppleseedProcedural( *m_project, name, p, renderer.get() , isInteractiveRender() );
}

void AppleseedRendererBase::createProject()
{
	assert( m_project.get() == nullptr );

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
	cfg_params->insert( "sampling_mode", "qmc" );
	cfg_params->insert( "spectrum_mode", "rgb" );
	cfg_params->insert_path( "progressive_frame_renderer.max_fps", "5" );

	// Insert some config params needed by the final renderer.
	cfg = m_project->configurations().get_by_name( "final" );
	cfg_params = &cfg->get_parameters();
	cfg_params->insert( "sample_renderer", "generic" );
	cfg_params->insert( "sample_generator", "generic" );
	cfg_params->insert( "tile_renderer", "adaptive" );
	cfg_params->insert( "frame_renderer", "generic" );
	cfg_params->insert( "lighting_engine", "pt" );
	cfg_params->insert( "pixel_renderer", "uniform" );
	cfg_params->insert( "sampling_mode", "qmc" );
	cfg_params->insert( "spectrum_mode", "rgb" );
	cfg_params->insert_path( "uniform_pixel_renderer.samples", "32" );
	cfg_params->insert_path( "adaptive_tile_renderer.min_samples", "0" );
	cfg_params->insert_path( "adaptive_tile_renderer.max_samples", "32" );
	cfg_params->insert_path( "adaptive_tile_renderer.batch_size", "16" );
	cfg_params->insert_path( "adaptive_tile_renderer.noise_threshold", "1.0" );

	// Create some basic project entities.
	asf::auto_release_ptr<asr::Frame> frame( asr::FrameFactory::create( "beauty", asr::ParamArray().insert( "resolution", "640 480" ) ) );
	m_project->set_frame( frame );

	// Create the scene
	asf::auto_release_ptr<asr::Scene> scene = asr::SceneFactory::create();
	m_project->set_scene( scene );

	// Create the main assembly
	asf::auto_release_ptr<asr::Assembly> assembly = asr::AssemblyFactory().create( "assembly", asr::ParamArray() );
	m_mainAssembly = assembly.get();
	m_project->get_scene()->assemblies().insert( assembly );

	// Create the default facing ratio diagnostic surface shader.
	asr::ParamArray params;
	params.insert( "mode", "facing_ratio" );
	asf::auto_release_ptr<asr::SurfaceShader> surfaceShader = asr::DiagnosticSurfaceShaderFactory().create( g_defaultSurfaceShaderlName, params );
	m_mainAssembly->surface_shaders().insert( surfaceShader );

	// Create the default facing ratio material.
	params.clear();
	params.insert( "surface_shader", g_defaultSurfaceShaderlName );
	asf::auto_release_ptr<asr::Material> material = asr::GenericMaterialFactory().create( g_defaultMaterialName, params );
	m_mainAssembly->materials().insert( material );

	// Create an empty black material for back faces and area lights.
	material = asr::GenericMaterialFactory().create( g_nullMaterialName, asr::ParamArray() );
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

} // namespace

//////////////////////////////////////////////////////////////////////////
// AppleseedRenderer
//////////////////////////////////////////////////////////////////////////

namespace
{

InternedString g_cameraOptionName( "camera" );
InternedString g_frameOptionName( "frame" );
InternedString g_lightingEngine( "as:cfg:lighting_engine" );
InternedString g_environmentEDFName( "as:environment_edf" );
InternedString g_environmentEDFBackground( "as:environment_edf_background" );
InternedString g_logLevelOptionName( "as:log:level" );
InternedString g_logFileNameOptionName( "as:log:filename" );
InternedString g_renderPasses( "as:cfg:passes" );
InternedString g_antialiasSampler( "as:cfg:sampler" );
InternedString g_maxAASamples( "as:cfg:adaptive_tile_renderer:max_samples" );
InternedString g_ptMaxRayIntensity( "as:cfg:pt:max_ray_intensity" );
InternedString g_overrideShadingMode( "as:cfg:shading_engine:override_shading:mode" );
InternedString g_searchPath( "as:searchpath" );
InternedString g_maxInteractiveRenderSamples( "as:cfg:progressive_frame_renderer:max_samples" );
InternedString g_textureCacheSize( "as:cfg:texture_store:max_size" );
// Appleseed 2.1 wants to be given a set of resource search paths, that
// are distinct from the project searchpaths. At the time of writing it
// only uses them to find `stdosl.h` for compiling shaders from source
// on the fly. This isn't a feature we use, so we just use an empty
// searchpath.
foundation::SearchPaths g_resourceSearchPaths;

/// The full renderer implementation as presented to the outside world.
class AppleseedRenderer final : public AppleseedRendererBase
{

	public :

		AppleseedRenderer( RenderType renderType, const string &fileName, const IECore::MessageHandlerPtr &messageHandler )
			:	AppleseedRendererBase( renderType , fileName, 0.0f, 0.0f )
			,	m_environmentEDFVisible( false )
			,	m_maxInteractiveRenderSamples( 0 )
			,	m_messageHandler( messageHandler )
		{
			// Create the renderer controller.
			m_rendererController = new RendererController();
		}

		~AppleseedRenderer() override
		{
			pause();
			delete m_rendererController;
		}

		void option( const InternedString &name, const Object *value ) override
		{
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

			if( name == g_cameraOptionName )
			{
				if( value == nullptr )
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
					if( value == nullptr )
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

				if( name == g_antialiasSampler )
				{
					if( value == nullptr )
					{
						m_project->configurations().get_by_name( "final" )->get_parameters().insert( "tile_renderer", "adaptive" );
					}
					else if( const StringData *d = reportedCast<const StringData>( value, "option", name ) )
					{
						const string& sampler = d->readable();
						m_project->configurations().get_by_name( "final" )->get_parameters().insert( "tile_renderer", sampler.c_str() );
					}
					return;
				}

				if ( name == g_maxAASamples )
				{
					const IECore::Data *dataValue = IECore::runTimeCast<const IECore::Data>( value );
					if( dataValue == nullptr )
					{
						m_project->configurations().get_by_name( "final" )->get_parameters().remove_path( optName.c_str() );
						m_project->configurations().get_by_name( "final" )->get_parameters().remove_path( "uniform_pixel_renderer.samples" );
					}
					else if( const IntData *d = reportedCast<const IntData>( value, "option", name ) )
					{
						int samples = d->readable();
						m_project->configurations().get_by_name( "final" )->get_parameters().insert_path( optName.c_str(), samples );
						m_project->configurations().get_by_name( "final" )->get_parameters().insert_path( "uniform_pixel_renderer.samples", samples );
					}
					return;
				}

				if( name == g_overrideShadingMode )
				{
					if( value == nullptr )
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

				if( name == g_lightingEngine )
				{
					if( value == nullptr )
					{
						// Remove lighting engine.
						m_project->configurations().get_by_name( "final" )->get_parameters().remove_path( "shading_engine.override_shading" );
						m_project->configurations().get_by_name( "interactive" )->get_parameters().remove_path( "shading_engine.override_shading" );
					}
					else if( const StringData *d = reportedCast<const StringData>( value, "option", name ) )
					{
						string lightingEngine = d->readable();
						string interactiveLightingEngine = lightingEngine;

						if( lightingEngine == "sppm" && isInteractiveRender() )
						{
							msg( Msg::Warning, "AppleseedRenderer::option", "SPPM cannot be used with interactive renders. Path tracing will be used." );
							interactiveLightingEngine = "pt";
						}

						m_project->configurations().get_by_name( "final" )->get_parameters().insert_path( optName.c_str(), lightingEngine );
						m_project->configurations().get_by_name( "interactive" )->get_parameters().insert_path( optName.c_str(), interactiveLightingEngine );
					}

					return;
				}

				if( name == g_ptMaxRayIntensity )
				{
					if( value == nullptr )
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
					if( value == nullptr )
					{
						m_maxInteractiveRenderSamples = 0;
					}
					else if( const IntData *d = reportedCast<const IntData>( value, "option", name ) )
					{
						m_maxInteractiveRenderSamples = d->readable();
					}
					return;
				}

				if ( name == g_textureCacheSize )
				{
					if ( value == nullptr )
					{
						// Reset texture cache size.
						m_project->configurations().get_by_name( "final" )->get_parameters().remove_path( optName.c_str() );
						m_project->configurations().get_by_name( "interactive" )->get_parameters().remove_path( optName.c_str() );
					}
					else if( const IntData *d = reportedCast<const IntData>( value, "option", name ) )
					{
						const uint64_t size = static_cast<uint64_t>( d->readable() ) * 1024 * 1024;
						m_project->configurations().get_by_name( "final" )->get_parameters().insert_path( optName.c_str(), size );
						m_project->configurations().get_by_name( "interactive" )->get_parameters().insert_path( optName.c_str(), size );
					}
				}

				// PT and SPPM per ray type bounces.
				if( boost::algorithm::ends_with( optName, "_bounces" ) )
				{
					if( value == nullptr )
					{
						m_project->configurations().get_by_name( "final" )->get_parameters().remove_path( optName.c_str() );
						m_project->configurations().get_by_name( "interactive" )->get_parameters().remove_path( optName.c_str() );
					}
					else if( const IntData *d = reportedCast<const IntData>( value, "option", name ) )
					{
						int maxBounces = d->readable();
						if( maxBounces < 0 )
						{
							// if max bounces is negative disable it.
							m_project->configurations().get_by_name( "final" )->get_parameters().remove_path( optName.c_str() );
							m_project->configurations().get_by_name( "interactive" )->get_parameters().remove_path( optName.c_str() );
						}
						else
						{
							m_project->configurations().get_by_name( "final" )->get_parameters().insert_path( optName.c_str(), maxBounces );
							m_project->configurations().get_by_name( "interactive" )->get_parameters().insert_path( optName.c_str(), maxBounces );
						}
					}
					return;
				}

				// general case.
				const IECore::Data *dataValue = IECore::runTimeCast<const IECore::Data>( value );
				if( dataValue == nullptr )
				{
					m_project->configurations().get_by_name( "final" )->get_parameters().remove_path( optName.c_str() );
					m_project->configurations().get_by_name( "interactive" )->get_parameters().remove_path( optName.c_str() );
				}
				else
				{
					string valueStr = ParameterAlgo::dataToString( dataValue );
					if( !valueStr.empty() )
					{
						m_project->configurations().get_by_name( "final" )->get_parameters().insert_path( optName.c_str(), valueStr.c_str() );
						m_project->configurations().get_by_name( "interactive" )->get_parameters().insert_path( optName.c_str(), valueStr.c_str() );
					}
				}

				return;
			}

			// appleseed frame settings.
			if( boost::starts_with( name.c_str(), "as:frame:" ) )
			{
				// remove the option prefix.
				string optName( name.string(), 9, string::npos );

				asr::Frame* frame = m_project->get_frame();

				const IECore::Data *dataValue = IECore::runTimeCast<const IECore::Data>( value );

				if( dataValue == nullptr )
				{
					frame->get_parameters().remove_path( optName.c_str() );
				}
				else
				{
					string valueStr = ParameterAlgo::dataToString( dataValue );
					frame->get_parameters().insert( optName.c_str(), valueStr.c_str() );
				}

				return;
			}

			// other appleseed options.
			if( boost::starts_with( name.c_str(), "as:" ) )
			{
				if( name == g_searchPath )
				{
					if( value == nullptr )
					{
						m_project->search_paths().clear_explicit_paths();
					}
					else if( const StringData *d = reportedCast<const StringData>( value, "option", name ) )
					{
						m_project->search_paths().clear_explicit_paths();

						vector<string> path_list;
						asf::split(d->readable().c_str(), ":", path_list);

						for (const auto& i:path_list)
							m_project->search_paths().push_back_explicit_path(i);
					}
					return;
				}

				if( name == g_environmentEDFName )
				{
					if( value == nullptr )
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
					if( value == nullptr )
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
					if( value == nullptr )
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
					if( value == nullptr )
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

				const IECore::Data *dataValue = IECore::runTimeCast<const IECore::Data>( value );
				if( dataValue == nullptr )
				{
					m_project->configurations().get_by_name( "final" )->get_parameters().remove_path( optName.c_str() );
					m_project->configurations().get_by_name( "interactive" )->get_parameters().remove_path( optName.c_str() );
				}
				else
				{
					string valueStr = ParameterAlgo::dataToString( dataValue );
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

		void output( const InternedString &name, const Output *output ) override
		{
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

			if( output == nullptr )
			{
				// Reset display / image output related params and recreate the frame.
				m_aovs.clear();
				m_project->get_frame()->get_parameters().remove_path( "output_filename" );
				m_project->set_frame( asr::FrameFactory::create( "beauty", m_project->get_frame()->get_parameters() ) );
				m_project->set_display( asf::auto_release_ptr<asr::Display>() );
				return;
			}

			const bool isFileOutput = output->getType() == "exr" || output->getType() == "png";
			const bool isBeauty = output->getData() == "rgba";

			if( isInteractiveRender() && !isBeauty )
			{
				// We do not support AOVs when doing interactive rendering.
				return;
			}

			// Create an AOV if needed,
			asr::AOV *aov = nullptr;
			if( !isBeauty )
			{
				const asr::AOVFactoryRegistrar factoryRegistrar;
				if( const asr::IAOVFactory *factory = factoryRegistrar.lookup( output->getData().c_str() ) )
				{
					asf::auto_release_ptr<asr::AOV> aovEntity = factory->create( asr::ParamArray() );
					aov = aovEntity.get();

					if( m_aovs.get_by_name( aov->get_name() ) != nullptr )
					{
						msg( Msg::Warning, "AppleseedRenderer::output", boost::format( "AOV \"%s\" already exists. Ignoring." ) % aov->get_name() );
						return;
					}

					if( isFileOutput )
					{
						// Save the image filename.
						aov->get_parameters().insert( "output_filename", output->getName().c_str() );
					}

					// Save the AOV and recreate the frame.
					m_aovs.insert( aovEntity );
					m_project->set_frame( asr::FrameFactory::create( "beauty", m_project->get_frame()->get_parameters(), m_aovs ) );
				}
				else
				{
					msg( Msg::Warning, "AppleseedRenderer::output", boost::format( "Unknown AOV \"%s\"." ) % aov->get_name() );
					return;
				}
			}

			if( isFileOutput ) // Batch output.
			{
				// Set the output filename.
				if( isBeauty ) // Batch Beauty.
				{
					m_project->get_frame()->get_parameters().insert( "output_filename", output->getName().c_str() );
				}
			}
			else if( output->getType() == "ieDisplay" ) // Interactive output.
			{
				// Create and set the display in the project if not already created.
				if( m_project->get_display() == nullptr )
				{
					asr::ParamArray params;
					params.insert( "plugin_name", output->getType().c_str() );

					asf::auto_release_ptr<asr::Display> dpy( asr::DisplayFactory::create( name.c_str(), params ) );
					m_project->set_display( dpy );
				}

				// Add the params for this output to the display params.
				asr::ParamArray& displayParams = m_project->get_display()->get_parameters();
				asr::ParamArray outputParams = ParameterAlgo::convertParams( output->parameters() );

				if( isBeauty )
				{
					displayParams.push( "beauty" ) = outputParams;
				}
				else
				{
					displayParams.push( aov->get_name() ) = outputParams;
				}
			}
			else
			{
				msg( Msg::Warning, "AppleseedRenderer::output", boost::format( "Unknown output type \"%s\"." ) % output->getType() );
			}
		}

		ObjectInterfacePtr camera( const string &name, const Camera *camera, const AttributesInterface *attributes ) override
		{
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

			// Check if this is the active camera.
			if( name == m_cameraName )
			{
				// Save the shutter times for later use.
				const V2f &shutter = camera->getShutter();
				m_shutterOpenTime = shutter.x;
				m_shutterCloseTime = shutter.y;

				updateFrame( name, camera->renderResolution(), camera->renderRegion() );
			}

			return new AppleseedCamera( *m_project, name, camera, attributes, isInteractiveRender() );
		}

		ObjectInterfacePtr light( const string &name, const Object *object, const AttributesInterface *attributes ) override
		{
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

			// For now we only do area lights using OSL emission().
			if( object == nullptr )
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
					else if( isAreaLight( lightModel ) )
					{
						return new AppleseedAreaLight( *m_project, name, attributes, m_renderType );
					}
				}
			}

			return new AppleseedNullObject( *m_project, name, isInteractiveRender() );
		}

		ObjectInterfacePtr lightFilter( const string &name, const Object *object, const AttributesInterface *attributes ) override
		{
			// There is no support for light filters in Appleseed
			return new AppleseedNullObject( *m_project, name, isInteractiveRender() );
		}

		void render() override
		{
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

			// Clear unused shaders.
			m_shaderCache->clearUnused();

			// Convert instanced primitives into assemblies.
			if( m_instanceMasterCache )
			{
				m_instanceMasterCache->movePrimitivesToAssemblies();
			}

			// Create a default camera if needed.
			if( m_project->get_uncached_active_camera() == nullptr )
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
				size_t numPixels = frame->get_crop_window().volume();
				m_project->configurations().get_by_name( "interactive" )->get_parameters().insert_path( "progressive_frame_renderer.max_samples", numPixels * m_maxInteractiveRenderSamples );
			}

			// Launch render.
			if( m_renderType == SceneDescription )
			{
				// Export the project and exit.
				asr::ProjectFileWriter::write( *m_project, m_appleseedFileName.c_str(), asr::ProjectFileWriter::OmitHandlingAssetFiles | asr::ProjectFileWriter::OmitWritingGeometryFiles, nullptr );
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

		void pause() override
		{
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

			m_rendererController->set_status( asr::IRendererController::AbortRendering );

			if( m_renderThread.joinable() )
			{
				m_renderThread.join();
			}
		}

	private :

		void batchRender()
		{
			// Reset the renderer controller.
			m_rendererController->set_status( asr::IRendererController::ContinueRendering );

			// Logging.
			ScopedLogTarget cortexLogTarget;
			if( m_messageHandler )
			{
				asf::auto_release_ptr<asf::ILogTarget> l( new CortexLogTarget( m_messageHandler.get() ) );
				cortexLogTarget.setLogTarget( asf::auto_release_ptr<asf::ILogTarget>( l.release() ) );
			}
			ScopedLogTarget fileLogTarget;
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

				fileLogTarget.setLogTarget( asf::auto_release_ptr<asf::ILogTarget>( l.release() ) );
			}

			// Render progress logging.
			ProgressTileCallbackFactory tileCallbackFactory;
			asr::ITileCallbackFactory *tileCallbackFactoryPtr = nullptr;

			if( m_project->get_display() == nullptr )
			{
				// If we don't have a display, because we are rendering
				// directly to an image file, use a progress reporting
				// tile callback to log render progress.
				tileCallbackFactoryPtr = &tileCallbackFactory;
			}

			// Create the master renderer.
			asr::Configuration *cfg = m_project->configurations().get_by_name( "final" );
			const asr::ParamArray &params = cfg->get_parameters();
#if APPLESEED_VERSION >= 20100
			m_renderer.reset( new asr::MasterRenderer( *m_project, params, g_resourceSearchPaths, tileCallbackFactoryPtr ) );
#else
			m_renderer.reset( new asr::MasterRenderer( *m_project, params, m_rendererController, tileCallbackFactoryPtr ) );
#endif

			// Render!.
			RENDERER_LOG_INFO( "rendering frame..." );
			asf::Stopwatch<asf::DefaultWallclockTimer> stopwatch;
			stopwatch.start();

			try
			{
#if APPLESEED_VERSION >= 20100
				m_renderer->render( *m_rendererController );
#else
				m_renderer->render();
#endif
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
			frame->write_main_and_aov_images();
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
#if APPLESEED_VERSION >= 20100
				m_renderer.reset( new asr::MasterRenderer( *m_project, params, g_resourceSearchPaths ) );
#else
				m_renderer.reset( new asr::MasterRenderer( *m_project, params, m_rendererController ) );
#endif
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
			ScopedLogTarget logTarget;
			{
				asf::auto_release_ptr<asf::ILogTarget> l(
					m_messageHandler ? new CortexLogTarget( m_messageHandler.get() ) : asf::create_console_log_target( stderr )
				);
				logTarget.setLogTarget( l );
			}

			try
			{
#if APPLESEED_VERSION >= 20100
				m_renderer->render( *m_rendererController );
#else
				m_renderer->render();
#endif
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

		void updateFrame( const string &cameraName, const V2i &resolution, const Box2i &renderRegion )
		{
			asr::Frame* frame = m_project->get_frame();
			asr::ParamArray &params = frame->get_parameters();

			// Resolution
			const asf::Vector2i oldRes = params.get<asf::Vector2i>( "resolution" );

			const asf::Vector2i res( resolution.x, resolution.y );
			params.insert( "resolution", res );

			// Render region.
			// For now, we don't do overscan.
			// We keep only the crop part of the render region.
			//
			// Note that we have to flip Y and subtract 1 from the max value, because
			// renderRegion is stored in Gaffer image format ( +Y up and an exclusive upper bound )
			asf::AABB2u crop;
			crop.min[0] = std::max( renderRegion.min.x, 0 );
			crop.min[1] = std::max( res[1] - renderRegion.max.y, 0 );
			crop.max[0] = std::min( renderRegion.max.x - 1, res[0] - 1 );
			crop.max[1] = std::min( res[1] - renderRegion.min.y - 1, res[1] - 1 );

			frame->set_crop_window( crop );

			// Set the active camera.
			params.insert( "camera", cameraName.c_str() );

			if ( isInteractiveRender() )
			{
				// If the resolution changed, we need to re-create the frame.
				if ( res != oldRes )
				{
					m_project->set_frame( asr::FrameFactory().create( "beauty", params, m_project->get_frame()->aovs() ) );

					// Re-create the display if we had one.
					if( const asr::Display *display = m_project->get_display() )
					{
						asf::auto_release_ptr<asr::Display> dpy( asr::DisplayFactory::create( display->get_name(), display->get_parameters() ) );
						m_project->set_display( dpy );
						m_renderer.reset();
					}
				}
			}
			else
			{
				m_project->set_frame( asr::FrameFactory().create( "beauty", params, m_project->get_frame()->aovs() ) );
			}
		}

		// Members used by all render types.

		string m_cameraName;

		string m_environmentEDFName;
		bool m_environmentEDFVisible;

		// Members used by batch and project generation renders

		asr::AOVContainer m_aovs;

		// Members used by interactive and batch renders

		RendererController *m_rendererController;
		boost::scoped_ptr<asr::MasterRenderer> m_renderer;

		// Members used by batch renders
		std::string m_logFileName;

		// Members used by interactive renders

		int m_maxInteractiveRenderSamples;
		boost::thread m_renderThread;
		IECore::MessageHandlerPtr m_messageHandler;

		// Registration with factory

		static IECoreScenePreview::Renderer::TypeDescription<AppleseedRenderer> g_typeDescription;

};

IECoreScenePreview::Renderer::TypeDescription<AppleseedRenderer> AppleseedRenderer::g_typeDescription( "Appleseed" );

} // namespace
