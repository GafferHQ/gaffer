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
#include "GafferScene/ScenePlug.h"

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
class ScopedTransform
{
	public:
		ScopedTransform( const M44f &transform )
		{
			m_nonIdentity = transform != M44f();
			if( m_nonIdentity )
			{
				glPushMatrix();
				glMultMatrixf( transform.getValue() );
			}
		}

		~ScopedTransform()
		{
			if( m_nonIdentity )
			{
				glPopMatrix();
			}
		}

	private :
		bool m_nonIdentity;
};

template <class... Vs>
bool haveMatchingVisualisations( Visualisation::Scale scale, Visualisation::Category category, const Vs & ... visualisations )
{
	for( auto vs : { visualisations... } )
	{
		for( auto v : vs )
		{
			if( v.scale == scale && v.category & category )
			{
				return true;
			}
		}
	}
	return false;
}

template <class... Vs>
void renderMatchingVisualisations( Visualisation::Scale scale, Visualisation::Category category, IECoreGL::State *state, const Vs & ... visualisations )
{
	for( auto vs : { visualisations... } )
	{
		for( auto v : vs )
		{
			if( v.scale == scale && v.category & category )
			{
				v.renderable()->render( state );
			}
		}
	}
}

template <class... Vs>
void accumulateVisualisationBounds( Box3f &target, Visualisation::Scale scale, Visualisation::Category category, const M44f &transform, const Vs & ... visualisations )
{
	for( auto vs : { visualisations... } )
	{
		for( auto v : vs )
		{
			if( !v.affectsFramingBound || v.scale != scale || !(v.category & category) )
			{
				continue;
			}

			const Box3f b = v.renderable()->bound();
			if( !b.isEmpty() )
			{
				target.extendBy( Imath::transform( b, transform ) );
			}
		}
	}
}

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
T option( const IECore::Object *v, const IECore::InternedString &name, const T &defaultValue )
{
	if( !v )
	{
		return defaultValue;
	}
	if( auto d = reportedCast<const IECore::TypedData<T>>( v, "option", name ) )
	{
		return d->readable();
	}
	return defaultValue;
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
			: m_frustumMode( FrustumMode::WhenSelected )
		{
			const FloatData *visualiserScaleData = attributes->member<FloatData>( "gl:visualiser:scale" );
			m_visualiserScale = visualiserScaleData ? visualiserScaleData->readable() : 1.0;

			if( const StringData *drawFrustumData = attributes->member<StringData>( "gl:visualiser:frustum" ) )
			{
				if( drawFrustumData->readable() == "off" )
				{
					m_frustumMode = FrustumMode::Off;
				}
				else if( drawFrustumData->readable() == "on" )
				{
					m_frustumMode = FrustumMode::On;
				}
			}

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
					m_lightVisualisations.insert( m_lightVisualisations.end(),
						m_lightFilterVisualisations.begin(), m_lightFilterVisualisations.end()
					);
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

		const IECoreGLPreview::Visualisations &visualisations() const
		{
			return m_visualisations;
		}

		const IECoreGLPreview::Visualisations &lightVisualisations() const
		{
			return m_lightVisualisations;
		}

		const IECoreGLPreview::Visualisations &lightFilterVisualisations() const
		{
			return m_lightFilterVisualisations;
		}

		float visualiserScale() const
		{
			return m_visualiserScale;
		}

		bool drawFrustum( bool isSelected ) const
		{
			switch ( m_frustumMode )
			{
				case FrustumMode::WhenSelected :
					return isSelected;
				case FrustumMode::On :
					return true;
				default :
					return false;
			}
		}

	private :

		ConstStatePtr m_state;
		Visualisations m_visualisations;
		Visualisations m_lightVisualisations;
		Visualisations m_lightFilterVisualisations;

		enum class FrustumMode : char
		{
			Off,
			WhenSelected,
			On
		};
		FrustumMode m_frustumMode;

		float m_visualiserScale = 1.0f;
};

IE_CORE_DECLAREPTR( OpenGLAttributes )

} // namespace

//////////////////////////////////////////////////////////////////////////
// OpenGLObject
//////////////////////////////////////////////////////////////////////////

namespace
{

using Edit = std::function<void ()>;
using EditQueue = tbb::concurrent_queue<Edit>;

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
					m_objectVisualisations = visualiser->visualise( object );
					m_renderable = nullptr;
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
				m_transformSansScale = sansScalingAndShear( transform, false );
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
				const Box3f renderableBound = m_renderable->bound();
				if( !renderableBound.isEmpty() )
				{
					b.extendBy( Imath::transform( renderableBound, m_transform ) );
				}
			}

			Visualisation::Category categories = Visualisation::Category::Generic;
			// Note: We don't have access to selection state here, so we assume it is
			// selected to make sure we consider the frustum if it's enabled.
			if( m_attributes->drawFrustum( true ) )
			{
				categories = Visualisation::Category( categories | Visualisation::Category::Frustum );
			}

			const Visualisations &attrVis = visualisations( *m_attributes );

			accumulateVisualisationBounds( b, Visualisation::Scale::None, categories, m_transformSansScale, attrVis, m_objectVisualisations );
			accumulateVisualisationBounds( b, Visualisation::Scale::Local, categories, m_transform, attrVis, m_objectVisualisations );
			accumulateVisualisationBounds( b, Visualisation::Scale::Visualiser, categories, visualiserTransform( false ), attrVis, m_objectVisualisations );
			accumulateVisualisationBounds( b, Visualisation::Scale::LocalAndVisualiser, categories, visualiserTransform( true ), attrVis, m_objectVisualisations );
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
			const Visualisations &attrVis = visualisations( *m_attributes );
			const bool haveVisualisations = attrVis.size() > 0 || m_objectVisualisations.size() > 0;

			if( !haveVisualisations && !m_renderable )
			{
				return;
			}

			const bool isSelected = selected( selection );

			IECoreGL::State::ScopedBinding scope( *m_attributes->state(), *currentState );
			IECoreGL::State::ScopedBinding selectionScope( selectionState(), *currentState, isSelected );

			// In order to minimize z-fighting, we draw non-geometric visualisations
			// first and real geometry last, so that they sit on top. This is
			// still prone to flicker, but seems to provide the best results.


			if( haveVisualisations )
			{
				Visualisation::Category categories = Visualisation::Category::Generic;
				if( m_attributes->drawFrustum( isSelected ) )
				{
					categories = Visualisation::Category( categories | Visualisation::Category::Frustum );
				}

				if( m_attributes->visualiserScale() > 0.0f )
				{
					if( haveMatchingVisualisations( Visualisation::Scale::Visualiser, categories, attrVis, m_objectVisualisations ) )
					{
						ScopedTransform v( visualiserTransform( false ) );
						renderMatchingVisualisations( Visualisation::Scale::Visualiser, categories, currentState, attrVis, m_objectVisualisations );
					}

					if( haveMatchingVisualisations( Visualisation::Scale::LocalAndVisualiser, categories, attrVis, m_objectVisualisations ) )
					{
						ScopedTransform c( visualiserTransform( true ) );
						renderMatchingVisualisations( Visualisation::Scale::LocalAndVisualiser, categories, currentState, attrVis, m_objectVisualisations );
					}
				}

				if( haveMatchingVisualisations( Visualisation::Scale::None, categories, attrVis, m_objectVisualisations ) )
				{
					ScopedTransform l( m_transformSansScale );
					renderMatchingVisualisations( Visualisation::Scale::None, categories, currentState, attrVis, m_objectVisualisations );
				}

				if( m_renderable || haveMatchingVisualisations( Visualisation::Scale::Local, categories, attrVis, m_objectVisualisations ) )
				{
					ScopedTransform l( m_transform );

					renderMatchingVisualisations( Visualisation::Scale::Local, categories, currentState, attrVis, m_objectVisualisations );
					if( m_renderable ) { m_renderable->render( currentState ); }
				}

			}
			else if( m_renderable )
			{
				ScopedTransform l( m_transform );
				m_renderable->render( currentState );
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

		virtual const Visualisations &visualisations( const OpenGLAttributes &attributes ) const
		{
			return attributes.visualisations();
		}

	private :

		// sansScalingAndShear is expensive, so we store that, the other
		// visualiser scaled variants we compute in transformedBound/render
		// to save memory.

		M44f visualiserTransform( bool includeLocal ) const
		{
			M44f t = includeLocal ? m_transform : m_transformSansScale;
			t.scale( V3f( m_attributes->visualiserScale() ) );
			return t;
		}

		IECore::TypeId m_objectType;
		M44f m_transform;
		M44f m_transformSansScale;
		ConstOpenGLAttributesPtr m_attributes;
		IECoreGL::ConstRenderablePtr m_renderable;
		Visualisations m_objectVisualisations;
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

		const Visualisations &visualisations( const OpenGLAttributes &attributes ) const override
		{
			return attributes.lightVisualisations();
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

		const Visualisations &visualisations( const OpenGLAttributes &attributes ) const override
		{
			return attributes.lightFilterVisualisations();
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

		OpenGLRenderer( RenderType renderType, const std::string &fileName, const IECore::MessageHandlerPtr &messageHandler )
			:	m_renderType( renderType ), m_baseStateOptions( new CompoundObject ), m_messageHandler( messageHandler )
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
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

			if( name == "camera" )
			{
				m_camera = ::option<string>( value, name, "" );
			}
			else if( name == "frame" || name == "sampleMotion" )
			{
				// We know what these mean, we just have no use for them.
			}
			else if( name == "gl:selection" )
			{
				m_selection = ::option<IECore::PathMatcher>( value, name, IECore::PathMatcher() );
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
			}
			else if( boost::contains( name.string(), ":" ) && !boost::starts_with( name.string(), "gl:" ) )
			{
				// Ignore options prefixed for some other renderer.
			}
			else
			{
				IECore::msg( IECore::Msg::Warning, "IECoreGL::Renderer::option", boost::format( "Unknown option \"%s\"." ) % name.c_str() );
			}
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
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

			OpenGLAttributesPtr result = new OpenGLAttributes( attributes );
			m_editQueue.push( [ this, result ]() { m_attributes.push_back( result ); } );
			return result;
		}

		ObjectInterfacePtr camera( const std::string &name, const IECoreScene::Camera *camera, const AttributesInterface *attributes ) override
		{
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

			OpenGLCameraPtr result = new OpenGLCamera( name, camera, static_cast<const OpenGLAttributes *>( attributes ), m_editQueue );
			m_editQueue.push( [this, result, name]() {
				m_objects.push_back( result );
				m_cameras[name] = result;
			} );
			return result;
		}

		ObjectInterfacePtr light( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

			OpenGLLightPtr result = new OpenGLLight( name, object, static_cast<const OpenGLAttributes *>( attributes ), m_editQueue );
			m_editQueue.push( [this, result]() { m_objects.push_back( result ); } );
			return result;
		}

		ObjectInterfacePtr lightFilter( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

			OpenGLLightFilterPtr result = new OpenGLLightFilter( name, object, static_cast<const OpenGLAttributes *>( attributes ), m_editQueue );
			m_editQueue.push( [this, result]() { m_objects.push_back( result ); } );
			return result;
		}

		Renderer::ObjectInterfacePtr object( const std::string &name, const IECore::Object *object, const AttributesInterface *attributes ) override
		{
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

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
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

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
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

			if( m_renderType != Interactive )
			{
				IECore::msg( IECore::Msg::Warning, "IECoreGL::Renderer::pause", "Cannot pause non-interactive renders" );
			}
		}

		IECore::DataPtr command( const IECore::InternedString name, const IECore::CompoundDataMap &parameters ) override
		{
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

			if( name == "gl:queryBound" )
			{
				return queryBound( parameters );
			}
			else if( name == "gl:querySelection" )
			{
				return querySelectedObjects( parameters );
			}
			else if( boost::starts_with( name.string(), "gl:" ) || name.string().find( ":" ) == string::npos )
			{
				IECore::msg( IECore::Msg::Warning, "IECoreGL::Renderer::command", boost::format( "Unknown command \"%s\"." ) % name.c_str() );
			}

			return nullptr;
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
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

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

			const PathMatcher omitted = parameter<PathMatcher>( parameters, "omitted", PathMatcher() );
			const bool omittedEmpty = omitted.isEmpty();

			processQueue();
			removeDeletedObjects();

			Box3f result;
			for( const auto &o : m_objects )
			{
				if(
					( selected && !o->selected( m_selection ) ) ||
					( !omittedEmpty && ( omitted.match( o->name() ) & ( PathMatcher::AncestorMatch | PathMatcher::ExactMatch ) ) )
				)
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

		IECore::MessageHandlerPtr m_messageHandler;

		// Queue used to pass edits from background threads to the render thread.
		EditQueue m_editQueue;

		// Render state. Updated on the render thread by processing Edits
		// from m_editQueue.

		unordered_map<InternedString, ConstOutputPtr> m_outputs;
		using CameraMap = std::unordered_map<string, OpenGLCameraPtr>;
		CameraMap m_cameras;

		using OpenGLObjectVector = std::vector<OpenGLObjectPtr>;
		OpenGLObjectVector m_objects;

		using OpenGLAttributesVector = std::vector<OpenGLAttributesPtr>;
		OpenGLAttributesVector m_attributes;

		// Registration with factory
		static Renderer::TypeDescription<OpenGLRenderer> g_typeDescription;

};

IECoreScenePreview::Renderer::TypeDescription<OpenGLRenderer> OpenGLRenderer::g_typeDescription( "OpenGL" );

} // namespace
