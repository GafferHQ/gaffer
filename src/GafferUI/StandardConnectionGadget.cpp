//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/StandardConnectionGadget.h"

#include "GafferUI/GraphGadget.h"
#include "GafferUI/NodeGadget.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/Style.h"

#include "Gaffer/Dot.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/UndoScope.h"

#include "OpenEXR/ImathBoxAlgo.h"
#include "OpenEXR/ImathFun.h"

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace std;
using namespace Imath;
using namespace Gaffer;
using namespace GafferUI;

IE_CORE_DEFINERUNTIMETYPED( StandardConnectionGadget );

ConnectionGadget::ConnectionGadgetTypeDescription<StandardConnectionGadget> StandardConnectionGadget::g_connectionGadgetTypeDescription( Gaffer::Plug::staticTypeId() );

static IECore::InternedString g_colorKey( "connectionGadget:color" );

StandardConnectionGadget::StandardConnectionGadget( GafferUI::NodulePtr srcNodule, GafferUI::NodulePtr dstNodule )
	:	ConnectionGadget( srcNodule, dstNodule ), m_dragEnd( Gaffer::Plug::Invalid ), m_hovering( false ), m_dotPreview( false ), m_dotPreviewLocation( 0 ), m_addingConnection( false )
{
	enterSignal().connect( boost::bind( &StandardConnectionGadget::enter, this, ::_2 ) );
	mouseMoveSignal().connect( boost::bind( &StandardConnectionGadget::mouseMove, this, ::_2 ) );
	leaveSignal().connect( boost::bind( &StandardConnectionGadget::leave, this, ::_2 ) );
	buttonPressSignal().connect( boost::bind( &StandardConnectionGadget::buttonPress, this,  ::_2 ) );
	dragBeginSignal().connect( boost::bind( &StandardConnectionGadget::dragBegin, this, ::_2 ) );
	dragEnterSignal().connect( boost::bind( &StandardConnectionGadget::dragEnter, this, ::_2 ) );
	dragMoveSignal().connect( boost::bind( &StandardConnectionGadget::dragMove, this, ::_2 ) );
	dragEndSignal().connect( boost::bind( &StandardConnectionGadget::dragEnd, this, ::_2 ) );

	Metadata::plugValueChangedSignal().connect( boost::bind( &StandardConnectionGadget::plugMetadataChanged, this, ::_1, ::_2, ::_3, ::_4 ) );

	updateUserColor();
}

StandardConnectionGadget::~StandardConnectionGadget()
{
}

void StandardConnectionGadget::setNodules( GafferUI::NodulePtr srcNodule, GafferUI::NodulePtr dstNodule )
{
	ConnectionGadget::setNodules( srcNodule, dstNodule );
	setPositionsFromNodules();
}

void StandardConnectionGadget::setPositionsFromNodules()
{
	const Gadget *p = parent<Gadget>();
	if( !p )
	{
		return;
	}

	if( dstNodule() && m_dragEnd!=Gaffer::Plug::In )
	{
		Gadget *dstNodeGadget = dstNodule()->ancestor<NodeGadget>();
		if( dstNodeGadget )
		{
			/// \todo
			/// this is a hack. we're calling bound() to trigger
			/// recomputation of the child positions within
			/// the nodule row - this is currently necessary when a
			/// nodule has just been added as connections are
			/// rendered before nodules and the nodule transforms
			/// would otherwise not be updated in time. see the todo item
			/// in Gadget.h which suggests that transforms are returned from
			/// a childTransform() virtual method - this would mean the
			/// container could update the transform as we request it.
			dstNodeGadget->bound();
		}
		M44f m = dstNodule()->fullTransform( p );
		m_dstPos = V3f( 0 ) * m;

		const NodeGadget *dstNoduleNodeGadget = dstNodule()->ancestor<NodeGadget>();
		m_dstTangent = dstNoduleNodeGadget ? dstNoduleNodeGadget->connectionTangent( dstNodule() ) : V3f( 0, 1, 0 );
	}

	if( srcNodule() && m_dragEnd!=Gaffer::Plug::Out )
	{
		Gadget *srcNodeGadget = srcNodule()->ancestor<NodeGadget>();
		if( srcNodeGadget )
		{
			/// \todo See above.
			srcNodeGadget->bound();
		}
		M44f m = srcNodule()->fullTransform( p );
		m_srcPos = V3f( 0 ) * m;

		const NodeGadget *srcNoduleNodeGadget = srcNodule()->ancestor<NodeGadget>();
		m_srcTangent = srcNoduleNodeGadget ? srcNoduleNodeGadget->connectionTangent( srcNodule() ) : V3f( 0, -1, 0 );
	}
	else if( m_dragEnd != Gaffer::Plug::Out )
	{
		// not dragging and don't have a source nodule.
		// we're a dangling connection because the source
		// node is hidden.
		m_srcPos = m_dstPos + m_dstTangent * 1.5f;
		m_srcTangent = -m_dstTangent;
	}

}

Imath::Box3f StandardConnectionGadget::bound() const
{
	const_cast<StandardConnectionGadget *>( this )->setPositionsFromNodules();
	Box3f r;
	r.extendBy( m_srcPos );
	r.extendBy( m_dstPos );
	return r;
}

bool StandardConnectionGadget::canCreateConnection( const Gaffer::Plug *endpoint ) const
{
	if( m_dragEnd != endpoint->direction() )
	{
		return false;
	}

	switch( m_dragEnd )
	{
	case Gaffer::Plug::Out :
		return dstNodule()->plug()->acceptsInput( endpoint );
	case Gaffer::Plug::In :
		return endpoint->acceptsInput( srcNodule()->plug() );
	case Gaffer::Plug::Invalid :
		return false;
	}
	return false;
}

void StandardConnectionGadget::updateDragEndPoint( const Imath::V3f position, const Imath::V3f &tangent )
{
	if( m_dragEnd==Gaffer::Plug::Out )
	{
		m_srcPos = position;
		m_srcTangent = tangent;
	}
	else if( m_dragEnd==Gaffer::Plug::In )
	{
		m_dstPos = position;
		m_dstTangent = tangent;
	}
	else
	{
		throw IECore::Exception( "Not dragging" );
	}
 	requestRender();
}

void StandardConnectionGadget::createConnection( Gaffer::Plug *endpoint )
{
	Plug::Direction destinationDirection = endpoint->direction();

	// If we are asked to make a connection that already exists, we can safely ignore the request.
	Plug *equivalentPlug = destinationDirection == Plug::Out ? srcNodule()->plug() : dstNodule()->plug();
	if( endpoint == equivalentPlug )
	{
		return;
	}

	switch( destinationDirection )
	{
		case Gaffer::Plug::Out :
			dstNodule()->plug()->setInput( endpoint );
			return;
		case Gaffer::Plug::In :
			endpoint->setInput( srcNodule()->plug() );

			// The new connection potentially replaces the old one. It's important
			// that we remove the old connection /after/ making the new connection, as
			// removing a connection can trigger an InputGenerator to remove plugs,
			// possibly including the input plug we want to connect to. See issue #302.
			if( !m_addingConnection )
			{
				dstNodule()->plug()->setInput( nullptr );
			}
			return;
		default :
			return;
	}
}

void StandardConnectionGadget::doRenderLayer( Layer layer, const Style *style ) const
{
	// Connections get rendered below NodeGadgets but over BackdropGadgets
	if( layer != GraphLayer::Connections )
	{
		return;
	}

	const_cast<StandardConnectionGadget *>( this )->setPositionsFromNodules();

	const Gadget *srcNodeGadget;
	if( !srcNodule() )
	{
		const Plug *srcPlug = dstNodule()->plug()->getInput();
		const GraphGadget *graphGadget = parent<GafferUI::GraphGadget>();
		srcNodeGadget = graphGadget->nodeGadget( srcPlug->node() );
	}

	Style::State state = ( m_hovering || m_dragEnd || m_dotPreview ) ? Style::HighlightedState : Style::NormalState;

	if( state != Style::HighlightedState)
	{
		if( srcNodule() )
		{
			srcNodeGadget = srcNodule()->ancestor<NodeGadget>();
		}
		if( srcNodeGadget && srcNodeGadget->getHighlighted() )
		{
			state = Style::HighlightedState;
		}
	}

	if( state != Style::HighlightedState && dstNodule())
	{
		const Gadget *dstNodeGadget = dstNodule()->ancestor<NodeGadget>();
		if( dstNodeGadget && dstNodeGadget->getHighlighted() )
		{
			state = Style::HighlightedState;
		}
	}

	// If we're missing the srcNodule, the source node is either hidden or we're
	// dealing with an AuxiliaryConnection.
	if( !srcNodule() && srcNodeGadget )
	{
		Box3f b = srcNodeGadget->transformedBound();
		style->renderAuxiliaryConnection( V2f( b.center().x, b.center().y ), V2f( m_srcTangent.x, m_srcTangent.y ), V2f( m_dstPos.x, m_dstPos.y ), V2f( m_dstTangent.x, m_dstTangent.y ), state );
		return;
	}

	V3f adjustedSrcPos = m_srcPos;
	V3f adjustedSrcTangent = m_srcTangent;
	if( getMinimised() && state != Style::HighlightedState )
	{
		adjustedSrcPos = m_dstPos + m_dstTangent * 1.5f;
		adjustedSrcTangent = -m_dstTangent;
	}

	style->renderConnection( adjustedSrcPos, adjustedSrcTangent, m_dstPos, m_dstTangent, state, m_userColor.get_ptr() );

	if(m_addingConnection)
	{
		style->renderConnection( m_srcPos, m_srcTangent, m_dstPosOrig, m_dstTangentOrig, state, m_userColor.get_ptr() );
	}

	if( m_dotPreview )
	{
		Imath::Box2f bounds = Imath::Box2f( V2f( m_dotPreviewLocation.x, m_dotPreviewLocation.y ) );
		style->renderNodeFrame(bounds, 1.0, state, m_userColor.get_ptr()  );
	}
}

bool StandardConnectionGadget::hasLayer( Layer layer ) const
{
	return layer == GraphLayer::Connections;
}

Imath::V3f StandardConnectionGadget::closestPoint( const Imath::V3f& p ) const
{
	const_cast<StandardConnectionGadget *>( this )->setPositionsFromNodules();

	Style::State state = ( m_hovering || m_dragEnd ) ? Style::HighlightedState : Style::NormalState;
	if( state != Style::HighlightedState && srcNodule() && dstNodule() )
	{
		const Gadget *srcNodeGadget = srcNodule()->ancestor<NodeGadget>();
		if( srcNodeGadget && srcNodeGadget->getHighlighted() )
		{
			state = Style::HighlightedState;
		}
		else
		{
			const Gadget *dstNodeGadget = dstNodule()->ancestor<NodeGadget>();
			if( dstNodeGadget && dstNodeGadget->getHighlighted() )
			{
				state = Style::HighlightedState;
			}
		}
	}

	V3f adjustedSrcPos = m_srcPos;
	V3f adjustedSrcTangent = m_srcTangent;
	if( getMinimised() && state != Style::HighlightedState )
	{
		adjustedSrcPos = m_dstPos + m_dstTangent * 1.5f;
		adjustedSrcTangent = -m_dstTangent;
	}

	return style()->closestPointOnConnection( p, adjustedSrcPos, adjustedSrcTangent, m_dstPos, m_dstTangent );
}

float StandardConnectionGadget::distanceToNodeGadget( const IECore::LineSegment3f &line, const Nodule *nodule ) const
{
	const NodeGadget *nodeGadget = nodule ? nodule->ancestor<NodeGadget>() : nullptr;
	if( !nodeGadget )
	{
		return Imath::limits<float>::max();
	}

	const M44f relativeTransform = fullTransform() * nodeGadget->fullTransform().inverse();
	V3f p0 = line.p0 * relativeTransform; p0.z = 0;
	const V3f p1 = closestPointOnBox( p0, nodeGadget->bound() );

	return (p0 - p1).length();
}

Gaffer::Plug::Direction StandardConnectionGadget::endAt( const IECore::LineSegment3f &line ) const
{
	// Connections are only sensitive to hovering and dragging close
	// to their ends, since it is confusing to accidentally pick up
	// a connection in the middle, and some graphs use very long
	// connections. The sensitive section is proportional to the
	// length of the connection, with some sensible minimum and
	// maximum limits.
	const float length = ( m_srcPos - m_dstPos ).length();
	const float threshold = clamp( length / 4.0f, 2.5f, 25.0f );

	float dSrc = numeric_limits<float>::max();
	if( srcNodule() )
	{
		line.distanceTo( m_srcPos );
	}
	float dDst = line.distanceTo( m_dstPos );

	if( min( dSrc, dDst ) >= threshold )
	{
		// If connections go backwards, the grabbable region of the
		// connection may be hidden behind the node it connects to.
		// In this case  we also consider a point to be grabbable if
		// it is less than the threshold distance from the node, rather
		// than from the endpoint.
		dSrc = distanceToNodeGadget( line, srcNodule() );
		dDst = distanceToNodeGadget( line, dstNodule() );
	}

	if( min( dSrc, dDst ) < threshold )
	{
		// close enough to the ends to consider
		if( dSrc < dDst )
		{
			return Gaffer::Plug::Out;
		}
		else
		{
			return Gaffer::Plug::In;
		}
	}

	return Gaffer::Plug::Invalid;

}

bool StandardConnectionGadget::buttonPress( const ButtonEvent &event )
{
	if( m_dotPreview )
	{
		if( event.buttons!=ButtonEvent::Left )
		{
			return false;
		}

		Gaffer::ScriptNode *script = dstNodule()->plug()->ancestor<Gaffer::ScriptNode>();
		GraphGadget *graphGadget = parent<GafferUI::GraphGadget>();
		if( script && graphGadget )
		{
			Gaffer::UndoScope undoEnabler( script );

			Gaffer::DotPtr dot = new Gaffer::Dot();
			Gaffer::Plug *srcPlug = srcNodule()->plug();
			dot->setup( srcPlug );

			srcPlug->node()->parent()->addChild( dot );
			graphGadget->setNodePosition( dot.get(), V2f( event.line.p0.x, event.line.p0.y ) );

			dot->inPlug()->setInput( srcNodule()->plug() );
			dstNodule()->plug()->setInput( dot->outPlug() );

			script->selection()->clear();
			script->selection()->add( dot );
		}
		// If we are showing a preview for a potential Dot to be added, we don't
		// want the user to move the connection away from under the preview. Users
		// should leave preview state before dragging the noodle.
		return false;
	}

	// We have to accept button presses so we can initiate dragging.
	return event.buttons==ButtonEvent::Left && m_hovering;
}

IECore::RunTimeTypedPtr StandardConnectionGadget::dragBegin( const DragDropEvent &event )
{
	if(
		MetadataAlgo::readOnly( dstNodule()->plug() ) ||
		( srcNodule() && MetadataAlgo::readOnly( srcNodule()->plug() ) )
	)
	{
		return nullptr;
	}

	setPositionsFromNodules();
	m_dragEnd = endAt( event.line );

	// prepare for adding additional connection
	if( event.modifiers & ButtonEvent::Shift && m_dragEnd == Gaffer::Plug::In )
	{
		m_addingConnection = true;

		m_dstPosOrig = m_dstPos;
		m_dstTangentOrig = m_dstTangent;
	}

	switch( m_dragEnd )
	{
		case Gaffer::Plug::Out :
			return dstNodule()->plug();
		case Gaffer::Plug::In :
			return dstNodule()->plug()->getInput<Gaffer::Plug>();
		default :
			return nullptr;
	}
}

bool StandardConnectionGadget::dragEnter( const DragDropEvent &event )
{
	if( event.sourceGadget == this )
	{
		return true;
	}
	return false;
}

bool StandardConnectionGadget::dragMove( const DragDropEvent &event )
{
	updateDragEndPoint( V3f( event.line.p0.x, event.line.p0.y, 0.0f ), V3f( 0 ) );
	return true;
}

bool StandardConnectionGadget::dragEnd( const DragDropEvent &event )
{
	if( !event.destinationGadget || event.destinationGadget == this )
	{
		// noone wanted the drop so we'll disconnect unless we were meant to add an additional connection
		if( !m_addingConnection )
		{
			Gaffer::UndoScope undoEnabler( dstNodule()->plug()->ancestor<Gaffer::ScriptNode>() );
			dstNodule()->plug()->setInput( nullptr );
		}
	}
	else
	{
		// We let the Nodule setup the connection through createConnection() when a
		// drop has actually landed.
	}

	m_dragEnd = Gaffer::Plug::Invalid;
	m_addingConnection = false;
	requestRender();
	return true;
}

std::string StandardConnectionGadget::getToolTip( const IECore::LineSegment3f &line ) const
{
	std::string result = Gadget::getToolTip( line );
	if( result.size() )
	{
		return result;
	}

	if( !dstNodule() )
	{
		return result;
	}

	const Gaffer::Plug *dstPlug = dstNodule()->plug();

	int numSkippedDots = 0;
	const Gaffer::Plug *srcPlug = dstPlug->getInput<Gaffer::Plug>();
	while( const Dot *dot = IECore::runTimeCast<const Gaffer::Dot>( srcPlug->node() ) )
	{
		const Gaffer::Plug *inPlug = srcPlug->getInput<Gaffer::Plug>();
		if(
			srcPlug == dot->outPlug<Gaffer::Plug>() &&
			inPlug == dot->inPlug<Gaffer::Plug>() &&
			inPlug->getInput<Gaffer::Plug>()
		)
		{
			srcPlug = inPlug->getInput<Gaffer::Plug>();
			numSkippedDots += 1;
		}
		else
		{
			break;
		}
	}

	const Gaffer::GraphComponent *ancestor = srcPlug->commonAncestor<Gaffer::GraphComponent>( dstPlug );

	std::string srcName;
	std::string dstName;
	if( ancestor )
	{
		srcName = srcPlug->relativeName( ancestor );
		dstName = dstPlug->relativeName( ancestor );
	}
	else
	{
		srcName = srcPlug->fullName();
		dstName = dstPlug->fullName();
	}

	result = srcName + " -> " + dstName;
	if( numSkippedDots )
	{
		result += boost::str(
			boost::format( " (via %d dot%s)" ) % numSkippedDots % ( numSkippedDots > 1 ? "s" : "" )
		);
	}
	return result;
}

void StandardConnectionGadget::updateDotPreviewLocation( const ButtonEvent &event )
{
	m_dotPreviewLocation = closestPoint( event.line.p0 );
}

bool StandardConnectionGadget::keyPressed( const KeyEvent &event )
{
	if( event.modifiers & ButtonEvent::Control && srcNodule() && dstNodule() )
	{
		m_dotPreview = true;
		requestRender();
		return true;
	}
	return false;
}

bool StandardConnectionGadget::keyReleased( const KeyEvent &event )
{
	if( !(event.modifiers & ButtonEvent::Control) )
	{
		m_dotPreview = false;
		requestRender();
		return true;
	}
	return false;
}


void StandardConnectionGadget::enter( const ButtonEvent &event )
{
	if( event.modifiers & ButtonEvent::Control && srcNodule() && dstNodule() )
	{
		m_dotPreview = true;
	}

	// we're connecting to key events to properly react to a user
	// pressing/releasing modifiers while already hovering over the connection
	GraphGadget *graphGadget = parent<GafferUI::GraphGadget>();
	m_keyPressConnection = graphGadget->keyPressSignal().connect( boost::bind( &StandardConnectionGadget::keyPressed, this, ::_2 ) );
	m_keyReleaseConnection = graphGadget->keyReleaseSignal().connect( boost::bind( &StandardConnectionGadget::keyReleased, this, ::_2 ) );
	updateDotPreviewLocation( event );

	m_hovering = endAt( event.line ) != Plug::Invalid;
	requestRender();
}

bool StandardConnectionGadget::mouseMove( const ButtonEvent &event )
{
	updateDotPreviewLocation( event );

	m_hovering = endAt( event.line ) != Plug::Invalid;
 	requestRender();
	return false;
}

void StandardConnectionGadget::leave( const ButtonEvent &event )
{
	m_keyPressConnection.disconnect();
	m_keyReleaseConnection.disconnect();
	m_dotPreview = false;

	m_hovering = false;
	requestRender();
}

void StandardConnectionGadget::plugMetadataChanged( IECore::TypeId nodeTypeId, const Gaffer::StringAlgo::MatchPattern &plugPath, IECore::InternedString key, const Gaffer::Plug *plug )
{
	if( key != g_colorKey || !MetadataAlgo::affectedByChange( dstNodule()->plug(), nodeTypeId, plugPath, plug ) )
	{
		return;
	}

	if( updateUserColor() )
	{
		requestRender();
	}
}

bool StandardConnectionGadget::updateUserColor()
{
	boost::optional<Color3f> c;
	if( IECore::ConstColor3fDataPtr d = Metadata::value<IECore::Color3fData>( dstNodule()->plug(), g_colorKey ) )
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
