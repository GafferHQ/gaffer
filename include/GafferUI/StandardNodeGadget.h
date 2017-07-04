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

#include "Gaffer/StringAlgo.h"

#include "GafferUI/Export.h"
#include "GafferUI/NodeGadget.h"
#include "GafferUI/LinearContainer.h"

namespace GafferUI
{

class PlugAdder;
class NoduleLayout;

/// The standard means of representing a Node in a GraphGadget.
/// Nodes are represented as rectangular boxes with the name displayed
/// centrally and the nodules arranged at the sides. Supports the following
/// Metadata entries :
///
/// - "nodeGadget:minWidth" : a node entry with a float value
/// - "nodeGadget:padding" : a node entry with a float value
/// - "nodeGadget:color" : Color3f
/// - "nodeGadget:shape" : StringData containing "rectangle" or "oval"
/// - "icon" : string naming an image to be used with ImageGadget
class GAFFERUI_API StandardNodeGadget : public NodeGadget
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::StandardNodeGadget, StandardNodeGadgetTypeId, NodeGadget );

		enum Edge
		{
			TopEdge,
			BottomEdge,
			LeftEdge,
			RightEdge,
			FirstEdge = TopEdge,
			LastEdge = RightEdge,
			NumEdges,
			InvalidEdge
		};

		StandardNodeGadget( Gaffer::NodePtr node );
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
		/// Places an additional Gadgets alongside the
		/// Nodules at the end of each outside edge.
		void setEdgeGadget( Edge edge, GadgetPtr gadget );
		Gadget *getEdgeGadget( Edge edge );
		const Gadget *getEdgeGadget( Edge edge ) const;

		void setLabelsVisibleOnHover( bool labelsVisible );
		bool getLabelsVisibleOnHover() const;

		virtual Imath::Box3f bound() const;

	protected :

		virtual void doRender( const Style *style ) const;

		const Imath::Color3f *userColor() const;

	private :

		LinearContainer *noduleContainer( Edge edge );
		const LinearContainer *noduleContainer( Edge edge ) const;

		NoduleLayout *noduleLayout( Edge edge );
		const NoduleLayout *noduleLayout( Edge edge ) const;

		LinearContainer *paddingRow();
		const LinearContainer *paddingRow() const;

		IndividualContainer *iconContainer();
		const IndividualContainer *iconContainer() const;

		IndividualContainer *contentsContainer();
		const IndividualContainer *contentsContainer() const;

		static NodeGadgetTypeDescription<StandardNodeGadget> g_nodeGadgetTypeDescription;

		void plugDirtied( const Gaffer::Plug *plug );

		void enter( Gadget *gadget );
		void leave( Gadget *gadget );
		bool dragEnter( GadgetPtr gadget, const DragDropEvent &event );
		bool dragMove( GadgetPtr gadget, const DragDropEvent &event );
		bool dragLeave( GadgetPtr gadget, const DragDropEvent &event );
		bool drop( GadgetPtr gadget, const DragDropEvent &event );

		Gadget *closestDragDestinationProxy( const DragDropEvent &event ) const;
		bool noduleIsCompatible( const Nodule *nodule, const DragDropEvent &event ) const;
		bool plugAdderIsCompatible( const PlugAdder *plugAdder, const DragDropEvent &event ) const;

		void nodeMetadataChanged( IECore::TypeId nodeTypeId, IECore::InternedString key, const Gaffer::Node *node );

		bool updateUserColor();
		void updatePadding();
		void updateNodeEnabled( const Gaffer::Plug *dirtiedPlug = NULL );
		void updateIcon();
		bool updateShape();

		IE_CORE_FORWARDDECLARE( ErrorGadget );
		ErrorGadget *errorGadget( bool createIfMissing = true );
		void error( const Gaffer::Plug *plug, const Gaffer::Plug *source, const std::string &message );
		void displayError( Gaffer::ConstPlugPtr plug, const std::string &message );

		bool m_nodeEnabled;
		bool m_labelsVisibleOnHover;
		// We accept drags onto the node itself and
		// forward them to the nearest compatible
		// Nodule or PlugAdder. This provides the user
		// with a bigger drag target that is easier
		// to hit.
		Gadget *m_dragDestinationProxy;
		boost::optional<Imath::Color3f> m_userColor;
		bool m_oval;

};

IE_CORE_DECLAREPTR( StandardNodeGadget )

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<StandardNodeGadget> > StandardNodeGadgetIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<StandardNodeGadget> > RecursiveStandardNodeGadgetIterator;

} // namespace GafferUI

#endif // GAFFERUI_STANDARDNODEGADGET_H
