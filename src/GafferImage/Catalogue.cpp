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

#include "boost/bind.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/filesystem/path.hpp"
#include "boost/filesystem/operations.hpp"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/ArrayPlug.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/DownstreamIterator.h"

#include "GafferImage/Catalogue.h"
#include "GafferImage/ImageReader.h"
#include "GafferImage/Constant.h"
#include "GafferImage/ImageMetadata.h"
#include "GafferImage/CopyChannels.h"
#include "GafferImage/Display.h"
#include "GafferImage/ImageWriter.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

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

			// Switches between the loaded image and the
			// live Displays.
			addChild( new ImageSwitch() );
			imageSwitch()->inPlugs()->getChild<ImagePlug>( 0 )->setInput( imageReader()->outPlug() );
			imageSwitch()->inPlugs()->getChild<ImagePlug>( 1 )->setInput( copyChannels()->outPlug() );

			// Adds on a description to the output
			addChild( new ImageMetadata() );
			imageMetadata()->inPlug()->setInput( imageSwitch()->outPlug() );
			CompoundDataPlug::MemberPlug *meta = imageMetadata()->metadataPlug()->addMember( "ImageDescription", new StringData() );
			meta->valuePlug<StringPlug>()->setInput( descriptionPlug() );

			outPlug()->setInput( imageMetadata()->outPlug() );
		}

		StringPlug *fileNamePlug()
		{
			return getChild<StringPlug>( g_firstChildIndex );
		}

		StringPlug *descriptionPlug()
		{
			return getChild<StringPlug>( g_firstChildIndex + 1 );
		}

		void save( const std::string &fileName ) const
		{
			ImageWriterPtr imageWriter = new ImageWriter;
			imageWriter->inPlug()->setInput( const_cast<ImagePlug *>( outPlug() ) );
			imageWriter->fileNamePlug()->setValue( fileName );
			imageWriter->taskPlug()->execute();
		}

		bool insertDriver( IECore::DisplayDriverPtr driver, const IECore::CompoundData *parameters )
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
			ConstStringVectorDataPtr existingChannelsData = copyChannels()->outPlug()->channelNamesPlug()->getValue();
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
			if( nextIndex == 1 && !a->getChild<ImagePlug>( 0 )->getInput<Plug>() )
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

			updateImageFlags( Plug::Serialisable, false ); // Don't serialise in-progress renders

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
			// Save the image to disk.

			string fileName = parent<Catalogue>()->generateFileName( outPlug() );
			if( fileName.empty() )
			{
				return;
			}
			save( fileName );

			// Load the image from disk and delete all our Display
			// nodes to save memory.

			fileNamePlug()->source<StringPlug>()->setValue( fileName );
			imageSwitch()->indexPlug()->setValue( 0 );

			vector<Display *> toDelete;
			for( DisplayIterator it( this ); !it.done(); ++it )
			{
				toDelete.push_back( it->get() );
			}
			for( vector<Display *>::const_iterator it = toDelete.begin(), eIt = toDelete.end(); it != eIt; ++it )
			{
				removeChild( *it );
			}

			updateImageFlags( Plug::Serialisable, true );
		}

	private :

		void updateImageFlags( unsigned flags, bool enable )
		{
			for( Image *i = fileNamePlug()->getInput<Plug>()->parent<Image>(); i; i = i->getInput<Image>() )
			{
				i->setFlags( flags, enable );
			}
		}

		ImageReader *imageReader()
		{
			return getChild<ImageReader>( g_firstChildIndex + 2 );
		}

		CopyChannels *copyChannels()
		{
			return getChild<CopyChannels>( g_firstChildIndex + 3 );
		}

		ImageSwitch *imageSwitch()
		{
			return getChild<ImageSwitch>( g_firstChildIndex + 4 );
		}

		ImageMetadata *imageMetadata()
		{
			return getChild<ImageMetadata>( g_firstChildIndex + 5 );
		}

		int m_clientPID;
		size_t m_numDriversClosed;

		static size_t g_firstChildIndex;

};

size_t Catalogue::InternalImage::g_firstChildIndex = 0;

//////////////////////////////////////////////////////////////////////////
// Image
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Catalogue::Image );

Catalogue::Image::Image( const std::string &name, Direction direction, unsigned flags )
	:	Plug( name, direction, flags )
{
	addChild( new StringPlug( "fileName" ) );
	addChild( new StringPlug( "description" ) );
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

Catalogue::Image::Ptr Catalogue::Image::load( const std::string &fileName )
{
	Ptr image = new Image( boost::filesystem::path( fileName ).stem().string(), Plug::In, Plug::Default | Plug::Dynamic );
	image->fileNamePlug()->setValue( fileName );

	ImageReaderPtr reader = new ImageReader;
	reader->fileNamePlug()->setValue( fileName );
	ConstCompoundObjectPtr meta = reader->outPlug()->metadataPlug()->getValue();
	if( const StringData *description = meta->member<const StringData>( "ImageDescription" ) )
	{
		image->descriptionPlug()->setValue( description->readable() );
	}

	return image;
}

void Catalogue::Image::save( const std::string &fileName ) const
{
	const InternalImage *internalImage = NULL;
	for( DownstreamIterator it( fileNamePlug() ); !it.done(); ++it )
	{
		internalImage = dynamic_cast<const InternalImage *>( it->node() );
		if( internalImage )
		{
			break;
		}
	}
	if( !internalImage )
	{
		throw IECore::Exception( "Catalogue::imageNode : Unable to find image" );
	}
	internalImage->save( fileName );
}

Gaffer::PlugPtr Catalogue::Image::createCounterpart( const std::string &name, Direction direction ) const
{
	return new Image( name, direction, getFlags() );
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

IE_CORE_DEFINERUNTIMETYPED( Catalogue );

size_t Catalogue::g_firstPlugIndex = 0;

Catalogue::Catalogue( const std::string &name )
	:   ImageNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new Plug( "images" ) );
	addChild( new IntPlug( "imageIndex" ) );
	addChild( new StringPlug( "name" ) );
	addChild( new StringPlug( "directory" ) );

	// Switch used to choose which image to output
	addChild( new ImageSwitch( "__switch" ) );
	imageSwitch()->indexPlug()->setInput( imageIndexPlug() );

	// Switch and constant used to implement disabled output
	ConstantPtr disabled = new Constant( "__disabled" );
	addChild( disabled );
	disabled->enabledPlug()->setValue( false );

	ImageSwitchPtr enabler = new ImageSwitch( "__enabler" );
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

ImageSwitch *Catalogue::imageSwitch()
{
	return getChild<ImageSwitch>( g_firstPlugIndex + 4 );
}

const ImageSwitch *Catalogue::imageSwitch() const
{
	return getChild<ImageSwitch>( g_firstPlugIndex + 4 );
}

Catalogue::InternalImage *Catalogue::imageNode( const Image *image ) const
{
	for( DownstreamIterator it( image->fileNamePlug() ); !it.done(); ++it )
	{
		const InternalImage *node = runTimeCast<const InternalImage>( it->node() );
		if( node && node->parent<Node>() == this )
		{
			/// \todo Make DownstreamIterator reference non-const
			/// plugs (and add a ConstDownstreamIterator) and then
			/// we don't need this cast.
			return const_cast<InternalImage *>( node );
		}
	}
	throw IECore::Exception( "Catalogue::imageNode : Unable to find image" );
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
	if( directory.empty() )
	{
		return "";
	}

	boost::filesystem::path result( directory );
	result /= image->imageHash().toString();
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

	Image *image = static_cast<Image *>( graphComponent );
	// This causes the image to disconnect from
 	// the switch automatically.
	removeChild( imageNode( image ) );
	// So now we go through and shuffle everything down
	// to fill the hole in the switch inputs.
	/// \todo Should there be an ArrayPlug method to do this for us?
	ArrayPlug *plug = imageSwitch()->inPlugs();
	for( size_t i = 0, offset = 0; i < plug->children().size(); ++i )
	{
		Plug *element = plug->getChild<Plug>( i );
		if( !element->getInput<Plug>() )
		{
			offset++;
		}
		if( offset )
		{
			if( i + offset < plug->children().size() - 1 )
			{
				element->setInput( plug->getChild<Plug>( i + offset )->source<Plug>() );
			}
			else
			{
				element->setInput( NULL );
			}
		}
	}
}

IECore::DisplayDriverServer *Catalogue::displayDriverServer()
{
	static IECore::DisplayDriverServerPtr g_server = new IECore::DisplayDriverServer();
	return g_server.get();
}

void Catalogue::driverCreated( IECore::DisplayDriver *driver, const IECore::CompoundData *parameters )
{
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
	Plug *images = imagesPlug()->source<Plug>();
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

