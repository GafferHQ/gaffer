//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include <unordered_map>

#include "tbb/concurrent_vector.h"
#include "tbb/concurrent_unordered_map.h"

#include "boost/format.hpp"
#include "boost/algorithm/string/predicate.hpp"

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/Writer.h"
#include "IECore/CompoundParameter.h"

#include "IECoreGL/GL.h"
#include "IECoreGL/State.h"
#include "IECoreGL/Renderable.h"
#include "IECoreGL/OrthographicCamera.h"
#include "IECoreGL/CachedConverter.h"
#include "IECoreGL/ToGLCameraConverter.h"
#include "IECoreGL/FrameBuffer.h"
#include "IECoreGL/ColorTexture.h"
#include "IECoreGL/DepthTexture.h"
#include "IECoreGL/Exception.h"
#include "IECoreGL/ShaderStateComponent.h"

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreGL;

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

	IECore::msg( IECore::Msg::Warning, "IECoreGL::Renderer", boost::format( "Expected %s but got %s for %s \"%s\"." ) % T::staticTypeName() % v->typeName() % type % name.c_str() );
	return nullptr;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// OpenGLAttributes
//////////////////////////////////////////////////////////////////////////

namespace
{

class OpenGLAttributes : public IECoreScenePreview::Renderer::AttributesInterface
{

	public :

		OpenGLAttributes( const IECore::CompoundObject *attributes )
		{
			m_state = static_pointer_cast<const State>(
				CachedConverter::defaultCachedConverter()->convert( attributes )
			);
		}

		const State *state() const
		{
			return m_state.get();
		}

	private :

		ConstStatePtr m_state;

};

IE_CORE_DECLAREPTR( OpenGLAttributes )

} // namespace

//////////////////////////////////////////////////////////////////////////
// OpenGLObject
//////////////////////////////////////////////////////////////////////////

namespace
{

class OpenGLObject : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		OpenGLObject( const IECoreGL::ConstRenderablePtr &renderable )
			:	m_renderable( renderable )
		{
		}

		void transform( const Imath::M44f &transform ) override
		{
			m_transform = transform;
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			transform( samples.front() );
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			m_attributes = static_cast<const OpenGLAttributes *>( attributes );
			return true;
		}

		void render( IECoreGL::State *currentState )
		{
			const bool haveTransform = m_transform != M44f();
			if( haveTransform )
			{
				glPushMatrix();
				glMultMatrixf( m_transform.getValue() );
			}

			IECoreGL::State::ScopedBinding scope( *m_attributes->state(), *currentState );
			m_renderable->render( currentState );

			if( haveTransform )
			{
				glPopMatrix();
			}
		}

	private :

		M44f m_transform;
		ConstOpenGLAttributesPtr m_attributes;
		IECoreGL::ConstRenderablePtr m_renderable;

};

IE_CORE_FORWARDDECLARE( OpenGLObject )

} // namespace

//////////////////////////////////////////////////////////////////////////
// OpenGLCamera
//////////////////////////////////////////////////////////////////////////

namespace
{

class OpenGLCamera : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		OpenGLCamera( const IECore::Camera *camera )
		{
			if( camera )
			{
				ToGLCameraConverterPtr converter = new ToGLCameraConverter( camera );
				m_camera = static_pointer_cast<IECoreGL::Camera>( converter->convert() );
			}
			else
			{
				m_camera = new IECoreGL::OrthographicCamera;
			}
		}

		void transform( const Imath::M44f &transform ) override
		{
			m_camera->setTransform( transform );
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			transform( samples.front() );
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			m_attributes = static_cast<const OpenGLAttributes *>( attributes );
			return true;
		}

		const IECoreGL::Camera *camera() const
		{
			return m_camera.get();
		}

	private :

		IECoreGL::CameraPtr m_camera;
		ConstOpenGLAttributesPtr m_attributes;

};

IE_CORE_FORWARDDECLARE( OpenGLCamera )

} // namespace

//////////////////////////////////////////////////////////////////////////
// OpenGLRenderer
//////////////////////////////////////////////////////////////////////////

namespace
{

class OpenGLRenderer final : public IECoreScenePreview::Renderer
{

	public :

		OpenGLRenderer( RenderType renderType, const std::string &fileName )
			:	m_renderType( renderType )
		{
			if( renderType == SceneDescription )
			{
				throw IECore::Exception( "Unsupported render type" );
			}
		}

		~OpenGLRenderer() override
		{
		}

		void option( const IECore::InternedString &name, const IECore::Data *value ) override
		{
			if( name == "camera" )
			{
				if( value == nullptr )
				{
					m_camera = "";
				}
				else if( const IECore::StringData *d = reportedCast<const IECore::StringData>( value, "option", name ) )
				{
					m_camera = d->readable();

				}
				return;
			}
			else if( name == "frame" )
			{
				// We know what this means, we just have no use for it.
				return;
			}
			else if( boost::contains( name.string(), ":" ) && !boost::starts_with( name.string(), "gl:" ) )
			{
				// Ignore options prefixed for some other renderer.
				return;
			}

			IECore::msg( IECore::Msg::Warning, "IECoreGL::Renderer::option", boost::format( "Unknown option \"%s\"." ) % name.c_str() );
		}

		void output( const IECore::InternedString &name, const Output *output ) override
		{
			if( output )
			{
				m_outputs[name] = output;
			}
			else
			{
				m_outputs.erase( name );
			}
		}

		Renderer::AttributesInterfacePtr attributes( const IECore::CompoundObject *attributes ) override
		{
			return new OpenGLAttributes( attributes );
		}

		ObjectInterfacePtr camera( const std::string &name, const IECore::Camera *camera, const AttributesInterface *attributes ) override
		{
			OpenGLCameraPtr result = new OpenGLCamera( camera );
			result->attributes( attributes );
			m_cameras[name] = result;
			return result;
		}

		ObjectInterfacePtr light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			IECore::msg( IECore::Msg::Warning, "IECoreGL::Renderer::light", "Lights are not implemented" );
			return nullptr;
		}

		Renderer::ObjectInterfacePtr object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			IECoreGL::ConstRenderablePtr renderable = runTimeCast<const IECoreGL::Renderable>(
				CachedConverter::defaultCachedConverter()->convert( object )
			);
			if( !renderable )
			{
				return nullptr;
			}
			OpenGLObjectPtr result = new OpenGLObject( renderable );
			result->attributes( attributes );
			m_objects.push_back( result );
			return result;
		}

		ObjectInterfacePtr object( const std::string &name, const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const AttributesInterface *attributes ) override
		{
			return object( name, samples.front(), attributes );
		}

		void render() override
		{
			if( m_renderType == Interactive )
			{
				renderInteractive();
			}
			else
			{
				renderBatch();
			}
		}

		void pause() override
		{
			if( m_renderType != Interactive )
			{
				IECore::msg( IECore::Msg::Warning, "IECoreGL::Renderer::pause", "Cannot pause non-interactive renders" );
			}
		}

	private :

		void renderInteractive()
		{
			removeDeletedObjects();
			CachedConverter::defaultCachedConverter()->clearUnused();

			GLint prevProgram;
			glGetIntegerv( GL_CURRENT_PROGRAM, &prevProgram );
			glPushAttrib( GL_ALL_ATTRIB_BITS );

				State::bindBaseState();
				StatePtr state = new State( /* complete = */ true );
				state->bind();

				renderObjects( state.get() );

			glPopAttrib();
			glUseProgram( prevProgram );
		}

		void renderBatch()
		{
			CachedConverter::defaultCachedConverter()->clearUnused();

			OpenGLCameraPtr camera;
			if( m_camera != "" )
			{
				CameraMap::const_iterator it = m_cameras.find( m_camera );
				if( it != m_cameras.end() )
				{
					camera = it->second;
				}
			}
			else
			{
				camera = new OpenGLCamera( nullptr );
			}

			const V2i resolution = camera->camera()->getResolution();
			IECoreGL::FrameBufferPtr frameBuffer = new FrameBuffer;
			frameBuffer->setColor( new ColorTexture( resolution.x, resolution.y ) );
			IECoreGL::Exception::throwIfError();
			frameBuffer->setDepth( new DepthTexture( resolution.x, resolution.y ) );
			IECoreGL::Exception::throwIfError();
			frameBuffer->validate();
			FrameBuffer::ScopedBinding frameBufferBinding( *frameBuffer );

			GLint prevProgram;
			glGetIntegerv( GL_CURRENT_PROGRAM, &prevProgram );
			glPushAttrib( GL_ALL_ATTRIB_BITS );

				glViewport( 0, 0, resolution.x, resolution.y );
				glClearColor( 0.0, 0.0, 0.0, 0.0 );
				glClearDepth( 1.0 );
				glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT );

				State::bindBaseState();
				StatePtr state = new State( /* complete = */ true );
				state->bind();

				camera->camera()->render( state.get() );

				renderObjects( state.get() );

				writeOutputs( frameBuffer.get() );

			glPopAttrib();
			glUseProgram( prevProgram );
		}

		// During interactive renders, the client code controls the lifetime
		// of objects by managing ObjectInterfacePtrs. But we also hold a
		// reference to the objects ourselves so that we iterate to render them.
		// Here we remove any objects with only a single reference - our own.
		// This does mean we delete objects later than the client might expect,
		// but this is actually necessary anyway, because we can only delete GL
		// resources on the main thread.
		void removeDeletedObjects()
		{
			for( auto it = m_cameras.begin(); it != m_cameras.end(); )
			{
				if( it->second->refCount() == 1 )
				{
					it = m_cameras.unsafe_erase( it );
				}
				else
				{
					++it;
				}
			}

			OpenGLObjectVector objectsToKeep;
			for( const auto &o : m_objects )
			{
				if( o->refCount() == 1 )
				{
					objectsToKeep.push_back( o );
				}
			}
			m_objects.swap( objectsToKeep );
		}

		void renderObjects( IECoreGL::State *currentState )
		{
			for( const auto &o : m_objects )
			{
				o->render( currentState );
			}
		}

		void writeOutputs( const FrameBuffer *frameBuffer )
		{
			for( const auto &namedOutput : m_outputs )
			{
				IECoreImage::ImagePrimitivePtr image = nullptr;
				const string &data = namedOutput.second->getData();
				if( data == "rgba" )
				{
					image = frameBuffer->getColor()->imagePrimitive();
				}
				else if( data == "rgb" )
				{
					image = frameBuffer->getColor()->imagePrimitive();
					image->channels.erase( "A" );
				}
				else if( data == "z" )
				{
					image = frameBuffer->getDepth()->imagePrimitive();
				}
				else
				{
					IECore::msg( IECore::Msg::Warning, "IECoreGL::Renderer", boost::format( "Unsupported data format \"%s\"." ) % data );
					return;
				}

				const string &type = namedOutput.second->getType();
				IECore::WriterPtr writer = IECore::Writer::create( image, "tmp." + type );
				if( !writer )
				{
					IECore::msg( IECore::Msg::Warning, "IECoreGL::Renderer", boost::format( "Unsupported display type \"%s\"." ) % type );
					return;
				}

				writer->parameters()->parameter<IECore::FileNameParameter>( "fileName" )->setTypedValue( namedOutput.second->getName() );
				writer->write();
			}
		}

		RenderType m_renderType;

		string m_camera;

		unordered_map<InternedString, ConstDisplayPtr> m_outputs;
		typedef tbb::concurrent_unordered_map<string, OpenGLCameraPtr> CameraMap;
		CameraMap m_cameras;
		typedef tbb::concurrent_vector<OpenGLObjectPtr> OpenGLObjectVector;
		OpenGLObjectVector m_objects;

		// Registration with factory
		static Renderer::TypeDescription<OpenGLRenderer> g_typeDescription;

};

IECoreScenePreview::Renderer::TypeDescription<OpenGLRenderer> OpenGLRenderer::g_typeDescription( "OpenGL" );

} // namespace
