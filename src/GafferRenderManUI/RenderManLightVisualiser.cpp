//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Cinesite VFX Ltd. nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "GafferSceneUI/Private/LightVisualiserAlgo.h"
#include "GafferSceneUI/StandardLightVisualiser.h"

#include "IECoreGL/CurvesPrimitive.h"

#include "IECore/Spline.h"
#include "IECore/VectorTypedData.h"

using namespace Imath;
using namespace IECore;
using namespace IECoreGLPreview;
using namespace IECoreScene;
using namespace GafferSceneUI;
using namespace GafferSceneUI::Private::LightVisualiserAlgo;

namespace
{

Color3f blackbody( float kelvins )
{
	// Table borrowed from `UsdLuxBlackbodyTemperatureAsRgb()`, which in
	// turn is borrowed from Colour Rendering of Spectra by John Walker.
	static SplinefColor3f g_spline(
		CubicBasisf::catmullRom(),
		{
			{  1000.0f, Color3f( 1.000000f, 0.027490f, 0.000000f ) },
			{  1000.0f, Color3f( 1.000000f, 0.027490f, 0.000000f ) },
			{  1500.0f, Color3f( 1.000000f, 0.149664f, 0.000000f ) },
			{  2000.0f, Color3f( 1.000000f, 0.256644f, 0.008095f ) },
			{  2500.0f, Color3f( 1.000000f, 0.372033f, 0.067450f ) },
			{  3000.0f, Color3f( 1.000000f, 0.476725f, 0.153601f ) },
			{  3500.0f, Color3f( 1.000000f, 0.570376f, 0.259196f ) },
			{  4000.0f, Color3f( 1.000000f, 0.653480f, 0.377155f ) },
			{  4500.0f, Color3f( 1.000000f, 0.726878f, 0.501606f ) },
			{  5000.0f, Color3f( 1.000000f, 0.791543f, 0.628050f ) },
			{  5500.0f, Color3f( 1.000000f, 0.848462f, 0.753228f ) },
			{  6000.0f, Color3f( 1.000000f, 0.898581f, 0.874905f ) },
			{  6500.0f, Color3f( 1.000000f, 0.942771f, 0.991642f ) },
			{  7000.0f, Color3f( 0.906947f, 0.890456f, 1.000000f ) },
			{  7500.0f, Color3f( 0.828247f, 0.841838f, 1.000000f ) },
			{  8000.0f, Color3f( 0.765791f, 0.801896f, 1.000000f ) },
			{  8500.0f, Color3f( 0.715255f, 0.768579f, 1.000000f ) },
			{  9000.0f, Color3f( 0.673683f, 0.740423f, 1.000000f ) },
			{  9500.0f, Color3f( 0.638992f, 0.716359f, 1.000000f ) },
			{ 10000.0f, Color3f( 0.609681f, 0.695588f, 1.000000f ) },
			{ 10000.0f, Color3f( 0.609681f, 0.695588f, 1.000000f ) },
		}
	);

	Color3f c = g_spline( kelvins );
	c /= c.dot( V3f( 0.2126f, 0.7152f, 0.0722f ) ); // Normalise luminance
	return Color3f( std::max( c[0], 0.0f ), std::max( c[1], 0.0f ), std::max( c[2], 0.0f ) );
}

template<typename T, typename P>
T parameterOrDefault( const P *parameters, const InternedString &name, const T &defaultValue )
{
	if( const auto d = parameters->member<TypedData<T>>( name ) )
	{
		return d->readable();
	}

	return defaultValue;
}

const InternedString g_colorMapGammaParameter( "colorMapGamma" );
const InternedString g_colorMapSaturationParameter( "colorMapSaturation" );
const InternedString g_emissionFocusParameter( "emissionFocus" );
const InternedString g_enableTemperatureParameter( "enableTemperature" );
const InternedString g_glLightDrawingModeString( "gl:light:drawingMode" );
const InternedString g_glVisualiserMaxTextureResolutionString( "gl:visualiser:maxTextureResolution" );
const InternedString g_hourParameter( "hour" );
const InternedString g_latitudeParameter( "latitude" );
const InternedString g_lightColorParameter( "lightColor" );
const InternedString g_lightColorMapParameter( "lightColorMap" );
const InternedString g_lightMuteString( "mute" );
const InternedString g_temperatureParameter( "temperature" );

}  // namespace

class RenderManLightVisualiser : public LightVisualiser
{

	public :

		IE_CORE_DECLAREMEMBERPTR( RenderManLightVisualiser )

		RenderManLightVisualiser();
		~RenderManLightVisualiser() override;

		Visualisations visualise( const InternedString &attributeName, const ShaderNetwork *shaderNetwork, const CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const override;

	private :

		static LightVisualiser::LightVisualiserDescription<RenderManLightVisualiser> g_description;

};

IE_CORE_DECLAREPTR( RenderManLightVisualiser )

IECoreGLPreview::LightVisualiser::LightVisualiserDescription<RenderManLightVisualiser> RenderManLightVisualiser::g_description( "ri:light", "*" );

RenderManLightVisualiser::RenderManLightVisualiser()
{
}

RenderManLightVisualiser::~RenderManLightVisualiser()
{
}

Visualisations RenderManLightVisualiser::visualise( const InternedString &attributeName, const ShaderNetwork *shaderNetwork, const CompoundObject *attributes, IECoreGL::ConstStatePtr &state ) const
{
	const Shader *lightShader = shaderNetwork->outputShader();

	const CompoundData *lightParameters = lightShader->parametersData();

	const Color3f tempColor = parameterOrDefault<int>( lightParameters, g_enableTemperatureParameter, 0 ) ?
		blackbody( parameterOrDefault( lightParameters, g_temperatureParameter, 6500.f ) ) :
		Color3f( 1.f )
	;
	const Color3f color = parameterOrDefault( lightParameters, g_lightColorParameter, Color3f( 1.f ) ) * tempColor;
	const float saturation = parameterOrDefault( lightParameters, g_colorMapSaturationParameter, 1.f );
	// RenderMan uses a vector for the gamma, we treat it as a color
	const Color3f gamma = parameterOrDefault( lightParameters, g_colorMapGammaParameter, V3f( 1.f ) );

	const std::string visualiserDrawingMode = parameterOrDefault( attributes, g_glLightDrawingModeString, std::string( "texture" ) );

	const bool drawShaded = visualiserDrawingMode != "wireframe";
	const bool drawTextured = visualiserDrawingMode == "texture";

	const int maxTextureResolution = parameterOrDefault( attributes, g_glVisualiserMaxTextureResolutionString, std::numeric_limits<int>::max() );
	const bool muted = parameterOrDefault( attributes, g_lightMuteString, false );

	// A shared curves primitive for ornament wireframes

	V3fVectorDataPtr ornamentWireframePoints = new V3fVectorData();
	IntVectorDataPtr ornamentWireframeVertsPerCurve = new IntVectorData();

	Visualisations result;

	if( lightShader->getName() == "PxrCylinderLight" )
	{
		M44f orientation = M44f().rotate( V3f( 0.f, M_PI_2, 0.f ) );

		IECoreGL::GroupPtr rayGroup = new IECoreGL::Group;
		rayGroup->setTransform( orientation );
		rayGroup->addChild( boost::const_pointer_cast<IECoreGL::Renderable>( cylinderRays( 0.5f, muted ) ) );
		result.push_back( Visualisation::createOrnament( rayGroup, true ) );

		IECoreGL::GroupPtr wireframeGroup = new IECoreGL::Group;
		wireframeGroup->setTransform( orientation );
		wireframeGroup->addChild( boost::const_pointer_cast<IECoreGL::Renderable>( cylinderWireframe( 0.5f, 1.f, muted ) ) );
		result.push_back( Visualisation::createGeometry( wireframeGroup ) );

		IECoreGL::GroupPtr surfaceGroup = new IECoreGL::Group;
		surfaceGroup->setTransform( orientation );
		if( drawShaded )
		{
			surfaceGroup->addChild( boost::const_pointer_cast<IECoreGL::Renderable>( cylinderSurface( 0.5f, 1.f, color ) ) );
			result.push_back( Visualisation::createGeometry( surfaceGroup, Visualisation::ColorSpace::Scene ) );
		}
		else
		{
			surfaceGroup->addChild( boost::const_pointer_cast<IECoreGL::Renderable>( colorIndicator( color ) ) );
			result.push_back( Visualisation::createOrnament(
					surfaceGroup,
					false,  // affectsFramingBound
					Visualisation::ColorSpace::Scene
				)
			);
		}
	}

	else if( lightShader->getName() == "PxrDomeLight" )
	{
		if( drawShaded )
		{
			const std::string lightColorMap = drawTextured ? parameterOrDefault( lightParameters, g_lightColorMapParameter, std::string() ) : "";
			ConstDataPtr textureData = lightColorMap.empty() ? nullptr : new StringData( lightColorMap );

			result.push_back(
				Visualisation::createOrnament(
					environmentSphereSurface( textureData, color, saturation, gamma, maxTextureResolution, color ),
					true,  // affectsFramingBound
					Visualisation::ColorSpace::Scene
				)
			);
		}
		result.push_back( Visualisation::createOrnament(
			sphereWireframe( 1.05f, Vec3<bool>( true ), 1.0f, V3f( 0.0f ), muted ),
			true  // affectsFramingBound
		) );
	}

	else if( lightShader->getName() == "PxrRectLight" )
	{
		if( drawShaded )
		{
			const std::string lightColorMap = drawTextured ? parameterOrDefault( lightParameters, g_lightColorMapParameter, std::string() ) : "";
			ConstDataPtr textureData = lightColorMap.empty() ? nullptr : new StringData( lightColorMap );

			result.push_back(
				Visualisation::createGeometry(
					quadSurface( V2f( 1.f ), textureData, color, saturation, gamma, maxTextureResolution, color, M33f().scale( V2f( -1.f, -1.f ) ) ),
					Visualisation::ColorSpace::Scene
				)
			);
		}
		else
		{
			result.push_back(
				Visualisation::createOrnament( colorIndicator( color ), /* affectsFramingBound */ true, Visualisation::ColorSpace::Scene )
			);
		}
		result.push_back( Visualisation::createGeometry( quadWireframe( V2f( 1.f ), muted ) ) );

		const float focus = parameterOrDefault( lightParameters, g_emissionFocusParameter, 0.f );
		addAreaSpread( pow( 0.707f, focus ), ornamentWireframeVertsPerCurve->writable(), ornamentWireframePoints->writable() );

		addRay( V3f( 0 ), V3f( 0, 0, -1 ), ornamentWireframeVertsPerCurve->writable(), ornamentWireframePoints->writable() );
	}

	if( ornamentWireframePoints->readable().size() > 0 )
	{
		IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive(
			CubicBasisf::linear(), false, ornamentWireframeVertsPerCurve
		);
		curves->addPrimitiveVariable( "P", PrimitiveVariable( PrimitiveVariable::Vertex, ornamentWireframePoints ) );
		curves->addPrimitiveVariable(
			"Cs",
			PrimitiveVariable(
				PrimitiveVariable::Constant,
				new Color3fData( lightWireframeColor( muted ) )
			)
		);
		result.push_back( Visualisation::createOrnament( curves, /* affectsFramingBound = */ false ) );
	}

	return result;
}