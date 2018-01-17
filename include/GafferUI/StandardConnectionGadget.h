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

#include "Gaffer/StringAlgo.h"

#include "GafferUI/Export.h"
#include "GafferUI/ConnectionGadget.h"

namespace GafferUI
{

/// The standard implementation of the abstract ConnectionGadget base
/// class. Connections endpoints may be dragged + dropped, and the tooltip
/// displays the name of the source and destination plugs.
class GAFFERUI_API StandardConnectionGadget : public ConnectionGadget
{

	public :

		StandardConnectionGadget( GafferUI::NodulePtr srcNodule, GafferUI::NodulePtr dstNodule );
		~StandardConnectionGadget() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::StandardConnectionGadget, StandardConnectionGadgetTypeId, ConnectionGadget );

		Imath::Box3f bound() const override;

		void setNodules( GafferUI::NodulePtr srcNodule, GafferUI::NodulePtr dstNodule ) override;

		void updateDragEndPoint( const Imath::V3f position, const Imath::V3f &tangent ) override;

		Imath::V3f closestPoint( const Imath::V3f &p ) const override;

		std::string getToolTip( const IECore::LineSegment3f &line ) const override;

	protected :

		void doRenderLayer( Layer layer, const Style *style ) const override;
		bool hasLayer( Layer layer ) const override;

	private :

		static ConnectionGadgetTypeDescription<StandardConnectionGadget> g_connectionGadgetTypeDescription;

		void setPositionsFromNodules();
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

		bool nodeSelected( const Nodule *nodule ) const;

		void plugMetadataChanged( IECore::TypeId nodeTypeId, const Gaffer::StringAlgo::MatchPattern &plugPath, IECore::InternedString key, const Gaffer::Plug *plug );

		bool updateUserColor();

		void updateDotPreviewLocation( const ButtonEvent &event );

		Imath::V3f m_srcPos;
		Imath::V3f m_srcTangent;
		Imath::V3f m_dstPos;
		Imath::V3f m_dstTangent;

		Gaffer::Plug::Direction m_dragEnd;

		/// \todo Store the end we are hovering over as
		/// type Plug::Direction, and update the Style
		/// classes so we can show which end is being
		/// hovered.
		bool m_hovering;
		boost::optional<Imath::Color3f> m_userColor;

		bool m_dotPreview;
		Imath::V3f m_dotPreviewLocation;

		boost::signals::scoped_connection m_keyPressConnection;
		boost::signals::scoped_connection m_keyReleaseConnection;
};

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<StandardConnectionGadget> > StandardConnectionGadgetIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<StandardConnectionGadget> > RecursiveStandardConnectionGadgetIterator;

} // namespace GafferUI

#endif // GAFFERUI_STANDARDCONNECTIONGADGET_H
