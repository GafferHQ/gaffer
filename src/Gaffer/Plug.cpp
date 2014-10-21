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

#include "Gaffer/Plug.h"
#include "Gaffer/DependencyNode.h"
#include "Gaffer/Action.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Metadata.h"

#include "IECore/Exception.h"

#include "boost/format.hpp"
#include "boost/bind.hpp"

using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( Plug );

Plug::Plug( const std::string &name, Direction direction, unsigned flags )
	:	GraphComponent( name ), m_direction( direction ), m_input( 0 ), m_flags( None )
{
	setFlags( flags );
}

Plug::~Plug()
{
	setInputInternal( 0, false );
	for( OutputContainer::iterator it=m_outputs.begin(); it!=m_outputs.end(); )
	{
	 	// get the next iterator now, as the call to setInputInternal invalidates
		// the current iterator.
		OutputContainer::iterator next = it; next++;
		(*it)->setInputInternal( 0, true );
		it = next;
	}
	Metadata::clearInstanceMetadata( this );
}

bool Plug::acceptsChild( const GraphComponent *potentialChild ) const
{
	if( !GraphComponent::acceptsChild( potentialChild ) )
	{
		return false;
	}
	const Plug *p = IECore::runTimeCast<const Plug>( potentialChild );
	if( !p )
	{
		return false;
	}
	return p->direction()==direction();
}

bool Plug::acceptsParent( const GraphComponent *potentialParent ) const
{
	if( !GraphComponent::acceptsParent( potentialParent ) )
	{
		return false;
	}
	return potentialParent->isInstanceOf( (IECore::TypeId)NodeTypeId ) || potentialParent->isInstanceOf( Plug::staticTypeId() );
}

Node *Plug::node()
{
	return ancestor<Node>();
}

const Node *Plug::node() const
{
	return ancestor<Node>();
}

Plug::Direction Plug::direction() const
{
	return m_direction;
}

unsigned Plug::getFlags() const
{
	return m_flags;
}

bool Plug::getFlags( unsigned flags ) const
{
	return (m_flags & flags) == flags;
}

void Plug::setFlags( unsigned flags )
{
	if( flags == m_flags )
	{
		return;
	}

	if( (flags & ReadOnly) && direction() == Out )
	{
		throw IECore::Exception( "Output plug cannot be read only" );
	}

	m_flags = flags;

	if( Node *n = node() )
	{
		n->plugFlagsChangedSignal()( this );
	}
}

void Plug::setFlags( unsigned flags, bool enable )
{
	setFlags( (m_flags & ~flags) | ( enable ? flags : 0 ) );
}

bool Plug::acceptsInput( const Plug *input ) const
{
	if( !getFlags( AcceptsInputs ) || getFlags( ReadOnly ) )
	{
		return false;
	}

	if( input == this )
	{
		return false;
	}

	if( const Node *n = node() )
	{
		if( !n->acceptsInput( this, input ) )
		{
			return false;
		}
	}

	for( OutputContainer::const_iterator it=m_outputs.begin(), eIt=m_outputs.end(); it!=eIt; ++it )
	{
		if( !(*it)->acceptsInput( input ) )
		{
			return false;
		}
	}

	if( input )
	{
		if( children().size() > input->children().size() )
		{
			return false;
		}
		for( PlugIterator it1( this ), it2( input ); it1!=it1.end(); ++it1, ++it2 )
		{
			if( !( *it1 )->acceptsInput( it2->get() ) )
			{
				return false;
			}
		}
	}

	return true;
}

void Plug::setInput( PlugPtr input )
{
	setInput( input, /* setChildInputs = */ true, /* updateParentInput = */ true );
}

void Plug::setInput( PlugPtr input, bool setChildInputs, bool updateParentInput )
{
	if( input.get()==m_input )
	{
		return;
	}

	if( input && !acceptsInput( input.get() ) )
	{
		std::string what = boost::str(
			boost::format( "Plug \"%s\" rejects input \"%s\"." )
			% fullName()
			% input->fullName()
		);
		throw IECore::Exception( what );
	}

	// connect our children first

	if( setChildInputs )
	{
		if( !input )
		{
			for( PlugIterator it( this ); it!=it.end(); ++it )
			{
				(*it)->setInput( NULL, /* setChildInputs = */ true, /* updateParentInput = */ false );
			}
		}
		else
		{
			for( PlugIterator it1( this ), it2( input.get() ); it1!=it1.end(); ++it1, ++it2 )
			{
				(*it1)->setInput( *it2, /* setChildInputs = */ true, /* updateParentInput = */ false );
			}
		}
	}

	// then connect ourselves

	if( refCount() )
	{
		// someone is referring to us, so we're definitely fully constructed and we may have a ScriptNode
		// above us, so we should do things in a way compatible with the undo system.
		Action::enact(
			this,
			boost::bind( &Plug::setInputInternal, PlugPtr( this ), input, true ),
			boost::bind( &Plug::setInputInternal, PlugPtr( this ), PlugPtr( m_input ), true )
		);
	}
	else
	{
		// noone is referring to us. we're probably still constructing, and undo is impossible anyway (we
		// have no ScriptNode ancestor), so we can't make a smart pointer
		// to ourselves (it will result in double destruction). so we just set the input directly.
		setInputInternal( input, false );
	}

	// finally, adjust our parent's connection to take account of
	// the changes to its child.

	if( updateParentInput )
	{
		if( Plug *parentPlug = parent<Plug>() )
		{
			parentPlug->updateInputFromChildInputs( this );
		}
	}

}

void Plug::setInputInternal( PlugPtr input, bool emit )
{
	if( m_input )
	{
		m_input->m_outputs.remove( this );
	}
	m_input = input.get();
	if( m_input )
	{
		m_input->m_outputs.push_back( this );
	}
	if( emit )
	{
		Node *n = node();
		if( n )
		{
			n->plugInputChangedSignal()( this );
		}
		DependencyNode::propagateDirtiness( this );
	}
}

void Plug::updateInputFromChildInputs( Plug *checkFirst )
{
	if( !children().size() )
	{
		return;
	}

	if( !checkFirst )
	{
		checkFirst = static_cast<Plug *>( children().front().get() );
	}

	Plug *input = checkFirst->getInput<Plug>();
	if( !input || !input->parent<Plug>() )
	{
		setInput( NULL, /* setChildInputs = */ false, /* updateParentInput = */ true );
		return;
	}

	Plug *commonParent = input->parent<Plug>();
	if( !acceptsInput( commonParent ) )
	{
		// if we're never going to accept the candidate input anyway, then
		// don't even bother checking to see if all the candidate's children
		// are connected to our children.
		setInput( NULL, /* setChildInputs = */ false, /* updateParentInput = */ true );
		return;
	}

	for( PlugIterator it( this ); it!=it.end(); ++it )
	{
		input = (*it)->getInput<Plug>();
		if( !input || input->parent<Plug>()!=commonParent )
		{
			setInput( NULL, /* setChildInputs = */ false, /* updateParentInput = */ true );
			return;
		}
	}

	setInput( commonParent, /* setChildInputs = */ false, /* updateParentInput = */ true );
}

void Plug::removeOutputs()
{
	for( OutputContainer::iterator it = m_outputs.begin(); it!=m_outputs.end();  )
	{
		Plug *p = *it++;
		p->setInput( 0 );
	}
}

const Plug::OutputContainer &Plug::outputs() const
{
	return m_outputs;
}

PlugPtr Plug::createCounterpart( const std::string &name, Direction direction ) const
{
	PlugPtr result = new Plug( name, direction, getFlags() );
	for( PlugIterator it( this ); it != it.end(); ++it )
	{
		result->addChild( (*it)->createCounterpart( (*it)->getName(), direction ) );
	}
	return result;
}

void Plug::parentChanging( Gaffer::GraphComponent *newParent )
{
	if( !newParent )
	{
		// we're losing our parent - remove all our connections first.
		// this must be done here (rather than in a parentChangedSignal() slot)
		// because we need a current parent for the operation to be undoable.
		setInput( 0 );
		removeOutputs();
	}
	else if( Plug *newParentPlug = IECore::runTimeCast<Plug>( newParent ) )
	{
		// we're getting a new parent - update its input connection from
		// all the children including the pending one.
		newParentPlug->updateInputFromChildInputs( this );
	}

}

