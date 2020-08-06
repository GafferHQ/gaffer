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

#include "GafferImage/Display.h"

#include "GafferImage/FormatPlug.h"

#include "Gaffer/Context.h"
#include "Gaffer/DirtyPropagationScope.h"
#include "Gaffer/ParallelAlgo.h"

#include "IECoreImage/DisplayDriver.h"

#include "IECore/BoxOps.h"
#include "IECore/MessageHandler.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/multi_array.hpp"

#include "tbb/spin_mutex.h"

#include <memory>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Implementation of a DisplayDriver to support the node itself
//////////////////////////////////////////////////////////////////////////

namespace GafferImage
{

static const std::string g_headerPrefix = "header:";

class GafferDisplayDriver : public IECoreImage::DisplayDriver
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

			m_tileRange = Box3i(
				V3i( dataWindowMinTileIndex.x, dataWindowMinTileIndex.y, 0 ),
				V3i( dataWindowMaxTileIndex.x + 1, dataWindowMaxTileIndex.y + 1, channelNames.size() )
			);
			m_tiles.resize( m_tileRange.size().x * m_tileRange.size().y * m_tileRange.size().z );

			m_parameters = parameters ? parameters->copy() : CompoundDataPtr( new CompoundData );
			CompoundDataPtr metadata = new CompoundData;
			for( const auto &p : m_parameters->readable() )
			{
				if( boost::starts_with( p.first.string(), g_headerPrefix ) )
				{
					metadata->writable()[p.first.string().substr( g_headerPrefix.size() )] = p.second;
				}
			}
			m_metadata = metadata;

			if( const FloatData *pixelAspect = m_parameters->member<FloatData>( "pixelAspect" ) )
			{
				/// \todo Give IECore::Display a Format rather than just
				/// a display window, then we won't need this workaround.
				m_gafferFormat.setPixelAspect( pixelAspect->readable() );
			}

			// This is a bit sketchy. By creating `Ptr( this )` we're adding a reference to ourselves from within
			// our own constructor - if that reference is dropped before we return, we'll be double deleted. We rely
			// on the fact that callOnUIThread() will keep us alive long enough for this not to occur.
			ParallelAlgo::callOnUIThread( boost::bind( &GafferDisplayDriver::emitDriverCreated, Ptr( this ), m_parameters ) );
		}

		GafferDisplayDriver( GafferDisplayDriver &other )
			:	DisplayDriver( other.displayWindow(), other.dataWindow(), other.channelNames(), other.parameters() ),
				m_gafferFormat( other.m_gafferFormat ), m_gafferDataWindow( other.m_gafferDataWindow ),
				m_parameters( other.m_parameters ), m_metadata( other.m_metadata )
		{
			m_tileRange = other.m_tileRange;

			m_tiles.resize( other.m_tiles.size() );

			for( unsigned int i = 0; i < other.m_tiles.size(); i++ )
			{
				tbb::spin_rw_mutex::scoped_lock tileLock( other.m_tiles[i].mutex, /* write = */ false );
				m_tiles[i] = other.m_tiles[i];
			}
		}

		~GafferDisplayDriver() override
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

		const CompoundData *metadata() const
		{
			return m_metadata.get();
		}

		void imageData( const Imath::Box2i &box, const float *data, size_t dataSize ) override
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
						Tile * tile = getTile( tileOrigin, channelIndex );
						if( !tile )
						{
							// we've been sent data outside of the data window
							continue;
						}


						// we must create a new object to hold the updated tile data,
						// because the old one might well have been returned from
						// computeChannelData and be being held in the cache.
						vector<float> &buffer = tile->backBuffer;

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
								buffer[dstIndex] = data[srcIndex];
								srcIndex += numChannels;
								dstIndex++;
							}
						}

						tile->dirty = true;
					}
				}
			}

			dataReceivedSignal()( this, box );
		}

		void imageClose() override
		{
			imageReceivedSignal()( this );
		}

		bool scanLineOrderOnly() const override
		{
			return false;
		}

		bool acceptsRepeatedData() const override
		{
			return true;
		}

		ConstFloatVectorDataPtr channelData( const Imath::V2i &tileOrigin, const std::string &channelName, int dataCount )
		{
			vector<string>::const_iterator cIt = find( channelNames().begin(), channelNames().end(), channelName );
			if( cIt == channelNames().end() )
			{
				return ImagePlug::blackTile();
			}

			Tile *tile = getTile( tileOrigin, cIt - channelNames().begin() );
			if( !tile )
			{
				return ImagePlug::blackTile();
			}

			int previousDataCount;

			{
				tbb::spin_rw_mutex::scoped_lock tileLock( tile->mutex, false /* read */ );

				previousDataCount = tile->cachedForDataCount;

				if( tile->cachedForDataCount == dataCount || !tile->dirty)
				{
					// In order to ensure hashes and computes are consistent, once we have
					// bound a version of the tile for this dataCount, we don't change it,
					// even if it has been dirtied in the meantime.
					return tile->cachedTile;
				}
			}

			// This is labelled as const just so we can swap it with the cachedTile
			ConstFloatVectorDataPtr newCache = new FloatVectorData();
			const_cast<FloatVectorData*>( newCache.get() )->writable() = tile->backBuffer;

			{
				tbb::spin_rw_mutex::scoped_lock tileLock( tile->mutex, true /* write */ );

				if( tile->cachedForDataCount != previousDataCount && tile->cachedForDataCount >= dataCount )
				{
					// Another process has beaten us to write the cache, and their data count was >= ours,
					// so we discard our update and just use theirs.
					// Note that there is a miniscule chance that this could be wrong, if we hit this weird race
					// condition right at the moment when the dataCount wraps around, but since this is
					// exceedingly unlikely, and the symptom of this error is just a tile that's one update out of
					// date until we receive the next update, this doesn't seem too concerning.
				}
				else
				{
					tile->cachedTile.swap( newCache );
					tile->dirty = false;
				}

			}

			newCache = nullptr;

			tbb::spin_rw_mutex::scoped_lock tileLock( tile->mutex, false /* read */ );
			return tile->cachedTile;
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

		struct Tile
		{
			Tile(): backBufferData( ImagePlug::blackTile()->copy() ), backBuffer( backBufferData->writable() ), dirty( false ), cachedTile( ImagePlug::blackTile() ), cachedForDataCount( 0 )
			{
			}

			Tile( const Tile& other ) : Tile()
			{
				*this = other;
			}

			Tile& operator=( const Tile& other )
			{
				memcpy( &backBuffer[0], &other.backBuffer[0], backBuffer.size() * sizeof( float ) );
				dirty = (bool)other.dirty;
				cachedTile = other.cachedTile;
				cachedForDataCount = other.cachedForDataCount;
				return *this;
			}

			FloatVectorDataPtr backBufferData;
			std::vector<float> &backBuffer;
			std::atomic<bool> dirty;
			tbb::spin_rw_mutex mutex;

			// Use mutex to access these 2
			ConstFloatVectorDataPtr cachedTile;
			int cachedForDataCount;
		};

		Tile *getTile( const V2i &tileOrigin, unsigned int channelIndex )
		{
			V3i tileCoord( tileOrigin.x / ImagePlug::tileSize(), tileOrigin.y / ImagePlug::tileSize(), channelIndex );


			if( !( m_tileRange.intersects( tileCoord ) && m_tileRange.intersects( tileCoord + V3i( 1 ) ) ) )
			{
				// outside data window
				return nullptr;
			}

			V3i s = m_tileRange.size();
			V3i offset = tileCoord - m_tileRange.min;
			return &m_tiles[offset.x + offset.y * s.x + offset.z * s.x * s.y];
		}

		// indexed by tileIndexX, tileIndexY, channelIndex, with y and then z wrapped around into a flat vector
		Box3i m_tileRange;
		std::vector<Tile> m_tiles;

		Format m_gafferFormat;
		Imath::Box2i m_gafferDataWindow;
		IECore::ConstCompoundDataPtr m_parameters;
		IECore::ConstCompoundDataPtr m_metadata;
		DataReceivedSignal m_dataReceivedSignal;
		ImageReceivedSignal m_imageReceivedSignal;

};

const IECoreImage::DisplayDriver::DisplayDriverDescription<GafferDisplayDriver> GafferDisplayDriver::g_description;

} // namespace GafferImage

//////////////////////////////////////////////////////////////////////////
// Implementation of the Display class itself
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Display );

size_t Display::g_firstPlugIndex = 0;

Display::Display( const std::string &name )
	:	ImageNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	// This plug is incremented when a new driver is set, triggering dirty signals
	// on all output plugs and prompting reevaluation in the viewer.
	addChild(
		new IntPlug(
			"__driverCount",
			Plug::In,
			0,
			0,
			Imath::limits<int>::max(),
			Plug::Default & ~Plug::Serialisable
		)
	);

	// This plug is incremented when new data is received, triggering dirty signals
	// on only the channel data plug and prompting reevaluation in the viewer.
	addChild(
		new IntPlug(
			"__channelDataCount",
			Plug::In,
			0,
			0,
			Imath::limits<int>::max(),
			Plug::Default & ~Plug::Serialisable
		)
	);
}

Display::~Display()
{
}

Gaffer::IntPlug *Display::driverCountPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *Display::driverCountPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *Display::channelDataCountPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *Display::channelDataCountPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

void Display::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageNode::affects( input, outputs );

	if( input == driverCountPlug() )
	{
		for( ValuePlugIterator it( outPlug() ); !it.done(); ++it )
		{
			outputs.push_back( it->get() );
		}
	}
	else if( input == channelDataCountPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

Display::DriverCreatedSignal &Display::driverCreatedSignal()
{
	static DriverCreatedSignal s;
	return s;
}

Node::UnaryPlugSignal &Display::imageReceivedSignal()
{
	static UnaryPlugSignal s;
	return s;
}

void Display::setDriver( IECoreImage::DisplayDriverPtr driver, bool copy )
{
	GafferDisplayDriver *gafferDisplayDriver = runTimeCast<GafferDisplayDriver>( driver.get() );
	if( !gafferDisplayDriver )
	{
		throw IECore::Exception( "Expected GafferDisplayDriver" );
	}

	setupDriver( copy ? new GafferDisplayDriver( *gafferDisplayDriver ) : gafferDisplayDriver );

	driverCountPlug()->setValue( driverCountPlug()->getValue() + 1 );
}

IECoreImage::DisplayDriver *Display::getDriver()
{
	return m_driver.get();
}

const IECoreImage::DisplayDriver *Display::getDriver() const
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

	h.append( format.getDisplayWindow().min );
	h.append( format.getDisplayWindow().max );
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

void Display::hashMetadata( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const CompoundData *d = m_driver ? m_driver->metadata() : outPlug()->metadataPlug()->defaultValue();
	h = d->Object::hash();
}

IECore::ConstCompoundDataPtr Display::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return m_driver ? m_driver->metadata() : outPlug()->metadataPlug()->defaultValue();
}

void Display::hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h.append( false );
}

bool Display::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return false;
}

void Display::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = ImagePlug::flatTileSampleOffsets()->Object::hash();
}

IECore::ConstIntVectorDataPtr Display::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::flatTileSampleOffsets();
}

void Display::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ConstFloatVectorDataPtr channelData = ImagePlug::blackTile();
	if( m_driver )
	{
		channelData = m_driver->channelData(
			context->get<Imath::V2i>( ImagePlug::tileOriginContextName ),
			context->get<std::string>( ImagePlug::channelNameContextName ),
			channelDataCountPlug()->getValue()
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
			context->get<std::string>( ImagePlug::channelNameContextName ),
			channelDataCountPlug()->getValue()
		);
	}
	return channelData;
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
typedef std::unique_ptr<PlugSet> PlugSetPtr;

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

// Called on a background thread when data is received on the driver.
// We need to increment `channelDataCountPlug()`, but all graph edits must
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
		ParallelAlgo::callOnUIThread( &Display::dataReceivedUI );
	}
}

// Called on the UI thread after being scheduled by `dataReceived()`.
void Display::dataReceivedUI()
{
	// Get the batch of plugs to trigger updates for. We want to hold the mutex
	// for the shortest duration possible, because it causes contention between
	// the background rendering thread and the UI thread, and can significantly
	// affect performance.  We do this by "stealing" the current batch, so the
	// background thread will create a new batch and we are safe to iterate our
	// batch without holding the lock.
	PlugSetPtr batch;
	{
		PendingUpdates &pending = pendingUpdates();
		tbb::spin_mutex::scoped_lock lock( pending.mutex );
		batch.reset( pending.plugs.release() );
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
				display->channelDataCountPlug()->setValue( display->channelDataCountPlug()->getValue() + 1 );
			}
		}
	}
}

void Display::imageReceived()
{
	ParallelAlgo::callOnUIThread( boost::bind( &Display::imageReceivedUI, DisplayPtr( this ) ) );
}

void Display::imageReceivedUI( Ptr display )
{
	imageReceivedSignal()( display->outPlug() );
}
