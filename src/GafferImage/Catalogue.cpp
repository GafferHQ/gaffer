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
#include "boost/filesystem/path.hpp"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/ArrayPlug.h"

#include "GafferImage/Catalogue.h"
#include "GafferImage/ImageReader.h"
#include "GafferImage/Constant.h"
#include "GafferImage/ImageMetadata.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// InternalImage.
// This node type provides the internal implementation of the images
// specified by the public Image plugs.
//////////////////////////////////////////////////////////////////////////

namespace
{

class InternalImage : public ImageNode
{

	public :

		InternalImage( const std::string &name = "InternalImage" )
			:	ImageNode( name )
		{
			storeIndexOfNextChild( g_firstChildIndex );

			addChild( new StringPlug( "fileName" ) );
			addChild( new StringPlug( "description" ) );

			addChild( new ImageReader() );
			imageReader()->fileNamePlug()->setInput( fileNamePlug() );

			addChild( new ImageMetadata() );
			imageMetadata()->inPlug()->setInput( imageReader()->outPlug() );

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

	private :

		ImageReader *imageReader()
		{
			return getChild<ImageReader>( g_firstChildIndex + 2 );
		}

		ImageMetadata *imageMetadata()
		{
			return getChild<ImageMetadata>( g_firstChildIndex + 3 );
		}

		static size_t g_firstChildIndex;

};

size_t InternalImage::g_firstChildIndex = 0;

IE_CORE_DECLAREPTR( InternalImage )

} // namespace

//////////////////////////////////////////////////////////////////////////
// Image
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Catalogue::Image );

Catalogue::Image::Image( const std::string &name )
	:	Plug( name, Plug::In, Plug::Default | Plug::Dynamic )
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
	Ptr image = new Image( boost::filesystem::path( fileName ).stem().string() );
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

//////////////////////////////////////////////////////////////////////////
// Catalogue
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Catalogue );

size_t Catalogue::g_firstPlugIndex = 0;

Catalogue::Catalogue( const std::string &name )
	:   ImageNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new Plug( "images" ) );
	addChild( new IntPlug( "imageIndex" ) );

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
	outPlug()->setFlags( Plug::Serialisable, false );

	imagesPlug()->childAddedSignal().connect( boost::bind( &Catalogue::imageAdded, this, ::_2 ) );
	imagesPlug()->childRemovedSignal().connect( boost::bind( &Catalogue::imageRemoved, this, ::_2 ) );
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

ImageSwitch *Catalogue::imageSwitch()
{
	return getChild<ImageSwitch>( g_firstPlugIndex + 2 );
}

const ImageSwitch *Catalogue::imageSwitch() const
{
	return getChild<ImageSwitch>( g_firstPlugIndex + 2 );
}

ImageNode *Catalogue::imageNode( Image *image ) const
{
	const Plug::OutputContainer &outputs = image->fileNamePlug()->outputs();
	for( Plug::OutputContainer::const_iterator it = outputs.begin(), eIt = outputs.end(); it != eIt; ++it )
	{
		ImageNode *node = runTimeCast<ImageNode>( (*it)->node() );
		if( node && node->parent<Node>() == this )
		{
			return node;
		}
	}
	throw IECore::Exception( "Catalogue::imageNode : Unable to find image" );
}

void Catalogue::imageAdded( GraphComponent *graphComponent )
{
	Image *image = static_cast<Image *>( graphComponent );

	InternalImagePtr internalImage = new InternalImage();
	addChild( internalImage );
	internalImage->fileNamePlug()->setInput( image->fileNamePlug() );
	internalImage->descriptionPlug()->setInput( image->descriptionPlug() );

	ImagePlug *nextSwitchInput = static_cast<ImagePlug *>( imageSwitch()->inPlugs()->children().back().get() );
	nextSwitchInput->setInput( internalImage->outPlug() );
}

void Catalogue::imageRemoved( GraphComponent *graphComponent )
{
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

