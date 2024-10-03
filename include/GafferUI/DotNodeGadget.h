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

#pragma once

#include "GafferUI/StandardNodeGadget.h"

#include "Gaffer/Dot.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Context )
IE_CORE_FORWARDDECLARE( Plug )

} // namespace Gaffer

namespace GafferUI
{

class GAFFERUI_API DotNodeGadget : public StandardNodeGadget
{

	public :

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferUI::DotNodeGadget, DotNodeGadgetTypeId, StandardNodeGadget );

		explicit DotNodeGadget( Gaffer::NodePtr node );
		~DotNodeGadget() override;

		Imath::Box3f bound() const override;

	protected :

		void renderLayer( Layer layer, const Style *style, RenderReason reason ) const override;
		void updateFromContextTracker( const ContextTracker *contextTracker ) override;

	private :

		Gaffer::Dot *dotNode();
		const Gaffer::Dot *dotNode() const;
		Gaffer::Node *upstreamNode();

		void plugDirtied( const Gaffer::Plug *plug );
		void nodeNameChanged( const Gaffer::GraphComponent *graphComponent );
		void updateUpstreamNameChangedConnection();
		void updateLabel();

		bool dragEnter( const DragDropEvent &event );
		bool drop( const DragDropEvent &event );

		Gaffer::Signals::ScopedConnection m_upstreamNameChangedConnection;

		Gaffer::ConstContextPtr m_labelContext;
		std::string m_label;
		Imath::V2f m_labelPosition;

		static NodeGadgetTypeDescription<DotNodeGadget> g_nodeGadgetTypeDescription;

};

IE_CORE_DECLAREPTR( DotNodeGadget )

} // namespace GafferUI
