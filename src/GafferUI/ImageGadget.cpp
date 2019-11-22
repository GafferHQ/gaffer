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

Box3f boundGetter( const std::string &fileName, size_t &cost )
{
	const char *s = getenv( "GAFFERUI_IMAGE_PATHS" );
	IECore::SearchPath sp( s ? s : "" );

	boost::filesystem::path path = sp.find( fileName );
	if( path.empty() )
	{
		throw Exception( "Could not find file '" + fileName + "'" );
	}

	ReaderPtr reader = Reader::create( path.string() );
	if( !reader )
	{
		throw Exception( "Could not create reader for '" + path.string() + "'" );
	}

	ImageReaderPtr imageReader = IECore::runTimeCast<ImageReader>( reader );
	if( !imageReader )
	{
		throw IECore::Exception( boost::str( boost::format( "File \"%s\" does not contain an image." ) % fileName ) );
	}

	cost = 1;
	V2i pixelSize = imageReader->displayWindow().size() + V2i( 1 );
	V3f size( pixelSize.x, pixelSize.y, 0.0f );
	return Box3f( -size/2.0f, size/2.0f );
}

void applyTextureParameters( IECoreGL::Texture *texture )
{
	IECoreGL::Texture::ScopedBinding binding( *texture );
	glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR );
	glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR );
	glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_LOD_BIAS, -1.0 );
	glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER );
	glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER );
}

const IECoreGL::Texture *loadTexture( IECore::ConstRunTimeTypedPtr &imageOrTextureOrFileName )
{
	if( const Texture *texture = runTimeCast<const Texture>( imageOrTextureOrFileName.get() ) )
	{
		return texture;
	}

	TexturePtr texture;
	if( const StringData *filename = runTimeCast<const StringData>( imageOrTextureOrFileName.get() ) )
	{
		// Load texture from file
		texture = ImageGadget::textureLoader()->load( filename->readable() );
	}
	else if( const ImagePrimitive *image = runTimeCast<const ImagePrimitive>( imageOrTextureOrFileName.get() ) )
	{
		// Convert image to texture
		ToGLTextureConverterPtr converter = new ToGLTextureConverter( image );
		texture =  boost::static_pointer_cast<Texture>( converter->convert() );
	}

	if( texture )
	{
		applyTextureParameters( texture.get() );
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

	typedef IECorePreview::LRUCache<std::string, Box3f> ImageBoundCache;
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

IECoreGL::TextureLoader *ImageGadget::textureLoader()
{
	static TextureLoaderPtr loader = nullptr;
	if( !loader )
	{
		const char *s = getenv( "GAFFERUI_IMAGE_PATHS" );
		IECore::SearchPath sp( s ? s : "" );
		loader = new TextureLoader( sp );
	}
	return loader.get();
}

IECoreGL::ConstTexturePtr ImageGadget::loadTexture( const std::string &fileName )
{
	TexturePtr texture = textureLoader()->load( fileName );
	if( texture )
	{
		applyTextureParameters( texture.get() );
	}
	return texture;
}

void ImageGadget::doRenderLayer( Layer layer, const Style *style ) const
{
	Gadget::doRenderLayer( layer, style );
	if( layer != Layer::Main )
	{
		return;
	}

	if( const Texture *texture = ::loadTexture( m_imageOrTextureOrFileName ) )
	{
		Box2f b( V2f( m_bound.min.x, m_bound.min.y ), V2f( m_bound.max.x, m_bound.max.y ) );
		style->renderImage( b, texture );
	}

	Gadget::doRenderLayer( layer, style );
}

Imath::Box3f ImageGadget::bound() const
{
	return m_bound;
}
