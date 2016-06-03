//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "tbb/compat/thread"
#include "tbb/concurrent_vector.h"

#include "boost/make_shared.hpp"
#include "boost/format.hpp"
#include "boost/algorithm/string/predicate.hpp"

#include "IECore/MessageHandler.h"
#include "IECore/Camera.h"
#include "IECore/Transform.h"
#include "IECore/VectorTypedData.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/ObjectVector.h"

#include "IECoreArnold/ParameterAlgo.h"
#include "IECoreArnold/CameraAlgo.h"
#include "IECoreArnold/NodeAlgo.h"
#include "IECoreArnold/UniverseBlock.h"

#include "Gaffer/StringAlgo.h"

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "GafferArnold/Private/IECoreArnoldPreview/ShaderAlgo.h"

using namespace std;
using namespace IECoreArnold;
using namespace IECoreArnoldPreview;

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

	IECore::msg( IECore::Msg::Warning, "IECoreArnold::Renderer", boost::format( "Expected %s but got %s for %s \"%s\"." ) % T::staticTypeName() % v->typeName() % type % name.c_str() );
	return NULL;
}

template<typename T>
T parameter( const IECore::CompoundDataMap &parameters, const IECore::InternedString &name, const T &defaultValue )
{
	IECore::CompoundDataMap::const_iterator it = parameters.find( name );
	if( it == parameters.end() )
	{
		return defaultValue;
	}

	typedef IECore::TypedData<T> DataType;
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
// ArnoldOutput
//////////////////////////////////////////////////////////////////////////

namespace
{

class ArnoldOutput : public IECore::RefCounted
{

	public :

		ArnoldOutput( const IECore::InternedString &name, const IECoreScenePreview::Renderer::Output *output )
		{
			// Create a driver node and set its parameters.

			std::string driverNodeType = output->getType();
			if( AiNodeEntryGetType( AiNodeEntryLookUp( driverNodeType.c_str() ) ) != AI_NODE_DRIVER )
			{
				// Automatically map tiff to driver_tiff and so on, to provide a degree of
				// compatibility with existing renderman driver names.
				std::string prefixedType = "driver_" + driverNodeType;
				if( AiNodeEntryLookUp( prefixedType.c_str() ) )
				{
					driverNodeType = prefixedType;
				}
			}

			m_driver.reset( AiNode( driverNodeType.c_str() ), AiNodeDestroy );
			if( !m_driver )
			{
				throw IECore::Exception( boost::str( boost::format( "Unable to create output driver of type \"%s\"" ) % driverNodeType ) );
			}

			const std::string driverNodeName = boost::str( boost::format( "ieCoreArnold:display:%s" ) % name.string() );
			AiNodeSetStr( m_driver.get(), "name", driverNodeName.c_str() );

			if( const AtParamEntry *fileNameParameter = AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( m_driver.get() ), "filename" ) )
			{
				AiNodeSetStr( m_driver.get(), AiParamGetName( fileNameParameter ), output->getName().c_str() );
			}

			ParameterAlgo::setParameters( m_driver.get(), output->parameters() );

			// Create a filter.

			std::string filterNodeType = parameter<std::string>( output->parameters(), "filter", "gaussian" );
			if( AiNodeEntryGetType( AiNodeEntryLookUp( filterNodeType.c_str() ) ) != AI_NODE_FILTER )
			{
				filterNodeType = filterNodeType + "_filter";
			}

			m_filter.reset( AiNode( filterNodeType.c_str() ), AiNodeDestroy );
			if( AiNodeEntryGetType( AiNodeGetNodeEntry( m_filter.get() ) ) != AI_NODE_FILTER )
			{
				throw IECore::Exception( boost::str( boost::format( "Unable to create filter of type \"%s\"" ) % filterNodeType ) );
			}

			const std::string filterNodeName = boost::str( boost::format( "ieCoreArnold:filter:%s" ) % name.string() );
			AiNodeSetStr( m_filter.get(), "name", filterNodeName.c_str() );

			// Convert the data specification to the form
			// supported by Arnold.

			m_data = output->getData();

			if( m_data=="rgb" )
			{
				m_data = "RGB RGB";
			}
			else if( m_data=="rgba" )
			{
				m_data = "RGBA RGBA";
			}
			else
			{
				vector<std::string> tokens;
				Gaffer::tokenize( m_data, ' ', tokens );
				if( tokens.size() == 2 && tokens[0] == "color" )
				{
					m_data = tokens[1] + " RGBA";
				}
			}
		}

		std::string string() const
		{
			return boost::str( boost::format( "%s %s %s" ) % m_data % AiNodeGetName( m_filter.get() ) % AiNodeGetName( m_driver.get() ) );
		}

	private :

		boost::shared_ptr<AtNode> m_driver;
		boost::shared_ptr<AtNode> m_filter;
		std::string m_data;

};

IE_CORE_DECLAREPTR( ArnoldOutput )

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldShader
//////////////////////////////////////////////////////////////////////////

namespace
{

/// \todo Cache these so we can reuse them across multiple ArnoldAttributes
/// instances. Bear in mind though that we don't want to cache light shaders.
class ArnoldShader : public IECore::RefCounted
{

	public :

		ArnoldShader( const IECore::ObjectVector *shader )
		{
			m_nodes = ShaderAlgo::convert( shader );
		}

		virtual ~ArnoldShader()
		{
			for( std::vector<AtNode *>::const_iterator it = m_nodes.begin(), eIt = m_nodes.end(); it != eIt; ++it )
			{
				AiNodeDestroy( *it );
			}
		}

		AtNode *root()
		{
			return !m_nodes.empty() ? m_nodes.back() : NULL;
		}

	private :

		std::vector<AtNode *> m_nodes;

};

IE_CORE_DECLAREPTR( ArnoldShader )

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldAttributes
//////////////////////////////////////////////////////////////////////////

namespace
{

IECore::InternedString g_surfaceShaderAttributeName( "surface" );
IECore::InternedString g_lightShaderAttributeName( "light" );
IECore::InternedString g_doubleSidedAttributeName( "doubleSided" );

IECore::InternedString g_cameraVisibilityAttributeName( "ai:visibility:camera" );
IECore::InternedString g_shadowVisibilityAttributeName( "ai:visibility:shadow" );
IECore::InternedString g_reflectedVisibilityAttributeName( "ai:visibility:reflected" );
IECore::InternedString g_refractedVisibilityAttributeName( "ai:visibility:refracted" );
IECore::InternedString g_diffuseVisibilityAttributeName( "ai:visibility:diffuse" );
IECore::InternedString g_glossyVisibilityAttributeName( "ai:visibility:glossy" );
IECore::InternedString g_arnoldSurfaceShaderAttributeName( "ai:surface" );
IECore::InternedString g_arnoldLightShaderAttributeName( "ai:light" );

class ArnoldAttributes : public IECoreScenePreview::Renderer::AttributesInterface
{

	public :

		ArnoldAttributes( const IECore::CompoundObject *attributes )
			:	visibility( AI_RAY_ALL ), sidedness( AI_RAY_ALL )
		{
			for( IECore::CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; ++it )
			{
				if( it->first == g_cameraVisibilityAttributeName )
				{
					updateVisibility( it->first, AI_RAY_CAMERA, it->second.get() );
				}
				else if( it->first == g_shadowVisibilityAttributeName )
				{
					updateVisibility( it->first, AI_RAY_SHADOW, it->second.get() );
				}
				else if( it->first == g_reflectedVisibilityAttributeName )
				{
					updateVisibility( it->first, AI_RAY_REFLECTED, it->second.get() );
				}
				else if( it->first == g_refractedVisibilityAttributeName )
				{
					updateVisibility( it->first, AI_RAY_REFRACTED, it->second.get() );
				}
				else if( it->first == g_diffuseVisibilityAttributeName )
				{
					updateVisibility( it->first, AI_RAY_DIFFUSE, it->second.get() );
				}
				else if( it->first == g_glossyVisibilityAttributeName )
				{
					updateVisibility( it->first, AI_RAY_GLOSSY, it->second.get() );
				}
				else if( it->first == g_doubleSidedAttributeName )
				{
					if( const IECore::BoolData *d = reportedCast<const IECore::BoolData>( it->second.get(), "attribute", it->first) )
					{
						sidedness = d->readable() ? AI_RAY_ALL : AI_RAY_UNDEFINED;
					}
				}
				else if(
					it->first == g_surfaceShaderAttributeName ||
					it->first == g_arnoldSurfaceShaderAttributeName
				)
				{
					if( const IECore::ObjectVector *o = reportedCast<const IECore::ObjectVector>( it->second.get(), "attribute", it->first) )
					{
						surfaceShader = new ArnoldShader( o );
					}
				}
				else if(
					it->first == g_lightShaderAttributeName ||
					it->first == g_arnoldLightShaderAttributeName
				)
				{
					if( const IECore::ObjectVector *o = reportedCast<const IECore::ObjectVector>( it->second.get(), "attribute", it->first) )
					{
						lightShader = new ArnoldShader( o );
					}
				}
			}
		}

		unsigned char visibility;
		unsigned char sidedness;
		ArnoldShaderPtr surfaceShader;
		ArnoldShaderPtr lightShader;

	private :

		void updateVisibility( const IECore::InternedString &name, unsigned char rayType, const IECore::Object *attribute )
		{
			if( const IECore::BoolData *d = reportedCast<const IECore::BoolData>( attribute, "attribute", name ) )
			{
				if( d->readable() )
				{
					visibility |= rayType;
				}
				else
				{
					visibility = visibility & ~rayType;
				}
			}
		}

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldObject
//////////////////////////////////////////////////////////////////////////

namespace
{

static IECore::InternedString g_surfaceAttributeName( "surface" );
static IECore::InternedString g_aiSurfaceAttributeName( "ai:surface" );

class ArnoldObject : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		ArnoldObject( const std::string &name, const IECore::Object *object )
			:	m_node( NULL )
		{
			if( object )
			{
				m_node = NodeAlgo::convert( object );
			}
			if( m_node )
			{
				AiNodeSetStr( m_node, "name", name.c_str() );
			}
		}

		ArnoldObject( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times )
			:	m_node( NULL )
		{
			m_node = NodeAlgo::convert( samples, times );
			if( m_node )
			{
				AiNodeSetStr( m_node, "name", name.c_str() );
			}
		}

		virtual ~ArnoldObject()
		{
			if( m_node )
			{
				AiNodeDestroy( m_node );
			}
		}

		virtual void transform( const Imath::M44f &transform )
		{
			if( !m_node )
			{
				return;
			}
			AiNodeSetMatrix( m_node, "matrix", const_cast<float (*)[4]>( transform.x ) );
		}

		virtual void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times )
		{
			if( !m_node )
			{
				return;
			}
			const size_t numSamples = samples.size();
			AtArray *timesArray = AiArrayAllocate( samples.size(), 1, AI_TYPE_FLOAT );
			AtArray *matricesArray = AiArrayAllocate( 1, numSamples, AI_TYPE_MATRIX );
			for( size_t i = 0; i < numSamples; ++i )
			{
				AiArraySetFlt( timesArray, i, times[i] );
				AiArraySetMtx( matricesArray, i, const_cast<float (*)[4]>( samples[i].x ) );
			}
			AiNodeSetArray( m_node, "matrix", matricesArray );
			if( AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( m_node ), "transform_time_samples" ) )
			{
				AiNodeSetArray( m_node, "transform_time_samples", timesArray );
			}
			else
			{
				AiNodeSetArray( m_node, "time_samples", matricesArray );
			}
		}

		virtual void attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes )
		{
			if( !m_node )
			{
				return;
			}

			if( AiNodeEntryGetType( AiNodeGetNodeEntry( m_node ) ) == AI_NODE_SHAPE )
			{
				const ArnoldAttributes *arnoldAttributes = static_cast<const ArnoldAttributes *>( attributes );
				AiNodeSetByte( m_node, "visibility", arnoldAttributes->visibility );
				AiNodeSetByte( m_node, "sidedness", arnoldAttributes->sidedness );
				m_shader = arnoldAttributes->surfaceShader; // Keep shader alive as long as we are alive
				AiNodeSetPtr( m_node, "shader", m_shader ? m_shader->root() : AiNodeLookUpByName( "ieCoreArnold:defaultShader" ) );
			}
		}

	private :

		AtNode *m_node;
		ArnoldShaderPtr m_shader;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldLight
//////////////////////////////////////////////////////////////////////////

namespace
{

class ArnoldLight : public ArnoldObject
{

	public :

		ArnoldLight( const std::string &name, const IECore::Object *object )
			:	ArnoldObject( name, object )
		{
		}

		virtual void transform( const Imath::M44f &transform )
		{
			ArnoldObject::transform( transform );
			m_transform = transform;
			applyTransform();
		}

		virtual void attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes )
		{
			ArnoldObject::attributes( attributes );
			const ArnoldAttributes *arnoldAttributes = static_cast<const ArnoldAttributes *>( attributes );
			m_lightShader = arnoldAttributes->lightShader;
			applyTransform();
		}

	private :

		void applyTransform()
		{
			if( !m_lightShader )
			{
				return;
			}
			AtNode *root = m_lightShader->root();
			AiNodeSetMatrix( root, "matrix", const_cast<float (*)[4]>( m_transform.x ) );
		}

		// Because the AtNode for the light arrives via attributes(),
		// we need to store the transform ourselves so we have it later
		// when we need it.
		Imath::M44f m_transform;
		ArnoldShaderPtr m_lightShader;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldRenderer
//////////////////////////////////////////////////////////////////////////

namespace
{

/// \todo Should these be defined in the Renderer base class?
/// Or maybe be in a utility header somewhere?
IECore::InternedString g_cameraOptionName( "camera" );
IECore::InternedString g_logFileNameOptionName( "ai:log:filename" );

class ArnoldRenderer : public IECoreScenePreview::Renderer
{

	public :

		ArnoldRenderer( RenderType renderType, const std::string &fileName )
			:	m_renderType( renderType ),
				m_universeBlock( boost::make_shared<UniverseBlock>() ),
				m_assFileName( fileName )
		{
			/// \todo Control with an option.
			AiMsgSetConsoleFlags( AI_LOG_ALL );

			AtNode *defaultShader = AiNode( "utility" );
			AiNodeSetStr( defaultShader, "name", "ieCoreArnold:defaultShader" );
		}

		virtual ~ArnoldRenderer()
		{
			pause();
		}

		virtual void option( const IECore::InternedString &name, const IECore::Data *value )
		{
			AtNode *options = AiUniverseGetOptions();
			if( name == g_cameraOptionName )
			{
				if( value == NULL )
				{
					m_cameraName = "";
				}
				else if( const IECore::StringData *d = reportedCast<const IECore::StringData>( value, "option", name ) )
				{
					m_cameraName = d->readable();

				}
				return;
			}
			else if( name == g_logFileNameOptionName )
			{
				if( value == NULL )
				{
					AiMsgSetLogFileName( "" );
				}
				else if( const IECore::StringData *d = reportedCast<const IECore::StringData>( value, "option", name ) )
				{
					AiMsgSetLogFileName( d->readable().c_str() );

				}
			}
			else if( boost::starts_with( name.c_str(), "ai:" ) )
			{
				const AtParamEntry *parameter = AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( options ), name.c_str() + 3 );
				if( parameter )
				{
					if( value )
					{
						ParameterAlgo::setParameter( options, name.c_str() + 3, value );
					}
					else
					{
						AiNodeResetParameter( options, name.c_str() + 3 );
					}
					return;
				}
			}
			else if( boost::starts_with( name.c_str(), "user:" ) )
			{
				if( value )
				{
					ParameterAlgo::setParameter( options, name.c_str(), value );
				}
				else
				{
					AiNodeResetParameter( options, name.c_str() );
				}
				return;
			}
			else if( boost::contains( name.c_str(), ":" ) )
			{
				// Ignore options prefixed for some other renderer.
				return;
			}

			IECore::msg( IECore::Msg::Warning, "IECoreArnold::Renderer::option", boost::format( "Unknown option \"%s\"." ) % name.c_str() );
		}

		virtual void output( const IECore::InternedString &name, const Output *output )
		{
			m_outputs.erase( name );
			if( output )
			{
				try
				{
					m_outputs[name] = new ArnoldOutput( name, output );
				}
				catch( const std::exception &e )
				{
					IECore::msg( IECore::Msg::Warning, "IECoreArnold::Renderer::output", e.what() );
				}
			}

			IECore::StringVectorDataPtr outputs = new IECore::StringVectorData;
			for( OutputMap::const_iterator it = m_outputs.begin(), eIt = m_outputs.end(); it != eIt; ++it )
			{
				outputs->writable().push_back( it->second->string() );
			}

			IECoreArnold::ParameterAlgo::setParameter( AiUniverseGetOptions(), "outputs", outputs.get() );
		}

		virtual Renderer::AttributesInterfacePtr attributes( const IECore::CompoundObject *attributes )
		{
			return new ArnoldAttributes( attributes );
		}

		virtual ObjectInterfacePtr camera( const std::string &name, const IECore::Camera *camera )
		{
			IECore::CameraPtr cameraCopy = camera->copy();
			cameraCopy->addStandardParameters();
			m_cameras[name] = cameraCopy;
			return store( new ArnoldObject( name, cameraCopy.get() ) );
		}

		virtual ObjectInterfacePtr light( const std::string &name, const IECore::Object *object = NULL )
		{
			return store( new ArnoldLight( name, object ) );
		}

		virtual Renderer::ObjectInterfacePtr object( const std::string &name, const IECore::Object *object )
		{
			return store( new ArnoldObject( name, object ) );
		}

		virtual ObjectInterfacePtr object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times )
		{
			return store( new ArnoldObject( name, samples, times ) );
		}

		virtual void render()
		{
			updateCamera();

			// Do the appropriate render based on
			// m_renderType.
			switch( m_renderType )
			{
				case Batch :
					AiRender( AI_RENDER_MODE_CAMERA );
					break;
				case SceneDescription :
					AiASSWrite( m_assFileName.c_str(), AI_NODE_ALL );
					break;
				case Interactive :
					std::thread thread( performInteractiveRender );
					m_interactiveRenderThread.swap( thread );
					break;
			}
		}

		virtual void pause()
		{
			if( AiRendering() )
			{
				AiRenderInterrupt();
			}
			if( m_interactiveRenderThread.joinable() )
			{
				m_interactiveRenderThread.join();
			}
		}

	private :

		ObjectInterfacePtr store( ObjectInterface *objectInterface )
		{
			if( m_renderType != Interactive )
			{
				// Our ObjectInterface class owns the AtNodes it
				// represents. In Interactive mode the client is
				// responsible for keeping it alive as long as the
				// object should exist, but in non-interactive modes
				// we are responsible for ensuring the object doesn't
				// die. Storing it is the simplest approach.
				//
				// \todo We might want to save memory by not storing
				// ObjectInterfaces, but instead giving them the notion
				// of whether or not they own the AtNodes they created.
				m_objects.push_back( objectInterface );
			}
			return objectInterface;
		}

		void updateCamera()
		{
			AtNode *options = AiUniverseGetOptions();

			const IECore::Camera *cortexCamera = m_cameras[m_cameraName].get();
			if( cortexCamera )
			{
				AiNodeSetPtr( options, "camera", AiNodeLookUpByName( m_cameraName.c_str() ) );
				m_defaultCamera = NULL;
			}
			else
			{
				if( !m_defaultCamera )
				{
					IECore::CameraPtr defaultCortexCamera = new IECore::Camera();
					defaultCortexCamera->addStandardParameters();
					m_defaultCamera = camera( "ieCoreArnold:defaultCamera", defaultCortexCamera.get() );
				}
				cortexCamera = m_cameras["ieCoreArnold:defaultCamera"].get();
				AiNodeSetPtr( options, "camera", AiNodeLookUpByName( "ieCoreArnold:defaultCamera" ) );
			}

			const IECore::V2iData *resolution = cortexCamera->parametersData()->member<IECore::V2iData>( "resolution" );
			AiNodeSetInt( options, "xres", resolution->readable().x );
			AiNodeSetInt( options, "yres", resolution->readable().y );

			const IECore::FloatData *pixelAspectRatio = cortexCamera->parametersData()->member<IECore::FloatData>( "pixelAspectRatio" );
			AiNodeSetFlt( options, "aspect_ratio", 1.0f / pixelAspectRatio->readable() ); // arnold is y/x, we're x/y

			const IECore::Box2fData *crop = cortexCamera->parametersData()->member<IECore::Box2fData>( "cropWindow" );
			AiNodeSetInt( options, "region_min_x", (int)(( resolution->readable().x - 1 ) * crop->readable().min.x ) );
			AiNodeSetInt( options, "region_min_y", (int)(( resolution->readable().y - 1 ) * crop->readable().min.y ) );
			AiNodeSetInt( options, "region_max_x", (int)(( resolution->readable().x - 1 ) * crop->readable().max.x ) );
			AiNodeSetInt( options, "region_max_y", (int)(( resolution->readable().y - 1 ) * crop->readable().max.y ) );
		}

		// Called in a background thread to control a
		// progressive interactive render.
		static void performInteractiveRender()
		{
			AtNode *options = AiUniverseGetOptions();
			const int finalAASamples = AiNodeGetInt( options, "AA_samples" );
			const int startAASamples = min( -5, finalAASamples );

			for( int aaSamples = startAASamples; aaSamples <= finalAASamples; ++aaSamples )
			{
				if( aaSamples == 0 || ( aaSamples > 1 && aaSamples != finalAASamples ) )
				{
					// 0 AA_samples is meaningless, and we want to jump straight
					// from 1 AA_sample to the final sampling quality.
					continue;
				}

				AiNodeSetInt( options, "AA_samples", aaSamples );
				if( AiRender( AI_RENDER_MODE_CAMERA ) != AI_SUCCESS )
				{
					// Render cancelled on main thread.
					break;
				}
			}

			// Restore the setting we've been monkeying with.
			AiNodeSetInt( options, "AA_samples", finalAASamples );
		}

		// Members used by all render types.

		RenderType m_renderType;

		boost::shared_ptr<IECoreArnold::UniverseBlock> m_universeBlock;

		typedef std::map<IECore::InternedString, ArnoldOutputPtr> OutputMap;
		OutputMap m_outputs;

		std::string m_cameraName;
		typedef std::map<std::string, IECore::ConstCameraPtr> CameraMap;
		CameraMap m_cameras;
		ObjectInterfacePtr m_defaultCamera;

		// Members used by batch renders

		tbb::concurrent_vector<ObjectInterfacePtr> m_objects;

		// Members used by interactive renders

		std::thread m_interactiveRenderThread;

		// Members used by ass generation "renders"

		std::string m_assFileName;

		// Registration with factory

		static Renderer::TypeDescription<ArnoldRenderer> g_typeDescription;

};

IECoreScenePreview::Renderer::TypeDescription<ArnoldRenderer> ArnoldRenderer::g_typeDescription( "IECoreArnold::Renderer" );

} // namespace
