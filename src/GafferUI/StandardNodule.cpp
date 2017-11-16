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

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

#include "IECore/AngleConversion.h"

#include "IECoreGL/Selector.h"

#include "Gaffer/Plug.h"
#include "Gaffer/UndoScope.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"

#include "GafferUI/StandardNodule.h"
#include "GafferUI/Style.h"
#include "GafferUI/ConnectionGadget.h"
#include "GafferUI/NodeGadget.h"
#include "GafferUI/Pointer.h"
#include "GafferUI/PlugAdder.h"

using namespace std;
using namespace Imath;
using namespace Gaffer;
using namespace GafferUI;

IE_CORE_DEFINERUNTIMETYPED( StandardNodule );

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

	Metadata::plugValueChangedSignal().connect( boost::bind( &StandardNodule::plugMetadataChanged, this, ::_1, ::_2, ::_3, ::_4 ) );

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
 	requestRender();
}

bool StandardNodule::getLabelVisible() const
{
	return m_labelVisible;
}

Imath::Box3f StandardNodule::bound() const
{
	return Box3f( V3f( -0.5, -0.5, 0 ), V3f( 0.5, 0.5, 0 ) );
}

void StandardNodule::updateDragEndPoint( const Imath::V3f position, const Imath::V3f &tangent )
{
	m_dragPosition = position;
	m_dragTangent = tangent;
	m_draggingConnection = true;
 	requestRender();
}

void StandardNodule::doRender( const Style *style ) const
{
	if( m_draggingConnection )
	{
		if( !IECoreGL::Selector::currentSelector() )
		{
			V3f srcTangent( 0.0f, 1.0f, 0.0f );
			const NodeGadget *nodeGadget = ancestor<NodeGadget>();
			if( nodeGadget )
			{
				srcTangent = nodeGadget->noduleTangent( this );
			}
			style->renderConnection( V3f( 0 ), srcTangent, m_dragPosition, m_dragTangent, Style::HighlightedState );
		}
	}

	float radius = 0.5f;
	Style::State state = Style::NormalState;
	if( getHighlighted() )
	{
		state = Style::HighlightedState;
		radius = 1.0f;
	}

	style->renderNodule( radius, state, m_userColor.get_ptr() );

	if( m_labelVisible && !IECoreGL::Selector::currentSelector() )
	{
		renderLabel( style );
	}
}

void StandardNodule::renderLabel( const Style *style ) const
{
	const NodeGadget *nodeGadget = ancestor<NodeGadget>();
	if( !nodeGadget )
	{
		return;
	}

	const std::string *label = NULL;
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
	V3f tangent = nodeGadget->noduleTangent( this );
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

	if( getHighlighted() )
	{
		glScalef( 1.2, 1.2, 1.2 );
	}

	glRotatef( theta, 0, 0, 1.0f );
	glTranslatef( -anchor.x, -anchor.y, 0.0f );

	style->renderText( Style::LabelText, *label );
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
	// menus in NodeGraph.py.
	if( event.buttons & ( ButtonEvent::LeftMiddle ) )
	{
		return true;
	}
	return false;
}

IECore::RunTimeTypedPtr StandardNodule::dragBegin( GadgetPtr gadget, const ButtonEvent &event )
{
 	requestRender();
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

	bool accept = false;
	if( IECore::runTimeCast<Plug>( event.data ) )
	{
		Gaffer::PlugPtr input, output;
		connection( event, input, output );
		accept = static_cast<bool>( input );
	}
	else if( const PlugAdder *plugAdder = IECore::runTimeCast<PlugAdder>( event.sourceGadget.get() ) )
	{
		// We must accept the drag so that the PlugAdder gets
		// a chance to do its thing.
		accept = plugAdder->acceptsPlug( plug() );
	}

	if( accept )
	{
		setHighlighted( true );

		if( event.sourceGadget )
		{
			// snap the drag endpoint to our centre, as another little visual indication
			// that we're well up for being connected.
			V3f centre = V3f( 0 ) * fullTransform();
			centre = centre * event.sourceGadget->fullTransform().inverse();

			V3f tangent( 0 );
			if( NodeGadget *nodeGadget = ancestor<NodeGadget>() )
			{
				tangent = nodeGadget->noduleTangent( this );
			}

			if( Nodule *sourceNodule = IECore::runTimeCast<Nodule>( event.sourceGadget.get() ) )
			{
				sourceNodule->updateDragEndPoint( centre, tangent );
			}
			else if( ConnectionGadget *sourceConnection = IECore::runTimeCast<ConnectionGadget>( event.sourceGadget.get() ) )
			{
				sourceConnection->updateDragEndPoint( centre, tangent );
			}
			else if( PlugAdder *plugAdder = IECore::runTimeCast<PlugAdder>( event.sourceGadget.get() ) )
			{
				plugAdder->updateDragEndPoint( centre, tangent );
			}
		}

		// show the labels of all compatible nodules on this node, if it doesn't
		// look like the previous drag destination would have done so.
		Nodule *prevDestination = IECore::runTimeCast<Nodule>( event.destinationGadget.get() );
		if( !prevDestination || prevDestination->plug()->node() != plug()->node() )
		{
			setCompatibleLabelsVisible( event, true );
		}

 		requestRender();
	}

	return accept;
}

bool StandardNodule::dragMove( GadgetPtr gadget, const DragDropEvent &event )
{
	m_dragPosition = V3f( event.line.p0.x, event.line.p0.y, 0 );
 	requestRender();
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

 	requestRender();
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

	if( PlugAdder *plugAdder = IECore::runTimeCast<PlugAdder>( event.sourceGadget.get() ) )
	{
		plugAdder->addPlug( plug() );
		return true;
	}

	Gaffer::PlugPtr input, output;
	connection( event, input, output );

	if( input )
	{
		Gaffer::UndoScope undoEnabler( input->ancestor<Gaffer::ScriptNode>() );

			input->setInput( output );

			ConnectionGadgetPtr connection = IECore::runTimeCast<ConnectionGadget>( event.sourceGadget );
			if( connection && plug()->direction()==Gaffer::Plug::In )
			{
				// it's important that we remove the old connection /after/ making the
				// new connection above, as removing a connection can trigger an InputGenerator
				// to remove plugs, possibly including the input plug we're want to connect to.
				// see issue #302.
				if( connection->dstNodule()->plug() != input )
				{
					connection->dstNodule()->plug()->setInput( 0 );
				}
			}

		return true;
	}

	return false;
}

void StandardNodule::connection( const DragDropEvent &event, Gaffer::PlugPtr &input, Gaffer::PlugPtr &output )
{
	Gaffer::PlugPtr dropPlug = IECore::runTimeCast<Gaffer::Plug>( event.data );
	if( dropPlug )
	{
		Gaffer::PlugPtr thisPlug = plug();
		if( thisPlug->node() != dropPlug->node() && thisPlug->direction()!=dropPlug->direction() )
		{
			if( thisPlug->direction()==Gaffer::Plug::In )
			{
				input = thisPlug;
				output = dropPlug;
			}
			else
			{
				input = dropPlug;
				output = thisPlug;
			}

			if( input->acceptsInput( output.get() ) )
			{
				// success
				return;
			}
		}
	}

	input = output = 0;
	return;
}

void StandardNodule::setCompatibleLabelsVisible( const DragDropEvent &event, bool visible )
{
	NodeGadget *nodeGadget = ancestor<NodeGadget>();
	if( !nodeGadget )
	{
		return;
	}

	for( RecursiveStandardNoduleIterator it( nodeGadget ); !it.done(); ++it )
	{
		bool compatible = false;
		if( IECore::runTimeCast<PlugAdder>( event.sourceGadget.get() ) )
		{
			compatible = true;
		}
		else
		{
			Gaffer::PlugPtr input, output;
			(*it)->connection( event, input, output );
			compatible = input && output;
		}
		if( compatible )
		{
			(*it)->setLabelVisible( visible );
		}
	}
}

void StandardNodule::plugMetadataChanged( IECore::TypeId nodeTypeId, const Gaffer::StringAlgo::MatchPattern &plugPath, IECore::InternedString key, const Gaffer::Plug *plug )
{
	if( !MetadataAlgo::affectedByChange( this->plug(), nodeTypeId, plugPath, plug ) )
	{
		return;
	}

	if( key == g_colorKey )
	{
		if( updateUserColor() )
		{
			requestRender();
		}
	}
	else if( key == g_labelKey )
	{
		if( m_labelVisible )
		{
			requestRender();
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
