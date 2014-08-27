//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, John Haddon. All rights reserved.
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

#include "IECore/NullObject.h"

#include "GafferUI/Handle.h"
#include "GafferUI/Style.h"
#include "GafferUI/ViewportGadget.h"

using namespace Imath;
using namespace IECore;
using namespace GafferUI;

IE_CORE_DEFINERUNTIMETYPED( Handle );

Handle::Handle( Type type )
	:	Gadget( defaultName<Handle>() ), m_type( type ), m_hovering( false )
{
	enterSignal().connect( boost::bind( &Handle::enter, this ) );
	leaveSignal().connect( boost::bind( &Handle::leave, this ) );

	buttonPressSignal().connect( boost::bind( &Handle::buttonPress, this, ::_2 ) );
	dragBeginSignal().connect( boost::bind( &Handle::dragBegin, this, ::_2 ) );
	dragEnterSignal().connect( boost::bind( &Handle::dragEnter, this, ::_2 ) );
}

Handle::~Handle()
{
}

void Handle::setType( Type type )
{
	if( type == m_type )
	{
		return;
	}

	m_type = type;
	renderRequestSignal()( this );
}

Handle::Type Handle::getType() const
{
	return m_type;
}

float Handle::dragOffset( const DragDropEvent &event ) const
{
	return absoluteDragOffset( event ) - m_dragBeginOffset;
}

Imath::Box3f Handle::bound() const
{
	switch( m_type )
	{
		case TranslateX :
			return Box3f( V3f( 0 ), V3f( 1, 0, 0 ) );
		case TranslateY :
			return Box3f( V3f( 0 ), V3f( 0, 1, 0 ) );
		case TranslateZ :
			return Box3f( V3f( 0 ), V3f( 0, 0, 1 ) );
	};

	return Box3f();
}

void Handle::doRender( const Style *style ) const
{
	Style::State state = getHighlighted() || m_hovering ? Style::HighlightedState : Style::NormalState;

	switch( m_type )
	{
		case TranslateX :
			style->renderTranslateHandle( 0, state );
			break;
		case TranslateY :
			style->renderTranslateHandle( 1, state );
			break;
		case TranslateZ :
			style->renderTranslateHandle( 2, state );
			break;
	}
}

void Handle::enter()
{
	m_hovering = true;
	renderRequestSignal()( this );
}

void Handle::leave()
{
	m_hovering = false;
	renderRequestSignal()( this );
}

bool Handle::buttonPress( const ButtonEvent &event )
{
	return event.buttons == ButtonEvent::Left;
}

IECore::RunTimeTypedPtr Handle::dragBegin( const DragDropEvent &event )
{
	// store the line of our handle in world space.
	V3f handle( 0.0f );
	handle[m_type] = 1.0f;

	m_dragHandleWorld = LineSegment3f(
		V3f( 0 ) * fullTransform(),
		handle * fullTransform()
	);

	m_dragBeginOffset = absoluteDragOffset( event );

	return IECore::NullObject::defaultNullObject();
}

bool Handle::dragEnter( const DragDropEvent &event )
{
	return event.sourceGadget == this;
}

float Handle::absoluteDragOffset( const DragDropEvent &event ) const
{
	const ViewportGadget *viewport = ancestor<ViewportGadget>();

	// Project the mouse position back into raster space.
	const V2f rasterP = viewport->gadgetToRasterSpace( event.line.p0, this );

	// Project our stored world space handle into raster space too.
	const LineSegment2f rasterHandle(
		viewport->worldToRasterSpace( m_dragHandleWorld.p0 ),
		viewport->worldToRasterSpace( m_dragHandleWorld.p1 )
	);

	// Find the closest point to the mouse on the handle in raster space.
	// We use Imath::Line rather than IECore::LineSegment because we want
	// to treat the handle as infinitely long. Unfortunately, there is no
	// Line2f so we must convert to a Line3f.
	const Line3f rasterHandle3(
		V3f( rasterHandle.p0.x, rasterHandle.p0.y, 0 ),
		V3f( rasterHandle.p1.x, rasterHandle.p1.y, 0 )
	);

	const V3f rasterClosestPoint = rasterHandle3.closestPointTo( V3f( rasterP.x, rasterP.y, 0 ) );

	// Project the raster point back into the world, and find the point
	// where it intersects the handle in 3d. Again, we convert to Line
	// rather than LineSegment because we want to treat our handle as
	// infinite.

	const LineSegment3f worldClosestLine = viewport->rasterToWorldSpace( V2f( rasterClosestPoint.x, rasterClosestPoint.y ) );

	const V3f worldClosestPoint =
		Line3f( m_dragHandleWorld.p0, m_dragHandleWorld.p1 ).closestPointTo(
			Line3f( worldClosestLine.p0, worldClosestLine.p1 )
		);

	return worldClosestPoint[m_type];
}
