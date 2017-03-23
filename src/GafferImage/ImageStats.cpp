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

#include "Gaffer/TypedPlug.h"
#include "Gaffer/BoxPlug.h"
#include "Gaffer/ScriptNode.h"

#include "GafferImage/ImageStats.h"
#include "GafferImage/Sampler.h"
#include "GafferImage/ChannelMaskPlug.h"
#include "GafferImage/FormatPlug.h"
#include "GafferImage/ImageAlgo.h"

using namespace GafferImage;
using namespace Gaffer;

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

IE_CORE_DEFINERUNTIMETYPED( ImageStats );

size_t ImageStats::g_firstPlugIndex = 0;

ImageStats::ImageStats( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "in", Gaffer::Plug::In ) );
	addChild(
		new ChannelMaskPlug(
			"channels",
			Gaffer::Plug::In,
			inPlug()->channelNamesPlug()->defaultValue(),
			Gaffer::Plug::Default
		)
	);
	addChild( new Box2iPlug( "regionOfInterest", Gaffer::Plug::In ) );
	addChild( new Color4fPlug( "average", Gaffer::Plug::Out, Imath::Color4f( 0, 0, 0, 1 ) ) );
	addChild( new Color4fPlug( "min", Gaffer::Plug::Out, Imath::Color4f( 0, 0, 0, 1 ) ) );
	addChild( new Color4fPlug( "max", Gaffer::Plug::Out, Imath::Color4f( 0, 0, 0, 1 ) ) );
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

ChannelMaskPlug *ImageStats::channelsPlug()
{
	return getChild<ChannelMaskPlug>( g_firstPlugIndex + 1 );
}

const ChannelMaskPlug *ImageStats::channelsPlug() const
{
	return getChild<ChannelMaskPlug>( g_firstPlugIndex + 1 );
}

Box2iPlug *ImageStats::regionOfInterestPlug()
{
	return getChild<Box2iPlug>( g_firstPlugIndex + 2 );
}

const Box2iPlug *ImageStats::regionOfInterestPlug() const
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

void ImageStats::parentChanging( Gaffer::GraphComponent *newParent )
{
	ComputeNode::parentChanging( newParent );

	// Set up the default format plug.
	Node *parentNode = IECore::runTimeCast<Node>( newParent );
	if( !parentNode )
	{
		return;
	}

	ScriptNode *scriptNode = parentNode->scriptNode();
	if( scriptNode )
	{
		FormatPlug::acquireDefaultFormatPlug( scriptNode );
	}
}

void ImageStats::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );
	if(
		input == inPlug()->dataWindowPlug() ||
		input == inPlug()->channelNamesPlug() ||
		input == inPlug()->channelDataPlug() ||
		input == channelsPlug() ||
		regionOfInterestPlug()->isAncestorOf( input )
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
	const Imath::Box2i regionOfInterest = regionOfInterestPlug()->getValue();

	if( channelName.empty() || BufferAlgo::empty( regionOfInterest ) )
	{
		h.append( static_cast<const FloatPlug *>( output )->defaultValue() );
		return;
	}

	Sampler s( inPlug(), channelName, regionOfInterest );
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
	const Imath::Box2i regionOfInterest = regionOfInterestPlug()->getValue();

	if( channelName.empty() || BufferAlgo::empty( regionOfInterest ) )
	{
		output->setToDefault();
		return;
	}

	// Loop over the ROI and compute the min, max and average channel values and then set our outputs.
	Sampler s( inPlug(), channelName, regionOfInterest );

	float min = Imath::limits<float>::max();
	float max = Imath::limits<float>::min();
	double sum = 0.;

	for( int y = regionOfInterest.min.y; y < regionOfInterest.max.y; ++y )
	{
		for( int x = regionOfInterest.min.x; x < regionOfInterest.max.x; ++x )
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
			sum / double( (regionOfInterest.size().x) * (regionOfInterest.size().y) )
		);
	}
}

std::string ImageStats::channelName( int colorIndex ) const
{
	IECore::ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
	std::vector<std::string> maskChannels = channelNamesData->readable();
	channelsPlug()->maskChannels( maskChannels );

	/// As the channelMaskPlug allows any combination of channels to be input we need to make sure that
	/// the channels that it masks each have a distinct channelIndex. Otherwise multiple channels would be
	/// outputting to the same plug.
	std::vector<std::string> uniqueChannels = maskChannels;
	GafferImage::ChannelMaskPlug::removeDuplicateIndices( uniqueChannels );

	for( std::vector<std::string>::iterator it( uniqueChannels.begin() ); it != uniqueChannels.end(); ++it )
	{
		if( ImageAlgo::colorIndex( *it ) == colorIndex )
		{
			return *it;
		}
	}
	return "";
}
