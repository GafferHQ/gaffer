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

#include "GafferUI/LinearContainer.h"
#include "GafferUI/NodeGadget.h"

namespace GafferUI
{

class PlugAdder;
class NoduleLayout;
class ConnectionCreator;

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

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferUI::StandardNodeGadget, StandardNodeGadgetTypeId, NodeGadget );

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

		explicit StandardNodeGadget( Gaffer::NodePtr node );
		~StandardNodeGadget() override;

		Nodule *nodule( const Gaffer::Plug *plug ) override;
		const Nodule *nodule( const Gaffer::Plug *plug ) const override;
		Imath::V3f connectionTangent( const ConnectionCreator *creator ) const override;

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

		Imath::Box3f bound() const override;

		/// This currently needs to be public so that AnnotationsGadget can manually account for
		/// the thick border on focussed StandardNodeGadgets.  This is a bit of a weird dependency:
		/// the long term solution may involve giving a NodeGadget more responsibility over how
		/// it's annotations are drawn
		float focusBorderWidth() const;

		void setHighlighted( bool highlighted ) override;

	protected :

		StandardNodeGadget( Gaffer::NodePtr node, bool auxillary );

		void renderLayer( Layer layer, const Style *style, RenderReason reason ) const override;
		unsigned layerMask() const override;
		Imath::Box3f renderBound() const override;

		const Imath::Color3f *userColor() const;

		void updateFromContextTracker( const ContextTracker *contextTracker ) override;

	private :

		LinearContainer *noduleContainer( Edge edge );
		const LinearContainer *noduleContainer( Edge edge ) const;

		NoduleLayout *noduleLayout( Edge edge );
		const NoduleLayout *noduleLayout( Edge edge ) const;

		LinearContainer *contentsColumn();
		const LinearContainer *contentsColumn() const;

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

		ConnectionCreator *closestDragDestination( const DragDropEvent &event ) const;

		void nodeMetadataChanged( IECore::InternedString key );

		bool updateUserColor();
		void updateMinWidth();
		void updatePadding();
		void updateStrikeThroughVisibility( const Gaffer::Plug *dirtiedPlug = nullptr );
		void updateIcon();
		bool updateShape();
		void updateFocusGadgetVisibility();
		void updateTextDimming();

		IE_CORE_FORWARDDECLARE( ErrorGadget );
		ErrorGadget *errorGadget( bool createIfMissing = true );
		void error( const Gaffer::Plug *plug, const Gaffer::Plug *source, const std::string &message );
		void displayError( Gaffer::ConstPlugPtr plug, const std::string &message );

		std::optional<bool> m_nodeEnabledInContextTracker;
		bool m_strikeThroughVisible;
		bool m_labelsVisibleOnHover;
		// We accept drags onto the NodeGadget itself and
		// use them to create a connection to the
		// nearest Nodule or PlugAdder child. This provides
		// the user with a bigger drag target that is easier
		// to hit.
		ConnectionCreator *m_dragDestination;
		std::optional<Imath::Color3f> m_userColor;
		bool m_oval;
		bool m_auxiliary;

		GadgetPtr m_focusGadget;

};

IE_CORE_DECLAREPTR( StandardNodeGadget )

} // namespace GafferUI
