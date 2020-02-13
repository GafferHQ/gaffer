//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, John Haddon. All rights reserved.
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

#include "GafferSceneUI/StandardLightVisualiser.h"

#include "Gaffer/Metadata.h"

#include "IECoreGL/CurvesPrimitive.h"
#include "IECoreGL/DiskPrimitive.h"
#include "IECoreGL/Group.h"
#include "IECoreGL/QuadPrimitive.h"
#include "IECoreGL/ShaderLoader.h"
#include "IECoreGL/ShaderStateComponent.h"
#include "IECoreGL/SpherePrimitive.h"
#include "IECoreGL/TextureLoader.h"
#include "IECoreGL/ToGLMeshConverter.h"

#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/Shader.h"

using namespace std;
using namespace boost;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreGL;
using namespace Gaffer;
using namespace GafferSceneUI;
using namespace IECoreGLPreview;

//////////////////////////////////////////////////////////////////////////
// Utility methods. We define these in an anonymouse namespace rather
// than clutter up the header with private methods.
//////////////////////////////////////////////////////////////////////////

namespace
{

const Color3f g_lightWireframeColor = Color3f( 1.0f, 0.835f, 0.07f );
const Color4f g_lightWireframeColor4 = Color4f( g_lightWireframeColor.x, g_lightWireframeColor.y, g_lightWireframeColor.z, 1.0f );

enum Axis { X, Y, Z };

IECore::InternedString metadataTargetForNetwork( const IECoreScene::ShaderNetwork *shaderNetwork )
{
	const IECoreScene::Shader *shader = shaderNetwork->outputShader();
	return shader->getType() + ":" + shader->getName();
}

template<typename T>
T parameter( InternedString metadataTarget, const IECore::CompoundData *parameters, InternedString parameterNameMetadata, T defaultValue )
{
	ConstStringDataPtr parameterName = Metadata::value<StringData>( metadataTarget, parameterNameMetadata );
	if( !parameterName )
	{
		return defaultValue;
	}

	typedef IECore::TypedData<T> DataType;
	if( const DataType *parameterData = parameters->member<DataType>( parameterName->readable() ) )
	{
		return parameterData->readable();
	}

	return defaultValue;
}

void addRay( const V3f &start, const V3f &end, vector<int> &vertsPerCurve, vector<V3f> &p )
{
	const float arrowScale = 0.05;

	const V3f dir = end - start;
	V3f perp = dir % V3f( 1, 0, 0 );
	if( perp.length() == 0.0f )
	{
		perp = dir % V3f( 0, 1, 0 );
	}

	p.push_back( start );
	p.push_back( end );
	vertsPerCurve.push_back( 2 );

	p.push_back( end + arrowScale * ( perp * 2 - dir * 3 ) );
	p.push_back( end );
	p.push_back( end + arrowScale * ( perp * -2 - dir * 3 ) );
	vertsPerCurve.push_back( 3 );
}

void addCircle( Axis axis, const V3f &center, float radius, vector<int> &vertsPerCurve, vector<V3f> &p )
{
	const int numDivisions = 100;
	for( int i = 0; i < numDivisions; ++i )
	{
		const float angle = 2 * M_PI * (float)i/(float)(numDivisions-1);
		if( axis == Axis::Z )
		{
			p.push_back( center + radius * V3f( cos( angle ), sin( angle ), 0 ) );
		}
		else if( axis == Axis::X )
		{
			p.push_back( center + radius * V3f( 0, cos( angle ), sin( angle ) ) );
		}
		else
		{
			p.push_back( center + radius * V3f( cos( angle ), 0, sin( angle ) ) );
		}
	}
	vertsPerCurve.push_back( numDivisions );
}

void addSolidArc( Axis axis, const V3f &center, float majorRadius, float minorRadius, float startFraction, float stopFraction, vector<int> &vertsPerPoly, vector<int> &vertIds, vector<V3f> &p )
{
	const int numSegmentsForCircle = 100;
	int numSegments = max( 1, (int)ceil( (stopFraction - startFraction) * numSegmentsForCircle ) );

	int start = p.size();
	for( int i = 0; i < numSegments + 1; ++i )
	{
		const float angle = 2 * M_PI * ( startFraction + (stopFraction - startFraction) * (float)i/(float)(numSegments) );
		V3f dir( -sin( angle ), cos( angle ), 0 );
		if( axis == Axis::X ) dir = V3f( 0, dir[1], -dir[0] );
		else if( axis == Axis::Y ) dir = V3f( dir[1], 0, dir[0] );
		p.push_back( center + majorRadius * dir );
		p.push_back( center + minorRadius * dir );
	}
	for( int i = 0; i < numSegments; ++i )
	{
		vertIds.push_back( start + i * 2 );
		vertIds.push_back( start + i * 2  + 1);
		vertIds.push_back( start + i * 2  + 3);
		vertIds.push_back( start + i * 2  + 2);
		vertsPerPoly.push_back( 4 );
	}
}

void addCone( float angle, float startRadius, vector<int> &vertsPerCurve, vector<V3f> &p, float length )
{
	const float halfAngle = 0.5 * M_PI * angle / 180.0;
	const float baseRadius = length * sin( halfAngle );
	const float baseDistance = length * cos( halfAngle );

	if( startRadius > 0 )
	{
		addCircle( Axis::Z, V3f( 0 ), startRadius, vertsPerCurve, p );
	}
	addCircle( Axis::Z, V3f( 0, 0, -baseDistance ), baseRadius + startRadius, vertsPerCurve, p );

	p.push_back( V3f( 0, startRadius, 0 ) );
	p.push_back( V3f( 0, baseRadius + startRadius, -baseDistance ) );
	vertsPerCurve.push_back( 2 );

	p.push_back( V3f( startRadius, 0, 0 ) );
	p.push_back( V3f( baseRadius + startRadius, 0, -baseDistance ) );
	vertsPerCurve.push_back( 2 );

	p.push_back( V3f( 0, -startRadius, 0 ) );
	p.push_back( V3f( 0, -baseRadius - startRadius, -baseDistance ) );
	vertsPerCurve.push_back( 2 );

	p.push_back( V3f( -startRadius, 0, 0 ) );
	p.push_back( V3f( -baseRadius - startRadius, 0, -baseDistance ) );
	vertsPerCurve.push_back( 2 );
}

// Shaders

const char *constantFragSource()
{
	return
		"#version 120\n"
		""
		"#if __VERSION__ <= 120\n"
		"#define in varying\n"
		"#endif\n"
		""
		"#include \"IECoreGL/ColorAlgo.h\"\n"
		""
		"in vec3 fragmentCs;"
		""
		"uniform int linearColor;"
		"uniform vec3 tint;"
		""
		"void main()"
		"{"
			"if( linearColor == 1 ) {"
				"gl_FragColor = vec4( ieLinToSRGB( fragmentCs * tint ), 1 );"
			"} else {"
				"gl_FragColor = vec4( fragmentCs * tint, 1 );"
			"}"
		"}"
	;
}

const char *texturedConstantFragSource()
{
	return
		"#version 120\n"
		""
		"#if __VERSION__ <= 120\n"
		"#define in varying\n"
		"#endif\n"
		""
		"#include \"IECoreGL/ColorAlgo.h\"\n"
		""
		"in vec2 fragmentuv;"
		"uniform sampler2D texture;"
		"uniform vec3 tint;"
		""
		"void main()"
		"{"
			"vec3 c = texture2D( texture, fragmentuv ).xyz;"
			"gl_FragColor = vec4( ieLinToSRGB( c * tint ), 1.0 );"
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
		"uniform int aimType;"
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
		"	if( aimType == 0 )"
		"	{"
		"		vec4 viewDirectionInObjectSpace = gl_ModelViewMatrixInverse * vec4( 0, 0, -1, 0 );"
		"		vec3 viewCross = cross( viewDirectionInObjectSpace.xyz, vec3( 0, 0, -1 ) );"
		"		aimedYAxis = length( viewCross ) > 0.0001 ? normalize( viewCross ) : vec3( 1, 0, 0 );"
		"		aimedXAxis = normalize( cross( aimedYAxis, vec3( 0, 0, -1 ) ) );"
		"		aimedZAxis = vec3( 0, 0, 1 );"
		"	}"
		"	else"
		"	{"
		"		aimedXAxis = normalize( gl_ModelViewMatrixInverse * vec4( 0, 0, -1, 0 ) ).xyz;"
		"		aimedYAxis = normalize( gl_ModelViewMatrixInverse * vec4( 0, 1, 0, 0 ) ).xyz;"
		"		aimedZAxis = normalize( gl_ModelViewMatrixInverse * vec4( 1, 0, 0, 0 ) ).xyz;"
		"	}"
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

// Shader state helpers

void addWireframeCurveState( IECoreGL::Group *group, float lineWidthScale = 1.0f )
{
	group->getState()->add( new IECoreGL::Primitive::DrawWireframe( false ) );
	group->getState()->add( new IECoreGL::Primitive::DrawSolid( true ) );
	group->getState()->add( new IECoreGL::CurvesPrimitive::UseGLLines( true ) );
	group->getState()->add( new IECoreGL::CurvesPrimitive::GLLineWidth( 2.0f * lineWidthScale ) );
	group->getState()->add( new IECoreGL::LineSmoothingStateComponent( true ) );
}

void addConstantShader( IECoreGL::Group *group, const Imath::Color3f &tint, bool linearColor = false, int aimType = -1 )
{
	IECore::CompoundObjectPtr parameters = new CompoundObject;

	if( aimType > -1 )
	{
		parameters->members()["aimType"] = new IntData( aimType );
	}

	parameters->members()["linearColor"] = new IntData( linearColor ? 1 : 0 );
	parameters->members()["tint"] = new Color3fData( tint );

	group->getState()->add(
		new IECoreGL::ShaderStateComponent(
			ShaderLoader::defaultShaderLoader(),
			TextureLoader::defaultTextureLoader(),
			aimType > -1 ? faceCameraVertexSource() : "",
			"",
			constantFragSource(),
			parameters
		)
	);
}

void addConstantShader( IECoreGL::Group *group, bool linearColor = false, int aimType = -1 )
{
	addConstantShader( group, Color3f( 1.0f ), linearColor, aimType );
}

void addTexturedConstantShader( IECoreGL::Group *group, IECore::ConstDataPtr textureData, const Color3f &tint, int maxTextureResolution )
{
	IECore::CompoundObjectPtr shaderParameters = new CompoundObject;

	shaderParameters->members()["texture"] = const_cast<Data *>( textureData.get() );
	shaderParameters->members()["texture:maxResolution"] = new IntData( maxTextureResolution );
	shaderParameters->members()["tint"] = new Color3fData( tint );

	group->getState()->add(
		new IECoreGL::ShaderStateComponent(
			ShaderLoader::defaultShaderLoader(),
			TextureLoader::defaultTextureLoader(),
			"",
			"",
			texturedConstantFragSource(),
			shaderParameters
		)
	);
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// StandardLightVisualiser implementation.
//////////////////////////////////////////////////////////////////////////

// Register as the standard fallback visualiser.
LightVisualiser::LightVisualiserDescription<StandardLightVisualiser> StandardLightVisualiser::g_description( "light *:light", "*" );

StandardLightVisualiser::StandardLightVisualiser()
{
}

StandardLightVisualiser::~StandardLightVisualiser()
{
}

Visualisations StandardLightVisualiser::visualise( const IECore::InternedString &attributeName, const IECoreScene::ShaderNetwork *shaderNetwork, const IECore::CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const
{
	const InternedString metadataTarget = metadataTargetForNetwork( shaderNetwork );
	const IECore::CompoundData *shaderParameters = shaderNetwork->outputShader()->parametersData();

	ConstStringDataPtr type = Metadata::value<StringData>( metadataTarget, "type" );
	ConstM44fDataPtr orientation = Metadata::value<M44fData>( metadataTarget, "visualiserOrientation" );

	const Color3f color = parameter<Color3f>( metadataTarget, shaderParameters, "colorParameter", Color3f( 1.0f ) );
	const Color3f tint = parameter<Color3f>( metadataTarget, shaderParameters, "tintParameter", Color3f( 1.0f ) );

	// Ornaments are affected by visualiser:scale and not local scale.
	GroupPtr ornaments = new Group;
	// Bound ornaments are considered when 'f' is pressed in the viewer to fit.
	GroupPtr boundOrnaments = new Group;
	// As part of our assumption that renderer's largely ignore scale, this is
	// contains anything that should always be in fixed world scale and not be
	// affected by visualiser scale.
	GroupPtr fixedScaleOrnaments = new Group;
	// Geometry is only affected by local scale (its size matters for rendering).
	GroupPtr geometry = new Group;
	// As 'projections' are largely for display, and lights don't generally
	// scale this group only follows visualiser scale.
	GroupPtr frustum = new Group;

	const FloatData *visualiserScaleData = attributes->member<FloatData>( "gl:visualiser:scale" );
	const float visualiserScale = visualiserScaleData ? visualiserScaleData->readable() : 1.0;
	const FloatData *frustumScaleData = attributes->member<FloatData>( "gl:light:frustumScale" );
	const float frustumScale = frustumScaleData ? frustumScaleData->readable() : 1.0;
	const StringData *visualiserDrawingModeData = attributes->member<StringData>( "gl:light:drawingMode" );
	const std::string visualiserDrawingMode = visualiserDrawingModeData ? visualiserDrawingModeData->readable() : "texture";

	const bool drawShaded = visualiserDrawingMode != "wireframe";
	const bool drawTextured = visualiserDrawingMode == "texture";

	const IntData *maxTextureResolutionData = attributes->member<IntData>( "gl:visualiser:maxTextureResolution" );
	const int maxTextureResolution = maxTextureResolutionData ? maxTextureResolutionData->readable() : std::numeric_limits<int>::max();

	Imath::M44f topTransform;
	if( orientation )
	{
		topTransform = orientation->readable();
	}
	geometry->setTransform( topTransform );
	ornaments->setTransform( topTransform );
	boundOrnaments->setTransform( topTransform );
	fixedScaleOrnaments->setTransform( topTransform );
	frustum->setTransform( topTransform );

	if( type && type->readable() == "environment" )
	{
		if( drawShaded )
		{
			ConstDataPtr textureData = drawTextured ? surfaceTexture( shaderNetwork, attributes, maxTextureResolution ) : nullptr;
			boundOrnaments->addChild( const_pointer_cast<IECoreGL::Renderable>( environmentSphereSurface( textureData, tint, maxTextureResolution, color ) ) );
		}
		boundOrnaments->addChild( const_pointer_cast<IECoreGL::Renderable>( sphereWireframe( 1.05f, Vec3<bool>( true ) ) ) );
	}
	else if( type && type->readable() == "spot" )
	{
		float innerAngle, outerAngle, radius, lensRadius;
		spotlightParameters( attributeName, shaderNetwork, innerAngle, outerAngle, radius, lensRadius );
		boundOrnaments->addChild( const_pointer_cast<IECoreGL::Renderable>( spotlightCone( innerAngle, outerAngle, lensRadius / visualiserScale, 1.0f, 1.0f ) ) );
		fixedScaleOrnaments->addChild( const_pointer_cast<IECoreGL::Renderable>( sphereWireframe( radius, Vec3<bool>( false, true, true ), 0.5f ) ) );
		ornaments->addChild( const_pointer_cast<IECoreGL::Renderable>( ray() ) );
		ornaments->addChild( const_pointer_cast<IECoreGL::Renderable>( colorIndicator( color ) ) );
		frustum->addChild( const_pointer_cast<IECoreGL::Renderable>( spotlightCone( innerAngle, outerAngle, lensRadius / visualiserScale, 10.0f * frustumScale, 0.2f ) ) );
	}
	else if( type && type->readable() == "distant" )
	{
		boundOrnaments->addChild( const_pointer_cast<IECoreGL::Renderable>( distantRays() ) );
		ornaments->addChild( const_pointer_cast<IECoreGL::Renderable>( colorIndicator( color ) ) );
	}
	else if( type && type->readable() == "quad" )
	{
		const V2f size( 2 );
		// Cycles/Arnold define portals via a parameter on a quad, rather than as it's own light type.
		if( parameter<bool>( metadataTarget, shaderParameters, "portalParameter", false ) )
		{
			geometry->addChild( const_pointer_cast<IECoreGL::Renderable>( quadPortal( size, visualiserScale ) ) );
		}
		else
		{
			if( drawShaded )
			{
				ConstDataPtr textureData = drawTextured ? surfaceTexture( shaderNetwork, attributes, maxTextureResolution ) : nullptr;
				geometry->addChild( const_pointer_cast<IECoreGL::Renderable>( quadSurface( size, textureData, tint, maxTextureResolution, color ) ) );
			}
			else
			{
				ornaments->addChild( const_pointer_cast<IECoreGL::Renderable>( colorIndicator( color * tint ) ) );
			}
			geometry->addChild( const_pointer_cast<IECoreGL::Renderable>( quadWireframe( size ) ) );

			const float spread = parameter<float>( metadataTarget, shaderParameters, "spreadParameter", -1 );
			if( spread >= 0.0f )
			{
				ornaments->addChild( const_pointer_cast<IECoreGL::Renderable>( areaSpread( spread ) ) );
			}
		}
		ornaments->addChild( const_pointer_cast<IECoreGL::Renderable>( ray() ) );
	}
	else if( type && type->readable() == "disk" )
	{
		const float radius = parameter<float>( metadataTarget, shaderParameters, "radiusParameter", 1 );

		if( drawShaded )
		{
			ConstDataPtr textureData = drawTextured ? surfaceTexture( shaderNetwork, attributes, maxTextureResolution ) : nullptr;
			geometry->addChild( const_pointer_cast<IECoreGL::Renderable>( diskSurface( radius, textureData, tint, maxTextureResolution, color ) ) );
		}
		else
		{
			ornaments->addChild( const_pointer_cast<IECoreGL::Renderable>( colorIndicator( color * tint ) ) );
		}
		geometry->addChild( const_pointer_cast<IECoreGL::Renderable>( diskWireframe( radius ) ) );
		ornaments->addChild( const_pointer_cast<IECoreGL::Renderable>( ray() ) );

		const float spread = parameter<float>( metadataTarget, shaderParameters, "spreadParameter", -1 );
		if( spread >= 0.0f )
		{
			ornaments->addChild( const_pointer_cast<IECoreGL::Renderable>( areaSpread( spread ) ) );
		}
	}
	else if( type && type->readable() == "cylinder" )
	{
		const float radius = parameter<float>( metadataTarget, shaderParameters, "radiusParameter", 1 );
		geometry->addChild( const_pointer_cast<IECoreGL::Renderable>( cylinderShape( radius, drawShaded, color * tint ) ) );
		ornaments->addChild( const_pointer_cast<IECoreGL::Renderable>( cylinderRays( radius ) ) );
		if( !drawShaded )
		{
			ornaments->addChild( const_pointer_cast<IECoreGL::Renderable>( colorIndicator( color * tint ) ) );
		}
	}
	else if( type && type->readable() == "mesh" )
	{
		// There isn't any meaningful place to draw anything for the mesh
		// light, so instead we make the mesh outline visible and light coloured.
		IECoreGL::StatePtr meshState = new IECoreGL::State( false );
		meshState->add( new IECoreGL::Primitive::DrawOutline( true ) );
		meshState->add( new IECoreGL::Primitive::OutlineWidth( 2.0f ) );
		meshState->add( new IECoreGL::OutlineColorStateComponent( g_lightWireframeColor4 ) );
		state = meshState;
	}
	else if( type && type->readable() == "photometric" )
	{
		const float radius = parameter<float>( metadataTarget, shaderParameters, "radiusParameter", 0 );
		if( radius > 0 )
		{
			fixedScaleOrnaments->addChild( const_pointer_cast<IECoreGL::Renderable>( sphereWireframe( radius, Vec3<bool>( true, false, true ), 0.5f ) ) );
		}
		ornaments->addChild( const_pointer_cast<IECoreGL::Renderable>( colorIndicator( color ) ) );
		ornaments->addChild( const_pointer_cast<IECoreGL::Renderable>( ray() ) );
	}
	else
	{
		// Treat everything else as a point light.
		const float radius = parameter<float>( metadataTarget, shaderParameters, "radiusParameter", 0 );
		if( radius > 0 )
		{
			fixedScaleOrnaments->addChild( const_pointer_cast<IECoreGL::Renderable>( pointShape( radius ) ) );
		}

		boundOrnaments->addChild( const_pointer_cast<IECoreGL::Renderable>( pointRays( radius / visualiserScale ) ) );
		ornaments->addChild( const_pointer_cast<IECoreGL::Renderable>( colorIndicator( color ) ) );

	}

	Visualisations result;
	if( !geometry->children().empty() )
	{
		result.push_back( Visualisation::createGeometry( geometry ) );
	}
	if( !ornaments->children().empty() )
	{
		result.push_back( Visualisation::createOrnament( ornaments, false ) );
	}
	if( !boundOrnaments->children().empty() )
	{
		result.push_back( Visualisation::createOrnament( boundOrnaments, true ) );
	}
	if( !fixedScaleOrnaments->children().empty() )
	{
		result.push_back( Visualisation( fixedScaleOrnaments, Visualisation::Scale::None ) );
	}
	if( !frustum->children().empty() )
	{
		result.push_back( Visualisation::createFrustum( frustum, Visualisation::Scale::Visualiser ) );
	}
	return result;
}

IECore::DataPtr StandardLightVisualiser::surfaceTexture( const IECoreScene::ShaderNetwork *shaderNetwork, const IECore::CompoundObject *attributes, int maxTextureResolution ) const
{
	const IECore::InternedString metadataTarget = metadataTargetForNetwork( shaderNetwork );
	const IECore::CompoundData *shaderParameters = shaderNetwork->outputShader()->parametersData();
	const std::string textureName = parameter<std::string>( metadataTarget, shaderParameters, "textureNameParameter", "" );
	if( !textureName.empty() )
	{
		return new IECore::StringData( textureName );
	}

	return nullptr;
}

void StandardLightVisualiser::spotlightParameters( const InternedString &attributeName, const IECoreScene::ShaderNetwork *shaderNetwork, float &innerAngle, float &outerAngle, float &radius, float &lensRadius )
{

	InternedString metadataTarget = metadataTargetForNetwork( shaderNetwork );
	const IECore::CompoundData *shaderParameters = shaderNetwork->outputShader()->parametersData();

	float coneAngle = parameter<float>( metadataTarget, shaderParameters, "coneAngleParameter", 0.0f );
	float penumbraAngle = parameter<float>( metadataTarget, shaderParameters, "penumbraAngleParameter", 0.0f );
	if( ConstStringDataPtr angleUnit = Metadata::value<StringData>( metadataTarget, "angleUnit" ) )
	{
		if( angleUnit->readable() == "radians" )
		{
			coneAngle *= 180.0 / M_PI;
			penumbraAngle *= 180 / M_PI;
		}
	}

	innerAngle = 0;
	outerAngle = 0;

	ConstStringDataPtr penumbraTypeData = Metadata::value<StringData>( metadataTarget, "penumbraType" );
	const std::string *penumbraType = penumbraTypeData ? &penumbraTypeData->readable() : NULL;

	if( !penumbraType || *penumbraType == "inset" )
	{
		outerAngle = coneAngle;
		innerAngle = coneAngle - 2.0f * penumbraAngle;
	}
	else if( *penumbraType == "outset" )
	{
		outerAngle = coneAngle + 2.0f * penumbraAngle;
		innerAngle = coneAngle ;
	}
	else if( *penumbraType == "absolute" )
	{
		outerAngle = coneAngle;
		innerAngle = penumbraAngle;
	}

	lensRadius = 0.0f;
	if( parameter<bool>( metadataTarget, shaderParameters, "lensRadiusEnableParameter", true ) )
	{
		lensRadius = parameter<float>( metadataTarget, shaderParameters, "lensRadiusParameter", 0.0f );
	}

	radius = 0.0f;
	radius = parameter<float>( metadataTarget, shaderParameters, "radiusParameter", 0.0f );

}


IECoreGL::ConstRenderablePtr StandardLightVisualiser::ray()
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get() );
	addConstantShader( group.get(), false, 0 );

	IntVectorDataPtr vertsPerCurve = new IntVectorData;
	V3fVectorDataPtr p = new V3fVectorData;
	addRay( V3f( 0 ), V3f( 0, 0, -1 ), vertsPerCurve->writable(), p->writable() );

	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurve );
	curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, p ) );
	curves->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( g_lightWireframeColor ) ) );

	group->addChild( curves );

	return group;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::pointRays( float radius )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get() );
	addConstantShader( group.get(), false, 1 );

	IntVectorDataPtr vertsPerCurve = new IntVectorData;
	V3fVectorDataPtr p = new V3fVectorData;

	const int numRays = 8;
	for( int i = 0; i < numRays; ++i )
	{
		const float angle = M_PI * 2.0f * float(i)/(float)numRays;
		const V3f dir( 0.0, sin( angle ), -cos( angle ) );
		addRay( dir * ( 0.2f + radius ), dir * ( 0.5f + radius ), vertsPerCurve->writable(), p->writable() );
	}

	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurve );
	curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, p ) );
	curves->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( g_lightWireframeColor ) ) );

	group->addChild( curves );

	return group;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::distantRays()
{
	GroupPtr result = new Group;
	for( int i = 0; i < 3; i++ )
	{
		IECoreGL::GroupPtr rayGroup = new IECoreGL::Group();

		Imath::M44f trans;
		trans.rotate( V3f( 0, 0, 2.0 * M_PI / 3.0 * i ) );
		trans.translate( V3f( 0, 0.4, 0.5 ) );
		rayGroup->addChild( const_pointer_cast<IECoreGL::Renderable>( ray() ) );
		rayGroup->setTransform( trans );

		result->addChild( rayGroup );
	}

	return result;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::spotlightCone( float innerAngle, float outerAngle, float lensRadius, float length, float lineWidthScale )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get(), lineWidthScale );
	addConstantShader( group.get(), false );

	IntVectorDataPtr vertsPerCurve = new IntVectorData;
	V3fVectorDataPtr p = new V3fVectorData;
	addCone( innerAngle, lensRadius, vertsPerCurve->writable(), p->writable(), length );

	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurve );
	curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, p ) );

	const Color3fDataPtr color = new Color3fData( lineWidthScale < 1.0f ? Color3f( 0.627f, 0.580f, 0.352f ) : g_lightWireframeColor );
	curves->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, color ) );

	group->addChild( curves );

	if( fabs( innerAngle - outerAngle ) > 0.1 )
	{
		IECoreGL::GroupPtr outerGroup = new Group;
		outerGroup->getState()->add( new IECoreGL::CurvesPrimitive::GLLineWidth( 1.0f * lineWidthScale ) );

		IntVectorDataPtr vertsPerCurve = new IntVectorData;
		V3fVectorDataPtr p = new V3fVectorData;
		addCone( outerAngle, lensRadius, vertsPerCurve->writable(), p->writable(), length );

		IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurve );
		curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, p ) );

		curves->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, color ) );

		outerGroup->addChild( curves );

		group->addChild( outerGroup );
	}

	return group;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::colorIndicator( const Imath::Color3f &color )
{

	IECoreGL::GroupPtr group = new IECoreGL::Group();

	addConstantShader( group.get(), true, 1 );

	const float indicatorRad = 0.1f;

	{
		IntVectorDataPtr vertsPerPoly = new IntVectorData;
		IntVectorDataPtr vertIds = new IntVectorData;
		V3fVectorDataPtr p = new V3fVectorData;

		addSolidArc( Axis::X, V3f( 0 ), 0, indicatorRad, 0, 1, vertsPerPoly->writable(), vertIds->writable(), p->writable() );

		IECoreScene::MeshPrimitivePtr mesh = new IECoreScene::MeshPrimitive( vertsPerPoly, vertIds, "linear", p );
		mesh->variables["N"] = IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new V3fData( V3f( 0 ) ) );
		mesh->variables["Cs"] = IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( color ) );
		ToGLMeshConverterPtr meshConverter = new ToGLMeshConverter( mesh );
		group->addChild( IECore::runTimeCast<IECoreGL::Renderable>( meshConverter->convert() ) );
	}

	return group;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::cylinderShape( float radius, bool filled, const Color3f &color )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get() );
	addConstantShader( group.get(), false, 0 );

	if( filled )
	{
		IntVectorDataPtr vertsPerPolyData = new IntVectorData;
		IntVectorDataPtr vertIdsData = new IntVectorData;
		V3fVectorDataPtr pData = new V3fVectorData;

		vector<int> &vertIds = vertIdsData->writable();
		vector<V3f> &p = pData->writable();

		addSolidArc( Axis::Z, V3f( 0, 0, -1 ), radius, 0, 0, 1, vertsPerPolyData->writable(), vertIds, p );
		addSolidArc( Axis::Z, V3f( 0, 0, 1 ), radius, 0, 0, 1, vertsPerPolyData->writable(), vertIds, p );

		size_t lastIndex = p.size();
		p.push_back( V3f( 0, radius, -1 ) );
		p.push_back( V3f( 0, radius, 1 ) );
		p.push_back( V3f( 0, -radius, 1 ) );
		p.push_back( V3f( 0, -radius, -1 ) );
		vertIds.push_back( lastIndex++ );
		vertIds.push_back( lastIndex++ );
		vertIds.push_back( lastIndex++ );
		vertIds.push_back( lastIndex );
		vertsPerPolyData->writable().push_back( 4 );

		IECoreScene::MeshPrimitivePtr mesh = new IECoreScene::MeshPrimitive( vertsPerPolyData, vertIdsData, "linear", pData );
		mesh->variables["N"] = IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new V3fData( V3f( 0 ) ) );
		mesh->variables["Cs"] = IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( color ) );
		ToGLMeshConverterPtr meshConverter = new ToGLMeshConverter( mesh );
		group->addChild( IECore::runTimeCast<IECoreGL::Renderable>( meshConverter->convert() ) );
	}

	IntVectorDataPtr vertsPerCurveData = new IntVectorData;
	vector<int> &vertsPerCurve = vertsPerCurveData->writable();
	V3fVectorDataPtr pData = new V3fVectorData;
	vector<V3f> &p = pData->writable();

	addCircle( Axis::Z, V3f( 0, 0, -1 ), radius, vertsPerCurve, p );
	addCircle( Axis::Z, V3f( 0, 0, 1 ), radius, vertsPerCurve, p );

	p.push_back( V3f( 0, radius, -1 ) );
	p.push_back( V3f( 0, radius, 1 ) );
	vertsPerCurve.push_back( 2 );

	p.push_back( V3f( 0, -radius, -1 ) );
	p.push_back( V3f( 0, -radius, 1 ) );
	vertsPerCurve.push_back( 2 );

	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurveData );
	curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );
	curves->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( g_lightWireframeColor ) ) );

	group->addChild( curves );

	return group;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::pointShape( float radius )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get(), 0.5f );
	addConstantShader( group.get(), false, 1 );

	IntVectorDataPtr vertsPerCurveData = new IntVectorData;
	V3fVectorDataPtr pData = new V3fVectorData;

	addCircle( Axis::Z, V3f( 0 ), radius, vertsPerCurveData->writable(), pData->writable() );

	M44f t = M44f().rotate( V3f( 0, M_PI * 0.5, 0 ) );
	for( V3f &p : pData->writable() )
	{
		p *= t;
	}

	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), /* periodic = */ false, vertsPerCurveData );
	curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );
	curves->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( g_lightWireframeColor ) ) );

	group->addChild( curves );

	return group;
}

/// \todo Expose publicly when we've decided what the
/// parameters should be.
IECoreGL::ConstRenderablePtr StandardLightVisualiser::cylinderRays( float radius )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get() );
	addConstantShader( group.get(), false, 0 );

	const int numRays = 8;
	for( int i = 0; i < numRays; ++i )
	{
		GroupPtr rayGroup = new Group;
		rayGroup->addChild( const_pointer_cast<IECoreGL::Renderable>( StandardLightVisualiser::ray() ) );

		const float angle = M_PI * 2.0f * float(i)/(float)numRays;
		M44f m;
		m.rotate( V3f( angle, 0, 0 ) );
		m.translate( V3f( 0, 0, -radius ) );

		rayGroup->setTransform( m );
		group->addChild( rayGroup );
	}

	group->setTransform( M44f().rotate( V3f( 0, M_PI / 2.0, 0 ) ) );

	return group;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::areaSpread( float spread )
{
	// Simple spaced parallel arrows that diverge by 45 degrees as spread approaches 1.

	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get(), 0.5f );
	addConstantShader( group.get() );

	IntVectorDataPtr vertsPerCurveData = new IntVectorData;
	V3fVectorDataPtr pData = new V3fVectorData;

	std::vector<int> &vpc = vertsPerCurveData->writable();
	std::vector<V3f> &p = pData->writable();

	static const float scale = 0.2f;

	const float spreadOffset = min( 1.0f, max( 0.0f, spread ) );

	// Offset the arrows from the center a little
	const V3f bl = V3f( -0.1f, -0.1f, 0.0f );
	const V3f tl = V3f( -0.1f, 0.1f, 0.0f );
	const V3f br = V3f( 0.1f, -0.1f, 0.0f );
	const V3f tr = V3f( 0.1f, 0.1f, 0.0f );

	addRay( bl, bl + scale * V3f( -spreadOffset, -spreadOffset, -1.0f ).normalized(), vpc, p );
	addRay( tl, tl + scale * V3f( -spreadOffset, spreadOffset, -1.0f ).normalized(), vpc, p );
	addRay( br, br + scale * V3f( spreadOffset, -spreadOffset, -1.0f ).normalized(), vpc, p );
	addRay( tr, tr + scale * V3f( spreadOffset, spreadOffset, -1.0f ).normalized(), vpc, p );

	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurveData );
	curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );
	curves->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( g_lightWireframeColor ) ) );

	group->addChild( curves );

	return group;
}

// Quads

IECoreGL::ConstRenderablePtr StandardLightVisualiser::quadSurface( const Imath::V2f &size, IECore::ConstDataPtr textureData, const Color3f &tint, int maxTextureResolution,  const Color3f &fallbackColor )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	if( textureData )
	{
		addTexturedConstantShader( group.get(), textureData, tint, maxTextureResolution );
	}
	else
	{
		addConstantShader( group.get(), tint, true );
	}

	IECoreGL::QuadPrimitivePtr textureQuad = new IECoreGL::QuadPrimitive( size.x, size.y );
	textureQuad->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( fallbackColor ) ) );
	group->addChild( textureQuad );

	M44f m;
	m.rotate( V3f( M_PI, 0, 0 ) );
	group->setTransform( m );

	return group;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::quadWireframe( const V2f &size )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get() );
	addConstantShader( group.get() );

	IntVectorDataPtr vertsPerCurveData = new IntVectorData;
	V3fVectorDataPtr pData = new V3fVectorData;

	vector<int> &vertsPerCurve = vertsPerCurveData->writable();
	vector<V3f> &p = pData->writable();

	vertsPerCurve.push_back( 4 );
	p.push_back( V3f( -size.x/2, -size.y/2, 0  ) );
	p.push_back( V3f( size.x/2, -size.y/2, 0  ) );
	p.push_back( V3f( size.x/2, size.y/2, 0  ) );
	p.push_back( V3f( -size.x/2, size.y/2, 0  ) );

	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), /* periodic = */ true, vertsPerCurveData );
	curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );
	curves->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( g_lightWireframeColor ) ) );

	group->addChild( curves );

	return group;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::quadPortal( const V2f &size, float visualiserScale )
{
	// Portals visualise differently as they only allow light through
	// their area. Effectively a hole cut in a big plane. We try to
	// represent this by shading outside of the quad area.

	IntVectorDataPtr vertsPerCurveData = new IntVectorData;
	V3fVectorDataPtr pData = new V3fVectorData;

	std::vector<int> &vertsPerCurve = vertsPerCurveData->writable();
	std::vector<V3f> &p = pData->writable();

	// Basic outline of the portal area

	vertsPerCurve.push_back( 4 );
	p.push_back( V3f( -size.x/2, -size.y/2, 0 ) );
	p.push_back( V3f( size.x/2, -size.y/2, 0 ) );
	p.push_back( V3f( size.x/2, size.y/2, 0 ) );
	p.push_back( V3f( -size.x/2, size.y/2, 0 ) );

	// 45 degree hatch outside the portal area (when centered at the origin)

	// Space between the lines
	const float spacing = 0.05f * visualiserScale;
	// Thickness of the shaded frame area
	const float fw = 0.25f * std::max( size.x, size.y );
	// Dimension of the shaded area
	const float dw = size.x + ( 2.0f * fw );
	const float dh = size.y + ( 2.0f * fw );

	// Working with a bottom left origin makes the maths easier for the lines
	const V3f origin( -(size.x/2)-fw, -(size.y/2)-fw, 0 );
	// Alternating line lengths creates a softer edge
	bool alt = true;

	// We iterate outwards from the bottom left corner drawing lines as we go.
	// We need different behaviour depending on whether we're overlapping the
	// portal region or not.
	const float oMax = dw + dh;
	for( float o = spacing; o < oMax; o += spacing, alt = !alt )
	{
		// extra length for alternate lines
		const float e = alt ? fw * 0.1f : 0.0f;

		if( o <= fw * 2.0f )
		{
			// A single line will do near the origin as we don't intersect the portal
			vertsPerCurve.push_back( 2 );
			p.push_back( origin + V3f( -e, o+e, 0 ) );
			p.push_back( origin + V3f( o+e, -e, 0 ) );
		}
		else if( o <= oMax - fw * 2.0f )
		{
			// We need to split either side of the central portal space
			// whilst we overlap it. As the iteration covers the maximum
			// dimension we need for non-square portals, we don't always
			// draw lines on each side.

			if( o <= dh )
			{
				// Left edge-to-frame
				vertsPerCurve.push_back( 2 );
				p.push_back( origin + V3f( -e, o+e, 0 ) );
				p.push_back( origin + V3f( fw, o-fw, 0 ) );
			}
			else if( o <= dh + size.x )
			{
				// Top edge-to-frame
				vertsPerCurve.push_back( 2 );
				p.push_back( origin + V3f( o-dh-e, dh+e, 0 ) );
				p.push_back( origin + V3f( o-dh+fw, dh-fw, 0 ) );
			}

			if( o <= dw )
			{
				// Bottom frame-to-edge
				vertsPerCurve.push_back( 2 );
				p.push_back( origin + V3f( o-fw, fw, 0 ) );
				p.push_back( origin + V3f( o+e, -e, 0 ) );
			}
			else if( o <= dw + size.y )
			{
				// Right frame-to-edge
				vertsPerCurve.push_back( 2 );
				p.push_back( origin + V3f( dw-fw, o-dw+fw, 0 ) );
				p.push_back( origin + V3f( dw+e, o-dw-e, 0 ) );
			}
		}
		else
		{
			// Single line at top-right corner
			vertsPerCurve.push_back( 2 );
			p.push_back( origin + V3f( o-dh-e, dh+e, 0 ) );
			p.push_back( origin + V3f( dw+e, dh-oMax+o-e, 0 ) );
		}
	}

	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), true, vertsPerCurveData );
	curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );
	curves->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( V3f( 0.0f ) ) ) );
	return curves;
}

// Spheres

IECoreGL::ConstRenderablePtr StandardLightVisualiser::sphereWireframe( float radius, const Vec3<bool> &axisRings, float lineWidthScale )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get(), lineWidthScale );
	addConstantShader( group.get() );

	IntVectorDataPtr vertsPerCurve = new IntVectorData;
	V3fVectorDataPtr p = new V3fVectorData;

	if( axisRings.x )
	{
		addCircle( Axis::X,  V3f( 0 ), radius, vertsPerCurve->writable(), p->writable() );
	}
	if( axisRings.y )
	{
		addCircle( Axis::Y,  V3f( 0 ), radius, vertsPerCurve->writable(), p->writable() );
	}
	if( axisRings.z )
	{
		addCircle( Axis::Z,  V3f( 0 ), radius, vertsPerCurve->writable(), p->writable() );
	}

	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, vertsPerCurve );
	curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, p ) );
	curves->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( Color3f( 1.0f, 0.835f, 0.07f ) ) ) );

	group->addChild( curves );

	return group;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::environmentSphereSurface( IECore::ConstDataPtr texture, const Color3f &tint, int maxTextureResolution, const Imath::Color3f &fallbackColor )
{
	IECoreGL::GroupPtr sphereGroup = new IECoreGL::Group();
	sphereGroup->getState()->add( new IECoreGL::DoubleSidedStateComponent( false ) );

	if( texture )
	{
		addTexturedConstantShader( sphereGroup.get(), texture, tint, maxTextureResolution );
	}
	else
	{
		addConstantShader( sphereGroup.get(), tint, true );
	}

	IECoreGL::SpherePrimitivePtr sphere = new IECoreGL::SpherePrimitive();
	sphere->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( fallbackColor ) ) );
	sphereGroup->addChild( sphere );

	Imath::M44f trans;
	trans.scale( V3f( 1, 1, -1 ) );
	trans.rotate( V3f( -0.5 * M_PI, -0.5 * M_PI, 0 ) );
	sphereGroup->setTransform( trans );

	return sphereGroup;
}

// Disk

IECoreGL::ConstRenderablePtr StandardLightVisualiser::diskSurface( float radius, IECore::ConstDataPtr textureData, const Color3f &tint, int maxTextureResolution, const Imath::Color3f &fallbackColor )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	if( textureData )
	{
		addTexturedConstantShader( group.get(), textureData, tint, maxTextureResolution );
	}
	else
	{
		addConstantShader( group.get(), tint, true );
	}

	IntVectorDataPtr vertsPerPoly = new IntVectorData;
	IntVectorDataPtr vertIds = new IntVectorData;
	V3fVectorDataPtr p = new V3fVectorData;

	addSolidArc( Axis::Z, V3f( 0 ), radius, 0, 0, 1, vertsPerPoly->writable(), vertIds->writable(), p->writable() );

	IECoreScene::MeshPrimitivePtr mesh = new IECoreScene::MeshPrimitive( vertsPerPoly, vertIds, "linear", p );
	mesh->variables["N"] = IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new V3fData( V3f( 0 ) ) );
	mesh->variables["Cs"] = IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( fallbackColor ) );
	ToGLMeshConverterPtr meshConverter = new ToGLMeshConverter( mesh );
	group->addChild( IECore::runTimeCast<IECoreGL::Renderable>( meshConverter->convert() ) );

	return group;
}

IECoreGL::ConstRenderablePtr StandardLightVisualiser::diskWireframe( float radius )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	addWireframeCurveState( group.get() );
	addConstantShader( group.get() );

	IntVectorDataPtr vertsPerCurveData = new IntVectorData;
	V3fVectorDataPtr pData = new V3fVectorData;

	addCircle( Axis::Z, V3f( 0 ), radius, vertsPerCurveData->writable(), pData->writable() );

	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), /* periodic = */ false, vertsPerCurveData );
	curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, pData ) );
	curves->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( g_lightWireframeColor ) ) );

	group->addChild( curves );

	return group;
}


