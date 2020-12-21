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

#include "GafferUI/GraphGadget.h"

#include "GafferUI/AnnotationsGadget.h"
#include "GafferUI/AuxiliaryConnectionsGadget.h"
#include "GafferUI/BackdropNodeGadget.h"
#include "GafferUI/ButtonEvent.h"
#include "GafferUI/ConnectionGadget.h"
#include "GafferUI/NodeGadget.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/Pointer.h"
#include "GafferUI/StandardGraphLayout.h"
#include "GafferUI/Style.h"
#include "GafferUI/ViewportGadget.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/DependencyNode.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/RecursiveChildIterator.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/TypedPlug.h"

#include "IECore/BoxOps.h"
#include "IECore/Export.h"
#include "IECore/NullObject.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "OpenEXR/ImathPlane.h"
IECORE_POP_DEFAULT_VISIBILITY

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace GafferUI;
using namespace Imath;
using namespace IECore;
using namespace std;

//////////////////////////////////////////////////////////////////////////
// Private utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

bool readOnly( const Gaffer::StandardSet *set )
{
	for( size_t i = 0, s = set->size(); i < s; ++i )
	{
		if( const Gaffer::GraphComponent *g = runTimeCast<const Gaffer::GraphComponent>( set->member( i ) ) )
		{
			if( Gaffer::MetadataAlgo::readOnly( g ) )
			{
				return true;
			}
		}
	}
	return false;
}

const InternedString g_positionPlugName( "__uiPosition" );
const InternedString g_inputConnectionsMinimisedPlugName( "__uiInputConnectionsMinimised" );
const InternedString g_outputConnectionsMinimisedPlugName( "__uiOutputConnectionsMinimised" );
const InternedString g_nodeGadgetTypeName( "nodeGadget:type" );
const InternedString g_auxiliaryConnectionsGadgetName( "__auxiliaryConnections" );
const InternedString g_annotationsGadgetName( "__annotations" );

struct CompareV2fX{
	bool operator()(const Imath::V2f &a, const Imath::V2f &b) const
	{
		return a[0] < b[0];
	}
};

// Action used to set node positions during drags. This implements
// a custom `merge()` operation to avoid excessive memory use when dragging
// large numbers of nodes around for a significant number of substeps. The
// standard merging implemented by `ScriptNode::CompoundAction` works great
// until a drag increment is 0 in one of the XY axes. When that occurs,
// the `setValue()` calls for that axis are optimised out and then
// `CompoundAction::merge()` falls back to a brute-force version
// that keeps all the actions for every single drag increment (because there
// are different numbers of actions from one substep to the next).
//
// Alternative approaches might be :
//
// - Improve `CompoundAction::merge()`. When the simple merge fails we could
//   perhaps construct a secondary map from subject to action, and then attempt
//   to merge all the actions pertaining to the same subject. In the general
//   case there is no guarantee of one action per subject though, so it seems
//   the benefits might be limited to this one use case anyway.
// - Allow `CompoundPlug::setValue()` to force all child plugs to be set, even
//   when one or more aren't changing. This seems counter to expectations from
//   the point of view of an observer of `plugSetSignal()` though.
//
// For now at least, I prefer the isolated scope of `SetPositionsAction` to the
// more core alternatives.
class SetPositionsAction : public Gaffer::Action
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( SetPositionsAction, GraphGadgetSetPositionsActionTypeId, Gaffer::Action );

		SetPositionsAction( Gaffer::Node *root )
			:	m_scriptNode( root->scriptNode() )
		{
		}

		void addOffset( Gaffer::V2fPlugPtr plug, const V2f &offset )
		{
			const V2f v = plug->getValue();
			m_positions[plug] = { v, v + offset };
		}

	protected :

		Gaffer::GraphComponent *subject() const override
		{
			return m_scriptNode;
		}

		void doAction() override
		{
			// The `setValue()` calls we make are themselves undoable, so we must disable
			// undo to stop them being recorded redundantly.
			Gaffer::UndoScope scope( m_scriptNode, Gaffer::UndoScope::Disabled );
			for( auto &p : m_positions )
			{
				p.first->setValue( p.second.newPosition );
			}
		}

		void undoAction() override
		{
			// The `setValue()` calls we make are themselves undoable, so we must disable
			// undo to stop them being recorded redundantly.
			Gaffer::UndoScope scope( m_scriptNode, Gaffer::UndoScope::Disabled );
			for( auto &p : m_positions )
			{
				p.first->setValue( p.second.oldPosition );
			}
		}

		bool canMerge( const Action *other ) const override
		{
			if( !Action::canMerge( other ) )
			{
				return false;
			}

			const auto a = runTimeCast<const SetPositionsAction>( other );
			return a && a->m_scriptNode == m_scriptNode;
		}

		void merge( const Action *other ) override
		{
			auto a = static_cast<const SetPositionsAction *>( other );
			for( auto &p : a->m_positions )
			{
				auto inserted = m_positions.insert( p );
				if( !inserted.second )
				{
					inserted.first->second.newPosition = p.second.newPosition;
				}
			}
		}

	private :

		Gaffer::ScriptNode *m_scriptNode;

		struct Positions
		{
			V2f oldPosition;
			V2f newPosition;
		};

		using PositionsMap = std::map<Gaffer::V2fPlugPtr, Positions>;
		PositionsMap m_positions;

};

IE_CORE_DEFINERUNTIMETYPED( SetPositionsAction );
IE_CORE_DECLAREPTR( SetPositionsAction )

} // namespace

//////////////////////////////////////////////////////////////////////////
// GraphGadget implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( GraphGadget );

GraphGadget::GraphGadget( Gaffer::NodePtr root, Gaffer::SetPtr filter )
	:	m_dragStartPosition( 0 ), m_lastDragPosition( 0 ), m_dragMode( None ), m_dragReconnectCandidate( nullptr ), m_dragReconnectSrcNodule( nullptr ), m_dragReconnectDstNodule( nullptr ), m_dragMergeGroupId( 0 )
{
	keyPressSignal().connect( boost::bind( &GraphGadget::keyPressed, this, ::_1,  ::_2 ) );
	buttonPressSignal().connect( boost::bind( &GraphGadget::buttonPress, this, ::_1,  ::_2 ) );
	buttonReleaseSignal().connect( boost::bind( &GraphGadget::buttonRelease, this, ::_1,  ::_2 ) );
	dragBeginSignal().connect( boost::bind( &GraphGadget::dragBegin, this, ::_1, ::_2 ) );
	dragEnterSignal().connect( boost::bind( &GraphGadget::dragEnter, this, ::_1, ::_2 ) );
	dragMoveSignal().connect( boost::bind( &GraphGadget::dragMove, this, ::_1, ::_2 ) );
	dragEndSignal().connect( boost::bind( &GraphGadget::dragEnd, this, ::_1, ::_2 ) );

	Gaffer::Metadata::nodeValueChangedSignal().connect(
		boost::bind( &GraphGadget::nodeMetadataChanged, this, ::_1, ::_2, ::_3 )
	);

	m_layout = new StandardGraphLayout;

	setChild( g_auxiliaryConnectionsGadgetName, new AuxiliaryConnectionsGadget() );
	setChild( g_annotationsGadgetName, new AnnotationsGadget() );

	setRoot( root, filter );
}

GraphGadget::~GraphGadget()
{
	removeChild( auxiliaryConnectionsGadget() );
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
	Gaffer::NodePtr previousRoot = m_root;
	if( root != m_root )
	{
		rootChanged = true;
		m_root = root;
		m_rootChildAddedConnection = m_root->childAddedSignal().connect( boost::bind( &GraphGadget::rootChildAdded, this, ::_1, ::_2 ) );
		m_rootChildRemovedConnection = m_root->childRemovedSignal().connect( boost::bind( &GraphGadget::rootChildRemoved, this, ::_1, ::_2 ) );
	}

	Gaffer::ScriptNodePtr scriptNode = runTimeCast<Gaffer::ScriptNode>( m_root );
	if( !scriptNode )
	{
		scriptNode = m_root->scriptNode();
	}

	if( scriptNode != m_scriptNode )
	{
		m_scriptNode = scriptNode;
		if( m_scriptNode )
		{
			m_selectionMemberAddedConnection = m_scriptNode->selection()->memberAddedSignal().connect(
				boost::bind( &GraphGadget::selectionMemberAdded, this, ::_1, ::_2 )
			);
			m_selectionMemberRemovedConnection = m_scriptNode->selection()->memberRemovedSignal().connect(
				boost::bind( &GraphGadget::selectionMemberRemoved, this, ::_1, ::_2 )
			);
		}
		else
		{
			m_selectionMemberAddedConnection.disconnect();
			m_selectionMemberAddedConnection.disconnect();
		}
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
		m_rootChangedSignal( this, previousRoot.get() );
	}
}

GraphGadget::RootChangedSignal &GraphGadget::rootChangedSignal()
{
	return m_rootChangedSignal;
}

Gaffer::Set *GraphGadget::getFilter()
{
	return m_filter.get();
}

const Gaffer::Set *GraphGadget::getFilter() const
{
	return m_filter.get();
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
				if( ConnectionGadget *connection = connectionGadget( plug ) )
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
			if( ConnectionGadget *connection = connectionGadget( *it ) )
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
	for( Gaffer::RecursivePlugIterator it( node ); !it.done(); ++it )
	{
		this->connectionGadgets( it->get(), connections, excludedNodes );
	}

	return connections.size();
}

size_t GraphGadget::connectionGadgets( const Gaffer::Node *node, std::vector<const ConnectionGadget *> &connections, const Gaffer::Set *excludedNodes ) const
{
	for( Gaffer::RecursivePlugIterator it( node ); !it.done(); ++it )
	{
		this->connectionGadgets( it->get(), connections, excludedNodes );
	}

	return connections.size();
}

AuxiliaryConnectionsGadget *GraphGadget::auxiliaryConnectionsGadget()
{
	return getChild<AuxiliaryConnectionsGadget>( g_auxiliaryConnectionsGadgetName );
}

const AuxiliaryConnectionsGadget *GraphGadget::auxiliaryConnectionsGadget() const
{
	return getChild<AuxiliaryConnectionsGadget>( g_auxiliaryConnectionsGadgetName );
}

size_t GraphGadget::upstreamNodeGadgets( const Gaffer::Node *node, std::vector<NodeGadget *> &upstreamNodeGadgets, size_t degreesOfSeparation )
{
	NodeGadget *g = nodeGadget( node );
	if( !g )
	{
		return 0;
	}

	std::set<NodeGadget *> n;
	connectedNodeGadgetsWalk( g, n, Gaffer::Plug::In, degreesOfSeparation );
	std::copy( n.begin(), n.end(), back_inserter( upstreamNodeGadgets ) );
	return 0;
}

size_t GraphGadget::upstreamNodeGadgets( const Gaffer::Node *node, std::vector<const NodeGadget *> &upstreamNodeGadgets, size_t degreesOfSeparation ) const
{
	// preferring naughty casts over maintaining two identical implementations
	return const_cast<GraphGadget *>( this )->upstreamNodeGadgets( node, reinterpret_cast<std::vector<NodeGadget *> &>( upstreamNodeGadgets ), degreesOfSeparation );
}

size_t GraphGadget::downstreamNodeGadgets( const Gaffer::Node *node, std::vector<NodeGadget *> &downstreamNodeGadgets, size_t degreesOfSeparation )
{
	NodeGadget *g = nodeGadget( node );
	if( !g )
	{
		return 0;
	}

	std::set<NodeGadget *> n;
	connectedNodeGadgetsWalk( g, n, Gaffer::Plug::Out, degreesOfSeparation );
	std::copy( n.begin(), n.end(), back_inserter( downstreamNodeGadgets ) );
	return 0;
}

size_t GraphGadget::downstreamNodeGadgets( const Gaffer::Node *node, std::vector<const NodeGadget *> &downstreamNodeGadgets, size_t degreesOfSeparation ) const
{
	// preferring naughty casts over maintaining two identical implementations
	return const_cast<GraphGadget *>( this )->downstreamNodeGadgets( node, reinterpret_cast<std::vector<NodeGadget *> &>( downstreamNodeGadgets ), degreesOfSeparation );
}

size_t GraphGadget::connectedNodeGadgets( const Gaffer::Node *node, std::vector<NodeGadget *> &connectedNodeGadgets, Gaffer::Plug::Direction direction, size_t degreesOfSeparation )
{
	NodeGadget *g = nodeGadget( node );
	if( !g )
	{
		return 0;
	}

	std::set<NodeGadget *> n;
	connectedNodeGadgetsWalk( g, n, direction, degreesOfSeparation );
	if( direction == Gaffer::Plug::Invalid )
	{
		// if we were traversing in both directions, we will have accidentally
		// traversed back to the start point, which we don't want.
		n.erase( nodeGadget( node ) );
	}
	std::copy( n.begin(), n.end(), back_inserter( connectedNodeGadgets ) );
	return 0;
}

size_t GraphGadget::connectedNodeGadgets( const Gaffer::Node *node, std::vector<const NodeGadget *> &connectedNodeGadgets, Gaffer::Plug::Direction direction, size_t degreesOfSeparation ) const
{
	// preferring naughty casts over maintaining two identical implementations
	return const_cast<GraphGadget *>( this )->connectedNodeGadgets( node, reinterpret_cast<std::vector<NodeGadget *> &>( connectedNodeGadgets ), direction, degreesOfSeparation );
}

void GraphGadget::connectedNodeGadgetsWalk( NodeGadget *gadget, std::set<NodeGadget *> &connectedNodeGadgets, Gaffer::Plug::Direction direction, size_t degreesOfSeparation )
{
	if( !degreesOfSeparation )
	{
		return;
	}

	for( Gaffer::RecursivePlugIterator it( gadget->node() ); !it.done(); ++it )
	{
		Gaffer::Plug *plug = it->get();
		if( ( direction != Gaffer::Plug::Invalid ) && ( plug->direction() != direction ) )
		{
			continue;
		}

		if( plug->direction() == Gaffer::Plug::In )
		{
			ConnectionGadget *connection = connectionGadget( plug );
			Nodule *nodule = connection ? connection->srcNodule() : nullptr;
			NodeGadget *inputNodeGadget = nodule ? nodeGadget( nodule->plug()->node() ) : nullptr;
			if( inputNodeGadget )
			{
				if( connectedNodeGadgets.insert( inputNodeGadget ).second )
				{
					// inserted the node for the first time
					connectedNodeGadgetsWalk( inputNodeGadget, connectedNodeGadgets, direction, degreesOfSeparation - 1 );
				}
			}
		}
		else
		{
			// output plug
			for( Gaffer::Plug::OutputContainer::const_iterator oIt = plug->outputs().begin(), eOIt = plug->outputs().end(); oIt != eOIt; oIt++ )
			{
				ConnectionGadget *connection = connectionGadget( *oIt );
				Nodule *nodule = connection ? connection->dstNodule() : nullptr;
				NodeGadget *outputNodeGadget = nodule ? nodeGadget( nodule->plug()->node() ) : nullptr;
				if( outputNodeGadget )
				{
					if( connectedNodeGadgets.insert( outputNodeGadget ).second )
					{
						// inserted the node for the first time
						connectedNodeGadgetsWalk( outputNodeGadget, connectedNodeGadgets, direction, degreesOfSeparation - 1 );
					}
				}
			}
		}
	}
}

size_t GraphGadget::unpositionedNodeGadgets( std::vector<NodeGadget *> &nodeGadgets ) const
{
	for( NodeGadgetMap::const_iterator it = m_nodeGadgets.begin(), eIt = m_nodeGadgets.end(); it != eIt; ++it )
	{
		if( !hasNodePosition( it->first ) )
		{
			nodeGadgets.push_back( it->second.gadget );
		}
	}
	return nodeGadgets.size();
}

void GraphGadget::setNodePosition( Gaffer::Node *node, const Imath::V2f &position )
{
	Gaffer::V2fPlug *plug = nodePositionPlug( node, /* createIfMissing = */ true );
	plug->setValue( position );
}

Imath::V2f GraphGadget::getNodePosition( const Gaffer::Node *node ) const
{
	const Gaffer::V2fPlug *plug = nodePositionPlug( node );
	return plug ? plug->getValue() : V2f( 0 );
}

bool GraphGadget::hasNodePosition( const Gaffer::Node *node ) const
{
	return nodePositionPlug( node );
}

const Gaffer::V2fPlug *GraphGadget::nodePositionPlug( const Gaffer::Node *node ) const
{
	return node->getChild<Gaffer::V2fPlug>( g_positionPlugName );
}

Gaffer::V2fPlug *GraphGadget::nodePositionPlug( Gaffer::Node *node, bool createIfMissing ) const
{
	Gaffer::V2fPlug *plug = node->getChild<Gaffer::V2fPlug>( g_positionPlugName );
	if( plug || !createIfMissing )
	{
		return plug;
	}

	plug = new Gaffer::V2fPlug( g_positionPlugName, Gaffer::Plug::In );
	plug->setFlags( Gaffer::Plug::Dynamic, true );
	node->addChild( plug );

	return plug;
}

void GraphGadget::setNodeInputConnectionsMinimised( Gaffer::Node *node, bool minimised )
{
	if( minimised == getNodeInputConnectionsMinimised( node ) )
	{
		return;
	}

	Gaffer::BoolPlug *p = node->getChild<Gaffer::BoolPlug>( g_inputConnectionsMinimisedPlugName );
	if( !p )
	{
		p = new Gaffer::BoolPlug( g_inputConnectionsMinimisedPlugName, Gaffer::Plug::In, false, Gaffer::Plug::Default | Gaffer::Plug::Dynamic );
		node->addChild( p );
	}
	p->setValue( minimised );
}

bool GraphGadget::getNodeInputConnectionsMinimised( const Gaffer::Node *node ) const
{
	const Gaffer::BoolPlug *p = node->getChild<Gaffer::BoolPlug>( g_inputConnectionsMinimisedPlugName );
	return p ? p->getValue() : false;
}

void GraphGadget::setNodeOutputConnectionsMinimised( Gaffer::Node *node, bool minimised )
{
	if( minimised == getNodeOutputConnectionsMinimised( node ) )
	{
		return;
	}

	Gaffer::BoolPlug *p = node->getChild<Gaffer::BoolPlug>( g_outputConnectionsMinimisedPlugName );
	if( !p )
	{
		p = new Gaffer::BoolPlug( g_outputConnectionsMinimisedPlugName, Gaffer::Plug::In, false, Gaffer::Plug::Default | Gaffer::Plug::Dynamic );
		node->addChild( p );
	}
	p->setValue( minimised );
}

bool GraphGadget::getNodeOutputConnectionsMinimised( const Gaffer::Node *node ) const
{
	const Gaffer::BoolPlug *p = node->getChild<Gaffer::BoolPlug>( g_outputConnectionsMinimisedPlugName );
	return p ? p->getValue() : false;
}

void GraphGadget::setLayout( GraphLayoutPtr layout )
{
	m_layout = layout;
}

GraphLayout *GraphGadget::getLayout()
{
	return m_layout.get();
}

const GraphLayout *GraphGadget::getLayout() const
{
	return m_layout.get();
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
		return nullptr;
	}

	NodeGadget *nodeGadget = runTimeCast<NodeGadget>( gadgetsUnderMouse[0].get() );
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
		return nullptr;
	}

	ConnectionGadget *connectionGadget = runTimeCast<ConnectionGadget>( gadgetsUnderMouse[0].get() );
	if ( !connectionGadget )
	{
		connectionGadget = gadgetsUnderMouse[0]->ancestor<ConnectionGadget>();
	}

	return connectionGadget;
}

ConnectionGadget *GraphGadget::reconnectionGadgetAt( const NodeGadget *gadget, const IECore::LineSegment3f &lineInGadgetSpace ) const
{
	std::vector<GadgetPtr> gadgetsUnderMouse;

	Imath::V3f center = gadget->transformedBound( this ).center();
	const Imath::V3f corner0 = center - Imath::V3f( 2, 2, 1 );
	const Imath::V3f corner1 = center + Imath::V3f( 2, 2, 1 );

	std::vector<IECoreGL::HitRecord> selection;
	{
		ViewportGadget::SelectionScope selectionScope( corner0, corner1, this, selection, IECoreGL::Selector::IDRender );

		for ( ChildContainer::const_iterator it = children().begin(); it != children().end(); ++it )
		{
			if ( ConnectionGadget *c = IECore::runTimeCast<ConnectionGadget>( it->get() ) )
			{
				// don't consider the node's own connections, or connections without a source nodule
				if ( c->srcNodule() && gadget->node() != c->srcNodule()->plug()->node() && gadget->node() != c->dstNodule()->plug()->node() )
				{
					c->render();
				}
			}
		}
	}

	for ( std::vector<IECoreGL::HitRecord>::const_iterator it = selection.begin(); it != selection.end(); ++it )
	{
		GadgetPtr gadget = Gadget::select( it->name );
		if ( gadget )
		{
			return runTimeCast<ConnectionGadget>( gadget.get() );
		}
	}

	return nullptr;
}

void GraphGadget::doRenderLayer( Layer layer, const Style *style ) const
{
	Gadget::doRenderLayer( layer, style );

	glDisable( GL_DEPTH_TEST );

	switch( layer )
	{

	case GraphLayer::Connections :

		// render the new drag connections if they exist
		if ( m_dragReconnectCandidate )
		{
			if ( m_dragReconnectDstNodule )
			{
				const Nodule *srcNodule = m_dragReconnectCandidate->srcNodule();
				const NodeGadget *srcNodeGadget = nodeGadget( srcNodule->plug()->node() );
				const Imath::V3f srcP = srcNodule->fullTransform( this ).translation();
				const Imath::V3f dstP = m_dragReconnectDstNodule->fullTransform( this ).translation();
				const Imath::V3f dstTangent = nodeGadget( m_dragReconnectDstNodule->plug()->node() )->connectionTangent( m_dragReconnectDstNodule );
				/// \todo: can there be a highlighted/dashed state?
				style->renderConnection( srcP, srcNodeGadget->connectionTangent( srcNodule ), dstP, dstTangent, Style::HighlightedState );
			}

			if ( m_dragReconnectSrcNodule )
			{
				const Nodule *dstNodule = m_dragReconnectCandidate->dstNodule();
				const NodeGadget *dstNodeGadget = nodeGadget( dstNodule->plug()->node() );
				const Imath::V3f srcP = m_dragReconnectSrcNodule->fullTransform( this ).translation();
				const Imath::V3f dstP = dstNodule->fullTransform( this ).translation();
				const Imath::V3f srcTangent = nodeGadget( m_dragReconnectSrcNodule->plug()->node() )->connectionTangent( m_dragReconnectSrcNodule );
				/// \todo: can there be a highlighted/dashed state?
				style->renderConnection( srcP, srcTangent, dstP, dstNodeGadget->connectionTangent( dstNodule ), Style::HighlightedState );
			}
		}
		break;

	case GraphLayer::Overlay :

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
		break;

	default:
		break;
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
		Gaffer::UndoScope undoScope( m_scriptNode );
		Gaffer::Set *selection = m_scriptNode->selection();
		for( size_t i = 0, s = selection->size(); i != s; i++ )
		{
			Gaffer::DependencyNode *node = IECore::runTimeCast<Gaffer::DependencyNode>( selection->member( i ) );
			if( node && findNodeGadget( node ) && !Gaffer::MetadataAlgo::readOnly( node ) )
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
		{
			if( NodeGadget *g = addNodeGadget( node ) )
			{
				addConnectionGadgets( g );
			}
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

void GraphGadget::selectionMemberAdded( Gaffer::Set *set, IECore::RunTimeTyped *member )
{
	if( Gaffer::Node *node = runTimeCast<Gaffer::Node>( member ) )
	{
		if( NodeGadget *nodeGadget = findNodeGadget( node ) )
		{
			nodeGadget->setHighlighted( true );
		}
	}
}

void GraphGadget::selectionMemberRemoved( Gaffer::Set *set, IECore::RunTimeTyped *member )
{
	if( Gaffer::Node *node = runTimeCast<Gaffer::Node>( member ) )
	{
		if( NodeGadget *nodeGadget = findNodeGadget( node ) )
		{
			nodeGadget->setHighlighted( false );
		}
	}
}

void GraphGadget::filterMemberAdded( Gaffer::Set *set, IECore::RunTimeTyped *member )
{
	Gaffer::Node *node = IECore::runTimeCast<Gaffer::Node>( member );
	if( node && node->parent<Gaffer::Node>() == m_root )
	{
		if( !findNodeGadget( node ) )
		{
			if( NodeGadget * g = addNodeGadget( node ) )
			{
				addConnectionGadgets( g );
			}
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
	Nodule *nodule = findNodule( dstPlug );
	if( !nodule )
	{
		return;
	}

	removeConnectionGadget( nodule );

	if( !dstPlug->getInput<Gaffer::Plug>() )
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

	addConnectionGadget( nodule );
}

void GraphGadget::plugSet( Gaffer::Plug *plug )
{
	const InternedString &name = plug->getName();
	if( name==g_positionPlugName )
	{
		Gaffer::Node *node = plug->node();
		NodeGadget *ng = findNodeGadget( node );
		if( ng )
		{
			updateNodeGadgetTransform( ng );
		}
	}
	else if( name==g_inputConnectionsMinimisedPlugName || name == g_outputConnectionsMinimisedPlugName )
	{
		std::vector<ConnectionGadget *> connections;
		connectionGadgets( plug->node(), connections );
		for( std::vector<ConnectionGadget *>::const_iterator it = connections.begin(), eIt = connections.end(); it != eIt; ++it )
		{
			updateConnectionGadgetMinimisation( *it );
		}
	}
}

void GraphGadget::noduleAdded( Nodule *nodule )
{
	addConnectionGadgets( nodule );
	for( RecursiveNoduleIterator it( nodule ); !it.done(); ++it )
	{
		addConnectionGadgets( it->get() );
	}
}

void GraphGadget::noduleRemoved( Nodule *nodule )
{
	removeConnectionGadgets( nodule );
	for( RecursiveNoduleIterator it( nodule ); !it.done(); ++it )
	{
		removeConnectionGadgets( it->get() );
	}
}

void GraphGadget::nodeMetadataChanged( IECore::TypeId nodeTypeId, IECore::InternedString key, Gaffer::Node *node )
{
	if( key != g_nodeGadgetTypeName )
	{
		return;
	}

	if( node && node->parent() == m_root )
	{
		// Metadata change for one instance
		removeNodeGadget( node );
		if( NodeGadget *g = addNodeGadget( node ) )
		{
			addConnectionGadgets( g );
		}
		return;
	}
	else
	{
		// In theory we should test all children of the root
		// here, but in practice it's only ever per-instance
		// metadata that changes at runtime.
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
			// background click. clear selection unless a modifier is held, in
			// which case we're expecting a drag to modify the selection.
			if( !(event.modifiers & ButtonEvent::Shift) && !(event.modifiers & ButtonEvent::Control) )
			{
				m_scriptNode->selection()->clear();
			}
			return true;
		}

		NodeGadget *nodeGadget = runTimeCast<NodeGadget>( gadgetsUnderMouse[0].get() );
		if( !nodeGadget )
		{
			nodeGadget = gadgetsUnderMouse[0]->ancestor<NodeGadget>();
		}

		Gaffer::Node *node = nodeGadget->node();

		if( nodeGadget )
		{
			// Quick Hack: Adjust focus if the hit is in the lower section
			V3f posInNode = event.line.p0 - nodeGadget->transformedBound().min;
			if( posInNode.y < 1.75f )
			{
				if( Gaffer::ScriptNode *script = node->ancestor<Gaffer::ScriptNode>() )
				{
					Gaffer::UndoScope undoScope( m_scriptNode );
					Gaffer::MetadataAlgo::setFocusNode( script, node );
				}
			}
			else
			{
				bool shiftHeld = event.modifiers & ButtonEvent::Shift;
				bool controlHeld = event.modifiers & ButtonEvent::Control;
				bool nodeSelected = m_scriptNode->selection()->contains( node );

				std::vector<Gaffer::Node *> affectedNodes;
				if( const BackdropNodeGadget *backdrop = runTimeCast<BackdropNodeGadget>( nodeGadget ) )
				{
					if( !controlHeld )
					{
						backdrop->framed( affectedNodes );
					}
				}

				if( ( event.modifiers & ButtonEvent::Alt ) && ( controlHeld || shiftHeld ) )
				{
					std::vector<NodeGadget *> connected;
					connectedNodeGadgets( node, connected, event.modifiers & ButtonEvent::Shift ? Gaffer::Plug::In : Gaffer::Plug::Out );
					for( std::vector<NodeGadget *>::const_iterator it = connected.begin(), eIt = connected.end(); it != eIt; ++it )
					{
						affectedNodes.push_back( (*it)->node() );
					}
				}

				affectedNodes.push_back( node );

				if( nodeSelected )
				{
					if( controlHeld )
					{
						m_scriptNode->selection()->remove( affectedNodes.begin(), affectedNodes.end() );
					}
				}
				else
				{
					if( !controlHeld && !shiftHeld )
					{
						m_scriptNode->selection()->clear();
					}
					m_scriptNode->selection()->add( affectedNodes.begin(), affectedNodes.end() );
				}
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
		return nullptr;
	}

	V3f i;
	if( !event.line.intersect( Plane3f( V3f( 0, 0, 1 ), 0 ), i ) )
	{
		return nullptr;
	}

	m_dragMode = None;
	m_dragStartPosition = m_lastDragPosition = V2f( i.x, i.y );

	NodeGadget *nodeGadget = nodeGadgetAt( event.line );
	if( event.buttons == ButtonEvent::Left )
	{
		if(
			nodeGadget &&
			m_scriptNode->selection()->contains( nodeGadget->node() ) &&
			!readOnly( m_scriptNode->selection() )
		)
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
			Pointer::setCurrent( "nodes" );
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

	return nullptr;
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
		return true;
	}
	else if( m_dragMode == Selecting )
	{
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
		const float snapThresh = 1.5;

		// snap the position using the offsets precomputed in calculateDragSnapOffsets()
		V2f startPos = V2f( i.x, i.y );
		V2f pos = startPos;
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

			if( snappedDist < snapThresh )
			{
				pos[axis] = snappedOffset + m_dragStartPosition[axis];
			}
		}

		// We have sorted the snap points on the X axis, so we just need to check points that are within
		// the right X range.
		const std::vector<Imath::V2f> &snapPoints = m_dragSnapPoints;
		V2f pOffset = startPos - m_dragStartPosition;
		vector<V2f>::const_iterator pEnd = lower_bound( snapPoints.begin(), snapPoints.end(), pOffset + V2f( snapThresh ), CompareV2fX() );
		vector<V2f>::const_iterator pIt = upper_bound( snapPoints.begin(), snapPoints.end(), pOffset - V2f( snapThresh ), CompareV2fX() );
		for( ; pIt != pEnd; pIt++ )
		{
			if( fabs( pOffset[1] - (*pIt)[1] ) < snapThresh &&
			    fabs( pOffset[0] - (*pIt)[0] ) < snapThresh )
			{
				pos = *pIt + m_dragStartPosition;
				break;
			}
		}

		// move all the nodes using the snapped offset
		Gaffer::UndoScope undoScope( m_scriptNode, Gaffer::UndoScope::Enabled, dragMergeGroup() );
		offsetNodes( m_scriptNode->selection(), pos - m_lastDragPosition );
		m_lastDragPosition = pos;
		updateDragReconnectCandidate( event );
		dirty( DirtyType::Render );
		return true;
	}
	else
	{
		// we're drag selecting
		m_lastDragPosition = V2f( i.x, i.y );
		updateDragSelection( false, event.modifiers );
		dirty( DirtyType::Render );
		return true;
	}

	assert( 0 ); // shouldn't get here
	return false;
}

void GraphGadget::updateDragReconnectCandidate( const DragDropEvent &event )
{
	if( m_dragReconnectCandidate )
	{
		m_dragReconnectCandidate->setVisible( true );
	}
	m_dragReconnectCandidate = nullptr;
	m_dragReconnectSrcNodule = nullptr;
	m_dragReconnectDstNodule = nullptr;

	// Find the node being dragged.

	if( m_scriptNode->selection()->size() != 1 )
	{
		return;
	}

	const Gaffer::DependencyNode *node = IECore::runTimeCast<const Gaffer::DependencyNode>( m_scriptNode->selection()->member( 0 ) );
	NodeGadget *nodeGadget = this->nodeGadget( node );
	if( !node || !nodeGadget )
	{
		return;
	}

	// See if it has been dragged onto a connection.

	ConnectionGadget *connection = reconnectionGadgetAt( nodeGadget, event.line );
	if( !connection )
	{
		return;
	}

	// See if the node can be sensibly inserted into that connection,
	// and if so, stash what we need into our m_dragReconnect member
	// variables for use in dragEnd.

	for( Gaffer::RecursiveOutputPlugIterator it( node ); !it.done(); ++it )
	{
		// See if the output has a corresponding input, and that
		// the resulting in/out plug pair can be inserted into the
		// connection.
		const Gaffer::Plug *outPlug = it->get();
		const Gaffer::Plug *inPlug = node->correspondingInput( outPlug );
		if( !inPlug )
		{
			continue;
		}

		if(
			!connection->dstNodule()->plug()->acceptsInput( outPlug ) ||
			!inPlug->acceptsInput( connection->srcNodule()->plug() )
		)
		{
			continue;
		}

		// Check that this pair of plugs doesn't have existing
		// connections. We do however allow output connections
		// provided they are not to plugs in this graph - this
		// allows us to ignore connections the UI components
		// make, for instance connecting an output plug into
		// a View outside the script.
		if( inPlug->getInput<Gaffer::Plug>() )
		{
			continue;
		}

		bool haveOutputs = false;
		for( Gaffer::Plug::OutputContainer::const_iterator oIt = outPlug->outputs().begin(), oeIt = outPlug->outputs().end(); oIt != oeIt; ++oIt )
		{
			if( m_root->isAncestorOf( *oIt ) )
			{
				haveOutputs = true;
				break;
			}
		}

		if( haveOutputs )
		{
			continue;
		}

		// Check that our plugs are represented in the graph.
		// If they are, we've found a valid place to insert the
		// dragged node.

		Nodule *inNodule = nodeGadget->nodule( inPlug );
		Nodule *outNodule = nodeGadget->nodule( outPlug );
		if( inNodule && outNodule )
		{
			m_dragReconnectCandidate = connection;
			m_dragReconnectDstNodule = inNodule;
			m_dragReconnectSrcNodule = outNodule;
			m_dragReconnectCandidate->setVisible( false );
			return;
		}
	}
}

bool GraphGadget::dragEnd( GadgetPtr gadget, const DragDropEvent &event )
{
	DragMode dragMode = m_dragMode;
	m_dragMode = None;
	Pointer::setCurrent( "" );

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
		if( m_dragReconnectCandidate )
		{
			Gaffer::UndoScope undoScope( m_scriptNode, Gaffer::UndoScope::Enabled, dragMergeGroup() );
			m_dragReconnectDstNodule->plug()->setInput( m_dragReconnectCandidate->srcNodule()->plug() );
			m_dragReconnectCandidate->dstNodule()->plug()->setInput( m_dragReconnectSrcNodule->plug() );
		}
		m_dragReconnectCandidate = nullptr;
		m_dragMergeGroupId++;
		dirty( DirtyType::Render );
	}
	else if( dragMode == Selecting )
	{
		updateDragSelection( true, event.modifiers );
		dirty( DirtyType::Render );
	}

	return true;
}

void GraphGadget::calculateDragSnapOffsets( Gaffer::Set *nodes )
{
	m_dragSnapOffsets[0].clear();
	m_dragSnapOffsets[1].clear();
	m_dragSnapPoints.clear();

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
			if( !srcNodule )
			{
				continue;
			}

			const Nodule *dstNodule = connection->dstNodule();
			const NodeGadget *srcNodeGadget = srcNodule->ancestor<NodeGadget>();
			const NodeGadget *dstNodeGadget = dstNodule->ancestor<NodeGadget>();

			if( !srcNodeGadget || !dstNodeGadget )
			{
				continue;
			}

			// check that the connection tangents are opposed - if not we don't want to snap

			V3f srcTangent = srcNodeGadget->connectionTangent( srcNodule );
			V3f dstTangent = dstNodeGadget->connectionTangent( dstNodule );

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
			float nodeOffset = srcNodePosition[snapAxis] - dstNodePosition[snapAxis];

			if( dstNodule->plug()->node() != node )
			{
				nodeOffset *= -1;
			}

			m_dragSnapOffsets[snapAxis].push_back( nodeOffset );

			// compute an offset that will position the node neatly next to its input
			// in the other axis.

			Box3f srcNodeBound = srcNodeGadget->transformedBound( nullptr );
			Box3f dstNodeBound = dstNodeGadget->transformedBound( nullptr );

			const int otherAxis = snapAxis == 1 ? 0 : 1;
			float baseOffsetOtherAxis;
			float offsetDirectionOtherAxis;
			if( otherAxis == 1 )
			{
				baseOffsetOtherAxis = dstNodeBound.max[otherAxis] - srcNodeBound.min[otherAxis];
				offsetDirectionOtherAxis = 1.0f;
			}
			else
			{
				baseOffsetOtherAxis = dstNodeBound.min[otherAxis] - srcNodeBound.max[otherAxis];
				offsetDirectionOtherAxis = -1.0f;
			}

			if( dstNodule->plug()->node() == node )
			{
				baseOffsetOtherAxis *= -1;
				offsetDirectionOtherAxis *= -1;
			}

			m_dragSnapOffsets[otherAxis].push_back( baseOffsetOtherAxis + 4.0f * offsetDirectionOtherAxis );

			if( snapAxis == 0 )
			{
				m_dragSnapPoints.push_back( Imath::V2f( offset, baseOffsetOtherAxis + 1.5f * offsetDirectionOtherAxis ) );
			}
			else
			{
				m_dragSnapPoints.push_back( Imath::V2f( baseOffsetOtherAxis + 1.5f * offsetDirectionOtherAxis, offset ) );
			}
		}
	}

	// sort and remove duplicates so that we can use lower_bound() to find appropriate
	// snap points in dragMove().

	for( int axis = 0; axis <= 1; ++axis )
	{
		std::sort( m_dragSnapOffsets[axis].begin(), m_dragSnapOffsets[axis].end() );
		m_dragSnapOffsets[axis].erase( std::unique( m_dragSnapOffsets[axis].begin(), m_dragSnapOffsets[axis].end()), m_dragSnapOffsets[axis].end() );
	}

	std::sort( m_dragSnapPoints.begin(), m_dragSnapPoints.end(), CompareV2fX() );

}

void GraphGadget::offsetNodes( Gaffer::Set *nodes, const Imath::V2f &offset )
{
	SetPositionsActionPtr action = new SetPositionsAction( m_root.get() );
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
			Gaffer::V2fPlug *p = nodePositionPlug( node, /* createIfMissing = */ true );
			action->addOffset( p, offset );
		}
	}
	Gaffer::Action::enact( action );
}

std::string GraphGadget::dragMergeGroup() const
{
	return boost::str( boost::format( "GraphGadget%1%%2%" ) % this % m_dragMergeGroupId );
}

void GraphGadget::updateDragSelection( bool dragEnd, ModifiableEvent::Modifiers modifiers )
{
	Box2f selectionBound;
	selectionBound.extendBy( m_dragStartPosition );
	selectionBound.extendBy( m_lastDragPosition );

	for( NodeGadgetMap::const_iterator it = m_nodeGadgets.begin(), eIt = m_nodeGadgets.end(); it != eIt; ++it )
	{
		NodeGadget *nodeGadget = it->second.gadget;
		const Box3f nodeBound3 = nodeGadget->transformedBound();
		const Box2f nodeBound2( V2f( nodeBound3.min.x, nodeBound3.min.y ), V2f( nodeBound3.max.x, nodeBound3.max.y ) );
		if( boxContains( selectionBound, nodeBound2 ) )
		{
			bool removeFromSelection = modifiers & DragDropEvent::Control;

			nodeGadget->setHighlighted( !removeFromSelection );

			if( !dragEnd )
			{
				continue;
			}

			if( removeFromSelection )
			{
				m_scriptNode->selection()->remove( const_cast<Gaffer::Node *>( it->first ) );
			}
			else
			{
				m_scriptNode->selection()->add( const_cast<Gaffer::Node *>( it->first ) );
			}
		}
		else
		{
			nodeGadget->setHighlighted( m_scriptNode->selection()->contains( it->first ) );
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
	for( Gaffer::NodeIterator it( m_root.get() ); !it.done(); ++it )
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

	for( NodeGadgetMap::iterator it = m_nodeGadgets.begin(); it != m_nodeGadgets.end(); ++it )
	{
		addConnectionGadgets( it->second.gadget );
	}

}

NodeGadget *GraphGadget::addNodeGadget( Gaffer::Node *node )
{
	NodeGadgetPtr nodeGadget = NodeGadget::create( node );
	if( !nodeGadget )
	{
		return nullptr;
	}

	// The call to `addChild( nodeGadget )` will uniquefy the name
	// with respect to all our other NodeGadgets. This can have
	// significant overhead when graphs get large, which we can
	// avoid by making sure the name is unique already. The node
	// name fits the bill, and is already conveniently available
	// in `InternedString` form. Note that we are deliberately not
	// synchronising the names in the case of them changing in the
	// future, and provide no guarantees about NodeGadget names in
	// general.
	// \todo It may be better to modify GraphComponent to allow nameless
	// children and then use them here. This would let us avoid _all_
	// uniquefication overhead and would also be useful for ArrayPlug
	// and Spreadsheet::RowsPlug children.
	nodeGadget->setName( node->getName() );

	addChild( nodeGadget );

	NodeGadgetEntry &nodeGadgetEntry = m_nodeGadgets[node];
	nodeGadgetEntry.inputChangedConnection = node->plugInputChangedSignal().connect( boost::bind( &GraphGadget::inputChanged, this, ::_1 ) );
	nodeGadgetEntry.plugSetConnection = node->plugSetSignal().connect( boost::bind( &GraphGadget::plugSet, this, ::_1 ) );
	nodeGadgetEntry.noduleAddedConnection = nodeGadget->noduleAddedSignal().connect( boost::bind( &GraphGadget::noduleAdded, this, ::_2 ) );
	nodeGadgetEntry.noduleRemovedConnection = nodeGadget->noduleRemovedSignal().connect( boost::bind( &GraphGadget::noduleRemoved, this, ::_2 ) );
	nodeGadgetEntry.gadget = nodeGadget.get();

	// highlight to reflect selection status
	if( m_scriptNode && m_scriptNode->selection()->contains( node ) )
	{
		nodeGadget->setHighlighted( true );
	}

	updateNodeGadgetTransform( nodeGadget.get() );

	return nodeGadget.get();
}

void GraphGadget::removeNodeGadget( const Gaffer::Node *node )
{
	NodeGadgetMap::iterator it = m_nodeGadgets.find( node );
	if( it!=m_nodeGadgets.end() )
	{
		removeConnectionGadgets( it->second.gadget );
		removeChild( it->second.gadget );
		m_nodeGadgets.erase( it );
	}
}

NodeGadget *GraphGadget::findNodeGadget( const Gaffer::Node *node ) const
{
	NodeGadgetMap::const_iterator it = m_nodeGadgets.find( node );
	if( it==m_nodeGadgets.end() )
	{
		return nullptr;
	}
	return it->second.gadget;
}

void GraphGadget::updateNodeGadgetTransform( NodeGadget *nodeGadget )
{
	Gaffer::Node *node = nodeGadget->node();
	M44f m;

	if( Gaffer::V2fPlug *p = nodePositionPlug( node, /* createIfMissing = */ false ) )
	{
		const V2f t = p->getValue();
	 	m.translate( V3f( t[0], t[1], 0 ) );
	}

	nodeGadget->setTransform( m );
}

void GraphGadget::addConnectionGadgets( NodeGadget *nodeGadget )
{
	for( RecursiveNoduleIterator it( nodeGadget ); !it.done(); ++it )
	{
		addConnectionGadgets( it->get() );
	}
}

Nodule *GraphGadget::findNodule( const Gaffer::Plug *plug ) const
{
	NodeGadget *g = findNodeGadget( plug->node() );
	return g ? g->nodule( plug ) : nullptr;
}

void GraphGadget::addConnectionGadgets( Nodule *nodule )
{
	if( nodule->plug()->direction() == Gaffer::Plug::In )
	{
		if( !findConnectionGadget( nodule ) )
		{
			addConnectionGadget( nodule );
		}
	}
	else
	{
		// Reconnect any old output connections which may have been dangling
		for( Gaffer::Plug::OutputContainer::const_iterator oIt( nodule->plug()->outputs().begin() ); oIt!= nodule->plug()->outputs().end(); ++oIt )
		{
			ConnectionGadget *connection = findConnectionGadget( *oIt );
			if( connection && connection->srcNodule() != nodule )
			{
				assert( connection->dstNodule()->plug()->getInput<Gaffer::Plug>() == nodule->plug() );
				connection->setNodules( nodule, connection->dstNodule() );
			}
		}
	}
}

void GraphGadget::addConnectionGadget( Nodule *dstNodule )
{
	Gaffer::Plug *dstPlug = dstNodule->plug();
	Gaffer::Plug *srcPlug = dstPlug->getInput<Gaffer::Plug>();
	if( !srcPlug )
	{
		// there is no connection
		return;
	}

	Gaffer::Node *srcNode = srcPlug->node();
	if( srcNode == dstPlug->node() )
	{
		// we don't want to visualise connections between plugs
		// on the same node.
		return;
	}

	Nodule *srcNodule = findNodule( srcPlug );

	ConnectionGadgetPtr connection = ConnectionGadget::create( srcNodule, dstNodule );
	updateConnectionGadgetMinimisation( connection.get() );
	addChild( connection );

	m_connectionGadgets[dstNodule] = connection.get();
}

void GraphGadget::removeConnectionGadgets( const NodeGadget *nodeGadget )
{
	for( RecursiveNoduleIterator it( nodeGadget ); !it.done(); ++it )
	{
		removeConnectionGadgets( it->get() );
	}
}

void GraphGadget::removeConnectionGadgets( const Nodule *nodule )
{
	if( nodule->plug()->direction() == Gaffer::Plug::In )
	{
		removeConnectionGadget( nodule );
	}
	else
	{
		// make output connection gadgets dangle
		for( Gaffer::Plug::OutputContainer::const_iterator oIt( nodule->plug()->outputs().begin() ); oIt != nodule->plug()->outputs().end(); oIt++ )
		{
			if( ConnectionGadget *connection = findConnectionGadget( *oIt ) )
			{
				if( connection->srcNodule() == nodule )
				{
					connection->setNodules( nullptr, connection->dstNodule() );
				}
			}
		}
	}
}

void GraphGadget::removeConnectionGadget( const Nodule *dstNodule )
{
	ConnectionGadgetMap::iterator it = m_connectionGadgets.find( dstNodule );
	if( it == m_connectionGadgets.end() )
	{
		return;
	}

	removeChild( it->second );
	m_connectionGadgets.erase( it );
}

ConnectionGadget *GraphGadget::findConnectionGadget( const Nodule *dstNodule ) const
{
	ConnectionGadgetMap::const_iterator it = m_connectionGadgets.find( dstNodule );
	if( it==m_connectionGadgets.end() )
	{
		return nullptr;
	}
	return it->second;
}

ConnectionGadget *GraphGadget::findConnectionGadget( const Gaffer::Plug *plug ) const
{
	Nodule *nodule = findNodule( plug );
	if( !nodule )
	{
		return nullptr;
	}
	return findConnectionGadget( nodule );
}

void GraphGadget::updateConnectionGadgetMinimisation( ConnectionGadget *gadget )
{
	bool minimised = getNodeInputConnectionsMinimised( gadget->dstNodule()->plug()->node() );
	if( const Nodule *srcNodule = gadget->srcNodule() )
	{
		minimised = minimised || getNodeOutputConnectionsMinimised( srcNodule->plug()->node() );
	}
	gadget->setMinimised( minimised );
}
