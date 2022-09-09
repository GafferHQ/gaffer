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

#include "GafferUI/PlugAdder.h"
#include "GafferUI/SpacerGadget.h"
#include "GafferUI/StandardNodeGadget.h"
#include "GafferUI/TextGadget.h"

#include "Gaffer/BoxIO.h"
#include "Gaffer/BoxOut.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/UndoScope.h"

#include "boost/algorithm/string/replace.hpp"
#include "boost/bind/bind.hpp"

using namespace boost::placeholders;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;

//////////////////////////////////////////////////////////////////////////
// PlugAdder
//////////////////////////////////////////////////////////////////////////

namespace
{

class BoxIOPlugAdder : public PlugAdder
{

	public :

		BoxIOPlugAdder( BoxIOPtr boxIO )
			:	m_boxIO( boxIO )
		{
			m_boxIO->childAddedSignal().connect( boost::bind( &BoxIOPlugAdder::childAdded, this ) );
			m_boxIO->childRemovedSignal().connect( boost::bind( &BoxIOPlugAdder::childRemoved, this ) );
			updateVisibility();
		}

	protected :

		bool canCreateConnection( const Plug *endpoint ) const override
		{
			if( !PlugAdder::canCreateConnection( endpoint ) )
			{
				return false;
			}

			if( MetadataAlgo::readOnly( m_boxIO.get() ) )
			{
				return false;
			}

			return endpoint->direction() == m_boxIO->direction();
		}

		void createConnection( Plug *endpoint ) override
		{
			std::string name = endpoint->relativeName( endpoint->node() );
			boost::replace_all( name, ".", "_" );
			m_boxIO->namePlug()->setValue( name );

			m_boxIO->setup( endpoint );

			applyEdgeMetadata( m_boxIO->plug() );
			if( BoxOut *boxOut = runTimeCast<BoxOut>( m_boxIO.get() ) )
			{
				applyEdgeMetadata( boxOut->passThroughPlug() );
			}
			if( m_boxIO->promotedPlug() )
			{
				applyEdgeMetadata( m_boxIO->promotedPlug(), /* opposite = */ true );
			}

			if( m_boxIO->direction() == Plug::In )
			{
				endpoint->setInput( m_boxIO->plug() );
			}
			else
			{
				m_boxIO->plug()->setInput( endpoint );
			}
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
			setVisible( !m_boxIO->plug() );
		}

		BoxIOPtr m_boxIO;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// StringPlugValueGadget
//////////////////////////////////////////////////////////////////////////

namespace
{

class NameGadget : public TextGadget
{

	public :

		NameGadget( BoxIOPtr boxIO )
			:	TextGadget( boxIO->namePlug()->getValue() ), m_boxIO( boxIO )
		{
			boxIO->plugSetSignal().connect( boost::bind( &NameGadget::plugSet, this, ::_1 ) );
		}

	private :

		void plugSet( const Plug *plug )
		{
			if( plug == m_boxIO->namePlug() )
			{
				setText( m_boxIO->namePlug()->getValue() );
			}
		}

		BoxIOPtr m_boxIO;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// NodeGadget
//////////////////////////////////////////////////////////////////////////

namespace
{

struct BoxIONodeGadgetCreator
{

	BoxIONodeGadgetCreator()
	{
		NodeGadget::registerNodeGadget( BoxIO::staticTypeId(), *this );
	}

	NodeGadgetPtr operator()( NodePtr node )
	{
		BoxIOPtr boxIO = runTimeCast<BoxIO>( node );
		if( !boxIO )
		{
			throw Exception( "Expected a BoxIO node" );
		}
		StandardNodeGadgetPtr result = new StandardNodeGadget( node );
		result->setEdgeGadget( StandardNodeGadget::LeftEdge, new BoxIOPlugAdder( boxIO ) );
		result->setEdgeGadget( StandardNodeGadget::RightEdge, new BoxIOPlugAdder( boxIO ) );
		result->setEdgeGadget( StandardNodeGadget::BottomEdge, new BoxIOPlugAdder( boxIO ) );
		result->setEdgeGadget( StandardNodeGadget::TopEdge, new BoxIOPlugAdder( boxIO ) );
		result->setContents( new NameGadget( boxIO ) );
		return result;
	}

};

BoxIONodeGadgetCreator g_boxIONodeGadgetCreator;

} // namespace
