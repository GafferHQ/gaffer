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

#include "GafferUI/Handle.h"

#include "GafferUI/Style.h"
#include "GafferUI/ViewportGadget.h"

#include "IECore/Export.h"
#include "IECore/NullObject.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "OpenEXR/ImathLine.h"
#include "OpenEXR/ImathPlane.h"
IECORE_POP_DEFAULT_VISIBILITY

#include "OpenEXR/ImathMatrixAlgo.h"
#include "OpenEXR/ImathVecAlgo.h"

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace GafferUI;

//////////////////////////////////////////////////////////////////////////
// Handle
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Handle );

Handle::Handle( const std::string &name )
	:	Gadget( name ), m_hovering( false ), m_rasterScale( 0.0f ), m_visibleOnHover( false )
{
	enterSignal().connect( boost::bind( &Handle::enter, this ) );
	leaveSignal().connect( boost::bind( &Handle::leave, this ) );

	buttonPressSignal().connect( boost::bind( &Handle::buttonPress, this, ::_2 ) );
	dragBeginSignal().connect( boost::bind( &Handle::dragBeginInternal, this, ::_2 ) );
	dragEnterSignal().connect( boost::bind( &Handle::dragEnter, this, ::_2 ) );
}

Handle::~Handle()
{
}

void Handle::setRasterScale( float rasterScale )
{
	if( rasterScale == m_rasterScale )
	{
		return;
	}

	m_rasterScale = rasterScale;
	dirty( DirtyType::Render );
}

float Handle::getRasterScale() const
{
	return m_rasterScale;
}

void Handle::setVisibleOnHover( bool visibleOnHover )
{
	if( visibleOnHover == m_visibleOnHover )
	{
		return;
	}

	m_visibleOnHover = visibleOnHover;
	dirty( DirtyType::Render );
}

bool Handle::getVisibleOnHover() const
{
	return m_visibleOnHover;
}

Imath::Box3f Handle::bound() const
{
	// Having a raster scale makes our bound somewhat meaningless
	// anyway, so save the derived classes some trouble and return
	// something fairly arbitrary.
	return Box3f( V3f( -1 ), V3f( 1 ) );
}

void Handle::renderLayer( Layer layer, const Style *style, RenderReason reason ) const
{
	if( m_visibleOnHover )
	{
		if( !enabled() || (!m_hovering && !isSelectionRender( reason ) ) )
		{
			return;
		}
	}

	glPushMatrix();
	const V3f scale = rasterScaleFactor();
	glScalef( scale.x, scale.y, scale.z );

	Style::State state = getHighlighted() || m_hovering ? Style::HighlightedState : Style::NormalState;
	state = !enabled() ? Style::DisabledState : state;

	renderHandle( style, state );

	glPopMatrix();
}

unsigned Handle::layerMask() const
{
	return (unsigned)Layer::MidFront;
}

Imath::Box3f Handle::renderBound() const
{
	// Having a raster scale makes our bound somewhat meaningless
	Box3f b;
	b.makeInfinite();
	return b;
}

Imath::V3f Handle::rasterScaleFactor() const
{
	if( m_rasterScale <= 0.0f )
	{
		return V3f( 1 );
	}

	// We want our handles to be a constant length in
	// raster space. Two things get in our way :
	//
	//  1. The distance from camera.
	//  2. Scaling applied to our transform.

	const ViewportGadget *viewport = ancestor<ViewportGadget>();
	const M44f fullTransform = this->fullTransform();

	// Scale factor to address 1.

	const M44f cameraToGadget = viewport->getCameraTransform() * fullTransform.inverse();
	V3f cameraUpInGadgetSpace = V3f( 0, 1, 0 );
	cameraToGadget.multDirMatrix( cameraUpInGadgetSpace, cameraUpInGadgetSpace );

	const V2f p1 = viewport->gadgetToRasterSpace( V3f( 0.0f ), this );
	const V2f p2 = viewport->gadgetToRasterSpace( cameraUpInGadgetSpace, this );
	const float s1 = m_rasterScale / ( p1 - p2 ).length();

	// Scale factor to address 2. We use fabs because we don't
	// want to lose the change of orientation brought about by
	// negative scaling.
	V3f s2;
	extractScaling( fullTransform, s2 );
	s2 = V3f( 1.0f / fabs( s2.x ), 1.0f / fabs( s2.y ), 1.0f / fabs( s2.z ) );

	return s1 * s2;
}

void Handle::enter()
{
	m_hovering = true;
	dirty( DirtyType::Render );
}

void Handle::leave()
{
	m_hovering = false;
	dirty( DirtyType::Render );
}

bool Handle::buttonPress( const ButtonEvent &event )
{
	return event.buttons == ButtonEvent::Left;
}

IECore::RunTimeTypedPtr Handle::dragBeginInternal( const DragDropEvent &event )
{
	dragBegin( event );
	return IECore::NullObject::defaultNullObject();
}

bool Handle::dragEnter( const DragDropEvent &event )
{
	return event.sourceGadget == this;
}

//////////////////////////////////////////////////////////////////////////
// LinearDrag
//////////////////////////////////////////////////////////////////////////

Handle::LinearDrag::LinearDrag( bool processModifiers )
	:	m_gadget( nullptr ),
		m_worldLine( V3f( 0 ), V3f( 1, 0, 0 ) ),
		m_dragBeginPosition( 0 ),
		m_processModifiers( processModifiers ),
		m_preciseMotionEnabled( false ),
		m_preciseMotionOrigin( 0 )
{
}

Handle::LinearDrag::LinearDrag( const Gadget *gadget, const Imath::V2f &line, const DragDropEvent &dragBeginEvent, bool processModifiers )
	:   m_gadget( gadget ),
		m_processModifiers( processModifiers ),
		m_preciseMotionEnabled( false )
{
	// We need an axis in world space, derived from the supplied camera space
	// line, normalized in gadget space...(!)
	const M44f gadgetTransform = gadget->fullTransform();

	const ViewportGadget *viewport = gadget->ancestor<ViewportGadget>();
	const M44f cameraToGadget = viewport->getCameraTransform() * gadgetTransform.inverse();

	V3f gadgetAxis;
	cameraToGadget.multDirMatrix( V3f( line.x, line.y, 0 ), gadgetAxis );
	gadgetAxis.normalize();

	V3f worldAxis;
	gadgetTransform.multDirMatrix( gadgetAxis, worldAxis );

	const V3f worldOrigin =  V3f( 0 ) * gadgetTransform;
	m_worldLine = LineSegment3f( worldOrigin, worldOrigin + worldAxis );

	m_dragBeginPosition = updatedPosition( dragBeginEvent );

	m_preciseMotionEnabled = dragBeginEvent.modifiers & ModifiableEvent::Shift;
	m_preciseMotionOrigin = m_dragBeginPosition;
}

Handle::LinearDrag::LinearDrag( const Gadget *gadget, const IECore::LineSegment3f &line, const DragDropEvent &dragBeginEvent, bool processModifiers )
	:	m_gadget( gadget ),
		m_worldLine(
			line.p0 * m_gadget->fullTransform(),
			line.p1 * m_gadget->fullTransform()
		),
		m_processModifiers( processModifiers ),
		m_preciseMotionEnabled( false )
{
	m_dragBeginPosition = updatedPosition( dragBeginEvent );

	m_preciseMotionEnabled = dragBeginEvent.modifiers & ModifiableEvent::Shift;
	m_preciseMotionOrigin = m_dragBeginPosition;
}

float Handle::LinearDrag::startPosition() const
{
	return m_dragBeginPosition;
}

float Handle::LinearDrag::updatedPosition( const DragDropEvent &event )
{
	const ViewportGadget *viewport = m_gadget->ancestor<ViewportGadget>();

	// Project the mouse position back into raster space.
	const V2f rasterP = viewport->gadgetToRasterSpace( event.line.p1, m_gadget );

	// Project our stored world space handle into raster space too.
	const LineSegment2f rasterHandle(
		viewport->worldToRasterSpace( m_worldLine.p0 ),
		viewport->worldToRasterSpace( m_worldLine.p1 )
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
		Line3f( m_worldLine.p0, m_worldLine.p1 ).closestPointTo(
			Line3f( worldClosestLine.p0, worldClosestLine.p1 )
		);

	float position = m_worldLine.direction().dot( worldClosestPoint - m_worldLine.p0 ) / m_worldLine.length2();

	if( m_processModifiers )
	{
		// Factor in precision motion, in which we scale down motion after the
		// key was held by a factor of 10, which means relative to the position
		// at that time.
		//
		const bool shiftHeld = event.modifiers & ModifiableEvent::Shift;

		// If this is the first time we've seen an event where precise motion is
		// enabled, then we need to store the position at this time.
		if( !m_preciseMotionEnabled && shiftHeld )
		{
			m_preciseMotionOrigin = position;
		}
		m_preciseMotionEnabled = shiftHeld;

		if( m_preciseMotionEnabled )
		{
			position = m_preciseMotionOrigin + ( ( position - m_preciseMotionOrigin ) * 0.1f );
		}
	}

	return position;
}

//////////////////////////////////////////////////////////////////////////
// PlanarDrag
//////////////////////////////////////////////////////////////////////////

Handle::PlanarDrag::PlanarDrag( bool processModifiers )
	:	m_gadget( nullptr ),
		m_processModifiers( processModifiers ),
		m_preciseMotionEnabled( false ),
		m_preciseMotionOrigin( 0 )
{
}

Handle::PlanarDrag::PlanarDrag( const Gadget *gadget, const DragDropEvent &dragBeginEvent, bool processModifiers )
	:	m_processModifiers( processModifiers ),
		m_preciseMotionEnabled( false )
{
	const ViewportGadget *viewport = gadget->ancestor<ViewportGadget>();
	const M44f cameraTransform = viewport->getCameraTransform();
	const M44f gadgetInverseTransform = gadget->fullTransform().inverse();
	const M44f cameraToGadget = cameraTransform * gadgetInverseTransform;

	V3f gadgetAxis0;
	V3f gadgetAxis1;
	cameraToGadget.multDirMatrix( V3f( 1, 0, 0 ), gadgetAxis0 );
	cameraToGadget.multDirMatrix( V3f( 0, 1, 0 ), gadgetAxis1 );
	gadgetAxis0.normalize();
	gadgetAxis1.normalize();

	init(
		gadget,
		V3f( 0 ),
		gadgetAxis0,
		gadgetAxis1,
		dragBeginEvent
	);
}

Handle::PlanarDrag::PlanarDrag( const Gadget *gadget, const Imath::V3f &origin, const Imath::V3f &axis0, const Imath::V3f &axis1, const DragDropEvent &dragBeginEvent, bool processModifiers )
	:	m_processModifiers( processModifiers ),
		m_preciseMotionEnabled( false )
{
	init( gadget, origin, axis0, axis1, dragBeginEvent );
}

const Imath::V3f &Handle::PlanarDrag::axis0() const
{
	return m_axis0;
}

const Imath::V3f &Handle::PlanarDrag::axis1() const
{
	return m_axis1;
}

Imath::V2f Handle::PlanarDrag::startPosition() const
{
	return m_dragBeginPosition;
}

Imath::V2f Handle::PlanarDrag::updatedPosition( const DragDropEvent &event )
{
	Line3f worldLine(
		event.line.p0 * m_gadget->fullTransform(),
		event.line.p1 * m_gadget->fullTransform()
	);
	Plane3f worldPlane(
		m_worldOrigin,
		m_worldOrigin + m_worldAxis0,
		m_worldOrigin + m_worldAxis1
	);
	V3f worldIntersection( 0 );
	worldPlane.intersect( worldLine, worldIntersection );

	// Form coordinates in the plane by projecting onto each axis
	// and returning the length of the projection as a proportion
	// of the axis length.

	V2f position = V2f(
		m_worldAxis0.dot( worldIntersection - m_worldOrigin ) / m_worldAxis0.length2(),
		m_worldAxis1.dot( worldIntersection - m_worldOrigin ) / m_worldAxis1.length2()
	);

	if( m_processModifiers )
	{
		const bool shiftHeld = event.modifiers & ModifiableEvent::Shift;
		// If this is the first time we've seen an event where precise motion is
		// enabled, then we need to store the position at this time.
		if( !m_preciseMotionEnabled && shiftHeld )
		{
			m_preciseMotionOrigin = position;
		}
		m_preciseMotionEnabled = shiftHeld;

		if( m_preciseMotionEnabled )
		{
			position = m_preciseMotionOrigin + ( ( position - m_preciseMotionOrigin ) * 0.1f );
		}
	}

	return position;
}

void Handle::PlanarDrag::init( const Gadget *gadget, const Imath::V3f &origin, const Imath::V3f &axis0, const Imath::V3f &axis1, const DragDropEvent &dragBeginEvent )
{
	m_axis0 = axis0;
	m_axis1 = axis1;
	m_gadget = gadget;
	const M44f transform = gadget->fullTransform();
	m_worldOrigin = origin * transform;
	transform.multDirMatrix( axis0, m_worldAxis0 );
	transform.multDirMatrix( axis1, m_worldAxis1 );

	m_dragBeginPosition = updatedPosition( dragBeginEvent );

	m_preciseMotionEnabled = dragBeginEvent.modifiers & ModifiableEvent::Shift;
	m_preciseMotionOrigin = m_dragBeginPosition;
}


//////////////////////////////////////////////////////////////////////////
// AngularDrag
//////////////////////////////////////////////////////////////////////////

Handle::AngularDrag::AngularDrag( bool processModifiers )
	:	m_rotation( 0.0f ),
		m_dragBeginRotation( 0.0f ),
		m_processModifiers( processModifiers ),
		m_preciseMotionEnabled( false )
{
	m_drag = PlanarDrag( false );
}

Handle::AngularDrag::AngularDrag( const Gadget *gadget, const Imath::V3f &origin, const Imath::V3f &axis0, const Imath::V3f axis1, const DragDropEvent &dragBeginEvent, bool processModifiers )
	:	m_rotation( 0.0f ),
		m_axis0( axis0 ),
		m_axis1( axis1 ),
		m_processModifiers( processModifiers ),
		m_preciseMotionEnabled( false )
{
	// We need to negate this, or rotation is opposite to the mouse movement direction
	V3f planeAxis0 = -axis0.cross( axis1 );
	// Disable modifier processing as we'll do our own precision mode in angle space
	m_drag = PlanarDrag( gadget, origin, planeAxis0, axis1, dragBeginEvent, false );

	m_dragBeginRotation = closestRotation( m_drag.startPosition(), m_rotation );

	m_preciseMotionEnabled = dragBeginEvent.modifiers & ModifiableEvent::Shift;
	m_preciseMotionOrigin = m_dragBeginRotation;
}


const Imath::V3f &Handle::AngularDrag::axis0() const
{
	return m_axis0;
}

const Imath::V3f &Handle::AngularDrag::axis1() const
{
	return m_axis1;
}

float Handle::AngularDrag::startRotation() const
{
	return m_dragBeginRotation;
}

float Handle::AngularDrag::updatedRotation( const DragDropEvent &event )
{
	// We can only recover an angle in the range -PI, PI from the 2d position
	// that our drag gives us, but we want to be able to support continuous
	// values and multiple revolutions. We need to store the un-modified rotation
	// such that we pick the closest rotation to the mouse itself.
	float rotation = closestRotation( m_drag.updatedPosition( event ), m_rotation );
	m_rotation = rotation;

	if( m_processModifiers )
	{
		const bool shiftHeld = event.modifiers & ModifiableEvent::Shift;
		// If this is the first time we've seen an event where precise motion is
		// enabled, then we need to store the position at this time.
		if( !m_preciseMotionEnabled && shiftHeld )
		{
			m_preciseMotionOrigin = rotation;
		}
		m_preciseMotionEnabled = shiftHeld;

		if( m_preciseMotionEnabled )
		{
			rotation = m_preciseMotionOrigin + ( ( rotation - m_preciseMotionOrigin ) * 0.1f );
		}
	}

	return rotation;
}

float Handle::AngularDrag::closestRotation( const V2f &p, float targetRotation )
{
	const float r = atan2( p.y, p.x );
	return Eulerf::angleMod( r - targetRotation ) + targetRotation;
}
