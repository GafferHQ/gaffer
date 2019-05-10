//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/GraphComponent.h"

#include "Gaffer/Action.h"
#include "Gaffer/DirtyPropagationScope.h"

#include "IECore/Exception.h"
#include "IECore/StringAlgo.h"

#include "boost/bind.hpp"
#include "boost/format.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/regex.hpp"

#include <set>

using namespace Gaffer;
using namespace IECore;
using namespace std;

//////////////////////////////////////////////////////////////////////////
// GraphComponent::Signals
//
// We allocate these separately because they have a significant overhead
// in both memory and construction time, and for many GraphComponent
// instances they are never actually used.
//////////////////////////////////////////////////////////////////////////

struct GraphComponent::Signals : boost::noncopyable
{

	UnarySignal nameChangedSignal;
	BinarySignal childAddedSignal;
	BinarySignal childRemovedSignal;
	BinarySignal parentChangedSignal;

	// Utility to emit a signal if it has been created, but do nothing
	// if it hasn't.
	template<typename SignalMemberPointer, typename... Args>
	static void emitLazily( Signals *signals, SignalMemberPointer signalMemberPointer, Args&&... args )
	{
		if( !signals )
		{
			return;
		}
		auto &signal = signals->*signalMemberPointer;
		signal( std::forward<Args>( args )... );
	}

};

//////////////////////////////////////////////////////////////////////////
// GraphComponent
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( GraphComponent );

GraphComponent::GraphComponent( const std::string &name )
	: m_name( name ), m_parent( nullptr )
{
}

GraphComponent::~GraphComponent()
{
	DirtyPropagationScope dirtyPropagationScope;

	// notify all the children that the parent is gone.
	// we don't call removeChild to achieve this, as that would also emit
	// childRemoved signals for this object, which is undesirable as it's dying.
	for( ChildContainer::iterator it=m_children.begin(); it!=m_children.end(); it++ )
	{
		(*it)->m_parent = nullptr;
		(*it)->parentChanging( nullptr );
		(*it)->parentChanged( nullptr );
		Signals::emitLazily( (*it)->m_signals.get(), &Signals::parentChangedSignal, (*it).get(), nullptr );
	}
}

const IECore::InternedString &GraphComponent::setName( const IECore::InternedString &name )
{
	// make sure the name is valid
	static boost::regex validator( "^[A-Za-z_]+[A-Za-z_0-9]*" );
	if( !regex_match( name.c_str(), validator ) )
	{
		std::string what = boost::str( boost::format( "Invalid name \"%s\"" ) % name.string() );
		throw IECore::Exception( what );
	}

	// make sure the name is unique
	IECore::InternedString newName = name;
	if( m_parent )
	{
		bool uniqueAlready = true;
		for( ChildContainer::const_iterator it=m_parent->m_children.begin(), eIt=m_parent->m_children.end(); it != eIt; it++ )
		{
			if( *it != this && (*it)->m_name == newName )
			{
				uniqueAlready = false;
				break;
			}
		}

		if( !uniqueAlready )
		{
			// split name into a prefix and a numeric suffix. if no suffix
			// exists then it defaults to 1.
			std::string prefix;
			int suffix = StringAlgo::numericSuffix( newName.value(), 1, &prefix );

			// iterate over all the siblings to find the minimum value for the suffix which
			// will be greater than any existing suffix.
			for( ChildContainer::const_iterator it=m_parent->m_children.begin(), eIt=m_parent->m_children.end(); it != eIt; it++ )
			{
				if( *it == this )
				{
					continue;
				}
				if( (*it)->m_name.value().compare( 0, prefix.size(), prefix ) == 0 )
				{
					char *endPtr = nullptr;
					long siblingSuffix = strtol( (*it)->m_name.value().c_str() + prefix.size(), &endPtr, 10 );
					if( *endPtr == '\0' )
					{
						suffix = max( suffix, (int)siblingSuffix + 1 );
					}
				}
			}
			newName = prefix + std::to_string( suffix );
		}
	}

	// set the new name if it's different to the old
	if( newName==m_name )
	{
		return m_name;
	}

	Action::enact(
		this,
		// ok to bind raw pointers to this, because enact() guarantees
		// the lifetime of the subject.
		boost::bind( &GraphComponent::setNameInternal, this, newName ),
		boost::bind( &GraphComponent::setNameInternal, this, m_name )
	);

	return m_name;
}

void GraphComponent::setNameInternal( const IECore::InternedString &name )
{
	m_name = name;
	Signals::emitLazily( m_signals.get(), &Signals::nameChangedSignal, this );
}

const IECore::InternedString &GraphComponent::getName() const
{
	return m_name;
}

std::string GraphComponent::fullName() const
{
	return relativeName( nullptr );
}

std::string GraphComponent::relativeName( const GraphComponent *ancestor ) const
{
	string fullName = m_name;
	GraphComponent *c = this->m_parent;
	while( c && c!=ancestor )
	{
		fullName = c->m_name.value() + "." + fullName;
		c = c->m_parent;
	}
	if( ancestor && c!=ancestor )
	{
		string what = boost::str( boost::format( "Object \"%s\" is not an ancestor of \"%s\"." ) % ancestor->m_name.value() % m_name.value() );
		throw Exception( what );
	}
	return fullName;
}

GraphComponent::UnarySignal &GraphComponent::nameChangedSignal()
{
	return signals()->nameChangedSignal;
}

bool GraphComponent::acceptsChild( const GraphComponent *potentialChild ) const
{
	return true;
}

bool GraphComponent::acceptsParent( const GraphComponent *potentialParent ) const
{
	return true;
}

void GraphComponent::addChild( GraphComponentPtr child )
{
	if( child->m_parent==this )
	{
		return;
	}

	throwIfChildRejected( child.get() );

	if( refCount() )
	{
		// someone is pointing to us, so we may have a ScriptNode ancestor and we should do things
		// in an undoable way. figure out what our undo function should be - it varies based on what
		// the previous parent was.
		Action::Function undoFn;
		if( child->m_parent )
		{
			if( child->m_parent->isInstanceOf( (IECore::TypeId)ScriptNodeTypeId ) )
			{
				// use raw pointer to avoid circular reference between script and undo queue
				undoFn = boost::bind( &GraphComponent::addChildInternal, child->m_parent, child, child->index() );
			}
			else
			{
				// use smart pointer to ensure parent remains alive, even if something unscrupulous
				// messes it with non-undoable actions that aren't stored in the undo queue.
				undoFn = boost::bind( &GraphComponent::addChildInternal, GraphComponentPtr( child->m_parent ), child, child->index() );
			}
		}
		else
		{
			// no previous parent.
			undoFn = boost::bind( &GraphComponent::removeChildInternal, this, child, true );
		}

		Action::enact(
			this,
			// ok to use raw pointer for this - lifetime of subject guaranteed.
			boost::bind( &GraphComponent::addChildInternal, this, child, m_children.size() ),
			undoFn
		);
	}
	else
	{
		// we have no references to us - chances are we're in construction still. adding ourselves to an
		// undo queue is impossible, and creating temporary smart pointers to ourselves (as above) will
		// cause our destruction before construction completes. just do the work directly.
		addChildInternal( child, m_children.size() );
	}
}

void GraphComponent::setChild( const IECore::InternedString &name, GraphComponentPtr child )
{
	GraphComponentPtr existingChild = getChild( name );
	if( existingChild && existingChild == child )
	{
		return;
	}

	throwIfChildRejected( child.get() );

	if( existingChild )
	{
		removeChild( existingChild );
	}

	child->setName( name );
	addChild( child );
}

void GraphComponent::throwIfChildRejected( const GraphComponent *potentialChild ) const
{
	if( potentialChild == this )
	{
		string what = boost::str( boost::format( "Child \"%s\" cannot be parented to itself." ) % m_name.value() );
		throw Exception( what );
	}

	if( potentialChild->isAncestorOf( this ) )
	{
		string what = boost::str( boost::format( "Child \"%s\" cannot be parented to parent \"%s\" as it is an ancestor of \"%s\"." ) % potentialChild->m_name.value() % m_name.value() % m_name.value() );
		throw Exception( what );
	}

	if( !acceptsChild( potentialChild ) )
	{
		string what = boost::str( boost::format( "Parent \"%s\" ( of type %s ) rejects child \"%s\" ( of type %s )." ) % m_name.value() % typeName() % potentialChild->m_name.value() % potentialChild->typeName() );
		throw Exception( what );
	}

	if( !potentialChild->acceptsParent( this ) )
	{
		string what = boost::str( boost::format( "Child \"%s\" rejects parent \"%s\"." ) % potentialChild->m_name.value() % m_name.value() );
		throw Exception( what );
	}
}

void GraphComponent::addChildInternal( GraphComponentPtr child, size_t index )
{
	child->parentChanging( this );
	GraphComponent *previousParent = child->m_parent;
	if( previousParent )
	{
		// remove the child from the previous parent, but don't emit parentChangedSignal.
		// this prevents a parent changed signal with new parent null followed by a parent
		// changed signal with the new parent.
		previousParent->removeChildInternal( child, false );
	}

	m_children.insert( m_children.begin() + min( index, m_children.size() ), child );
	child->m_parent = this;
	child->setName( child->m_name.value() ); // to force uniqueness
	Signals::emitLazily( m_signals.get(), &Signals::childAddedSignal, this, child.get() );
	child->parentChanged( previousParent );
	Signals::emitLazily( child->m_signals.get(), &Signals::parentChangedSignal, child.get(), previousParent );
}

void GraphComponent::removeChild( GraphComponentPtr child )
{
	if( child->m_parent!=this )
	{
		throw Exception( "Object is not a child." );
	}

	if( refCount() )
	{
		// someone is pointing to us, so we may have a ScriptNode ancestor and we should do things
		// in an undoable way.
		Action::enact(
			this,
			// ok to bind raw pointers to this, because enact() guarantees
			// the lifetime of the subject.
			boost::bind( &GraphComponent::removeChildInternal, this, child, true ),
			boost::bind( &GraphComponent::addChildInternal, this, child, child->index() )
		);
	}
	else
	{
		// we have no references to us - chances are we're in construction still. adding ourselves to an
		// undo queue is impossible, and creating temporary smart pointers to ourselves (as above) will
		// cause our destruction before construction completes. just do the work directly.
		removeChildInternal( child, true );
	}
}

void GraphComponent::clearChildren()
{
	// because our storage is a vector, it's a good bit quicker to remove
	// from the back to the front.
	for( int i = (int)(m_children.size()) - 1; i >= 0; --i )
	{
		removeChild( m_children[i] );
	}
}

void GraphComponent::removeChildInternal( GraphComponentPtr child, bool emitParentChanged )
{
	if( emitParentChanged )
	{
		child->parentChanging( nullptr );
	}
	ChildContainer::iterator it = std::find( m_children.begin(), m_children.end(), child );
	if( it == m_children.end() || child->m_parent != this )
	{
		// the public removeChild() method protects against this case, but it's still possible to
		// arrive here if an Action (which has a direct binding to removeChildInternal) is being replayed
		// from the undo queue, and just prior to that something called the public removeChild() method.
		// this can occur if a slot calls removeChild() from a signal triggered during the replay of the
		// undo queue. the onus is on such slots to not reperform their work when ScriptNode::currentActionStage()
		// is Action::Redo - instead they should rely on the fact that their actions will have been
		// recorded and replayed automatically.
		throw Exception( boost::str( boost::format( "GraphComponent::removeChildInternal : \"%s\" is not a child of \"%s\"." ) % child->fullName() % fullName() ) );
	}
	m_children.erase( it );
	child->m_parent = nullptr;
	Signals::emitLazily( m_signals.get(), &Signals::childRemovedSignal, this, child.get() );
	if( emitParentChanged )
	{
		child->parentChanged( this );
		Signals::emitLazily( child->m_signals.get(), &Signals::parentChangedSignal, child.get(), this );
	}
}

size_t GraphComponent::index() const
{
	assert( m_parent );
	const ChildContainer &c = m_parent->m_children;
	return std::find( c.begin(), c.end(), this ) - c.begin();
}

const GraphComponent::ChildContainer &GraphComponent::children() const
{
	return m_children;
}

GraphComponent *GraphComponent::ancestor( IECore::TypeId type )
{
	GraphComponent *a = m_parent;
	while( a )
	{
		if( a->isInstanceOf( type ) )
		{
			return a;
		}
		a = a->m_parent;
	}
	return nullptr;
}

const GraphComponent *GraphComponent::ancestor( IECore::TypeId type ) const
{
	return const_cast<GraphComponent *>( this )->ancestor( type );
}

GraphComponent *GraphComponent::commonAncestor( const GraphComponent *other, IECore::TypeId ancestorType )
{
	set<GraphComponent *> candidates;
	GraphComponent *ancestor = m_parent;
	while( ancestor )
	{
		if( ancestor->isInstanceOf( ancestorType ) )
		{
			candidates.insert( ancestor );
		}
		ancestor = ancestor->m_parent;
	}

	ancestor = other->m_parent;
	while( ancestor )
	{
		if( ancestor->isInstanceOf( ancestorType ) )
		{
			if( candidates.find( ancestor )!=candidates.end() )
			{
				return ancestor;
			}
		}
		ancestor = ancestor->m_parent;
	}
	return nullptr;

}

const GraphComponent *GraphComponent::commonAncestor( const GraphComponent *other, IECore::TypeId ancestorType ) const
{
	return const_cast<GraphComponent *>( this )->commonAncestor( other, ancestorType );
}

bool GraphComponent::isAncestorOf( const GraphComponent *other ) const
{
	const GraphComponent *p = other;
	while( p )
	{
		if( p->m_parent==this )
		{
			return true;
		}
		p = p->m_parent;
	}
	return false;
}

GraphComponent::BinarySignal &GraphComponent::childAddedSignal()
{
	return signals()->childAddedSignal;
}

GraphComponent::BinarySignal &GraphComponent::childRemovedSignal()
{
	return signals()->childRemovedSignal;
}

GraphComponent::BinarySignal &GraphComponent::parentChangedSignal()
{
	return signals()->parentChangedSignal;
}

void GraphComponent::parentChanging( Gaffer::GraphComponent *newParent )
{
}

void GraphComponent::parentChanged( Gaffer::GraphComponent *oldParent )
{
}

void GraphComponent::storeIndexOfNextChild( size_t &index ) const
{
	if( index )
	{
		if( index != m_children.size() )
		{
			throw Exception( "Inconsistent child offset" );
		}
	}
	else
	{
		index = m_children.size();
	}
}

std::string GraphComponent::unprefixedTypeName( const char *typeName )
{
	string result( typeName );
	string::size_type colonPos = result.find_last_of( ':' );
	if( colonPos != string::npos )
	{
		result.erase( 0, colonPos + 1 );
	}
	return result;
}

GraphComponent::Signals *GraphComponent::signals()
{
	if( !m_signals )
	{
		m_signals.reset( new Signals );
	}
	return m_signals.get();
}
