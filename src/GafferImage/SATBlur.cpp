//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/SATBlur.h"

#include "GafferImage/ImageAlgo.h"
#include "GafferImage/BufferAlgo.h"

#include "Gaffer/Context.h"

#include "IECore/NullObject.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

namespace {

// Should we allow choosing the alpha channel for occlusion?
const std::string g_alphaChannelName = "A";

// Read exactly one pixel back from a Summed Area Table.
// This should exactly reconstruct the pixel value used to construct the table,
// aside from floating point error.
inline float satReconstructPixel( const Imath::V2i &p, const std::vector<float> &sat )
{
	int index = ImagePlug::pixelIndex( p, Imath::V2i( 0 ) );

	if( p.x == 0 || p.y == 0 )
	{
		if( p.x == 0 && p.y == 0 )
		{
			// Bottom left corner, just use the first value
			return sat[0];
		}
		else if( p.y == 0 )
		{
			// Bottom edge, recover value via horizontal diff
			return sat[index] - sat[ index - 1 ];
		}
		else // p.x == 0
		{
			// Left edge, recover value via horizontal diff
			return sat[index] - sat[ index - ImagePlug::tileSize() ];
		}
	}
	else
	{
		// Not on an edge, recover value by a SAT rect lookup on the
		// 4 corners of the pixel
		return sat[index] + sat[ index - ImagePlug::tileSize() - 1 ]
			- sat[ index - ImagePlug::tileSize() ] - sat[ index - 1 ];
	}
}

// Read a Summed Area Table value from a floating point pixel coordinate.
// This is basically just a bilinear lookup, but with a bunch of special case
// handling of edges, extending the summed area function for this tile
// to the entire plane ( assuming that all pixels outside the tile are zero ).
// This means 4 calls to satBilinear can return the sum for a rectangle's
// overlap with this tile, whether or not the rectangle is within the tile.
inline float satBilinear( float x, float y, const std::vector<float> &sat )
{
	float floorX = floor( x );
	float floorY = floor( y );
	int intX = floorX;
	int intY = floorY;
	float xFrac = x - floorX;
	float yFrac = y - floorY;


	// We divide the plane into a bunch of special cases. Usually you'd just have 9 regions based
	// on below/within/above the tile in X and Y, but here we have a few extra because we distinguish
	// between "within the lower edge" ( the pixel value is blended to zero ) and "below the lower edge"
	// ( the value is just zero ).

	if( intX >= 0 && intY >= 0 && intX < ImagePlug::tileSize() - 1 && intY < ImagePlug::tileSize() - 1 )
	{
		// Not on an edge, regular bilinear interpolation
		int baseIndex = ( intY << ImagePlug::tileSizeLog2() ) + intX;
		return
			( sat[ baseIndex ] * ( 1.0f - xFrac ) + sat[ baseIndex + 1 ] * xFrac ) * ( 1.0f - yFrac ) +
			( sat[ baseIndex + ImagePlug::tileSize() ] * ( 1.0f - xFrac ) + sat[ baseIndex + ImagePlug::tileSize() + 1 ] * xFrac ) * yFrac;
	}
	else if( intX < -1 || intY < -1 )
	{
		// Outside the tile on the low side, return 0
		return 0.0f;
	}
	else if( intX >= ImagePlug::tileSize() - 1 && intY >= ImagePlug::tileSize() - 1 )
	{
		// Outside the tile in the upper right - the entire tile is included in the sum
		return sat[ ImagePlug::tilePixels() - 1 ];
	}
	else if( intX == -1 && intY == -1 )
	{
		// Within the lower left corner - this is a bilinear blend with 3 zero pixels
		return sat[0] * xFrac * yFrac;
	}
	else if( intX == -1 && intY >= ImagePlug::tileSize() - 1 )
	{
		// Within the left edge, but above it. Interpolate the top left pixel with black, this
		// value extends out to infinity
		return sat[ ( ImagePlug::tileSize() - 1 ) << ImagePlug::tileSizeLog2() ] * xFrac;
	}
	else if( intY == -1 && intX >= ImagePlug::tileSize() - 1 )
	{
		// Within the bottom edge, but to the right of it. Interpolate the bottom right pixel with black, this
		// value extends out to infinity
		return sat[ ImagePlug::tileSize() - 1 ] * yFrac;
	}
	else if( intX == -1 )
	{
		// Within the left edge. Two pixels bilinearly interpolated with 2 zero pixels
		return ( sat[ intY << ImagePlug::tileSizeLog2() ] * ( 1.0f - yFrac ) + sat[ ( intY + 1 ) << ImagePlug::tileSizeLog2() ] * yFrac ) * xFrac;
	}
	else if( intY == -1 )
	{
		// Within the bottom edge. Two pixels bilinearly interpolated with 2 zero pixels
		return ( sat[ intX ] * ( 1.0f - xFrac ) + sat[ intX + 1 ] * xFrac ) * yFrac;
	}
	else if( intX >= ImagePlug::tileSize() - 1 )
	{
		// Within the correct height, but right of the tile - we blend the two rightmost pixels at this height
		return
			sat[ ( intY << ImagePlug::tileSizeLog2() ) + ImagePlug::tileSize() - 1 ] * ( 1.0f - yFrac ) +
			sat[ ( ( intY + 1 ) << ImagePlug::tileSizeLog2() ) + ImagePlug::tileSize() - 1 ] * yFrac;
	}
	else // Remaining case is intY >= ImagePlug::tileSize() - 1 )
	{
		// Within the correct width, but above the tile - we blend the two top pixels at this x value
		return
			sat[ ( ( ImagePlug::tileSize() - 1 ) << ImagePlug::tileSizeLog2() ) + intX ] * ( 1.0f - xFrac ) +
			sat[ ( ( ImagePlug::tileSize() - 1 ) << ImagePlug::tileSizeLog2() ) + intX + 1 ] * xFrac;
	}
}

// Return a vector of up to n rectangles which approximate as well as possible a radius 1 disk.
// n must be at least 3. If n is even, it will be rounded down ( the best approximation using 4
// disks is identical to the best approximation using 3 disks ).
std::vector<Box2f> diskApproximationRects( int n )
{
	std::vector<Box2f> rects;

	const int halfN = ( n - 1 ) / 2;

	// Our disk approximation is chosen to be highly symmetric - it has 90 degree rotational symmetry
	// but also an additional mirror symmetry, so one 45 degree slice defines all the vertex positions.
	// We refer to this slice as an "octant".

	// The idea here is that when drawing a sequence of stair steps that form one octant
	// of the approximate disk, we use a fixed size step on the minor axis, and then the
	// size of the larger steps on the major axis is computed by intersecting the middle
	// of the step with the disk.

	// The main thing that makes this a bit awkward to describe is the 4 corners on the exact
	// diagonals, which point inwards if halfN is odd, so are just implicit, but point outwards
	// and must be output explicitly if halfN is even.

	int octantSteps = ( halfN + 1 ) / 2;
	bool halfNOdd = halfN % 2;

	// The step size is determined based on the point on the unit circle at 45 degrees - this defines a symmetry
	// plane, and is where we switch which axis is major and minor.

	// With increasing octantSteps, the corner at 45 degrees will alternate between pointing out or pointing in,
	// and this will determine whether the number of steps before we reach the unit circle at 45 degree goes up
	// or down by a half-step.
	const float stepsToCircle45 = octantSteps + ( halfNOdd ? -0.5 : 0.5f );

	// In the loop below, we compute the sizes of each step based on the middle of the step intersecting the
	// unit circle. In order to make sure things align correctly at the 45 degree mirror plane, we have to do
	// some algebra to ensure that the final step halfWidths will be equal to stepScale * octantSteps.
	// Note that if halfNOdd is false, the final step halfWidth is implicit, instead of being stored in stepHalfWidths.
	const float stepScale = 1.0f / ( octantSteps + stepsToCircle45 + sqrtf( 2.0f * octantSteps * stepsToCircle45 ) );

	std::vector<float> stepHalfWidths;
	stepHalfWidths.reserve( octantSteps );

	// Compute the sizes of each step on the major axis
	for( int i = 0; i < octantSteps; i++ )
	{
		float qq = 1.0f - ( i + 0.5f ) * stepScale;
		stepHalfWidths.push_back( sqrtf( 1.0 - qq * qq ) );
	}

	// Now that we've got the sizes of all our steps for an octant, we need to translate that into
	// rectangles that cover all 8 octants

	// The top and bottom-most rectangles use fixed size minor steps in Y, and the longer halfWidths
	// we've computed in X.
	for( int i = 0; i < octantSteps; i++ )
	{
		float q = 1.0f - i * stepScale;
		float nextQ = 1.0f - ( i + 1 ) * stepScale;
		float stepRadius = stepHalfWidths[i];
		rects.push_back( Box2f( V2f( -stepRadius, nextQ ), V2f( stepRadius, q ) ) );
		rects.push_back( Box2f( V2f( -stepRadius, -q ), V2f( stepRadius, -nextQ ) ) );
	}

	// If halfN is even, the exact diagonals stick out, and we need to add 2 rectangles to cover them.
	if( !halfNOdd )
	{
		float zz = 1.0f - stepScale * octantSteps;
		rects.push_back( Box2f( V2f( -zz, stepHalfWidths.back() ), V2f( zz, zz ) ) );
		rects.push_back( Box2f( V2f( -zz, -zz ), V2f( zz, -stepHalfWidths.back() ) ) );
	}

	// As we approach the middle, we use rectangles with a fixed minor step in X, and the longer halfWidths
	// in Y.
	for( int i = 1; i < octantSteps; i++ )
	{
		float q = 1.0f - i * stepScale;
		rects.push_back( Box2f( V2f( -q, stepHalfWidths[ i - 1 ] ), V2f( q, stepHalfWidths[i] ) ) );
		rects.push_back( Box2f( V2f( -q, -stepHalfWidths[i] ), V2f( q, -stepHalfWidths[ i - 1 ] ) ) );
	}

	// The very middle rectangle always has a half width of 1, and the height is the one we computed
	// so that the intersection with the disk will be in the middle of the first step
	rects.push_back( Box2f( V2f( -1.0f, -stepHalfWidths[0] ), V2f( 1.0f, stepHalfWidths[0] ) ) );

	// It's easier to generate these rects out of order, but we require them in order. This is currently
	// called rarely, so it's fine to just sort them, and we know their Y coords are unique.
	std::sort( rects.begin(), rects.end(), []( const Box2f &a, const Box2f &b ){ return a.min.y < b.min.y; } );
	return rects;
}

const InternedString g_layerBoundaryName( "satBlur:layerBoundary" );

} // namespace

//////////////////////////////////////////////////////////////////////////
// SATBlur node
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( SATBlur );

size_t SATBlur::g_firstPlugIndex = 0;

SATBlur::SATBlur( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new V2fPlug( "radius", Plug::In, V2f(0.0f), V2f(0.0f) ) );
	addChild( new StringPlug( "radiusChannel" ) );
	addChild( new FloatPlug( "maxRadius", Plug::In, 512, 1 ) );
	addChild( new IntPlug( "boundingMode", Plug::In, (int)SATBlur::BoundingMode::Black ) );
	addChild( new StringPlug( "filter", Plug::In, "box" ) );
	addChild( new IntPlug( "diskRectangles", Plug::In, 3, 3 ) );

	addChild( new FloatVectorDataPlug( "layerBoundaries", Plug::In ) );
	addChild( new StringPlug( "depthChannel" ) );
	addChild( new StringPlug( "depthLookupChannel" ) );

	addChild( new FloatVectorDataPlug( "__sat", Plug::Out ) );

	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
	outPlug()->viewNamesPlug()->setInput( inPlug()->viewNamesPlug() );

	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	outPlug()->deepPlug()->setInput( inPlug()->deepPlug() );
	outPlug()->sampleOffsetsPlug()->setInput( inPlug()->sampleOffsetsPlug() );
}

SATBlur::~SATBlur()
{
}

Gaffer::V2fPlug *SATBlur::radiusPlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex );
}

const Gaffer::V2fPlug *SATBlur::radiusPlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *SATBlur::radiusChannelPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *SATBlur::radiusChannelPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::FloatPlug *SATBlur::maxRadiusPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::FloatPlug *SATBlur::maxRadiusPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

Gaffer::IntPlug *SATBlur::boundingModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::IntPlug *SATBlur::boundingModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *SATBlur::filterPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *SATBlur::filterPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

Gaffer::IntPlug *SATBlur::diskRectanglesPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::IntPlug *SATBlur::diskRectanglesPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 5 );
}

Gaffer::FloatVectorDataPlug *SATBlur::layerBoundariesPlug()
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::FloatVectorDataPlug *SATBlur::layerBoundariesPlug() const
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex + 6 );
}

Gaffer::StringPlug *SATBlur::depthChannelPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::StringPlug *SATBlur::depthChannelPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 7 );
}

Gaffer::StringPlug *SATBlur::depthLookupChannelPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::StringPlug *SATBlur::depthLookupChannelPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 8 );
}

Gaffer::FloatVectorDataPlug *SATBlur::satPlug()
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex + 9 );
}

const Gaffer::FloatVectorDataPlug *SATBlur::satPlug() const
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex + 9 );
}

void SATBlur::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if(
		input == inPlug()->channelDataPlug() ||
		input == inPlug()->channelNamesPlug() ||
		input == inPlug()->dataWindowPlug() ||
		input == inPlug()->deepPlug() ||
		input == depthChannelPlug()
	)
	{
		outputs.push_back( satPlug() );
	}

	if(
		input->parent<V2fPlug>() == radiusPlug() ||
		input == radiusChannelPlug() ||
		input == boundingModePlug() ||
		input == filterPlug() ||
		input == diskRectanglesPlug() ||
		input == maxRadiusPlug() ||
		input == satPlug() ||
		input == inPlug()->channelDataPlug() ||
		input == inPlug()->dataWindowPlug() ||
		input == inPlug()->deepPlug() ||
		input == inPlug()->channelNamesPlug() ||
		input == layerBoundariesPlug() ||
		input == depthLookupChannelPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void SATBlur::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hash( output, context, h );
	if( output == satPlug() )
	{
		const float *layerBoundary = context->getIfExists< float >( g_layerBoundaryName );

		Context::EditableScope scope( context );
		if( layerBoundary )
		{
			scope.remove( g_layerBoundaryName );
		}

		inPlug()->channelDataPlug()->hash( h );

		std::string depthChannel;
		Box2i dataWindow;
		{
			ImagePlug::GlobalScope c( scope.context() );
			inPlug()->deepPlug()->hash( h );
			depthChannel = depthChannelPlug()->getValue();
			dataWindow = inPlug()->dataWindowPlug()->getValue();

			if( layerBoundary && depthChannel != "" )
			{
				if( !ImageAlgo::channelExists( inPlug()->channelNamesPlug()->getValue()->readable(), depthChannel ) )
				{
					throw IECore::Exception( fmt::format( "Cannot find depth channel {}", depthChannel ) );
				}
			}
		}

		const V2i &tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
		const Box2i localDataWindow = BufferAlgo::intersection(
			Box2i( dataWindow.min - tileOrigin, dataWindow.max - tileOrigin ),
			Box2i( V2i( 0 ), V2i( ImagePlug::tileSize() ) )
		);

		// \todo : This should just be
		// h.append( localDataWindow );
		// We're currently working around a bug in Cortex < 10.6.3.1, replace with the simpler form once all
		// dependency packages are on an up-to-date Cortex.
		h.append( localDataWindow.min );
		h.append( localDataWindow.max );

		if( layerBoundary )
		{
			h.append( *layerBoundary );

			if( depthChannel != "" )
			{
				ImagePlug::ChannelDataScope channelDataScope( scope.context() );
				channelDataScope.setChannelName( &depthChannel );
				inPlug()->channelDataPlug()->hash( h );
			}
		}
	}
}

void SATBlur::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == satPlug() )
	{
		// Computing the summed area table is pretty straightforward, we just need to convert the pixel
		// values to running sums horizontally, and then vertically. The only unique thing for this node
		// is that if a layerBoundary is specified in the context, we treat any pixels nearer than that
		// as zero.

		const float *layerBoundary = context->getIfExists< float >( g_layerBoundaryName );
		Context::EditableScope scope( context );
		if( layerBoundary )
		{
			scope.remove( g_layerBoundaryName );
		}

		if( inPlug()->deep() )
		{
			throw IECore::Exception( "Deep not yet supported" );
		}

		ConstFloatVectorDataPtr sourceData = inPlug()->channelDataPlug()->getValue();

		std::string depthChannel;
		Box2i dataWindow;
		{
			ImagePlug::GlobalScope c( scope.context() );
			depthChannel = depthChannelPlug()->getValue();
			dataWindow = inPlug()->dataWindowPlug()->getValue();
		}

		const V2i &tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
		const Box2i localDataWindow = BufferAlgo::intersection(
			Box2i( dataWindow.min - tileOrigin, dataWindow.max - tileOrigin ),
			Box2i( V2i( 0 ), V2i( ImagePlug::tileSize() ) )
		);

		ConstFloatVectorDataPtr depthData;
		const std::vector<float> *depth = nullptr;
		if( layerBoundary )
		{
			if( depthChannel != "" )
			{
				ImagePlug::ChannelDataScope channelDataScope( scope.context() );
				channelDataScope.setChannelName( &depthChannel );
				depthData = inPlug()->channelDataPlug()->getValue();
				depth = &depthData->readable();
			}
		}

		const std::vector<float> &source = sourceData->readable();

		FloatVectorDataPtr resultData = new FloatVectorData();
		std::vector<float> &result = resultData->writable();
		result.reserve( ImagePlug::tilePixels() );

		Imath::V2i p;
		for( p.y = 0; p.y < ImagePlug::tileSize(); p.y++ )
		{
			if( !( p.y >= localDataWindow.min.y && p.y < localDataWindow.max.y ) )
			{
				// Skip whole scanlines outside the data window
				result.insert( result.end(), ImagePlug::tileSize(), 0.0f );
				continue;
			}

			float accum = 0;
			for( p.x = 0; p.x < ImagePlug::tileSize(); p.x++ )
			{
				if( !( p.x >= localDataWindow.min.x && p.x < localDataWindow.max.x ) )
				{
					// Skip pixels outside that data window
					result.push_back( accum );
					continue;
				}

				int index = ImagePlug::pixelIndex( p, Imath::V2i( 0 ) );
				if( !depth )
				{
					// Convert pixels to running horizontal sum
					accum += source[ index ];
				}
				else
				{
					// If we have a depth to check, check it, then convert pixels to running horizontal sum
					if( (*depth)[ index ] > *layerBoundary )
					{
						accum += source[ index ];
					}
				}
				result.push_back( accum );
			}
		}

		// Perform a running vertical sum as well
		for( p.x = 0; p.x < ImagePlug::tileSize(); p.x++ )
		{
			float accum = 0;
			p.y = 0;
			int index = ImagePlug::pixelIndex( p, Imath::V2i( 0 ) );
			for( ; p.y < ImagePlug::tileSize(); p.y++ )
			{
				accum += result[ index ];
				result[ index ] = accum;
				index += ImagePlug::tileSize();
			}
		}

		static_cast<FloatVectorDataPlug *>( output )->setValue( resultData );
	}
	else
	{
		ImageProcessor::compute( output, context );
	}
}

Gaffer::ValuePlug::CachePolicy SATBlur::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == satPlug() )
	{
		// There isn't actually anything in the calculation of satPlug that is worth parallelizing,
		// but due to the high contention on this plug, there's still a measurable benefit to having other
		// threads wait instead of repeating the work.
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return ImageNode::computeCachePolicy( output );
}

void SATBlur::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelData( parent, context, h );

	int maxRadiusInt;
	Box2i dataWindow;
	std::string radiusChannel;
	std::string depthLookupChannel;


	ConstFloatVectorDataPtr layerBoundariesData;
	const std::vector<float> *layerBoundaries;
	{
		ImagePlug::GlobalScope c( context );
		inPlug()->deepPlug()->hash( h );
		radiusPlug()->hash( h );
		boundingModePlug()->hash( h );
		filterPlug()->hash( h );
		diskRectanglesPlug()->hash( h );
		radiusChannel = radiusChannelPlug()->getValue();
		depthLookupChannel = depthLookupChannelPlug()->getValue();
		maxRadiusPlug()->hash( h );
		maxRadiusInt = ceilf( maxRadiusPlug()->getValue() );
		layerBoundariesData = layerBoundariesPlug()->getValue();
		layerBoundaries = &layerBoundariesData->readable();
		inPlug()->dataWindowPlug()->hash( h );
		dataWindow = inPlug()->dataWindowPlug()->getValue();

		if( radiusChannel.size() )
		{
			if( !ImageAlgo::channelExists( inPlug()->channelNamesPlug()->getValue()->readable(), radiusChannel ) )
			{
				throw IECore::Exception( fmt::format( "Cannot find radius channel {}", radiusChannel ) );
			}
		}

		if( layerBoundaries->size() && depthLookupChannel != "" )
		{
			if( !ImageAlgo::channelExists( inPlug()->channelNamesPlug()->getValue()->readable(), depthLookupChannel ) )
			{
				throw IECore::Exception( fmt::format( "Cannot find depth lookup channel {}", depthLookupChannel ) );
			}
		}
	}

	h.append( *layerBoundaries );

	const V2i &tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );

	const Box2i possibleInBound = BufferAlgo::intersection(
		dataWindow,
		Box2i( tileOrigin - V2i( maxRadiusInt ), tileOrigin + V2i( ImagePlug::tileSize() + maxRadiusInt ) )
	);
	const Box2i possibleTileBound = Box2i( ImagePlug::tileOrigin( possibleInBound.min ), ImagePlug::tileOrigin( possibleInBound.max - V2i( 1 ) ) + V2i( ImagePlug::tileSize() ) );

	ImagePlug::ChannelDataScope channelDataScope( context );

	if( radiusChannel.size() )
	{
		channelDataScope.setChannelName( &radiusChannel );
		inPlug()->channelDataPlug()->hash( h );
	}

	static const float g_zero( 0 );
	if( layerBoundaries->size() && depthLookupChannel.size() )
	{
		channelDataScope.setChannelName( &depthLookupChannel );
		inPlug()->channelDataPlug()->hash( h );

		// Need some flag so that we don't hash the same with just a depth channel as with just
		// a radius channel.
		h.append( true );

		// We don't need to actually pass the different layer boundaries when we
		// evaluate satPlug - the hash function for any layer will include all the
		// inputs that affect every layer. But we do need to set the layer boundary
		// context variable to something, just as a flag that we need include the
		// depth channel in the satPlug() hash.
		channelDataScope.set<float>( g_layerBoundaryName, &g_zero );
	}

	channelDataScope.setChannelName( &channelName );
	V2i inTileOrigin;
	for( inTileOrigin.y = possibleTileBound.min.y; inTileOrigin.y < possibleTileBound.max.y; inTileOrigin.y += ImagePlug::tileSize() )
	{
		for( inTileOrigin.x = possibleTileBound.min.x; inTileOrigin.x < possibleTileBound.max.x; inTileOrigin.x += ImagePlug::tileSize() )
		{
			channelDataScope.setTileOrigin( &inTileOrigin );
			satPlug()->hash( h );
		}
	}

	// In case the possibleTileBound includes the whole image, it's important to include our own offset for which
	// part of the image we're using
	h.append( possibleTileBound.min - tileOrigin );
	h.append( possibleTileBound.max - tileOrigin );
}

namespace {

// Helper function with logic from computeChannelData that needs to be called multiple times
float readSat(
	const V2i &tileOrigin, const V2i &outPixel, float floatX, float floatY, const V2f &inputRad,
	const Box2i &possibleTileBound, const Box2i &inputTileBound, const V2i &visitOrderPermutate,
	const FloatVectorDataPlug *satPlug, ImagePlug::ChannelDataScope &tileScope,
	ConstFloatVectorDataPtr* satData, const std::vector<float>** satDataReadable,
	const std::vector< Box2f > &rects
)
{
	const int possibleTileBoundWidth = possibleTileBound.size().x;

	if( inputRad.x == 0.0f && inputRad.y == 0.0f )
	{
		V2i tile2DIndex = ImagePlug::tileIndex( tileOrigin ) - possibleTileBound.min;
		int tileIndex = tile2DIndex.y * possibleTileBoundWidth + tile2DIndex.x;

		if( !satDataReadable[ tileIndex ] )
		{
			tileScope.setTileOrigin( &tileOrigin );
			satData[tileIndex] = satPlug->getValue();
			satDataReadable[tileIndex] = &satData[tileIndex]->readable();
		}

		return satReconstructPixel( outPixel, *satDataReadable[tileIndex] );
	}

	const V2i inputTileBoundSize = inputTileBound.size();
	float ret = 0;
	for( int sy = 0; sy < inputTileBoundSize.y; sy++ )
	{
		for( int sx = 0; sx < inputTileBoundSize.x; sx++ )
		{
			Imath::V2i sp(
				inputTileBound.min.x + ( visitOrderPermutate.x + sx ) % inputTileBoundSize.x,
				inputTileBound.min.y + ( visitOrderPermutate.y + sy ) % inputTileBoundSize.y
			);
			V2i tile2DIndex = sp - possibleTileBound.min;
			int tileIndex = tile2DIndex.y * possibleTileBoundWidth + tile2DIndex.x;

			V2i spTileOrigin = sp * ImagePlug::tileSize();
			if( !satDataReadable[ tileIndex ] )
			{
				tileScope.setTileOrigin( &spTileOrigin );
				satData[tileIndex] = satPlug->getValue();
				satDataReadable[tileIndex] = &satData[tileIndex]->readable();
			}

			const vector<float> &sat = *satDataReadable[tileIndex];

			float floatXLocal = floatX + tileOrigin.x - spTileOrigin.x;
			float floatYLocal = floatY + tileOrigin.y - spTileOrigin.y;

			int minRect = 0;
			int maxRect = rects.size() - 1;

			// If our kernel involves multiple rectangles, it's worth doing a quick pre-scan to
			// determine which ones may contribute to this tile
			if( maxRect > 1 )
			{
				float radRelativeBoundMin = ( -floatYLocal - 1 ) / inputRad.y;
				float radRelativeBoundMax = ( float(ImagePlug::tileSize() - 1) - floatYLocal ) / inputRad.y;
				while( rects[minRect].max.y < radRelativeBoundMin && minRect <= maxRect )
				{
					minRect++;
				}

				while( rects[maxRect].min.y > radRelativeBoundMax && maxRect >= minRect )
				{
					maxRect--;
				}
			}

			for( int i = minRect; i <= maxRect; i++ )
			{
				const Box2f &r = rects[i];
				ret +=
					satBilinear( floatXLocal + inputRad.x * r.min.x, floatYLocal + inputRad.y * r.min.y, sat ) +
					satBilinear( floatXLocal + inputRad.x * r.max.x, floatYLocal + inputRad.y * r.max.y, sat ) -
					satBilinear( floatXLocal + inputRad.x * r.min.x, floatYLocal + inputRad.y * r.max.y, sat ) -
					satBilinear( floatXLocal + inputRad.x * r.max.x, floatYLocal + inputRad.y * r.min.y, sat );
			}
		}
	}

	return ret;
}

} // namespace

IECore::ConstFloatVectorDataPtr SATBlur::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	if( inPlug()->deep() )
	{
		throw IECore::Exception( "Deep not yet supported" );
	}

	Box2i dataWindow;
	V2f radius;
	std::string radiusChannel;
	BoundingMode boundingMode;
	std::string depthLookupChannel;
	float maxRadius;
	bool diskApprox;
	int diskRectangles;
	ConstFloatVectorDataPtr layerBoundariesData;

	{
		ImagePlug::GlobalScope c( context );
		dataWindow = inPlug()->dataWindowPlug()->getValue();
		radius = radiusPlug()->getValue();
		radiusChannel = radiusChannelPlug()->getValue();
		boundingMode = (BoundingMode)boundingModePlug()->getValue();
		diskApprox = filterPlug()->getValue() == "disk";
		diskRectangles = diskRectanglesPlug()->getValue();
		maxRadius = maxRadiusPlug()->getValue();

		layerBoundariesData = layerBoundariesPlug()->getValue();
		depthLookupChannel = depthLookupChannelPlug()->getValue();
	}

	const std::vector<float> &layerBoundaries = layerBoundariesData->readable();

	int maxRadiusInt = ceilf( maxRadius + 0.5f );

	ImagePlug::ChannelDataScope tileScope( context );

	ConstFloatVectorDataPtr radiusData;
	const std::vector<float> *radiuses = nullptr;

	if( radiusChannel.size() )
	{
		tileScope.setChannelName( &radiusChannel );
		radiusData = inPlug()->channelDataPlug()->getValue();
		radiuses = &radiusData->readable();
		tileScope.setChannelName( &channelName );
	}

	ConstFloatVectorDataPtr depthLookupData;
	const std::vector<float> *depthLookups = nullptr;

	if( layerBoundaries.size() && depthLookupChannel.size() )
	{
		tileScope.setChannelName( &depthLookupChannel );
		depthLookupData = inPlug()->channelDataPlug()->getValue();
		depthLookups = &depthLookupData->readable();
		tileScope.setChannelName( &channelName );
	}

	const Box2i possibleInBound = BufferAlgo::intersection(
		dataWindow,
		Box2i( tileOrigin - V2i( maxRadiusInt ), tileOrigin + V2i( ImagePlug::tileSize() + maxRadiusInt ) )
	);
	const Box2i possibleTileBound = Box2i( ImagePlug::tileIndex( possibleInBound.min ), ImagePlug::tileIndex( possibleInBound.max - V2i( 1 ) ) + V2i( 1 ) );

	// We use a fixed size vector cache with an entry for every tile we may use - this gives us fast,
	// constant time access when reusing tiles ( this is crucial because for large radiuses, every
	// input tile could be used by every output pixel ).

	// We need to store the ConstFloatVectorDataPtr in order to keep alive the tiles we're using
	std::vector< ConstFloatVectorDataPtr > satData;
	// Storing the readable() result instead of recalling readable() is an easy minor performance improvement
	// ( about 5% when accessing a lot of tiles )
	std::vector< const std::vector<float>* > satDataReadable;

	const int layerTiles = possibleTileBound.size().x * possibleTileBound.size().y;
	satData.resize( layerTiles * ( layerBoundaries.size() + 1 ) );
	satDataReadable.resize( layerTiles * ( layerBoundaries.size() + 1 ), nullptr );

	FloatVectorDataPtr resultData = new FloatVectorData();
	std::vector<float> &result = resultData->writable();
	result.reserve( ImagePlug::tilePixels() );

	std::vector<Box2f> rects;

	float normalization;

	if( !diskApprox )
	{
		rects.push_back( Box2f( V2f( -1 ), V2f( 1 ) ) );
		normalization = 1.0f;
	}
	else
	{
		rects = diskApproximationRects( diskRectangles );

		float totalArea = 0.0f;
		for( const Box2f &b : rects )
		{
			totalArea += b.size().x * b.size().y;
		}
		normalization = 4.0f / totalArea;
	}


	Imath::V2i outPixel;
	for( outPixel.y = 0; outPixel.y < ImagePlug::tileSize(); outPixel.y++ )
	{
		const float floatY = float( outPixel.y ) - 0.5f;
		for( outPixel.x = 0; outPixel.x < ImagePlug::tileSize(); outPixel.x++ )
		{
			if( !BufferAlgo::contains( dataWindow, tileOrigin + outPixel ) )
			{
				result.push_back( 0.0f );
				continue;
			}

			const float floatX = float( outPixel.x ) - 0.5f;

			V2f curRadius = radius;
			if( radiuses )
			{
				curRadius *= (*radiuses)[ ImagePlug::pixelIndex( outPixel, Imath::V2i( 0 ) ) ];
			}

			// Skip actual blurring for radiuses that are within a reasonable tolerance of zero.
			bool noBlur = fabs( curRadius.x ) <= 1e-6f && fabs( curRadius.y ) <= 1e-6f;

			// The total input radius we actually use includes this half pixel offset because the user
			// specified radius doesn't include the pixel itself.
			const V2f inputRad = noBlur ? V2f( 0.0f ) : V2f(
				0.5f + std::min( maxRadius, fabs( curRadius.x ) ),
				0.5f + std::min( maxRadius, fabs( curRadius.y ) )
			);

			if( boundingMode == BoundingMode::Normalize && !noBlur )
			{
				// When we're in normalize mode, we recompute the normalization for each pixel, based
				// how much of each box is inside the dataWindow

				// Rather than transforming each box, we transform the dataWindow once to be in the space
				// of the default kernel.
				Box2f relativeDataWindow( ( V2f( dataWindow.min ) - V2f( 0.5 ) - outPixel - tileOrigin ) / inputRad, ( V2f( dataWindow.max ) - V2f( 0.5 ) - outPixel - tileOrigin ) / inputRad );

				float totalArea = 0;
				for( const Box2f &r : rects )
				{
					// Compute the area of the part of this rectangle inside the dataWindow.
					totalArea += std::max( 0.0f,
						std::min( r.max.x, relativeDataWindow.max.x ) -
						std::max( r.min.x, relativeDataWindow.min.x )
					) * std::max( 0.0f,
						std::min( r.max.y, relativeDataWindow.max.y ) -
						std::max( r.min.y, relativeDataWindow.min.y )
					);
				}
				normalization = 4.0f / totalArea;
			}

			int layerIndex = 0;
			float layerLerp = 0.0f;

			// If we're using layerBoundaries, we need to figure out the index of two closest boundaries,
			// and the lerp value we're using to blend between them.
			if( layerBoundaries.size() && depthLookups )
			{
				float depthLookup = (*depthLookups)[ ImagePlug::pixelIndex( outPixel, Imath::V2i( 0 ) ) ];
				layerIndex = -1 + ( std::lower_bound( layerBoundaries.begin(), layerBoundaries.end(), depthLookup ) - layerBoundaries.begin() );

				layerIndex = std::max( 0, std::min( (int)layerBoundaries.size() - 2, layerIndex ) );

				layerLerp = ( depthLookup - layerBoundaries[layerIndex] ) / ( layerBoundaries[layerIndex + 1] - layerBoundaries[layerIndex] );

				// If an image is locally flat in depth, we don't want the region to receive zero contribution
				// from itself, so we bias the depth by 0.01.
				//
				// This kind of only makes sense if you're expecting something like an unpremult step afterwards,
				// I do sort of wonder whether the unpremult should be part of this node ... but maybe there
				// could be something use case for this node without an unpremult ... and the multilayer features
				// of both DiskBlur and SATBlur are both quite technical, and a bit specific to FocalBlur.
				layerLerp -= 0.01f;

				if( layerLerp < 0.0f )
				{
					layerIndex--;
					layerLerp += 1.0f;
				}

				if( layerIndex < 0 )
				{
					layerIndex = 0;
					layerLerp = 0.0f;
				}

				layerLerp = std::max( 0.0f, std::min( 1.0f, layerLerp ) );
			}

			V2i curRadiusInt( ceilf( inputRad.x ), ceilf( inputRad.y ) );

			// Find all the tiles that contribute to this output pixel
			const Box2i inputBound = BufferAlgo::intersection(
				dataWindow,
				Box2i( outPixel + tileOrigin - curRadiusInt, outPixel + tileOrigin + curRadiusInt + V2i( 1 ) )
			);
			const Box2i inputTileBound(
				ImagePlug::tileIndex( inputBound.min ),
				ImagePlug::tileIndex( inputBound.max - V2i( 1 ) ) + V2i( 1 )
			);

			// This is a rather odd optimization, which doesn't always help, but it's also pretty simple:
			// if the radius is large, every output tile depends on many input tiles. If every output tile
			// starts evaluating the region of contributing input tiles in the same corner, then the
			// boundaries of the output image will involve many output tiles simultaneously trying to
			// evaluate the same input tiles. If the input is slow and not threaded, this is terrible for
			// performance. This offset shifts things so that each output tile first evaluates the
			// corresponding input tile, before evaluating its neighbours. This sometimes provides
			// a noticeable benefit.
			//
			// A proper solution to this problem might look something like John's suggestion of a
			// collaborative extension to ImageSampler that would allow image nodes to declare a range
			// of input tiles they want, so that if something is already computing the first tile they
			// want, they can compute other tiles they want.
			//
			// Actually, this makes me wonder if there is a way of expressing this that isn't specific
			// to images ... any time a node has a long list of input values it needs, it would be nice
			// if it was possible to initially skip over inputs that are already being computed, and
			// start evaluating other inputs, rather than trying to join the compute of the first input.
			//
			// But anyway, that is extremely out-of-scope. For the moment, this little offset isn't doing
			// any harm, and sometimes helps.
			const V2i visitOrderPermutate = ImagePlug::tileIndex( tileOrigin ) - inputTileBound.min;

			float val = 0.0f;

			if( !( layerBoundaries.size() && depthLookups ) )
			{
				// Just doing a simple one layer lookup
				val = readSat(
					tileOrigin, outPixel, floatX, floatY, inputRad,
					possibleTileBound, inputTileBound, visitOrderPermutate,
					satPlug(),
					tileScope, &satData[0], &satDataReadable[0],
					rects
				);
			}
			else
			{
				// We're in multilayer mode, so we may need to look up two layers, and blend between them.
				for( int layerSwitch = 0; layerSwitch < 2; layerSwitch++ )
				{
					int planeIndex = layerIndex + layerSwitch;
					float curWeight = layerSwitch ? layerLerp : 1.0f - layerLerp;

					if( curWeight == 0.0f )
					{
						continue;
					}

					if( planeIndex > 0 )
					{
						tileScope.set<float>( g_layerBoundaryName, &layerBoundaries[planeIndex ] );
					}
					else
					{
						tileScope.remove( g_layerBoundaryName );
					}

					val += curWeight * readSat(
						tileOrigin, outPixel, floatX, floatY, inputRad,
						possibleTileBound, inputTileBound, visitOrderPermutate,
						satPlug(),
						tileScope, &satData[layerTiles * planeIndex], &satDataReadable[layerTiles * planeIndex],
						rects
					);
				}
			}

			if( noBlur )
			{
				result.push_back( val );
			}
			else
			{
				result.push_back( val * normalization / ( inputRad.x * inputRad.y * 4.0f ) );
			}
		}
	}

	return resultData;
}
