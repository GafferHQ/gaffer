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
#include "OpenEXR/OpenEXRConfig.h"
#if OPENEXR_VERSION_MAJOR < 3
#include "OpenEXR/ImathEuler.h"
#include "OpenEXR/ImathMatrixAlgo.h"
#else
#include "Imath/ImathEuler.h"
#include "Imath/ImathMatrixAlgo.h"
#endif
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
const Color3f g_lightToolColor = Color3f( 1.0f, 0.835f, 0.07f );
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

V3f shadowSourcePosition( const V3f &shadowPivot, const V3f &shadowTarget, const float pivotDistance )
{
	return (shadowPivot - shadowTarget ).normalized() * pivotDistance + shadowPivot;
}

// Must be called with the current context scoped.
M44f shadowSourceOrientation( const TransformTool::Selection &s, const V3f &shadowPivot, const V3f &shadowTarget )
{
	ScenePlug::ScenePath parentPath( s.path() );
	parentPath.pop_back();

	const M44f worldParentTransform = s.scene()->fullTransform( parentPath );
	const M44f worldParentTransformInverse = worldParentTransform.inverse();
	const M44f localTransform = s.scene()->transform( s.path() );

	V3f currentYAxis;
	localTransform.multDirMatrix( V3f( 0.f, 1.f, 0.f ), currentYAxis );

	// Point in the pivot-shadowTarget direction, in local space
	V3f targetZAxis;
	worldParentTransformInverse.multDirMatrix( ( shadowTarget - shadowPivot ), targetZAxis );

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

class ShadowHandle : public Handle
{

	public :

		ShadowHandle()
		{

		}

		~ShadowHandle() override
		{

		}

		// Set the position of the shadow pivot from the given world-space coordinate.
		void setShadowPivot( const std::optional<V3f> &p )
		{
			m_shadowPivot = p;
			dirty( DirtyType::Render );
		}

		const std::optional<V3f> &getShadowPivot() const
		{
			return m_shadowPivot;
		}

		// Set the position of the shadow target from the given world-space coordinate.
		void setShadowTarget( const std::optional<V3f> &p )
		{
			m_shadowTarget = p;
			dirty( DirtyType::Render );
		}

		const std::optional<V3f> &getShadowTarget() const
		{
			return m_shadowTarget;
		}

		void setPivotDistance( const std::optional<float> d )
		{
			m_pivotDistance = d;
		}

		const std::optional<float> &getPivotDistance() const
		{
			return m_pivotDistance;
		}

	protected :

		void renderHandle( const Style *style, Style::State state ) const override
		{
			if( !m_shadowPivot && !m_shadowTarget )
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

			if( m_shadowPivot )
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

				const V3f localPivot = m_shadowPivot.value() * fullTransformInverse;

				pivotGroup->setTransform(
					M44f().scale( V3f( circleSize ) * ::rasterScaleFactor( this, localPivot ) ) *
					M44f().translate( localPivot )
				);

				group->addChild( pivotGroup );
			}

			V3f localTarget;
			V3f coneHeightOffset;

			if( m_shadowTarget )
			{
				IECoreGL::GroupPtr coneGroup = new IECoreGL::Group;
				coneGroup->addChild( unitCone() );

				localTarget = m_shadowTarget.value() * fullTransformInverse;
				const V3f coneScale = V3f( coneSize ) * ::rasterScaleFactor( this, localTarget );
				coneHeightOffset = V3f( 0, 0, g_unitConeHeight * coneScale.z );

				coneGroup->setTransform(
					M44f().scale( coneScale ) *
					M44f().translate( localTarget + coneHeightOffset )
				);

				group->addChild( coneGroup );
			}

			if( m_shadowTarget && m_shadowPivot )
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

			group->render( glState );
		}

		void dragBegin( const DragDropEvent &event ) override
		{
		}

	private :

		std::optional<V3f> m_shadowPivot;
		std::optional<V3f> m_shadowTarget;
		std::optional<float> m_pivotDistance;

};

}  // namespace

GAFFER_NODE_DEFINE_TYPE( LightPositionTool );

LightPositionTool::ToolDescription<LightPositionTool, SceneView> LightPositionTool::g_toolDescription;
size_t LightPositionTool::g_firstPlugIndex = 0;

LightPositionTool::LightPositionTool( SceneView *view, const std::string &name ) :
	TransformTool( view, name ),
	m_targetMode( TargetMode::None )
{
	m_shadowHandle = new ShadowHandle();
	m_shadowHandle->setRasterScale( 0 );
	handles()->setChild( "shadowHandle", m_shadowHandle );

	SceneGadget *sg = runTimeCast<SceneGadget>( this->view()->viewportGadget()->getPrimaryChild() );
	sg->keyPressSignal().connect( boost::bind( &LightPositionTool::keyPress, this, ::_2 ) );
	sg->keyReleaseSignal().connect( boost::bind( &LightPositionTool::keyRelease, this, ::_2 ) );
	// We have to insert this before the underlying SelectionTool connections or it starts an object drag.
	sg->buttonPressSignal().connectFront( boost::bind( &LightPositionTool::buttonPress, this, ::_2 ) );
	sg->buttonReleaseSignal().connectFront( boost::bind( &LightPositionTool::buttonRelease, this, ::_2 ) );

	// We need to track the tool state/view visibility so we don't leave a lingering target cursor
	sg->visibilityChangedSignal().connect( boost::bind( &LightPositionTool::visibilityChanged, this, ::_1 ) );

	this->view()->viewportGadget()->leaveSignal().connect( boost::bind( &LightPositionTool::viewportGadgetLeave, this, ::_2 ) );

	plugSetSignal().connect( boost::bind( &LightPositionTool::plugSet, this, ::_1 ) );

	storeIndexOfNextChild( g_firstPlugIndex );
}

LightPositionTool::~LightPositionTool()
{
}

void LightPositionTool::position( const V3f &shadowPivot, const V3f &shadowTarget, const float pivotDistance )
{
	if( !m_shadowHandle->enabled() || selection().empty() )
	{
		return;
	}
	const Selection &s = selection().back();

	const V3f newP = shadowSourcePosition( shadowPivot, shadowTarget, pivotDistance );

	// See `RotateTool::buttonPress()` for a description of why we use this relatively
	// elaborate orientation calculation.

	Context::Scope scopedContext( s.context() );

	const M44f localTransform = s.scene()->transform( s.path() );

	const M44f orientationMatrix = shadowSourceOrientation( s, shadowPivot, shadowTarget );

	V3f originalRotation;
	extractEulerXYZ( localTransform, originalRotation );
	const M44f originalRotationMatrix = M44f().rotate( originalRotation );

	const M44f relativeMatrix = originalRotationMatrix.inverse() * orientationMatrix;

	V3f relativeRotation;
	extractEulerXYZ( relativeMatrix, relativeRotation );

	const V3f p = V3f( 0 ) * s.orientedTransform( Orientation::World );
	const V3f offset = newP - p;

	TranslationRotation( s ).apply( offset, relativeRotation );
}

bool LightPositionTool::affectsHandles( const Gaffer::Plug *input ) const
{
	if( TransformTool::affectsHandles( input ) )
	{
		return true;
	}

	return input == scenePlug()->transformPlug();
}

void LightPositionTool::updateHandles( float rasterScale )
{
	Selection s = selection().back();

	handles()->setTransform( s.orientedTransform( Orientation::Local ) );

	m_shadowHandle->setEnabled( selection().size() == 1 && TranslationRotation( s ).canApply() );

	m_shadowHandle->setRasterScale( 0 );

	auto shadowHandle = static_cast<ShadowHandle *>( m_shadowHandle.get() );

	std::optional<V3f> shadowPivot = getShadowPivot();
	std::optional<V3f> shadowTarget = getShadowTarget();

	shadowHandle->setShadowPivot( shadowPivot );
	shadowHandle->setShadowTarget( shadowTarget );

	if( !shadowPivot || !shadowTarget )
	{
		return;
	}

	// The user can control the distance along the line from shadow target
	// to pivot, and the rotation around the Z-axis. Any variance from those
	// contraints invalidates the stored shadow parameters.

	Context::Scope scopedContext( s.context() );

	const M44f worldTransform = s.scene()->fullTransform( s.path() );
	const V3f p = worldTransform.translation();
	const Line3f handleLine( shadowTarget.value(), shadowPivot.value() );

	V3f direction;
	worldTransform.multDirMatrix( V3f( 0, 0, -1.f ), direction );

	if(
		!direction.equalWithAbsError( ( shadowTarget.value() - shadowPivot.value() ).normalized(), 1e-4 ) ||
		handleLine.distanceTo( p ) > shadowHandle->getPivotDistance().value() * 1e-4
	)
	{
		shadowHandle->setShadowPivot( std::nullopt );
		shadowHandle->setShadowTarget( std::nullopt );
		shadowHandle->setPivotDistance( std::nullopt );

		const std::string p = ScenePlug::pathToString( s.path() );
		m_shadowTargetMap.erase( p );
		m_shadowPivotMap.erase( p );
		m_shadowPivotDistanceMap.erase( p );
	}

	shadowHandle->setPivotDistance( ( p - shadowPivot.value() ).length() );
}

bool LightPositionTool::keyPress( const KeyEvent &event )
{
	if( activePlug()->getValue() )
	{
		if(
			( event.key == "V" && event.modifiers == KeyEvent::Modifiers::Shift ) ||
			( event.key == "Shift" && getTargetMode() == TargetMode::ShadowTarget )
		)
		{
			setTargetMode( TargetMode::ShadowPivot );
			return true;
		}
		if( event.key == "V" && event.modifiers == KeyEvent::Modifiers::None )
		{
			setTargetMode( TargetMode::ShadowTarget );
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
		if( event.key == "Shift" && getTargetMode() == TargetMode::ShadowPivot )
		{
			setTargetMode( TargetMode::ShadowTarget );
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

	if( !selectionEditable() || !m_shadowHandle->enabled() )
	{
		return true;
	}

	ScenePlug::ScenePath scenePath;
	V3f targetPos;

	const SceneGadget *sceneGadget = runTimeCast<SceneGadget>( view()->viewportGadget()->getPrimaryChild() );
	if( !sceneGadget->objectAt( event.line, scenePath, targetPos ) )
	{
		return true;
	}

	const auto shadowHandle = static_cast<ShadowHandle *>( m_shadowHandle.get() );
	Selection s = selection().back();
	ScriptNodePtr scriptNode = s.editTarget()->ancestor<ScriptNode>();

	UndoScope undoScope( scriptNode );

	if( getTargetMode() == TargetMode::ShadowPivot )
	{
		const V3f newPivot = targetPos * sceneGadget->fullTransform();
		if( !shadowHandle->getShadowPivot() )
		{
			setShadowPivotDistance(
				( newPivot - ( V3f( 0 ) * s.orientedTransform( Orientation::World ) ) ).length()
			);
		}
		setShadowPivot( newPivot, scriptNode );
	}
	else if( getTargetMode() == TargetMode::ShadowTarget )
	{
		setShadowTarget( targetPos * sceneGadget->fullTransform(), scriptNode );
	}

	if( !shadowHandle->getShadowPivot() || !shadowHandle->getShadowTarget() )
	{
		return true;
	}

	position( shadowHandle->getShadowPivot().value(), shadowHandle->getShadowTarget().value(), shadowHandle->getPivotDistance().value() );

	return true;
}

void LightPositionTool::setTargetMode( TargetMode targeted )
{
	if( targeted == m_targetMode )
	{
		return;
	}

	m_targetMode = targeted;

	switch( m_targetMode )
	{
		case TargetMode::None : GafferUI::Pointer::setCurrent( "" ); break;
		case TargetMode::ShadowPivot : GafferUI::Pointer::setCurrent( "pivot" ); break;
		case TargetMode::ShadowTarget : GafferUI::Pointer::setCurrent( "target" ); break;
	}
}

void LightPositionTool::setShadowPivot( const V3f &p, ScriptNodePtr scriptNode )
{
	std::optional<V3f> currentValue = getShadowPivot();
	auto shadowHandle = static_cast<ShadowHandle *>( m_shadowHandle.get() );
	const auto pathString = selectedUpstreamPathToString( selection() );
	Action::enact(
		scriptNode,
		[t = LightPositionToolPtr( this ), k = pathString, p, shadowHandle]() {
			t->m_shadowPivotMap[k] = p;
			shadowHandle->setShadowPivot( p );
		},
		[t = LightPositionToolPtr( this ), k = pathString, currentValue, shadowHandle]() {
			t->m_shadowPivotMap[k] = currentValue;
			const std::string upstreamPath = selectedUpstreamPathToString( t->selection() );
			if( !upstreamPath.empty() && upstreamPath == k )
			{
				shadowHandle->setShadowPivot( currentValue );
			}
		}
	);
}

std::optional<V3f> LightPositionTool::getShadowPivot() const
{
	auto it = m_shadowPivotMap.find( selectedUpstreamPathToString( selection() ) );
	if( it == m_shadowPivotMap.end() )
	{
		return std::nullopt;
	}
	return it->second;
}

void LightPositionTool::setShadowTarget( const V3f &p, ScriptNodePtr scriptNode )
{
	std::optional<V3f> currentValue = getShadowTarget();
	auto shadowHandle = static_cast<ShadowHandle *>( m_shadowHandle.get() );
	const auto pathString = selectedUpstreamPathToString( selection() );
	Action::enact(
		scriptNode,
		[t = LightPositionToolPtr( this ), k = pathString, p, shadowHandle]() {
			t->m_shadowTargetMap[k] = p;
			shadowHandle->setShadowTarget( p );
		},
		[t = LightPositionToolPtr( this ), k = pathString, currentValue, shadowHandle]() {
			t->m_shadowTargetMap[k] = currentValue;
			const std::string upstreamPath = selectedUpstreamPathToString( t->selection() );
			if( !upstreamPath.empty() && upstreamPath == k )
			{
				shadowHandle->setShadowTarget( currentValue );
			}
		}
	);
}

std::optional<V3f> LightPositionTool::getShadowTarget() const
{
	auto it = m_shadowTargetMap.find( selectedUpstreamPathToString( selection() ) );
	if( it == m_shadowTargetMap.end() )
	{
		return std::nullopt;
	}
	return it->second;
}

void LightPositionTool::setShadowPivotDistance( const float d )
{
	m_shadowPivotDistanceMap[selectedUpstreamPathToString( selection() )] = d;
	static_cast<ShadowHandle *>( m_shadowHandle.get() )->setPivotDistance( d );
}

std::optional<float> LightPositionTool::getShadowPivotDistance() const
{
	auto it = m_shadowPivotDistanceMap.find( selectedUpstreamPathToString( selection() ) );
	if( it == m_shadowPivotDistanceMap.end() )
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

LightPositionTool::TranslationRotation::TranslationRotation( const Selection &selection )
	: m_selection( selection )
{
	const M44f handleRotationXform = selection.orientedTransform( Orientation::World );
	m_gadgetToRotationXform = handleRotationXform * selection.sceneToTransformSpace();

	const M44f handleTranslateXform = selection.orientedTransform( Orientation::Parent );
	m_gadgetToTranslationXform = handleTranslateXform * selection.sceneToTransformSpace();
}

bool LightPositionTool::TranslationRotation::canApply() const
{
	auto edit = m_selection.acquireTransformEdit( /* createIfNecessary = */ false );
	if( !edit )
	{
		// Edit will be created on demand in `apply()`.
		return !MetadataAlgo::readOnly( m_selection.editTarget() );
	}

	for( int i = 0; i < 3; ++i )
	{
		if(
			!canSetValueOrAddKey( edit->translate->getChild( i ) ) ||
			!canSetValueOrAddKey( edit->rotate->getChild( i ) )
		)
		{
			return false;
		}
	}

	return true;
}

void LightPositionTool::TranslationRotation::apply( const V3f &translation, const Eulerf &rotation )
{
	V3fPlug *translatePlug = m_selection.acquireTransformEdit()->translate.get();
	if( !m_originalTranslation )
	{
		Context::Scope scopedContext( m_selection.context() );
		m_originalTranslation = translatePlug->getValue();
	}

	V3f offsetInTransformSpace;
	m_gadgetToTranslationXform.multDirMatrix( translation, offsetInTransformSpace );

	V3fPlug *rotatePlug = m_selection.acquireTransformEdit()->rotate.get();

	const Imath::V3f e = updatedRotateValue( rotatePlug, rotation );
	for( int i = 0; i < 3; ++i )
	{
		FloatPlug *pTranslate = translatePlug->getChild( i );
		if( canSetValueOrAddKey( pTranslate ) )
		{
			setValueOrAddKey( pTranslate, m_selection.context()->getTime(), (*m_originalTranslation)[i] + offsetInTransformSpace[i] );
		}

		FloatPlug *pRotate = rotatePlug->getChild( i );
		if( canSetValueOrAddKey( pRotate ) )
		{
			setValueOrAddKey( pRotate, m_selection.context()->getTime(), e[i] );
		}
	}
}

V3f LightPositionTool::TranslationRotation::updatedRotateValue( const V3fPlug *rotatePlug, const Eulerf &rotation, V3f *currentValue ) const
{
	// Duplicated verbatim from `RotateTool::Rotation::updatedRotateValue()`

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
