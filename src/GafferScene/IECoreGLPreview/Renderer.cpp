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

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "GafferScene/Private/IECoreGLPreview/AttributeVisualiser.h"
#include "GafferScene/Private/IECoreGLPreview/LightVisualiser.h"
#include "GafferScene/Private/IECoreGLPreview/LightFilterVisualiser.h"
#include "GafferScene/Private/IECoreGLPreview/ObjectVisualiser.h"

#include "IECoreGL/CachedConverter.h"
#include "IECoreGL/Camera.h"
#include "IECoreGL/ColorTexture.h"
#include "IECoreGL/CurvesPrimitive.h"
#include "IECoreGL/DepthTexture.h"
#include "IECoreGL/Exception.h"
#include "IECoreGL/FrameBuffer.h"
#include "IECoreGL/GL.h"
#include "IECoreGL/Group.h"
#include "IECoreGL/PointsPrimitive.h"
#include "IECoreGL/Primitive.h"
#include "IECoreGL/Renderable.h"
#include "IECoreGL/Selector.h"
#include "IECoreGL/ShaderStateComponent.h"
#include "IECoreGL/State.h"
#include "IECoreGL/ToGLCameraConverter.h"
#include "IECoreGL/IECoreGL.h"

#include "IECore/CompoundParameter.h"
#include "IECore/MessageHandler.h"
#include "IECore/PathMatcherData.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/StringAlgo.h"
#include "IECore/Writer.h"

#include "OpenEXR/ImathBoxAlgo.h"
#include "OpenEXR/ImathMatrixAlgo.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/format.hpp"

#include "tbb/concurrent_queue.h"

#include <functional>
#include <unordered_map>
#include <vector>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreGL;
using namespace IECoreGLPreview;

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

const IECoreGL::State &selectionState()
{
	static IECoreGL::StatePtr s;
	if( !s )
	{
		s = new IECoreGL::State( false );
		s->add( new IECoreGL::Primitive::DrawWireframe( true ), /* override = */ true );
		s->add( new IECoreGL::WireframeColorStateComponent( Color4f( 0.466f, 0.612f, 0.741f, 1.0f ) ), /* override = */ true );
	}
	return *s;
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

			IECoreGL::ConstStatePtr visualisationState;
			m_visualisations = AttributeVisualiser::allVisualisations( attributes, visualisationState );

			IECoreGL::ConstStatePtr lightVisualisationState;
			m_lightVisualisations = LightVisualiser::allVisualisations( attributes, lightVisualisationState );

			IECoreGL::ConstStatePtr lightFilterVisualisationState;
			m_lightFilterVisualisations = LightFilterVisualiser::allVisualisations( attributes, lightFilterVisualisationState );

			if( !m_lightFilterVisualisations.empty() )
			{
				if( !m_lightVisualisations.empty() )
				{
					// Light filter visualisers are in `m_lightFilterVisualisations` and light visualisers are in
					// `m_lightVisualisations`. Combine them both into `m_lightVisualisations` so that
					// filters attached to light locations are drawn as expected.
					Visualisations allVisualisation;
					Private::collectVisualisations( m_lightVisualisations, allVisualisation );
					Private::collectVisualisations( m_lightFilterVisualisations, allVisualisation );
					m_lightVisualisations = allVisualisation;
				}
				else
				{
					// If we don't have a light visualisation, but do have filters, make sure they're drawn.
					m_lightVisualisations = m_lightFilterVisualisations;
				}
			}

			if( visualisationState || lightVisualisationState || lightFilterVisualisationState )
			{
				StatePtr combinedState = new State( *m_state );

				if( visualisationState )
				{
					combinedState->add( const_cast<State *>( visualisationState.get() ) );
				}

				if( lightVisualisationState )
				{
					combinedState->add( const_cast<State *>( lightVisualisationState.get() ) );
				}

				if( lightFilterVisualisationState )
				{
					combinedState->add( const_cast<State *>( lightFilterVisualisationState.get() ) );
				}

				m_state = combinedState;
			}
		}

		const State *state() const
		{
			return m_state.get();
		}

		const IECoreGL::Renderable *visualisation( VisualisationType type ) const
		{
			return m_visualisations[ type ].get();
		}

		const IECoreGL::Renderable *lightVisualisation( VisualisationType type ) const
		{
			return m_lightVisualisations[ type ].get();
		}

		const IECoreGL::Renderable *lightFilterVisualisation( VisualisationType type ) const
		{
			return m_lightFilterVisualisations[ type  ].get();
		}

	private :

		ConstStatePtr m_state;
		Visualisations m_visualisations;
		Visualisations m_lightVisualisations;
		Visualisations m_lightFilterVisualisations;

};

IE_CORE_DECLAREPTR( OpenGLAttributes )

} // namespace

//////////////////////////////////////////////////////////////////////////
// OpenGLObject
//////////////////////////////////////////////////////////////////////////

namespace
{

typedef std::function<void ()> Edit;
typedef tbb::concurrent_queue<Edit> EditQueue;

class OpenGLObject : public IECoreScenePreview::Renderer::ObjectInterface
{

	public :

		OpenGLObject( const std::string &name, const IECore::Object *object, const ConstOpenGLAttributesPtr &attributes, EditQueue &editQueue )
			:	m_objectType( object ? object->typeId() : IECore::NullObjectTypeId ),
				m_attributes( attributes ),
				m_editQueue( editQueue )
		{
			IECore::StringAlgo::tokenize( name, '/', m_name );

			if( object )
			{
				if( const ObjectVisualiser *visualiser = IECoreGLPreview::ObjectVisualiser::acquire( object->typeId() ) )
				{
					m_renderable = visualiser->visualise( object );
				}
				else
				{
					try
					{
						IECore::ConstRunTimeTypedPtr glObject = IECoreGL::CachedConverter::defaultCachedConverter()->convert( object );
						m_renderable = IECore::runTimeCast<const IECoreGL::Renderable>( glObject.get() );
					}
					catch( ... )
					{
						// Leave m_renderable as null
					}
				}
			}
		}

		void transform( const Imath::M44f &transform ) override
		{
			m_editQueue.push( [this, transform]() {
				m_transform = transform;
				m_translation = sansScalingAndShear( transform );
			} );
		}

		void transform( const std::vector<Imath::M44f> &samples, const std::vector<float> &times ) override
		{
			transform( samples.front() );
		}

		bool attributes( const IECoreScenePreview::Renderer::AttributesInterface *attributes ) override
		{
			ConstOpenGLAttributesPtr openGLAttributes = static_cast<const OpenGLAttributes *>( attributes );
			m_editQueue.push( [this, openGLAttributes]() {
				m_attributes = openGLAttributes;
			} );
			return true;
		}

		void link( const IECore::InternedString &type, const IECoreScenePreview::Renderer::ConstObjectSetPtr &objects ) override
		{
		}

		Box3f transformedBound() const
		{
			Box3f b;
			if( m_renderable )
			{
				b.extendBy( m_renderable->bound() );
			}

			if( auto v = visualisation( *m_attributes, VisualisationType::Geometry ) )
			{
				b.extendBy( v->bound() );
			}

			if( b.isEmpty() )
			{
				return b;
			}

			b = Imath::transform( b, m_transform );

			if( auto v = visualisation( *m_attributes, VisualisationType::Ornament ) )
			{
				b.extendBy( Imath::transform( v->bound(), m_translation ) );
			}

			return b;
		}

		const vector<InternedString> &name() const
		{
			return m_name;
		}

		bool selected( const IECore::PathMatcher &selection ) const
		{
			return selection.match( m_name ) & ( PathMatcher::AncestorMatch | PathMatcher::ExactMatch );
		}

		void render( IECoreGL::State *currentState, const IECore::PathMatcher &selection ) const
		{
			const bool haveTransform = m_transform != M44f();
			if( haveTransform )
			{
				glPushMatrix();
				glMultMatrixf( m_transform.getValue() );
			}

			IECoreGL::State::ScopedBinding scope( *m_attributes->state(), *currentState );
			IECoreGL::State::ScopedBinding selectionScope( selectionState(), *currentState, selected( selection ) );

			if( m_renderable )
			{
				m_renderable->render( currentState );
			}

			// Local space visualisations

			if( auto v = visualisation( *m_attributes, VisualisationType::Geometry ) )
			{
				v->render( currentState );
			}

			if( haveTransform )
			{
				glPopMatrix();
			}

			// Local scale-free visualisations

			if( auto v = visualisation( *m_attributes, VisualisationType::Ornament ) )
			{
				if( haveTransform )
				{
					glPushMatrix();
					glMultMatrixf( m_translation.getValue() );
				}

				v->render( currentState );

				if( haveTransform )
				{
					glPopMatrix();
				}
			}
		}

		IECore::TypeId objectType() const
		{
			return m_objectType;
		}

	protected :

		EditQueue &editQueue()
		{
			return m_editQueue;
		}

		virtual const IECoreGL::Renderable *visualisation( const OpenGLAttributes &attributes, VisualisationType type ) const
		{
			return attributes.visualisation( type );
		}

	private :

		IECore::TypeId m_objectType;
		M44f m_transform;
		M44f m_translation;
		ConstOpenGLAttributesPtr m_attributes;
		IECoreGL::ConstRenderablePtr m_renderable;
		vector<InternedString> m_name;
		EditQueue &m_editQueue;

};

IE_CORE_FORWARDDECLARE( OpenGLObject )

} // namespace

//////////////////////////////////////////////////////////////////////////
// OpenGLCamera
//////////////////////////////////////////////////////////////////////////

namespace
{

class OpenGLCamera : public OpenGLObject
{

	public :

		OpenGLCamera( const std::string &name, const IECoreScene::Camera *camera, const ConstOpenGLAttributesPtr &attributes, EditQueue &editQueue )
			:	OpenGLObject( name, camera, attributes, editQueue )
		{
			if( camera )
			{
				ToGLCameraConverterPtr converter = new ToGLCameraConverter( camera );
				m_camera = static_pointer_cast<IECoreGL::Camera>( converter->convert() );
				m_resolution = camera->getResolution();
			}
			else
			{
				m_camera = new IECoreGL::Camera;
				m_resolution = V2i( 640, 480 );
			}
		}

		void transform( const Imath::M44f &transform ) override
		{
			OpenGLObject::transform( transform );
			editQueue().push( [this, transform]() {
				m_camera->setTransform( transform );
			} );
		}

		const IECoreGL::Camera *camera() const
		{
			return m_camera.get();
		}

		const V2i getResolution() const
		{
			return m_resolution;
		}

	private :

		IECoreGL::CameraPtr m_camera;
		ConstOpenGLAttributesPtr m_attributes;
		V2i m_resolution;

};

IE_CORE_FORWARDDECLARE( OpenGLCamera )

} // namespace

//////////////////////////////////////////////////////////////////////////
// OpenGLLight
//////////////////////////////////////////////////////////////////////////

namespace
{

class OpenGLLight : public OpenGLObject
{

	public :

		OpenGLLight( const std::string &name, const IECore::Object *light, const ConstOpenGLAttributesPtr &attributes, EditQueue &editQueue )
			:	OpenGLObject( name, light, attributes, editQueue )
		{
		}

	protected :

		const IECoreGL::Renderable *visualisation( const OpenGLAttributes &attributes, VisualisationType type ) const override
		{
			return attributes.lightVisualisation( type );
		}

};

IE_CORE_FORWARDDECLARE( OpenGLLight )

class OpenGLLightFilter : public OpenGLObject
{

	public :

		OpenGLLightFilter( const std::string &name, const IECore::Object *object, const ConstOpenGLAttributesPtr &attributes, EditQueue &editQueue )
			:	OpenGLObject( name, object, attributes, editQueue )
		{
		}

	protected :

		const IECoreGL::Renderable *visualisation( const OpenGLAttributes &attributes, VisualisationType type ) const override
		{
			return attributes.lightFilterVisualisation( type );
		}

};

IE_CORE_FORWARDDECLARE( OpenGLLightFilter )

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
			:	m_renderType( renderType ), m_baseStateOptions( new CompoundObject )
		{
			if( renderType == SceneDescription )
			{
				throw IECore::Exception( "Unsupported render type" );
			}
		}

		~OpenGLRenderer() override
		{
		}

		IECore::InternedString name() const override
		{
			return "OpenGL";
		}

		void option( const IECore::InternedString &name, const IECore::Object *value ) override
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
			else if( name == "frame" || name == "sampleMotion" )
			{
				// We know what these mean, we just have no use for them.
				return;
			}
			else if( name == "gl:selection" )
			{
				if( value == nullptr )
				{
					m_selection.clear();
				}
				else if( auto d = reportedCast<const IECore::PathMatcherData>( value, "option", name ) )
				{
					m_selection = d->readable();
				}
				return;
			}
			else if(
				boost::starts_with( name.string(), "gl:primitive:" ) ||
				boost::starts_with( name.string(), "gl:pointsPrimitive:" ) ||
				boost::starts_with( name.string(), "gl:curvesPrimitive:" ) ||
				boost::starts_with( name.string(), "gl:smoothing:" )
			)
			{
				if( value )
				{
					m_baseStateOptions->members()[name] = value->copy();
				}
				else
				{
					m_baseStateOptions->members().erase( name );
				}
				m_baseState = nullptr; // We'll update it lazily in `baseState()`
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
			OpenGLAttributesPtr result = new OpenGLAttributes( attributes );
			m_editQueue.push( [ this, result ]() { m_attributes.push_back( result ); } );
			return result;
		}

		ObjectInterfacePtr camera( const std::string &name, const IECoreScene::Camera *camera, const AttributesInterface *attributes ) override
		{
			OpenGLCameraPtr result = new OpenGLCamera( name, camera, static_cast<const OpenGLAttributes *>( attributes ), m_editQueue );
			m_editQueue.push( [this, result, name]() {
				m_objects.push_back( result );
				m_cameras[name] = result;
			} );
			return result;
		}

		ObjectInterfacePtr light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			OpenGLLightPtr result = new OpenGLLight( name, object, static_cast<const OpenGLAttributes *>( attributes ), m_editQueue );
			m_editQueue.push( [this, result]() { m_objects.push_back( result ); } );
			return result;
		}

		ObjectInterfacePtr lightFilter( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			OpenGLLightFilterPtr result = new OpenGLLightFilter( name, object, static_cast<const OpenGLAttributes *>( attributes ), m_editQueue );
			m_editQueue.push( [this, result]() { m_objects.push_back( result ); } );
			return result;
		}

		Renderer::ObjectInterfacePtr object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			OpenGLObjectPtr result = new OpenGLObject( name, object, static_cast<const OpenGLAttributes *>( attributes ), m_editQueue );
			m_editQueue.push( [this, result]() { m_objects.push_back( result ); } );
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

		IECore::DataPtr command( const IECore::InternedString name, const IECore::CompoundDataMap &parameters ) override
		{
			if( name == "gl:queryBound" )
			{
				return queryBound( parameters );
			}
			else if( name == "gl:querySelection" )
			{
				return querySelectedObjects( parameters );
			}

			throw IECore::Exception( "Unknown command" );
		}

	private :

		void renderInteractive()
		{
			processQueue();
			removeDeletedObjects();
			CachedConverter::defaultCachedConverter()->clearUnused();

			GLint prevProgram;
			glGetIntegerv( GL_CURRENT_PROGRAM, &prevProgram );
			glPushAttrib( GL_ALL_ATTRIB_BITS );

				State::bindBaseState();
				State *state = baseState();
				state->bind();

				if( IECoreGL::Selector *selector = IECoreGL::Selector::currentSelector() )
				{
					// IECoreGL expects us to bind `selector->baseState()` here, so the
					// selector can control a few specific parts of the state.
					// That overrides _all_ of our own state though, including things that
					// are crucial to accurate selection because they change the size of
					// primitives on screen. So we need to bind the selection state and then
					// rebind the crucial bits of our state back on top of it.
					/// \todo Change IECoreGL::Selector so it provides a partial state object
					/// containing only the things it needs to change.
					IECoreGL::StatePtr shapeState = new IECoreGL::State( /* complete = */ false );
					shapeState->add( state->get<IECoreGL::PointsPrimitive::UseGLPoints>() );
					shapeState->add( state->get<IECoreGL::PointsPrimitive::GLPointWidth>() );
					shapeState->add( state->get<IECoreGL::CurvesPrimitive::UseGLLines>() );
					shapeState->add( state->get<IECoreGL::CurvesPrimitive::IgnoreBasis>() );
					shapeState->add( state->get<IECoreGL::CurvesPrimitive::GLLineWidth>() );
					IECoreGL::State::ScopedBinding selectorStateBinding(
						*selector->baseState(), const_cast<IECoreGL::State &>( *state )
					);
					IECoreGL::State::ScopedBinding shapeStateBinding(
						*shapeState, const_cast<IECoreGL::State &>( *state )
					);
					renderObjects( state );
				}
				else
				{
					renderObjects( state );
				}

			glPopAttrib();
			glUseProgram( prevProgram );
		}

		void renderBatch()
		{
			IECoreGL::init();

			processQueue();
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
				camera = new OpenGLCamera( "/defaultCamera", nullptr, nullptr, m_editQueue );
			}

			// We don't want to render the visualiser of the camera we're looking through.  For the viewport,
			// we do this using SceneView::deleteObjectFilter, but here, instead of setting up a filter,
			// we just delete the camera from the list of things to render.
			m_objects.erase( std::remove( m_objects.begin(), m_objects.end(), camera), m_objects.end() );

			const V2i resolution = camera->getResolution();
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
				State *state = baseState();
				state->bind();

				camera->camera()->render( state );

				renderObjects( state );

				writeOutputs( frameBuffer.get() );

			glPopAttrib();
			glUseProgram( prevProgram );
		}

		void processQueue()
		{
			Edit edit;
			while( m_editQueue.try_pop( edit ) )
			{
				edit();
			}
		}

		// During interactive renders, the client code controls the lifetime
		// of objects by managing ObjectInterfacePtrs. But we also hold a
		// reference to the objects ourselves so we can iterate to render them.
		// Here we remove any objects with only a single reference - our own.
		// This does mean we delete objects later than the client might expect,
		// but this is actually necessary anyway, because we can only delete GL
		// resources on the main thread.
		void removeDeletedObjects()
		{
			for( auto it = m_cameras.begin(); it != m_cameras.end(); )
			{
				// Cameras are referenced by both m_cameras and m_objects
				if( it->second->refCount() == 2 )
				{
					it = m_cameras.erase( it );
				}
				else
				{
					++it;
				}
			}

			m_objects.erase(
				remove_if(
					m_objects.begin(),
					m_objects.end(),
					[]( const OpenGLObjectPtr &o ) { return o->refCount() == 1; }
				),
				m_objects.end()
			);

			m_attributes.erase(
				remove_if(
					m_attributes.begin(),
					m_attributes.end(),
					[]( const OpenGLAttributesPtr &a ) { return a->refCount() == 1; }
				),
				m_attributes.end()
			);
		}

		void renderObjects( IECoreGL::State *currentState )
		{
			IECoreGL::Selector *selector = IECoreGL::Selector::currentSelector();

			GLuint i = 1;
			for( const auto &o : m_objects )
			{
				if( selector )
				{
					selector->loadName( i++ );
				}
				o->render( currentState, m_selection );
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

		DataPtr queryBound( const CompoundDataMap &parameters )
		{
			const bool selected = parameter<bool>( parameters, "selection", false );

			processQueue();
			removeDeletedObjects();

			Box3f result;
			for( const auto &o : m_objects )
			{
				if( selected && !o->selected( m_selection ) )
				{
					continue;
				}
				result.extendBy( o->transformedBound() );
			}
			return new Box3fData( result );
		}

		DataPtr querySelectedObjects( const CompoundDataMap &parameters )
		{
			ConstUIntVectorDataPtr names;
			CompoundDataMap::const_iterator it = parameters.find( "selection" );
			if( it != parameters.end() )
			{
				names = runTimeCast<const UIntVectorData>( it->second );
			}
			if( !names )
			{
				throw InvalidArgumentException( "Expected UIntVectorData \"selection\" parameter" );
			}

			vector<IECore::TypeId> maskTypeIds;
			it = parameters.find( "mask" );
			if( it != parameters.end() )
			{
				if( ConstStringVectorDataPtr typeNames = runTimeCast<const StringVectorData>( it->second ) )
				{
					for( const auto &n : typeNames->readable() )
					{
						maskTypeIds.push_back( RunTimeTyped::typeIdFromTypeName( n.c_str() ) );
					}
				}
				else
				{
					throw InvalidArgumentException( "Expected StringVectorData for \"mask\" parameter" );
				}
			}
			else
			{
				maskTypeIds.push_back( IECore::ObjectTypeId );
			}

			PathMatcher result;
			for( auto i : names->readable() )
			{
				const OpenGLObject *o = m_objects[i-1].get();
				for( auto t : maskTypeIds )
				{
					if( t == o->objectType() || RunTimeTyped::inheritsFrom( o->objectType(), t ) )
					{
						result.addPath( o->name() );
						break;
					}
				}
			}

			return new PathMatcherData( result );
		}

		IECoreGL::State *baseState()
		{
			if( !m_baseState )
			{
				m_baseState = new IECoreGL::State( /* complete = */ true );
				IECoreGL::ConstStatePtr optionsState = static_pointer_cast<const State>(
					CachedConverter::defaultCachedConverter()->convert( m_baseStateOptions.get() )
				);
				m_baseState->add( const_pointer_cast<State>( optionsState ) );
			}
			return m_baseState.get();
		}

		// Global options
		RenderType m_renderType;
		string m_camera;
		IECore::PathMatcher m_selection;
		IECore::CompoundObjectPtr m_baseStateOptions;
		IECoreGL::StatePtr m_baseState;

		// Queue used to pass edits from background threads to the render thread.
		EditQueue m_editQueue;

		// Render state. Updated on the render thread by processing Edits
		// from m_editQueue.

		unordered_map<InternedString, ConstOutputPtr> m_outputs;
		typedef std::unordered_map<string, OpenGLCameraPtr> CameraMap;
		CameraMap m_cameras;

		typedef std::vector<OpenGLObjectPtr> OpenGLObjectVector;
		OpenGLObjectVector m_objects;

		typedef std::vector<OpenGLAttributesPtr> OpenGLAttributesVector;
		OpenGLAttributesVector m_attributes;

		// Registration with factory
		static Renderer::TypeDescription<OpenGLRenderer> g_typeDescription;

};

IECoreScenePreview::Renderer::TypeDescription<OpenGLRenderer> OpenGLRenderer::g_typeDescription( "OpenGL" );

} // namespace
