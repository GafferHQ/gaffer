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

#include "GafferImage/ImageReader.h"

#include "GafferImage/ColorSpace.h"
#include "GafferImage/OpenImageIOReader.h"

#include "Gaffer/StringPlug.h"

#include "OpenEXR/ImathFun.h"

#include "OpenColorIO/OpenColorIO.h"

#include "boost/bind.hpp"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

class FrameMaskScope : public Context::EditableScope
{

	public :

		FrameMaskScope( const Context *context, const ImageReader *reader, bool clampBlack = false )
			:	EditableScope( context ), m_mode( ImageReader::None )
		{
				const int startFrame = reader->startFramePlug()->getValue();
				const int endFrame = reader->endFramePlug()->getValue();
				const int frame = (int)context->getFrame();

				if( frame < startFrame )
				{
					m_mode = (ImageReader::FrameMaskMode)reader->startModePlug()->getValue();
				}
				else if( frame > endFrame )
				{
					m_mode = (ImageReader::FrameMaskMode)reader->endModePlug()->getValue();
				}

				if( m_mode == ImageReader::BlackOutside && clampBlack )
				{
					m_mode = ImageReader::ClampToFrame;
				}

				if( m_mode == ImageReader::ClampToFrame )
				{
					setFrame( clamp( frame, startFrame, endFrame ) );
				}
		}

		ImageReader::FrameMaskMode mode()
		{
			return m_mode;
		}

	private :

		ImageReader::FrameMaskMode m_mode;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// ImageReader implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( ImageReader );

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

	addChild( new StringPlug( "colorSpace" ) );

	addChild( new AtomicCompoundDataPlug( "__intermediateMetadata", Plug::In, new CompoundData, Plug::Default & ~Plug::Serialisable ) );
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
	OpenColorIO::ConstConfigRcPtr config = OpenColorIO::GetCurrentConfig();
	colorSpace->outputSpacePlug()->setValue( config->getColorSpace( OpenColorIO::ROLE_SCENE_LINEAR )->getName() );
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

StringPlug *ImageReader::colorSpacePlug()
{
	return getChild<StringPlug>( g_firstChildIndex + 5 );
}

const StringPlug *ImageReader::colorSpacePlug() const
{
	return getChild<StringPlug>( g_firstChildIndex + 5 );
}

AtomicCompoundDataPlug *ImageReader::intermediateMetadataPlug()
{
	return getChild<AtomicCompoundDataPlug>( g_firstChildIndex + 6 );
}

const AtomicCompoundDataPlug *ImageReader::intermediateMetadataPlug() const
{
	return getChild<AtomicCompoundDataPlug>( g_firstChildIndex + 6 );
}

StringPlug *ImageReader::intermediateColorSpacePlug()
{
	return getChild<StringPlug>( g_firstChildIndex + 7 );
}

const StringPlug *ImageReader::intermediateColorSpacePlug() const
{
	return getChild<StringPlug>( g_firstChildIndex + 7 );
}

ImagePlug *ImageReader::intermediateImagePlug()
{
	return getChild<ImagePlug>( g_firstChildIndex + 8 );
}

const ImagePlug *ImageReader::intermediateImagePlug() const
{
	return getChild<ImagePlug>( g_firstChildIndex + 8 );
}

OpenImageIOReader *ImageReader::oiioReader()
{
	return getChild<OpenImageIOReader>( g_firstChildIndex + 9 );
}

const OpenImageIOReader *ImageReader::oiioReader() const
{
	return getChild<OpenImageIOReader>( g_firstChildIndex + 9 );
}

ColorSpace *ImageReader::colorSpace()
{
	return getChild<ColorSpace>( g_firstChildIndex + 10 );
}

const ColorSpace *ImageReader::colorSpace() const
{
	return getChild<ColorSpace>( g_firstChildIndex + 10 );
}

size_t ImageReader::supportedExtensions( std::vector<std::string> &extensions )
{
	OpenImageIOReader::supportedExtensions( extensions );
	return extensions.size();
}

void ImageReader::setDefaultColorSpaceFunction( DefaultColorSpaceFunction f )
{
	defaultColorSpaceFunction() = f;
}

ImageReader::DefaultColorSpaceFunction ImageReader::getDefaultColorSpaceFunction()
{
	return defaultColorSpaceFunction();
}

ImageReader::DefaultColorSpaceFunction &ImageReader::defaultColorSpaceFunction()
{
	// We deliberately make no attempt to free this, because typically a python
	// function is registered here, and we can't free that at exit because python
	// is already shut down by then.
	static DefaultColorSpaceFunction *g_colorSpaceFunction = new DefaultColorSpaceFunction;
	return *g_colorSpaceFunction;
}

void ImageReader::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageNode::affects( input, outputs );

	if( input == intermediateMetadataPlug() || input == colorSpacePlug() )
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
		colorSpacePlug()->hash( h );
		fileNamePlug()->hash( h );
	}
}

void ImageReader::compute( ValuePlug *output, const Context *context ) const
{
	if( output == intermediateColorSpacePlug() )
	{
		std::string colorSpace = colorSpacePlug()->getValue();
		if( colorSpace.empty() )
		{
			ConstCompoundDataPtr metadata = intermediateMetadataPlug()->getValue();
			if( const StringData *fileFormatData = metadata->member<StringData>( "fileFormat" ) )
			{
				const StringData *dataTypeData = metadata->member<StringData>( "dataType" );
				colorSpace = defaultColorSpaceFunction()(
					fileNamePlug()->getValue(),
					fileFormatData->readable(),
					dataTypeData ? dataTypeData->readable() : "",
					metadata.get()
				);
			}
		}
		static_cast<StringPlug *>( output )->setValue( colorSpace );
	}
	else
	{
		ImageNode::compute( output, context );
	}
}

void ImageReader::hashFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FrameMaskScope scope( context, this, /* clampBlack = */ true );
	h = intermediateImagePlug()->formatPlug()->hash();
}

GafferImage::Format ImageReader::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	FrameMaskScope scope( context, this, /* clampBlack = */ true );
	return intermediateImagePlug()->formatPlug()->getValue();
}

void ImageReader::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FrameMaskScope scope( context, this, /* clampBlack = */ true );
	h = intermediateImagePlug()->dataWindowPlug()->hash();
}

Imath::Box2i ImageReader::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	FrameMaskScope scope( context, this, /* clampBlack = */ true );
	return intermediateImagePlug()->dataWindowPlug()->getValue();
}

void ImageReader::hashMetadata( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FrameMaskScope scope( context, this );
	if( scope.mode() == BlackOutside )
	{
		h = intermediateImagePlug()->metadataPlug()->defaultValue()->Object::hash();
	}
	else
	{
		h = intermediateImagePlug()->metadataPlug()->hash();
	}
}

IECore::ConstCompoundDataPtr ImageReader::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	FrameMaskScope scope( context, this );
	if( scope.mode() == BlackOutside )
	{
		return intermediateImagePlug()->metadataPlug()->defaultValue();
	}
	else
	{
		return intermediateImagePlug()->metadataPlug()->getValue();
	}
}

void ImageReader::hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FrameMaskScope scope( context, this );
	if( scope.mode() == BlackOutside )
	{
		ImageNode::hashDeep( parent, context, h );
	}
	else
	{
		h = intermediateImagePlug()->deepPlug()->hash();
	}
}

bool ImageReader::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	FrameMaskScope scope( context, this );
	if( scope.mode() == BlackOutside )
	{
		return intermediateImagePlug()->deepPlug()->defaultValue();
	}
	else
	{
		return intermediateImagePlug()->deepPlug()->getValue();
	}
}

void ImageReader::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FrameMaskScope scope( context, this );
	if( scope.mode() == BlackOutside )
	{
		h = intermediateImagePlug()->sampleOffsetsPlug()->defaultValue()->Object::hash();
	}
	else
	{
		h = intermediateImagePlug()->sampleOffsetsPlug()->hash();
	}
}

IECore::ConstIntVectorDataPtr ImageReader::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	FrameMaskScope scope( context, this );
	if( scope.mode() == BlackOutside )
	{
		return intermediateImagePlug()->sampleOffsetsPlug()->defaultValue();
	}
	else
	{
		return intermediateImagePlug()->sampleOffsetsPlug()->getValue();
	}
}



void ImageReader::hashChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FrameMaskScope scope( context, this );
	if( scope.mode() == BlackOutside )
	{
		h = intermediateImagePlug()->channelNamesPlug()->defaultValue()->Object::hash();
	}
	else
	{
		h = intermediateImagePlug()->channelNamesPlug()->hash();
	}
}

IECore::ConstStringVectorDataPtr ImageReader::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	FrameMaskScope scope( context, this );
	if( scope.mode() == BlackOutside )
	{
		return intermediateImagePlug()->channelNamesPlug()->defaultValue();
	}
	else
	{
		return intermediateImagePlug()->channelNamesPlug()->getValue();
	}
}

void ImageReader::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FrameMaskScope scope( context, this );
	if( scope.mode() == BlackOutside )
	{
		h = intermediateImagePlug()->channelDataPlug()->defaultValue()->Object::hash();
	}
	else
	{
		h = intermediateImagePlug()->channelDataPlug()->hash();
	}
}

IECore::ConstFloatVectorDataPtr ImageReader::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	FrameMaskScope scope( context, this );
	if( scope.mode() == BlackOutside )
	{
		return intermediateImagePlug()->channelDataPlug()->defaultValue();
	}
	else
	{
		return intermediateImagePlug()->channelDataPlug()->getValue();
	}
}
