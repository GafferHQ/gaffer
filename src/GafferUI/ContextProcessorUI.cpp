//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/NoduleLayout.h"
#include "GafferUI/PlugAdder.h"

#include "Gaffer/ContextProcessor.h"

#include "boost/bind/bind.hpp"

using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;

namespace
{

class ContextProcessorPlugAdder : public PlugAdder
{

	public :

		ContextProcessorPlugAdder( ContextProcessorPtr node )
			:	m_node( node )
		{
			node->childAddedSignal().connect( boost::bind( &ContextProcessorPlugAdder::childAdded, this ) );
			node->childRemovedSignal().connect( boost::bind( &ContextProcessorPlugAdder::childRemoved, this ) );

			updateVisibility();
		}

	protected :

		void createConnection( Plug *endpoint ) override
		{
			m_node->setup( endpoint );

			bool inOpposite = false;
			if( endpoint->direction() == Plug::Out )
			{
				m_node->inPlug()->setInput( endpoint );
				inOpposite = false;
			}
			else
			{
				endpoint->setInput( m_node->outPlug() );
				inOpposite = true;
			}

			applyEdgeMetadata( m_node->inPlug(), inOpposite );
			applyEdgeMetadata( m_node->outPlug(), !inOpposite );
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
			setVisible( !m_node->inPlug() );
		}

		ContextProcessorPtr m_node;

};

struct Registration
{

	Registration()
	{
		NoduleLayout::registerCustomGadget( "GafferUI.ContextProcessorUI.PlugAdder", &create );
	}

	private :

		static GadgetPtr create( GraphComponentPtr parent )
		{
			ContextProcessorPtr contextProcessor = runTimeCast<ContextProcessor>( parent );
			if( !contextProcessor )
			{
				throw Exception( "ContextProcessorPlugAdder requires a ContextProcessor" );
			}

			return new ContextProcessorPlugAdder( contextProcessor );
		}

};

Registration g_registration;

} // namespace
