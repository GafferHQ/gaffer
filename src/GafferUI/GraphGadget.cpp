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

#include "IECore/NullObject.h"

#include "Gaffer/ScriptNode.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/CompoundPlug.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/RecursiveChildIterator.h"
#include "Gaffer/DependencyNode.h"

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
	:	m_dragStartPosition( 0 ), m_lastDragPosition( 0 ), m_dragMode( None ), m_dragReconnectCandidate( 0 ), m_dragReconnectSrcNodule( 0 ), m_dragReconnectDstNodule( 0 )
{
	keyPressSignal().connect( boost::bind( &GraphGadget::keyPressed, this, ::_1,  ::_2 ) );
	buttonPressSignal().connect( boost::bind( &GraphGadget::buttonPress, this, ::_1,  ::_2 ) );
	buttonReleaseSignal().connect( boost::bind( &GraphGadget::buttonRelease, this, ::_1,  ::_2 ) );
	dragBeginSignal().connect( boost::bind( &GraphGadget::dragBegin, this, ::_1, ::_2 ) );
	dragEnterSignal().connect( boost::bind( &GraphGadget::dragEnter, this, ::_1, ::_2 ) );
	dragMoveSignal().connect( boost::bind( &GraphGadget::dragMove, this, ::_1, ::_2 ) );
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

size_t GraphGadget::connectionGadgets( const Gaffer::Plug *plug, std::vector<ConnectionGadget *> &connections, const Gaffer::Set *excludedNodes )
{
	if( plug->direction() == Gaffer::Plug::In )
	{
		const Gaffer::Plug *input = plug->getInput<Gaffer::Plug>();
		if( input )
		{
			if( !excludedNodes || !excludedNodes->contains( input->node() ) )
			{
				ConnectionGadget *connection = connectionGadget( plug );
				if( connection && connection->srcNodule() )
				{
					connections.push_back( connection );
				}
			}
		}
	}
	else
	{
		const Gaffer::Plug::OutputContainer &outputs = plug->outputs();
		for( Gaffer::Plug::OutputContainer::const_iterator it = outputs.begin(), eIt = outputs.end(); it != eIt; ++it )
		{
			if( excludedNodes && excludedNodes->contains( (*it)->node() ) )
			{
				continue;
			}
			ConnectionGadget *connection = connectionGadget( *it );
			if( connection && connection->srcNodule() )
			{
				connections.push_back( connection );
			}
		}
	}
	return connections.size();
}

size_t GraphGadget::connectionGadgets( const Gaffer::Plug *plug, std::vector<const ConnectionGadget *> &connections, const Gaffer::Set *excludedNodes ) const
{
	// preferring naughty casts over maintaining two identical implementations
	return const_cast<GraphGadget *>( this )->connectionGadgets( plug, reinterpret_cast<std::vector<ConnectionGadget *> &>( connections ), excludedNodes );
}
		
size_t GraphGadget::connectionGadgets( const Gaffer::Node *node, std::vector<ConnectionGadget *> &connections, const Gaffer::Set *excludedNodes )
{
	for( Gaffer::RecursivePlugIterator it( node ); it != it.end(); ++it )
	{
		this->connectionGadgets( it->get(), connections, excludedNodes );
	}
	
	return connections.size();
}

size_t GraphGadget::connectionGadgets( const Gaffer::Node *node, std::vector<const ConnectionGadget *> &connections, const Gaffer::Set *excludedNodes ) const
{
	for( Gaffer::RecursivePlugIterator it( node ); it != it.end(); ++it )
	{
		this->connectionGadgets( it->get(), connections, excludedNodes );
	}
	
	return connections.size();
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

NodeGadget *GraphGadget::nodeGadgetAt( const IECore::LineSegment3f &lineInGadgetSpace ) const
{
	const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
				
	std::vector<GadgetPtr> gadgetsUnderMouse;
	viewportGadget->gadgetsAt(
		viewportGadget->gadgetToRasterSpace( lineInGadgetSpace.p0, this ),
		gadgetsUnderMouse
	);
				
	if( !gadgetsUnderMouse.size() )
	{
		return 0;
	}
	
	NodeGadget *nodeGadget = runTimeCast<NodeGadget>( gadgetsUnderMouse[0] );
	if( !nodeGadget )
	{
		nodeGadget = gadgetsUnderMouse[0]->ancestor<NodeGadget>();
	}

	return nodeGadget;
}

ConnectionGadget *GraphGadget::connectionGadgetAt( const IECore::LineSegment3f &lineInGadgetSpace ) const
{
	const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
	
	std::vector<GadgetPtr> gadgetsUnderMouse;
	viewportGadget->gadgetsAt( viewportGadget->gadgetToRasterSpace( lineInGadgetSpace.p0, this ), gadgetsUnderMouse );
	
	if ( !gadgetsUnderMouse.size() )
	{
		return 0;
	}
	
	ConnectionGadget *connectionGadget = runTimeCast<ConnectionGadget>( gadgetsUnderMouse[0] );
	if ( !connectionGadget )
	{
		connectionGadget = gadgetsUnderMouse[0]->ancestor<ConnectionGadget>();
	}
	
	return connectionGadget;
}

ConnectionGadget *GraphGadget::reconnectionGadgetAt( NodeGadget *gadget, const IECore::LineSegment3f &lineInGadgetSpace ) const
{
	std::vector<GadgetPtr> gadgetsUnderMouse;
	
	Imath::V3f center = gadget->transformedBound( this ).center();
	const Imath::V3f corner0 = center - Imath::V3f( 2, 2, 1 );
	const Imath::V3f corner1 = center + Imath::V3f( 2, 2, 1 );
	
	std::vector<IECoreGL::HitRecord> selection;
	{
		ViewportGadget::SelectionScope selectionScope( corner0, corner1, this, selection, IECoreGL::Selector::IDRender );
		
		const Style *s = style();
		s->bind();
		
		for ( ChildContainer::const_iterator it = children().begin(); it != children().end(); ++it )
		{
			if ( ConnectionGadget *c = IECore::runTimeCast<ConnectionGadget>( it->get() ) )
			{
				// don't consider the node's own connections, or connections without a source nodule
				if ( c->srcNodule() && gadget->node() != c->srcNodule()->plug()->node() && gadget->node() != c->dstNodule()->plug()->node() )
				{
					c->render( s );
				}
			}
		}
	}
	
	for ( std::vector<IECoreGL::HitRecord>::const_iterator it = selection.begin(); it != selection.end(); ++it )
	{
		GadgetPtr gadget = Gadget::select( it->name.value() );
		if ( gadget )
		{
			return runTimeCast<ConnectionGadget>( gadget );
		}
	}
	
	return 0;
}

void GraphGadget::doRender( const Style *style ) const
{
	glDisable( GL_DEPTH_TEST );
	
	// render connection first so they go underneath
	for( ChildContainer::const_iterator it=children().begin(); it!=children().end(); it++ )
	{
		ConnectionGadget *c = IECore::runTimeCast<ConnectionGadget>( it->get() );
		if ( c && c != m_dragReconnectCandidate )
		{
			c->render( style );
		}
	}

	// render the new drag connections if they exist
	if ( m_dragReconnectCandidate )
	{
		if ( m_dragReconnectDstNodule )
		{
			const Nodule *srcNodule = m_dragReconnectCandidate->srcNodule();
			const NodeGadget *srcNodeGadget = nodeGadget( srcNodule->plug()->node() );
			const Imath::V3f srcP = srcNodule->fullTransform( this ).translation();
			const Imath::V3f dstP = m_dragReconnectDstNodule->fullTransform( this ).translation();
			const Imath::V3f dstTangent = nodeGadget( m_dragReconnectDstNodule->plug()->node() )->noduleTangent( m_dragReconnectDstNodule );
			/// \todo: can there be a highlighted/dashed state?
			style->renderConnection( srcP, srcNodeGadget->noduleTangent( srcNodule ), dstP, dstTangent, Style::HighlightedState );
		}
		
		if ( m_dragReconnectSrcNodule )
		{
			const Nodule *dstNodule = m_dragReconnectCandidate->dstNodule();
			const NodeGadget *dstNodeGadget = nodeGadget( dstNodule->plug()->node() );
			const Imath::V3f srcP = m_dragReconnectSrcNodule->fullTransform( this ).translation();
			const Imath::V3f dstP = dstNodule->fullTransform( this ).translation();
			const Imath::V3f srcTangent = nodeGadget( m_dragReconnectSrcNodule->plug()->node() )->noduleTangent( m_dragReconnectSrcNodule );
			/// \todo: can there be a highlighted/dashed state?
			style->renderConnection( srcP, srcTangent, dstP, dstNodeGadget->noduleTangent( dstNodule ), Style::HighlightedState );
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
	if( m_dragMode == Selecting )
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
	if( event.key == "D" )
	{
		/// \todo This functionality would be better provided by a config file,
		/// rather than being hardcoded in here. For that to be done easily we
		/// need a static keyPressSignal() in Widget, which needs figuring out
		/// some more before we commit to it. In the meantime, this will do.
		Gaffer::UndoContext undoContext( m_scriptNode );
		Gaffer::Set *selection = m_scriptNode->selection();
		for( size_t i = 0, s = selection->size(); i != s; i++ )
		{
			Gaffer::DependencyNode *node = IECore::runTimeCast<Gaffer::DependencyNode>( selection->member( i ) );
			if( node && findNodeGadget( node ) )
			{
				Gaffer::BoolPlug *enabledPlug = node->enabledPlug();
				if( enabledPlug && enabledPlug->settable() )
				{
					enabledPlug->setValue( !enabledPlug->getValue() );
				}
			}
		}
	}
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
			// background click. clear selection unless shift is
			// held, in which case we're expecting a shift drag
			// to add to the selection.
			if( !(event.modifiers & ButtonEvent::Shift) )
			{
				m_scriptNode->selection()->clear();
			}
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
	else if( event.buttons == ButtonEvent::Middle )
	{
		// potentially the start of a middle button drag on a node
		return nodeGadgetAt( event.line );		
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
	
	m_dragMode = None;
	m_dragStartPosition = m_lastDragPosition = V2f( i.x, i.y );
	
	NodeGadget *nodeGadget = nodeGadgetAt( event.line );
	if( event.buttons == ButtonEvent::Left )
	{
		if( nodeGadget && m_scriptNode->selection()->contains( nodeGadget->node() ) )
		{
			m_dragMode = Moving;
			// we have to return an object to start the drag but the drag we're
			// starting is for our purposes only, so we return an object that won't
			// be accepted by any other drag targets.
			return IECore::NullObject::defaultNullObject();
		}
		else if( !nodeGadget )
		{
			m_dragMode = Selecting;
			return IECore::NullObject::defaultNullObject();
		}
	}
	else if( event.buttons == ButtonEvent::Middle )
	{
		if( nodeGadget )
		{
			m_dragMode = Sending;
			if( m_scriptNode->selection()->contains( nodeGadget->node() ) )
			{
				return m_scriptNode->selection();
			}
			else
			{
				return nodeGadget->node();
			}
		}
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

	if( event.sourceGadget != this )
	{
		return false;
	}

	if( m_dragMode == Moving )
	{
		calculateDragSnapOffsets( m_scriptNode->selection() );
		
		V2f pos = V2f( i.x, i.y );
		offsetNodes( m_scriptNode->selection(), pos - m_lastDragPosition );
		m_lastDragPosition = pos;
		renderRequestSignal()( this );
		return true;
	}
	else if( m_dragMode == Selecting )
	{
		m_lastDragPosition = V2f( i.x, i.y );
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
	
	if( m_dragMode == Moving )
	{
		// snap the position using the offsets precomputed in calculateDragSnapOffsets()
		V2f pos = V2f( i.x, i.y );
		for( int axis = 0; axis <= 1; ++axis )
		{
			const std::vector<float> &snapOffsets = m_dragSnapOffsets[axis];

			float offset = pos[axis] - m_dragStartPosition[axis];
			float snappedDist = Imath::limits<float>::max();
			float snappedOffset = offset;
			vector<float>::const_iterator it = lower_bound( snapOffsets.begin(), snapOffsets.end(), offset );
			if( it != snapOffsets.end() )
			{
				snappedOffset = *it;
				snappedDist = fabs( offset - *it );
			}
			if( it != snapOffsets.begin() )
			{
				it--;
				if( fabs( offset - *it ) < snappedDist )
				{
					snappedDist = fabs( offset - *it );
					snappedOffset = *it;
				}
			}

			if( snappedDist < 1.5 )
			{
				pos[axis] = snappedOffset + m_dragStartPosition[axis];
			}
		}
		
		// move all the nodes using the snapped offset
		offsetNodes( m_scriptNode->selection(), pos - m_lastDragPosition );
		m_lastDragPosition = pos;
		updateDragReconnectCandidate( event );
		renderRequestSignal()( this );
		return true;
	}
	else
	{
		// we're drag selecting
		m_lastDragPosition = V2f( i.x, i.y );
		renderRequestSignal()( this );
		return true;
	}
		
	assert( 0 ); // shouldn't get here
	return false;
}

void GraphGadget::updateDragReconnectCandidate( const DragDropEvent &event )
{
	m_dragReconnectCandidate = 0;
	m_dragReconnectSrcNodule = 0;
	m_dragReconnectDstNodule = 0;
	
	if ( m_scriptNode->selection()->size() != 1 )
	{
		return;
	}
	
	// make sure the connection applies to this node.
	Gaffer::Node *node = IECore::runTimeCast<Gaffer::Node>( m_scriptNode->selection()->member( 0 ) );
	NodeGadget *selNodeGadget = nodeGadget( node );
	if ( !node || !selNodeGadget )
	{
		return;
	}
	
	m_dragReconnectCandidate = reconnectionGadgetAt( selNodeGadget, event.line );
	if ( !m_dragReconnectCandidate )
	{
		return;
	}
	
	// we don't want to reconnect the selected node to itself
	Gaffer::Plug *srcPlug = m_dragReconnectCandidate->srcNodule()->plug();
	Gaffer::Plug *dstPlug = m_dragReconnectCandidate->dstNodule()->plug();
	if ( srcPlug->node() == node || dstPlug->node() == node )
	{
		m_dragReconnectCandidate = 0;
		return;
	}
	
	Gaffer::DependencyNode *depNode = IECore::runTimeCast<Gaffer::DependencyNode>( node );
	for ( Gaffer::RecursiveOutputPlugIterator cIt( node ); cIt != cIt.end(); ++cIt )
	{
		// must be compatible
		Gaffer::Plug *p = cIt->get();
		if ( !dstPlug->acceptsInput( p ) )
		{
			continue;
		}
		
		// must have a nodule
		m_dragReconnectSrcNodule = selNodeGadget->nodule( p );
		if ( !m_dragReconnectSrcNodule )
		{
			continue;
		}
		
		// must not be connected to a nodule
		for ( Gaffer::Plug::OutputContainer::const_iterator oIt = p->outputs().begin(); oIt != p->outputs().end(); ++oIt )
		{
			NodeGadget *oNodeGadget = nodeGadget( (*oIt)->node() );
			if ( oNodeGadget && oNodeGadget->nodule( *oIt ) )
			{
				m_dragReconnectSrcNodule = 0;
				break;
			}
		}
		
		if ( !m_dragReconnectSrcNodule )
		{
			continue;
		}
		
		if ( !depNode )
		{
			// found the best option
			break;
		}
		
		// make sure its corresponding input is also free
		if ( Gaffer::Plug *in = depNode->correspondingInput( p ) )
		{
			if ( in->getInput<Gaffer::Plug>() )
			{
				m_dragReconnectSrcNodule = 0;
				continue;
			}
			
			m_dragReconnectDstNodule = selNodeGadget->nodule( in );
			if ( m_dragReconnectDstNodule )
			{
				break;
			}
		}
	}
	
	// check input plugs on non-dependencyNodes
	if ( !depNode && !m_dragReconnectDstNodule )
	{
		for ( Gaffer::RecursiveInputPlugIterator cIt( node ); cIt != cIt.end(); ++cIt )
		{
			Gaffer::Plug *p = cIt->get();
			if ( !p->getInput<Gaffer::Plug>() && p->acceptsInput( srcPlug ) )
			{
				m_dragReconnectDstNodule = selNodeGadget->nodule( p );
				if ( m_dragReconnectDstNodule )
				{
					break;
				}
			}
		}
	}
	
	if ( !m_dragReconnectSrcNodule && !m_dragReconnectDstNodule )
	{
		m_dragReconnectCandidate = 0;
	}
}

bool GraphGadget::dragEnd( GadgetPtr gadget, const DragDropEvent &event )
{
	DragMode dragMode = m_dragMode;
	m_dragMode = None;
	
	if( !m_scriptNode )
	{
		return false;
	}
	
	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return false;
	}
	
	if( dragMode == Moving )
	{
		if ( m_dragReconnectCandidate )
		{
			if ( m_dragReconnectDstNodule || m_dragReconnectSrcNodule )
			{
				Gaffer::Plug *srcPlug = m_dragReconnectCandidate->srcNodule()->plug();
				Gaffer::Plug *dstPlug = m_dragReconnectCandidate->dstNodule()->plug();
				
				Gaffer::UndoContext undoContext( m_scriptNode );
				
				if ( m_dragReconnectDstNodule )
				{
					m_dragReconnectDstNodule->plug()->setInput( srcPlug );
					dstPlug->setInput( 0 );
				}

				if ( m_dragReconnectSrcNodule )
				{
					dstPlug->setInput( m_dragReconnectSrcNodule->plug() );
				}
			}
		}
		
		m_dragReconnectCandidate = 0;
		renderRequestSignal()( this );
	}
	else if( dragMode == Selecting )
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

void GraphGadget::calculateDragSnapOffsets( Gaffer::Set *nodes )
{
	m_dragSnapOffsets[0].clear();
	m_dragSnapOffsets[1].clear();
	
	std::vector<const ConnectionGadget *> connections;
	for( size_t i = 0, s = nodes->size(); i < s; ++i )
	{
		Gaffer::Node *node = runTimeCast<Gaffer::Node>( nodes->member( i ) );
		if( !node )
		{
			continue;
		}
	
		connections.clear();
		connectionGadgets( node, connections, nodes );
		
		for( std::vector<const ConnectionGadget *>::const_iterator it = connections.begin(), eIt = connections.end(); it != eIt; ++it )
		{
			// get the node gadgets at either end of the connection
			
			const ConnectionGadget *connection = *it;
			const Nodule *srcNodule = connection->srcNodule();
			const Nodule *dstNodule = connection->dstNodule();
			const NodeGadget *srcNodeGadget = srcNodule->ancestor<NodeGadget>();
			const NodeGadget *dstNodeGadget = dstNodule->ancestor<NodeGadget>();
			
			if( !srcNodeGadget || !dstNodeGadget )
			{
				continue;
			}
			
			// check that the connection tangents are opposed - if not we don't want to snap
			
			V3f srcTangent = srcNodeGadget->noduleTangent( srcNodule );
			V3f dstTangent = dstNodeGadget->noduleTangent( dstNodule );
				
			if( srcTangent.dot( dstTangent ) > -0.5f )
			{
				continue;
			}
			
			// compute an offset that will bring the src and destination nodules into line
			
			const int snapAxis = fabs( srcTangent.x ) > 0.5 ? 1 : 0;
						
			V3f srcPosition = V3f( 0 ) * srcNodule->fullTransform();
			V3f dstPosition = V3f( 0 ) * dstNodule->fullTransform();
			float offset = srcPosition[snapAxis] - dstPosition[snapAxis];
				
			if( dstNodule->plug()->node() != node )
			{
				offset *= -1;
			}
			
			m_dragSnapOffsets[snapAxis].push_back( offset );
			
			// compute an offset that will bring the src and destination nodes into line
			
			V3f srcNodePosition = V3f( 0 ) * srcNodeGadget->fullTransform();
			V3f dstNodePosition = V3f( 0 ) * dstNodeGadget->fullTransform();
			offset = srcNodePosition[snapAxis] - dstNodePosition[snapAxis];
				
			if( dstNodule->plug()->node() != node )
			{
				offset *= -1;
			}

			m_dragSnapOffsets[snapAxis].push_back( offset );

			// compute an offset that will position the node snugly next to its input
			// in the other axis.
			
			Box3f srcNodeBound = srcNodeGadget->transformedBound( 0 );
			Box3f dstNodeBound = dstNodeGadget->transformedBound( 0 );
			
			const int otherAxis = snapAxis == 1 ? 0 : 1;
			if( otherAxis == 1 )
			{
				offset = dstNodeBound.max[otherAxis] - srcNodeBound.min[otherAxis] + 1.0f;
			}
			else
			{
				offset = dstNodeBound.min[otherAxis] - srcNodeBound.max[otherAxis] - 1.0f;				
			}
			
			if( dstNodule->plug()->node() == node )
			{
				offset *= -1;
			}
			
			m_dragSnapOffsets[otherAxis].push_back( offset );
		}
	}
	
	// sort and remove duplicates so that we can use lower_bound() to find appropriate
	// snap points in dragMove().
	
	for( int axis = 0; axis <= 1; ++axis )
	{
		std::sort( m_dragSnapOffsets[axis].begin(), m_dragSnapOffsets[axis].end() );
		m_dragSnapOffsets[axis].erase( std::unique( m_dragSnapOffsets[axis].begin(), m_dragSnapOffsets[axis].end()), m_dragSnapOffsets[axis].end() );
	}
	
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
		m_layout->positionNode( this, node );
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
						assert( connection->dstNodule()->plug()->getInput<Gaffer::Plug>() == *pIt ); 
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
	Gaffer::Plug *srcPlug = dstPlug->getInput<Gaffer::Plug>();
	if( !srcPlug )
	{
		// there is no connection
		return;
	}
	
	Gaffer::Node *dstNode = dstPlug->node();
	Nodule *dstNodule = findNodeGadget( dstNode )->nodule( dstPlug );
	if( !dstNodule )
	{
		// the destination connection point is not represented in the graph
		return;
	}
	
	Gaffer::Node *srcNode = srcPlug->node();
	if( srcNode == dstNode )
	{
		// we don't want to visualise connections between plugs
		// on the same node.
		return;
	}
	
	// find the input nodule for the connection if there is one
	NodeGadget *srcNodeGadget = findNodeGadget( srcNode );
	Nodule *srcNodule = 0;
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
