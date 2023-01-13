//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, John Haddon. All rights reserved.
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

#include "GafferUI/RotateHandle.h"

#include "IECore/Exception.h"
#include "IECore/Export.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "OpenEXR/OpenEXRConfig.h"
#if OPENEXR_VERSION_MAJOR < 3
#include "OpenEXR/ImathEuler.h"
#include "OpenEXR/ImathMatrixAlgo.h"
#include "OpenEXR/ImathSphere.h"
#include "OpenEXR/ImathQuat.h"
#else
#include "Imath/ImathEuler.h"
#include "Imath/ImathMatrixAlgo.h"
#include "Imath/ImathSphere.h"
#include "Imath/ImathQuat.h"
#endif
IECORE_POP_DEFAULT_VISIBILITY

#include "boost/bind/bind.hpp"

#include <cmath>

using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace GafferUI;

//////////////////////////////////////////////////////////////////////////
// RotateHandle
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( RotateHandle );

RotateHandle::RotateHandle( Style::Axes axes )
	:	Handle( defaultName<RotateHandle>() ),
		m_axes( Style::X ),
		m_preciseMotionEnabled( false )
{
	setAxes( axes );
	dragMoveSignal().connect( boost::bind( &RotateHandle::dragMove, this, ::_2 ) );
	mouseMoveSignal().connect( boost::bind( &RotateHandle::mouseMove, this, ::_2 ) );
}

RotateHandle::~RotateHandle()
{
}

void RotateHandle::setAxes( Style::Axes axes )
{
	if( axes == m_axes )
	{
		return;
	}

	switch( axes )
	{
		case Style::X :
		case Style::Y :
		case Style::Z :
		case Style::XYZ :
			break;
		default :
			throw IECore::Exception( "Unsupported axes" );
	}

	m_axes = axes;
	dirty( DirtyType::Render );
}

Style::Axes RotateHandle::getAxes() const
{
	return m_axes;
}

Imath::V3i RotateHandle::axisMask() const
{
	switch( m_axes )
	{
		case Style::X :
			return V3i( 1, 0, 0 );
		case Style::Y :
			return V3i( 0, 1, 0 );
		case Style::Z :
			return V3i( 0, 0, 1 );
		case Style::XYZ :
			return V3i( 1, 1, 1 );
		default :
			// Checks in `setAxes()` prevent us getting here
			return V3i( 0 );
	}
}

Imath::Eulerf RotateHandle::rotation( const DragDropEvent &event )
{
	if( m_axes == Style::XYZ )
	{
		const LineSegment3f line = updatedLineFromEvent( event ) * fullTransform() * m_dragBeginWorldTransform.inverse();
		const M44f m = rotationMatrix( m_dragBeginPointOnSphere, pointOnSphere( line ) );
		Eulerf e; e.extract( m );

		return e;
	}

	float rotate = m_drag.updatedRotation( event ) - m_drag.startRotation();

	// snap
	if( event.modifiers & ButtonEvent::Control )
	{
		// Offset such that it behaves like round not floor.
		const float snapIncrement = event.modifiers & ButtonEvent::Shift ? ( M_PI / 60.0f ) : ( M_PI / 6.0f );
		const float snapOffset = snapIncrement * 0.5f;
		rotate = rotate - fmodf( rotate - snapOffset, snapIncrement ) + snapOffset;
	}

	switch( m_axes )
	{
		case Style::X :
			return Eulerf( V3f( rotate, 0, 0 ) );
		case Style::Y :
			return Eulerf( V3f( 0, rotate, 0 ) );
		case Style::Z :
			return Eulerf( V3f( 0, 0, rotate ) );
		default :
			// Checks in `setAxes()` prevent us getting here
			return Eulerf();
	}
}

void RotateHandle::renderHandle( const Style *style, Style::State state ) const
{
	style->renderRotateHandle( m_axes, state, m_highlightVector );
}

void RotateHandle::updatePreciseMotionState( const DragDropEvent &event )
{
	const bool shiftHeld = event.modifiers & ModifiableEvent::Shift;
	if( !m_preciseMotionEnabled && shiftHeld )
	{
		m_preciseMotionOriginLine = event.line;
	}
	m_preciseMotionEnabled = shiftHeld;
}

IECore::LineSegment3f RotateHandle::updatedLineFromEvent( const DragDropEvent &event ) const
{
	LineSegment3f line = event.line;

	if( m_preciseMotionEnabled )
	{
		// We interpolate the mouse position, not the resulting rotation to
		// ensure we don't get clamped by pointOnSphere once the actual mouse
		// has moved way away from the handle. The compromise is a non-linear
		// rotation response, but we have that anyway as the mouse is on a
		// plane to start with.
		const V3f dP0 = ( event.line.p0 - m_preciseMotionOriginLine.p0 ) * 0.1f;
		const V3f dP1 = ( event.line.p1 - m_preciseMotionOriginLine.p1 ) * 0.1f;
		line = LineSegment3f(
			V3f( m_preciseMotionOriginLine.p0 + dP0 ),
			V3f( m_preciseMotionOriginLine.p1 + dP1 )
		);
	}

	return line;
}

void RotateHandle::dragBegin( const DragDropEvent &event )
{
	switch( m_axes )
	{
		case Style::X :
			m_drag = AngularDrag( this, V3f( 0 ), V3f( 1, 0, 0 ), V3f( 0, 0, 1 ), event );
			m_rotation = m_drag.startRotation();
			break;
		case Style::Y :
			m_drag = AngularDrag( this, V3f( 0 ), V3f( 0, 1, 0 ), V3f( 1, 0, 0 ), event );
			m_rotation = m_drag.startRotation();
			break;
		case Style::Z :
			m_drag = AngularDrag( this, V3f( 0 ), V3f( 0, 0, 1 ), V3f( 0, 1, 0 ), event );
			m_rotation = m_drag.startRotation();
			break;
		case Style::XYZ :
			m_dragBeginWorldTransform = fullTransform();
			m_dragBeginPointOnSphere = pointOnSphere( event.line );
			m_preciseMotionEnabled = false;
			m_preciseMotionOriginLine = event.line;
			updatePreciseMotionState( event );
			break;
		default :
			// Checks in `setAxes()` prevent us getting here
			break;
	}
}

bool RotateHandle::dragMove( const DragDropEvent &event )
{
	if( m_axes == Style::XYZ )
	{
		updatePreciseMotionState( event );
		m_highlightVector = pointOnSphere( updatedLineFromEvent( event ) );
		dirty( DirtyType::Render );
	}
	else
	{
		m_rotation = m_drag.updatedRotation( event );
	}
	return false;
}

bool RotateHandle::mouseMove( const ButtonEvent &event )
{
	m_highlightVector = pointOnSphere( event.line );
	dirty( DirtyType::Render );
	return true;
}

Imath::V3f RotateHandle::pointOnSphere( const IECore::LineSegment3f &line ) const
{
	const LineSegment3f scaledLine = line * M44f().scale( V3f( 1 ) / rasterScaleFactor() );
	const Imath::Sphere3f sphere( V3f( 0 ), 1.0f );
	V3f result;
	if( !sphere.intersect( Line3f( scaledLine.p0, scaledLine.p1 ), result ) )
	{
		result = scaledLine.closestPointTo( V3f( 0 ) );
		result.normalize();
	}
	return result;
}
