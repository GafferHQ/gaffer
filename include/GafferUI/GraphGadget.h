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

#pragma once

#include "GafferUI/AnnotationsGadget.h"
#include "GafferUI/ContainerGadget.h"
#include "GafferUI/ContextTracker.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/Plug.h"

#include "Gaffer/BackgroundTask.h"

#include "tbb/spin_mutex.h"

#include <unordered_set>

namespace Gaffer
{
IE_CORE_FORWARDDECLARE( Node );
IE_CORE_FORWARDDECLARE( ScriptNode );
IE_CORE_FORWARDDECLARE( Set );
}

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( NodeGadget );
IE_CORE_FORWARDDECLARE( Nodule );
IE_CORE_FORWARDDECLARE( ConnectionGadget );
IE_CORE_FORWARDDECLARE( GraphLayout );
IE_CORE_FORWARDDECLARE( AuxiliaryConnectionsGadget );

/// Aliases that define the intended use of each
/// Gadget::Layer by the GraphGadget components.
namespace GraphLayer
{
	constexpr Gadget::Layer Backdrops = Gadget::Layer::Back;
	constexpr Gadget::Layer OverBackdrops = Gadget::Layer::BackMidBack;
	constexpr Gadget::Layer Connections = Gadget::Layer::MidBack;
	constexpr Gadget::Layer Nodes = Gadget::Layer::Main;
	constexpr Gadget::Layer Highlighting = Gadget::Layer::MidFront;
	constexpr Gadget::Layer Overlay = Gadget::Layer::Front;
};

/// The GraphGadget class provides a ui for connecting nodes together.
class GAFFERUI_API GraphGadget : public ContainerGadget
{

	public :

		/// Creates a graph showing the children of root, optionally
		/// filtered by the specified set. Nodes are only displayed if
		/// they are both a child of root and a member of filter.
		explicit GraphGadget( Gaffer::NodePtr root, Gaffer::SetPtr filter = nullptr );

		~GraphGadget() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferUI::GraphGadget, GraphGadgetTypeId, ContainerGadget );

		Gaffer::Node *getRoot();
		const Gaffer::Node *getRoot() const;
		void setRoot( Gaffer::NodePtr root, Gaffer::SetPtr filter = nullptr );
		using RootChangedSignal = Gaffer::Signals::Signal<void ( GraphGadget *, Gaffer::Node * )>;
		/// A signal emitted when the root has been changed - the signature
		/// of the signal is ( graphGadget, previousRoot ).
		RootChangedSignal &rootChangedSignal();

		/// May return nullptr if no filter has been specified.
		Gaffer::Set *getFilter();
		const Gaffer::Set *getFilter() const;
		void setFilter( Gaffer::SetPtr filter );

		/// Returns the NodeGadget representing the specified node or nullptr
		/// if none exists.
		NodeGadget *nodeGadget( const Gaffer::Node *node );
		const NodeGadget *nodeGadget( const Gaffer::Node *node ) const;

		/// Returns the ConnectionGadget representing the specified
		/// destination Plug or nullptr if none exists.
		ConnectionGadget *connectionGadget( const Gaffer::Plug *dstPlug );
		const ConnectionGadget *connectionGadget( const Gaffer::Plug *dstPlug ) const;

		/// Finds all the ConnectionGadgets (both inputs and outputs) connected
		/// to the specified plug and appends them to the connections vector.
		/// Returns the new size of the vector. If excludedNodes is specified,
		/// then connections to any nodes it contains will be ignored.
		size_t connectionGadgets( const Gaffer::Plug *plug, std::vector<ConnectionGadget *> &connections, const Gaffer::Set *excludedNodes = nullptr );
		size_t connectionGadgets( const Gaffer::Plug *plug, std::vector<const ConnectionGadget *> &connections, const Gaffer::Set *excludedNodes = nullptr ) const;

		/// Finds all the ConnectionGadgets connected to the specified node and
		/// appends them to the connections vector. Returns the new size of the
		/// vector. If excludedNodes is specified, then connections to any
		/// nodes it contains will be ignored.
		size_t connectionGadgets( const Gaffer::Node *node, std::vector<ConnectionGadget *> &connections, const Gaffer::Set *excludedNodes = nullptr );
		size_t connectionGadgets( const Gaffer::Node *node, std::vector<const ConnectionGadget *> &connections, const Gaffer::Set *excludedNodes = nullptr ) const;

		/// Returns the Gadget responsible for representing auxiliary connections.
		AuxiliaryConnectionsGadget *auxiliaryConnectionsGadget();
		const AuxiliaryConnectionsGadget *auxiliaryConnectionsGadget() const;

		/// Returns the Gadget responsible for drawing annotations.
		AnnotationsGadget *annotationsGadget();
		const AnnotationsGadget *annotationsGadget() const;

		/// Finds all the upstream NodeGadgets connected to the specified node
		/// and appends them to the specified vector. Returns the new size of the vector.
		/// \note Here "upstream" nodes are defined as nodes at the end of input
		/// connections as shown in the graph - auxiliary connections and
		/// invisible nodes are not considered at all.
		size_t upstreamNodeGadgets( const Gaffer::Node *node, std::vector<NodeGadget *> &upstreamNodeGadgets, size_t degreesOfSeparation = std::numeric_limits<size_t>::max() );
		size_t upstreamNodeGadgets( const Gaffer::Node *node, std::vector<const NodeGadget *> &upstreamNodeGadgets, size_t degreesOfSeparation = std::numeric_limits<size_t>::max() ) const;

		/// Finds all the downstream NodeGadgets connected to the specified node
		/// and appends them to the specified vector. Returns the new size of the vector.
		/// \note Here "downstream" nodes are defined as nodes at the end of output
		/// connections as shown in the graph - auxiliary connections and
		/// invisible nodes are not considered at all.
		size_t downstreamNodeGadgets( const Gaffer::Node *node, std::vector<NodeGadget *> &downstreamNodeGadgets, size_t degreesOfSeparation = std::numeric_limits<size_t>::max() );
		size_t downstreamNodeGadgets( const Gaffer::Node *node, std::vector<const NodeGadget *> &downstreamNodeGadgets, size_t degreesOfSeparation = std::numeric_limits<size_t>::max() ) const;

		/// Finds all the NodeGadgets connected to the specified node
		/// and appends them to the specified vector. Returns the new size of the vector.
		/// \note Here "connected" nodes are defined as nodes at the end of
		/// connections as shown in the graph - auxiliary connections and
		/// invisible nodes are not considered at all.
		size_t connectedNodeGadgets( const Gaffer::Node *node, std::vector<NodeGadget *> &connectedNodeGadgets, Gaffer::Plug::Direction direction = Gaffer::Plug::Invalid, size_t degreesOfSeparation = std::numeric_limits<size_t>::max() );
		size_t connectedNodeGadgets( const Gaffer::Node *node, std::vector<const NodeGadget *> &connectedNodeGadgets, Gaffer::Plug::Direction direction = Gaffer::Plug::Invalid, size_t degreesOfSeparation = std::numeric_limits<size_t>::max() ) const;

		/// Finds all the NodeGadgets which haven't been given an explicit position
		/// using setNodePosition().
		size_t unpositionedNodeGadgets( std::vector<NodeGadget *> &nodeGadgets ) const;

		/// Sets the position of the specified node within the graph. This
		/// method may be used even when the node currently has no NodeGadget
		/// associated with it, and the position will be used if and when a NodeGadget
		/// is created. Note that currently all GraphGadgets share the same node
		/// positioning, so having the node appear in different places in different
		/// Gadgets is not possible.
		/// \undoable
		void setNodePosition( Gaffer::Node *node, const Imath::V2f &position );
		Imath::V2f getNodePosition( const Gaffer::Node *node ) const;
		bool hasNodePosition( const Gaffer::Node *node ) const;

		/// May be used to minimise the input connections for a particular node.
		/// \undoable
		void setNodeInputConnectionsMinimised( Gaffer::Node *node, bool minimised );
		bool getNodeInputConnectionsMinimised( const Gaffer::Node *node ) const;

		/// May be used to minimise the output connections for a particular node.
		/// \undoable
		void setNodeOutputConnectionsMinimised( Gaffer::Node *node, bool minimised );
		bool getNodeOutputConnectionsMinimised( const Gaffer::Node *node ) const;

		/// Sets the layout algorithm used by the graph editor. This defaults to
		/// an instance of StandardGraphLayout.
		void setLayout( GraphLayoutPtr layout );
		/// Returns the layout algorithm used by the graph editor.
		GraphLayout *getLayout();
		const GraphLayout *getLayout() const;

		/// Returns the nodeGadget under the specified line.
		NodeGadget *nodeGadgetAt( const IECore::LineSegment3f &lineInGadgetSpace ) const;
		/// Returns the connectionGadget under the specified line.
		ConnectionGadget *connectionGadgetAt( const IECore::LineSegment3f &lineInGadgetSpace ) const;

	protected :

		void renderLayer( Layer layer, const Style *style, RenderReason reason ) const override;
		unsigned layerMask() const override;
		Imath::Box3f renderBound() const override;

	private :

		const Gaffer::V2fPlug *nodePositionPlug( const Gaffer::Node *node ) const;
		Gaffer::V2fPlug *nodePositionPlug( Gaffer::Node *node, bool createIfMissing ) const;

		void rootChildAdded( Gaffer::GraphComponent *root, Gaffer::GraphComponent *child );
		void rootChildRemoved( Gaffer::GraphComponent *root, Gaffer::GraphComponent *child );
		void selectionMemberAdded( Gaffer::Set *set, IECore::RunTimeTyped *member );
		void selectionMemberRemoved( Gaffer::Set *set, IECore::RunTimeTyped *member );
		void filterMemberAdded( Gaffer::Set *set, IECore::RunTimeTyped *member );
		void filterMemberRemoved( Gaffer::Set *set, IECore::RunTimeTyped *member );
		void inputChanged( Gaffer::Plug *dstPlug );
		void plugSet( Gaffer::Plug *plug );
		void noduleAdded( Nodule *nodule );
		void noduleRemoved( Nodule *nodule );
		void nodeMetadataChanged( IECore::TypeId nodeTypeId, IECore::InternedString key, Gaffer::Node *node );

		bool buttonPress( GadgetPtr gadget, const ButtonEvent &event );
		bool buttonRelease( GadgetPtr gadget, const ButtonEvent &event );

		IECore::RunTimeTypedPtr dragBegin( GadgetPtr gadget, const DragDropEvent &event );
		bool dragEnter( GadgetPtr gadget, const DragDropEvent &event );
		bool dragMove( GadgetPtr gadget, const DragDropEvent &event );
		bool dragEnd( GadgetPtr gadget, const DragDropEvent &event );
		void calculateDragSnapOffsets( Gaffer::Set *nodes );
		void offsetNodes( Gaffer::Set *nodes, const Imath::V2f &offset );
		std::string dragMergeGroup() const;

		void updateDragSelection( bool dragEnd, ModifiableEvent::Modifiers modifiers );

		void updateGraph();
		/// May return nullptr if NodeGadget::create() returns nullptr, signifying that
		/// someone has registered a creator in order to hide all nodes of a certain type.
		NodeGadget *addNodeGadget( Gaffer::Node *node );
		void removeNodeGadget( const Gaffer::Node *node );
		NodeGadget *findNodeGadget( const Gaffer::Node *node ) const;
		void updateNodeGadgetTransform( NodeGadget *nodeGadget );

		Nodule *findNodule( const Gaffer::Plug *plug ) const;

		void addConnectionGadgets( NodeGadget *nodeGadget );
		void addConnectionGadgets( Nodule *nodule );
		void addConnectionGadget( Nodule *dstNodule );
		void removeConnectionGadgets( const NodeGadget *nodeGadget );
		void removeConnectionGadgets( const Nodule *nodule );
		void removeConnectionGadget( const Nodule *dstNodule );
		ConnectionGadget *findConnectionGadget( const Nodule *dstNodule ) const;
		ConnectionGadget *findConnectionGadget( const Gaffer::Plug *dstPlug ) const;
		void updateConnectionGadgetMinimisation( ConnectionGadget *gadget );
		ConnectionGadget *reconnectionGadgetAt( const NodeGadget *gadget, const IECore::LineSegment3f &lineInGadgetSpace ) const;
		void updateDragReconnectCandidate( const DragDropEvent &event );

		void connectedNodeGadgetsWalk( NodeGadget *gadget, std::set<NodeGadget *> &connectedGadgets, Gaffer::Plug::Direction direction, size_t degreesOfSeparation );

		Gaffer::NodePtr m_root;
		Gaffer::ScriptNodePtr m_scriptNode;
		RootChangedSignal m_rootChangedSignal;
		Gaffer::Signals::ScopedConnection m_rootChildAddedConnection;
		Gaffer::Signals::ScopedConnection m_rootChildRemovedConnection;
		Gaffer::Signals::ScopedConnection m_selectionMemberAddedConnection;
		Gaffer::Signals::ScopedConnection m_selectionMemberRemovedConnection;

		Gaffer::SetPtr m_filter;
		Gaffer::Signals::ScopedConnection m_filterMemberAddedConnection;
		Gaffer::Signals::ScopedConnection m_filterMemberRemovedConnection;

		struct NodeGadgetEntry
		{
			NodeGadget *gadget;
			Gaffer::Signals::ScopedConnection inputChangedConnection;
			Gaffer::Signals::ScopedConnection plugSetConnection;
			Gaffer::Signals::ScopedConnection noduleAddedConnection;
			Gaffer::Signals::ScopedConnection noduleRemovedConnection;
		};
		using NodeGadgetMap = std::map<const Gaffer::Node *, NodeGadgetEntry>;
		NodeGadgetMap m_nodeGadgets;

		using ConnectionGadgetMap = std::map<const Nodule *, ConnectionGadget *>;
		ConnectionGadgetMap m_connectionGadgets;

		enum DragMode
		{
			None,
			Selecting,
			Moving,
			Sending
		};

		Imath::V2f m_dragStartPosition;
		Imath::V2f m_lastDragPosition;
		DragMode m_dragMode;
		ConnectionGadget *m_dragReconnectCandidate;
		Nodule *m_dragReconnectSrcNodule;
		Nodule *m_dragReconnectDstNodule;
		std::vector<float> m_dragSnapOffsets[2]; // offsets in x and y
		std::vector<Imath::V2f> m_dragSnapPoints; // specific points that are also target for point snapping
		int m_dragMergeGroupId;

		GraphLayoutPtr m_layout;

		void applyFocusContexts();

		ContextTrackerPtr m_contextTracker;
		Gaffer::Signals::ScopedConnection m_contextTrackerChangedConnection;

};

IE_CORE_DECLAREPTR( GraphGadget );

} // namespace GafferUI
