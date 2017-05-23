//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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
#include "Gaffer/DirtyPropagationScope.h"

#include "GafferImage/Display.h"
#include "GafferImage/FormatPlug.h"

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
				m_gafferFormat( displayWindow, 1, /* fromEXRSpace = */ true ),
				m_gafferDataWindow( m_gafferFormat.fromEXRSpace( dataWindow ) )
		{
			const V2i dataWindowMinTileIndex = ImagePlug::tileOrigin( m_gafferDataWindow.min ) / ImagePlug::tileSize();
			const V2i dataWindowMaxTileIndex = ImagePlug::tileOrigin( m_gafferDataWindow.max - Imath::V2i( 1 ) ) / ImagePlug::tileSize();

			m_tiles.resize(
				TileArray::extent_gen()
					[TileArray::extent_range( dataWindowMinTileIndex.x, dataWindowMaxTileIndex.x + 1 )]
					[TileArray::extent_range( dataWindowMinTileIndex.y, dataWindowMaxTileIndex.y + 1 )]
					[channelNames.size()]
			);

			m_parameters = parameters ? parameters->copy() : CompoundDataPtr( new CompoundData );

			if( const FloatData *pixelAspect = m_parameters->member<FloatData>( "pixelAspect" ) )
			{
				/// \todo Give IECore::Display a Format rather than just
				/// a display window, then we won't need this workaround.
				m_gafferFormat.setPixelAspect( pixelAspect->readable() );
			}

			// This is a bit sketchy. By creating `Ptr( this )` we're adding a reference to ourselves from within
			// our own constructor - if that reference is dropped before we return, we'll be double deleted. We rely
			// on the fact that executeOnUIThreadl() will keep us alive long enough for this not to occur.
			Display::executeOnUIThread( boost::bind( &GafferDisplayDriver::emitDriverCreated, Ptr( this ), m_parameters ) );
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
			Box2i gafferBox = m_gafferFormat.fromEXRSpace( box );

			const V2i boxMinTileOrigin = ImagePlug::tileOrigin( gafferBox.min );
			const V2i boxMaxTileOrigin = ImagePlug::tileOrigin( gafferBox.max - Imath::V2i( 1 ) );
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

						const Box2i tileBound( tileOrigin, tileOrigin + Imath::V2i( GafferImage::ImagePlug::tileSize() ) );
						const Box2i transferBound = IECore::boxIntersection( tileBound, gafferBox );

						for( int y = transferBound.min.y; y<transferBound.max.y; ++y )
						{
							int srcY = m_gafferFormat.toEXRSpace( y );
							size_t srcIndex = ( ( srcY - box.min.y ) * ( box.size().x + 1 ) + ( transferBound.min.x - box.min.x ) ) * numChannels + channelIndex;
							size_t dstIndex = ( y - tileBound.min.y ) * ImagePlug::tileSize() + transferBound.min.x - tileBound.min.x;
							const size_t srcEndIndex = srcIndex + transferBound.size().x * numChannels;
							while( srcIndex < srcEndIndex )
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

	private :

		static const DisplayDriverDescription<GafferDisplayDriver> g_description;

		static void emitDriverCreated( Ptr driver, IECore::ConstCompoundDataPtr parameters )
		{
			Display::driverCreatedSignal()( driver.get(), parameters.get() );
		}

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

	// This plug is incremented when new data is received, triggering dirty signals
	// and prompting reevaluation in the viewer.
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
	driverCreatedSignal().connect( boost::bind( &Display::driverCreated, this, ::_1 ) );
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
		for( ValuePlugIterator it( outPlug() ); !it.done(); ++it )
		{
			outputs.push_back( it->get() );
		}
	}
}

Display::DriverCreatedSignal &Display::driverCreatedSignal()
{
	static DriverCreatedSignal s;
	return s;
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

void Display::setDriver( IECore::DisplayDriverPtr driver )
{
	GafferDisplayDriver *gafferDisplayDriver = runTimeCast<GafferDisplayDriver>( driver.get() );
	if( !gafferDisplayDriver )
	{
		throw IECore::Exception( "Expected GafferDisplayDriver" );
	}

	setupDriver( gafferDisplayDriver );
}

IECore::DisplayDriver *Display::getDriver()
{
	return m_driver.get();
}

const IECore::DisplayDriver *Display::getDriver() const
{
	return m_driver.get();
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
		format = FormatPlug::getDefaultFormat( Context::current() );
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
		format = FormatPlug::getDefaultFormat( context );
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

IECore::ConstCompoundDataPtr Display::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return outPlug()->metadataPlug()->defaultValue();
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
	if( executeOnUIThreadSignal().empty() )
	{
		// If the executeOnUIThreadSignal is empty,
		// it means that GafferImageUI hasn't
		// been imported (see DisplayUI.py).
		// If there's no UI then there's no point
		// running a server because no-one will
		// be looking anyway.
		//
		// This allows us to avoid confusing error output
		// when the script is loaded in a separate process
		// to do a local render dispatch, and the
		// Display node trys to reuse the port that
		// is already in use in the main GUI process.
		return;
	}

	try
	{
		m_server = g_serverCache.get( portPlug()->getValue() );
	}
	catch( const std::exception &e )
	{
		m_server = 0;
		g_serverCache.erase( portPlug()->getValue() );
		msg( Msg::Error, "Display::setupServer", e.what() );
	}
}

void Display::driverCreated( IECore::DisplayDriver *driver )
{
	GafferDisplayDriver *gafferDisplayDriver = runTimeCast<GafferDisplayDriver>( driver );
	if( !gafferDisplayDriver )
	{
		return;
	}

	const StringData *portNumber = gafferDisplayDriver->parameters()->member<StringData>( "displayPort" );
	if( portNumber && boost::lexical_cast<int>( portNumber->readable() ) == portPlug()->getValue() )
	{
		setupDriver( gafferDisplayDriver );
	}
}

void Display::setupDriver( GafferDisplayDriverPtr driver )
{
	if( m_driver )
	{
		m_driver->dataReceivedSignal().disconnect( boost::bind( &Display::dataReceived, this) );
		m_driver->imageReceivedSignal().disconnect( boost::bind( &Display::imageReceived, this ) );
	}

	m_driver = driver;
	if( m_driver )
	{
		m_driver->dataReceivedSignal().connect( boost::bind( &Display::dataReceived, this ) );
		m_driver->imageReceivedSignal().connect( boost::bind( &Display::imageReceived, this ) );
	}
}

//////////////////////////////////////////////////////////////////////////
// Signalling and update mechanism
//////////////////////////////////////////////////////////////////////////

namespace
{

typedef set<PlugPtr> PlugSet;
typedef auto_ptr<PlugSet> PlugSetPtr;

struct PendingUpdates
{

	tbb::spin_mutex mutex;
	PlugSetPtr plugs;

};

PendingUpdates &pendingUpdates()
{
	static PendingUpdates *p = new PendingUpdates;
	return *p;
}

};

void Display::executeOnUIThread( UIThreadFunction function )
{
	executeOnUIThreadSignal()( function );
}

// Called on a background thread when data is received on the driver.
// We need to increment `updateCountPlug()`, but all graph edits must
// be performed on the UI thread, so we can't do it directly.
void Display::dataReceived()
{
	bool scheduleUpdate = false;
	{
		// To minimise overhead we perform updates in batches by storing
		// a set of plugs which are pending update. If we're the creator
		// of a new batch then we are responsible for scheduling a call
		// to `dataReceivedUI()` to process the batch. Otherwise we just
		// add to the current batch.
		PendingUpdates &pending = pendingUpdates();
		tbb::spin_mutex::scoped_lock lock( pending.mutex );
		if( !pending.plugs.get() )
		{
			scheduleUpdate = true;
			pending.plugs.reset( new PlugSet );
		}
		pending.plugs->insert( outPlug() );
	}
	if( scheduleUpdate )
	{
		executeOnUIThread( &Display::dataReceivedUI );
	}
}

// Called on the UI thread after being scheduled by `dataReceived()`.
void Display::dataReceivedUI()
{
	// Get the batch of plugs to trigger updates for. We want to hold
	// g_plugsPendingUpdateMutex for the shortest duration possible,
	// because it causes contention between the background rendering
	// thread and the UI thread, and can significantly affect performance.
	// We do this by "stealing" the current batch, so the background
	// thread will create a new batch and we are safe to iterate our
	// batch without holding the lock.
	PlugSetPtr batch;
	{
		PendingUpdates &pending = pendingUpdates();
		tbb::spin_mutex::scoped_lock lock( pending.mutex );
		batch = pending.plugs; // Resets pending.plugs to NULL
	}

	// Now increment the update count for the Display nodes
	// that have received data. This gives them a new hash
	// and also propagates dirtiness to the output image.
	{
		// Use a DirtyPropgationScope to batch up dirty propagation
		// for improved performance.
		DirtyPropagationScope dirtyPropagationScope;
		for( set<PlugPtr>::const_iterator it = batch->begin(), eIt = batch->end(); it != eIt; ++it )
		{
			PlugPtr plug = *it;
			// Because `dataReceivedUI()` is deferred to the UI thread,
			// it's possible that the node has actually been deleted by
			// the time we're called, so we must check.
			if( Display *display = runTimeCast<Display>( plug->node() ) )
			{
				display->updateCountPlug()->setValue( display->updateCountPlug()->getValue() + 1 );
			}
		}
	}

	// Now that dirty propagation is complete, we can emit dataReceivedSignal()
	// for any observers that wish to update that way.
	/// \todo Do we even need this now? Could the tests just use plugDirtiedSignal()?
	for( set<PlugPtr>::const_iterator it = batch->begin(), eIt = batch->end(); it != eIt; ++it )
	{
		dataReceivedSignal()( it->get() );
	}
}

void Display::imageReceived()
{
	executeOnUIThread( boost::bind( &Display::imageReceivedUI, DisplayPtr( this ) ) );
}

void Display::imageReceivedUI( Ptr display )
{
	imageReceivedSignal()( display->outPlug() );
}

Display::ExecuteOnUIThreadSignal &Display::executeOnUIThreadSignal()
{
	static ExecuteOnUIThreadSignal s;
	return s;
}
