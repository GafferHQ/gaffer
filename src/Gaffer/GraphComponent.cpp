//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

#include "IECore/Exception.h"

#include "boost/format.hpp"
#include "boost/bind.hpp"
#include "boost/regex.hpp"
#include "boost/lexical_cast.hpp"

#include <set>

using namespace Gaffer;
using namespace IECore;
using namespace std;

IE_CORE_DEFINERUNTIMETYPED( GraphComponent );

GraphComponent::GraphComponent( const std::string &name )
	: m_name( name ), m_parent( 0 )
{
}

GraphComponent::~GraphComponent()
{
	// notify all the children that the parent is gone.
	// we don't call removeChild to achieve this, as that would also emit
	// childRemoved signals for this object, which is undesirable as it's dying.
	for( ChildContainer::iterator it=m_children.begin(); it!=m_children.end(); it++ )
	{
		(*it)->m_parent = 0;
		(*it)->parentChanging( 0 );
		(*it)->parentChangedSignal()( (*it).get(), 0 );
	}	
}

bool GraphComponent::nameExists( const IECore::InternedString &name )
{
	for( ChildContainer::const_iterator it=m_parent->m_children.begin(); it!=m_parent->m_children.end(); it++ )
	{
		if( it->get()!=this && (*it)->m_name==name )
		{
			return true;
		}
	}
	return false;
}

const std::string &GraphComponent::setName( const std::string &name )
{
	// make sure the name is valid
	static boost::regex validator( "^[A-Za-z_]+[A-Za-z_0-9]*" );
	if( !regex_match( name.c_str(), validator ) )
	{
		std::string what = boost::str( boost::format( "Invalid name \"%s\"" ) % name );
		throw IECore::Exception( what );
	}
	
	// make sure the name is unique
	IECore::InternedString newName = name;
	if( m_parent )
	{
		if( nameExists( newName ) )
		{
			std::string prefix = newName.value();
			int suffix = 1;
			
			static boost::regex reg( "^(.*[^0-9]+)([0-9]+)$" );
			boost::cmatch match;
			if( regex_match( newName.value().c_str(), match, reg ) )
			{
				prefix = match[1];
				suffix = boost::lexical_cast<int>( match[2] );
			}
			
			do
			{
				static boost::format formatter( "%s%d" );
				newName = boost::str( formatter % prefix % suffix );
				suffix++;
			} while( nameExists( newName ) );	
		}
	}
	
	// set the new name if it's different to the old
	if( newName==m_name.value() )
	{
		return m_name.value();
	}
	
	Action::enact(
		this,
		boost::bind( &GraphComponent::setNameInternal, GraphComponentPtr( this ), newName ),
		boost::bind( &GraphComponent::setNameInternal, GraphComponentPtr( this ), m_name )		
	);
	
	return m_name.value();
}

void GraphComponent::setNameInternal( const IECore::InternedString &name )
{
	m_name = name;
	nameChangedSignal()( this );
}

const std::string &GraphComponent::getName() const
{
	return m_name.value();
}

std::string GraphComponent::fullName() const
{
	return relativeName( 0 );
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
	return m_nameChangedSignal;
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
	if( !acceptsChild( child ) )
	{
		string what = boost::str( boost::format( "Parent \"%s\" rejects child \"%s\"." ) % m_name.value() % child->m_name.value() );
		throw Exception( what );
	}
	if( !child->acceptsParent( this ) )
	{
		string what = boost::str( boost::format( "Child \"%s\" rejects parent \"%s\"." ) % child->m_name.value() % m_name.value() );
		throw Exception( what );
	}

	if( refCount() )
	{
		// someone is pointing to us, so we may have a ScriptNode ancestor and we should do things
		// in an undoable way.
		if( child->m_parent )
		{
			Action::enact(
				this,
				boost::bind( &GraphComponent::addChildInternal, GraphComponentPtr( this ), child ),
				boost::bind( &GraphComponent::addChildInternal, GraphComponentPtr( child->m_parent ), child )		
			);
		}
		else
		{
			Action::enact(
				this,
				boost::bind( &GraphComponent::addChildInternal, GraphComponentPtr( this ), child ),
				boost::bind( &GraphComponent::removeChildInternal, GraphComponentPtr( this ), child, true )	
			);
		}
	}
	else
	{
		// we have no references to us - chances are we're in construction still. adding ourselves to an
		// undo queue is impossible, and creating temporary smart pointers to ourselves (as above) will
		// cause our destruction before construction completes. just do the work directly.
		addChildInternal( child );
	}
}

void GraphComponent::setChild( const std::string &name, GraphComponentPtr child )
{
	GraphComponentPtr existingChild = getChild<GraphComponent>( name );
	if( existingChild )
	{
		if( existingChild == child )
		{
			return;
		}
		removeChild( existingChild );
	}
	
	child->setName( name );
	addChild( child );
}

void GraphComponent::addChildInternal( GraphComponentPtr child )
{
	GraphComponent *previousParent = child->m_parent;
	if( previousParent )
	{
		// remove the child from the previous parent, but don't emit parentChangedSignal.
		// this prevents a parent changed signal with new parent 0 followed by a parent
		// changed signal with the new parent.
		previousParent->removeChildInternal( child, false );
	}
	child->parentChanging( this );
	m_children.push_back( child );
	child->m_parent = this;
	child->setName( child->m_name.value() ); // to force uniqueness
	childAddedSignal()( this, child.get() );
	child->parentChangedSignal()( child.get(), previousParent );
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
			boost::bind( &GraphComponent::removeChildInternal, GraphComponentPtr( this ), child, true ),
			boost::bind( &GraphComponent::addChildInternal, GraphComponentPtr( this ), child )		
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

void GraphComponent::removeChildInternal( GraphComponentPtr child, bool emitParentChanged )
{
	if( emitParentChanged )
	{
		child->parentChanging( 0 );
	}
	m_children.remove( child );
	child->m_parent = 0;
	childRemovedSignal()( this, child.get() );
	if( emitParentChanged )
	{	
		child->parentChangedSignal()( child.get(), this );
	}
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
	return 0;
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
	return 0;

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
	return m_childAddedSignal;
}

GraphComponent::BinarySignal &GraphComponent::childRemovedSignal()
{
	return m_childRemovedSignal;
}

GraphComponent::BinarySignal &GraphComponent::parentChangedSignal()
{
	return m_parentChangedSignal;
}

void GraphComponent::parentChanging( Gaffer::GraphComponent *newParent )
{
}
