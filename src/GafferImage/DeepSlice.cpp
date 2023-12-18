//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/DeepSlice.h"

#include "GafferImage/DeepState.h"
#include "GafferImage/ImageAlgo.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

// \todo - might be nice to move this a central algo header, and share this math with DeepState,
// though precision is important there, so we'd probably have to modify the API to return the
// directly computed alpha and the sample multiplier separately, and maybe that's not worth it.
float sampleMultiplier( float alpha, float fraction )
{
	if( alpha <= 0.0f )
	{
		// If alpha is zero, then EXR says that this represents a fully transparent incandescent
		// volume, and the contribution is linear in the fraction of the sample that we take
		// ( the exponential shape comes from visibility blocking in fog causing later
		// contributions to contribute less than the start of the curve, which doesn't
		// happen without visibility blocking ).
		return fraction;
	}
	else if( alpha == 1.0f )
	{
		// If the alpha is 1, then this represents a fully opaque volume, which requires infinite density.
		// It reaches an opacity of 1 immediately with no curve.
		return 1.0f;
	}
	else if( fraction == 1.0f || fraction == 0.0f )
	{
		// For these two values, the equation below will evaluate to simply the value of "fraction"
		// in the limit, regardless of the value of alpha ( as long as it isn't one of the special
		// values checked above ).
		//
		// The fraction == 0.0 case is not currently used ( because we exclude samples which we are
		// taking 0% of when computing start/end for the sample range ), but is included for
		// completeness.
		return fraction;
	}
	else
	{
		// Use the numerically reliable math from "Interpreting OpenEXR Deep Pixels" to find the
		// alpha after taking the fraction of the segment, and then divide by the original alpha
		// to find the weighting factor we need to multiply this sample by.
		return -expm1( fraction * log1p( -alpha ) ) / alpha;
	}
}

const IECore::InternedString g_sampleOffsetsName = "sampleOffsets";
const IECore::InternedString g_inputIndicesName = "inputIndices";
const IECore::InternedString g_firstWeightsName = "firstWeights";
const IECore::InternedString g_lastWeightsName = "lastWeights";

} // namespace

//////////////////////////////////////////////////////////////////////////
// DeepSlice
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( DeepSlice );

size_t DeepSlice::g_firstPlugIndex = 0;

DeepSlice::DeepSlice( const std::string &name )
	: ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new OptionalValuePlug( "nearClip", new FloatPlug( "value", Gaffer::Plug::In, 0.0f, 0.0f ) ) );
	addChild( new OptionalValuePlug( "farClip", new FloatPlug( "value", Gaffer::Plug::In, 0.0f, 0.0f ) ) );
	addChild( new BoolPlug( "flatten", Plug::In ) );

	addChild( new ImagePlug( "__tidyIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );

	// The "sliceData" contains all the information about which samples to take that depends on Z/ZBack.
	// See compute() for more description.
	addChild( new CompoundObjectPlug( "__sliceData", Gaffer::Plug::Out, new IECore::CompoundObject ) );

	// We tidy the input image before we process it, because this means we can just process each sample
	// in order ( and is quite cheap if the image is already tidy ).
	DeepStatePtr tidy = new DeepState( "__tidy" );
	addChild( tidy );
	tidy->inPlug()->setInput( inPlug() );
	tidyInPlug()->setInput( tidy->outPlug() );

	// We don't ever want to change these, so we make pass-through connections.
	outPlug()->viewNamesPlug()->setInput( inPlug()->viewNamesPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
}

DeepSlice::~DeepSlice()
{
}

Gaffer::OptionalValuePlug *DeepSlice::nearClipPlug()
{
	return getChild<OptionalValuePlug>( g_firstPlugIndex );
}

const Gaffer::OptionalValuePlug *DeepSlice::nearClipPlug() const
{
	return getChild<OptionalValuePlug>( g_firstPlugIndex );
}

Gaffer::OptionalValuePlug *DeepSlice::farClipPlug()
{
	return getChild<OptionalValuePlug>( g_firstPlugIndex + 1 );
}

const Gaffer::OptionalValuePlug *DeepSlice::farClipPlug() const
{
	return getChild<OptionalValuePlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *DeepSlice::flattenPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *DeepSlice::flattenPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

GafferImage::ImagePlug *DeepSlice::tidyInPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex + 3 );
}

const GafferImage::ImagePlug *DeepSlice::tidyInPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex + 3 );
}

CompoundObjectPlug *DeepSlice::sliceDataPlug()
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 4 );
}

const CompoundObjectPlug *DeepSlice::sliceDataPlug() const
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 4 );
}

void DeepSlice::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if(
		input == inPlug()->deepPlug() ||
		input == flattenPlug()
	)
	{
		outputs.push_back( outPlug()->deepPlug() );
	}

	if(
		nearClipPlug()->isAncestorOf( input ) ||
		farClipPlug()->isAncestorOf( input ) ||
		input == inPlug()->deepPlug() ||
		input == inPlug()->channelNamesPlug() ||
		input == tidyInPlug()->channelDataPlug() ||
		input == tidyInPlug()->sampleOffsetsPlug()
	)
	{
		outputs.push_back( sliceDataPlug() );
	}

	if(
		nearClipPlug()->isAncestorOf( input ) ||
		farClipPlug()->isAncestorOf( input ) ||
		input == flattenPlug() ||
		input == inPlug()->deepPlug() ||
		input == inPlug()->channelNamesPlug() ||
		input == tidyInPlug()->channelDataPlug() ||
		input == inPlug()->channelDataPlug() || // Used by special passthrough when nearClip/farClip/flatten disabled
		input == sliceDataPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}

	if(
		nearClipPlug()->isAncestorOf( input ) ||
		farClipPlug()->isAncestorOf( input ) ||
		input == inPlug()->sampleOffsetsPlug() || // Used by special passthrough when nearClip/farClip/flatten disabled
		input == sliceDataPlug()
	)
	{
		outputs.push_back( outPlug()->sampleOffsetsPlug() );
	}
}

void DeepSlice::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hash( output, context, h );

	if( output != sliceDataPlug() )
	{
		return;
	}

	ConstStringVectorDataPtr channelNamesData;

	{
		ImagePlug::GlobalScope s( context );
		inPlug()->deepPlug()->hash( h );
		nearClipPlug()->hash( h );
		farClipPlug()->hash( h );
		channelNamesData = inPlug()->channelNamesPlug()->getValue();
	}

	const std::vector<std::string> &channelNames = channelNamesData->readable();

	tidyInPlug()->sampleOffsetsPlug()->hash( h );

	{
		ImagePlug::ChannelDataScope s( context );
		if( ImageAlgo::channelExists( channelNames, ImageAlgo::channelNameA ) )
		{
			s.setChannelName( &ImageAlgo::channelNameA );
			tidyInPlug()->channelDataPlug()->hash( h );
		}
		else
		{
			h.append( false );
		}

		if( ImageAlgo::channelExists( channelNames, ImageAlgo::channelNameZ ) )
		{
			s.setChannelName( &ImageAlgo::channelNameZ );
			tidyInPlug()->channelDataPlug()->hash( h );
		}
		else
		{
			h.append( false );
		}

		if( ImageAlgo::channelExists( channelNames, ImageAlgo::channelNameZBack ) )
		{
			s.setChannelName( &ImageAlgo::channelNameZBack );
			tidyInPlug()->channelDataPlug()->hash( h );
		}
		else
		{
			h.append( false );
		}
	}
}

void DeepSlice::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	ImageProcessor::compute( output, context );

	if( output != sliceDataPlug() )
	{
		return;
	}

	// sliceData is a CompoundObject with up to 4 members, storing the following things
	//
	// "sampleOffsets" : a running sum of the number of samples contributing to each pixel.
	//                   When outputting a deep image, this will be the sampleOffsets of the output.
	//                   When outputting a flat image, this is used to know which samples to sum.
	// "inputIndices"  : an int vector with the sample index where we start taking samples for each pixel
	// "firstWeights"  : a float for each pixel with a multiplier for the first sample for each pixel
	//                   ( included when nearClip is on )
	// "lastWeights"   : a float for each pixel with a multiplier for the last sample for each pixel
	//                   ( included when farClip is on )
	//
	// ( Note that any sample that is not first or last cannot intersect a clip plane, so we always take 100% )

	// In order to compute this, we first need to get the control parameters, and the Z, ZBack, and A channel data

	bool deep;
	bool nearClip;
	float nearClipDepth;
	bool farClip;
	float farClipDepth;

	ConstStringVectorDataPtr channelNamesData;

	{
		ImagePlug::GlobalScope s( context );
		deep = inPlug()->deepPlug()->getValue();
		nearClip = nearClipPlug()->enabledPlug()->getValue();
		nearClipDepth = nearClipPlug()->valuePlug<FloatPlug>()->getValue();
		farClip = farClipPlug()->enabledPlug()->getValue();
		farClipDepth = farClipPlug()->valuePlug<FloatPlug>()->getValue();
		channelNamesData = inPlug()->channelNamesPlug()->getValue();
	}

	const std::vector<std::string> &channelNames = channelNamesData->readable();

	ConstIntVectorDataPtr sampleOffsetsData;
	if( deep )
	{
		sampleOffsetsData = tidyInPlug()->sampleOffsetsPlug()->getValue();
	}
	else
	{
		sampleOffsetsData = ImagePlug::flatTileSampleOffsets();
	}

	ConstFloatVectorDataPtr aData;
	ConstFloatVectorDataPtr zData;
	ConstFloatVectorDataPtr zBackData;

	{
		ImagePlug::ChannelDataScope s( context );
		if( ImageAlgo::channelExists( channelNames, ImageAlgo::channelNameA ) )
		{
			s.setChannelName( &ImageAlgo::channelNameA );
			aData = tidyInPlug()->channelDataPlug()->getValue();
		}
		else
		{
			// We can produce legitimate results without an alpha channel by treating the alpha
			// as zero, but we don't have a reliable and efficient way to get a buffer of zeros
			// guaranteed to be large enough, so I guess we just have to have a special case for
			// null a later in this function.
		}

		if( ImageAlgo::channelExists( channelNames, ImageAlgo::channelNameZ ) )
		{
			s.setChannelName( &ImageAlgo::channelNameZ );
			zData = tidyInPlug()->channelDataPlug()->getValue();
		}
		else
		{
			throw IECore::Exception( "DeepSlice requires a Z channel" );
		}

		if( ImageAlgo::channelExists( channelNames, ImageAlgo::channelNameZBack ) )
		{
			s.setChannelName( &ImageAlgo::channelNameZBack );
			zBackData = tidyInPlug()->channelDataPlug()->getValue();
		}
		else
		{
			zBackData = zData;
		}
	}

	const std::vector<int> &sampleOffsets = sampleOffsetsData->readable();
	const float *a = aData ? &aData->readable()[0] : nullptr;
	const std::vector<float> &z = zData->readable();
	const std::vector<float> &zBack = zBackData->readable();

	// Allocate outputs

	FloatVectorDataPtr firstWeightsData;
	float *firstWeights = nullptr;
	FloatVectorDataPtr lastWeightsData;
	float *lastWeights = nullptr;

	IntVectorDataPtr outputSampleOffsetsData = new IntVectorData();
	outputSampleOffsetsData->writable().resize( ImagePlug::tilePixels() );
	int *outputSampleOffsets = &outputSampleOffsetsData->writable()[0];
	IntVectorDataPtr inputIndicesData = new IntVectorData();
	inputIndicesData->writable().resize( ImagePlug::tilePixels() );
	int *inputIndices = &inputIndicesData->writable()[0];

	if( nearClip )
	{
		firstWeightsData = new FloatVectorData();
		firstWeightsData->writable().resize( ImagePlug::tilePixels() );
		firstWeights = &firstWeightsData->writable()[0];
	}

	if( farClip )
	{
		lastWeightsData = new FloatVectorData();
		lastWeightsData->writable().resize( ImagePlug::tilePixels() );
		lastWeights = &lastWeightsData->writable()[0];
	}

	// Now we're ready to actually process all the samples

	int prevOffset = 0;
	int outputSampleOffset = 0;

	for( int i = 0; i < ImagePlug::tilePixels(); i++ )
	{
		// Figure out the start and end of the range of samples to consider for each pixel.
		//
		// This is where we implement the logic that includes samples exactly at nearClipDepth,
		// but exclude samples exactly at farClipDepth.
		//
		// We need to include point samples at the threshold on one side and not the other so that you
		// can split on a chosen depth and then composite the two slices back together.
		//
		// The choice to keep samples at the the near clip was made to avoid a specific weird special
		// case: if we kept samples at the far clip, then it would really make sense to include a
		// volume sample with an alpha of 1 starting at the far clip, since an alpha of 1 means it reaches
		// full opacity immediately at the start of the volume range. However, if we include this sample,
		// it would become a point sample, once the zBack is reduced to the far clip. The problem with this
		// is that there could already be a point sample at this depth, before the volume sample. Outputting
		// two point samples at the same depth would violate tidyness, and produce unexpected results because
		// the two point samples wouldn't be combined in the right order. The only real solution would be
		// adding a special case to combine the two source samples into one output point sample, but this
		// would add some annoying complexity, since other than this, each output sample corresponds to
		// exactly one input sample.
		//
		// Solution: discard point samples at the far clip, and keep point samples at the near clip instead.
		// There is hypothetically the same problem with the near clip being exactly equal to the zBack value
		// of a volume sample with an alpha of 1 ... but in order for this to happen, we're looking at something
		// behind a sample with an alpha of 1, which isn't very meaningful anyway. Under these circumstances,
		// I'm OK with simply discarding a volume sample when we are taking 0% of it, even if its alpha is 1,
		// which keeps the code simpler.

		int offset = sampleOffsets[i];
		int start = prevOffset;
		if( nearClip )
		{
			// Increment start to omit any samples that are before the near clip, but don't skip a point
			// sample exactly at the near clip ( if zBack is exactly on the clip, we only skip if it's
			// a volume sample with z < zBack )
			while( start < offset && ( zBack[start] < nearClipDepth || ( zBack[start] == nearClipDepth && z[start] < nearClipDepth ) ) )
			{
				start++;
			}
		}

		int end = offset;
		if( farClip )
		{
			end = start;

			// Increment end to include any samples that are strictly before the far clip. Point samples exactly
			// at the near clip are omitted.
			while( end < offset && z[end] < farClipDepth )
			{
				end++;
			}
		}

		outputSampleOffset += end - start;
		outputSampleOffsets[i] = outputSampleOffset;
		inputIndices[i] = start;

		// Now set the weights for what fractions of the input samples to take.
		//
		// Note: you'll see a bunch of cases skipping these calculations when zBack == z.
		// That's a point sample, which we either take or don't, you can't slice a fraction
		// of a sample with no size.
		float firstWeight = 1.0f;
		float lastWeight = 1.0f;
		if( end - start == 0 )
		{
			// If there are no samples, no need to worry about the values of the multipliers
		}
		else if( nearClip && farClip && end - start == 1 && zBack[start] > z[start] )
		{
			// Weird special case: if there is exactly one sample, then there's the possibility
			// that both the start and end of the sample could be clipped. We put the combined
			// weight representing both clips into firstWeight, and leave lastWeight set to 1.0.

			float usedFraction =
				( std::min( zBack[start], farClipDepth ) - std::max( z[start], nearClipDepth ) ) /
				( zBack[start] - z[start] );

			firstWeight = sampleMultiplier( a ? a[start] : 0.0f, usedFraction );
		}
		else
		{
			if( nearClip && zBack[start] > z[start] )
			{
				float usedFraction =
					( zBack[start] - std::max( z[start], nearClipDepth ) ) /
					( zBack[start] - z[start] );

				firstWeight = sampleMultiplier( a ? a[start] : 0.0f, usedFraction );
			}

			if( farClip && zBack[end - 1] > z[end - 1] )
			{
				float usedFraction =
					( std::min( zBack[end - 1], farClipDepth ) - z[end - 1] ) /
					( zBack[end - 1] - z[end - 1] );

				lastWeight = sampleMultiplier( a ? a[end - 1] : 0.0f, usedFraction );
			}
		}

		if( firstWeights )
		{
			firstWeights[i] = firstWeight;
		}

		if( lastWeights )
		{
			lastWeights[i] = lastWeight;
		}

		prevOffset = offset;
	}

	// Fill the result CompoundObject

	CompoundObjectPtr result = new CompoundObject;
	result->members()[ g_sampleOffsetsName ] = std::move( outputSampleOffsetsData );
	result->members()[ g_inputIndicesName ] = std::move( inputIndicesData );
	if( firstWeightsData )
	{
		result->members()[ g_firstWeightsName ] = std::move( firstWeightsData );
	}
	if( lastWeightsData )
	{
		result->members()[ g_lastWeightsName ] = std::move( lastWeightsData );
	}
	static_cast<CompoundObjectPlug *>( output )->setValue( result );
}

void DeepSlice::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{


	bool deep;
	bool flatten;
	bool nearClip;
	IECore::MurmurHash nearClipDepthHash;
	bool farClip;
	IECore::MurmurHash farClipDepthHash;

	{
		ImagePlug::GlobalScope s( context );
		flatten = flattenPlug()->getValue();
		deep = inPlug()->deepPlug()->getValue();
		nearClip = nearClipPlug()->enabledPlug()->getValue();
		nearClipDepthHash = nearClipPlug()->valuePlug<FloatPlug>()->hash();
		farClip = farClipPlug()->enabledPlug()->getValue();
		farClipDepthHash = farClipPlug()->valuePlug<FloatPlug>()->hash();
	}

	if( !flatten && !nearClip && !farClip )
	{
		h = inPlug()->channelDataPlug()->hash();
		return;
	}

	ImageProcessor::hashChannelData( parent, context, h );
	tidyInPlug()->channelDataPlug()->hash( h );

	h.append( deep );
	h.append( flatten );
	h.append( nearClip );
	h.append( nearClipDepthHash );
	h.append( farClip );
	h.append( farClipDepthHash );

	{
		ImagePlug::ChannelDataScope scope( context );
		scope.remove( ImagePlug::channelNameContextName );
		sliceDataPlug()->hash( h );

		const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );

		if(
			flatten && deep &&
			channelName != ImageAlgo::channelNameA &&
			channelName != ImageAlgo::channelNameZ &&
			channelName != ImageAlgo::channelNameZBack
		)
		{
			ConstStringVectorDataPtr channelNamesData = inPlug()->channelNames();
			const std::vector<std::string> &channelNames = channelNamesData->readable();
			if( ImageAlgo::channelExists( channelNames, ImageAlgo::channelNameA ) )
			{
				scope.setChannelName( &ImageAlgo::channelNameA );
				tidyInPlug()->channelDataPlug()->hash( h );
			}
			else
			{
				h.append( false );
			}
		}
	}
}


IECore::ConstFloatVectorDataPtr DeepSlice::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstFloatVectorDataPtr channelData = tidyInPlug()->channelDataPlug()->getValue();
	const std::vector<float> &channel = channelData->readable();

	bool deep;
	bool flatten;
	bool nearClip;
	float nearClipDepth;
	bool farClip;
	float farClipDepth;

	{
		ImagePlug::GlobalScope s( context );
		deep = inPlug()->deepPlug()->getValue();
		flatten = flattenPlug()->getValue();
		nearClip = nearClipPlug()->enabledPlug()->getValue();
		nearClipDepth = nearClipPlug()->valuePlug<FloatPlug>()->getValue();
		farClip = farClipPlug()->enabledPlug()->getValue();
		farClipDepth = farClipPlug()->valuePlug<FloatPlug>()->getValue();
	}

	if( !flatten && !nearClip && !farClip )
	{
		return inPlug()->channelDataPlug()->getValue();
	}

	if( !deep )
	{
		// If the input is flat, we always make a flat output
		flatten = true;
	}

	ConstCompoundObjectPtr sliceData;
	ConstFloatVectorDataPtr alphaData;

	{
		ImagePlug::ChannelDataScope scope( context );
		scope.remove( ImagePlug::channelNameContextName );
		sliceData = sliceDataPlug()->getValue();

		if(
			flatten && deep &&
			channelName != ImageAlgo::channelNameA &&
			channelName != ImageAlgo::channelNameZ &&
			channelName != ImageAlgo::channelNameZBack
		)
		{
			// If the input is deep, and we're flattening, then we need to take into account the alpha's
			// of samples in front of us when compositing this channel. ( If we're not flattening,
			// then this compositing happens later, and if we're not deep, then nothing can come in front ).
			ConstStringVectorDataPtr channelNamesData = inPlug()->channelNames();
			const std::vector<std::string> &channelNames = channelNamesData->readable();
			if( ImageAlgo::channelExists( channelNames, ImageAlgo::channelNameA ) )
			{
				scope.setChannelName( &ImageAlgo::channelNameA );
				alphaData = tidyInPlug()->channelDataPlug()->getValue();
			}
		}
	}

	const int *sliceDataSampleOffsets = nullptr;
	const int *inputIndices = nullptr;
	const float *firstWeights = nullptr;
	const float *lastWeights = nullptr;

	if( const IntVectorData *sliceDataSampleOffsetsData = sliceData->member<IntVectorData>( g_sampleOffsetsName ) )
	{
		sliceDataSampleOffsets = &sliceDataSampleOffsetsData->readable()[0];
	}
	if( const IntVectorData *inputIndicesData = sliceData->member<IntVectorData>( g_inputIndicesName ) )
	{
		inputIndices = &inputIndicesData->readable()[0];
	}
	if( const FloatVectorData *firstWeightsData = sliceData->member<FloatVectorData>( g_firstWeightsName ) )
	{
		firstWeights = &firstWeightsData->readable()[0];
	}
	if( const FloatVectorData *lastWeightsData = sliceData->member<FloatVectorData>( g_lastWeightsName ) )
	{
		lastWeights = &lastWeightsData->readable()[0];
	}

	FloatVectorDataPtr resultData = new FloatVectorData;
	std::vector<float> &result = resultData->writable();
	if( flatten )
	{
		result.reserve( ImagePlug::tilePixels() );
	}
	else
	{
		result.reserve( sliceDataSampleOffsets[ ImagePlug::tilePixels() - 1 ] );
	}

	if( channelName == ImageAlgo::channelNameZ )
	{
		// Special case for Z - instead of using the weights from sliceDataPlug(), we just apply the
		// nearClipDepth here.
		int prevAccumCount = 0;
		for( int i = 0; i < ImagePlug::tilePixels(); i++ )
		{
			int count = 1;
			if( deep )
			{
				count = sliceDataSampleOffsets[i] - prevAccumCount;
				prevAccumCount = sliceDataSampleOffsets[i];

				if( count == 0 )
				{
					if( flatten )
					{
						result.push_back( 0.0f );
					}
					continue;
				}

				if( flatten )
				{
					count = 1;
				}
			}

			int inputIndex = inputIndices[i];

			int curIndex = inputIndex;
			if( nearClip )
			{
				result.push_back( std::max( channel[inputIndex], nearClipDepth ) );
				curIndex++;
			}

			for( ; curIndex < inputIndex + count; curIndex++ )
			{
				result.push_back( channel[curIndex] );
			}
		}
	}
	else if( channelName == ImageAlgo::channelNameZBack )
	{
		// Special case for Z - instead of using the weights from sliceDataPlug(), we just apply the
		// farClipDepth here.
		int prevAccumCount = 0;
		for( int i = 0; i < ImagePlug::tilePixels(); i++ )
		{
			int inputIndex = inputIndices[i];

			int count = 1;

			if( deep )
			{
				count = sliceDataSampleOffsets[i] - prevAccumCount;
				prevAccumCount = sliceDataSampleOffsets[i];

				if( count == 0 )
				{
					if( flatten )
					{
						result.push_back( 0.0f );
					}
					continue;
				}

				if( !flatten )
				{
					for( int curIndex = inputIndex; curIndex < inputIndex + count - 1; curIndex++ )
					{
						result.push_back( channel[curIndex] );
					}
				}

			}

			if( farClip )
			{
				result.push_back( std::min( channel[inputIndex + count - 1], farClipDepth ) );
			}
			else
			{
				result.push_back( channel[inputIndex + count - 1] );
			}
		}
	}
	else if( flatten && channelName == ImageAlgo::channelNameA )
	{
		// Flattening alpha is a pretty common case, and offers a significant simplification over any other
		// channel when flattening: whenever we flatten, we need to include the occlusion from the alpha of
		// other samples, so we need both the channel and the alpha - but in the case of alpha, we only need
		// one channel.
		int prevAccumCount = 0;
		for( int i = 0; i < ImagePlug::tilePixels(); i++ )
		{
			int inputIndex = inputIndices[i];
			int curIndex = inputIndex;

			// When flattening, the slice data sample offsets are not used as our actual sample offsets
			// ( which are just flat ), but we still use these sample offsets to find which samples
			// to accumulate.
			int count = sliceDataSampleOffsets[i] - prevAccumCount;
			prevAccumCount = sliceDataSampleOffsets[i];

			if( count == 0 )
			{
				result.push_back( 0.0f );
				continue;
			}

			float accumAlpha = 0;

			// If nearClip is set, multiply the first sample by the provided weight, and increment the current
			// output index.
			if( nearClip )
			{
				accumAlpha = channel[inputIndex] * firstWeights[i];
				curIndex++;
			}

			// Process all the samples that weren't output yet, except for the last sample
			for( ; curIndex < inputIndex + count - 1; curIndex++ )
			{
				accumAlpha += channel[curIndex] * ( 1 - accumAlpha );
			}

			// This conditional only fails when there was a single deep sample, and it was output by the near
			// clip ( we build the weights so that the firstWeight will include the far clip as well in this case )
			if( curIndex < inputIndex + count )
			{
				// Process the last sample
				if( farClip )
				{
					accumAlpha += channel[curIndex] * lastWeights[i] * ( 1 - accumAlpha );
				}
				else
				{
					accumAlpha += channel[curIndex] * ( 1 - accumAlpha );
				}
			}
			result.push_back( accumAlpha );
		}
	}
	else if( flatten )
	{
		// Now the more complex general case, where we have both an alpha and a separate channel
		const float* alpha = nullptr;
		if( alphaData )
		{
			alpha = &alphaData->readable()[0];
		}

		int prevAccumCount = 0;
		for( int i = 0; i < ImagePlug::tilePixels(); i++ )
		{
			int inputIndex = inputIndices[i];
			int curIndex = inputIndex;

			// When flattening, the slice data sample offsets are not used as our actual sample offsets
			// ( which are just flat ), but we still use these sample offsets to find which samples
			// to accumulate.
			int count = sliceDataSampleOffsets[i] - prevAccumCount;
			prevAccumCount = sliceDataSampleOffsets[i];

			if( count == 0 )
			{
				result.push_back( 0.0f );
				continue;
			}

			float accumAlpha = 0;
			float accumChannel = 0;

			// If nearClip is set, multiply the first sample by the provided weight, and increment the current
			// output index.
			if( nearClip )
			{
				accumChannel = channel[inputIndex] * firstWeights[i];
				if( alpha )
				{
					accumAlpha = alpha[inputIndex] * firstWeights[i];
				}
				curIndex++;
			}

			// Process all the samples that weren't output yet, except for the last sample
			for( ; curIndex < inputIndex + count - 1; curIndex++ )
			{
				accumChannel += channel[curIndex] * ( 1 - accumAlpha );
				if( alpha )
				{
					accumAlpha += alpha[curIndex] * ( 1 - accumAlpha );
				}
			}

			// This conditional only fails when there was a single deep sample, and it was output by the near
			// clip ( we build the weights so that the firstWeight will include the far clip as well in this case )
			if( curIndex < inputIndex + count )
			{
				// Process the last sample
				if( farClip )
				{
					accumChannel += channel[curIndex] * lastWeights[i] * ( 1 - accumAlpha );
					// We don't care about updating accumAlpha, because we have no more samples to alpha-
					// composite
				}
				else
				{
					accumChannel += channel[curIndex] * ( 1 - accumAlpha );
				}
			}

			result.push_back( accumChannel );
		}
	}
	else
	{
		// Finally, if we're not flattening, then we don't account for alpha occlusion yet. It's basically the
		// same as above, but simpler, and we output separate samples instead of accumulating.
		int prevAccumCount = 0;
		for( int i = 0; i < ImagePlug::tilePixels(); i++ )
		{
			int count = 1;
			int inputIndex = inputIndices[i];
			int curIndex = inputIndex;
			if( deep )
			{
				count = sliceDataSampleOffsets[i] - prevAccumCount;
				prevAccumCount = sliceDataSampleOffsets[i];
				if( count == 0 )
				{
					continue;
				}

				if( nearClip )
				{
					result.push_back( channel[inputIndex] * firstWeights[i] );
					curIndex++;
				}
			}

			for( ; curIndex < inputIndex + count - 1; curIndex++ )
			{
				result.push_back( channel[curIndex] );
			}

			// This conditional only fails when there was a single deep sample, and it was output by the near
			// clip ( we build the weights so that the firstWeight will include the far clip as well in this case )
			if( curIndex < inputIndex + count )
			{
				if( farClip )
				{
					result.push_back( channel[inputIndex + count - 1] * lastWeights[i] );
				}
				else
				{
					result.push_back( channel[inputIndex + count - 1] );
				}
			}
		}
	}

	return resultData;
}

void DeepSlice::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	bool passThrough = false;

	{
		ImagePlug::GlobalScope s( context );
		bool flatten = flattenPlug()->getValue();
		if( flatten || !inPlug()->deepPlug()->getValue() )
		{
			h = ImagePlug::flatTileSampleOffsets()->Object::hash();
			return;
		}
		bool nearClip = nearClipPlug()->enabledPlug()->getValue();
		bool farClip = farClipPlug()->enabledPlug()->getValue();
		if( !flatten && !nearClip && !farClip )
		{
			passThrough = true;
		}
	}

	if( passThrough )
	{
		h = inPlug()->sampleOffsetsPlug()->hash();
		return;
	}

	ImageProcessor::hashSampleOffsets( parent, context, h );


	sliceDataPlug()->hash( h );
}

IECore::ConstIntVectorDataPtr DeepSlice::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{

	bool passThrough = false;

	{
		ImagePlug::GlobalScope s( context );
		bool flatten = flattenPlug()->getValue();
		if( flatten || !inPlug()->deepPlug()->getValue() )
		{
			return ImagePlug::flatTileSampleOffsets();
		}
		bool nearClip = nearClipPlug()->enabledPlug()->getValue();
		bool farClip = farClipPlug()->enabledPlug()->getValue();
		if( !flatten && !nearClip && !farClip )
		{
			passThrough = true;
		}
	}

	if( passThrough )
	{
		return inPlug()->sampleOffsetsPlug()->getValue();
	}

	// Just output the sample offsets computed in the the sliceData
	ConstCompoundObjectPtr sliceData = sliceDataPlug()->getValue();
	return sliceData->member<IntVectorData>( g_sampleOffsetsName );
}

void DeepSlice::hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inPlug()->deepPlug()->hash( h );
	flattenPlug()->hash( h );
}

bool DeepSlice::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	bool deep = inPlug()->deepPlug()->getValue();
	if( flattenPlug()->getValue() )
	{
		deep = false;
	}
	return deep;
}
