//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferSceneUI/LightPositionTool.h"
#include "GafferSceneUI/SceneView.h"

#include "GafferSceneUI/ContextAlgo.h"

#include "GafferUI/Handle.h"
#include "GafferUI/Pointer.h"
#include "GafferUI/StandardStyle.h"

#include "Gaffer/MetadataAlgo.h"

#include "IECoreGL/Group.h"
#include "IECoreGL/MeshPrimitive.h"
#include "IECoreGL/ShaderLoader.h"
#include "IECoreGL/ShaderStateComponent.h"
#include "IECoreGL/TextureLoader.h"
#include "IECoreGL/ToGLMeshConverter.h"

#include "IECoreScene/MeshPrimitive.h"

#include "IECore/AngleConversion.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "Imath/ImathEuler.h"
#include "Imath/ImathMatrixAlgo.h"
#include "Imath/ImathVecAlgo.h"
IECORE_POP_DEFAULT_VISIBILITY

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind/bind.hpp"

#include "fmt/format.h"

using namespace boost::placeholders;
using namespace Imath;
using namespace IECoreScene;
using namespace IECoreGL;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

namespace
{

// Color from `StandardLightVisualiser`
const Color3f g_lightToolColor = Color3f( 0.850f, 0.345f, 0.129f );
const Color4f g_lightToolColor4 = Color4f( g_lightToolColor.x, g_lightToolColor.y, g_lightToolColor.z, 1.f );

const Color4f g_lightToolDisabledColor4 = Color4f( 0.4f, 0.4f, 0.4f, 1.f );

const float g_circleHandleWidth = 4.375f;
const float g_circleHandleWidthLarge = 5.25f;
const float g_circleHandleSelectionWidth = 8.875f;

const float g_lineHandleWidth = 0.875f;
const float g_lineHandleWidthLarge = 1.75f;
const float g_lineSelectionWidth = 5.25f;

const float g_arrowHandleSize = g_circleHandleWidth * 2.f;
const float g_arrowHandleSizeLarge = g_circleHandleWidthLarge * 2.f;
const float g_arrowHandleSelectionSize = g_circleHandleSelectionWidth * 2.f;

const float g_unitConeHeight = 1.5f;

InternedString g_lightsSetName( "__lights" );

const char *constantFragSource()
{
	return
		"#version 120\n"
		""
		"#if __VERSION__ <= 120\n"
		"#define in varying\n"
		"#endif\n"
		""
		"in vec3 fragmentCs;"
		""
		"void main()"
		"{"
			"gl_FragColor = vec4( fragmentCs, 1 );"
		"}"
	;
}

const char *faceCameraVertexSource()
{
	return

		"#version 120\n"
		""
		"#if __VERSION__ <= 120\n"
		"#define in attribute\n"
		"#define out varying\n"
		"#endif\n"
		""
		"uniform vec3 Cs = vec3( 1, 1, 1 );"
		"uniform bool vertexCsActive = false;"
		""
		"in vec3 vertexP;"
		"in vec3 vertexN;"
		"in vec2 vertexuv;"
		"in vec3 vertexCs;"
		""
		"out vec3 geometryI;"
		"out vec3 geometryP;"
		"out vec3 geometryN;"
		"out vec2 geometryuv;"
		"out vec3 geometryCs;"
		""
		"out vec3 fragmentI;"
		"out vec3 fragmentP;"
		"out vec3 fragmentN;"
		"out vec2 fragmentuv;"
		"out vec3 fragmentCs;"
		""
		"void main()"
		"{"
		""
		""
		"	vec3 aimedXAxis, aimedYAxis, aimedZAxis;"

		"	aimedXAxis = normalize( gl_ModelViewMatrixInverse * vec4( 0, 0, -1, 0 ) ).xyz;"
		"	aimedYAxis = normalize( gl_ModelViewMatrixInverse * vec4( 0, 1, 0, 0 ) ).xyz;"
		"	aimedZAxis = normalize( gl_ModelViewMatrixInverse * vec4( 1, 0, 0, 0 ) ).xyz;"
		""
		"	vec3 pAimed = vertexP.x * aimedXAxis + vertexP.y * aimedYAxis + vertexP.z * aimedZAxis;"
		""
		"	vec4 pCam = gl_ModelViewMatrix * vec4( pAimed, 1 );"
		"	gl_Position = gl_ProjectionMatrix * pCam;"
		"	geometryP = pCam.xyz;"
		"	geometryN = normalize( gl_NormalMatrix * vertexN );"
		"	if( gl_ProjectionMatrix[2][3] != 0.0 )"
		"	{"
		"		geometryI = normalize( -pCam.xyz );"
		"	}"
		"	else"
		"	{"
		"		geometryI = vec3( 0, 0, -1 );"
		"	}"
		""
		"	geometryuv = vertexuv;"
		"	geometryCs = mix( Cs, vertexCs, float( vertexCsActive ) );"
		""
		"	fragmentI = geometryI;"
		"	fragmentP = geometryP;"
		"	fragmentN = geometryN;"
		"	fragmentuv = geometryuv;"
		"	fragmentCs = geometryCs;"
		"}"

	;
}

// Adapted from `Handle::rasterScaleFactor()` to get the raster scale factor for
// an arbitrary point in gadget space.
float rasterScaleFactor( const Handle *handle, const V3f &p )
{
	auto viewport = handle->ancestor<ViewportGadget>();
	const M44f fullTransform = handle->fullTransform();

	const M44f cameraToGadget = viewport->getCameraTransform() * fullTransform.inverse();
	V3f cameraUpInGadgetSpace = V3f( 0, 1, 0 );
	cameraToGadget.multDirMatrix( cameraUpInGadgetSpace, cameraUpInGadgetSpace );

	const V2f p1 = viewport->gadgetToRasterSpace( p, handle );
	const V2f p2 = viewport->gadgetToRasterSpace( p + cameraUpInGadgetSpace, handle );

	return 1.f / ( p1 - p2 ).length();
}

// Returns a solid circle with normal along the +X-axis
IECoreGL::MeshPrimitivePtr circle()
{
	static IECoreGL::MeshPrimitivePtr result;
	if( result )
	{
		return result;
	}

	IntVectorDataPtr vertsPerPolyData = new IntVectorData;
	IntVectorDataPtr vertIdsData = new IntVectorData;
	V3fVectorDataPtr pData = new V3fVectorData;

	std::vector<int> &vertsPerPoly = vertsPerPolyData->writable();
	std::vector<int> &vertIds = vertIdsData->writable();
	std::vector<V3f> &p = pData->writable();

	p.push_back( V3f( 0 ) );

	const int numSegments = 20;
	for( int i = 0; i < numSegments + 1; ++i )
	{
		const float a = ( (float)i / (float)numSegments ) * 2.f * M_PI;
		const V3f v = V3f( 0, cos( a ), -sin( a ) );
		p.push_back( v );
	}
	for( int i = 0; i < numSegments; ++i )
	{
		vertIds.push_back( i + 1 );
		vertIds.push_back( i + 2 );
		vertIds.push_back( 0 );
		vertsPerPoly.push_back( 3 );
	}

	IECoreScene::MeshPrimitivePtr circle = new IECoreScene::MeshPrimitive( vertsPerPolyData, vertIdsData, "linear", pData );
	ToGLMeshConverterPtr converter = new ToGLMeshConverter( circle );
	result = runTimeCast<IECoreGL::MeshPrimitive>( converter->convert() );

	return result;
}

// Returns a (potentially truncated) cone facing the -Z axis.
IECoreGL::MeshPrimitivePtr cone( float height, float startRadius, float endRadius )
{
	IECoreGL::MeshPrimitivePtr result;

	IntVectorDataPtr vertsPerPolyData = new IntVectorData;
	IntVectorDataPtr vertIdsData = new IntVectorData;
	V3fVectorDataPtr pData = new V3fVectorData;

	std::vector<int> &vertsPerPoly = vertsPerPolyData->writable();
	std::vector<int> &vertIds = vertIdsData->writable();
	std::vector<V3f> &p = pData->writable();

	const int numSegments = 20;
	for( int i = 0; i < numSegments + 1; ++i )
	{
		const float a = ( (float)i / (float)numSegments ) * 2.f * M_PI;

		p.push_back( V3f( -sin( a ) * startRadius, cos( a ) * startRadius, 0 ) );
		p.push_back( V3f( -sin( a ) * endRadius, cos( a ) * endRadius, -height ) );
	}
	for( int i = 0; i < numSegments; ++i )
	{
		vertIds.push_back( i * 2 );
		vertIds.push_back( i * 2 + 1 );
		vertIds.push_back( i * 2 + 3 );
		vertIds.push_back( i * 2 + 2 );
		vertsPerPoly.push_back( 4 );
	}

	IECoreScene::MeshPrimitivePtr mesh = new IECoreScene::MeshPrimitive( vertsPerPolyData, vertIdsData, "linear", pData );
	IECoreGL::ToGLMeshConverterPtr converter = new ToGLMeshConverter( mesh );
	result = runTimeCast<IECoreGL::MeshPrimitive>( converter->convert() );

	return result;
}

// Returns a cone faceing the -Z axis.
IECoreGL::MeshPrimitivePtr unitCone()
{
	static IECoreGL::MeshPrimitivePtr result = cone( g_unitConeHeight, 0.5f, 0 );
	return result;
}

V3f shadowSourcePosition( const V3f &Pivot, const V3f &Target, const float pivotDistance )
{
	return (Pivot - Target ).normalized() * pivotDistance + Pivot;
}

// Must be called with the current context scoped.
M44f sourceOrientation( const TransformTool::Selection &s, const V3f &origin, const V3f &target )
{
	ScenePlug::ScenePath parentPath( s.path() );
	parentPath.pop_back();

	const M44f worldParentTransform = s.scene()->fullTransform( parentPath );
	const M44f worldParentTransformInverse = worldParentTransform.inverse();
	const M44f localTransform = s.scene()->transform( s.path() );

	V3f currentYAxis;
	localTransform.multDirMatrix( V3f( 0.f, 1.f, 0.f ), currentYAxis );

	// Point in the pivot-target direction, in local space
	V3f targetZAxis;
	worldParentTransformInverse.multDirMatrix( ( target - origin ), targetZAxis );

	return rotationMatrixWithUpDir( V3f( 0.f, 0.f, -1.f ), targetZAxis, currentYAxis );

}

std::string selectedUpstreamPathToString( const std::vector<TransformTool::Selection> &s )
{
	if( !s.empty() )
	{
		return ScenePlug::pathToString( s.back().upstreamPath() );
	}
	return "";
}

class DistanceHandle : public Handle
{

	public :

		DistanceHandle( const bool requiresPivot ) : m_requiresPivot( requiresPivot )
		{

		}

		~DistanceHandle() override
		{

		}

		// Set the position of the pivot from the given world-space coordinate.
		void setPivot( const std::optional<V3f> &p )
		{
			m_pivot = p;
			dirty( DirtyType::Render );
		}

		const std::optional<V3f> &getPivot() const
		{
			return m_pivot;
		}

		// Set the position of the target from the given world-space coordinate.
		void setTarget( const std::optional<V3f> &p )
		{
			m_target = p;
			dirty( DirtyType::Render );
		}

		const std::optional<V3f> &getTarget() const
		{
			return m_target;
		}

		void setPivotDistance( const std::optional<float> d )
		{
			m_pivotDistance = d;
		}

		const std::optional<float> &getPivotDistance() const
		{
			return m_pivotDistance;
		}

		V3f translation( const DragDropEvent &event )
		{
			return V3f( 0, 0, m_drag.updatedPosition( event ) - m_drag.startPosition() );
		}

		void setTransformToSceneSpace( const M44f &t )
		{
			m_transformToSceneSpace = t;
		}

		void setRequiresPivot( const bool requiresPivot )
		{
			m_requiresPivot = requiresPivot;
		}

		bool getRequiresPivot() const
		{
			return m_requiresPivot;
		}

	protected :

		void renderHandle( const Style *style, Style::State state ) const override
		{
			if( !m_pivot && !m_target )
			{
				return;
			}

			float lineRadius = 0;
			float circleSize = 0;
			float coneSize = 0;

			const bool highlighted = state == Style::State::HighlightedState;
			const bool selectionPass = (bool)IECoreGL::Selector::currentSelector();

			if( selectionPass )
			{
				lineRadius = g_lineSelectionWidth;
				circleSize = g_circleHandleSelectionWidth;
				coneSize = g_arrowHandleSelectionSize;
			}
			else
			{
				lineRadius = highlighted ? g_lineHandleWidthLarge : g_lineHandleWidth;
				circleSize = highlighted ? g_circleHandleWidthLarge : g_circleHandleWidth;
				coneSize = highlighted ? g_arrowHandleSizeLarge : g_arrowHandleSize;
			}

			State::bindBaseState();
			auto glState = const_cast<State *>( State::defaultState() );

			IECoreGL::GroupPtr group = new IECoreGL::Group;

			group->getState()->add(
				new IECoreGL::ShaderStateComponent(
					ShaderLoader::defaultShaderLoader(),
					TextureLoader::defaultTextureLoader(),
					"",
					"",
					constantFragSource(),
					new CompoundObject
				)
			);

			auto standardStyle = runTimeCast<const StandardStyle>( style );
			const Color3f highlightColor3 = standardStyle ? standardStyle->getColor( StandardStyle::Color::HighlightColor ) : Color3f( 0.466, 0.612, 0.741 );
			const Color4f highlightColor4 = Color4f( highlightColor3.x, highlightColor3.y, highlightColor3.z, 1.f );

			group->getState()->add(
				new IECoreGL::Color(
					enabled() ? ( highlighted ? highlightColor4 : g_lightToolColor4 ) : g_lightToolDisabledColor4
				)
			);

			const M44f fullTransformInverse = fullTransform().inverse();

			if( m_pivot && m_requiresPivot )
			{
				IECoreGL::GroupPtr pivotGroup = new IECoreGL::Group;
				pivotGroup->getState()->add(
					new IECoreGL::ShaderStateComponent(
						ShaderLoader::defaultShaderLoader(),
						TextureLoader::defaultTextureLoader(),
						faceCameraVertexSource(),
						"",
						constantFragSource(),
						new CompoundObject
					)
				);
				pivotGroup->addChild( circle() );

				const V3f localPivot = m_pivot.value() * m_transformToSceneSpace * fullTransformInverse;

				pivotGroup->setTransform(
					M44f().scale( V3f( circleSize ) * ::rasterScaleFactor( this, localPivot ) ) *
					M44f().translate( localPivot )
				);

				group->addChild( pivotGroup );
			}

			V3f localTarget;
			V3f coneHeightOffset;

			if( m_target )
			{
				IECoreGL::GroupPtr coneGroup = new IECoreGL::Group;
				coneGroup->addChild( unitCone() );

				localTarget = m_target.value() * m_transformToSceneSpace * fullTransformInverse;
				const V3f coneScale = V3f( coneSize ) * ::rasterScaleFactor( this, localTarget );
				coneHeightOffset = V3f( 0, 0, g_unitConeHeight * coneScale.z );

				coneGroup->setTransform(
					M44f().scale( coneScale ) *
					M44f().translate( localTarget + coneHeightOffset )
				);

				group->addChild( coneGroup );

				if( !m_requiresPivot || m_pivot )
				{
					IECoreGL::GroupPtr lineGroup = new IECoreGL::Group;
					lineGroup->addChild(
						cone(
							localTarget.length() - coneHeightOffset.z,
							lineRadius * ::rasterScaleFactor( this, V3f( 0 ) ),
							lineRadius * ::rasterScaleFactor( this, localTarget )
						)
					);

					group->addChild( lineGroup );
				}
			}

			group->render( glState );
		}

		void dragBegin( const DragDropEvent &event ) override
		{
			m_drag = LinearDrag( this, LineSegment3f( V3f( 0 ), V3f( 0, 0, 1 ) ), event );

			assert( m_pivotDistance );

			m_startDistance = m_pivotDistance.value();
		}

	private :

		// As with `LightPositionTool::m_pivotMap` and `LightPositionTool::m_targetMap`,
		// we store the pivot and target position in transform space.
		std::optional<V3f> m_pivot;
		std::optional<V3f> m_target;

		std::optional<float> m_pivotDistance;

		// Used to transform the rendered elements from transform to world space.
		M44f m_transformToSceneSpace;

		LinearDrag m_drag;
		float m_startDistance;

		bool m_requiresPivot;

};

}  // namespace

GAFFER_NODE_DEFINE_TYPE( LightPositionTool );

LightPositionTool::ToolDescription<LightPositionTool, SceneView> LightPositionTool::g_toolDescription;
size_t LightPositionTool::g_firstPlugIndex = 0;

LightPositionTool::LightPositionTool( SceneView *view, const std::string &name ) :
	TransformTool( view, name ),
	m_targetMode( TargetMode::None ),
	m_draggingTarget( false )
{
	m_distanceHandle = new DistanceHandle( true );
	m_distanceHandle->setRasterScale( 0 );
	handles()->setChild( "distanceHandle", m_distanceHandle );
	m_distanceHandle->dragBeginSignal().connectFront( boost::bind( &LightPositionTool::handleDragBegin, this, ::_1 ) );
	m_distanceHandle->dragMoveSignal().connect( boost::bind( &LightPositionTool::handleDragMove, this, ::_1, ::_2 ) );
	m_distanceHandle->dragEndSignal().connect( boost::bind( &LightPositionTool::handleDragEnd, this ) );
	m_distanceHandle->enterSignal().connect( boost::bind( &LightPositionTool::handleEnter, this, ::_2 ) );
	m_distanceHandle->leaveSignal().connect( boost::bind( &LightPositionTool::handleLeave, this ) );

	m_rotateHandle = new RotateHandle( GafferUI::Style::Axes::Z );
	handles()->setChild( "rotateHandle", m_rotateHandle );
	m_rotateHandle->dragBeginSignal().connectFront( boost::bind( &LightPositionTool::handleDragBegin, this, ::_1 ) );
	m_rotateHandle->dragMoveSignal().connect( boost::bind( &LightPositionTool::handleDragMove, this, ::_1, ::_2 ) );
	m_rotateHandle->dragEndSignal().connect( boost::bind( &LightPositionTool::handleDragEnd, this ) );
	m_rotateHandle->enterSignal().connect( boost::bind( &LightPositionTool::handleEnter, this, ::_2 ) );
	m_rotateHandle->leaveSignal().connect( boost::bind( &LightPositionTool::handleLeave, this ) );

	SceneGadget *sg = runTimeCast<SceneGadget>( this->view()->viewportGadget()->getPrimaryChild() );
	sg->keyPressSignal().connect( boost::bind( &LightPositionTool::keyPress, this, ::_2 ) );
	sg->keyReleaseSignal().connect( boost::bind( &LightPositionTool::keyRelease, this, ::_2 ) );
	// We have to insert this before the underlying SelectionTool connections or it starts an object drag.
	sg->buttonPressSignal().connectFront( boost::bind( &LightPositionTool::buttonPress, this, ::_2 ) );
	sg->buttonReleaseSignal().connectFront( boost::bind( &LightPositionTool::buttonRelease, this, ::_2 ) );

	sg->dragBeginSignal().connectFront( boost::bind( &LightPositionTool::sceneGadgetDragBegin, this, ::_1, ::_2 ) );
	sg->dragEnterSignal().connectFront( boost::bind( &LightPositionTool::sceneGadgetDragEnter, this, ::_1, ::_2 ) );
	sg->dragMoveSignal().connectFront( boost::bind( &LightPositionTool::sceneGadgetDragMove, this, ::_2 ) );
	sg->dragEndSignal().connectFront( boost::bind( &LightPositionTool::sceneGadgetDragEnd, this ) );

	// We need to track the tool state/view visibility so we don't leave a lingering target cursor
	sg->visibilityChangedSignal().connect( boost::bind( &LightPositionTool::visibilityChanged, this, ::_1 ) );

	this->view()->viewportGadget()->leaveSignal().connect( boost::bind( &LightPositionTool::viewportGadgetLeave, this, ::_2 ) );

	plugSetSignal().connect( boost::bind( &LightPositionTool::plugSet, this, ::_1 ) );

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "mode", Plug::In, (int)Mode::Shadow, (int)Mode::First, (int)Mode::Last ) );
}

IntPlug *LightPositionTool::modePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const IntPlug *LightPositionTool::modePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

LightPositionTool::~LightPositionTool()
{
}

void LightPositionTool::positionShadow( const V3f &pivot, const V3f &target, const float pivotDistance )
{
	if( !m_distanceHandle->enabled() || selection().empty() )
	{
		return;
	}
	const Selection &s = selection().back();

	const V3f newP = shadowSourcePosition( pivot, target, pivotDistance );

	// See `RotateTool::buttonPress()` for a description of why we use this relatively
	// elaborate orientation calculation.

	Context::Scope scopedContext( s.context() );

	const M44f orientationMatrix = sourceOrientation( s, pivot, target );

	const M44f localTransform = s.scene()->transform( s.path() );
	translateAndOrient( s, localTransform, newP, orientationMatrix );
}

void LightPositionTool::positionHighlight(
	const V3f &highlightTarget,
	const V3f &viewpoint,
	const V3f &normal,
	const float targetDistance
)
{
	const V3f reflectionRay = reflect( ( viewpoint - highlightTarget ), normal ).normalize();
	positionAlongNormal( highlightTarget, reflectionRay, targetDistance );
}

void LightPositionTool::positionAlongNormal(
	const V3f &target,
	const V3f &normal,
	const float distance
)
{
	if( !m_distanceHandle->enabled() || selection().empty() )
	{
		return;
	}
	const Selection &s = selection().back();

	const V3f newP = target + normal * distance;

	Context::Scope scopedContext( s.context() );

	const M44f orientationMatrix = sourceOrientation ( s, newP, target );

	const M44f localTransform = s.scene()->transform( s.path() );
	translateAndOrient( s, localTransform, newP, orientationMatrix );
}

bool LightPositionTool::affectsHandles( const Gaffer::Plug *input ) const
{
	if( TransformTool::affectsHandles( input ) )
	{
		return true;
	}

	return input == scenePlug()->transformPlug() || input == modePlug();
}

void LightPositionTool::updateHandles( float rasterScale )
{
	Selection s = selection().back();

	handles()->setTransform( s.orientedTransform( Orientation::Local ) );

	Context::Scope scopedContext( s.context() );

	if( !m_drag )
	{
		bool isLight = s.scene()->set( g_lightsSetName )->readable().match( s.path() ) & IECore::PathMatcher::ExactMatch;
		m_distanceHandle->setVisible( isLight );
		m_rotateHandle->setVisible( isLight );

		bool singleSelection = selection().size() == 1;

		TranslationRotation trDistanceHandle( s, Orientation::World );
		m_distanceHandle->setEnabled(
			singleSelection &&
			trDistanceHandle.canApplyTranslation() &&
			trDistanceHandle.canApplyRotation( V3i( 1, 1, 1 ) )
		);

		TranslationRotation trRotateHandle( s, Orientation::Local );
		m_rotateHandle->setEnabled( singleSelection && trRotateHandle.canApplyRotation( V3i( 0, 0, 1 ) ) );

		m_distanceHandle->setRasterScale( 0 );
		m_rotateHandle->setRasterScale( rasterScale );
	}

	auto distanceHandle = static_cast<DistanceHandle *>( m_distanceHandle.get() );

	std::optional<V3f> pivot = getPivot();
	std::optional<V3f> target = getTarget();

	const M44f sceneToTransform = s.sceneToTransformSpace();
	const M44f sceneToTransformInverse = sceneToTransform.inverse();
	distanceHandle->setPivot( pivot );
	distanceHandle->setTarget( target );
	distanceHandle->setTransformToSceneSpace( sceneToTransformInverse );

	const Mode mode = (Mode)modePlug()->getValue();
	distanceHandle->setRequiresPivot( mode == Mode::Shadow );

	if( !target || ( mode == Mode::Shadow && !pivot ) )
	{
		return;
	}

	// The user can control the distance along the line from target
	// to pivot, and the rotation around the Z-axis. Any variance from those
	// contraints invalidates the stored parameters.

	const M44f transform = s.scene()->fullTransform( s.path() ) * sceneToTransform;
	const V3f p = transform.translation();

	Line3f handleLine;
	V3f handleDir;
	float handleLength = 0;

	if( mode == Mode::Shadow )
	{
		handleLine = Line3f( target.value(), pivot.value() );
		handleDir = V3f( ( target.value() - pivot.value() ).normalized() );
		handleLength = ( p - pivot.value() ).length();
	}
	else
	{
		handleLine = Line3f( target.value(), p );
		const V3f handleDelta = target.value() - p;
		handleDir = handleDelta.normalized();
		handleLength = handleDelta.length();
	}

	V3f direction;
	transform.multDirMatrix( V3f( 0, 0, -1.f ), direction );

	if(
		!m_drag &&
		(
			!direction.normalized().equalWithAbsError( handleDir, 1e-4 ) ||
			handleLine.distanceTo( p ) > distanceHandle->getPivotDistance().value() * 1e-4
		)
	)
	{
		distanceHandle->setPivot( std::nullopt );
		distanceHandle->setTarget( std::nullopt );
		distanceHandle->setPivotDistance( std::nullopt );

		const std::string p = ScenePlug::pathToString( s.path() );
		m_targetMap.erase( p );
		m_pivotMap.erase( p );
		m_pivotDistanceMap.erase( p );
	}
	else
	{
		setPivotDistance( handleLength );
	}
}

IECore::RunTimeTypedPtr LightPositionTool::handleDragBegin( Gadget *gadget )
{
	m_drag.emplace( selection().back(), Orientation::Local );
	if( gadget == m_distanceHandle.get() )
	{
		assert( getPivotDistance() );
		m_startPivotDistance = getPivotDistance().value();
	}

	TransformTool::dragBegin();

	return nullptr;  // let the handle start the drag with the event system
}

bool LightPositionTool::handleDragMove( Gadget *gadget, const DragDropEvent &event )
{
	UndoScope undoScope( view()->scriptNode(), UndoScope::Enabled, undoMergeGroup() );

	if( gadget == m_distanceHandle.get() )
	{
		const auto distanceHandle = static_cast<DistanceHandle *>( m_distanceHandle.get() );

		V3f t = distanceHandle->translation( event );
		t.z = std::max( -m_startPivotDistance, t.z );

		m_drag.value().applyTranslation( t );
	}
	else if( gadget == m_rotateHandle.get() )
	{
		const V3f rotation = m_rotateHandle->rotation( event );
		m_drag.value().applyRotation( rotation );
	}

	return true;
}

bool LightPositionTool::handleDragEnd()
{
	TransformTool::dragEnd();
	m_drag = std::nullopt;
	return false;
}

bool LightPositionTool::handleEnter( const GafferUI::ButtonEvent &event )
{
	// Always use the default pointer, the handle appearance indicates editability
	GafferUI::Pointer::setCurrent( "" );
	return true;
}

void LightPositionTool::handleLeave()
{
	updatePointer();
}

RunTimeTypedPtr LightPositionTool::sceneGadgetDragBegin( Gadget *gadget, const DragDropEvent &event )
{
	if(
		!activePlug()->getValue() ||
		getTargetMode() == TargetMode::None ||
		!m_distanceHandle->visible()
	)
	{
		return nullptr;
	}
	const auto distanceHandle = static_cast<DistanceHandle *>( m_distanceHandle.get() );
	if( getTargetMode() == TargetMode::Pivot && !distanceHandle->getRequiresPivot() )
	{
		return nullptr;
	}

	m_draggingTarget = true;

	TransformTool::dragBegin();
	return gadget;
}

bool LightPositionTool::sceneGadgetDragEnter( Gadget *gadget, const DragDropEvent &event )
{
	return m_draggingTarget && event.sourceGadget == gadget && event.data == gadget;
}

bool LightPositionTool::sceneGadgetDragMove( const DragDropEvent &event )
{
	if( !m_draggingTarget )
	{
		return false;
	}

	// We always return true to prevent the SelectTool defaults.
	if( !selectionEditable() || !m_distanceHandle->enabled() )
	{
		return true;
	}

	UndoScope undoScope( view()->scriptNode(), UndoScope::Enabled, undoMergeGroup() );

	placeTarget( event.line );
	return true;
}

bool LightPositionTool::sceneGadgetDragEnd()
{
	m_draggingTarget = false;
	TransformTool::dragEnd();
	return false;
}

bool LightPositionTool::keyPress( const KeyEvent &event )
{
	if( activePlug()->getValue() )
	{
		if(
			( event.key == "V" && event.modifiers == KeyEvent::Modifiers::Shift ) ||
			( event.key == "Shift" && getTargetMode() == TargetMode::Target )
		)
		{
			setTargetMode( TargetMode::Pivot );
			return true;
		}
		if( event.key == "V" && event.modifiers == KeyEvent::Modifiers::None )
		{
			setTargetMode( TargetMode::Target );
			return true;
		}
	}

	return false;
}

bool LightPositionTool::keyRelease( const KeyEvent &event )
{
	if( activePlug()->getValue() )
	{
		if( event.key == "V" )
		{
			setTargetMode( TargetMode::None );
			return true;
		}
		if(
			event.key == "Shift" &&
			( getTargetMode() == TargetMode::Pivot )
		)
		{
			setTargetMode( TargetMode::Target );
			return true;
		}
	}

	return false;
}

void LightPositionTool::viewportGadgetLeave( const ButtonEvent &event )
{
	if( getTargetMode() != TargetMode::None )
	{
		// We loose keyRelease events in a variety of scenarios so turn targeted
		// off whenever the mouse leaves the viewport. Key-repeat events will
		// cause it to be re-enabled when the mouse re-enters if the key is still
		// held down at that time.
		setTargetMode( TargetMode::None );
	}
}

void LightPositionTool::visibilityChanged( GafferUI::Gadget *gadget )
{
	if( !gadget->visible() && getTargetMode() != TargetMode::None )
	{
		setTargetMode( TargetMode::None );
	}
}

void LightPositionTool::plugSet( Plug *plug )
{
	if( plug == activePlug() && !activePlug()->getValue() && getTargetMode() != TargetMode::None )
	{
		setTargetMode( TargetMode::None );
	}
}

bool LightPositionTool::buttonPress( const ButtonEvent &event )
{
	if( event.button != ButtonEvent::Left || !activePlug()->getValue() || getTargetMode() == TargetMode::None )
	{
		return false;
	}

	// We always return true to prevent the SelectTool defaults.

	if( !selectionEditable() || !m_distanceHandle->enabled() || !m_distanceHandle->visible() )
	{
		return true;
	}

	const auto distanceHandle = static_cast<DistanceHandle *>( m_distanceHandle.get() );
	if( getTargetMode() == TargetMode::Pivot && !distanceHandle->getRequiresPivot() )
	{
		return true;
	}

	UndoScope undoScope( view()->scriptNode(), UndoScope::Enabled, undoMergeGroup() );

	placeTarget( event.line );
	return true;
}

bool LightPositionTool::buttonRelease( const ButtonEvent &event )
{
	if( event.button != ButtonEvent::Left || !activePlug()->getValue() || getTargetMode() == TargetMode::None )
	{
		return false;
	}

	// We're not in a drag event, but we do want to increment `TransformTool::m_mergeGroupId`
	TransformTool::dragEnd();
	return true;
}

bool LightPositionTool::placeTarget( const LineSegment3f &eventLine )
{
	ScenePlug::ScenePath scenePath;
	V3f gadgetTargetPos;

	const SceneGadget *sceneGadget = runTimeCast<SceneGadget>( view()->viewportGadget()->getPrimaryChild() );
	if( !sceneGadget->objectAt( eventLine, scenePath, gadgetTargetPos ) )
	{
		return false;
	}

	const auto distanceHandle = static_cast<DistanceHandle *>( m_distanceHandle.get() );
	Selection s = selection().back();
	ScriptNodePtr scriptNode = s.editTarget()->ancestor<ScriptNode>();

	const M44f sceneToTransformSpace = s.sceneToTransformSpace();
	const M44f sceneToTransformSpaceInverse = sceneToTransformSpace.inverse();

	distanceHandle->setTransformToSceneSpace( sceneToTransformSpaceInverse );

	if( getTargetMode() == TargetMode::Pivot )
	{
		const V3f newPivot = gadgetTargetPos * sceneGadget->fullTransform() * sceneToTransformSpace;
		if( !distanceHandle->getPivot() )
		{
			setPivotDistance(
				( newPivot - ( V3f( 0 ) * ( s.orientedTransform( Orientation::World ) * sceneToTransformSpace ) ) ).length()
			);
		}
		setPivot( newPivot, scriptNode );
	}
	else if( getTargetMode() == TargetMode::Target )
	{
		if( !distanceHandle->getRequiresPivot() && !distanceHandle->getTarget() )
		{
			setPivotDistance(
				(
					( V3f( 0 ) * ( s.orientedTransform( Orientation::World ) * sceneToTransformSpace ) ) -
					gadgetTargetPos * sceneGadget->fullTransform().inverse()
				).length()
			);
		}
		setTarget( gadgetTargetPos * sceneGadget->fullTransform() * sceneToTransformSpace, scriptNode );
	}

	if( modePlug()->getValue() == (int)Mode::Shadow )
	{
		if( !distanceHandle->getPivot() || !distanceHandle->getTarget() )
		{
			return false;
		}

		positionShadow(
			distanceHandle->getPivot().value() * sceneToTransformSpaceInverse,
			distanceHandle->getTarget().value() * sceneToTransformSpaceInverse,
			distanceHandle->getPivotDistance().value()
		);
	}
	else if( modePlug()->getValue() == (int)Mode::Highlight )
	{
		if( !distanceHandle->getTarget() )
		{
			return false;
		}

		const M44f cameraTransform = view()->viewportGadget()->getCameraTransform();
		std::optional<V3f> sceneGadgetNormal = sceneGadget->normalAt( eventLine );
		if( sceneGadgetNormal )
		{
			V3f worldNormal;
			sceneGadget->fullTransform().inverse().transpose().multDirMatrix( sceneGadgetNormal.value(), worldNormal );

			positionHighlight(
				distanceHandle->getTarget().value() * sceneToTransformSpaceInverse,
				cameraTransform.translation(),
				worldNormal,
				distanceHandle->getPivotDistance().value()
			);
		}
	}
	else
	{
		if( !distanceHandle->getTarget() )
		{
			return false;
		}

		std::optional<V3f> sceneGadgetNormal = sceneGadget->normalAt( eventLine );
		if( sceneGadgetNormal )
		{
			V3f worldNormal;
			sceneGadget->fullTransform().inverse().transpose().multDirMatrix( sceneGadgetNormal.value(), worldNormal );

			positionAlongNormal(
				distanceHandle->getTarget().value() * sceneToTransformSpaceInverse,
				worldNormal,
				distanceHandle->getPivotDistance().value()
			);
		}
	}

	return true;
}

void LightPositionTool::translateAndOrient( const Selection &s, const M44f &localTransform, const V3f &newPosition, const M44f &newOrientation ) const
{
	V3f originalRotation;
	extractEulerXYZ( localTransform, originalRotation );
	const M44f originalRotationMatrix = M44f().rotate( originalRotation );

	const M44f relativeMatrix = originalRotationMatrix.inverse() * newOrientation;

	V3f relativeRotation;
	extractEulerXYZ( relativeMatrix, relativeRotation );

	const V3f p = V3f( 0 ) * s.orientedTransform( TransformTool::Orientation::World );
	const V3f offset = newPosition - p;

	TranslationRotation trTranslate( s, Orientation::World );
	trTranslate.applyTranslation( offset );
	TranslationRotation trRotate( s, Orientation::Parent );
	trRotate.applyRotation( relativeRotation );
}

void LightPositionTool::setTargetMode( TargetMode targeted )
{
	if( targeted == m_targetMode )
	{
		return;
	}

	m_targetMode = targeted;

	updatePointer();
}

void LightPositionTool::updatePointer() const
{
	if( m_targetMode == TargetMode::None )
	{
		GafferUI::Pointer::setCurrent( "" );
	}
	else if( !m_distanceHandle->enabled() || !m_distanceHandle->visible() )
	{
		GafferUI::Pointer::setCurrent( "notEditable" );
	}
	else if( m_targetMode == TargetMode::Pivot )
	{
		auto distanceHandle = static_cast<DistanceHandle *>( m_distanceHandle.get() );
		GafferUI::Pointer::setCurrent(
			distanceHandle->getRequiresPivot() ? "pivot" : "notEditable"
		);
	}
	else if( m_targetMode == TargetMode::Target )
	{
		GafferUI::Pointer::setCurrent( "target" );
	}
}

void LightPositionTool::setPivot( const V3f &p, ScriptNodePtr scriptNode )
{
	std::optional<V3f> currentValue = getPivot();
	auto distanceHandle = static_cast<DistanceHandle *>( m_distanceHandle.get() );
	const auto pathString = selectedUpstreamPathToString( selection() );
	Action::enact(
		scriptNode,
		[t = LightPositionToolPtr( this ), k = pathString, p, distanceHandle]() {
			t->m_pivotMap[k] = p;
			distanceHandle->setPivot( p );
		},
		[t = LightPositionToolPtr( this ), k = pathString, currentValue, distanceHandle]() {
			t->m_pivotMap[k] = currentValue;
			const std::string upstreamPath = selectedUpstreamPathToString( t->selection() );
			if( !upstreamPath.empty() && upstreamPath == k )
			{
				distanceHandle->setPivot( currentValue );
			}
		}
	);
}

std::optional<V3f> LightPositionTool::getPivot() const
{
	auto it = m_pivotMap.find( selectedUpstreamPathToString( selection() ) );
	if( it == m_pivotMap.end() )
	{
		return std::nullopt;
	}
	return it->second;
}

void LightPositionTool::setTarget( const V3f &p, ScriptNodePtr scriptNode )
{
	std::optional<V3f> currentValue = getTarget();
	auto distanceHandle = static_cast<DistanceHandle *>( m_distanceHandle.get() );
	const auto pathString = selectedUpstreamPathToString( selection() );
	Action::enact(
		scriptNode,
		[t = LightPositionToolPtr( this ), k = pathString, p, distanceHandle]() {
			t->m_targetMap[k] = p;
			distanceHandle->setTarget( p );
		},
		[t = LightPositionToolPtr( this ), k = pathString, currentValue, distanceHandle]() {
			t->m_targetMap[k] = currentValue;
			const std::string upstreamPath = selectedUpstreamPathToString( t->selection() );
			if( !upstreamPath.empty() && upstreamPath == k )
			{
				distanceHandle->setTarget( currentValue );
			}
		}
	);
}

std::optional<V3f> LightPositionTool::getTarget() const
{
	auto it = m_targetMap.find( selectedUpstreamPathToString( selection() ) );
	if( it == m_targetMap.end() )
	{
		return std::nullopt;
	}
	return it->second;
}

void LightPositionTool::setPivotDistance( const float d )
{
	m_pivotDistanceMap[selectedUpstreamPathToString( selection() )] = d;
	static_cast<DistanceHandle *>( m_distanceHandle.get() )->setPivotDistance( d );
}

std::optional<float> LightPositionTool::getPivotDistance() const
{
	auto it = m_pivotDistanceMap.find( selectedUpstreamPathToString( selection() ) );
	if( it == m_pivotDistanceMap.end() )
	{
		return std::nullopt;
	}
	return it->second;
}

//////////////////////////////////////////////////////////////////////////
// LightPositionTool::TranslationRotation
//////////////////////////////////////////////////////////////////////////

/// \todo These methods are either exactly the same as those in
/// `TranslateTool` and `RotateTool` or very close. Do they belong
/// in a `TransformToolAlgo` or something similar?

LightPositionTool::TranslationRotation::TranslationRotation( const Selection &selection, Orientation orientation )
	: m_selection( selection )
{
	const M44f handleRotationXform = selection.orientedTransform( orientation );
	m_gadgetToRotationXform = handleRotationXform * selection.sceneToTransformSpace();

	const M44f handleTranslateXform = selection.orientedTransform( orientation );
	m_gadgetToTranslationXform = handleTranslateXform * selection.sceneToTransformSpace();
}

bool LightPositionTool::TranslationRotation::canApplyTranslation() const
{
	auto edit = m_selection.acquireTransformEdit( /* createIfNecessary = */ false );
	if( !edit )
	{
		// Edit will be created on demand in `apply()`.
		return !MetadataAlgo::readOnly( m_selection.editTarget() );
	}

	for( int i = 0; i < 3; ++i )
	{
		if( !canSetValueOrAddKey( edit->translate->getChild( i ) ) )
		{
			return false;
		}
	}

	return true;
}

bool LightPositionTool::TranslationRotation::canApplyRotation( const V3i &axisMask ) const
{
	auto edit = m_selection.acquireTransformEdit( /* createIfNecessary = */ false );
	if( !edit )
	{
		// Edit will be created on demand in `apply()`.
		return !MetadataAlgo::readOnly( m_selection.editTarget() );
	}

	Imath::V3f current;
	const Imath::V3f updated = updatedRotateValue( edit->rotate.get(), V3f( axisMask ), &current );
	for( int i = 0; i < 3; ++i )
	{
		if( updated[i] == current[i] )
		{
			continue;
		}

		if( !canSetValueOrAddKey( edit->rotate->getChild( i ) ) )
		{
			return false;
		}
	}

	return true;
}

void LightPositionTool::TranslationRotation::applyTranslation( const V3f &translation )
{
	V3fPlug *translatePlug = m_selection.acquireTransformEdit()->translate.get();
	if( !m_originalTranslation )
	{
		Context::Scope scopedContext( m_selection.context() );
		m_originalTranslation = translatePlug->getValue();
	}

	V3f offsetInTransformSpace;
	m_gadgetToTranslationXform.multDirMatrix( translation, offsetInTransformSpace );

	for( int i = 0; i < 3; ++i )
	{
		FloatPlug *pTranslate = translatePlug->getChild( i );
		if( canSetValueOrAddKey( pTranslate ) )
		{
			setValueOrAddKey( pTranslate, m_selection.context()->getTime(), (*m_originalTranslation)[i] + offsetInTransformSpace[i] );
		}
	}
}

void LightPositionTool::TranslationRotation::applyRotation( const Eulerf &rotation )
{
	V3fPlug *rotatePlug = m_selection.acquireTransformEdit()->rotate.get();
	const Imath::V3f e = updatedRotateValue( rotatePlug, rotation );
	for( int i = 0; i < 3; ++i )
	{
		FloatPlug *pRotate = rotatePlug->getChild( i );
		if( canSetValueOrAddKey( pRotate ) )
		{
			setValueOrAddKey( pRotate, m_selection.context()->getTime(), e[i] );
		}
	}
}

V3f LightPositionTool::TranslationRotation::updatedRotateValue( const V3fPlug *rotatePlug, const Eulerf &rotation, V3f *currentValue ) const
{
	if( !m_originalRotation )
	{
		Context::Scope scopedContext( m_selection.context() );
		m_originalRotation = degreesToRadians( rotatePlug->getValue() );
	}

	// Convert the rotation into the space of the
	// upstream transform.
	Quatf q = rotation.toQuat();
	V3f transformSpaceAxis;
	m_gadgetToRotationXform.multDirMatrix( q.axis(), transformSpaceAxis );
	float d = Imath::sign( m_gadgetToRotationXform.determinant() );
	q.setAxisAngle( transformSpaceAxis, q.angle() * d );

	// Compose it with the original.

	M44f m = q.toMatrix44();
	m.rotate( *m_originalRotation );

	// Convert to the euler angles closest to
	// those we currently have.

	const V3f current = rotatePlug->getValue();
	if( currentValue )
	{
		*currentValue = current;
	}

	Eulerf e; e.extract( m );
	e.makeNear( degreesToRadians( current ) );

	return radiansToDegrees( V3f( e ) );
}
