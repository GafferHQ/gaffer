//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Image Engine Design Inc. All rights reserved.
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

#include "GafferImageUI/ColorInspectorTool.h"

#include "GafferImageUI/ImageGadget.h"

#include "GafferUI/Pointer.h"
#include "GafferUI/Style.h"

#include "GafferImage/ImagePlug.h"
#include "GafferImage/Sampler.h"

#include "Gaffer/Metadata.h"

#include "IECore/NullObject.h"

#include "boost/bind/bind.hpp"

using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferImage;
using namespace GafferImageUI;

namespace
{

IECore::InternedString g_hoveredKey( "__hovered" );

void renderLine2D( const Style *style, V2f a, V2f b, float width, const Color4f &col )
{
	style->renderLine( LineSegment3f( V3f( a.x, a.y, 0.0 ), V3f( b.x, b.y, 0 ) ), width, &col );
}

// TODO - these are some terrible ways of drawing circles, but I just wanted something quick that works. Add
// something better somewhere central
void renderCircle2D( const Style *style, V2f center, V2f radius, float width, const Color4f &col )
{
	int segments = 16;
	V2f prevAngle( 1, 0 );
	for( int i = 0; i < segments; i++ )
	{
		V2f angle( cos( 2.0f * M_PI * ( i + 1.0f ) / segments ), sin( 2.0f * M_PI * ( i + 1.0f ) / segments ) );
		renderLine2D( style, center + prevAngle * radius, center + angle * radius, width, col );
		prevAngle = angle;
	}
}

void renderFilledCircle2D( const Style *style, V2f center, V2f radius, const Color4f &col )
{
	// TODO : Terrible hack, rendering a dummy rectangle which will put the style's shader in a state where
	// it will allow us to draw a polygon
	style->renderRectangle( Box2f( center, center ) );
	int segments = 16;
	IECoreGL::glColor( col );
	glBegin( GL_POLYGON );

		for( int i = 0; i < segments; i++ )
		{
			V2f angle( cos( 2.0f * M_PI * ( i + 1.0f ) / segments ), sin( 2.0f * M_PI * ( i + 1.0f ) / segments ) );
			glVertex2f( center.x + angle.x * radius.x, center.y + angle.y * radius.y );
		}

	glEnd();
}

float pixelAspectFromImageGadget( const ImageGadget *imageGadget )
{
	// We want to grab the cached version of imageGadget->format(), but it's not exposed publicly, so we
	// get it from pixelAt.
	// In the future, it would be better if format() was public and we didn't have to worry about it
	// throwing.
	try
	{
		return 1.0f / imageGadget->pixelAt( LineSegment3f( V3f( 1, 0, 0 ), V3f( 1, 0, 1 ) ) ).x;
	}
	catch( ... )
	{
		// Not worried about rendering correctly for images which can't be evaluated properly
		return 1.0f;
	}
}

class Box2iGadget : public GafferUI::Gadget
{

	public :

		Box2iGadget( Box2iPlugPtr plug, std::string id )
			: Gadget(), m_plug( plug ), m_id( id ), m_editable( true ), m_handleSize( 10 ), m_hover( 0 ), m_deletePressed( false )
		{
			enterSignal().connect( boost::bind( &Box2iGadget::enter, this, ::_2 ) );
			mouseMoveSignal().connect( boost::bind( &Box2iGadget::mouseMove, this, ::_2 ) );
			buttonPressSignal().connect( boost::bind( &Box2iGadget::buttonPress, this, ::_2 ) );
			dragBeginSignal().connect( boost::bind( &Box2iGadget::dragBegin, this, ::_1, ::_2 ) );
			dragEnterSignal().connect( boost::bind( &Box2iGadget::dragEnter, this, ::_1, ::_2 ) );
			dragMoveSignal().connect( boost::bind( &Box2iGadget::dragMove, this, ::_2 ) );
			dragEndSignal().connect( boost::bind( &Box2iGadget::dragEnd, this, ::_2 ) );
			buttonReleaseSignal().connect( boost::bind( &Box2iGadget::buttonRelease, this, ::_2 ) );
			leaveSignal().connect( boost::bind( &Box2iGadget::leave, this ) );

			plug->node()->plugDirtiedSignal().connect( boost::bind( &Box2iGadget::plugDirtied, this, ::_1 ) );
		}

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( Box2iGadget, Box2iGadgetTypeId, GafferUI::Gadget );

		Imath::Box3f bound() const override
		{
			Box2i rect = m_plug->getValue();
			return Box3f(
				V3f( rect.min.x, rect.min.y, 0 ),
				V3f( rect.max.x, rect.max.y, 0 )
			);
		}

		const Box2iPlug *getPlug() const
		{
			return m_plug.get();
		}

		using DeleteClickedSignal = Signals::Signal<void ( Plug * )>;
		DeleteClickedSignal &deleteClickedSignal()
		{
			return m_deleteClickedSignal;
		}

	protected :

		void renderLayer( Layer layer, const Style *style, RenderReason reason ) const override
		{
			if( layer != Layer::Front )
			{
				return;
			}

			Box2i rect = m_plug->getValue();
			if( rect.isEmpty() )
			{
				return;
			}

			float pixelAspect = 1.0f;
			V2f screenScale = screenToImageScale( &pixelAspect );

			const V2f threshold( screenScale * m_handleSize );

			glPushMatrix();
			glScalef( pixelAspect, 1, 1 );

			V2f crossHairSize(
				std::min ( threshold.x, rect.size().x * 0.5f ),
				std::min ( threshold.y, rect.size().y * 0.5f )
			);

			V2f rectCenter( 0.5f * ( V2f( rect.min ) + V2f( rect.max ) ) );
			V2f deleteButtonCenter( rect.max.x + threshold.x, rect.max.y + threshold.y );
			V2f deleteButtonSize( threshold.x * 0.5, threshold.y * 0.5 );
			glPushAttrib( GL_CURRENT_BIT | GL_LINE_BIT | GL_ENABLE_BIT );

				if( isSelectionRender( reason ) )
				{
					if( m_editable )
					{
						V2f upperLeft( rect.min.x, rect.max.y );
						V2f lowerRight( rect.max.x, rect.min.y );
						// Center handle
						style->renderSolidRectangle( Box2f( rectCenter - threshold, rectCenter + threshold ) );
						// Vertical bars
						style->renderSolidRectangle( Box2f( rect.min - threshold, upperLeft + threshold ) );
						style->renderSolidRectangle( Box2f( lowerRight - threshold, rect.max + threshold ) );
						// Horizontal bars
						style->renderSolidRectangle( Box2f( rect.min - threshold, lowerRight + threshold ) );
						style->renderSolidRectangle( Box2f( upperLeft - threshold, rect.max + threshold ) );
						// Delete button
						style->renderSolidRectangle( Box2f( V2f( deleteButtonCenter.x, deleteButtonCenter.y ) - 0.5f * threshold, V2f( deleteButtonCenter.x, deleteButtonCenter.y ) + 0.5f * threshold ) );
					}
				}
				else
				{
					glEnable( GL_LINE_SMOOTH );
					glLineWidth( 2.0f );
					glColor4f( 0.0f, 0.0f, 0.0f, 1.0f );
					style->renderRectangle( Box2f( V2f(rect.min) - 1.0f * screenScale, V2f(rect.max) + 1.0f * screenScale ) );
					glLineWidth( 1.0f );
					glColor4f( 1.0f, 1.0f, 1.0f, 1.0f );
					Color4f foreground( 0.8f, 0.8f, 0.8f, 1.0f );
					style->renderRectangle( Box2f( rect.min, rect.max ) );
					renderLine2D( style, rectCenter - crossHairSize * V2f( 1, 0 ), rectCenter + crossHairSize * V2f( 1, 0 ), 1 * screenScale.x, foreground );
					renderLine2D( style, rectCenter - crossHairSize * V2f( 0, 1 ), rectCenter + crossHairSize * V2f( 0, 1 ), 1 * screenScale.x, foreground );

					if( m_hover )
					{
						renderFilledCircle2D( style, deleteButtonCenter, deleteButtonSize * 1.4f, Color4f( 0.4, 0.4, 0.4, 1.0 ) );
						Color4f buttonCol( 0.0f, 0.0f, 0.0f, 1.0f );
						if( m_hover == 2 )
						{
							buttonCol = Color4f( 1.0f, 1.0f, 1.0f, 1.0f );
						}
						renderLine2D( style, deleteButtonCenter - deleteButtonSize, deleteButtonCenter + deleteButtonSize, 4.0 * screenScale.x, buttonCol );
						renderLine2D( style, deleteButtonCenter + deleteButtonSize * V2f( 1, -1 ), deleteButtonCenter + deleteButtonSize * V2f( -1, 1 ), 4.0 * screenScale.x, buttonCol );
					}

					float textScale = 10;
					float textLength = style->textBound( Style::LabelText, m_id ).size().x;
					glColor4f( 1.0f, 1.0f, 1.0f, 1.0f );
					glPushMatrix();
						glTranslatef( rect.min.x - ( textScale * textLength + 5 ) * screenScale.x, rect.max.y + 5 * screenScale.y, 0.0f );
						glScalef( textScale * screenScale.x, textScale * screenScale.y, 1 );
						style->renderText( Style::LabelText, m_id );
					glPopMatrix();
				}

			glPopAttrib();

			glPopMatrix();
		}

		unsigned layerMask() const override
		{
			return (unsigned)Layer::Front;
		}

		Imath::Box3f renderBound() const override
		{
			// We draw handles outside the box, so we need to extend outside box - since we
			// don't usually have many Box2iGadgets at once, we return infinite rather than
			// finessing the overrender
			Box3f b;
			b.makeInfinite();
			return b;
		}

	private :

		void plugDirtied( Plug *plug )
		{
			if( plug == m_plug )
			{
				dirty( DirtyType::Bound );
			}
		}

		bool enter( const ButtonEvent &event )
		{
			Metadata::registerValue( m_plug.get(), g_hoveredKey, new IECore::BoolData( true ), false );
			return true;
		}

		bool mouseMove( const ButtonEvent &event )
		{
			// Request render in case the hover state has changed
			dirty( DirtyType::Render );

			const V2f p = eventPosition( event );

			if( onDeleteButton( p ) )
			{
				Pointer::setCurrent( "" );
				m_hover = 2;
				return false;
			}

			m_hover = 1;

			const V2i dir = dragDirection( p );
			if( dir.x && dir.y )
			{
				Pointer::setCurrent( ( dir.x * dir.y < 0 ) ? "moveDiagonallyDown" : "moveDiagonallyUp" );
			}
			else if( dir.x )
			{
				Pointer::setCurrent( "moveHorizontally" );
			}
			else if( dir.y )
			{
				Pointer::setCurrent( "moveVertically" );
			}
			else
			{
				Pointer::setCurrent( "move" );
			}

			return false;
		}

		bool buttonPress( const GafferUI::ButtonEvent &event )
		{
			if( event.buttons != ButtonEvent::Left )
			{
				return false;
			}

			// Anything within the bound is draggable except the delete button
			const V2f p = eventPosition( event );
			if( onDeleteButton( p ) )
			{
				m_deletePressed = true;
				return true;
			}

			return true;
		}

		IECore::RunTimeTypedPtr dragBegin( GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
		{
			if( m_deletePressed )
			{
				return nullptr;
			}
			m_dragStart = eventPosition( event );
			m_dragDirection = dragDirection( m_dragStart );
			m_dragStartRectangle = m_plug->getValue();
			return IECore::NullObject::defaultNullObject();
		}

		bool dragEnter( const GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
		{
			if( event.sourceGadget != this )
			{
				return false;
			}

			updateDragRectangle( event );
			return true;
		}

		bool dragMove( const GafferUI::DragDropEvent &event )
		{
			updateDragRectangle( event );
			return true;
		}

		bool dragEnd( const GafferUI::DragDropEvent &event )
		{
			updateDragRectangle( event );
			return true;
		}


		void updateDragRectangle( const GafferUI::DragDropEvent &event )
		{
			const V2f p = eventPosition( event );
			Box2i b = m_dragStartRectangle;

			if( m_dragDirection == V2i( 0, 0 ) )
			{
				const V2f offset = p - m_dragStart;
				const V2i intOffset = V2i( round( offset.x ), round( offset.y ) );
				b.min += intOffset;
				b.max += intOffset;
			}
			else
			{
				if( m_dragDirection.x == -1 )
				{
					b.min.x = round( p.x );
				}
				else if( m_dragDirection.x == 1 )
				{
					b.max.x = round( p.x );
				}

				if( m_dragDirection.y == -1 )
				{
					b.min.y = round( p.y );
				}
				else if( m_dragDirection.y == 1 )
				{
					b.max.y = round( p.y );
				}
			}

			// fix max < min issues
			Box2i c;
			c.extendBy( b.min );
			c.extendBy( b.max );

			m_plug->setValue( c );
		}

		bool buttonRelease( const GafferUI::ButtonEvent &event )
		{
			const V2f p = eventPosition( event );
			if( m_deletePressed && onDeleteButton( p ) )
			{
				m_deleteClickedSignal( m_plug.get() );
			}
			m_deletePressed = false;

			return true;
		}

		void leave()
		{
			Pointer::setCurrent( "" );
			m_hover = 0;

			Metadata::registerValue( m_plug.get(), g_hoveredKey, new IECore::BoolData( false ), false );
		}

		// Returns the scale from screen raster pixels to Gaffer image pixels. This includes both
		// the scaling applied by ViewportGadget, and the pixelAspect scaling which isn't applied
		// automatically ( it is optionally returned separately so we can apply it manually in
		// renderLayer )
		V2f screenToImageScale( float *pixelAspectOut = nullptr ) const
		{
			const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
			const V2f viewportPlanarScale(
				viewportGadget->getCamera()->getAperture()[0] / viewportGadget->getViewport()[0],
				viewportGadget->getCamera()->getAperture()[1] / viewportGadget->getViewport()[1]
			);

			const ImageGadget *imageGadget = static_cast<const ImageGadget *>( viewportGadget->getPrimaryChild() );

			float pixelAspect = pixelAspectFromImageGadget( imageGadget );

			if( pixelAspectOut )
			{
				*pixelAspectOut = pixelAspect;
			}

			return viewportPlanarScale * V2f( 1.0f / pixelAspect, 1.0f );
		}

		bool onDeleteButton( const V2f &p ) const
		{
			// Any positions that are part of the gadget, but not part of an extended bound, are
			// on the delete button
			Box2i rect = m_plug->getValue();
			const V2f screenScale = screenToImageScale();
			const V2f threshold( screenScale * m_handleSize );
			return
				p.x > rect.max.x + 0.5 * threshold.x - screenScale.x &&
				p.y > rect.max.y + 0.5 * threshold.y - screenScale.y;
		}

		V2i dragDirection( const V2f &p ) const
		{

			Box2i rect = m_plug->getValue();
			V2f rectCenter( 0.5f * ( V2f( rect.min ) + V2f( rect.max ) ) );
			V2f centerDisp = p - rectCenter;

			const V2f screenScale = screenToImageScale();
			const V2f threshold( screenToImageScale() * m_handleSize );

			if( rect.intersects( p ) && fabs( centerDisp.x ) < threshold.x && fabs( centerDisp.y ) < threshold.y )
			{
				// Center handle
				return V2i( 0, 0 );
			}


			// We're not in the center, so we must be over an edge. Return which edge
			// Not that there is an extra pixel of tolerance here, since the selection rect snaps
			// to the nearest half-pixel, and we need to include the whole selection rect
			Box2f rectInner( V2f(rect.min) + threshold + screenScale, V2f(rect.max) - threshold - screenScale );
			return V2i(
				p.x > rectInner.max.x ? 1 : ( p.x < rectInner.min.x ? -1 : 0 ),
				p.y > rectInner.max.y ? 1 : ( p.y < rectInner.min.y ? -1 : 0 )
			);
		}

		V2f eventPosition( const ButtonEvent &event ) const
		{
			const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
			const ImageGadget *imageGadget = static_cast<const ImageGadget *>( viewportGadget->getPrimaryChild() );
			V2f pixel = imageGadget->pixelAt( event.line );
			Context::Scope contextScope( imageGadget->getContext() );
			return pixel;
		}

		Box2iPlugPtr m_plug;
		const std::string m_id;
		bool m_editable;
		float m_handleSize;
		int m_hover; // Hover state: 0 no hover, 1 for hovered, 2 for deleteButton hovered
		bool m_deletePressed;

		DeleteClickedSignal m_deleteClickedSignal;


		Imath::Box2i m_dragStartRectangle;
		Imath::V2f m_dragStart;
		Imath::V2i m_dragDirection;
};
GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Box2iGadget )


class V2iGadget : public GafferUI::Gadget
{

	public :

		V2iGadget( V2iPlugPtr plug, std::string id )
			: Gadget(), m_plug( plug ), m_id( id ), m_editable( true ), m_handleSize( 10 ), m_hover( 0 ), m_deletePressed( false )
		{
			enterSignal().connect( boost::bind( &V2iGadget::enter, this, ::_2 ) );
			mouseMoveSignal().connect( boost::bind( &V2iGadget::mouseMove, this, ::_2 ) );
			buttonPressSignal().connect( boost::bind( &V2iGadget::buttonPress, this, ::_2 ) );
			dragBeginSignal().connect( boost::bind( &V2iGadget::dragBegin, this, ::_1, ::_2 ) );
			dragEnterSignal().connect( boost::bind( &V2iGadget::dragEnter, this, ::_1, ::_2 ) );
			dragMoveSignal().connect( boost::bind( &V2iGadget::dragMove, this, ::_2 ) );
			dragEndSignal().connect( boost::bind( &V2iGadget::dragEnd, this, ::_2 ) );
			buttonReleaseSignal().connect( boost::bind( &V2iGadget::buttonRelease, this, ::_2 ) );
			leaveSignal().connect( boost::bind( &V2iGadget::leave, this ) );

			plug->node()->plugDirtiedSignal().connect( boost::bind( &V2iGadget::plugDirtied, this, ::_1 ) );
		}

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( V2iGadget, V2iGadgetTypeId, GafferUI::Gadget );

		Imath::Box3f bound() const override
		{
			V2i p = m_plug->getValue();
			return Box3f(
				V3f( p.x, p.y, 0 ),
				V3f( p.x, p.y, 0 )
			);
		}

		const V2iPlug *getPlug() const
		{
			return m_plug.get();
		}

		using DeleteClickedSignal = Signals::Signal<void ( Plug * )>;
		DeleteClickedSignal &deleteClickedSignal()
		{
			return m_deleteClickedSignal;
		}

	protected :

		void renderLayer( Layer layer, const Style *style, RenderReason reason ) const override
		{
			if( layer != Layer::Front )
			{
				return;
			}

			float pixelAspect = 1.0f;
			V2f screenScale = screenToImageScale( &pixelAspect );

			const V2f threshold( screenScale * m_handleSize );

			glPushMatrix();
			glScalef( pixelAspect, 1, 1 );

			V2f point = V2f(m_plug->getValue()) + V2f( 0.5 );
			V2f deleteButtonCenter( point.x + threshold.x, point.y + threshold.y );
			V2f deleteButtonSize( threshold.x * 0.5, threshold.y * 0.5 );
			glPushAttrib( GL_CURRENT_BIT | GL_LINE_BIT | GL_ENABLE_BIT );

				if( isSelectionRender( reason ) )
				{
					if( m_editable )
					{
						// Center handle
						style->renderSolidRectangle( Box2f( point - threshold, point + threshold ) );
						// Delete button
						style->renderSolidRectangle( Box2f( V2f( deleteButtonCenter.x, deleteButtonCenter.y ) - 0.5f * threshold, V2f( deleteButtonCenter.x, deleteButtonCenter.y ) + 0.5f * threshold ) );
					}
				}
				else
				{
					glEnable( GL_LINE_SMOOTH );
					Color4f black( 0.0f, 0.0f, 0.0f, 1.0f );
					renderCircle2D( style, point, 3.5f * screenScale, screenScale.x * 2.0f, black );
					renderCircle2D( style, point, 2.5f * screenScale, screenScale.x * 2.0f, Color4f( 1.0, 1.0, 1.0, 1.0 ) );

					if( m_hover )
					{
						renderFilledCircle2D( style, deleteButtonCenter, deleteButtonSize * 1.4f, Color4f( 0.4, 0.4, 0.4, 1.0 ) );
						Color4f buttonCol( 0.0f, 0.0f, 0.0f, 1.0f );
						if( m_hover == 2 )
						{
							buttonCol = Color4f( 1.0f, 1.0f, 1.0f, 1.0f );
						}
						renderLine2D( style, deleteButtonCenter - deleteButtonSize, deleteButtonCenter + deleteButtonSize, 4.0 * screenScale.x, buttonCol );
						renderLine2D( style, deleteButtonCenter + deleteButtonSize * V2f( 1, -1 ), deleteButtonCenter + deleteButtonSize * V2f( -1, 1 ), 4.0 * screenScale.x, buttonCol );
					}

					float textScale = 10;
					float textLength = style->textBound( Style::LabelText, m_id ).size().x;
					glColor4f( 1.0f, 1.0f, 1.0f, 1.0f );
					glPushMatrix();
						glTranslatef( point.x - ( textScale * textLength + 5 ) * screenScale.x, point.y + 5 * screenScale.y, 0.0f );
						glScalef( textScale * screenScale.x, textScale * screenScale.y, 1 );
						style->renderText( Style::LabelText, m_id );
					glPopMatrix();
				}

			glPopAttrib();

			glPopMatrix();
		}

		unsigned layerMask() const override
		{
			return (unsigned)Layer::Front;
		}

		Imath::Box3f renderBound() const override
		{
			// We draw handles outside the box, so we need to extend outside box - since we
			// don't usually have many Box2iGadgets at once, we return infinite rather than
			// finessing the overrender
			Box3f b;
			b.makeInfinite();
			return b;
		}

	private :

		void plugDirtied( Plug *plug )
		{
			if( plug == m_plug )
			{
				dirty( DirtyType::Bound );
			}
		}

		bool enter( const ButtonEvent &event )
		{
			Metadata::registerValue( m_plug.get(), g_hoveredKey, new IECore::BoolData( true ), false );
			return true;
		}

		bool mouseMove( const ButtonEvent &event )
		{
			// Request render in case the hover state has changed
			dirty( DirtyType::Render );

			const V2f p = eventPosition( event );

			if( onDeleteButton( p ) )
			{
				Pointer::setCurrent( "" );
				m_hover = 2;
				return false;
			}

			m_hover = 1;

			Pointer::setCurrent( "move" );


			return false;
		}

		bool buttonPress( const GafferUI::ButtonEvent &event )
		{
			if( event.buttons != ButtonEvent::Left )
			{
				return false;
			}

			// Anything within the bound is draggable except the delete button
			const V2f p = eventPosition( event );
			if( onDeleteButton( p ) )
			{
				m_deletePressed = true;
				return true;
			}

			return true;
		}

		IECore::RunTimeTypedPtr dragBegin( GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
		{
			if( m_deletePressed )
			{
				return nullptr;
			}

			m_dragStart = eventPosition( event );
			m_dragStartPlugValue = m_plug->getValue();
			return IECore::NullObject::defaultNullObject();
		}

		bool dragEnter( const GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
		{
			if( event.sourceGadget != this )
			{
				return false;
			}

			updateDragPoint( event );
			return true;
		}

		bool dragMove( const GafferUI::DragDropEvent &event )
		{
			updateDragPoint( event );
			return true;
		}

		bool dragEnd( const GafferUI::DragDropEvent &event )
		{
			updateDragPoint( event );
			return true;
		}


		void updateDragPoint( const GafferUI::DragDropEvent &event )
		{
			const V2f p = eventPosition( event );
			V2i point = m_dragStartPlugValue;

			const V2f offset = p - m_dragStart;
			point += V2i( round( offset.x ), round( offset.y ) );

			m_plug->setValue( point );
		}

		bool buttonRelease( const GafferUI::ButtonEvent &event )
		{
			const V2f p = eventPosition( event );
			if( m_deletePressed && onDeleteButton( p ) )
			{
				m_deleteClickedSignal( m_plug.get() );
			}
			m_deletePressed = false;

			return true;
		}

		void leave()
		{
			Pointer::setCurrent( "" );
			m_hover = 0;

			Metadata::registerValue( m_plug.get(), g_hoveredKey, new IECore::BoolData( false ), false );
		}

		// Returns the scale from screen raster pixels to Gaffer image pixels. This includes both
		// the scaling applied by ViewportGadget, and the pixelAspect scaling which isn't applied
		// automatically ( it is optionally returned separately so we can apply it manually in
		// renderLayer )
		V2f screenToImageScale( float *pixelAspectOut = nullptr ) const
		{
			const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
			const V2f viewportPlanarScale(
				viewportGadget->getCamera()->getAperture()[0] / viewportGadget->getViewport()[0],
				viewportGadget->getCamera()->getAperture()[1] / viewportGadget->getViewport()[1]
			);

			const ImageGadget *imageGadget = static_cast<const ImageGadget *>( viewportGadget->getPrimaryChild() );

			// We want to grab the cached version of imageGadget->format(), but it's not exposed publicly, so we
			// get it from pixelAt.
			// In the future, it would be better if format() was public and we didn't have to worry about it
			// throwing.
			float pixelAspect = 1.0f;
			try
			{
				pixelAspect = 1.0f / imageGadget->pixelAt( LineSegment3f( V3f( 1, 0, 0 ), V3f( 1, 0, 1 ) ) ).x;
			}
			catch( ... )
			{
				// Not worried about rendering correctly for images which can't be evaluated properly
			}

			if( pixelAspectOut )
			{
				*pixelAspectOut = pixelAspect;
			}

			return viewportPlanarScale * V2f( 1.0f / pixelAspect, 1.0f );
		}

		bool onDeleteButton( const V2f &p ) const
		{
			// Any positions that are part of the gadget, but not part of an extended bound, are
			// on the delete button
			V2f point = V2f(m_plug->getValue()) + V2f( 0.5 );
			const V2f screenScale = screenToImageScale();
			const V2f threshold( screenScale * m_handleSize );
			return
				p.x > point.x + 0.5 * threshold.x - screenScale.x &&
				p.y > point.y + 0.5 * threshold.y - screenScale.y;
		}

		V2f eventPosition( const ButtonEvent &event ) const
		{
			const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
			const ImageGadget *imageGadget = static_cast<const ImageGadget *>( viewportGadget->getPrimaryChild() );
			V2f pixel = imageGadget->pixelAt( event.line );
			Context::Scope contextScope( imageGadget->getContext() );
			return pixel;
		}

		V2iPlugPtr m_plug;
		const std::string m_id;
		bool m_editable;
		float m_handleSize;
		int m_hover; // Hover state: 0 no hover, 1 for hovered, 2 for deleteButton hovered
		bool m_deletePressed;

		DeleteClickedSignal m_deleteClickedSignal;

		Imath::V2i m_dragStartPlugValue;
		Imath::V2f m_dragStart;
};

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( V2iGadget )

} // namespace


GAFFER_NODE_DEFINE_TYPE( ColorInspectorTool );

size_t ColorInspectorTool::g_firstPlugIndex = 0;
ColorInspectorTool::ToolDescription<ColorInspectorTool, ImageView> ColorInspectorTool::g_imageToolDescription;

ColorInspectorTool::ColorInspectorTool( View *view, const std::string &name )
	:	Tool( view, name ),
		m_contextQuery( new ContextQuery ),
		m_deleteContextVariables( new DeleteContextVariables ),
		m_sampler( new ImageSampler ),
		m_areaSampler( new ImageStats )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ArrayPlug( "inspectors", Plug::In, new ColorInspectorPlug( "defaultInspector" ), 1, 1024, Plug::Default & ~Plug::AcceptsInputs ) );

	inspectorsPlug()->getChild<ColorInspectorPlug>( 0 )->modePlug()->setValue( (int)ColorInspectorPlug::Mode::Cursor );

	PlugPtr evaluatorPlug = new Plug( "evaluator" );
	addChild( evaluatorPlug );
	evaluatorPlug->addChild( new Color4fPlug( "pixelColor" ) );
	evaluatorPlug->addChild( new Color4fPlug( "areaColor" ) );

	// We use `m_contextQuery` to fetch a context variable to transfer
	// the mouse position into `m_sampler`. We could use `mouseMoveSignal()`
	// to instead call `m_sampler->pixelPlug()->setValue()`, but that
	// would cause cancellation of the ImageView background compute every
	// time the mouse was moved. The "colorInspector:source" variable is
	// created in `_ColorInspectorPlugValueWidget`.
	V2fPlugPtr v2fTemplate = new Gaffer::V2fPlug( "v2fTemplate" );
	m_contextQuery->addQuery( v2fTemplate.get(), "colorInspector:source" );

	// The same thing, but when we need an area to evaluate areaColor
	// instead of a pixel to evaluate pixelColor
	Box2iPlugPtr box2iTemplate = new Gaffer::Box2iPlug( "box2iTemplate" );
	m_contextQuery->addQuery( box2iTemplate.get(), "colorInspector:source" );

	// And we use a DeleteContextVariables node to make sure that our
	// private context variable doesn't become visible to the upstream
	// graph.

	ImagePlugPtr dummyImage = new ImagePlug();
	m_deleteContextVariables->setup( dummyImage.get() );
	m_deleteContextVariables->variablesPlug()->setValue( "colorInspector:source" );

	ImageGadget *imageGadget = static_cast<ImageGadget *>( view->viewportGadget()->getPrimaryChild() );

	// We want to inspect the same image we are displaying in the ImageGadget ( this includes some preprocessing
	// by ImageView such as selecting the correct view ), so we take the plug from the ImageGadget as our input.

	// \todo - this const_cast is technically not safe ... but when would we ever have the ImageGadget
	// connected to something that it wasn't safe to pass to setInput? John says he isn't concerned.
	ImagePlug *image = const_cast< ImagePlug* >( imageGadget->getImage() );
	m_deleteContextVariables->inPlug()->setInput( image );
	m_sampler->imagePlug()->setInput( m_deleteContextVariables->outPlug() );

	ValuePlugPtr v2iValuePlug = m_contextQuery->valuePlugFromQueryPlug( m_contextQuery->queriesPlug()->getChild<NameValuePlug>( 0 ) );
	m_sampler->pixelPlug()->setInput( v2iValuePlug );
	m_sampler->interpolatePlug()->setValue( false );

	evaluatorPlug->getChild<Color4fPlug>( "pixelColor" )->setInput( m_sampler->colorPlug() );

	m_areaSampler->inPlug()->setInput( m_deleteContextVariables->outPlug() );
	ValuePlugPtr box2iValuePlug = m_contextQuery->valuePlugFromQueryPlug( m_contextQuery->queriesPlug()->getChild<NameValuePlug>( 1 ) );
	m_areaSampler->areaPlug()->setInput( box2iValuePlug );
	evaluatorPlug->getChild<Color4fPlug>( "areaColor" )->setInput( m_areaSampler->averagePlug() );

	m_gadgets = new ContainerGadget();
	view->viewportGadget()->addChild( m_gadgets );

	imageGadget->channelsChangedSignal().connect( boost::bind( &ColorInspectorTool::channelsChanged, this ) );

	inspectorsPlug()->childAddedSignal().connect( boost::bind( &ColorInspectorTool::colorInspectorAdded, this, ::_2 ) );
	inspectorsPlug()->childRemovedSignal().connect( boost::bind( &ColorInspectorTool::colorInspectorRemoved, this, ::_2 ) );

	plugSetSignal().connect( boost::bind( &ColorInspectorTool::plugSet, this, ::_1 ) );

}

ColorInspectorTool::~ColorInspectorTool()
{
}

Gaffer::ArrayPlug *ColorInspectorTool::inspectorsPlug()
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 0 );
}

const Gaffer::ArrayPlug *ColorInspectorTool::inspectorsPlug() const
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 0 );
}


void ColorInspectorTool::plugSet( Gaffer::Plug *plug )
{
	if( plug == activePlug() )
	{
		bool active = activePlug()->getValue();
		m_gadgets->setVisible( active );
	}
	else if( plug->parent()->parent() == inspectorsPlug() )
	{
		// Triggered from Python when a drag move happens on a Ctrl click, and we need to convert a
		// pixel inspector to an area inspector.

		ColorInspectorPlug *colorInspector = static_cast<ColorInspectorPlug*>( plug->parent() );
		if( plug == colorInspector->modePlug() )
		{
			colorInspectorRemoved( colorInspector );
			colorInspectorAdded( colorInspector );
		}
	}
}

void ColorInspectorTool::colorInspectorAdded( GraphComponent *colorInspector )
{
	ColorInspectorPlug *colorInspectorTyped = static_cast<ColorInspectorPlug*>( colorInspector );
	if( colorInspectorTyped->modePlug()->getValue() == (int)ColorInspectorPlug::Mode::Pixel )
	{
		V2iGadget::Ptr r = new V2iGadget( colorInspectorTyped->pixelPlug(), colorInspector->getName().value().substr( 9 ) );
		r->deleteClickedSignal().connect( boost::bind( &ColorInspectorTool::deleteClicked, this, ::_1 ) );
		m_gadgets->addChild( r );
	}
	else
	{
		Box2iGadget::Ptr r = new Box2iGadget( colorInspectorTyped->areaPlug(), colorInspector->getName().value().substr( 9 ) );
		r->deleteClickedSignal().connect( boost::bind( &ColorInspectorTool::deleteClicked, this, ::_1 ) );
		m_gadgets->addChild( r );
	}
}

void ColorInspectorTool::colorInspectorRemoved( GraphComponent *colorInspector )
{
	ColorInspectorPlug *colorInspectorTyped = static_cast<ColorInspectorPlug*>( colorInspector );
	for( auto &i : m_gadgets->children() )
	{
		if( Box2iGadget *boxGadget = runTimeCast<Box2iGadget>( i.get() ) )
		{
			if( boxGadget->getPlug() == colorInspectorTyped->areaPlug() )
			{
				m_gadgets->removeChild( i );
				return;
			}
		}
		else if( V2iGadget *v2iGadget = runTimeCast<V2iGadget>( i.get() ) )
		{
			if( v2iGadget->getPlug() == colorInspectorTyped->pixelPlug() )
			{
				m_gadgets->removeChild( i );
				return;
			}
		}
	}
}

void ColorInspectorTool::deleteClicked( Gaffer::Plug *plug )
{
	inspectorsPlug()->removeChild( plug->parent() );
}

void ColorInspectorTool::channelsChanged()
{
	ImageGadget *imageGadget = static_cast<ImageGadget *>( view()->viewportGadget()->getPrimaryChild() );
	StringVectorDataPtr channels = new StringVectorData( std::vector<std::string>(
		imageGadget->getChannels().begin(),
		imageGadget->getChannels().end()
	) );
	m_sampler->channelsPlug()->setValue( channels );
	m_areaSampler->channelsPlug()->setValue( channels );
}

ColorInspectorTool::ColorInspectorPlug::ColorInspectorPlug( const std::string &name, Direction direction, unsigned flags )
	: ValuePlug( name, direction, flags )
{
	addChild( new IntPlug( "mode", Direction::In, (int)Mode::Pixel, (int)Mode::Cursor, (int)Mode::Area ) );
	addChild( new V2iPlug( "pixel" ) );
	addChild( new Box2iPlug( "area" ) );
}

Gaffer::IntPlug *ColorInspectorTool::ColorInspectorPlug::modePlug()
{
	return getChild<IntPlug>( 0 );
}

const Gaffer::IntPlug *ColorInspectorTool::ColorInspectorPlug::modePlug() const
{
	return getChild<IntPlug>( 0 );
}

Gaffer::V2iPlug *ColorInspectorTool::ColorInspectorPlug::pixelPlug()
{
	return getChild<V2iPlug>( 1 );
}

const Gaffer::V2iPlug *ColorInspectorTool::ColorInspectorPlug::pixelPlug() const
{
	return getChild<V2iPlug>( 1 );
}

Gaffer::Box2iPlug *ColorInspectorTool::ColorInspectorPlug::areaPlug()
{
	return getChild<Box2iPlug>( 2 );
}

const Gaffer::Box2iPlug *ColorInspectorTool::ColorInspectorPlug::areaPlug() const
{
	return getChild<Box2iPlug>( 2 );
}

bool ColorInspectorTool::ColorInspectorPlug::acceptsChild( const Gaffer::GraphComponent *potentialChild ) const
{
	if( !Plug::acceptsChild( potentialChild ) )
	{
		return false;
	}
	return children().size() <= 3;
}

Gaffer::PlugPtr ColorInspectorTool::ColorInspectorPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	return new ColorInspectorPlug( name, direction, getFlags() );
}
