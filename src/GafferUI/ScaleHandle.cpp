//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, John Haddon. All rights reserved.
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/ScaleHandle.h"

#include "GafferUI/ViewportGadget.h"

#include "IECore/Exception.h"

using namespace Imath;
using namespace IECore;
using namespace GafferUI;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( ScaleHandle );

ScaleHandle::ScaleHandle( Style::Axes axes )
	:	Handle( defaultName<ScaleHandle>() ), m_axes( Style::X )
{
	setAxes( axes );
}

ScaleHandle::~ScaleHandle()
{
}

void ScaleHandle::setAxes( Style::Axes axes )
{
	if( axes == m_axes )
	{
		return;
	}

	m_axes = axes;
	dirty( DirtyType::Render );
}

Style::Axes ScaleHandle::getAxes() const
{
	return m_axes;
}

Imath::V3i ScaleHandle::axisMask() const
{
	switch( m_axes )
	{
		case Style::X :
			return V3i( 1, 0, 0 );
		case Style::Y :
			return V3i( 0, 1, 0 );
		case Style::Z :
			return V3i( 0, 0, 1 );
		case Style::XY :
			return V3i( 1, 1, 0 );
		case Style::XZ :
			return V3i( 1, 0, 1 );
		case Style::YZ :
			return V3i( 0, 1, 1 );
		case Style::XYZ :
			return V3i( 1, 1, 1 );
		default :
			return V3i( 0 );
	}
}

Imath::V3f ScaleHandle::scaling( const DragDropEvent &event )
{
	float scale = 1;

	if( m_axes != Style::XYZ )
	{
		// When performing per-axis scale, the user has clicked and dragged a
		// handle. This means the start position is far enough away from the
		// origin that we can treat the click point as scale=1 and the gadget's
		// origin as scale=0.
		scale = m_drag.updatedPosition( event ) / m_drag.startPosition() - 1;
	}
	else
	{
		// When performing uniform scales, the handle is at the origin, so the
		// pattern we use above gets very twitchy. We instead need to treat the
		// click point as scale=1 and relative movement in +ve x as a scale
		// increase and anything in -ve x as a scale decrease. Coordinates are in
		// gadget-space, which does not scale by camera position. Normalize
		// by `rasterScaleFactor()` to prevent very large scaling when zoomed out
		// and small scaling when zoomed in.
		//
		// Note that using `rasterScaleFactor()` here works as long as the handle
		// transform is uniform, which is currently all cases. If that changes,
		// a more sophisticated scale factor may need to be used.
		scale = ( m_drag.updatedPosition( event ) - m_drag.startPosition() ) / rasterScaleFactor().x;
	}

	// snap
	if( event.modifiers & ButtonEvent::Control )
	{
		// Offset such that it behaves like round not floor.
		const float snapIncrement = event.modifiers & ButtonEvent::Shift ? 0.1f : 1.0f;
		const float snapOffset = snapIncrement * 0.5f;
		scale = scale - fmodf( scale - snapOffset, snapIncrement ) + snapOffset;
	}

	scale = 1 + scale;

	// guard against scaling to 0
	scale = scale == 0 ? 1 : scale;

	switch( m_axes )
	{
		case Style::X :
			return V3f( scale, 1, 1 );
		case Style::Y :
			return V3f( 1, scale, 1 );
		case Style::Z :
			return V3f( 1, 1, scale );
		case Style::XY :
			return V3f( scale, scale, 1 );
		case Style::XZ :
			return V3f( scale, 1, scale );
		case Style::YZ :
			return V3f( 1, scale, scale );
		case Style::XYZ :
			return V3f( scale );
		default :
			return V3f( 1 );
	}
}

void ScaleHandle::renderHandle( const Style *style, Style::State state ) const
{
	style->renderScaleHandle( m_axes, state );
}

void ScaleHandle::dragBegin( const DragDropEvent &event )
{
	switch( m_axes )
	{
		case Style::X :
			m_drag = LinearDrag( this, LineSegment3f( V3f( 0 ), V3f( 1, 0, 0 ) ), event );
			break;
		case Style::Y :
			m_drag = LinearDrag( this, LineSegment3f( V3f( 0 ), V3f( 0, 1, 0 ) ), event );
			break;
		case Style::Z :
			m_drag = LinearDrag( this, LineSegment3f( V3f( 0 ), V3f( 0, 0, 1 ) ), event );
			break;
		case Style::XY :
			m_drag = LinearDrag( this, LineSegment3f( V3f( 0 ), V3f( 1, 1, 0 ) ), event );
			break;
		case Style::XZ :
			m_drag = LinearDrag( this, LineSegment3f( V3f( 0 ), V3f( 1, 0, 1 ) ), event );
			break;
		case Style::YZ :
			m_drag = LinearDrag( this, LineSegment3f( V3f( 0 ), V3f( 0, 1, 1 ) ), event );
			break;
		case Style::XYZ :
			m_drag = LinearDrag( this, V2f( 1, 0 ), event );
	}
}
