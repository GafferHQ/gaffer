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

#include "boost/bind.hpp"

#include "Gaffer/TypedPlug.h"
#include "Gaffer/BoxPlug.h"
#include "Gaffer/Context.h"
#include "Gaffer/ScriptNode.h"

#include "GafferImage/ImageStats.h"
#include "GafferImage/Sampler.h"
#include "GafferImage/ChannelMaskPlug.h"
#include "GafferImage/Format.h"

using namespace GafferImage;
using namespace Gaffer;

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
	addChild( new Color4fPlug( "average", Gaffer::Plug::Out ) );
	addChild( new Color4fPlug( "min", Gaffer::Plug::Out ) );
	addChild( new Color4fPlug( "max", Gaffer::Plug::Out ) );
	plugInputChangedSignal().connect( boost::bind( &ImageStats::inputChanged, this, ::_1 ) );
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

void ImageStats::inputChanged( Gaffer::Plug *plug )
{
	const Imath::Box2i regionOfInterest( regionOfInterestPlug()->getValue() );
	if( plug->isInstanceOf( ImagePlug::staticTypeId() ) && regionOfInterest.isEmpty() )
	{
		Imath::Box2i box( inPlug()->formatPlug()->getValue().getDisplayWindow() );
		if( box.isEmpty() )
		{
			Gaffer::ScriptNode *s( scriptNode() );
			if( s )
			{
				box = GafferImage::Format::getDefaultFormat( s ).getDisplayWindow();
			}
		}
		regionOfInterestPlug()->setValue( box );
	}
}

void ImageStats::parentChanging( Gaffer::GraphComponent *newParent )
{
	// Initialise the default format and setup any format knobs that are on this node.
	if( newParent )
	{
		if ( static_cast<Gaffer::TypeId>(newParent->typeId()) == ScriptNodeTypeId )
		{
			ScriptNode *scriptNode =  static_cast<Gaffer::ScriptNode*>( newParent );
			Format::addDefaultFormatPlug( scriptNode );
		}
	}

	ComputeNode::parentChanging( newParent );
}

void ImageStats::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );
	if (
			input == channelsPlug() ||
			input->parent<ImagePlug>() == inPlug() ||
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

	bool earlyOut = true;
	for( int i = 0; i < 4; ++i )
	{
		if (
				output == minPlug()->getChild(i) ||
				output == maxPlug()->getChild(i) ||
				output == averagePlug()->getChild(i)
		   )
		{
			earlyOut = false;
			break;
		}
	}
	if( earlyOut )
	{
		return;
	}

	const Imath::Box2i regionOfInterest( regionOfInterestPlug()->getValue() );
	regionOfInterestPlug()->hash( h );
	inPlug()->channelNamesPlug()->hash( h );
	inPlug()->dataWindowPlug()->hash( h );

	IECore::ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
	std::vector<std::string> maskChannels = channelNamesData->readable();
	channelsPlug()->maskChannels( maskChannels );
	const int nChannels( maskChannels.size() );

	if ( nChannels > 0 )
	{
		std::vector<std::string> uniqueChannels = maskChannels;
		GafferImage::ChannelMaskPlug::removeDuplicateIndices( uniqueChannels );
		std::string channel;
		channelNameFromOutput( output, channel );

		if ( !channel.empty() )
		{
			h.append( channel );
			Sampler s( inPlug(), channel, regionOfInterest );
			s.hash( h );
			return;
		}
	}

	// If our node is not enabled then we just append the default value that we will give the plug.
	if(
			output == maxPlug()->getChild(3) ||
			output == minPlug()->getChild(3) ||
			output == averagePlug()->getChild(3)
	  )
	{
		h.append( 0 );
	}
	else
	{
		h.append( 1 );
	}
}

void ImageStats::channelNameFromOutput( const ValuePlug *output, std::string &channelName ) const
{
	IECore::ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
	std::vector<std::string> maskChannels = channelNamesData->readable();
	channelsPlug()->maskChannels( maskChannels );

	/// As the channelMaskPlug allows any combination of channels to be input we need to make sure that
	/// the channels that it masks each have a distinct channelIndex. Otherwise multiple channels would be
	/// outputting to the same plug.
	std::vector<std::string> uniqueChannels = maskChannels;
	GafferImage::ChannelMaskPlug::removeDuplicateIndices( uniqueChannels );

	for( int channelIndex = 0; channelIndex < 4; ++channelIndex )
	{
		if ( output == minPlug()->getChild( channelIndex ) ||
			 output == maxPlug()->getChild( channelIndex ) ||
			 output == averagePlug()->getChild( channelIndex )
		   )
		{
			for( std::vector<std::string>::iterator it( uniqueChannels.begin() ); it != uniqueChannels.end(); ++it )
			{
				if ( GafferImage::ChannelMaskPlug::channelIndex( *it ) == channelIndex )
				{
					channelName = *it;
					return;
				}
			}
		}
	}
	return;
}

void ImageStats::setOutputToDefault( FloatPlug *output ) const
{
	if (
			output == minPlug()->getChild(3) ||
			output == maxPlug()->getChild(3) ||
			output == averagePlug()->getChild(3)
	   )
	{
		output->setValue( 1. );
	}
	else
	{
		output->setValue( 0. );
	}
}

void ImageStats::compute( ValuePlug *output, const Context *context ) const
{
	const Imath::Box2i &regionOfInterest( regionOfInterestPlug()->getValue() );
	if( regionOfInterest.isEmpty() )
	{
		setOutputToDefault( static_cast<FloatPlug*>( output ) );
		return;
	}

	std::string channelName;
	channelNameFromOutput( output, channelName );
	if ( channelName.empty() )
	{
		setOutputToDefault( static_cast<FloatPlug*>( output ) );
		return;
	}

	int channelIndex = GafferImage::ChannelMaskPlug::channelIndex( channelName );

	// Set up the execution context.
	ContextPtr tmpContext = new Context( *context, Context::Borrowed );
	tmpContext->set( ImagePlug::channelNameContextName, channelName );
	Context::Scope scopedContext( tmpContext.get() );

	// Loop over the ROI and compute the min, max and average channel values and then set our outputs.
	Sampler s( inPlug(), channelName, regionOfInterest );

	float min = std::numeric_limits<float>::max();
	float max = std::numeric_limits<float>::min();
	float average = 0.f;

	double sum = 0.;
	for( int y = regionOfInterest.min.y; y <= regionOfInterest.max.y; ++y )
	{
		for( int x = regionOfInterest.min.x; x <= regionOfInterest.max.x; ++x )
		{
			float v = s.sample( x, y );
			min = std::min( v, min );
			max = std::max( v, max );
			sum += v;
		}
	}
	average = sum / double( (regionOfInterest.size().x+1) * (regionOfInterest.size().y+1) );

	if ( minPlug()->getChild( channelIndex ) == output )
	{
		static_cast<FloatPlug *>( output )->setValue( min );
	}
	else if ( maxPlug()->getChild( channelIndex ) == output )
	{
		static_cast<FloatPlug *>( output )->setValue( max );
	}
	else if ( averagePlug()->getChild( channelIndex ) == output )
	{
		static_cast<FloatPlug *>( output )->setValue( average );
	}
	else
	{
		static_cast<FloatPlug *>( output )->setValue( 0 );
	}
}

