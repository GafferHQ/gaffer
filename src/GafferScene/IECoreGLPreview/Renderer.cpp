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
#include "GafferScene/Private/IECoreScenePreview/Placeholder.h"
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
#include "IECoreGL/ShaderLoader.h"
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

#include "Imath/ImathBoxAlgo.h"
#include "Imath/ImathMatrixAlgo.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/container/flat_map.hpp"

#include "tbb/concurrent_queue.h"
#include "tbb/concurrent_unordered_map.h"

#include "fmt/format.h"

#include <functional>
#include <mutex>
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
bool haveMatchingVisualisations( Visualisation::ColorSpace colorSpace, Visualisation::Scale scale, Visualisation::Category category, const Vs & ... visualisations )
{
	for( auto vs : { visualisations... } )
	{
		for( auto v : vs )
		{
			if( v.colorSpace == colorSpace && v.scale == scale && v.category & category )
			{
				return true;
			}
		}
	}
	return false;
}

template <class... Vs>
void renderMatchingVisualisations( Visualisation::ColorSpace colorSpace, Visualisation::Scale scale, Visualisation::Category category, IECoreGL::State *state, const Vs & ... visualisations )
{
	for( auto vs : { visualisations... } )
	{
		for( auto v : vs )
		{
			if( v.colorSpace == colorSpace && v.scale == scale && v.category & category )
			{
				v.renderable->render( state );
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

			const Box3f b = v.renderable->bound();
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

	IECore::msg( IECore::Msg::Warning, "IECoreGL::Renderer", fmt::format( "Expected {} but got {} for {} \"{}\".", T::staticTypeName(), v->typeName(), type, name.string() ) );
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

const IECoreGL::State &selectedSceneState()
{
	static IECoreGL::StatePtr s;
	if( !s )
	{
		s = new IECoreGL::State( false );
		// Turn off wireframe when rendering `ColorSpace::Scene`, because we'll
		// be using it for a selection overlay in `ColorSpace::Display`.
		s->add( new IECoreGL::Primitive::DrawWireframe( false ), /* override = */ true );
	}
	return *s;
}

const IECoreGL::State &selectedCurvesSceneState()
{
	static IECoreGL::StatePtr s;
	if( !s )
	{
		s = new IECoreGL::State( false );
		// Turn off wireframe as for `selectedSceneState()`, but also turn off solid drawing
		// because it also conflicts with the wireframe.
		s->add( new IECoreGL::Primitive::DrawWireframe( false ), /* override = */ true );
		s->add( new IECoreGL::Primitive::DrawSolid( false ), /* override = */ true );
	}
	return *s;
}

const IECoreGL::State &selectedPointsSceneState()
{
	static IECoreGL::StatePtr s;
	if( !s )
	{
		s = new IECoreGL::State( false );
		// See above.
		s->add( new IECoreGL::Primitive::DrawWireframe( false ), /* override = */ true );
		s->add( new IECoreGL::Primitive::DrawSolid( false ), /* override = */ true );
		s->add( new IECoreGL::Primitive::DrawPoints( false ), /* override = */ true );
	}
	return *s;
}

const Color4f selectedColor( 0.466f, 0.612f, 0.741f, 1.0f );

const IECoreGL::State &selectedDisplayState()
{
	static IECoreGL::StatePtr s;
	if( !s )
	{
		s = new IECoreGL::State( false );
		s->add( new IECoreGL::Primitive::DrawPoints( false ), /* override = */ true );
		s->add( new IECoreGL::Primitive::DrawSolid( false ), /* override = */ true );
		s->add( new IECoreGL::Primitive::DrawWireframe( true ), /* override = */ true );
		s->add( new IECoreGL::WireframeColorStateComponent( selectedColor ), /* override = */ true );
	}
	return *s;
}

const IECoreGL::State &selectedVisualiserDisplayState()
{
	static IECoreGL::StatePtr s;
	if( !s )
	{
		s = new IECoreGL::State( false );
		s->add( new IECoreGL::Primitive::DrawPoints( false ), /* override = */ true );
		s->add( new IECoreGL::Primitive::DrawSolid( true ), /* override = */ true );
		s->add( new IECoreGL::Primitive::DrawWireframe( true ), /* override = */ true );
		s->add( new IECoreGL::WireframeColorStateComponent( selectedColor ), /* override = */ true );
		s->add( new IECoreGL::Color( selectedColor ), /* override = */ true );
	}
	return *s;
}

const IECoreGL::State &selectionState( const IECoreGL::Renderable *renderable, const IECoreGL::State *currentState, Visualisation::ColorSpace colorSpace )
{
	if( colorSpace == Visualisation::ColorSpace::Display )
	{
		return selectedDisplayState();
	}

	switch( (IECoreGL::TypeId)renderable->typeId() )
	{
		case IECoreGL::PointsPrimitiveTypeId :
			if( static_cast<const IECoreGL::PointsPrimitive *>( renderable )->renderUsesGLPoints( currentState ) ) {
				return selectedPointsSceneState();
			} else {
				return selectedSceneState();
			}
		case IECoreGL::CurvesPrimitiveTypeId :
			if( static_cast<const IECoreGL::CurvesPrimitive *>( renderable )->renderUsesGLLines( currentState ) ) {
				return selectedCurvesSceneState();
			} else {
				return selectedSceneState();
			}
		default :
			return selectedSceneState();
	}
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
			:	m_frustumMode( FrustumMode::WhenSelected ), m_visualisationStateColorSpace( Visualisation::ColorSpace::Display )
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
				StatePtr combinedState = new State( /* complete = */ false );

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

				m_visualisationState = combinedState;
				auto solidState = m_visualisationState->get<IECoreGL::Primitive::DrawSolid>();
				// The Visualiser API doesn't currently allow a colour space to
				// be associated with the visualisation state. So we use a
				// heuristic : if the state includes solid drawing then we
				// assume Scene space. This allows custom mesh light texture
				// visualisers to be shown with an appropriate colour transform.
				// Otherwise we assume Display space, which gives us what we
				// want for the coloured outline from our own mesh light
				// visualiser.
				if( !solidState || solidState->value() )
				{
					m_visualisationStateColorSpace = Visualisation::ColorSpace::Scene;
				}
			}
		}

		const State *state() const
		{
			return m_state.get();
		}

		const State *visualisationState( Visualisation::ColorSpace colorSpace ) const
		{
			return colorSpace == m_visualisationStateColorSpace ? m_visualisationState.get() : nullptr;
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
		ConstStatePtr m_visualisationState;
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
		Visualisation::ColorSpace m_visualisationStateColorSpace;
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

		/// Constructs with a pre-built renderable, using `sourceObjectType` as
		/// the type for `gl:querySelection` masking.
		OpenGLObject( const std::string &name, const IECoreGL::ConstRenderablePtr &renderable, IECore::TypeId sourceObjectType, const ConstOpenGLAttributesPtr &attributes, EditQueue &editQueue )
			:	m_objectType( sourceObjectType ),
				m_attributes( attributes ),
				m_renderable( renderable ),
				m_editQueue( editQueue )
		{
			IECore::StringAlgo::tokenize( name, '/', m_name );
		}

		void transform( const IECoreScenePreview::Renderer::TransformSamples &samples, const IECoreScenePreview::Renderer::SampleTimes &times ) override
		{
			m_editQueue.push( [this, transform=samples.front()]() {
				m_transform = transform;
				m_transformSansScale = sansScalingAndShear( transform, false );
			} );
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

		void assignID( uint32_t id ) override
		{
			// The GL renderer provides a more lightweight ID mechanism where
			// IDs are just the index in the object list, and don't need
			// assigning. This is exposed via the `gl:querySelection` command.
			// So we don't implement `assignID()` for now.
			/// \todo Evaluate overhead of the more general ID mechanism, and
			/// consider dropping the custom OpenGL one.
		}

		void assignInstanceID( uint32_t instanceID ) override
		{
			// The GL renderer doesn't support encapsulated instancers, so we have no
			// need for instance ids.
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

		void render( IECoreGL::State *currentState, const IECore::PathMatcher &selection, Visualisation::ColorSpace colorSpace ) const
		{
			const Visualisations &attrVis = visualisations( *m_attributes );
			const bool haveVisualisations = attrVis.size() > 0 || m_objectVisualisations.size() > 0;

			if( !haveVisualisations && !m_renderable )
			{
				return;
			}

			const bool isSelected = selected( selection );

			// In order to minimize z-fighting, we draw non-geometric visualisations
			// first and real geometry last, so that they sit on top. This is
			// still prone to flicker, but seems to provide the best results.

			if( haveVisualisations )
			{
				IECoreGL::State::ScopedBinding selectionScope(
					selectedVisualiserDisplayState(), *currentState, isSelected && colorSpace == Visualisation::ColorSpace::Display
				);

				Visualisation::Category categories = Visualisation::Category::Generic;
				if( m_attributes->drawFrustum( isSelected ) )
				{
					categories = Visualisation::Category( categories | Visualisation::Category::Frustum );
				}

				if( m_attributes->visualiserScale() > 0.0f )
				{
					if( haveMatchingVisualisations( colorSpace, Visualisation::Scale::Visualiser, categories, attrVis, m_objectVisualisations ) )
					{
						ScopedTransform v( visualiserTransform( false ) );
						renderMatchingVisualisations( colorSpace, Visualisation::Scale::Visualiser, categories, currentState, attrVis, m_objectVisualisations );
					}

					if( haveMatchingVisualisations( colorSpace, Visualisation::Scale::LocalAndVisualiser, categories, attrVis, m_objectVisualisations ) )
					{
						ScopedTransform c( visualiserTransform( true ) );
						renderMatchingVisualisations( colorSpace, Visualisation::Scale::LocalAndVisualiser, categories, currentState, attrVis, m_objectVisualisations );
					}
				}

				if( haveMatchingVisualisations( colorSpace, Visualisation::Scale::None, categories, attrVis, m_objectVisualisations ) )
				{
					ScopedTransform l( m_transformSansScale );
					renderMatchingVisualisations( colorSpace, Visualisation::Scale::None, categories, currentState, attrVis, m_objectVisualisations );
				}

				if( haveMatchingVisualisations( colorSpace, Visualisation::Scale::Local, categories, attrVis, m_objectVisualisations ) )
				{
					ScopedTransform l( m_transform );
					renderMatchingVisualisations( colorSpace, Visualisation::Scale::Local, categories, currentState, attrVis, m_objectVisualisations );
				}
			}

			// Objects are rendered into `ColorSpace::Scene`, with the caveat that selection
			// overlays and additional visualisations are drawn into `ColorSpace::Display`.

			const IECoreGL::State *visualisationState = m_attributes->visualisationState( colorSpace );
			if( m_renderable && ( colorSpace == Visualisation::ColorSpace::Scene || isSelected || visualisationState ) )
			{
				IECoreGL::State::ScopedBinding stateScope( *m_attributes->state(), *currentState );
				std::optional<IECoreGL::State::ScopedBinding> visualisationStateScope;
				if( visualisationState )
				{
					visualisationStateScope.emplace( *visualisationState, *currentState );
				}
				IECoreGL::State::ScopedBinding selectionScope(
					selectionState( m_renderable. get(), currentState, colorSpace ),
					*currentState, isSelected
				);

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
// PointInstancerCache
//////////////////////////////////////////////////////////////////////////

namespace
{

// Vertex shader that places each vertex of a prototype using a per-instance
// transform. Outputs match those of `IECoreGL::Shader::defaultVertexSource()`,
// so that it can be paired with any fragment and geometry shader that would
// work with the default.
const std::string g_instancingVertexSource = R"(

#version 120

#if __VERSION__ <= 120
#define in attribute
#define out varying
#endif

// Guarantees identical depths between our shaded, constant and ID
// variants, so that `GL_LEQUAL` depth testing works for overlays.
invariant gl_Position;

uniform vec3 Cs = vec3( 1, 1, 1 );
uniform bool vertexCsActive = false;
uniform bool vertexNActive = false;

in vec3 vertexP;
in vec3 vertexN;
in vec2 vertexuv;
in vec3 vertexCs;

// Per-instance transform components.
in vec3 instanceP;
in vec4 instanceOrientation; // Imath layout - real part is in `x` and imaginary part is in `yzw`.
in vec3 instanceScale;
uniform bool instancePActive = false;
uniform bool instanceOrientationActive = false;
uniform bool instanceScaleActive = false;

out vec3 geometryI;
out vec3 geometryP;
out vec3 geometryN;
out vec2 geometryuv;
out vec3 geometryCs;
out float geometryIsCurveEndPoint;

out vec3 fragmentI;
out vec3 fragmentP;
out vec3 fragmentN;
out vec2 fragmentuv;
out vec3 fragmentCs;

vec3 rotate( vec4 q, vec3 v )
{
	vec3 u = q.yzw;
	return v + 2.0 * cross( u, cross( u, v ) + q.x * v );
}

void main()
{
	vec3 translation = instancePActive ? instanceP : vec3( 0.0 );
	vec3 scale = instanceScaleActive ? instanceScale : vec3( 1.0 );
	vec4 orientation = vec4( 1.0, 0.0, 0.0, 0.0 );
	if( instanceOrientationActive )
	{
		float orientationLength = length( instanceOrientation );
		if( orientationLength > 0.0 )
		{
			orientation = instanceOrientation / orientationLength;
		}
	}

	vec3 p = rotate( orientation, vertexP * scale ) + translation;
	vec4 pCam = gl_ModelViewMatrix * vec4( p, 1 );
	gl_Position = gl_ProjectionMatrix * pCam;
	geometryP = pCam.xyz;

	if( vertexNActive )
	{
		// Transform by the inverse transpose of the scale, using cofactors rather
		// than reciprocals so that zero scales are handled gracefully. This differs
		// from the true inverse transpose by a scale factor, which is removed by
		// normalisation, but we must account for the sign of the determinant.
		vec3 n = vertexN * vec3( scale.y * scale.z, scale.x * scale.z, scale.x * scale.y );
		n = rotate( orientation, n ) * ( scale.x * scale.y * scale.z < 0.0 ? -1.0 : 1.0 );
		geometryN = normalize( gl_NormalMatrix * n );
	}
	else
	{
		geometryN = vec3( 0.0, 0.0, 1.0 );
	}

	if( gl_ProjectionMatrix[2][3] != 0.0 )
	{
		geometryI = normalize( -pCam.xyz );
	}
	else
	{
		geometryI = vec3( 0, 0, -1 );
	}

	geometryuv = vertexuv;
	geometryCs = mix( Cs, vertexCs, float( vertexCsActive ) );
	geometryIsCurveEndPoint = 0.0;

	fragmentI = geometryI;
	fragmentP = geometryP;
	fragmentN = geometryN;
	fragmentuv = geometryuv;
	fragmentCs = geometryCs;
}

)";

// Instances a single prototype from a `PointInstancer`, using a single
// instanced draw call provided by `prototype->renderInstances()`. This is the
// same approach as taken by `IECoreGL::PointsPrimitive` to draw
// quads/disks/spheres.
class InstancedPrimitive : public IECoreGL::Primitive
{

	public :

		IE_CORE_DECLAREMEMBERPTR( InstancedPrimitive )

		InstancedPrimitive( const IECoreGL::ConstPrimitivePtr &prototype, const IECoreScene::PointInstancer *pointInstancer, const std::vector<size_t> &pointIndices )
			:	m_prototype( prototype ), m_numInstances( pointIndices.size() )
		{
			// Build arrays containing only the specific points our prototype is applied to.
			/// \todo For an instancer with a single prototype and non-indexed arrays, we
			/// could just reference the input data directly.

			const auto position = pointInstancer->getPosition();
			const auto orientation = pointInstancer->getOrientation();
			const auto scale = pointInstancer->getScale();

			V3fVectorDataPtr p = position ? new V3fVectorData : nullptr;
			QuatfVectorDataPtr o = orientation ? new QuatfVectorData : nullptr;
			V3fVectorDataPtr s = scale ? new V3fVectorData : nullptr;

			const IECoreScene::PointInstancer::TransformQuery transformQuery( *pointInstancer );
			const Box3f prototypeBound = m_prototype->bound();
			for( auto pointIndex : pointIndices )
			{
				if( p )
				{
					p->writable().push_back( position[pointIndex] );
				}
				if( o )
				{
					o->writable().push_back( orientation[pointIndex] );
				}
				if( s )
				{
					s->writable().push_back( scale[pointIndex] );
				}
				m_bound.extendBy( Imath::transform( prototypeBound, transformQuery.transform( pointIndex ) ) );
			}

			m_instanceP = p;
			m_instanceOrientation = o;
			m_instanceScale = s;
		}

		// Implementation of `IECoreGL::Primitive` API.

		void addPrimitiveVariable( const std::string &name, const PrimitiveVariable &primVar ) override
		{
			// No need to implement, as won't be called.
		}

		Box3f bound() const override
		{
			return m_bound;
		}

		// Called by the Primitive base class to acquire a shader setup for rendering this primitive
		// with the specified state. This is our chance to switch in our special instancing vertex
		// shader.
		const IECoreGL::Shader::Setup *shaderSetup( const IECoreGL::Shader *shader, IECoreGL::State *state ) const override
		{
			IECoreGL::ShaderStateComponent *shaderStateComponent = state->get<IECoreGL::ShaderStateComponent>();

			// `shader` may be the state's shader or one of `Primitive::render()`'s
			// constant/ID variants. We bake the state's parameters into the setup,
			// so must key on the state's hash as well as the shader.
			IECoreGL::Shader::SetupPtr &setup = m_shaderSetups[{ shader, shaderStateComponent->hash() }];
			if( setup )
			{
				return setup.get();
			}

			IECoreGL::ConstShaderPtr instancingShader = shaderStateComponent->shaderLoader()->create(
				g_instancingVertexSource, shader->geometrySource(), shader->fragmentSource()
			);

			setup = new IECoreGL::Shader::Setup( instancingShader );
			shaderStateComponent->addParametersToShaderSetup( setup.get() );
			m_prototype->addPrimitiveVariablesToShaderSetup( setup.get() );
			addInstanceAttribute( setup.get(), "instanceP", m_instanceP.get() );
			addInstanceAttribute( setup.get(), "instanceOrientation", m_instanceOrientation.get() );
			addInstanceAttribute( setup.get(), "instanceScale", m_instanceScale.get() );

			return setup.get();
		}

		/// Called by the Primitive base class to render this primitive in one
		// of various styles - solid, wireframe etc. Implemented to call the
		// prototypes `renderInstances()` method, allowing our shader to instance
		// onto the points.
		void render( const IECoreGL::State *state, IECore::TypeId style ) const override
		{
			// Since we're bypassing the prototype's own `render( state, style )`, we're
			// on the hook for applying any GL point/line widths it would have set.
			if( runTimeCast<const IECoreGL::CurvesPrimitive>( m_prototype.get() ) )
			{
				if( style == IECoreGL::Primitive::DrawSolid::staticTypeId() || style == IECoreGL::Primitive::DrawWireframe::staticTypeId() )
				{
					glLineWidth( state->get<IECoreGL::CurvesPrimitive::GLLineWidth>()->value() );
				}
			}
			else if( style == IECoreGL::Primitive::DrawSolid::staticTypeId() )
			{
				glPointSize( state->get<IECoreGL::PointsPrimitive::GLPointWidth>()->value() );
			}

			if( style != IECoreGL::Primitive::DrawSolid::staticTypeId() )
			{
				// Allow overlays like wireframe to win out over the underlying
				// solid drawing. The base class uses `glPolygonOffset()` for
				// this, but that doesn't work for points and lines.
				/// \todo Maybe the base class should be doing this for us?
				glDepthFunc( GL_LEQUAL );
			}

			m_prototype->renderInstances( m_numInstances );
		}

		void renderInstances( size_t numInstances ) const override
		{
			// Unused. We're the instancer - nobody is instancing us.
		}

	private :

		static void addInstanceAttribute( IECoreGL::Shader::Setup *setup, const std::string &name, const IECore::Data *data )
		{
			if( data )
			{
				setup->addVertexAttribute( name, data, /* divisor = */ 1 );
				setup->addUniformParameter( name + "Active", new BoolData( true ) );
			}
		}

		IECoreGL::ConstPrimitivePtr m_prototype;
		size_t m_numInstances;
		IECore::ConstV3fVectorDataPtr m_instanceP;
		IECore::ConstQuatfVectorDataPtr m_instanceOrientation;
		IECore::ConstV3fVectorDataPtr m_instanceScale;
		Box3f m_bound;
		// Only accessed on the render thread.
		using ShaderSetupKey = std::pair<IECoreGL::ConstShaderPtr, IECore::MurmurHash>;
		mutable boost::container::flat_map<ShaderSetupKey, IECoreGL::Shader::SetupPtr> m_shaderSetups;

};

class PointInstancerCache
{

	public :

		// Can be called concurrently with other calls to `get()`.
		IECoreGL::RenderablePtr get( const IECoreScene::PointInstancer *instancer, const std::vector<IECoreScenePreview::Renderer::Prototype> &prototypes )
		{
			// Get a unique hash for the prototype geometry and instancer. We
			// don't need to consider the prototype attributes, because we don't
			// include those in the cache entry.

			IECore::MurmurHash h = instancer->Object::hash();
			for( const auto &prototype : prototypes )
			{
				if( prototype.samples.size() )
				{
					prototype.samples[0]->hash( h );
				}
			}

			// Look up cache entry, and ensure it is populated.

			CacheEntry &cacheEntry = m_cache[h];
			std::call_once(

				cacheEntry.onceFlag,

				[&] {

					// Start with all null primitives.

					cacheEntry.instancedPrototypes.resize( prototypes.size() );

					// Build lists of which points each prototype should be
					// instanced onto.

					const auto prototypeIndices = instancer->getPrototypeIndex();
					if( !prototypeIndices )
					{
						return;
					}

					IECoreScene::PointInstancer::VisibilityQuery visibilityQuery( *instancer );
					std::vector<std::vector<size_t>> prototypePoints( prototypes.size() );

					for( size_t pointIndex = 0; pointIndex < prototypeIndices.size(); ++pointIndex )
					{
						const int p = prototypeIndices[pointIndex];
						if( p >= 0 && p < (int)prototypes.size() && visibilityQuery.visible( pointIndex ) )
						{
							prototypePoints[p].push_back( pointIndex );
						}
					}

					// Make an InstancedPrimitive for each prototype.

					for( size_t prototypeIndex = 0; prototypeIndex < prototypes.size(); ++prototypeIndex )
					{
						if( prototypePoints[prototypeIndex].empty() || prototypes[prototypeIndex].samples.empty() )
						{
							continue;
						}

						IECoreGL::ConstPrimitivePtr primitive;
						try
						{
							primitive = runTimeCast<const IECoreGL::Primitive>(
								IECoreGL::CachedConverter::defaultCachedConverter()->convert( prototypes[prototypeIndex].samples.front().get() )
							);
						}
						catch( ... )
						{
							// Leave primitive as null
						}

						if( !primitive )
						{
							continue;
						}

						cacheEntry.instancedPrototypes[prototypeIndex] = new InstancedPrimitive( primitive, instancer, prototypePoints[prototypeIndex] );
					}
				}

			);

			// Build a unique Group which reunites the cached InstancedPrototypes with
			// the attributes for each prototype they represent.

			IECoreGL::GroupPtr result = new IECoreGL::Group;
			for( size_t prototypeIndex = 0; prototypeIndex < prototypes.size(); ++prototypeIndex )
			{
				if( !cacheEntry.instancedPrototypes[prototypeIndex] )
				{
					continue;
				}
				IECoreGL::GroupPtr prototypeGroup = new IECoreGL::Group;
				prototypeGroup->setState( const_cast<IECoreGL::State *>( static_cast<const OpenGLAttributes *>( prototypes[prototypeIndex].attributes.get() )->state() ) );
				prototypeGroup->addChild( cacheEntry.instancedPrototypes[prototypeIndex] );
				result->addChild( prototypeGroup );
			}

			return result;
		}

		// Must not be called concurrently with anything.
		void clearUnused()
		{
			for( auto it = m_cache.begin(); it != m_cache.end(); )
			{
				const bool ours = std::all_of(
					it->second.instancedPrototypes.begin(), it->second.instancedPrototypes.end(),
					[] ( const InstancedPrimitive::Ptr &p ) {
						return !p || p->refCount() <= 1;
					}
				);
				if( ours )
				{
					// No references from outside cache.
					it = m_cache.unsafe_erase( it );
				}
				else
				{
					++it;
				}
			}
		}

	private :

		struct CacheEntry
		{
			std::once_flag onceFlag;
			std::vector<InstancedPrimitive::Ptr> instancedPrototypes;
		};
		using Cache = tbb::concurrent_unordered_map<IECore::MurmurHash, CacheEntry>;
		Cache m_cache;

};

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

		void transform(const IECoreScenePreview::Renderer::TransformSamples &samples, const IECoreScenePreview::Renderer::SampleTimes &times) override
		{
			OpenGLObject::transform( samples, times );
			editQueue().push( [this, transform=samples.front()]() {
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

const std::string g_headerPrefix( "header:" );

class OpenGLRenderer final : public IECoreScenePreview::Renderer
{

	public :

		OpenGLRenderer( RenderType renderType, const std::string &fileName, const IECore::MessageHandlerPtr &messageHandler )
			:	m_renderType( renderType ), m_baseStateOptions( new CompoundObject ),
				m_renderObjects( true ), m_messageHandler( messageHandler ),
				m_pointInstancerCache( std::make_unique<PointInstancerCache>() )
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
			else if( name == "gl:drawingExclusions" )
			{
				m_drawingExclusions = ::option<IECore::PathMatcher>( value, name, IECore::PathMatcher() );
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
			/// \todo We can't support this being modified after the scene has
			/// already been generated, because we've thrown away the source
			/// objects already. This is similar to `ai:ignore_subdivision`.
			/// Perhaps `option()` should have a return value to indicate to the
			/// RenderController that it needs to resend objects?
			else if( name == "gl:renderObjects" )
			{
				m_renderObjects = ::option<bool>( value, name, true );
			}
			else if( boost::contains( name.string(), ":" ) && !boost::starts_with( name.string(), "gl:" ) )
			{
				// Ignore options prefixed for some other renderer.
			}
			else
			{
				IECore::msg( IECore::Msg::Warning, "IECoreGL::Renderer::option", fmt::format( "Unknown option \"{}\".", name.string() ) );
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

		ObjectInterfacePtr camera( const std::string &name, const CameraSamples &samples, const SampleTimes &times, const AttributesInterface *attributes ) override
		{
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

			ConstOpenGLAttributesPtr openGLAttributes = static_cast<const OpenGLAttributes *>( attributes );
			if( !openGLAttributes )
			{
				ConstCompoundObjectPtr emptyAttributes = new CompoundObject;
				openGLAttributes = new OpenGLAttributes( emptyAttributes.get() );
			}

			OpenGLCameraPtr result = new OpenGLCamera( name, samples.front().get(), openGLAttributes, m_editQueue );
			m_editQueue.push( [this, result, name]() {
				m_objects.push_back( result );
				m_cameras[name] = result;
			} );
			return result;
		}

		ObjectInterfacePtr light( const std::string &name, const ObjectSamples &samples, const SampleTimes &times, const AttributesInterface *attributes ) override
		{
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

			OpenGLLightPtr result = new OpenGLLight( name, samples.size() ? samples[0].get() : nullptr, static_cast<const OpenGLAttributes *>( attributes ), m_editQueue );
			m_editQueue.push( [this, result]() { m_objects.push_back( result ); } );
			return result;
		}

		ObjectInterfacePtr lightFilter( const std::string &name, const ObjectSamples &samples, const SampleTimes &times, const AttributesInterface *attributes ) override
		{
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

			OpenGLLightFilterPtr result = new OpenGLLightFilter( name, samples.size() ? samples[0].get() : nullptr, static_cast<const OpenGLAttributes *>( attributes ), m_editQueue );
			m_editQueue.push( [this, result]() { m_objects.push_back( result ); } );
			return result;
		}

		ObjectInterfacePtr object( const std::string &name, const ObjectSamples &samples, const SampleTimes &times, const AttributesInterface *attributes ) override
		{
			const IECore::Object *object = samples.front().get();
			if( !m_renderObjects && !runTimeCast<const IECoreScenePreview::Placeholder>( object ) )
			{
				return nullptr;
			}

			IECore::MessageHandler::Scope s( m_messageHandler.get() );

			OpenGLObjectPtr result = new OpenGLObject( name, object, static_cast<const OpenGLAttributes *>( attributes ), m_editQueue );
			m_editQueue.push( [this, result]() { m_objects.push_back( result ); } );
			return result;
		}

		ObjectInterfacePtr pointInstancer( const std::string &name, const PointInstancerSamples &samples, const SampleTimes &times, const std::vector<Prototype> &prototypes, const AttributesInterface *attributes ) override
		{
			if( !m_renderObjects )
			{
				return nullptr;
			}

			IECore::MessageHandler::Scope s( m_messageHandler.get() );

			OpenGLObjectPtr result = new OpenGLObject(
				name, m_pointInstancerCache->get( samples.front().get(), prototypes ), IECoreScene::PointInstancer::staticTypeId(),
				static_cast<const OpenGLAttributes *>( attributes ), m_editQueue
			);
			m_editQueue.push( [this, result]() { m_objects.push_back( result ); } );
			return result;
		}

		void render() override
		{
			IECore::MessageHandler::Scope s( m_messageHandler.get() );

			if( m_renderType == Interactive )
			{
				// We currently don't have any use for interactively rendering
				// to outputs defined by the `output()` function. To facilitate
				// interactive use in a CompoundRenderer (where the other
				// renderer _is_ rendering to the outputs), we instead define a
				// separate `gl:renderToCurrentContext` command which renders
				// into a framebuffer managed by the client.
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
			else if( name == "gl:renderToCurrentContext" )
			{
				renderToCurrentContext( parameters );
				return nullptr;
			}
			else if( boost::starts_with( name.string(), "gl:" ) || name.string().find( ":" ) == string::npos )
			{
				IECore::msg( IECore::Msg::Warning, "IECoreGL::Renderer::command", fmt::format( "Unknown command \"{}\".", name.string() ) );
			}

			return nullptr;
		}

	private :

		void renderToCurrentContext( const IECore::CompoundDataMap &parameters )
		{
			const string colorSpaceString = parameter<string>( parameters, "colorSpace", "scene" );
			const Visualisation::ColorSpace colorSpace = colorSpaceString == "scene" ? Visualisation::ColorSpace::Scene : Visualisation::ColorSpace::Display;

			processQueue();
			removeDeletedObjects();
			m_pointInstancerCache->clearUnused();
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
					shapeState->add( state->get<IECoreGL::Primitive::DrawWireframe>() );
					shapeState->add( state->get<IECoreGL::Primitive::DrawSolid>() );
					shapeState->add( state->get<IECoreGL::Primitive::DrawOutline>() );
					shapeState->add( state->get<IECoreGL::Primitive::DrawPoints>() );
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
					renderObjects( state, colorSpace );
				}
				else
				{
					renderObjects( state, colorSpace );
				}

			glPopAttrib();
			glUseProgram( prevProgram );
		}

		void renderBatch()
		{
			IECoreGL::init();

			processQueue();
			m_pointInstancerCache->clearUnused();
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

				/// \todo Should we separate these into different AOVs rendered
				/// to different files? Or provide a mechanism for registering
				/// transforms that we apply ourselves?
				renderObjects( state, Visualisation::ColorSpace::Scene );
				renderObjects( state, Visualisation::ColorSpace::Display );

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

		void renderObjects( IECoreGL::State *currentState, Visualisation::ColorSpace colorSpace )
		{
			IECoreGL::Selector *selector = IECoreGL::Selector::currentSelector();

			GLuint i = 1;
			for( const auto &o : m_objects )
			{
				if( selector )
				{
					selector->loadName( i++ );
				}
				else if(
					!m_drawingExclusions.isEmpty() &&
					( m_drawingExclusions.match( o->name() ) & PathMatcher::ExactMatch )
				)
				{
					// If this isn't a selection render, and this location is in drawingExclusions,
					// then we skip it ( this probably indicates that a tool is taking over the
					// drawing of this object )
					continue;
				}

				o->render( currentState, m_selection, colorSpace );
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
					IECore::msg( IECore::Msg::Warning, "IECoreGL::Renderer", fmt::format( "Unsupported data format \"{}\".", data ) );
					return;
				}

				for( const auto &[parameterName, parameterValue] : namedOutput.second->parameters() )
				{
					if( boost::starts_with( parameterName.string(), g_headerPrefix ) )
					{
						image->blindData()->writable()[parameterName.string().substr( g_headerPrefix.size() )] = parameterValue;
					}
				}

				const string &type = namedOutput.second->getType();
				IECore::WriterPtr writer = IECore::Writer::create( image, "tmp." + type );
				if( !writer )
				{
					IECore::msg( IECore::Msg::Warning, "IECoreGL::Renderer", fmt::format( "Unsupported display type \"{}\".", type ) );
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
		IECore::PathMatcher m_drawingExclusions;
		IECore::CompoundObjectPtr m_baseStateOptions;
		IECoreGL::StatePtr m_baseState;
		bool m_renderObjects;

		IECore::MessageHandlerPtr m_messageHandler;

		std::unique_ptr<PointInstancerCache> m_pointInstancerCache;

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
