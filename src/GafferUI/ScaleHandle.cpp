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

IE_CORE_DEFINERUNTIMETYPED( ScaleHandle );

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
 	requestRender();
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

Imath::V3f ScaleHandle::scaling( const DragDropEvent &event ) const
{
	switch( m_axes )
	{
		case Style::X :
			return V3f(
				m_drag.position( event ) / m_drag.startPosition(),
				1,
				1
			);
		case Style::Y :
			return V3f(
				1,
				m_drag.position( event ) / m_drag.startPosition(),
				1
			);
		case Style::Z :
			return V3f(
				1,
				1,
				m_drag.position( event ) / m_drag.startPosition()
			);
		case Style::XY : {
			const float s = m_drag.position( event ) / m_drag.startPosition();
			return V3f( s, s, 1 );
		}
		case Style::XZ : {
			const float s = m_drag.position( event ) / m_drag.startPosition();
			return V3f( s, 1, s );
		}
		case Style::YZ : {
			const float s = m_drag.position( event ) / m_drag.startPosition();
			return V3f( 1, s, s );
		}
		case Style::XYZ : {
			const ViewportGadget *viewport = ancestor<ViewportGadget>();
			const V2f p = viewport->gadgetToRasterSpace( event.line.p1, this );
			const float d = (p.x - m_uniformDragStartPosition.x) / (float)viewport->getViewport().x;
			return V3f( 1.0f + d * 3.0f );
		}
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
		case Style::XYZ : {
			const ViewportGadget *viewport = ancestor<ViewportGadget>();
			m_uniformDragStartPosition = viewport->gadgetToRasterSpace( event.line.p1, this );
		}
	}
}
