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

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"
#include "boost/format.hpp"

#include "Gaffer/Context.h"

#include "GafferUI/Gadget.h"
#include "GafferUI/Style.h"
#include "GafferUI/StandardStyle.h"
#include "GafferImage/Format.h"

#include "GafferImageUI/ImageView.h"

#include "IECoreGL/ToGLTextureConverter.h"
#include "IECoreGL/TextureLoader.h"
#include "IECoreGL/Texture.h"
#include "IECore/FastFloat.h"
#include "IECore/BoxOps.h"
#include "IECore/BoxAlgo.h"

using namespace boost;
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
			:	Gadget( defaultName<ImageViewGadget>() ),
				m_displayBound( image->bound() ),
				m_displayWindow( image->getDisplayWindow() ),
				m_dataWindow( image->getDataWindow() ),
				m_image( image->copy() ),
				m_texture( 0 ),
				m_sampleColour( Color4f( 0.f, 0.f, 0.f, 0.f ) ),
				m_dragSelecting( false )
		{
			Box2i dataWindow( image->getDataWindow() );
			V3f dataMin( dataWindow.min.x, dataWindow.min.y, 0.0 );
			V3f dataMax( dataWindow.max.x + 1.f, dataWindow.max.y + 1.f, 0.0 );
			V3f dataCenter = (dataMin + dataMax) / 2.0;
			V3f dispCenter = ( m_displayBound.size() ) / V3f( 2. );
			V3f dataOffset( dispCenter - dataCenter );
			
			m_dataBound = Box3f(
				V3f( dataMin.x - dispCenter.x, dataMin.y - dispCenter.y + dataOffset.y * 2, 0. ),
				V3f( dataMax.x - dispCenter.x, dataMax.y - dispCenter.y + dataOffset.y * 2, 0. )
			);

			buttonPressSignal().connect( boost::bind( &ImageViewGadget::buttonPress, this, ::_1,  ::_2 ) );
			dragBeginSignal().connect( boost::bind( &ImageViewGadget::dragBegin, this, ::_1, ::_2 ) );
			dragEnterSignal().connect( boost::bind( &ImageViewGadget::dragEnter, this, ::_1, ::_2 ) );
			dragMoveSignal().connect( boost::bind( &ImageViewGadget::dragMove, this, ::_1, ::_2 ) );
			dragEndSignal().connect( boost::bind( &ImageViewGadget::dragEnd, this, ::_1, ::_2 ) );
			mouseMoveSignal().connect( boost::bind( &ImageViewGadget::mouseMove, this, ::_1, ::_2 ) );
		}

		virtual ~ImageViewGadget()
		{
		};

		virtual Imath::Box3f bound() const
		{
			return m_displayBound;
		}
		
	protected :
		
		/// Returns the data window of the image in raster space.
		inline Box2f dataRasterBox() const
		{
			const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
			return Box2f(
				viewportGadget->gadgetToRasterSpace( V3f( m_dataBound.min.x, m_dataBound.min.y, 0.), this ),
				viewportGadget->gadgetToRasterSpace( V3f( m_dataBound.max.x, m_dataBound.max.y, 0.), this )
			);
		}
		
		/// Returns the display window of the image in raster space.
		inline Box2f displayRasterBox() const
		{
			const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
			return Box2f(
				viewportGadget->gadgetToRasterSpace( V3f( m_displayBound.min.x, m_displayBound.min.y, 0.), this ),
				viewportGadget->gadgetToRasterSpace( V3f( m_displayBound.max.x, m_displayBound.max.y, 0.), this )
			);
		}
	
		/// Transforms and returns a point from raster space to display space.
		V2f rasterToDisplaySpace( const V2f &point ) const
		{
			Box2f dispRasterBox( displayRasterBox() );
			V2f wh( dispRasterBox.max - dispRasterBox.min + V2f(1.f) );
			V2f t = ( point - dispRasterBox.min ) / wh;
			return V2f(
				float( m_displayWindow.min.x ) + t.x * ( m_displayWindow.size().x + 1.f ),
				float( m_displayWindow.min.y ) + t.y * ( m_displayWindow.size().y + 1.f )
			);
		}
	
		Box2f rasterToDisplaySpace( const Box2f &box ) const
		{
			return Box2f( rasterToDisplaySpace( box.min ), rasterToDisplaySpace( box.max ) );
		}
		
		/// Transforms and returns a point from raster to display space.
		V2f gadgetToDisplaySpace( const V3f &point ) const
		{
			const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
			V2i pointRasterPos( viewportGadget->gadgetToRasterSpace( point, this ) );
			return rasterToDisplaySpace( V2f( floorf( pointRasterPos.x ), floorf( pointRasterPos.y ) ) );
		}
		
		Box2f gadgetToDisplaySpace( const Box3f &box ) const
		{
			return Box2f( gadgetToDisplaySpace( box.min ), gadgetToDisplaySpace( box.max ) );
		}

		/// Samples a colour from the image.		
		Color4f sampleColour( const V2f &point ) const
		{
			V2i samplePos(
				fastFloatRound( point.x - .5 ) - m_dataWindow.min.x,
				m_dataWindow.size().y - ( fastFloatRound( point.y - .5 ) - m_dataWindow.min.y )
			);
				
			if ( samplePos.x < 0 || samplePos.y < 0 || samplePos.x > m_dataWindow.size().x || samplePos.y > m_dataWindow.size().y )
			{
				return Color4f( 0.f, 0.f, 0.f, 0.f );
			}
			
			Color4f colour;
			std::vector<std::string> channelNames;
			m_image->channelNames( channelNames );
			std::string channel[4] = { "R", "G", "B", "A" };
			for ( int c = 0; c < 4; ++c )
			{
				if ( std::find( channelNames.begin(), channelNames.end(), channel[c] ) != channelNames.end() )
				{
					const std::vector<float> &channelData = m_image->getChannel<float>( channel[c] )->readable();
					colour[c] = channelData[ samplePos.y * ( m_dataWindow.size().x + 1 ) + samplePos.x ];
				}
				else
				{
					colour[c] = 0.f;
				}
			}

			return colour;
		};

		bool buttonPress( GadgetPtr gadget, const ButtonEvent &event )
		{
			if( event.buttons != ButtonEvent::Left )
			{
				return false;
			}
			
			m_mousePos = gadgetToDisplaySpace( V3f( event.line.p0.x, event.line.p0.y, 0 ) );
			m_dragColour = m_sampleColour = sampleColour( m_mousePos);
			renderRequestSignal()( this );
			
			return true;
		}
		
		bool mouseMove( GadgetPtr gadget, const ButtonEvent &event )
		{
			m_mousePos = gadgetToDisplaySpace( V3f( event.line.p0.x, event.line.p0.y, 0 ) );
			m_dragColour = sampleColour( m_mousePos );
			renderRequestSignal()( this );
			return true;
		}

		bool dragEnter( GadgetPtr gadget, const DragDropEvent &event )
		{
			if ( m_dragSelecting )
			{
				return true;
			}
			return event.sourceGadget == this && event.data == this;
		}

		bool dragMove( GadgetPtr gadget, const DragDropEvent &event )
		{
			m_lastDragPosition = event.line.p1;
			
			// Update the selection box.
			if ( m_dragSelecting )
			{				
				Box3f selectionBox;
				selectionBox.extendBy( m_dragStartPosition );
				selectionBox.extendBy( m_lastDragPosition );
				setSelectionArea( selectionBox );
			}

			m_mousePos = gadgetToDisplaySpace( V3f( event.line.p0.x, event.line.p0.y, 0 ) );
			m_dragColour = sampleColour( m_mousePos );
			renderRequestSignal()( this );
			return true;
		}

		bool dragEnd( GadgetPtr gadget, const DragDropEvent &event )
		{
			if( !m_dragSelecting )
			{
				return false;
			}
			m_dragSelecting = false;

			renderRequestSignal()( this );
			return true;
		}

		IECore::RunTimeTypedPtr dragBegin( GadgetPtr gadget, const DragDropEvent &event )
		{
			if ( event.modifiers & ModifiableEvent::Shift )
			{
				m_dragSelecting = true;
				m_dragStartPosition = m_lastDragPosition = event.line.p0;
				return this;
			}

			return new Color4fData( m_sampleColour );
		}
	
		void setSelectionArea( Box3f selectionBox )
		{
			// Get the bounds of the selection.
			selectionBox = boxIntersection( selectionBox, m_displayBound );

			if ( selectionBox.size().x < 0. )
			{
				selectionBox.max.x = selectionBox.min.x;
			}

			if ( selectionBox.size().y < 0. )
			{
				selectionBox.max.y = selectionBox.min.y;
			}

			selectionBox.min.x = floorf( selectionBox.min.x );
			selectionBox.min.y = floorf( selectionBox.min.y );
			selectionBox.max.x = ceilf( selectionBox.max.x );
			selectionBox.max.y = ceilf( selectionBox.max.y );
			
			// Save the box in gadget space.
			m_sampleWindow = selectionBox;
		}

		void drawWindow( Box2f &rasterWindow, const Style *style ) const
		{
			V2f minPt( rasterToDisplaySpace( rasterWindow.min ) );
			V2f maxPt( rasterToDisplaySpace( rasterWindow.max ) );
				
			std::string rasterWindowMinStr = std::string( boost::str( boost::format( "(%d, %d)" ) % fastFloatRound( minPt.x ) % fastFloatRound( minPt.y ) ) );
			std::string rasterWindowMaxStr = std::string( boost::str( boost::format( "(%d, %d)" ) % fastFloatRound( maxPt.x ) % fastFloatRound( maxPt.y ) ) );
				
			// Draw the box around the data window.
			style->renderRectangle( rasterWindow );
			
			glTranslatef( rasterWindow.max.x+5, rasterWindow.max.y-5, 0.f ); 
			glScalef( 10.f, -10.f, 1.f );
			style->renderText( Style::LabelText, rasterWindowMaxStr );
				
			glLoadIdentity();
			glTranslatef( rasterWindow.min.x+5, rasterWindow.min.y+10, 0.f ); 
			glScalef( 10.f, -10.f, 1.f );
			
			style->renderText( Style::LabelText, rasterWindowMinStr );
			glLoadIdentity();
		}

		virtual void doRender( const Style *style ) const
		{

			if( !m_texture )
			{
				// convert image to texture
				ToGLTextureConverterPtr converter = new ToGLTextureConverter( staticPointerCast<const ImagePrimitive>( m_image ) );
				m_texture = IECore::runTimeCast<IECoreGL::Texture>( converter->convert() );

				{
					Texture::ScopedBinding scope( *m_texture );
					glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR );
					glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST );
				}
			}

			// Transform them to Raster Space
			///\todo: The RasterScope class transforms Gadgets into a space where coordinate (0, 0) is in the top left corner.
			/// If we are rasterizing gadgets in 2D then we want (0, 0) to be in the bottom left corner. Perhaps we should write
			/// a new Scope class to transform to the appropriate 2D space or add a flag to the RasterScope class to flip the Y axis.
			/// Because of this issue we have to flip the Y axis in a few places such as when we scale the text.
			const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
			Box2f dispRasterBox( displayRasterBox() );
			Box2f dataRasterBox( ImageViewGadget::dataRasterBox() );

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
				style->renderImage( b, (const Texture *)m_texture.get() );
			}

			ViewportGadget::RasterScope rasterScope( viewportGadget );

			// Mask the data window where it doesn't overlap the display window.
			if ( m_dataWindow != m_displayWindow )
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
			glLoadIdentity();

			// Draw the display window text.
			glTranslatef( dispRasterBox.min.x+5, dispRasterBox.min.y+10, 0.f );
			glScalef( 10.f, -10.f, 1.f );

			///\todo: How do we handle looking up the format here when we have a pixel aspect other than 1?
			/// Does the IECore::ImagePrimitive have a pixel aspect?
			GafferImage::Format f( m_displayWindow.size().x+1, m_displayWindow.size().y+1, 1. );
			std::string formatName( Format::formatName( f ) ) ;

			style->renderText( Style::LabelText, formatName );
			glLoadIdentity();

			// Draw the data window if it is different to the display window.
			if ( m_dataWindow != m_displayWindow && m_dataWindow.hasVolume() )
			{
				colour = Color4f( .2f, .2f, .2f, 1.f );
				glColor( colour );
				drawWindow( dataRasterBox, style );
			}

			/// Draw the selection window.
			if( m_dragSelecting )
			{
				Box2f rasterBox(
					V2i( viewportGadget->gadgetToRasterSpace( m_sampleWindow.min, this ) ),
					V2i( viewportGadget->gadgetToRasterSpace( m_sampleWindow.max, this ) )
				);

				colour = Color4f( 1.f, 0.f, 1.f, 1.f );
				glColor( colour );
				drawWindow( rasterBox, style );
			}

			/// Draw the colour info bar.	
			colour = Color4f( 0.f, 0.f, 0.f, 1.f );
			glColor( colour );
			V2i viewportWH( viewportGadget->getViewport() );

			Box2f infoBox(
				V2f( 0.f, viewportWH.y-20 ), 
				viewportWH
			);
			style->renderSolidRectangle( infoBox );

			// Draw the mouse's XY position.
			glTranslatef( infoBox.min.x+10, infoBox.min.y+14, 0.f );
			glScalef( 10.f, -10.f, 1.f );
			std::string mousePosStr = std::string( boost::str( boost::format( "XY: %d, %d" ) % fastFloatRound( m_mousePos.x - .5 ) % fastFloatRound( m_mousePos.y - .5 ) ) );
			style->renderText( Style::LabelText, mousePosStr );
			glLoadIdentity();
			
			glTranslatef( infoBox.min.x+130, infoBox.min.y+14, 0.f );
			glScalef( 10.f, -10.f, 1.f );
			std::string colourStr = std::string( boost::str( boost::format( "RGBA: %.4f, %.4f, %.4f, %.4f" ) % m_dragColour[0] % m_dragColour[1] % m_dragColour[2] % m_dragColour[3] ) );
			style->renderText( Style::LabelText, colourStr );
			glLoadIdentity();
		}

	private :
		
		Imath::Box3f m_displayBound;
		Imath::Box3f m_dataBound;
		Imath::Box2i m_displayWindow;
		Imath::Box2i m_dataWindow;
		ConstImagePrimitivePtr m_image;
		mutable ConstTexturePtr m_texture;

		Imath::V2f m_mousePos;
		Imath::V3f m_dragStartPosition;
		Imath::V3f m_lastDragPosition;
		Color4f m_sampleColour;
		Color4f m_dragColour;
		bool m_dragSelecting;
		
		Imath::Box3f m_sampleWindow;
};

IE_CORE_DECLAREPTR( ImageViewGadget );

}; // namespace Detail

}; // namespace GafferImageUI

//////////////////////////////////////////////////////////////////////////
/// Implementation of ImageView
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( ImageView );

ImageView::ViewDescription<ImageView> ImageView::g_viewDescription( GafferImage::ImagePlug::staticTypeId() );

ImageView::ImageView( const std::string &name )
	:	View( name, new GafferImage::ImagePlug() )
{
}

ImageView::ImageView( const std::string &name, Gaffer::PlugPtr input )
	:	View( name, input )
{
}

ImageView::~ImageView()
{
}

void ImageView::update()
{
	IECore::ConstImagePrimitivePtr image = 0;
	{
		Context::Scope context( getContext() );
		ImagePlug *imagePlug = preprocessedInPlug<ImagePlug>();
		if( !imagePlug )
		{
			throw IECore::Exception( "ImageView::preprocessedInPlug() is not an ImagePlug" );
		}
		image = imagePlug->image();
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

