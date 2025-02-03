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

#include "GafferImage/DiskBlur.h"

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

// How many entries per pixel increment of radius in the table of which pixels are covered by a disk.
// 4 means we will be accurate to the quarter pixel.
constexpr int g_lutDensity = 4;

// Should we allow choosing the alpha channel for occlusion?
const std::string g_alphaChannelName = "A";

// TODO - All this scanline logic could really use some more commenting.
std::pair< int, int > scanlineLUTForIndex( int i )
{
	int lutSize = i / g_lutDensity + 2;
	int fraction = i % g_lutDensity;

	int startIndex = ( ( ( lutSize * ( lutSize - 1 ) ) >> 1 ) - 1 ) * g_lutDensity + lutSize * fraction;
	return { lutSize, startIndex };
}

float radiusForLUTIndex( int i )
{
	constexpr float g_lutDensityInv = 1.0f / float( g_lutDensity );
	return float( i ) * g_lutDensityInv + 1.0f;
}

float lutIndexForRadius( float radius )
{
	return ( ( radius - 1.0f ) * float( g_lutDensity ) ) ;
}

// Fill a table with how large the scanlines are that are covered by a disk.
// Return a normalization factor that is the inverse of the area of the disk.
float precalcScanlineSizes( float radius, uint16_t *result, int resultSize )
{
	int radiusSquared = floorf( radius * radius );

	int x = resultSize;
	int slope = 0;

	int area = 0;
	for( int y = 0; y < resultSize; y++ )
	{
		int ySquared = y*y;
		int nextX = x - slope;
		while( nextX >= 0 && ySquared + nextX*nextX > radiusSquared )
		{
			nextX--;
		}

		slope = std::max( 0, x - nextX - 1 );
		x = nextX;
		result[y] = x;
		area += x;
	}

	// We measure the area of just a quarter of the disk, excluding the center pixel,
	// so `* 4 + 1` gives the total area.
	return 1.0f / float( area * 4 + 1 );
}

// TODO - Would probably be clearer to use std::lower_bound instead of a custom binary search, but the performance
// of this has been oddly sensitive to changing details, so this would require some performance testing.
inline int binarySearchLessThanEqual( const uint16_t *vec, int val, int min, int max )
{
	if( vec[ min ] <= val )
	{
		return min;
	}
	if( vec[ max - 1 ] > val )
	{
		return max;
	}
	while( max - min > 1 )
	{
		int midPoint = ( min + max ) >> 1;
		if( vec[ midPoint ] <= val )
		{
			max = midPoint;
		}
		else
		{
			min = midPoint;
		}
	}
	return max;
}

// TODO - this badly needs commenting, but I'm scrambling now to get a PR up.
template< int dir >
inline int applyScanlineHalfKernel( int minRowInd, int maxRowInd, int centerX, int centerY, float value, const uint16_t *rowsSimple, std::vector<float> &accumBuffer )
{
	if( !( maxRowInd > minRowInd ) )
	{
		return -1;
	}
	int leftMinRowInd = binarySearchLessThanEqual( rowsSimple, centerX, minRowInd, maxRowInd );
	int leftMaxRowInd = binarySearchLessThanEqual( rowsSimple, centerX - ImagePlug::tileSize(), leftMinRowInd, maxRowInd );
	for( int i = leftMinRowInd; i < leftMaxRowInd; i++ )
	{
		int inner = rowsSimple[i];
		accumBuffer[ ( ( centerY + dir * i ) << ImagePlug::tileSizeLog2() ) + centerX - inner ] += value;
	}

	int rightMinRowInd = binarySearchLessThanEqual( rowsSimple, ImagePlug::tileSize() - centerX - 2 , minRowInd, maxRowInd );
	int rightMaxRowInd = binarySearchLessThanEqual( rowsSimple, -centerX - 1, rightMinRowInd, maxRowInd );

	for( int i = rightMinRowInd; i < rightMaxRowInd; i++ )
	{
		int inner = rowsSimple[i];
		accumBuffer[ ( ( centerY + dir * i ) << ImagePlug::tileSizeLog2() ) + centerX + inner + 1 ] -= value;
	}

	if( leftMinRowInd > minRowInd )
	{
		// Don't include solid rows that never actually reach the start of this tile
		return std::min( leftMinRowInd, rightMaxRowInd );
	}
	else
	{
		return -1;
	}

}

void renderTinyDisk(
	const V2i &p, float radius, const float value, std::vector<float> &result
)
{
	// Special case for radius < 1.0
	// It doesn't really make sense for these extremely tiny disks to think of it as rasterizing a circle,
	// and we don't want to try and use the accumulation buffer for these ( since there are no runs of >1
	// pixel of the same value ), so we have a special case that just writes values to the 9 pixels touched
	// by a pixel convolved with a disk of radius 1.

	// The values are chosen as follows:
	// * the center pixel is set to value of 1
	// * the 4 edge pixels are set to a value of the radius
	// * the 4 corner pixels are set to a value of radius^2 * ( 2 - sqrt( 2 ) )
	// ( this is chosen so it matches the regular renderDisk when radius == 1 )
	// Then the values are normalized, and multiplied by the value we are rendering.

	float corner = radius * radius * ( 2.0f - sqrtf( 2.0f ) );
	float normalization = 1.0f / ( 1.0f + 4.0f * ( radius + corner ) );

	float cornerVal = corner * value * normalization;
	float edgeVal = radius * value * normalization;
	float centerVal = value * normalization;

	if(
		p.x >= 1 && p.x < ImagePlug::tileSize() - 1 &&
		p.y >= 1 && p.y < ImagePlug::tileSize() - 1
	)
	{
		// Fast path, we're not straddling a tile boundary, so we just unconditionally add to 9 pixels
		int i = ( ( p.y - 1 ) << ImagePlug::tileSizeLog2() ) + p.x - 1;
		result[ i++ ] += cornerVal;
		result[ i++ ] += edgeVal;
		result[ i ] += cornerVal;

		i = ( ( p.y ) << ImagePlug::tileSizeLog2() ) + p.x - 1;
		result[ i++ ] += edgeVal;
		result[ i++ ] += centerVal;
		result[ i ] += edgeVal;

		i = ( ( p.y + 1 ) << ImagePlug::tileSizeLog2() ) + p.x - 1;
		result[ i++ ] += cornerVal;
		result[ i++ ] += edgeVal;
		result[ i ] += cornerVal;
	}
	else
	{
		// If we are straddling a tile boundary, this is a special case where performance is way less important
		if( p.y - 1 >= 0 && p.y - 1 < ImagePlug::tileSize() )
		{
			if( p.x - 1 >= 0 )
			{
				result[( ( p.y - 1 ) << ImagePlug::tileSizeLog2() ) + p.x - 1] += cornerVal;
			}
			if( p.x >= 0 && p.x < ImagePlug::tileSize() )
			{
				result[( ( p.y - 1 ) << ImagePlug::tileSizeLog2() ) + p.x] += edgeVal;
			}
			if( p.x + 1 < ImagePlug::tileSize() )
			{
				result[( ( p.y - 1 ) << ImagePlug::tileSizeLog2() ) + p.x + 1] += cornerVal;
			}
		}
		if( p.y >= 0 && p.y < ImagePlug::tileSize() )
		{
			if( p.x - 1 >= 0 )
			{
				result[( ( p.y ) << ImagePlug::tileSizeLog2() ) + p.x - 1] += edgeVal;
			}
			if( p.x >= 0 && p.x < ImagePlug::tileSize() )
			{
				result[( ( p.y ) << ImagePlug::tileSizeLog2() ) + p.x] += centerVal;
			}
			if( p.x + 1 < ImagePlug::tileSize() )
			{
				result[( ( p.y ) << ImagePlug::tileSizeLog2() ) + p.x + 1] += edgeVal;
			}
		}
		if( p.y + 1 >= 0 && p.y + 1 < ImagePlug::tileSize() )
		{
			if( p.x - 1 >= 0 )
			{
				result[( ( p.y + 1 ) << ImagePlug::tileSizeLog2() ) + p.x - 1] += cornerVal;
			}
			if( p.x >= 0 && p.x < ImagePlug::tileSize() )
			{
				result[( ( p.y + 1 ) << ImagePlug::tileSizeLog2() ) + p.x] += edgeVal;
			}
			if( p.x + 1 < ImagePlug::tileSize() )
			{
				result[( ( p.y + 1 ) << ImagePlug::tileSizeLog2() ) + p.x + 1] += cornerVal;
			}
		}
	}
}

// TODO - This could absolutely use some documentation.
void addScanlinesToAccumulators(
	const V2i &p, int lutSize, const uint16_t *scanlineSizes, float normalizedValue,
	std::vector<float> &accumBuffer, std::vector<double> &vertAccumBuffer
)
{
	int lowestY = std::max( 0, p.y - ( lutSize - 1 ) );
	int highestY = std::min( ImagePlug::tileSize() - 1, p.y + lutSize - 1 );

	int solidDown =
	applyScanlineHalfKernel<-1>(
		std::max( 1, p.y - highestY ), p.y - lowestY + 1,
		p.x, p.y, normalizedValue,
		scanlineSizes, accumBuffer
	);
	int solidUp =
	applyScanlineHalfKernel<1>(
		std::max( 0, lowestY - p.y ), highestY - p.y + 1,
		p.x, p.y, normalizedValue,
		scanlineSizes, accumBuffer
	);
	int solidStart = std::max( 0, p.y + ( solidDown != -1 ? ( - solidDown + 1 ) : 0 ) );
	int solidEnd = p.y + ( solidUp != -1 ? solidUp : 0 );

	if( solidStart < solidEnd && solidStart < ImagePlug::tileSize())
	{
		vertAccumBuffer[solidStart] += normalizedValue;

		if( solidEnd > 0 && solidEnd < ImagePlug::tileSize() )
		{
			vertAccumBuffer[solidEnd] -= normalizedValue;
		}
	}
}

// Add the anti-aliased pixels on the edge of the scanline that are outside of the solid region we render
// to the scanline accumulator
inline void addEdgeFalloff(
	int lowestX, int highestX, int y, float normalizedValue, int centerX, int dy2, float radius,
	std::vector<float> &result
)
{
	if( highestX >= lowestX )
	{
		for( int x = lowestX; x <= highestX; x++ )
		{
			int dx = x - centerX;
			// This sqrt definitely has performance a cost, and for any sizeable radius, the error from
			// just applying a linear blend from innerRadius**2 to outerRadius**2 instead of doing an actual
			// sqrt would be neglible. But doing it correctly with a sqrt makes the normalization math a bit
			// cleaner, and it makes this node more canonically correct, and the performance loss isn't
			// significant as long as approximationThreshold is set reasonably ( since then most large
			// disks won't be anti-aliased at all ).
			float falloff = 1.0 - ( sqrtf( dx * dx + dy2 ) - radius );

			result[ ( y << ImagePlug::tileSizeLog2() ) + x ] += normalizedValue * std::max( 0.0f, std::min( 1.0f, falloff ) );
		}
	}
}

void renderDisk(
	const V2i &p, float radius, const float value, const float approximationThreshold,
	const std::vector<uint16_t> &lutScanlineSizes, const std::vector<float> &lutNormalizations, const std::vector<float> &lutDistances, int distanceLUTSize,
	const std::vector<V2f> &floatNormalizations, const std::vector<int> &floatNormalizationRanges,
	std::vector<float> &accumBuffer, std::vector<double> &vertAccumBuffer, std::vector<float> &result
)
{
	int intRadius = ceilf( radius );

	// Early out to test if all x values are outside this tile ( we don't want to repeat this test for every scanline )
	if(
		p.x - intRadius >= ImagePlug::tileSize() ||
		p.x + intRadius < 0
	)
	{
		return;
	}
	if(
		p.y - intRadius >= ImagePlug::tileSize() ||
		p.y + intRadius < 0
	)
	{
		return;
	}

	if( radius < 1.0f )
	{
		renderTinyDisk( p, radius, value, result );
		return;
	}

	const float fullRadius = radius + 0.5;
	int lutIndex = roundf( lutIndexForRadius( fullRadius ) );

	const float quantizedNormalizedValue = value * lutNormalizations[ lutIndex ];

	if( quantizedNormalizedValue <= approximationThreshold )
	{
		// If each pixel contribution we're making is under the approximationThreshold, we don't need to
		// anti-alias the edges, and we can just render this disk to the accumulation buffers.
		auto [ lutSize, scanlineIndex ] = scanlineLUTForIndex( lutIndex );

		assert( lutSize <= 1 + intRadius );

		addScanlinesToAccumulators(
			p, lutSize, &lutScanlineSizes[scanlineIndex], quantizedNormalizedValue,
			accumBuffer, vertAccumBuffer
		);
	}
	else
	{
		int innerLutIndex = floorf( lutIndexForRadius( fullRadius - 0.5f ) );
		int outerLutIndex = ceilf( lutIndexForRadius( fullRadius + 0.5f ) );

		float testRadius = radius + 1.0f;
		size_t normalizationIndex = std::lower_bound(
			floatNormalizations.begin() + floatNormalizationRanges[lutIndex], floatNormalizations.begin() + floatNormalizationRanges[lutIndex + 1], testRadius, [](const V2f &a, float b) { return a.x < b; }
		) - floatNormalizations.begin();
		normalizationIndex = std::min( floatNormalizations.size() - 1, std::max( (size_t)1, normalizationIndex ) );

		V2f a = floatNormalizations[ normalizationIndex - 1];
		V2f b = floatNormalizations[ normalizationIndex ];

		// Approximate the area of this anti-aliased disk using a linear interpolation between values in the
		// table.
		float area = a.y + ( b.y - a.y ) * ( testRadius - a.x ) / ( b.x - a.x );

		float normalizedValue = value / area;

		auto [ innerLutSize, innerScanlineIndex ] = scanlineLUTForIndex( innerLutIndex );
		auto [ outerLutSize, outerScanlineIndex ] = scanlineLUTForIndex( outerLutIndex );

		// Render the solid core of this disk to the accumulation buffers. Then we'll only need to render
		// the anti-aliased edges pixel-by-pixel, and we can still benefit from the scanline accumulators
		// to more quickly render the bulk of the disk.
		addScanlinesToAccumulators(
			p, innerLutSize, &lutScanlineSizes[innerScanlineIndex], normalizedValue,
			accumBuffer, vertAccumBuffer
		);

		// Now render the leftover anti-aliased edges for each scanline.
		int lowestY = std::max( 0, p.y - ( outerLutSize - 1 ) );
		int highestY = std::min( ImagePlug::tileSize() - 1, p.y + outerLutSize - 1 );
		for( int y = lowestY; y <= highestY; y++ )
		{
			int lutRow = abs( y - p.y );
			int outerScanlineSize = lutScanlineSizes[ outerScanlineIndex + lutRow ];
			if( lutRow >= innerLutSize )
			{
				// The final scanline has no solid core, so we evaluate the edge falloff for
				// all the pixel in this scanline.
				addEdgeFalloff(
					std::max( p.x - outerScanlineSize, 0 ),
					std::min( p.x + outerScanlineSize, ImagePlug::tileSize() - 1 ),
					y, normalizedValue, p.x, lutRow * lutRow, radius,
					result
				);
				continue;
			}

			// Handle the anti-aliased pixels to the left of this scanline
			int innerScanlineSize = lutScanlineSizes[ innerScanlineIndex + lutRow ];
			addEdgeFalloff(
				std::max( p.x - outerScanlineSize, 0 ),
				std::min( p.x - innerScanlineSize - 1, ImagePlug::tileSize() - 1 ),
				y, normalizedValue, p.x, lutRow * lutRow, radius,
				result
			);
			// Handle the anti-aliased pixels to the right of this scanline
			addEdgeFalloff(
				std::max( p.x + innerScanlineSize + 1, 0 ),
				std::min( p.x + outerScanlineSize, ImagePlug::tileSize() - 1 ),
				y, normalizedValue, p.x, lutRow * lutRow, radius,
				result
			);
		}

	}
}

// Used in the very slow reference implemenation, where instead of computing the intersection of the disk
// with the current tile, we just blindly render every pixel in the disk, and ignore writes outside the
// current tile.
void safeAddToTile( const V2i &p, const float value, std::vector<double> &result, float *measureAreaOnly )
{
	if( measureAreaOnly )
	{
		// This allows us to use the same code as rendering for brute force area computation instead.
		*measureAreaOnly += value;
		return;
	}

	if( p.x >= 0 && p.y >= 0 && p.x < ImagePlug::tileSize() && p.y < ImagePlug::tileSize() )
	{
		result[ ImagePlug::pixelIndex( p, V2i( 0 ) ) ] += value;
	}
}

// A very slow reference implementation that doesn't use scanline accumulators, or any optimizations at
// all. Should never be used by users, is just useful for verifying correctness.
void renderDiskReferenceImplementation(
	const V2i &p, float radius, float value, bool approximate, std::vector<double> &result,
	float *measureAreaOnly = nullptr
)
{
	if( radius < 1.0f )
	{
		float corner = radius * radius * ( 2.0f - sqrtf( 2.0f ) );

		float cornerVal = corner * value;
		float edgeVal = radius * value;

		safeAddToTile( p + V2i( -1, -1 ), cornerVal, result, measureAreaOnly );
		safeAddToTile( p + V2i(  0, -1 ), edgeVal, result, measureAreaOnly );
		safeAddToTile( p + V2i(  1, -1 ), cornerVal, result, measureAreaOnly );
		safeAddToTile( p + V2i( -1,  0 ), edgeVal, result, measureAreaOnly );
		safeAddToTile( p + V2i(  0,  0 ), value, result, measureAreaOnly );
		safeAddToTile( p + V2i(  1,  0 ), edgeVal, result, measureAreaOnly );
		safeAddToTile( p + V2i( -1,  1 ), cornerVal, result, measureAreaOnly );
		safeAddToTile( p + V2i(  0,  1 ), edgeVal, result, measureAreaOnly );
		safeAddToTile( p + V2i(  1,  1 ), cornerVal, result, measureAreaOnly );

		return;
	}


	if( approximate )
	{
		float roundedRadius = roundf( radius * g_lutDensity ) / g_lutDensity;

		const float fullRadius = roundedRadius + 0.5;

		int intRadius = ceilf( fullRadius );

		V2i q;
		for( q.y = p.y - intRadius; q.y <= p.y + intRadius; q.y++ )
		{
			for( q.x = p.x - intRadius; q.x <= p.x + intRadius; q.x++ )
			{
				V2i d = q - p;
				if( d.x * d.x + d.y * d.y <= fullRadius * fullRadius )
				{
					safeAddToTile( q, value, result, measureAreaOnly );
				}
			}
		}
	}
	else
	{
		const float expandedRadius = radius + 1.0f;

		int intRadius = ceilf( expandedRadius );

		V2i q;
		for( q.y = p.y - intRadius; q.y <= p.y + intRadius; q.y++ )
		{
			for( q.x = p.x - intRadius; q.x <= p.x + intRadius; q.x++ )
			{
				V2i d = q - p;
				float falloff = 1.0 - ( sqrtf( d.x * d.x + d.y * d.y ) - radius ) / ( expandedRadius - radius );
				safeAddToTile( q, value * std::max( 0.0f, std::min( 1.0f, falloff ) ), result, measureAreaOnly );
			}
		}
	}
}

// A chunk size of 8 seems like a decent compromise between skipping as large a region as possible at once,
// while still being useful as an acceleration structure in images with rapidly varying radii.
constexpr int g_chunkSize = 8;

void loadSurroundingTiles(
	const FloatVectorDataPlug *channelPlug, const ObjectVectorPlug *tileBoundPlug,
	const Context *context, const V2i &tileOrigin, const Box2i &dataWindow, int maxRadius,
	const std::string &channelName, const std::string &radiusChannel,

	Box2i &inTileBound,
	std::vector<ConstObjectVectorPtr> &tileBounds,
	std::vector<ConstFloatVectorDataPtr> &channelTiles,
	std::vector<ConstFloatVectorDataPtr> &radiusTiles
)
{
	const Box2i inBound = BufferAlgo::intersection(
		dataWindow,
		Box2i( tileOrigin - V2i( maxRadius ), tileOrigin + V2i( ImagePlug::tileSize() + maxRadius ) )
	);
	inTileBound = Box2i( ImagePlug::tileOrigin( inBound.min ), ImagePlug::tileOrigin( inBound.max - V2i( 1 ) ) + V2i( ImagePlug::tileSize() ) );

	int numContributingTiles = ( inTileBound.size().x / ImagePlug::tileSize() ) * ( inTileBound.size().y / ImagePlug::tileSize() );

	tileBounds.reserve( numContributingTiles );
	channelTiles.reserve( numContributingTiles );
	radiusTiles.reserve( numContributingTiles );


	ImagePlug::ChannelDataScope channelDataScope( context );
	V2i inTileOrigin;
	for( inTileOrigin.y = inTileBound.min.y; inTileOrigin.y < inTileBound.max.y; inTileOrigin.y += ImagePlug::tileSize() )
	{
		for( inTileOrigin.x = inTileBound.min.x; inTileOrigin.x < inTileBound.max.x; inTileOrigin.x += ImagePlug::tileSize() )
		{
			channelDataScope.setTileOrigin( &inTileOrigin );

			channelDataScope.remove( ImagePlug::channelNameContextName );
			ConstObjectVectorPtr tb = tileBoundPlug->getValue();
			if( !BufferAlgo::intersects(
				Box2i( tileOrigin - inTileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) - inTileOrigin ),
				static_cast< const Box2iData*>( tb->members()[0].get() )->readable()
			) )
			{
				tileBounds.push_back( nullptr );
				radiusTiles.push_back( nullptr );
				channelTiles.push_back( nullptr );
				continue;
			}
			tileBounds.push_back( tb );


			if( radiusChannel.size() )
			{
				channelDataScope.setChannelName( &radiusChannel );

				radiusTiles.push_back( channelPlug->getValue() );
			}
			else
			{
				radiusTiles.push_back( nullptr );
			}

			channelDataScope.setChannelName( &channelName );
			channelTiles.push_back( channelPlug->getValue() );

		}
	}
}

void renderTile(
	std::vector<float> &result,
	std::vector<float> &accumBuffer,
	std::vector<double> &vertAccumBuffer,

	const Imath::V2i &tileOrigin,
	const Imath::Box2i &dataWindow,

	float planeMin,
	float planeMax,

	const Box2i &contributingTilesBound,
	const std::vector< ConstFloatVectorDataPtr > &channelTiles,
	float radius,
	const std::vector< ConstFloatVectorDataPtr > &radiusTiles,
	const std::vector< ConstObjectVectorPtr > &tileBounds,

	int maxRadius,
	const ObjectVector *scanlinesLUT,
	int useRefImpl,
	float approximationThreshold,
	const IECore::Canceller *canceller
)
{
	int distanceTableSize = maxRadius + 1;

	int tileIndex = 0;

	if( useRefImpl )
	{
		// Slow reference code path.

		// Use a double precision accumulutator for the reference result - this option is just as a ground truth
		// where we don't care about performance, and if there is any issues with precision, it's useful to
		// have a ground truth to compare to.
		std::vector< double > referenceResult( ImagePlug::tilePixels() );

		// Currently this reference implementation approximates either everything or nothing ... we don't currently
		// have specific test coverage for varying the approximationThreshold
		bool approximate = approximationThreshold != 0.0f;

		V2i inTileOrigin;
		for( inTileOrigin.y = contributingTilesBound.min.y; inTileOrigin.y < contributingTilesBound.max.y; inTileOrigin.y += ImagePlug::tileSize() )
		{
			for( inTileOrigin.x = contributingTilesBound.min.x; inTileOrigin.x < contributingTilesBound.max.x; inTileOrigin.x += ImagePlug::tileSize() )
			{
				if( !channelTiles[tileIndex] )
				{
					tileIndex++;
					continue;
				}

				const std::vector<float> &channel = channelTiles[tileIndex]->readable();

				const float *radiusPixels = nullptr;
				if( radiusTiles[tileIndex] )
				{
					radiusPixels = &( radiusTiles[tileIndex]->readable()[0] );
				}

				const V2i tileOffset = tileOrigin - inTileOrigin;

				const Box2i relativeDataWindow( dataWindow.min - inTileOrigin, dataWindow.max - inTileOrigin );

				for( int y = 0; y < ImagePlug::tileSize(); y++ )
				{
					for( int x = 0; x < ImagePlug::tileSize(); x ++ )
					{
						Canceller::check( canceller );

						V2i p( x, y );

						if( !BufferAlgo::contains( relativeDataWindow, p ) )
						{
							continue;
						}
						int pixelIndex = ImagePlug::pixelIndex( p, V2i( 0 ) );

						float signedRadius = radiusPixels ? radiusPixels[ pixelIndex ] * radius : radius;

						if( signedRadius < planeMin || signedRadius >= planeMax )
						{
							continue;
						}
						float radius = std::min( fabsf( signedRadius ), float( maxRadius ) );


						float value = channel[ pixelIndex ];

						if( value == 0.0f )
						{
							continue;
						}

						// To do a totally accurate brute force rendering with normalization, we make two separate
						// calls, where the first one just measures the area ( the sum of the kernel weight for every
						// pixel this disk touches ).
						float area = 0;
						renderDiskReferenceImplementation(
							p - tileOffset, radius, 1.0f, approximate,
							referenceResult, &area
						);

						float normalizedValue = value / area;

						// And the second call actually renders
						renderDiskReferenceImplementation(
							p - tileOffset, radius, normalizedValue, approximate,
							referenceResult
						);
					}
				}

				tileIndex++;
			}
		}

		for( int i = 0; i < ImagePlug::tilePixels(); i++ )
		{
			// Cast the accumulated result back to float
			result[i] = referenceResult[i];
		}

		return;
	}

	const std::vector<uint16_t> &scanlineSizesLUT = IECore::runTimeCast<IECore::UShortVectorData>( scanlinesLUT->members()[0] )->readable();
	const std::vector<float> &normalizationsLUT = IECore::runTimeCast<IECore::FloatVectorData>( scanlinesLUT->members()[1] )->readable();
	const std::vector<float> &distancesLUT = IECore::runTimeCast<IECore::FloatVectorData>( scanlinesLUT->members()[2] )->readable();
	const std::vector<V2f> &floatNormalizations = IECore::runTimeCast<IECore::V2fVectorData>( scanlinesLUT->members()[3] )->readable();
	const std::vector<int> &floatNormalizationRanges = IECore::runTimeCast<IECore::IntVectorData>( scanlinesLUT->members()[4] )->readable();

	V2i inTileOrigin;
	for( inTileOrigin.y = contributingTilesBound.min.y; inTileOrigin.y < contributingTilesBound.max.y; inTileOrigin.y += ImagePlug::tileSize() )
	{
		for( inTileOrigin.x = contributingTilesBound.min.x; inTileOrigin.x < contributingTilesBound.max.x; inTileOrigin.x += ImagePlug::tileSize() )
		{
			if( !channelTiles[tileIndex] )
			{
				tileIndex++;
				continue;
			}

			const std::vector<float> &channel = channelTiles[tileIndex]->readable();

			ConstFloatVectorDataPtr radiusPixelsData;
			const float *radiusPixels = nullptr;
			if( radiusTiles[tileIndex] )
			{
				radiusPixels = &( radiusTiles[tileIndex]->readable()[0] );
			}


			const V2i tileOffset = tileOrigin - inTileOrigin;
			const Box2i relativeDataWindow( dataWindow.min - inTileOrigin, dataWindow.max - inTileOrigin );

			const std::vector<Box2i> &chunkBounds = static_cast< const Box2iVectorData*>( tileBounds[tileIndex]->members()[1].get() )->readable();
			const std::vector<V2f> &chunkDepths = static_cast< const V2fVectorData*>( tileBounds[tileIndex]->members()[2].get() )->readable();

			const Box2i relativeTargetWindow = Imath::Box2i( tileOffset, tileOffset + Imath::V2i( ImagePlug::tileSize(), ImagePlug::tileSize() ) );

			int chunkIndex = 0;
			for( int cy = 0; cy < ImagePlug::tileSize(); cy += g_chunkSize )
			{
				Canceller::check( canceller );

				for( int cx = 0; cx < ImagePlug::tileSize(); cx += g_chunkSize )
				{
					// Check if each "chunk" of pixels intersects this tile, and this plane. Being able to
					// early reject chunks of pixels all at once can save 30% of runtime when rendering
					// tiny disks, and potentially even more for certain mixtures of small and large radii,
					// and when using many planeDividers.
					if(
						( chunkDepths[chunkIndex].y < planeMin ) ||
						( chunkDepths[chunkIndex].x >= planeMax ) ||
						!BufferAlgo::intersects( relativeTargetWindow, chunkBounds[chunkIndex] )
					)
					{
						chunkIndex++;
						continue;
					}

					Canceller::check( canceller );

					for( int y = 0; y < g_chunkSize; y++ )
					{
						for( int x = 0; x < g_chunkSize; x++ )
						{
							V2i p( cx + x, cy + y );

							if( !BufferAlgo::contains( relativeDataWindow, p ) )
							{
								continue;
							}

							int pixelIndex = ImagePlug::pixelIndex( p, V2i( 0 ) );

							float signedRadius = radiusPixels ? radiusPixels[ pixelIndex ] * radius : radius;

							if( signedRadius < planeMin || signedRadius >= planeMax )
							{
								continue;
							}
							float radius = std::min( fabsf( signedRadius ), float( maxRadius ) );


							float value = channel[ pixelIndex ];

							if( value == 0.0f )
							{
								continue;
							}

							renderDisk(
								p - tileOffset, radius, value, approximationThreshold,
								scanlineSizesLUT, normalizationsLUT, distancesLUT, distanceTableSize,
								floatNormalizations, floatNormalizationRanges,
								accumBuffer, vertAccumBuffer, result
							);
						}
					}

					chunkIndex++;
				}
			}

			tileIndex++;
		}
	}

	float va = 0;
	for( int i = 0; i < ImagePlug::tilePixels(); i += ImagePlug::tileSize() )
	{
		va += vertAccumBuffer[ i >> ImagePlug::tileSizeLog2() ];
		float accum = va;
		for( int j = i; j < i + ImagePlug::tileSize(); j++ )
		{
			accum += accumBuffer[j];
			result[j] += accum;
		}
	}
}

void hashSurroundingTiles(
	const FloatVectorDataPlug *channelPlug,
	const Context *context, const V2i &tileOrigin, const Box2i &dataWindow, int maxRadius,
	const std::string &channelName, const std::string &radiusChannel,
	IECore::MurmurHash &result
)
{
	const Box2i inBound = BufferAlgo::intersection(
		dataWindow,
		Box2i( tileOrigin - V2i( maxRadius ), tileOrigin + V2i( ImagePlug::tileSize() + maxRadius ) )
	);
	const Box2i inTileBound = Box2i( ImagePlug::tileOrigin( inBound.min ), ImagePlug::tileOrigin( inBound.max - V2i( 1 ) ) + V2i( ImagePlug::tileSize() ) );

	ImagePlug::ChannelDataScope channelDataScope( context );
	V2i inTileOrigin;
	for( inTileOrigin.y = inTileBound.min.y; inTileOrigin.y < inTileBound.max.y; inTileOrigin.y += ImagePlug::tileSize() )
	{
		for( inTileOrigin.x = inTileBound.min.x; inTileOrigin.x < inTileBound.max.x; inTileOrigin.x += ImagePlug::tileSize() )
		{
			// Note that the corresponding loadSurroundingTiles includes the tileBoundPlug() here - we don't
			// need to include it because it's just computed from the radius channel, so we still get unique
			// hashes without including it.

			channelDataScope.setTileOrigin( &inTileOrigin );

			if( radiusChannel.size() )
			{
				channelDataScope.setChannelName( &radiusChannel );
				channelPlug->hash( result );
			}

			channelDataScope.setChannelName( &channelName );
			channelPlug->hash( result );
		}
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// DiskBlur node
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( DiskBlur );

size_t DiskBlur::g_firstPlugIndex = 0;

DiskBlur::DiskBlur( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new FloatPlug( "radius", Plug::In, 1.0f ) );
	addChild( new StringPlug( "radiusChannel" ) );
	addChild( new FloatPlug( "approximationThreshold", Plug::In, 0.001f, 0.0f ) );
	addChild( new IntPlug( "maxRadius", Plug::In, 512, 1 ) );
	addChild( new FloatVectorDataPlug( "planeDividers", Plug::In ) );

	addChild( new ObjectVectorPlug( "__tileBound", Plug::Out ) );
	addChild( new ObjectVectorPlug( "__scanlinesLUT", Plug::Out ) );
	addChild( new IntPlug( "__useReferenceImplementation", Plug::In, 0 ) );
	addChild( new ObjectVectorPlug( "__planeWeights", Plug::Out ) );

	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
	outPlug()->viewNamesPlug()->setInput( inPlug()->viewNamesPlug() );

	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
}

DiskBlur::~DiskBlur()
{
}

Gaffer::FloatPlug *DiskBlur::radiusPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex );
}

const Gaffer::FloatPlug *DiskBlur::radiusPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *DiskBlur::radiusChannelPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *DiskBlur::radiusChannelPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::FloatPlug *DiskBlur::approximationThresholdPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::FloatPlug *DiskBlur::approximationThresholdPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

Gaffer::IntPlug *DiskBlur::maxRadiusPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::IntPlug *DiskBlur::maxRadiusPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

Gaffer::FloatVectorDataPlug *DiskBlur::planeDividersPlug()
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::FloatVectorDataPlug *DiskBlur::planeDividersPlug() const
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex + 4 );
}

Gaffer::ObjectVectorPlug *DiskBlur::tileBoundPlug()
{
	return getChild<ObjectVectorPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::ObjectVectorPlug *DiskBlur::tileBoundPlug() const
{
	return getChild<ObjectVectorPlug>( g_firstPlugIndex + 5 );
}

Gaffer::ObjectVectorPlug *DiskBlur::scanlinesLUTPlug()
{
	return getChild<ObjectVectorPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::ObjectVectorPlug *DiskBlur::scanlinesLUTPlug() const
{
	return getChild<ObjectVectorPlug>( g_firstPlugIndex + 6 );
}

Gaffer::IntPlug *DiskBlur::useReferenceImplementationPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::IntPlug *DiskBlur::useReferenceImplementationPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 7 );
}

Gaffer::ObjectVectorPlug *DiskBlur::planeWeightsPlug()
{
	return getChild<ObjectVectorPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::ObjectVectorPlug *DiskBlur::planeWeightsPlug() const
{
	return getChild<ObjectVectorPlug>( g_firstPlugIndex + 8 );
}

void DiskBlur::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( input == maxRadiusPlug() )
	{
		outputs.push_back( scanlinesLUTPlug() );
	}

	if(
		input == radiusPlug() ||
		input == radiusChannelPlug() ||
		input == inPlug()->channelDataPlug() ||
		input == inPlug()->dataWindowPlug() ||
		input == inPlug()->sampleOffsetsPlug() ||
		input == inPlug()->deepPlug() ||
		input == inPlug()->channelNamesPlug()
	)
	{
		outputs.push_back( tileBoundPlug() );
	}

	if(
		input == radiusPlug() ||
		input == radiusChannelPlug() ||
		input == approximationThresholdPlug() ||
		input == scanlinesLUTPlug() ||
		input == inPlug()->channelDataPlug() ||
		input == inPlug()->sampleOffsetsPlug() ||
		input == inPlug()->dataWindowPlug() ||
		input == inPlug()->deepPlug() ||
		input == inPlug()->channelNamesPlug() ||
		input == useReferenceImplementationPlug() ||
		input == maxRadiusPlug() ||
		input == planeDividersPlug() ||
		input == tileBoundPlug()
	)
	{
		outputs.push_back( planeWeightsPlug() );
	}

	if(
		input == radiusPlug() ||
		input == radiusChannelPlug() ||
		input == approximationThresholdPlug() ||
		input == scanlinesLUTPlug() ||
		input == inPlug()->channelDataPlug() ||
		input == inPlug()->sampleOffsetsPlug() ||
		input == inPlug()->dataWindowPlug() ||
		input == inPlug()->deepPlug() ||
		input == inPlug()->channelNamesPlug() ||
		input == useReferenceImplementationPlug() ||
		input == maxRadiusPlug() ||
		input == planeDividersPlug() ||
		input == planeWeightsPlug() ||
		input == tileBoundPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void DiskBlur::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hash( output, context, h );
	if( output == scanlinesLUTPlug() )
	{
		h.append( maxRadiusPlug()->getValue() );
	}
	else if( output == tileBoundPlug() )
	{
		const V2i &tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );

		ConstStringVectorDataPtr channelNames;
		std::string radiusChannel;
		{
			ImagePlug::GlobalScope c( context );

			inPlug()->deepPlug()->hash( h );
			inPlug()->dataWindowPlug()->hash( h );
			h.append( radiusPlug()->getValue() );
			channelNames = inPlug()->channelNamesPlug()->getValue();
			radiusChannel = radiusChannelPlug()->getValue();
		}

		if( radiusChannel.size() )
		{
			if( !ImageAlgo::channelExists( channelNames->readable(), radiusChannel ) )
			{
				throw IECore::Exception( fmt::format( "Cannot find radius channel {}", radiusChannel ) );
			}
			h.append( inPlug()->channelDataHash( radiusChannel, tileOrigin ) );
		}
	}
	else if( output == planeWeightsPlug() )
	{
		const V2i &tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
		h.append( tileOrigin );

		ConstStringVectorDataPtr channelNames;
		std::string radiusChannel;
		Box2i dataWindow;
		{
			ImagePlug::GlobalScope c( context );

			inPlug()->deepPlug()->hash( h );

			channelNames = inPlug()->channelNamesPlug()->getValue();
			inPlug()->dataWindowPlug()->hash( h );
			ConstFloatVectorDataPtr planeDividers = planeDividersPlug()->getValue();

			if(
				planeDividers->readable().size() == 0 ||
				!ImageAlgo::channelExists( channelNames->readable(), g_alphaChannelName )
			)
			{
				// If there are no plane dividers, or there is no alpha channel, then no occlusion
				// occurs between planes, and we don't need to compute plane weights.
				return;
			}

			planeDividersPlug()->hash( h );
			radiusPlug()->hash( h );
			scanlinesLUTPlug()->hash( h );
			useReferenceImplementationPlug()->hash( h );
			approximationThresholdPlug()->hash( h );

			radiusChannel = radiusChannelPlug()->getValue();
			dataWindow = inPlug()->dataWindow();
		}

		const int maxRadius = maxRadiusPlug()->getValue();
		h.append( maxRadius );
		h.append( dataWindow );
		h.append( tileOrigin );

		if( radiusChannel.size() && !ImageAlgo::channelExists( channelNames->readable(), radiusChannel ) )
		{
			throw IECore::Exception( fmt::format( "Cannot find radius channel {}", radiusChannel ) );
		}

		hashSurroundingTiles(
			inPlug()->channelDataPlug(), context, tileOrigin, dataWindow, maxRadius,
			g_alphaChannelName, radiusChannel,
			h
		);
	}
}

void DiskBlur::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == scanlinesLUTPlug() )
	{
		int maxRadius = maxRadiusPlug()->getValue();
		int maxIndex = maxRadius * g_lutDensity;

		UShortVectorDataPtr scanlineSizesData = new UShortVectorData();
		std::vector<uint16_t> &scanlineSizes = scanlineSizesData->writable();

		FloatVectorDataPtr normalizationsData = new FloatVectorData();
		std::vector<float> &normalizations = normalizationsData->writable();

		auto [ finalSize, finalLUTIndex ] = scanlineLUTForIndex( maxIndex - 1 );

		scanlineSizes.resize( finalLUTIndex + finalSize );
		normalizations.resize( maxIndex );

		for( int i = 0; i < maxIndex; i++ )
		{
			auto [ lutSize, scanlineIndex ] = scanlineLUTForIndex( i );
			float radius = radiusForLUTIndex( i );

			normalizations[i] = precalcScanlineSizes( radius, &scanlineSizes[ scanlineIndex ], lutSize );
		}

		FloatVectorDataPtr distancesData = new FloatVectorData();
		std::vector<float> &distances = distancesData->writable();

		int distanceTableSize = maxRadius + 1;
		distances.resize( distanceTableSize * distanceTableSize );
		for( int y = 0; y < distanceTableSize; y++ )
		{
			for( int x = 0; x < distanceTableSize; x++ )
			{
				distances[ y * distanceTableSize + x ] = sqrtf( (float)( x * x + y * y ) );
			}
		}

		V2fVectorDataPtr floatNormalizationsData = new V2fVectorData();
		std::vector<V2f> &floatNormalizations = floatNormalizationsData->writable();

		// TODO - this could sure use documentation.
		std::vector<float> distancesSorted( distances.begin() + distanceTableSize, distances.end() );
		std::sort( distancesSorted.begin(), distancesSorted.end() );

		int queueStart = 0;
		int queueStop = 0;

		float currentScan = 0;
		float currentSlope = 0;
		float currentArea = 0;

		float stop = maxRadius;
		while( currentScan <= stop )
		{
			bool evicting = queueStop < queueStart && distancesSorted[ queueStop ] + 1.0f <= distancesSorted[ queueStart ];
			float nextScan = evicting ? distancesSorted[ queueStop ] + 1.0f : distancesSorted[ queueStart ];
			if( nextScan != currentScan )
			{
				currentArea += currentSlope * ( nextScan - currentScan );

				floatNormalizations.push_back( Imath::V2f( nextScan, currentArea * 4.0f + 1.0f ) );
			}

			if( evicting )
			{
				currentSlope -= 1.0f;
				queueStop++;
			}
			else
			{
				currentSlope += 1.0f;
				queueStart++;
			}
			currentScan = nextScan;
		}

		IntVectorDataPtr floatNormalizationRangesData = new IntVectorData();
		std::vector<int> &floatNormalizationRanges = floatNormalizationRangesData->writable();
		floatNormalizationRanges.resize( maxIndex + 1 );

		for( int i = 0; i < maxIndex; i++ )
		{
			float radius = radiusForLUTIndex( i );

			size_t normalizationIndex = std::lower_bound(
				floatNormalizations.begin(), floatNormalizations.end(), radius + 0.5f * ( 1.0f - 1.0f / float( g_lutDensity ) ), [](const V2f &a, float b) { return a.x < b; }) - floatNormalizations.begin();

			floatNormalizationRanges[i] = normalizationIndex;
		}

		floatNormalizationRanges[maxIndex] = floatNormalizations.size() - 1;

		ObjectVectorPtr result = new ObjectVector();
		result->members().push_back( scanlineSizesData );
		result->members().push_back( normalizationsData );
		result->members().push_back( distancesData );
		result->members().push_back( floatNormalizationsData );
		result->members().push_back( floatNormalizationRangesData );

		static_cast<ObjectVectorPlug *>( output )->setValue( result );
	}
	else if( output == tileBoundPlug() )
	{
		if( inPlug()->deep() )
		{
			throw IECore::Exception( "Deep not yet supported" );
		}

		const V2i &tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );

		ConstStringVectorDataPtr channelNames;
		float radius;
		std::string radiusChannel;
		Box2i dataWindow;
		{
			ImagePlug::GlobalScope c( context );

			radius = radiusPlug()->getValue();
			channelNames = inPlug()->channelNamesPlug()->getValue();
			dataWindow = inPlug()->dataWindowPlug()->getValue();
			radiusChannel = radiusChannelPlug()->getValue();
		}

		Imath::Box2i tileBound;
		IECore::Box2iVectorDataPtr chunkBoundsData = new Box2iVectorData();
		std::vector<Box2i> &chunkBounds = chunkBoundsData->writable();
		IECore::V2fVectorDataPtr chunkDepthsData = new V2fVectorData();
		std::vector<V2f> &chunkDepths = chunkDepthsData->writable();
		chunkBounds.reserve( ImagePlug::tilePixels() / ( g_chunkSize * g_chunkSize ) );
		chunkDepths.reserve( ImagePlug::tilePixels() / ( g_chunkSize * g_chunkSize ) );

		if( ImageAlgo::channelExists( channelNames->readable(), radiusChannel ) )
		{
			ConstFloatVectorDataPtr radiusPixelsData = inPlug()->channelData( radiusChannel, tileOrigin );
			const std::vector< float > radiusPixels = radiusPixelsData->readable();

			Box2i relativeDataWindow( dataWindow.min - tileOrigin, dataWindow.max - tileOrigin );

			for( int cy = 0; cy < ImagePlug::tileSize(); cy += g_chunkSize )
			{
				for( int cx = 0; cx < ImagePlug::tileSize(); cx += g_chunkSize )
				{
					Imath::Box2i chunkBound;
					Imath::V2f chunkDepth( std::numeric_limits<float>::infinity(), -std::numeric_limits<float>::infinity( ) );
					for( int y = 0; y < g_chunkSize; y++ )
					{
						for( int x = 0; x < g_chunkSize; x++ )
						{
							V2i pixel( cx + x, cy + y );
							if( !BufferAlgo::contains( relativeDataWindow, pixel ) )
							{
								continue;
							}

							int index = ImagePlug::pixelIndex( pixel, Imath::V2i( 0 ) );

							float curRadius = radiusPixels[index] * radius;

							int intRadius = int( ceilf( fabsf( curRadius ) ) );
							chunkBound.extendBy( pixel - V2i( intRadius ) );
							chunkBound.extendBy( pixel + V2i( intRadius + 1 ) );

							chunkDepth.x = std::min( chunkDepth.x, curRadius );
							chunkDepth.y = std::max( chunkDepth.y, curRadius );
						}
					}

					chunkBounds.push_back( chunkBound );
					chunkDepths.push_back( chunkDepth );
					tileBound.extendBy( chunkBound );
				}
			}

		}
		else
		{
			int intRadius = int( ceilf( fabsf( radius ) ) );
			tileBound = Imath::Box2i( -V2i( intRadius ), V2i( ImagePlug::tileSize() + intRadius ) );
			for( int cy = 0; cy < ImagePlug::tileSize(); cy += g_chunkSize )
			{
				for( int cx = 0; cx < ImagePlug::tileSize(); cx += g_chunkSize )
				{
					// Feels a bit wasteful to store these when there could be a more efficient version
					// that didn't need to store them when the radius doesn't vary. But the actual cost
					// is not significant, and it's not worth a separate code path when we expect the users
					// of this node to be using variable radii.
					chunkBounds.push_back( Imath::Box2i( V2i( cx - intRadius, cy - intRadius ), V2i( cx + g_chunkSize + intRadius, cy + g_chunkSize + intRadius ) ) );
					chunkDepths.push_back( Imath::V2f( radius, radius ) );
				}
			}
		}

		ObjectVectorPtr result = new ObjectVector();
		result->members().push_back( new Box2iData( tileBound ) );
		result->members().push_back( chunkBoundsData );
		result->members().push_back( chunkDepthsData );
		static_cast<ObjectVectorPlug *>( output )->setValue( result );
	}
	else if( output == planeWeightsPlug() )
	{
		// The plane weights store the visibility of each plane after accounting for alpha occlusion ( plus
		// the final alpha because we need to compute that anyway ).

		// My original plan was to fade out the degree that a plane blocks the plane directly behind it - as
		// the depth approaches the plane divider, it should not have a full occluding effect on adjacent
		// pixels ( pixels at the same depth don't occlude each other, and we don't want to see a sudden
		// snap as pixels cross the plane divider ). However, a simpler approach seems to have just as good
		// results: a plane only occludes disks that are more than one plane behind it. This ensures that
		// things that are far apart don't incorrectly mix, but when there is a smooth transition between
		// two directly adjacent planes, they can mix.

		if( inPlug()->deep() )
		{
			throw IECore::Exception( "Deep not yet supported" );
		}

		ObjectVectorPtr result = new ObjectVector;

		ConstFloatVectorDataPtr planeDividersData;
		ConstStringVectorDataPtr channelNames;
		Box2i dataWindow;
		float radius;
		std::string radiusChannel;
		ConstObjectVectorPtr scanlinesLUT;
		int useRefImpl;
		float approximationThreshold;
		int maxRadius;

		{
			ImagePlug::GlobalScope c( context );

			planeDividersData = planeDividersPlug()->getValue();
			channelNames = inPlug()->channelNamesPlug()->getValue();
			dataWindow = inPlug()->dataWindowPlug()->getValue();

			if(
				planeDividersData->readable().size() == 0 ||
				!ImageAlgo::channelExists( channelNames->readable(), g_alphaChannelName )
			)
			{
				// If there are no plane dividers, or there is no alpha channel, then no occlusion
				// occurs between planes, and we don't need to compute plane weights.
				static_cast<ObjectVectorPlug *>( output )->setValue( result );
				return;
			}

			radius = radiusPlug()->getValue();
			radiusChannel = radiusChannelPlug()->getValue();
			scanlinesLUT = scanlinesLUTPlug()->getValue();
			useRefImpl = useReferenceImplementationPlug()->getValue();
			approximationThreshold = approximationThresholdPlug()->getValue();
			maxRadius = maxRadiusPlug()->getValue();
		}

		const std::vector<float> &planeDividers = planeDividersData->readable();

		const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );

		if( radiusChannel.size() && !ImageAlgo::channelExists( channelNames->readable(), radiusChannel ) )
		{
			throw IECore::Exception( fmt::format( "Cannot find radius channel {}", radiusChannel ) );
		}

		Box2i inTileBound;
		std::vector<ConstObjectVectorPtr> tileBounds;
		std::vector<ConstFloatVectorDataPtr> channelTiles;
		std::vector<ConstFloatVectorDataPtr> radiusTiles;
		loadSurroundingTiles(
			inPlug()->channelDataPlug(), tileBoundPlug(),
			context, tileOrigin, dataWindow, maxRadius,
			g_alphaChannelName, radiusChannel,
			inTileBound, tileBounds, channelTiles, radiusTiles
		);

		std::vector<float> accumBuffer;
		std::vector<double> vertAccumBuffer;
		accumBuffer.resize( ImagePlug::tilePixels(), 0.0f );
		vertAccumBuffer.resize( ImagePlug::tileSize(), 0.0 );

		// Render the alpha channel separately for every plane
		std::vector<FloatVectorDataPtr> planes;
		for( unsigned int planeID = 0; planeID < planeDividers.size() + 1; planeID++ )
		{
			FloatVectorDataPtr planeAlphaData = new FloatVectorData;
			std::vector<float> &planeAlpha = planeAlphaData->writable();
			planeAlpha.resize( ImagePlug::tilePixels(), 0.0f );

			renderTile(
				planeAlpha, accumBuffer, vertAccumBuffer,
				tileOrigin, dataWindow,
				planeID >= 1 ? planeDividers[ planeID - 1 ] : -std::numeric_limits<float>::infinity(),
				planeID < planeDividers.size() ? planeDividers[ planeID ] : std::numeric_limits<float>::infinity(),
				inTileBound, channelTiles, radius, radiusTiles, tileBounds,
				maxRadius, scanlinesLUT.get(), useRefImpl, approximationThreshold, context->canceller()
			);

			std::fill( accumBuffer.begin(), accumBuffer.end(), 0.0f );
			std::fill( vertAccumBuffer.begin(), vertAccumBuffer.end(), 0.0 );

			planes.push_back( planeAlphaData );
		}


		std::vector<float> *prevPlane = nullptr;
		std::vector<float> *prevPrevPlane = nullptr;
		for( FloatVectorDataPtr &planeData : planes )
		{
			std::vector<float> &plane = planeData->writable();

			if( prevPrevPlane )
			{
				for( int i = 0; i < ImagePlug::tilePixels(); i++ )
				{
					// Once we're dealing with planes in the middle of the stack, the amount of
					// blocking we get from this plane is reduced by this plane being partially
					// blocked.
					plane[i] = (*prevPlane)[i] - (*prevPrevPlane)[i] * plane[i];
				}
			}
			else if( prevPlane )
			{
				for( int i = 0; i < ImagePlug::tilePixels(); i++ )
				{
					// The alpha of the second plane just adds to the blocking
					plane[i] = (*prevPlane)[i] - plane[i];
				}
			}
			else
			{
				for( int i = 0; i < ImagePlug::tilePixels(); i++ )
				{
					// The alpha of the first plane just does simple blocking
					plane[i] = 1.0f - plane[i];
				}
			}

			prevPrevPlane = prevPlane;
			prevPlane = &plane;
		}

		// The final plane contains the total transmission for the whole stack - we can
		// invert this to get the final alpha.
		FloatVectorDataPtr finalPlane = planes.back();

		// The last two planes aren't used as transmissions, because there is nothing behind them.
		planes.pop_back();
		planes.pop_back();

		for( FloatVectorDataPtr &planeData : planes )
		{
			result->members().push_back( planeData );
		}

		for( float &f : finalPlane->writable() )
		{
			f = 1.0f - f;
		}
		result->members().push_back( finalPlane );

		static_cast<ObjectVectorPlug *>( output )->setValue( result );
	}
	else
	{
		ImageProcessor::compute( output, context );
	}
}

ValuePlug::CachePolicy DiskBlur::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	return ComputeNode::computeCachePolicy( output );
}

ValuePlug::CachePolicy DiskBlur::hashCachePolicy( const Gaffer::ValuePlug *output ) const
{
	return ComputeNode::hashCachePolicy( output );
}

void DiskBlur::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelData( parent, context, h );


	ConstStringVectorDataPtr channelNames;
	std::string radiusChannel;
	Box2i dataWindow;
	{
		ImagePlug::GlobalScope c( context );
		inPlug()->deepPlug()->hash( h );
		radiusPlug()->hash( h );
		scanlinesLUTPlug()->hash( h );
		useReferenceImplementationPlug()->hash( h );
		approximationThresholdPlug()->hash( h );
		planeDividersPlug()->hash( h );

		channelNames = inPlug()->channelNamesPlug()->getValue();
		inPlug()->dataWindowPlug()->hash( h );
		radiusChannel = radiusChannelPlug()->getValue();
		dataWindow = inPlug()->dataWindow();
	}

	{
		Context::EditableScope tileScope( context );
		tileScope.remove( ImagePlug::channelNameContextName );
		planeWeightsPlug()->hash( h );
	}

	const int maxRadius = maxRadiusPlug()->getValue();
	h.append( maxRadius );

	// We usually try not to make the hash dependent on the absolute data window and tile origin - but in
	// this case, we depend on our position relative to all tiles within maxRadius ... we can't reuse data
	// from a different tile even if all the channel data is the same for this tile. So here, we might as
	// well just hash in the absolute data window and tile origin. The only real case I can think of where
	// we could reuse a cache that isn't handled by this is if the whole image was offset by an exact
	// multiple of the tile size, and that seems quite rare.
	h.append( dataWindow );
	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	h.append( tileOrigin );

	if( radiusChannel.size() && !ImageAlgo::channelExists( channelNames->readable(), radiusChannel ) )
	{
		throw IECore::Exception( fmt::format( "Cannot find radius channel {}", radiusChannel ) );
	}

	hashSurroundingTiles(
		inPlug()->channelDataPlug(), context, tileOrigin, dataWindow, maxRadius,
		context->get<std::string>( ImagePlug::channelNameContextName ), radiusChannel,
		h
	);

	// The alpha channel is processed differently ( even if all the pixels are identical ), so we need to include this
	h.append( context->get<std::string>( ImagePlug::channelNameContextName ) == g_alphaChannelName );
}

IECore::ConstFloatVectorDataPtr DiskBlur::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	if( inPlug()->deep() )
	{
		throw IECore::Exception( "Deep not yet supported" );
	}

	ConstStringVectorDataPtr channelNames;
	Box2i dataWindow;
	float radius;
	std::string radiusChannel;
	ConstObjectVectorPtr scanlinesLUT;
	int useRefImpl;
	float approximationThreshold;
	int maxRadius;
	ConstFloatVectorDataPtr planeDividersData;

	{
		ImagePlug::GlobalScope c( context );
		channelNames = inPlug()->channelNamesPlug()->getValue();
		dataWindow = inPlug()->dataWindowPlug()->getValue();
		radius = radiusPlug()->getValue();
		radiusChannel = radiusChannelPlug()->getValue();
		scanlinesLUT = scanlinesLUTPlug()->getValue();
		useRefImpl = useReferenceImplementationPlug()->getValue();
		approximationThreshold = approximationThresholdPlug()->getValue();

		maxRadius = maxRadiusPlug()->getValue();

		planeDividersData = planeDividersPlug()->getValue();
	}

	const std::vector<float> &planeDividers = planeDividersData->readable();

	ConstObjectVectorPtr planeWeights = new ObjectVector();
	if( planeDividers.size() )
	{
		Context::EditableScope tileScope( context );
		tileScope.remove( ImagePlug::channelNameContextName );
		planeWeights = planeWeightsPlug()->getValue();

		if( channelName == g_alphaChannelName && planeWeights->members().size() )
		{
			// Alpha is computed while computing the plane weights anyway, so we store the final
			// alpha as the last element in this list
			return static_cast<const FloatVectorData*>( planeWeights->members().back().get() );
		}
	}


	FloatVectorDataPtr resultData = new FloatVectorData();
	std::vector<float> &result = resultData->writable();
	result.resize( ImagePlug::tilePixels(), 0.0f );
	std::vector<float> accumBuffer;
	accumBuffer.resize( ImagePlug::tilePixels(), 0.0f );
	std::vector<double> vertAccumBuffer;
	vertAccumBuffer.resize( ImagePlug::tileSize(), 0.0 );

	if( radiusChannel.size() && !ImageAlgo::channelExists( channelNames->readable(), radiusChannel ) )
	{
		throw IECore::Exception( fmt::format( "Cannot find radius channel {}", radiusChannel ) );
	}

	Box2i inTileBound;
	std::vector<ConstObjectVectorPtr> tileBounds;
	std::vector<ConstFloatVectorDataPtr> channelTiles;
	std::vector<ConstFloatVectorDataPtr> radiusTiles;
	loadSurroundingTiles(
		inPlug()->channelDataPlug(), tileBoundPlug(),
		context, tileOrigin, dataWindow, maxRadius,
		channelName, radiusChannel,
		inTileBound, tileBounds, channelTiles, radiusTiles
	);



	if( !planeDividers.size() )
	{
		renderTile(
			result, accumBuffer, vertAccumBuffer,
			tileOrigin, dataWindow,
			-std::numeric_limits<float>::infinity(), std::numeric_limits<float>::infinity(),
			inTileBound, channelTiles, radius, radiusTiles, tileBounds,
			maxRadius, scanlinesLUT.get(), useRefImpl, approximationThreshold, context->canceller()
		);
	}
	else
	{
		std::vector<float> curPlaneBuffer;
		curPlaneBuffer.resize( ImagePlug::tilePixels(), 0.0f );

		for( unsigned int planeID = 0; planeID < planeDividers.size() + 1; planeID++ )
		{
			renderTile(
				curPlaneBuffer, accumBuffer, vertAccumBuffer,
				tileOrigin, dataWindow,
				planeID >= 1 ? planeDividers[ planeID - 1 ] : -std::numeric_limits<float>::infinity(),
				planeID < planeDividers.size() ? planeDividers[ planeID ] : std::numeric_limits<float>::infinity(),
				inTileBound, channelTiles, radius, radiusTiles, tileBounds,
				maxRadius, scanlinesLUT.get(), useRefImpl, approximationThreshold, context->canceller()
			);


			if( planeID < 2 )
			{
				// The first two planes have nothing in front of them, and can be added straight to the result.
				for( int i = 0; i < ImagePlug::tilePixels(); i++ )
				{
					result[i] += curPlaneBuffer[i];
				}
			}
			else
			{
				// The remaining planes have corresponding tranmission values in the planeWeights
				const std::vector<float> &transmission = static_cast<const FloatVectorData*>( planeWeights->members()[planeID - 2].get() )->readable();

				for( int i = 0; i < ImagePlug::tilePixels(); i++ )
				{
					result[i] += curPlaneBuffer[i] * transmission[i];
				}
			}

			// Reset our buffers before we render the next iteration ( would sort of be cleaner to do this
			// as the first step in renderTile, but it would be silly to do it twice in cases where we only call
			// renderTile once, and it's hard to tell C++ not to zero-init a vector when we allocate it.
			std::fill( accumBuffer.begin(), accumBuffer.end(), 0.0f );
			std::fill( vertAccumBuffer.begin(), vertAccumBuffer.end(), 0.0 );
			std::fill( curPlaneBuffer.begin(), curPlaneBuffer.end(), 0.0f );
		}
	}

	return resultData;
}

void DiskBlur::hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashDeep( parent, context, h );
	h.append( false );
}

bool DiskBlur::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return false;
}

void DiskBlur::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = ImagePlug::flatTileSampleOffsets()->Object::hash();
}

IECore::ConstIntVectorDataPtr DiskBlur::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::flatTileSampleOffsets();
}
