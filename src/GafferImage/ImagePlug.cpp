//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
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

#include "tbb/tbb.h"

#include "IECore/Exception.h"
#include "IECore/BoxOps.h"
#include "IECore/BoxAlgo.h"

#include "Gaffer/Context.h"

#include "GafferImage/ImagePlug.h"
#include "GafferImage/FormatPlug.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;
using namespace tbb;

IE_CORE_DEFINERUNTIMETYPED( ImagePlug );

//////////////////////////////////////////////////////////////////////////
// Implementation of CopyTiles:
// A simple class for multithreading the copying of
// image tiles from an input plug to an output plug.
//////////////////////////////////////////////////////////////////////////

namespace GafferImage
{

namespace Detail
{

class CopyTiles
{
	public:
		CopyTiles(
				const vector<float *> &imageChannelData,
				const vector<string> &channelNames,
				const Gaffer::FloatVectorDataPlug *channelDataPlug,
				const Box2i& dataWindow,
				const Context *context, const int tileSize
			) :
				m_imageChannelData( imageChannelData ),
				m_channelNames( channelNames ),
				m_channelDataPlug( channelDataPlug ),
				m_dataWindow( dataWindow ),
				m_parentContext( context ),
				m_tileSize( tileSize )
		{}

		void operator()( const blocked_range2d<size_t>& r ) const
		{
			ContextPtr context = new Context( *m_parentContext );
			const Box2i operationWindow( V2i( r.rows().begin()+m_dataWindow.min.x, r.cols().begin()+m_dataWindow.min.y ), V2i( r.rows().end()+m_dataWindow.min.x-1, r.cols().end()+m_dataWindow.min.y-1 ) );
			V2i minTileOrigin = ImagePlug::tileOrigin( operationWindow.min );
			V2i maxTileOrigin = ImagePlug::tileOrigin( operationWindow.max );
			size_t imageStride = m_dataWindow.size().x + 1;

			for( int tileOriginY = minTileOrigin.y; tileOriginY <= maxTileOrigin.y; tileOriginY += m_tileSize )
			{
				for( int tileOriginX = minTileOrigin.x; tileOriginX <= maxTileOrigin.x; tileOriginX += m_tileSize )
				{
					for( vector<string>::const_iterator it = m_channelNames.begin(), eIt = m_channelNames.end(); it != eIt; it++ )
					{
						context->set( ImagePlug::channelNameContextName, *it );
						context->set( ImagePlug::tileOriginContextName, V2i( tileOriginX, tileOriginY ) );
						Context::Scope scope( context );
						Box2i tileBound( V2i( tileOriginX, tileOriginY ), V2i( tileOriginX + m_tileSize - 1, tileOriginY + m_tileSize - 1 ) );
						Box2i b = boxIntersection( tileBound, operationWindow );

						ConstFloatVectorDataPtr tileData = m_channelDataPlug->getValue();

						for( int y = b.min.y; y<=b.max.y; y++ )
						{
							const float *tilePtr = &(tileData->readable()[0]) + (y - tileOriginY) * m_tileSize + (b.min.x - tileOriginX);
							float *channelPtr = m_imageChannelData[it-m_channelNames.begin()] + ( m_dataWindow.size().y - ( y - m_dataWindow.min.y ) ) * imageStride + (b.min.x - m_dataWindow.min.x);
							for( int x = b.min.x; x <= b.max.x; x++ )
							{
								*channelPtr++ = *tilePtr++;
							}
						}
					}
				}
			}
		}
		
	private:
		const vector<float *> &m_imageChannelData;
		const vector<string> &m_channelNames;
		const Gaffer::FloatVectorDataPlug *m_channelDataPlug;
		const Box2i &m_dataWindow;
		const Context *m_parentContext;
		const int m_tileSize;
};

};

};

//////////////////////////////////////////////////////////////////////////
// Implementation of ImagePlug
//////////////////////////////////////////////////////////////////////////
const IECore::InternedString ImagePlug::channelNameContextName = "image:channelName";
const IECore::InternedString ImagePlug::tileOriginContextName = "image:tileOrigin";

size_t ImagePlug::g_firstPlugIndex = 0;

ImagePlug::ImagePlug( const std::string &name, Direction direction, unsigned flags )
	:	CompoundPlug( name, direction, flags )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	
	// we don't want the children to be serialised in any way - we always create
	// them ourselves in this constructor so they aren't Dynamic, and we don't ever
	// want to store their values because they are meaningless without an input
	// connection, so they aren't Serialisable either.
	unsigned childFlags = flags & ~(Dynamic | Serialisable);
	
	addChild(
		new FormatPlug(
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
	return children().size() != 4;
}

bool ImagePlug::acceptsInput( const Gaffer::Plug *input ) const
{
	if( !CompoundPlug::acceptsInput( input ) )
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

GafferImage::FormatPlug *ImagePlug::formatPlug()
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

const GafferImage::FormatPlug *ImagePlug::formatPlug() const
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

Gaffer::AtomicBox2iPlug *ImagePlug::dataWindowPlug()
{
	return getChild<AtomicBox2iPlug>( g_firstPlugIndex+1 );
}

const Gaffer::AtomicBox2iPlug *ImagePlug::dataWindowPlug() const
{
	return getChild<AtomicBox2iPlug>( g_firstPlugIndex+1 );
}

Gaffer::StringVectorDataPlug *ImagePlug::channelNamesPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex+2 );
}

const Gaffer::StringVectorDataPlug *ImagePlug::channelNamesPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex+2 );
}

Gaffer::FloatVectorDataPlug *ImagePlug::channelDataPlug()
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex+3 );
}

const Gaffer::FloatVectorDataPlug *ImagePlug::channelDataPlug() const
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex+3 );
}

IECore::ConstFloatVectorDataPtr ImagePlug::channelData( const std::string &channelName, const Imath::V2i &tile ) const
{
	if( direction()==In && !getInput<Plug>() )
	{
		return channelDataPlug()->defaultValue();
	}
	
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( ImagePlug::channelNameContextName, channelName );
	tmpContext->set( ImagePlug::tileOriginContextName, tile );
	Context::Scope scopedContext( tmpContext );
	
	return channelDataPlug()->getValue();
}

IECore::MurmurHash ImagePlug::channelDataHash( const std::string &channelName, const Imath::V2i &tile ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( ImagePlug::channelNameContextName, channelName );
	tmpContext->set( ImagePlug::tileOriginContextName, tile );
	Context::Scope scopedContext( tmpContext );
	return channelDataPlug()->hash();
}

IECore::ImagePrimitivePtr ImagePlug::image() const
{
	Format format = formatPlug()->getValue();
	Box2i dataWindow = dataWindowPlug()->getValue();
	Box2i newDataWindow( Imath::V2i(0) );
	
	if( dataWindow.isEmpty() )
	{
		dataWindow = Box2i( Imath::V2i(0) );
	}
	else
	{
		newDataWindow = format.yDownToFormatSpace( dataWindow );
	}
	
	ImagePrimitivePtr result = new ImagePrimitive( newDataWindow, format.getDisplayWindow() );

	ConstStringVectorDataPtr channelNamesData = channelNamesPlug()->getValue();
	const vector<string> &channelNames = channelNamesData->readable();
	
	vector<float *> imageChannelData;
	for( vector<string>::const_iterator it = channelNames.begin(), eIt = channelNames.end(); it!=eIt; it++ )
	{
		FloatVectorDataPtr cd = new FloatVectorData;
		vector<float> &c = cd->writable();
		c.resize( result->variableSize( PrimitiveVariable::Vertex ), 0.0f );
		result->variables[*it] = PrimitiveVariable( PrimitiveVariable::Vertex, cd );
		imageChannelData.push_back( &(c[0]) );
	}
	
	parallel_for( blocked_range2d<size_t>( 0, dataWindow.size().x+1, tileSize(), 0, dataWindow.size().y+1, tileSize() ),
		      GafferImage::Detail::CopyTiles( imageChannelData, channelNames, channelDataPlug(), dataWindow, Context::current(), tileSize()) );
	
	return result;
}

IECore::MurmurHash ImagePlug::imageHash() const
{
	const Box2i dataWindow = dataWindowPlug()->getValue();
	ConstStringVectorDataPtr channelNamesData = channelNamesPlug()->getValue();
	const vector<string> &channelNames = channelNamesData->readable();
	
	MurmurHash result = formatPlug()->hash();
	result.append( dataWindowPlug()->hash() );
	result.append( channelNamesPlug()->hash() );

	V2i minTileOrigin = tileOrigin( dataWindow.min );
	V2i maxTileOrigin = tileOrigin( dataWindow.max );

	ContextPtr context = new Context( *Context::current(), Context::Borrowed );
	for( vector<string>::const_iterator it = channelNames.begin(), eIt = channelNames.end(); it!=eIt; it++ )
	{
		for( int tileOriginY = minTileOrigin.y; tileOriginY<=maxTileOrigin.y; tileOriginY += tileSize() )
		{
			for( int tileOriginX = minTileOrigin.x; tileOriginX<=maxTileOrigin.x; tileOriginX += tileSize() )
			{
				for( vector<string>::const_iterator it = channelNames.begin(), eIt = channelNames.end(); it!=eIt; it++ )
				{
					context->set( ImagePlug::channelNameContextName, *it );
					context->set( ImagePlug::tileOriginContextName, V2i( tileOriginX, tileOriginY ) );
					Context::Scope scope( context );
					channelDataPlug()->hash( result );
				}
			}
		}
	}
	
	return result;
}
