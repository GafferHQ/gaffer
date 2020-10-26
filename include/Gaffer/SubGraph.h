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

#ifndef GAFFER_SUBGRAPH_H
#define GAFFER_SUBGRAPH_H

#include "Gaffer/DependencyNode.h"

namespace Gaffer
{

class GAFFER_API SubGraph : public DependencyNode
{

	public :

		SubGraph( const std::string &name=defaultName<SubGraph>() );
		~SubGraph() override;

		GAFFER_NODE_DECLARE_TYPE( Gaffer::SubGraph, SubGraphTypeId, DependencyNode );

		/// Does nothing
		void affects( const Plug *input, AffectedPlugsContainer &outputs ) const override;

		/// Returns getChild<BoolPlug>( "enabled" ).
		BoolPlug *enabledPlug() override;
		const BoolPlug *enabledPlug() const override;

		/// Implemented to allow a user to define a pass-through behaviour
		/// by wiring the nodes inside this sub graph up appropriately. The
		/// input to the output plug must be connected from a node inside
		/// the sub graph, where that node itself has its enabled plug driven
		/// by the external enabled plug, and the correspondingInput for the
		/// node comes from one of the inputs to the sub graph.
		Plug *correspondingInput( const Plug *output ) override;
		const Plug *correspondingInput( const Plug *output ) const override;

};

} // namespace Gaffer

#endif // GAFFER_SUBGRAPH_H
