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

#include "boost/filesystem.hpp"

#include "OpenImageIO/imageio.h"
OIIO_NAMESPACE_USING

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
	addChild( new IntPlug( "writeMode" ) );
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
}

ImageWriter::~ImageWriter()
{
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

Gaffer::IntPlug *ImageWriter::writeModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex+2 );
}

const Gaffer::IntPlug *ImageWriter::writeModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex+2 );
}

GafferImage::ChannelMaskPlug *ImageWriter::channelsPlug()
{
	return getChild<ChannelMaskPlug>( g_firstPlugIndex+3 );
}

const GafferImage::ChannelMaskPlug *ImageWriter::channelsPlug() const
{
	return getChild<ChannelMaskPlug>( g_firstPlugIndex+3 );
}

GafferImage::ImagePlug *ImageWriter::outPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex + 4 );
}

const GafferImage::ImagePlug *ImageWriter::outPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex + 4 );
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
	h.append( writeModePlug()->hash() );
	h.append( channelsPlug()->hash() );
	return h;
}

///\todo: We are currently computing all of the channels regardless of whether or not we are outputting them.
/// Change the execute() method to only compute the channels that are masked by the channelsPlug().

///\todo: It seems that if a JPG is written with RGBA channels the output is wrong but it should be supported. Find out why and fix it.
/// There is a test case in ImageWriterTest which checks the output of the jpg writer against an incorrect image and it will fail if it is equal to the writer output.
void ImageWriter::execute() const
{
	if( !inPlug()->getInput<ImagePlug>() )
	{
		throw IECore::Exception( "No input image." );
	}

	std::string fileName = fileNamePlug()->getValue();
	fileName = Context::current()->substitute( fileName );

	boost::shared_ptr<ImageOutput> out( ImageOutput::create( fileName.c_str() ) );
	if( !out )
	{
		throw IECore::Exception( OpenImageIO::geterror() );
	}

	// Grab the intersection of the channels from the "channels" plug and the image input to see which channels we are to write out.
	IECore::ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
	std::vector<std::string> maskChannels = channelNamesData->readable();
	channelsPlug()->maskChannels( maskChannels );
	const int nChannels = maskChannels.size();

	// Get the image channel data.
	IECore::ImagePrimitivePtr imagePtr( inPlug()->image() );

	// Get the image's display window.
	const Imath::Box2i displayWindow( imagePtr->getDisplayWindow() );
	const int displayWindowWidth = displayWindow.size().x+1;
	const int displayWindowHeight = displayWindow.size().y+1;

	// Get the image's data window and if it then set a flag.
	bool imageIsBlack = false;
	Imath::Box2i dataWindow( imagePtr->getDataWindow() );
	if ( inPlug()->dataWindowPlug()->getValue().isEmpty() )
	{
		dataWindow = displayWindow;
		imageIsBlack = true;
	}

	bool supportsDisplayWindow = out->supports( "displaywindow" );
	bool resizeDataArea = false;

	int dataWindowWidth;
	int dataWindowHeight;

	if ( supportsDisplayWindow )
	{
		dataWindowWidth = dataWindow.size().x+1;
		dataWindowHeight = dataWindow.size().y+1;
	}
	else
	{
		dataWindowWidth = displayWindow.size().x+1;
		dataWindowHeight = displayWindow.size().y+1;
	}

	// Create the image header.
	ImageSpec spec( dataWindowWidth, dataWindowHeight, nChannels, TypeDesc::FLOAT );

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

	// Specify the display window.
	spec.full_x = displayWindow.min.x;
	spec.full_y = displayWindow.min.y;
	spec.full_width = displayWindowWidth;
	spec.full_height = displayWindowHeight;

	if ( supportsDisplayWindow )
	{
		spec.x = dataWindow.min.x;
		spec.y = dataWindow.min.y;
	}
	else
	{
		spec.x = displayWindow.min.x;
		spec.y = displayWindow.min.y;

		resizeDataArea = (displayWindow != dataWindow);
	}

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
	if ( const ScriptNode *script = ancestor<ScriptNode>() )
	{
		const std::string scriptFile = script->fileNamePlug()->getValue();
		document = ( scriptFile == "" ) ? document : scriptFile;
	}
	spec.attribute( "DocumentName", document );
	
	// Add the metadata to the spec, removing metadata that could affect the resulting channel data
	CompoundObjectPtr metadata = inPlug()->metadataPlug()->getValue()->copy();
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
	
	// PixelAspectRatio must be defined by the FormatPlug
	spec.attribute( "PixelAspectRatio", (float)inPlug()->formatPlug()->getValue().getPixelAspect() );
	
	// create the directories before opening the file
	boost::filesystem::path directory = boost::filesystem::path( fileName ).parent_path();
	if( !directory.empty() )
	{
		boost::filesystem::create_directories( directory );
	}
	
	if ( !out->open( fileName, spec ) )
	{
		throw IECore::Exception( boost::str( boost::format( "Could not open \"%s\", error = %s" ) % fileName % out->geterror() ) );
	}

	// Only allow tiled output if our file format supports it.
	int writeMode = writeModePlug()->getValue() & out->supports( "tile" );

	if ( writeMode == Scanline )
	{
		// Create a buffer for the scanline.
		float scanline[ nChannels*dataWindowWidth ];
		bool scanlineIsBlack = false;

		if ( imageIsBlack )
		{
			memset( scanline, 0, sizeof(float) * nChannels*dataWindowWidth );

			for ( int y = spec.y; y < spec.y + dataWindowHeight; ++y )
			{
				if ( !out->write_scanline( y, 0, TypeDesc::FLOAT, &scanline[0] ) )
				{
					throw IECore::Exception( boost::str( boost::format( "Could not write scanline to \"%s\", error = %s" ) % fileName % out->geterror() ) );
				}
			}
		}
		else
		{
			// Interleave the channel data and write it by scanline to the file.
			if ( resizeDataArea )
			{
				if ( dataWindow.min.x > 0 || dataWindow.max.x < dataWindowWidth )
				{
					memset( scanline, 0, sizeof(float) * nChannels*dataWindowWidth );
					scanlineIsBlack = true;
				}

				for ( int y = 0; y < dataWindowHeight; ++y )
				{
					if ( y < dataWindow.min.y || y > dataWindow.max.y )
					{
						if ( !scanlineIsBlack )
						{
							memset( scanline, 0, sizeof(float) * nChannels*dataWindowWidth );
							scanlineIsBlack = true;
						}
					}
					else
					{
						for ( std::vector<const float *>::iterator channelDataIt( channelPtrs.begin() ); channelDataIt != channelPtrs.end(); channelDataIt++ )
						{
							scanlineIsBlack = false;
							float *outPtr = &scanline[0] + (channelDataIt - channelPtrs.begin()); // The pointer that we are writing to.
							// The row that we are reading from is flipped (in the Y) as we use a different image space internally to OpenEXR and OpenImageIO.
							const float *inRowPtr = (*channelDataIt) + ( y - dataWindow.min.y ) * (dataWindow.max.x - dataWindow.min.x + 1);
							const int inc = channelPtrs.size();

							outPtr += (inc * dataWindow.min.x);

							// Because scanline was initalised as black, we never need to set the pixels either side
							// of the data window, as they will remain black
							for ( int x = dataWindow.min.x; x < min(dataWindow.max.x+1, dataWindowWidth); ++x, outPtr += inc )
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
			else
			{
				for ( int y = dataWindow.min.y; y <= dataWindow.max.y; ++y )
				{
					for ( std::vector<const float *>::iterator channelDataIt( channelPtrs.begin() ); channelDataIt != channelPtrs.end(); channelDataIt++ )
					{
						float *outPtr = &scanline[0] + (channelDataIt - channelPtrs.begin()); // The pointer that we are writing to.
						// The row that we are reading from is flipped (in the Y) as we use a different image space internally to OpenEXR and OpenImageIO.
						const float *inRowPtr = (*channelDataIt) + ( y - spec.y ) * dataWindowWidth;
						const int inc = channelPtrs.size();
						for ( int x = 0; x < dataWindowWidth; ++x, outPtr += inc )
						{
							*outPtr = *inRowPtr++;
						}
					}

					if ( !out->write_scanline( y, 0, TypeDesc::FLOAT, &scanline[0] ) )
					{
						throw IECore::Exception( boost::str( boost::format( "Could not write scanline to \"%s\", error = %s" ) % fileName % out->geterror() ) );
					}
				}
			}
		}
	}
	// Tiled output
	else
	{
		// Create a buffer for the tile.
		const int tileSize = ImagePlug::tileSize();
		float tile[ nChannels*tileSize*tileSize ];

		if ( imageIsBlack )
		{
			memset( tile, 0,  sizeof(float) * nChannels*tileSize*tileSize );
			for ( int tileY = 0; tileY < dataWindowHeight; tileY += tileSize )
			{
				for ( int tileX = 0; tileX < dataWindowWidth; tileX += tileSize )
				{
					if ( !out->write_tile( tileX+spec.x, tileY+spec.y, 0, TypeDesc::FLOAT, &tile[0] ) )
					{
						throw IECore::Exception( boost::str( boost::format( "Could not write tile to \"%s\", error = %s" ) % fileName % out->geterror() ) );
					}
				}
			}
		}
		else
		{
			if ( resizeDataArea )
			{
			}
			else
			{
				// Interleave the channel data and write it to the file tile-by-tile.
				for ( int tileY = 0; tileY < dataWindowHeight; tileY += tileSize )
				{
					for ( int tileX = 0; tileX < dataWindowWidth; tileX += tileSize )
					{
						float *outPtr = &tile[0];

						const int r = std::min( tileSize+tileX, dataWindowWidth );
						const int t = std::min( tileSize+tileY, dataWindowHeight );

						for ( int y = 0; y < t; ++y )
						{
							for ( std::vector<const float *>::iterator channelDataIt( channelPtrs.begin() ); channelDataIt != channelPtrs.end(); channelDataIt++ )
							{
								const int inc = channelPtrs.size();
								const float *inRowPtr = (*channelDataIt) + ( tileY + t - y - 1 ) * dataWindowWidth;
								for ( int x = 0; x < r; ++x, outPtr += inc )
								{
									*outPtr = *inRowPtr+(tileX+x);
								}
							}
						}

						if ( !out->write_tile( tileX+spec.x, tileY+spec.y, 0, TypeDesc::FLOAT, &tile[0] ) )
						{
							throw IECore::Exception( boost::str( boost::format( "Could not write tile to \"%s\", error = %s" ) % fileName % out->geterror() ) );
						}
					}
				}
			}
		}
	}

	out->close();
}

