//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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

#include "OpenEXR/half.h"

#include "OpenImageIO/imagecache.h"
OIIO_NAMESPACE_USING

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

#include "GafferImage/ImageReader.h"

using namespace std;
using namespace tbb;
using namespace Imath;
using namespace IECore;
using namespace GafferImage;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// We use an OIIO image cache to deal with all file loading etc. This works
// well for us, as due to the Gaffer architecture we'll be receiving many
// different calls on different threads, each potentially asking for different
// files (expressions and timewarps etc can change the fileName at any time).
// The OIIO image cache is designed for exactly this scenario.
//////////////////////////////////////////////////////////////////////////

spin_rw_mutex g_imageCacheMutex;
static ImageCache *imageCache()
{
	spin_rw_mutex::scoped_lock lock( g_imageCacheMutex, false );
	static ImageCache *cache = 0;
	if( cache == 0 )
	{
		if( lock.upgrade_to_writer() )
		{
			cache = ImageCache::create();
			// ImageReaderTest.testOIIOJpgRead exposes a bug in
			// OpenImageIO where ImageCache::get_pixels() returns
			// incorrect data when reading from non-float images.
			// By forcing the image to be float on loading, we
			// can work around that problem.
			/// \todo Consider removing this once the bug is fixed in
			/// OIIO - and test any performance implications of performing
			/// the conversion in get_pixels() rather than immediately on load.
			cache->attribute( "forcefloat", 1 );
		}
	}
	return cache;
}

//////////////////////////////////////////////////////////////////////////
// Utility for converting OIIO::TypeDesc types to IECore::Data types.
//////////////////////////////////////////////////////////////////////////

namespace
{

void oiioParameterListToMetadata( const ImageIOParameterList &paramList, CompoundObject *metadata )
{
	CompoundObject::ObjectMap &members = metadata->members();
	for ( ImageIOParameterList::const_iterator it = paramList.begin(); it != paramList.end(); ++it )
	{
		ObjectPtr value = NULL;
		
		const TypeDesc &type = it->type();
		switch ( type.basetype )
		{
			case TypeDesc::CHAR :
			{
				if ( type.aggregate == TypeDesc::SCALAR )
				{
					value = new CharData( *static_cast<const char *>( it->data() ) );
				}
				break;
			}
			case TypeDesc::UCHAR :
			{
				if ( type.aggregate == TypeDesc::SCALAR )
				{
					value = new UCharData( *static_cast<const unsigned char *>( it->data() ) );
				}
				break;
			}
			case TypeDesc::STRING :
			{
				if ( type.aggregate == TypeDesc::SCALAR )
				{
					value = new StringData( *static_cast<const std::string *>( it->data() ) );
				}
				break;
			}
			case TypeDesc::USHORT :
			{
				if ( type.aggregate == TypeDesc::SCALAR )
				{
					value = new UShortData( *static_cast<const unsigned short *>( it->data() ) );
				}
				break;
			}
			case TypeDesc::SHORT :
			{
				if ( type.aggregate == TypeDesc::SCALAR )
				{
					value = new ShortData( *static_cast<const short *>( it->data() ) );
				}
				break;
			}
			case TypeDesc::UINT :
			{
				if ( type.aggregate == TypeDesc::SCALAR )
				{
					value = new UIntData( *static_cast<const unsigned *>( it->data() ) );
				}
				break;
			}
			case TypeDesc::INT :
			{
				const int *data = static_cast<const int *>( it->data() );
				switch ( type.aggregate )
				{
					case TypeDesc::SCALAR :
					{
						value = new IntData( *data );
						break;
					}
					case TypeDesc::VEC2 :
					{
						value = new V2iData( Imath::V2i( data[0], data[1] ) );
						break;
					}
					case TypeDesc::VEC3 :
					{
						value = new V3iData( Imath::V3i( data[0], data[1], data[2] ) );
						break;
					}
					default :
					{
						break;
					}
				}
				break;
			}
			case TypeDesc::HALF :
			{
				if ( type.aggregate == TypeDesc::SCALAR )
				{
					value = new HalfData( *static_cast<const half *>( it->data() ) );
				}
				break;
			}
			case TypeDesc::FLOAT :
			{
				const float *data = static_cast<const float *>( it->data() );
				switch ( type.aggregate )
				{
					case TypeDesc::SCALAR :
					{
						value = new FloatData( *data );
						break;
					}
					case TypeDesc::VEC2 :
					{
						value = new V2fData( Imath::V2f( data[0], data[1] ) );
						break;
					}
					case TypeDesc::VEC3 :
					{
						value = new V3fData( Imath::V3f( data[0], data[1], data[2] ) );
						break;
					}
					case TypeDesc::MATRIX44 :
					{
						value = new M44fData( Imath::M44f( data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10], data[11], data[12], data[13], data[14], data[15] ) );
						break;
					}
					default :
					{
						break;
					}
				}
				break;
			}
			case TypeDesc::DOUBLE :
			{
				const double *data = static_cast<const double *>( it->data() );
				switch ( type.aggregate )
				{
					case TypeDesc::SCALAR :
					{
						value = new DoubleData( *data );
						break;
					}
					case TypeDesc::VEC2 :
					{
						value = new V2dData( Imath::V2d( data[0], data[1] ) );
						break;
					}
					case TypeDesc::VEC3 :
					{
						value = new V3dData( Imath::V3d( data[0], data[1], data[2] ) );
						break;
					}
					case TypeDesc::MATRIX44 :
					{
						value = new M44dData( Imath::M44d( data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10], data[11], data[12], data[13], data[14], data[15] ) );
						break;
					}
					default :
					{
						break;
					}
				}
				break;
			}
			default :
			{
				break;
			}
		}
		
		if ( value )
		{
			members[ it->name().string() ] = value;
		}
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// ImageReader implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( ImageReader );

size_t ImageReader::g_firstPlugIndex = 0;

ImageReader::ImageReader( const std::string &name )
	:	ImageNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "fileName" ) );
	addChild( new IntPlug( "refreshCount" ) );

	// disable caching on our outputs, as OIIO is already doing caching for us.
	for( OutputPlugIterator it( outPlug() ); it!=it.end(); it++ )
	{
		(*it)->setFlags( Plug::Cacheable, false );
	}
	
	plugSetSignal().connect( boost::bind( &ImageReader::plugSet, this, ::_1 ) );
}

ImageReader::~ImageReader()
{
}

Gaffer::StringPlug *ImageReader::fileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *ImageReader::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *ImageReader::refreshCountPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *ImageReader::refreshCountPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

bool ImageReader::enabled() const
{
	std::string fileName = fileNamePlug()->getValue();
	
	/// \todo We get the spec here, and then we go and get it again in the
	/// hash()/compute() functions if we turn out to be enabled. This overhead
	/// is a fundamental problem with the whole enabled() mechanism - we should
	/// stop using it, and just deal with missing files in the various methods
	/// that try to access them.
	/// \todo This is swallowing errors when we should be reporting them via
	/// exceptions. Fix it.
	const ImageSpec *spec = imageCache()->imagespec( ustring( fileName.c_str() ) );
	if( spec == 0 )
	{
		// clear error on failure to prevent error buffer overflow crash.
		imageCache()->geterror();
		return false;
	}
	
	return ImageNode::enabled();
}

size_t ImageReader::supportedExtensions( std::vector<std::string> &extensions )
{
	std::string attr;
	if( !getattribute( "extension_list", attr ) )
	{
		return extensions.size();
	}

	typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;
	Tokenizer formats( attr, boost::char_separator<char>( ";" ) );
	for( Tokenizer::const_iterator fIt = formats.begin(), eFIt = formats.end(); fIt != eFIt; ++fIt )
	{
		size_t colonPos = fIt->find( ':' );
		if( colonPos != string::npos )
		{
			std::string formatExtensions = fIt->substr( colonPos + 1 );
			Tokenizer extTok( formatExtensions, boost::char_separator<char>( "," ) );
			std::copy( extTok.begin(), extTok.end(), std::back_inserter( extensions ) );
		}
	}

	return extensions.size();
}

void ImageReader::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageNode::affects( input, outputs );

	if( input == fileNamePlug() || input == refreshCountPlug() )
	{
		for( ValuePlugIterator it( outPlug() ); it != it.end(); it++ )
		{
			outputs.push_back( it->get() );
		}
	}
}

void ImageReader::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashFormat( output, context, h );
	fileNamePlug()->hash( h );
	refreshCountPlug()->hash( h );
}

GafferImage::Format ImageReader::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	const ImageSpec *spec = imageCache()->imagespec( ustring( fileName.c_str() ) );

	return GafferImage::Format(
		Imath::Box2i(
			Imath::V2i( spec->full_x, spec->full_y ),
			Imath::V2i( spec->full_x + spec->full_width - 1, spec->full_y + spec->full_height - 1 )
		),
		spec->get_float_attribute( "PixelAspectRatio", 1.0f )
	);
}

void ImageReader::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashDataWindow( output, context, h );
	fileNamePlug()->hash( h );
	refreshCountPlug()->hash( h );
}

Imath::Box2i ImageReader::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	const ImageSpec *spec = imageCache()->imagespec( ustring( fileName.c_str() ) );

	Format format( Imath::Box2i( Imath::V2i( spec->full_x, spec->full_y ), Imath::V2i( spec->full_width + spec->full_x - 1, spec->full_height + spec->full_y - 1 ) ) );
	Imath::Box2i dataWindow( Imath::V2i( spec->x, spec->y ), Imath::V2i( spec->width + spec->x - 1, spec->height + spec->y - 1 ) );

	return format.yDownToFormatSpace( dataWindow );
}

void ImageReader::hashMetadata( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashMetadata( output, context, h );
	fileNamePlug()->hash( h );
	refreshCountPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr ImageReader::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	const ImageSpec *spec = imageCache()->imagespec( ustring( fileName.c_str() ) );
	
	CompoundObjectPtr result = new CompoundObject;
	oiioParameterListToMetadata( spec->extra_attribs, result.get() );
	
	return result;
}

void ImageReader::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashChannelNames( output, context, h );
	fileNamePlug()->hash( h );
	refreshCountPlug()->hash( h );
}

IECore::ConstStringVectorDataPtr ImageReader::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	const ImageSpec *spec = imageCache()->imagespec( ustring( fileName.c_str() ) );
	StringVectorDataPtr result = new StringVectorData();
	result->writable() = spec->channelnames;
	return result;
}

void ImageReader::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashChannelData( output, context, h );
	h.append( context->get<V2i>( ImagePlug::tileOriginContextName ) );
	h.append( context->get<std::string>( ImagePlug::channelNameContextName ) );
	fileNamePlug()->hash( h );
	refreshCountPlug()->hash( h );
}

IECore::ConstFloatVectorDataPtr ImageReader::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	ustring uFileName( fileName.c_str() );
	const ImageSpec *spec = imageCache()->imagespec( uFileName );

	vector<string>::const_iterator channelIt = find( spec->channelnames.begin(), spec->channelnames.end(), channelName );
	if( channelIt == spec->channelnames.end() )
	{
		{
			return parent->channelDataPlug()->defaultValue();
		}
	}

	Format format( Imath::Box2i( Imath::V2i( spec->full_x, spec->full_y ), Imath::V2i( spec->full_width + spec->full_x - 1, spec->full_height + spec->full_y - 1 ) ) );
	const int newY = format.formatToYDownSpace( tileOrigin.y + ImagePlug::tileSize() - 1 );

	std::vector<float> channelData( ImagePlug::tileSize() * ImagePlug::tileSize() );
	size_t channelIndex = channelIt - spec->channelnames.begin();
	imageCache()->get_pixels(
		uFileName,
		0, 0, // subimage, miplevel
		tileOrigin.x, tileOrigin.x + ImagePlug::tileSize(),
		newY, newY + ImagePlug::tileSize(),
		0, 1,
		channelIndex, channelIndex + 1,
		TypeDesc::FLOAT,
		&(channelData[0])
	);

	// Create the output data buffer.
	FloatVectorDataPtr resultData = new FloatVectorData;
	vector<float> &result = resultData->writable();
	result.resize( ImagePlug::tileSize() * ImagePlug::tileSize() );

	// Flip the tile in the Y axis to convert it to our internal image data representation.
	for( int y = 0; y < ImagePlug::tileSize(); ++y )
	{
		memcpy( &(result[ ( ImagePlug::tileSize() - y - 1 ) * ImagePlug::tileSize() ]), &(channelData[ y * ImagePlug::tileSize() ]), sizeof(float)*ImagePlug::tileSize()  );
	}

	return resultData;
}

void ImageReader::plugSet( Gaffer::Plug *plug )
{
	// this clears the cache every time the refresh count is updated, so you don't get entries
	// from old files hanging around.
	if( plug == refreshCountPlug() )
	{
		imageCache()->invalidate_all( true );
	}
}
