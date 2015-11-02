//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

#include <sys/utsname.h>
#include <zlib.h>

#include "boost/filesystem.hpp"

#include "OpenImageIO/imageio.h"
OIIO_NAMESPACE_USING

#include "OpenEXR/ImfCRgbaFile.h"  // JUST to get symbols to figure out version!

#include "IECore/MessageHandler.h"

#include "Gaffer/Context.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"

#include "GafferImage/ImageWriter.h"
#include "GafferImage/ImagePlug.h"
#include "GafferImage/ChannelMaskPlug.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace GafferImage;
using namespace Gaffer;

static InternedString g_modePlugName( "mode" );
static InternedString g_compressionPlugName( "compression" );
static InternedString g_compressionQualityPlugName( "compressionQuality" );
static InternedString g_compressionLevelPlugName( "compressionLevel" );
static InternedString g_dataTypePlugName( "dataType" );

//////////////////////////////////////////////////////////////////////////
// Utility for converting IECore::Data types to OIIO::TypeDesc types.
//////////////////////////////////////////////////////////////////////////

namespace
{

TypeDesc typeDescFromData( const Data *data, const void *&basePointer )
{
	switch( data->typeId() )
	{
		// simple data

		case CharDataTypeId :
		{
			basePointer = static_cast<const CharData *>( data )->baseReadable();
			return TypeDesc( TypeDesc::CHAR );
		}
		case UCharDataTypeId :
		{
			basePointer = static_cast<const UCharData *>( data )->baseReadable();
			return TypeDesc( TypeDesc::UCHAR );
		}
		case StringDataTypeId :
		{
			basePointer = static_cast<const StringData *>( data )->baseReadable();
			return TypeDesc::TypeString;
		}
		case UShortDataTypeId :
		{
			basePointer = static_cast<const UShortData *>( data )->baseReadable();
			return TypeDesc( TypeDesc::USHORT );
		}
		case ShortDataTypeId :
		{
			basePointer = static_cast<const ShortData *>( data )->baseReadable();
			return TypeDesc( TypeDesc::SHORT );
		}
		case UIntDataTypeId :
		{
			basePointer = static_cast<const UIntData *>( data )->baseReadable();
			return TypeDesc( TypeDesc::UINT );
		}
		case HalfDataTypeId :
		{
			basePointer = static_cast<const HalfData *>( data )->baseReadable();
			return TypeDesc( TypeDesc::HALF );
		}
		case IntDataTypeId :
		{
			basePointer = static_cast<const IntData *>( data )->baseReadable();
			return TypeDesc::TypeInt;
		}
		case V2iDataTypeId :
		{
			basePointer = static_cast<const V2iData *>( data )->baseReadable();
			return TypeDesc(
				TypeDesc::INT,
				TypeDesc::VEC2
			);
		}
		case V3iDataTypeId :
		{
			basePointer = static_cast<const V3iData *>( data )->baseReadable();
			return TypeDesc(
				TypeDesc::INT,
				TypeDesc::VEC3
			);
		}
		case FloatDataTypeId :
		{
			basePointer = static_cast<const FloatData *>( data )->baseReadable();
			return TypeDesc::TypeFloat;
		}
		case V2fDataTypeId :
		{
			basePointer = static_cast<const V2fData *>( data )->baseReadable();
			return TypeDesc(
				TypeDesc::FLOAT,
				TypeDesc::VEC2
			);
		}
		case V3fDataTypeId :
		{
			basePointer = static_cast<const V3fData *>( data )->baseReadable();
			return TypeDesc(
				TypeDesc::FLOAT,
				TypeDesc::VEC3
			);
		}
		case M44fDataTypeId :
		{
			basePointer = static_cast<const M44fData *>( data )->baseReadable();
			return TypeDesc(
				TypeDesc::FLOAT,
				TypeDesc::MATRIX44
			);
		}
		case DoubleDataTypeId :
		{
			basePointer = static_cast<const DoubleData *>( data )->baseReadable();
			return TypeDesc( TypeDesc::DOUBLE );
		}
		case V2dDataTypeId :
		{
			basePointer = static_cast<const V2dData *>( data )->baseReadable();
			return TypeDesc(
				TypeDesc::DOUBLE,
				TypeDesc::VEC2
			);
		}
		case V3dDataTypeId :
		{
			basePointer = static_cast<const V3dData *>( data )->baseReadable();
			return TypeDesc(
				TypeDesc::DOUBLE,
				TypeDesc::VEC3
			);
		}
		case M44dDataTypeId :
		{
			basePointer = static_cast<const M44dData *>( data )->baseReadable();
			return TypeDesc(
				TypeDesc::DOUBLE,
				TypeDesc::MATRIX44
			);
		}
		case Color3fDataTypeId :
		{
			basePointer = static_cast<const Color3fData *>( data )->baseReadable();
			return TypeDesc::TypeColor;
		}
		default :
		{
			return TypeDesc();
		}
	}
};

void setImageSpecAttribute( const std::string &name, const Data *data, ImageSpec &spec )
{
	const void *value = NULL;
	TypeDesc type = typeDescFromData( data, value );
	if ( value )
	{
		spec.attribute( name, type, value );
	}
}

void metadataToImageSpecAttributes( const CompoundObject *metadata, ImageSpec &spec )
{
	const CompoundObject::ObjectMap &members = metadata->members();
	for ( CompoundObject::ObjectMap::const_iterator it = members.begin(); it != members.end(); ++it )
	{
		setImageSpecAttribute( it->first, IECore::runTimeCast<const Data>( it->second.get() ), spec );
	}
}

void setImageSpecFormatOptions( const ImageWriter *node, ImageSpec *spec, const std::string &fileFormatName )
{
	const ValuePlug *optionsPlug = node->getChild<ValuePlug>( fileFormatName );

	if( optionsPlug == NULL)
	{
		return;
	}

	const StringPlug *dataTypePlug = optionsPlug->getChild<StringPlug>( g_dataTypePlugName );
	std::string dataType;

	if( dataTypePlug != NULL )
	{
		dataType = dataTypePlug->getValue();

		if( dataType == "int8" )
		{
			spec->set_format( TypeDesc::INT8 );
		}
		else if( dataType == "int16" )
		{
			spec->set_format( TypeDesc::INT16 );
		}
		else if( dataType == "int32" )
		{
			spec->set_format( TypeDesc::INT32 );
		}
		else if( dataType == "int64" )
		{
			spec->set_format( TypeDesc::INT64 );
		}
		else if( dataType == "uint8" )
		{
			spec->set_format( TypeDesc::UINT8 );
		}
		else if( dataType == "uint16" )
		{
			spec->set_format( TypeDesc::UINT16 );
		}
		else if( dataType == "uint32" )
		{
			spec->set_format( TypeDesc::UINT32 );
		}
		else if( dataType == "uint64" )
		{
			spec->set_format( TypeDesc::UINT64 );
		}
		else if( dataType == "half" )
		{
			spec->set_format( TypeDesc::HALF );
		}
		else if( dataType == "float" )
		{
			spec->set_format( TypeDesc::FLOAT );
		}
		else if( dataType == "double" )
		{
			spec->set_format( TypeDesc::DOUBLE );
		}
	}

	const IntPlug *modePlug = optionsPlug->getChild<IntPlug>( g_modePlugName );

	if( modePlug != NULL && modePlug->getValue() == ImageWriter::Tile )
	{
		spec->tile_width = spec->tile_height = ImagePlug::tileSize();
	}

	const StringPlug *compressionPlug = optionsPlug->getChild<StringPlug>( g_compressionPlugName );

	if( compressionPlug != NULL )
	{
		spec->attribute( "compression", compressionPlug->getValue() );
	}

	if( fileFormatName == "jpeg" )
	{
		spec->attribute( "CompressionQuality", optionsPlug->getChild<IntPlug>( g_compressionQualityPlugName )->getValue() );
	}
	else if( fileFormatName == "dpx" )
	{
		if( dataType == "uint10" )
		{
			spec->set_format( TypeDesc::UINT16 );
			spec->attribute ("oiio:BitsPerSample", 10);
		}
		else if( dataType == "uint12" )
		{
			spec->set_format( TypeDesc::UINT16 );
			spec->attribute ("oiio:BitsPerSample", 12);
		}
	}
	else if( fileFormatName == "png" )
	{
		spec->attribute( "png:compressionLevel", optionsPlug->getChild<IntPlug>( g_compressionLevelPlugName )->getValue() );
	}
	else if( fileFormatName == "webp" )
	{
		spec->attribute( "CompressionQuality", optionsPlug->getChild<IntPlug>( g_compressionQualityPlugName )->getValue() );
	}
}

ImageSpec createImageSpec( const ImageWriter *node, const ImageOutput *out, const Imath::Box2i &dataWindow, const Imath::Box2i &displayWindow )
{
	const std::string fileFormatName = out->format_name();
	const bool supportsDisplayWindow = out->supports( "displaywindow" ) && fileFormatName != "dpx";

	ImageSpec spec( TypeDesc::UNKNOWN );

	// Specify the display window.
	spec.full_x = displayWindow.min.x;
	spec.full_y = displayWindow.min.y;
	spec.full_width = displayWindow.size().x + 1;
	spec.full_height = displayWindow.size().y + 1;

	if ( supportsDisplayWindow && dataWindow.hasVolume() )
	{
		spec.x = dataWindow.min.x;
		spec.y = dataWindow.min.y;
		spec.width = dataWindow.size().x + 1;
		spec.height = dataWindow.size().y + 1;
	}
	else
	{
		spec.x = spec.full_x;
		spec.y = spec.full_y;
		spec.width = spec.full_width;
		spec.height = spec.full_height;
	}

	// Add the metadata to the spec, removing metadata that could affect the resulting channel data
	CompoundObjectPtr metadata = node->inPlug()->metadataPlug()->getValue()->copy();
	CompoundObject::ObjectMap &members = metadata->members();

	std::vector<InternedString> oiioSpecifics;
	oiioSpecifics.push_back( "oiio:ColorSpace" );
	oiioSpecifics.push_back( "oiio:Gamma" );
	oiioSpecifics.push_back( "oiio:UnassociatedAlpha" );
	for ( std::vector<InternedString>::iterator it = oiioSpecifics.begin(); it != oiioSpecifics.end(); ++it )
	{
		CompoundObject::ObjectMap::iterator mIt = members.find( *it );
		if ( mIt != members.end() )
		{
			members.erase( mIt );
		}
	}

	metadataToImageSpecAttributes( metadata.get(), spec );

	// Apply the spec format options. Note this must happen
	// after we transfer the input metadata to ensure the
	// settings override anything from upstream data.
	setImageSpecFormatOptions( node, &spec, fileFormatName );

	// Add common attribs to the spec
	std::string software = ( boost::format( "Gaffer %d.%d.%d.%d" ) % GAFFER_MILESTONE_VERSION % GAFFER_MAJOR_VERSION % GAFFER_MINOR_VERSION % GAFFER_PATCH_VERSION ).str();
	spec.attribute( "Software", software );
	struct utsname info;
	if ( !uname( &info ) )
	{
		spec.attribute( "HostComputer", info.nodename );
	}
	if ( const char *artist = getenv( "USER" ) )
	{
		spec.attribute( "Artist", artist );
	}
	std::string document = "untitled";
	if ( const ScriptNode *script = node->ancestor<ScriptNode>() )
	{
		const std::string scriptFile = script->fileNamePlug()->getValue();
		document = ( scriptFile == "" ) ? document : scriptFile;
	}
	spec.attribute( "DocumentName", document );

	// PixelAspectRatio must be defined by the FormatPlug
	spec.attribute( "PixelAspectRatio", (float)node->inPlug()->formatPlug()->getValue().getPixelAspect() );

	return spec;
}

void writeImageScanlines( const ImageWriter *node, boost::shared_ptr<ImageOutput> &out, std::vector<const float*> &channelPtrs, const ImageSpec &spec, const Imath::Box2i &dataWindow, const std::string &fileName )
{
	// Create a buffer for the scanline.
	float scanline[ spec.nchannels*spec.width ];

	for ( int y = spec.y; y < spec.height + spec.y; ++y )
	{
		memset( scanline, 0, sizeof(float) * spec.nchannels*spec.width );

		if ( y >= dataWindow.min.y && y <= dataWindow.max.y )
		{
			for ( std::vector<const float *>::iterator channelDataIt( channelPtrs.begin() ); channelDataIt != channelPtrs.end(); channelDataIt++ )
			{
				const int inc = channelPtrs.size();
				// The row that we are reading from is flipped (in the Y) as we use a different image space internally to OpenEXR and OpenImageIO.
				const float *inRowPtr = (*channelDataIt) + ( y - dataWindow.min.y ) * (dataWindow.max.x - dataWindow.min.x + 1) + std::max( 0, ( spec.x - dataWindow.min.x ) );
				float *outPtr = &scanline[0] + ( std::max( 0, ( dataWindow.min.x - spec.x ) ) * inc ) + (channelDataIt - channelPtrs.begin()); // The pointer that we are writing to.

				// Because scanline was initalised as black, we never need to set the pixels either side
				// of the data window, as they will remain black
				for ( int x = std::max( dataWindow.min.x, spec.x ); x < std::min( dataWindow.max.x + 1, spec.width + spec.x ); ++x, outPtr += inc )
				{
					*outPtr = *inRowPtr++;
				}
			}
		}

		if ( !out->write_scanline( y, 0, TypeDesc::FLOAT, &scanline[0] ) )
		{
			throw IECore::Exception( boost::str( boost::format( "Could not write scanline to \"%s\", error = %s" ) % fileName % out->geterror() ) );
		}
	}
}

void writeImageTiles( const ImageWriter *node, boost::shared_ptr<ImageOutput> &out, std::vector<const float*> &channelPtrs, const ImageSpec &spec, const Imath::Box2i &dataWindow, const std::string &fileName )
{
	// Create a buffer for the tile.
	float tile[ spec.nchannels*spec.tile_width*spec.tile_height ];

	// Interleave the channel data and write it to the file tile-by-tile.
	for ( int tileY = spec.y; tileY < spec.height; tileY += spec.tile_height )
	{
		for ( int tileX = spec.x; tileX < spec.width; tileX += spec.tile_width )
		{
			memset( tile, 0, sizeof(float) * spec.nchannels * spec.tile_width * spec.tile_height );
			const int r = tileX + spec.tile_width;
			const int t = tileY + spec.tile_height;

			for ( int y = std::max( tileY, std::min( t, dataWindow.min.y ) ); y < std::min( t, dataWindow.max.y + 1 ); ++y )
			{
				for ( std::vector<const float *>::iterator channelDataIt( channelPtrs.begin() ); channelDataIt != channelPtrs.end(); channelDataIt++ )
				{
					const int inc = channelPtrs.size();
					float *outPtr = &tile[0] + ( ( ( ( y - tileY ) * spec.tile_width ) + ( std::max( tileX, std::min( r, dataWindow.min.x ) ) - tileX ) ) * inc ) + ( channelDataIt - channelPtrs.begin() );

					if ( y >= dataWindow.min.y && y <= dataWindow.max.y )
					{
						const float *inRowPtr = (*channelDataIt) + ( y - dataWindow.min.y ) * (dataWindow.max.x - dataWindow.min.x + 1);
						for ( int x = std::max( tileX, std::min( r, dataWindow.min.x ) ); x < std::min( r, dataWindow.max.x + 1 ); ++x, outPtr += inc )
						{
							*outPtr = *(inRowPtr + x - dataWindow.min.x);
						}
					}
				}
			}

			if ( !out->write_tile( tileX, tileY, 0, TypeDesc::FLOAT, &tile[0] ) )
			{
				throw IECore::Exception( boost::str( boost::format( "Could not write tile to \"%s\", error = %s" ) % fileName % out->geterror() ) );
			}
		}
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// ImageWriter implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( ImageWriter );

size_t ImageWriter::g_firstPlugIndex = 0;

ImageWriter::ImageWriter( const std::string &name )
	:	Gaffer::ExecutableNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ImagePlug( "in" ) );
	addChild( new StringPlug( "fileName" ) );
	addChild(
		new ChannelMaskPlug(
			"channels",
			Gaffer::Plug::In,
			inPlug()->channelNamesPlug()->defaultValue(),
			Gaffer::Plug::Default & ~(Gaffer::Plug::Dynamic | Gaffer::Plug::ReadOnly)
		)
	);
	addChild( new ImagePlug( "out", Plug::Out, Plug::Default & ~Plug::Serialisable ) );
	outPlug()->setInput( inPlug() );

	createFileFormatOptionsPlugs();
}

ImageWriter::~ImageWriter()
{
}

void ImageWriter::createFileFormatOptionsPlugs()
{
	ValuePlug *exrOptionsPlug = new ValuePlug( "openexr" );
	addChild( exrOptionsPlug );
	exrOptionsPlug->addChild( new IntPlug( g_modePlugName, Plug::In, 0 ) );
	exrOptionsPlug->addChild( new StringPlug( g_compressionPlugName, Plug::In, "zip" ) );
	exrOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "half" ) );

	ValuePlug *dpxOptionsPlug = new ValuePlug( "dpx" );
	addChild( dpxOptionsPlug );
	dpxOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "uint10" ) );

	ValuePlug *tifOptionsPlug = new ValuePlug( "tiff" );
	addChild( tifOptionsPlug );
	tifOptionsPlug->addChild( new IntPlug( g_modePlugName, Plug::In, 0 ) );
	tifOptionsPlug->addChild( new StringPlug( g_compressionPlugName, Plug::In, "zip" ) );
	tifOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "uint8" ) );

	ValuePlug *f3dOptionsPlug = new ValuePlug( "field3d" );
	addChild( f3dOptionsPlug );
	f3dOptionsPlug->addChild( new IntPlug( g_modePlugName, Plug::In, 0 ) );
	f3dOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "float" ) );

	ValuePlug *fitsOptionsPlug = new ValuePlug( "fits" );
	addChild( fitsOptionsPlug );
	fitsOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "float" ) );

	ValuePlug *iffOptionsPlug = new ValuePlug( "iff" );
	addChild( iffOptionsPlug );
	iffOptionsPlug->addChild( new IntPlug( g_modePlugName, Plug::In, 1 ) );

	ValuePlug *jpgOptionsPlug = new ValuePlug( "jpeg" );
	addChild( jpgOptionsPlug );
	jpgOptionsPlug->addChild( new IntPlug( g_compressionQualityPlugName, Plug::In, 98, 0, 100 ) );

	ValuePlug *jpeg2000OptionsPlug = new ValuePlug( "jpeg2000" );
	addChild( jpeg2000OptionsPlug );
	jpeg2000OptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "uint8" ) );

	ValuePlug *pngOptionsPlug = new ValuePlug( "png" );
	addChild( pngOptionsPlug );
	pngOptionsPlug->addChild( new StringPlug( g_compressionPlugName, Plug::In, "filtered" ) );
	pngOptionsPlug->addChild( new IntPlug( g_compressionLevelPlugName, Plug::In, 6, Z_NO_COMPRESSION, Z_BEST_COMPRESSION ) );

	ValuePlug *rlaOptionsPlug = new ValuePlug( "rla" );
	addChild( rlaOptionsPlug );
	rlaOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "uint8" ) );

	ValuePlug *sgiOptionsPlug = new ValuePlug( "sgi" );
	addChild( sgiOptionsPlug );
	sgiOptionsPlug->addChild( new StringPlug( g_dataTypePlugName, Plug::In, "uint8" ) );

	ValuePlug *targaOptionsPlug = new ValuePlug( "targa" );
	addChild( targaOptionsPlug );
	targaOptionsPlug->addChild( new StringPlug( g_compressionPlugName, Plug::In, "rle" ) );

	ValuePlug *webpOptionsPlug = new ValuePlug( "webp" );
	addChild( webpOptionsPlug );
	webpOptionsPlug->addChild( new IntPlug( g_compressionQualityPlugName, Plug::In, 100, 0, 100 ) );
}

GafferImage::ImagePlug *ImageWriter::inPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

const GafferImage::ImagePlug *ImageWriter::inPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *ImageWriter::fileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex+1 );
}

const Gaffer::StringPlug *ImageWriter::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex+1 );
}

GafferImage::ChannelMaskPlug *ImageWriter::channelsPlug()
{
	return getChild<ChannelMaskPlug>( g_firstPlugIndex+2 );
}

const GafferImage::ChannelMaskPlug *ImageWriter::channelsPlug() const
{
	return getChild<ChannelMaskPlug>( g_firstPlugIndex+2 );
}

GafferImage::ImagePlug *ImageWriter::outPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex+3 );
}

const GafferImage::ImagePlug *ImageWriter::outPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex+3 );
}

Gaffer::ValuePlug *ImageWriter::fileFormatSettingsPlug( const std::string &fileFormat )
{
	return getChild<ValuePlug>( fileFormat );
}

const Gaffer::ValuePlug *ImageWriter::fileFormatSettingsPlug( const std::string &fileFormat ) const
{
	return getChild<ValuePlug>( fileFormat );
}

const std::string ImageWriter::currentFileFormat() const
{
	const std::string fileName = Context::current()->substitute( fileNamePlug()->getValue() );
	boost::shared_ptr<ImageOutput> out( ImageOutput::create( fileName.c_str() ) );
	if( out != NULL )
	{
		return out->format_name();
	}
	else
	{
		return "";
	}
}

IECore::MurmurHash ImageWriter::hash( const Context *context ) const
{
	Context::Scope scope( context );
	if ( ( fileNamePlug()->getValue() == "" ) || inPlug()->source<ImagePlug>() == inPlug() )
	{
		return IECore::MurmurHash();
	}

	IECore::MurmurHash h = ExecutableNode::hash( context );
	h.append( fileNamePlug()->hash() );
	h.append( channelsPlug()->hash() );
	const std::string fileFormat = currentFileFormat();

	if( fileFormat != "" )
	{
		const ValuePlug *fmtSettingsPlug = fileFormatSettingsPlug( fileFormat );
		if( fmtSettingsPlug != NULL )
		{
			h.append( fmtSettingsPlug->hash() );
		}
	}

	return h;
}

///\todo: We are currently computing all of the channels regardless of whether or not we are outputting them.
/// Change the execute() method to only compute the channels that are masked by the channelsPlug().
void ImageWriter::execute() const
{
	if( !inPlug()->getInput<ImagePlug>() )
	{
		throw IECore::Exception( "No input image." );
	}

	std::string fileName = Context::current()->substitute( fileNamePlug()->getValue() );

	boost::shared_ptr<ImageOutput> out( ImageOutput::create( fileName.c_str() ) );
	if( !out )
	{
		throw IECore::Exception( OpenImageIO::geterror() );
	}

	// Grab the intersection of the channels from the "channels" plug and the image input to see which channels we are to write out.
	IECore::ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
	std::vector<std::string> maskChannels = channelNamesData->readable();
	channelsPlug()->maskChannels( maskChannels );

	if ( !out->supports( "nchannels" ) )
	{
		std::vector<std::string>::iterator cIt( maskChannels.begin() );
		while ( cIt != maskChannels.end() )
		{
			if ( (*cIt) != "R" && (*cIt) != "G" && (*cIt) != "B" && (*cIt) != "A" )
			{
				cIt = maskChannels.erase( cIt );
			}
			else
			{
				++cIt;
			}
		}
	}

	if ( !out->supports( "alpha" ) )
	{
		std::vector<std::string>::iterator alphaChannel( std::find( maskChannels.begin(), maskChannels.end(), "A" ) );
		if ( alphaChannel != maskChannels.end() )
		{
			maskChannels.erase( alphaChannel );
		}
	}

	const int nChannels = maskChannels.size();

	// Get the image channel data.
	IECore::ImagePrimitivePtr imagePtr( inPlug()->image() );

	// Get the image's display window.
	const Imath::Box2i displayWindow( imagePtr->getDisplayWindow() );
	const Imath::Box2i dataWindow( imagePtr->getDataWindow() );

	ImageSpec spec = createImageSpec( this, out.get(), dataWindow, displayWindow );

	spec.nchannels = nChannels;
	spec.default_channel_names();

	// Add the channel names to the header whilst getting pointers to the channel data.
	std::vector<const float*> channelPtrs;
	spec.channelnames.clear();
	for ( std::vector<std::string>::iterator channelIt( maskChannels.begin() ); channelIt != maskChannels.end(); channelIt++ )
	{
		spec.channelnames.push_back( *channelIt );
		IECore::FloatVectorDataPtr dataPtr = imagePtr->getChannel<float>( *channelIt );
		channelPtrs.push_back( &(dataPtr->readable()[0]) );

		// OIIO has a special attribute for the Alpha and Z channels. If we find some, we should tag them...
		if ( *channelIt == "A" )
		{
			spec.alpha_channel = channelIt-maskChannels.begin();
		} else if ( *channelIt == "Z" )
		{
			spec.z_channel = channelIt-maskChannels.begin();
		}
	}

	// create the directories before opening the file
	boost::filesystem::path directory = boost::filesystem::path( fileName ).parent_path();
	if( !directory.empty() )
	{
		boost::filesystem::create_directories( directory );
	}

	if ( out->open( fileName, spec ) )
	{
		IECore::msg( IECore::MessageHandler::Info, this->relativeName( this->scriptNode() ), "Writing " + fileName );
	}
	else
	{
		throw IECore::Exception( boost::str( boost::format( "Could not open \"%s\", error = %s" ) % fileName % out->geterror() ) );
	}

	if ( spec.tile_width == 0 )
	{
		writeImageScanlines( this, out, channelPtrs, spec, dataWindow, fileName );
	}
	else
	{
		writeImageTiles( this, out, channelPtrs, spec, dataWindow, fileName );
	}

	out->close();
}
