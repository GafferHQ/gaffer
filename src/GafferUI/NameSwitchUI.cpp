//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "GafferUI/PlugAdder.h"

#include "GafferUI/NoduleLayout.h"

#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/NameSwitch.h"
#include "Gaffer/NameValuePlug.h"

#include "boost/bind/bind.hpp"

using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;

namespace
{

class NameSwitchPlugAdder : public PlugAdder
{

	public :

		NameSwitchPlugAdder( ArrayPlugPtr plug )
			:	m_plug( plug )
		{
		}

	protected :

		bool canCreateConnection( const Plug *endpoint ) const override
		{
			if( !PlugAdder::canCreateConnection( endpoint ) )
			{
				return false;
			}

			// Assume that if the first plug wouldn't accept the input,
			// then neither would the new one that we add.

			if( !m_plug->children().size() )
			{
				return false;
			}
			else if( !m_plug->getChild<NameValuePlug>( 0 )->valuePlug()->acceptsInput( endpoint ) )
			{
				return false;
			}

			return m_plug->children().size() < m_plug->maxSize();
		}

		void createConnection( Plug *endpoint ) override
		{
			const size_t s = m_plug->children().size();
			m_plug->resize( s + 1 );
			auto p = m_plug->getChild<NameValuePlug>( s );

			if( endpoint->direction() == Plug::In )
			{
				endpoint->setInput( p->valuePlug() );
			}
			else
			{
				p->valuePlug()->setInput( endpoint );
			}

			auto nameSwitch = m_plug->parent<NameSwitch>();
			if( !nameSwitch || m_plug != nameSwitch->inPlugs() )
			{
				// Not `NameSwitch.in` - most likely a promoted copy.
				// We won't be inheriting the metadata registered for
				// NameSwitch nodes, so must explicitly copy the
				// right metadata onto the new plug.
				//
				// > Todo : Consider improvements to the Medatata registration
				// > mechanism so that "ancestor relative" metadata can be
				// > registered against specific GraphComponent _instances_ rather
				// > than only against GraphComponent _types_. Also introduce
				// > the ability to register dynamic (Metadata::PlugValueFunction)
				// > metadata against instances, so we can properly support the
				// > "noduleLayout:label" metadata.
				MetadataAlgo::copy( m_plug->getChild<Plug>( s - 1 ), p );
			}
		}

	private :

		ArrayPlugPtr m_plug;

};

struct Registration
{

	Registration()
	{
		NoduleLayout::registerCustomGadget( "GafferUI.NameSwitchUI.PlugAdder", &create );
	}

	private :

		static GadgetPtr create( GraphComponentPtr parent )
		{
			if( auto a = runTimeCast<ArrayPlug>( parent ) )
			{
				return new NameSwitchPlugAdder( a );
			}
			throw IECore::Exception( "Expected an ArrayPlug" );
		}

};

Registration g_registration;

} // namespace
