//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Switch.h"

#include "GafferUI/StandardNodeGadget.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/PlugAdder.h"

using namespace Gaffer;
using namespace GafferUI;

namespace
{

class SwitchNodeGadget : public StandardNodeGadget
{

	public :

		SwitchNodeGadget( Gaffer::NodePtr node )
			:	StandardNodeGadget( node )
		{
			setEdgeGadget( LeftEdge, new PlugAdder( node, LeftEdge ) );
			setEdgeGadget( RightEdge, new PlugAdder( node, RightEdge ) );
			if( !node->isInstanceOf( "GafferScene::ShaderSwitch" ) )
			{
				/// \todo Either remove ShaderSwitch on the grounds that it
				/// doesn't really do anything above and beyond a regular
				/// SwitchComputeNode, or come up with a metadata convention
				/// to control this behaviour. What would be really nice is
				/// to control the whole of the NodeGadget layout using the
				/// same metadata conventions as the PlugLayout on the widget
				/// side of things.
				setEdgeGadget( TopEdge, new PlugAdder( node, TopEdge ) );
				setEdgeGadget( BottomEdge, new PlugAdder( node, BottomEdge ) );
			}
		}

	private :

		static NodeGadgetTypeDescription<SwitchNodeGadget> g_nodeGadgetTypeDescription;

};

StandardNodeGadget::NodeGadgetTypeDescription<SwitchNodeGadget> SwitchNodeGadget::g_nodeGadgetTypeDescription( SwitchComputeNode::staticTypeId() );

} // namespace
