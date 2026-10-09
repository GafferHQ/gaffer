//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2016, Image Engine Design Inc. All rights reserved.
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
//     * Neither the name of Image Engine Design nor the names of any
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

#include "IECoreArnold/NodeAlgo.h"
#include "IECoreArnold/ShapeAlgo.h"

#include "IECoreScene/PointsPrimitive.h"

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"

#include "ai_version.h"

#include "fmt/format.h"

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreArnold;

namespace
{

bool aiVersionLessThan( int arch, int major, int minor, int patch )
{
	// This is _not_ the same as `AiCheckAPIVersion()` :
	//
	// - `AiCheckAPIVersion()` is for determining ABI compatibility and
	//   returns false if the `arch` or `major` numbers are not equal.
	// - `AiCheckAPIVersion()` doesn't support a patch version.
	// - `aiVersionLess()` is suitable for determining if an Arnold
	//   feature or bugfix is available.
	const char *arnoldVersionString = AiGetVersion( nullptr, nullptr, nullptr, nullptr );
	int arnoldVersion[4];
	for( int i = 0; i < 4; ++i )
	{
		arnoldVersion[i] = strtol( arnoldVersionString, const_cast<char **>( &arnoldVersionString ), 10 );
		++arnoldVersionString;
	}

	auto version = { arch, major, minor, patch };

	return std::lexicographical_compare(
		begin( arnoldVersion ), end( arnoldVersion ),
		version.begin(), version.end()
	);
}

const AtString g_gaussianArnoldString( "gaussian" );
const AtString g_gsColorSpaceArnoldString( "gs_input_color_space" );
const AtString g_gsOpacityArnoldString( "gs_opacity" );
const AtString g_gsRotationArnoldString( "gs_rotation" );
const AtString g_gsScaleArnoldString( "gs_scale" );
const AtString g_gsShArnoldString( "gs_sh" );
const AtString g_modeArnoldString( "mode" );
const AtString g_motionStartArnoldString( "motion_start" );
const AtString g_motionEndArnoldString( "motion_end" );
const AtString g_pointsArnoldString( "points" );
const AtString g_quadArnoldString( "quad" );
const AtString g_sphereArnoldString( "sphere" );

const std::string g_scalesVariable( "scales" );
const std::string g_opacitiesVariable( "opacities" );
const std::string g_orientationsVariable( "orientations" );
const std::string g_radianceColorSpace( "radiance:colorSpace" );
const std::string g_radianceSphericalHarmonicsCoefficientsPrefix( "radiance:sphericalHarmonicsCoefficients" );
const std::string g_radianceSphericalHarmonicsDegreeVariable( "radiance:sphericalHarmonicsDegree" );

const std::string g_gaussianSplatTypeName( "gaussianSplat" );

const float g_C0 = 1.f / ( 2.f * sqrt( M_PI ) );

AtNode *convertStatic( const IECoreScene::PointsPrimitive *points, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode, const std::string &messageContext )
{

	AtNode *result = AiNode( universe, g_pointsArnoldString, AtString( nodeName.c_str() ), parentNode );

	// mode

	const StringData *t = points->variableData<StringData>( "type", PrimitiveVariable::Constant );
	if( t )
	{
		if( t->readable() == "particle" || t->readable()=="disk" )
		{
			// default type is disk - no need to do anything
		}
		else if( t->readable() == "sphere" )
		{
			AiNodeSetStr( result, g_modeArnoldString, g_sphereArnoldString );
		}
		else if( t->readable() == "patch" )
		{
			AiNodeSetStr( result, g_modeArnoldString, g_quadArnoldString );
		}
		else if( t->readable() == g_gaussianSplatTypeName && !aiVersionLessThan( 7, 5, 2, 0 ) )
		{
			AiNodeSetStr( result, g_modeArnoldString, g_gaussianArnoldString );
		}
		else
		{
			IECore::msg( IECore::Msg::Warning, messageContext, fmt::format( "Unknown type \"{}\" - reverting to disk mode.", t->readable() ) );
		}
	}

	// arbitrary user parameters

	const char *ignore[] = { "P", "width", "radius", nullptr };
	const char *ignoreGaussianSplat[] = {
		"P", "width", "radius",
		g_scalesVariable.c_str(), g_opacitiesVariable.c_str(), g_orientationsVariable.c_str(), g_radianceSphericalHarmonicsDegreeVariable.c_str(), g_radianceColorSpace.c_str(),
		"radiance:sphericalHarmonicsCoefficients:0", "radiance:sphericalHarmonicsCoefficients:1", "radiance:sphericalHarmonicsCoefficients:2", "radiance:sphericalHarmonicsCoefficients:3",
		"radiance:sphericalHarmonicsCoefficients:4", "radiance:sphericalHarmonicsCoefficients:5", "radiance:sphericalHarmonicsCoefficients:6", "radiance:sphericalHarmonicsCoefficients:7",
		"radiance:sphericalHarmonicsCoefficients:8", "radiance:sphericalHarmonicsCoefficients:9", "radiance:sphericalHarmonicsCoefficients:10", "radiance:sphericalHarmonicsCoefficients:11",
		"radiance:sphericalHarmonicsCoefficients:12", "radiance:sphericalHarmonicsCoefficients:13", "radiance:sphericalHarmonicsCoefficients:14", "radiance:sphericalHarmonicsCoefficients:15",
		nullptr
	};

	ShapeAlgo::convertPrimitiveVariables( points, result, AiNodeGetStr( result, g_modeArnoldString ) == g_gaussianArnoldString ? ignoreGaussianSplat : ignore, messageContext );

	return result;

}

AtNode *convert( const IECoreScenePreview::Renderer::Samples<const IECoreScene::PointsPrimitive *> &samples, float motionStart, float motionEnd, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode, const std::string &messageContext )
{
	AtNode *result = convertStatic( samples.front(), universe, nodeName, parentNode, messageContext );

	const auto primitiveSamples = IECoreScenePreview::Renderer::staticSamplesCast<const Primitive *>( samples );
	if( !ShapeAlgo::convertP( primitiveSamples, result, g_pointsArnoldString, messageContext ) )
	{
		AiNodeDestroy( result );
		return nullptr;
	}

	ShapeAlgo::convertRadius( primitiveSamples, result, messageContext );

	AiNodeSetFlt( result, g_motionStartArnoldString, motionStart );
	AiNodeSetFlt( result, g_motionEndArnoldString, motionEnd );

	/// \todo Aspect, rotation

	if( AiNodeGetStr( result, g_modeArnoldString ) == g_gaussianArnoldString && !aiVersionLessThan( 7, 5, 2, 0 ) )
	{

		if( const V3fVectorData *scalesData = samples.front()->variableData<V3fVectorData>( g_scalesVariable, PrimitiveVariable::Interpolation::Vertex ) )
		{
			const std::vector<Imath::V3f> &scales = scalesData->readable();
			AiNodeSetArray( result, g_gsScaleArnoldString, AiArrayConvert( scales.size(), 1, AI_TYPE_VECTOR, scales.data() ) );
		}

		if( const FloatVectorData *opacitiesData = samples.front()->variableData<FloatVectorData>( g_opacitiesVariable, PrimitiveVariable::Interpolation::Vertex ) )
		{
			const std::vector<float> &opacities = opacitiesData->readable();
			AiNodeSetArray( result, g_gsOpacityArnoldString, AiArrayConvert( opacities.size(), 1, AI_TYPE_FLOAT, opacities.data() ) );
		}

		if( const StringData *colorSpaceData = samples.front()->variableData<StringData>( g_radianceColorSpace, PrimitiveVariable::Interpolation::Constant ) )
		{
			AiNodeSetStr( result, g_gsColorSpaceArnoldString, AtString( colorSpaceData->readable().c_str() ) );
		}

		if( const QuatfVectorData *orientationsData = samples.front()->variableData<QuatfVectorData>( g_orientationsVariable, PrimitiveVariable::Vertex ) )
		{
			// Arnold wants the quaternions as groups of four floats with the imaginary part first.
			// Cortex represents them with the imaginary part second, so we need to flip them.
			const std::vector<Imath::Quatf> &orientation = orientationsData->readable();
			AtArray *orientationArray = AiArrayAllocate( orientation.size() * 4, 1, AI_TYPE_FLOAT );
			float *shuffledOrientationArray = static_cast<float *>( AiArrayMap( orientationArray ) );
			for( size_t i = 0, eI = orientation.size(); i < eI; ++i )
			{
				shuffledOrientationArray[i * 4] = orientation[i].v.x;
				shuffledOrientationArray[i * 4 + 1] = orientation[i].v.y;
				shuffledOrientationArray[i * 4 + 2] = orientation[i].v.z;
				shuffledOrientationArray[i * 4 + 3] = orientation[i].r;
			}
			AiArrayUnmap( orientationArray );
			AiNodeSetArray( result, g_gsRotationArnoldString, orientationArray );
		}

		// Cortex stores spherical harmonics coefficients as one primitive variable per factor.
		// This way the primitive variable size matches the vertex primvar size.
		// i.e. factor0point0, factor0point1, factor0point2... factor0pointN
		// Arnold expects them to be in a single array where all the factors of a point are
		// listed sequentially, followed by all factors of the next point.
		// i.e. factor0point0, factor1point0, factor2point0... factorMpoint0, factor0point1, factor1point1... factorMpointN

		if( const IntData *degreeData = samples.front()->variableData<IntData>( g_radianceSphericalHarmonicsDegreeVariable, PrimitiveVariable::Constant ) )
		{
			const int degree = degreeData->readable();
			const int coefficientCount = ( degree + 1 ) * ( degree + 1 );

			std::vector<Imath::Color3f> allCoefficients( coefficientCount * samples.front()->getNumPoints() );

			for( int i = 0; i < coefficientCount; ++i )
			{
				auto coefficientsData = samples.front()->variableData<const V3fVectorData>(
					fmt::format( g_radianceSphericalHarmonicsCoefficientsPrefix + ":{}", i ),
					PrimitiveVariable::Vertex
				);

				if( !coefficientsData )
				{
					IECore::msg(
						IECore::Msg::Warning, messageContext,
						fmt::format( "Could not find Gaussian Splat coefficient data set {}", i )
					);
					continue;
				}

				const std::vector<Imath::V3f> &coefficients = coefficientsData->readable();
				for( size_t j = 0, eJ = samples.front()->getNumPoints(); j < eJ; ++j )
				{
					allCoefficients[j * coefficientCount + i] = coefficients[j];
				}

			}

			// Cortex adopts the USD standard and stores the DC (index 0) coefficient in raw form. Arnold
			// expects it to be normalized. See arnold-usd for more information.
			for( size_t i = 0, eI = samples.front()->getNumPoints(); i < eI; ++i )
			{
				allCoefficients[i * coefficientCount] = allCoefficients[i * coefficientCount] * g_C0 + Imath::Color3f( 0.5f );
			}

			AiNodeSetArray( result, g_gsShArnoldString, AiArrayConvert( allCoefficients.size(), 1, AI_TYPE_RGB, allCoefficients.data() ) );
		}
	}

	return result;
}

NodeAlgo::ConverterDescription<PointsPrimitive> g_description( ::convert );

} // namespace
