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

#include "GafferSceneUI/Private/LightVisualiserAlgo.h"

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
using namespace GafferSceneUI::Private::LightVisualiserAlgo;
using namespace IECoreGLPreview;

//////////////////////////////////////////////////////////////////////////
// Utility methods. We define these in an anonymouse namespace rather
// than clutter up the header with private methods.
//////////////////////////////////////////////////////////////////////////

namespace
{

IECore::InternedString metadataTargetForNetwork( const IECore::InternedString &attributeName, const IECoreScene::ShaderNetwork *shaderNetwork )
{
	const IECoreScene::Shader *shader = shaderNetwork->outputShader();
	return attributeName.string() + ":" + shader->getName();
}

template<typename T>
T parameter( InternedString metadataTarget, const IECore::CompoundData *parameters, InternedString parameterNameMetadata, T defaultValue )
{
	ConstStringDataPtr parameterName = Metadata::value<StringData>( metadataTarget, parameterNameMetadata );
	if( !parameterName )
	{
		return defaultValue;
	}

	using DataType = IECore::TypedData<T>;
	if( const DataType *parameterData = parameters->member<DataType>( parameterName->readable() ) )
	{
		return parameterData->readable();
	}

	return defaultValue;
}

const InternedString g_typeString( "type" );
const InternedString g_colorParameterString( "colorParameter" );
const InternedString g_tintParameterString( "tintParameter" );
const InternedString g_glVisualiserScaleString( "gl:visualiser:scale" );
const InternedString g_glLightFrustumScaleString( "gl:light:frustumScale" );
const InternedString g_glLightDrawingModeString( "gl:light:drawingMode" );
const InternedString g_glVisualiserMaxTextureResolutionString( "gl:visualiser:maxTextureResolution" );
const InternedString g_lightMuteString( "light:mute" );
const InternedString g_coneAngleParameterString( "coneAngleParameter" );
const InternedString g_radiusParameterString( "radiusParameter" );
const InternedString g_uvOrientationString( "uvOrientation" );
const InternedString g_widthParameterString( "widthParameter" );
const InternedString g_heightParameterString( "heightParameter" );
const InternedString g_portalParameterString( "portalParameter" );
const InternedString g_spreadParameterString( "spreadParameter" );
const InternedString g_lengthParameterString( "lengthParameter" );
const InternedString g_visualiserOrientationString( "visualiserOrientation" );

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
	const InternedString metadataTarget = metadataTargetForNetwork( attributeName, shaderNetwork );
	const IECore::CompoundData *shaderParameters = shaderNetwork->outputShader()->parametersData();

	ConstStringDataPtr typeData = Metadata::value<StringData>( metadataTarget, g_typeString );
	string type = typeData ? typeData->readable() : "";
	if( type == "quad" )
	{
		// Cycles and Arnold define portals via a parameter on a quad, rather having a specific light type.
		if( parameter<bool>( metadataTarget, shaderParameters, g_portalParameterString, false ) )
		{
			type = "portal";
		}
	}

	const Color3f color = parameter<Color3f>( metadataTarget, shaderParameters, g_colorParameterString, Color3f( 1.0f ) );
	const Color3f tint = parameter<Color3f>( metadataTarget, shaderParameters, g_tintParameterString, Color3f( 1.0f ) );

	const FloatData *visualiserScaleData = attributes->member<FloatData>( g_glVisualiserScaleString );
	const float visualiserScale = visualiserScaleData ? visualiserScaleData->readable() : 1.0;
	const FloatData *frustumScaleData = attributes->member<FloatData>( g_glLightFrustumScaleString );
	const float frustumScale = frustumScaleData ? frustumScaleData->readable() : 1.0;
	const StringData *visualiserDrawingModeData = attributes->member<StringData>( g_glLightDrawingModeString );
	const std::string visualiserDrawingMode = visualiserDrawingModeData ? visualiserDrawingModeData->readable() : "texture";

	const bool drawShaded = visualiserDrawingMode != "wireframe";
	const bool drawTextured = visualiserDrawingMode == "texture";

	const IntData *maxTextureResolutionData = attributes->member<IntData>( g_glVisualiserMaxTextureResolutionString );
	const int maxTextureResolution = maxTextureResolutionData ? maxTextureResolutionData->readable() : std::numeric_limits<int>::max();

	const BoolData *muteData = attributes->member<BoolData>( g_lightMuteString );
	const bool muted = muteData ? muteData->readable() : false;

	Visualisations result;

	// A shared curves primitive for ornament wireframes

	V3fVectorDataPtr ornamentWireframePoints = new V3fVectorData();
	IntVectorDataPtr ornamentWireframeVertsPerCurve = new IntVectorData();

	// UsdLux allows a shaping cone to be applied to _any_ light, so we visualise those here
	// before dealing with specific light types.

	const bool haveCone =
		type == "spot" ||
		parameter<float>( metadataTarget, shaderParameters, g_coneAngleParameterString, -1.0f ) >= 0.0f
	;
	if( haveCone )
	{
		float innerAngle, outerAngle, radius, lensRadius;
		spotlightParameters( attributeName, shaderNetwork, innerAngle, outerAngle, radius, lensRadius );
		result.push_back( Visualisation::createOrnament(
			spotlightCone( innerAngle, outerAngle, lensRadius / visualiserScale, 1.0f, 1.0f, muted ),
			/* affectsFramingBound = */ true
		) );
		result.push_back( Visualisation::createFrustum(
			spotlightCone( innerAngle, outerAngle, lensRadius / visualiserScale, 10.0f * frustumScale, 0.5f, muted ),
			Visualisation::Scale::Visualiser
		) );
	}

	// Now do visualisations based on light type.

	if( type == "environment" )
	{
		if( drawShaded )
		{
			ConstDataPtr textureData = drawTextured ? surfaceTexture( attributeName, shaderNetwork, attributes, maxTextureResolution ) : nullptr;
			result.push_back( Visualisation::createOrnament(
				environmentSphereSurface( textureData, tint, /* saturation = */ 1.f, /* gamma = */ Color3f( 1.f ), maxTextureResolution, color ),
				/* affectsFramingBound = */ true, Visualisation::ColorSpace::Scene
			) );
		}
		result.push_back( Visualisation::createOrnament(
			sphereWireframe( 1.05f, Vec3<bool>( true ), 1.0f, V3f( 0.0f ), muted ),
			/* affectsFramingBound = */ true
		) );
	}
	else if( type == "spot" )
	{
		const float radius = parameter<float>( metadataTarget, shaderParameters, g_radiusParameterString, 0.0f );
		result.push_back( Visualisation(
			sphereWireframe( radius, Vec3<bool>( false, false, true ), 0.5f, V3f( 0.0f, 0.0f, 0.1f * visualiserScale ), muted ),
			Visualisation::Scale::None
		) );
		addRay( V3f( 0 ), V3f( 0, 0, -1 ), ornamentWireframeVertsPerCurve->writable(), ornamentWireframePoints->writable() );
		result.push_back( Visualisation::createOrnament( colorIndicator( color ), /* affectsFramingBound = */ false, Visualisation::ColorSpace::Scene ) );
	}
	else if( type == "distant" )
	{
		result.push_back( Visualisation::createOrnament( distantRays( muted ), /* affectsFramingBound = */ true ) );
		result.push_back( Visualisation::createOrnament( colorIndicator( color ), /* affectsFramingBound = */ false, Visualisation::ColorSpace::Scene ) );
	}
	else if( type == "quad" )
	{
		ConstM33fDataPtr uvOrientation = Metadata::value<M33fData>( metadataTarget, g_uvOrientationString );

		const V2f size(
			parameter<float>( metadataTarget, shaderParameters, g_widthParameterString, 2.0f ),
			parameter<float>( metadataTarget, shaderParameters, g_heightParameterString, 2.0f )
		);

		if( drawShaded )
		{
			ConstDataPtr textureData = drawTextured ? surfaceTexture( attributeName, shaderNetwork, attributes, maxTextureResolution ) : nullptr;
			result.push_back( Visualisation::createGeometry(
				quadSurface( size, textureData, tint, /* saturation = */ 1.f, /* gamma = */ Color3f( 1.f ), maxTextureResolution, color, uvOrientation ? uvOrientation->readable() : M33f() ),
				Visualisation::ColorSpace::Scene
			) );
		}
		else
		{
			result.push_back( Visualisation::createOrnament( colorIndicator( color * tint ), /* affectsFramingBound = */ true, Visualisation::ColorSpace::Scene ) );
		}
		result.push_back( Visualisation::createGeometry( quadWireframe( size, 1.f, muted ) ) );

		const float spread = parameter<float>( metadataTarget, shaderParameters, g_spreadParameterString, -1 );
		if( spread >= 0.0f )
		{
			addAreaSpread( spread, ornamentWireframeVertsPerCurve->writable(), ornamentWireframePoints->writable() );
		}
		addRay( V3f( 0 ), V3f( 0, 0, -1 ), ornamentWireframeVertsPerCurve->writable(), ornamentWireframePoints->writable() );
	}
	else if( type == "portal" )
	{
		const V2f size(
			parameter<float>( metadataTarget, shaderParameters, g_widthParameterString, 1.0f ),
			parameter<float>( metadataTarget, shaderParameters, g_heightParameterString, 1.0f )
		);
		result.push_back( Visualisation::createGeometry( quadPortal( size, /* hatchingScale = */ 1.0f, muted ) ) );
		addRay( V3f( 0 ), V3f( 0, 0, -1 ), ornamentWireframeVertsPerCurve->writable(), ornamentWireframePoints->writable() );
	}
	else if( type == "disk" )
	{
		float radius = parameter<float>( metadataTarget, shaderParameters, g_widthParameterString, 2.0f ) / 2.0f;
		radius = parameter<float>( metadataTarget, shaderParameters, g_radiusParameterString, radius );

		if( drawShaded )
		{
			ConstDataPtr textureData = drawTextured ? surfaceTexture( attributeName, shaderNetwork, attributes, maxTextureResolution ) : nullptr;
			result.push_back( Visualisation::createGeometry(
				diskSurface( radius, textureData, tint, /* saturation = */ 1.f, /* gamma = */ Color3f( 1.f ), maxTextureResolution, color ),
				Visualisation::ColorSpace::Scene
			) );
		}
		else
		{
			result.push_back( Visualisation::createOrnament( colorIndicator( color * tint ), /* affectsFramingBound = */ false, Visualisation::ColorSpace::Scene ) );
		}

		result.push_back( Visualisation::createGeometry( diskWireframe( radius, 1.f, muted ) ) );
		addRay( V3f( 0 ), V3f( 0, 0, -1 ), ornamentWireframeVertsPerCurve->writable(), ornamentWireframePoints->writable() );

		const float spread = parameter<float>( metadataTarget, shaderParameters, g_spreadParameterString, -1 );
		if( spread >= 0.0f )
		{
			addAreaSpread( spread, ornamentWireframeVertsPerCurve->writable(), ornamentWireframePoints->writable() );
		}
	}
	else if( type == "cylinder" )
	{
		const float radius = parameter<float>( metadataTarget, shaderParameters, g_radiusParameterString, 1 );
		const float length = parameter<float>( metadataTarget, shaderParameters, g_lengthParameterString, 2 );
		result.push_back( Visualisation::createOrnament( cylinderRays( radius, muted ), /* affectsFramingBound = */ false ) );
		result.push_back( Visualisation::createGeometry( cylinderWireframe( radius, length, 1.f, muted ) ) );
		if( drawShaded )
		{
			result.push_back( Visualisation::createGeometry( cylinderSurface( radius, length, color * tint ), Visualisation::ColorSpace::Scene ) );
		}
		else
		{
			result.push_back( Visualisation::createOrnament( colorIndicator( color * tint ), /* affectsFramingBound = */ false, Visualisation::ColorSpace::Scene ) );
		}
	}
	else if( type == "mesh" )
	{
		// There isn't any meaningful place to draw anything for the mesh
		// light, so instead we make the mesh outline visible and light coloured.
		IECoreGL::StatePtr meshState = new IECoreGL::State( false );
		meshState->add( new IECoreGL::Primitive::DrawSolid( false ) );
		meshState->add( new IECoreGL::Primitive::DrawOutline( true ) );
		meshState->add( new IECoreGL::Primitive::OutlineWidth( 2.0f ) );
		meshState->add( new IECoreGL::OutlineColorStateComponent( lightWireframeColor4( muted ) ) );
		state = meshState;
	}
	else if( type == "photometric" )
	{
		const float radius = parameter<float>( metadataTarget, shaderParameters, g_radiusParameterString, 0 );
		if( radius > 0 )
		{
			result.push_back( Visualisation(
				sphereWireframe( radius, Vec3<bool>( true, false, true ), 0.5f, V3f( 0.0f ), muted ),
				Visualisation::Scale::None
			) );
		}
		result.push_back( Visualisation::createOrnament( colorIndicator( color ), /* affectsFramingBound = */ false, Visualisation::ColorSpace::Scene ) );
		addRay( V3f( 0 ), V3f( 0, 0, -1 ), ornamentWireframeVertsPerCurve->writable(), ornamentWireframePoints->writable() );
	}
	else
	{
		// Treat everything else as a point light.
		const float radius = parameter<float>( metadataTarget, shaderParameters, g_radiusParameterString, 0 );
		if( radius > 0 )
		{
			result.push_back( Visualisation( pointShape( radius, muted ), Visualisation::Scale::None ) );
		}

		if( !haveCone )
		{
			result.push_back( Visualisation::createOrnament( pointRays( radius / visualiserScale, muted ), /* affectsFramingBound = */ true ) );
		}
		result.push_back( Visualisation::createOrnament( colorIndicator( color ), /* affectsFramingBound = */ false, Visualisation::ColorSpace::Scene ) );
	}

	if( ornamentWireframePoints->readable().size() > 0 )
	{
		IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive( IECore::CubicBasisf::linear(), false, ornamentWireframeVertsPerCurve );
		curves->addPrimitiveVariable( "P", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Vertex, ornamentWireframePoints ) );
		curves->addPrimitiveVariable( "Cs", IECoreScene::PrimitiveVariable( IECoreScene::PrimitiveVariable::Constant, new Color3fData( lightWireframeColor( muted ) ) ) );
		result.push_back( Visualisation::createOrnament( curves, /* affectsFramingBound = */ false ) );
	}

	// Apply orientation corrective matrix if necessary.

	if( auto orientation = Metadata::value<M44fData>( metadataTarget, g_visualiserOrientationString ) )
	{
		for( auto &v : result )
		{
			IECoreGL::GroupPtr group = new IECoreGL::Group;
			group->addChild( boost::const_pointer_cast<IECoreGL::Renderable>( v.renderable ) );
			group->setTransform( orientation->readable() );
			v.renderable = group;
		}
	}

	return result;
}

IECore::DataPtr StandardLightVisualiser::surfaceTexture( const IECore::InternedString &attributeName, const IECoreScene::ShaderNetwork *shaderNetwork, const IECore::CompoundObject *attributes, int maxTextureResolution ) const
{
	const IECore::InternedString metadataTarget = metadataTargetForNetwork( attributeName, shaderNetwork );
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

	InternedString metadataTarget = metadataTargetForNetwork( attributeName, shaderNetwork );
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

	if( ConstStringDataPtr coneAngleType = Metadata::value<StringData>( metadataTarget, "coneAngleType" ) )
	{
		if( coneAngleType->readable() == "half" )
		{
			coneAngle *= 2;
		}
	}

	innerAngle = 0;
	outerAngle = 0;

	ConstStringDataPtr penumbraTypeData = Metadata::value<StringData>( metadataTarget, "penumbraType" );
	const std::string *penumbraType = penumbraTypeData ? &penumbraTypeData->readable() : nullptr;

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

	radius = parameter<float>( metadataTarget, shaderParameters, "radiusParameter", 0.0f );

}
