//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
//      * Neither the name of Image Engine Design nor the names of
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

#include "GafferImage/Resample.h"

#include "GafferImage/DeepState.h"
#include "GafferImage/DeepPixelAccessor.h"
#include "GafferImage/ImageAlgo.h"
#include "GafferImage/FilterAlgo.h"
#include "GafferImage/Sampler.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

#include "IECore/NullObject.h"

#include "OpenImageIO/filter.h"
#include "OpenImageIO/fmath.h"

#include <iostream>
#include <limits>

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

const std::string g_nearestString( "nearest" );

// Used as a bitmask to say which filter pass(es) we're computing.
enum Passes
{
	Horizontal = 1,
	Vertical = 2,
	Both = Horizontal | Vertical,

	// Special pass label when we must compute both passes in one, but there is no scaling.
	// This allows a special code path which is up to 6X faster.
	BothOptimized = Both | 4
};

Passes requiredPasses( const Resample *resample, const ImagePlug *image, const OIIO::Filter2D *filter, V2f &ratio )
{
	int debug = resample->debugPlug()->getValue();
	if( debug == Resample::HorizontalPass )
	{
		return Horizontal;
	}
	else if( debug == Resample::SinglePass )
	{
		// For a SinglePass debug mode, we always use Both.
		// Note that we don't use the optimized pass here, even if the ratio is 1 - we want debug to always
		// use the same path.
		return (Passes)( Horizontal | Vertical );
	}

	if( image == image->parent<ImageNode>()->outPlug() )
	{
		if( !filter )
		{
			// For the nearest filter, we use a separate code path that doesn't consider RequiredPasses anyway.
			return Both;
		}
		if( filter->separable() )
		{
			return Vertical;
		}
		else
		{
			// The filter isn't separable, so we must process everything at once. If the ratio has no
			// scaling though, we can use the optimized path.
			return ( ratio == V2f( 1.0 ) ) ? BothOptimized : Both;
		}
	}
	return Horizontal;
}

// Rounds min down, and max up, while converting from float to int.
Box2i box2fToBox2i( const Box2f &b )
{
	return Box2i(
		V2i( floor( b.min.x ), floor( b.min.y ) ),
		V2i( ceil( b.max.x ), ceil( b.max.y ) )
	);
}

// Calculates the scale and offset needed to convert from output
// coordinates to input coordinates.
void ratioAndOffset( const M33f &matrix, V2f &ratio, V2f &offset )
{
	ratio = V2f( matrix[0][0], matrix[1][1] );
	offset = -V2f( matrix[2][0], matrix[2][1] ) / ratio;
}

// The radius for the filter is specified in the output space. This
// method returns it as a number of pixels in the input space.
V2f inputFilterRadius( const OIIO::Filter2D *filter, const V2f &inputFilterScale )
{
	if( !filter )
	{
		return V2f( 0.0f );
	}

	return V2f(
		filter->width() * inputFilterScale.x * 0.5f,
		filter->height() * inputFilterScale.y * 0.5f
	);
}

// Returns the input region that will need to be sampled when
// generating a given output tile.
Box2i inputRegion( const V2i &tileOrigin, unsigned passes, const V2f &ratio, const V2f &offset, const OIIO::Filter2D *filter, const V2f &inputFilterScale )
{
	Box2f outputRegion( V2f( tileOrigin ), tileOrigin + V2f( ImagePlug::tileSize() ) );
	V2f filterRadius = inputFilterRadius( filter, inputFilterScale );
	V2i filterRadiusCeil( ceilf( filterRadius.x ), ceilf( filterRadius.y ) );

	Box2f result = outputRegion;
	if( passes & Horizontal )
	{
		result.min.x = result.min.x / ratio.x + offset.x;
		result.max.x = result.max.x / ratio.x + offset.x;
		if( result.min.x > result.max.x )
		{
			// Correct for negative scaling inverting
			// the relationship between min and max.
			std::swap( result.min.x, result.max.x );
		}
		result.min.x -= filterRadiusCeil.x;
		result.max.x += filterRadiusCeil.x;
	}
	if( passes & Vertical )
	{
		result.min.y = result.min.y / ratio.y + offset.y;
		result.max.y = result.max.y / ratio.y + offset.y;
		if( result.min.y > result.max.y )
		{
			std::swap( result.min.y, result.max.y );
		}
		result.min.y -= filterRadiusCeil.y;
		result.max.y += filterRadiusCeil.y;
	}

	return box2fToBox2i( result );
}

// Given a filter name, the current scaling ratio of input size / output size, and the desired filter scale in
// output space, return a filter and the correct filter scale in input space
const OIIO::Filter2D *filterAndScale( const std::string &name, V2f ratio, V2f &inputFilterScale )
{
	ratio.x = fabs( ratio.x );
	ratio.y = fabs( ratio.y );

	const OIIO::Filter2D *result;
	if( name == g_nearestString )
	{
		inputFilterScale = V2f( 0 );
		return nullptr;
	}
	else if( name == "" )
	{
		if( ratio.x > 1.0f || ratio.y > 1.0f )
		{
			// Upsizing
			result = FilterAlgo::acquireFilter( "blackman-harris" );
		}
		else
		{
			// Downsizing
			result = FilterAlgo::acquireFilter( "lanczos3" );
		}
	}
	else
	{
		result = FilterAlgo::acquireFilter( name );
	}

	// Convert the filter scale into input space
	inputFilterScale = V2f( 1.0f ) / ratio;

	// Don't allow the filter scale to cover less than 1 pixel in input space
	inputFilterScale = V2f( std::max( 1.0f, inputFilterScale.x ), std::max( 1.0f, inputFilterScale.y ) );

	return result;
}

inline std::pair< int, int > filterSupport( const float filterRadius, const int x, const float ratio, const float offset )
{
	float iX = ( x + 0.5f ) / ratio + offset;

	return std::make_pair(
		(int)ceilf( iX - 0.5f - filterRadius ),
		(int)floorf( iX + 0.5f + filterRadius )
	);
}

// Precomputes all the filter weights for a whole row or column of a tile. For separable
// filters these weights can then be reused across all rows/columns in the same tile.
/// \todo The weights computed for a particular tile could also be reused for all
/// tiles in the same tile column or row. We could achieve this by outputting
/// the weights on an internal plug, and using Gaffer's caching to ensure they are
/// only computed once and then reused. At the time of writing, profiles indicate that
/// accessing pixels via the Sampler is the main bottleneck, but once that is optimised
/// perhaps cached filter weights could have a benefit.
void filterWeights1D( const OIIO::Filter2D *filter, const float inputFilterScale, const float filterRadius, const int x, const float ratio, const float offset, Passes pass, std::vector<int> &supportRanges, std::vector<float> &weights )
{
	weights.reserve( ( 2 * ceilf( filterRadius ) + 1 ) * ImagePlug::tileSize() );
	supportRanges.reserve( 2 * ImagePlug::tileSize() );

	const float filterCoordinateMult = 1.0f / inputFilterScale;

	for( int oX = x, eX = x + ImagePlug::tileSize(); oX < eX; ++oX )
	{
		// input pixel position (floating point)
		float iX = ( oX + 0.5f ) / ratio + offset;

		int minX = ceilf( iX - 0.5f - filterRadius );
		int maxX = floorf( iX + 0.5f + filterRadius );

		supportRanges.push_back( minX );
		supportRanges.push_back( maxX );

		for( int fX = minX; fX < maxX; ++fX )
		{
			const float f = filterCoordinateMult * ( float( fX ) + 0.5f - iX );
			// \todo - supportRanges should only include values != 0. Address at same time as
			// moving normalization in here.
			const float w = pass == Horizontal ? filter->xfilt( f ) : filter->yfilt( f );
			weights.push_back( w );
		}
	}
}

// For the inseparable case, we can't always reuse the weights for an adjacent row or column.
// There are a lot of possible scaling factors where the ratio can be represented as a fraction,
// and the weights needed would repeat after a certain number of pixels, and we could compute weights
// for a limited section of pixels, and reuse them in a tiling way.
// That's a bit complicated though, so we're just handling the simplest case currently ( since it is
// a common case ):
// if there is no scaling, then we only need to compute the weights for one pixel, and we can reuse them
// for all pixels. This means we don't loop over output pixels at all here - we just compute the weights
// for one output pixel, and return one 2D support for this pixel - it just gets shifted for each adjacent
// pixel.
void filterWeights2D( const OIIO::Filter2D *filter, const V2f inputFilterScale, const V2f filterRadius, const V2i p, const V2f ratio, const V2f offset, Box2i &support, std::vector<float> &weights )
{
	weights.reserve( ( 2 * ceilf( filterRadius.x ) + 1 ) * ( 2 * ceilf( filterRadius.y ) + 1 ) );
	weights.resize( 0 );

	const V2f filterCoordinateMult( 1.0f / inputFilterScale.x, 1.0f / inputFilterScale.y );

	// input pixel position (floating point)
	V2f i = ( V2f( p ) + V2f( 0.5f ) ) / ratio + offset;

	support = Box2i(
		V2i( ceilf( i.x - 0.5f - filterRadius.x ), ceilf( i.y - 0.5f - filterRadius.y ) ),
		V2i( floorf( i.x + 0.5f + filterRadius.x ), floorf( i.y + 0.5f + filterRadius.y ) )
	);

	for( int fY = support.min.y; fY < support.max.y; ++fY )
	{
		const float fy = filterCoordinateMult.y * ( float( fY ) + 0.5f - i.y );
		for( int fX = support.min.x; fX < support.max.x; ++fX )
		{
			const float fx = filterCoordinateMult.x * ( float( fX ) + 0.5f - i.x );
			const float w = (*filter)( fx, fy );
			weights.push_back( w );
		}
	}
}

// Find the x index of the nearest input pixel for each pixel in this row. Used to implement the fast
// path for the "nearest" filter.
void nearestInputPixelX( const int x, const float ratio, const float offset, std::vector<int> &result )
{
	result.reserve( ImagePlug::tileSize() );

	for( int oX = x, eX = x + ImagePlug::tileSize(); oX < eX; ++oX )
	{
		result.push_back( floorf( ( oX + 0.5f ) / ratio + offset ) );
	}
}

Box2f transform( const Box2f &b, const M33f &m )
{
	if( b.isEmpty() )
	{
		return b;
	}

	Box2f r;
	r.extendBy( V2f( b.min.x, b.min.y ) * m );
	r.extendBy( V2f( b.max.x, b.min.y ) * m );
	r.extendBy( V2f( b.max.x, b.max.y ) * m );
	r.extendBy( V2f( b.min.x, b.max.y ) * m );
	return r;
}

struct MixRange
{
	int min;
	int max;
};

// Given the filter parameters, find the total range of input values, and for each input value, give the
// possible other input values it may be filtered together with
void computeMixing(
	float filterRadius, int tileOrigin, float ratio, float offset,
	std::vector< MixRange > &mixing, int &mixingOrigin, int &mixingSize
)
{
	for( int i = 0; i < ImagePlug::tileSize(); i++ )
	{
		// Find the range of inputs for this output pixel
		int inputMin, inputMax;
		std::tie( inputMin, inputMax ) = filterSupport(
			filterRadius, tileOrigin + i, ratio, offset
		);

		if( i == 0 )
		{
			mixingOrigin = inputMin;
		}
		inputMin -= mixingOrigin;
		inputMax -= mixingOrigin;

		mixing.resize( inputMax, MixRange { std::numeric_limits<int>::max(), std::numeric_limits<int>::lowest() } );

		// Record that for every input used to output this output pixel, it may be mixed with any of the other
		// inputs used
		for( int j = inputMin; j < inputMax; j++ )
		{
			auto &cur = mixing[ j ];
			cur.min = std::min( cur.min, inputMin );
			cur.max = std::max( cur.max, inputMax );
		}
	}

	mixingSize = mixing.size();
}

struct ContributionElement
{
	int sourceIndex;
	int sampleIndex;
	float weight;
};

class DeepResampleData : public IECore::Data
{
public:
	IntVectorDataPtr sampleOffsetsData;
	FloatVectorDataPtr AData;
	FloatVectorDataPtr ZData;
	FloatVectorDataPtr ZBackData;
	std::vector< Box2i > contributionSupports;
	std::vector< int > contributionCounts;
	std::vector< ContributionElement > contributionElements;
};

IE_CORE_DECLAREPTR( DeepResampleData )

// In order to efficiently combine deep pixels, we first sample them at every depth we need to evaluate them
// at. Each sample is one of these 4 types:
enum DepthSampleType {
	// A point sample, which represent an instantenous increase in alpha at this depth. Originates from
	// source segments with ZBack == Z, or A == 1.0
	DepthSamplePoint = -2,

	// The beginning of volume segment. Does not add any extra information other than marking a beginning depth.
	// May be omitted if there is another sample type at the same depth, but we do need some sample at this
	// depth to mark the start Z of a volume segment
	DepthSampleStart = -1,

	// The end of a volume segment, outputted with at a depth of ZBack. Holds the completed values for the segment.
	DepthSampleEnd = 0,

	// A sample that is in between the start and end of a volume segment - it isn't required to be included
	// by this input pixel, but some pixel it is mixed with will require this interpolated value.
	//
	// We don't actually store these with an enum value of 1, instead any positive integer is treated as
	// an interpolated segment. This allows the "type" field for interpolated samples to store the index of
	// their corresponding End sample, to allow fast-forwarding.
	DepthSampleInterpolated = 1,
};

// Store all the information we need for a sampled depth
struct SampledDepth
{
	// The depth of this sample
	float depth;

	// What weight of the source segment do we take to reach the full value at this depth.
	// This fully bakes in both the alpha curve if we are taking a fraction of a segment,
	// but also alpha occlusion from previous segments.
	float linearContribution;

	// The final combined alpha of the source pixel at this depth.
	float accumAlpha;

	// The type of this sample, according to DepthSampleType. As described above, this includes the index
	// of the corresponding End sample for interpolated samples
	int type;
};

// Given the channel data for a pixel, and all depths it may be evaluated at, convert it to a list of
// SampledDepths will all information needed to evaluate it at any of those depths.
void samplePixelDepths(
	int count,
	const boost::span<const float> &z, const boost::span<const float> &zBack, const boost::span<const float> &alpha,
	const std::vector<float> &depths,
	std::vector< SampledDepth > &result
)
{
	// This is the maximum possible size of the result - it's usually larger than necessary, by an average
	// of 4X, but this excess size doesn't seem to hurt performance. The real big win here would probably
	// be to reuse the memory used for a sampled pixel once we have processed all output pixels that use it.
	result.reserve( depths.size() );

	float accumAlpha = 0.0f;
	unsigned int depthIndex = 0;
	for( int i = 0; i < count; i++ )
	{
		float segmentZ = z.size() ? z[i] : 0.0f;
		float segmentZBack = zBack.size() ? zBack[i] : segmentZ;

		if( std::isnan( segmentZ ) || std::isnan( segmentZBack ) )
		{
			continue;
		}

		float segmentAlpha = alpha.size() ? alpha[i] : 0.0f;
		if( !( segmentAlpha > 0.0f ) )
		{
			// Negative alphas aren't valid, treat them as zero, deal with NaN while we're at it
			segmentAlpha = 0.0f;
		}

		// Point samples come from source segments with ZBack == Z, or an alpha of 1 ( a fully opaque
		// segment always applies fully immediately )
		if( segmentAlpha >= 1.0f || !( segmentZBack > segmentZ ) )
		{
			float linearContribution = ( 1.0f - accumAlpha );
			accumAlpha += std::min( segmentAlpha, 1.0f ) * ( 1.0f - accumAlpha );
			result.push_back( SampledDepth { segmentZ, linearContribution, accumAlpha, DepthSamplePoint } );
		}
		else
		{
			// A start sample doesn't contain any information other than marking this depth:
			// we don't need to output it if there is already a sample at this depth.
			if( !result.size() || result.back().depth != segmentZ )
			{
				result.push_back( SampledDepth { segmentZ, 0.0f, accumAlpha, DepthSampleStart } );
			}

			// Skip any depths before the current segment ( we don't need to output samples
			// in order to support evaluating at depths that don't overlap with any of our segments )
			while( depthIndex < depths.size() && !( depths[depthIndex] > segmentZ ) )
			{
				depthIndex++;
			}

			// Check if we need to output any interpolated samples within this segment
			if( depthIndex < depths.size() && depths[depthIndex] < segmentZBack )
			{
				// Count how many interpolated samples we need
				unsigned int nextDepthIndex = depthIndex;
				while( nextDepthIndex < depths.size() && depths[nextDepthIndex] < segmentZBack )
				{
					nextDepthIndex++;
				}

				unsigned int endSample = result.size() + nextDepthIndex - depthIndex;
				// Splitting a segment at a given depth requires converting from and back to
				// an exponential curve. The first part can be shared between all interpolated samples
				// for this segment.
				float log1MinusAlpha = log1pf( -segmentAlpha );

				for( unsigned int j = depthIndex; j < nextDepthIndex; j++ )
				{
					float depth = depths[j];

					float depthFraction = std::min( 1.0f, ( depth - segmentZ ) / ( segmentZBack - segmentZ ) );
					if( !( depthFraction > 0.0f ) )
					{
						depthFraction = 0.0f;
					}

					if( segmentAlpha == 0.0f )
					{
						// If the segment has 0 alpha, the EXR deep spec mandates a different, linear behaviour
						result.push_back( SampledDepth { depth, ( 1.0f - accumAlpha ) * depthFraction, accumAlpha, (int)endSample } );
					}
					else
					{
						// Output an interpolated sample at this depth, storing the accumulated alpha after
						// taking part of this segment, and the linear contribution amount that comes from
						// the fraction of this segment that we're taking, multiplied by occlusion from previous
						// segments.
						float curAlpha = -expm1f( depthFraction * log1MinusAlpha );
						result.push_back( SampledDepth {
							depth,
							std::min( 1.0f, curAlpha / segmentAlpha ) * ( 1.0f - accumAlpha ),
							accumAlpha + curAlpha * ( 1.0f - accumAlpha ),
							(int)endSample
						} );
					}
				}

				depthIndex = nextDepthIndex;
			}

			// Every volume segment must store an end sample
			float linearContribution = ( 1 - accumAlpha );
			accumAlpha += segmentAlpha - segmentAlpha * accumAlpha;
			result.push_back( { segmentZBack, linearContribution, accumAlpha, DepthSampleEnd } );
		}
	}
}

// Given sampled depths for a series of source pixels, each with a corresponding weight, combine them
// into an output pixel with alpha, Z and ZBack channels, and return the number of samples. Also
// optionally fill vectors storing the source indices and weights for each contribution to each output
// sample, which can be used to later process other channels in a matching way.
int linearCombineSampledPixels(
	const std::vector< const std::vector< SampledDepth > * > &sources, const std::vector< float > &weights,
	std::vector< float > &outputAlpha, std::vector< float > &outputZ, std::vector< float > &outputZBack,
	std::vector< int > *contributionCounts, std::vector< ContributionElement > *contributionElements
)
{
	const unsigned int numSources = sources.size();

	unsigned int totalSamplesToProcess = 0;

	// Store the number of source volume segments that have reached their start, but not yet reached
	// their end. As long as there are any open segments, we much split them at the current depth
	// if we start a new segment.
	int numVolumeSegmentsOpen = 0;

	// Store the next sample depth for each source, allowing us to quickly skip sources that
	// don't have samples at the current depth
	std::vector<float> sourceNextSample( numSources, std::numeric_limits<float>::infinity() );

	// We may not need to output anything at interpolated samples ( they could represent depths
	// that are needed for output pixels other than the current one ), but we must output something
	// at any Start, End, or Point samples. This vector stores the next required sample for each
	// source, so we can quickly find the minimum to know the next thing to output.
	std::vector<float> sourceNextMandatory( numSources, std::numeric_limits<float>::infinity() );

	// terminateAccumAlpha holds the final accumulated alpha value for this pixel. It is used in
	// the case of negative lobes to store the value we can never go over. With negative lobes,
	// it is possible for the true filtered alpha value to go over the final value, and then back
	// down to it - which we can't do in our output, because a deep alpha must be non-decreasing
	// in depth. Instead, we stop as soon as we go over the final value, clamp to the final alpha,
	// and then combine all contributions into that final segment - which results in something
	// that sums up properly to the final value, even though it omits the part of the curve that
	// overshoots.
	double terminateAccumAlpha = 0.0f;
	bool hasNegativeWeights = false;

	for( unsigned int i = 0; i < numSources; i++ )
	{
		if( sources[i]->size() )
		{
			sourceNextSample[i] = (*sources[i])[0].depth;
			sourceNextMandatory[i] = (*sources[i])[0].depth;
			totalSamplesToProcess += sources[i]->size();
			hasNegativeWeights |= weights[i] < 0.0f;
			terminateAccumAlpha += ( (double)sources[i]->back().accumAlpha ) * weights[i];
		}
	}

	terminateAccumAlpha = std::min( terminateAccumAlpha, 1.0 );

	if( !hasNegativeWeights )
	{
		// If we have no negative weights, then we don't need to worry about prematurely going over the
		// final alpha, before subtracting back down to it. The only way the terminateAccumAlpha
		// conditional could trip is due to floating point precision issues ... to avoid that, just
		// set it to something that won't trip prematurely.
		terminateAccumAlpha = 1.0;
	}

	if( terminateAccumAlpha < 0.0 )
	{
		// Our rule for dealing with negative lobes is that contributions in areas where the curve is decreasing
		// will be buffered and output once the curve goes positive again. If the curve never goes positive,
		// we don't output anything.
		return 0;
	}

	// The index of sampled depth we have currently covered up to for each source
	std::vector<int> sourceIndex( numSources, -1 );

	// The original index of the segment in the source pixel which the current sample came from for each source.
	// Because of interpolated samples, there may be many samples per original segment.
	std::vector<int> sourceOrigIndex( numSources, 0 );
	double totalAccumAlpha = 0;
	double prevTotalAccumAlpha = 0;

	float prevDepth = std::numeric_limits<float>::infinity();
	int numSegments = 0;

	int contributionCount = 0;

	unsigned int totalSamplesDone = 0;
	unsigned int prevTotalSamplesDone = 0;
	bool terminating = false;
	while( totalSamplesDone < totalSamplesToProcess && totalAccumAlpha < 1.0f && !terminating )
	{
		// The depth we output something at is the minimum depth required by any source
		float outputDepth = std::numeric_limits<float>::infinity();
		for( unsigned int i = 0; i < numSources; i++ )
		{
			if( sourceNextMandatory[i] < outputDepth )
			{
				outputDepth = sourceNextMandatory[i];
			}
		}

		// If there are volume segments open, we must output a volume, unless we've already output a volume
		// up to the current depth, and then we can output a point sample here before we go back to outputting
		// volume samples.
		bool segmentIsVolume = numVolumeSegmentsOpen > 0 && !( outputDepth == prevDepth );

		// Now loop through our sources, and take any samples that match this depth.
		for( unsigned int i = 0; i < numSources; i++ )
		{
			if( !( sourceNextSample[i] <= outputDepth ) )
			{
				continue;
			}

			const std::vector<SampledDepth> &curSamples = (*sources[i]);

			int curIndex = sourceIndex[i] + 1;

			// The early out using sourceNextSample should handle hitting the end of the source, but
			// there's a weird case if some samples actually have depth values of infinity.
			if( !( curIndex < (int)curSamples.size() ) )
			{
				continue;
			}

			int sampleType = curSamples[ curIndex ].type;

			// If we've completed some section of volume, remove one from count of open volume segments.
			// If we're actually in the middle of a volume segment, it will immediately be added back below.
			numVolumeSegmentsOpen -= sampleType >= DepthSampleEnd;
			if( sampleType == DepthSamplePoint && segmentIsVolume )
			{
				// The next event is finishing a volume segment. We must finish that first,
				// before outputting a point sample.
				continue;
			}

			if( sampleType == DepthSamplePoint )
			{
				if( curIndex + 1 < (int)curSamples.size() && curSamples[ curIndex + 1 ].depth <= outputDepth )
				{
					// Ugly special case where we need to consider the possibility of two points at the
					// same depth. See comment "Double Point Sample" below.
					curIndex++;
				}
			}
			else if( sampleType >= DepthSampleInterpolated )
			{
				if( curSamples[ sampleType ].depth <= outputDepth )
				{
					curIndex = sampleType;
				}
				else
				{
					while( curIndex + 1 < (int)curSamples.size() && curSamples[ curIndex + 1 ].depth <= outputDepth )
					{
						curIndex++;
					}
				}
			}

			if( curSamples[curIndex].type != DepthSampleStart )
			{
				// Rather than keeping a running sum, it would be a bit simpler to reason about this if
				// we just summed sources[i][sourceIndex[i]] * weights[i] for all i after each segment.
				// The performance cost of doing that is not actually noticeable, however it seems that
				// there is noticeable error introduced by doing this sum in float, rather than double.
				// And if we have to use double precision anyway, we have plenty of precision to keep
				// an accurate running sum.
				totalAccumAlpha += ( (double)curSamples[curIndex].accumAlpha - ( sourceIndex[i] >= 0 ? (double)curSamples[sourceIndex[i]].accumAlpha : 0.0 ) ) * weights[i];

				if( contributionElements )
				{
					if( curSamples[curIndex].type == DepthSamplePoint && curIndex - sourceIndex[i] == 2 && curSamples[curIndex-1].type == DepthSamplePoint )
					{
						// "Double Point Sample" - this is an unfortunate special case.
						// Usually, we include a single source index per source in each output sample, and this
						// should be adequate to capture everything - the input is "tidy", which requires there
						// be no more than one segment at each depth. However, we allow "volume" segments with
						// an alpha of 1, which have different Z and ZBack values, but because they are fully
						// opaque, their entire contribution applies as soon as you reach the Z depth, regardless
						// of ZBack. This means that we must treat them as point samples in order to composite
						// properly with other pixel we are blending with ... but that means that there is a legal
						// input with a point segment followed by an opaque volume segment at the same depth, with
						// the result that we get two point samples at the same depth, which need to be output
						// at the same time, which is handled here.
						//
						// If we wanted to omit this special case, the cleanest option might be to redefine "tidy"
						// to include converting samples with an alpha of 1 to point samples ( since it's weird to
						// store a ZBack value that has no effect ), and then tidying would be responsible for
						// combining these two segments into one ... this is not part of the standard definition
						// of "tidy" however.
						contributionCount++;
						float skippedContribution = curSamples[curIndex-1].linearContribution / ( 1.0 - prevTotalAccumAlpha );
						contributionElements->push_back( ContributionElement {
							(int)i, sourceOrigIndex[i], weights[i] * skippedContribution
						} );

						sourceOrigIndex[i]++;
					}
					contributionCount++;

					// To find the linear weighting of this contribution to the output, we must include 3 factors:
					// * the linearContribution stored in the sample
					// * if it's an interpolated sample, we must substract off the fraction already output
					// * and we must include occlusion from the output segments so far
					float prevContribution = 0.0f;
					if( curSamples[curIndex].type != DepthSamplePoint && curSamples[sourceIndex[i]].type >= DepthSampleInterpolated )
					{
						prevContribution = curSamples[sourceIndex[i]].linearContribution;
					}
					float linearContribution =
						( curSamples[curIndex].linearContribution - prevContribution ) /
						( 1.0 - prevTotalAccumAlpha );

					assert( linearContribution >= 0.0f );

					contributionElements->push_back( ContributionElement {
						(int)i, sourceOrigIndex[i], weights[i] * linearContribution
					} );

					if( curSamples[curIndex].type < DepthSampleInterpolated )
					{
						// We must track the index of the source segment we are adding contributions from. This
						// goes up for every sample we output, unless it's an interpolated sample.
						sourceOrigIndex[i]++;
					}
				}
			}

			totalSamplesDone += curIndex - sourceIndex[i];

			sourceIndex[i] = curIndex;

			int nextIndex = curIndex + 1;

			if( nextIndex < (int)curSamples.size() )
			{
				int sampleType = curSamples[nextIndex].type;

				// If the next sample in this source is an end sample or an interpolated sample,
				// then add one open segment.
				numVolumeSegmentsOpen += sampleType >= DepthSampleEnd;

				if( sampleType >= DepthSampleInterpolated )
				{
					// Leverage the special way we store interpolated types - the value of the type is actually
					// the index of the End sample for this segment, which is the next depth this source
					// requires us to output.
					sourceNextMandatory[i] = curSamples[ sampleType ].depth;
				}
				else
				{
					// If this isn't an interpolated sample, then we need to output this depth.
					sourceNextMandatory[i] = curSamples[ nextIndex ].depth;
				}

				// Update the sourceNextSample value used to quick skip this source when it doesn't
				// have anything to contribute.
				sourceNextSample[i] = curSamples[ nextIndex ].depth;
			}
			else
			{
				// This source is done, we don't need to do more with it
				sourceNextMandatory[i] = std::numeric_limits<float>::infinity();
				sourceNextSample[i] = std::numeric_limits<float>::infinity();
			}
		}

		// We've processed all the sources at this depth, now we can actually consider outputting a segment.
		// There are two cases where we don't output a segment, because the totalAccumAlpha has not increased:
		// * we might have processed just samples of type DepthSampleStart, which are just there to get the
		//   depth correct, and don't add any contribution.
		// * if there are negative lobes, we might have had contributions which lowered the alpha. In this
		//   case, we buffer up those contributions, and don't output them until the alpha goes back up above
		//   the last valid prevTotalAccumAlpha
		if( totalAccumAlpha >= prevTotalAccumAlpha )
		{
			// For volume segments, the segment starts at the last depth we processed, for point samples,
			// it starts right her.
			if( !segmentIsVolume )
			{
				prevDepth = outputDepth;
			}

			double segmentEndAccumAlpha = totalAccumAlpha;
			if( segmentEndAccumAlpha > terminateAccumAlpha )
			{
				segmentEndAccumAlpha = terminateAccumAlpha;
				terminating = true;
			}

			// The accumAlpha is accumulated additively. We need to convert that into a multiplicative
			// alpha that will composite properly.
			float segmentAlpha = ( segmentEndAccumAlpha - prevTotalAccumAlpha ) / ( 1.0 - prevTotalAccumAlpha );

			// Add a value to each of our hardcode output channels
			outputAlpha.push_back( segmentAlpha );
			outputZ.push_back( prevDepth );
			outputZBack.push_back( outputDepth );

			// And if we need to process arbitrary channels, we need to store how many contributions we
			// need for this output
			if( contributionCounts )
			{
				contributionCounts->push_back( contributionCount );
				contributionCount = 0;
			}

			numSegments++;

			if( !terminating )
			{
				// If we have more segments left to output, update prevTotalAccumAlpha to be ready for the
				// next segment. Otherwise, keep the value, so we can use it if we need to cram a few more
				// samples into the last segment in the final part of this function.
				prevTotalAccumAlpha = totalAccumAlpha;
			}
		}

		// Ready for next loop
		prevDepth = outputDepth;

		if( !( totalSamplesDone > prevTotalSamplesDone ) )
		{
			// In theory, this should just be an assert, but if there is any logic error here
			// triggered by a weird floating point value or something, this could lead to a hang.
			// We definitely don't want to hang - if we complete an iteration without progress, throw
			// an exception instead.
			throw IECore::Exception(
				"Internal failure in Resample while processing deep image. This should "
				"not be possible. We would appreciate if you can isolate a crop of the image which triggers "
				"the issue and submit it to the Gaffer dev team."
			);
		}
		prevTotalSamplesDone = totalSamplesDone;
	}

	// Negative filter lobes may cause us to terminate the depth traversal prematurely, because the
	// curve tries to go over the final alpha and then back down. In this case, we stop the traversal
	// when we first reach the final alpha, and then cram all remaining contributions into that final
	// segment, which should yield a correct final accumulated value.
	if( totalSamplesDone < totalSamplesToProcess && contributionElements && prevTotalAccumAlpha < 1.0 )
	{
		for( unsigned int i = 0; i < numSources; i++ )
		{
			const std::vector<SampledDepth> &curSamples = (*sources[i]);

			// The first segment may be the second half of a volume segment, which is more complex.
			// After the first segment, we only output full segments during termination.
			bool firstSegment = true;

			for( int curIndex = sourceIndex[i] + 1; curIndex < (int)curSamples.size(); curIndex++ )
			{
				// We don't need to consider partial contributions while cramming in the remaining
				// contributions - we only take complete contribution represented by Point or End
				// samples.
				if( curSamples[curIndex].type == DepthSamplePoint || curSamples[curIndex].type == DepthSampleEnd )
				{
					float linearContribution = 0.0f;
					// The first contribution segment we find may be the end of a segment which we've already
					// output some interpolated segments from, in which case we need to subtract that.
					if( firstSegment && curSamples[curIndex].type == DepthSampleEnd && sourceIndex[i] >= 0 && curSamples[sourceIndex[i]].type >= DepthSampleInterpolated )
					{
						float prevContribution = curSamples[sourceIndex[i]].linearContribution;
						linearContribution =
							( curSamples[curIndex].linearContribution - prevContribution ) /
							( 1.0f - prevTotalAccumAlpha );
					}
					else
					{
						linearContribution = curSamples[curIndex].linearContribution / ( 1.0 - prevTotalAccumAlpha );
					}

					// Add to the list of contributions
					contributionCount++;
					contributionElements->push_back( ContributionElement {
						(int)i, sourceOrigIndex[i], weights[i] * linearContribution
					} );

					sourceOrigIndex[i]++;
					firstSegment = false;
				}
			}
		}
	}

	if( contributionCounts && numSegments )
	{
		// Any contributions that haven't been output yet are getting tacked on to the last segment.
		contributionCounts->back() += contributionCount;
	}
	else if( contributionElements && contributionCount )
	{
		// I don't think this should ever trigger - if there are contributions left over, and
		// terminateAccumAlpha is >= 0, so that we didn't early exit, then there should be at least
		// one segment output, and we'll take the branch above. But just in case there's somehow
		// some floating point precision issue where we somehow don't output any segments, it feels
		// safer to discard the unused contributions.
		contributionElements->resize( contributionElements->size() - contributionCount );
	}

	return numSegments;
}


// This is a pretty specific tool, but this step is quite important to the performance of deep resampling.
// It is initialized with a vector of vectors of sorted floats. You can then call addList with the indices
// of the lists you want to merge, and then call mergeLists to get a sorted list formed by merging all
// the lists you've selected. You then call clear() to clear out the selected lists, and can pick a different
// subset to merge.
class MergeListsByIndices
{
public:
	MergeListsByIndices( const std::vector< std::vector<float> > &allLists )
		: m_allLists( allLists ), m_listPositions( allLists.size() )
	{
	}

	void clear()
	{
		m_heap.resize( 0 );
	}

	void addList( int i )
	{
		if( m_allLists[i].size() )
		{
			m_heap.push_back( { m_allLists[i][0], i } );
		}
	}

	void mergeLists( std::vector< float > &result )
	{
		for( const auto &i : m_heap )
		{
			m_listPositions[ i.listIndex ] = 0;
		}

		std::make_heap( m_heap.begin(), m_heap.end() );

		result.resize( 0 );

		if( !m_heap.size() )
		{
			return;
		}

		float prev = m_heap[0].depth;
		result.push_back( m_heap[0].depth );

		while( m_heap.size() )
		{
			if( m_heap[0].depth != prev )
			{
				result.push_back( m_heap[0].depth );
				prev = m_heap[0].depth;
			}
			int listIndex = m_heap[0].listIndex;
			const std::vector< float > &curList = m_allLists[ listIndex ];

			m_listPositions[ listIndex ] ++;

			// This seems like the best we can do that adheres to the spec for the STL.
			// Updating the root priority by doing rotations starting at the root seems
			// to be 10% faster, but this is good enough for now.
			std::pop_heap( m_heap.begin(), m_heap.end() );
			if( m_listPositions[ listIndex ] < curList.size() )
			{
				m_heap.back().depth = curList[ m_listPositions[ listIndex ] ];
				std::push_heap( m_heap.begin(), m_heap.end() );
			}
			else
			{
				m_heap.pop_back();
			}
		}
	}

private:
	struct HeapEntry
	{
		float depth;
		int listIndex;
		inline bool operator<( const HeapEntry& other ) const
		{
			return depth > other.depth;
		}
	};

	std::vector< HeapEntry > m_heap;
	const std::vector< std::vector<float> > &m_allLists;
	std::vector< unsigned int > m_listPositions;
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Resample
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Resample );

size_t Resample::g_firstPlugIndex = 0;

Resample::Resample( const std::string &name )
	: ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new M33fPlug( "matrix" ) );
	addChild( new StringPlug( "filter" ) );
	addChild( new V2fPlug( "filterScale", Plug::In, V2f( 1 ), V2f( 0 ) ) );
	addChild( new IntPlug( "boundingMode", Plug::In, Sampler::Black, Sampler::Black, Sampler::Clamp ) );
	addChild( new BoolPlug( "expandDataWindow" ) );
	addChild( new IntPlug( "debug", Plug::In, Off, Off, SinglePass ) );
	addChild( new BoolPlug( "filterDeep" ) );
	addChild( new ImagePlug( "__horizontalPass", Plug::Out ) );
	addChild( new ImagePlug( "__tidyIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );
	addChild( new ObjectPlug( "__deepResampleData", Gaffer::Plug::Out, IECore::NullObject::defaultNullObject() ) );


	// We don't ever want to change these, so we make pass-through connections.

	outPlug()->viewNamesPlug()->setInput( inPlug()->viewNamesPlug() );
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );

	horizontalPassPlug()->viewNamesPlug()->setInput( inPlug()->viewNamesPlug() );
	horizontalPassPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	horizontalPassPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	horizontalPassPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );

	DeepStatePtr tidy = new DeepState( "__tidy" );
	addChild( tidy );
	tidy->inPlug()->setInput( inPlug() );
	tidyInPlug()->setInput( tidy->outPlug() );

	outPlug()->deepPlug()->setInput( inPlug()->deepPlug() );
	horizontalPassPlug()->deepPlug()->setInput( inPlug()->deepPlug() );
}

Resample::~Resample()
{
}

Gaffer::M33fPlug *Resample::matrixPlug()
{
	return getChild<M33fPlug>( g_firstPlugIndex );
}

const Gaffer::M33fPlug *Resample::matrixPlug() const
{
	return getChild<M33fPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *Resample::filterPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *Resample::filterPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::V2fPlug *Resample::filterScalePlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::V2fPlug *Resample::filterScalePlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 2 );
}

Gaffer::IntPlug *Resample::boundingModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::IntPlug *Resample::boundingModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

Gaffer::BoolPlug *Resample::expandDataWindowPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::BoolPlug *Resample::expandDataWindowPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

Gaffer::IntPlug *Resample::debugPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::IntPlug *Resample::debugPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 5 );
}

Gaffer::BoolPlug *Resample::filterDeepPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::BoolPlug *Resample::filterDeepPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 6 );
}

ImagePlug *Resample::horizontalPassPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex + 7 );
}

const ImagePlug *Resample::horizontalPassPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex + 7 );
}

ImagePlug *Resample::tidyInPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex + 8 );
}

const ImagePlug *Resample::tidyInPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex + 8 );
}

ObjectPlug *Resample::deepResampleDataPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 9 );
}

const ObjectPlug *Resample::deepResampleDataPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 9 );
}

void Resample::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if(
		input == inPlug()->dataWindowPlug() ||
		input == matrixPlug() ||
		input == expandDataWindowPlug() ||
		input == filterPlug() ||
		input->parent<V2fPlug>() == filterScalePlug() ||
		input == debugPlug()
	)
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( horizontalPassPlug()->dataWindowPlug() );
	}

	if(
		input == inPlug()->dataWindowPlug() ||
		input == matrixPlug() ||
		input == filterPlug() ||
		input->parent<V2fPlug>() == filterScalePlug() ||
		input == inPlug()->channelDataPlug() ||
		input == boundingModePlug() ||
		input == debugPlug() ||
		input == filterDeepPlug() ||
		input == inPlug()->deepPlug() ||
		input == deepResampleDataPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
		outputs.push_back( horizontalPassPlug()->channelDataPlug() );
	}

	if(
		input == inPlug()->channelNamesPlug() ||
		input == inPlug()->dataWindowPlug() ||
		input == matrixPlug() ||
		input == filterPlug() ||
		input->parent<V2fPlug>() == filterScalePlug() ||
		input == tidyInPlug()->channelDataPlug() ||
		input == tidyInPlug()->sampleOffsetsPlug() ||
		input == boundingModePlug()
	)
	{
		outputs.push_back( deepResampleDataPlug() );
	}

	if(
		input == inPlug()->dataWindowPlug() ||
		input == deepResampleDataPlug() ||
		input == matrixPlug() ||
		input == filterPlug() ||
		input == boundingModePlug() ||
		input == filterDeepPlug() ||
		input == inPlug()->deepPlug()
	)
	{
		outputs.push_back( outPlug()->sampleOffsetsPlug() );
	}
}

void Resample::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hash( output, context, h );

	if( output != deepResampleDataPlug() )
	{
		return;
	}

	ConstStringVectorDataPtr channelNamesData;
	V2f ratio, offset;
	Sampler::BoundingMode boundingMode;
	V2f filterScale;
	std::string filterName;

	V2f inputFilterScale( 0 );
	const OIIO::Filter2D *filter = nullptr;

	{
		ImagePlug::GlobalScope s( context );
		channelNamesData = inPlug()->channelNamesPlug()->getValue();
		ratioAndOffset( matrixPlug()->getValue(), ratio, offset );
		boundingMode = (Sampler::BoundingMode)boundingModePlug()->getValue();

		const std::string filterName = filterPlug()->getValue();
		filter = filterAndScale( filterName, ratio, inputFilterScale );
		inputFilterScale *= filterScalePlug()->getValue();
	}

	filterPlug()->hash( h );
	h.append( inputFilterScale );
	h.append( ratio );
	h.append( offset );

	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	Box2i ir = inputRegion( tileOrigin, Both, ratio, offset, filter, inputFilterScale );

	bool hasA = false;
	bool hasZ = false;
	bool hasZBack = false;
	bool hasArbitraryChannel = false;
	for( const std::string &c : channelNamesData->readable() )
	{
		if( c == ImageAlgo::channelNameA )
		{
			hasA = true;
		}
		else if( c == ImageAlgo::channelNameZ )
		{
			hasZ = true;
		}
		else if( c == ImageAlgo::channelNameZBack )
		{
			hasZBack = true;
		}
		else
		{
			hasArbitraryChannel = true;
		}
	}

	if( hasZ )
	{
		DeepPixelAccessor( tidyInPlug(), ImageAlgo::channelNameZ, ir, boundingMode ).hash( h );
	}
	else
	{
		h.append( false );
	}
	if( hasZBack )
	{
		DeepPixelAccessor( tidyInPlug(), ImageAlgo::channelNameZBack, ir, boundingMode ).hash( h );
	}
	else
	{
		h.append( false );
	}
	if( hasA )
	{
		DeepPixelAccessor( tidyInPlug(), ImageAlgo::channelNameA, ir, boundingMode ).hash( h );
	}
	else
	{
		h.append( false );
	}

	h.append( hasArbitraryChannel );

	// Another tile might happen to need to filter over the same input
	// tiles as this one, so we must include the tile origin to make sure
	// each tile has a unique hash.
	h.append( tileOrigin );
}

void Resample::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	ImageProcessor::compute( output, context );

	if( output != deepResampleDataPlug() )
	{
		return;
	}

	ConstStringVectorDataPtr channelNamesData;
	V2f ratio, offset;
	Sampler::BoundingMode boundingMode;

	V2f inputFilterScale(0);
	const OIIO::Filter2D *filter = nullptr;

	{
		ImagePlug::GlobalScope s( context );
		channelNamesData = inPlug()->channelNamesPlug()->getValue();
		ratioAndOffset( matrixPlug()->getValue(), ratio, offset );
		boundingMode = (Sampler::BoundingMode)boundingModePlug()->getValue();

		const std::string filterName = filterPlug()->getValue();
		filter = filterAndScale( filterName, ratio, inputFilterScale );
		inputFilterScale *= filterScalePlug()->getValue();
	}

	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	Box2i ir = inputRegion( tileOrigin, Both, ratio, offset, filter, inputFilterScale );

	// Pass in an empty channel name to only access the sampleOffsets
	DeepPixelAccessor sampleOffsetsSampler( tidyInPlug(), "", ir, boundingMode );
	sampleOffsetsSampler.populate();

	bool hasA = false;
	bool hasZ = false;
	bool hasZBack = false;

	// We usually try to process channels independently, and not make a computation like this dependent on
	// whether other channels are going to read it, but this is a bit of a special case. Computing the
	// resampling of a deep image requires using A, Z, and ZBack, so we can directly compute the results
	// for those channels. If there are other channels that need processing, we can output the weights
	// for how that channel data needs to be combined to match our results ... but those weights take a lot
	// of memory ( larger than the result for any channel, which requires combining multiple weighted inputs
	// for each output ). We can save a lot of memory and time if there are no arbitrary channels, and all
	// we need is the A/Z/ZBack results, and we don't need to store the weights. It would likely actually be
	// more efficient to directly compute the results for every channel, rather than storing the weights,
	// though that would be even more atypical for Gaffer's approach ( and would be very inefficient if you
	// have a large number of channels, and don't read all of them ).
	bool hasArbitraryChannel = false;

	for( const std::string &c : channelNamesData->readable() )
	{
		if( c == ImageAlgo::channelNameA )
		{
			hasA = true;
		}
		else if( c == ImageAlgo::channelNameZ )
		{
			hasZ = true;
		}
		else if( c == ImageAlgo::channelNameZBack )
		{
			hasZBack = true;
		}
		else
		{
			hasArbitraryChannel = true;
		}
	}
	std::optional<DeepPixelAccessor> zSampler, zBackSampler, alphaSampler;
	if( hasZ )
	{
		zSampler.emplace( sampleOffsetsSampler, ImageAlgo::channelNameZ );
	}
	if( hasZBack )
	{
		zBackSampler.emplace( sampleOffsetsSampler, ImageAlgo::channelNameZBack );
	}
	if( hasA )
	{
		alphaSampler.emplace( sampleOffsetsSampler, ImageAlgo::channelNameA );
	}

	const V2f filterRadius = inputFilterRadius( filter, inputFilterScale );
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

	// In order to produce resampled pixels by combining input pixels, we will need to split those input
	// pixels at each depth we need to output. We want to do any expensive computations required for this
	// splitting up front, so we need to start by looking at the surrounding pixels, and finding every depth
	// where one of the surrounding pixels that gets mixed together with this pixel could trigger a split.
	//
	// In order to determine this, we start by finding the total range of inputs, and for each input,
	// the range of inputs it is mixed with.
	std::vector< MixRange > horizontalMixing, verticalMixing;
	V2i inputOrigin, inputSize;
	computeMixing(
		filterRadius.x, tileOrigin.x, ratio.x, offset.x,
		horizontalMixing, inputOrigin.x, inputSize.x
	);
	computeMixing(
		filterRadius.y, tileOrigin.y, ratio.y, offset.y,
		verticalMixing, inputOrigin.y, inputSize.y
	);

	// Now that we have these lists defining the rectangular range that each input pixel will be mixed with,
	// we start by collecting all the depths from other input pixels in the same row that are mixed with
	// each input pixel.
	std::vector< std::vector< float > > horizontallyMixedDepths;
	horizontallyMixedDepths.reserve( inputSize.x * inputSize.y );

	for( int y = 0; y < inputSize.y; y++ )
	{
		Canceller::check( context->canceller() );
		for( int x = 0; x < inputSize.x; x++ )
		{
			horizontallyMixedDepths.push_back( std::vector< float >() );
			std::vector<float> &curMixDepths = horizontallyMixedDepths.back();

			// Loop through the other pixels in this row that influence this pixel, collect all depths.
			for( int j = horizontalMixing[x].min; j < horizontalMixing[x].max; j++ )
			{
				boost::span<const float> zSamples;
				boost::span<const float> zBackSamples;
				if( zSampler )
				{
					zSamples = zSampler->sample( j + inputOrigin.x, y + inputOrigin.y );

					if( zBackSampler )
					{
						zBackSamples = zBackSampler->sample( j + inputOrigin.x, y + inputOrigin.y );
						assert( zSamples.size() == zBackSamples.size() );

						for( unsigned int k = 0; k < zSamples.size(); k++ )
						{
							if( !std::isnan( zSamples[k] ) ) curMixDepths.push_back( zSamples[k] );
							if( !std::isnan( zBackSamples[k] ) ) curMixDepths.push_back( zBackSamples[k] );
						}
					}
					else
					{
						for( unsigned int k = 0; k < zSamples.size(); k++ )
						{
							if( !std::isnan( zSamples[k] ) ) curMixDepths.push_back( zSamples[k] );
						}
					}
				}
			}

			// Sort all the depths from this row that contribute to this pixel.
			// By presorting per row, that means that when we go to collect all depths in the full
			// rectangular range affecting each input pixel, we can just merge sorted lists, rather than
			// doing a full sort.
			std::sort( curMixDepths.begin(), curMixDepths.end() );

			// It's also worth it to get rid of dupes here, since this work is shared across columns,
			// and it takes care of ZBack == Z
			curMixDepths.erase( std::unique( curMixDepths.begin(), curMixDepths.end() ), curMixDepths.end() );
		}
	}


	// We've now got everything we need to determine all depths that each input pixel needs to be evaluated at,
	// so we can put together a list of input pixels, sampled at each depth we will need during the actual
	// combining step.
	std::vector< std::vector< SampledDepth > > sampledPixels( inputSize.x * inputSize.y );

	MergeListsByIndices listMerger( horizontallyMixedDepths );
	std::vector< float > fullyMixedDepths;

	for( int y = 0; y < inputSize.y; y++ )
	{
		for( int x = 0; x < inputSize.x; x++ )
		{
			Canceller::check( context->canceller() );
			// We've already computed the horizontal mixing of depths - select all of those sublists
			// in this column that contribute to the mixing in this pixel in order to get a full list
			// of depths.
			listMerger.clear();
			for( int j = verticalMixing[y].min; j < verticalMixing[y].max; j++ )
			{
				listMerger.addList( j * inputSize.x + x );
			}
			listMerger.mergeLists( fullyMixedDepths );

			// fullyMixedDepths now contains a sorted list of every depth that this pixel could be evaluated at

			// Collect all channel data for this pixel
			unsigned int pixelCount = 0;
			boost::span<const float> pixelZ;
			boost::span<const float> pixelZBack;
			boost::span<const float> pixelAlpha;

			if( alphaSampler )
			{
				pixelAlpha = alphaSampler->sample( x + inputOrigin.x, y + inputOrigin.y );
				pixelCount = pixelAlpha.size();
			}
			if( zSampler )
			{
				pixelZ = zSampler->sample( x + inputOrigin.x, y + inputOrigin.y );
				pixelCount = pixelZ.size();
			}
			if( zBackSampler )
			{
				pixelZBack = zBackSampler->sample( x + inputOrigin.x, y + inputOrigin.y );
				pixelCount = pixelZBack.size();
			}

			// Sample this pixel at all depths where we may need to evaluate it
			samplePixelDepths(
				pixelCount, pixelZ, pixelZBack, pixelAlpha,
				fullyMixedDepths,
				sampledPixels[ y * inputSize.x + x ]
			);
		}
	}

	Box2i support;
	std::vector<float> weights;
	// If the ratio is 1, then we can reuse the same filter weights for every pixel
	if( ratio == V2f(1) )
	{
		filterWeights2D( filter, inputFilterScale, filterRadius, tileBound.min, V2f( 1 ), offset, support, weights );
		// \todo - why the heck isn't this being done in filterWeights*?
		float total = 0;
		for( float w : weights )
		{
			total += w;
		}
		for( float &w : weights )
		{
			w /= total;
		}
	}

	DeepResampleDataPtr result = new DeepResampleData();
	result->sampleOffsetsData = new IntVectorData();
	std::vector<int> &outputSampleOffsets = result->sampleOffsetsData->writable();
	result->AData = new FloatVectorData();
	std::vector<float> &outputAlpha = result->AData->writable();
	result->ZData = new FloatVectorData();
	std::vector<float> &outputZ = result->ZData->writable();
	result->ZBackData = new FloatVectorData();
	std::vector<float> &outputZBack = result->ZBackData->writable();

	unsigned int currentOutputSampleOffset = 0;

	if( hasArbitraryChannel )
	{
		result->contributionSupports.reserve( ImagePlug::tilePixels() );
		// \todo - it's a noticable performance improvement to reserve contributionElements as well
		// here, but it's harder to find a good estimate for that.
	}

	V2i oP; // output pixel position
	V2i supportOffset( 0 );

	const std::vector< SampledDepth > emptyPixel;
	std::vector< const std::vector< SampledDepth > * > contributingPixels;
	for( oP.y = tileBound.min.y; oP.y < tileBound.max.y; ++oP.y )
	{
		for( oP.x = tileBound.min.x; oP.x < tileBound.max.x; ++oP.x )
		{
			if( ratio != V2f(1) )
			{
				// If the ratio is not 1, we need to compute new weights for every pixel
				filterWeights2D( filter, inputFilterScale, filterRadius, oP, ratio, offset, support, weights );
				float total = 0;
				for( float w : weights )
				{
					total += w;
				}
				for( float &w : weights )
				{
					w /= total;
				}
			}
			else
			{
				supportOffset = oP - tileBound.min;
			}

			// Assert all our accesses are in bounds
			assert(
				support.min.x + supportOffset.x >= inputOrigin.x &&
				support.min.y + supportOffset.y >= inputOrigin.y &&
				support.max.x + supportOffset.x <= inputOrigin.x + inputSize.x &&
				support.max.y + supportOffset.y <= inputOrigin.y + inputSize.y
			);

			Canceller::check( context->canceller() );

			contributingPixels.resize( weights.size() );

			if( hasArbitraryChannel )
			{
				result->contributionSupports.push_back( Imath::Box2i( support.min + supportOffset, support.max + supportOffset ) );
			}

			// Collect all the sampled input pixel which contribute to this output pixel
			int i = 0;
			for( int iy = support.min.y + supportOffset.y; iy < support.max.y + supportOffset.y; ++iy )
			{
				for( int ix = support.min.x + supportOffset.x; ix < support.max.x + supportOffset.x; ++ix )
				{
					if( weights[i] == 0.0f )
					{
						contributingPixels[i] = &emptyPixel;
					}
					else
					{
						contributingPixels[i] = &sampledPixels[ ( iy - inputOrigin.y ) * horizontalMixing.size() + ix - inputOrigin.x ];
					}

					i++;
				}
			}

			// Now that we have a set of weights and input pixels that have been sampled at every depth where
			// we may need to evaluate them, linearCombineSampledPixel can do all the actual work of combining
			// them into one output.
			// Call the variant that returns contribution weights if we need to use them to process other
			// channels, or use a variant which saves memory if we only need the A/Z/ZBack channels.
			int numSamples = 0;
			if( hasArbitraryChannel )
			{
				numSamples = linearCombineSampledPixels(
					contributingPixels, weights,
					outputAlpha, outputZ, outputZBack,
					&result->contributionCounts, &result->contributionElements
				);
			}
			else
			{
				numSamples = linearCombineSampledPixels(
					contributingPixels, weights,
					outputAlpha, outputZ, outputZBack,
					nullptr, nullptr
				);
			}
			currentOutputSampleOffset += numSamples;
			outputSampleOffsets.push_back( currentOutputSampleOffset );
		}
	}

	static_cast<ObjectPlug *>( output )->setValue( result );
}

void Resample::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashDataWindow( parent, context, h );

	inPlug()->dataWindowPlug()->hash( h );
	inPlug()->deepPlug()->hash( h );
	matrixPlug()->hash( h );
	expandDataWindowPlug()->hash( h );
	filterPlug()->hash( h );
	filterScalePlug()->hash( h );
	filterDeepPlug()->hash( h );
	debugPlug()->hash( h );
}

Imath::Box2i Resample::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const Box2i srcDataWindow = inPlug()->dataWindowPlug()->getValue();
	if( BufferAlgo::empty( srcDataWindow ) )
	{
		return srcDataWindow;
	}

	// Figure out our data window as a Box2f with fractional
	// pixel values.

	const M33f matrix = matrixPlug()->getValue();
	Box2f dstDataWindow = transform( Box2f( srcDataWindow.min, srcDataWindow.max ), matrix );

	if( expandDataWindowPlug()->getValue() )
	{
		V2f ratio, offset;
		ratioAndOffset( matrix, ratio, offset );

		V2f inputFilterScale( 0 );
		const OIIO::Filter2D *filter = nullptr;

		if( filterDeepPlug()->getValue() || !inPlug()->deepPlug()->getValue() )
		{
			filter = filterAndScale( filterPlug()->getValue(), ratio, inputFilterScale );
			inputFilterScale *= filterScalePlug()->getValue();
		}

		const V2f filterRadius = filter ? V2f( filter->width(), filter->height() ) * inputFilterScale * 0.5f : V2f( 0.0f );

		dstDataWindow.min -= filterRadius * ratio;
		dstDataWindow.max += filterRadius * ratio;
	}

	// Convert that Box2f to a Box2i that fully encloses it.
	// Cheat a little to avoid adding additional pixels when
	// we're really close to the edge. This is primarily to
	// meet user expectations in the Resize node, where it is
	// expected that the dataWindow will exactly match the format.

	const float eps = 1e-4;
	if( ceilf( dstDataWindow.min.x ) - dstDataWindow.min.x < eps )
	{
		dstDataWindow.min.x = ceilf( dstDataWindow.min.x );
	}
	if( dstDataWindow.max.x - floorf( dstDataWindow.max.x ) < eps )
	{
		dstDataWindow.max.x = floorf( dstDataWindow.max.x );
	}
	if( ceilf( dstDataWindow.min.y ) - dstDataWindow.min.y < eps )
	{
		dstDataWindow.min.y = ceilf( dstDataWindow.min.y );
	}
	if( dstDataWindow.max.y - floorf( dstDataWindow.max.y ) < eps )
	{
		dstDataWindow.max.y = floorf( dstDataWindow.max.y );
	}

	Box2i dataWindow = box2fToBox2i( dstDataWindow );

	// If we're outputting the horizontal pass, then replace
	// the vertical range with the original.

	if( parent == horizontalPassPlug() || debugPlug()->getValue() == HorizontalPass )
	{
		dataWindow.min.y = srcDataWindow.min.y;
		dataWindow.max.y = srcDataWindow.max.y;
	}

	return dataWindow;
}

void Resample::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelData( parent, context, h );

	V2f ratio, offset;

	V2f inputFilterScale( 0 );
	const OIIO::Filter2D *filter = nullptr;
	bool deep;

	Sampler::BoundingMode boundingMode;
	{
		ImagePlug::GlobalScope c( context );
		ratioAndOffset( matrixPlug()->getValue(), ratio, offset );

		deep = inPlug()->deepPlug()->getValue();
		if( !deep || filterDeepPlug()->getValue() )
		{
			const std::string filterName = filterPlug()->getValue();
			filter = filterAndScale( filterName, ratio, inputFilterScale );
			inputFilterScale *= filterScalePlug()->getValue();
		}

		boundingMode = (Sampler::BoundingMode)boundingModePlug()->getValue();
	}

	filterPlug()->hash( h );

	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	Passes passes = requiredPasses( this, parent, filter, ratio );
	Box2i ir = inputRegion( tileOrigin, deep ? Both : passes, ratio, offset, filter, inputFilterScale );

	if( deep )
	{
		Context::EditableScope withoutChannelScope( Context::current() );
		withoutChannelScope.remove( ImagePlug::channelNameContextName );

		if( filter )
		{
			deepResampleDataPlug()->hash( h );
		}
		else
		{
			h.append( inputFilterScale );
			h.append( ratio );
			h.append( offset );
			outPlug()->sampleOffsetsPlug()->hash( h );
		}

		if( filter && ( channelName == ImageAlgo::channelNameZ || channelName == ImageAlgo::channelNameZBack || channelName == ImageAlgo::channelNameA ) )
		{
			h.append( channelName );
		}
		else
		{
			DeepPixelAccessor( inPlug(), channelName, ir, boundingMode ).hash( h );
		}

		return;
	}

	if( passes & Horizontal )
	{
		h.append( inputFilterScale.x );
		h.append( ratio.x );
		h.append( offset.x );
	}
	if( passes & Vertical )
	{
		h.append( inputFilterScale.y );
		h.append( ratio.y );
		h.append( offset.y );
	}

	if( passes == BothOptimized )
	{
		// Append an extra flag so our hash reflects that we are going to take the optimized path
		h.append( true );
	}

	Sampler sampler(
		passes == Vertical ? horizontalPassPlug() : inPlug(),
		channelName,
		ir,
		boundingMode
	);
	sampler.hash( h );

	// Another tile might happen to need to filter over the same input
	// tiles as this one, so we must include the tile origin to make sure
	// each tile has a unique hash.
	h.append( tileOrigin );
}

IECore::ConstFloatVectorDataPtr Resample::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	V2f ratio, offset;
	V2f inputFilterScale( 0 );
	const OIIO::Filter2D *filter = nullptr;
	bool deep;
	Sampler::BoundingMode boundingMode;
	{
		ImagePlug::GlobalScope c( context );
		ratioAndOffset( matrixPlug()->getValue(), ratio, offset );

		deep = inPlug()->deepPlug()->getValue();
		if( !deep || filterDeepPlug()->getValue() )
		{
			const std::string filterName = filterPlug()->getValue();
			filter = filterAndScale( filterName, ratio, inputFilterScale );
			inputFilterScale *= filterScalePlug()->getValue();
		}

		boundingMode = (Sampler::BoundingMode)boundingModePlug()->getValue();
	}

	Passes passes = requiredPasses( this, parent, filter, ratio );
	Box2i ir = inputRegion( tileOrigin, deep ? Both : passes, ratio, offset, filter, inputFilterScale );

	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

	if( deep )
	{
		Context::EditableScope withoutChannelScope( Context::current() );
		withoutChannelScope.remove( ImagePlug::channelNameContextName );

		if( !filter )
		{
			// We only use the output sample offsets so that we know ahead of time how many points
			// we're going to generate. Bit of a shame to add this complexity, but it does seem
			// like a worthwhile win to not need to reallocate the output buffer.
			ConstIntVectorDataPtr outputSampleOffsetsData = outPlug()->sampleOffsetsPlug()->getValue();

			FloatVectorDataPtr resultData = new FloatVectorData();
			std::vector<float> &result = resultData->writable();
			result.resize( outputSampleOffsetsData->readable().back() );

			DeepPixelAccessor sampleOffsetsSampler( tidyInPlug(), channelName, ir, boundingMode );

			std::vector<int> iPx;
			nearestInputPixelX( tileBound.min.x, ratio.x, offset.x, iPx );

			V2i oP; // output pixel position
			int iPy; // input pixel position Y

			int outputSamplePosition = 0;

			for( oP.y = tileBound.min.y; oP.y < tileBound.max.y; ++oP.y )
			{
				iPy = floorf( ( oP.y + 0.5f ) / ratio.y + offset.y );
				std::vector<int>::const_iterator iPxIt = iPx.begin();

				Canceller::check( context->canceller() );
				for( oP.x = tileBound.min.x; oP.x < tileBound.max.x; ++oP.x )
				{
					boost::span<const float> channelSamples = sampleOffsetsSampler.sample( *iPxIt, iPy );
					memcpy( &result[outputSamplePosition], &channelSamples[0], channelSamples.size() * sizeof( float ) );
					outputSamplePosition += channelSamples.size();
					++iPxIt;
				}
			}

			return resultData;

		}


		ConstDeepResampleDataPtr deepResampleData = boost::static_pointer_cast<const DeepResampleData>(
			deepResampleDataPlug()->getValue()
		);

		if( channelName == ImageAlgo::channelNameZ )
		{
			return deepResampleData->ZData;
		}
		else if( channelName == ImageAlgo::channelNameZBack )
		{
			return deepResampleData->ZBackData;
		}
		else if( channelName == ImageAlgo::channelNameA )
		{
			return deepResampleData->AData;
		}

		const std::vector<int> &outputSampleOffsets = deepResampleData->sampleOffsetsData->readable();
		const std::vector<int> &contributionCounts = deepResampleData->contributionCounts;
		const std::vector<ContributionElement> &contributionElements = deepResampleData->contributionElements;

		DeepPixelAccessor deepChannelSampler( tidyInPlug(), channelName, ir, boundingMode );

		std::vector<const float *> channelSamples;

		FloatVectorDataPtr resultData = new FloatVectorData;
		std::vector<float> &result = resultData->writable();
		result.reserve( outputSampleOffsets.back() );

		int contributionIndex = 0;
		int prevOffset = 0;
		for( int i = 0; i < ImagePlug::tilePixels(); i++ )
		{
			int offset = outputSampleOffsets[i];

			const Box2i &support = deepResampleData->contributionSupports[i];

			channelSamples.reserve( support.size().x * support.size().y );
			channelSamples.resize( 0 );
			for( int iy = support.min.y; iy < support.max.y; ++iy )
			{
				for( int ix = support.min.x; ix < support.max.x; ++ix )
				{
					channelSamples.push_back( &deepChannelSampler.sample( ix, iy )[0] );
				}
			}

			for( int i = prevOffset; i < offset; i++ )
			{
				float combinedChannelValue = 0;
				for( int j = 0; j < contributionCounts[i]; j++ )
				{
					float contributionChannelValue = channelSamples[contributionElements[contributionIndex].sourceIndex]
						[ contributionElements[contributionIndex].sampleIndex ];
					combinedChannelValue += contributionElements[contributionIndex].weight * contributionChannelValue;
					contributionIndex++;
				}
				result.push_back( combinedChannelValue );
			}

			prevOffset = offset;
		}

		return resultData;
	}

	Sampler sampler(
		passes == Vertical ? horizontalPassPlug() : inPlug(),
		channelName,
		ir,
		boundingMode
	);

	const V2f filterRadius = inputFilterRadius( filter, inputFilterScale );

	FloatVectorDataPtr resultData = new FloatVectorData;
	std::vector<float> &result = resultData->writable();
	result.resize( ImagePlug::tileSize() * ImagePlug::tileSize() );
	std::vector<float>::iterator pIt = result.begin();

	if( !filter )
	{
		std::vector<int> iPx;
		nearestInputPixelX( tileBound.min.x, ratio.x, offset.x, iPx );

		V2i oP; // output pixel position
		int iPy; // input pixel position Y

		for( oP.y = tileBound.min.y; oP.y < tileBound.max.y; ++oP.y )
		{
			iPy = floorf( ( oP.y + 0.5f ) / ratio.y + offset.y );
			std::vector<int>::const_iterator iPxIt = iPx.begin();

			Canceller::check( context->canceller() );
			for( oP.x = tileBound.min.x; oP.x < tileBound.max.x; ++oP.x )
			{
				*pIt = sampler.sample( *iPxIt, iPy );
				++iPxIt;
				++pIt;
			}
		}
	}
	else if( passes == Both )
	{
		// When the filter isn't separable we must perform all the
		// filtering in a single pass. This version also provides
		// a reference implementation against which the two-pass
		// version can be validated - use the SinglePass debug mode
		// to force the use of this code path.

		V2i oP; // output pixel position
		V2f iP; // input pixel position (floating point)

		V2f	filterCoordinateMult = V2f(1.0f) / inputFilterScale;

		for( oP.y = tileBound.min.y; oP.y < tileBound.max.y; ++oP.y )
		{
			iP.y = ( oP.y + 0.5f ) / ratio.y + offset.y;
			int minY = ceilf( iP.y - 0.5f - filterRadius.y );
			int maxY = floorf( iP.y + 0.5f + filterRadius.y );

			for( oP.x = tileBound.min.x; oP.x < tileBound.max.x; ++oP.x )
			{
				Canceller::check( context->canceller() );

				iP.x = ( oP.x + 0.5f ) / ratio.x + offset.x;

				int minX = ceilf( iP.x - 0.5f - filterRadius.x );
				int maxX = floorf( iP.x + 0.5f + filterRadius.x );

				float v = 0.0f;
				float totalW = 0.0f;
				sampler.visitPixels(
					Imath::Box2i( Imath::V2i( minX, minY ), Imath::V2i( maxX, maxY ) ),
					[&filter, &filterCoordinateMult, &iP, &v, &totalW]( float cur, int x, int y )
					{
						const float w = (*filter)(
							filterCoordinateMult.x * ( float(x) + 0.5f - iP.x ),
							filterCoordinateMult.y * ( float(y) + 0.5f - iP.y )
						);

						v += w * cur;
						totalW += w;
					}
				);

				if( totalW != 0.0f )
				{
					*pIt = v / totalW;
				}

				++pIt;
			}
		}
	}
	else if( passes == BothOptimized )
	{
		Box2i support;
		std::vector<float> weights;
		filterWeights2D( filter, inputFilterScale, filterRadius, tileBound.min, V2f( 1 ), offset, support, weights );

		V2i oP; // output pixel position
		V2i supportOffset;
		for( oP.y = tileBound.min.y; oP.y < tileBound.max.y; ++oP.y )
		{
			supportOffset.y = oP.y - tileBound.min.y;

			for( oP.x = tileBound.min.x; oP.x < tileBound.max.x; ++oP.x )
			{
				Canceller::check( context->canceller() );

				supportOffset.x = oP.x - tileBound.min.x;
				std::vector<float>::const_iterator wIt = weights.begin();

				float v = 0.0f;
				float totalW = 0.0f;
				sampler.visitPixels(
					Imath::Box2i( support.min + supportOffset, support.max + supportOffset ),
					[&wIt, &v, &totalW]( float cur, int x, int y )
					{
						const float w = *wIt++;
						v += w * cur;
						totalW += w;
					}
				);

				if( totalW != 0.0f )
				{
					*pIt = v / totalW;
				}

				++pIt;
			}
		}

	}
	else if( passes == Horizontal )
	{
		// When the filter is separable we can perform filtering in two
		// passes, one for the horizontal and one for the vertical. We
		// output the horizontal pass on the horizontalPassPlug() so that
		// it is cached for use in the vertical pass. The HorizontalPass
		// debug mode causes this pass to be output directly for inspection.

		// Pixels in the same column share the same support ranges and filter weights, so
		// we precompute the weights now to avoid repeating work later.
		std::vector<int> supportRanges;
		std::vector<float> weights;
		filterWeights1D( filter, inputFilterScale.x, filterRadius.x, tileBound.min.x, ratio.x, offset.x, Horizontal, supportRanges, weights );

		V2i oP; // output pixel position

		for( oP.y = tileBound.min.y; oP.y < tileBound.max.y; ++oP.y )
		{
			Canceller::check( context->canceller() );

			std::vector<int>::const_iterator supportIt = supportRanges.begin();
			std::vector<float>::const_iterator wIt = weights.begin();
			for( oP.x = tileBound.min.x; oP.x < tileBound.max.x; ++oP.x )
			{
				float v = 0.0f;
				float totalW = 0.0f;

				sampler.visitPixels( Imath::Box2i(
						Imath::V2i( *supportIt, oP.y ),
						Imath::V2i( *( supportIt + 1 ), oP.y + 1 )
					),
					[&wIt, &v, &totalW]( float cur, int x, int y )
					{
						const float w = *wIt++;
						v += w * cur;
						totalW += w;
					}
				);

				supportIt += 2;

				if( totalW != 0.0f )
				{
					*pIt = v / totalW;
				}

				++pIt;
			}
		}
	}
	else if( passes == Vertical )
	{
		V2i oP; // output pixel position

		// Pixels in the same row share the same support ranges and filter weights, so
		// we precompute the weights now to avoid repeating work later.
		std::vector<int> supportRanges;
		std::vector<float> weights;
		filterWeights1D( filter, inputFilterScale.y, filterRadius.y, tileBound.min.y, ratio.y, offset.y, Vertical, supportRanges, weights );

		std::vector<int>::const_iterator supportIt = supportRanges.begin();
		std::vector<float>::const_iterator rowWeightsIt = weights.begin();

		for( oP.y = tileBound.min.y; oP.y < tileBound.max.y; ++oP.y )
		{
			Canceller::check( context->canceller() );

			for( oP.x = tileBound.min.x; oP.x < tileBound.max.x; ++oP.x )
			{
				float v = 0.0f;
				float totalW = 0.0f;

				std::vector<float>::const_iterator wIt = rowWeightsIt;

				sampler.visitPixels( Imath::Box2i(
						Imath::V2i( oP.x, *supportIt ),
						Imath::V2i( oP.x + 1, *(supportIt + 1) )
					),
					[&wIt, &v, &totalW]( float cur, int x, int y )
					{
						const float w = *wIt++;
						v += w * cur;
						totalW += w;
					}
				);


				if( totalW != 0.0f )
				{
					*pIt = v / totalW;
				}

				++pIt;
			}

			rowWeightsIt += (*(supportIt + 1)) - (*supportIt);
			supportIt += 2;
		}
	}

	return resultData;
}

void Resample::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( !inPlug()->deep() )
	{
		h = ImagePlug::flatTileSampleOffsets()->Object::hash();
	}

	ImageProcessor::hashSampleOffsets( parent, context, h );

	V2f ratio, offset;

	const OIIO::Filter2D *filter = nullptr;

	Sampler::BoundingMode boundingMode;
	{
		ImagePlug::GlobalScope c( context );
		ratioAndOffset( matrixPlug()->getValue(), ratio, offset );

		if( filterDeepPlug()->getValue() || !inPlug()->deepPlug()->getValue() )
		{
			const std::string filterName = filterPlug()->getValue();
			V2f inputFilterScaleUnused;
			filter = filterAndScale( filterName, ratio, inputFilterScaleUnused );
		}

		boundingMode = (Sampler::BoundingMode)boundingModePlug()->getValue();
	}


	if( filter )
	{
		deepResampleDataPlug()->hash( h );
		return;
	}

	h.append( ratio );
	h.append( offset );
	h.append( boundingMode );

	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	Box2i ir = inputRegion( tileOrigin, Both, ratio, offset, nullptr, V2f( 0.0f ) );
	DeepPixelAccessor( tidyInPlug(), "", ir, boundingMode ).hash( h );
}

IECore::ConstIntVectorDataPtr Resample::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	if( !inPlug()->deep() )
	{
		return ImagePlug::flatTileSampleOffsets();
	}

	V2f ratio, offset;
	const OIIO::Filter2D *filter = nullptr;
	Sampler::BoundingMode boundingMode;
	{
		ImagePlug::GlobalScope c( context );
		ratioAndOffset( matrixPlug()->getValue(), ratio, offset );

		if( filterDeepPlug()->getValue() || !inPlug()->deepPlug()->getValue() )
		{
			const std::string filterName = filterPlug()->getValue();
			V2f inputFilterScaleUnused;
			filter = filterAndScale( filterName, ratio, inputFilterScaleUnused );
		}

		boundingMode = (Sampler::BoundingMode)boundingModePlug()->getValue();
	}

	if( filter )
	{
		ConstDeepResampleDataPtr deepResampleData = boost::static_pointer_cast<const DeepResampleData>(
			deepResampleDataPlug()->getValue()
		);
		return deepResampleData->sampleOffsetsData;
	}

	Box2i ir = inputRegion( tileOrigin, Both, ratio, offset, nullptr, V2f( 0.0f ) );
	DeepPixelAccessor sampleOffsetsSampler( tidyInPlug(), "", ir, boundingMode );

	IntVectorDataPtr outputSampleOffsetsData = new IntVectorData();
	std::vector<int> &outputSampleOffsets = outputSampleOffsetsData->writable();
	outputSampleOffsets.reserve( ImagePlug::tilePixels() );

	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

	std::vector<int> iPx;
	nearestInputPixelX( tileBound.min.x, ratio.x, offset.x, iPx );

	V2i oP; // output pixel position
	int iPy; // input pixel position Y

	int sampleOffset = 0;
	for( oP.y = tileBound.min.y; oP.y < tileBound.max.y; ++oP.y )
	{
		iPy = floorf( ( oP.y + 0.5f ) / ratio.y + offset.y );
		std::vector<int>::const_iterator iPxIt = iPx.begin();

		Canceller::check( context->canceller() );
		for( oP.x = tileBound.min.x; oP.x < tileBound.max.x; ++oP.x )
		{
			sampleOffset += sampleOffsetsSampler.sampleCount( *iPxIt, iPy );
			++iPxIt;
			outputSampleOffsets.push_back( sampleOffset );
		}
	}

	return outputSampleOffsetsData;
}
