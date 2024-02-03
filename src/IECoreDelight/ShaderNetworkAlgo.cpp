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

#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "IECoreDelight/ParameterList.h"
#include "IECoreDelight/ShaderNetworkAlgo.h"

#include "IECoreScene/ShaderNetworkAlgo.h"

#include "IECore/MessageHandler.h"
#include "IECore/SearchPath.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/SplineData.h"
#include "IECore/VectorTypedData.h"

#include "OSL/oslquery.h"
// Don't let windows.h smash over IECore::SearchPath via a macro
#ifdef SearchPath
#undef SearchPath
#endif

#include "boost/algorithm/string/predicate.hpp"

using namespace Imath;
using namespace IECore;
using namespace IECoreScene;

namespace
{

/////////////////////////////////////////////////////////////////////////
// LRUCache of OSLQueries
//////////////////////////////////////////////////////////////////////////

using OSLQueryPtr = std::shared_ptr<OSL::OSLQuery>;
using QueryCache = IECorePreview::LRUCache<std::string, OSLQueryPtr, IECorePreview::LRUCachePolicy::Parallel>;

QueryCache &queryCache()
{
	static QueryCache g_cache(
		[] ( const std::string &shaderName, size_t &cost, const IECore::Canceller *canceller ) -> OSLQueryPtr {
			const char *searchPath = getenv( "OSL_SHADER_PATHS" );
			OSLQueryPtr query = std::make_shared<OSL::OSLQuery>();
			cost = 1;
			if( !query->open( shaderName, searchPath ? searchPath : "" ) )
			{
				return nullptr;
			}
			return query;
		},
		10000
	);
	return g_cache;
}

}  // namespace

namespace
{

// From https://gitlab.com/3Delight/3delight-for-houdini/-/blob/master/osl_utilities.cpp
enum BasisTypes
{
	CONSTANT,
	LINEAR,
	MONOTONECUBIC,
	CATMULLROM
};

int basisInt( const std::string &basis )
{
	if( basis == "constant" )
	{
		return BasisTypes::CONSTANT;
	}
	if( basis == "linear" )
	{
		return BasisTypes::LINEAR;
	}
	// `SplinePlug` converts from `monotonecubic` to `bezier`, so we'll never get `monotonecubic`

	return BasisTypes::CATMULLROM;
}

const OSL::OSLQuery::Parameter *splineValueParameter(
	const OSL::OSLQuery &query,
	const std::string &splineParameterName
)
{
	for( size_t i = 0, eI = query.nparams(); i < eI; ++i )
	{
		const OSL::OSLQuery::Parameter *p = query.getparam( i );

		if( !boost::starts_with( p->name, splineParameterName ) )
		{
			continue;
		}
		for( const auto &m : p->metadata )
		{
			if(
				m.name == "widget" &&
				m.sdefault.size() > 0 &&
				m.sdefault[0].find( "Ramp" ) != std::string::npos
			)
			{
				return p;
			}
		}
	}
	return nullptr;
}

bool find3DelightSplineParameters(
	const OSL::OSLQuery &query,
	const std::string &splineParameterName,
	const OSL::OSLQuery::Parameter * &positionsParameter,
	const OSL::OSLQuery::Parameter * &valuesParameter,
	const OSL::OSLQuery::Parameter * &basisParameter
)
{
	positionsParameter = nullptr;
	valuesParameter = nullptr;
	basisParameter = nullptr;

	valuesParameter = splineValueParameter( query, splineParameterName );

	if( valuesParameter )
	{
		for( size_t i = 0, eI = query.nparams(); i < eI; ++i )
		{
			const OSL::OSLQuery::Parameter *p = query.getparam( i );
			if( p == valuesParameter || !p->type.is_array() || !boost::starts_with( p->name, splineParameterName ) )
			{
				continue;
			}
			if( p->type.basetype == OSL::TypeDesc::INT && p->type.aggregate == OSL::TypeDesc::SCALAR )
			{
				// Here we prefer the `int` value basis parameter because that is the only
				// basis parameter that is consistently found in all 3delight splines.
				basisParameter = p;
			}
			if( p->type.basetype == OSL::TypeDesc::FLOAT && p->type.aggregate == OSL::TypeDesc::SCALAR )
			{
				positionsParameter = p;
			}
		}
	}

	return positionsParameter && valuesParameter && basisParameter;
}

void renameSplineParameters( ShaderNetwork *shaderNetwork )
{
	for( const auto &[handle, oldShader] : shaderNetwork->shaders() )
	{
		ShaderPtr shader = oldShader->copy();

		if( OSLQueryPtr query = queryCache().get( shader->getName() ) )
		{
			for( const auto &[name, value] : oldShader->parameters() )
			{
				InternedString newName = name;
				DataPtr newValue = value;

				const std::string &parameterName = name.string();
				if(
					boost::ends_with( parameterName, "Positions" ) ||
					boost::ends_with( parameterName, "Values" ) ||
					boost::ends_with( parameterName, "Basis" )
				)
				{
					std::string splineParameterName;

					if( boost::ends_with( parameterName, "Positions" ) )
					{
						splineParameterName = parameterName.substr( 0, parameterName.size() - 9 );
					}
					else if( boost::ends_with( parameterName, "Values" ) )
					{
						splineParameterName = parameterName.substr( 0, parameterName.size() - 6 );
					}
					else
					{
						splineParameterName = parameterName.substr( 0, parameterName.size() - 5 );
					}

					const OSL::OSLQuery::Parameter *positionsParameter;
					const OSL::OSLQuery::Parameter *valuesParameter;
					const OSL::OSLQuery::Parameter *basisParameter;

					if( find3DelightSplineParameters(
							*query,
							splineParameterName,
							positionsParameter,
							valuesParameter,
							basisParameter
						)
					)
					{
						if( name == splineParameterName + "Positions" )
						{
							newName = positionsParameter->name.string();
						}
						else if( name == splineParameterName + "Values" )
						{
							newName = valuesParameter->name.string();
						}
						else if( boost::ends_with( parameterName, "Basis" ) )
						{
							auto positionData = oldShader->parametersData()->member<const FloatVectorData>( splineParameterName + "Positions" );
							auto basisData = runTimeCast<const StringData>( value );

							if( positionData && basisData )
							{
								newName = basisParameter->name.string();
								newValue = new IntVectorData(
									std::vector<int>( positionData->readable().size(), basisInt( basisData->readable() ) )
								);
							}
						}
						shader->parameters().erase( name );
					}
				}
				shader->parameters()[newName] = newValue;
			}
		}

		shaderNetwork->setShader( handle, shader.get() );
	}
}

const InternedString g_uvCoordParameterName( "uvCoord" );
const std::string g_uvCoordNodeName = "__uvCoordsDefault";
const std::string g_uvCoordShaderName = "uvCoord";
const InternedString g_uvCoordOutputParameter( "o_outUV" );

void addDefaultUVShader( ShaderNetwork *shaderNetwork )
{
	InternedString uvCoordHandle;

	for( const auto &[handle, shader] : shaderNetwork->shaders() )
	{
		auto it = shader->parameters().find( g_uvCoordParameterName );
		if(
			it != shader->parameters().end() &&
			!shaderNetwork->input( ShaderNetwork::Parameter( handle, g_uvCoordParameterName) )
		)
		{
			if( uvCoordHandle.string().empty() )
			{
				ShaderPtr uvCoordShader = new Shader( g_uvCoordShaderName, "osl:shader" );
				uvCoordHandle = shaderNetwork->addShader( g_uvCoordNodeName, std::move( uvCoordShader ) );
			}
			shaderNetwork->addConnection(
				ShaderNetwork::Connection(
					ShaderNetwork::Parameter( uvCoordHandle, g_uvCoordOutputParameter ),
					ShaderNetwork::Parameter( handle, g_uvCoordParameterName )
				)
			);
		}
	}
}

/// \todo This is almost identical (maybe should be completely identical)
/// to `IECoreArnold::ShaderNetworkAlgo::parameterValue`. Should that get
/// pulled out to a common location?
template<typename T>
T parameterValue( const Shader *shader, InternedString parameterName, const T &defaultValue )
{
	if( auto d = shader->parametersData()->member<TypedData<T>>( parameterName ) )
	{
		return d->readable();
	}

	if constexpr( std::is_same_v<std::remove_cv_t<T>, Color3f> )
	{
		// Correction for USD files which author `float3` instead of `color3f`.
		// See `ShaderNetworkAlgoTest.testConvertUSDFloat3ToColor3f()`.
		if( auto d = shader->parametersData()->member<V3fData>( parameterName ) )
		{
			return d->readable();
		}
		/// \todo Do we need the corresponding conversion of Color4 from `IECoreArnold::ShaderNetworkAlgo::parameterValue`?
	}

	else if constexpr( std::is_same_v<std::remove_cv_t<T>, std::string> )
	{
		// Support for USD `token`, which will be loaded as `InternedString`, but which
		// we want to translate to `string`.
		if( auto d = shader->parametersData()->member<InternedStringData>( parameterName ) )
		{
			return d->readable().string();
		}
	}

	return defaultValue;
}

//////////////////////////////////////////////////////////////////////////
// USD conversion code
//////////////////////////////////////////////////////////////////////////

// Traits class to handle the GeometricTypedData fiasco.
template<typename T>
struct DataTraits
{

	using DataType = IECore::TypedData<T>;

};

template<typename T>
struct DataTraits<Vec2<T> >
{

	using DataType = IECore::GeometricTypedData<Vec2<T>>;

};

template<typename T>
struct DataTraits<Vec3<T> >
{

	using DataType = IECore::GeometricTypedData<Vec3<T>>;

};

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

const InternedString g_angleParameter( "angle" );
const InternedString g_aParameter( "a" );
const InternedString g_bParameter( "b" );
const InternedString g_colorParameter( "color" );
const InternedString g_colorTemperatureParameter( "colorTemperature" );
const InternedString g_coneAngleParameter( "coneAngle" );
const InternedString g_penumbraAngleParameter( "penumbraAngle" );
const InternedString g_diffuseParameter( "diffuse" );
const InternedString g_enableColorTemperatureParameter( "enableColorTemperature" );
const InternedString g_exposureParameter( "exposure" );
const InternedString g_gParameter( "g" );
const InternedString g_heightParameter( "height" );
const InternedString g_intensityParameter( "intensity" );
const InternedString g_lengthParameter ("length" );
const InternedString g_radiusParameter( "radius" );
const InternedString g_multiplyColorParameter( "b" );
const InternedString g_multiplyInputParameter( "a" );
const InternedString g_multiplyOutputParameter( "out" );
const InternedString g_normalizeParameter( "normalize" );
const InternedString g_rParameter( "r" );
const InternedString g_shapingConeAngleParameter( "shaping:cone:angle" );
const InternedString g_shapingConeSoftnessParameter( "shaping:cone:softness" );
const InternedString g_specularParameter( "specular" );
const InternedString g_textureFileParameter( "texture:file" );
const InternedString g_textureFormatParameter( "texture:format" );
const InternedString g_textureOutputParameter( "outColor" );
const InternedString g_widthParameter( "width" );

const InternedString g_dlColorParameter( "i_color" );
const InternedString g_dlDiffuseParameter( "diffuse_contribution" );
const InternedString g_dlEnvironmentTextureFileParameter( "image" );
const InternedString g_dlEnvironmentTextureFormatParameter( "mapping" );
const InternedString g_dlEnvSpecularParameter( "specular_contribution" );
const InternedString g_dlNormalizeParameter( "normalize_area" );
const InternedString g_dlSpecularParameter( "reflection_contribution" );
const InternedString g_dlTextureFileParameter( "textureFile" );

const float g_defaultAngle = 0.53f;
const float g_defaultLength = 1.f;
const float g_defaultWidth = 1.f;
const float g_defaultHeight = 1.f;
const float g_defaultRadius = 0.5f;

const std::map<std::string, int> g_textureMappingModes{ { "latlong", 0 }, { "angular", 1 } };

template<typename T>
void transferUSDParameter( ShaderNetwork *network, InternedString shaderHandle, const Shader *usdShader, InternedString usdName, Shader *shader, InternedString name, const T &defaultValue )
{
	shader->parameters()[name] = new typename DataTraits<T>::DataType( parameterValue( usdShader, usdName, defaultValue ) );

	if( ShaderNetwork::Parameter input = network->input( { shaderHandle, usdName } ) )
	{
		network->addConnection( { input, { shaderHandle, name } } );
		network->removeConnection( { input, { shaderHandle, usdName } } );
	}
}

void transferUSDLightParameters( ShaderNetwork *network, InternedString shaderHandle, const Shader *usdShader, Shader *shader )
{
	Color3f color = parameterValue( usdShader, g_colorParameter, Color3f( 1 ) );
	if( parameterValue( usdShader, g_enableColorTemperatureParameter, false ) )
	{
		color *= blackbody( parameterValue( usdShader, g_colorTemperatureParameter, 6500.f ) );
	}
	shader->parameters()[g_dlColorParameter] = new Color3fData( color );

	transferUSDParameter( network, shaderHandle, usdShader, g_diffuseParameter, shader, g_dlDiffuseParameter, 1.f );
	transferUSDParameter( network, shaderHandle, usdShader, g_exposureParameter, shader, g_exposureParameter, 0.f );
	transferUSDParameter( network, shaderHandle, usdShader, g_intensityParameter, shader, g_intensityParameter, 1.f );

	transferUSDParameter(
		network,
		shaderHandle,
		usdShader,
		g_specularParameter,
		shader,
		shader->getName() != "environmentLight" ? g_dlSpecularParameter : g_dlEnvSpecularParameter,
		1.f
	);
}

void transferUSDShapingParameters( ShaderNetwork *network, InternedString shaderHandle, const Shader *usdShader, Shader *shader )
{
	if( auto d = usdShader->parametersData()->member<FloatData>( g_shapingConeAngleParameter) )
	{
		shader->setName( "spotLight" );
		// USD docs don't currently specify any semantics for `shaping:cone:softness`, but we assume
		// the semantics documented for RenderMan's PxrSphereLight, where it's basically specifying
		// a penumbra as a 0-1 proportion of the cone. Relevant conversations on usd-interest :
		//
		// - https://groups.google.com/u/1/g/usd-interest/c/A6bc4OZjSB0/m/hwUL7Wf1AwAJ, in
		//   which the opportunity to define semantics is declined.
		// - https://groups.google.com/u/1/g/usd-interest/c/Ybe4aroAKbc/m/0Ui3DKMyCgAJ, in
		//   which folks take their best guess.
		// 3Delight treats the penumbra angle as an outset penumbra, expanding the total cone coverage.
		// PxrSphereLight appears to treat it as inset, so the cone angle is still the angle at which
		// light intensity reaches zero.
		const float halfConeAngle = d->readable();
		const float softness = parameterValue( usdShader, g_shapingConeSoftnessParameter, 0.f );
		if( softness > 1.0 )
		{
			// Houdini apparently has (or had?) its own interpretation of softness, with the "bar scene"
			// containing lights with an angle of 20 degrees and a softness of 60! We have no idea how
			// to interpret that, so punt for now.
			/// \todo Hopefully things get more standardised and we can remove this, because the RenderMan
			/// docs do imply that values above one are allowed.
			IECore::msg( IECore::Msg::Warning, "transferUSDShapingParameters", "Ignoring `shaping:cone:softness` as it is greater than 1" );
		}
		else
		{
			const float penumbraAngle = softness * halfConeAngle;
			shader->parameters()[g_coneAngleParameter] = new FloatData( ( halfConeAngle * 2.f ) - ( penumbraAngle * 2.f ) );
			shader->parameters()[g_penumbraAngleParameter] = new FloatData( penumbraAngle );
		}
	}
}

void replaceUSDShader( ShaderNetwork *network, InternedString handle, ShaderPtr &&newShader )
{
	// Replace original shader with the new.
	network->setShader( handle, std::move( newShader ) );

	// Iterating over a copy because we will modify the range during iteration
	ShaderNetwork::ConnectionRange range = network->outputConnections( handle );
	std::vector<ShaderNetwork::Connection> outputConnections( range.begin(), range.end() );
	for( auto &c : outputConnections )
	{
		if( c.source.name != g_rParameter && c.source.name != g_gParameter && c.source.name != g_bParameter && c.source.name != g_aParameter )
		{
			network->removeConnection( c );
			c.source.name = InternedString();
			network->addConnection( c );
		}
	}
}

void cylinderStatic(
	std::vector<int> &vertsPerPoly,
	std::vector<int> &vertIds,
	std::vector<V3f> &n,
	std::vector<int> &nIds
)
{
	const int numSegments = 100;
	vertsPerPoly.reserve( numSegments * 3 );
	vertIds.reserve( numSegments * 10 );
	n.reserve( numSegments + 2 );
	nIds.reserve( numSegments * 10 );

	// sides
	for( int i = 0; i < numSegments + 1; ++i )
	{
		const float a = ( (float)i / (float)numSegments ) * 2.f * M_PI;

		const float z = sin( a ) ;
		const float y = cos( a );

		n.push_back( V3f( 0, y, z ) );
	}
	for( int i = 0; i < numSegments; ++i )
	{
		vertIds.push_back( i * 2 );
		vertIds.push_back( i * 2 + 1 );
		vertIds.push_back( i * 2 + 3 );
		vertIds.push_back( i * 2 + 2 );

		nIds.push_back( i );
		nIds.push_back( i );
		nIds.push_back( i + 1 );
		nIds.push_back( i + 1 );

		vertsPerPoly.push_back( 4 );
	}

	// end caps
	n.push_back( V3f( 1, 0, 0 ) );
	n.push_back( V3f( -1, 0, 0 ) );

	for( int i = 0; i < numSegments; ++i )
	{
		vertIds.push_back( numSegments + 1 );
		vertIds.push_back( i * 2 );
		vertIds.push_back( i * 2 + 2 );

		nIds.push_back( numSegments + 1 );
		nIds.push_back( numSegments + 1 );
		nIds.push_back( numSegments + 1 );

		vertsPerPoly.push_back( 3 );

		vertIds.push_back( numSegments + 2 );
		vertIds.push_back( i * 2 + 3 );
		vertIds.push_back( i * 2 + 1 );

		nIds.push_back( numSegments + 2 );
		nIds.push_back( numSegments + 2 );
		nIds.push_back( numSegments + 2 );

		vertsPerPoly.push_back( 3 );
	}
}

void cylinderP( const float radius, const float length, std::vector<V3f> &p )
{
	const int numSegments = 100;
	p.reserve( numSegments * 2 + 2 );

	const float halfLength = length * 0.5;

	// sides
	for( int i = 0; i < numSegments + 1; ++i )
	{
		const float a = ( (float)i / (float)numSegments ) * 2.f * M_PI;

		const float z = sin( a ) * radius;
		const float y = cos( a ) * radius;

		p.push_back( V3f( halfLength, y, z ) );  // Length along the X-axis
		p.push_back( V3f( -halfLength, y, z ) );
	}

	// end caps
	p.push_back( V3f( halfLength, 0, 0 ) );
	p.push_back( V3f( -halfLength, 0, 0 ) );
}

const std::unordered_map<std::string, std::string> g_shaderNameMap{
	{ "SphereLight", "pointLight" },
	{ "RectLight", "areaLight" },
	{ "DiskLight", "areaLight" },
	{ "DistantLight", "distantLight" },
	{ "DomeLight", "environmentLight" },
	{ "CylinderLight", "areaLight" }
};

}  // namespace

namespace IECoreDelight
{

namespace ShaderNetworkAlgo
{

void convertUSDShaders( ShaderNetwork *shaderNetwork )
{
	for( const auto &[handle, shader] : shaderNetwork->shaders() )
	{
		ShaderPtr newShader;
		const auto it = g_shaderNameMap.find( shader->getName() );
		if( it != g_shaderNameMap.end() )
		{
			newShader = new Shader( it->second, "osl:light" );
		}

		if( newShader )
		{
			transferUSDLightParameters( shaderNetwork, handle, shader.get(), newShader.get() );
			transferUSDShapingParameters( shaderNetwork, handle, shader.get(), newShader.get() );

			// `pointLight` and `spotLight` are normalized by nature
			// and normalization doesn't apply to `environmentLight`
			if( newShader->getName() == "distantLight" || newShader->getName() == "areaLight" )
			{
				transferUSDParameter( shaderNetwork, handle, shader.get(), g_normalizeParameter, newShader.get(), g_dlNormalizeParameter, false );
			}

			if( shader->getName() == "RectLight" )
			{
				const std::string textureFile = parameterValue( shader.get(), g_textureFileParameter, std::string() );
				if( textureFile != "" )
				{
					ShaderPtr textureShader = new Shader( "dlTexture" );
					textureShader->parameters()[g_dlTextureFileParameter] = new StringData( textureFile );
					// Add a `uvCoord` stub for `addDefaultUVShader()` to work with
					textureShader->parameters()[g_uvCoordParameterName] = new FloatVectorData( { 0, 0 } );
					const InternedString textureHandle = shaderNetwork->addShader( handle.string() + "Texture", std::move( textureShader ) );

					const Color3f color = parameterValue( shader.get(), g_colorParameter, Color3f( 1 ) );
					if( color != Color3f( 1 ) )
					{
						// Multiply image with color
						ShaderPtr multiplyShader = new Shader( "Maths/MultiplyColor" );
						multiplyShader->parameters()[g_multiplyColorParameter] = new Color3fData( color );
						const InternedString multiplyHandle = shaderNetwork->addShader( handle.string() + "Multiply", std::move( multiplyShader ) );
						shaderNetwork->addConnection( ShaderNetwork::Connection( { multiplyHandle, g_multiplyOutputParameter }, { handle, g_dlColorParameter } ) );
						shaderNetwork->addConnection( ShaderNetwork::Connection( { textureHandle, g_textureOutputParameter }, { multiplyHandle, g_multiplyInputParameter } ) );
					}
					else
					{
						// Connect image directly
						shaderNetwork->addConnection( ShaderNetwork::Connection( { textureHandle, g_textureOutputParameter }, { handle, g_dlColorParameter } ) );
					}
				}
			}
			if( shader->getName() == "DomeLight" )
			{
				const std::string textureFile = parameterValue( shader.get(), g_textureFileParameter, std::string() );
				newShader->parameters()[g_dlEnvironmentTextureFileParameter] = new StringData( textureFile );

				if( !textureFile.empty() )
				{
					const std::string format = parameterValue( shader.get(), g_textureFormatParameter, std::string() );
					auto it = g_textureMappingModes.find( format );
					if( it == g_textureMappingModes.end() )
					{
						IECore::msg( IECore::Msg::Warning, "transferUSDTextureFile", fmt::format( "Unsupported mapping mode \"{}\"", format ) );
					}
					else
					{
						newShader->parameters()[g_dlEnvironmentTextureFormatParameter] = new IntData( it->second );
					}
				}
			}

			replaceUSDShader( shaderNetwork, handle, std::move( newShader ) );
		}
	}
}

ShaderNetworkPtr preprocessedNetwork( const ShaderNetwork *shaderNetwork )
{
	ShaderNetworkPtr result = shaderNetwork->copy();

	IECoreScene::ShaderNetworkAlgo::expandSplines( result.get() );
	renameSplineParameters( result.get() );
	convertUSDShaders( result.get() );
	addDefaultUVShader( result.get() );

	IECoreScene::ShaderNetworkAlgo::removeUnusedShaders( result.get() );

	return result;
}

const char *lightGeometryType( const ShaderNetwork *shaderNetwork )
{
	if( const Shader *light = shaderNetwork->outputShader() )
	{
		if( light->getName() == "SphereLight" || light->getName() == "DiskLight" )
		{
			return "particles";
		}
		else if( light->getName() == "RectLight" || light->getName() == "CylinderLight" )
		{
			return "mesh";
		}
		else if( light->getName() == "DistantLight" || light->getName() == "DomeLight" )
		{
			return "environment";
		}
	}

	return nullptr;
}

void updateLightGeometry( const ShaderNetwork *shaderNetwork, NSIContext_t context, const char *handle, MurmurHash &state )
{
	if( const Shader *light = shaderNetwork->outputShader() )
	{
		if( light->getName() == "SphereLight" || light->getName() == "DiskLight" )
		{
			if( state == MurmurHash() )
			{
				const V3f p( 0 );
				ParameterList parameters;
				parameters.add( { "P", &p, NSITypePoint, 1, 1, 0 } );

				if( light->getName() == "DiskLight" )
				{
					const V3f n( 0, 0, -1.f );
					parameters.add( { "N", &n, NSITypeNormal, 1, 1, 0 } );
				}

				NSISetAttribute( context, handle, parameters.size(), parameters.data() );
			}

			const float width = parameterValue( light, g_radiusParameter, g_defaultRadius ) * 2.f;

			MurmurHash newState;
			newState.append( width );

			if( newState != state )
			{
				ParameterList parameters;
				parameters.add( { "width", &width, NSITypeFloat, 0, 1, 0 } );

				NSISetAttribute( context, handle, parameters.size(), parameters.data() );

				state = newState;
			}
		}
		else if( light->getName() == "RectLight" )
		{
			if( state == MurmurHash() )
			{
				const int nvertices = 4;
				ParameterList parameters;
				parameters.add( { "nvertices", &nvertices, NSITypeInteger, 1, 1, 0 } );

				const V2f st[4] = { V2f( 0, 1.f ), V2f( 0, 0 ), V2f( 1.f, 0 ), V2f( 1.f, 1.f ) };
				parameters.add( { "st", &st, NSITypeFloat, 2, 4, NSIParamIsArray } );

				const V3f n( 0, 0, -1.f );
				parameters.add( { "N", &n, NSITypeNormal, 1, 1, 0 } );
				const int nIndices[4] = { 0, 0, 0, 0 };
				parameters.add( { "N.indices", &nIndices, NSITypeInteger, 1, 4, 0 } );

				NSISetAttribute( context, handle, parameters.size(), parameters.data() );
			}

			const float width = parameterValue( light, g_widthParameter, g_defaultWidth );
			const float height = parameterValue( light, g_heightParameter, g_defaultHeight );

			MurmurHash newState;
			newState.append( width );
			newState.append( height );

			if( newState != state )
			{
				const V3f p[4] = {
					V3f( 0.5f * width, 0.5f * height, 0 ),
					V3f( 0.5f * width, -0.5f * height, 0 ),
					V3f( -0.5f * width, -0.5f * height, 0 ),
					V3f( -0.5f * width, 0.5f * height, 0 )
				};
				ParameterList parameters;
				parameters.add( { "P", &p, NSITypePoint, 1, 4, 0 } );

				const int pIndices[4] = { 0, 1, 2, 3 };
				parameters.add( { "P.indices", &pIndices, NSITypeInteger, 1, 4, 0 } );

				NSISetAttribute( context, handle, parameters.size(), parameters.data() );

				state = newState;
			}
		}
		else if( light->getName() == "DistantLight" )
		{
			const double angle = parameterValue( light, g_angleParameter, g_defaultAngle );

			MurmurHash newState;
			newState.append( angle );

			if( newState != state )
			{
				ParameterList parameters;
				parameters.add( { "angle", &angle, NSITypeDouble, 0, 1, 0 } );

				NSISetAttribute( context, handle, parameters.size(), parameters.data() );

				state = newState;
			}
		}
		else if( light->getName() == "DomeLight" )
		{
			if( state == MurmurHash() )
			{
				const double angle = 360.f;
				ParameterList parameters;
				parameters.add( { "angle", &angle, NSITypeDouble, 0, 1, 0 } );

				NSISetAttribute( context, handle, parameters.size(), parameters.data() );
			}
		}
		else if( light->getName() == "CylinderLight" )
		{
			if( state == MurmurHash() )
			{
				std::vector<int> vertsPerPoly;
				std::vector<int> vertIds;
				std::vector<V3f> n;
				std::vector<int> nIds;

				cylinderStatic( vertsPerPoly, vertIds, n, nIds );

				ParameterList parameters;
				parameters.add( { "nvertices", vertsPerPoly.data(), NSITypeInteger, 1, vertsPerPoly.size(), 0 } );
				parameters.add( { "P.indices", vertIds.data(), NSITypeInteger, 1, vertIds.size(), 0 } );
				parameters.add( { "N", n.data(), NSITypeNormal, 1, n.size(), 0 } );
				parameters.add( { "N.indices", nIds.data(), NSITypeInteger, 1, nIds.size(), 0 } );

				NSISetAttribute( context, handle, parameters.size(), parameters.data() );
			}

			const float radius = parameterValue( light, g_radiusParameter, g_defaultRadius );
			const float length = parameterValue( light, g_lengthParameter, g_defaultLength );

			MurmurHash newState;
			newState.append( radius );
			newState.append( length );

			if( newState != state )
			{
				std::vector<V3f> p;
				cylinderP( radius, length, p );

				ParameterList parameters;
				parameters.add( { "P", p.data(), NSITypePoint, 1, p.size(), 0 } );

				NSISetAttribute( context, handle, parameters.size(), parameters.data() );

				state = newState;
			}
		}
	}
}

}  // namespace ShaderNetworkAlgo

}  // namespace IECoreDelight