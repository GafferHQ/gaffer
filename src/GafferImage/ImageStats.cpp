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

#include "GafferImage/ImageStats.h"

#include "GafferImage/FormatPlug.h"
#include "GafferImage/ImageAlgo.h"
#include "GafferImage/Sampler.h"

#include "Gaffer/BoxPlug.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/TypedPlug.h"

using namespace std;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

int colorIndex( const ValuePlug *plug )
{
	const Color4fPlug *colorPlug = plug->parent<Color4fPlug>();
	if( !colorPlug )
	{
		return -1;
	}
	for( size_t i = 0; i < 4; ++i )
	{
		if( plug == colorPlug->getChild( i ) )
		{
			return i;
		}
	}
	return -1;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// ImageStats
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( ImageStats );

size_t ImageStats::g_firstPlugIndex = 0;

ImageStats::ImageStats( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "in", Gaffer::Plug::In ) );

	IECore::StringVectorDataPtr defaultChannelsData = new IECore::StringVectorData;
	vector<string> &defaultChannels = defaultChannelsData->writable();
	defaultChannels.push_back( "R" );
	defaultChannels.push_back( "G" );
	defaultChannels.push_back( "B" );
	defaultChannels.push_back( "A" );
	addChild( new StringVectorDataPlug( "channels", Plug::In, defaultChannelsData ) );

	addChild( new Box2iPlug( "area", Gaffer::Plug::In ) );
	addChild( new Color4fPlug( "average", Gaffer::Plug::Out, Imath::Color4f( 0, 0, 0, 1 ) ) );
	addChild( new Color4fPlug( "min", Gaffer::Plug::Out, Imath::Color4f( 0, 0, 0, 1 ) ) );
	addChild( new Color4fPlug( "max", Gaffer::Plug::Out, Imath::Color4f( 0, 0, 0, 1 ) ) );

	addChild( new ImagePlug( "__flattenedIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );

	DeepStatePtr deepStateNode = new DeepState( "__deepState" );
	addChild( deepStateNode );

	deepStateNode->inPlug()->setInput( inPlug() );
	deepStateNode->deepStatePlug()->setValue( int( DeepState::TargetState::Flat ) );
	flattenedInPlug()->setInput( deepStateNode->outPlug() );
}

ImageStats::~ImageStats()
{
}

ImagePlug *ImageStats::inPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const ImagePlug *ImageStats::inPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

Gaffer::StringVectorDataPlug *ImageStats::channelsPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringVectorDataPlug *ImageStats::channelsPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 1 );
}

Box2iPlug *ImageStats::areaPlug()
{
	return getChild<Box2iPlug>( g_firstPlugIndex + 2 );
}

const Box2iPlug *ImageStats::areaPlug() const
{
	return getChild<Box2iPlug>( g_firstPlugIndex + 2 );
}

Color4fPlug *ImageStats::averagePlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 3 );
}

const Color4fPlug *ImageStats::averagePlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 3 );
}

Color4fPlug *ImageStats::minPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 4 );
}

const Color4fPlug *ImageStats::minPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 4 );
}

Color4fPlug *ImageStats::maxPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 5 );
}

const Color4fPlug *ImageStats::maxPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 5 );
}

ImagePlug *ImageStats::flattenedInPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex + 6 );
}

const ImagePlug *ImageStats::flattenedInPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex + 6 );
}

DeepState *ImageStats::deepState()
{
	return getChild<DeepState>( g_firstPlugIndex + 4 );
}

const DeepState *ImageStats::deepState() const
{
	return getChild<DeepState>( g_firstPlugIndex + 4 );
}

void ImageStats::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );
	if(
		input == flattenedInPlug()->dataWindowPlug() ||
		input == flattenedInPlug()->channelNamesPlug() ||
		input == flattenedInPlug()->channelDataPlug() ||
		input == channelsPlug() ||
		areaPlug()->isAncestorOf( input )
	)
	{
		for( unsigned int i = 0; i < 4; ++i )
		{
			outputs.push_back( minPlug()->getChild(i) );
			outputs.push_back( averagePlug()->getChild(i) );
			outputs.push_back( maxPlug()->getChild(i) );
		}
		return;
	}
}

void ImageStats::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h);

	const int colorIndex = ::colorIndex( output );
	if( colorIndex == -1 )
	{
		// Not a plug we know about
		return;
	}

	const std::string channelName = this->channelName( colorIndex );
	const Imath::Box2i area = areaPlug()->getValue();

	if( channelName.empty() || BufferAlgo::empty( area ) )
	{
		h.append( static_cast<const FloatPlug *>( output )->defaultValue() );
		return;
	}

	Sampler s( inPlug(), channelName, area );
	s.hash( h );
}

void ImageStats::compute( ValuePlug *output, const Context *context ) const
{
	const int colorIndex = ::colorIndex( output );
	if( colorIndex == -1 )
	{
		// Not a plug we know about
		ComputeNode::compute( output, context );
		return;
	}

	const std::string channelName = this->channelName( colorIndex );
	const Imath::Box2i area = areaPlug()->getValue();

	if( channelName.empty() || BufferAlgo::empty( area ) )
	{
		output->setToDefault();
		return;
	}

	// Loop over the ROI and compute the min, max and average channel values and then set our outputs.
	Sampler s( inPlug(), channelName, area );

	float min = Imath::limits<float>::max();
	float max = Imath::limits<float>::min();
	double sum = 0.;

	for( int y = area.min.y; y < area.max.y; ++y )
	{
		for( int x = area.min.x; x < area.max.x; ++x )
		{
			float v = s.sample( x, y );
			min = std::min( v, min );
			max = std::max( v, max );
			sum += v;
		}
	}

	if( output->parent<Plug>() == minPlug() )
	{
		static_cast<FloatPlug *>( output )->setValue( min );
	}
	else if( output->parent<Plug>() == maxPlug() )
	{
		static_cast<FloatPlug *>( output )->setValue( max );
	}
	else if( output->parent<Plug>() == averagePlug() )
	{
		static_cast<FloatPlug *>( output )->setValue(
			sum / double( (area.size().x) * (area.size().y) )
		);
	}
}

std::string ImageStats::channelName( int colorIndex ) const
{
	IECore::ConstStringVectorDataPtr channelsData = channelsPlug()->getValue();
	const vector<string> &channels = channelsData->readable();
	if( channels.size() <= (size_t)colorIndex )
	{
		return "";
	}

	IECore::ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
	const vector<string> &channelNames = channelNamesData->readable();
	if( find( channelNames.begin(), channelNames.end(), channels[colorIndex] ) != channelNames.end() )
	{
		return channels[colorIndex];
	}

	return "";
}
