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

IE_CORE_DEFINERUNTIMETYPED( ImagePlug );

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

class CopyTile
{

	public :

		CopyTile(
				const vector<float *> &imageChannelData,
				const vector<string> &channelNames,
				const Box2i &dataWindow
			) :
				m_imageChannelData( imageChannelData ),
				m_channelNames( channelNames ),
				m_dataWindow( dataWindow )
		{}

		void operator()( const ImagePlug *imagePlug, const string &channelName, const V2i &tileOrigin )
		{
			const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
			const Box2i b = BufferAlgo::intersection( tileBound, m_dataWindow );

			const size_t imageStride = m_dataWindow.size().x;
			const size_t tileStrideSize = sizeof(float) * b.size().x;

			const int channelIndex = std::find( m_channelNames.begin(), m_channelNames.end(), channelName ) - m_channelNames.begin();
			float *channelBegin = m_imageChannelData[channelIndex];

			ConstFloatVectorDataPtr tileData = imagePlug->channelDataPlug()->getValue();
			const float *tileDataBegin = &(tileData->readable()[0]);

			for( int y = b.min.y; y < b.max.y; y++ )
			{
				const float *tilePtr = tileDataBegin + ( y - tileOrigin.y ) * ImagePlug::tileSize() + ( b.min.x - tileOrigin.x );
				float *channelPtr = channelBegin + ( m_dataWindow.size().y - ( 1 + y - m_dataWindow.min.y ) ) * imageStride + ( b.min.x - m_dataWindow.min.x );
				std::memcpy( channelPtr, tilePtr, tileStrideSize );
			}
		}

	private :

		const vector<float *> &m_imageChannelData;
		const vector<string> &m_channelNames;
		const Box2i &m_dataWindow;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Implementation of ImagePlug
//////////////////////////////////////////////////////////////////////////

const IECore::InternedString ImagePlug::channelNameContextName = "image:channelName";
const IECore::InternedString ImagePlug::tileOriginContextName = "image:tileOrigin";

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

	/// \todo Default value should be empty.
	IECore::StringVectorDataPtr channelStrVectorData( new IECore::StringVectorData() );
	std::vector<std::string> &channelStrVector( channelStrVectorData->writable() );
	channelStrVector.push_back("R");
	channelStrVector.push_back("G");
	channelStrVector.push_back("B");

	addChild(
		new StringVectorDataPlug(
			"channelNames",
			direction,
			channelStrVectorData,
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

const IECore::FloatVectorData *ImagePlug::whiteTile()
{
	static IECore::ConstFloatVectorDataPtr g_whiteTile( new IECore::FloatVectorData( std::vector<float>( ImagePlug::tileSize()*ImagePlug::tileSize(), 1. ) ) );
	return g_whiteTile.get();
};

const IECore::FloatVectorData *ImagePlug::blackTile()
{
	static IECore::ConstFloatVectorDataPtr g_blackTile( new IECore::FloatVectorData( std::vector<float>( ImagePlug::tileSize()*ImagePlug::tileSize(), 0. ) ) );
	return g_blackTile.get();
};

bool ImagePlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	if( !ValuePlug::acceptsChild( potentialChild ) )
	{
		return false;
	}
	return children().size() != 5;
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

GafferImage::AtomicFormatPlug *ImagePlug::formatPlug()
{
	return getChild<AtomicFormatPlug>( g_firstPlugIndex );
}

const GafferImage::AtomicFormatPlug *ImagePlug::formatPlug() const
{
	return getChild<AtomicFormatPlug>( g_firstPlugIndex );
}

Gaffer::AtomicBox2iPlug *ImagePlug::dataWindowPlug()
{
	return getChild<AtomicBox2iPlug>( g_firstPlugIndex+1 );
}

const Gaffer::AtomicBox2iPlug *ImagePlug::dataWindowPlug() const
{
	return getChild<AtomicBox2iPlug>( g_firstPlugIndex+1 );
}

Gaffer::AtomicCompoundDataPlug *ImagePlug::metadataPlug()
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex+2 );
}

const Gaffer::AtomicCompoundDataPlug *ImagePlug::metadataPlug() const
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex+2 );
}

Gaffer::StringVectorDataPlug *ImagePlug::channelNamesPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex+3 );
}

const Gaffer::StringVectorDataPlug *ImagePlug::channelNamesPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex+3 );
}

Gaffer::FloatVectorDataPlug *ImagePlug::channelDataPlug()
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex+4 );
}

const Gaffer::FloatVectorDataPlug *ImagePlug::channelDataPlug() const
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex+4 );
}

ImagePlug::GlobalScope::GlobalScope( const Gaffer::Context *context )
	:   EditableScope( context )
{
	remove( channelNameContextName );
	remove( tileOriginContextName );
}

ImagePlug::ChannelDataScope::ChannelDataScope( const Gaffer::Context *context )
	:   EditableScope( context )
{
}

void ImagePlug::ChannelDataScope::setTileOrigin( const V2i &tileOrigin )
{
	set( tileOriginContextName, tileOrigin );
}

void ImagePlug::ChannelDataScope::setChannelName( const std::string &channelName )
{
	set( channelNameContextName, channelName );
}

IECore::ConstFloatVectorDataPtr ImagePlug::channelData( const std::string &channelName, const Imath::V2i &tile ) const
{
	if( direction()==In && !getInput() )
	{
		return channelDataPlug()->defaultValue();
	}

	ChannelDataScope channelDataScope( Context::current() );
	channelDataScope.setChannelName( channelName );
	channelDataScope.setTileOrigin( tile );

	return channelDataPlug()->getValue();
}

IECore::MurmurHash ImagePlug::channelDataHash( const std::string &channelName, const Imath::V2i &tile ) const
{
	ChannelDataScope channelDataScope( Context::current() );
	channelDataScope.setChannelName( channelName );
	channelDataScope.setTileOrigin( tile );
	return channelDataPlug()->hash();
}

GafferImage::Format ImagePlug::format() const
{
	GlobalScope globalScope( Context::current() );
	return formatPlug()->getValue();
}

IECore::MurmurHash ImagePlug::formatHash() const
{
	GlobalScope globalScope( Context::current() );
	return formatPlug()->hash();
}

Imath::Box2i ImagePlug::dataWindow() const
{
	GlobalScope globalScope( Context::current() );
	return dataWindowPlug()->getValue();
}

IECore::MurmurHash ImagePlug::dataWindowHash() const
{
	GlobalScope globalScope( Context::current() );
	return dataWindowPlug()->hash();
}

IECore::ConstStringVectorDataPtr ImagePlug::channelNames() const
{
	GlobalScope globalScope( Context::current() );
	return channelNamesPlug()->getValue();
}

IECore::MurmurHash ImagePlug::channelNamesHash() const
{
	GlobalScope globalScope( Context::current() );
	return channelNamesPlug()->hash();
}

IECore::ConstCompoundDataPtr ImagePlug::metadata() const
{
	GlobalScope globalScope( Context::current() );
	return metadataPlug()->getValue();
}

IECore::MurmurHash ImagePlug::metadataHash() const
{
	GlobalScope globalScope( Context::current() );
	return metadataPlug()->hash();
}

IECoreImage::ImagePrimitivePtr ImagePlug::image() const
{
	Format format = formatPlug()->getValue();
	Box2i dataWindow = dataWindowPlug()->getValue();
	Box2i newDataWindow( Imath::V2i( 0 ) );

	if( !BufferAlgo::empty( dataWindow ) )
	{
		newDataWindow = format.toEXRSpace( dataWindow );
	}
	else
	{
		dataWindow = newDataWindow;
	}

	Box2i newDisplayWindow = format.toEXRSpace( format.getDisplayWindow() );

	IECoreImage::ImagePrimitivePtr result = new IECoreImage::ImagePrimitive( newDataWindow, newDisplayWindow );

	ConstCompoundDataPtr metadata = metadataPlug()->getValue();
	result->blindData()->Object::copyFrom( metadata.get() );

	ConstStringVectorDataPtr channelNamesData = channelNamesPlug()->getValue();
	const vector<string> &channelNames = channelNamesData->readable();

	vector<float *> imageChannelData;
	for( vector<string>::const_iterator it = channelNames.begin(), eIt = channelNames.end(); it!=eIt; it++ )
	{
		FloatVectorDataPtr cd = new FloatVectorData;
		vector<float> &c = cd->writable();
		c.resize( result->channelSize(), 0.0f );
		result->channels[*it] = cd;
		imageChannelData.push_back( &(c[0]) );
	}

	CopyTile copyTile( imageChannelData, channelNames, dataWindow );
	ImageAlgo::parallelProcessTiles( this, channelNames, copyTile, dataWindow );

	return result;
}

IECore::MurmurHash ImagePlug::imageHash() const
{
	const Box2i dataWindow = dataWindowPlug()->getValue();
	ConstStringVectorDataPtr channelNamesData = channelNamesPlug()->getValue();
	const vector<string> &channelNames = channelNamesData->readable();

	MurmurHash result = formatPlug()->hash();
	result.append( dataWindowPlug()->hash() );
	result.append( metadataPlug()->hash() );
	result.append( channelNamesPlug()->hash() );

	ImageAlgo::parallelGatherTiles(
		this, channelNames,
		// Tile
		[] ( const ImagePlug *imagePlug, const string &channelName, const V2i &tileOrigin )
		{
			return imagePlug->channelDataPlug()->hash();
		},
		// Gather
		[ &result ] ( const ImagePlug *imagePlug, const string &channelName, const V2i &tileOrigin, const IECore::MurmurHash &tileHash )
		{
			result.append( tileHash );
		},
		dataWindow,
		ImageAlgo::BottomToTop
	);

	return result;
}
