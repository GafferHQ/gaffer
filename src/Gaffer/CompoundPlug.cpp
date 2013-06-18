//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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
#include "boost/format.hpp"

#include "IECore/MurmurHash.h"

#include "Gaffer/CompoundPlug.h"
#include "Gaffer/Node.h"
#include "Gaffer/BlockedConnection.h"

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

bool CompoundPlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	ConstPlugPtr p = IECore::runTimeCast<const Plug>( potentialChild );
	if( !p )
	{
		return false;
	}
	return p->direction()==direction();
}

bool CompoundPlug::acceptsInput( const Plug *input ) const
{
	if( !ValuePlug::acceptsInput( input ) )
	{
		return false;
	}
	if( input )
	{
		const CompoundPlug *p = IECore::runTimeCast<const CompoundPlug>( input );
		if( !p )
		{
			return false;
		}
		if( children().size() > p->children().size() )
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
	if( input.get() == getInput<Plug>() )
	{
		return;
	}
	
	// unfortunately we have to duplicate the check in Plug::setInput()
	// ourselves as we delay calling Plug::setInput() until we've connected
	// the children, but need to do the check first.
	/// \todo I think there's a case for not having CompoundPlug at all,
	/// and having Plug have all its functionality.
	if( input && !acceptsInput( input ) )
	{
		std::string what = boost::str(
			boost::format( "Plug \"%s\" rejects input \"%s\"." )
			% fullName()
			% input->fullName()
		);
		throw IECore::Exception( what );
	}
	
	{
		// we use the plugInputChangedConnection to trigger calls to updateInputFromChildInputs()
		// when child inputs are changed by code elsewhere. it would be counterproductive for
		// us to call updateInputFromChildInputs() while we ourselves are changing those inputs,
		// so we temporarily block the connection.
		BlockedConnection block( m_plugInputChangedConnection );
	
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
	}
	
	// we connect ourselves last, so that all our child plugs are correctly connected
	// before we signal our own connection change.
	ValuePlug::setInput( input );
}

PlugPtr CompoundPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	CompoundPlugPtr result = new CompoundPlug( name, direction, getFlags() );
	for( PlugIterator it( this ); it != it.end(); it++ )
	{
		result->addChild( (*it)->createCounterpart( (*it)->getName(), direction ) );
	}
	return result;
}

bool CompoundPlug::settable() const
{
	ChildContainer::const_iterator it, eIt;
	for( it=children().begin(), eIt=children().end(); it!=eIt; ++it )
	{
		ValuePlug *valuePlug = IECore::runTimeCast<ValuePlug>( it->get() );
		if( !valuePlug || !valuePlug->settable() )
		{
			return false;
		}
	}
	return true;
}

void CompoundPlug::setToDefault()
{
	ChildContainer::const_iterator it;
	for( it=children().begin(); it!=children().end(); it++ )
	{
		ValuePlug *valuePlug = IECore::runTimeCast<ValuePlug>( it->get() );
		if( valuePlug )
		{
			valuePlug->setToDefault();
		}
	}
}

void CompoundPlug::setFrom( const ValuePlug *other )
{
	const CompoundPlug *typedOther = IECore::runTimeCast<const CompoundPlug>( other );
	if( !typedOther )
	{
		throw IECore::Exception( "Unsupported plug type" );
	}

	ChildContainer::const_iterator it, otherIt;
	for( it = children().begin(), otherIt = typedOther->children().begin(); it!=children().end() && otherIt!=typedOther->children().end(); it++, otherIt++ )
	{
		ValuePlug *child = IECore::runTimeCast<ValuePlug>( it->get() );
		const ValuePlug *otherChild = IECore::runTimeCast<ValuePlug>( otherIt->get() );
		if( !child || !otherChild )
		{
			throw IECore::Exception( "Children are not ValuePlugs" );
		}
		child->setFrom( otherChild );
	}
}

IECore::MurmurHash CompoundPlug::hash() const
{
	IECore::MurmurHash h;
	for( ValuePlugIterator it( this ); it!=it.end(); it++ )
	{
		/// \todo Do we need to hash the child names too?
		(*it)->hash( h );
	}
	return h;
}

void CompoundPlug::hash( IECore::MurmurHash &h ) const
{
	ValuePlug::hash( h );
}

void CompoundPlug::parentChanged()
{
	m_plugInputChangedConnection.disconnect();
	
	Node *n = node();
	if( n )
	{
		m_plugInputChangedConnection = n->plugInputChangedSignal().connect( boost::bind( &CompoundPlug::plugInputChanged, this, ::_1 ) );
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

void CompoundPlug::plugInputChanged( Plug *plug )
{
	if( plug->parent<CompoundPlug>()==this )
	{
		updateInputFromChildInputs( plug );
	}
}

void CompoundPlug::updateInputFromChildInputs( Plug *checkFirst )
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
	if( !acceptsInput( commonParent ) )
	{
		// if we're never going to accept the candidate input anyway, then
		// don't even bother checking to see if all the candidate's children
		// are connected to our children.
		ValuePlug::setInput( 0 );
		return;
	}

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
