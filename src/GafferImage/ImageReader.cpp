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

#include "boost/bind.hpp"

#include "OpenColorIO/OpenColorIO.h"

#include "Gaffer/StringPlug.h"

#include "GafferImage/ColorSpace.h"
#include "GafferImage/ImageReader.h"
#include "GafferImage/OpenImageIOReader.h"

using namespace std;
using namespace tbb;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// ImageReader implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( ImageReader );

size_t ImageReader::g_firstChildIndex = 0;

ImageReader::ImageReader( const std::string &name )
	:	ImageNode( name )
{
	storeIndexOfNextChild( g_firstChildIndex );
	addChild(
		new StringPlug(
			"fileName", Plug::In, "",
			/* flags */ Plug::Default,
			/* substitutions */ Context::AllSubstitutions & ~Context::FrameSubstitutions
		)
	);
	addChild( new IntPlug( "refreshCount" ) );
	addChild( new IntPlug( "missingFrameMode", Plug::In, Error, /* min */ Error, /* max */ Hold ) );

	ValuePlugPtr startPlug = new ValuePlug( "start", Plug::In );
	startPlug->addChild( new IntPlug( "mode", Plug::In, None, /* min */ None, /* max */ ClampToFrame ) );
	startPlug->addChild( new IntPlug( "frame", Plug::In, 0 ) );
	addChild( startPlug );

	ValuePlugPtr endPlug = new ValuePlug( "end", Plug::In );
	endPlug->addChild( new IntPlug( "mode", Plug::In, None, /* min */ None, /* max */ ClampToFrame ) );
	endPlug->addChild( new IntPlug( "frame", Plug::In, 0 ) );
	addChild( endPlug );

	addChild( new CompoundObjectPlug( "__intermediateMetadata", Plug::In, new CompoundObject, Plug::Default & ~Plug::Serialisable ) );
	addChild( new StringPlug( "__intermediateColorSpace", Plug::Out, "", Plug::Default & ~Plug::Serialisable ) );
	addChild( new ImagePlug( "__intermediateImage", Plug::In, Plug::Default & ~Plug::Serialisable ) );

	// We don't really do much work ourselves - we just
	// defer to internal nodes to do the hard work.

	OpenImageIOReaderPtr oiioReader = new OpenImageIOReader( "__oiioReader" );
	addChild( oiioReader );
	oiioReader->fileNamePlug()->setInput( fileNamePlug() );
	oiioReader->refreshCountPlug()->setInput( refreshCountPlug() );
	oiioReader->missingFrameModePlug()->setInput( missingFrameModePlug() );
	intermediateMetadataPlug()->setInput( oiioReader->outPlug()->metadataPlug() );

	ColorSpacePtr colorSpace = new ColorSpace( "__colorSpace" );
	addChild( colorSpace );
	colorSpace->inPlug()->setInput( oiioReader->outPlug() );
	colorSpace->inputSpacePlug()->setInput( intermediateColorSpacePlug() );
	colorSpace->outputSpacePlug()->setValue( OpenColorIO::ROLE_SCENE_LINEAR );
	intermediateImagePlug()->setInput( colorSpace->outPlug() );
}

ImageReader::~ImageReader()
{
}

StringPlug *ImageReader::fileNamePlug()
{
	return getChild<StringPlug>( g_firstChildIndex );
}

const StringPlug *ImageReader::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstChildIndex );
}

IntPlug *ImageReader::refreshCountPlug()
{
	return getChild<IntPlug>( g_firstChildIndex + 1 );
}

const IntPlug *ImageReader::refreshCountPlug() const
{
	return getChild<IntPlug>( g_firstChildIndex + 1 );
}

IntPlug *ImageReader::missingFrameModePlug()
{
	return getChild<IntPlug>( g_firstChildIndex + 2 );
}

const IntPlug *ImageReader::missingFrameModePlug() const
{
	return getChild<IntPlug>( g_firstChildIndex + 2 );
}

IntPlug *ImageReader::startModePlug()
{
	return getChild<ValuePlug>( g_firstChildIndex + 3 )->getChild<IntPlug>( 0 );
}

const IntPlug *ImageReader::startModePlug() const
{
	return getChild<ValuePlug>( g_firstChildIndex + 3 )->getChild<IntPlug>( 0 );
}

IntPlug *ImageReader::startFramePlug()
{
	return getChild<ValuePlug>( g_firstChildIndex + 3 )->getChild<IntPlug>( 1 );
}

const IntPlug *ImageReader::startFramePlug() const
{
	return getChild<ValuePlug>( g_firstChildIndex + 3 )->getChild<IntPlug>( 1 );
}

IntPlug *ImageReader::endModePlug()
{
	return getChild<ValuePlug>( g_firstChildIndex + 4 )->getChild<IntPlug>( 0 );
}

const IntPlug *ImageReader::endModePlug() const
{
	return getChild<ValuePlug>( g_firstChildIndex + 4 )->getChild<IntPlug>( 0 );
}

IntPlug *ImageReader::endFramePlug()
{
	return getChild<ValuePlug>( g_firstChildIndex + 4 )->getChild<IntPlug>( 1 );
}

const IntPlug *ImageReader::endFramePlug() const
{
	return getChild<ValuePlug>( g_firstChildIndex + 4 )->getChild<IntPlug>( 1 );
}

CompoundObjectPlug *ImageReader::intermediateMetadataPlug()
{
	return getChild<CompoundObjectPlug>( g_firstChildIndex + 5 );
}

const CompoundObjectPlug *ImageReader::intermediateMetadataPlug() const
{
	return getChild<CompoundObjectPlug>( g_firstChildIndex + 5 );
}

StringPlug *ImageReader::intermediateColorSpacePlug()
{
	return getChild<StringPlug>( g_firstChildIndex + 6 );
}

const StringPlug *ImageReader::intermediateColorSpacePlug() const
{
	return getChild<StringPlug>( g_firstChildIndex + 6 );
}

ImagePlug *ImageReader::intermediateImagePlug()
{
	return getChild<ImagePlug>( g_firstChildIndex + 7 );
}

const ImagePlug *ImageReader::intermediateImagePlug() const
{
	return getChild<ImagePlug>( g_firstChildIndex + 7 );
}

OpenImageIOReader *ImageReader::oiioReader()
{
	return getChild<OpenImageIOReader>( g_firstChildIndex + 8 );
}

const OpenImageIOReader *ImageReader::oiioReader() const
{
	return getChild<OpenImageIOReader>( g_firstChildIndex + 8 );
}

ColorSpace *ImageReader::colorSpace()
{
	return getChild<ColorSpace>( g_firstChildIndex + 9 );
}

const ColorSpace *ImageReader::colorSpace() const
{
	return getChild<ColorSpace>( g_firstChildIndex + 9 );
}

size_t ImageReader::supportedExtensions( std::vector<std::string> &extensions )
{
	OpenImageIOReader::supportedExtensions( extensions );
	return extensions.size();
}

void ImageReader::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageNode::affects( input, outputs );

	if( input == intermediateMetadataPlug() )
	{
		outputs.push_back( intermediateColorSpacePlug() );
	}
	else if( input->parent<ImagePlug>() == intermediateImagePlug() )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
	else if (
		input == startFramePlug() ||
		input == startModePlug() ||
		input == endFramePlug() ||
		input == endModePlug()
	)
	{
		for( ValuePlugIterator it( outPlug() ); !it.done(); ++it )
		{
			outputs.push_back( it->get() );
		}
	}
}

void ImageReader::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hash( output, context, h );

	if( output == intermediateColorSpacePlug() )
	{
		intermediateMetadataPlug()->hash( h );
	}
	else if(
		output == outPlug()->formatPlug() ||
		output == outPlug()->dataWindowPlug()
	)
	{
		// we always want to match the windows
		// we would get inside the frame mask
		hashMaskedOutput( output, context, h, /* alwaysClampToFrame */ true );
	}
	else if(
		output == outPlug()->metadataPlug() ||
		output == outPlug()->channelNamesPlug() ||
		output == outPlug()->channelDataPlug()
	)
	{
		hashMaskedOutput( output, context, h );
	}
}

void ImageReader::compute( ValuePlug *output, const Context *context ) const
{
	if( output == intermediateColorSpacePlug() )
	{
		std::string intermediateSpace = "";
		ConstCompoundObjectPtr metadata = intermediateMetadataPlug()->getValue();
		if( const StringData *intermediateSpaceData = metadata->member<const StringData>( "oiio:ColorSpace" ) )
		{
			std::vector<std::string> colorSpaces;
			OpenColorIOTransform::availableColorSpaces( colorSpaces );
			if( std::find( colorSpaces.begin(), colorSpaces.end(), intermediateSpaceData->readable() ) != colorSpaces.end() )
			{
				intermediateSpace = intermediateSpaceData->readable();
			}
		}

		static_cast<StringPlug *>( output )->setValue( intermediateSpace );
	}
	else if(
		output == outPlug()->formatPlug() ||
		output == outPlug()->dataWindowPlug()
	)
	{
		// we always want to match the windows
		// we would get inside the frame mask
		computeMaskedOutput( output, context, /* alwaysClampToFrame */ true );
	}
	else if(
		output == outPlug()->metadataPlug() ||
		output == outPlug()->channelNamesPlug() ||
		output == outPlug()->channelDataPlug() ||
		output == outPlug()->sampleOffsetsPlug() ||
		output == outPlug()->deepStatePlug()
	)
	{
		computeMaskedOutput( output, context );
	}
	else
	{
		ImageNode::compute( output, context );
	}
}

void ImageReader::hashMaskedOutput( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h, bool alwaysClampToFrame ) const
{
	ContextPtr maskedContext = NULL;
	if( !computeFrameMask( context, maskedContext ) || alwaysClampToFrame )
	{
		Context::Scope scope( maskedContext.get() );
		h = intermediateImagePlug()->getChild<ValuePlug>( output->getName() )->hash();
	}
}

void ImageReader::computeMaskedOutput( Gaffer::ValuePlug *output, const Gaffer::Context *context, bool alwaysClampToFrame ) const
{
	ContextPtr maskedContext = NULL;
	bool blackOutside = computeFrameMask( context, maskedContext );
	if( blackOutside && !alwaysClampToFrame )
	{
		output->setToDefault();
		return;
	}

	Context::Scope scope( maskedContext.get() );
	output->setFrom( intermediateImagePlug()->getChild<ValuePlug>( output->getName() ) );
}

bool ImageReader::computeFrameMask( const Context *context, ContextPtr &maskedContext ) const
{
	int frameStartMask = startFramePlug()->getValue();
	int frameEndMask = endFramePlug()->getValue();
	FrameMaskMode frameStartMaskMode = (FrameMaskMode)startModePlug()->getValue();
	FrameMaskMode frameEndMaskMode = (FrameMaskMode)endModePlug()->getValue();

	int origFrame = (int)context->getFrame();
	int maskedFrame = std::min( frameEndMask, std::max( frameStartMask, origFrame ) );

	if( origFrame == maskedFrame )
	{
		// no need for anything special when
		// we're within the mask range.
		return false;
	}

	FrameMaskMode maskMode = ( origFrame < maskedFrame ) ? frameStartMaskMode : frameEndMaskMode;

	if( maskMode == None )
	{
		// no need for anything special when
		// we're in FrameMaskMode::None
		return false;
	}

	// we need to create the masked context
	// for both BlackOutSide and ClampToFrame,
	// because some plugs require valid data
	// from the mask range even in either way.

	maskedContext = new Gaffer::Context( *context, Context::Borrowed );
	maskedContext->setFrame( maskedFrame );

	return ( maskMode == BlackOutside );
}
