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

#ifndef GAFFERUI_GRAPHGADGET_H
#define GAFFERUI_GRAPHGADGET_H

#include "GafferUI/ContainerGadget.h"

namespace Gaffer
{
IE_CORE_FORWARDDECLARE( Node );
IE_CORE_FORWARDDECLARE( Plug );
IE_CORE_FORWARDDECLARE( ScriptNode );
IE_CORE_FORWARDDECLARE( Set );
}

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( NodeGadget );
IE_CORE_FORWARDDECLARE( Nodule );
IE_CORE_FORWARDDECLARE( ConnectionGadget );
IE_CORE_FORWARDDECLARE( GraphLayout );

/// The GraphGadget class provides a ui for connecting nodes together.
/// \todo Implement much better auto-positioning. Currently we try to position
/// each node the instant it is added to the graph, even though subsequent scripted
/// operations might add connections and other nodes. We need to batch up such operations,
/// layout the new nodes as a unit, and then position them based on the existing nodes
/// they have connections to.
class GraphGadget : public ContainerGadget
{

	public :

		IE_CORE_FORWARDDECLARE( Filter )

		/// Creates a graph showing the children of root, optionally
		/// filtered by the specified set. Nodes are only displayed if
		/// they are both a child of root and a member of filter.
		GraphGadget( Gaffer::NodePtr root, Gaffer::SetPtr filter = 0 );
		
		virtual ~GraphGadget();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GraphGadget, GraphGadgetTypeId, ContainerGadget );

		Gaffer::Node *getRoot();
		const Gaffer::Node *getRoot() const;
		void setRoot( Gaffer::NodePtr root, Gaffer::SetPtr filter = 0 );
		typedef boost::signal<void ( GraphGadget * )> GraphGadgetSignal;
		GraphGadgetSignal &rootChangedSignal();

		/// May return 0 if no filter has been specified.
		Gaffer::Set *getFilter();
		const Gaffer::Set *getFilter() const;
		void setFilter( Gaffer::SetPtr filter );

		/// Returns the NodeGadget representing the specified node or 0
		/// if none exists.
		NodeGadget *nodeGadget( const Gaffer::Node *node );
		const NodeGadget *nodeGadget( const Gaffer::Node *node ) const;
		
		/// Returns the ConnectionGadget representing the specified
		/// destination Plug or 0 if none exists.
		ConnectionGadget *connectionGadget( const Gaffer::Plug *dstPlug );
		const ConnectionGadget *connectionGadget( const Gaffer::Plug *dstPlug ) const;
		
		/// Sets the position of the specified node within the graph. This
		/// method may be used even when the node currently has no NodeGadget
		/// associated with it, and the position will be used if and when a NodeGadget
		/// is created. Note that currently all GraphGadgets share the same node
		/// positioning, so having the node appear in different places in different
		/// Gadgets is not possible.
		void setNodePosition( Gaffer::Node *node, const Imath::V2f &position );
		Imath::V2f getNodePosition( Gaffer::Node *node ) const;
		
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

		void doRender( const Style *style ) const;
		
	private :
		
		void rootChildAdded( Gaffer::GraphComponent *root, Gaffer::GraphComponent *child );
		void rootChildRemoved( Gaffer::GraphComponent *root, Gaffer::GraphComponent *child );
		void filterMemberAdded( Gaffer::Set *set, IECore::RunTimeTyped *member );
		void filterMemberRemoved( Gaffer::Set *set, IECore::RunTimeTyped *member );
		void inputChanged( Gaffer::Plug *dstPlug );
		void plugSet( Gaffer::Plug *plug );
	
		bool keyPressed( GadgetPtr gadget, const KeyEvent &event );
		
		bool buttonPress( GadgetPtr gadget, const ButtonEvent &event );
		bool buttonRelease( GadgetPtr gadget, const ButtonEvent &event );
		
		IECore::RunTimeTypedPtr dragBegin( GadgetPtr gadget, const DragDropEvent &event );	
		bool dragEnter( GadgetPtr gadget, const DragDropEvent &event );
		bool dragMove( GadgetPtr gadget, const DragDropEvent &event );
		bool dragEnd( GadgetPtr gadget, const DragDropEvent &event );
		void offsetNodes( Gaffer::Set *nodes, const Imath::V2f &offset );
		
		void updateGraph();
		void addNodeGadget( Gaffer::Node *node );
		void removeNodeGadget( const Gaffer::Node *node );
		NodeGadget *findNodeGadget( const Gaffer::Node *node ) const;
		void updateNodeGadgetTransform( NodeGadget *nodeGadget );
		
		void addConnectionGadgets( Gaffer::GraphComponent *plugParent );
		void addConnectionGadget( Gaffer::Plug *dstPlug );
		void removeConnectionGadgets( const Gaffer::GraphComponent *plugParent );
		void removeConnectionGadget( const Gaffer::Plug *dstPlug );
		ConnectionGadget *findConnectionGadget( const Gaffer::Plug *dstPlug ) const;
		ConnectionGadget *reconnectionGadgetAt( NodeGadget *gadget, const IECore::LineSegment3f &lineInGadgetSpace ) const;
		void updateDragReconnectCandidate( const DragDropEvent &event );
		
		Gaffer::NodePtr m_root;
		Gaffer::ScriptNodePtr m_scriptNode;
		GraphGadgetSignal m_rootChangedSignal;
		boost::signals::scoped_connection m_rootChildAddedConnection;
		boost::signals::scoped_connection m_rootChildRemovedConnection;

		Gaffer::SetPtr m_filter;
		boost::signals::scoped_connection m_filterMemberAddedConnection;
		boost::signals::scoped_connection m_filterMemberRemovedConnection;
		
		struct NodeGadgetEntry
		{
			NodeGadget *gadget;
			boost::signals::connection inputChangedConnection;
			boost::signals::connection plugSetConnection;
		};
		typedef std::map<const Gaffer::Node *, NodeGadgetEntry> NodeGadgetMap;
		NodeGadgetMap m_nodeGadgets;
	
		typedef std::map<const Gaffer::Plug *, ConnectionGadget *> ConnectionGadgetMap;
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
		
		GraphLayoutPtr m_layout;
		
};

IE_CORE_DECLAREPTR( GraphGadget );

} // namespace GafferUI

#endif // GAFFERUI_GRAPHGADGET_H
