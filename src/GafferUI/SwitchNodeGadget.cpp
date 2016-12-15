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

#include "boost/bind.hpp"

#include "Gaffer/Switch.h"
#include "Gaffer/ArrayPlug.h"
#include "Gaffer/UndoContext.h"
#include "Gaffer/ScriptNode.h"

#include "GafferUI/Nodule.h"
#include "GafferUI/PlugAdder.h"
#include "GafferUI/Private/SwitchNodeGadget.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferUI::Private;

namespace
{

class SwitchPlugAdder : public PlugAdder
{

	public :

		SwitchPlugAdder( SwitchComputeNodePtr node, StandardNodeGadget::Edge edge )
			:	PlugAdder( edge ), m_switch( node )
		{
			node->childAddedSignal().connect( boost::bind( &SwitchPlugAdder::childAdded, this ) );
			node->childRemovedSignal().connect( boost::bind( &SwitchPlugAdder::childRemoved, this ) );

			updateVisibility();
		}

	protected :

		virtual bool acceptsPlug( const Plug *connectionEndPoint ) const
		{
			return true;
		}

		virtual void addPlug( Plug *connectionEndPoint )
		{
			UndoContext undoContext( m_switch->ancestor<ScriptNode>() );

			m_switch->setup( connectionEndPoint );
			ArrayPlug *inPlug = m_switch->getChild<ArrayPlug>( "in" );
			Plug *outPlug = m_switch->getChild<Plug>( "out" );

			bool inOpposite = false;
			if( connectionEndPoint->direction() == Plug::Out )
			{
				inPlug->getChild<Plug>( 0 )->setInput( connectionEndPoint );
				inOpposite = false;
			}
			else
			{
				connectionEndPoint->setInput( outPlug );
				inOpposite = true;
			}

			applyEdgeMetadata( inPlug, inOpposite );
			applyEdgeMetadata( outPlug, !inOpposite );
		}

	private :

		void childAdded()
		{
			updateVisibility();
		}

		void childRemoved()
		{
			updateVisibility();
		}

		void updateVisibility()
		{
			setVisible( m_switch->getChild<ArrayPlug>( "in" ) == NULL );
		}

		SwitchComputeNodePtr m_switch;

};

} // namespace

StandardNodeGadget::NodeGadgetTypeDescription<SwitchNodeGadget> SwitchNodeGadget::g_nodeGadgetTypeDescription( SwitchComputeNode::staticTypeId() );

SwitchNodeGadget::SwitchNodeGadget( Gaffer::NodePtr node )
	:	StandardNodeGadget( node )
{
	SwitchComputeNodePtr switchNode = runTimeCast<SwitchComputeNode>( node );
	if( !switchNode )
	{
		throw Exception( "SwitchNodeGadget requires a SwitchComputeNode" );
	}

	setEdgeGadget( LeftEdge, new SwitchPlugAdder( switchNode, LeftEdge ) );
	setEdgeGadget( RightEdge, new SwitchPlugAdder( switchNode, RightEdge ) );
	if( !node->isInstanceOf( "GafferScene::ShaderSwitch" ) )
	{
		/// \todo Either remove ShaderSwitch on the grounds that it
		/// doesn't really do anything above and beyond a regular
		/// SwitchComputeNode, or come up with a metadata convention
		/// to control this behaviour. What would be really nice is
		/// to control the whole of the NodeGadget layout using the
		/// same metadata conventions as the PlugLayout on the widget
		/// side of things.
		setEdgeGadget( TopEdge, new SwitchPlugAdder( switchNode, TopEdge ) );
		setEdgeGadget( BottomEdge, new SwitchPlugAdder( switchNode, BottomEdge ) );
	}
}
