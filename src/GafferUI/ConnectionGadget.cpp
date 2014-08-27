//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
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

#include "IECore/Exception.h"

#include "Gaffer/Node.h"

#include "GafferUI/ConnectionGadget.h"
#include "GafferUI/GraphGadget.h"
#include "GafferUI/Nodule.h"

using namespace GafferUI;

IE_CORE_DEFINERUNTIMETYPED( ConnectionGadget );

ConnectionGadget::ConnectionGadget( GafferUI::NodulePtr srcNodule, GafferUI::NodulePtr dstNodule )
	:	Gadget( defaultName<ConnectionGadget>() ), m_minimised( false )
{
	setNodules( srcNodule, dstNodule );
}

ConnectionGadget::~ConnectionGadget()
{
}

bool ConnectionGadget::acceptsParent( const Gaffer::GraphComponent *potentialParent ) const
{
	if( !Gadget::acceptsParent( potentialParent ) )
	{
		return false;
	}
	return IECore::runTimeCast<const GraphGadget>( potentialParent );
}

Nodule *ConnectionGadget::srcNodule()
{
	return m_srcNodule.get();
}

const Nodule *ConnectionGadget::srcNodule() const
{
	return m_srcNodule.get();
}

Nodule *ConnectionGadget::dstNodule()
{
	return m_dstNodule.get();
}

const Nodule *ConnectionGadget::dstNodule() const
{
	return m_dstNodule.get();
}

void ConnectionGadget::setNodules( GafferUI::NodulePtr srcNodule, GafferUI::NodulePtr dstNodule )
{
	if( !dstNodule )
	{
		// we must have a destination
		throw IECore::Exception( "No destination Nodule." );
	}
	if( srcNodule )
	{
		// if we have a source nodule then it must be connected to the destination
		if( srcNodule->plug() != dstNodule->plug()->getInput<Gaffer::Plug>() )
		{
			throw IECore::Exception( "Source plug not connected to destination plug." );
		}
	}
	else
	{
		// if we have no source nodule (because it isn't visible) then our destination
		// plug must at least have an input for us to represent as a dangler.
		if( !dstNodule->plug()->getInput<Gaffer::Plug>() )
		{
			throw IECore::Exception( "Destination plug has no input." );
		}
	}

	m_srcNodule = srcNodule;
	m_dstNodule = dstNodule;
}

void ConnectionGadget::setMinimised( bool minimised )
{
	if( minimised == m_minimised )
	{
		return;
	}
	m_minimised = minimised;
	renderRequestSignal()( this );
}

bool ConnectionGadget::getMinimised() const
{
	return m_minimised;
}

ConnectionGadgetPtr ConnectionGadget::create( NodulePtr srcNodule, NodulePtr dstNodule )
{
	const Gaffer::Plug *plug = dstNodule->plug();

	if( const Gaffer::Node *node = plug->node() )
	{
		std::string plugPath = plug->relativeName( node );
		const NamedCreatorMap &m = namedCreators();
		IECore::TypeId t = node->typeId();
		while( t!=IECore::InvalidTypeId )
		{
			NamedCreatorMap::const_iterator it = m.find( t );
			if( it!=m.end() )
			{
				for( RegexAndCreatorVector::const_reverse_iterator nIt = it->second.rbegin(); nIt!=it->second.rend(); nIt++ )
				{
					if( boost::regex_match( plugPath, nIt->first ) )
					{
						return nIt->second( srcNodule, dstNodule );
					}
				}
			}
			t = IECore::RunTimeTyped::baseTypeId( t );
		}
	}

	CreatorMap &m = creators();
	IECore::TypeId t = plug->typeId();
	while( t!=IECore::InvalidTypeId )
	{
		CreatorMap::const_iterator it = m.find( t );
		if( it!=m.end() )
		{
			return it->second( srcNodule, dstNodule );
		}
		t = IECore::RunTimeTyped::baseTypeId( t );
	}

	return NULL;
}

void ConnectionGadget::registerConnectionGadget( IECore::TypeId dstPlugType, ConnectionGadgetCreator creator )
{
	creators()[dstPlugType] = creator;
}

void ConnectionGadget::registerConnectionGadget( const IECore::TypeId nodeType, const std::string &dstPlugPathRegex, ConnectionGadgetCreator creator )
{
	namedCreators()[nodeType].push_back( RegexAndCreator( boost::regex( dstPlugPathRegex ), creator ) );
}

ConnectionGadget::CreatorMap &ConnectionGadget::creators()
{
	static CreatorMap m;
	return m;
}

ConnectionGadget::NamedCreatorMap &ConnectionGadget::namedCreators()
{
	static NamedCreatorMap m;
	return m;
}
