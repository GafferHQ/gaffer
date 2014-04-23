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

#ifndef GAFFERUI_STANDARDNODEGADGET_H
#define GAFFERUI_STANDARDNODEGADGET_H

#include "GafferUI/NodeGadget.h"
#include "GafferUI/LinearContainer.h"

namespace GafferUI
{

/// The standard means of representing a Node in a GraphGadget.
/// Nodes are represented as rectangular boxes with the name displayed
/// centrally and the nodules arranged at the sides. The orientation
/// argument to the constructor is used to determine whether the direction
/// of flow is left->right or top->bottom, and in addition nodules may be
/// positioned arbitrarily using a "nodeGadget:nodulePosition" Metadata entry
/// with a value of "left", "right", "top" or "bottom".
class StandardNodeGadget : public NodeGadget
{

	public :
	
		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::StandardNodeGadget, StandardNodeGadgetTypeId, NodeGadget );

		StandardNodeGadget( Gaffer::NodePtr node, LinearContainer::Orientation orientation=LinearContainer::X );
		virtual ~StandardNodeGadget();

		virtual Nodule *nodule( const Gaffer::Plug *plug );
		virtual const Nodule *nodule( const Gaffer::Plug *plug ) const;
		virtual Imath::V3f noduleTangent( const Nodule *nodule ) const;
		
		/// The central content of the Gadget may be customised. By default
		/// the contents is a simple NameGadget for the node, but any Gadget or
		/// Container can be placed there instead.
		void setContents( GadgetPtr contents );
		Gadget *getContents();
		const Gadget *getContents() const;
		
		void setLabelsVisibleOnHover( bool labelsVisible );
		bool getLabelsVisibleOnHover() const;
		
		Imath::Box3f bound() const;

	protected :
			
		virtual void doRender( const Style *style ) const;
		
	private :
		
		NodulePtr addNodule( Gaffer::PlugPtr plug );
		
		enum Edge
		{
			TopEdge,
			BottomEdge,
			LeftEdge,
			RightEdge,
			FirstEdge = TopEdge,
			LastEdge = RightEdge
		};
		
		LinearContainer *noduleContainer( Edge edge );
		const LinearContainer *noduleContainer( Edge edge ) const;
		
		IndividualContainer *contentsContainer();
		const IndividualContainer *contentsContainer() const;
		
		static NodeGadgetTypeDescription<StandardNodeGadget> g_nodeGadgetTypeDescription;
				
		typedef std::map<const Gaffer::Plug *, Nodule *> NoduleMap;
		NoduleMap m_nodules;
				
		void childAdded( Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child );
		void childRemoved( Gaffer::GraphComponent *parent, Gaffer::GraphComponent *child );
		
		void plugDirtied( const Gaffer::Plug *plug );
		
		void enter( Gadget *gadget );
		void leave( Gadget *gadget );
		bool dragEnter( GadgetPtr gadget, const DragDropEvent &event );
		bool dragMove( GadgetPtr gadget, const DragDropEvent &event );
		bool dragLeave( GadgetPtr gadget, const DragDropEvent &event );
		bool drop( GadgetPtr gadget, const DragDropEvent &event );

		Nodule *closestCompatibleNodule( const DragDropEvent &event );
		bool noduleIsCompatible( const Nodule *nodule, const DragDropEvent &event );

		const LinearContainer::Orientation m_orientation;
		bool m_nodeEnabled;
		bool m_labelsVisibleOnHover;
		// we accept drags from nodules and forward them to the
		// closest compatible child nodule - m_dragDestinationProxy.
		Nodule *m_dragDestinationProxy;
		
};

IE_CORE_DECLAREPTR( StandardNodeGadget )

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<StandardNodeGadget> > StandardNodeGadgetIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<StandardNodeGadget> > RecursiveStandardNodeGadgetIterator;

} // namespace GafferUI

#endif // GAFFERUI_STANDARDNODEGADGET_H
