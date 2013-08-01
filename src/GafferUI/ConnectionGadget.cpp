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

#include "IECore/Exception.h"

#include "Gaffer/UndoContext.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StandardSet.h"

#include "GafferUI/ConnectionGadget.h"
#include "GafferUI/GraphGadget.h"
#include "GafferUI/Style.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/NodeGadget.h"

using namespace GafferUI;
using namespace Imath;
using namespace std;

IE_CORE_DEFINERUNTIMETYPED( ConnectionGadget );

ConnectionGadget::ConnectionGadget( GafferUI::NodulePtr srcNodule, GafferUI::NodulePtr dstNodule )
	:	Gadget( defaultName<ConnectionGadget>() ), m_minimised( false ), m_dragEnd( Gaffer::Plug::Invalid ), m_hovering( false )
{
	setNodules( srcNodule, dstNodule );
	
	enterSignal().connect( boost::bind( &ConnectionGadget::enter, this, ::_1, ::_2 ) );
	leaveSignal().connect( boost::bind( &ConnectionGadget::leave, this, ::_1, ::_2 ) );
	buttonPressSignal().connect( boost::bind( &ConnectionGadget::buttonPress, this, ::_1,  ::_2 ) );
	dragBeginSignal().connect( boost::bind( &ConnectionGadget::dragBegin, this, ::_1, ::_2 ) );
	dragEnterSignal().connect( boost::bind( &ConnectionGadget::dragEnter, this, ::_1, ::_2 ) );
	dragMoveSignal().connect( boost::bind( &ConnectionGadget::dragMove, this, ::_1, ::_2 ) );
	dragEndSignal().connect( boost::bind( &ConnectionGadget::dragEnd, this, ::_1, ::_2 ) );
}

ConnectionGadget::~ConnectionGadget()
{
}

bool ConnectionGadget::acceptsParent( const Gaffer::GraphComponent *potentialParent ) const
{
	if( !Gadget::acceptsParent( potentialParent ) )
	{
		return false;
	}
	return IECore::runTimeCast<const GraphGadget>( potentialParent );
}	

Nodule *ConnectionGadget::srcNodule()
{
	return m_srcNodule.get();
}

const Nodule *ConnectionGadget::srcNodule() const
{
	return m_srcNodule.get();
}

Nodule *ConnectionGadget::dstNodule()
{
	return m_dstNodule.get();
}

const Nodule *ConnectionGadget::dstNodule() const
{
	return m_dstNodule.get();
}

void ConnectionGadget::setNodules( GafferUI::NodulePtr srcNodule, GafferUI::NodulePtr dstNodule )
{
	if( !dstNodule )
	{
		// we must have a destination
		throw IECore::Exception( "No destination Nodule." );
	}
	if( srcNodule )
	{
		// if we have a source nodule then it must be connected to the destination
		if( srcNodule->plug() != dstNodule->plug()->getInput<Gaffer::Plug>() )
		{
			throw IECore::Exception( "Source plug not connected to destination plug." );
		}
	}
	else
	{
		// if we have no source nodule (because it isn't visible) then our destination
		// plug must at least have an input for us to represent as a dangler.
		if( !dstNodule->plug()->getInput<Gaffer::Plug>() )
		{
			throw IECore::Exception( "Destination plug has no input." );
		}
	}
	
	m_srcNodule = srcNodule;
	m_dstNodule = dstNodule;
	
	setPositionsFromNodules();
}

void ConnectionGadget::setMinimised( bool minimised )
{
	if( minimised == m_minimised )
	{
		return;
	}
	m_minimised = minimised;
	renderRequestSignal()( this );
}

bool ConnectionGadget::getMinimised() const
{
	return m_minimised;
}
		
void ConnectionGadget::setPositionsFromNodules()
{
	const Gadget *p = parent<Gadget>();
	if( !p )
	{
		return; // we have no parent during construction
	}
	
	if( m_dstNodule && m_dragEnd!=Gaffer::Plug::In )
	{
		Gadget *dstNoduleParent = m_dstNodule->parent<Gadget>();
		if( dstNoduleParent )
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
			dstNoduleParent->bound();
		}
		M44f m = m_dstNodule->fullTransform( p );
		m_dstPos = V3f( 0 ) * m;
		
		const NodeGadget *dstNoduleNodeGadget = m_dstNodule->ancestor<NodeGadget>();
		m_dstTangent = dstNoduleNodeGadget ? dstNoduleNodeGadget->noduleTangent( m_dstNodule ) : V3f( 0, 1, 0 );
	}
	
	if( m_srcNodule && m_dragEnd!=Gaffer::Plug::Out )
	{
		Gadget *dstNoduleParent = m_dstNodule->parent<Gadget>();
		if( dstNoduleParent )
		{
			/// \todo See above.
			dstNoduleParent->bound();
		}
		M44f m = m_srcNodule->fullTransform( p );
		m_srcPos = V3f( 0 ) * m;
		
		const NodeGadget *srcNoduleNodeGadget = m_srcNodule->ancestor<NodeGadget>();
		m_srcTangent = srcNoduleNodeGadget ? srcNoduleNodeGadget->noduleTangent( m_srcNodule ) : V3f( 0, -1, 0 );
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
		
Imath::Box3f ConnectionGadget::bound() const
{
	const_cast<ConnectionGadget *>( this )->setPositionsFromNodules();
	Box3f r;
	r.extendBy( m_srcPos );
	r.extendBy( m_dstPos );
	return r;
}

void ConnectionGadget::updateDragEndPoint( const Imath::V3f position, const Imath::V3f &tangent )
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
	renderRequestSignal()( this );
}

void ConnectionGadget::doRender( const Style *style ) const
{
	const_cast<ConnectionGadget *>( this )->setPositionsFromNodules();
	
	Style::State state = m_hovering ? Style::HighlightedState : Style::NormalState;
	if( state != Style::HighlightedState )
	{
		if( nodeSelected( m_srcNodule ) || nodeSelected( m_dstNodule ) )
		{
			state = Style::HighlightedState;
		}
	}
	
	V3f adjustedSrcPos = m_srcPos;
	V3f adjustedSrcTangent = m_srcTangent;
	if( m_minimised && state != Style::HighlightedState )
	{
		adjustedSrcPos = m_dstPos + m_dstTangent * 1.5f;
		adjustedSrcTangent = -m_dstTangent;
	}
		
	style->renderConnection( adjustedSrcPos, adjustedSrcTangent, m_dstPos, m_dstTangent, state );
}

bool ConnectionGadget::buttonPress( GadgetPtr gadget, const ButtonEvent &event )
{
	if( event.buttons==ButtonEvent::Left )
	{
		// we have to accept button presses so we can initiate dragging
		return true;
	}
	return false;
}

IECore::RunTimeTypedPtr ConnectionGadget::dragBegin( GadgetPtr gadget, const DragDropEvent &event )
{
	setPositionsFromNodules();
	float length = ( m_srcPos - m_dstPos ).length();
	
	float dSrc = event.line.distanceTo( m_srcPos );
	float dDst = event.line.distanceTo( m_dstPos );
	
	float dMin = min( dSrc, dDst );
	if( dMin < length / 3.0f )
	{
		// close enough to the ends to consider
		if( dSrc < dDst )
		{
			m_dragEnd = Gaffer::Plug::Out;
			return m_dstNodule->plug();
		}
		else
		{
			m_dragEnd = Gaffer::Plug::In;
			return m_dstNodule->plug()->getInput<Gaffer::Plug>();
		}
	}
	
	return 0;
}

bool ConnectionGadget::dragEnter( GadgetPtr gadget, const DragDropEvent &event )
{
	if( event.sourceGadget == this )
	{
		return true;
	}
	return false;
}

bool ConnectionGadget::dragMove( GadgetPtr gadget, const DragDropEvent &event )
{
	updateDragEndPoint( event.line.p0, V3f( 0 ) );
	return true;
}

bool ConnectionGadget::dragEnd( GadgetPtr gadget, const DragDropEvent &event )
{
	if( !event.destinationGadget || event.destinationGadget == this )
	{
		// noone wanted the drop so we'll disconnect
		Gaffer::UndoContext undoEnabler( m_dstNodule->plug()->ancestor<Gaffer::ScriptNode>() );
		m_dstNodule->plug()->setInput( 0 );
	}
	else
	{
		// we let the Nodule do all the work when a drop has actually landed
	}

	m_dragEnd = Gaffer::Plug::Invalid;
	renderRequestSignal()( this );
	return true;
}

std::string ConnectionGadget::getToolTip( const IECore::LineSegment3f &line ) const
{
	std::string result = Gadget::getToolTip( line );
	if( result.size() )
	{
		return result;
	}
	
	if( !m_dstNodule )
	{
		return result;
	}
	
	Gaffer::Plug *dstPlug = m_dstNodule->plug();
	Gaffer::Plug *srcPlug = dstPlug->getInput<Gaffer::Plug>();
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
	
	return srcName + " -> " + dstName;
}

void ConnectionGadget::enter( GadgetPtr gadget, const ButtonEvent &event )
{
	m_hovering = true;
	renderRequestSignal()( this );
}

void ConnectionGadget::leave( GadgetPtr gadget, const ButtonEvent &event )
{
	m_hovering = false;
	renderRequestSignal()( this );
}

bool ConnectionGadget::nodeSelected( const Nodule *nodule ) const
{
	if( !nodule )
	{
		return false;
	}
	
	const Gaffer::Node *node = nodule->plug()->node();
	if( !node )
	{
		return false;
	}

	const Gaffer::ScriptNode *script = node->scriptNode();
	return script && script->selection()->contains( node );
}
