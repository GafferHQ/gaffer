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

#include "IECore/LRUCache.h"
#include "IECore/Exception.h"
#include "IECore/SearchPath.h"
#include "IECore/ImageReader.h"

#include "IECoreGL/ToGLTextureConverter.h"
#include "IECoreGL/TextureLoader.h"
#include "IECoreGL/Texture.h"

#include "GafferUI/ImageGadget.h"
#include "GafferUI/Style.h"

using namespace Imath;
using namespace IECore;
using namespace IECoreGL;
using namespace GafferUI;

IE_CORE_DEFINERUNTIMETYPED( ImageGadget );

static Box3f boundGetter( const std::string &fileName, size_t &cost )
{
	const char *s = getenv( "GAFFERUI_IMAGE_PATHS" );
	IECore::SearchPath sp( s ? s : "", ":" );

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

ImageGadget::ImageGadget( const std::string &fileName )
	:	Gadget( defaultName<ImageGadget>() )
{

	// we'll load the actual texture later when we're sure a GL context exists,
	// but we need to find the bounding box now so that bound() will always be correct.

	typedef LRUCache<std::string, Box3f> ImageBoundCache;
	static ImageBoundCache g_imageBoundCache( boundGetter, 10000 );
	m_bound = g_imageBoundCache.get( fileName );

	m_imageOrTextureOrFileName = new StringData( fileName );
}

ImageGadget::ImageGadget( IECore::ConstImagePrimitivePtr image )
	:	Gadget( defaultName<ImageGadget>() ), m_bound( image->bound() ), m_imageOrTextureOrFileName( image->copy() )
{
}

ImageGadget::~ImageGadget()
{
}

void ImageGadget::doRender( const Style *style ) const
{

	if( const StringData *filename = runTimeCast<const StringData>( m_imageOrTextureOrFileName.get() ) )
	{
		// load texture from file
		static TextureLoaderPtr g_textureLoader = 0;
		if( !g_textureLoader )
		{
			const char *s = getenv( "GAFFERUI_IMAGE_PATHS" );
			IECore::SearchPath sp( s ? s : "", ":" );
			g_textureLoader = new TextureLoader( sp );
		}

		m_imageOrTextureOrFileName = g_textureLoader->load( filename->readable() );
	}
	else if( const ImagePrimitive *image = runTimeCast<const ImagePrimitive>( m_imageOrTextureOrFileName.get() ) )
	{
		// convert image to texture
		ToGLTextureConverterPtr converter = new ToGLTextureConverter( image );
		m_imageOrTextureOrFileName = converter->convert();
	}

	// render texture
	if( const Texture *texture = runTimeCast<const Texture>( m_imageOrTextureOrFileName.get() ) )
	{
		Box2f b( V2f( m_bound.min.x, m_bound.min.y ), V2f( m_bound.max.x, m_bound.max.y ) );
		style->renderImage( b, texture );
	}

}

Imath::Box3f ImageGadget::bound() const
{
	return m_bound;
}
