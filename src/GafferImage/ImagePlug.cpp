//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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

#include "boost/iterator/counting_iterator.hpp"

#include "GafferImage/ImagePlug.h"

#include "GafferImage/BufferAlgo.h"
#include "GafferImage/FormatPlug.h"
#include "GafferImage/ImageAlgo.h"

#include "Gaffer/Context.h"
#include "Gaffer/ContextAlgo.h"

using namespace std;
using namespace tbb;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_PLUG_DEFINE_TYPE( ImagePlug );

//////////////////////////////////////////////////////////////////////////
// Implementation of ImagePlug
//////////////////////////////////////////////////////////////////////////

const IECore::InternedString ImagePlug::channelNameContextName = "image:channelName";
const IECore::InternedString ImagePlug::viewNameContextName = "image:viewName";
const IECore::InternedString ImagePlug::tileOriginContextName = "image:tileOrigin";

const std::string ImagePlug::defaultViewName = "default";

static ContextAlgo::GlobalScope::Registration g_globalScopeRegistration(
	ImagePlug::staticTypeId(),
	{ ImagePlug::channelNameContextName, ImagePlug::tileOriginContextName }
);

size_t ImagePlug::g_firstPlugIndex = 0;

ImagePlug::ImagePlug( const std::string &name, Direction direction, unsigned flags )
	:	ValuePlug( name, direction, flags )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	// we don't want the children to be serialised in any way - we always create
	// them ourselves in this constructor so they aren't Dynamic, and we don't ever
	// want to store their values because they are meaningless without an input
	// connection, so they aren't Serialisable either.
	unsigned childFlags = flags & ~(Dynamic | Serialisable);

	addChild(
		new StringVectorDataPlug(
			"viewNames",
			direction,
			defaultViewNames(),
			childFlags
		)
	);

	addChild(
		new AtomicFormatPlug(
			"format",
			direction,
			Format(),
			childFlags
		)
	);

	addChild(
		new AtomicBox2iPlug(
			"dataWindow",
			direction,
			Imath::Box2i(),
			childFlags
		)
	);

	addChild(
		new AtomicCompoundDataPlug(
			"metadata",
			direction,
			new IECore::CompoundData,
			childFlags
		)
	);

	addChild(
		new BoolPlug(
			"deep",
			direction,
			false,
			childFlags
		)
	);

	addChild(
		new IntVectorDataPlug(
			"sampleOffsets",
			direction,
			flatTileSampleOffsets(),
			childFlags
		)
	);

	addChild(
		new StringVectorDataPlug(
			"channelNames",
			direction,
			new StringVectorData(),
			childFlags
		)
	);

	addChild(
		new FloatVectorDataPlug(
			"channelData",
			direction,
			blackTile(),
			childFlags
		)
	);
}

ImagePlug::~ImagePlug()
{
}

const IECore::IntVectorData *ImagePlug::flatTileSampleOffsets()
{
	static boost::counting_iterator<int> begin( 1 ), end( ImagePlug::tilePixels() + 1 );
	// counting_iterator syntax is a tad funny looking, but this does create N samples
	// from 1, ... , N, where N = tilePixels
	static IECore::ConstIntVectorDataPtr g_flatTileSampleOffsets(
		new IECore::IntVectorData( std::vector<int>( begin, end ) )
	);

	return g_flatTileSampleOffsets.get();
};

const IECore::StringVectorData *ImagePlug::defaultViewNames()
{
	static IECore::ConstStringVectorDataPtr g_defaultViewNames( new IECore::StringVectorData( { defaultViewName } ) );
	return g_defaultViewNames.get();
};

const IECore::IntVectorData *ImagePlug::emptyTileSampleOffsets()
{
	static IECore::ConstIntVectorDataPtr g_emptyTileSampleOffsets(
		new IECore::IntVectorData( std::vector<int>( ImagePlug::tilePixels(), 0 ) )
	);
	return g_emptyTileSampleOffsets.get();
};

const IECore::FloatVectorData *ImagePlug::emptyTile()
{
	static IECore::ConstFloatVectorDataPtr g_emptyTile( new IECore::FloatVectorData() );
	return g_emptyTile.get();
};

const IECore::FloatVectorData *ImagePlug::whiteTile()
{
	static IECore::ConstFloatVectorDataPtr g_whiteTile( new IECore::FloatVectorData( std::vector<float>( ImagePlug::tilePixels(), 1. ) ) );
	return g_whiteTile.get();
};

const IECore::FloatVectorData *ImagePlug::blackTile()
{
	static IECore::ConstFloatVectorDataPtr g_blackTile( new IECore::FloatVectorData( std::vector<float>( ImagePlug::tilePixels(), 0. ) ) );
	return g_blackTile.get();
};

bool ImagePlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	if( !ValuePlug::acceptsChild( potentialChild ) )
	{
		return false;
	}
	return children().size() != 8;
}

bool ImagePlug::acceptsInput( const Gaffer::Plug *input ) const
{
	if( !ValuePlug::acceptsInput( input ) )
	{
		return false;
	}
	if( input )
	{
		return input->isInstanceOf( staticTypeId() );
	}
	return true;
}

Gaffer::PlugPtr ImagePlug::createCounterpart( const std::string &name, Direction direction ) const
{
	return new ImagePlug( name, direction, getFlags() );
}

Gaffer::StringVectorDataPlug *ImagePlug::viewNamesPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex );
}

const Gaffer::StringVectorDataPlug *ImagePlug::viewNamesPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex );
}


GafferImage::AtomicFormatPlug *ImagePlug::formatPlug()
{
	return getChild<AtomicFormatPlug>( g_firstPlugIndex+1 );
}

const GafferImage::AtomicFormatPlug *ImagePlug::formatPlug() const
{
	return getChild<AtomicFormatPlug>( g_firstPlugIndex+1 );
}

Gaffer::AtomicBox2iPlug *ImagePlug::dataWindowPlug()
{
	return getChild<AtomicBox2iPlug>( g_firstPlugIndex+2 );
}

const Gaffer::AtomicBox2iPlug *ImagePlug::dataWindowPlug() const
{
	return getChild<AtomicBox2iPlug>( g_firstPlugIndex+2 );
}

Gaffer::AtomicCompoundDataPlug *ImagePlug::metadataPlug()
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex+3 );
}

const Gaffer::AtomicCompoundDataPlug *ImagePlug::metadataPlug() const
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex+3 );
}

Gaffer::BoolPlug *ImagePlug::deepPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex+4 );
}

const Gaffer::BoolPlug *ImagePlug::deepPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex+4 );
}

Gaffer::IntVectorDataPlug *ImagePlug::sampleOffsetsPlug()
{
	return getChild<IntVectorDataPlug>( g_firstPlugIndex+5 );
}

const Gaffer::IntVectorDataPlug *ImagePlug::sampleOffsetsPlug() const
{
	return getChild<IntVectorDataPlug>( g_firstPlugIndex+5 );
}

Gaffer::StringVectorDataPlug *ImagePlug::channelNamesPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex+6 );
}

const Gaffer::StringVectorDataPlug *ImagePlug::channelNamesPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex+6 );
}

Gaffer::FloatVectorDataPlug *ImagePlug::channelDataPlug()
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex+7 );
}

const Gaffer::FloatVectorDataPlug *ImagePlug::channelDataPlug() const
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex+7 );
}

ImagePlug::GlobalScope::GlobalScope( const Gaffer::Context *context )
	:   EditableScope( context )
{
	remove( channelNameContextName );
	remove( tileOriginContextName );
}

ImagePlug::GlobalScope::GlobalScope( const Gaffer::ThreadState &threadState )
	:	EditableScope( threadState )
{
	remove( channelNameContextName );
	remove( tileOriginContextName );
}

ImagePlug::ViewScope::ViewScope( const Gaffer::Context *context )
	:   EditableScope( context )
{
}

ImagePlug::ViewScope::ViewScope( const Gaffer::ThreadState &threadState )
	:	EditableScope( threadState )
{
}

void ImagePlug::ViewScope::setViewName( const std::string *viewName )
{
	set( viewNameContextName, viewName );
}

void ImagePlug::ViewScope::setViewNameChecked( const std::string *viewName, const IECore::StringVectorData *viewNamesData )
{
	const std::vector< std::string > &viewNames = viewNamesData->readable();
	if( std::find( viewNames.begin(), viewNames.end(), *viewName ) == viewNames.end() )
	{
		if( std::find( viewNames.begin(), viewNames.end(), ImagePlug::defaultViewName) == viewNames.end() )
		{
			throw IECore::Exception( "View does not exist \"" + *viewName + "\"" );
		}
	}

	set( viewNameContextName, viewName );
}

ImagePlug::ChannelDataScope::ChannelDataScope( const Gaffer::Context *context )
	:   ViewScope( context )
{
}

ImagePlug::ChannelDataScope::ChannelDataScope( const Gaffer::ThreadState &threadState )
	:	ViewScope( threadState )
{
}

void ImagePlug::ChannelDataScope::setTileOrigin( const V2i &tileOrigin )
{
	setAllocated( tileOriginContextName, tileOrigin );
}

void ImagePlug::ChannelDataScope::setChannelName( const std::string &channelName )
{
	setAllocated( channelNameContextName, channelName );
}

void ImagePlug::ChannelDataScope::setTileOrigin( const V2i *tileOrigin )
{
	set( tileOriginContextName, tileOrigin );
}

void ImagePlug::ChannelDataScope::setChannelName( const std::string *channelName )
{
	set( channelNameContextName, channelName );
}

IECore::ConstFloatVectorDataPtr ImagePlug::channelData( const std::string &channelName, const Imath::V2i &tile, const std::string *viewName ) const
{
	ChannelDataScope channelDataScope( Context::current() );
	channelDataScope.setChannelName( &channelName );
	channelDataScope.setTileOrigin( &tile );
	if( viewName )
	{
		channelDataScope.set( ImagePlug::viewNameContextName, viewName );
	}

	return channelDataPlug()->getValue();
}

IECore::MurmurHash ImagePlug::channelDataHash( const std::string &channelName, const Imath::V2i &tile, const std::string *viewName ) const
{
	ChannelDataScope channelDataScope( Context::current() );
	channelDataScope.setChannelName( &channelName );
	channelDataScope.setTileOrigin( &tile );
	if( viewName )
	{
		channelDataScope.set( ImagePlug::viewNameContextName, viewName );
	}

	return channelDataPlug()->hash();
}

IECore::ConstStringVectorDataPtr ImagePlug::viewNames() const
{
	GlobalScope globalScope( Context::current() );
	globalScope.remove( ImagePlug::viewNameContextName );
	return viewNamesPlug()->getValue();
}

IECore::MurmurHash ImagePlug::viewNamesHash() const
{
	GlobalScope globalScope( Context::current() );
	globalScope.remove( ImagePlug::viewNameContextName );
	return viewNamesPlug()->hash();
}

GafferImage::Format ImagePlug::format( const std::string *viewName ) const
{
	GlobalScope globalScope( Context::current() );
	if( viewName )
	{
		globalScope.set( ImagePlug::viewNameContextName, viewName );
	}

	return formatPlug()->getValue();
}

IECore::MurmurHash ImagePlug::formatHash( const std::string *viewName ) const
{
	GlobalScope globalScope( Context::current() );
	if( viewName )
	{
		globalScope.set( ImagePlug::viewNameContextName, viewName );
	}

	return formatPlug()->hash();
}

Imath::Box2i ImagePlug::dataWindow( const std::string *viewName ) const
{
	GlobalScope globalScope( Context::current() );
	if( viewName )
	{
		globalScope.set( ImagePlug::viewNameContextName, viewName );
	}

	return dataWindowPlug()->getValue();
}

IECore::MurmurHash ImagePlug::dataWindowHash( const std::string *viewName ) const
{
	GlobalScope globalScope( Context::current() );
	if( viewName )
	{
		globalScope.set( ImagePlug::viewNameContextName, viewName );
	}

	return dataWindowPlug()->hash();
}

IECore::ConstStringVectorDataPtr ImagePlug::channelNames( const std::string *viewName ) const
{
	GlobalScope globalScope( Context::current() );
	if( viewName )
	{
		globalScope.set( ImagePlug::viewNameContextName, viewName );
	}

	return channelNamesPlug()->getValue();
}

IECore::MurmurHash ImagePlug::channelNamesHash( const std::string *viewName ) const
{
	GlobalScope globalScope( Context::current() );
	if( viewName )
	{
		globalScope.set( ImagePlug::viewNameContextName, viewName );
	}

	return channelNamesPlug()->hash();
}

IECore::ConstCompoundDataPtr ImagePlug::metadata( const std::string *viewName ) const
{
	GlobalScope globalScope( Context::current() );
	if( viewName )
	{
		globalScope.set( ImagePlug::viewNameContextName, viewName );
	}

	return metadataPlug()->getValue();
}

IECore::MurmurHash ImagePlug::metadataHash( const std::string *viewName ) const
{
	GlobalScope globalScope( Context::current() );
	if( viewName )
	{
		globalScope.set( ImagePlug::viewNameContextName, viewName );
	}

	return metadataPlug()->hash();
}

bool ImagePlug::deep( const std::string *viewName ) const
{
	GlobalScope globalScope( Context::current() );
	if( viewName )
	{
		globalScope.set( ImagePlug::viewNameContextName, viewName );
	}

	return deepPlug()->getValue();
}

IECore::MurmurHash ImagePlug::deepHash( const std::string *viewName ) const
{
	GlobalScope globalScope( Context::current() );
	if( viewName )
	{
		globalScope.set( ImagePlug::viewNameContextName, viewName );
	}

	return deepPlug()->hash();
}

IECore::ConstIntVectorDataPtr ImagePlug::sampleOffsets( const Imath::V2i &tile, const std::string *viewName ) const
{
	ChannelDataScope channelDataScope( Context::current() );
	channelDataScope.setTileOrigin( &tile );
	if( viewName )
	{
		channelDataScope.set( ImagePlug::viewNameContextName, viewName );
	}

	return sampleOffsetsPlug()->getValue();
}

IECore::MurmurHash ImagePlug::sampleOffsetsHash( const Imath::V2i &tile, const std::string *viewName ) const
{
	ChannelDataScope channelDataScope( Context::current() );
	channelDataScope.setTileOrigin( &tile );
	if( viewName )
	{
		channelDataScope.set( ImagePlug::viewNameContextName, viewName );
	}

	return sampleOffsetsPlug()->hash();
}
