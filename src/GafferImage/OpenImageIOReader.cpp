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
#include "boost/filesystem/path.hpp"
#include "boost/regex.hpp"

#include "OpenEXR/half.h"

#include "OpenImageIO/imagecache.h"
OIIO_NAMESPACE_USING

#include "IECore/FileSequence.h"
#include "IECore/FileSequenceFunctions.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"

#include "GafferImage/OpenImageIOReader.h"
#include "GafferImage/FormatPlug.h"

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

namespace
{

spin_rw_mutex g_imageCacheMutex;
ImageCache *imageCache()
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

			// Set an initial cache size of 500Mb
			cache->attribute( "max_memory_MB", 500.0f );
		}
	}
	return cache;
}

// Returns the OIIO ImageSpec for the given filename in the current
// context. Throws if the file is invalid, and returns NULL if
// the filename is empty.
const ImageSpec *imageSpec( std::string &fileName, OpenImageIOReader::MissingFrameMode mode, const OpenImageIOReader *node, const Context *context )
{
	if( fileName.empty() )
	{
		return NULL;
	}

	const std::string resolvedFileName = context->substitute( fileName );

	ImageCache *cache = imageCache();
	const ImageSpec *spec = cache->imagespec( ustring( resolvedFileName ) );
	if( !spec )
	{
		if( mode == OpenImageIOReader::Black )
		{
			// we can simply return the null spec and rely on the
			// compute methods to return default plug values.
			return spec;
		}
		else if( mode == OpenImageIOReader::Hold )
		{
			ConstIntVectorDataPtr frameData = node->availableFramesPlug()->getValue();
			const std::vector<int> &frames = frameData->readable();
			if( frames.size() )
			{
				std::vector<int>::const_iterator fIt = std::lower_bound( frames.begin(), frames.end(), (int)context->getFrame() );

				// decrement to get the previous frame, unless
				// this is the first frame, in which case we
				// hold to the beginning of the sequence
				if( fIt != frames.begin() )
				{
					fIt--;
				}

				// clear any error from the original fileName
				cache->geterror();

				// setup a context with the new frame
				ContextPtr holdContext = new Context( *context, Context::Shared );
				holdContext->setFrame( *fIt );

				return imageSpec( fileName, OpenImageIOReader::Error, node, holdContext.get() );
			}

			// if we got here, there was no suitable file sequence
			throw( IECore::Exception( cache->geterror() ) );
		}
		else
		{
			throw( IECore::Exception( cache->geterror() ) );
		}
	}

	// we overwrite the incoming fileName with
	// the final successful fileName because
	// computeChannelData needs to know the real
	// file in order to fetch the pixels, and it
	// isn't available from the ImageSpec directly.
	fileName = resolvedFileName;

	return spec;
}

} // namespace

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
// OpenImageIOReader implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( OpenImageIOReader );

size_t OpenImageIOReader::g_firstPlugIndex = 0;

OpenImageIOReader::OpenImageIOReader( const std::string &name )
	:	ImageNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild(
		new StringPlug(
			"fileName", Plug::In, "",
			/* flags */ Plug::Default,
			/* substitutions */ Context::AllSubstitutions & ~Context::FrameSubstitutions
		)
	);
	addChild( new IntPlug( "refreshCount" ) );
	addChild( new IntPlug( "missingFrameMode", Plug::In, Error, /* min */ Error, /* max */ Hold ) );
	addChild( new IntVectorDataPlug( "availableFrames", Plug::Out, new IntVectorData ) );

	// disable caching on our outputs, as OIIO is already doing caching for us.
	for( OutputPlugIterator it( outPlug() ); !it.done(); ++it )
	{
		(*it)->setFlags( Plug::Cacheable, false );
	}

	plugSetSignal().connect( boost::bind( &OpenImageIOReader::plugSet, this, ::_1 ) );
}

OpenImageIOReader::~OpenImageIOReader()
{
}

Gaffer::StringPlug *OpenImageIOReader::fileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *OpenImageIOReader::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *OpenImageIOReader::refreshCountPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *OpenImageIOReader::refreshCountPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug *OpenImageIOReader::missingFrameModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *OpenImageIOReader::missingFrameModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

Gaffer::IntVectorDataPlug *OpenImageIOReader::availableFramesPlug()
{
	return getChild<IntVectorDataPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::IntVectorDataPlug *OpenImageIOReader::availableFramesPlug() const
{
	return getChild<IntVectorDataPlug>( g_firstPlugIndex + 3 );
}

size_t OpenImageIOReader::supportedExtensions( std::vector<std::string> &extensions )
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

void OpenImageIOReader::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageNode::affects( input, outputs );

	if( input == fileNamePlug() || input == refreshCountPlug() )
	{
		outputs.push_back( availableFramesPlug() );
	}

	if( input == fileNamePlug() || input == refreshCountPlug() || input == missingFrameModePlug() )
	{
		for( ValuePlugIterator it( outPlug() ); !it.done(); ++it )
		{
			outputs.push_back( it->get() );
		}
	}
}

void OpenImageIOReader::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hash( output, context, h );

	if( output == availableFramesPlug() )
	{
		fileNamePlug()->hash( h );
		refreshCountPlug()->hash( h );
	}
}

void OpenImageIOReader::compute( ValuePlug *output, const Context *context ) const
{
	if( output == availableFramesPlug() )
	{
		FileSequencePtr fileSequence = NULL;
		IECore::ls( fileNamePlug()->getValue(), fileSequence, /* minSequenceSize */ 1 );

		if( fileSequence )
		{
			IntVectorDataPtr resultData = new IntVectorData;
			std::vector<FrameList::Frame> frames;
			fileSequence->getFrameList()->asList( frames );
			std::vector<int> &result = resultData->writable();
			result.resize( frames.size() );
			std::copy( frames.begin(), frames.end(), result.begin() );
			static_cast<IntVectorDataPlug *>( output )->setValue( resultData );
		}
		else
		{
			static_cast<IntVectorDataPlug *>( output )->setToDefault();
		}
	}
	else
	{
		ImageNode::compute( output, context );
	}
}

void OpenImageIOReader::hashFileName( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	// since fileName excludes frame substitutions
	// but we internally vary the result output by
	// frame, we need to explicitly hash the frame
	// when the value contains FrameSubstitutions.
	const std::string fileName = fileNamePlug()->getValue();
	h.append( fileName );
	if( Context::substitutions( fileName ) & Context::FrameSubstitutions )
	{
		h.append( context->getFrame() );
	}
}

void OpenImageIOReader::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashFormat( output, context, h );
	hashFileName( context, h );
	refreshCountPlug()->hash( h );
	missingFrameModePlug()->hash( h );
}

GafferImage::Format OpenImageIOReader::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	// when we're in MissingFrameMode::Black we still want to
	// match the format of the Hold frame.
	MissingFrameMode mode = (MissingFrameMode)missingFrameModePlug()->getValue();
	mode = ( mode == Black ) ? Hold : mode;
	const ImageSpec *spec = imageSpec( fileName, mode, this, context );
	if( !spec )
	{
		return FormatPlug::getDefaultFormat( context );
	}

	return GafferImage::Format(
		Imath::Box2i(
			Imath::V2i( spec->full_x, spec->full_y ),
			Imath::V2i( spec->full_x + spec->full_width, spec->full_y + spec->full_height )
		),
		spec->get_float_attribute( "PixelAspectRatio", 1.0f )
	);
}

void OpenImageIOReader::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashDataWindow( output, context, h );
	hashFileName( context, h );
	refreshCountPlug()->hash( h );
	missingFrameModePlug()->hash( h );
}

Imath::Box2i OpenImageIOReader::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	const ImageSpec *spec = imageSpec( fileName, (MissingFrameMode)missingFrameModePlug()->getValue(), this, context );
	if( !spec )
	{
		return parent->dataWindowPlug()->defaultValue();
	}

	Format format( Imath::Box2i( Imath::V2i( spec->full_x, spec->full_y ), Imath::V2i( spec->full_width + spec->full_x, spec->full_height + spec->full_y ) ) );
	Imath::Box2i dataWindow( Imath::V2i( spec->x, spec->y ), Imath::V2i( spec->width + spec->x - 1, spec->height + spec->y - 1 ) );

	return format.fromEXRSpace( dataWindow );
}

void OpenImageIOReader::hashMetadata( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashMetadata( output, context, h );
	hashFileName( context, h );
	refreshCountPlug()->hash( h );
	missingFrameModePlug()->hash( h );
}

IECore::ConstCompoundObjectPtr OpenImageIOReader::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	const ImageSpec *spec = imageSpec( fileName, (MissingFrameMode)missingFrameModePlug()->getValue(), this, context );
	if( !spec )
	{
		return parent->metadataPlug()->defaultValue();
	}

	CompoundObjectPtr result = new CompoundObject;
	oiioParameterListToMetadata( spec->extra_attribs, result.get() );

	return result;
}

void OpenImageIOReader::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashChannelNames( output, context, h );
	hashFileName( context, h );
	refreshCountPlug()->hash( h );
	missingFrameModePlug()->hash( h );
}

IECore::ConstStringVectorDataPtr OpenImageIOReader::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	const ImageSpec *spec = imageSpec( fileName, (MissingFrameMode)missingFrameModePlug()->getValue(), this, context );
	if( !spec )
	{
		return parent->channelNamesPlug()->defaultValue();
	}

	StringVectorDataPtr result = new StringVectorData();
	result->writable() = spec->channelnames;
	return result;
}

void OpenImageIOReader::hashDeepState( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashDeepState( output, context, h );
}

int OpenImageIOReader::computeDeepState( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::Flat;
}

void OpenImageIOReader::hashSampleOffsets( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImagePlug::flatTileSampleOffsets()->hash( h );
}

IECore::ConstIntVectorDataPtr OpenImageIOReader::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::flatTileSampleOffsets();
}

void OpenImageIOReader::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashChannelData( output, context, h );
	h.append( context->get<V2i>( ImagePlug::tileOriginContextName ) );
	h.append( context->get<std::string>( ImagePlug::channelNameContextName ) );
	hashFileName( context, h );
	refreshCountPlug()->hash( h );
	missingFrameModePlug()->hash( h );
}

IECore::ConstFloatVectorDataPtr OpenImageIOReader::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string fileName = fileNamePlug()->getValue();
	const ImageSpec *spec = imageSpec( fileName, (MissingFrameMode)missingFrameModePlug()->getValue(), this, context );
	if( !spec )
	{
		return parent->channelDataPlug()->defaultValue();
	}

	vector<string>::const_iterator channelIt = find( spec->channelnames.begin(), spec->channelnames.end(), channelName );
	if( channelIt == spec->channelnames.end() )
	{
		{
			return parent->channelDataPlug()->defaultValue();
		}
	}

	Format format( Imath::Box2i( Imath::V2i( spec->full_x, spec->full_y ), Imath::V2i( spec->full_width + spec->full_x, spec->full_height + spec->full_y ) ) );
	const int newY = format.toEXRSpace( tileOrigin.y + ImagePlug::tileSize() - 1 );

	std::vector<float> channelData( ImagePlug::tileSize() * ImagePlug::tileSize() );
	size_t channelIndex = channelIt - spec->channelnames.begin();
	imageCache()->get_pixels(
		ustring( fileName ),
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

size_t OpenImageIOReader::getCacheMemoryLimit()
{
	float memoryLimit;
	imageCache()->getattribute( "max_memory_MB", memoryLimit );
	return (size_t)memoryLimit;
}

void OpenImageIOReader::setCacheMemoryLimit( size_t mb )
{
	imageCache()->attribute( "max_memory_MB", float( mb ) );
}

void OpenImageIOReader::plugSet( Gaffer::Plug *plug )
{
	// this clears the cache every time the refresh count is updated, so you don't get entries
	// from old files hanging around.
	if( plug == refreshCountPlug() )
	{
		imageCache()->invalidate_all( true );
	}
}
