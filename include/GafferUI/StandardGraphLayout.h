//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFERUI_STANDARDGRAPHLAYOUT_H
#define GAFFERUI_STANDARDGRAPHLAYOUT_H

#include "OpenEXR/ImathBox.h"

#include "GafferUI/GraphLayout.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Plug )

} // namespace Gaffer

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( NodeGadget )
IE_CORE_FORWARDDECLARE( ConnectionGadget )

class StandardGraphLayout : public GraphLayout
{

	public :

		StandardGraphLayout();		
		virtual ~StandardGraphLayout();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::StandardGraphLayout, StandardGraphLayoutTypeId, GraphLayout );

		virtual bool connectNode( GraphGadget *graph, Gaffer::Node *node, Gaffer::Set *potentialInputs ) const;
		virtual bool connectNodes( GraphGadget *graph, Gaffer::Set *nodes, Gaffer::Set *potentialInputs ) const;
		
		virtual void positionNode( GraphGadget *graph, Gaffer::Node *node, const Imath::V2f &fallbackPosition = Imath::V2f( 0 ) ) const;
		virtual void positionNodes( GraphGadget *graph, Gaffer::Set *nodes, const Imath::V2f &fallbackPosition = Imath::V2f( 0 ) ) const;		

	private :
	
		bool connectNodeInternal( GraphGadget *graph, Gaffer::Node *node, Gaffer::Set *potentialInputs, bool insertIfPossible ) const;

		size_t outputPlugs( NodeGadget *nodeGadget, std::vector<Gaffer::Plug *> &plugs ) const;
		size_t outputPlugs( GraphGadget *graph, Gaffer::Set *nodes, std::vector<Gaffer::Plug *> &plugs ) const;
		Gaffer::Plug *correspondingOutput( const Gaffer::Plug *input ) const;
		size_t unconnectedInputPlugs( NodeGadget *nodeGadget, std::vector<Gaffer::Plug *> &plugs ) const;
						
		// We calculate node positions based on their connections to other nodes. We first compute a hard
		// constraint which guarantees that the node is to the side of it's connections indicated by the nodule
		// tangents. In the case of all connections being either vertical or horizontal, this will only
		// give us a constraint in one dimension, so we compute a soft constraint for that dimension, based on
		// trying to keep the node centered between its connections. Returns false if no connections were found
		// and therefore nothing could be computed, true otherwise.
		bool nodeConstraints( GraphGadget *graph, Gaffer::Node *node, Gaffer::Set *excludedNodes, Imath::Box2f &hardConstraint, Imath::V2f &softConstraint ) const;

};

IE_CORE_DECLAREPTR( GraphLayout );

} // namespace GafferUI

#endif // GAFFERUI_STANDARDGRAPHLAYOUT_H
