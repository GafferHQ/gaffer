//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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
#include "GafferUI/StandardNodeGadget.h"

#include "Gaffer/EditScope.h"
#include "Gaffer/MetadataAlgo.h"

#include "boost/bind/bind.hpp"

using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;

namespace
{

class EditScopePlugAdder : public PlugAdder
{

	public :

		EditScopePlugAdder( EditScopePtr editScope )
			:	m_editScope( editScope )
		{
			m_editScope->childAddedSignal().connect( boost::bind( &EditScopePlugAdder::childAdded, this ) );
			m_editScope->childRemovedSignal().connect( boost::bind( &EditScopePlugAdder::childRemoved, this ) );
			updateVisibility();
		}

	protected :

		bool canCreateConnection( const Plug *endpoint ) const override
		{
			if( !PlugAdder::canCreateConnection( endpoint ) )
			{
				return false;
			}

			if(
				endpoint->node() == m_editScope ||
				m_editScope->inPlug()
			)
			{
				return false;
			}

			if( MetadataAlgo::readOnly( m_editScope.get() ) )
			{
				return false;
			}

			return true;
		}

		void createConnection( Plug *endpoint ) override
		{
			m_editScope->setup( endpoint );
			if( endpoint->direction() == Plug::In )
			{
				endpoint->setInput( m_editScope->outPlug() );
			}
			else
			{
				m_editScope->inPlug()->setInput( endpoint );
			}
		}

	private :

		void updateVisibility()
		{
			setVisible( !m_editScope->inPlug() );
		}

		void childAdded()
		{
			updateVisibility();
		}

		void childRemoved()
		{
			updateVisibility();
		}

		EditScopePtr m_editScope;

};

struct Registration
{

	Registration()
	{
		NoduleLayout::registerCustomGadget(
			"GafferUI.EditScopeUI.PlugAdder",
			[]( GraphComponentPtr parent ) {
				if( EditScopePtr editScope = runTimeCast<EditScope>( parent ) )
				{
					return new EditScopePlugAdder( editScope );
				}
				throw IECore::Exception( "Expected an EditScope" );
			}
		);
	}

};

Registration g_registration;

} // namespace
