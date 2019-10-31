//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/DeepHoldout.h"

#include "GafferImage/ImageAlgo.h"
#include "GafferImage/DeepMerge.h"
#include "GafferImage/DeepState.h"
#include "GafferImage/DeleteChannels.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"


using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( DeepHoldout );

size_t DeepHoldout::g_firstPlugIndex = 0;

DeepHoldout::DeepHoldout( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new GafferImage::ImagePlug( "holdout" ) );
	addChild( new GafferImage::ImagePlug( "__intermediateIn", Plug::Out ) );
	addChild( new GafferImage::ImagePlug( "__flattened" ) );

	DeleteChannelsPtr deleteHoldoutChannels = new GafferImage::DeleteChannels( "__deleteHoldoutChannels" );
	addChild( deleteHoldoutChannels );
	deleteHoldoutChannels->inPlug()->setInput( holdoutPlug() );
	deleteHoldoutChannels->modePlug()->setValue( DeleteChannels::Keep );
	deleteHoldoutChannels->channelsPlug()->setValue( "A Z ZBack" );

	DeepMergePtr mergeHoldout = new GafferImage::DeepMerge( "__mergeHoldout" );
	addChild( mergeHoldout );
	mergeHoldout->inPlugs()->getChild<ImagePlug>( 0 )->setInput( intermediateInPlug() );
	mergeHoldout->inPlugs()->getChild<ImagePlug>( 1 )->setInput( deleteHoldoutChannels->outPlug() );

	DeepStatePtr flatten = new GafferImage::DeepState( "__flatten" );
	addChild( flatten );
	flatten->inPlug()->setInput( mergeHoldout->outPlug() );
	flatten->deepStatePlug()->setValue( int( DeepState::TargetState::Flat ) );

	flattenedPlug()->setInput( flatten->outPlug() );

	// The intermediate inPlug is mostly just connected through to the input
	intermediateInPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	intermediateInPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	intermediateInPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	intermediateInPlug()->deepPlug()->setInput( inPlug()->deepPlug() );
	intermediateInPlug()->sampleOffsetsPlug()->setInput( inPlug()->sampleOffsetsPlug() );

	// We don't ever want to change these, so we make pass-through connections.
	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
}

DeepHoldout::~DeepHoldout()
{
}

GafferImage::ImagePlug *DeepHoldout::holdoutPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const GafferImage::ImagePlug *DeepHoldout::holdoutPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

GafferImage::ImagePlug *DeepHoldout::intermediateInPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex + 1 );
}

const GafferImage::ImagePlug *DeepHoldout::intermediateInPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex + 1 );
}

GafferImage::ImagePlug *DeepHoldout::flattenedPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex + 2 );
}

const GafferImage::ImagePlug *DeepHoldout::flattenedPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex + 2 );
}

void DeepHoldout::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( input == inPlug()->channelDataPlug() || input == inPlug()->channelNamesPlug() )
	{
		outputs.push_back( intermediateInPlug()->channelDataPlug() );
	}

	if( input == inPlug()->channelNamesPlug() )
	{
		outputs.push_back( intermediateInPlug()->channelNamesPlug() );
	}

	if( input == flattenedPlug()->channelDataPlug() || input == inPlug()->channelNamesPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void DeepHoldout::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelNames( output, context, h );
	h.append( output == intermediateInPlug() );
	inPlug()->channelNamesPlug()->hash( h );
}

IECore::ConstStringVectorDataPtr DeepHoldout::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstStringVectorDataPtr inChannelNamesData = inPlug()->channelNamesPlug()->getValue();

	if( parent == intermediateInPlug() )
	{
		StringVectorDataPtr resultData = inChannelNamesData->copy();
		std::vector<string> &result = resultData->writable();
		result.reserve( result.size() + 2 );
		result.push_back( "__premultipliedAverageZ" );
		result.push_back( "__holdoutAlpha" );
		return resultData;
	}
	else
	{
		StringVectorDataPtr resultData = new StringVectorData();
		std::vector<string> &result = resultData->writable();
		result.reserve( inChannelNamesData->readable().size() );
		for( const std::string &n : inChannelNamesData->readable() )
		{
			if( n == "ZBack" )
			{
				continue;
			}
			result.push_back( n );
		}
		return resultData;
	}
}


void DeepHoldout::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == intermediateInPlug() )
	{
		const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );
		if( channelName == "__premultipliedAverageZ" )
		{
			ImageProcessor::hashChannelData( output, context, h );

			ImagePlug::ChannelDataScope channelScope( context );
			channelScope.setChannelName( "Z" );
			inPlug()->channelDataPlug()->hash( h );

			ConstStringVectorDataPtr channelNames = inPlug()->channelNames();
			if( ImageAlgo::channelExists( channelNames->readable(), "ZBack" ) )
			{
				channelScope.setChannelName( "ZBack" );
				inPlug()->channelDataPlug()->hash( h );
			}
			if( ImageAlgo::channelExists( channelNames->readable(), "A" ) )
			{
				channelScope.setChannelName( "A" );
				inPlug()->channelDataPlug()->hash( h );
			}
		}
		else
		{
			h = inPlug()->channelDataPlug()->hash();
		}
	}
	else
	{
		const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );
		if( !( channelName == "A" || channelName == "Z" ) )
		{
			h = flattenedPlug()->channelDataPlug()->hash();
			return;
		}

		ImageProcessor::hashChannelData( output, context, h );

		ImagePlug::ChannelDataScope channelScope( context );
		if( channelName == "A" )
		{
			channelScope.setChannelName( "__holdoutAlpha" );
			flattenedPlug()->channelDataPlug()->hash( h );
		}
		else if( channelName == "Z" )
		{
			channelScope.setChannelName( "A" );
			outPlug()->channelDataPlug()->hash( h );
			channelScope.setChannelName( "__premultipliedAverageZ" );
			flattenedPlug()->channelDataPlug()->hash( h );
		}
	}
}

IECore::ConstFloatVectorDataPtr DeepHoldout::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	if( parent == intermediateInPlug() )
	{
		const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );
		if( channelName == "__premultipliedAverageZ" )
		{
			ImagePlug::ChannelDataScope channelScope( context );
			channelScope.setChannelName( "Z" );

			FloatVectorDataPtr resultData = inPlug()->channelDataPlug()->getValue()->copy();
			std::vector<float> &result = resultData->writable();

			ConstStringVectorDataPtr channelNames = inPlug()->channelNames();
			if( ImageAlgo::channelExists( channelNames->readable(), "ZBack" ) )
			{
				// If we have a ZBack channel, find the average depth of each sample
				channelScope.setChannelName( "ZBack" );
				ConstFloatVectorDataPtr zBackData = inPlug()->channelDataPlug()->getValue();
				const std::vector<float> &zBack = zBackData->readable();
				for( unsigned int i = 0; i < result.size(); i++ )
				{
					result[i] = result[i] * 0.5f + zBack[i] * 0.5f;
				}
			}
			if( ImageAlgo::channelExists( channelNames->readable(), "A" ) )
			{
				channelScope.setChannelName( "A" );
				ConstFloatVectorDataPtr alphaData = inPlug()->channelDataPlug()->getValue();
				const std::vector<float> &alpha = alphaData->readable();
				for( unsigned int i = 0; i < result.size(); i++ )
				{
					result[i] *= alpha[i];
				}
			}
			return resultData;
		}
		else if( channelName == "__holdoutAlpha" )
		{
			ImagePlug::ChannelDataScope channelScope( context );
			channelScope.setChannelName( "A" );
			return inPlug()->channelDataPlug()->getValue();
		}
		else
		{
			return inPlug()->channelDataPlug()->getValue();
		}
	}
	else
	{
		if( !( channelName == "A" || channelName == "Z" ) )
		{
			return flattenedPlug()->channelDataPlug()->getValue();
		}

		ImagePlug::ChannelDataScope channelScope( context );

		if( channelName == "A" )
		{
			channelScope.setChannelName( "__holdoutAlpha" );
			return flattenedPlug()->channelDataPlug()->getValue();
		}

		channelScope.setChannelName( "__premultipliedAverageZ" );
		FloatVectorDataPtr resultData = flattenedPlug()->channelDataPlug()->getValue()->copy();
		std::vector<float> &result = resultData->writable();

		ConstStringVectorDataPtr channelNames = inPlug()->channelNames();
		if( ImageAlgo::channelExists( channelNames->readable(), "A" ) )
		{
			// For consistency with other uses of Z, once we've got a properly filtered and merged Z,
			// we can unpremult it again
			channelScope.setChannelName( "A" );
			ConstFloatVectorDataPtr alphaData = outPlug()->channelDataPlug()->getValue();
			const std::vector<float> &alpha = alphaData->readable();
			for( unsigned int i = 0; i < result.size(); i++ )
			{
				if( alpha[i] != 0.0f )
				{
					result[i] /= alpha[i];
				}
			}
		}
		return resultData;
	}
}

bool DeepHoldout::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return false;
}

void DeepHoldout::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = ImagePlug::flatTileSampleOffsets()->Object::hash();
}

IECore::ConstIntVectorDataPtr DeepHoldout::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::flatTileSampleOffsets();
}

