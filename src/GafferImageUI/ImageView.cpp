//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#include "GafferImageUI/ImageView.h"

#include "GafferImageUI/ImageGadget.h"
#include "GafferImageUI/OpenColorIOAlgo.h"

#include "GafferImage/ImagePlug.h"
#include "GafferImage/ImageSampler.h"
#include "GafferImage/ImageStats.h"
#include "GafferImage/OpenColorIOTransform.h"
#include "GafferImage/SelectView.h"

#include "GafferUI/Gadget.h"
#include "GafferUI/Pointer.h"
#include "GafferUI/StandardStyle.h"
#include "GafferUI/Style.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"
#include "Gaffer/ContextQuery.h"
#include "Gaffer/ContextVariables.h"
#include "Gaffer/DeleteContextVariables.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/BoxPlug.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/NameSwitch.h"

#include "IECoreGL/IECoreGL.h"
#include "IECoreGL/Shader.h"
#include "IECoreGL/ShaderLoader.h"
#include "IECoreGL/Texture.h"
#include "IECoreGL/TextureLoader.h"
#include "IECoreGL/ToGLTextureConverter.h"

#include "IECore/NullObject.h"
#include "IECore/BoxAlgo.h"
#include "IECore/BoxOps.h"
#include "IECore/FastFloat.h"

#include "Imath/ImathColorAlgo.h"
#include "Imath/ImathMatrixAlgo.h"

#include "boost/bind/bind.hpp"
#include "boost/bind/placeholders.hpp"
#include "boost/lexical_cast.hpp"

#include <cmath>

using namespace boost;
using namespace boost::placeholders;
using namespace IECoreGL;
using namespace IECore;
using namespace Imath;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferImage;
using namespace GafferImageUI;

//////////////////////////////////////////////////////////////////////////
/// Implementation of ImageView::ColorInspector
//////////////////////////////////////////////////////////////////////////

namespace
{

IECore::InternedString g_hoveredKey( "__hovered" );

void renderLine2D( const Style *style, V2f a, V2f b, float width, const Color4f &col )
{
	style->renderLine( LineSegment3f( V3f( a.x, a.y, 0.0 ), V3f( b.x, b.y, 0 ) ), width, &col );
}

// TODO - these are some terrible ways of drawing circles, but I just wanted something quick that works.  Add
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
	glColor( col );
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
			:   Gadget(), m_plug( plug ), m_id( id ), m_editable( true ), m_handleSize( 10 ), m_hover( 0 ), m_deletePressed( false )
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
					glColor4f( 0.8f, 0.8f, 0.8f, 1.0f );
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

		// Returns the scale from screen raster pixels to Gaffer image pixels.  This includes both
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


			// We're not in the center, so we must be over an edge.  Return which edge
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
		int m_hover;  // Hover state:  0 no hover, 1 for hovered, 2 for deleteButton hovered
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
			:   Gadget(), m_plug( plug ), m_id( id ), m_editable( true ), m_handleSize( 10 ), m_hover( 0 ), m_deletePressed( false )
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
					renderLine2D( style, point - V2f( threshold.x, 0 ), point - V2f( 2.5 * screenScale.x, 0 ), screenScale.y * 2.0f, black );
					renderLine2D( style, point + V2f( threshold.x, 0 ), point + V2f( 2.5 * screenScale.x, 0 ), screenScale.y * 2.0f, black );
					renderLine2D( style, point - V2f( 0, threshold.y ), point - V2f( 0, 2.5 * screenScale.y ), screenScale.x * 2.0f, black );
					renderLine2D( style, point + V2f( 0, threshold.y ), point + V2f( 0, 2.5 * screenScale.y ), screenScale.x * 2.0f, black );
					renderCircle2D( style, point, 2.5f * screenScale, screenScale.x * 2.0f, Color4f( 0.8, 0.8, 0.8, 1.0 ) );

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

		// Returns the scale from screen raster pixels to Gaffer image pixels.  This includes both
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
		int m_hover;  // Hover state:  0 no hover, 1 for hovered, 2 for deleteButton hovered
		bool m_deletePressed;

		DeleteClickedSignal m_deleteClickedSignal;

		Imath::V2i m_dragStartPlugValue;
		Imath::V2f m_dragStart;
};
GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( V2iGadget )

const float g_wipeHandleThickness = 14.0f;

} // namespace

class ImageView::WipeHandle : public GafferUI::Gadget
{

	public :

		WipeHandle()
			:	Gadget(), m_pos( 0 ), m_dir( 1, 0 ), m_editable( true ), m_dragHandle( HandleSelect::None )
		{
			mouseMoveSignal().connect( boost::bind( &WipeHandle::mouseMove, this, ::_2 ) );
			buttonPressSignal().connect( boost::bind( &WipeHandle::buttonPress, this, ::_2 ) );
			buttonReleaseSignal().connect( boost::bind( &WipeHandle::buttonRelease, this, ::_2 ) );
			dragBeginSignal().connect( boost::bind( &WipeHandle::dragBegin, this, ::_1, ::_2 ) );
			dragEnterSignal().connect( boost::bind( &WipeHandle::dragEnter, this, ::_1, ::_2 ) );
			dragMoveSignal().connect( boost::bind( &WipeHandle::dragMove, this, ::_2 ) );
			dragEndSignal().connect( boost::bind( &WipeHandle::dragEnd, this, ::_2 ) );
			leaveSignal().connect( boost::bind( &WipeHandle::leave, this ) );
		}

		Imath::Box3f bound() const override
		{
			// The wipe indicator is an infinite line, so we don't have a sensible bound
			return Box3f();
		}

		void setPosition( const Imath::V2f &p )
		{
			setWipeInternal( p, m_dir );
		}

		const Imath::V2f &getPosition() const
		{
			return m_pos;
		}

		void setDirection( const Imath::V2f &d )
		{
			if( d != V2f( 0 ) )
			{
				setWipeInternal( m_pos, d.normalized() );
			}
		}

		const Imath::V2f &getDirection() const
		{
			return m_dir;
		}

		void setEditable( bool editable )
		{
			m_editable = editable;
		}

		bool getEditable() const
		{
			return m_editable;
		}

	protected :

		void renderLayer( Layer layer, const Style *style, RenderReason reason ) const override
		{
			if( layer != Layer::Front )
			{
				return;
			}

			float rsf = rasterScaleFactor();
			float handleRadius = 30.0f * rsf;

			Color4f bright( 0.8f, 0.8f, 0.8f, 0.5f );
			Color4f dark( 0.2f, 0.2f, 0.2f, 0.5f );

			if( isSelectionRender( reason ) )
			{
				if( m_editable )
				{
					// Draw one thick handle for selection
					renderHandle( style, handleRadius, rsf * g_wipeHandleThickness * 1.2f, 0.0f, dark );
				}
			}
			else
			{
				// Draw a thin bright handle offset from a dark handle, so that it will
				// be visible on any background
				renderHandle( style, handleRadius, rsf * 1.7f, -rsf * 0.5, dark );
				renderHandle( style, handleRadius, rsf * 1.7f, rsf * 0.5, bright );
			}
		}

		unsigned layerMask() const override
		{
			return (unsigned)Layer::Front;
		}

		Imath::Box3f renderBound() const override
		{
			Box3f b;
			b.makeInfinite();
			return b;
		}

	private :

		void renderHandle( const Style *style, float rotateHandleSize, float thickness, float offset, const Color4f &color ) const
		{
			const ViewportGadget *viewport = ancestor<ViewportGadget>();
			const V2i &viewportSize = viewport->getViewport();

			Box2f rasterViewport( V2f( 0 ), V2f( viewportSize.x, viewportSize.y ) );
			Box3f worldViewport3d(
				viewport->rasterToWorldSpace( rasterViewport.min ).p0,
				viewport->rasterToWorldSpace( rasterViewport.max ).p0
			);
			float size = ( worldViewport3d.max - worldViewport3d.min ).length();
			V2f worldViewportCenter( worldViewport3d.center().x, worldViewport3d.center().y );

			// For the infinite line defined by the wipe, find the closest point to the center of the viewport,
			// for a good place to draw it from
			V2f closestPoint = worldViewportCenter + m_dir * m_dir.dot( m_pos - worldViewportCenter );

			V2f perp( m_dir.y, -m_dir.x );
			line2D( style, closestPoint + perp * size + m_dir * offset, closestPoint - perp * size + m_dir * offset, thickness, color );

			// Draw the arc
			const int segments = 32;
			V2f prevArcPos;
			for( int i = 0; i < segments + 1; i++ )
			{
				float angle = i * M_PI / float( segments );
				V2f arcPos = ( m_dir * sinf( angle ) + perp * cosf( angle ) ) * ( rotateHandleSize + offset );
				if( i != 0 )
				{
					line2D( style, m_pos + arcPos, m_pos + prevArcPos, thickness, color );
				}

				prevArcPos = arcPos;
			}
		}

		// Compute the scaling from our space to raster space, so we can compensate for UIs that we
		// want to be constant sized in raster space
		float rasterScaleFactor() const
		{
			const ViewportGadget *viewport = ancestor<ViewportGadget>();

			V3f s;
			Imath::extractScaling( this->fullTransform(), s );

			const V2f p1 = viewport->gadgetToRasterSpace( V3f( 0.0f ), this );
			const V2f p2 = viewport->gadgetToRasterSpace( V3f( s.x, 0.0f, 0.0f ), this );
			return 1.0 / ( p1 - p2 ).length();
		}

		void setWipeInternal( const Imath::V2f &pos, const Imath::V2f &dir )
		{
			m_pos = pos;
			m_dir = dir;
			dirty( DirtyType::Render );
		}

		static void line2D( const Style *style, V2f p1, V2f p2, float width, const Color4f &c, float hack = 0 )
		{
			style->renderLine( IECore::LineSegment3f( V3f( p1.x, p1.y, 0 ), V3f( p2.x, p2.y, 0 ) ), width, &c );
		}

		bool mouseMove( const ButtonEvent &event )
		{
			HandleSelect h;
			if( m_dragHandle != HandleSelect::None )
			{
				// Don't change the cursor during a drag - stick with whatever we started the drag with
				h = m_dragHandle;
			}
			else
			{
				h = hoveredHandle( event );
			}


			if( h == HandleSelect::Translate )
			{
				Pointer::setCurrent( "move" );
			}
			else if( h == HandleSelect::Rotate )
			{
				Pointer::setCurrent( "rotate" );
			}
			else
			{
				Pointer::setCurrent( "" );
			}

			return false;
		}

		bool buttonPress( const GafferUI::ButtonEvent &event )
		{
			if( event.buttons != ButtonEvent::Left )
			{
				return false;
			}

			m_dragHandle = hoveredHandle( event );
			return true;
		}

		bool buttonRelease( const GafferUI::ButtonEvent &event )
		{
			m_dragHandle = HandleSelect::None;
			return false;
		}

		IECore::RunTimeTypedPtr dragBegin( GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
		{
			m_dragStart = eventPosition( event );
			m_dragStartPos = m_pos;
			V2f startCursorDir = ( m_dragStart - m_pos ).normalized();
			m_dragStartAlignment = V2f(
				startCursorDir.x * m_dir.x + startCursorDir.y * m_dir.y,
				startCursorDir.x * m_dir.y - startCursorDir.y * m_dir.x
			);
			return IECore::NullObject::defaultNullObject();
		}

		bool dragEnter( const GafferUI::Gadget *gadget, const GafferUI::DragDropEvent &event )
		{
			if( event.sourceGadget != this )
			{
				return false;
			}

			updateDrag( event );
			return true;
		}

		bool dragMove( const GafferUI::DragDropEvent &event )
		{
			updateDrag( event );
			return true;
		}

		bool dragEnd( const GafferUI::DragDropEvent &event )
		{
			updateDrag( event );
			m_dragHandle = HandleSelect::None;
			return true;
		}

		void updateDrag( const GafferUI::DragDropEvent &event )
		{
			const V2f p = eventPosition( event );

			if( m_dragHandle == HandleSelect::Translate )
			{
				const V2f offset = p - m_dragStart;
				setWipeInternal( m_dragStartPos + offset, m_dir );
			}
			else if( m_dragHandle == HandleSelect::Rotate )
			{
				V2f disp = p - m_pos;

				disp = V2f(
					disp.x * m_dragStartAlignment.x - disp.y * m_dragStartAlignment.y,
					disp.x * m_dragStartAlignment.y + disp.y * m_dragStartAlignment.x
				);

				if( disp != V2f( 0 ) )
				{
					setWipeInternal( m_pos, disp.normalized() );
				}
			}
		}

		void leave()
		{
			Pointer::setCurrent( "" );
		}

		enum class HandleSelect
		{
			None,
			Translate,
			Rotate
		};

		HandleSelect hoveredHandle( const ButtonEvent &event ) const
		{
			const V2f p = eventPosition( event );

			float rsf = rasterScaleFactor();
			if( ( p - m_pos ).dot( m_dir ) < rsf * g_wipeHandleThickness * 0.5f )
			{
				return HandleSelect::Translate;
			}

			return HandleSelect::Rotate;
		}

		V2f eventPosition( const ButtonEvent &event ) const
		{
			const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
			const ImageGadget *imageGadget = static_cast<const ImageGadget *>( viewportGadget->getPrimaryChild() );
			V2f pixel = imageGadget->pixelAt( event.line );
			Context::Scope contextScope( imageGadget->getContext() );
			pixel.x *= imageGadget->getImage()->format().getPixelAspect();
			return pixel;
		}

		V2f m_pos;
		V2f m_dir;

		bool m_editable;

		Imath::V2f m_dragStartPos;
		Imath::V2f m_dragStartAlignment;
		Imath::V2f m_dragStart;

		HandleSelect m_dragHandle;
};

ImageView::ColorInspectorPlug::ColorInspectorPlug( const std::string &name, Direction direction, unsigned flags )
	: ValuePlug( name, direction, flags )
{
	addChild( new IntPlug( "mode", Direction::In, (int)Mode::Pixel, (int)Mode::Cursor, (int)Mode::Area ) );
	addChild( new V2iPlug( "pixel" ) );
	addChild( new Box2iPlug( "area" ) );
}

Gaffer::IntPlug *ImageView::ColorInspectorPlug::modePlug()
{
	return getChild<IntPlug>( 0 );
}

const Gaffer::IntPlug *ImageView::ColorInspectorPlug::modePlug() const
{
	return getChild<IntPlug>( 0 );
}

Gaffer::V2iPlug *ImageView::ColorInspectorPlug::pixelPlug()
{
	return getChild<V2iPlug>( 1 );
}

const Gaffer::V2iPlug *ImageView::ColorInspectorPlug::pixelPlug() const
{
	return getChild<V2iPlug>( 1 );
}

Gaffer::Box2iPlug *ImageView::ColorInspectorPlug::areaPlug()
{
	return getChild<Box2iPlug>( 2 );
}

const Gaffer::Box2iPlug *ImageView::ColorInspectorPlug::areaPlug() const
{
	return getChild<Box2iPlug>( 2 );
}

bool ImageView::ColorInspectorPlug::acceptsChild( const Gaffer::GraphComponent *potentialChild ) const
{
	if( !Plug::acceptsChild( potentialChild ) )
	{
		return false;
	}
	return children().size() <= 3;
}

Gaffer::PlugPtr ImageView::ColorInspectorPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	return new ColorInspectorPlug( name, direction, getFlags() );
}

class ImageView::ColorInspector : public Signals::Trackable
{

	public :

		ColorInspector( ImageView *view )
			:	m_view( view ),
				m_contextQuery( new ContextQuery ),
				m_deleteContextVariables( new DeleteContextVariables ),
				m_sampler( new ImageSampler ),
				m_areaSampler( new ImageStats )
		{
			// ---- Create a plug on ImageView which will be used for evaluating colorInspectors

			PlugPtr colorInspectorPlug = new Plug( "colorInspector" );
			view->addChild( colorInspectorPlug );

			PlugPtr evaluatorPlug = new Plug( "evaluator" );
			colorInspectorPlug->addChild( evaluatorPlug );
			evaluatorPlug->addChild( new Color4fPlug( "pixelColor" ) );
			evaluatorPlug->addChild( new Color4fPlug( "areaColor" ) );

			// We use `m_pixel` to fetch a context variable to transfer
			// the mouse position into `m_sampler`. We could use `mouseMoveSignal()`
			// to instead call `m_sampler->pixelPlug()->setValue()`, but that
			// would cause cancellation of the ImageView background compute every
			// time the mouse was moved. The "colorInspector:source" variable is
			// created in ImageViewUI's `_ColorInspectorPlugValueWidget`.
			V2fPlugPtr v2fTemplate = new Gaffer::V2fPlug( "v2fTemplate" );
			m_contextQuery->addQuery( v2fTemplate.get(), "colorInspector:source" );

			// The same thing, but when we need an area to evaluate areaColor
			// instead of a pixel to evaluate pixelColor
			Box2iPlugPtr box2iTemplate = new Gaffer::Box2iPlug( "box2iTemplate" );
			m_contextQuery->addQuery( box2iTemplate.get(), "colorInspector:source" );

			// And we use a DeleteContextVariables node to make sure that our
			// private context variable doesn't become visible to the upstream
			// graph.
			m_deleteContextVariables->setup( view->inPlug<ImagePlug>() );
			m_deleteContextVariables->variablesPlug()->setValue( "colorInspector:source" );

			// We want to sample the image before the display transforms
			// are applied. We can't simply get this image from inPlug()
			// because derived classes may have called insertConverter(),
			// so we take it from the input to the display transform chain.

			ImagePlug *image = view->getPreprocessor()->getChild<DeepState>( "__flattenedImage" )->getChild<ImagePlug>( "out" );
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

			ImageGadget *imageGadget = static_cast<ImageGadget *>( m_view->viewportGadget()->getPrimaryChild() );
			imageGadget->channelsChangedSignal().connect( boost::bind( &ColorInspector::channelsChanged, this ) );


			// ---- Create a plug on ImageView for storing colorInspectors
			colorInspectorPlug->addChild( new ArrayPlug( "inspectors", Plug::In, new ColorInspectorPlug(), 1, 1024, Plug::Default & ~Plug::AcceptsInputs ) );
			colorInspectorsPlug()->childAddedSignal().connect( boost::bind( &ColorInspector::colorInspectorAdded, this, ::_2 ) );
			colorInspectorsPlug()->childRemovedSignal().connect( boost::bind( &ColorInspector::colorInspectorRemoved, this, ::_2 ) );

			colorInspectorsPlug()->getChild<ColorInspectorPlug>( 0 )->modePlug()->setValue( (int)ColorInspectorPlug::Mode::Cursor );

			view->plugSetSignal().connect( boost::bind( &ColorInspector::plugSet, this, ::_1 ) );
		}

	private :

		Gaffer::ArrayPlug *colorInspectorsPlug()
		{
			return m_view->getChild<Plug>( "colorInspector" )->getChild<ArrayPlug>( "inspectors" );
		}

		const Gaffer::ArrayPlug *colorInspectorsPlug() const
		{
			return m_view->getChild<Plug>( "colorInspector" )->getChild<ArrayPlug>( "inspectors" );
		}

		void plugSet( Gaffer::Plug *plug )
		{
			// Note that this code is currently unused, since I've disabled the ability to toggle
			// mode from the UI.  Perhaps this should be deleted?
			if( plug->parent()->parent() == colorInspectorsPlug() )
			{
				ColorInspectorPlug *colorInspector = static_cast<ColorInspectorPlug*>( plug->parent() );
				if( plug == colorInspector->modePlug() )
				{
					if( colorInspector->modePlug()->getValue() == (int)ColorInspectorPlug::Mode::Pixel )
					{
						colorInspector->pixelPlug()->setValue( colorInspector->areaPlug()->getValue().center() );
					}
					else if( colorInspector->modePlug()->getValue() == (int)ColorInspectorPlug::Mode::Area )
					{
						V2i pixel = colorInspector->pixelPlug()->getValue();
						colorInspector->areaPlug()->setValue( Box2i( pixel - V2i( 50 ), pixel + V2i( 50 ) ) );
					}
					colorInspectorRemoved( colorInspector );
					colorInspectorAdded( colorInspector );
				}
			}
		}

		void colorInspectorAdded( GraphComponent *colorInspector )
		{
			ColorInspectorPlug *colorInspectorTyped = static_cast<ColorInspectorPlug*>( colorInspector );
			if( colorInspectorTyped->modePlug()->getValue() == (int)ColorInspectorPlug::Mode::Pixel )
			{
				V2iGadget::Ptr r = new V2iGadget( colorInspectorTyped->pixelPlug(), colorInspector->getName().value().substr( 1 ) );
				r->deleteClickedSignal().connect( boost::bind( &ColorInspector::deleteClicked, this, ::_1 ) );
				m_view->viewportGadget()->addChild( r );
			}
			else
			{
				Box2iGadget::Ptr r = new Box2iGadget( colorInspectorTyped->areaPlug(), colorInspector->getName().value().substr( 1 ) );
				r->deleteClickedSignal().connect( boost::bind( &ColorInspector::deleteClicked, this, ::_1 ) );
				m_view->viewportGadget()->addChild( r );
			}
		}

		void colorInspectorRemoved( GraphComponent *colorInspector )
		{
			ColorInspectorPlug *colorInspectorTyped = static_cast<ColorInspectorPlug*>( colorInspector );
			for( auto &i : m_view->viewportGadget()->children() )
			{
				if( Box2iGadget *boxGadget = runTimeCast<Box2iGadget>( i.get() ) )
				{
					if( boxGadget->getPlug() == colorInspectorTyped->areaPlug() )
					{
						m_view->viewportGadget()->removeChild( i );
						return;
					}
				}
				else if( V2iGadget *v2iGadget = runTimeCast<V2iGadget>( i.get() ) )
				{
					if( v2iGadget->getPlug() == colorInspectorTyped->pixelPlug() )
					{
						m_view->viewportGadget()->removeChild( i );
						return;
					}
				}
			}
		}

		void deleteClicked( Gaffer::Plug *plug )
		{
			colorInspectorsPlug()->removeChild( plug->parent() );
		}

		void channelsChanged()
		{
			ImageGadget *imageGadget = static_cast<ImageGadget *>( m_view->viewportGadget()->getPrimaryChild() );
			StringVectorDataPtr channels = new StringVectorData( std::vector<std::string>(
				imageGadget->getChannels().begin(),
				imageGadget->getChannels().end()
			) );
			m_sampler->channelsPlug()->setValue( channels );
			m_areaSampler->channelsPlug()->setValue( channels );
		}

		ImageView *m_view;
		ContextQueryPtr m_contextQuery;
		DeleteContextVariablesPtr m_deleteContextVariables;
		ImageSamplerPtr m_sampler;
		ImageStatsPtr m_areaSampler;

};

//////////////////////////////////////////////////////////////////////////
/// Implementation of ImageView
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( ImageView );

GAFFERIMAGEUI_API ImageView::ViewDescription<ImageView> ImageView::g_viewDescription( GafferImage::ImagePlug::staticTypeId() );

ImageView::ImageView( const std::string &name )
	:	View( name, new GafferImage::ImagePlug() ),
		m_imageGadgets{ new ImageGadget(), new ImageGadget() },
		m_framed( false )
{

	// build the preprocessor we use for applying colour
	// transforms, and the stats node we use for displaying stats.

	NodePtr preprocessor = new Node;
	ImagePlugPtr preprocessorInput = new ImagePlug( "in" );
	preprocessor->addChild( preprocessorInput );

	addChild( new StringPlug( "view", Plug::In, "default", Plug::Default & ~Plug::AcceptsInputs ) );

	PlugPtr compareParent = new Plug( "compare" );
	addChild( compareParent );
	compareParent->addChild( new StringPlug( "mode", Plug::In, "", Plug::Default & ~Plug::AcceptsInputs ) );
	compareParent->addChild( new BoolPlug( "matchDisplayWindows", Plug::In ) );
	compareParent->addChild( new BoolPlug( "wipe", Plug::In, true, Plug::Default & ~Plug::AcceptsInputs ) );
	compareParent->addChild( new ImagePlug( "image", Plug::In ) );
	compareParent->addChild( new StringPlug( "catalogueOutput", Plug::In, "output:1", Plug::Default & ~Plug::AcceptsInputs ) );

	StringVectorDataPtr channelsDefaultData = new StringVectorData;
	channelsDefaultData->writable() = { "R", "G", "B", "A" };
	addChild( new StringVectorDataPlug( "channels", Plug::In, channelsDefaultData ) );

	[[maybe_unused]] auto displayTransform = new DisplayTransform( this );
	assert( displayTransform->parent() == this );

	ImagePlugPtr preprocessorOutput = new ImagePlug( "out", Plug::Out );
	preprocessor->addChild( preprocessorOutput );

	DeleteContextVariablesPtr comparisonDeleteContext = new DeleteContextVariables( "_comparisonDeleteContext" );
	preprocessor->addChild( comparisonDeleteContext );
	comparisonDeleteContext->setup( compareImagePlug() );
	comparisonDeleteContext->variablesPlug()->setValue( "imageView:__useComparisonImage" );
	comparisonDeleteContext->inPlug()->setInput( compareImagePlug() );

	NameSwitchPtr comparisonSwitch = new NameSwitch( "_comparisonSwitch" );
	preprocessor->addChild( comparisonSwitch );
	comparisonSwitch->setup( preprocessorInput.get() );
	comparisonSwitch->selectorPlug()->setValue( "${imageView:__useComparisonImage}" );
	comparisonSwitch->inPlugs()->getChild<NameValuePlug>(0)->valuePlug()->setInput( preprocessorInput );
	comparisonSwitch->inPlugs()->getChild<NameValuePlug>(1)->namePlug()->setValue( "True" );
	comparisonSwitch->inPlugs()->getChild<NameValuePlug>(1)->valuePlug()->setInput( comparisonDeleteContext->outPlug() );

	SelectViewPtr selectView = new SelectView( "_selectView" );
	preprocessor->addChild( selectView );
	selectView->inPlug()->setInput( runTimeCast< NameValuePlug >( comparisonSwitch->outPlug() )->valuePlug() );

	// All of the ways we want to interact with the image here require it to be flattened first ( ImageGadget,
	// ImageStats, ImageSampler ).  By flattening it before any of these things, we ensure it only gets
	// flattened once ( the flattens inside ImageStats and ImageSamplers will simply pass through when they
	// notice the image is already flat ).
	DeepStatePtr deepState = new DeepState( "__flattenedImage" );
	preprocessor->addChild( deepState );
	deepState->deepStatePlug()->setValue( int( DeepState::TargetState::Flat ) );
	deepState->inPlug()->setInput( selectView->outPlug() );

	preprocessorOutput->setInput( deepState->outPlug() );

	// tell the base class about all the preprocessing we want to do

	setPreprocessor( preprocessor );

	// connect up to some signals

	plugSetSignal().connect( boost::bind( &ImageView::plugSet, this, ::_1 ) );
	viewportGadget()->keyPressSignal().connect( boost::bind( &ImageView::keyPress, this, ::_2 ) );
	viewportGadget()->preRenderSignal().connect( boost::bind( &ImageView::preRender, this ) );

	// Now we can connect up our ImageGadget, which will do the
	// hard work of actually displaying the image.

	m_imageGadgets[0]->setImage( preprocessedInPlug<ImagePlug>() );
	m_imageGadgets[0]->setContext( getContext() );

	m_comparisonSelect = new Gaffer::ContextVariables( "__comparisonSelect" );
	addChild( m_comparisonSelect );
	m_comparisonSelect->setup( compareImagePlug() );
	m_comparisonSelect->inPlug()->setInput( preprocessedInPlug<ImagePlug>() );
	m_comparisonSelect->variablesPlug()->addChild( new NameValuePlug( "catalogue:imageName",  new StringData( "output:1" ), true ) );
	m_comparisonSelect->variablesPlug()->getChild<NameValuePlug>( 0 )->valuePlug<StringPlug>()->setInput( compareCatalogueOutputPlug() );
	m_comparisonSelect->variablesPlug()->addChild( new NameValuePlug( "imageView:__useComparisonImage",  new StringData( "True" ), true ) );

	m_imageGadgets[1]->setImage( IECore::runTimeCast<GafferImage::ImagePlug>( m_comparisonSelect->outPlug() ) );
	m_imageGadgets[1]->setContext( getContext() );
	m_imageGadgets[1]->setLabelsVisible( false );
	m_imageGadgets[1]->setVisible( false );
	viewportGadget()->addChild( m_imageGadgets[1] );

	// We add the primary gadget last, because we want it to be on top
	viewportGadget()->setPrimaryChild( m_imageGadgets[0] );

	selectView->viewPlug()->setInput( viewPlug() );

	m_colorInspector.reset( new ColorInspector( this ) );

	m_wipeHandle = new WipeHandle();
	m_wipeHandle->setVisible( false );
	viewportGadget()->setChild( "__wipeHandle", m_wipeHandle );

}

void ImageView::insertConverter( Gaffer::NodePtr converter )
{
	PlugPtr converterInput = converter->getChild<Plug>( "in" );
	if( !converterInput )
	{
		throw IECore::Exception( "Converter has no Plug named \"in\"" );
	}
	ImagePlugPtr converterOutput = converter->getChild<ImagePlug>( "out" );
	if( !converterOutput )
	{
		throw IECore::Exception( "Converter has no ImagePlug named \"out\"" );
	}

	PlugPtr newInput = converterInput->createCounterpart( "in", Plug::In );
	setChild( "in", newInput );

	NodePtr preprocessor = getPreprocessor();
	Plug::OutputContainer outputsToRestore = preprocessor->getChild<ImagePlug>( "in" )->outputs();

	/// \todo Replacing the `in` plug like this is bogus. It breaks the ordering
	/// of children (the original is removed and the replacement is added at the
	/// end) and forces accessors like `View::tools()` to perform lookups using
	/// names rather than indices. We only want to do a one-off setup of
	/// converters anyway, so it might make more sense to pass the converter to
	/// the `ImageView` constructor so we can pass an appropriate plug to the
	/// View constructor in the first place.
	PlugPtr newPreprocessorInput = converterInput->createCounterpart( "in", Plug::In );
	preprocessor->setChild( "in", newPreprocessorInput );
	newPreprocessorInput->setInput( newInput );

	preprocessor->setChild( "__converter", converter );
	converterInput->setInput( newPreprocessorInput );

	for( Plug::OutputContainer::const_iterator it = outputsToRestore.begin(), eIt = outputsToRestore.end(); it != eIt; ++it )
	{
		(*it)->setInput( converterOutput );
	}
}

ImageView::~ImageView()
{
	// Addons like m_colorInspector add plugs to us which are connected to nodes held by them, which are not
	// our children.  If these were child nodes, they would be held by the GraphComponent base class which
	// gets destructed very late, but because they are not actually children, they will be destructed fairly
	// quickly by our destructor ... before the signals in the Node base class get destructed.
	//
	// These graph modifications happening during our destructor would trigger signals to be sent, which
	// is very dangerous - those signals could be connected to something which tries to access us, and anyone
	// who takes an intrusive pointer to us while we're destructing will trigger a segfault.
	//
	// We can safeguard against this by disconnecting any slots that would be trigger by graph structure changes
	// before we destruct member variables.
	//
	// This shouldn't be necessary once we come up with a more general solution to:
	// https://github.com/GafferHQ/gaffer/issues/4221
	plugInputChangedSignal().disconnectAllSlots();
	plugDirtiedSignal().disconnectAllSlots();
}

StringVectorDataPlug *ImageView::channelsPlug()
{
	return getChild<StringVectorDataPlug>( "channels" );
}

const StringVectorDataPlug *ImageView::channelsPlug() const
{
	return getChild<StringVectorDataPlug>( "channels" );
}

Gaffer::StringPlug *ImageView::viewPlug()
{
	return getChild<StringPlug>( "view" );
}

const Gaffer::StringPlug *ImageView::viewPlug() const
{
	return getChild<StringPlug>( "view" );
}

Gaffer::StringPlug *ImageView::compareModePlug()
{
	return getChild<Plug>( "compare" )->getChild<StringPlug>( "mode" );
}

const Gaffer::StringPlug *ImageView::compareModePlug() const
{
	return getChild<Plug>( "compare" )->getChild<StringPlug>( "mode" );
}

Gaffer::BoolPlug *ImageView::compareMatchDisplayWindowsPlug()
{
	return getChild<Plug>( "compare" )->getChild<BoolPlug>( "matchDisplayWindows" );
}

const Gaffer::BoolPlug *ImageView::compareMatchDisplayWindowsPlug() const
{
	return getChild<Plug>( "compare" )->getChild<BoolPlug>( "matchDisplayWindows" );
}

Gaffer::BoolPlug *ImageView::compareWipePlug()
{
	return getChild<Plug>( "compare" )->getChild<BoolPlug>( "wipe" );
}

const Gaffer::BoolPlug *ImageView::compareWipePlug() const
{
	return getChild<Plug>( "compare" )->getChild<BoolPlug>( "wipe" );
}

GafferImage::ImagePlug *ImageView::compareImagePlug()
{
	return getChild<Plug>( "compare" )->getChild<ImagePlug>( "image" );
}

const GafferImage::ImagePlug *ImageView::compareImagePlug() const
{
	return getChild<Plug>( "compare" )->getChild<ImagePlug>( "image" );
}

Gaffer::StringPlug *ImageView::compareCatalogueOutputPlug()
{
	return getChild<Plug>( "compare" )->getChild<StringPlug>( "catalogueOutput" );
}

const Gaffer::StringPlug *ImageView::compareCatalogueOutputPlug() const
{
	return getChild<Plug>( "compare" )->getChild<StringPlug>( "catalogueOutput" );
}

ImageGadget *ImageView::imageGadget()
{
	return m_imageGadgets[0].get();
}

const ImageGadget *ImageView::imageGadget() const
{
	return m_imageGadgets[0].get();
}

void ImageView::setContext( Gaffer::ContextPtr context )
{
	View::setContext( context );
	m_imageGadgets[0]->setContext( context );
	m_imageGadgets[1]->setContext( context );
}

void ImageView::plugSet( Gaffer::Plug *plug )
{
	if( plug == channelsPlug() )
	{
		ConstStringVectorDataPtr channelsData = channelsPlug()->getValue();
		const std::vector<std::string> &channels = channelsData->readable();
		ImageGadget::Channels c;
		for( size_t i = 0; i < std::min( channels.size(), (size_t)4 ); ++i )
		{
			c[i] = channels[i];
		}

		m_imageGadgets[0]->setChannels( c );
		m_imageGadgets[1]->setChannels( c );
	}
	else if( plug == compareModePlug() )
	{
		std::string compareMode = compareModePlug()->getValue();
		ImageGadget::BlendMode m = ImageGadget::BlendMode::Replace;

		bool compareEnabled = true;

		if( compareMode == "" )
		{
			compareEnabled = false;
			m = ImageGadget::BlendMode::Replace;
		}
		else if( compareMode == "replace" )
		{
			m = ImageGadget::BlendMode::Replace;
		}
		else if( compareMode == "over" )
		{
			m = ImageGadget::BlendMode::Over;
		}
		else if( compareMode == "under" )
		{
			m = ImageGadget::BlendMode::Under;
		}
		else if( compareMode == "difference" )
		{
			m = ImageGadget::BlendMode::Difference;
		}
		else if( compareMode == "sideBySide" )
		{
			m = ImageGadget::BlendMode::Replace;
		}

		m_imageGadgets[1]->setVisible( compareEnabled );

		m_imageGadgets[0]->setBlendMode( m );

		setWipeActive( compareMode != "" && compareWipePlug()->getValue() );

		getChild( "displayTransform" )->getChild<BoolPlug>( "absolute" )->setValue(
			m == ImageGadget::BlendMode::Difference
		);
	}
	else if( plug == compareWipePlug() )
	{
		setWipeActive( compareModePlug()->getValue() != "" && compareWipePlug()->getValue() );
	}
	else if( plug == compareCatalogueOutputPlug() )
	{
		m_comparisonSelect->variablesPlug()->getChild<NameValuePlug>( 0 )->enabledPlug()->setValue( compareCatalogueOutputPlug()->getValue() != "" );
	}
	else if( plug == getChild( "displayTransform" )->getChild( "soloChannel" ) )
	{
		const int soloChannel = static_cast<IntPlug *>( plug )->getValue();
		m_imageGadgets[0]->setSoloChannel( soloChannel );
		m_imageGadgets[1]->setSoloChannel( soloChannel );
	}
}

void ImageView::setWipeActive( bool active )
{
	if( active && !m_wipeHandle->getVisible() )
	{
		// We're turning on the Wipe.
		// Check if it has a reasonable position

		Box3f b = m_imageGadgets[0]->bound();
		V2f dir = m_wipeHandle->getDirection();
		V2f pos = m_wipeHandle->getPosition();
		float proj1 = ( V2f( b.min.x, b.min.y ) - pos ).dot( dir );
		float proj2 = ( V2f( b.min.x, b.max.y ) - pos ).dot( dir );
		float proj3 = ( V2f( b.max.x, b.min.y ) - pos ).dot( dir );
		float proj4 = ( V2f( b.max.x, b.max.y ) - pos ).dot( dir );

		float minProj = std::min( std::min( proj1, proj2 ), std::min( proj3, proj4 ) );
		float maxProj = std::max( std::max( proj1, proj2 ), std::max( proj3, proj4 ) );

		if( minProj * maxProj >= 0 )
		{
			// We don't have image on both sides of the wipe, so it isn't positioned usefully.
			// Reset the wipe position
			m_wipeHandle->setDirection( V2f( 1.0f, 0.0f ) );
			V3f center = 0.5f * ( b.min + b.max );
			m_wipeHandle->setPosition( V2f( center.x, center.y ) );
		}
	}

	m_wipeHandle->setVisible( active );
}


bool ImageView::keyPress( const GafferUI::KeyEvent &event )
{
	if( event.key == "F" && !event.modifiers )
	{
		const Box3f b = m_imageGadgets[0]->bound();
		if( !b.isEmpty() && viewportGadget()->getCameraEditable() )
		{
			viewportGadget()->frame( b );
			return true;
		}
	}
	else if( event.key == "Home" && !event.modifiers )
	{
		V2i viewport = viewportGadget()->getViewport();
		V3f halfViewportSize(viewport.x / 2, viewport.y / 2, 0);
		V3f imageCenter = m_imageGadgets[0]->bound().center();
		viewportGadget()->frame(
			Box3f(
				V3f(imageCenter.x - halfViewportSize.x, imageCenter.y - halfViewportSize.y, 0),
				V3f(imageCenter.x + halfViewportSize.x, imageCenter.y + halfViewportSize.y, 0)
			)
		);
		return true;
	}
	else if( event.key == "Escape" )
	{
		m_imageGadgets[0]->setPaused( true );
	}

	return false;
}

void ImageView::preRender()
{
	V3f comparisonScale( 1.0f );
	V3f comparisonTranslate( 0.0f );
	if( compareMatchDisplayWindowsPlug()->getValue() )
	{
		Imath::Box3f mainBound = m_imageGadgets[0]->bound();
		Imath::Box3f compareBound = m_imageGadgets[1]->bound();
		float s = mainBound.size().x / compareBound.size().x;
		comparisonScale = V3f( s, s, 1.0f );
		comparisonTranslate = mainBound.center() - compareBound.center() * comparisonScale;
		Imath::M44f m;
		m.translate( comparisonTranslate );
		m.scale( comparisonScale );
		m_imageGadgets[1]->setTransform( m );
	}
	else
	{
		m_imageGadgets[1]->setTransform( Imath::M44f() );
	}

	V2f scale0( 1.0f / pixelAspectFromImageGadget( m_imageGadgets[0].get() ), 1.0f );
	m_imageGadgets[0]->setWipeEnabled( m_wipeHandle->getVisible() );
	m_imageGadgets[0]->setWipePosition( m_wipeHandle->getPosition() * scale0 );
	m_imageGadgets[0]->setWipeAngle(
		atan2f( m_wipeHandle->getDirection()[1] * scale0.x, m_wipeHandle->getDirection()[0] * scale0.y ) * 180.0f / M_PI
	);

	if( m_wipeHandle->getVisible() && m_imageGadgets[0]->getBlendMode() == ImageGadget::BlendMode::Replace )
	{
		V2f scale1( 1.0f / ( comparisonScale.x * pixelAspectFromImageGadget( m_imageGadgets[1].get() ) ), 1.0f / comparisonScale.y );
		m_imageGadgets[1]->setWipeEnabled( true );
		m_imageGadgets[1]->setWipePosition( ( m_wipeHandle->getPosition() - V2f( comparisonTranslate.x, comparisonTranslate.y ) ) * scale1 );
		m_imageGadgets[1]->setWipeAngle(
			atan2f( -m_wipeHandle->getDirection()[1] * scale1.x, -m_wipeHandle->getDirection()[0] * scale1.y ) * 180.0f / M_PI
		);
	}
	else
	{
		m_imageGadgets[1]->setWipeEnabled( false );
	}

	if( m_framed )
	{
		return;
	}

	const Box3f b = m_imageGadgets[0]->bound();
	if( b.isEmpty() )
	{
		return;
	}

	viewportGadget()->frame( b );
	m_framed = true;
}
