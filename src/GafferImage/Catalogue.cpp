//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
//      * Neither the name of Image Engine Design nor the names of
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

#include "GafferImage/Catalogue.h"

#include "GafferImage/Constant.h"
#include "GafferImage/CopyChannels.h"
#include "GafferImage/DeleteImageMetadata.h"
#include "GafferImage/Display.h"
#include "GafferImage/FormatQuery.h"
#include "GafferImage/ImageAlgo.h"
#include "GafferImage/ImageMetadata.h"
#include "GafferImage/ImageReader.h"
#include "GafferImage/ImageWriter.h"
#include "GafferImage/Text.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"
#include "Gaffer/DownstreamIterator.h"
#include "Gaffer/ParallelAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"

#include "IECore/NullObject.h"

#include "boost/algorithm/string.hpp"
#include "boost/bind/bind.hpp"
#include "boost/filesystem/operations.hpp"
#include "boost/filesystem/path.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/regex.hpp"
#include "boost/unordered_map.hpp"

#include <thread>
#include <unordered_map>

using namespace std;
using namespace boost::placeholders;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Allow Imath::V2i to be used in boost::unordered_map
//////////////////////////////////////////////////////////////////////////

IMATH_INTERNAL_NAMESPACE_HEADER_ENTER

size_t hash_value( const Imath::V2i &v )
{
	size_t s = 0;
	boost::hash_combine( s, v.x );
	boost::hash_combine( s, v.y );
	return s;
}

IMATH_INTERNAL_NAMESPACE_HEADER_EXIT

namespace
{
	// Used by imageIndexMapPlug()
	struct ImageIndexMapData : public IECore::Data
	{
		using Map = std::unordered_map< std::string, int >;
		Map map;
	};
	IE_CORE_DECLAREPTR( ImageIndexMapData )

	std::string g_isRenderingMetadataName = "gaffer:isRendering";
	std::string g_emptyString( "" );
	std::string g_outputPrefix( "output:" );
	IECore::InternedString g_imageNameContextName( "catalogue:imageName" );
}

//////////////////////////////////////////////////////////////////////////
// InternalImage.
// This node type provides the internal implementation of the images
// specified by the public Image plugs.
//////////////////////////////////////////////////////////////////////////

class Catalogue::InternalImage : public ImageNode
{

	public :

		InternalImage( const std::string &name = "InternalImage" )
			:	ImageNode( name ), m_clientPID( -1 ), m_numDriversClosed( 0 )
		{
			storeIndexOfNextChild( g_firstChildIndex );

			addChild( new StringPlug( "fileName" ) );
			addChild( new StringPlug( "description" ) );

			// Used to load an image from disk, according to
			// the fileName plug.
			addChild( new ImageReader() );
			imageReader()->fileNamePlug()->setInput( fileNamePlug() );

			// Used to merge all channels from multiple
			// incoming Display nodes.
			addChild( new CopyChannels() );
			copyChannels()->channelsPlug()->setValue( "*" );

			// Used to overlay a "Saving..." message
			// while displays are being saved to disk in
			// the background.
			addChild( new Text() );
			text()->inPlug()->setInput( copyChannels()->outPlug() );
			text()->colorPlug()->setValue( Imath::Color4f( 1, 1, 1, 0.75 ) );
			text()->textPlug()->setValue( "Saving..." );
			text()->horizontalAlignmentPlug()->setValue( Text::HorizontalCenter );
			text()->verticalAlignmentPlug()->setValue( Text::VerticalCenter );
			text()->shadowPlug()->setValue( true );
			text()->shadowColorPlug()->setValue( Imath::Color4f( 0, 0, 0, 0.75 ) );
			text()->shadowOffsetPlug()->setValue( Imath::V2f( 3.5, -3.5 ) );
			text()->shadowBlurPlug()->setValue( 5 );
			text()->enabledPlug()->setValue( false );

			// Switches between the loaded image and the
			// live Displays.
			addChild( new Switch() );
			imageSwitch()->setup( outPlug() );
			imageSwitch()->inPlugs()->getChild<ImagePlug>( 0 )->setInput( imageReader()->outPlug() );
			imageSwitch()->inPlugs()->getChild<ImagePlug>( 1 )->setInput( text()->outPlug() );

			// Adds on a description to the output
			addChild( new ImageMetadata() );
			imageMetadata()->inPlug()->setInput( imageSwitch()->outPlug() );

			NameValuePlugPtr descriptionMeta = new NameValuePlug( "ImageDescription", new StringData(), true, "imageDescription" );
			imageMetadata()->metadataPlug()->addChild( descriptionMeta );
			descriptionMeta->valuePlug()->setInput( descriptionPlug() );
			descriptionMeta->enabledPlug()->setInput( descriptionPlug() ); // Enable only for non-empty strings

			NameValuePlugPtr isRenderingMeta = new NameValuePlug( g_isRenderingMetadataName, new BoolData( true ), true, "isRendering" );
			imageMetadata()->metadataPlug()->addChild( isRenderingMeta );

			outPlug()->setInput( imageMetadata()->outPlug() );

			isRendering( false );
		}

		~InternalImage() override
		{
			if( m_saver )
			{
				m_saver->deregisterClient( this );
			}
		}

		StringPlug *fileNamePlug()
		{
			return getChild<StringPlug>( g_firstChildIndex );
		}

		const StringPlug *fileNamePlug() const
		{
			return getChild<StringPlug>( g_firstChildIndex );
		}

		StringPlug *descriptionPlug()
		{
			return getChild<StringPlug>( g_firstChildIndex + 1 );
		}

		const StringPlug *descriptionPlug() const
		{
			return getChild<StringPlug>( g_firstChildIndex + 1 );
		}

		void copyFrom( const InternalImage *other )
		{
			descriptionPlug()->source<StringPlug>()->setValue( other->descriptionPlug()->getValue() );
			fileNamePlug()->source<StringPlug>()->setValue( other->fileNamePlug()->getValue() );
			imageSwitch()->indexPlug()->setValue( other->imageSwitch()->indexPlug()->getValue() );
			text()->enabledPlug()->setValue( other->text()->enabledPlug()->getValue() );

			removeDisplays();
			size_t numDisplays = 0;
			for( Display::Iterator it( other ); !it.done(); ++it )
			{
				Display *display = it->get();
				DisplayPtr displayCopy = new Display;
				displayCopy->setDriver( display->getDriver(), /* copy = */ true );
				addChild( displayCopy );
				copyChannels()->inPlugs()->getChild<Plug>( numDisplays++ )->setInput( displayCopy->outPlug() );
			}

			isRendering( false );

			m_saver = nullptr;
			if( other->m_saver )
			{
				m_saver = other->m_saver;
				m_saver->registerClient( this );
			}
			else if( numDisplays )
			{
				m_saver = AsynchronousSaver::create( this );
			}

			m_clientPID = -2; // Make sure insertDriver() will reject new drivers
		}

		void save( const std::string &fileName ) const
		{
			DeleteImageMetadataPtr deleteMetadata = new DeleteImageMetadata();
			deleteMetadata->inPlug()->setInput( const_cast<ImagePlug *>( outPlug() ) );
			deleteMetadata->namesPlug()->setValue( g_isRenderingMetadataName );
			ImageWriterPtr imageWriter = new ImageWriter;
			imageWriter->inPlug()->setInput( deleteMetadata->outPlug() );
			imageWriter->fileNamePlug()->setValue( fileName );
			imageWriter->taskPlug()->execute();
		}

		bool insertDriver( IECoreImage::DisplayDriverPtr driver, const IECore::CompoundData *parameters )
		{
			// If we represent a disk-based image, we can't accept
			// a render.
			if( fileNamePlug()->getValue() != "" )
			{
				return false;
			}

			// If we already represent a render, we can't
			// accept a different one.
			const IntData *clientPID = parameters->member<IntData>( "clientPID" );
			if( m_clientPID != -1 && clientPID && clientPID->readable() != m_clientPID )
			{
				return false;
			}

			// The clientPID mechanism isn't foolproof,
			// so if the channels in the new driver clash
			// with the existing channels, we must assume
			// they're from another render.

			const vector<string> &channels = driver->channelNames();

			if( copyChannels()->outPlug()->viewNames()->readable() != ImagePlug::defaultViewNames()->readable() )
			{
				throw IECore::Exception( "Catalogue::insertDriver : Multi-view images not supported" );
			}

			ConstStringVectorDataPtr existingChannelsData;
			{
				ImagePlug::ViewScope viewScope( Context::current() );
				viewScope.setViewName( &ImagePlug::defaultViewName );
				existingChannelsData = copyChannels()->outPlug()->channelNamesPlug()->getValue();
			}

			const vector<string> &existingChannels = existingChannelsData->readable();
			for( vector<string>::const_iterator it = channels.begin(), eIt = channels.end(); it != eIt; ++it )
			{
				if( find( existingChannels.begin(), existingChannels.end(), *it ) != existingChannels.end() )
				{
					return false;
				}
			}

			// All is well - insert the display.
			DisplayPtr display = new Display;
			display->setDriver( driver );
			addChild( display );
			ArrayPlug *a = copyChannels()->inPlugs();
			size_t nextIndex = a->children().size() - 1;
			if( nextIndex == 1 && !a->getChild<ImagePlug>( 0 )->getInput() )
			{
				// CopyChannels starts with two input plugs, and we must use
				// the first one to make sure the format etc is passed through.
				nextIndex = 0;
			}

			a->getChild<ImagePlug>( nextIndex )->setInput( display->outPlug() );
			imageSwitch()->indexPlug()->setValue( 1 );

			if( clientPID )
			{
				m_clientPID = clientPID->readable();
			}

			if( auto nameData = parameters->member<StringData>( "catalogue:imageName" ) )
			{
				if( Plug *p = fileNamePlug()->getInput() )
				{
					if( Image *image = p->source()->parent<Image>() )
					{
						/// \todo GraphComponent or GraphComponentAlgo really should have
						/// a utility for sanitising names and/or we should loosen the naming
						/// restrictions anyway.
						const std::string name = boost::regex_replace(
							nameData->readable(),
							boost::regex( "(^[0-9])|([^0-9a-zA-Z_]+)" ),
							"_"
						);
						image->setName( name );
					}
				}
			}

			updateImageFlags( Plug::Serialisable, false ); // Don't serialise in-progress renders
			isRendering( true );

			return true;
		}

		void driverClosed()
		{
			m_numDriversClosed++;
			if( m_numDriversClosed != copyChannels()->inPlugs()->children().size() - 1 )
			{
				return;
			}

			// All our drivers have been closed, so the render has completed.
			// Save the image to disk. We do this in the background because
			// saving large images with many AOVs takes several seconds.

			isRendering( false );
			m_saver = AsynchronousSaver::create( this );
		}

	protected :

		void hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override
		{
			assert( m_saver );
			AsynchronousSaver::ChannelDataHashes::const_iterator it = m_saver->channelDataHashes.find(
				AsynchronousSaver::TileIndex(
					context->get<string>( ImagePlug::channelNameContextName ),
					context->get<Imath::V2i>( ImagePlug::tileOriginContextName )
				)
			);
			if( it != m_saver->channelDataHashes.end() )
			{
				h = it->second;
			}
			else
			{
				h = imageReader()->outPlug()->channelDataPlug()->hash();
			}
		}

		IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const override
		{
			return imageReader()->outPlug()->channelDataPlug()->getValue();
		}

	private :

		void isRendering( bool rendering )
		{
			NameValuePlug *isRendering = static_cast<NameValuePlug *>( imageMetadata()->metadataPlug()->getChild( "isRendering" ) );
			static_cast<BoolPlug *>( isRendering->enabledPlug() )->setValue( rendering );
		}

		void updateImageFlags( unsigned flags, bool enable )
		{
			Plug *p = fileNamePlug()->getInput();
			if( !p )
			{
				return;
			}
			for( Image *i = p->parent<Image>(); i; i = i->getInput<Image>() )
			{
				i->setFlags( flags, enable );
			}
		}

		void removeDisplays()
		{
			vector<Display *> toDelete;
			for( Display::Iterator it( this ); !it.done(); ++it )
			{
				toDelete.push_back( it->get() );
			}
			for( vector<Display *>::const_iterator it = toDelete.begin(), eIt = toDelete.end(); it != eIt; ++it )
			{
				removeChild( *it );
			}
		}

		ImageReader *imageReader()
		{
			return getChild<ImageReader>( g_firstChildIndex + 2 );
		}

		const ImageReader *imageReader() const
		{
			return getChild<ImageReader>( g_firstChildIndex + 2 );
		}

		CopyChannels *copyChannels()
		{
			return getChild<CopyChannels>( g_firstChildIndex + 3 );
		}

		const CopyChannels *copyChannels() const
		{
			return getChild<CopyChannels>( g_firstChildIndex + 3 );
		}

		Text *text()
		{
			return getChild<Text>( g_firstChildIndex + 4 );
		}

		const Text *text() const
		{
			return getChild<Text>( g_firstChildIndex + 4 );
		}

		Switch *imageSwitch()
		{
			return getChild<Switch>( g_firstChildIndex + 5 );
		}

		const Switch *imageSwitch() const
		{
			return getChild<Switch>( g_firstChildIndex + 5 );
		}

		ImageMetadata *imageMetadata()
		{
			return getChild<ImageMetadata>( g_firstChildIndex + 6 );
		}

		const ImageMetadata *imageMetadata() const
		{
			return getChild<ImageMetadata>( g_firstChildIndex + 6 );
		}

		struct AsynchronousSaver
		{

			using Ptr = std::shared_ptr<AsynchronousSaver>;
			using WeakPtr = std::weak_ptr<AsynchronousSaver>;

			static Ptr create( InternalImage *client )
			{
				// We use a copy of the image to do the saving, because the original
				// might be modified on the main thread while we save in the background.

				InternalImagePtr imageCopy = new InternalImage;

				size_t i = 0;
				for( Display::Iterator it( client ); !it.done(); ++it )
				{
					Display *display = it->get();
					DisplayPtr displayCopy = new Display;
					displayCopy->setDriver( display->getDriver(), /* copy = */ true );
					imageCopy->addChild( displayCopy );
					imageCopy->copyChannels()->inPlugs()->getChild<Plug>( i++ )->setInput( displayCopy->outPlug() );
				}
				imageCopy->imageSwitch()->indexPlug()->setValue( 1 );

				// If there's nowhere to save, then a saver is useless, so return null.
				const string fileName = client->parent<Catalogue>()->generateFileName( imageCopy->outPlug() );
				if( fileName.empty() )
				{
					return nullptr;
				}

				// Otherwise, make a saver and schedule its background execution.
				Ptr saver = Ptr( new AsynchronousSaver( imageCopy, fileName ) );
				saver->registerClient( client );

				// Note that the background thread doesn't own a reference to the saver -
				// see ~AsychronousSaver for details.
				std::thread thread( boost::bind( &AsynchronousSaver::save, saver.get(), WeakPtr( saver ) ) );
				saver->m_thread.swap( thread );
				return saver;
			}

			virtual ~AsynchronousSaver()
			{
				// Wait for our background thread to complete. This achieves
				// two things :
				//
				// - Makes sure our member data is not deleted until the background
				//   thread has finished using it.
				// - Ensures that the background thread finishes before program shutdown
				//   reaches the stage of calling static destructors, at which point
				//   it would crash as the libraries it relies on are torn down around it.
				//
				// Note that for this to work, the background thread must _not_ own a
				// reference to `this`, as that would prevent destruction on the main
				// thread and never give us an opportunity to wait for the background
				// thread.
				m_thread.join();
			}

			void registerClient( InternalImage *client )
			{
				if( m_imageCopy )
				{
					// Still in the process of saving
					m_clients.insert( client );
					client->text()->enabledPlug()->setValue( true );
				}
				else
				{
					// Saving already completed
					DirtyPropagationScope dirtyPropagationScope;
					wrapUpClient( client );
				}
			}

			void deregisterClient( InternalImage *client )
			{
				m_clients.erase( client );
			}

			using TileIndex = std::pair<std::string, Imath::V2i>;
			using ChannelDataHashes = boost::unordered_map<TileIndex, IECore::MurmurHash>;
			ChannelDataHashes channelDataHashes;

			private :

				AsynchronousSaver( InternalImagePtr imageCopy, const std::string &fileName )
					:	m_imageCopy( imageCopy )
				{
					// Set up an ImageWriter to do the actual saving.
					// We do all graph construction here in the main thread
					// so that the background thread only does execution.
					m_writer = new ImageWriter;
					m_writer->inPlug()->setInput( m_imageCopy->outPlug() );
					m_writer->fileNamePlug()->setValue( fileName );
				}

				void save( WeakPtr forWrapUp )
				{
					if( m_imageCopy->copyChannels()->outPlug()->viewNames()->readable() != ImagePlug::defaultViewNames()->readable() )
					{
						IECore::msg( IECore::Msg::Error, "Saving Catalogue image", "Catalogue does not yet support multi-view images." );
					}

					{
						ImagePlug::ViewScope viewScope( Context::current() );
						viewScope.setViewName( &ImagePlug::defaultViewName );
						ImageAlgo::parallelGatherTiles(
							m_imageCopy->copyChannels()->outPlug(),
							m_imageCopy->copyChannels()->outPlug()->channelNamesPlug()->getValue()->readable(),
							// Tile
							[] ( const ImagePlug *imagePlug, const string &channelName, const Imath::V2i &tileOrigin )
							{
								return imagePlug->channelDataPlug()->hash();
							},
							// Gather
							[ this ] ( const ImagePlug *imagePlug, const string &channelName, const Imath::V2i &tileOrigin, const IECore::MurmurHash &tileHash )
							{
								channelDataHashes[TileIndex(channelName, tileOrigin)] = tileHash;
							}
						);
					}

					try
					{
						m_writer->taskPlug()->execute();
					}
					catch( const std::exception &e )
					{
						IECore::msg( IECore::Msg::Error, "Saving Catalogue image", e.what() );
					}

					// Schedule execution of wrapUp() on the UI thread,
					// to make our results visible to the user. Note that
					// we absolutely _must not_ create a Ptr here on the
					// background thread - ownership must be managed on
					// the UI thread only (see ~AsynchronousSaver).
					ParallelAlgo::callOnUIThread(
						[forWrapUp] {
							if( Ptr that = forWrapUp.lock() )
							{
								that->wrapUp();
							}
						}
					);
				}

				void wrapUp()
				{
					DirtyPropagationScope dirtyPropagationScope;

					for( set<InternalImage *>::const_iterator it = m_clients.begin(), eIt = m_clients.end(); it != eIt; ++it )
					{
						wrapUpClient( *it );
					}

					// Destroy the image to release the memory used by the copied display drivers.
					m_imageCopy = nullptr;
				}

				void wrapUpClient( InternalImage *client )
				{
					// Set up the client to read from the saved image
					client->text()->enabledPlug()->setValue( false );
					client->fileNamePlug()->source<StringPlug>()->setValue( m_writer->fileNamePlug()->getValue() );
					client->imageSwitch()->indexPlug()->setValue( 0 );
					// But force hashChannelData and computeChannelData to be called
					// so that we can reuse the cache entries created by the original
					// Display nodes, rather than force an immediate load of the image
					// from disk, which would be slow.
					client->outPlug()->channelDataPlug()->setInput( nullptr );

					client->removeDisplays();
					client->updateImageFlags( Plug::Serialisable, true );
				}

				InternalImagePtr m_imageCopy;
				ImageWriterPtr m_writer;

				std::thread m_thread;
				set<InternalImage *> m_clients;

		};

		int m_clientPID;
		size_t m_numDriversClosed;
		AsynchronousSaver::Ptr m_saver;

		static size_t g_firstChildIndex;

};

size_t Catalogue::InternalImage::g_firstChildIndex = 0;

//////////////////////////////////////////////////////////////////////////
// Image
//////////////////////////////////////////////////////////////////////////

GAFFER_PLUG_DEFINE_TYPE( Catalogue::Image );

Catalogue::Image::Image( const std::string &name, Direction direction, unsigned flags )
	:	Plug( name, direction, flags )
{
	addChild( new StringPlug( "fileName" ) );
	addChild( new StringPlug( "description" ) );
	addChild( new IntPlug( "outputIndex" ) );
	addChild( new StringPlug( "__name", Plug::In, name, Plug::Default & ~Plug::Serialisable ) );

	nameChangedSignal().connect( boost::bind( &Image::nameChanged, this ) );
}

Gaffer::StringPlug *Catalogue::Image::fileNamePlug()
{
	return getChild<StringPlug>( 0 );
}

const Gaffer::StringPlug *Catalogue::Image::fileNamePlug() const
{
	return getChild<StringPlug>( 0 );
}

Gaffer::StringPlug *Catalogue::Image::descriptionPlug()
{
	return getChild<StringPlug>( 1 );
}

const Gaffer::StringPlug *Catalogue::Image::descriptionPlug() const
{
	return getChild<StringPlug>( 1 );
}

Gaffer::IntPlug *Catalogue::Image::outputIndexPlug()
{
	return getChild<IntPlug>( 2 );
}

const Gaffer::IntPlug *Catalogue::Image::outputIndexPlug() const
{
	return getChild<IntPlug>( 2 );
}

Gaffer::StringPlug *Catalogue::Image::namePlug()
{
	return getChild<StringPlug>( 3 );
}

const Gaffer::StringPlug *Catalogue::Image::namePlug() const
{
	return getChild<StringPlug>( 3 );
}

void Catalogue::Image::copyFrom( const Image *other )
{
	imageNode( this )->copyFrom( imageNode( other ) );
}

Catalogue::Image::Ptr Catalogue::Image::load( const std::string &fileName )
{
	// GraphComponent names are much more restrictive than filenames, so
	// we must replace all non-alphanumeric characters with `_`, and make
	// sure it doesn't start with a number.
	/// \todo Relax these restrictions and/or provide automatic name
	/// sanitisation in GraphComponent.
	std::string name = boost::filesystem::path( fileName ).stem().string();
	std::replace_if(
		name.begin(), name.end(),
		[] ( char c ) {
			return !std::isalnum( c, std::locale::classic() );
		},
		'_'
	);
	if( std::isdigit( name[0], std::locale::classic() ) )
	{
		name = "_" + name;
	}

	Ptr image = new Image( name, Plug::In, Plug::Default | Plug::Dynamic );
	image->fileNamePlug()->setValue( fileName );

	return image;
}

void Catalogue::Image::save( const std::string &fileName ) const
{
	Catalogue::imageNode( this )->save( fileName );
}

Gaffer::PlugPtr Catalogue::Image::createCounterpart( const std::string &name, Direction direction ) const
{
	return new Image( name, direction, getFlags() );
}

void Catalogue::Image::nameChanged()
{
	if( !getInput() )
	{
		namePlug()->setValue( getName() );
	}
	else
	{
		// We have an input, so can't call `namePlug()->setValue()`.
		// This typically occurs when `Catalogue.images` has been promoted
		// to a Box or custom node. Ideally we would override `setInput()`
		// and update the name when we lose our input, but the virtual
		// `setInput()` is only called for the top level `setInput()` call
		// and our input will most likely be managed as a child of the
		// entire `images` plug. Doing nothing is OK in practice because
		// we don't expect a promoted `images` plug to be disconnected, and
		// if it was, we'd be losing all the promoted values for `fileNamePlug()`
		// etc anyway.
		//
		// > Note : ValuePlug.cpp has a todo for replacing the flawed `virtual setInput()`
		// > with a non-virtual public method and a protected `virtual inputChanging()`
		// > method. If we added a protected `virtual inputChanged()` method to that
		// > then we could be 100% reliable here, and the new API would closely
		// > match `parentChanging()/parentChanged()` from GraphComponent.
	}
}


//////////////////////////////////////////////////////////////////////////
// Catalogue
//////////////////////////////////////////////////////////////////////////

namespace
{

bool undoingOrRedoing( const Node *node )
{
	const ScriptNode *script = node->scriptNode();
	if( !script )
	{
		return false;
	}

	return (
		script->currentActionStage() == Action::Undo ||
		script->currentActionStage() == Action::Redo
	);
}

} // namespace

GAFFER_NODE_DEFINE_TYPE( Catalogue );

size_t Catalogue::g_firstPlugIndex = 0;

Catalogue::Catalogue( const std::string &name )
	:   ImageNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new Plug( "images" ) );
	addChild( new IntPlug( "imageIndex" ) );
	addChild( new StringPlug( "name" ) );
	addChild( new StringPlug( "directory" ) );
	addChild( new IntPlug( "__imageIndex", Plug::Out ) );
	addChild( new ObjectPlug( "__imageIndexMap", Plug::Out, IECore::NullObject::defaultNullObject() ) );
	addChild( new StringPlug( "__invalidImageText", Plug::Out ) );

	// Switch used to choose which image to output
	addChild( new Switch( "__switch" ) );
	imageSwitch()->setup( outPlug() );
	imageSwitch()->indexPlug()->setInput( internalImageIndexPlug() );



	GafferImage::TextPtr errorText = new GafferImage::Text( "__errorText" );
	addChild( errorText );
	errorText->textPlug()->setInput( invalidImageTextPlug() );
	errorText->sizePlug()->setValue( Imath::V2i( 100 ) );
	errorText->horizontalAlignmentPlug()->setValue( GafferImage::Text::HorizontalCenter );
	errorText->verticalAlignmentPlug()->setValue( GafferImage::Text::VerticalCenter );

	GafferImage::FormatQueryPtr textFormatQuery = new GafferImage::FormatQuery( "__errorTextFormatQuery" );
	addChild( textFormatQuery );
	textFormatQuery->imagePlug()->setInput( errorText->outPlug() );
	errorText->areaPlug()->setInput( textFormatQuery->formatPlug()->displayWindowPlug() );

	imageSwitch()->inPlugs()->getChild< Plug >( 0 )->setInput( errorText->outPlug() );


	// Switch and constant used to implement disabled output
	ConstantPtr disabled = new Constant( "__disabled" );
	addChild( disabled );
	disabled->enabledPlug()->setValue( false );

	SwitchPtr enabler = new Switch( "__enabler" );
	enabler->setup( outPlug() );
	addChild( enabler );
	enabler->inPlugs()->getChild<ImagePlug>( 0 )->setInput( disabled->outPlug() );
	enabler->inPlugs()->getChild<ImagePlug>( 1 )->setInput( imageSwitch()->outPlug() );
	enabler->enabledPlug()->setInput( enabledPlug() );
	enabler->indexPlug()->setValue( 1 );

	outPlug()->setInput( enabler->outPlug() );

	imagesPlug()->childAddedSignal().connect( boost::bind( &Catalogue::imageAdded, this, ::_2 ) );
	imagesPlug()->childRemovedSignal().connect( boost::bind( &Catalogue::imageRemoved, this, ::_2 ) );

	Display::driverCreatedSignal().connect( boost::bind( &Catalogue::driverCreated, this, ::_1, ::_2 ) );
	Display::imageReceivedSignal().connect( boost::bind( &Catalogue::imageReceived, this, ::_1 ) );

	plugSetSignal().connect( boost::bind( &Catalogue::plugSet, this, ::_1 ) );
}

Catalogue::~Catalogue()
{
}

Gaffer::Plug *Catalogue::imagesPlug()
{
	return getChild<Plug>( g_firstPlugIndex );
}

const Gaffer::Plug *Catalogue::imagesPlug() const
{
	return getChild<Plug>( g_firstPlugIndex );
}

Gaffer::IntPlug *Catalogue::imageIndexPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *Catalogue::imageIndexPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *Catalogue::namePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *Catalogue::namePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *Catalogue::directoryPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *Catalogue::directoryPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::IntPlug *Catalogue::internalImageIndexPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::IntPlug *Catalogue::internalImageIndexPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 4 );
}

Gaffer::ObjectPlug *Catalogue::imageIndexMapPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::ObjectPlug *Catalogue::imageIndexMapPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 5 );
}

Gaffer::StringPlug *Catalogue::invalidImageTextPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::StringPlug *Catalogue::invalidImageTextPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 6 );
}

Switch *Catalogue::imageSwitch()
{
	return getChild<Switch>( g_firstPlugIndex + 7 );
}

const Switch *Catalogue::imageSwitch() const
{
	return getChild<Switch>( g_firstPlugIndex + 7 );
}

Catalogue::InternalImage *Catalogue::imageNode( Image *image )
{
	// Prefer const_cast over maintaining two identical functions
	return const_cast<InternalImage *>( imageNode( const_cast<const Image *>( image ) ) );
}

const Catalogue::InternalImage *Catalogue::imageNode( const Image *image )
{
	const InternalImage *result = nullptr;
	for( DownstreamIterator it( image->fileNamePlug() ); !it.done(); ++it )
	{
		if( const InternalImage *internalImage = dynamic_cast<const InternalImage *>( it->node() ) )
		{
			if( result && internalImage != result )
			{
				// We expect to find only one InternalImage node for any given Image plug.
				// But we also allow Image plugs to have input connections so that Catalogues
				// can be used with Boxes with their imagesPlug() promoted. This means we can't
				// enforce the one-to-one relationship via plug flags, so we must instead enforce
				// it here.
				throw IECore::Exception( "Catalogue::imageNode : Multiple internal images not supported" );
			}
			else
			{
				result = internalImage;
			}
		}

		if( !it->isInstanceOf( StringPlug::staticTypeId() ) )
		{
			// We only want to follow the chain leading to the name plug of the InternalImage,
			// we don't want to follow off into some other output network that could be costly
			// to spider ( If we follow the output image of the InternalImage off into a large
			// comp network, this could get extraordinarily costly, due to DownstreamIterator
			// not pruning when revisiting nodes ).
			it.prune();
		}
	}

	if( !result )
	{
		throw IECore::Exception( "Catalogue::imageNode : Unable to find image" );
	}

	return result;
}

std::string Catalogue::generateFileName( const Image *image ) const
{
	return generateFileName( imageNode( image )->outPlug() );
}

std::string Catalogue::generateFileName( const ImagePlug *image ) const
{
	string directory = directoryPlug()->getValue();
	if( const ScriptNode *script = ancestor<ScriptNode>() )
	{
		directory = script->context()->substitute( directory );
	}
	else if( IECore::StringAlgo::hasSubstitutions( directory ) )
	{
		// Its possible for a Catalogue to have been removed from its script
		// and still receive an image. If it will attempt to save that image
		// to a file which needed the script context to resolve properly, the
		// saving will eventually error, so we return an empty string instead.
		// Its likely this only occurs while the node is in the process of
		// being deleted (perhaps inside python's garbage collector).
		return "";
	}

	if( directory.empty() )
	{
		return "";
	}

	boost::filesystem::path result( directory );

	// Hash all views of the image
	IECore::MurmurHash h;
	for( const std::string &v : image->viewNames()->readable() )
	{
		h.append( ImageAlgo::imageHash( image, &v ) );
	}
	result /= h.toString();
	result.replace_extension( "exr" );

	return result.string();
}

void Catalogue::imageAdded( GraphComponent *graphComponent )
{
	Image *image = runTimeCast<Image>( graphComponent );
	if( !image )
	{
		throw IECore::Exception( "Expected a Catalogue::Image" );
	}

	if( undoingOrRedoing( this ) )
	{
		// Just let the undo queue replay our previous actions
		return;
	}

	InternalImagePtr internalImage = new InternalImage();
	addChild( internalImage );
	internalImage->fileNamePlug()->setInput( image->fileNamePlug() );
	internalImage->descriptionPlug()->setInput( image->descriptionPlug() );

	ImagePlug *nextSwitchInput = static_cast<ImagePlug *>( imageSwitch()->inPlugs()->children().back().get() );
	nextSwitchInput->setInput( internalImage->outPlug() );
}

void Catalogue::imageRemoved( GraphComponent *graphComponent )
{
	if( undoingOrRedoing( this ) )
	{
		// Just let the undo queue replay our previous actions
		return;
	}

	// Remove the InternalImage corresponding to the external Image
	// plug that was removed. We can't call `imageNode()` to find this
	// for us, because the connections will have been removed along
	// with the plug. So we search for an internal image which has
	// no input connection.

	// `maybe_unused` keeps the compiler happy when release builds omit the
	// `assert()`.
	[[maybe_unused]] bool removed = false;
	for( auto &c : children() )
	{
		if( auto *internalImage = dynamic_cast<InternalImage *>( c.get() ) )
		{
			if( !internalImage->fileNamePlug()->getInput() )
			{
				assert( !removed );
				// This causes the image to disconnect from
				// the switch automatically.
				removeChild( internalImage );
				removed = true;
			}
		}
	}
	assert( removed );

	// Now we go through and shuffle everything down
	// to fill the hole in the switch inputs.
	/// \todo Should there be an ArrayPlug method to do this for us?
	ArrayPlug *plug = imageSwitch()->inPlugs();
	for( size_t i = 0, offset = 0; i < plug->children().size(); ++i )
	{
		Plug *element = plug->getChild<Plug>( i );
		if( !element->getInput() )
		{
			offset++;
		}
		if( offset )
		{
			if( i + offset < plug->children().size() - 1 )
			{
				element->setInput( plug->getChild<Plug>( i + offset )->getInput() );
			}
			else
			{
				element->setInput( nullptr );
			}
		}
	}
}

IECoreImage::DisplayDriverServer *Catalogue::displayDriverServer()
{
	static IECoreImage::DisplayDriverServerPtr g_server = new IECoreImage::DisplayDriverServer();
	return g_server.get();
}

void Catalogue::driverCreated( IECoreImage::DisplayDriver *driver, const IECore::CompoundData *parameters )
{
	// Check the image is destined for catalogues in general
	if( const StringData *portNumberData = parameters->member<StringData>( "displayPort" ) )
	{
		try
		{
			if( boost::lexical_cast<int>( portNumberData->readable() ) != displayDriverServer()->portNumber() )
			{
				return;
			}
		}
		catch( boost::bad_lexical_cast &e )
		{
			throw IECore::Exception( "Invalid port number: <" + portNumberData->readable() + ">\n" );
		}
	}

	// Check the image is destined for this catalogue
	string catalogueName = "";
	if( const StringData *catalogueNameData = parameters->member<StringData>( "catalogue:name" ) )
	{
		catalogueName = catalogueNameData->readable();
	}

	string name = namePlug()->getValue();
	if( ScriptNode *script = scriptNode() )
	{
		name = script->context()->substitute( name );
	}
	if( name != catalogueName )
	{
		return;
	}

	// Try to find an existing InternalImage from
	// the same render, so we can just combine all
	// AOVs into a single image. We iterate backwards
	// because the last image is most likely to be the
	// one we want.
	Plug *images = imagesPlug()->source();
	for( int i = images->children().size() - 1; i >= 0; --i )
	{
		InternalImage *candidateImage = imageNode( images->getChild<Image>( i ) );
		if( candidateImage->insertDriver( driver, parameters ) )
		{
			return;
		}
	}

	// We don't have an existing image for this
	// render, so create one and use that.
	Image::Ptr image = new Image( "Image", Plug::In, Plug::Default | Plug::Dynamic );
	images->addChild( image );
	imageNode( image.get() )->insertDriver( driver, parameters );
	imageIndexPlug()->source<IntPlug>()->setValue( images->children().size() - 1 );
}

void Catalogue::imageReceived( Gaffer::Plug *plug )
{
	if( plug->ancestor<Catalogue>() != this )
	{
		return;
	}

	InternalImage *internalImage = static_cast<InternalImage *>( plug->node()->parent<Node>() );
	internalImage->driverClosed();
}


void Catalogue::plugSet( const Plug *plug )
{
	// Enforce that only one image may have a particular output index
	//
	// We consider this code to enforce uniqueness to be easier than needing to sync indices during
	// deletion / reordering.  \todo - handle selection this same way?
	auto currentImage = plug->parent<Image>();
	if( currentImage && currentImage->parent() == imagesPlug() && plug == currentImage->outputIndexPlug() )
	{
		int newIndex = currentImage->outputIndexPlug()->getValue();
		if( newIndex == 0 )
		{
			return;
		}

		for( const auto &image : Image::Range( *imagesPlug() ) )
		{
			if( image != currentImage && image->outputIndexPlug()->getValue() == newIndex )
			{
				image->outputIndexPlug()->source<IntPlug>()->setValue( 0 );
			}
		}
	}
}

void Catalogue::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageNode::affects( input, outputs );

	auto image = input->parent<Image>();
	if( image && image->parent() == imagesPlug() &&
		( input == image->namePlug() || input == image->outputIndexPlug() )
	)
	{
		outputs.push_back( imageIndexMapPlug() );
	}

	if( input == imageIndexPlug() || input == imageIndexMapPlug() )
	{
		outputs.push_back( internalImageIndexPlug() );
	}
}

void Catalogue::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hash( output, context, h );
	if( output == invalidImageTextPlug() )
	{
		h.append( context->get<std::string>( g_imageNameContextName, g_emptyString ) );
	}
	else if( output == imageIndexMapPlug() )
	{
		for( const auto &image : Image::Range( *imagesPlug() ) )
		{
			image->namePlug()->hash( h );
			image->outputIndexPlug()->hash( h );
		}
	}
	else if( output == internalImageIndexPlug() )
	{
		const std::string &imageName = context->get<std::string>( g_imageNameContextName, g_emptyString );
		if( imageName.empty() )
		{
			imageIndexPlug()->hash( h );
		}
		else
		{
			h.append( imageName );

			Context::EditableScope mapScope( context );
			mapScope.remove( g_imageNameContextName );
			imageIndexMapPlug()->hash( h );
		}
	}
}

void Catalogue::compute( ValuePlug *output, const Context *context ) const
{
	if( output == invalidImageTextPlug() )
	{
		const std::string &imageName = context->get<std::string>( g_imageNameContextName, g_emptyString );
		int outputIndex = 0;

		if( boost::starts_with( imageName, g_outputPrefix ) )
		{
			outputIndex = std::stoi( imageName.substr( g_outputPrefix.size() ) );
		}

		std::string result;
		if( imageName.empty() )
		{
			// Failing to find an image even with no query set can happen on a freshly created
			// catalog with no images.  This does not require an error.
			result = "";
		}
		else if( outputIndex > 0 )
		{
			result = "Catalogue : Unassigned Output " + std::to_string( outputIndex );
		}
		else
		{
			result = "Catalogue : Unknown Image \"" + imageName + "\"";
		}
		static_cast<StringPlug *>( output )->setValue( result );
	}
	else if( output == imageIndexMapPlug() )
	{
		ImageIndexMapDataPtr result = new ImageIndexMapData();
		int childIndex = 0;
		for( const auto &image : Image::Range( *imagesPlug() ) )
		{
			result->map[ image->namePlug()->getValue() ] = childIndex;
			int outputIndex = image->outputIndexPlug()->getValue();
			if( outputIndex > 0 )
			{
				result->map[ "output:" + std::to_string( outputIndex ) ] = childIndex;
			}
			childIndex++;
		}

		static_cast<ObjectPlug *>( output )->setValue( result );
	}

	if( output != internalImageIndexPlug() )
	{
		ImageNode::compute( output, context );
		return;
	}

	int index = -1;
	const std::string &imageName = context->get<std::string>( g_imageNameContextName, g_emptyString );
	if( imageName.empty() )
	{
		index = imageIndexPlug()->getValue();
	}
	else
	{
		Context::EditableScope mapScope( context );
		mapScope.remove( g_imageNameContextName );
		ConstImageIndexMapDataPtr imageIndexMap = boost::static_pointer_cast<const ImageIndexMapData>( imageIndexMapPlug()->getValue() );
		auto it = imageIndexMap->map.find( imageName );
		if( it != imageIndexMap->map.end() )
		{
			index = it->second;
		}
	}

	static_cast<IntPlug *>( output )->setValue( index + 1 );

}

const std::type_info &Catalogue::internalImageTypeInfo()
{
	return typeid( InternalImage );
}
