//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/GraphLayout.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Plug )

} // namespace Gaffer

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( NodeGadget )
IE_CORE_FORWARDDECLARE( ConnectionGadget )

class GAFFERUI_API StandardGraphLayout : public GraphLayout
{

	public :

		StandardGraphLayout();
		~StandardGraphLayout() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::StandardGraphLayout, StandardGraphLayoutTypeId, GraphLayout );

		bool connectNode( GraphGadget *graph, Gaffer::Node *node, Gaffer::Set *potentialInputs ) const override;
		bool connectNodes( GraphGadget *graph, Gaffer::Set *nodes, Gaffer::Set *potentialInputs ) const override;

		void positionNode( GraphGadget *graph, Gaffer::Node *node, const Imath::V2f &fallbackPosition = Imath::V2f( 0 ) ) const override;
		void positionNodes( GraphGadget *graph, Gaffer::Set *nodes, const Imath::V2f &fallbackPosition = Imath::V2f( 0 ) ) const override;

		void layoutNodes( GraphGadget *graph, Gaffer::Set *nodes ) const override;

		/// @name Layout algorithm parameters
		////////////////////////////////////////////////////////////////////
		//@{
		/// A multiplier on the preferred connection length.
		void setConnectionScale( float scale );
		float getConnectionScale() const;
		/// A multiplier on the preferred separation between
		/// adjacent nodes.
		void setNodeSeparationScale( float scale );
		float getNodeSeparationScale() const;
		//@}

	private :

		bool connectNodeInternal( GraphGadget *graph, Gaffer::Node *node, Gaffer::Set *potentialInputs, bool insertIfPossible ) const;

		size_t outputPlugs( NodeGadget *nodeGadget, std::vector<Gaffer::Plug *> &plugs ) const;
		size_t outputPlugs( GraphGadget *graph, Gaffer::Set *nodes, std::vector<Gaffer::Plug *> &plugs ) const;
		Gaffer::Plug *correspondingOutput( const Gaffer::Plug *input ) const;
		size_t unconnectedInputPlugs( NodeGadget *nodeGadget, std::vector<Gaffer::Plug *> &plugs ) const;

		float m_connectionScale;
		float m_nodeSeparationScale;

};

IE_CORE_DECLAREPTR( StandardGraphLayout );

} // namespace GafferUI
