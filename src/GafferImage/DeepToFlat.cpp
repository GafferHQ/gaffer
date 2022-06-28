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

#include "GafferImage/DeepToFlat.h"

#include "GafferImage/ImageAlgo.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"

#include "IECore/BoxOps.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

namespace
{
	std::string g_premultipliedAverageZName( "__premultipliedAverageZ" );
}


GAFFER_NODE_DEFINE_TYPE( DeepToFlat );

size_t DeepToFlat::g_firstPlugIndex = 0;

DeepToFlat::DeepToFlat( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "depthMode", Gaffer::Plug::In, int( DepthMode::Filtered ) ) );

	addChild( new FloatVectorDataPlug( "__intermediateChannelData", Gaffer::Plug::Out, ImagePlug::blackTile(), Plug::Default & ~Plug::Serialisable ) );
	addChild( new FloatVectorDataPlug( "__flattenedChannelData", Gaffer::Plug::Out, ImagePlug::blackTile(), Plug::Default & ~Plug::Serialisable ) );

	addChild( new DeepState() );

	deepState()->deepStatePlug()->setValue( int( DeepState::TargetState::Flat ) );
	deepState()->inPlug()->setInput( inPlug() );
	deepState()->inPlug()->channelDataPlug()->setInput( intermediateChannelDataPlug() );

	flattenedChannelDataPlug()->setInput( deepState()->outPlug()->channelDataPlug() );

	// We don't ever want to change these, so we make pass-through connections.
	outPlug()->viewNamesPlug()->setInput( inPlug()->viewNamesPlug() );
	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
}

DeepToFlat::~DeepToFlat()
{
}

Gaffer::IntPlug *DeepToFlat::depthModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *DeepToFlat::depthModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::FloatVectorDataPlug *DeepToFlat::intermediateChannelDataPlug()
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex+1 );
}

const Gaffer::FloatVectorDataPlug *DeepToFlat::intermediateChannelDataPlug() const
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex+1 );
}

Gaffer::FloatVectorDataPlug *DeepToFlat::flattenedChannelDataPlug()
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex+2 );
}

const Gaffer::FloatVectorDataPlug *DeepToFlat::flattenedChannelDataPlug() const
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex+2 );
}

GafferImage::DeepState *DeepToFlat::deepState()
{
	return getChild<DeepState>( g_firstPlugIndex+3 );
}

const GafferImage::DeepState *DeepToFlat::deepState() const
{
	return getChild<DeepState>( g_firstPlugIndex+3 );
}

void DeepToFlat::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( input == inPlug()->channelDataPlug() )
	{
		outputs.push_back( intermediateChannelDataPlug() );
	}
	else if( input == flattenedChannelDataPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if( input == depthModePlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
		outputs.push_back( outPlug()->channelNamesPlug() );
	}
	else if( input == inPlug()->channelNamesPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
		outputs.push_back( outPlug()->channelNamesPlug() );
	}
}

void DeepToFlat::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hash( output, context, h );

	if( output != intermediateChannelDataPlug() )
	{
		return;
	}

	const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	if( channelName == g_premultipliedAverageZName )
	{
		ImagePlug::ChannelDataScope channelScope( context );
		channelScope.setChannelName( &ImageAlgo::channelNameZ );
		inPlug()->channelDataPlug()->hash( h );

		ConstStringVectorDataPtr channelNames = inPlug()->channelNames();
		if( ImageAlgo::channelExists( channelNames->readable(), ImageAlgo::channelNameZBack ) )
		{
			channelScope.setChannelName( &ImageAlgo::channelNameZBack );
			inPlug()->channelDataPlug()->hash( h );
		}
		if( ImageAlgo::channelExists( channelNames->readable(), ImageAlgo::channelNameA ) )
		{
			channelScope.setChannelName( &ImageAlgo::channelNameA );
			inPlug()->channelDataPlug()->hash( h );
		}
	}
	else
	{
		h = inPlug()->channelDataPlug()->hash();
	}
}

void DeepToFlat::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	ImageProcessor::compute( output, context );

	if( output != intermediateChannelDataPlug() )
	{
		return;
	}

	const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	if( channelName == g_premultipliedAverageZName )
	{
		ImagePlug::ChannelDataScope channelScope( context );
		channelScope.setChannelName( &ImageAlgo::channelNameZ );

		FloatVectorDataPtr resultData = inPlug()->channelDataPlug()->getValue()->copy();
		std::vector<float> &result = resultData->writable();

		ConstStringVectorDataPtr channelNames = inPlug()->channelNames();
		if( ImageAlgo::channelExists( channelNames->readable(), ImageAlgo::channelNameZBack ) )
		{
			// If we have a ZBack channel, find the average depth of each sample
			channelScope.setChannelName( &ImageAlgo::channelNameZBack );
			ConstFloatVectorDataPtr zBackData = inPlug()->channelDataPlug()->getValue();
			const std::vector<float> &zBack = zBackData->readable();
			for( unsigned int i = 0; i < result.size(); i++ )
			{
				result[i] = result[i] * 0.5f + zBack[i] * 0.5f;
			}
		}
		if( ImageAlgo::channelExists( channelNames->readable(), "A" ) )
		{
			channelScope.setChannelName( &ImageAlgo::channelNameA );
			ConstFloatVectorDataPtr alphaData = inPlug()->channelDataPlug()->getValue();
			const std::vector<float> &alpha = alphaData->readable();
			for( unsigned int i = 0; i < result.size(); i++ )
			{
				result[i] *= alpha[i];
			}
		}
		static_cast<FloatVectorDataPlug *>( output )->setValue( resultData );
	}
	else
	{
		static_cast<FloatVectorDataPlug *>( output )->setValue( inPlug()->channelDataPlug()->getValue() );
	}
}

void DeepToFlat::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelNames( output, context, h );
	inPlug()->channelNamesPlug()->hash( h );
	depthModePlug()->hash( h );
}

IECore::ConstStringVectorDataPtr DeepToFlat::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	DepthMode depthMode = DepthMode( depthModePlug()->getValue() );

	ConstStringVectorDataPtr inChannelNamesData = inPlug()->channelNamesPlug()->getValue();
	if( depthMode == DepthMode::Range )
	{
		return inChannelNamesData;
	}

	StringVectorDataPtr resultData = new StringVectorData();
	std::vector<string> &result = resultData->writable();
	result.reserve( inChannelNamesData->readable().size() );
	for( const std::string &n : inChannelNamesData->readable() )
	{
		if( n[0] == 'Z' )
		{
			if(
				( ( depthMode == DepthMode::None || depthMode == DepthMode::Filtered ) && n == "ZBack" ) ||
				( ( depthMode == DepthMode::None ) && n == "Z" )
			)
			{
				continue;
			}
		}
		result.push_back( n );
	}
	return resultData;
}

void DeepToFlat::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	bool needsProcessing = false;

	const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	if( channelName == "Z" )
	{
		if( DepthMode( depthModePlug()->getValue() ) == DepthMode::Filtered )
		{
			needsProcessing = true;
		}
	}

	if( !needsProcessing )
	{
		h = flattenedChannelDataPlug()->hash();
		return;
	}

	ImageProcessor::hashChannelData( output, context, h );

	ImagePlug::ChannelDataScope channelScope( context );
	channelScope.setChannelName( &g_premultipliedAverageZName );

	flattenedChannelDataPlug()->hash( h );
}

IECore::ConstFloatVectorDataPtr DeepToFlat::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	bool needsProcessing = false;

	if( channelName == "Z" )
	{
		if( DepthMode( depthModePlug()->getValue() ) == DepthMode::Filtered )
		{
			needsProcessing = true;
		}
	}

	if( !needsProcessing )
	{
		return flattenedChannelDataPlug()->getValue();
	}

	ImagePlug::ChannelDataScope channelScope( context );

	// In general, it is not valid to query channel data for a channel which is not in the channelNames.
	// But in this case, we know that the internal DeepState node will just do the filtering of whatever
	// it gets by querying this channel from its input channelData, and that will just hit our
	// intermediateChannelData plug, which has a special case to handle this
	channelScope.setChannelName( &g_premultipliedAverageZName );
	FloatVectorDataPtr resultData = flattenedChannelDataPlug()->getValue()->copy();
	std::vector<float> &result = resultData->writable();

	ConstStringVectorDataPtr channelNames = inPlug()->channelNames();
	if( ImageAlgo::channelExists( channelNames->readable(), "A" ) )
	{
		// For consistency with other uses of Z, once we've got a properly filtered and merged Z,
		// we can unpremult it again
		channelScope.setChannelName( &ImageAlgo::channelNameA );
		ConstFloatVectorDataPtr alphaData = flattenedChannelDataPlug()->getValue();
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

bool DeepToFlat::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return false;
}

void DeepToFlat::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = ImagePlug::flatTileSampleOffsets()->Object::hash();
}

IECore::ConstIntVectorDataPtr DeepToFlat::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::flatTileSampleOffsets();
}
