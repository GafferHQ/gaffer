//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Lucien Fostier. All rights reserved.
//  Copyright (c) 2012-2017, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/Checkerboard.h"

#include "GafferImage/ImageAlgo.h"

#include "Gaffer/Context.h"
#include "Gaffer/Transform2DPlug.h"

#include "Imath/ImathFun.h"
#include "Imath/ImathMatrixAlgo.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace GafferImage;
using namespace Gaffer;


namespace
{

inline float filteredStripes( float x, float period, float filterWidth )
{
	// \todo : this call to round is actually quite slow, and isn't being inlined.
	//
	// Replacing it with nearbyintf is faster, and should be inlinable, but there are
	// two issues:
	// * nearbyintf is influenced by the current rounding mode, which could be something
	//   other than FE_TONEAREST ( but if it was something other than FE_TONEAREST, it looks
	//   like that would also break OIIO's use of rint(), so maybe that's fine?
	// * This bug in GCC means it wouldn't get inlined until we get on GCC 9:
	//   https://gcc.gnu.org/bugzilla/show_bug.cgi?id=71278
	//
	// Alternatively, we could explicitly use an intrinsic for the ASM instruction we actually
	// want, avoiding both issues:
	//
	//   float nearestBoundary;
	//   __m128 d = _mm_load_ss(&xp);
	//   d = _mm_round_ss(d, d, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
	//   _mm_store_ss(&nearestBoundary, d);
	//
	// But mm_round_ss requires sse4.2 - I doubt if anyone is running Gaffer without sse4.2
	// support, but we would need to make a decision about what processors we support, and this
	// isn't important enough to justify it.
	//
	// The other approach used by oiio's fast_rint is just static_cast<int>(x + copysignf(0.5f, x)).
	// This is faster than round(), but messy, and not as fast as nearbyintf or mm_round_ss.
	//
	// Just sticking with the old round() for now, since this isn't too important
	float xp = x / ( period * 0.5f );
	float nearestBoundary = round( xp );
	float boundaryDirection = (((int)nearestBoundary) % 2 ) == 0 ? -1.0f : 1.0f;
	return max( 0.0f, min( 1.0f, ( ( xp - nearestBoundary ) * ( period * 0.5f ) / filterWidth * boundaryDirection + 0.5f ) ) );
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Checkerboard implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Checkerboard );

size_t Checkerboard::g_firstPlugIndex = 0;

Checkerboard::Checkerboard( const std::string &name )
	:	FlatImageSource( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new FormatPlug( "format" ) );
	addChild( new V2fPlug( "size", Plug::In, V2i( 64.f ), V2i( 1.f ), V2i( 4096.f ) ) );
	addChild( new Color4fPlug( "colorA", Plug::In, Color4f( 0.1, 0.1, 0.1, 1 ) ) );
	addChild( new Color4fPlug( "colorB", Plug::In, Color4f( .5, 0.5, 0.5, 1 ) ) );
	addChild( new StringPlug( "layer" ) );
	addChild( new Transform2DPlug( "transform" ) );
}

Checkerboard::~Checkerboard()
{
}

GafferImage::FormatPlug *Checkerboard::formatPlug()
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

const GafferImage::FormatPlug *Checkerboard::formatPlug() const
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

Gaffer::V2fPlug *Checkerboard::sizePlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::V2fPlug *Checkerboard::sizePlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 1 );
}

Gaffer::Color4fPlug *Checkerboard::colorAPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::Color4fPlug *Checkerboard::colorAPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 2 );
}

Gaffer::Color4fPlug *Checkerboard::colorBPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::Color4fPlug *Checkerboard::colorBPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *Checkerboard::layerPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *Checkerboard::layerPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

Gaffer::Transform2DPlug *Checkerboard::transformPlug()
{
	return getChild<Transform2DPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::Transform2DPlug *Checkerboard::transformPlug() const
{
	return getChild<Transform2DPlug>( g_firstPlugIndex + 5 );
}

void Checkerboard::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FlatImageSource::affects( input, outputs );

	if(
		input->parent<Plug>() == colorAPlug() ||
		input->parent<Plug>() == colorBPlug() ||
		input->parent<V2fPlug>() == sizePlug() ||
		transformPlug()->isAncestorOf( input )
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}

	if( formatPlug()->displayWindowPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->formatPlug() );
		outputs.push_back( outPlug()->dataWindowPlug() );
	}

	if( input == formatPlug()->pixelAspectPlug() )
	{
		outputs.push_back( outPlug()->formatPlug() );
	}

	if( input == layerPlug() )
	{
		outputs.push_back( outPlug()->channelNamesPlug() );
	}
}

void Checkerboard::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageSource::hashFormat( output, context, h );
	h.append( formatPlug()->hash() );
}

GafferImage::Format Checkerboard::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return formatPlug()->getValue();
}

void Checkerboard::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageSource::hashDataWindow( output, context, h );
	h.append( formatPlug()->hash() );
}

Imath::Box2i Checkerboard::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return formatPlug()->getValue().getDisplayWindow();
}

IECore::ConstCompoundDataPtr Checkerboard::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return outPlug()->metadataPlug()->defaultValue();
}

void Checkerboard::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageSource::hashChannelNames( output, context, h );
	layerPlug()->hash( h );
}

IECore::ConstStringVectorDataPtr Checkerboard::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string channelNamePrefix = layerPlug()->getValue();
	if( !channelNamePrefix.empty() )
	{
		channelNamePrefix += ".";
	}

	StringVectorDataPtr resultData = new StringVectorData();
	vector<string> &result = resultData->writable();

	result.push_back( channelNamePrefix + "R" );
	result.push_back( channelNamePrefix + "G" );
	result.push_back( channelNamePrefix + "B" );
	result.push_back( channelNamePrefix + "A" );

	return resultData;
}

void Checkerboard::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageSource::hashChannelData( output, context, h );

	V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	h.append( tileOrigin );

	string channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	h.append( channelName );

	const int channelIndex = ImageAlgo::colorIndex( channelName );
	colorAPlug()->getChild( channelIndex )->hash( h );
	colorBPlug()->getChild( channelIndex )->hash( h );

	h.append( sizePlug()->getValue() );
	transformPlug()->hash( h );
}

IECore::ConstFloatVectorDataPtr Checkerboard::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const int channelIndex = ImageAlgo::colorIndex( context->get<std::string>( ImagePlug::channelNameContextName ) );

	const float valueA = colorAPlug()->getChild( channelIndex )->getValue();
	const float valueB = colorBPlug()->getChild( channelIndex )->getValue();
	const V2f size = sizePlug()->getValue();
	const M33f transform = transformPlug()->matrix();
	const M33f inverseTransform = transform.inverse();

	V2f baseA( 1, 0 );
	V2f filterWidthA;
	V2f baseB( 0, 1 );
	V2f filterWidthB;
	inverseTransform.multDirMatrix( baseA, filterWidthA );
	inverseTransform.multDirMatrix( baseB, filterWidthB );
	V2f filterWidth( fabs( filterWidthA.x ) + fabs( filterWidthB.x ), fabs( filterWidthA.y ) + fabs( filterWidthB.y ) );

	FloatVectorDataPtr resultData = new FloatVectorData;
	vector<float> &result = resultData->writable();
	result.reserve( ImagePlug::tileSize() * ImagePlug::tileSize() );

	// If there is no dependency between X and Y, we can treat them separably, for much better perf
	if( transform[0][1] == 0 && transform[1][0] == 0 )
	{
		// Position of pixel <0,0>
		float xOffset = inverseTransform[2][0] + (tileOrigin.x + .5f) * inverseTransform[0][0];
		float yOffset = inverseTransform[2][1] + (tileOrigin.y + .5f) * inverseTransform[1][1];

		// Use the first scanline as a buffer to store the x component of the checkerboard
		for( int x = 0; x < ImagePlug::tileSize(); ++x )
		{
			float w0 = filteredStripes( x * inverseTransform[0][0] + xOffset, size.x, filterWidth.x );
			result.push_back( w0 );
		}

		// Compute the y components and fill the rest of the image by copying the x components
		// stored in the first scanline
		for( int y = 1; y < ImagePlug::tileSize(); ++y )
		{
			float h0 = filteredStripes( y * inverseTransform[1][1] + yOffset, size.y, filterWidth.y );
			for( int x = 0; x < ImagePlug::tileSize(); ++x )
			{
				float v = lerp<float>( result[x], 1 - result[x], h0 );
				result.push_back( lerp<float>( valueA, valueB, v ) );
			}
		}

		// Apply the y component to the first scanline
		float h0 = filteredStripes( yOffset, size.y, filterWidth.y );
		for( int x = 0; x < ImagePlug::tileSize(); ++x )
		{
			float v = lerp<float>( result[x], 1 - result[x], h0 );
			result[x] = lerp<float>( valueA, valueB, v );
		}
	}
	else
	{
		for( int y = 0; y < ImagePlug::tileSize(); ++y )
		{
			for( int x = 0; x < ImagePlug::tileSize(); ++x )
			{
				V2f p( tileOrigin.x + x + .5f, tileOrigin.y + y + .5f );
				p *= inverseTransform;

				float w0 = filteredStripes( p.x, size.x, filterWidth.x );
				float h0 = filteredStripes( p.y, size.y, filterWidth.y );

				float v = lerp<float>( w0, 1 - w0, h0 );
				result.push_back( lerp<float>( valueA, valueB, v ) );
			}
		}
	}

	return resultData;
}
