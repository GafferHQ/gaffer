//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/ImageGadget.h"

#include "GafferUI/Style.h"
#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "IECoreGL/Texture.h"
#include "IECoreGL/TextureLoader.h"
#include "IECoreGL/ToGLTextureConverter.h"

#include "IECoreImage/ImageReader.h"

#include "IECore/Exception.h"
#include "IECore/SearchPath.h"

#include "OpenImageIO/color.h"
#include "OpenImageIO/imagebuf.h"
#include "OpenImageIO/imagebufalgo.h"

#include "fmt/format.h"

using namespace Imath;
using namespace IECore;
using namespace IECoreImage;
using namespace IECoreGL;
using namespace GafferUI;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

std::string resolvedFileName( const std::string &fileName )
{
	const char *s = getenv( "GAFFERUI_IMAGE_PATHS" );
	IECore::SearchPath sp( s ? s : "" );

	boost::filesystem::path path = sp.find( fileName );
	if( path.empty() )
	{
		throw Exception( "Could not find file '" + fileName + "'" );
	}

	return path.generic_string();
}

Box3f boundGetter( const std::string &fileName, size_t &cost, const IECore::Canceller *canceller )
{
	OIIO::ImageBuf imageBuf( resolvedFileName( fileName ) );
	if( imageBuf.has_error() )
	{
		throw Exception( imageBuf.geterror() );
	}

	cost = 1;
	const V2i pixelSize( imageBuf.spec().full_width, imageBuf.spec().full_height );
	V3f size( pixelSize.x, pixelSize.y, 0.0f );
	return Box3f( -size/2.0f, size/2.0f );
}

void applyTextureParameters( IECoreGL::Texture *texture, const ImageGadget::TextureParameters &parameters )
{
	IECoreGL::Texture::ScopedBinding binding( *texture );
	glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, parameters.minFilter );
	glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, parameters.magFilter );
	glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_LOD_BIAS, parameters.lodBias );
	glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, parameters.wrapS );
	glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, parameters.wrapT );
}

struct TextureCacheKey
{
	std::string fileName;
	ImageGadget::TextureParameters parameters;
	bool operator==( const TextureCacheKey &other ) const
	{
		return
			fileName == other.fileName &&
			parameters.minFilter == other.parameters.minFilter &&
			parameters.magFilter == other.parameters.magFilter &&
			parameters.lodBias == other.parameters.lodBias &&
			parameters.wrapS == other.parameters.wrapS &&
			parameters.wrapT == other.parameters.wrapT
		;
	}
};

size_t hash_value( const TextureCacheKey &key )
{
	size_t result = 0;
	boost::hash_combine( result, key.fileName );
	boost::hash_combine( result, key.parameters.minFilter );
	boost::hash_combine( result, key.parameters.magFilter );
	boost::hash_combine( result, key.parameters.lodBias );
	boost::hash_combine( result, key.parameters.wrapS );
	boost::hash_combine( result, key.parameters.wrapT );
	return result;
}

using TextureCache = IECorePreview::LRUCache<TextureCacheKey, ConstTexturePtr>;

IECoreGL::ConstTexturePtr textureGetter( const TextureCacheKey &key, size_t &cost, const IECore::Canceller *canceller )
{
	const OIIO::ImageSpec config( OIIO::TypeDesc::UINT8 );
	const std::string fileName = resolvedFileName( key.fileName );
	OIIO::ImageBuf imageBuf( fileName, /* subimage = */ 0, /* miplevel = */ 0, /* imagecache = */ nullptr, &config );
	imageBuf = OIIO::ImageBufAlgo::flip( imageBuf );
	if( imageBuf.has_error() )
	{
		throw Exception( imageBuf.geterror() );
	}

	static const OIIO::ColorConfig colorConfig( "ocio://default" );
	static const OIIO::ColorProcessorHandle colorProcessor = colorConfig.createColorProcessor(
		"sRGB - Texture", "Linear Rec.709 (sRGB)"
	);

	imageBuf = OIIO::ImageBufAlgo::colorconvert( imageBuf, colorProcessor.get(), true );
	if( imageBuf.spec().format != OIIO::TypeDesc::UINT8 )
	{
		imageBuf = imageBuf.copy( OIIO::TypeDesc::UINT8 );
	}

	GLint pixelFormat;
	switch( imageBuf.nchannels() )
	{
		case 1 :
			pixelFormat = GL_RED;
			break;
		case 2 :
			pixelFormat = GL_LUMINANCE_ALPHA;
			break;
		case 3 :
			pixelFormat = GL_RGB;
			break;
		case 4 :
			pixelFormat = GL_RGBA;
			break;
		default :
			throw IECore::Exception( fmt::format( "Unsupported number of channels ({}) in \"{}\"", imageBuf.nchannels(), fileName ) );
	}

	GLuint id;
	glGenTextures( 1, &id );
	TexturePtr texture = new Texture( id );
	Texture::ScopedBinding binding( *texture );

	glPixelStorei( GL_UNPACK_ALIGNMENT, 1 );
	glTexImage2D( GL_TEXTURE_2D, /* level = */ 0, pixelFormat, imageBuf.spec().width, imageBuf.spec().height, /* border = */ 0, pixelFormat, GL_UNSIGNED_BYTE, imageBuf.localpixels() );
	glGenerateMipmap( GL_TEXTURE_2D );

	applyTextureParameters( texture.get(), key.parameters );

	cost = 0; // Never evict
	return texture;
}

const IECoreGL::Texture *loadTexture( IECore::ConstRunTimeTypedPtr &imageOrTextureOrFileName )
{
	if( const Texture *texture = runTimeCast<const Texture>( imageOrTextureOrFileName.get() ) )
	{
		return texture;
	}

	ConstTexturePtr texture;
	if( const StringData *filename = runTimeCast<const StringData>( imageOrTextureOrFileName.get() ) )
	{
		// Load texture from file
		texture = ImageGadget::loadTexture( filename->readable() );
	}
	else if( const ImagePrimitive *image = runTimeCast<const ImagePrimitive>( imageOrTextureOrFileName.get() ) )
	{
		// Convert image to texture
		ToGLTextureConverterPtr converter = new ToGLTextureConverter( image );
		if( auto converted = boost::static_pointer_cast<Texture>( converter->convert() ) )
		{
			applyTextureParameters( converted.get(), ImageGadget::TextureParameters() );
			texture = converted;
		}
	}

	imageOrTextureOrFileName = texture;

	return texture.get();
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// ImageGadget
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( ImageGadget );

ImageGadget::ImageGadget( const std::string &fileName )
	:	Gadget( defaultName<ImageGadget>() )
{

	// we'll load the actual texture later when we're sure a GL context exists,
	// but we need to find the bounding box now so that bound() will always be correct.

	using ImageBoundCache = IECorePreview::LRUCache<std::string, Box3f>;
	static ImageBoundCache g_imageBoundCache( boundGetter, 10000 );
	m_bound = g_imageBoundCache.get( fileName );

	m_imageOrTextureOrFileName = new StringData( fileName );
}

ImageGadget::ImageGadget( IECoreImage::ConstImagePrimitivePtr image )
	:	Gadget( defaultName<ImageGadget>() ), m_imageOrTextureOrFileName( image->copy() )
{
	const V2i pixelSize = image->getDisplayWindow().size() + V2i( 1 );
	const V3f size( pixelSize.x, pixelSize.y, 0.0f );
	m_bound = Box3f( -size/2.0f, size/2.0f );
}

ImageGadget::~ImageGadget()
{
}

IECoreGL::ConstTexturePtr ImageGadget::loadTexture( const std::string &fileName, const TextureParameters &parameters )
{
	static TextureCache g_textureCache( textureGetter, 10000 );
	return g_textureCache.get( { fileName, parameters } );
}

void ImageGadget::renderLayer( Layer layer, const Style *style, RenderReason reason ) const
{
	if( layer != Layer::Main )
	{
		return;
	}

	if( const Texture *texture = ::loadTexture( m_imageOrTextureOrFileName ) )
	{
		Box2f b( V2f( m_bound.min.x, m_bound.min.y ), V2f( m_bound.max.x, m_bound.max.y ) );
		style->renderImage( b, texture );
	}
}

unsigned ImageGadget::layerMask() const
{
	return (unsigned)Layer::Main;
}

Imath::Box3f ImageGadget::renderBound() const
{
	return bound();
}

Imath::Box3f ImageGadget::bound() const
{
	return m_bound;
}
