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

#include "IECoreScene/MeshPrimitive.h"

#include "IECoreGL/CurvesPrimitive.h"
#include "IECoreGL/Font.h"
#include "IECoreGL/FontLoader.h"
#include "IECoreGL/MeshPrimitive.h"

#include "IECore/AngleConversion.h"
#include "IECore/Spline.h"
#include "IECore/VectorTypedData.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "Imath/ImathMatrixAlgo.h"
IECORE_POP_DEFAULT_VISIBILITY

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
	// Ideally we'd use RenderMan's `RixColorTemperature` functions to get
	// RGB from Kelvin, but that is only available for shader plugins.
	// Since we can't use that, we use the table we've used elsewhere,
	// borrowed from `UsdLuxBlackbodyTemperatureAsRgb()`, which in
	// turn is borrowed from Colour Rendering of Spectra by John Walker.
	// Color values have been converted from sRGB to ACEScg and normalized
	// on the greatest channel value.

	static SplinefColor3f g_spline(
		CubicBasisf::catmullRom(),
		{
			{  1000.0f, Color3f( 1.000000f, 0.117531f, 0.033965f ) },
			{  1000.0f, Color3f( 1.000000f, 0.117531f, 0.033965f ) },
			{  1500.0f, Color3f( 1.000000f, 0.142142f, 0.036718f ) },
			{  2000.0f, Color3f( 1.000000f, 0.188965f, 0.042816f ) },
			{  2500.0f, Color3f( 1.000000f, 0.268097f, 0.058378f ) },
			{  3000.0f, Color3f( 1.000000f, 0.364075f, 0.087632f ) },
			{  3500.0f, Color3f( 1.000000f, 0.466183f, 0.139475f ) },
			{  4000.0f, Color3f( 1.000000f, 0.566143f, 0.220068f ) },
			{  4500.0f, Color3f( 1.000000f, 0.658711f, 0.331499f ) },
			{  5000.0f, Color3f( 1.000000f, 0.741232f, 0.471858f ) },
			{  5500.0f, Color3f( 1.000000f, 0.812843f, 0.636389f ) },
			{  6000.0f, Color3f( 1.000000f, 0.873825f, 0.819128f ) },
			{  6500.0f, Color3f( 0.986339f, 0.912465f, 1.000000f ) },
			{  7000.0f, Color3f( 0.823835f, 0.797532f, 1.000000f ) },
			{  7500.0f, Color3f( 0.707631f, 0.710010f, 1.000000f ) },
			{  8000.0f, Color3f( 0.621684f, 0.641759f, 1.000000f ) },
			{  8500.0f, Color3f( 0.556315f, 0.587453f, 1.000000f ) },
			{  9000.0f, Color3f( 0.505383f, 0.543478f, 1.000000f ) },
			{  9500.0f, Color3f( 0.464866f, 0.507313f, 1.000000f ) },
			{ 10000.0f, Color3f( 0.432048f, 0.477160f, 1.000000f ) },
			{ 10000.0f, Color3f( 0.432048f, 0.477160f, 1.000000f ) },
		}
	);

	Color3f c = g_spline( kelvins );
	c /= c.dot( V3f( 0.2126f, 0.7152f, 0.0722f ) ); // Normalise luminance
	return Color3f( std::max( c[0], 0.0f ), std::max( c[1], 0.0f ), std::max( c[2], 0.0f ) );
}

template<typename T, typename P>
T parameterOrDefault( const P *parameters, const InternedString &name, const T &defaultValue )
{
	if( const auto d = parameters->template member<TypedData<T>>( name ) )
	{
		return d->readable();
	}

	return defaultValue;
}

int dayNumber( const int day, const int month, const int year )
{
	if( month == 1 )
	{
		return day;
	}
	if( month == 2 )
	{
		return day + 31;
	}

	int yearMod = 0;
	if( fmod( year, 4 ) != 0 )
	{
		yearMod = 0;
	}
	else if( fmod( year, 100 ) != 0 )
	{
		yearMod = 1;
	}
	else if( fmod( year, 400 ) != 0 )
	{
		yearMod = 0;
	}
	else
	{
		yearMod = 1;
	}
	return floor( 30.6f * month - 91.4f ) + day + 59.f + yearMod;
}
/// Returns the position of the sun on a unit sphere.
/// Based on the implementation in https://github.com/prman-pixar/RenderManForBlender
V3f sunPosition(
	const float hour,
	const int day,
	const int month,
	const int year,
	const int timeZone,
	const float longitude,
	const float latitude
)
{
	const int dayNumber = ::dayNumber( day, month, year );

	const float dayAngle = 2.f * M_PI * ( dayNumber - 81.f + ( hour - timeZone ) / 24.f ) / 365.f;
	const float timeCorrection =
		4.f * ( longitude - 15.f * timeZone ) +
		9.87f * sin( 2.f * dayAngle ) -
		7.53f * cos( dayAngle ) -
		1.5f * sin( dayAngle )
	;
	const float hourAngle = degreesToRadians( 15.f ) * ( hour + timeCorrection / 60.f - 12.f );
	const float declination = asin( sin( degreesToRadians( 23.45f ) ) * sin( dayAngle ) );
	const float latRadians = degreesToRadians( latitude );
	const float elevation = asin( sin( declination ) * sin( latRadians ) + cos( declination ) * cos( latRadians ) * cos( hourAngle ) );
	float azimuth = acos( ( sin( declination ) *  cos( latRadians ) - cos( declination ) * sin( latRadians ) * cos( hourAngle ) ) / cos( elevation ) );

	if( hourAngle > 0.f )
	{
		azimuth = 2.f * M_PI - azimuth;
	}

	return V3f(
		cos( elevation ) * sin( azimuth ),
		std::max( sin( elevation ), 0.f ),
		-cos( elevation ) * cos( azimuth )
	);
}

IECoreGL::ConstRenderablePtr triangle( const V3f &p0, const V3f &p1, const V3f &p2, const bool wireFrame )
{
	IECoreGL::GroupPtr group = new IECoreGL::Group();
	if( wireFrame )
	{
		addWireframeCurveState( group.get() );
	}

	V3fVectorDataPtr pData = new V3fVectorData( { p0, p1, p2 } );

	IECoreGL::PrimitivePtr result;
	if( wireFrame )
	{
		IntVectorDataPtr vertsPerCurveData = new IntVectorData( { 3 } );
		result = new IECoreGL::CurvesPrimitive(
			CubicBasisf::linear(), /* periodic = */ true, vertsPerCurveData
		);
	}
	else
	{
		result = new IECoreGL::MeshPrimitive( 1 );
		const V3f n( ( p2 - p1 ).cross( p0 - p1 ).normalized() );
		V3fVectorDataPtr nData = new V3fVectorData( { n, n, n } );
		nData->setInterpretation( GeometricData::Interpretation::Normal );
		result->addPrimitiveVariable( "N", PrimitiveVariable( PrimitiveVariable::FaceVarying, nData ) );
	}
	result->addPrimitiveVariable( "P", PrimitiveVariable( PrimitiveVariable::FaceVarying, pData ) );

	group->addChild( result );

	return group;
}

IECoreGL::ConstRenderablePtr sunWireframe( const float radius )
{
	const int numSpikes = 12;
	const int pointsPerSpike = 7;
	const float innerRadius = 0.1f * radius;
	const float outerRadius = 0.15f * radius;

	std::vector<V3f> p;
	p.reserve( numSpikes * ( pointsPerSpike + 1 ) );

	for( int i = 0; i < numSpikes; ++i )
	{
		const float startAngle = 2 * M_PI * ( (float)i / (float)numSpikes );
		const float segmentInterval = 2 * M_PI / ( (float)numSpikes * (float)( pointsPerSpike - 1 ) );

		const float peakAngle = startAngle + segmentInterval * ( (float)( pointsPerSpike - 1 ) * 0.5f );
		p.push_back( V3f( 0, cos( peakAngle ), sin( peakAngle ) ) * outerRadius );

		for( int j = 0; j < pointsPerSpike; ++j )
		{
			const float angle = startAngle + segmentInterval * (float)j;
			p.push_back( V3f( 0, cos( angle ), sin( angle ) ) * innerRadius );
		}
	}

	IntVectorDataPtr vertsPerCurveData = new IntVectorData( std::vector<int>( numSpikes, pointsPerSpike + 1 ) );
	IECoreGL::CurvesPrimitivePtr curves = new IECoreGL::CurvesPrimitive(
		CubicBasisf::linear(), /* periodic = */ true, vertsPerCurveData
	);

	V3fVectorDataPtr pData = new V3fVectorData( p );
	curves->addPrimitiveVariable( "P", PrimitiveVariable( PrimitiveVariable::FaceVarying, pData ) );

	IECoreGL::GroupPtr result = new IECoreGL::Group();
	addWireframeCurveState( result.get() );
	result->addChild( curves );

	return result;
}

IECoreGL::ConstRenderablePtr sunSurface( const float radius )
{
	const int numSpikes = 12;
	const int pointsPerSpike = 7;
	const float numTriangles = numSpikes * ( pointsPerSpike - 1 );
	const float innerRadius = 0.1f * radius;
	const float outerRadius = 0.15f * radius;

	std::vector<V3f> p;
	p.reserve( numTriangles * 3 );

	for( int i = 0; i < numSpikes; ++i )
	{
		const float startAngle = 2 * M_PI * ( (float)i / (float)numSpikes );
		const float segmentInterval = 2 * M_PI / ( (float)numSpikes * (float)( pointsPerSpike - 1 ) );

		const float peakAngle = startAngle + segmentInterval * ( (float)( pointsPerSpike - 1 ) * 0.5f );

		for( int j = 0, eJ = pointsPerSpike - 1; j < eJ; ++j )
		{
			const float angle0 = startAngle + segmentInterval * (float)j;
			const float angle1 = startAngle + segmentInterval * (float)( j + 1 );
			p.push_back( V3f( 0, cos( peakAngle ), sin( peakAngle ) ) * outerRadius );
			p.push_back( V3f( 0, cos( angle0 ), sin( angle0 ) ) * innerRadius );
			p.push_back( V3f( 0, cos( angle1 ), sin( angle1 ) ) * innerRadius );
		}
	}

	IECoreGL::MeshPrimitivePtr mesh = new IECoreGL::MeshPrimitive( numTriangles );

	V3fVectorDataPtr pData = new V3fVectorData( p );
	mesh->addPrimitiveVariable( "P", PrimitiveVariable( PrimitiveVariable::FaceVarying, pData ) );

	V3fVectorDataPtr nData = new V3fVectorData( std::vector<V3f>( numTriangles * 3, V3f( 1.f, 0.f, 0.f ) ) );
	nData->setInterpretation( GeometricData::Interpretation::Normal );
	mesh->addPrimitiveVariable( "N", PrimitiveVariable( PrimitiveVariable::FaceVarying, nData ) );

	IECoreGL::GroupPtr result = new IECoreGL::Group();
	result->addChild( mesh );

	return result;
}

const InternedString g_colorMapGammaParameter( "colorMapGamma" );
const InternedString g_colorMapSaturationParameter( "colorMapSaturation" );
const InternedString g_dayParameter( "day" );
const InternedString g_emissionFocusParameter( "emissionFocus" );
const InternedString g_enableTemperatureParameter( "enableTemperature" );
const InternedString g_glLightDrawingModeString( "gl:light:drawingMode" );
const InternedString g_glVisualiserMaxTextureResolutionString( "gl:visualiser:maxTextureResolution" );
const InternedString g_hourParameter( "hour" );
const InternedString g_latitudeParameter( "latitude" );
const InternedString g_lightColorParameter( "lightColor" );
const InternedString g_lightColorMapParameter( "lightColorMap" );
const InternedString g_lightMuteString( "mute" );
const InternedString g_longitudeParameter( "longitude" );
const InternedString g_monthParameter( "month" );
const InternedString g_sunDirectionParameter( "sunDirection" );
const InternedString g_sunTintParameter( "sunTint" );
const InternedString g_temperatureParameter( "temperature" );
const InternedString g_yearParameter( "year" );
const InternedString g_zoneParameter( "zone" );

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

	else if( lightShader->getName() == "PxrDiskLight" )
	{
		if( drawShaded )
		{
			result.push_back(
				Visualisation::createGeometry(
					diskSurface( 0.5f, /* textureData = */ nullptr, color, /* saturation = */ 1.f, /* gamma = */ Color3f( 1.f ), maxTextureResolution, Color3f( 1.f ) ),
					Visualisation::ColorSpace::Scene
				)
			);
		}
		else
		{
			result.push_back(
				Visualisation::createOrnament(
					colorIndicator( color ),
					false,  // affectsFramingBounds
					Visualisation::ColorSpace::Scene
				)
			);
		}

		result.push_back(
			Visualisation::createGeometry( diskWireframe( 0.5f, muted ) )
		);

		const float focus = parameterOrDefault( lightParameters, g_emissionFocusParameter, 0.f );
		addAreaSpread( pow( 0.707f, focus ), ornamentWireframeVertsPerCurve->writable(), ornamentWireframePoints->writable() );

		addRay( V3f( 0.f ), V3f( 0.f, 0.f, -1.f ), ornamentWireframeVertsPerCurve->writable(), ornamentWireframePoints->writable() );
	}

	else if( lightShader->getName() == "PxrDistantLight" )
	{
		result.push_back( Visualisation::createOrnament( distantRays( muted ), /* affectsFramingBouds = */ true ) );
		result.push_back( Visualisation::createOrnament( colorIndicator( color ), /* affectsFramingBounds = */ false, Visualisation::ColorSpace::Scene ) );
	}

	else if( lightShader->getName() == "PxrDomeLight" )
	{
		if( drawShaded )
		{
			const std::string lightColorMap = drawTextured ? parameterOrDefault( lightParameters, g_lightColorMapParameter, std::string() ) : "";
			ConstDataPtr textureData = lightColorMap.empty() ? nullptr : new StringData( lightColorMap );

			result.push_back(
				Visualisation::createOrnament(
					environmentSphereSurface( textureData, color, saturation, gamma, maxTextureResolution, Color3f( 1.f ) ),
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

	else if ( lightShader->getName() == "PxrEnvDayLight" )
	{
		ConstCompoundObjectPtr emptyParameters = new CompoundObject();
		const float compassScale = 5.f;

		V3f sunPosition;

		const int monthParameter = parameterOrDefault( lightParameters, g_monthParameter, 11 );
		if( monthParameter != 0 )
		{
			IECoreGL::GroupPtr compassGroup = new IECoreGL::Group();
			// The `LightVisualiserAlgo::constantShader()` applies a tint to the color, which makes
			// for a muddled color when selected if the tint is set to the light color. Instead we
			// set the tint to `1.0` and set the color on the group.
			addConstantShader( compassGroup.get(), Color3f( 1.f ) );
			compassGroup->getState()->add( new IECoreGL::Color( lightWireframeColor4( muted ) ), /* override = */ true );

			static IECoreGL::FontPtr compassFont = IECoreGL::FontLoader::defaultFontLoader()->load( "VeraBd.ttf" );
			IECoreGL::GroupPtr compassLabelGroup = new IECoreGL::Group();

			IECoreGL::ConstMeshPrimitivePtr nLabel = compassFont->mesh( 'N' );
			compassLabelGroup->addChild( boost::const_pointer_cast<IECoreGL::MeshPrimitive>( nLabel ) );
			compassLabelGroup->setTransform(
				M44f().translate( V3f( -nLabel->bound().center().x, 2.4f, 0.f ) ) *
				M44f().rotate( V3f( -M_PI_2, 0.f, 0.f ) ) *
				M44f().scale( V3f( compassScale * .25f ) )
			);
			compassGroup->addChild( compassLabelGroup );

			compassGroup->addChild(
				boost::const_pointer_cast<IECoreGL::Renderable>(
					triangle(
						V3f( compassScale * -0.1f, 0.f, 0.f ),
						V3f( compassScale * 0.1f, 0.f, 0.f ),
						V3f( 0.f, 0.f, -compassScale * 0.5f ),
						false  // Wireframe
					)
				)
			);
			compassGroup->addChild(
				boost::const_pointer_cast<IECoreGL::Renderable>(
					triangle(
						V3f( compassScale * 0.1f, 0.f, 0.f ),
						V3f( compassScale * -0.1f, 0.f, 0.f ),
						V3f( 0.f, 0.f, compassScale * 0.5f ),
						true  // Wireframe
					)
				)
			);

			result.push_back( Visualisation::createOrnament( compassGroup, /* affectsFramingBounds = */ true, Visualisation::ColorSpace::Display ) );

			sunPosition = ::sunPosition(
				parameterOrDefault( lightParameters, g_hourParameter, 14.633333f ),
				parameterOrDefault( lightParameters, g_dayParameter, 20 ),
				monthParameter,
				parameterOrDefault( lightParameters, g_yearParameter, 2014 ),
				parameterOrDefault( lightParameters, g_zoneParameter, -8 ),
				parameterOrDefault( lightParameters, g_longitudeParameter, -122.3318f ),
				parameterOrDefault( lightParameters, g_latitudeParameter, 47.6019f )
			);
		}
		else
		{
			sunPosition = parameterOrDefault(
				lightParameters,
				g_sunDirectionParameter,
				V3f( 0.f, 1.f, 0.f )
			).normalized() * M44f().rotate( V3f( -M_PI_2, 0.f, 0.f ) );
		}

		IECoreGL::GroupPtr raysGroup = new IECoreGL::Group();
		raysGroup->addChild( boost::const_pointer_cast<IECoreGL::Renderable>( distantRays( muted ) ) );
		M44f rayTransform;
		alignZAxisWithTargetDir( rayTransform, sunPosition, V3f( 0.f, 1.f, 0.f ) );
		rayTransform.translate( V3f( 0.f, 0.f, compassScale - 1.f ) );
		raysGroup->setTransform( rayTransform );
		result.push_back( Visualisation::createOrnament( raysGroup, /* affectsFramingBounds = */ true, Visualisation::ColorSpace::Display ) );

		IECoreGL::GroupPtr tintIndicatorGroup = new IECoreGL::Group();
		tintIndicatorGroup->addChild(
			boost::const_pointer_cast<IECoreGL::Renderable>(
				colorIndicator( parameterOrDefault( lightParameters, g_sunTintParameter, Color3f( 1.f ) ) )
			)
		);
		tintIndicatorGroup->setTransform( M44f().scale( V3f( drawShaded ? compassScale : 1.f ) ) * M44f().translate( sunPosition * compassScale ) );
		result.push_back(
			Visualisation::createOrnament(
				tintIndicatorGroup,
				true,  //affectsFramingBound
				Visualisation::ColorSpace::Scene
			)
		);

		IECoreGL::GroupPtr sunIndicatorGroup = new IECoreGL::Group();
		// The `LightVisualiserAlgo::constantShader()` applies a tint to the color, which makes
		// for a muddled color when selected if the tint is set to the light color. Instead we
		// set the tint to `1.0` and set the color on the group.
		addConstantShader( sunIndicatorGroup.get(), Color3f( 1.f ), 1 );
		sunIndicatorGroup->getState()->add( new IECoreGL::Color( lightWireframeColor4( muted ) ), /* override = */ true );
		if( drawShaded )
		{
			sunIndicatorGroup->addChild( boost::const_pointer_cast<IECoreGL::Renderable>( sunSurface( compassScale ) ) );
		}
		else
		{
			sunIndicatorGroup->addChild( boost::const_pointer_cast<IECoreGL::Renderable>( sunWireframe( compassScale ) ) );
		}
		sunIndicatorGroup->setTransform( M44f().translate( sunPosition * compassScale ) );
		result.push_back(
			Visualisation::createOrnament(
				sunIndicatorGroup,
				true,  // affects FramingBound
				Visualisation::ColorSpace::Display
			)
		);
	}

	else if( lightShader->getName() == "PxrMeshLight" )
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

	else if( lightShader->getName() == "PxrRectLight" )
	{
		if( drawShaded )
		{
			const std::string lightColorMap = drawTextured ? parameterOrDefault( lightParameters, g_lightColorMapParameter, std::string() ) : "";
			ConstDataPtr textureData = lightColorMap.empty() ? nullptr : new StringData( lightColorMap );

			result.push_back(
				Visualisation::createGeometry(
					quadSurface( V2f( 1.f ), textureData, color, saturation, gamma, maxTextureResolution, Color3f( 1.f ), M33f().scale( V2f( -1.f, -1.f ) ) ),
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