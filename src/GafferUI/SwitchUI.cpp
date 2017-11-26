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
#include "Gaffer/UndoScope.h"
#include "Gaffer/ScriptNode.h"

#include "GafferUI/Nodule.h"
#include "GafferUI/PlugAdder.h"
#include "GafferUI/NoduleLayout.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;

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

		bool canCreateConnection( const Plug *endpoint ) const override
		{
			return PlugAdder::canCreateConnection( endpoint );
		}

		void createConnection( Plug *endpoint ) override
		{
			m_switch->setup( endpoint );
			ArrayPlug *inPlug = m_switch->getChild<ArrayPlug>( "in" );
			Plug *outPlug = m_switch->getChild<Plug>( "out" );

			bool inOpposite = false;
			if( endpoint->direction() == Plug::Out )
			{
				inPlug->getChild<Plug>( 0 )->setInput( endpoint );
				inOpposite = false;
			}
			else
			{
				endpoint->setInput( outPlug );
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
			setVisible( m_switch->getChild<ArrayPlug>( "in" ) == nullptr );
		}

		SwitchComputeNodePtr m_switch;

};

struct Registration
{

	Registration()
	{
		NoduleLayout::registerCustomGadget( "GafferUI.SwitchUI.PlugAdder.Top", boost::bind( &create, ::_1, StandardNodeGadget::TopEdge ) );
		NoduleLayout::registerCustomGadget( "GafferUI.SwitchUI.PlugAdder.Bottom", boost::bind( &create, ::_1, StandardNodeGadget::BottomEdge ) );
		NoduleLayout::registerCustomGadget( "GafferUI.SwitchUI.PlugAdder.Left", boost::bind( &create, ::_1, StandardNodeGadget::LeftEdge ) );
		NoduleLayout::registerCustomGadget( "GafferUI.SwitchUI.PlugAdder.Right", boost::bind( &create, ::_1, StandardNodeGadget::RightEdge ) );
	}

	private :

		static GadgetPtr create( GraphComponentPtr parent, StandardNodeGadget::Edge edge )
		{
			SwitchComputeNodePtr switchNode = runTimeCast<SwitchComputeNode>( parent );
			if( !switchNode )
			{
				throw Exception( "SwitchPlugAdder requires a SwitchComputeNode" );
			}

			return new SwitchPlugAdder( switchNode, edge );
		}

};

Registration g_registration;

} // namespace
