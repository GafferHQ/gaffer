//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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
IE_CORE_FORWARDDECLARE( ConnectionGadget );

/// The GraphGadget class provides a ui for connecting nodes together.
class GraphGadget : public ContainerGadget
{

	public :

		IE_CORE_FORWARDDECLARE( Filter )

		/// Creates a graph showing the nodes held in the graphSet
		/// set.
		GraphGadget( Gaffer::SetPtr graphSet );
		/// Creates a graph showing all the children of graphRoot. This
		/// is equivalent to calling the Set based constructor passing
		/// ChildSet( graphRoot ).
		GraphGadget( Gaffer::NodePtr graphRoot );
		
		virtual ~GraphGadget();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GraphGadget, GraphGadgetTypeId, ContainerGadget );

		/// Returns the Set specifying the contents of the graph - the
		/// membership may be freely modified to change what is displayed.
		Gaffer::SetPtr getGraphSet();
		Gaffer::ConstSetPtr getGraphSet() const;
		/// Changes the set used to specify the graph contents.
		void setGraphSet( Gaffer::SetPtr graphSet );

		/// Returns the NodeGadget representing the specified node or 0
		/// if none exists.
		NodeGadgetPtr nodeGadget( Gaffer::ConstNodePtr node );
		ConstNodeGadgetPtr nodeGadget( Gaffer::ConstNodePtr node ) const;
		
		/// Returns the ConnectionGadget representing the specified
		/// destination Plug or 0 if none exists.
		ConnectionGadgetPtr connectionGadget( Gaffer::ConstPlugPtr dstPlug );
		ConstConnectionGadgetPtr connectionGadget( Gaffer::ConstPlugPtr dstPlug ) const;
		
	protected :

		void doRender( IECore::RendererPtr renderer ) const;
		
	private :
	
		void constructCommon( Gaffer::SetPtr graphSet );
		
		void memberAdded( Gaffer::SetPtr set, IECore::RunTimeTypedPtr member );
		void memberRemoved( Gaffer::SetPtr set, IECore::RunTimeTypedPtr member );
		void inputChanged( Gaffer::PlugPtr dstPlug );
		void plugSet( Gaffer::PlugPtr plug );
	
		bool keyPressed( GadgetPtr gadget, const KeyEvent &event );
		
		bool buttonPress( GadgetPtr gadget, const ButtonEvent &event );
		bool buttonRelease( GadgetPtr gadget, const ButtonEvent &event );
		
		IECore::RunTimeTypedPtr dragBegin( GadgetPtr gadget, const DragDropEvent &event );	
		bool dragUpdate( GadgetPtr gadget, const DragDropEvent &event );
		bool dragEnd( GadgetPtr gadget, const DragDropEvent &event );
		
		void updateGraph();
		void addNodeGadget( Gaffer::Node *node );
		void removeNodeGadget( const Gaffer::Node *node );
		NodeGadget *findNodeGadget( const Gaffer::Node *node ) const;
		void updateNodeGadgetTransform( NodeGadget *nodeGadget );
		
		void addConnectionGadgets( Gaffer::Node *dstNode );
		void addConnectionGadget( Gaffer::Plug *dstPlug );
		void removeConnectionGadget( const Gaffer::Plug *dstPlug );
		ConnectionGadget *findConnectionGadget( const Gaffer::Plug *dstPlug ) const;
	
		Gaffer::SetPtr m_graphSet;
		boost::signals::scoped_connection m_graphSetMemberAddedConnection;
		boost::signals::scoped_connection m_graphSetMemberRemovedConnection;
		
		Gaffer::ScriptNodePtr m_scriptNode;
		
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

		Imath::V2f m_dragStartPosition;
		Imath::V2f m_lastDragPosition;
		bool m_dragSelecting;
		
};

IE_CORE_DECLAREPTR( GraphGadget );

} // namespace GafferUI

#endif // GAFFERUI_GRAPHGADGET_H
