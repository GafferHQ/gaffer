//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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
#include "boost/bind/placeholders.hpp"

#include "Gaffer/CompoundPlug.h"
#include "Gaffer/Node.h"

using namespace Gaffer;
using namespace boost;

IE_CORE_DEFINERUNTIMETYPED( CompoundPlug )

CompoundPlug::CompoundPlug( const std::string &name, Direction direction, unsigned flags )
	:	ValuePlug( name, direction, flags )
{
	parentChangedSignal().connect( boost::bind( &CompoundPlug::parentChanged, this ) );
	childAddedSignal().connect( boost::bind( &CompoundPlug::childAddedOrRemoved, this ) );
	childRemovedSignal().connect( boost::bind( &CompoundPlug::childAddedOrRemoved, this ) );
}

CompoundPlug::~CompoundPlug()
{
}

bool CompoundPlug::acceptsChild( ConstGraphComponentPtr potentialChild ) const
{
	ConstPlugPtr p = IECore::runTimeCast<const Plug>( potentialChild );
	if( !p )
	{
		return false;
	}
	return p->direction()==direction();
}

bool CompoundPlug::acceptsInput( ConstPlugPtr input ) const
{
	if( !ValuePlug::acceptsInput( input ) )
	{
		return false;
	}
	if( input )
	{
		ConstCompoundPlugPtr p = IECore::runTimeCast<const CompoundPlug>( input );
		if( !p )
		{
			return false;
		}
		if( children().size()!=p->children().size() )
		{
			return false;
		}
		ChildContainer::const_iterator it1, it2;
		for( it1 = children().begin(), it2 = p->children().begin(); it1!=children().end(); it1++, it2++ )
		{
			if( !IECore::staticPointerCast<Plug>( *it1 )->acceptsInput( IECore::staticPointerCast<Plug>( *it2 ) ) )
			{
				return false;
			}
		}
	}
	return true;
}

void CompoundPlug::setInput( PlugPtr input )
{
	if( !input )
	{
		for( ChildContainer::const_iterator it = children().begin(); it!=children().end(); it++ )
		{
			IECore::staticPointerCast<Plug>( *it )->setInput( 0 );			
		}
	}
	else
	{
		CompoundPlugPtr p = IECore::staticPointerCast<CompoundPlug>( input );
		ChildContainer::const_iterator it1, it2;
		for( it1 = children().begin(), it2 = p->children().begin(); it1!=children().end(); it1++, it2++ )
		{
			IECore::staticPointerCast<Plug>( *it1 )->setInput( IECore::staticPointerCast<Plug>( *it2 ) );
		}
	}
	ValuePlug::setInput( input );
}

void CompoundPlug::setFrom( const ValuePlug *other )
{
	/// \todo Probably need to propagate the call to children, but not sure yet.
}

void CompoundPlug::parentChanged()
{
	m_plugInputChangedConnection.disconnect();
	m_plugSetConnection.disconnect();
	
	Node *n = node();
	if( n )
	{
		m_plugInputChangedConnection = n->plugInputChangedSignal().connect( boost::bind( &CompoundPlug::plugInputChanged, this, ::_1 ) );
		m_plugSetConnection = n->plugSetSignal().connect( boost::bind( &CompoundPlug::plugSet, this, ::_1 ) );
	}
}

void CompoundPlug::childAddedOrRemoved()
{
	updateInputFromChildInputs( 0 );
	// addition or removal of a child to a compound is considered to
	// change its value, so we emit the appropriate signal. this is
	// mostly of use for the SplinePlug, as points are added by adding
	// plugs and removed by removing them.
	Node *n = node();
	if( n )
	{
		n->plugSetSignal()( this );
	}
}

void CompoundPlug::plugInputChanged( PlugPtr plug )
{
	if( plug->parent<CompoundPlug>()==this )
	{
		updateInputFromChildInputs( plug );
	}
}

void CompoundPlug::plugSet( PlugPtr plug )
{
	// the CompoundPlug immediately below the Node takes on the task
	// of emitting the plugSet signals for all CompoundPlugs between
	// the plug and the Node.
	Node *n = node();
	if( !n )
	{
		return;
	}
	if( this->isAncestorOf( plug ) )
	{
		PlugPtr p = plug;
		m_plugSetConnection.block();
			do {
				p = p->parent<Plug>();
				n->plugSetSignal()( p );
			} while( p!=this );
		m_plugSetConnection.unblock();
	}
}

void CompoundPlug::updateInputFromChildInputs( PlugPtr checkFirst )
{
	if( !children().size() )
	{
		return;
	}

	if( !checkFirst )
	{
		checkFirst = IECore::staticPointerCast<Plug>( *( children().begin() ) );
	}

	PlugPtr input = checkFirst->getInput<Plug>();	
	if( !input || !input->ancestor<CompoundPlug>() )
	{
		// calling ValuePlug::setInput explicitly rather than setInput
		// so that we don't invoke the behaviour of changing the child
		// plugs' inputs too.
		ValuePlug::setInput( 0 );
		return;
	}
	
	CompoundPlugPtr commonParent = input->ancestor<CompoundPlug>();

	ChildContainer::const_iterator it;
	for( it = children().begin(); it!=children().end(); it++ )
	{
		input = IECore::staticPointerCast<Plug>(*it)->getInput<Plug>();
		if( !input || input->ancestor<CompoundPlug>()!=commonParent )
		{
			ValuePlug::setInput( 0 );
			return;
		}
	}

	ValuePlug::setInput( commonParent );
}
