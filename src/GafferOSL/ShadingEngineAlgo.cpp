//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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
//      * Neither the name of Cinesite VFX Ltd. nor the names of
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

#include "GafferOSL/ShadingEngineAlgo.h"

#include "Gaffer/Context.h"

#include "IECore/SimpleTypedData.h"
#include "IECore/VectorTypedData.h"

#include "OpenEXR/OpenEXRConfig.h"
#if OPENEXR_VERSION_MAJOR < 3
#include "OpenEXR/ImathBox.h"
#else
#include "Imath/ImathBox.h"
#endif

using namespace Imath;
using namespace IECore;
using namespace IECoreScene;


namespace
{

/// Returns points suitable for shading a flat image of the specified resolution.
///   - u and v will be initialised as pixel centers.
///   - P will be initialised to ( 0, 0, 0 )
///
/// Throws if either resolution component is < 1
CompoundDataPtr imageShadingPoints( const V2i &resolution )
{
	if( resolution.x < 1 || resolution.y < 1 )
	{
		throw IECore::Exception( "Invalid resolution x: " + std::to_string( resolution.x ) + " y: " + std::to_string( resolution.y ) );
	}

	CompoundDataPtr shadingPoints = new CompoundData();

	V3fVectorDataPtr pData = new V3fVectorData;
	FloatVectorDataPtr uData = new FloatVectorData;
	FloatVectorDataPtr vData = new FloatVectorData;

	std::vector<V3f> &pWritable = pData->writable();
	std::vector<float> &uWritable = uData->writable();
	std::vector<float> &vWritable = vData->writable();

	const int numPoints = resolution.x * resolution.y;

	pWritable.reserve( numPoints );
	uWritable.reserve( numPoints );
	vWritable.reserve( numPoints );

	for( int y = 0; y < resolution.y; ++y )
	{
		for( int x = 0; x < resolution.x; ++x )
		{
			// Generally speaking, real renderers leave P as 0 for the
			// majority of 'texture' evaluations.
			pWritable.push_back( V3f( 0.0f ) );
			uWritable.push_back( ( x + 0.5f ) / resolution.x );
			vWritable.push_back( ( y + 0.5f ) / resolution.y );
		}
	}

	shadingPoints->writable()["P"] = pData;
	shadingPoints->writable()["u"] = uData;
	shadingPoints->writable()["v"] = vData;

	return shadingPoints;
}

/// Converts shaded points returned by ShadingEngine::shade to an RGB
/// CompoundData image representation of the supplied resolution. The result is
/// suitable for use with IECoreGL::ToGLTextureConverter.  Null is returned if
/// 'Ci' is missing from the shaded points.
///
/// Note: No checks are made to verify the correct number of pixels exist for
/// the supplied resolution.
CompoundDataPtr shadedPointsToImageData( const CompoundData* shadedPoints, const V2i &resolution )
{
	const ConstColor3fVectorDataPtr colors = shadedPoints->member<Color3fVectorData>( "Ci" );
	if( !colors )
	{
		return nullptr;
	}

	CompoundDataPtr result = new CompoundData();

	Box2i dataWindow( V2i( 0 ), V2i( resolution -  V2i( 1 ) ) );
	Box2i displayWindow( V2i( 0 ), V2i( resolution - V2i( 1 ) ) );

	result->writable()["dataWindow"] = new Box2iData( dataWindow );
	result->writable()["displayWindow"] = new Box2iData( displayWindow );

	FloatVectorDataPtr redChannelData = new FloatVectorData();
	FloatVectorDataPtr greenChannelData = new FloatVectorData();
	FloatVectorDataPtr blueChannelData = new FloatVectorData();
	std::vector<float> &r = redChannelData->writable();
	std::vector<float> &g = greenChannelData->writable();
	std::vector<float> &b = blueChannelData->writable();

	std::vector<Color3f>::size_type numColors = colors->readable().size();
	r.reserve( numColors );
	g.reserve( numColors );
	b.reserve( numColors );

	for( std::vector<Color3f>::size_type u = 0; u < numColors; ++u )
	{
		Color3f c = colors->readable()[u];

		r.push_back( c[0] );
		g.push_back( c[1] );
		b.push_back( c[2] );
	}

	CompoundDataPtr channelData = new CompoundData;
	channelData->writable()["R"] = redChannelData;
	channelData->writable()["G"] = greenChannelData;
	channelData->writable()["B"] = blueChannelData;

	result->writable()["channels"] = channelData;

	return result;
}

} // Anon namespace

namespace GafferOSL
{

CompoundDataPtr ShadingEngineAlgo::shadeUVTexture( const IECoreScene::ShaderNetwork *shaderNetwork, const Imath::V2i &resolution, IECoreScene::ShaderNetwork::Parameter output )
{
	IECoreScene::ShaderNetworkPtr surfaceNetwork = shaderNetwork->copy();

	if( !output )
	{
		output = shaderNetwork->getOutput();
	}

	const IECoreScene::Shader *outputShader = shaderNetwork->getShader( output.shader );
	if( !outputShader )
	{
		throw IECore::Exception( "Requested output shader does not exist: " + output.shader.string() );
	}

	if( output != surfaceNetwork->getOutput() || outputShader->getType() != "osl:surface" )
	{
		IECore::InternedString surface = surfaceNetwork->addShader( "surface", new IECoreScene::Shader( "Surface/Constant", "osl:shader" ) );
		surfaceNetwork->addConnection( { output, { surface, "Cs" } } );
		surfaceNetwork->setOutput( { surface, "" } );
	}

	GafferOSL::ShadingEnginePtr shadingEngine = new GafferOSL::ShadingEngine( surfaceNetwork.get() );
	const ConstCompoundDataPtr shadingPoints = imageShadingPoints( resolution );

	// ShadingEngine currently respects cancellation via the context. If we do this
	// shading for visualisation isn't designed for cancellation, so we scope a new context to
	// temporarily ensure this doesn't happen. Long term, we plan to refactor such
	// that cancellation is explicitly expressed in the API.
	Gaffer::ContextPtr context = new Gaffer::Context();
	Gaffer::Context::Scope contextScope( context.get() );
	const ConstCompoundDataPtr shadingResult = shadingEngine->shade( shadingPoints.get() );

	return shadedPointsToImageData( shadingResult.get(), resolution );
}

} // namespace GafferOSL
