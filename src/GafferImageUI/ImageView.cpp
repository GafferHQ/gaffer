//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Context.h"

#include "GafferUI/Gadget.h"
#include "GafferUI/Style.h"
#include "GafferUI/StandardStyle.h"
#include "GafferImage/Format.h"

#include "GafferImageUI/ImageView.h"

#include "IECoreGL/ToGLTextureConverter.h"
#include "IECoreGL/TextureLoader.h"
#include "IECoreGL/Texture.h"
#include "IECore/BoxOps.h"

#include "boost/format.hpp"

using namespace IECoreGL;
using namespace IECore;
using namespace Imath;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferImage;
using namespace GafferImageUI;

namespace GafferImageUI
{

namespace Detail
{

class ImageViewGadget : public GafferUI::Gadget
{

	public :

		ImageViewGadget( IECore::ConstImagePrimitivePtr image )
			:	Gadget( staticTypeName() ),
				m_displayBound( image->bound() ),
				m_displayWindow( image->getDisplayWindow() ),
				m_dataWindow( image->getDataWindow() ),
				m_imageOrTexture( image->copy() )
		{
			Box2i dataWindow( image->getDataWindow() );
			V3f dataMin( dataWindow.min.x, dataWindow.min.y, 0.0 );
			V3f dataMax( 1.0f + dataWindow.max.x, 1.0f + dataWindow.max.y, 0.0 );
			V3f dataCenter = (dataMin + dataMax) / 2.0;
			V3f dispCenter = m_displayBound.size() / V3f( 2. );
			V3f dataOffset( dispCenter - dataCenter );
			
			m_dataBound = Box3f(
				V3f( dataMin.x - dispCenter.x, dataMin.y - dispCenter.y + dataOffset.y*2, 0. ),
				V3f( dataMax.x - dispCenter.x, dataMax.y - dispCenter.y + dataOffset.y*2, 0. )
			);
		}

		virtual ~ImageViewGadget()
		{
		};

		virtual Imath::Box3f bound() const
		{
			return m_displayBound;
		}
		
	protected :
	
		virtual void doRender( const Style *style ) const
		{
			
			if( m_imageOrTexture->isInstanceOf( IECore::ImagePrimitiveTypeId ) )
			{
				// convert image to texture
				ToGLTextureConverterPtr converter = new ToGLTextureConverter( staticPointerCast<const ImagePrimitive>( m_imageOrTexture ) );
				m_imageOrTexture = converter->convert();
			}
			
			// render texture
			if( m_imageOrTexture->isInstanceOf( IECoreGL::Texture::staticTypeId() ) )
			{
				// Transform them to Raster Space
				///\todo: The RasterScope class transforms Gadgets into a space where coordinate (0, 0) is in the top left corner.
				/// If we are rasterizing gadgets in 2D then we want (0, 0) to be in the bottom left corner. Perhaps we should write
				/// a new Scope class to transform to the appropriate 2D space or add a flag to the RasterScope class to flip the Y axis.
				/// Because of this issue we have to flip the Y axis in a few places such as when we scale the text.
				const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
				V2f dispRasterMin = viewportGadget->gadgetToRasterSpace( V3f( m_displayBound.min.x, m_displayBound.min.y, 0.), this );
				V2f dispRasterMax = viewportGadget->gadgetToRasterSpace( V3f( m_displayBound.max.x, m_displayBound.max.y, 0.), this );
				V2f dataRasterMin = viewportGadget->gadgetToRasterSpace( V3f( m_dataBound.min.x, m_dataBound.min.y, 0.), this );
				V2f dataRasterMax = viewportGadget->gadgetToRasterSpace( V3f( m_dataBound.max.x, m_dataBound.max.y, 0.), this );
				
				Box2f dispRasterBox( dispRasterMin, dispRasterMax );
				Box2f dataRasterBox( dataRasterMin, dataRasterMax );
				
				{
					ViewportGadget::RasterScope rasterScope( viewportGadget );
					
					// Draw the display window background.
					Color4f colour( 0.0f, .0f, .0f, 1.f );
					glColor( colour );
					style->renderSolidRectangle( dispRasterBox );
				}
				
				// Draw the image data.
				{
					// Get the bounds of the data window in Gadget space.
					Box2f b( V2f( m_dataBound.min.x, m_dataBound.min.y ), V2f( m_dataBound.max.x, m_dataBound.max.y ) );
					style->renderImage( b, (const Texture *)m_imageOrTexture.get(), GL_NEAREST );
				}
				
				ViewportGadget::RasterScope rasterScope( viewportGadget );
				
				// Mask the data window where it doesn't overlap the display window.
				if ( !IECore::boxContains( dataRasterBox, dispRasterBox ) &&  m_dataWindow != m_displayWindow )
				{
					const Box2f& c = dispRasterBox;
					Box2f b = dataRasterBox;
					
					///\todo We should query the raised colour of the current style here and use it but the current design won't allow us. For now it is hard-coded...
					glColor( Color4f( .29804, .29804, .29804, .90 ) );
					
					if ( b.min.x <= c.min.x )
					{
						Box2f l(b);
						l.max.x = c.min.x;
						b.min.x = c.min.x;
						style->renderSolidRectangle( l );
					}
					
					if ( b.max.x >= c.max.x )
					{
						Box2f r(b);
						r.min.x = c.max.x;
						b.max.x = c.max.x;
						style->renderSolidRectangle( r );
					}
					
					if ( b.max.y <= c.max.y )
					{
						Box2f l(b);
						l.min.y = c.max.y;
						b.max.y = c.max.y;
						style->renderSolidRectangle( l );
					}
					
					if ( b.min.y >= c.min.y )
					{
						Box2f r(b);
						r.max.y = c.min.y;
						b.min.y = c.min.y;
						style->renderSolidRectangle( r );
					}
				}
				
				// Draw the box around the display window.
				Color4f colour( .1f, .1f, .1f, 1.f );
				glColor( colour );
				style->renderRectangle( dispRasterBox );
				
				// Draw the box around the data window.
				colour = Color4f( .2f, .2f, .2f, 1.f );
				glColor( colour );
				style->renderRectangle( dataRasterBox );
				
				// Draw the data window text if it is different to the display window.
				if ( m_dataWindow != m_displayWindow && m_dataWindow.hasVolume() )
				{
					glTranslatef( dataRasterBox.max.x+5, dataRasterBox.max.y-5, 0.f ); 
					glScalef( 10.f, -10.f, 1.f );
					
					std::string dataWindowMaxStr = std::string( boost::str( boost::format( "(%d, %d)" ) % int(m_dataWindow.max.x+1) % int(m_dataWindow.max.y+1) ) );
					style->renderText( Style::LabelText, dataWindowMaxStr );
					
					glLoadIdentity();
					glTranslatef( dataRasterBox.min.x+5, dataRasterBox.min.y+10, 0.f ); 
					glScalef( 10.f, -10.f, 1.f );
					
					std::string dataWindowMinStr = std::string( boost::str( boost::format( "(%d, %d)" ) % int(m_dataWindow.min.x) % int(m_dataWindow.min.y) ) );
					style->renderText( Style::LabelText, dataWindowMinStr );
				}
				
				// Draw the display window text.
				glLoadIdentity();
				glTranslatef( dispRasterBox.min.x+5, dispRasterBox.min.y+10, 0.f );
				glScalef( 10.f, -10.f, 1.f );
				
				///\todo: How do we handle looking up the format here when we have a pixel aspect other than 1?
				/// Does the IECore::ImagePrimitive have a pixel aspect?
				GafferImage::Format f( m_displayWindow.size().x+1, m_displayWindow.size().y+1, 1. );
				std::string formatName( Format::formatName( f ) ) ;
				
				style->renderText( Style::LabelText, formatName );
			}
		}

	private :

		Imath::Box3f m_displayBound;
		Imath::Box3f m_dataBound;
		Imath::Box2i m_displayWindow;
		Imath::Box2i m_dataWindow;
		mutable IECore::ConstRunTimeTypedPtr m_imageOrTexture;

};

IE_CORE_DECLAREPTR( ImageViewGadget );

}; // namespace Detail

}; // namespace GafferImageUI

//////////////////////////////////////////////////////////////////////////
/// Implementation of ImageView
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( ImageView );

ImageView::ViewDescription<ImageView> ImageView::g_viewDescription( GafferImage::ImagePlug::staticTypeId() );

ImageView::ImageView( GafferImage::ImagePlugPtr inPlug )
	:	View( staticTypeName(), new GafferImage::ImagePlug() )
{
	View::inPlug<ImagePlug>()->setInput( inPlug );
}

ImageView::~ImageView()
{
}

void ImageView::update()
{
	IECore::ConstImagePrimitivePtr image = 0;
	{
		Context::Scope context( getContext() );
		image = preprocessedInPlug<ImagePlug>()->image();
	}

	if( image )
	{
		Detail::ImageViewGadgetPtr imageViewGadget = new Detail::ImageViewGadget( image );
		bool hadChild = viewportGadget()->getChild<Gadget>();
		viewportGadget()->setChild( imageViewGadget );
		if( !hadChild )
		{
			viewportGadget()->frame( imageViewGadget->bound() );
		}
	}
	else
	{
		viewportGadget()->setChild( 0 );	
	}
}

