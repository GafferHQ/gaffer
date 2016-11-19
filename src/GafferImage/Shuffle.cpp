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

#include "GafferImage/Shuffle.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Shuffle::ChannelPlug
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Shuffle::ChannelPlug );

Shuffle::ChannelPlug::ChannelPlug( const std::string &name, Direction direction, unsigned flags)
	:	ValuePlug( name, direction, flags )
{
	const unsigned childFlags = flags & ~Dynamic;
	addChild( new StringPlug( "out", direction, "", childFlags ) );
	addChild( new StringPlug( "in", direction, "", childFlags ) );
}

Shuffle::ChannelPlug::ChannelPlug( const std::string &out, const std::string &in )
	:	ValuePlug( "channel", In, Default | Dynamic )
{
	addChild( new StringPlug( "out" ) );
	addChild( new StringPlug( "in" ) );
	outPlug()->setValue( out );
	inPlug()->setValue( in );
}

StringPlug *Shuffle::ChannelPlug::outPlug()
{
	return getChild<StringPlug>( 0 );
}

const StringPlug *Shuffle::ChannelPlug::outPlug() const
{
	return getChild<StringPlug>( 0 );
}

StringPlug *Shuffle::ChannelPlug::inPlug()
{
	return getChild<StringPlug>( 1 );
}

const StringPlug *Shuffle::ChannelPlug::inPlug() const
{
	return getChild<StringPlug>( 1 );
}

bool Shuffle::ChannelPlug::acceptsChild( const Gaffer::GraphComponent *potentialChild ) const
{
	return children().size() < 2;
}

PlugPtr Shuffle::ChannelPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	return new ChannelPlug( name, direction, getFlags() );
}

//////////////////////////////////////////////////////////////////////////
// Shuffle
//////////////////////////////////////////////////////////////////////////

size_t Shuffle::g_firstPlugIndex = 0;

IE_CORE_DEFINERUNTIMETYPED( Shuffle );

Shuffle::Shuffle( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ValuePlug( "channels" ) );

	// Pass-through the things we don't want to modify.
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->deepStatePlug()->setInput( inPlug()->deepStatePlug() );
	outPlug()->sampleOffsetsPlug()->setInput( inPlug()->sampleOffsetsPlug() );
}

Shuffle::~Shuffle()
{
}

ValuePlug *Shuffle::channelsPlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex );
}

const ValuePlug *Shuffle::channelsPlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex );
}

void Shuffle::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( input == inPlug()->channelNamesPlug() )
	{
		outputs.push_back( outPlug()->channelNamesPlug() );
	}
	else if( input == inPlug()->channelDataPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if( channelsPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->channelNamesPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void Shuffle::hashChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelNames( parent, context, h );
	inPlug()->channelNamesPlug()->hash( h );
	for( ChannelPlugIterator it( channelsPlug() ); !it.done(); ++it )
	{
		(*it)->outPlug()->hash( h );
	}
}

IECore::ConstStringVectorDataPtr Shuffle::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	StringVectorDataPtr resultData = inPlug()->channelNamesPlug()->getValue()->copy();
	vector<string> &result = resultData->writable();
	for( ChannelPlugIterator it( channelsPlug() ); !it.done(); ++it )
	{
		string channelName = (*it)->outPlug()->getValue();
		if( channelName != "" && find( result.begin(), result.end(), channelName ) == result.end() )
		{
			result.push_back( channelName );
		}
	}

	return resultData;
}


void Shuffle::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	std::string c = inChannelName( context->get<string>( ImagePlug::channelNameContextName ) );

	if( c == "__black" || c == "" )
	{
		h = ImagePlug::blackTile()->Object::hash();
	}
	else if( c == "__white" )
	{
		h = ImagePlug::whiteTile()->Object::hash();
	}
	else
	{
		ContextPtr tmpContext = new Context( *context, Context::Borrowed );
		Context::Scope scopedContext( tmpContext.get() );
		tmpContext->set( ImagePlug::channelNameContextName, c );
		h = inPlug()->channelDataPlug()->hash();
	}
}

IECore::ConstFloatVectorDataPtr Shuffle::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string c = inChannelName( context->get<string>( ImagePlug::channelNameContextName ) );

	if( c == "__black" || c == "" )
	{
		return ImagePlug::blackTile();
	}
	else if( c == "__white" )
	{
		return ImagePlug::whiteTile();
	}
	else
	{
		ContextPtr tmpContext = new Context( *context, Context::Borrowed );
		Context::Scope scopedContext( tmpContext.get() );
		tmpContext->set( ImagePlug::channelNameContextName, c );
		return inPlug()->channelDataPlug()->getValue();
	}
}

std::string Shuffle::inChannelName( const std::string &outChannelName ) const
{
	for( ChannelPlugIterator it( channelsPlug() ); !it.done(); ++it )
	{
		if( (*it)->outPlug()->getValue() == outChannelName )
		{
			return (*it)->inPlug()->getValue();
		}
	}
	return outChannelName;
}
