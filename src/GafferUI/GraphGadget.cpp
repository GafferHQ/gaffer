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

#include "OpenEXR/ImathRandom.h"
#include "OpenEXR/ImathPlane.h"

#include "IECore/SimpleTypedData.h"
#include "IECore/MessageHandler.h"

#include "Gaffer/ScriptNode.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/ChildSet.h"
#include "Gaffer/CompoundPlug.h"

#include "GafferUI/GraphGadget.h"
#include "GafferUI/NodeGadget.h"
#include "GafferUI/ButtonEvent.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/ConnectionGadget.h"
#include "GafferUI/Style.h"
#include "GafferUI/ViewportGadget.h"

using namespace GafferUI;
using namespace Imath;
using namespace IECore;
using namespace std;

//////////////////////////////////////////////////////////////////////////
// GraphGadget implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( GraphGadget );

GraphGadget::GraphGadget( Gaffer::SetPtr graphSet )
{
	constructCommon( graphSet );
}
		
GraphGadget::GraphGadget( Gaffer::NodePtr graphRoot )
{
	constructCommon( new Gaffer::ChildSet( graphRoot ) );
}

void GraphGadget::constructCommon( Gaffer::SetPtr graphSet )
{
	m_scriptNode = 0; // we'll fill this in when we get our first node
		
	m_dragStartPosition = V2f( 0 );
	m_lastDragPosition = V2f( 0 );
	m_dragSelecting = false;

	keyPressSignal().connect( boost::bind( &GraphGadget::keyPressed, this, ::_1,  ::_2 ) );
	buttonPressSignal().connect( boost::bind( &GraphGadget::buttonPress, this, ::_1,  ::_2 ) );
	buttonReleaseSignal().connect( boost::bind( &GraphGadget::buttonRelease, this, ::_1,  ::_2 ) );
	dragBeginSignal().connect( boost::bind( &GraphGadget::dragBegin, this, ::_1, ::_2 ) );
	dragEnterSignal().connect( boost::bind( &GraphGadget::dragEnter, this, ::_1, ::_2 ) );
	dragMoveSignal().connect( boost::bind( &GraphGadget::dragMove, this, ::_1, ::_2 ) );
	dragLeaveSignal().connect( boost::bind( &GraphGadget::dragLeave, this, ::_1, ::_2 ) );
	dragEndSignal().connect( boost::bind( &GraphGadget::dragEnd, this, ::_1, ::_2 ) );

	setGraphSet( graphSet );
}

GraphGadget::~GraphGadget()
{
}

	
Gaffer::Set *GraphGadget::getGraphSet()
{
	return m_graphSet;
}

const Gaffer::Set *GraphGadget::getGraphSet() const
{
	return m_graphSet;
}

void GraphGadget::setGraphSet( Gaffer::SetPtr graphSet )
{
	if( graphSet==m_graphSet )
	{
		return;
	}
	m_graphSet = graphSet;
	m_graphSetMemberAddedConnection = m_graphSet->memberAddedSignal().connect( boost::bind( &GraphGadget::memberAdded, this, ::_1,  ::_2 ) );
	m_graphSetMemberRemovedConnection = m_graphSet->memberRemovedSignal().connect( boost::bind( &GraphGadget::memberRemoved, this, ::_1,  ::_2 ) );
	updateGraph();
}

NodeGadget *GraphGadget::nodeGadget( const Gaffer::Node *node )
{
	return findNodeGadget( node );
}

const NodeGadget *GraphGadget::nodeGadget( const Gaffer::Node *node ) const
{
	return findNodeGadget( node );
}

ConnectionGadget *GraphGadget::connectionGadget( const Gaffer::Plug *dstPlug )
{
	return findConnectionGadget( dstPlug );
}

const ConnectionGadget *GraphGadget::connectionGadget( const Gaffer::Plug *dstPlug ) const
{
	return findConnectionGadget( dstPlug );
}
		
void GraphGadget::doRender( const Style *style ) const
{
	glDisable( GL_DEPTH_TEST );
	
	// render connection first so they go underneath
	for( ChildContainer::const_iterator it=children().begin(); it!=children().end(); it++ )
	{
		if( ConnectionGadget *c = IECore::runTimeCast<ConnectionGadget>( it->get() ) )
		{
			c->render( style );
		}
	}

	// then render the rest on top
	for( ChildContainer::const_iterator it=children().begin(); it!=children().end(); it++ )
	{
		if( !((*it)->isInstanceOf( ConnectionGadget::staticTypeId() )) )
		{
			static_cast<const Gadget *>( it->get() )->render( style );
		}
	}

	// render drag select thing if needed
	if( m_dragSelecting )
	{
		const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
		ViewportGadget::RasterScope rasterScope( viewportGadget );

		Box2f b;
		b.extendBy( viewportGadget->gadgetToRasterSpace( V3f( m_dragStartPosition.x, m_dragStartPosition.y, 0 ), this ) );
		b.extendBy( viewportGadget->gadgetToRasterSpace( V3f( m_lastDragPosition.x, m_lastDragPosition.y, 0 ), this ) );
		style->renderSelectionBox( b );		
	}
	
}

bool GraphGadget::keyPressed( GadgetPtr gadget, const KeyEvent &event )
{
	return false;
}

void GraphGadget::memberAdded( Gaffer::Set *set, IECore::RunTimeTyped *member )
{
	Gaffer::Node *node = IECore::runTimeCast<Gaffer::Node>( member );
	if( node )
	{
		addNodeGadget( node );
		addConnectionGadgets( node );
	}
}

void GraphGadget::memberRemoved( Gaffer::Set *set, IECore::RunTimeTyped *member )
{
	Gaffer::Node *node = IECore::runTimeCast<Gaffer::Node>( member );
	if( node )
	{
		removeNodeGadget( node );
	}
}

void GraphGadget::inputChanged( Gaffer::Plug *dstPlug )
{
	removeConnectionGadget( dstPlug );

	Gaffer::PlugPtr srcPlug = dstPlug->getInput<Gaffer::Plug>();
	if( !srcPlug )
	{
		// it's a disconnection, no need to make a new gadget.
		return;
	}
	
	if( dstPlug->direction() == Gaffer::Plug::Out )
	{
		// it's an internal connection - no need to
		// represent it.
		return;
	}
	
	addConnectionGadget( dstPlug );
}

void GraphGadget::plugSet( Gaffer::Plug *plug )
{
	const std::string &name = plug->getName();
	if( name=="__uiX" || name=="__uiY" )
	{
		Gaffer::Node *node = plug->node();
		NodeGadget *ng = findNodeGadget( node );
		if( ng )
		{
			updateNodeGadgetTransform( ng );
		}
	}
}

bool GraphGadget::buttonRelease( GadgetPtr gadget, const ButtonEvent &event )
{
	return true;
}

bool GraphGadget::buttonPress( GadgetPtr gadget, const ButtonEvent &event )
{
	if( event.buttons==ButtonEvent::Left )
	{
		// selection/deselection
		
		if( !m_scriptNode )
		{
			return false;
		}
		
		ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
				
		std::vector<GadgetPtr> gadgetsUnderMouse;
		viewportGadget->gadgetsAt(
			viewportGadget->gadgetToRasterSpace( event.line.p0, this ),
			gadgetsUnderMouse
		);
				
		if( !gadgetsUnderMouse.size() || gadgetsUnderMouse[0] == this )
		{
			// background click - clear the current selection
			m_scriptNode->selection()->clear();
			return true;
		}
				
		NodeGadget *nodeGadget = runTimeCast<NodeGadget>( gadgetsUnderMouse[0] );
		if( !nodeGadget )
		{
			nodeGadget = gadgetsUnderMouse[0]->ancestor<NodeGadget>();
		}
				
		if( nodeGadget )
		{				
			Gaffer::NodePtr node = nodeGadget->node();
			bool shiftHeld = event.modifiers && ButtonEvent::Shift;
			bool nodeSelected = m_scriptNode->selection()->contains( node );

			if( nodeSelected )
			{
				if( shiftHeld )
				{
					m_scriptNode->selection()->remove( node );
				}
			}
			else
			{
				if( !shiftHeld )
				{
					m_scriptNode->selection()->clear();
				}
				m_scriptNode->selection()->add( node );			
			}

			return true;
		}
	}
	return false;
}

IECore::RunTimeTypedPtr GraphGadget::dragBegin( GadgetPtr gadget, const DragDropEvent &event )
{
	if( !m_scriptNode )
	{
		return 0;
	}
	
	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return 0;
	}
	
	m_dragStartPosition = m_lastDragPosition = V2f( i.x, i.y );
	if( m_scriptNode->selection()->size() )
	{
		return m_scriptNode->selection();
	}
	else
	{
		return new IECore::V2fData( m_dragStartPosition );
	}
	return 0;
}

bool GraphGadget::dragEnter( GadgetPtr gadget, const DragDropEvent &event )
{
	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return false;
	}

	if( event.sourceGadget == this )
	{
		V2f pos = V2f( i.x, i.y );
		if( event.data->isInstanceOf( Gaffer::Set::staticTypeId() ) )
		{
			offsetNodes( static_cast<Gaffer::Set *>( event.data.get() ), pos - m_lastDragPosition );
		}
		m_lastDragPosition = pos;
		renderRequestSignal()( this );		
		return true;
	}
	
	return false;
}

bool GraphGadget::dragMove( GadgetPtr gadget, const DragDropEvent &event )
{
	if( !m_scriptNode )
	{
		return false;
	}
	
	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return false;
	}
	
	if( event.data->isInstanceOf( Gaffer::Set::staticTypeId() ) )
	{
		// we're dragging some nodes around
		V2f pos = V2f( i.x, i.y );
		offsetNodes( static_cast<Gaffer::Set *>( event.data.get() ), pos - m_lastDragPosition );
		m_lastDragPosition = pos;
		renderRequestSignal()( this );
		return true;
	}
	else
	{
		// we're drag selecting
		m_dragSelecting	= true;
		m_lastDragPosition = V2f( i.x, i.y );
		renderRequestSignal()( this );
		return true;
	}
		
	assert( 0 ); // shouldn't get here
	return false;
}

bool GraphGadget::dragLeave( GadgetPtr gadget, const DragDropEvent &event )
{
	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return false;
	}

	if( event.data->isInstanceOf( Gaffer::Set::staticTypeId() ) )
	{
		// we've been dragging some nodes around, but now they've been accepted
		// by some other destination. put the nodes back where they came from.
		offsetNodes( static_cast<Gaffer::Set *>( event.data.get() ), m_dragStartPosition - m_lastDragPosition );
		m_lastDragPosition = m_dragStartPosition;		
	}
	
	return true;
}

bool GraphGadget::dragEnd( GadgetPtr gadget, const DragDropEvent &event )
{
	m_dragSelecting = false;
	
	if( !m_scriptNode )
	{
		return false;
	}
	
	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return false;
	}

	if( event.data->isInstanceOf( V2fData::staticTypeId() ) )
	{
		Box2f selectionBound;
		selectionBound.extendBy( m_dragStartPosition );
		selectionBound.extendBy( m_lastDragPosition );
	
		for( ChildContainer::const_iterator it=children().begin(); it!=children().end(); it++ )
		{
			NodeGadgetPtr nodeGadget = runTimeCast<NodeGadget>( *it );
			if( nodeGadget )
			{
				Box3f nodeBound3 = nodeGadget->transformedBound();
				Box2f nodeBound2( V2f( nodeBound3.min.x, nodeBound3.min.y ), V2f( nodeBound3.max.x, nodeBound3.max.y ) );
				if( selectionBound.intersects( nodeBound2 ) )
				{
					m_scriptNode->selection()->add( nodeGadget->node() );
				}
			}
		}
	
		renderRequestSignal()( this );
	}

	return true;
}

void GraphGadget::offsetNodes( Gaffer::Set *nodes, const Imath::V2f &offset )
{
	for( size_t i = 0, e = nodes->size(); i < e; i++ )
	{
		Gaffer::Node *node = runTimeCast<Gaffer::Node>( nodes->member( i ) );
		if( !node )
		{
			continue;
		}
		
		NodeGadget *gadget = nodeGadget( node );
		if( gadget )
		{			
			Gaffer::FloatPlug *xp = node->getChild<Gaffer::FloatPlug>( "__uiX" );
			Gaffer::FloatPlug *yp = node->getChild<Gaffer::FloatPlug>( "__uiY" );
			xp->setValue( xp->getValue() + offset.x );
			yp->setValue( yp->getValue() + offset.y );
		}
	}
}

void GraphGadget::updateGraph()
{
	
	// first remove any gadgets we don't need any more
	for( NodeGadgetMap::iterator it = m_nodeGadgets.begin(); it != m_nodeGadgets.end(); )
	{
		const Gaffer::Node *node = it->first;
		it++; // increment now as the iterator will be invalidated by removeNodeGadget()
		if( !m_graphSet->contains( node ) )
		{
			removeNodeGadget( node );
		}
	}
		
	// now make sure we have gadgets for all the nodes we're meant to display
	for( size_t i = 0, e = m_graphSet->size(); i < e; i++ )
	{
		Gaffer::Node *node = IECore::runTimeCast<Gaffer::Node>( m_graphSet->member( i ) );
		if( node && !findNodeGadget( node ) )
		{
			addNodeGadget( node );
		}
	}
	
	// and that we have gadgets for each connection
	
	for( size_t i = 0, e = m_graphSet->size(); i < e; i++ )
	{
		Gaffer::Node *node = IECore::runTimeCast<Gaffer::Node>( m_graphSet->member( i ) );
		if( node )
		{
			addConnectionGadgets( node );
		}
	}
	
}

void GraphGadget::addNodeGadget( Gaffer::Node *node )
{	

	if( !node->scriptNode() )
	{
		IECore::msg( IECore::Msg::Error, "GraphGadget::addNodeGadget", boost::format( "Node \"%s\" does not belong to a script." ) % node->getName() );
		return;
	}
	
	if( !m_scriptNode )
	{
		m_scriptNode = node->scriptNode();
	}
	else
	{
		if( node->scriptNode() != m_scriptNode )
		{
			IECore::msg( IECore::Msg::Error, "GraphGadget::addNodeGadget", boost::format( "Node \"%s\" does not belong to the same script as the existing nodes." ) % node->getName() );
			return;
		}
	}

	NodeGadgetPtr nodeGadget = NodeGadget::create( node );
	addChild( nodeGadget );
	
	NodeGadgetEntry nodeGadgetEntry;
	nodeGadgetEntry.inputChangedConnection = node->plugInputChangedSignal().connect( boost::bind( &GraphGadget::inputChanged, this, ::_1 ) );
	nodeGadgetEntry.plugSetConnection = node->plugSetSignal().connect( boost::bind( &GraphGadget::plugSet, this, ::_1 ) );	
	nodeGadgetEntry.gadget = nodeGadget.get();
	
	m_nodeGadgets[node] = nodeGadgetEntry;
	
	// place it if it's not placed already.
	/// \todo we need to do this intelligently rather than randomly!!
	/// this probably means knowing what part of the graph is being viewed at the time. i think we
	/// can do this by having the panning and zooming handled by a parent ViewportGadget rather than
	/// letting the GadgetWidget do it. or do we need to query mouse position??
	
	/// \todo Use a V2f plug when we get one
	static Imath::Rand32 r;
	Gaffer::FloatPlugPtr xPlug = node->getChild<Gaffer::FloatPlug>( "__uiX" );
	if( !xPlug )
	{
		xPlug = new Gaffer::FloatPlug( "__uiX", Gaffer::Plug::In );
		xPlug->setFlags( Gaffer::Plug::Dynamic, true );
		xPlug->setValue( r.nextf( -10, 10 ) );
		node->addChild( xPlug );
	}
	
	Gaffer::FloatPlugPtr yPlug = node->getChild<Gaffer::FloatPlug>( "__uiY" );
	if( !yPlug )
	{	
		Gaffer::FloatPlugPtr yPlug = new Gaffer::FloatPlug( "__uiY", Gaffer::Plug::In );
		yPlug->setFlags( Gaffer::Plug::Dynamic, true );
		yPlug->setValue( r.nextf( -10, 10 ) );
		node->addChild( yPlug );
	}
	
	updateNodeGadgetTransform( nodeGadget.get() );
	
}

void GraphGadget::removeNodeGadget( const Gaffer::Node *node )
{
	NodeGadgetMap::iterator it = m_nodeGadgets.find( node );
	if( it!=m_nodeGadgets.end() )
	{
		removeChild( it->second.gadget );
		it->second.inputChangedConnection.disconnect();
		it->second.plugSetConnection.disconnect();
		
		m_nodeGadgets.erase( it );
		
		removeConnectionGadgets( node );
	}
}
		
NodeGadget *GraphGadget::findNodeGadget( const Gaffer::Node *node ) const
{
	NodeGadgetMap::const_iterator it = m_nodeGadgets.find( node );
	if( it==m_nodeGadgets.end() )
	{
		return 0;
	}
	return it->second.gadget;
}

void GraphGadget::updateNodeGadgetTransform( NodeGadget *nodeGadget )
{
	Gaffer::NodePtr node = nodeGadget->node();
	V3f t( 0 );

	Gaffer::FloatPlugPtr x = node->getChild<Gaffer::FloatPlug>( "__uiX" );
	if( x )
	{
		t[0] = x->getValue();
	}

	Gaffer::FloatPlugPtr y = node->getChild<Gaffer::FloatPlug>( "__uiY" );
	if( y )
	{
		t[1] = y->getValue();
	}

	M44f m; m.translate( t );
	nodeGadget->setTransform( m );
}

void GraphGadget::addConnectionGadgets( Gaffer::GraphComponent *plugParent )
{
	/// \todo I think this could be faster if we could iterate over just the nodules rather than all the plugs. Perhaps
	/// we could make it easy to recurse over all the Nodules of a NodeGadget if we had a RecursiveChildIterator for GraphComponents?
	Gaffer::Node *node = plugParent->isInstanceOf( Gaffer::Node::staticTypeId() ) ? static_cast<Gaffer::Node *>( plugParent ) : plugParent->ancestor<Gaffer::Node>();
	
	NodeGadget *nodeGadget = findNodeGadget( node );

	for( Gaffer::PlugIterator pIt( plugParent->children().begin(), plugParent->children().end() ); pIt!=pIt.end(); pIt++ )
	{
		if( (*pIt)->direction() == Gaffer::Plug::In )
		{
			// add connections for input plugs
			if( !findConnectionGadget( pIt->get() ) )
			{
				addConnectionGadget( pIt->get() );
			}
		}
		else
		{
			// reconnect any old output connections which may have been dangling
			Nodule *srcNodule = nodeGadget->nodule( *pIt );
			if( srcNodule )
			{
				for( Gaffer::Plug::OutputContainer::const_iterator oIt( (*pIt)->outputs().begin() ); oIt!= (*pIt)->outputs().end(); oIt++ )
				{
					ConnectionGadget *connection = findConnectionGadget( *oIt );
					if( connection && !connection->srcNodule() )
					{
						assert( connection->dstNodule()->plug()->getInput<Plug>() == *pIt ); 
						connection->setNodules( srcNodule, connection->dstNodule() );
					}
				}
			}
		}
		
		if( (*pIt)->isInstanceOf( Gaffer::CompoundPlug::staticTypeId() ) )
		{
			addConnectionGadgets( pIt->get() );
		}
	}
	
}
		
void GraphGadget::addConnectionGadget( Gaffer::Plug *dstPlug )
{
	Gaffer::PlugPtr srcPlug = dstPlug->getInput<Gaffer::Plug>();
	if( !srcPlug )
	{
		// there is no connection
		return;
	}
	
	Gaffer::NodePtr dstNode = dstPlug->node();
	NodulePtr dstNodule = findNodeGadget( dstNode.get() )->nodule( dstPlug );
	if( !dstNodule )
	{
		// the destination connection point is not represented in the graph
		return;
	}
	
	// find the input nodule for the connection if there is one
	Gaffer::NodePtr srcNode = srcPlug->node();
	NodeGadgetPtr srcNodeGadget = findNodeGadget( srcNode.get() );
	NodulePtr srcNodule = 0;
	if( srcNodeGadget )
	{
		srcNodule = srcNodeGadget->nodule( srcPlug );
	}
		
	ConnectionGadgetPtr connection = new ConnectionGadget( srcNodule, dstNodule );
	addChild( connection );

	m_connectionGadgets[dstPlug] = connection.get();
}

void GraphGadget::removeConnectionGadgets( const Gaffer::GraphComponent *plugParent )
{
	
	/// \todo I think this could be faster if we could iterate over just the nodules rather than all the plugs. Perhaps
	/// we could make it easy to recurse over all the Nodules of a NodeGadget if we had a RecursiveChildIterator for GraphComponents?

	for( Gaffer::PlugIterator pIt( plugParent->children().begin(), plugParent->children().end() ); pIt!=pIt.end(); pIt++ )
	{
		if( (*pIt)->direction() == Gaffer::Plug::In )
		{
			// remove input connection gadgets
			{
				removeConnectionGadget( pIt->get() );
			}
		}
		else
		{
			// make output connection gadgets dangle
			for( Gaffer::Plug::OutputContainer::const_iterator oIt( (*pIt)->outputs().begin() ); oIt!= (*pIt)->outputs().end(); oIt++ )
			{
				ConnectionGadget *connection = findConnectionGadget( *oIt );
				if( connection )
				{
					connection->setNodules( 0, connection->dstNodule() );
				}
			}
		}
		
		if( (*pIt)->isInstanceOf( Gaffer::CompoundPlug::staticTypeId() ) )
		{
			removeConnectionGadgets( pIt->get() );
		}
	}
	
}

void GraphGadget::removeConnectionGadget( const Gaffer::Plug *dstPlug )
{
	ConnectionGadget *connection = findConnectionGadget( dstPlug );
	if( connection )
	{
		m_connectionGadgets.erase( dstPlug );
		removeChild( connection );
	}
}
	
ConnectionGadget *GraphGadget::findConnectionGadget( const Gaffer::Plug *plug ) const
{
	ConnectionGadgetMap::const_iterator it = m_connectionGadgets.find( plug );
	if( it==m_connectionGadgets.end() )
	{
		return 0;
	}
	return it->second;
}
