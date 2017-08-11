//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Box.h"
#include "Gaffer/BoxIn.h"
#include "Gaffer/BoxOut.h"
#include "Gaffer/UndoScope.h"
#include "Gaffer/ScriptNode.h"

#include "GafferUI/StandardNodeGadget.h"
#include "GafferUI/PlugAdder.h"
#include "GafferUI/NoduleLayout.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;

namespace
{

class BoxPlugAdder : public PlugAdder
{

	public :

		BoxPlugAdder( BoxPtr box, StandardNodeGadget::Edge edge )
			:	PlugAdder( edge ), m_box( box )
		{
		}

	protected :

		bool canCreateConnection( const Plug *endpoint ) override
		{
			if( !PlugAdder::canCreateConnection( endpoint ) )
			{
				return false;
			}

			if( endpoint->node() == m_box )
			{
				return false;
			}

			return true;
		}

		void createConnection( Plug *endpoint ) override
		{
			UndoScope undoScope( m_box->ancestor<ScriptNode>() );

			BoxIOPtr boxIO;
			if( endpoint->direction() == Plug::In )
			{
				boxIO = new BoxOut;
			}
			else
			{
				boxIO = new BoxIn;
			}

			m_box->addChild( boxIO );
			boxIO->setup( endpoint );

			if( endpoint->direction() == Plug::In )
			{
				endpoint->setInput( boxIO->promotedPlug<Plug>() );
			}
			else
			{
				boxIO->promotedPlug<Plug>()->setInput( endpoint );
			}

			applyEdgeMetadata( boxIO->promotedPlug<Plug>() );
			applyEdgeMetadata( boxIO->plug<Plug>(), /* opposite = */ true );
		}

	private :

		BoxPtr m_box;

};

struct Registration
{

	Registration()
	{
		NoduleLayout::registerCustomGadget( "GafferUI.BoxUI.PlugAdder.Top", boost::bind( &create, ::_1, StandardNodeGadget::TopEdge ) );
		NoduleLayout::registerCustomGadget( "GafferUI.BoxUI.PlugAdder.Bottom", boost::bind( &create, ::_1, StandardNodeGadget::BottomEdge ) );
		NoduleLayout::registerCustomGadget( "GafferUI.BoxUI.PlugAdder.Left", boost::bind( &create, ::_1, StandardNodeGadget::LeftEdge ) );
		NoduleLayout::registerCustomGadget( "GafferUI.BoxUI.PlugAdder.Right", boost::bind( &create, ::_1, StandardNodeGadget::RightEdge ) );
	}

	private :

		static GadgetPtr create( GraphComponentPtr parent, StandardNodeGadget::Edge edge )
		{
			if( BoxPtr box = runTimeCast<Box>( parent ) )
			{
				return new BoxPlugAdder( box, edge );
			}
			throw IECore::Exception( "Expected a Box" );
		}

};

Registration g_registration;

} // namespace

