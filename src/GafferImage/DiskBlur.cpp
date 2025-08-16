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

// Should we allow choosing the alpha channel for occlusion?
const std::string g_alphaChannelName = "A";

// ----------------------------------------------------------------------------
// Some helper functions for dealing with the scanlines look up table.
//
// In order to very quickly render disks of various sizes, we precompute the sizes of each scanline
// for disks of particular fixed size. This means when rendering, we just look up the entry closest
// to the current radius, and then just read how many pixels to render for each scanline.


// How many entries per pixel increment of radius in the table of which pixels are covered by a disk.
// 4 means we will be accurate to the quarter pixel.
constexpr int g_lutDensity = 4;

// This defines the mapping of radius to a LUT index.
float lutIndexForRadius( float radius )
{
	return ( ( radius - 1.0f ) * float( g_lutDensity ) ) ;
}

// And the mapping back from a lut index to a radius
float radiusForLUTIndex( int i )
{
	constexpr float g_lutDensityInv = 1.0f / float( g_lutDensity );
	return float( i ) * g_lutDensityInv + 1.0f;
}

// The scanline table contains the lists of scanlines for every radius concatenated together. Because these
// sizes are all predictable, we can do a bit of math to get a closed form solution for the exact range of
// the table used for a given LUT index.
std::pair< int, int > scanlineLUTRangeForIndex( int i )
{
	int lutSize = i / g_lutDensity + 2;
	int fraction = i % g_lutDensity;

	int startIndex = ( ( ( lutSize * ( lutSize - 1 ) ) >> 1 ) - 1 ) * g_lutDensity + lutSize * fraction;
	return { lutSize, startIndex };
}


// Fill a table with how large the scanlines are for a disk of one particular radius.
// Returns the area of the disk.
int precalcScanlineSizes( float radius, uint16_t *result, int resultSize )
{
	// Since the pixel coordinates are all integers, we can compute the scanline sizes using integer
	// math. We start by converting the squared target radius to an integer.

	int radiusSquared = floorf( radius * radius );

	// The first scanline will have a width equal to the radius
	int x = resultSize;

	// Tracking slope is an optimization - we know that the second derivative of the top of a circle is
	// negative, so we can cut out some brute force checks of the distance by keeping track of the slope
	int slope = 0;

	int area = 0;

	// Loop through the scanlines computing their size
	for( int y = 0; y < resultSize; y++ )
	{
		int ySquared = y*y;
		int nextX = x - slope;

		// Decrease x until we find a pixel that is within the radius
		while( nextX >= 0 && ySquared + nextX*nextX > radiusSquared )
		{
			nextX--;
		}

		slope = std::max( 0, x - nextX - 1 );
		x = nextX;

		// Write out the size for this scanline
		result[y] = x;

		// And add the size to the area accumulator
		area += x;
	}

	// We measure the area of just a quarter of the disk, excluding the center pixel,
	// so `* 4 + 1` gives the total area.
	return area * 4 + 1;
}

// ----------------------------------------------------------------------------
// Some helper functions for actually rendering disks
//
// These low level functions are all brought together in the renderDisk() function, which can
// efficiently render disks with or without anti-aliasing using accumulation buffers.
//
// The key to renderDisk() is being provided with 3 separate possible buffers to render each
// contribution to - this means we can render to whichever of the buffers is most efficient
// - the contributions are all summed afterwards, so it doesn't matter where each contribution
// goes.
// The 3 buffers are:
// * accumBuffer : this will have a running sum applied to it per scanline. This means that to
//   write add a constant run of values across a scanline, you just need to add a value to the
//   pixel where it starts, and then subtract that same value to the pixel after it ends. The
//   pixels in between will be filled by the running sum.
// * vertAccumBuffer : A similar idea, but operating on whole scanlines at a time - you set
//   one value per scanline. By setting one positive and one negative value, you can fill in
//   a whole range of scanlines then width of a tile.
// * results : A regular output buffer with no running sums. Used for outputting anti-aliased
//   edges and disks with < 1 pixel radius.


// Given an array sorted from low to high, return the first element in the range [ indexMin, indexMax ) which is <= val.
//
// This code is hottest loop in this node, and is extremely performance sensitive.
// When I tried replacing this with:
// `std::lower_bound( &array[indexMin], &array[indexMax], val, []( const uint16_t &a, const uint16_t &b ){ return a > b; } ) - &array[0];`
// I saw performance losses of 14% in testPerfHugeApprox and testPerfLargeApprox, so it's probably worth sticking
// with version.
inline int binarySearchLessThanEqual( const uint16_t *array, int val, int indexMin, int indexMax )
{
	if( array[ indexMin ] <= val )
	{
		return indexMin;
	}

	// This early out is not necessary for correctness ( the loop would converge to the correct value anyway ),
	// but improves performance by ~5%.
	if( array[ indexMax - 1 ] > val )
	{
		return indexMax;
	}

	while( indexMax - indexMin > 1 )
	{
		int midPoint = ( indexMin + indexMax ) >> 1;
		if( array[ midPoint ] <= val )
		{
			indexMax = midPoint;
		}
		else
		{
			indexMin = midPoint;
		}
	}
	return indexMax;
}

// Private utility function of addScanlinesToAccumulators
// This is extremely specific - due to symmetry, we only store the scanlines for half a disk - this function
// just takes care of the top or bottom half of the disk ( yDir indicates which half ).
//
// It also only adds contributions to the horizontal accumulator. If there are fully covered scanlines, instead
// of outputting them, it just returns how far the fully covered region extends - addScanlinesToAccumulators
// handles adding these contributions the vertical accumulator.
template< int yDir >
inline int addHalfScanlinesToHorizAccum(
	const V2i &p, int numScanlines, const uint16_t *scanlineSizes, float normalizedValue, std::vector<float> &accumBuffer )
{
	// Find the maximum possible and minimum possible index of scanlines that may interact with this tile,
	// based on the size of the current scanline table, and the distance to the edge of the tile.
	int minIndex;
	int maxIndex;
	if constexpr( yDir > 0 )
	{
		// The minimum index is 0, unless the center point is below the current tile
		minIndex = std::max( 0, -p.y );
		// The maximum index is the number of scanlines, unless the center point is too close to the end of the tile.
		maxIndex = std::min( numScanlines, ImagePlug::tileSize() - p.y );
	}
	else
	{
		// When rendering the bottom of half of the disk, the minimum index must be at least 1 ( because
		// we don't want to duplicate the rendering of the 0th scanline from the top half.
		// Otherwise, we still need to check if we're outside the tile ( though in this direction, it's
		// the top edge we need to check.
		minIndex = std::max( 1, p.y - ( ImagePlug::tileSize() - 1 ) );
		// The maximum index is the number of scanlines, unless the center point too close to the start of the tile.
		maxIndex = std::min( numScanlines, p.y + 1 );
	}

	if( !( maxIndex > minIndex ) )
	{
		return -1;
	}

	// We now know the range where these scanlines could interact with this tile.
	// To find the precise range where they actually do interact with this tile, we need to do binary searches to
	// find the intersections of the left and right ends of the scanlines with the edges of the tile.

	// Use binary searches to limit us to the valid range for the left quadrant.
	int leftMinIndex = binarySearchLessThanEqual( scanlineSizes, p.x, minIndex, maxIndex );
	// Note the tiny optimization here that if we find an intersection on the left of the tile, the right
	// intersection must be greater, so we start the search at leftMinIndex
	int leftMaxIndex = binarySearchLessThanEqual( scanlineSizes, p.x - ImagePlug::tileSize(), leftMinIndex, maxIndex );

	// We now have a range of scanlines that we know are valid within this tile, so we can mark all of these
	// scanline beginnings in the accumBuffer. ( Not having to have extra conditionals in this loop to test
	// if the position is valid seems to have been a win ... it's hard to do a direct comparison, but an earlier
	// version tested each scanline for whether it is in range, and that was slower ).
	for( int i = leftMinIndex; i < leftMaxIndex; i++ )
	{
		int inner = scanlineSizes[i];
		accumBuffer[ ( ( p.y + yDir * i ) << ImagePlug::tileSizeLog2() ) + p.x - inner ] += normalizedValue;
	}

	// Same for the right edge - restrict the range if the right quadrant intersects the edges of the tile.
	int rightMinIndex = binarySearchLessThanEqual( scanlineSizes, ImagePlug::tileSize() - p.x - 2 , minIndex, maxIndex );
	int rightMaxIndex = binarySearchLessThanEqual( scanlineSizes, -p.x - 1, rightMinIndex, maxIndex );

	// Now we can mark all the ends of the scanlines in the accumBuffer
	for( int i = rightMinIndex; i < rightMaxIndex; i++ )
	{
		int inner = scanlineSizes[i];
		accumBuffer[ ( ( p.y + yDir * i ) << ImagePlug::tileSizeLog2() ) + p.x + inner + 1 ] -= normalizedValue;
	}

	// If there is part of the left quadrant that is vaild within this y range, but the left of this tile
	// cut it off, that means it has already on at the left edge of this tile - it may be a candidate for
	// the vertical accumulation buffer.
	if( leftMinIndex > minIndex )
	{
		// We still need to check against the right quadrant as well ( some scanlines might have started
		// to the left of this tile, but also ended before reaching this tile, and we don't want to include
		// those )
		return std::min( leftMinIndex, rightMaxIndex );
	}
	else
	{
		return -1;
	}

}

// Now we can write a function that actually fully renders a list of scanlines to the right accumulators.
void addScanlinesToAccumulators(
	const V2i &p, int numScanlines, const uint16_t *scanlineSizes, float normalizedValue,
	std::vector<float> &accumBuffer, std::vector<double> &vertAccumBuffer
)
{
	// Add the bottom half of the disk to the horizontal accumBuffer, and return the number of scanlines
	// down that start the tile on
	int alreadyOnDown = addHalfScanlinesToHorizAccum<-1>(
		p, numScanlines, scanlineSizes, normalizedValue, accumBuffer
	);
	// Add the top half of the disk to the horizontal accumBuffer, and return the number of scanlines
	// up that start the tile on
	int alreadyOnUp = addHalfScanlinesToHorizAccum<1>(
		p, numScanlines, scanlineSizes, normalizedValue, accumBuffer
	);

	// Now find the range of scanlines that start this tile already on
	// These can be added to the vertAccumBuffer, which operates on whole scanlines, for even
	// more performance improvement. Note the consequence of this that if this tile is fully
	// within the disk being rendered, the 2 previous calls to addHalfScanlinesToHorizAccum won't
	// have found any intersections with the tile, and the coverage of the entire tile can be
	// rendered just by adding a single contribution to the first element of the vertAccumBuffer.

	int alreadyOnStart = std::max( 0, p.y + ( alreadyOnDown != -1 ? ( - alreadyOnDown + 1 ) : 0 ) );
	int alreadyOnEnd = p.y + ( alreadyOnUp != -1 ? alreadyOnUp : 0 );

	if( alreadyOnStart < alreadyOnEnd && alreadyOnStart < ImagePlug::tileSize())
	{
		// Scanlines that start this tile already on can be added to the vertAccumBuffer
		vertAccumBuffer[alreadyOnStart] += normalizedValue;

		if( alreadyOnEnd > 0 && alreadyOnEnd < ImagePlug::tileSize() )
		{
			// And if the range of already on scanlines ends within this tile, we need to mark
			// that too.
			vertAccumBuffer[alreadyOnEnd] -= normalizedValue;
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

// Special case for radius < 1.0
// It doesn't really make sense for these extremely tiny disks to think of it as rasterizing a circle,
// and we don't want to try and use the accumulation buffer for these ( since there are no runs of >1
// pixel of the same value ), so we have a special case that just writes values to the 9 pixels touched
// by a pixel convolved with a disk of radius 1.
void renderTinyDisk(
	const V2i &p, float radius, const float value, std::vector<float> &result
)
{
	// The pixel values are chosen as follows:
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

// Now we can use the previous set of low level functions to make a function that handles all aspects of
// rendering disks to the 3 buffers, with or without anti-aliasing.

#if defined( __clang__ )
[[clang::noinline]]
#elif defined ( _MSC_VER )
[[msvc::noinline]]
#else
[[gnu::noinline]]
#endif
// The use of this attribute calls for some explanation: I noticed while refactoring that some
// seemingly unrelated changes ( changing orders of things, removing unused variables ), would have
// surprising performance impacts ( consistent changes of up to 10% ). Based on this, my guess
// is that the compiler's heuristics are sometimes unpredictably leading it to make some bad decisions
// about inlining or register spilling or something. We know that all the really performance important
// stuff is inside this function, so the hypothesis is that by preventing this function from being
// inlined, we allow the compiler to examine the really important stuff inside this function in
// isolation. This hopefully allows the compiler to make better decisions, and reduces the likelyhood
// that unrelated changes elsewhere in the code will change how this code is optimized.
//
// I'm seeing a consistent ~5% improvement across testPerfLarge, testPerfMedium and testPerfSmall just
// by adding this attribute, so it seems worth it. Hopefully it helps with consistency as well.
// ( Would be really nice if this didn't require a weird compiler conditional, but that's a different
// topic ).

void renderDisk(
	const V2i &p, float radius, const float value, const float approximationThreshold,
	const std::vector<uint16_t> &lutScanlineSizes, const std::vector<float> &lutNormalizations,
	const std::vector<V2f> &aaAreas, const std::vector<int> &aaAreaRanges,
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
		auto [ numScanlines, scanlineIndex ] = scanlineLUTRangeForIndex( lutIndex );

		assert( numScanlines <= 1 + intRadius );

		addScanlinesToAccumulators(
			p, numScanlines, &lutScanlineSizes[scanlineIndex], quantizedNormalizedValue,
			accumBuffer, vertAccumBuffer
		);
	}
	else
	{
		int innerLutIndex = floorf( lutIndexForRadius( fullRadius - 0.5f ) );
		int outerLutIndex = ceilf( lutIndexForRadius( fullRadius + 0.5f ) );

		float testRadius = radius + 1.0f;
		size_t areaIndex = std::lower_bound(
			aaAreas.begin() + aaAreaRanges[lutIndex], aaAreas.begin() + aaAreaRanges[lutIndex + 1], testRadius, [](const V2f &a, float b) { return a.x < b; }
		) - aaAreas.begin();
		areaIndex = std::min( aaAreas.size() - 1, std::max( (size_t)1, areaIndex ) );

		// Find the area of this anti-aliased disk using a linear interpolation between values in the
		// piecewise linear function.
		V2f a = aaAreas[ areaIndex - 1];
		V2f b = aaAreas[ areaIndex ];
		float area = a.y + ( b.y - a.y ) * ( testRadius - a.x ) / ( b.x - a.x );

		float normalizedValue = value / area;

		auto [ innerLutSize, innerScanlineIndex ] = scanlineLUTRangeForIndex( innerLutIndex );
		auto [ outerLutSize, outerScanlineIndex ] = scanlineLUTRangeForIndex( outerLutIndex );

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
				// all the pixels in this scanline.
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


// ----------------------------------------------------------------------------
// A very slow reference implementation.

// Helper function that allows us to just blindly render every pixel in the disk, and ignore writes outside the
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

// ----------------------------------------------------------------------------
// Utilities for accessing all the tiles that contribute to a tile

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

// For all the tiles that may contribute to the current tile, load the tile bounds, and the channel data
// for the current channel and the radius channel.
//
// This is separate from renderTile() because when using multi-layer rendering, renderTile() is called in
// a loop, and we don't want to repeat the getValue() calls.
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
				// Early rejection for tiles that don't actually contribute to this tile. ( This helps reduce
				// the impact if maxRadius is set much larger than the average radius ).
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

// A chunk size of 8 seems like a decent compromise between skipping as large a region as possible at once,
// while still being useful as an acceleration structure in images with rapidly varying radii.
constexpr int g_chunkSize = 8;

// ----------------------------------------------------------------------------
// renderTile() calls renderDisk() for every pixel that contributes to the tile,
// and then combines the accumulation buffers.
void renderTile(
	std::vector<float> &result,
	std::vector<float> &accumBuffer,
	std::vector<double> &vertAccumBuffer,

	const Imath::V2i &tileOrigin,
	const Imath::Box2i &dataWindow,

	float layerMin,
	float layerMax,

	const Box2i &contributingTilesBound,
	const std::vector< ConstFloatVectorDataPtr > &channelTiles,
	float radius,
	const std::vector< ConstFloatVectorDataPtr > &radiusTiles,
	const std::vector< ConstObjectVectorPtr > &tileBounds,

	int maxRadius,
	const ObjectVector *scanlinesLUT,
	bool useRefImpl,
	float approximationThreshold,
	const IECore::Canceller *canceller
)
{
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

						if( signedRadius < layerMin || signedRadius >= layerMax )
						{
							continue;
						}
						float pixelRadius = std::min( fabsf( signedRadius ), float( maxRadius ) );


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
							p - tileOffset, pixelRadius, 1.0f, approximate,
							referenceResult, &area
						);

						float normalizedValue = value / area;

						// And the second call actually renders
						renderDiskReferenceImplementation(
							p - tileOffset, pixelRadius, normalizedValue, approximate,
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

	// Load all the things we need that were precomputed in the scanlinesLUT
	const std::vector<uint16_t> &scanlineSizesLUT = IECore::runTimeCast<IECore::UShortVectorData>( scanlinesLUT->members()[0] )->readable();
	const std::vector<float> &normalizationsLUT = IECore::runTimeCast<IECore::FloatVectorData>( scanlinesLUT->members()[1] )->readable();
	const std::vector<V2f> &aaAreas = IECore::runTimeCast<IECore::V2fVectorData>( scanlinesLUT->members()[2] )->readable();
	const std::vector<int> &aaAreaRanges = IECore::runTimeCast<IECore::IntVectorData>( scanlinesLUT->members()[3] )->readable();

	// Loop over all tiles that contribute to this tile
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

			// Loop over "chunks" of pixels. These blocks of pixels have their own bounding boxes stored in
			// tileBounds, allowing us to quickly reject blocks that don't overlap this tile ( or if their
			// radii places them all in a different depth layer ).
			int chunkIndex = 0;
			for( int cy = 0; cy < ImagePlug::tileSize(); cy += g_chunkSize )
			{
				Canceller::check( canceller );

				for( int cx = 0; cx < ImagePlug::tileSize(); cx += g_chunkSize )
				{
					// Check if each "chunk" of pixels intersects this tile, and this layer. Being able to
					// early reject chunks of pixels all at once can save 30% of runtime when rendering
					// tiny disks, and potentially even more for certain mixtures of small and large radii,
					// and when using many layerBoundaries.
					if(
						( chunkDepths[chunkIndex].y < layerMin ) ||
						( chunkDepths[chunkIndex].x >= layerMax ) ||
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

							if( signedRadius < layerMin || signedRadius >= layerMax )
							{
								continue;
							}

							float value = channel[ pixelIndex ];

							if( value == 0.0f )
							{
								continue;
							}

							float pixelRadius = std::min( fabsf( signedRadius ), float( maxRadius ) );

							// If we've gotten past all the early rejections, the disk is valid.
							// Actually render it to the 3 buffers where we accumulate results.
							renderDisk(
								p - tileOffset, pixelRadius, value, approximationThreshold,
								scanlineSizesLUT, normalizationsLUT,
								aaAreas, aaAreaRanges,
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

	// We now have all the disks rendered to our 3 buffers.
	// We can now combine the buffers.

	float vertAccum = 0;
	for( int i = 0; i < ImagePlug::tilePixels(); i += ImagePlug::tileSize() )
	{
		// The vertAccumBuffer needs to have a running sum applied once per
		// scanline, and then it will provide the starting value for the
		// accumulator for each scanline.

		vertAccum += vertAccumBuffer[ i >> ImagePlug::tileSizeLog2() ];
		float accum = vertAccum;
		for( int j = i; j < i + ImagePlug::tileSize(); j++ )
		{
			// Within each scanline, do a running sum from the accumBuffer
			accum += accumBuffer[j];

			// Add the running sum to the directly rendered contributions already in result
			result[j] += accum;
		}
	}
}

// The standard approach as per Bit-Twiddling Hacks:
// https://graphics.stanford.edu/%7Eseander/bithacks.html#RoundUpPowerOf2
// \todo : Replace with std::bit_ceil once we're on C++20
unsigned int intNextPowerOfTwo( unsigned int v )
{
	v--;
	v |= v >> 1;
	v |= v >> 2;
	v |= v >> 4;
	v |= v >> 8;
	v |= v >> 16;
	v++;
	return v;
}

const IECore::InternedString g_quantizedMaxRadiusContextName( "__quantizedMaxRadius" );

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
	addChild( new FloatPlug( "radius", Plug::In, 1.0f, 0.0f ) );
	addChild( new StringPlug( "radiusChannel" ) );
	addChild( new FloatPlug( "approximationThreshold", Plug::In, 0.001f, 0.0f ) );
	addChild( new IntPlug( "maxRadius", Plug::In, 512, 1 ) );
	addChild( new FloatVectorDataPlug( "layerBoundaries", Plug::In ) );

	addChild( new ObjectVectorPlug( "__tileBound", Plug::Out ) );
	addChild( new ObjectVectorPlug( "__scanlinesLUT", Plug::Out ) );
	addChild( new BoolPlug( "__useReferenceImplementation", Plug::In, false ) );
	addChild( new ObjectVectorPlug( "__layerWeights", Plug::Out ) );

	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
	outPlug()->viewNamesPlug()->setInput( inPlug()->viewNamesPlug() );

	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	outPlug()->deepPlug()->setInput( inPlug()->deepPlug() );
	outPlug()->sampleOffsetsPlug()->setInput( inPlug()->sampleOffsetsPlug() );
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

Gaffer::FloatVectorDataPlug *DiskBlur::layerBoundariesPlug()
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::FloatVectorDataPlug *DiskBlur::layerBoundariesPlug() const
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

Gaffer::BoolPlug *DiskBlur::useReferenceImplementationPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::BoolPlug *DiskBlur::useReferenceImplementationPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 7 );
}

Gaffer::ObjectVectorPlug *DiskBlur::layerWeightsPlug()
{
	return getChild<ObjectVectorPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::ObjectVectorPlug *DiskBlur::layerWeightsPlug() const
{
	return getChild<ObjectVectorPlug>( g_firstPlugIndex + 8 );
}

void DiskBlur::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if(
		input == radiusPlug() ||
		input == radiusChannelPlug() ||
		input == inPlug()->channelDataPlug() ||
		input == inPlug()->dataWindowPlug() ||
		input == inPlug()->deepPlug() ||
		input == inPlug()->channelNamesPlug()
	)
	{
		outputs.push_back( tileBoundPlug() );
	}

	// Note that the scanlinesLUTPlug isn't affected by anything - we put a quantized version of maxRadius
	// in the context when evaluating it.

	if(
		input == radiusPlug() ||
		input == radiusChannelPlug() ||
		input == approximationThresholdPlug() ||
		input == scanlinesLUTPlug() ||
		input == inPlug()->channelDataPlug() ||
		input == inPlug()->dataWindowPlug() ||
		input == inPlug()->deepPlug() ||
		input == inPlug()->channelNamesPlug() ||
		input == useReferenceImplementationPlug() ||
		input == maxRadiusPlug() ||
		input == layerBoundariesPlug() ||
		input == tileBoundPlug()
	)
	{
		outputs.push_back( layerWeightsPlug() );
	}

	if(
		input == radiusPlug() ||
		input == radiusChannelPlug() ||
		input == approximationThresholdPlug() ||
		input == scanlinesLUTPlug() ||
		input == inPlug()->channelDataPlug() ||
		input == inPlug()->dataWindowPlug() ||
		input == inPlug()->deepPlug() ||
		input == inPlug()->channelNamesPlug() ||
		input == useReferenceImplementationPlug() ||
		input == maxRadiusPlug() ||
		input == layerBoundariesPlug() ||
		input == layerWeightsPlug() ||
		input == tileBoundPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void DiskBlur::hashScanlinesLUT( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h.append( context->get<int>( g_quantizedMaxRadiusContextName ) );
}

IECore::ConstObjectVectorPtr DiskBlur::computeScanlinesLUT( const Gaffer::Context *context ) const
{
	// The scanlinesLUT plug hold several precalculated things that don't depend on the image
	// content. They depend solely on the maxRadius plug, and should only be computed once per
	// Gaffer session.
	int maxRadius = context->get<int>( g_quantizedMaxRadiusContextName );

	// Extend the table size out by one because rendering an anti-aliased disk of maxRadius
	// requires extends half a pixel higher.
	int maxIndex = ( maxRadius + 1 ) * g_lutDensity;

	// The most important thing we store is a table of the size of all scanlines needed to render
	// disks of certain sizes
	UShortVectorDataPtr scanlineSizesData = new UShortVectorData();
	std::vector<uint16_t> &scanlineSizes = scanlineSizesData->writable();

	// We also normalization factors based on the total area of the disks of certain sizes
	FloatVectorDataPtr normalizationsData = new FloatVectorData();
	std::vector<float> &normalizations = normalizationsData->writable();

	// Preallocate the sizes of the tables
	auto [ finalSize, finalLUTIndex ] = scanlineLUTRangeForIndex( maxIndex - 1 );
	scanlineSizes.resize( finalLUTIndex + finalSize );
	normalizations.resize( maxIndex );

	// Fill the scanline sizes and normalization tables for each disk size
	for( int i = 0; i < maxIndex; i++ )
	{
		auto [ numScanlines, scanlineIndex ] = scanlineLUTRangeForIndex( i );
		float radius = radiusForLUTIndex( i );

		normalizations[i] = 1.0f / float(
			precalcScanlineSizes( radius, &scanlineSizes[ scanlineIndex ], numScanlines )
		);
	}

	// --------------------------------------------------------
	// The second thing we need to precompute is a bit weirder: a look up table
	// for the area of anti-aliased disks.
	//
	// If we were doing perfectly accurate anti-aliasing, then it would just have
	// an area of pi * r**2 - but calculating the exact overlap of a disk with a
	// pixel for perfect AA would require a bunch of per-pixel trig operations,
	// which doesn't make sense for performance. Instead we just take the distance
	// to the center, and pass through a 1 pixel wide lerp based on the radius.
	//
	// This means that the area of what we're actually rendering is a piecewise
	// linear function of radius, with a derivative discontinuity every time the
	// radius crosses a pixel center. There doesn't seem to be any good way to
	// analytically model this function with so many discontinuities ... so we
	// just explicitly evaluate this function at every corner, so we can evaluate
	// it exactly using linear interpolation ... this is quite cheap when
	// rendering ( compared to the cost of rendering an anti-aliased disk ), but
	// is a bit complicated to set up.

	// We need a sorted list of the distances to every pixel center
	// ( this is where our function has a corner, and these are the distances
	// where we need to store an area ).

	// We start by finding the distances to all of the pixels with an 8-fold
	// symmetry ( this is one octant, not including the center pixel, or the
	// cardinal directions and diagonals, which only repeat 4 times )
	std::vector<int> octantSquaredDistances;

	int distanceTableSize = maxRadius + 1;
	int maxDistanceSquared = distanceTableSize * distanceTableSize;
	octantSquaredDistances.reserve( distanceTableSize * distanceTableSize / 2 );
	for( int y = 1; y < distanceTableSize; y++ )
	{
		for( int x = y + 1; x < distanceTableSize; x++ )
		{
			int distanceSquared = x * x + y * y;
			if( distanceSquared <= maxDistanceSquared )
			{
				octantSquaredDistances.push_back( distanceSquared );
			}
		}
	}
	// Sort the octant
	std::sort( octantSquaredDistances.begin(), octantSquaredDistances.end() );

	// Now we'll combine this into a full quadrant of distances. The quadrant
	// includes 2 octants, plus one cardinal direction, and one diagonal.
	std::vector<float> quadrantDistances;
	quadrantDistances.reserve( octantSquaredDistances.size() * 2 + distanceTableSize * 2 );

	unsigned int diagonalIndex = 1;
	unsigned int cardinalIndex = 1;
	unsigned int octantIndex = 0;
	while( true )
	{
		int cardinalDistanceSquared = cardinalIndex * cardinalIndex;
		int diagonalDistanceSquared = 2 * diagonalIndex * diagonalIndex;

		if(
			octantIndex < octantSquaredDistances.size() &&
			octantSquaredDistances[ octantIndex ] < std::min( cardinalDistanceSquared, diagonalDistanceSquared )
		)
		{
			float d = sqrtf( float( octantSquaredDistances[ octantIndex ] ) );
			quadrantDistances.push_back( d );
			quadrantDistances.push_back( d );
			octantIndex++;
		}
		else
		{
			if( cardinalDistanceSquared <= diagonalDistanceSquared )
			{
				if( cardinalDistanceSquared > maxDistanceSquared )
				{
					break;
				}
				float d = sqrtf( float( cardinalDistanceSquared ) );
				quadrantDistances.push_back( d );
				cardinalIndex++;
			}
			else
			{
				float d = sqrtf( float( diagonalDistanceSquared ) );
				quadrantDistances.push_back( d );
				diagonalIndex++;
			}
		}

	}

	// Now we need to iterate through through the list of distances to pixel centers, keeping
	// track of the current area. We keep a queue of pixels which are contributing at the
	// current distance by keeping two indices, queueStart and queueStop in the sorted
	// distances list. Pixel distances are added to the queue by incrementing queueStart
	// when the current distance reaches them, and once the current distance is 1.0 greater
	// than the pixel distance, that pixel center will no longer contribute, and it is removed
	//from the queue by incrementing queueStop.

	V2fVectorDataPtr aaAreasData = new V2fVectorData();
	std::vector<V2f> &aaAreas = aaAreasData->writable();

	unsigned int queueStart = 0;
	unsigned int queueStop = 0;

	float currentDistance = 0;
	float currentArea = 0;

	while( true )
	{
		// The current rate that area is increasing in this piecewise linear segement depends on
		// how many pixels are currently in the queue of active contributors.
		int curSlope = queueStart - queueStop;

		float nextDistance;
		if( queueStop < queueStart && quadrantDistances[ queueStop ] + 1.0f <= quadrantDistances[ queueStart ] )
		{
			// The next corner is due to a pixel distance falling out of the queue
			nextDistance = quadrantDistances[ queueStop ] + 1.0f;
			queueStop++;
		}
		else if( queueStart < quadrantDistances.size() )
		{
			// The next corner is due to a pixel distance entering the queue
			nextDistance = quadrantDistances[ queueStart ];
			queueStart++;
		}
		else
		{
			// We've reached the end of the list of distances
			break;
		}

		if( nextDistance != currentDistance )
		{
			// Increment the area based on the distance to the previous corner, and the slope
			// for this segment
			currentArea += curSlope * ( nextDistance - currentDistance );

			// Put the distance / area pair in the output. ( We're only measuring the area of
			// of one quadrant, so we multiply by 4 and add the centre pixel )
			aaAreas.push_back( Imath::V2f( nextDistance, currentArea * 4.0f + 1.0f ) );
		}

		currentDistance = nextDistance;
	}

	// And now one final table, just to optimize accessing the aaAreas function: we don't want to
	// have to binary search the whole list whenenver we look up a radius, so we prepare a simple
	// array mapping from the closest radius with a lut index, to the corresponding position in
	// the aaAreas list. This allows us to just search within the range between the two closest
	// lut indices.
	IntVectorDataPtr aaAreaRangesData = new IntVectorData();
	std::vector<int> &aaAreaRanges = aaAreaRangesData->writable();
	aaAreaRanges.resize( maxIndex + 1 );

	for( int i = 0; i < maxIndex; i++ )
	{
		float radius = radiusForLUTIndex( i );

		size_t aaAreaIndex = std::lower_bound(
			aaAreas.begin(), aaAreas.end(), radius + 0.5f * ( 1.0f - 1.0f / float( g_lutDensity ) ), [](const V2f &a, float b) { return a.x < b; }) - aaAreas.begin();

		aaAreaRanges[i] = aaAreaIndex;
	}

	aaAreaRanges[maxIndex] = aaAreas.size() - 1;

	// Store all the various things we've precalculated in the result
	ObjectVectorPtr result = new ObjectVector();
	result->members().push_back( scanlineSizesData );
	result->members().push_back( normalizationsData );
	result->members().push_back( aaAreasData );
	result->members().push_back( aaAreaRangesData );
	return result;
}

void DiskBlur::hashTileBound( const Gaffer::Context *context, IECore::MurmurHash &h ) const
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

IECore::ConstObjectVectorPtr DiskBlur::computeTileBound( const Imath::V2i &tileOrigin, const Gaffer::Context *context ) const
{
	// We store 3 things in this plug, used to skip processing of things that won't contribute to the final result:
	// * the overall bound of which pixels this whole tile contributes to
	// * for each chunk of pixels ( defined as a block of dimensions g_chunkSize x g_chunkSize ), the pixel bound
	// * for each chunk of pixels, the range of radii ( used to reject chunks when doing multi-layer rendering
	//   if the radii are all outside the layer )

	if( inPlug()->deep() )
	{
		throw IECore::Exception( "Deep not yet supported" );
	}

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
	return result;
}

void DiskBlur::hashLayerWeights( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const V2i &tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	h.append( tileOrigin );

	ConstStringVectorDataPtr channelNames;
	std::string radiusChannel;
	Box2i dataWindow;
	int maxRadius;
	{
		ImagePlug::GlobalScope c( context );

		inPlug()->deepPlug()->hash( h );

		channelNames = inPlug()->channelNamesPlug()->getValue();
		inPlug()->dataWindowPlug()->hash( h );
		ConstFloatVectorDataPtr layerBoundaries = layerBoundariesPlug()->getValue();

		if(
			layerBoundaries->readable().size() == 0 ||
			!ImageAlgo::channelExists( channelNames->readable(), g_alphaChannelName )
		)
		{
			// If there are no layer boundaries, or there is no alpha channel, then no occlusion
			// occurs between layers, and we don't need to compute layer weights.
			return;
		}

		layerBoundariesPlug()->hash( h );
		radiusPlug()->hash( h );
		useReferenceImplementationPlug()->hash( h );
		approximationThresholdPlug()->hash( h );

		radiusChannel = radiusChannelPlug()->getValue();
		dataWindow = inPlug()->dataWindow();
		maxRadius = maxRadiusPlug()->getValue();
	}

	// Note that we're not including the scanlines plug here - it only depends on maxRadius, so we
	// don't need it to ensure uniqueness as long as we include maxRadius.

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

IECore::ConstObjectVectorPtr DiskBlur::computeLayerWeights( const Imath::V2i &tileOrigin, const Gaffer::Context *context ) const
{
	// The layer weights store the visibility of each layer after accounting for alpha occlusion ( plus
	// the final alpha because we need to compute that anyway ).

	// My original plan was to fade out the degree that a layer blocks the layer directly behind it - as
	// the depth approaches the layer boundary, it should not have a full occluding effect on adjacent
	// pixels ( pixels at the same depth don't occlude each other, and we don't want to see a sudden
	// snap as pixels cross the layer divider ). However, a simpler approach seems to have just as good
	// results: a layer only occludes disks that are more than one layer behind it. This ensures that
	// things that are far apart don't incorrectly mix, but when there is a smooth transition between
	// two directly adjacent layers, they can mix.

	if( inPlug()->deep() )
	{
		throw IECore::Exception( "Deep not yet supported" );
	}

	ObjectVectorPtr result = new ObjectVector;

	ConstFloatVectorDataPtr layerBoundariesData;
	ConstStringVectorDataPtr channelNames;
	Box2i dataWindow;
	float radius;
	std::string radiusChannel;
	ConstObjectVectorPtr scanlinesLUT;
	bool useRefImpl;
	float approximationThreshold;
	int maxRadius;

	{
		ImagePlug::GlobalScope c( context );

		layerBoundariesData = layerBoundariesPlug()->getValue();
		channelNames = inPlug()->channelNamesPlug()->getValue();
		dataWindow = inPlug()->dataWindowPlug()->getValue();

		if(
			layerBoundariesData->readable().size() == 0 ||
			!ImageAlgo::channelExists( channelNames->readable(), g_alphaChannelName )
		)
		{
			// If there are no layer boundaries, or there is no alpha channel, then no occlusion
			// occurs between layers, and we don't need to compute layer weights.
			return result;
		}

		radius = radiusPlug()->getValue();
		radiusChannel = radiusChannelPlug()->getValue();
		useRefImpl = useReferenceImplementationPlug()->getValue();
		approximationThreshold = approximationThresholdPlug()->getValue();
		maxRadius = maxRadiusPlug()->getValue();

		int maxRadiusQuantized = intNextPowerOfTwo( maxRadius );
		c.set<int>( g_quantizedMaxRadiusContextName, &maxRadiusQuantized );
		scanlinesLUT = scanlinesLUTPlug()->getValue();
	}

	const std::vector<float> &layerBoundaries = layerBoundariesData->readable();


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

	// Render the alpha channel separately for every layer
	// Doing this serially would be disasterous for performance if multiple channels of the same tile are
	// accessed in parallel - while one channel does the work, the others would be stuck. We could somewhat
	// alleviate this by doing this loop in parallel. However, lots of existing nodes already have terrible
	// performance when accessing multiple channels in parallel ( ie. ColorProcessor accesses the input
	// channels serially ) - the current convention is just to make sure that you don't access channels
	// in parallel.
	std::vector<FloatVectorDataPtr> layers;
	for( unsigned int layerID = 0; layerID < layerBoundaries.size() + 1; layerID++ )
	{
		FloatVectorDataPtr layerAlphaData = new FloatVectorData;
		std::vector<float> &layerAlpha = layerAlphaData->writable();
		layerAlpha.resize( ImagePlug::tilePixels(), 0.0f );

		renderTile(
			layerAlpha, accumBuffer, vertAccumBuffer,
			tileOrigin, dataWindow,
			layerID >= 1 ? layerBoundaries[ layerID - 1 ] : -std::numeric_limits<float>::infinity(),
			layerID < layerBoundaries.size() ? layerBoundaries[ layerID ] : std::numeric_limits<float>::infinity(),
			inTileBound, channelTiles, radius, radiusTiles, tileBounds,
			maxRadius, scanlinesLUT.get(), useRefImpl, approximationThreshold, context->canceller()
		);

		std::fill( accumBuffer.begin(), accumBuffer.end(), 0.0f );
		std::fill( vertAccumBuffer.begin(), vertAccumBuffer.end(), 0.0 );

		layers.push_back( layerAlphaData );
	}


	std::vector<float> *prevLayer = nullptr;
	std::vector<float> *prevPrevLayer = nullptr;
	for( FloatVectorDataPtr &layerData : layers )
	{
		std::vector<float> &layer = layerData->writable();

		if( prevPrevLayer )
		{
			for( int i = 0; i < ImagePlug::tilePixels(); i++ )
			{
				// Once we're dealing with layers in the middle of the stack, the amount of
				// blocking we get from this layer is reduced by this layer being partially
				// blocked.
				layer[i] = (*prevLayer)[i] - (*prevPrevLayer)[i] * layer[i];
			}
		}
		else if( prevLayer )
		{
			for( int i = 0; i < ImagePlug::tilePixels(); i++ )
			{
				// The alpha of the second layer just adds to the blocking
				layer[i] = (*prevLayer)[i] - layer[i];
			}
		}
		else
		{
			for( int i = 0; i < ImagePlug::tilePixels(); i++ )
			{
				// The alpha of the first layer just does simple blocking
				layer[i] = 1.0f - layer[i];
			}
		}

		prevPrevLayer = prevLayer;
		prevLayer = &layer;
	}

	// The final layer contains the total transmission for the whole stack - we can
	// invert this to get the final alpha.
	FloatVectorDataPtr finalLayer = layers.back();

	// The last two layers aren't used as transmissions, because there is nothing behind them.
	layers.pop_back();
	layers.pop_back();

	for( FloatVectorDataPtr &layerData : layers )
	{
		result->members().push_back( layerData );
	}

	for( float &f : finalLayer->writable() )
	{
		f = 1.0f - f;
	}
	result->members().push_back( finalLayer );

	return result;
}

void DiskBlur::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hash( output, context, h );
	if( output == scanlinesLUTPlug() )
	{
		hashScanlinesLUT( context, h );
	}
	else if( output == tileBoundPlug() )
	{
		hashTileBound( context, h );
	}
	else if( output == layerWeightsPlug() )
	{
		hashLayerWeights( context, h );
	}
}

void DiskBlur::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == scanlinesLUTPlug() )
	{
		static_cast<ObjectVectorPlug *>( output )->setValue( computeScanlinesLUT( context ) );
	}
	else if( output == tileBoundPlug() )
	{
		const V2i &tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
		static_cast<ObjectVectorPlug *>( output )->setValue( computeTileBound( tileOrigin, context ) );
	}
	else if( output == layerWeightsPlug() )
	{
		const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
		static_cast<ObjectVectorPlug *>( output )->setValue( computeLayerWeights( tileOrigin, context ) );
	}
	else
	{
		ImageProcessor::compute( output, context );
	}
}

Gaffer::ValuePlug::CachePolicy DiskBlur::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == scanlinesLUTPlug() )
	{
		// There isn't actually anything in the calculation of scanlinesLUTPlug that is worth parallelizing,
		// but due to the high contention on this plug, there's still a measurable benefit to having other
		// threads wait instead of repeating the work.
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return ImageNode::computeCachePolicy( output );
}

void DiskBlur::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelData( parent, context, h );


	ConstStringVectorDataPtr channelNames;
	std::string radiusChannel;
	Box2i dataWindow;
	int maxRadius;
	{
		ImagePlug::GlobalScope c( context );
		inPlug()->deepPlug()->hash( h );
		radiusPlug()->hash( h );

		useReferenceImplementationPlug()->hash( h );
		approximationThresholdPlug()->hash( h );
		layerBoundariesPlug()->hash( h );

		channelNames = inPlug()->channelNamesPlug()->getValue();
		inPlug()->dataWindowPlug()->hash( h );
		radiusChannel = radiusChannelPlug()->getValue();
		dataWindow = inPlug()->dataWindow();
		maxRadius = maxRadiusPlug()->getValue();
	}

	{
		Context::EditableScope tileScope( context );
		tileScope.remove( ImagePlug::channelNameContextName );
		layerWeightsPlug()->hash( h );
	}

	h.append( maxRadius );

	// Note that we're not including the scanlines plug here - it only depends on maxRadius, so we
	// don't need it to ensure uniqueness as long as we include maxRadius.

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
	// Most of the complexity is in the lower level functions, to compute the channel data, we'll
	// basically just be using renderTile() and the layerWeightsPlug()
	if( inPlug()->deep() )
	{
		throw IECore::Exception( "Deep not yet supported" );
	}

	ConstStringVectorDataPtr channelNames;
	Box2i dataWindow;
	float radius;
	std::string radiusChannel;
	ConstObjectVectorPtr scanlinesLUT;
	bool useRefImpl;
	float approximationThreshold;
	int maxRadius;
	ConstFloatVectorDataPtr layerBoundariesData;

	{
		ImagePlug::GlobalScope c( context );
		channelNames = inPlug()->channelNamesPlug()->getValue();
		dataWindow = inPlug()->dataWindowPlug()->getValue();
		radius = radiusPlug()->getValue();
		radiusChannel = radiusChannelPlug()->getValue();
		useRefImpl = useReferenceImplementationPlug()->getValue();
		approximationThreshold = approximationThresholdPlug()->getValue();

		maxRadius = maxRadiusPlug()->getValue();

		layerBoundariesData = layerBoundariesPlug()->getValue();

		int maxRadiusQuantized = intNextPowerOfTwo( maxRadius );
		c.set<int>( g_quantizedMaxRadiusContextName, &maxRadiusQuantized );
		scanlinesLUT = scanlinesLUTPlug()->getValue();
	}

	const std::vector<float> &layerBoundaries = layerBoundariesData->readable();

	ConstObjectVectorPtr layerWeights = new ObjectVector();
	if( layerBoundaries.size() )
	{
		Context::EditableScope tileScope( context );
		tileScope.remove( ImagePlug::channelNameContextName );
		layerWeights = layerWeightsPlug()->getValue();

		if( channelName == g_alphaChannelName && layerWeights->members().size() )
		{
			// Alpha is computed while computing the layer weights anyway, so we store the final
			// alpha as the last element in this list
			return static_cast<const FloatVectorData*>( layerWeights->members().back().get() );
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

	// Load all tiles that contribute to this result ( this will consider all tiles within
	// maxRadius, but won't actually load the data for tiles if the tileBound indicates that
	// they don't overlap this tile ).
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



	if( !layerWeights->members().size() )
	{
		// If we're not doing multi-layer rendering, then we just need to renderTile()
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
		// If we're doing multi-layer rendering, then we'll need to call renderTile() for each layer,
		// and combine the results using the correct transmission weights
		std::vector<float> curLayerBuffer;
		curLayerBuffer.resize( ImagePlug::tilePixels(), 0.0f );

		for( unsigned int layerID = 0; layerID < layerBoundaries.size() + 1; layerID++ )
		{
			renderTile(
				curLayerBuffer, accumBuffer, vertAccumBuffer,
				tileOrigin, dataWindow,
				layerID >= 1 ? layerBoundaries[ layerID - 1 ] : -std::numeric_limits<float>::infinity(),
				layerID < layerBoundaries.size() ? layerBoundaries[ layerID ] : std::numeric_limits<float>::infinity(),
				inTileBound, channelTiles, radius, radiusTiles, tileBounds,
				maxRadius, scanlinesLUT.get(), useRefImpl, approximationThreshold, context->canceller()
			);


			if( layerID < 2 )
			{
				// The first two layers have nothing in front of them, and can be added straight to the result.
				for( int i = 0; i < ImagePlug::tilePixels(); i++ )
				{
					result[i] += curLayerBuffer[i];
				}
			}
			else
			{
				// The remaining layers have corresponding transmission values in the layerWeights
				const std::vector<float> &transmission = static_cast<const FloatVectorData*>( layerWeights->members()[layerID - 2].get() )->readable();

				for( int i = 0; i < ImagePlug::tilePixels(); i++ )
				{
					result[i] += curLayerBuffer[i] * transmission[i];
				}
			}

			// Reset our buffers before we render the next iteration ( would sort of be cleaner to do this
			// as the first step in renderTile, but it would be silly to do it twice in cases where we only call
			// renderTile once, and it's hard to tell C++ not to zero-init a vector when we allocate it.
			std::fill( accumBuffer.begin(), accumBuffer.end(), 0.0f );
			std::fill( vertAccumBuffer.begin(), vertAccumBuffer.end(), 0.0 );
			std::fill( curLayerBuffer.begin(), curLayerBuffer.end(), 0.0f );
		}
	}

	return resultData;
}
