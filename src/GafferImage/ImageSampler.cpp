//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/ImageSampler.h"

#include "GafferImage/ImagePlug.h"
#include "GafferImage/Sampler.h"

#include <limits>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( ImageSampler );

size_t ImageSampler::g_firstPlugIndex = 0;

ImageSampler::ImageSampler( const std::string &name )
	:	ComputeNode( name )
{

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ImagePlug( "image" ) );
	addChild( new StringPlug( "view", Plug::In, "default" ) );

	IECore::StringVectorDataPtr defaultChannelsData = new IECore::StringVectorData;
	vector<string> &defaultChannels = defaultChannelsData->writable();
	defaultChannels.push_back( "R" );
	defaultChannels.push_back( "G" );
	defaultChannels.push_back( "B" );
	defaultChannels.push_back( "A" );
	addChild( new StringVectorDataPlug( "channels", Plug::In, defaultChannelsData ) );

	addChild( new V2fPlug( "pixel" ) );
	addChild( new Color4fPlug("color", Plug::Out, Imath::Color4f( 0.0f ),
		// Override the standard limits on FloatPlug - if there is an inf value in the image,
		// ImageSampler should be able to report that
		Imath::Color4f( -std::numeric_limits<float>::infinity() ), Imath::Color4f( std::numeric_limits<float>::infinity() )
	) );

	addChild( new ImagePlug( "__flattenedIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );

	DeepStatePtr deepStateNode = new DeepState( "__deepState" );
	addChild( deepStateNode );

	deepStateNode->inPlug()->setInput( imagePlug() );
	deepStateNode->deepStatePlug()->setValue( int( DeepState::TargetState::Flat ) );
	flattenedInPlug()->setInput( deepStateNode->outPlug() );
}

ImageSampler::~ImageSampler()
{
}

ImagePlug *ImageSampler::imagePlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const ImagePlug *ImageSampler::imagePlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *ImageSampler::viewPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *ImageSampler::viewPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringVectorDataPlug *ImageSampler::channelsPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringVectorDataPlug *ImageSampler::channelsPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 2 );
}

Gaffer::V2fPlug *ImageSampler::pixelPlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::V2fPlug *ImageSampler::pixelPlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 3 );
}

Gaffer::Color4fPlug *ImageSampler::colorPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::Color4fPlug *ImageSampler::colorPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 4 );
}

ImagePlug *ImageSampler::flattenedInPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex + 5 );
}

const ImagePlug *ImageSampler::flattenedInPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex + 5 );
}

DeepState *ImageSampler::deepState()
{
	return getChild<DeepState>( g_firstPlugIndex + 6 );
}

const DeepState *ImageSampler::deepState() const
{
	return getChild<DeepState>( g_firstPlugIndex + 6 );
}

void ImageSampler::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if(
		input == flattenedInPlug()->viewNamesPlug() ||
		input == flattenedInPlug()->dataWindowPlug() ||
		input == flattenedInPlug()->channelDataPlug() ||
		input == flattenedInPlug()->channelNamesPlug() ||
		input == viewPlug() ||
		input == channelsPlug() ||
		input->parent<Plug>() == pixelPlug()
	)
	{
		for( ValuePlug::Iterator componentIt( colorPlug() ); !componentIt.done(); ++componentIt )
		{
			outputs.push_back( componentIt->get() );
		}
	}
}

void ImageSampler::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );

	if( output->parent<Plug>() == colorPlug() )
	{
		ImagePlug::ViewScope viewScope( context );

		std::string view = viewPlug()->getValue();
		if( !view.size() )
		{
			view = context->get<std::string>( ImagePlug::viewNameContextName, ImagePlug::defaultViewName );
		}
		viewScope.setViewNameChecked( &view, flattenedInPlug()->viewNames().get() );

		std::string channel = channelName( output );
		if( channel.size() )
		{
			V2f pixel = pixelPlug()->getValue();
			V2i intPixel( floorf( pixel.x ), floorf( pixel.y ) );
			Box2i sampleWindow( intPixel, intPixel + V2i( 1 ) );
			Sampler sampler( flattenedInPlug(), channel, sampleWindow );

			sampler.hash( h );
			h.append( pixel );
		}
	}
}

void ImageSampler::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output->parent<Plug>() == colorPlug() )
	{
		ImagePlug::ViewScope viewScope( context );

		std::string view = viewPlug()->getValue();
		if( !view.size() )
		{
			view = context->get<std::string>( ImagePlug::viewNameContextName, ImagePlug::defaultViewName );
		}
		viewScope.setViewNameChecked( &view, flattenedInPlug()->viewNames().get() );

		float sample = 0;

		std::string channel = channelName( output );
		if( channel.size() )
		{
			V2f pixel = pixelPlug()->getValue();
			V2i intPixel( floorf( pixel.x ), floorf( pixel.y ) );
			Box2i sampleWindow( intPixel, intPixel + V2i( 1 ) );
			Sampler sampler( flattenedInPlug(), channel, sampleWindow );
			sample = sampler.sample( pixel.x, pixel.y );
		}

		static_cast<FloatPlug *>( output )->setValue( sample );
		return;
	}

	ComputeNode::compute( output, context );
}

std::string ImageSampler::channelName( const Gaffer::ValuePlug *output ) const
{
	size_t index = 0;
	const Color4fPlug *c = colorPlug();
	for( size_t i = 0; i < 4; ++i )
	{
		if( output == c->getChild( i ) )
		{
			index = i;
			break;
		}
	}

	ConstStringVectorDataPtr channelsData = channelsPlug()->getValue();
	const vector<string> &channels = channelsData->readable();
	if( channels.size() <= index )
	{
		return "";
	}

	ConstStringVectorDataPtr channelNamesData = flattenedInPlug()->channelNamesPlug()->getValue();
	const vector<string> &channelNames = channelNamesData->readable();
	if( find( channelNames.begin(), channelNames.end(), channels[index] ) != channelNames.end() )
	{
		return channels[index];
	}

	return "";
}
