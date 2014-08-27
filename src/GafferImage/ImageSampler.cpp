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
#include "GafferImage/FilterPlug.h"
#include "GafferImage/Sampler.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

IE_CORE_DEFINERUNTIMETYPED( ImageSampler );

size_t ImageSampler::g_firstPlugIndex = 0;

ImageSampler::ImageSampler( const std::string &name )
	:	ComputeNode( name )
{

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ImagePlug( "image" ) );
	addChild( new V2fPlug( "pixel" ) );
	addChild( new FilterPlug( "filter" ) );
	addChild( new Color4fPlug( "color", Plug::Out ) );

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

Gaffer::V2fPlug *ImageSampler::pixelPlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::V2fPlug *ImageSampler::pixelPlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 1 );
}

FilterPlug *ImageSampler::filterPlug()
{
	return getChild<FilterPlug>( g_firstPlugIndex + 2 );
}

const FilterPlug *ImageSampler::filterPlug() const
{
	return getChild<FilterPlug>( g_firstPlugIndex + 2 );
}

Gaffer::Color4fPlug *ImageSampler::colorPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::Color4fPlug *ImageSampler::colorPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 3 );
}

void ImageSampler::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	const Gaffer::Plug *inputParent = input->parent<Plug>();
	if( inputParent == imagePlug() || inputParent == pixelPlug() || input == filterPlug() )
	{
		for( ValuePlugIterator componentIt( colorPlug() ); componentIt != componentIt.end(); ++componentIt )
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
		std::string channel = channelName( output );
		if( channel.size() )
		{
			V2f pixel = pixelPlug()->getValue();
			Box2i sampleWindow;
			sampleWindow.extendBy( V2i( pixel ) - V2i( 1 ) );
			sampleWindow.extendBy( V2i( pixel ) + V2i( 1 ) );
			const string filter = filterPlug()->getValue();
			Sampler sampler( imagePlug(), channel, sampleWindow, Filter::create( filter ) );

			sampler.hash( h );
			h.append( pixel );
			h.append( filter );
		}
	}
}

void ImageSampler::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output->parent<Plug>() == colorPlug() )
	{
		float sample = 0;

		std::string channel = channelName( output );
		if( channel.size() )
		{
			V2f pixel = pixelPlug()->getValue();
			Box2i sampleWindow;
			sampleWindow.extendBy( V2i( pixel ) - V2i( 1 ) );
			sampleWindow.extendBy( V2i( pixel ) + V2i( 1 ) );
			Sampler sampler( imagePlug(), channel, sampleWindow, Filter::create( filterPlug()->getValue() ) );
			sample = sampler.sample( pixel.x, pixel.y );
		}

		static_cast<FloatPlug *>( output )->setValue( sample );
		return;
	}

	ComputeNode::compute( output, context );
}

std::string ImageSampler::channelName( const Gaffer::ValuePlug *output ) const
{
	std::string name;

	const Color4fPlug *c = colorPlug();
	if( output == c->getChild( 0 ) )
	{
		name = "R";
	}
	else if( output == c->getChild( 1 ) )
	{
		name = "G";
	}
	else if( output == c->getChild( 2 ) )
	{
		name = "B";
	}
	else if( output == c->getChild( 3 ) )
	{
		name = "A";
	}

	ConstStringVectorDataPtr channelNames = imagePlug()->channelNamesPlug()->getValue();
	if( find( channelNames->readable().begin(), channelNames->readable().end(), name ) != channelNames->readable().end() )
	{
		return name;
	}

	return "";
}
