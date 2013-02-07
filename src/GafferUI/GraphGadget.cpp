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
#include "Gaffer/CompoundPlug.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/CompoundNumericPlug.h"

#include "GafferUI/GraphGadget.h"
#include "GafferUI/NodeGadget.h"
#include "GafferUI/ButtonEvent.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/ConnectionGadget.h"
#include "GafferUI/Style.h"
#include "GafferUI/ViewportGadget.h"
#include "GafferUI/StandardGraphLayout.h"

using namespace GafferUI;
using namespace Imath;
using namespace IECore;
using namespace std;

//////////////////////////////////////////////////////////////////////////
// GraphGadget implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( GraphGadget );

GraphGadget::GraphGadget( Gaffer::NodePtr root, Gaffer::SetPtr filter )
	:	m_dragStartPosition( 0 ), m_lastDragPosition( 0 ), m_dragSelecting( false )
{
	keyPressSignal().connect( boost::bind( &GraphGadget::keyPressed, this, ::_1,  ::_2 ) );
	buttonPressSignal().connect( boost::bind( &GraphGadget::buttonPress, this, ::_1,  ::_2 ) );
	buttonReleaseSignal().connect( boost::bind( &GraphGadget::buttonRelease, this, ::_1,  ::_2 ) );
	dragBeginSignal().connect( boost::bind( &GraphGadget::dragBegin, this, ::_1, ::_2 ) );
	dragEnterSignal().connect( boost::bind( &GraphGadget::dragEnter, this, ::_1, ::_2 ) );
	dragMoveSignal().connect( boost::bind( &GraphGadget::dragMove, this, ::_1, ::_2 ) );
	dragLeaveSignal().connect( boost::bind( &GraphGadget::dragLeave, this, ::_1, ::_2 ) );
	dragEndSignal().connect( boost::bind( &GraphGadget::dragEnd, this, ::_1, ::_2 ) );

	m_layout = new StandardGraphLayout;
	
	setRoot( root, filter );
}

GraphGadget::~GraphGadget()
{
}

Gaffer::Node *GraphGadget::getRoot()
{
	return m_root.get();
}

const Gaffer::Node *GraphGadget::getRoot() const
{
	return m_root.get();
}

void GraphGadget::setRoot( Gaffer::NodePtr root, Gaffer::SetPtr filter )
{
	if( root == m_root && filter == m_filter )
	{
		return;
	}

	bool rootChanged = false;
	if( root != m_root )
	{
		rootChanged = true;
		m_root = root;
		m_rootChildAddedConnection = m_root->childAddedSignal().connect( boost::bind( &GraphGadget::rootChildAdded, this, ::_1, ::_2 ) );
		m_rootChildRemovedConnection = m_root->childRemovedSignal().connect( boost::bind( &GraphGadget::rootChildRemoved, this, ::_1, ::_2 ) );
	}
	
	m_scriptNode = runTimeCast<Gaffer::ScriptNode>( m_root );
	if( !m_scriptNode )
	{
		m_scriptNode = m_root->scriptNode();
	}
	
	if( filter != m_filter )
	{
		setFilter( filter );
		// setFilter() will call updateGraph() for us.
	}
	else
	{
		updateGraph();
	}

	if( rootChanged )
	{
		m_rootChangedSignal( this );
	}
}

GraphGadget::GraphGadgetSignal &GraphGadget::rootChangedSignal()
{
	return m_rootChangedSignal;
}

Gaffer::Set *GraphGadget::getFilter()
{
	return m_filter;
}

const Gaffer::Set *GraphGadget::getFilter() const
{
	return m_filter;
}

void GraphGadget::setFilter( Gaffer::SetPtr filter )
{
	if( filter == m_filter )
	{
		return;
	}
	
	m_filter = filter;
	if( m_filter )
	{
		m_filterMemberAddedConnection = m_filter->memberAddedSignal().connect( boost::bind( &GraphGadget::filterMemberAdded, this, ::_1,  ::_2 ) );
		m_filterMemberRemovedConnection = m_filter->memberRemovedSignal().connect( boost::bind( &GraphGadget::filterMemberRemoved, this, ::_1,  ::_2 ) );
	}
	else
	{
		m_filterMemberAddedConnection = boost::signals::connection();
		m_filterMemberRemovedConnection = boost::signals::connection();
	}
	
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

void GraphGadget::setNodePosition( Gaffer::Node *node, const Imath::V2f &position )
{
	Gaffer::V2fPlug *plug = node->getChild<Gaffer::V2fPlug>( "__uiPosition" );
	if( !plug )
	{
		plug = new Gaffer::V2fPlug( "__uiPosition", Gaffer::Plug::In );
		plug->setFlags( Gaffer::Plug::Dynamic, true );
		node->addChild( plug );
	}
	
	plug->setValue( position );
}

Imath::V2f GraphGadget::getNodePosition( Gaffer::Node *node ) const
{
	Gaffer::V2fPlug *plug = node->getChild<Gaffer::V2fPlug>( "__uiPosition" );
	return plug ? plug->getValue() : V2f( 0 );
}

void GraphGadget::setLayout( GraphLayoutPtr layout )
{
	m_layout = layout;
}

GraphLayout *GraphGadget::getLayout()
{
	return m_layout;
}

const GraphLayout *GraphGadget::getLayout() const
{
	return m_layout;
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

void GraphGadget::rootChildAdded( Gaffer::GraphComponent *root, Gaffer::GraphComponent *child )
{
	Gaffer::Node *node = IECore::runTimeCast<Gaffer::Node>( child );
	if( node && ( !m_filter || m_filter->contains( node ) ) )
	{
		if( !findNodeGadget( node ) )
		{	addNodeGadget( node );
			addConnectionGadgets( node );   
		}
	}
}

void GraphGadget::rootChildRemoved( Gaffer::GraphComponent *root, Gaffer::GraphComponent *child )
{
	Gaffer::Node *node = IECore::runTimeCast<Gaffer::Node>( child );
	if( node )
	{
		removeNodeGadget( node );
	}
}

void GraphGadget::filterMemberAdded( Gaffer::Set *set, IECore::RunTimeTyped *member )
{
	Gaffer::Node *node = IECore::runTimeCast<Gaffer::Node>( member );
	if( node && node->parent<Gaffer::Node>() == m_root )
	{
		if( !findNodeGadget( node ) )
		{	addNodeGadget( node );
			addConnectionGadgets( node );   
		}
	}
}

void GraphGadget::filterMemberRemoved( Gaffer::Set *set, IECore::RunTimeTyped *member )
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
	if( name=="__uiPosition" )
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
			Gaffer::V2fPlug *p = node->getChild<Gaffer::V2fPlug>( "__uiPosition" );
			p->setValue( p->getValue() + offset );
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
		if( (m_filter && !m_filter->contains( node )) || node->parent<Gaffer::Node>() != m_root )
		{
			removeNodeGadget( node );
		}
	}
		
	// now make sure we have gadgets for all the nodes we're meant to display
	for( Gaffer::NodeIterator it( m_root ); it != it.end(); it++ )
	{
		if( !m_filter || m_filter->contains( it->get() ) )
		{
			if( !findNodeGadget( it->get() ) )
			{
				addNodeGadget( it->get() );
			}
		}
	}
	
	// and that we have gadgets for each connection
	
	for( Gaffer::NodeIterator it( m_root ); it != it.end(); it++ )
	{
		if( !m_filter || m_filter->contains( it->get() ) )
		{
			addConnectionGadgets( it->get() );
		}
	}

}

void GraphGadget::addNodeGadget( Gaffer::Node *node )
{	
	NodeGadgetPtr nodeGadget = NodeGadget::create( node );
	addChild( nodeGadget );
	
	NodeGadgetEntry nodeGadgetEntry;
	nodeGadgetEntry.inputChangedConnection = node->plugInputChangedSignal().connect( boost::bind( &GraphGadget::inputChanged, this, ::_1 ) );
	nodeGadgetEntry.plugSetConnection = node->plugSetSignal().connect( boost::bind( &GraphGadget::plugSet, this, ::_1 ) );	
	nodeGadgetEntry.gadget = nodeGadget.get();
	
	m_nodeGadgets[node] = nodeGadgetEntry;
	
	// place it if it's not placed already.	
	if( !node->getChild<Gaffer::V2fPlug>( "__uiPosition" ) )
	{
		if( !m_layout->positionNode( this, node ) )
		{
			setNodePosition( node, V2f( 0 ) );
		}
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
	Gaffer::Node *node = nodeGadget->node();
	M44f m;
	
	Gaffer::V2fPlug *p = node->getChild<Gaffer::V2fPlug>( "__uiPosition" );
	if( p )
	{
		V2f t = p->getValue();
	 	m.translate( V3f( t[0], t[1], 0 ) );
	}

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
