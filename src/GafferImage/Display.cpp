//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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
#include "boost/bind/placeholders.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/multi_array.hpp"

#include "IECore/LRUCache.h"
#include "IECore/DisplayDriverServer.h"
#include "IECore/DisplayDriver.h"
#include "IECore/MessageHandler.h"
#include "IECore/BoxOps.h"

#include "Gaffer/Context.h"

#include "GafferImage/Display.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Implementation of a cache of DisplayDriverServers. We use the cache
// as many nodes may want to use the same port number, and this allows us
// to share the servers between the nodes.
//////////////////////////////////////////////////////////////////////////

typedef LRUCache<int, DisplayDriverServerPtr> DisplayDriverServerCache;

static DisplayDriverServerPtr cacheGetter( int key, size_t &cost )
{
	cost = 1;
	return new DisplayDriverServer( key );
}

static DisplayDriverServerCache g_serverCache( cacheGetter, 10 );

//////////////////////////////////////////////////////////////////////////
// Implementation of a DisplayDriver to support the node itself
//////////////////////////////////////////////////////////////////////////

namespace GafferImage
{

class GafferDisplayDriver : public IECore::DisplayDriver
{

	public :
	
		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::GafferDisplayDriver, GafferDisplayDriverTypeId, DisplayDriver );

		GafferDisplayDriver( const Imath::Box2i &displayWindow, const Imath::Box2i &dataWindow,
			const vector<string> &channelNames, ConstCompoundDataPtr parameters )
			:	DisplayDriver( displayWindow, dataWindow, channelNames, parameters ),
				m_gafferFormat( displayWindow, 1 ),
				m_gafferDataWindow( m_gafferFormat.yDownToFormatSpace( dataWindow ) )
		{
			const V2i dataWindowMinTileIndex = ImagePlug::tileOrigin( m_gafferDataWindow.min ) / ImagePlug::tileSize();
			const V2i dataWindowMaxTileIndex = ImagePlug::tileOrigin( m_gafferDataWindow.max ) / ImagePlug::tileSize();
			
			m_tiles.resize(
				TileArray::extent_gen()
					[TileArray::extent_range( dataWindowMinTileIndex.x, dataWindowMaxTileIndex.x + 1 )]
					[TileArray::extent_range( dataWindowMinTileIndex.y, dataWindowMaxTileIndex.y + 1 )]
					[channelNames.size()]
			);
			
			m_parameters = parameters ? parameters->copy() : CompoundDataPtr( new CompoundData );
			instanceCreatedSignal()( this );
		}

		virtual ~GafferDisplayDriver()
		{
		}
		
		const Format &gafferFormat() const
		{
			return m_gafferFormat;
		}
		
		const Box2i &gafferDataWindow() const
		{
			return m_gafferDataWindow;
		}
		
		const CompoundData *parameters() const
		{
			return m_parameters.get();
		}
		
		virtual void imageData( const Imath::Box2i &box, const float *data, size_t dataSize )
		{
			Box2i yUpBox = m_gafferFormat.yDownToFormatSpace( box );
			const V2i boxMinTileOrigin = ImagePlug::tileOrigin( yUpBox.min );
			const V2i boxMaxTileOrigin = ImagePlug::tileOrigin( yUpBox.max );
			for( int tileOriginY = boxMinTileOrigin.y; tileOriginY <= boxMaxTileOrigin.y; tileOriginY += ImagePlug::tileSize() )
			{
				for( int tileOriginX = boxMinTileOrigin.x; tileOriginX <= boxMaxTileOrigin.x; tileOriginX += ImagePlug::tileSize() )
				{
					for( int channelIndex = 0, numChannels = channelNames().size(); channelIndex < numChannels; ++channelIndex )
					{
						const V2i tileOrigin( tileOriginX, tileOriginY );
						ConstFloatVectorDataPtr tileData = getTile( tileOrigin, channelIndex );
						if( !tileData )
						{
							// we've been sent data outside of the data window
							continue;
						}
						
						// we must create a new object to hold the updated tile data,
						// because the old one might well have been returned from
						// computeChannelData and be being held in the cache.
						FloatVectorDataPtr updatedTileData = tileData->copy();
						vector<float> &updatedTile = updatedTileData->writable();
						
						const Box2i tileBound( tileOrigin, tileOrigin + Imath::V2i( GafferImage::ImagePlug::tileSize() - 1 ) );
						const Box2i transferBound = IECore::boxIntersection( tileBound, yUpBox );
						for( int y = transferBound.min.y; y<=transferBound.max.y; ++y )
						{
							int srcY = m_gafferFormat.formatToYDownSpace( y );
							size_t srcIndex = ( ( srcY - box.min.y ) * ( box.size().x + 1 ) * numChannels ) + ( transferBound.min.x - box.min.x ) + channelIndex;
							size_t dstIndex = ( y - tileBound.min.y ) * ImagePlug::tileSize() + transferBound.min.x - tileBound.min.x;
							const size_t srcEndIndex = srcIndex + transferBound.size().x * numChannels;
							while( srcIndex <= srcEndIndex )
							{
								updatedTile[dstIndex] = data[srcIndex];
								srcIndex += numChannels;
								dstIndex++;
							}
						}
						
						setTile( tileOrigin, channelIndex, updatedTileData );
					}
				}
			}
			
			dataReceivedSignal()( this, box );
		}
		
		virtual void imageClose()
		{
			imageReceivedSignal()( this );
		}

		virtual bool scanLineOrderOnly() const
		{
			return false;
		}
		
		virtual bool acceptsRepeatedData() const
		{
			return true;
		}
		
		ConstFloatVectorDataPtr channelData( const Imath::V2i &tileOrigin, const std::string &channelName )
		{
			vector<string>::const_iterator cIt = find( channelNames().begin(), channelNames().end(), channelName );
			if( cIt == channelNames().end() )
			{
				return ImagePlug::blackTile();
			}
			
			ConstFloatVectorDataPtr tile = getTile( tileOrigin, cIt - channelNames().begin() );
			if( tile )
			{
				return tile;
			}
			else
			{
				return ImagePlug::blackTile();
			}
		}
		
		typedef boost::signal<void ( GafferDisplayDriver *, const Imath::Box2i & )> DataReceivedSignal;
		DataReceivedSignal &dataReceivedSignal()
		{
			return m_dataReceivedSignal;
		}
		
		typedef boost::signal<void ( GafferDisplayDriver * )> ImageReceivedSignal;
		ImageReceivedSignal &imageReceivedSignal()
		{
			return m_imageReceivedSignal;
		}

		typedef boost::signal<void ( GafferDisplayDriver * )> InstanceCreatedSignal;
		static InstanceCreatedSignal &instanceCreatedSignal()
		{
			static InstanceCreatedSignal s;
			return s;
		}

	private :
	
		static const DisplayDriverDescription<GafferDisplayDriver> g_description;

		ConstFloatVectorDataPtr getTile( const V2i &tileOrigin, size_t channelIndex )
		{
			V2i tileIndex = tileOrigin / ImagePlug::tileSize();
			
			if(
				tileIndex.x < m_tiles.index_bases()[0] ||
				tileIndex.x >= (int)(m_tiles.index_bases()[0] + m_tiles.shape()[0] ) ||
				tileIndex.y < m_tiles.index_bases()[1] ||
				tileIndex.y >= (int)(m_tiles.index_bases()[1] + m_tiles.shape()[1] )
			)
			{
				// outside data window
				return NULL;
			}
			
			tbb::spin_rw_mutex::scoped_lock tileLock( m_tileMutex, false /* read */ );
			
			ConstFloatVectorDataPtr result = m_tiles[tileIndex.x][tileIndex.y][channelIndex];
			if( !result )
			{
				result = ImagePlug::blackTile();
			}
			
			return result;
		}
		
		void setTile( const V2i &tileOrigin, size_t channelIndex, ConstFloatVectorDataPtr tile )
		{
			V2i tileIndex = tileOrigin / ImagePlug::tileSize();
			tbb::spin_rw_mutex::scoped_lock tileLock( m_tileMutex, true /* write */ );
			m_tiles[tileIndex.x][tileIndex.y][channelIndex] = tile;
		}

		// indexed by tileIndexX, tileIndexY, channelIndex.
		typedef boost::multi_array<ConstFloatVectorDataPtr, 3> TileArray;
		TileArray m_tiles;
		tbb::spin_rw_mutex m_tileMutex;

		Format m_gafferFormat;
		Imath::Box2i m_gafferDataWindow;
		IECore::ConstCompoundDataPtr m_parameters;
		DataReceivedSignal m_dataReceivedSignal;
		ImageReceivedSignal m_imageReceivedSignal;

};

const DisplayDriver::DisplayDriverDescription<GafferDisplayDriver> GafferDisplayDriver::g_description;

} // namespace GafferImage

//////////////////////////////////////////////////////////////////////////
// Implementation of the Display class itself
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Display );

size_t Display::g_firstPlugIndex = 0;

Display::Display( const std::string &name )
	:	ImageNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild(
		new IntPlug(
			"port",
			Plug::In,
			1559,
			1,
			65535,
			// disabling input connections because they could be used
			// to create a port number which changes with context. we 
			// can't allow that because we can only have a single server
			// associated with a given node.
			Plug::Default & ~Plug::AcceptsInputs
		)
	);
	
	// this plug is incremented when new data is received, triggering dirty signals
	// and prompting reevaluation in the viewer. see GafferImageUI.DisplayUI for
	// details of how it is set (we can't set it from dataReceived() because we're
	// not on the ui thread at that point.
	addChild(
		new IntPlug(
			"__updateCount",
			Plug::In,
			0,
			0,
			Imath::limits<int>::max(),
			Plug::Default & ~Plug::Serialisable
		)
	);
		
	plugSetSignal().connect( boost::bind( &Display::plugSet, this, ::_1 ) );
	GafferDisplayDriver::instanceCreatedSignal().connect( boost::bind( &Display::driverCreated, this, ::_1 ) );
	setupServer();
}

Display::~Display()
{
}
		
Gaffer::IntPlug *Display::portPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *Display::portPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *Display::updateCountPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *Display::updateCountPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}
				
void Display::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageNode::affects( input, outputs );
	
	if( input == portPlug() || input == updateCountPlug() )
	{
		for( ValuePlugIterator it( outPlug() ); it != it.end(); it++ )
		{
			outputs.push_back( it->get() );
		}
	}
}

Node::UnaryPlugSignal &Display::dataReceivedSignal()
{
	static UnaryPlugSignal s;
	return s;
}

Node::UnaryPlugSignal &Display::imageReceivedSignal()
{
	static UnaryPlugSignal s;
	return s;
}

void Display::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashFormat( output, context, h );
	
	Format format;
	if( m_driver )
	{
		format = m_driver->gafferFormat();
	}
	else
	{
		/// \todo We should not need the default value here - there should always be a default
		/// format in the context - something is broken in the Format mechanism.
		format = Context::current()->get<Format>( Format::defaultFormatContextName, Format() );
	}
	
	h.append( format.getDisplayWindow() );
	h.append( format.getPixelAspect() );
}

GafferImage::Format Display::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	Format format;
	if( m_driver )
	{
		format = m_driver->gafferFormat();
	}
	else
	{
		/// \todo We should not need the default value here - there should always be a default
		/// format in the context - something is broken in the Format mechanism.
		format = Context::current()->get<Format>( Format::defaultFormatContextName, Format() );
	}
	
	return format;
}

void Display::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashChannelNames( output, context, h );
	if( m_driver )
	{
		h.append(
			&(m_driver->channelNames()[0]),
			m_driver->channelNames().size()
		);
	}	
}

IECore::ConstStringVectorDataPtr Display::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	if( m_driver )
	{
		return new StringVectorData( m_driver->channelNames() );
	}
	return new StringVectorData();
}

void Display::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashDataWindow( output, context, h );
	Box2i dataWindow; // empty
	if( m_driver )
	{
		dataWindow = m_driver->gafferDataWindow();
	}
	h.append( dataWindow );
}

Imath::Box2i Display::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	if( m_driver )
	{
		return m_driver->gafferDataWindow();
	}
	return Box2i();
}

void Display::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ConstFloatVectorDataPtr channelData = ImagePlug::blackTile();
	if( m_driver )
	{
		channelData = m_driver->channelData(
			context->get<Imath::V2i>( ImagePlug::tileOriginContextName ),
			context->get<std::string>( ImagePlug::channelNameContextName )
		);
	}
	h = channelData->Object::hash();
}

IECore::ConstFloatVectorDataPtr Display::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstFloatVectorDataPtr channelData = ImagePlug::blackTile();
	if( m_driver )
	{
		channelData = m_driver->channelData(
			context->get<Imath::V2i>( ImagePlug::tileOriginContextName ),
			context->get<std::string>( ImagePlug::channelNameContextName )
		);
	}
	return channelData;
}

void Display::plugSet( Gaffer::Plug *plug )
{
	if( plug == portPlug() )
	{
		setupServer();
	}
}

void Display::setupServer()
{
	try
	{
		m_server = g_serverCache.get( portPlug()->getValue() );	
	}
	catch( const std::exception &e )
	{
		m_server = 0;
		msg( Msg::Error, "Display::setupServer", e.what() );
	}
}

void Display::driverCreated( GafferDisplayDriver *driver )
{
	ConstStringDataPtr portNumber = driver->parameters()->member<StringData>( "displayPort" );
	if( portNumber && boost::lexical_cast<int>( portNumber->readable() ) == portPlug()->getValue() )
	{
		setupDriver( driver );
	}
}

void Display::setupDriver( GafferDisplayDriverPtr driver )
{
	if( m_driver )
	{
		m_driver->dataReceivedSignal().disconnect( boost::bind( &Display::dataReceived, this, _1, _2 ) );
		m_driver->imageReceivedSignal().disconnect( boost::bind( &Display::imageReceived, this, _1 ) );
	}
	
	m_driver = driver;
	if( m_driver )
	{
		m_driver->dataReceivedSignal().connect( boost::bind( &Display::dataReceived, this, _1, _2 ) );	
		m_driver->imageReceivedSignal().connect( boost::bind( &Display::imageReceived, this, _1 ) );	
	}
}

void Display::dataReceived( GafferDisplayDriver *driver, const Imath::Box2i &bound )
{
	dataReceivedSignal()( outPlug() );
}

void Display::imageReceived( GafferDisplayDriver *driver )
{
	imageReceivedSignal()( outPlug() );
}
