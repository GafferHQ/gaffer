//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2015, Nvizible Ltd. All rights reserved.
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

#include "Gaffer/Context.h"

#include "GafferImage/ImageAlgo.h"
#include "GafferImage/DeepState.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( DeepState );

namespace
{

const IECore::InternedString g_AName = "A";
const IECore::InternedString g_ZName = "Z";
const IECore::InternedString g_ZBackName = "ZBack";
const IECore::InternedString g_sampleOffsetsName = "sampleOffsets";
const IECore::InternedString g_contributionIdsName = "contributionIds";
const IECore::InternedString g_contributionWeightsName = "contributionWeights";
const IECore::InternedString g_contributionOffsetsName = "contributionOffsets";

// This class stores all information about how samples are merged together.
// It is initialized just based on the sorted Z and ZBack channels ( and the sampleOffsets that
// map them ).  The outputs are stored in members, and include:
// * the Z and ZBack channels of merged samples
// *  the sample offsets of the merged samples ( the samples per pixel may be reduced when
//    identical samples are merged, or increased when overlapping samples are split to remove overlap )
// * contributionIds, contributionAmounts, contributionOffsets : describe the contributions from input samples
//   to output samples.  For each output sample, there is an entry in contributionOffsets, which indicates
//   which contributions to take.  For each contribution, there is in an entry in contributionIds and
//   contributionAmounts, which indicate which input sample to take, and what fraction of it to take
//
// Note that the contributionAmounts are stored as a fraction of the thickness of the input sample.
// Converting this into an alpha value is done in alphaToLinearWeights
class SampleMerge
{
	public :
		SampleMerge( const vector<int> &inSampleOffsets, const vector<float> *inZ, const vector<float> *inZBack )
			:	zData( new FloatVectorData() ),
				zBackData( new FloatVectorData() ),
				sampleOffsetsData( new IntVectorData() ),
				contributionIdsData( new IntVectorData() ),
				contributionAmountsData( new FloatVectorData() ),
				contributionOffsetsData( new IntVectorData() ),
				m_inZ( inZ ? *inZ : zData->writable() ),  // Unused when there is no inZ
				m_inZBack( inZBack ? *inZBack : zBackData->writable() ),  // Unused when there is no inZ
				m_zOut( zData->writable() ),
				m_zBackOut( zBackData->writable() ),
				m_contributionIdsOut( contributionIdsData->writable() ),
				m_contributionAmountsOut( contributionAmountsData->writable() ),
				m_contributionOffsetsOut( contributionOffsetsData->writable() )
		{
			vector<int> &sampleOffsetsOut = sampleOffsetsData->writable();
			sampleOffsetsOut.reserve( ImagePlug::tilePixels() );

			if( !inZ )
			{
				// If we don't have a Z channel, then no samples can "overlap", so we shouldn't really need
				// to perform merging.  But we could still to run a "tidy" in order to do the pruning of
				// transparent or occluded samples.  In order to set up for that, we set up all the merging
				// data structures with an identity transform that just passes through all the input data.
				std::copy(inSampleOffsets.begin(), inSampleOffsets.end(), std::back_inserter( sampleOffsetsOut ) );
				m_contributionIdsOut.resize( inSampleOffsets.back() );
				m_contributionAmountsOut.resize( inSampleOffsets.back(), 1.0f );
				m_contributionOffsetsOut.resize( inSampleOffsets.back() );

				for( int i = 0; i < inSampleOffsets.back(); i++ )
				{
					m_contributionIdsOut[i] = i;
					m_contributionOffsetsOut[i] = i + 1;
				}
				return;
			}

			// We don't know how many merged samples we will end up with, but in image with many
			// hard surfaces, it's often just slightly higher than the number of input samples
			m_zOut.reserve( m_inZ.size() * 1.1f );
			m_zBackOut.reserve( m_inZ.size() * 1.1f );
			m_contributionOffsetsOut.reserve( m_inZ.size() * 1.1f );

			// The number of contributions could get a lot higher, but for the moment use a low estimate
			m_contributionIdsOut.reserve( m_inZ.size() * 1.1f );
			m_contributionAmountsOut.reserve( m_inZ.size() * 1.1f );

			int currentSampleId = 0;
			for( int i = 0; i < ImagePlug::tilePixels(); i++ )
			{
				float outputDepth = numeric_limits<float>::lowest();
				int offset = inSampleOffsets[i];

				while( currentSampleId < offset )
				{
					// If we exactly match an existing open sample, we don't need to close anything
					// ( This check avoids closing an open point sample when receiving another
					// point sample at the same depth )
					if( m_openSamples.size() && ! ( m_inZ[ m_openSamples.back() ] == m_inZ[currentSampleId] && m_inZBack[ m_openSamples.back() ] == m_inZBack[currentSampleId] ) )
					{
						closeOpenSamples( outputDepth, m_inZ[currentSampleId] );
						outputDepth = m_inZ[currentSampleId];
					}

					if( m_openSamples.size() == 0 && ( currentSampleId + 1 == offset ||
						( m_inZBack[currentSampleId] <= m_inZ[currentSampleId+1] &&
							m_inZ[currentSampleId] < m_inZBack[currentSampleId+1] )
					) )
					{
						// There are no open samples, and this sample does not interact with the next sample.
						// We can take a fast path, knowing that we can directly output this sample without
						// putting it in the open samples list.
						// This does the same thing that that putting it in the open sample list and then
						// closing it immediately would do, but is an optimization that saves ~15% of
						// sampleMapping compute time when tidying data that is almost all already tidy
						m_zOut.push_back( m_inZ[currentSampleId] );
						m_zBackOut.push_back( m_inZBack[currentSampleId] );
						m_contributionIdsOut.push_back( currentSampleId );
						m_contributionAmountsOut.push_back( 1.0 );
						m_contributionOffsetsOut.push_back( m_contributionIdsOut.size() );
					}
					else
					{
						// This sample interacts with the previous or next sample, so we need to add it
						// to the open sample list, so it can be merged appropriately
						unsigned int insertionIndex = m_openSamples.size();
						while( insertionIndex > 0 && m_inZBack[ m_openSamples[insertionIndex - 1] ] < m_inZBack[currentSampleId] )
						{
							insertionIndex--;
						}
						m_openSamples.insert( m_openSamples.begin() + insertionIndex, currentSampleId );
					}

					currentSampleId++;
				}
				closeOpenSamples( outputDepth, numeric_limits<float>::max() );
				sampleOffsetsOut.push_back( m_contributionOffsetsOut.size() );
			}
		}

		FloatVectorDataPtr zData;
		FloatVectorDataPtr zBackData;
		IntVectorDataPtr sampleOffsetsData;

		// Which sorted samples are contributing to which tidy samples, and by how much.
		// mergedSampleContributionIds : The indices of the original samples that will
		//    be used in each new sample
		// mergedSampleContributionAmounts : The proportion of each of the original samples
		//    that will be used in the new samples
		// mergedSampleContributionOffsets : The offsets in the mergedSampleContribution
		//    vectors for each of the new samples
		IntVectorDataPtr contributionIdsData;
		FloatVectorDataPtr contributionAmountsData;
		IntVectorDataPtr contributionOffsetsData;


	private :

		void closeOpenSamples( float currentDepth, const float closeUpToZ )
		{
			while( m_openSamples.size() && m_inZBack[ m_openSamples.back() ] <= closeUpToZ )
			{
				const float closeBack = m_inZBack[ m_openSamples.back() ];
				currentDepth = std::max( currentDepth, m_inZ[ m_openSamples.back() ] );

				outputSample( currentDepth, closeBack );

				while( m_openSamples.size() && m_inZBack[ m_openSamples.back() ] == closeBack )
				{
					m_openSamples.pop_back();
				}

				currentDepth = closeBack;
			}

			if( m_openSamples.size() )
			{
				currentDepth = std::max( currentDepth, m_inZ[ m_openSamples.back() ] );
				if( currentDepth != closeUpToZ )
				{
					outputSample( currentDepth, closeUpToZ );
				}
			}
		}

		void outputSample( float z, float zBack )
		{
			m_zOut.push_back( z );
			m_zBackOut.push_back( zBack );
			if( z == zBack )
			{
				// Outputting a point sample, it will only contain contributions from matching point samples
				for( int i = m_openSamples.size() - 1; i >= 0; i-- )
				{
					if( m_inZBack[ m_openSamples[i] ] != zBack )
					{
						break;
					}
					m_contributionIdsOut.push_back( m_openSamples[i] );
					m_contributionAmountsOut.push_back( 1.0 );
				}
			}
			else
			{
				for( const auto &i : m_openSamples )
				{
					const float amount = ( zBack - z ) / ( m_inZBack[i] - m_inZ[i] );
					m_contributionIdsOut.push_back( i );
					m_contributionAmountsOut.push_back( amount );
				}
			}
			m_contributionOffsetsOut.push_back( m_contributionIdsOut.size() );
		}

		const vector<float> &m_inZ;
		const vector<float> &m_inZBack;
		std::vector<int> m_openSamples;
		vector<float> &m_zOut;
		vector<float> &m_zBackOut;
		vector<int> &m_contributionIdsOut;
		vector<float> &m_contributionAmountsOut;
		vector<int> &m_contributionOffsetsOut;

};

// Given alpha values interpreted as exponential fog, and contribution weights for the fraction
// of this exponential fog taken by each sample contribution, replace the contribution weights
// with a simple linear weight that can be used to sum together the channel contributions.
// If flatten is passed, the contributions are set up per pixel, otherwise they are set up
// per sample.  The return value is the final alpha, per sample, or per pixel ( depending on
// flatten ).
FloatVectorDataPtr alphaToLinearWeights(
		std::vector<float> &contributionWeightsBuffer,  // Modified in place
		const std::vector<int> &contributionIds,
		const std::vector<int> &contributionOffsets,
		const std::vector<float> &alpha,
		const std::vector<int> &sampleOffsets,
		bool flatten
)
{
	static const float MAX = numeric_limits<float>::max();

	FloatVectorDataPtr mergedAlphaData = new FloatVectorData;
	vector<float> &mergedAlpha = mergedAlphaData->writable();

	if( flatten )
	{
		mergedAlpha.resize( ImagePlug::tilePixels(), 0.0f );
	}
	else
	{
		mergedAlpha.resize( contributionOffsets.size() );
	}

	float pixelAlpha = 0;
	float pixelAlphaMultiplier = 1;

	unsigned int pixel = 0;
	unsigned int pixelEnd = sampleOffsets[0];

	// Fast forward past any initial empty pixels
	while( pixelEnd == 0 && pixel + 1 < sampleOffsets.size() )
	{
		pixel++;
		pixelEnd = sampleOffsets[pixel];
	}

	unsigned int contributionStart = 0;
	for( unsigned int sample = 0; sample < contributionOffsets.size(); sample++ )
	{
		unsigned int contributionEnd = contributionOffsets[ sample ];

		assert( contributionEnd != contributionStart ); // There can't be a sample with no contributions

		float sampleAccumAlpha = 0.0;

		if( contributionEnd == contributionStart + 1 )
		{
			// Exactly one contribution to the sample.  Don't need to worry about merging
			const float contributionAlpha = alpha[contributionIds[contributionStart]];

			float weight;
			if( contributionAlpha >= 1.0f )
			{
				weight = 1.0f;
				sampleAccumAlpha = 1.0f;
			}
			else
			{
				const float sampleAmount = contributionWeightsBuffer[contributionStart];

				// See "Interpreting OpenEXR Deep Pixels" for reference on the math
				// far splitting and merging samples
				// https://www.openexr.com/documentation/InterpretingDeepPixels.pdf

				if( contributionAlpha <= 0.0f )
				{
					sampleAccumAlpha = 0.0f;
					weight = sampleAmount;
				}
				else if( sampleAmount == 1.0f )
				{
					sampleAccumAlpha = contributionAlpha;
					weight = sampleAmount;
				}
				else
				{
					sampleAccumAlpha = -expm1( sampleAmount * log1p( -contributionAlpha ) );
					weight = sampleAccumAlpha / contributionAlpha;
				}
			}

			contributionWeightsBuffer[contributionStart] = weight * pixelAlphaMultiplier;
		}
		else
		{
			int opaqueSamples = 0;
			float accumU = 0;

			for( unsigned int contrib = contributionStart; contrib < contributionEnd; contrib++ )
			{
				const float contributionAlpha = alpha[contributionIds[contrib]];

				if( contributionAlpha >= 1.0f )
				{
					if( opaqueSamples == 0 )
					{
						// When we find our first opaque sample, no previous samples matter, since an opaque
						// sample always overpowers everything it is merged with
						for( unsigned int skippedContrib = contributionStart; skippedContrib < contrib; skippedContrib++ )
						{
							contributionWeightsBuffer[skippedContrib] = 0.0f;
						}
					}
					contributionWeightsBuffer[contrib] = 1.0f;
					opaqueSamples++;
					continue;
				}
				else if( opaqueSamples )
				{
					// If there is an opaque sample, and we aren't opaque, then we have no impact
					contributionWeightsBuffer[contrib] = 0.0f;
					continue;
				}

				const float sampleAmount = contributionWeightsBuffer[contrib];

				// See "Interpreting OpenEXR Deep Pixels" for reference on the math
				// far splitting and merging samples
				// https://www.openexr.com/documentation/InterpretingDeepPixels.pdf

				float splitAlpha;
				float splitValueWeight;
				float splitU;

				if( contributionAlpha <= 0.0f )
				{
					splitU = 0.0f;
					splitAlpha = 0.0f;
					splitValueWeight = sampleAmount;
				}
				else if( sampleAmount == 1.0f )
				{
					splitAlpha = contributionAlpha;
					splitU = -log1p( -splitAlpha );
					splitValueWeight = 1.0;
				}
				else
				{
					splitU = -sampleAmount * log1p( -contributionAlpha );
					splitAlpha = -expm1( -splitU );
					splitValueWeight = splitAlpha / contributionAlpha;
				}

				sampleAccumAlpha = sampleAccumAlpha + splitAlpha - ( sampleAccumAlpha * splitAlpha );

				float splitV = ( splitU < splitAlpha * MAX ) ? splitU / splitAlpha : 1.0f;

				accumU += splitU;

				contributionWeightsBuffer[contrib] = splitV * splitValueWeight;
			}

			float sampleWeightMultiplier;
			if( opaqueSamples )
			{
				// When we're dealing with an opaque sample, we just average all the opaque contributions
				sampleWeightMultiplier = 1.0f / float(opaqueSamples);
				sampleAccumAlpha = 1.0f;
			}
			else
			{
				sampleWeightMultiplier = ( accumU > 1 || sampleAccumAlpha < accumU * MAX ) ? sampleAccumAlpha / accumU : 1.0f;
			}

			// When flattening, we include a multiplier to account for occlusion by previous samples
			sampleWeightMultiplier *= pixelAlphaMultiplier;

			for( unsigned int j = contributionStart; j < contributionEnd; j++ )
			{
				contributionWeightsBuffer[j] *= sampleWeightMultiplier;
			}
		}

		contributionStart = contributionEnd;

		if( flatten )
		{
			// If we are flattening, then we need to compute the accumulated pixelAlpha, and we
			// only write out the mergedAlpha once per pixel
			pixelAlpha = pixelAlpha + sampleAccumAlpha - pixelAlpha * sampleAccumAlpha;
			pixelAlphaMultiplier = 1.0f - pixelAlpha;
			if( sample + 1 == pixelEnd )
			{
				assert( pixel < sampleOffsets.size() );
				mergedAlpha[ pixel ] = pixelAlpha;

				while( pixelEnd == sample + 1 && pixel + 1 < sampleOffsets.size() )
				{
					pixel++;
					pixelEnd = sampleOffsets[pixel];
				}

				pixelAlpha = 0.0f;
				pixelAlphaMultiplier = 1.0f;
			}
		}
		else
		{
			mergedAlpha[sample] = sampleAccumAlpha;
		}
	}
	return mergedAlphaData;
}

// This function removes samples that are transparent or occluded.  Removing samples requires updating
// all the contribution arrays, and the channel data and sample offsets.
//
// The one trick about this function is that when occludedThreshold is less than 1, samples which are
// past the occluded threshold, but not 100% hidden, are merged with the last sample, to preserve the
// flattened appearance of the image
void pruneSamples(
		std::vector<float> &contributionWeights,
		std::vector<int> &contributionIds,
		std::vector<int> &contributionOffsets,
		std::vector<float> &alpha,
		std::vector<float> *z,
		std::vector<float> *zBack,
		std::vector<int> &sampleOffsets,
		bool pruneTransparent, bool pruneOccluded, float occludedThreshold
)
{
	// If we considered an alpha value of 0 to be occluded, the initial alpha value would be
	// considered already occluded, which totally breaks things.  It's probably totally unreasonable to
	// use anything less than 0.9, but down to 0.00000001 will work.
	float clampedOccludedThreshold = std::max( 0.00000001f, std::min( 1.0f, occludedThreshold ) );
	int prevSampleOffset = 0;
	int prevContributionOffset = 0;
	int writeSampleIndex = 0;
	int writeContributionIndex = 0;
	for( int pixel = 0; pixel < ImagePlug::tilePixels(); pixel++ )
	{
		int sampleOffset = sampleOffsets[pixel];

		float pixelAlpha = 0.0f;
		float squashAlpha = 0.0f;
		for( int sample = prevSampleOffset; sample < sampleOffset; sample++ )
		{
			int contributionOffset = contributionOffsets[ sample ];
			float sampleAlpha = alpha[sample];
			if( ( pruneTransparent && sampleAlpha == 0.0f ) || ( pruneOccluded && pixelAlpha == 1.0f ) )
			{
				// If this sample is pruned because of transparency, or because it's 100% occluded,
				// it's a simple skip
				prevContributionOffset = contributionOffset;
				continue;
			}

			// Otherwise, this sample is either being output normally, or merged with the previous sample

			float contributionWeightMultiplier = 1.0f - squashAlpha;
			for( int contribution = prevContributionOffset; contribution < contributionOffset; contribution++ )
			{
				contributionIds[writeContributionIndex] = contributionIds[contribution];
				contributionWeights[writeContributionIndex] = contributionWeights[contribution] * contributionWeightMultiplier;
				writeContributionIndex++;
			}

			contributionOffsets[writeSampleIndex] = writeContributionIndex;

			if( !( pruneOccluded && pixelAlpha >= clampedOccludedThreshold ) )
			{
				// Output normally
				alpha[writeSampleIndex] = sampleAlpha;
				if( z )
				{
					(*z)[writeSampleIndex] = (*z)[sample];
					(*zBack)[writeSampleIndex] = (*zBack)[sample];
				}
			}
			pixelAlpha = pixelAlpha + sampleAlpha - pixelAlpha * sampleAlpha;

			if( !( pruneOccluded && pixelAlpha >= clampedOccludedThreshold ) )
			{
				// If we're still not over the threshold, we can move on to the
				// next write index
				writeSampleIndex++;
			}
			else
			{
				// We're now over the threshold.  All remaining samples for this pixel will be
				// squashed into this index
				squashAlpha = squashAlpha + sampleAlpha - squashAlpha * sampleAlpha;
				alpha[writeSampleIndex] = squashAlpha;
			}

			prevContributionOffset = contributionOffset;
		}

		if( pruneOccluded && pixelAlpha >= clampedOccludedThreshold )
		{
			// Inside a squashed sample
			writeSampleIndex++;
		}

		sampleOffsets[pixel] = writeSampleIndex;

		prevSampleOffset = sampleOffset;
	}

	// These vectors may have all been shrunk - resize to their correct size
	alpha.resize( writeSampleIndex );
	if( z )
	{
		z->resize( writeSampleIndex );
		zBack->resize( writeSampleIndex );
	}
	contributionOffsets.resize( writeSampleIndex );
	contributionIds.resize( writeContributionIndex );
	contributionWeights.resize( writeContributionIndex );
}

// In the general case, we come up with the linear sample weights by performing a SampleMerge,
// and then feeding the contribution amounts through alphaToLinearWeights.  When we are
// starting with tidy data, however, we can get to the same end point with a simple accumulate.
FloatVectorDataPtr tidyAlphaToFlatLinearWeights(
		std::vector<float> &outputWeights,
		const std::vector<float> &alpha,
		const std::vector<int> &sampleOffsets
)
{
	FloatVectorDataPtr mergedAlphaData = new FloatVectorData;
	vector<float> &mergedAlpha = mergedAlphaData->writable();
	mergedAlpha.resize( ImagePlug::tilePixels(), 0.0f );

	int prevOffset = 0;
	for( unsigned int pixel = 0; pixel < sampleOffsets.size(); pixel++ )
	{
		int offset = sampleOffsets[pixel];

		float pixelAlpha = 0.0f;
		for( int sample = prevOffset; sample < offset; sample++ )
		{
			float sampleAlpha = alpha[sample];
			outputWeights[sample] = 1.0 - pixelAlpha;
			pixelAlpha = pixelAlpha + sampleAlpha - pixelAlpha * sampleAlpha;
		}
		mergedAlpha[pixel] = pixelAlpha;

		prevOffset = offset;
	}
	return mergedAlphaData;
}

// Return a float vector data which for each element of indices, contains the element of input with that index.
IECore::ConstFloatVectorDataPtr sortByIndices( const std::vector<float> &input, const vector<int> &indices )
{
	FloatVectorDataPtr resultData = new FloatVectorData();
	std::vector<float> &result = resultData->writable();
	result.resize( input.size() );

	for( unsigned int i = 0; i < input.size(); i++ )
	{
		result[ i ] = input[ indices[ i ] ];
	}

	return resultData;
}

// Return a FloatVectorData which for each element of indices, contains the element of input with that index.
IECore::ConstFloatVectorDataPtr sumByIndicesAndWeights( const std::vector<float> &input,
	const vector<int> &indices,
	const vector<float> &weights,
	const vector<int> &offsets
)
{
	FloatVectorDataPtr resultData = new FloatVectorData;
	vector<float> &result = resultData->writable();
	result.resize( offsets.size() );

	int prevOffset = 0;
	for( unsigned int pixel = 0; pixel < offsets.size(); pixel++ )
	{
		int offset = offsets[pixel];

		float accumValue = 0;
		for( int sample = prevOffset; sample < offset; sample++ )
		{
			accumValue += input[ indices[ sample ] ] * weights[sample];
		}

		result[pixel] = accumValue;
		prevOffset = offset;
	}

	return resultData;
}

// For each range of samples indicated by offsets, multiply the corresponding input sample by the
// corresponding weight, and sum.  Returns a FloatVectorData with the sum for each range.
IECore::ConstFloatVectorDataPtr sumByWeights( const std::vector<float> &input,
	const vector<float> &weights,
	const vector<int> &offsets
)
{
	FloatVectorDataPtr resultData = new FloatVectorData;
	vector<float> &result = resultData->writable();
	result.resize( offsets.size() );

	int prevOffset = 0;
	for( unsigned int i = 0; i < offsets.size(); i++ )
	{
		int offset = offsets[i];

		float accumValue = 0;
		for( int j = prevOffset; j < offset; j++ )
		{
			accumValue += input[ j ] * weights[j];
		}

		result[i] = accumValue;
		prevOffset = offset;
	}

	return resultData;
}

// Given the Z and ZBack channels, and corresponding sampleOffsets, return an IntVectorData
// a list of sample indices that would produce sorted samples.
IECore::IntVectorDataPtr computeSampleSorting(
	const vector<int> &sampleOffsets, const vector<float> &z, const vector<float> &zBack
)
{
	// We compare based on the Z channel - if it is equal, compare based on ZBack
	struct CompareDepth
	{
		const vector<float> &m_zSamples;
		const vector<float> &m_zBackSamples;

		CompareDepth( const vector<float> &zSamples, const vector<float> &zBackSamples )
			: m_zSamples( zSamples ), m_zBackSamples( zBackSamples )
		{}

		bool operator()( int a, int b ) const
		{
			if( m_zSamples[a] != m_zSamples[b] )
			{
				return m_zSamples[a] < m_zSamples[b];
			}
			else if( m_zBackSamples[a] != m_zBackSamples[b] )
			{
				return m_zBackSamples[a] < m_zBackSamples[b];
			}
			else
			{
				// If everything is equal, preserve initial order
				return a < b;
			}
		}
	};

	IntVectorDataPtr resultData = new IntVectorData();
	std::vector<int> &result = resultData->writable();
	result.resize( sampleOffsets.back() );
	for( unsigned int i = 0; i < result.size(); i++ )
	{
		result[i] = i;
	}

	CompareDepth compare( z, zBack );

	int prevOffset = 0;
	for( int offset : sampleOffsets )
	{
		if( offset > prevOffset )
		{
			std::sort( &result[prevOffset], &result[offset], compare );
			prevOffset = offset;
		}
	}

	return resultData;
}

void checkState( const std::vector<int> &offsets,
	const std::vector<float> &zChannel, const std::vector<float> &zBackChannel,
	bool &isSorted, bool &isTidy )
{
	isSorted = true;
	isTidy = true;

	int prevOffset = 0;
	for( const int offset : offsets )
	{
		if( offset == prevOffset )
		{
			continue;
		}

		float z = zChannel[prevOffset];
		float zBack = zBackChannel[prevOffset];
		for( int i = prevOffset + 1; i < offset; i++ )
		{
			float newZ = zChannel[i];
			float newZBack = zBackChannel[i];
			if( newZ < zBack )
			{
				isTidy = false;
			}

			if( newZ <= z )
			{
				if( newZ < z )
				{
					isSorted = false;
					isTidy = false;
					return;
				}
				else
				{
					if( zBack <= z && newZBack > newZ )
					{
						// Volume sample after point sample starting at the same depth is still tidy
					}
					else
					{
						if( newZ == z && newZBack > zBack )
						{
							isTidy = false;
						}
						else
						{
							isSorted = false;
							isTidy = false;
							return;
						}
					}
				}
			}
			z = newZ;
			zBack = newZBack;
		}
		prevOffset = offset;
	}
}

};

size_t DeepState::g_firstPlugIndex = 0;

DeepState::DeepState( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "deepState", Gaffer::Plug::In, int( TargetState::Tidy ) ) );
	addChild( new BoolPlug( "pruneTransparent", Gaffer::Plug::In, false ) );
	addChild( new BoolPlug( "pruneOccluded", Gaffer::Plug::In, false ) );
	addChild( new FloatPlug( "occludedThreshold", Gaffer::Plug::In, 1.0 ) );

	addChild( new CompoundObjectPlug( "__sampleMapping", Gaffer::Plug::Out, new IECore::CompoundObject ) );

	// We don't ever want to change these, so we make pass-through connections.
	outPlug()->viewNamesPlug()->setInput( inPlug()->viewNamesPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
}

DeepState::~DeepState()
{
}

Gaffer::IntPlug *DeepState::deepStatePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *DeepState::deepStatePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *DeepState::pruneTransparentPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *DeepState::pruneTransparentPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *DeepState::pruneOccludedPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *DeepState::pruneOccludedPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

Gaffer::FloatPlug *DeepState::occludedThresholdPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::FloatPlug *DeepState::occludedThresholdPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

Gaffer::CompoundObjectPlug *DeepState::sampleMappingPlug()
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::CompoundObjectPlug *DeepState::sampleMappingPlug() const
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 4 );
}

void DeepState::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( input == inPlug()->sampleOffsetsPlug() )
	{
		outputs.push_back( sampleMappingPlug() );
	}
	else if( input == inPlug()->channelDataPlug() )
	{
		outputs.push_back( sampleMappingPlug() );
	}
	else if( input == inPlug()->channelNamesPlug() )
	{
		outputs.push_back( sampleMappingPlug() );
	}
	else if( input == pruneTransparentPlug() )
	{
		outputs.push_back( sampleMappingPlug() );
	}
	else if( input == pruneOccludedPlug() )
	{
		outputs.push_back( sampleMappingPlug() );
	}
	else if( input == occludedThresholdPlug() )
	{
		outputs.push_back( sampleMappingPlug() );
	}
	else if( input == inPlug()->deepPlug() )
	{
		outputs.push_back( sampleMappingPlug() );
		outputs.push_back( outPlug()->deepPlug() );
	}
	else if( input == sampleMappingPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
		outputs.push_back( outPlug()->sampleOffsetsPlug() );
	}
	else if( input == deepStatePlug() )
	{
		outputs.push_back( sampleMappingPlug() );
		outputs.push_back( outPlug()->deepPlug() );
	}
}

void DeepState::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hash( output, context, h );

	if( output != sampleMappingPlug() )
	{
		return;
	}

	ConstStringVectorDataPtr channelNamesData;

	{
		ImagePlug::GlobalScope s( context );
		pruneTransparentPlug()->hash( h );
		pruneOccludedPlug()->hash( h );
		occludedThresholdPlug()->hash( h );
		deepStatePlug()->hash( h );
		channelNamesData = inPlug()->channelNamesPlug()->getValue();
	}

	inPlug()->sampleOffsetsPlug()->hash( h );

	const std::vector<std::string> &channelNames = channelNamesData->readable();

	ImagePlug::ChannelDataScope channelScope( context );
	if( ImageAlgo::channelExists( channelNames, ImageAlgo::channelNameZ ) )
	{
		channelScope.setChannelName( &ImageAlgo::channelNameZ );
		inPlug()->channelDataPlug()->hash( h );
	}
	else
	{
		h.append( false );
	}
	if( ImageAlgo::channelExists( channelNames, ImageAlgo::channelNameZBack ) )
	{
		channelScope.setChannelName( &ImageAlgo::channelNameZBack );
		inPlug()->channelDataPlug()->hash( h );
	}
	else
	{
		h.append( false );
	}
	if( ImageAlgo::channelExists( channelNames, ImageAlgo::channelNameA ) )
	{
		channelScope.setChannelName( &ImageAlgo::channelNameA );
		inPlug()->channelDataPlug()->hash( h );
	}
	else
	{
		h.append( false );
	}
}

void DeepState::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	ImageProcessor::compute( output, context );

	if( output != sampleMappingPlug() )
	{
		return;
	}

	ConstIntVectorDataPtr sampleOffsetsData = inPlug()->sampleOffsetsPlug()->getValue();
	ConstStringVectorDataPtr channelNamesData;

	TargetState requestedDeepState;
	bool pruneTransparent, pruneOccluded;
	float occludedThreshold;

	{
		ImagePlug::GlobalScope s( context );
		requestedDeepState = TargetState( deepStatePlug()->getValue() );
		pruneTransparent = pruneTransparentPlug()->getValue();
		pruneOccluded = pruneOccludedPlug()->getValue();
		occludedThreshold = occludedThresholdPlug()->getValue();

		channelNamesData = inPlug()->channelNamesPlug()->getValue();
	}

	const std::vector<std::string> &channelNames = channelNamesData->readable();

	CompoundObjectPtr result = new CompoundObject;

	ImagePlug::ChannelDataScope channelScope( Context::current() );
	bool hasZ = ImageAlgo::channelExists( channelNames, ImageAlgo::channelNameZ );

	ConstFloatVectorDataPtr zData;
	if( hasZ )
	{
		channelScope.setChannelName( &ImageAlgo::channelNameZ );
		zData = inPlug()->channelDataPlug()->getValue();
	}

	ConstFloatVectorDataPtr zBackData;
	bool hasZBack = ImageAlgo::channelExists( channelNames, ImageAlgo::channelNameZBack );
	if( hasZBack )
	{
		channelScope.setChannelName( &ImageAlgo::channelNameZBack );
		zBackData = inPlug()->channelDataPlug()->getValue();
	}
	else
	{
		zBackData = zData;
	}

	bool isSorted, isTidy;
	if( hasZ )
	{
		checkState( sampleOffsetsData->readable(), zData->readable(), zBackData->readable(), isSorted, isTidy );
	}
	else
	{
		// Without a Z channel, we assume the samples are already ordered
		isSorted = true;
		isTidy = true;
	}

	IECore::IntVectorDataPtr sampleSortingData = nullptr;

	if( isTidy )
	{
		if( requestedDeepState == TargetState::Flat )
		{
			// Special simple/fast case for flattening data that's already tidy

			FloatVectorDataPtr sampleWeightsData = new FloatVectorData();
			std::vector<float> &sampleWeights = sampleWeightsData->writable();

			if( ImageAlgo::channelExists( channelNames, ImageAlgo::channelNameA ) )
			{
				ImagePlug::ChannelDataScope channelScope( Context::current() );
				channelScope.setChannelName( &ImageAlgo::channelNameA );
				ConstFloatVectorDataPtr alphaData = inPlug()->channelDataPlug()->getValue();

				sampleWeights.resize( sampleOffsetsData->readable().back() );
				FloatVectorDataPtr mergedAlphaData = tidyAlphaToFlatLinearWeights(
					sampleWeights,
					alphaData->readable(),
					sampleOffsetsData->readable()
				);

				result->members()[ g_AName ] = mergedAlphaData;
				result->members()[ g_contributionWeightsName ] = sampleWeightsData;
			}
			else
			{
				sampleWeights.resize( sampleOffsetsData->readable().back(), 1.0f );
				result->members()[ g_contributionWeightsName ] = sampleWeightsData;
			}
			static_cast<CompoundObjectPlug *>( output )->setValue( result );
			return;
		}
		else if( requestedDeepState == TargetState::Sorted || ( requestedDeepState == TargetState::Tidy &&
			!pruneTransparent && !pruneOccluded ) )
		{
			// We're already sorted, nothing needs to be done
			static_cast<CompoundObjectPlug *>( output )->setValue( result );
			return;
		}
	}

	if( !isSorted )
	{
		sampleSortingData = computeSampleSorting(
				sampleOffsetsData->readable(), zData->readable(), zBackData->readable()
			);
	}

	if( requestedDeepState == TargetState::Sorted )
	{
		// If all we want is to sort, we can just return the sort indices
		if( sampleSortingData )
		{
			result->members()[ g_contributionIdsName ] = sampleSortingData;
		}
	}
	else
	{
		if( sampleSortingData )
		{
			// If the input is unsorted, we need to apply the sort to Z and ZBack before
			// we can merge samples
			zData = sortByIndices( zData->readable(), sampleSortingData->readable() );
			if( hasZBack )
			{
				zBackData = sortByIndices( zBackData->readable(), sampleSortingData->readable() );
			}
			else
			{
				zBackData = zData;
			}
		}

		// Set up the sample merge data
		SampleMerge sampleMerge( sampleOffsetsData->readable(),
			hasZ ? &zData->readable() : nullptr, hasZ ? &zBackData->readable() : nullptr );

		if( sampleSortingData )
		{
			// If the input was unsorted, we now rearrange the contributionIds to correspond to the
			// original, unsorted inputs.  This means we don't have to sort the inputs.
			std::vector<int> &contributionIds = sampleMerge.contributionIdsData->writable();
			const std::vector<int> &sampleSorting = sampleSortingData->readable();
			for( unsigned int i = 0; i < contributionIds.size(); i++ )
			{
				contributionIds[i] = sampleSorting[ contributionIds[i] ];
			}
		}

		ConstFloatVectorDataPtr alphaData;
		if( ImageAlgo::channelExists( channelNames, ImageAlgo::channelNameA ) )
		{
			channelScope.setChannelName( &ImageAlgo::channelNameA );
			alphaData = inPlug()->channelDataPlug()->getValue();
		}
		else
		{
			FloatVectorDataPtr newAlphaData = new FloatVectorData();
			// It's a bit sloppy to allocate this data here, but it allows the rest of the code
			// to deal with this case consistently, and deep images with missing alpha channels
			// don't seem like a case worth optimizing for
			newAlphaData->writable().resize( sampleMerge.sampleOffsetsData->readable().back(), 0.0f );
			alphaData = newAlphaData;
		}

		// Do the math that converts from depth fractions into linear weights
		FloatVectorDataPtr mergedAlphaData = alphaToLinearWeights(
			sampleMerge.contributionAmountsData->writable(),  // Modified in place
			sampleMerge.contributionIdsData->readable(),
			sampleMerge.contributionOffsetsData->readable(),
			alphaData->readable(),
			sampleMerge.sampleOffsetsData->readable(),
			requestedDeepState == TargetState::Flat
		);

		if( requestedDeepState == TargetState::Tidy )
		{
			if( pruneTransparent || pruneOccluded )
			{
				// Prune transparent or occluded samples
				pruneSamples(
						sampleMerge.contributionAmountsData->writable(),
						sampleMerge.contributionIdsData->writable(),
						sampleMerge.contributionOffsetsData->writable(),
						mergedAlphaData->writable(),
						hasZ ? &sampleMerge.zData->writable() : nullptr,
						hasZ ? &sampleMerge.zBackData->writable() : nullptr,
						sampleMerge.sampleOffsetsData->writable(),
						pruneTransparent, pruneOccluded, occludedThreshold
				);
			}

			// Both SampleMerge and pruneSamples don't know the exact size of thier outputs
			// beforehand.  We deal with this either by using push_back to expand a vector,
			// or working in a worst case sized vector.  We don't want to do unnecessary
			// allocations, but we also don't want to cache vectors that are larger than
			// necessary.  Calling shrink_to_fit should be a reasonable compromise, leaving
			// it up to the STL implementation whether there is enough size reduction to be
			// worth an allocation.
			if( hasZ )
			{
				sampleMerge.zData->writable().shrink_to_fit();
				sampleMerge.zBackData->writable().shrink_to_fit();
			}
			sampleMerge.contributionAmountsData->writable().shrink_to_fit();
			sampleMerge.contributionIdsData->writable().shrink_to_fit();
			sampleMerge.contributionOffsetsData->writable().shrink_to_fit();
			mergedAlphaData->writable().shrink_to_fit();


			if( hasZ )
			{
				result->members()[ g_ZName ] = sampleMerge.zData;
				result->members()[ g_ZBackName ] = sampleMerge.zBackData;
			}
			result->members()[ g_AName ] = mergedAlphaData;
			result->members()[ g_sampleOffsetsName ] = sampleMerge.sampleOffsetsData;
			result->members()[ g_contributionIdsName ] = sampleMerge.contributionIdsData;
			result->members()[ g_contributionWeightsName ] = sampleMerge.contributionAmountsData;
			result->members()[ g_contributionOffsetsName ] = sampleMerge.contributionOffsetsData;
		}
		else // requestedDeepState must be TargetState::Flat
		{
			FloatVectorDataPtr sampleWeightsData = new FloatVectorData();
			std::vector<float> &sampleWeights = sampleWeightsData->writable();
			sampleWeights.resize( sampleOffsetsData->readable().back(), 0.0f );

			// Accumulate all contribution weights into the index corresponding to the original samples
			// This allows us to then apply these weights in one pass through the channel data
			const std::vector<int> &ids =  sampleMerge.contributionIdsData->readable();
			const std::vector<float> &weights =  sampleMerge.contributionAmountsData->readable();
			for( unsigned int i = 0; i < ids.size(); i++ )
			{
				sampleWeights[ ids[i] ] += weights[i];
			}

			result->members()[ g_AName ] = mergedAlphaData;
			result->members()[ g_contributionWeightsName ] = sampleWeightsData;
		}
	}

	static_cast<CompoundObjectPlug *>( output )->setValue( result );
}

void DeepState::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelData( output, context, h );

	int inDeep;
	TargetState requestedDeepState;

	{
		ImagePlug::GlobalScope s( context );
		requestedDeepState = TargetState( deepStatePlug()->getValue() );
		inDeep = inPlug()->deepPlug()->getValue();
	}

	if( !inDeep )
	{
		// We don't do anything to flat images
		h = inPlug()->channelDataPlug()->hash();
		return;
	}

	h.append( inPlug()->channelNamesHash() );

	h.append( int( requestedDeepState ) );

	const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );

	// Some channels are handled specially
	if( channelName == "Z" )
	{
		h.append( 1 );
	}
	else if( channelName == "ZBack" )
	{
		h.append( 2 );
	}
	else if( channelName == "A" )
	{
		h.append( 3 );
	}
	else
	{
		h.append( 0 );
	}

	inPlug()->channelDataPlug()->hash( h );

	ImagePlug::ChannelDataScope channelScope( Context::current() );
	channelScope.remove( ImagePlug::channelNameContextName );

	// The sample merging plug really drives everything
	sampleMappingPlug()->hash( h );
}

IECore::ConstFloatVectorDataPtr DeepState::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	bool inDeep;
	TargetState requestedDeepState;

	{
		ImagePlug::GlobalScope s( context );
		requestedDeepState = TargetState( deepStatePlug()->getValue() );
		inDeep = inPlug()->deepPlug()->getValue();
	}

	ConstFloatVectorDataPtr inData = inPlug()->channelDataPlug()->getValue();

	if( !inDeep )
	{
		// We don't do anything to flat images
		return inData;
	}

	bool isAlpha = channelName == "A";
	bool isZ = false;
	if( channelName[0] == 'Z' )
	{
		if( channelName == "Z" || channelName == "ZBack" )
		{
			isZ = true;
		}
	}

	ImagePlug::ChannelDataScope channelScope( Context::current() );
	channelScope.remove( ImagePlug::channelNameContextName );

	if( isZ && ( requestedDeepState == TargetState::Flat ) )
	{
		// When flattening, we treat Z and ZBack specially, and just return the minimum and
		// maximum values over the pixel ( If you want properly filtered depth, use Flatten )
		FloatVectorDataPtr flatZData = new FloatVectorData();
		std::vector<float> &flatZ = flatZData->writable();
		flatZ.resize( ImagePlug::tilePixels() );

		ConstIntVectorDataPtr sampleOffsetsData = inPlug()->sampleOffsetsPlug()->getValue();
		const std::vector<int> &sampleOffsets = sampleOffsetsData->readable();

		const std::vector<float> &in = inData->readable();

		bool back = channelName == "ZBack";

		int prevOffset = 0;
		for( int pixel = 0; pixel < ImagePlug::tilePixels(); pixel++ )
		{
			int offset = sampleOffsets[pixel];

			float extreme = 0.0f;

			if( offset != prevOffset )
			{
				extreme = in[prevOffset];
				if( back )
				{
					for( int sample = prevOffset + 1; sample < offset; sample++ )
					{
						extreme = std::max( extreme, in[sample] );
					}
				}
				else
				{
					for( int sample = prevOffset + 1; sample < offset; sample++ )
					{
						extreme = std::min( extreme, in[sample] );
					}
				}
			}

			flatZ[pixel] = extreme;
			prevOffset = offset;
		}

		return flatZData;
	}

	// Everything is driven by the sampleMapping plug, which tells us how to map from the input
	// channel data to the output channel data
	ConstCompoundObjectPtr sampleMappingData = sampleMappingPlug()->getValue();

	ConstFloatVectorDataPtr result;
	if( requestedDeepState == TargetState::Sorted )
	{
		// Just reindex, based on the sorted indices
		ConstIntVectorDataPtr mergedSampleContributionIdsData = sampleMappingData->member<IntVectorData>( g_contributionIdsName, false );
		if( mergedSampleContributionIdsData )
		{
			result = sortByIndices( inData->readable(), mergedSampleContributionIdsData->readable() );
		}
		else
		{
			// Null sort indices means sorting not needed - inData is already sorted
			result = inData;
		}
	}
	else if( isAlpha || isZ )
	{
		// Some channels must be computed in order to compute the sampleMapping, and these channels
		// are just stored in the sampleMapping plug to avoid recomputing them
		result = sampleMappingData->member<FloatVectorData>( channelName, false );

		if( !result )
		{
			// If the data wasn't stored, it's because we can just pass through the input
			result = inData;
		}
	}
	else
	{
		if( requestedDeepState == TargetState::Flat )
		{
			// When flattening, we get a weight corresponding to each sample, and we just need to multiply
			// the input samples by these weights and sum them.
			ConstFloatVectorDataPtr mergedSampleContributionAmountsData = sampleMappingData->member<FloatVectorData>( g_contributionWeightsName, true );
			ConstIntVectorDataPtr sampleOffsetsData = inPlug()->sampleOffsetsPlug()->getValue();
			assert( (int)inData->readable().size() == sampleOffsetsData->readable().back() );
			result = sumByWeights( inData->readable(),
				mergedSampleContributionAmountsData->readable(),
				sampleOffsetsData->readable()
			);
		}
		else
		{
			// When tidying, we get a set of weights and ids corresponding to each sample, and we must sum
			// per sample, based on the ids.
			ConstIntVectorDataPtr mergedSampleContributionIdsData = sampleMappingData->member<IntVectorData>( g_contributionIdsName, false );

			if( !mergedSampleContributionIdsData )
			{
				// Null indices means tidying not needed - inData is already tidy
				result = inData;
			}
			else
			{
				ConstFloatVectorDataPtr mergedSampleContributionAmountsData = sampleMappingData->member<FloatVectorData>( g_contributionWeightsName, true );
				ConstIntVectorDataPtr mergedSampleContributionOffsetsData = sampleMappingData->member<IntVectorData>( g_contributionOffsetsName, true );
				result = sumByIndicesAndWeights( inData->readable(),
					mergedSampleContributionIdsData->readable(),
					mergedSampleContributionAmountsData->readable(),
					mergedSampleContributionOffsetsData->readable()
				);
			}
		}
	}

	return result;
}

void DeepState::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	TargetState requestedDeepState;
	{
		ImagePlug::GlobalScope s( context );
		requestedDeepState = TargetState( deepStatePlug()->getValue() );
	}

	if( requestedDeepState == TargetState::Flat )
	{
		h = ImagePlug::flatTileSampleOffsets()->IECore::Object::hash();
		return;
	}

	if( requestedDeepState == TargetState::Sorted )
	{
		// If we aren't going to be changing the offsets, pass through the hash
		h = inPlug()->sampleOffsetsPlug()->hash();
		return;
	}

	ImageProcessor::hashSampleOffsets( parent, context, h );
	sampleMappingPlug()->hash( h );
}

IECore::ConstIntVectorDataPtr DeepState::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstStringVectorDataPtr channelNamesData;
	TargetState requestedDeepState;

	{
		ImagePlug::GlobalScope s( context );
		requestedDeepState = TargetState( deepStatePlug()->getValue() );
		if( requestedDeepState == TargetState::Flat )
		{
			return ImagePlug::flatTileSampleOffsets();
		}
		channelNamesData = inPlug()->channelNamesPlug()->getValue();
	}

	if( requestedDeepState == TargetState::Sorted )
	{
		return inPlug()->sampleOffsetsPlug()->getValue();
	}
	else
	{
		ConstIntVectorDataPtr remapped = sampleMappingPlug()->getValue()->member<IntVectorData>( g_sampleOffsetsName, false );
		if( remapped )
		{
			return remapped;
		}
		else
		{
			return inPlug()->sampleOffsetsPlug()->getValue();
		}
	}
}

void DeepState::hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( TargetState( deepStatePlug()->getValue() ) == TargetState::Flat )
	{
		ImageProcessor::hashDeep( parent, context, h );
	}
	else
	{
		// If we aren't going to be changing the state, pass through the hash
		h = inPlug()->deepPlug()->hash();
	}
}

bool DeepState::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	if( TargetState( deepStatePlug()->getValue() ) == TargetState::Flat )
	{
		return false;
	}
	else
	{
		return inPlug()->deepPlug()->getValue();
	}
}
