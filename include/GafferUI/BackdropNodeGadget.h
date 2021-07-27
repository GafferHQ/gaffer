//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_BACKDROPNODEGADGET_H
#define GAFFERUI_BACKDROPNODEGADGET_H

#include "GafferUI/NodeGadget.h"

#include "Gaffer/Backdrop.h"
#include "Gaffer/BoxPlug.h"

namespace GafferUI
{

class GAFFERUI_API BackdropNodeGadget : public NodeGadget
{

	public :

		BackdropNodeGadget( Gaffer::NodePtr node );
		~BackdropNodeGadget() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferUI::BackdropNodeGadget, BackdropNodeGadgetTypeId, NodeGadget );

		std::string getToolTip( const IECore::LineSegment3f &line ) const override;

		void setBound( const Imath::Box2f &bound );
		Imath::Box2f getBound() const;

		/// Resizes the backdrop to frame the specified nodes.
		/// \undoable
		void frame( const std::vector<Gaffer::Node *> &nodes );
		/// Fills nodes with all the nodes currently enclosed by the backdrop.
		void framed( std::vector<Gaffer::Node *> &nodes ) const;

		Imath::Box3f bound() const override;

	protected :

		void doRenderLayer( Layer layer, const Style *style, RenderReason reason ) const override;
		unsigned layerMask() const override;
		Imath::Box3f renderBound() const override;

	private :

		void contextChanged();
		void plugDirtied( const Gaffer::Plug *plug );

		bool mouseMove( Gadget *gadget, const ButtonEvent &event );
		bool buttonPress( Gadget *gadget, const ButtonEvent &event );
		IECore::RunTimeTypedPtr dragBegin( Gadget *gadget, const DragDropEvent &event );
		bool dragEnter( Gadget *gadget, const DragDropEvent &event );
		bool dragMove( Gadget *gadget, const DragDropEvent &event );
		bool dragEnd( Gadget *gadget, const DragDropEvent &event );
		void leave( Gadget *gadget, const ButtonEvent &event );

		// The width in gadget coordinates that can be hovered and then dragged at the edge of frame.
		float hoverWidth() const;
		// -1 means the min in that direction, +1 means the max in that direction, 0
		// means not hovered in that direction.
		void hoveredEdges( const ButtonEvent &event, int &horizontal, int &vertical ) const;

		void nodeMetadataChanged( IECore::InternedString key );

		bool updateUserColor();

		Gaffer::Box2fPlug *acquireBoundPlug( bool createIfMissing = true );

		bool m_hovered;
		int m_horizontalDragEdge;
		int m_verticalDragEdge;
		int m_mergeGroupId;

		boost::optional<Imath::Color3f> m_userColor;

		static NodeGadgetTypeDescription<BackdropNodeGadget> g_nodeGadgetTypeDescription;

};

IE_CORE_DECLAREPTR( BackdropNodeGadget );

} // namespace GafferUI

#endif // GAFFERUI_BACKDROPNODEGADGET_H
