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

#include "GafferSceneUI/LightTool.h"

#include "GafferSceneUI/Private/ParameterInspector.h"
#include "GafferSceneUI/Private/Inspector.h"
#include "GafferSceneUI/ContextAlgo.h"
#include "GafferSceneUI/SceneView.h"

#include "GafferScene/ScenePath.h"

#include "GafferUI/Handle.h"
#include "GafferUI/ImageGadget.h"
#include "GafferUI/StandardStyle.h"

#include "Gaffer/Animation.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/NameValuePlug.h"
#include "Gaffer/OptionalValuePlug.h"
#include "Gaffer/PathFilter.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/TweakPlug.h"
#include "Gaffer/UndoScope.h"

#include "IECoreGL/Camera.h"
#include "IECoreGL/CurvesPrimitive.h"
#include "IECoreGL/Group.h"
#include "IECoreGL/MeshPrimitive.h"
#include "IECoreGL/ShaderLoader.h"
#include "IECoreGL/ShaderStateComponent.h"
#include "IECoreGL/TextureLoader.h"
#include "IECoreGL/ToGLMeshConverter.h"

#include "IECoreScene/CurvesPrimitive.h"
#include "IECoreScene/MeshPrimitive.h"

#include "IECore/AngleConversion.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind/bind.hpp"

#include "OpenEXR/OpenEXRConfig.h"
#if OPENEXR_VERSION_MAJOR < 3
#include "OpenEXR/ImathMatrixAlgo.h"
#include "OpenEXR/ImathSphere.h"
#else
#include "Imath/ImathMatrixAlgo.h"
#include "Imath/ImathSphere.h"
#endif

#include "fmt/format.h"

#include <algorithm>

using namespace boost::placeholders;
using namespace Imath;
using namespace IECoreScene;
using namespace IECoreGL;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;
using namespace GafferSceneUI::Private;

// ============================================================================
// Utility Functions
// ============================================================================

namespace
{

const std::string g_lightAttributePattern = "light *:light";

const Color3f g_lightToolHandleColor = Color3f( 0.825, 0.720f, 0.230f );

// Color from `StandardLightVisualiser`
const Color3f g_lightToolHighlightColor = Color3f( 1.0f, 0.835f, 0.07f );
const Color4f g_lightToolHighlightColor4 = Color4f( g_lightToolHighlightColor.x, g_lightToolHighlightColor.y, g_lightToolHighlightColor.z, 1.f );

const Color4f g_lightToolDisabledColor4 = Color4f( 0.4f, 0.4f, 0.4f, 1.f );

// Multiplied by the highlight color for drawing a parameter's previous value
const float g_highlightMultiplier = 0.8f;

const InternedString g_lightVisualiserScaleAttributeName( "gl:visualiser:scale" );
const InternedString g_frustumScaleAttributeName( "gl:light:frustumScale" );
const InternedString g_insetPenumbraType( "inset" );
const InternedString g_outsetPenumbraType( "outset" );
const InternedString g_absolutePenumbraType( "absolute" );

const float g_circleHandleWidth = 4.375f;
const float g_circleHandleWidthLarge = 5.25f;
const float g_circleHandleSelectionWidth = 8.875f;

const float g_lineHandleWidth = 0.875f;
const float g_lineHandleWidthLarge = 1.75f;
const float g_lineSelectionWidth = 5.25f;

const float g_minorLineHandleWidth = 0.4375f;
const float g_minorLineHandleWidthLarge = 0.875f;

const float g_dragArcWidth = 24.f;

const float g_arrowHandleSize = g_circleHandleWidth * 2.f;
const float g_arrowHandleSizeLarge = g_circleHandleWidthLarge * 2.f;
const float g_arrowHandleSelectionSize = g_circleHandleSelectionWidth * 2.f;

const float g_spotLightHandleSizeMultiplier = 1 / 1.75f;

const Color4f g_hoverTextColor( 1, 1, 1, 1 );

const int g_warningTipCount = 3;

const ModifiableEvent::Modifiers g_quadLightConstrainAspectRatioKey = ModifiableEvent::Modifiers::Control;

const InternedString g_coneAngleParameter = "coneAngleParameter";
const InternedString g_penumbraAngleParameter = "penumbraAngleParameter";

// Return the plug that holds the value we need to edit, and make sure it's enabled.

/// \todo This currently does nothing to enable a row if is disabled. Is that worth doing?

Plug *activeValuePlug( Plug *sourcePlug )
{
	if( auto nameValuePlug = runTimeCast<NameValuePlug>( sourcePlug ) )
	{
		nameValuePlug->enabledPlug()->setValue( true );
		return nameValuePlug->valuePlug();
	}
	if( auto tweakPlug = runTimeCast<TweakPlug>( sourcePlug ) )
	{
		tweakPlug->enabledPlug()->setValue( true );
		return tweakPlug->valuePlug();
	}
	if( auto optionalValuePlug = runTimeCast<OptionalValuePlug>( sourcePlug ) )
	{
		optionalValuePlug->enabledPlug()->setValue( true );
		return optionalValuePlug->valuePlug();
	}
	return sourcePlug;
}

void setValueOrAddKey( FloatPlug *plug, float time, float value )
{
	if( Animation::isAnimated( plug ) )
	{
		Animation::CurvePlug *curve = Animation::acquire( plug );
		curve->insertKey( time, value );
	}
	else
	{
		plug->setValue( value );
	}
}

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

const char *translucentConstantFragSource()
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
		"	gl_FragColor = vec4( fragmentCs, 0.375 );"
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

IECoreScene::MeshPrimitivePtr solidArc( float minorRadius, float majorRadius, float startFraction, float stopFraction, const Color3f &color )
{
	IntVectorDataPtr vertsPerPolyData = new IntVectorData;
	IntVectorDataPtr vertIdsData = new IntVectorData;
	V3fVectorDataPtr pData = new V3fVectorData;

	std::vector<int> &vertsPerPoly = vertsPerPolyData->writable();
	std::vector<int> &vertIds = vertIdsData->writable();
	std::vector<V3f> &p = pData->writable();

	const int numCircleDivisions = 100;
	const int numSegments = std::max( 1, (int)ceil( abs( stopFraction - startFraction ) * numCircleDivisions ) );

	for( int i = 0; i < numSegments + 1; ++i )
	{
		const float a = ( startFraction + ( stopFraction - startFraction ) * (float)i / (float)numSegments ) * 2.f * M_PI;
		p.push_back( V3f( sin( a ), 0, cos( a ) ) * minorRadius );
		p.push_back( V3f( sin( a ), 0, cos( a ) ) * majorRadius );
	}

	for( int i = 0; i < numSegments; ++i )
	{

		vertIds.push_back( i * 2 );
		vertIds.push_back( i * 2 + 1 );
		vertIds.push_back( i * 2 + 3 );
		vertIds.push_back( i * 2 + 2 );
		vertsPerPoly.push_back( 4 );
	}

	IECoreScene::MeshPrimitivePtr solidAngle = new IECoreScene::MeshPrimitive( vertsPerPolyData, vertIdsData, "linear", pData );
	solidAngle->variables["N"] = IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new V3fData( V3f( 0, 1, 0 ) ) );
	solidAngle->variables["Cs"] = IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( color ) );

	return solidAngle;
}

enum class Axis { X, Y, Z };

// Reorients `p` so that `p.z` points along the positive `axis`
V3f axisAlignedVector( const Axis axis, const V3f &p )
{
	return axis == Axis::X ? V3f( p.z, p.y, p.x ) : ( axis == Axis::Y ? V3f( p.x, p.z, p.y ) : p );
}

IECoreGL::MeshPrimitivePtr circle( const Axis axis = Axis::X, const V3f &offset = V3f( 0 ) )
{
	IntVectorDataPtr vertsPerPolyData = new IntVectorData;
	IntVectorDataPtr vertIdsData = new IntVectorData;
	V3fVectorDataPtr pData = new V3fVectorData;

	std::vector<int> &vertsPerPoly = vertsPerPolyData->writable();
	std::vector<int> &vertIds = vertIdsData->writable();
	std::vector<V3f> &p = pData->writable();

	p.push_back( offset );

	const int numSegments = 20;
	for( int i = 0; i < numSegments + 1; ++i )
	{
		const float a = ( (float)i / (float)numSegments ) * 2.f * M_PI;
		const V3f v = axisAlignedVector( axis, V3f( -sin( a ), cos( a ), 0 ) );
		p.push_back( v + offset );
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
	IECoreGL::MeshPrimitivePtr result = runTimeCast<IECoreGL::MeshPrimitive>( converter->convert() );

	return result;
}

IECoreGL::MeshPrimitivePtr ring()
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

	const int numSegments = 20;
	for( int i = 0; i < numSegments + 1; ++i )
	{
		const float a = ( (float)i / (float)numSegments ) * 2.f * M_PI;
		const V3f dir( 0, cos( a ) , -sin( a ) );  // Face the X-axis

		p.push_back( dir * 1.f );
		p.push_back( dir * 0.5f );
	}
	for( int i = 0; i < numSegments; ++i )
	{
		vertIds.push_back( i * 2 );
		vertIds.push_back( i * 2 + 1 );
		vertIds.push_back( i * 2 + 3 );
		vertIds.push_back( i * 2 + 2 );
		vertsPerPoly.push_back( 4 );
	}

	IECoreScene::MeshPrimitivePtr ring = new IECoreScene::MeshPrimitive( vertsPerPolyData, vertIdsData, "linear", pData );
	ToGLMeshConverterPtr converter = new ToGLMeshConverter( ring );
	result = runTimeCast<IECoreGL::MeshPrimitive>( converter->convert() );

	return result;
}

// Returns a (potentially truncated) cone facing the +Z axis.
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
		p.push_back( V3f( -sin( a ) * endRadius, cos( a ) * endRadius, height ) );  // Face the +Z axis
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

// Returns a cone faceing the +Z axis.
IECoreGL::MeshPrimitivePtr unitCone()
{
	static IECoreGL::MeshPrimitivePtr result = cone( 1.5f, 0.5f, 0 );
	return result;
}

IECoreGL::MeshPrimitivePtr torus( const float width, const float height, const float tubeRadius, const Handle *handle, const Axis axis )
{
	IECoreGL::MeshPrimitivePtr result;

	IECore::IntVectorDataPtr verticesPerFaceData = new IECore::IntVectorData;
	std::vector<int> &verticesPerFace = verticesPerFaceData->writable();

	IECore::IntVectorDataPtr vertexIdsData = new IECore::IntVectorData;
	std::vector<int> &vertexIds = vertexIdsData->writable();

	IECore::V3fVectorDataPtr pData = new IECore::V3fVectorData;
	std::vector<V3f> &p = pData->writable();

	const V3f radiusScale = V3f( width, height, 0 );

	const int numDivisionsI = 60;
	const int numDivisionsJ = 15;
	for( int i = 0; i < numDivisionsI; ++i )
	{
		const float iAngle = 2 * M_PI * (float)i / (float)( numDivisionsI - 1 );
		const V3f v = V3f( -sin( iAngle ), cos( iAngle ), 0 );
		const V3f tubeCenter = v * radiusScale;

		const int ii = i == numDivisionsI - 1 ? 0 : i + 1;

		const float jRadius = tubeRadius * rasterScaleFactor( handle, tubeCenter );

		for( int j = 0; j < numDivisionsJ; ++j )
		{
			const float jAngle = 2 * M_PI * (float)j / (float)( numDivisionsJ - 1 );

			p.push_back(
				axisAlignedVector(
					axis,
					tubeCenter + jRadius * ( cos( jAngle ) * v + V3f( 0, 0, sin( jAngle ) ) )
				)
			);

			const int jj = j == numDivisionsJ - 1 ? 0 : j + 1;

			verticesPerFace.push_back( 4 );

			vertexIds.push_back( i * numDivisionsJ + j );
			vertexIds.push_back( i * numDivisionsJ + jj );
			vertexIds.push_back( ii * numDivisionsJ + jj );
			vertexIds.push_back( ii * numDivisionsJ + j );
		}
	}

	IECoreScene::MeshPrimitivePtr mesh = new IECoreScene::MeshPrimitive( verticesPerFaceData, vertexIdsData, "linear", pData );
	IECoreGL::ToGLMeshConverterPtr converter = new ToGLMeshConverter( mesh );
	result = runTimeCast<IECoreGL::MeshPrimitive>( converter->convert() );

	return result;
}

GraphComponent *commonAncestor( std::vector<GraphComponent *> &graphComponents )
{
	const size_t gcSize = graphComponents.size();
	if( gcSize == 0 )
	{
		return nullptr;
	}
	if( gcSize == 1 )
	{
		return graphComponents[0];
	}

	GraphComponent *commonAncestor = graphComponents[0]->commonAncestor( graphComponents[1] );

	for( size_t i = 2; i < gcSize; ++i )
	{
		if( commonAncestor->isAncestorOf( graphComponents[i] ) )
		{
			continue;
		}
		commonAncestor = graphComponents[i]->commonAncestor( commonAncestor );
	}

	return commonAncestor;
}

const float g_tipScale = 10.f;
const float g_tipIconSize = 1.25f;
const float g_tipIconOffset = -0.25f;
const float g_tipIndent = 1.75f;
const float g_tipLineSpacing = -1.375f;

void drawSelectionTips(
	const V3f &gadgetSpacePosition,
	std::vector<const Inspector::Result *> inspections,
	const std::string multiPlugDescription,
	const std::string infoSuffix,
	const Handle *handle,
	const ViewportGadget *viewport,
	const GafferUI::Style *style
)
{
	std::vector<GraphComponent *> parameterSources;
	std::vector<std::string> warningTips;
	for( const auto &inspection : inspections )
	{
		if( auto source = inspection->source() )
		{
			EditScope *editScope = inspection->editScope();
			if( !editScope || ( editScope && editScope->isAncestorOf( source ) ) )
			{
				parameterSources.push_back( source );
			}
			else
			{
				parameterSources.push_back( editScope );
			}

			if( inspection->editable() && !inspection->editWarning().empty() )
			{
				warningTips.push_back( inspection->editWarning() );
			}
			else if( !inspection->editable() )
			{
				warningTips.push_back( inspection->nonEditableReason() );
			}
		}
	}

	std::string parameterInfo;
	if( parameterSources.size() == 1 )
	{
		parameterInfo = fmt::format(
			"Editing : {}",
			parameterSources.front()->relativeName( parameterSources.front()->ancestor<ScriptNode>() )
		);
	}
	else if( parameterSources.size() > 1 )
	{
		GraphComponent *commonAncestor = ::commonAncestor( parameterSources );

		parameterInfo = fmt::format( "Editing {} {}", parameterSources.size(), multiPlugDescription );

		if( commonAncestor && (Gaffer::TypeId)commonAncestor->typeId() != Gaffer::TypeId::ScriptNodeTypeId )
		{
			parameterInfo += fmt::format(
				" on {}",
				commonAncestor->relativeName( commonAncestor->ancestor<ScriptNode>() )
			);
		}
	}

	std::string warningInfo;
	int warningSize = (int)warningTips.size();
	int warningLines = 0;
	for( int i = 0, eI = std::min( warningSize, g_warningTipCount ); i < eI; ++i )
	{
		warningInfo += warningTips[i] + ( i < eI -1 ? "\n" : "" );
		warningLines++;
	}
	if( warningSize == g_warningTipCount + 1 )
	{
		// May as well print the real warning instead of a mysterious "and 1 more"
		warningInfo += "\n" + warningTips[warningSize - 1];
		warningLines++;
	}
	if( warningSize > g_warningTipCount + 1 )
	{
		warningInfo += fmt::format( "\nand {} more", warningSize - g_warningTipCount );
		warningLines++;
	}

	ViewportGadget::RasterScope rasterScope( viewport );

	glPushAttrib( GL_DEPTH_BUFFER_BIT );

	glDisable( GL_DEPTH_TEST );
	glDepthMask( GL_FALSE );

	glPushMatrix();

	const V2f rasterPosition = viewport->gadgetToRasterSpace( gadgetSpacePosition, handle );
	const Box3f infoBound = style->textBound( Style::TextType::BodyText, parameterInfo );
	const Box3f warningBound = style->textBound( Style::TextType::BodyText, warningInfo );

	const float maxWidth = std::max( infoBound.max.x, warningBound.max.x );

	const V2i screenBound = viewport->getViewport();

	const float x =
		(rasterPosition.x + 15.f ) -
		std::max( ( rasterPosition.x + 15.f + maxWidth * g_tipScale ) - ( screenBound.x - 45.f ), 0.f )
	;
	float y = rasterPosition.y + g_tipLineSpacing * g_tipScale;
	if( !warningInfo.empty() )
	{
		y += g_tipLineSpacing * g_tipScale;
	}
	if( !infoSuffix.empty() )
	{
		y += g_tipLineSpacing * g_tipScale;
	}

	glTranslate( V2f( x, y ) );
	glScalef( g_tipScale, -g_tipScale, g_tipScale );

	IECoreGL::ConstTexturePtr infoTexture = ImageGadget::loadTexture( "infoSmall.png" );
	glPushMatrix();
	glTranslate( V2f( 0, g_tipIconOffset ) );
	style->renderImage( Box2f( V2f( 0 ), V2f( g_tipIconSize ) ), infoTexture.get() );
	glPopMatrix();

	glPushMatrix();
	glTranslate( V2f( g_tipIndent, 0 ) );
	style->renderText( Style::TextType::BodyText, parameterInfo, Style::NormalState, &g_hoverTextColor );
	glPopMatrix();

	if( !warningInfo.empty() )
	{
		IECoreGL::ConstTexturePtr warningTexture = ImageGadget::loadTexture( "warningSmall.png" );
		glPushMatrix();
		glTranslate( V2f( 0, g_tipIconOffset) );
		for( int i = 0; i < warningLines; ++i )
		{
			glTranslate( V2f( 0, g_tipLineSpacing ) );
			style->renderImage( Box2f( V2f( 0 ), V2f( g_tipIconSize ) ), warningTexture.get() );
		}
		glPopMatrix();

		glPushMatrix();
		glTranslate( V2f( g_tipIndent, g_tipLineSpacing ) );
		style->renderText( Style::TextType::BodyText, warningInfo, Style::NormalState, &g_hoverTextColor );
		glPopMatrix();
	}
	if( !infoSuffix.empty() )
	{
		glTranslate( V2f( g_tipIndent, g_tipLineSpacing * ( warningLines + 1 ) ) );
		style->renderText( Style::TextType::BodyText, infoSuffix, Style::NormalState, &g_hoverTextColor );
	}

	glPopMatrix();
	glPopAttrib();
}

float sphereSpokeClickAngle( const Line3f &eventLine, float radius, float spokeAngle, float &newAngle )
{
	const float B = 2.f * ( eventLine.dir ^ eventLine.pos );
	const float C = ( eventLine.pos ^ eventLine.pos ) - ( radius * radius );

	const float discriminant = B * B - 4.f * C;
	// If discriminant is negative, the click is outside the sphere.
	if( discriminant < 0 )
	{
		return false;
	}

	// t = ( -B +/- sqrt( B^2 - 4AC ) ) / 2A ( A = 1 )
	const float sqRoot = std::sqrt( discriminant );

	const V3f minusP = eventLine( ( -B - sqRoot ) * 0.5f );
	const V3f plusP = eventLine( ( -B + sqRoot ) * 0.5f );

	if( minusP.z > 0 && plusP.z > 0 )
	{
		newAngle = 180.f;
		return true;
	}
	else if( minusP.z >= 0 && plusP.z < 0 )
	{
		newAngle = radiansToDegrees( atan2( -plusP.x, -plusP.z ) );
		return true;
	}
	else if( minusP.z < 0 && plusP.z >= 0 )
	{
		newAngle = radiansToDegrees( atan2( -minusP.x, -minusP.z ) );
		return true;
	}

	const M44f r = M44f().rotate( V3f( 0, degreesToRadians( spokeAngle ), 0 ) );
	const Line3f handleLine( V3f( 0 ), V3f( 0, 0, -radius ) * r );

	const V3f p = handleLine.distanceTo( minusP ) < handleLine.distanceTo( plusP ) ? minusP : plusP;
	newAngle = radiansToDegrees( atan2( -p.x, -p.z ) );

	return true;
}

// Returns the intersection point between the line and sphere closest to the line origin.
// If the line and sphere don't intersect, returns the closest point between them.
template<typename T>
T lineSphereIntersection( const LineSegment<T> &line, const T &center, const float radius )
{
	const LineSegment<T> offsetLine( line.p0 - center, line.p1 - center );
	const T direction = line.direction();
	const float A = direction.dot( direction );
	const float B = 2.f * ( direction ^ ( offsetLine.p0 ) );
	const float C = ( offsetLine.p0 ^ offsetLine.p0 ) - ( radius * radius );

	const float discriminant = B * B - 4.f * A * C;
	if( discriminant < 0 )
	{
		return line.closestPointTo( center );
	}

	return line( ( -B - std::sqrt( discriminant ) ) / ( 2.f * A ) );
}

// ============================================================================
// LightToolHandle
// ============================================================================

class LightToolHandle : public Handle
{

	public :

		using InspectionMap = std::unordered_map<InternedString, Inspector::ResultPtr>;

		~LightToolHandle() override
		{

		}

		// Update inspectors and data needed to display and interact with the handle. Called
		// in `preRender()` if the inspections are dirty.
		void updateHandlePath( ScenePlugPtr scene, const Context *context, const ScenePlug::ScenePath &handlePath )
		{
			m_scene = scene;
			m_context = context;
			m_handlePath = handlePath;

			m_inspectors.clear();

			if( !m_scene->exists( m_handlePath ) )
			{
				return;
			}

			m_editScope = m_view->editScopePlug();

			/// \todo This can be simplified and some of the logic, especially getting the inspectors, can
			/// be moved to the constructor when we standardize on a single USDLux light representation.

			ConstCompoundObjectPtr attributes = m_scene->fullAttributes( m_handlePath );

			for( const auto &[attributeName, value ] : attributes->members() )
			{
				if(
					StringAlgo::matchMultiple( attributeName, g_lightAttributePattern ) &&
					value->typeId() == (IECore::TypeId)ShaderNetworkTypeId
				)
				{
					const auto shader = attributes->member<ShaderNetwork>( attributeName )->outputShader();
					std::string shaderAttribute = shader->getType() + ":" + shader->getName();

					if( !isLightType( shaderAttribute ) )
					{
						continue;
					}

					for( const auto &m : m_metaParameters )
					{
						if( auto parameter = Metadata::value<StringData>( shaderAttribute, m ) )
						{
							m_inspectors[m] = new ParameterInspector(
								m_scene,
								m_editScope,
								attributeName,
								ShaderNetwork::Parameter( "", parameter->readable() )
							);
						}
					}

					break;
				}
			}

			handlePathChanged();
		}

		/// \todo Should these three be protected, or left out entirely until they are needed by client code?
		const ScenePlug *scene() const
		{
			return m_scene.get();
		}

		const Context *context() const
		{
			return m_context;
		}

		const ScenePlug::ScenePath &handlePath() const
		{
			return m_handlePath;
		}

		/// \todo Remove these and handle the lookThrough logic internally?
		void setLookThroughLight( bool lookThroughLight )
		{
			m_lookThroughLight = lookThroughLight;
		}

		bool getLookThroughLight() const
		{
			return m_lookThroughLight;
		}

		// Adds an inspection for all metaParameters for the current context.
		void addInspection()
		{
			InspectionMap inspectionMap;
			for( const auto &m : m_metaParameters )
			{
				if( Inspector::ResultPtr i = inspection( m ) )
				{
					inspectionMap[m] = i;
				}
			}

			m_inspections.push_back( inspectionMap );
		}

		void clearInspections()
		{
			m_inspections.clear();
		}

		// Called by `LightTool` to handle `dragMove` events.
		bool handleDragMove( const GafferUI::DragDropEvent &event )
		{
			if( m_inspections.empty() || !allInspectionsEnabled() )
			{
				return true;
			}

			const bool result = handleDragMoveInternal( event );
			updateTooltipPosition( event.line );

			return result;
		}

		// Called by `LightTool` at the end of a drag event.
		bool handleDragEnd()
		{
			m_dragStartInspection.clear();

			return handleDragEndInternal();
		}

		// Called by `LightTool` when the transform changes for the scene location the handle
		// is attached to.
		void updateLocalTransform( const V3f &scale, const V3f &shear )
		{
			updateLocalTransformInternal( scale, shear );
		}

		// Called by `LightTool` to determine if the handle is enabled.
		bool enabled() const
		{
			// Return true without checking the `enabled()` state of our inspections.
			// This allows the tooltip-on-highlight behavior to show a tooltip explaining
			// why an edit is not possible. The alternative is to draw the tooltip for all
			// handles regardless of mouse position because a handle can only be in a disabled
			// or highlighted drawing state.
			// The drawing code takes care of graying out uneditable handles and the inspections
			// prevent the value from being changed.
			return !m_inspectors.empty();
		}

		// Called by `LightTool` to determine if the handle is visible.
		bool visible() const
		{
			if( m_inspectors.empty() )
			{
				return false;
			}

			for( const auto &i : m_inspectors )
			{
				if( !i.second->inspect() )
				{
					return false;
				}
			}

			return visibleInternal();
		}

	protected :

		// Protected to reinforce that `LightToolHandle` can not be created directly, only
		// derived classes.
		LightToolHandle(
			const std::string &lightTypePattern,
			SceneView *view,
			const std::vector<InternedString> &metaParameters,
			const std::string &name
		) :
			Handle( name ),
			m_lightTypePattern( lightTypePattern ),
			m_view( view ),
			m_metaParameters( metaParameters ),
			m_inspectors(),
			m_inspections(),
			m_dragStartInspection(),
			m_tooltipPosition(),
			m_lookThroughLight( false )
		{
			mouseMoveSignal().connect( boost::bind( &LightToolHandle::mouseMove, this, ::_2 ) );
		}

		// Returns true if `shaderAttribute` refers to the same light type
		// as this handle was constructed to apply to.
		bool isLightType( const std::string &shaderAttribute ) const
		{
			auto lightType = Metadata::value<StringData>( shaderAttribute, "type" );

			if( !lightType || !StringAlgo::matchMultiple( lightType->readable(), m_lightTypePattern ) )
			{
				return false;
			}

			return true;
		}

		// Returns the inspection stored when the drag event started. Returns `nullptr`
		// if not inspection was stored.
		Inspector::ResultPtr dragStartInspection( const InternedString &metaParameter ) const
		{
			auto it = m_dragStartInspection.find( metaParameter );
			if( it != m_dragStartInspection.end() )
			{
				return it->second;
			}
			return nullptr;
		}

		// Returns the inspection for the scene location the handle is attached to.
		// Returns `nullptr` if no inspection exists for the handle.
		Inspector::ResultPtr handleInspection( const InternedString &metaParameter ) const
		{
			ScenePlug::PathScope pathScope( m_context );
			pathScope.setPath( &m_handlePath );

			return inspection( metaParameter );
		}

		// Applies an multiplier edit to all of the inspections for `metaParameter`.
		void applyMultiplier( const InternedString &metaParameter, const float mult )
		{
			for( const auto &i : m_inspections )
			{
				auto it = i.find( metaParameter );
				if( it == i.end() )
				{
					continue;
				}

				ValuePlugPtr parameterPlug = it->second->acquireEdit();
				auto floatPlug = runTimeCast<FloatPlug>( activeValuePlug( parameterPlug.get() ) );
				if( !floatPlug )
				{
					throw Exception( fmt::format( "\"{}\" parameter must use `FloatPlug`", metaParameter.string() ) );
				}

				const float originalValue = it->second->typedValue<float>( 0.f );
				const float nonZeroValue = originalValue == 0 ? 1.f : originalValue;
				setValueOrAddKey( floatPlug, m_view->getContext()->getTime(), nonZeroValue * mult );

			}
		}

		// Increments the values for all inspections for `metaParameter`, limiting the resulting
		// values to minimum and maximum values.
		void applyIncrement( const InternedString &metaParameter, const float incr, const float minValue, const float maxValue )
		{
			for( const auto &i : m_inspections )
			{
				auto it = i.find( metaParameter );
				if( it == i.end() )
				{
					continue;
				}

				ValuePlugPtr parameterPlug = it->second->acquireEdit();
				auto floatPlug = runTimeCast<FloatPlug>( activeValuePlug( parameterPlug.get() ) );
				if( !floatPlug )
				{
					throw Exception( fmt::format( "\"{}\" parameter must use `FloatPlug`", metaParameter.string() ) );
				}

				const float originalValue = it->second->typedValue<float>( 0.f );
				setValueOrAddKey(
					floatPlug,
					m_view->getContext()->getTime(),
					std::clamp( originalValue + incr, minValue, maxValue )
				);
			}
		}

		bool hasInspectors() const
		{
			return !m_inspectors.empty();
		}

		const std::vector<InspectionMap> &inspections() const
		{
			return m_inspections;
		}

		// Sets the position of the tooltip in gadget space.
		void setTooltipPosition( const V3f &p )
		{
			m_tooltipPosition = p;
		}

		const V3f getTooltipPosition() const
		{
			return m_tooltipPosition;
		}

		const SceneView *view() const
		{
			return m_view;
		}

		const Inspector *inspector( const InternedString &metaParameter ) const
		{
			const auto it = m_inspectors.find( metaParameter );
			if( it == m_inspectors.end() )
			{
				return nullptr;
			}

			return it->second.get();
		}

		// The following protected methods are used by derived classes to implement
		// handle-specific behavior.

		// May be overriden to update internal state when the scene location the handle
		// is attached to changes.
		virtual void handlePathChanged()
		{

		}

		// May be overriden to clean up internal state after a drag.
		virtual bool handleDragEndInternal()
		{
			return false;
		}

		// May be overridden to set the local transform of the handle
		// relative to the light. The parent of the handle will have rotation and translation
		// set independently. `scale` and `shear` are passed here to allow the handle to decide
		// how to deal with those transforms.
		/// \todo Should this be something like `setScaleAndShear()` and rework `updateLocalTransform()`?
		virtual void updateLocalTransformInternal( const V3f &, const V3f & )
		{

		}

		// Called by `visible()`, may be overridden to extend the logic determining visibility.
		// Called with `scenePath` set in the current context.
		virtual bool visibleInternal() const
		{
			return true;
		}

		// Called by `renderHandle()`, may be overridden to return a string suffix to be
		// displayed in a tool tip after the plug count in the case of modifying multiple
		// unrelated plugs.
		virtual std::string tipPlugSuffix() const
		{
			return "";
		}

		// Called by `renderHandle()`, may be overridden to include a string suffix to be
		// displayed at the end of the entire tool tip.
		virtual std::string tipInfoSuffix() const
		{
			return "";
		}

		// May be overridden to return a vector of inspection results that will receive
		// edits from this handle. By default, returns all inspections.
		// Handles can hold inspections for additional parameters
		// than those being edited, but only the inspections returned from `handleValueInspections()`
		// will be considered for editing and related UI indications.
		virtual std::vector<const Inspector::Result *> handleValueInspections() const
		{
			std::vector<const Inspector::Result *> result;
			for( const auto &i : m_inspections )
			{
				for( const auto &p : i )
				{
					result.push_back( p.second.get() );
				}
			}

			return result;
		}

		// Must be overriden to set the tooltip position in gadget space based
		// on `eventLine` from a `DragDropEvent` or `ButtonEvent`.
		virtual void updateTooltipPosition( const LineSegment3f &eventLine ) = 0;

		// Must be overriden to make edits to the inspections in `handleDragMove()`.
		virtual bool handleDragMoveInternal( const GafferUI::DragDropEvent &event ) = 0;

		// Must be overridden to add `IECoreGL` components to `rootGroup` in `renderHandle()`.
		virtual void addHandleVisualisation( IECoreGL::Group *rootGroup, const bool selectionPass, const bool highlighted ) const = 0;

		// Must be overridden to prepare for the drag in `dragBegin()`.
		virtual void setupDrag( const DragDropEvent &event ) = 0;

	private :

		bool mouseMove( const ButtonEvent &event )
		{
			updateTooltipPosition( event.line );
			dirty( DirtyType::Render );

			return false;
		}

		void renderHandle( const Style *style, Style::State state ) const override
		{
			State::bindBaseState();
			auto glState = const_cast<State *>( State::defaultState() );

			IECoreGL::GroupPtr group = new IECoreGL::Group;

			const bool highlighted = state == Style::State::HighlightedState;
			const bool selectionPass = (bool)IECoreGL::Selector::currentSelector();

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
			assert( standardStyle );
			const Color3f highlightColor3 = standardStyle->getColor( StandardStyle::Color::HighlightColor );
			const Color4f highlightColor4 = Color4f( highlightColor3.x, highlightColor3.y, highlightColor3.z, 1.f );

			const bool enabled = allInspectionsEnabled();

			group->getState()->add(
				new IECoreGL::Color(
					enabled ? ( highlighted ? g_lightToolHighlightColor4 : highlightColor4 ) : g_lightToolDisabledColor4
				)
			);

			addHandleVisualisation( group.get(), selectionPass, highlighted );

			group->render( glState );

			if( highlighted )
			{
				std::vector<const Inspector::Result *> inspections = handleValueInspections();

				drawSelectionTips(
					m_tooltipPosition,
					inspections,
					tipPlugSuffix(),
					tipInfoSuffix(),
					this,
					m_view->viewportGadget(),
					style
				);
			}
		}

		void dragBegin( const DragDropEvent &event ) override
		{
			for( const auto &m : m_metaParameters )
			{
				if( Inspector::ResultPtr i = handleInspection( m ) )
				{
					m_dragStartInspection[m] = i;
				}
			}

			setupDrag( event );
		}

		// Returns the inspection for `metaParameter` in the current context.
		// Returns `nullptr` if no inspector or no inspection exists.
		Inspector::ResultPtr inspection( const InternedString &metaParameter ) const
		{
			auto it = m_inspectors.find( metaParameter );
			if( it == m_inspectors.end() )
			{
				return nullptr;
			}

			if( Inspector::ResultPtr inspection = it->second->inspect() )
			{
				return inspection;
			}

			return nullptr;
		}

		bool allInspectionsEnabled() const
		{
			std::vector<const Inspector::Result *> requiredInspections = handleValueInspections();
			if( requiredInspections.empty() )
			{
				return false;
			}

			bool enabled = true;
			for( const auto &i : requiredInspections )
			{
				enabled &= i && i->editable();
			}

			return enabled;
		}

		ScenePlugPtr m_scene;
		const Context *m_context;
		ScenePlug::ScenePath m_handlePath;

		const std::string m_lightTypePattern;
		SceneView *m_view;
		Gaffer::PlugPtr m_editScope;
		const std::vector<InternedString> m_metaParameters;

		using InspectorMap = std::unordered_map<InternedString, InspectorPtr>;
		InspectorMap m_inspectors;

		std::vector<InspectionMap> m_inspections;
		InspectionMap m_dragStartInspection;
		V3f m_tooltipPosition;

		bool m_lookThroughLight;
};

// ============================================================================
// SpotLightHandle
// ============================================================================

class SpotLightHandle : public LightToolHandle
{
	public :

		enum class HandleType
		{
			Cone,
			Penumbra
		};

		SpotLightHandle(
			const std::string &lightType,
			HandleType handleType,
			SceneView *view,
			const float zRotation,
			const std::string &name
		) :
			LightToolHandle( lightType, view, { g_coneAngleParameter, g_penumbraAngleParameter }, name ),
			m_zRotation( zRotation ),
			m_handleType( handleType ),
			m_angleMultiplier( 1.f ),
			m_visualiserScale( 1.f ),
			m_frustumScale( 1.f ),
			m_lensRadius( 0 )
		{
		}
		~SpotLightHandle() override
		{

		}

	protected :

		void addHandleVisualisation( IECoreGL::Group *rootGroup, const bool selectionPass, const bool highlighted ) const override
		{
			// Line along cone. Use a cylinder because GL_LINE with width > 1
			// are not reliably selected.

			GroupPtr spokeGroup = new Group;

			float spokeRadius = 0;
			float handleRadius = 0;

			if( selectionPass )
			{
				spokeRadius = g_lineSelectionWidth;
				handleRadius = g_circleHandleSelectionWidth;
			}
			else
			{
				spokeRadius = m_handleType == HandleType::Cone ? (
					highlighted ? g_lineHandleWidthLarge : g_lineHandleWidth
				) : (
					highlighted ? g_minorLineHandleWidthLarge : g_minorLineHandleWidth
				);

				handleRadius = highlighted ? g_circleHandleWidthLarge : g_circleHandleWidth;
			}

			spokeRadius *= g_spotLightHandleSizeMultiplier;
			handleRadius *= g_spotLightHandleSizeMultiplier;

			const V3f farP = V3f( 0, 0, m_frustumScale * m_visualiserScale * -10.f );
			const auto &[coneHandleAngle, penumbraHandleAngle] = handleAngles();
			const float angle = m_handleType == HandleType::Cone ? coneHandleAngle : penumbraHandleAngle.value();

			const M44f handleTransform = M44f().rotate( V3f( 0, degreesToRadians( angle ), 0 ) );

			spokeGroup->addChild(
				cone(
					m_visualiserScale * m_frustumScale * -10.f,
					spokeRadius * ::rasterScaleFactor( this, V3f( 0 ) ),
					spokeRadius * ::rasterScaleFactor( this, farP * handleTransform )
				)
			);

			rootGroup->addChild( spokeGroup );

			// Circles at end of cone and frustum

			IECoreGL::GroupPtr iconGroup = new IECoreGL::Group;

			iconGroup->getState()->add(
				new IECoreGL::ShaderStateComponent(
					ShaderLoader::defaultShaderLoader(),
					TextureLoader::defaultTextureLoader(),
					faceCameraVertexSource(),
					"",
					constantFragSource(),
					new CompoundObject
				)
			);

			IECoreGL::MeshPrimitivePtr decoration;
			if(
				( m_handleType == HandleType::Cone && inspector( g_penumbraAngleParameter ) && ( !m_penumbraType || m_penumbraType == g_insetPenumbraType ) ) ||
				( m_handleType == HandleType::Penumbra && ( m_penumbraType == g_outsetPenumbraType || m_penumbraType == g_absolutePenumbraType ) )
			)
			{
				decoration = ring();
			}
			else
			{
				decoration = circle();
			}

			IECoreGL::GroupPtr nearIconGroup = new IECoreGL::Group;
			nearIconGroup->addChild( decoration );

			const V3f nearP = V3f( 0, 0, -m_visualiserScale );

			nearIconGroup->setTransform(
				M44f().scale( V3f( handleRadius ) * ::rasterScaleFactor( this, nearP * handleTransform ) ) *
				M44f().translate( nearP )
			);
			iconGroup->addChild( nearIconGroup );

			IECoreGL::GroupPtr farIconGroup = new IECoreGL::Group;
			const float farRasterScaleFactor = ::rasterScaleFactor( this, farP * handleTransform );
			farIconGroup->addChild( decoration );
			farIconGroup->setTransform(
				M44f().scale( V3f( handleRadius ) * farRasterScaleFactor ) *
				M44f().translate(  farP + V3f( 0, 0, -handleRadius * farRasterScaleFactor ) )
			);
			iconGroup->addChild( farIconGroup );

			rootGroup->addChild( iconGroup );

			// Drag arcs

			if( m_drag && !getLookThroughLight() )
			{
				const float currentFraction = angle / 360.f;

				Inspector::ResultPtr coneInspection = dragStartInspection( g_coneAngleParameter );
				Inspector::ResultPtr penumbraInspection = dragStartInspection( g_penumbraAngleParameter );

				const float previousFraction = !inspections().empty() ?
					( m_handleType == HandleType::Cone ?
						this->coneHandleAngle( coneInspection->typedValue<float>( 0.f ) ) :
						this->penumbraHandleAngle( penumbraInspection->typedValue<float>( 0.f ) )
					) / 360.f : currentFraction;

				IECoreScene::MeshPrimitivePtr previousSolidArc = nullptr;
				IECoreScene::MeshPrimitivePtr currentSolidArc = nullptr;

				const Color3f previousColor = g_lightToolHandleColor * g_highlightMultiplier;
				const Color3f currentColor = g_lightToolHandleColor;

				const float arcWidth = g_dragArcWidth * ::rasterScaleFactor( this, V3f( 0, 0, -m_arcRadius ) );
				previousSolidArc = solidArc(
					std::min( -m_arcRadius + arcWidth * 1.5f, 0.f ),
					std::min( -m_arcRadius + arcWidth, 0.f ),
					previousFraction - currentFraction,
					-currentFraction,
					previousColor
				);
				currentSolidArc = solidArc(
					std::min( -m_arcRadius, 0.f ),
					std::min( -m_arcRadius + arcWidth, 0.f ),
					0,
					-currentFraction,
					currentColor
				);

				IECoreGL::GroupPtr solidAngleGroup = new IECoreGL::Group;
				solidAngleGroup->getState()->add(
					new IECoreGL::ShaderStateComponent(
						ShaderLoader::defaultShaderLoader(),
						TextureLoader::defaultTextureLoader(),
						"",  // vertexSource
						"",  // geometrySource
						translucentConstantFragSource(),
						new CompoundObject
					)
				);

				if( currentSolidArc )
				{
					ToGLMeshConverterPtr meshConverter = new ToGLMeshConverter( currentSolidArc );
					solidAngleGroup->addChild( runTimeCast<IECoreGL::Renderable>( meshConverter->convert() ) );
				}
				if( previousSolidArc )
				{
					ToGLMeshConverterPtr meshConverter = new ToGLMeshConverter( previousSolidArc );
					solidAngleGroup->addChild( runTimeCast<IECoreGL::Renderable>( meshConverter->convert() ) );
				}

				rootGroup->addChild( solidAngleGroup );
			}

			rootGroup->setTransform( handleTransform );
		}

		std::vector<const Inspector::Result *> handleValueInspections()
		{
			std::vector<const Inspector::Result *> result;
			for( const auto &i : inspections() )
			{
				for( const auto &p: i )
				{
					if( p.first == ( m_handleType == HandleType::Cone ? g_coneAngleParameter : g_penumbraAngleParameter ) )
					{
						result.push_back( p.second.get() );
					}
				}
			}

			return result;
		}

		std::string tipPlugSuffix() const override
		{
			return m_handleType == HandleType::Cone ? "cone angles" : "penumbra angles";
		}

		void handlePathChanged() override
		{
			ConstCompoundObjectPtr attributes = scene()->fullAttributes( handlePath() );

			float defaultVisualiserScale = 1.f;
			if( auto p = view()->descendant<const FloatPlug>( "drawingMode.visualiser.scale" ) )
			{
				defaultVisualiserScale = p->getValue();
			}
			auto visualiserScaleData = attributes->member<FloatData>( g_lightVisualiserScaleAttributeName );
			m_visualiserScale = visualiserScaleData ? visualiserScaleData->readable() : defaultVisualiserScale;

			float defaultFrustumScale = 1.f;
			if( auto p = view()->descendant<const FloatPlug>( "drawingMode.light.frustumScale" ) )
			{
				defaultFrustumScale = p->getValue();
			}
			auto frustumScaleData = attributes->member<FloatData>( g_frustumScaleAttributeName );
			m_frustumScale = frustumScaleData ? frustumScaleData->readable() : defaultFrustumScale;

			/// \todo This can be simplified and some of the logic, especially getting the inspectors, can
			/// be moved to the constructor when we standardize on a single USDLux light representation.

			for( const auto &[attributeName, value] : attributes->members() )
			{
				if(
					StringAlgo::matchMultiple( attributeName, g_lightAttributePattern ) &&
					value->typeId() == (IECore::TypeId)ShaderNetworkTypeId
				)
				{
					const auto shader = attributes->member<ShaderNetwork>( attributeName )->outputShader();
					std::string shaderAttribute = shader->getType() + ":" + shader->getName();

					if( !isLightType( shaderAttribute ) )
					{
						continue;
					}

					auto penumbraTypeData = Metadata::value<StringData>( shaderAttribute, "penumbraType" );
					m_penumbraType = penumbraTypeData ? std::optional<InternedString>( InternedString( penumbraTypeData->readable() ) ) : std::nullopt;

					m_lensRadius = 0;
					if( auto lensRadiusParameterName = Metadata::value<StringData>( shaderAttribute, "lensRadiusParameter" ) )
					{
						if( auto lensRadiusData = shader->parametersData()->member<FloatData>( lensRadiusParameterName->readable() ) )
						{
							m_lensRadius = lensRadiusData->readable();
						}
					}

					auto angleType = Metadata::value<StringData>( shaderAttribute, "coneAngleType" );
					if( angleType && angleType->readable() == "half" )
					{
						m_angleMultiplier = 2.f;
					}
					else
					{
						m_angleMultiplier = 1.f;
					}

					break;
				}
			}
		}

		bool handleDragMoveInternal( const GafferUI::DragDropEvent &event ) override
		{
			float newHandleAngle = 0;
			if( getLookThroughLight() )
			{
				// When looking through a light, the viewport field of view changes
				// with the cone angle. When dragging, taking just the `event` coordinates
				// causes a feedback loop where the `event` coordinates as a fraction of
				// the viewport cause the viewport to get smaller / larger, which causes the fraction
				// to get smaller / larger, quickly going to zero / 180.
				// We can avoid the feedback loop by using raster coordinates, which unproject
				// the local coordinates to a fixed frame of reference (the screen).
				const Line3f dragLine( event.line.p0, event.line.p1 );

				newHandleAngle = radiansToDegrees(
					atan2( rasterDragDistance( dragLine ) + m_rasterXOffset, m_rasterZPosition )
				);
			}
			else if( m_drag.value().isLinearDrag() )
			{
				// Intersect the gadget-local `event` line with the sphere centered at the gadget
				// origin with radius equal to the distance along the handle where the user clicked.
				// `Imath::Sphere3::intersect()` returns the closest (if any) intersection, but we
				// want the intersection closest to the handle line, so we do the calculation here.

				const Line3f eventLine( event.line.p0, event.line.p1 );

				const auto &[coneHandleAngle, penumbraHandleAngle] = handleAngles();
				const float angle = m_handleType == HandleType::Cone ? coneHandleAngle : penumbraHandleAngle.value();

				if( !sphereSpokeClickAngle( eventLine, m_arcRadius, angle, newHandleAngle ) )
				{
					return true;
				}
			}
			else
			{
				// All other drags can use the `AngularDrag` directly.
				newHandleAngle = radiansToDegrees( m_drag.value().updatedRotation( event ) );
			}

			// Clamp the handle being dragged, then calculate the angle delta.

			Inspector::ResultPtr coneDragStartInspection = dragStartInspection( g_coneAngleParameter );
			Inspector::ResultPtr penumbraDragStartInspection = dragStartInspection( g_penumbraAngleParameter );

			const float clampedPlugAngle = clampPlugAngle(
				m_handleType == HandleType::Cone ? conePlugAngle( newHandleAngle ) : penumbraPlugAngle( newHandleAngle ),
				coneDragStartInspection->typedValue<float>( 0.f ),
				penumbraDragStartInspection ? penumbraDragStartInspection->typedValue<float>( 0.f ) : 0.f
			);
			const float angleDelta =
				clampedPlugAngle -
				(
					m_handleType == HandleType::Cone ?
					coneDragStartInspection->typedValue<float>( 0.f ) :
					penumbraDragStartInspection->typedValue<float>( 0.f )
				)
			;

			for( const auto &i : inspections() )
			{
				auto coneIt = i.find( g_coneAngleParameter );
				if( coneIt == i.end() )
				{
					continue;
				}

				auto penumbraIt = i.find( g_penumbraAngleParameter );
				if( penumbraIt == i.end() && m_handleType == HandleType::Penumbra )
				{
					continue;
				}

				float penumbraHandleAngle = 0;
				if( penumbraIt != i.end() )
				{
					penumbraHandleAngle = penumbraIt->second->typedValue<float>( 0.f );
				}

				auto it = m_handleType == HandleType::Cone ? coneIt : penumbraIt;

				ValuePlugPtr plug = it->second->acquireEdit();
				auto floatPlug = runTimeCast<FloatPlug>( activeValuePlug( plug.get() ) );
				if( !floatPlug )
				{
					throw Exception(
						fmt::format(
							"Invalid type for \"{}\"",
							m_handleType == HandleType::Cone ? g_coneAngleParameter.string() : g_penumbraAngleParameter.string()
						)
					);
				}

				// Clamp each individual cone angle as well
				setValueOrAddKey(
					floatPlug,
					view()->getContext()->getTime(),
					clampPlugAngle(
						it->second->typedValue<float>( 0.f ) + angleDelta,
						coneIt->second->typedValue<float>( 0.f ),
						penumbraHandleAngle
					)
				);

			}

			return true;
		}

		bool handleDragEndInternal() override
		{
			m_drag = std::nullopt;

			return false;
		}

		void updateLocalTransformInternal( const V3f &, const V3f & ) override
		{
			M44f transform;
			if( m_handleType == HandleType::Penumbra && ( !m_penumbraType || m_penumbraType == g_insetPenumbraType ) )
			{
				// Rotate 180 on the Z-axis to make positive rotations inset
				transform *= M44f().rotate( V3f( 0, 0, M_PI ) );
			}

			if( m_handleType == HandleType::Penumbra )
			{
				// For inset and outset penumbras, transform the handle so the -Z axis
				// points along the cone line, making all angles relative to the cone angle.
				const auto &[coneHandleAngle, penumbraHandleAngle] = handleAngles();
				if( !m_penumbraType || m_penumbraType == g_insetPenumbraType || m_penumbraType == g_outsetPenumbraType )
				{
					transform *= M44f().rotate( V3f( 0, degreesToRadians( coneHandleAngle ), 0 ) );
				}
			}

			transform *= M44f().translate( V3f( -m_lensRadius, 0, 0 ) );
			transform *= M44f().rotate( V3f( 0, 0, degreesToRadians( m_zRotation ) ) );

			setTransform( transform );
		}

		bool visibleInternal() const override
		{
			const Inspector *coneInspector = inspector( g_coneAngleParameter );
			const Inspector *penumbraInspector = inspector( g_penumbraAngleParameter );
			if( !coneInspector || ( m_handleType == HandleType::Penumbra && !penumbraInspector ) )
			{
				return false;
			}

			// We can be called to check visibility for any scene location set in the current context, spot light
			// or otherwise. If there isn't an inspection, this handle should be hidden (likely because the scene
			// location is not a spot light).

			Inspector::ResultPtr contextConeInspection = coneInspector->inspect();
			Inspector::ResultPtr contextPenumbraInspection = penumbraInspector ? penumbraInspector->inspect() : nullptr;

			if( !contextConeInspection || ( m_handleType == HandleType::Penumbra && !contextPenumbraInspection ) )
			{
				return false;
			}

			// We are a spot light, but the penumbra will be hidden if it's too close to the cone angle, for
			// the location we're attaching the handles to.

			/// \todo This checks the penumbra / cone angles only for the last selected location, causing
			/// repeated checks of the same location when `visible()` is called in a loop over multiple scene
			/// locations. We rely on history caching to make this relatively fast, but ideally this could be
			/// tested only once per selection list.

			const auto &[coneAngle, penumbraAngle] = handleAngles();
			if( m_handleType == HandleType::Penumbra && penumbraAngle )
			{
				const float radius = m_visualiserScale * m_frustumScale * -10.f;
				const V2f coneRaster = view()->viewportGadget()->gadgetToRasterSpace(
					V3f( 0, 0, radius ),
					this
				);
				const M44f rot = M44f().rotate( V3f( 0, degreesToRadians( penumbraAngle.value() ), 0 ) );
				const V2f penumbraRaster = view()->viewportGadget()->gadgetToRasterSpace(
					V3f( 0, 0, radius ) * rot,
					this
				);

				if( ( coneRaster - penumbraRaster ).length() < ( 2.f * g_circleHandleWidthLarge ) )
				{
					return false;
				}
			}

			return true;
		}

		void setupDrag( const DragDropEvent &event ) override
		{
			m_drag = AngularDrag(
				this,
				V3f( 0, 0, 0 ),
				V3f( 0, 1.f, 0 ),
				V3f( 0, 0, -1.f ),
				event
			);

			if( getLookThroughLight() )
			{
				const auto &[ coneHandleAngle, penumbraHandleAngle] = handleAngles();

				const float dragStartAngle = m_handleType == HandleType::Cone ? coneHandleAngle : penumbraHandleAngle.value();

				const Line3f clickLine( event.line.p0, event.line.p1 );
				const Line3f originLine( V3f( 0 ), V3f( 0, 0, -1.f ) );
				const Line3f handleLine(
					V3f( 0 ),
					V3f( 0, 0, -1.f ) * M44f().rotate( V3f( 0, degreesToRadians( dragStartAngle ), 0 ) )
				);

				const float clickRaster = rasterDragDistance( clickLine );
				const float originRaster = rasterDragDistance( originLine );
				const float handleRaster = rasterDragDistance( handleLine );

				const float delta = handleRaster - originRaster;

				m_rasterXOffset = delta - clickRaster;
				m_rasterZPosition = abs( delta ) / tan( degreesToRadians( dragStartAngle ) );
			}
		}

		std::vector<const Inspector::Result *> handleValueInspections() const override
		{
			std::vector<const Inspector::Result *> result;
			for( const auto &i : inspections() )
			{
				for( const auto &p : i )
				{
					if( m_handleType == HandleType::Cone && p.first == g_coneAngleParameter )
					{
						result.push_back( p.second.get() );
					}
					else if( m_handleType == HandleType::Penumbra && p.first == g_penumbraAngleParameter )
					{
						result.push_back( p.second.get() );
					}
				}
			}
			return result;
		}

		void updateTooltipPosition( const LineSegment3f &eventLine ) override
		{
			if( !hasInspectors() )
			{
				return;
			}

			const auto &[coneHandleAngle, penumbraHandleAngle] = handleAngles();

			const float angle = m_handleType == HandleType::Cone ? coneHandleAngle : penumbraHandleAngle.value();

			const M44f r = M44f().rotate( V3f( 0, degreesToRadians( angle ), 0 ) );

			if( getLookThroughLight() )
			{
				setTooltipPosition( V3f( 0, 0, -1.f ) * r );
				return;
			}

			if( m_drag )
			{
				setTooltipPosition( V3f( 0, 0, -m_arcRadius ) * r );
				return;
			}

			const Line3f rayLine(
				V3f( 0 ),
				V3f( 0, 0, m_visualiserScale * m_frustumScale * -10.f ) * r
			);
			const V3f dragPoint = rayLine.closestPointTo( Line3f( eventLine.p0, eventLine.p1 ) );

			setTooltipPosition( dragPoint );

			if( !m_drag )
			{
				m_arcRadius = dragPoint.length();
			}
		}

	private :

		std::pair<float, std::optional<float>> handleAngles() const
		{
			Inspector::ResultPtr coneHandleInspection = handleInspection( g_coneAngleParameter );
			Inspector::ResultPtr penumbraHandleInspection = handleInspection( g_penumbraAngleParameter );

			return {
				coneHandleAngle( coneHandleInspection->typedValue<float>( 0.f ) ),
				penumbraHandleInspection ? std::optional<float>( penumbraHandleAngle( penumbraHandleInspection->typedValue<float>( 0.f ) ) ) : std::nullopt
			};
		}

		// Convert from the angle representation used by plugs to that used by handles.
		float coneHandleAngle( const float angle ) const
		{
			return angle * 0.5f;
		}

		float penumbraHandleAngle( const float angle ) const
		{
			if( m_penumbraType != g_absolutePenumbraType )
			{
				return angle;
			}
			return angle * 0.5f;
		}

		float conePlugAngle(const float a ) const
		{
			return a * 2.f / m_angleMultiplier;
		}

		float penumbraPlugAngle(const float a ) const
		{
			return ( m_penumbraType != g_absolutePenumbraType ? a : a * 2.f );
		}

		// Find the intersection of a line in gadget space with a unit sphere and
		// project that intersection to the handle's plane in raster space. Return
		// the projected point's distance from the raster center.
		float rasterDragDistance( const Line3f &ray )
		{
			V3f sphereIntersection;
			Sphere3f( V3f( 0 ), 1.f ).intersect( ray, sphereIntersection );

			const V2f gadgetRasterOrigin = view()->viewportGadget()->gadgetToRasterSpace( V3f( 0, 0, -1.f ), this );
			const V2f rasterSphereIntersection = view()->viewportGadget()->gadgetToRasterSpace( sphereIntersection, this );
			const V2f rasterNormal = ( view()->viewportGadget()->gadgetToRasterSpace( V3f( 0, 1.f, -1.f ), this ) - gadgetRasterOrigin ).normalized();

			const V2f projectedPoint = rasterSphereIntersection - (rasterSphereIntersection - gadgetRasterOrigin).dot( rasterNormal ) * rasterNormal;

			const V2f rasterDistance = gadgetRasterOrigin - projectedPoint;

			// Flip the signs to account for the viewport origin, ensuring the returned value
			// is positive. We could take the absolute value, but that would cause drags to mirror
			// about the raster center. Instead we want to clamp at zero.
			if( abs( rasterDistance.x ) > abs( rasterDistance.y ) )
			{
				return rasterNormal.y < 0 ? rasterDistance.x : -rasterDistance.x;
			}
			return rasterNormal.x > 0 ? rasterDistance.y : -rasterDistance.y;
		}

		float clampPlugAngle(
			const float angle,
			const float originalConeAngle,
			const std::optional<float> originalPenumbraAngle
		)
		{
			float result = std::clamp( angle, 0.f, 180.f );
			if( m_handleType == HandleType::Cone )
			{
				if( originalPenumbraAngle && ( !m_penumbraType || m_penumbraType == g_insetPenumbraType ) )
				{
					result = std::max( result, originalPenumbraAngle.value() * 2.f );
				}
				else if( m_penumbraType == g_outsetPenumbraType )
				{
					result = std::min( result, 180.f - originalPenumbraAngle.value() * 2.f );
				}
			}

			else
			{
				if( !m_penumbraType || m_penumbraType == g_insetPenumbraType )
				{
					result = std::min( result, originalConeAngle * 0.5f );
				}
				else if( m_penumbraType == g_outsetPenumbraType )
				{
					result = std::min( result, ( 180.f - originalConeAngle ) * 0.5f );
				}
			}
			return result;
		}

		const float m_zRotation;

		std::optional<AngularDrag> m_drag;

		HandleType m_handleType;
		std::optional<InternedString> m_penumbraType;

		float m_angleMultiplier;

		float m_visualiserScale;
		float m_frustumScale;
		float m_lensRadius;

		// The reference coordinates of the start of a drag
		// when looking through a light. `x` is the x distance, in raster
		// space, on the plane of the gadget. `y` is the depth, into the
		// screen, calculated as if it was in raster space.
		V2f m_lookThroughRasterReference;
		float m_rasterXOffset;
		float m_rasterZPosition;
		float m_arcRadius;
};

class EdgeHandle : public LightToolHandle
{
	public :
		enum class LightAxis
		{
			Width = 1,
			Height = 2
		};

		EdgeHandle(
			const std::string &lightType,
			SceneView *view,
			const InternedString &edgeParameter,
			const V3f &edgeAxis,
			const float edgeToHandleRatio,
			const InternedString &oppositeParameter,
			const V3f &oppositeAxis,
			const float oppositeToHandleRatio,
			const InternedString &oppositeScaleAttributeName,
			const float edgeMargin,
			const std::string &tipPlugSuffix,
			const std::string &name
		) :
			LightToolHandle( lightType, view, {edgeParameter, oppositeParameter}, name ),
			m_edgeParameter( edgeParameter ),
			m_edgeAxis( edgeAxis ),
			m_edgeToHandleRatio( edgeToHandleRatio ),
			m_oppositeParameter( oppositeParameter ),
			m_oppositeAxis( oppositeAxis ),
			m_oppositeToHandleRatio( oppositeToHandleRatio ),
			m_oppositeScaleAttributeName( oppositeScaleAttributeName ),
			m_edgeMargin( edgeMargin ),
			m_tipPlugSuffix( tipPlugSuffix ),
			m_edgeScale( 1.f ),
			m_oppositeScale( 1.f ),
			m_orientation(),
			m_oppositeAdditionalScale( 1.f )
		{
		}

		~EdgeHandle() override
		{

		}

	protected :

		void handlePathChanged() override
		{
			/// \todo This can be simplified and some of the logic, especially getting the inspectors, can
			/// be moved to the constructor when we standardize on a single USDLux light representation.

			ConstCompoundObjectPtr attributes = scene()->fullAttributes( handlePath() );

			for( const auto &[attributeName, value] : attributes->members() )
			{
				if(
					StringAlgo::matchMultiple( attributeName, g_lightAttributePattern ) &&
					value->typeId() == (IECore::TypeId)ShaderNetworkTypeId
				)
				{
					const auto shader = attributes->member<ShaderNetwork>( attributeName )->outputShader();
					std::string shaderAttribute = shader->getType() + ":" + shader->getName();

					if( !isLightType( shaderAttribute ) )
					{
						continue;
					}

					m_orientation = M44f();
					if( auto orientationData = Metadata::value<M44fData>( shaderAttribute, "visualiserOrientation" ) )
					{
						m_orientation = orientationData->readable();
					}

					m_oppositeAdditionalScale = 1.f;
					if( auto scaleData = Metadata::value<FloatData>( shaderAttribute, m_oppositeScaleAttributeName ) )
					{
						m_oppositeAdditionalScale = scaleData->readable();
					}

					break;
				}
			}
		}

		bool handleDragMoveInternal( const GafferUI::DragDropEvent &event ) override
		{
			Inspector::ResultPtr edgeInspection = dragStartInspection( m_edgeParameter );
			if( !edgeInspection )
			{
				return true;
			}

			const float nonZeroValue = edgeInspection->typedValue<float>( 0.f ) == 0 ? 1.f : edgeInspection->typedValue<float>( 0.f );
			const float newValue = m_drag.value().updatedPosition( event ) - m_drag.value().startPosition();

			float mult = std::max( ( newValue * m_edgeToHandleRatio ) / ( nonZeroValue * m_edgeScale ) + 1.f, 0.f );

			applyMultiplier( m_edgeParameter, mult );

			return true;
		}

		void updateLocalTransformInternal( const V3f &scale, const V3f & ) override
		{
			m_edgeScale = abs( scale.dot( m_edgeAxis * m_orientation ) );
			m_oppositeScale = abs( scale.dot( m_oppositeAxis * m_orientation ) ) * m_oppositeAdditionalScale;
		}

		bool handleDragEndInternal() override
		{
			m_drag = std::nullopt;
			return false;
		}

		void addHandleVisualisation( IECoreGL::Group *rootGroup, const bool selectionPass, const bool highlighted ) const override
		{
			if( getLookThroughLight() )
			{
				return;
			}

			Inspector::ResultPtr edgeInspection = handleInspection( m_edgeParameter );
			if( !edgeInspection )
			{
				return;
			}

			float spokeRadius = 0;
			float coneSize = 0;

			if( selectionPass )
			{
				spokeRadius = g_lineSelectionWidth;
				coneSize = g_arrowHandleSelectionSize;
			}
			else
			{
				spokeRadius = highlighted ? g_lineHandleWidthLarge : g_lineHandleWidth;
				coneSize = highlighted ? g_arrowHandleSizeLarge : g_arrowHandleSize;
			}

			LineSegment3f edgeSegment = this->edgeSegment(
				edgeInspection->typedValue<float>( 0.f ),
				oppositeInspectionValue()
			);

			M44f edgeTransform;
			this->edgeTransform( edgeInspection->typedValue<float>( 0.f ), edgeSegment, edgeTransform );
			M44f coneTransform;
			this->coneTransform( edgeInspection->typedValue<float>( 0.f ), coneTransform );

			IECoreGL::GroupPtr coneGroup = new IECoreGL::Group;
			coneGroup->setTransform( M44f().scale( V3f( coneSize ) ) * coneTransform );
			coneGroup->addChild( unitCone() );
			rootGroup->addChild( coneGroup );

			IECoreGL::GroupPtr edgeGroup = new IECoreGL::Group;
			edgeGroup->addChild(
				cone(
					edgeSegment.length(),
					spokeRadius * ::rasterScaleFactor( this, edgeSegment.p0 ),
					spokeRadius * ::rasterScaleFactor( this, edgeSegment.p1 )
				)
			);
			edgeGroup->setTransform( edgeTransform );

			rootGroup->addChild( edgeGroup );
			rootGroup->setTransform( m_orientation );
		}

		void setupDrag( const DragDropEvent &event ) override
		{
			m_drag = LinearDrag( this, LineSegment3f( V3f( 0 ), m_edgeAxis * m_orientation ), event );
		}

		std::vector<const Inspector::Result *> handleValueInspections() const override
		{
			std::vector<const Inspector::Result *> result;
			for( const auto &i : inspections() )
			{
				for( const auto &p: i )
				{
					if( p.first == m_edgeParameter )
					{
						result.push_back( p.second.get() );
					}
				}
			}

			return result;
		}

		std::string tipPlugSuffix() const override
		{
			return m_tipPlugSuffix;
		}

		std::string tipInfoSuffix() const override
		{
			return "";
		}

		void updateTooltipPosition( const LineSegment3f &eventLine ) override
		{
			if( !hasInspectors() )
			{
				return;
			}

			Inspector::ResultPtr edgeInspection = handleInspection( m_edgeParameter );
			if( !edgeInspection )
			{
				return;
			}

			LineSegment3f edgeSegment = this->edgeSegment( edgeInspection->typedValue<float>( 0.f ), oppositeInspectionValue() );
			V3f offset = edgeToGadgetSpace( edgeInspection->typedValue<float>( 0.f ) );
			edgeSegment.p0 += offset;
			edgeSegment.p1 += offset;
			edgeSegment *= m_orientation;

			V3f eventClosest;
			setTooltipPosition( edgeSegment.closestPoints( LineSegment3f( eventLine.p0, eventLine.p1 ), eventClosest ) );
		}

	private :

		float oppositeInspectionValue() const
		{
			Inspector::ResultPtr oppositeInspection = handleInspection( m_oppositeParameter );
			return oppositeInspection ? oppositeInspection->typedValue<float>( 0.f ) : 1.f;
		}

		V3f edgeToGadgetSpace( const float edge ) const
		{
			return ( ( m_edgeAxis * edge * m_edgeScale ) / m_edgeToHandleRatio );
		}

		LineSegment3f edgeSegment( const float edgeLength, const float oppositeLength ) const
		{
			float fullEdgeLength = 0;
			float fullEdgeLengthHalf = 0;
			float radius0 = 0;
			float radius1 = 0;

			fullEdgeLength = oppositeLength * m_oppositeScale;
			fullEdgeLengthHalf = fullEdgeLength * 0.5f;

			radius0 = m_edgeMargin * ::rasterScaleFactor( this, -fullEdgeLengthHalf * m_oppositeAxis );
			radius1 = m_edgeMargin * ::rasterScaleFactor( this, fullEdgeLengthHalf * m_oppositeAxis );

			LineSegment3f result;

			result.p0 = std::min( 0.f, -fullEdgeLengthHalf + radius0 ) * m_oppositeAxis;
			result.p1 = std::max( 0.f, fullEdgeLengthHalf - radius1  ) * m_oppositeAxis;

			return result;
		}

		void edgeTransform( const float edgeLength, const LineSegment3f &edgeSegment, M44f &edgeTransform ) const
		{
			edgeTransform =
				rotationMatrix( V3f( 0, 0, 1.f ), m_oppositeAxis ) *
				M44f().translate(
					edgeSegment.p0 * m_oppositeAxis + edgeToGadgetSpace( edgeLength )
				)
			;
		}

		void coneTransform( const float edgeLength, M44f &coneTransform ) const
		{
			const V3f gadgetSpaceEdge = edgeToGadgetSpace( edgeLength );
			// Rotate the cone 90 degrees around the axis that is the width axis rotated 90 degrees around the z axis.
			coneTransform =
				rotationMatrix( V3f( 0, 0, 1.f ), m_edgeAxis ) *
				M44f().scale( V3f( ::rasterScaleFactor( this, gadgetSpaceEdge ) ) ) *
				M44f().translate( gadgetSpaceEdge )
			;
		}

		const InternedString m_edgeParameter;
		const V3f m_edgeAxis;
		const float m_edgeToHandleRatio;
		const InternedString m_oppositeParameter;
		const V3f m_oppositeAxis;
		const float m_oppositeToHandleRatio;
		const InternedString m_oppositeScaleAttributeName;
		const float m_edgeMargin;
		const std::string m_tipPlugSuffix;

		float m_edgeScale;
		float m_oppositeScale;
		M44f m_orientation;
		float m_oppositeAdditionalScale;
		std::optional<LinearDrag> m_drag;
};

class CornerHandle : public LightToolHandle
{
	public :

		CornerHandle(
			const std::string &lightType,
			SceneView *view,
			const InternedString &widthParameter,
			const V3f &widthAxis,
			const float widthToHandleRatio,
			const InternedString &heightParameter,
			const V3f &heightAxis,
			const float heightToHandleRatio,
			const std::string &name
		) :
			LightToolHandle( lightType, view, {widthParameter, heightParameter}, name ),
			m_widthParameter( widthParameter ),
			m_widthAxis( widthAxis ),
			m_widthToHandleRatio( widthToHandleRatio ),
			m_heightParameter( heightParameter ),
			m_heightAxis( heightAxis ),
			m_heightToHandleRatio( heightToHandleRatio ),
			m_scale( V2f( 1.f ) ),
			m_drag()
		{
		}

		~CornerHandle() override
		{

		}

	protected :

		bool handleDragMoveInternal( const GafferUI::DragDropEvent &event ) override
		{
			if( !m_drag )
			{
				return true;
			}

			Inspector::ResultPtr widthInspection = dragStartInspection( m_widthParameter );
			Inspector::ResultPtr heightInspection = dragStartInspection( m_heightParameter );
			if( !widthInspection || !heightInspection )
			{
				return true;
			}

			const float nonZeroWidth = widthInspection->typedValue<float>( 0.f ) == 0 ? 1.f : widthInspection->typedValue<float>( 0.f );
			const float nonZeroHeight = heightInspection->typedValue<float>( 0.f ) == 0 ? 1.f : heightInspection->typedValue<float>( 0.f );

			const V2f newPosition = m_drag.value().updatedPosition( event ) - m_drag.value().startPosition();

			float xMult = ( newPosition.x * m_widthToHandleRatio ) / ( nonZeroWidth * m_scale.x ) + 1.f;
			float yMult = ( newPosition.y * m_heightToHandleRatio ) / ( nonZeroHeight * m_scale.y ) + 1.f;

			if( event.modifiers == g_quadLightConstrainAspectRatioKey )
			{
				if( widthInspection->typedValue<float>( 0.f ) > heightInspection->typedValue<float>( 0.f ) )
				{
					yMult = xMult;
				}
				else{
					xMult = yMult;
				}
			}

			xMult = std::max( xMult, 0.f );
			yMult = std::max( yMult, 0.f );

			applyMultiplier( m_widthParameter, xMult );
			applyMultiplier( m_heightParameter, yMult );

			return true;
		}

		void updateLocalTransformInternal( const V3f &scale, const V3f & ) override
		{
			m_scale = V2f( scale.x, scale.y );
		}

		bool handleDragEndInternal() override
		{
			m_drag = std::nullopt;
			return false;
		}

		void addHandleVisualisation( IECoreGL::Group *rootGroup, const bool selectionPass, const bool highlighted ) const override
		{
			if( getLookThroughLight() )
			{
				return;
			}

			Inspector::ResultPtr widthInspection = handleInspection( m_widthParameter );
			Inspector::ResultPtr heightInspection = handleInspection( m_heightParameter );
			if( !widthInspection || !heightInspection )
			{
				return;
			}

			float cornerRadius = 0;

			if( selectionPass )
			{
				cornerRadius = g_circleHandleSelectionWidth;
			}
			else
			{
				cornerRadius = highlighted ? g_circleHandleWidthLarge : g_circleHandleWidth;
			}

			IECoreGL::GroupPtr iconGroup = new IECoreGL::Group;
			iconGroup->getState()->add(
				new IECoreGL::ShaderStateComponent(
					ShaderLoader::defaultShaderLoader(),
					TextureLoader::defaultTextureLoader(),
					faceCameraVertexSource(),
					"",
					constantFragSource(),
					new CompoundObject
				)
			);

			const V3f widthOffset = ( ( m_widthAxis * widthInspection->typedValue<float>( 0.f ) * m_scale.x ) / m_widthToHandleRatio );
			const V3f heightOffset = (( m_heightAxis * heightInspection->typedValue<float>( 0.f ) * m_scale.y ) / m_heightToHandleRatio );

			iconGroup->setTransform(
				M44f().scale( V3f( cornerRadius ) * ::rasterScaleFactor( this, V3f( 0 ) ) ) *
				M44f().translate( widthOffset + heightOffset )
			);
			iconGroup->addChild( circle() );

			rootGroup->addChild( iconGroup );
		}

		void setupDrag( const DragDropEvent &event ) override
		{
			m_drag = PlanarDrag( this, V3f( 0 ), m_widthAxis, m_heightAxis, event, true );
		}

		std::vector<const Inspector::Result *> handleValueInspections() const override
		{
			std::vector<const Inspector::Result *> result;
			for( const auto &i : inspections() )
			{
				for( const auto &p: i )
				{
					result.push_back( p.second.get() );
				}
			}

			return result;
		}

		std::string tipPlugSuffix() const override
		{
			return "plugs";
		}

		std::string tipInfoSuffix() const override
		{
			return "Hold Ctrl to maintain aspect ratio";
		}

		void updateTooltipPosition( const LineSegment3f &eventLine ) override
		{
			if( !hasInspectors() )
			{
				return;
			}

			Inspector::ResultPtr widthInspection = handleInspection( m_widthParameter );
			Inspector::ResultPtr heightInspection = handleInspection( m_heightParameter );
			if( !widthInspection || !heightInspection )
			{
				return;
			}

			setTooltipPosition( edgeTooltipPosition( widthInspection->typedValue<float>( 0.f ), heightInspection->typedValue<float>( 0.f ) ) );
		}

	private :

		V3f edgeTooltipPosition( const float width, const float height ) const
		{
			return ( width * 0.5f * m_widthAxis * m_scale.x ) + ( height * 0.5f * m_heightAxis * m_scale.y );
		}

		const InternedString m_widthParameter;
		const V3f m_widthAxis;
		const float m_widthToHandleRatio;
		const InternedString m_heightParameter;
		const V3f m_heightAxis;
		const float m_heightToHandleRatio;
		V2f m_scale;
		std::optional<PlanarDrag> m_drag;
};

class RadiusHandle : public LightToolHandle
{
	public :
		RadiusHandle(
			const std::string &lightType,
			SceneView *view,
			const InternedString &radiusParameter,
			const float radiusToHandleRatio,
			const bool faceCamera,
			const bool useScale,
			const std::string &name
		) :
			LightToolHandle( lightType, view, {radiusParameter}, name ),
			m_radiusParameter( radiusParameter ),
			m_radiusToHandleRatio( radiusToHandleRatio ),
			m_faceCamera( faceCamera ),
			m_useScale( useScale ),
			m_dragDirection()
		{
		}

	protected :
		bool handleDragMoveInternal( const GafferUI::DragDropEvent &event ) override
		{
			if( !m_drag )
			{
				return true;
			}

			if( !dragStartInspection( m_radiusParameter ) )
			{
				return true;
			}

			const float increment =
				(
					( m_drag.value().updatedPosition( event ) ) -
					( m_drag.value().startPosition() )
				) * m_radiusToHandleRatio
			;

			applyIncrement( m_radiusParameter, increment, 0, std::numeric_limits<float>::max() );

			return true;
		}

		void updateLocalTransformInternal( const V3f &scale, const V3f & ) override
		{
			if( m_useScale )
			{
				setTransform( M44f().scale( scale ) );
			}
		}

		bool handleDragEndInternal() override
		{
			m_drag = std::nullopt;
			return false;
		}

		void addHandleVisualisation( IECoreGL::Group *rootGroup, const bool selectionPass, const bool highlighted ) const override
		{
			if( getLookThroughLight() )
			{
				return;
			}

			Inspector::ResultPtr radiusInspection = handleInspection( m_radiusParameter );
			if( !radiusInspection )
			{
				return;
			}

			float thickness = 0.f;
			float iconRadius = 0.f;

			if( selectionPass )
			{
				thickness = g_lineSelectionWidth;
				iconRadius = g_circleHandleSelectionWidth;
			}
			else
			{
				thickness = highlighted ? g_lineHandleWidthLarge : g_lineHandleWidth;
				iconRadius = highlighted ? g_circleHandleWidthLarge : g_circleHandleWidth;
			}

			const float radius = radiusInspection->typedValue<float>( 0.f ) / m_radiusToHandleRatio;

			IECoreGL::GroupPtr torusGroup = new IECoreGL::Group;
			if( m_faceCamera )
			{
				torusGroup->getState()->add(
					new IECoreGL::ShaderStateComponent(
						ShaderLoader::defaultShaderLoader(),
						TextureLoader::defaultTextureLoader(),
						faceCameraVertexSource(),
						"",
						constantFragSource(),
						new CompoundObject
					)
				);
			}

			V3f scale;
			extractScaling( getTransform(), scale );
			torusGroup->addChild(
				torus(
					radius * scale.x,
					radius * scale.y,
					thickness,
					this,
					m_faceCamera ? Axis::X : Axis::Z
				)
			);
			rootGroup->addChild( torusGroup );

			IECoreGL::GroupPtr iconGroup = new IECoreGL::Group;
			iconGroup->getState()->add(
				new IECoreGL::ShaderStateComponent(
					ShaderLoader::defaultShaderLoader(),
					TextureLoader::defaultTextureLoader(),
					faceCameraVertexSource(),
					"",
					constantFragSource(),
					new CompoundObject
				)
			);

			const float xOffset = radius * scale.x;

			const V3f iconScale = V3f( iconRadius ) * ::rasterScaleFactor( this, V3f( xOffset, 0, 0 ) );
			M44f transform = M44f().scale( iconScale );
			if( !m_faceCamera )
			{
				// If the entire handle is not facing the camera, offset the icon in
				// gadget space so the center of the rotation is the center of the circle icon.
				// Otherwise we bake in the offset below into the circle geometry so the center
				// of "facing" rotation is the center of the handle.
				transform *= M44f().translate( V3f( xOffset, 0, 0 ) );
			}
			iconGroup->setTransform( transform );
			iconGroup->addChild( circle( Axis::X, m_faceCamera ? ( V3f( 0, 0, xOffset ) / iconScale ) : V3f( 0 ) ) );

			rootGroup->addChild( iconGroup );
			rootGroup->setTransform( M44f().scale( V3f( 1.f / scale.x, 1.f / scale.y, 1.f / scale.z ) ) );
		}

		void setupDrag( const DragDropEvent &event ) override
		{
			m_dragDirection = circlePosition( event.line ).normalized();
			m_drag = Handle::LinearDrag(
				this,
				LineSegment3f( V3f( 0 ), m_dragDirection ),
				event,
				true
			);
		}

		std::string tipPlugSuffix() const override
		{
			return "radii";
		}

		void updateTooltipPosition( const LineSegment3f &eventLine ) override
		{
			if( m_drag )
			{
				const Inspector::ResultPtr radiusInspection = handleInspection( m_radiusParameter );
				const float radius = radiusInspection->typedValue<float>( 0 );
				setTooltipPosition( ( m_dragDirection * radius ) / m_radiusToHandleRatio );
			}
			else
			{
				setTooltipPosition( circlePosition( eventLine ) );
			}
		}

	private :

		V3f circlePosition( const LineSegment3f &line ) const
		{
			if( m_faceCamera )
			{
				// Closest intersection of the line and a sphere at the origin with our radius
				Inspector::ResultPtr radiusInspection = handleInspection( m_radiusParameter );
				const float radius = radiusInspection->typedValue<float>( 0.f ) / m_radiusToHandleRatio;
				return lineSphereIntersection( line, V3f( 0 ), radius );
			}

			// If the line intersects the plane, the result is simply the intersection point
			V3f planeIntersection;
			if( line.intersect( Plane3f( V3f( 0 ), V3f( 0, 0, -1 ) ), planeIntersection ) )
			{
				return planeIntersection;
			}

			// If no line / plane intersection, project the line to the Z plane and take
			// the first intersection with the circle
			const LineSegment2f projectedLine(
				V2f( line.p0.x, line.p0.y ), V2f( line.p1.x, line.p1.y )
			);

			Inspector::ResultPtr radiusInspection = handleInspection( m_radiusParameter );
			const float radius = radiusInspection->typedValue<float>( 0.f ) / m_radiusToHandleRatio;
			const V2f intersection = lineSphereIntersection( projectedLine, V2f( 0 ), radius );

			// We don't scale here on purpose : when used for a linear drag axis, we normalize
			// the returned value, and when drawing the tooltip, the scale transform is part
			// of the gadget transform already.
			return V3f( intersection.x, intersection.y, 0 );
		}

		const InternedString m_radiusParameter;
		const float m_radiusToHandleRatio;
		const bool m_faceCamera;
		const float m_useScale;
		V3f m_dragDirection;
		std::optional<LinearDrag> m_drag;
};

class LengthHandle : public LightToolHandle
{
	public :
		LengthHandle(
			const std::string &lightType,
			SceneView *view,
			const InternedString &parameter,
			const V3f &axis,
			const float lengthToHandleRatio,
			const std::string &name
		) :
			LightToolHandle( lightType, view, {parameter}, name ),
			m_parameter( parameter ),
			m_axis( axis ),
			m_lengthToHandleRatio( lengthToHandleRatio ),
			m_orientation(),
			m_scale()
		{
		}

		~LengthHandle() override
		{

		}

	protected :
		void handlePathChanged() override
		{
			/// \todo This can be simplified and some of the logic, especially getting the inspectors, can
			/// be moved to the constructor when we standardize on a single USDLux light representation.

			ConstCompoundObjectPtr attributes = scene()->fullAttributes( handlePath() );

			for( const auto &[attributeName, value] : attributes->members() )
			{
				if(
					StringAlgo::matchMultiple( attributeName, g_lightAttributePattern ) &&
					value->typeId() == (IECore::TypeId)ShaderNetworkTypeId
				)
				{
					const auto shader = attributes->member<ShaderNetwork>( attributeName )->outputShader();
					std::string shaderAttribute = shader->getType() + ":" + shader->getName();

					if( !isLightType( shaderAttribute ) )
					{
						continue;
					}

					m_orientation = M44f();
					if( auto orientationData = Metadata::value<M44fData>( shaderAttribute, "visualiserOrientation" ) )
					{
						m_orientation = orientationData->readable();
					}

					break;
				}
			}
		}

		bool handleDragMoveInternal( const GafferUI::DragDropEvent &event ) override
		{
			if( !m_drag )
			{
				return true;
			}

			if( !dragStartInspection( m_parameter ) )
			{
				return true;
			}

			const float updatedPosition = m_drag.value().updatedPosition( event ) / m_scale;
			const float startPosition = m_drag.value().startPosition() / m_scale;
			const float increment = ( updatedPosition - startPosition ) * m_lengthToHandleRatio;

			applyIncrement( m_parameter, increment, 0, std::numeric_limits<float>::max() );

			return true;
		}

		void updateLocalTransformInternal( const V3f &scale, const V3f & ) override
		{
			m_scale = abs( m_axis.dot( scale * m_orientation ) );
		}

		bool handleDragEndInternal() override
		{
			m_drag = std::nullopt;
			return false;
		}

		void addHandleVisualisation( IECoreGL::Group *rootGroup, const bool selectionPass, const bool highlighted ) const override
		{
			if( getLookThroughLight() )
			{
				return;
			}

			Inspector::ResultPtr inspection = handleInspection( m_parameter );
			if( !inspection )
			{
				return;
			}

			float coneSize = 0.f;
			if( selectionPass )
			{
				coneSize = g_arrowHandleSelectionSize;
			}
			else
			{
				coneSize = highlighted ? g_arrowHandleSizeLarge : g_arrowHandleSize;
			}

			const V3f offset = this->offset( inspection.get() );

			IECoreGL::GroupPtr coneGroup = new IECoreGL::Group;
			coneGroup->setTransform(
				M44f().scale( V3f( coneSize ) * ::rasterScaleFactor( this, offset ) ) *
				rotationMatrix( V3f( 0, 0, 1.f ), m_axis ) *
				M44f().translate( offset ) *
				m_orientation
			);
			coneGroup->addChild( unitCone() );

			rootGroup->addChild( coneGroup );
		}

		void setupDrag( const DragDropEvent &event ) override
		{
			Inspector::ResultPtr inspection = handleInspection( m_parameter );
			V3f offset = this->offset( inspection.get() );

			m_drag = Handle::LinearDrag(
				this,
				LineSegment3f( V3f( 0 ), ( m_axis * m_orientation ) ),
				event,
				true
			);
		}

		std::string tipPlugSuffix() const override
		{
			return "lengths";
		}

		void updateTooltipPosition( const LineSegment3f &eventLine ) override
		{
			if( !hasInspectors() )
			{
				return;
			}

			Inspector::ResultPtr inspection = handleInspection( m_parameter );

			const M44f transform =
				M44f().translate( offset( inspection.get() ) ) *
				m_orientation
			;

			setTooltipPosition( V3f( 0 ) * transform );
		}

	private :

		V3f offset( Inspector::Result *inspection ) const
		{
			return ( m_axis * inspection->typedValue<float>( 0.f ) * m_scale ) / m_lengthToHandleRatio;
		}

		const InternedString m_parameter;
		const V3f m_axis;
		const float m_lengthToHandleRatio;
		M44f m_orientation;
		float m_scale;
		std::optional<LinearDrag> m_drag;
};

// ============================================================================
// HandlesGadget
// ============================================================================

class HandlesGadget : public Gadget
{

	public :

		HandlesGadget( const std::string &name="HandlesGadget" )
			:	Gadget( name )
		{
		}

	protected :

		Imath::Box3f renderBound() const override
		{
			// We need `renderLayer()` to be called any time it will
			// be called for one of our children. Our children claim
			// infinite bounds to account for their raster scale, so
			// we must too.
			Box3f b;
			b.makeInfinite();
			return b;
		}

		void renderLayer( Layer layer, const Style *, RenderReason ) const override
		{
			if( layer != Layer::MidFront )
			{
				return;
			}

			// Clear the depth buffer so that the handles render
			// over the top of the SceneGadget. Otherwise they are
			// unusable when the object is larger than the handles.
			/// \todo Can we really justify this approach? Does it
			/// play well with new Gadgets we'll add over time? If
			/// so, then we should probably move the depth clearing
			/// to `Gadget::render()`, in between each layer. If
			/// not we'll need to come up with something else, perhaps
			/// going back to punching a hole in the depth buffer using
			/// `glDepthFunc( GL_GREATER )`. Or maybe an option to
			/// render gadgets in an offscreen buffer before compositing
			/// them over the current framebuffer?
			glClearDepth( 1.0f );
			glClear( GL_DEPTH_BUFFER_BIT );
			glEnable( GL_DEPTH_TEST );

		}

		unsigned layerMask() const override
		{
			return (unsigned)Layer::MidFront;
		}

};

}  // namespace

// ============================================================================
// LightTool
// ============================================================================

GAFFER_NODE_DEFINE_TYPE( LightTool );

LightTool::ToolDescription<LightTool, SceneView> LightTool::g_toolDescription;
size_t LightTool::g_firstPlugIndex = 0;

LightTool::LightTool( SceneView *view, const std::string &name ) :
	SelectionTool( view, name ),
	m_handles( new HandlesGadget() ),
	m_handleInspectionsDirty( true ),
	m_handleTransformsDirty( true ),
	m_priorityPathsDirty( true ),
	m_dragging( false ),
	m_scriptNode( nullptr ),
	m_mergeGroupId( 0 )
{
	view->viewportGadget()->addChild( m_handles );
	m_handles->setVisible( false );

	// Spotlight handles

	m_handles->addChild( new SpotLightHandle( "spot", SpotLightHandle::HandleType::Penumbra, view, 0, "westConeAngleParameter" ) );
	m_handles->addChild( new SpotLightHandle( "spot", SpotLightHandle::HandleType::Cone, view, 0, "westPenumbraAngleParameter" ) );
	m_handles->addChild( new SpotLightHandle( "spot", SpotLightHandle::HandleType::Penumbra, view, 90, "southConeAngleParameter" ) );
	m_handles->addChild( new SpotLightHandle( "spot", SpotLightHandle::HandleType::Cone, view, 90, "southPenumbraAngleParameter" ) );
	m_handles->addChild( new SpotLightHandle( "spot", SpotLightHandle::HandleType::Penumbra, view, 180, "eastConeAngleParameter" ) );
	m_handles->addChild( new SpotLightHandle( "spot", SpotLightHandle::HandleType::Cone, view, 180, "eastPenumbraAngleParameter" ) );
	m_handles->addChild( new SpotLightHandle( "spot", SpotLightHandle::HandleType::Penumbra, view, 270, "northConeAngleParameter" ) );
	m_handles->addChild( new SpotLightHandle( "spot", SpotLightHandle::HandleType::Cone, view, 270, "northPenumbraAngleParameter" ) );

	// Quadlight handles

	m_handles->addChild( new EdgeHandle( "quad", view, "widthParameter", V3f( -1.f, 0, 0 ), 2.f, "heightParameter", V3f( 0, 1.f, 0 ), 2.f, "", g_circleHandleWidthLarge, "widths", "westParameter" ) );
	m_handles->addChild( new CornerHandle( "quad", view, "widthParameter", V3f( -1.f, 0, 0 ), 2.f, "heightParameter", V3f( 0, -1.f, 0 ), 2.f, "southWestParameter" ) );
	m_handles->addChild( new EdgeHandle( "quad", view, "heightParameter", V3f( 0, -1.f, 0 ), 2.f, "widthParameter", V3f( 1.f, 0, 0 ), 2.f, "", g_circleHandleWidthLarge, "heights", "southParameter" ) );
	m_handles->addChild( new CornerHandle( "quad", view, "widthParameter", V3f( 1.f, 0, 0 ), 2.f, "heightParameter", V3f( 0, -1.f, 0 ), 2.f, "soutEastParameter" ) );
	m_handles->addChild( new EdgeHandle( "quad", view, "widthParameter", V3f( 1.f, 0, 0 ), 2.f, "heightParameter", V3f( 0, 1.f, 0 ), 2.f, "", g_circleHandleWidthLarge, "widths", "eastParameter" ) );
	m_handles->addChild( new CornerHandle( "quad", view, "widthParameter", V3f( 1.f, 0, 0 ), 2.f, "heightParameter", V3f( 0, 1.f, 0 ), 2.f, "northEastParameter" ) );
	m_handles->addChild( new EdgeHandle( "quad", view, "heightParameter", V3f( 0, 1.f, 0 ), 2.f, "widthParameter", V3f( 1.f, 0, 0 ), 2.f, "", g_circleHandleWidthLarge, "heights", "northParameter" ) );
	m_handles->addChild( new CornerHandle( "quad", view, "widthParameter", V3f( -1.f, 0, 0 ), 2.f, "heightParameter", V3f( 0, 1.f, 0 ), 2.f, "northWestParameter" ) );

	// DiskLight handles
	m_handles->addChild( new RadiusHandle( "disk", view, "radiusParameter", 1.f, false, true, "diskHandle" ) );
	m_handles->addChild( new RadiusHandle( "disk", view, "widthParameter", 2.f, false, true, "diskHandle" ) );

	// Sphere / PointLight handles
	m_handles->addChild( new RadiusHandle( "point", view, "radiusParameter", 1.f, true, false, "pointHandle" ) );

	// CylinderLight handles
	m_handles->addChild( new EdgeHandle( "cylinder", view, "radiusParameter", V3f( 0, 1.f, 0 ), 1.f, "lengthParameter", V3f( 0, 0, 1.f ), 2.f, "heightToScaleRatio", 0, "radii", "northRadiusParameter" ) );
	m_handles->addChild( new EdgeHandle( "cylinder", view, "radiusParameter", V3f( 1.f, 0, 0 ), 1.f, "lengthParameter", V3f( 0, 0, 1.f ), 2.f, "heightToScaleRatio", 0, "radii", "northRadiusParameter" ) );
	m_handles->addChild( new EdgeHandle( "cylinder", view, "radiusParameter", V3f( 0, -1.f, 0 ), 1.f, "lengthParameter", V3f( 0, 0, 1.f ), 2.f, "heightToScaleRatio", 0, "radii", "northRadiusParameter" ) );
	m_handles->addChild( new EdgeHandle( "cylinder", view, "radiusParameter", V3f( -1.f, 0, 0 ), 1.f, "lengthParameter", V3f( 0, 0, 1.f ), 2.f, "heightToScaleRatio", 0, "radii", "northRadiusParameter" ) );
	m_handles->addChild( new LengthHandle( "cylinder", view, "lengthParameter", V3f( 0, 0, 1.f ), 2.f, "cylinderLengthTop" ) );
	m_handles->addChild( new LengthHandle( "cylinder", view, "lengthParameter", V3f( 0, 0, -1.f ), 2.f, "cylinderLengthBottom" ) );

	for( const auto &c : m_handles->children() )
	{
		auto handle = runTimeCast<Handle>( c );
		handle->setVisible( false );
		handle->dragBeginSignal().connectFront( boost::bind( &LightTool::dragBegin, this, ::_1 ) );
		handle->dragMoveSignal().connect( boost::bind( &LightTool::dragMove, this, ::_1, ::_2 ) );
		handle->dragEndSignal().connect( boost::bind( &LightTool::dragEnd, this, ::_1 ) );
	}

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ScenePlug( "__scene", Plug::In ) );

	scenePlug()->setInput( view->inPlug<ScenePlug>() );

	plugDirtiedSignal().connect( boost::bind( &LightTool::plugDirtied, this, ::_1 ) );
	view->plugDirtiedSignal().connect( boost::bind( &LightTool::plugDirtied, this, ::_1 ) );

	connectToViewContext();
	view->contextChangedSignal().connect( boost::bind( &LightTool::connectToViewContext, this ) );

	Metadata::plugValueChangedSignal().connect( boost::bind( &LightTool::metadataChanged, this, ::_3 ) );
	Metadata::nodeValueChangedSignal().connect( boost::bind( &LightTool::metadataChanged, this, ::_2 ) );
}

LightTool::~LightTool()
{

}

const PathMatcher LightTool::selection() const
{
	return ContextAlgo::getSelectedPaths( view()->getContext() );
}

LightTool::SelectionChangedSignal &LightTool::selectionChangedSignal()
{
	return m_selectionChangedSignal;
}

ScenePlug *LightTool::scenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *LightTool::scenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

void LightTool::connectToViewContext()
{
	m_contextChangedConnection = view()->getContext()->changedSignal().connect(
		boost::bind( &LightTool::contextChanged, this, ::_2 )
	);
}

void LightTool::contextChanged( const InternedString &name )
{
	if(
		ContextAlgo::affectsSelectedPaths( name ) ||
		ContextAlgo::affectsLastSelectedPath( name ) ||
		!boost::starts_with( name.string(), "ui:" )
	)
	{
		m_handleInspectionsDirty = true;
		m_handleTransformsDirty = true;
		m_priorityPathsDirty = true;
		selectionChangedSignal()( *this );
	}
}

void LightTool::metadataChanged( InternedString key )
{
	if( !MetadataAlgo::readOnlyAffectedByChange( key ) )
	{
		return;
	}

	if( !m_handleInspectionsDirty )
	{
		m_handleInspectionsDirty = true;
		view()->viewportGadget()->renderRequestSignal()( view()->viewportGadget() );
	}
}

void LightTool::updateHandleInspections()
{
	if( m_dragging )
	{
		return;
	}

	auto scene = scenePlug()->getInput<ScenePlug>();
	scene = scene ? scene->getInput<ScenePlug>() : scene;
	if( !scene )
	{
		return;
	}

	m_inspectorsDirtiedConnection.clear();

	const PathMatcher selection = this->selection();
	if( selection.isEmpty() )
	{
		for( auto &c : m_handles->children() )
		{
			auto handle = runTimeCast<LightToolHandle>( c );
			handle->setVisible( false );
		}
		return;
	}

	ScenePlug::ScenePath lastSelectedPath = ContextAlgo::getLastSelectedPath( view()->getContext() );
	assert( selection.match( lastSelectedPath ) & PathMatcher::ExactMatch );

	bool lookThroughLight = false;

	if( auto lookThroughEnabledPlug = view()->descendant<BoolPlug>( "camera.lookThroughEnabled") )
	{
		if( lookThroughEnabledPlug->getValue() )
		{
			Path lookThroughCamera = Path( view()->descendant<StringPlug>( "camera.lookThroughCamera" )->getValue() );
			lookThroughLight = lookThroughCamera == Path( lastSelectedPath );
		}
	}

	ScenePlug::PathScope pathScope( view()->getContext() );

	for( auto &c : m_handles->children() )
	{
		auto handle = runTimeCast<LightToolHandle>( c );
		assert( handle );

		handle->updateHandlePath( scene, view()->getContext(), lastSelectedPath );

		bool handleVisible = true;
		bool handleEnabled = true;

		for( PathMatcher::Iterator it = selection.begin(), eIt = selection.end(); it != eIt; ++it )
		{
			pathScope.setPath( &(*it) );

			handleVisible &= handle->visible();
			handleEnabled &= handle->enabled();
		}

		handle->setLookThroughLight( lookThroughLight );

		handle->setEnabled( handleEnabled );
		handle->setVisible( handleVisible );

		handle->clearInspections();

		if( handleVisible )
		{
			for( PathMatcher::Iterator it = selection.begin(), eIt = selection.end(); it != eIt; ++it )
			{
				pathScope.setPath( &(*it) );
				handle->addInspection();
			}
		}
	}
}

void LightTool::updateHandleTransforms( float rasterScale )
{
	Context::Scope scopedContext( view()->getContext() );

	auto scene = scenePlug()->getInput<ScenePlug>();
	scene = scene ? scene->getInput<ScenePlug>() : scene;
	if( !scene )
	{
		return;
	}

	const PathMatcher selection = this->selection();
	if( selection.isEmpty() )
	{
		return;
	}

	ScenePlug::ScenePath lastSelectedPath = ContextAlgo::getLastSelectedPath( view()->getContext() );
	assert( selection.match( lastSelectedPath ) & PathMatcher::Result::ExactMatch );
	if( !scene->exists( lastSelectedPath ) )
	{
		return;
	}

	const M44f fullTransform = scene->fullTransform( lastSelectedPath );
	/// \todo Should this be handled in the LightToolHandle derived classes
	/// and make `updateLocalTransform()` a more general `setTransform()` method?
	m_handles->setTransform( sansScalingAndShear( fullTransform ) );

	V3f scale;
	V3f shear;
	extractScalingAndShear( fullTransform, scale, shear );

	for( auto &c : m_handles->children() )
	{
		auto handle = runTimeCast<LightToolHandle>( c );
		assert( handle );

		if( handle->getVisible() )
		{
			handle->updateLocalTransform( scale, shear );
			handle->setRasterScale( rasterScale );
		}

	}
}

void LightTool::plugDirtied( const Plug *plug )
{

	// Note : This method is called not only when plugs
	// belonging to the LightTool are dirtied, but
	// _also_ when plugs belonging to the View are dirtied.

	if(
		plug == activePlug() ||
		plug == scenePlug()->childNamesPlug() ||
		( plug->ancestor<View>() && plug == view()->editScopePlug() )
	)
	{
		if( !m_dragging )
		{
			selectionChangedSignal()( *this );
		}
		m_handleInspectionsDirty = true;
		m_priorityPathsDirty = true;
	}

	if( plug == activePlug() )
	{
		if( activePlug()->getValue() )
		{
			m_preRenderConnection = view()->viewportGadget()->preRenderSignal().connect(
				boost::bind( &LightTool::preRender, this )
			);
		}
		else
		{
			m_preRenderConnection.disconnect();
			m_handles->setVisible( false );
		}
	}

	if( plug == scenePlug()->transformPlug() )
	{
		m_handleTransformsDirty = true;
	}

	if(
		plug == view()->descendant<FloatPlug>( "drawingMode.visualiser.scale" ) ||
		plug == view()->descendant<FloatPlug>( "drawingMode.light.frustumScale" )
	)
	{
		m_handleInspectionsDirty = true;
	}

	/// \todo Checking for dirty attributes overlaps with the job of the inspector
	/// dirtied plug from `updateHandleInspections()`. Should we remove handling
	/// inspector dirtied signals? The `gl:visualiser:scale` attribute is used to
	/// place the handles, so we at least need to catch changes to that attribute.
	if( plug == scenePlug()->attributesPlug() )
	{
		m_handleInspectionsDirty = true;
		m_handleTransformsDirty = true;
	}
}

void LightTool::preRender()
{
	if( !m_dragging )
	{
		if( m_priorityPathsDirty )
		{
			m_priorityPathsDirty = false;
			auto sceneGadget = static_cast<SceneGadget *>( view()->viewportGadget()->getPrimaryChild() );
			if( !selection().isEmpty() )
			{
				sceneGadget->setPriorityPaths( ContextAlgo::getSelectedPaths( view()->getContext() ) );
			}
			else
			{
				sceneGadget->setPriorityPaths( IECore::PathMatcher() );
			}
		}
	}

	if( m_handleInspectionsDirty && !m_dragging )
	{
		updateHandleInspections();
		m_handleInspectionsDirty = false;

		for( auto &c : m_handles->children() )
		{
			auto handle = runTimeCast<LightToolHandle>( c );
			if( handle->getVisible() )
			{
				m_handles->setVisible( true );
				break;
			}
		}
	}

	if( m_handleTransformsDirty )
	{
		updateHandleTransforms( 0 );
		m_handleTransformsDirty = false;
	}
}

void LightTool::dirtyHandleTransforms()
{
	m_handleTransformsDirty = true;
}

RunTimeTypedPtr LightTool::dragBegin( Gadget *gadget )
{
	m_dragging = true;
	m_scriptNode = view()->inPlug()->source()->ancestor<ScriptNode>();

	return nullptr;
}

bool LightTool::dragMove( Gadget *gadget, const DragDropEvent &event )
{
	auto handle = runTimeCast<LightToolHandle>( gadget );
	assert( handle );

	UndoScope undoScope( m_scriptNode.get(), UndoScope::Enabled, undoMergeGroup() );

	handle->handleDragMove( event );

	return true;
}

bool LightTool::dragEnd( Gadget *gadget )
{
	m_dragging = false;
	m_mergeGroupId++;
	selectionChangedSignal()( *this );

	auto handle = runTimeCast<LightToolHandle>( gadget );
	handle->handleDragEnd();

	return false;
}

std::string LightTool::undoMergeGroup() const
{
	return fmt::format( "LightTool{}{}", fmt::ptr( this ), m_mergeGroupId );
}
