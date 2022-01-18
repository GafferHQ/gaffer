//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_STANDARDCONNECTIONGADGET_H
#define GAFFERUI_STANDARDCONNECTIONGADGET_H

#include "GafferUI/ConnectionGadget.h"

#include "Gaffer/Plug.h"

#include "IECore/StringAlgo.h"

namespace GafferUI
{

class NodeGadget;

/// The standard implementation of the abstract ConnectionGadget base
/// class. Connections endpoints may be dragged + dropped, and the tooltip
/// displays the name of the source and destination plugs.
class GAFFERUI_API StandardConnectionGadget : public ConnectionGadget
{

	public :

		StandardConnectionGadget( GafferUI::NodulePtr srcNodule, GafferUI::NodulePtr dstNodule );
		~StandardConnectionGadget() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferUI::StandardConnectionGadget, StandardConnectionGadgetTypeId, ConnectionGadget );

		Imath::Box3f bound() const override;

		void setNodules( GafferUI::NodulePtr srcNodule, GafferUI::NodulePtr dstNodule ) override;

		bool canCreateConnection( const Gaffer::Plug *endpoint ) const override;
		void updateDragEndPoint( const Imath::V3f position, const Imath::V3f &tangent ) override;
		void createConnection( Gaffer::Plug *endpoint ) override;

		Imath::V3f closestPoint( const Imath::V3f &p ) const override;

		std::string getToolTip( const IECore::LineSegment3f &line ) const override;

	protected :

		void renderLayer( Layer layer, const Style *style, RenderReason reason ) const override;
		unsigned layerMask() const override;
		Imath::Box3f renderBound() const override;

	private :

		static ConnectionGadgetTypeDescription<StandardConnectionGadget> g_connectionGadgetTypeDescription;

		// Returns the NodeGadget for the source end of the
		// connection, even if `srcNodule()` is null. Will
		// return null if the node is hidden though.
		const NodeGadget *srcNodeGadget() const;
		// Decides whether this connection should be highlighted,
		// taking into account hovering, dragging, dot insertion
		// and the highlighted state of the nodes at either end.
		bool highlighted() const;
		// `m_srcPos` and `m_srcTangent` are stored as if the
		// connection is not minimised. This method returns them
		// adjusted according to `getMinimised().
		void minimisedPositionAndTangent( bool highlighted, Imath::V3f &position, Imath::V3f &tangent ) const;
		// Updates m_srcPos, m_srcTangent etc. We basically always
		// call this before accessing that state, so I'm not sure
		// why we store it at all - we could just return it instead.
		/// \todo Consider making the updates lazy based on events, or
		/// just drop the state.
		void updateConnectionGeometry();
		float distanceToNodeGadget( const IECore::LineSegment3f &line, const Nodule *nodule ) const;
		Gaffer::Plug::Direction endAt( const IECore::LineSegment3f &line ) const;

		void enter( const ButtonEvent &event );
		bool mouseMove( const ButtonEvent &event );
		void leave( const ButtonEvent &event );
		bool buttonPress( const ButtonEvent &event );
		IECore::RunTimeTypedPtr dragBegin( const DragDropEvent &event );
		bool dragEnter( const DragDropEvent &event );
		bool dragMove( const DragDropEvent &event );
		bool dragEnd(  const DragDropEvent &event );
		bool keyPressed( const KeyEvent &event );
		bool keyReleased( const KeyEvent &event );

		void plugMetadataChanged( const Gaffer::Plug *plug, IECore::InternedString key );

		bool updateUserColor();

		void updateDotPreviewLocation( const ButtonEvent &event );

		// Connection geometry - computed by `updateConnectionGeometry()`.
		Imath::V3f m_srcPos;
		Imath::V3f m_srcTangent;
		Imath::V3f m_dstPos;
		Imath::V3f m_dstTangent;
		bool m_auxiliary;

		Gaffer::Plug::Direction m_dragEnd;

		/// \todo Store the end we are hovering over as
		/// type Plug::Direction, and update the Style
		/// classes so we can show which end is being
		/// hovered.
		bool m_hovering;
		std::optional<Imath::Color3f> m_userColor;

		bool m_dotPreview;
		Imath::V3f m_dotPreviewLocation;

		bool m_addingConnection;
		Imath::V3f m_dstPosOrig;
		Imath::V3f m_dstTangentOrig;

		Gaffer::Signals::ScopedConnection m_keyPressConnection;
		Gaffer::Signals::ScopedConnection m_keyReleaseConnection;
};

} // namespace GafferUI

#endif // GAFFERUI_STANDARDCONNECTIONGADGET_H
