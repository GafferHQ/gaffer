//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Murray Stevenson. All rights reserved.
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

#include "GafferUI/Gadget.h"

#include "IECore/VectorTypedData.h"

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( ConnectionGadget );
IE_CORE_FORWARDDECLARE( GraphGadget );

class GAFFERUI_API DragEditGadget : public Gadget
{

	public :

		~DragEditGadget() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferUI::DragEditGadget, DragEditGadgetTypeId, Gadget );

		bool acceptsParent( const GraphComponent *potentialParent ) const override;

	protected :

		// Protected constructor and friend status so only GraphGadget can
		// construct us.
		DragEditGadget();
		friend class GraphGadget;

		void parentChanging( Gaffer::GraphComponent *newParent ) override;
		void renderLayer( Layer layer, const Style *style, RenderReason reason ) const override;
		unsigned layerMask() const override;
		Imath::Box3f renderBound() const override;

	private :

		GraphGadget *graphGadget();
		const GraphGadget *graphGadget() const;

		bool keyPress( GadgetPtr gadget, const KeyEvent &event );
		bool keyRelease( GadgetPtr gadget, const KeyEvent &event );
		bool buttonPress( GadgetPtr gadget, const ButtonEvent &event );
		bool buttonRelease( GadgetPtr gadget, const ButtonEvent &event );

		IECore::RunTimeTypedPtr dragBegin( GadgetPtr gadget, const DragDropEvent &event );
		bool dragEnter( GadgetPtr gadget, const DragDropEvent &event );
		bool dragMove( GadgetPtr gadget, const DragDropEvent &event );
		bool dragEnd( GadgetPtr gadget, const DragDropEvent &event );
		void leave();

		std::string undoMergeGroup() const;

		void disconnectConnectionGadgets();

		Gaffer::Signals::ScopedConnection m_graphGadgetKeyPressConnection;
		Gaffer::Signals::ScopedConnection m_graphGadgetKeyReleaseConnection;

		enum Mode
		{
			None,
			Disconnect
		};

		Mode m_mode;
		bool m_editable;
		int m_mergeGroupId;
		IECore::V3fVectorDataPtr m_dragPositions;

};

} // namespace GafferUI
