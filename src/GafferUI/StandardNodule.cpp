//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/StandardNodule.h"

#include "GafferUI/ConnectionGadget.h"
#include "GafferUI/GraphGadget.h"
#include "GafferUI/NodeGadget.h"
#include "GafferUI/PlugAdder.h"
#include "GafferUI/Pointer.h"
#include "GafferUI/Style.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/Plug.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/UndoScope.h"

#include "IECoreGL/Selector.h"

#include "IECore/AngleConversion.h"

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace std;
using namespace Imath;
using namespace Gaffer;
using namespace GafferUI;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( StandardNodule );

Nodule::NoduleTypeDescription<StandardNodule> StandardNodule::g_noduleTypeDescription( Gaffer::Plug::staticTypeId() );

static IECore::InternedString g_colorKey( "nodule:color" );
static IECore::InternedString g_labelKey( "noduleLayout:label" );

StandardNodule::StandardNodule( Gaffer::PlugPtr plug )
	:	Nodule( plug ), m_labelVisible( false ), m_draggingConnection( false )
{
	enterSignal().connect( boost::bind( &StandardNodule::enter, this, ::_1, ::_2 ) );
	leaveSignal().connect( boost::bind( &StandardNodule::leave, this, ::_1, ::_2 ) );
	buttonPressSignal().connect( boost::bind( &StandardNodule::buttonPress, this, ::_1,  ::_2 ) );
	dragBeginSignal().connect( boost::bind( &StandardNodule::dragBegin, this, ::_1, ::_2 ) );
	dragMoveSignal().connect( boost::bind( &StandardNodule::dragMove, this, ::_1, ::_2 ) );
	dragEnterSignal().connect( boost::bind( &StandardNodule::dragEnter, this, ::_1, ::_2 ) );
	dragLeaveSignal().connect( boost::bind( &StandardNodule::dragLeave, this, ::_1, ::_2 ) );
	dragEndSignal().connect( boost::bind( &StandardNodule::dragEnd, this, ::_1, ::_2 ) );

	dropSignal().connect( boost::bind( &StandardNodule::drop, this, ::_1, ::_2 ) );

	Metadata::plugValueChangedSignal( plug->node() ).connect( boost::bind( &StandardNodule::plugMetadataChanged, this, ::_1, ::_2 ) );

	updateUserColor();
}

StandardNodule::~StandardNodule()
{
}

void StandardNodule::setLabelVisible( bool labelVisible )
{
	if( labelVisible == m_labelVisible )
	{
		return;
	}
	m_labelVisible = labelVisible;
	dirty( DirtyType::Render );
}

bool StandardNodule::getLabelVisible() const
{
	return m_labelVisible;
}

Imath::Box3f StandardNodule::bound() const
{
	return Box3f( V3f( -0.5, -0.5, 0 ), V3f( 0.5, 0.5, 0 ) );
}

bool StandardNodule::canCreateConnection( const Gaffer::Plug *endpoint ) const
{
	const Gaffer::Plug *localPlug = plug();

	if( localPlug->node() == endpoint->node() || localPlug->direction() == endpoint->direction() )
	{
		return false;
	}

	if( localPlug->direction() == Gaffer::Plug::Direction::In )
	{
		return localPlug->acceptsInput( endpoint );
	}
	else
	{
		return endpoint->acceptsInput( localPlug );
	}
}

void StandardNodule::updateDragEndPoint( const Imath::V3f position, const Imath::V3f &tangent )
{
	m_dragPosition = position;
	m_dragTangent = tangent;
	m_draggingConnection = true;
	dirty( DirtyType::Render );
}

void StandardNodule::createConnection( Gaffer::Plug *endpoint )
{
	Gaffer::Plug *localPlug = plug();

	if( localPlug->direction() == Gaffer::Plug::Direction::In )
	{
		localPlug->setInput( endpoint );
	}
	else
	{
		endpoint->setInput( localPlug );
	}
}

bool StandardNodule::hasLayer( Layer layer ) const
{
	if( children().size() )
	{
		return true;
	}

	switch( layer )
	{
		case GraphLayer::Connections :
			return m_draggingConnection;
		case GraphLayer::Nodes :
			return !getHighlighted();
		case GraphLayer::Highlighting :
			return getHighlighted();
		case GraphLayer::Overlay :
			return m_labelVisible && !IECoreGL::Selector::currentSelector();
		default :
			return false;
	}
}

void StandardNodule::doRenderLayer( Layer layer, const Style *style ) const
{
	switch( layer )
	{

		case GraphLayer::Connections :

			if( m_draggingConnection && !IECoreGL::Selector::currentSelector() )
			{
				V3f srcTangent( 0.0f, 1.0f, 0.0f );
				if( const NodeGadget *nodeGadget = ancestor<NodeGadget>() )
				{
					srcTangent = nodeGadget->connectionTangent( this );
				}
				style->renderConnection( V3f( 0 ), srcTangent, m_dragPosition, m_dragTangent, Style::HighlightedState );
			}
			break;

		case GraphLayer::Nodes :

			if( !getHighlighted() )
			{
				style->renderNodule( 0.5f, Style::NormalState, m_userColor.get_ptr() );
			}
			break;

		case GraphLayer::Highlighting :

			if( getHighlighted() )
			{
				style->renderNodule( 1.0f, Style::HighlightedState, m_userColor.get_ptr() );
			}
			break;

		case GraphLayer::Overlay :

			if( m_labelVisible && !IECoreGL::Selector::currentSelector() )
			{
				renderLabel( style );
			}
			break;

		default :

			break;

	}

	// if the nodule isn't highlighted it will be drawn in the normal, non-overlayed manner
}

void StandardNodule::renderLabel( const Style *style ) const
{
	const NodeGadget *nodeGadget = ancestor<NodeGadget>();
	if( !nodeGadget )
	{
		return;
	}

	const std::string *label = nullptr;
	IECore::ConstStringDataPtr labelData = Metadata::value<IECore::StringData>( plug(), g_labelKey );
	if( labelData )
	{
		label = &labelData->readable();
	}
	else
	{
		label = &plug()->getName().string();
	}

	// we rotate the label based on the angle the connection exits the node at.
	V3f tangent = nodeGadget->connectionTangent( this );
	float theta = IECore::radiansToDegrees( atan2f( tangent.y, tangent.x ) );

	// but we don't want the text to be vertical, so we bend it away from the
	// vertical axis.
	if( ( theta > 0.0f && theta < 90.0f ) || ( theta < 0.0f && theta >= -90.0f ) )
	{
		theta = sign( theta ) * lerp( 0.0f, 45.0f, fabs( theta ) / 90.0f );
	}
	else
	{
		theta = sign( theta ) * lerp( 135.0f, 180.0f, (fabs( theta ) - 90.0f) / 90.0f );
	}

	// we also don't want the text to be upside down, so we correct the rotation
	// if that would be the case.
	Box3f labelBound = style->textBound( Style::LabelText, *label );
	V2f anchor( labelBound.min.x - 1.0f, labelBound.center().y );

	if( theta > 90.0f || theta < -90.0f )
	{
		theta = theta - 180.0f;
		anchor.x = labelBound.max.x + 1.0f;
	}

	// now we can actually do the rendering.
	glPushMatrix();

	if( getHighlighted() )
	{
		glScalef( 1.2, 1.2, 1.2 );
	}

	glRotatef( theta, 0, 0, 1.0f );
	glTranslatef( -anchor.x, -anchor.y, 0.0f );

	style->renderText( Style::LabelText, *label );

	glPopMatrix();
}

void StandardNodule::enter( GadgetPtr gadget, const ButtonEvent &event )
{
	setHighlighted( true );
}

void StandardNodule::leave( GadgetPtr gadget, const ButtonEvent &event )
{
	setHighlighted( false );
}

bool StandardNodule::buttonPress( GadgetPtr gadget, const ButtonEvent &event )
{
	// we handle the button press so we can get the dragBegin event,
	// ignoring right clicks so that they can be used for context sensitive
	// menus in GraphEditor.py.
	if( event.buttons & ( ButtonEvent::LeftMiddle ) )
	{
		return true;
	}
	return false;
}

IECore::RunTimeTypedPtr StandardNodule::dragBegin( GadgetPtr gadget, const ButtonEvent &event )
{
	dirty( DirtyType::Render );
	if( event.buttons == ButtonEvent::Middle )
	{
		GafferUI::Pointer::setCurrent( "plug" );
	}
	return plug();
}

bool StandardNodule::dragEnter( GadgetPtr gadget, const DragDropEvent &event )
{
	if( MetadataAlgo::readOnly( plug() ) )
	{
		return false;
	}

	if( event.buttons != DragDropEvent::Left )
	{
		// we only accept drags with the left button, so as to
		// allow the middle button to be used for dragging the
		// plug out of the node graph (and into places like the
		// script editor), rather than dragging a connection
		// around within it.
		return false;
	}

	if( event.sourceGadget == this )
	{
		updateDragEndPoint( V3f( event.line.p0.x, event.line.p0.y, 0 ), V3f( 0 ) );
		return true;
	}

	ConnectionCreator *creator = IECore::runTimeCast<ConnectionCreator>( event.sourceGadget.get() );
	if( !creator )
	{
		// we only accept drags from compatible gadgets, namely ConnectionCreators
		return false;
	}

	if( creator->canCreateConnection( plug() ) )
	{
		setHighlighted( true );

		// snap the drag endpoint to our centre, as another little visual indication
		// that we're well up for being connected.
		V3f centre = V3f( 0 ) * fullTransform();
		centre = centre * event.sourceGadget->fullTransform().inverse();

		V3f tangent( 0 );
		if( NodeGadget *nodeGadget = ancestor<NodeGadget>() )
		{
			tangent = nodeGadget->connectionTangent( this );
		}

		creator->updateDragEndPoint( centre, tangent );

		// show the labels of all compatible nodules on this node, if it doesn't
		// look like the previous drag destination would have done so.
		Nodule *prevDestination = IECore::runTimeCast<Nodule>( event.destinationGadget.get() );
		if( !prevDestination || prevDestination->plug()->node() != plug()->node() )
		{
			setCompatibleLabelsVisible( event, true );
		}

		dirty( DirtyType::Render );
		return true;
	}

	return false;
}

bool StandardNodule::dragMove( GadgetPtr gadget, const DragDropEvent &event )
{
	m_dragPosition = V3f( event.line.p0.x, event.line.p0.y, 0 );
	dirty( DirtyType::Render );
	return true;
}

bool StandardNodule::dragLeave( GadgetPtr gadget, const DragDropEvent &event )
{
	if( this != event.sourceGadget )
	{
		setHighlighted( false );
		// if the new drag destination isn't one that would warrant having the labels
		// showing, then hide them.
		if( Nodule *newDestination = IECore::runTimeCast<Nodule>( event.destinationGadget.get() ) )
		{
			if( newDestination->plug()->node() != plug()->node() )
			{
				setCompatibleLabelsVisible( event, false );
			}
		}
		else if( NodeGadget *newDestination = IECore::runTimeCast<NodeGadget>( event.destinationGadget.get() ) )
		{
			if( newDestination->node() != plug()->node() )
			{
				setCompatibleLabelsVisible( event, false );
			}
		}
		else
		{
			setCompatibleLabelsVisible( event, false );
		}
	}
	else if( !event.destinationGadget )
	{
		m_draggingConnection = false;
	}

	dirty( DirtyType::Render );
	return true;
}

bool StandardNodule::dragEnd( GadgetPtr gadget, const DragDropEvent &event )
{
	GafferUI::Pointer::setCurrent( "" );
	m_draggingConnection = false;
	setHighlighted( false );
	return true;
}

bool StandardNodule::drop( GadgetPtr gadget, const DragDropEvent &event )
{
	setHighlighted( false );
	setCompatibleLabelsVisible( event, false );

	if( ConnectionCreator *creator = IECore::runTimeCast<ConnectionCreator>( event.sourceGadget.get() ) )
	{
		if( !creator->canCreateConnection( plug() ) )
		{
			return false;
		}

		UndoScope undoScope( plug()->ancestor<ScriptNode>() );
		creator->createConnection( plug() );
		return true;
	}

	return false;
}

void StandardNodule::setCompatibleLabelsVisible( const DragDropEvent &event, bool visible )
{
	NodeGadget *nodeGadget = ancestor<NodeGadget>();
	if( !nodeGadget )
	{
		return;
	}

	ConnectionCreator *creator = IECore::runTimeCast<ConnectionCreator>( event.sourceGadget.get() );
	if( !creator )
	{
		return;
	}

	for( RecursiveStandardNoduleIterator it( nodeGadget ); !it.done(); ++it )
	{
		if( creator->canCreateConnection( it->get()->plug() ) )
		{
			(*it)->setLabelVisible( visible );
		}
	}
}

void StandardNodule::plugMetadataChanged( const Gaffer::Plug *plug, IECore::InternedString key )
{
	if( plug != this->plug() )
	{
		return;
	}

	if( key == g_colorKey )
	{
		if( updateUserColor() )
		{
			dirty( DirtyType::Render );
		}
	}
	else if( key == g_labelKey )
	{
		if( m_labelVisible )
		{
			dirty( DirtyType::Render );
		}
	}
}

bool StandardNodule::updateUserColor()
{
	boost::optional<Color3f> c;
	if( IECore::ConstColor3fDataPtr d = Metadata::value<IECore::Color3fData>( plug(), g_colorKey ) )
	{
		c = d->readable();
	}

	if( c == m_userColor )
	{
		return false;
	}

	m_userColor = c;
	return true;
}
