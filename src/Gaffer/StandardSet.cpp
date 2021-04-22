//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#include "Gaffer/StandardSet.h"

#include "IECore/Exception.h"

using namespace Gaffer;

StandardSet::StandardSet( bool removeOrphans )
	:	m_removeOrphans( removeOrphans )
{
}

StandardSet::~StandardSet()
{
}

StandardSet::MemberAcceptanceSignal &StandardSet::memberAcceptanceSignal()
{
	return m_memberAcceptanceSignal;
}

bool StandardSet::add( MemberPtr member )
{
	if( !m_memberAcceptanceSignal( this, member.get() ) )
	{
		throw IECore::Exception( "Member is not eligible for inclusion in StandardSet." );
	}

	bool result = m_members.insert( member ).second;
	if( result )
	{
		if( m_removeOrphans )
		{
			if( GraphComponent *graphComponent = IECore::runTimeCast<GraphComponent>( member.get() ) )
			{
				graphComponent->parentChangedSignal().connect( boost::bind( &StandardSet::parentChanged, this, ::_1 ) );
			}
		}
		memberAddedSignal()( this, member.get() );
	}
	return result;
}

size_t StandardSet::add( const Set *other )
{
	size_t result = 0;
	for( size_t i = 0, e = other->size(); i < e; i++ )
	{
		result += add( const_cast<Member *>( other->member( i ) ) );
	}
	return result;
}

bool StandardSet::remove( Member *member )
{
	MemberContainer::iterator it = m_members.find( member );
	if( it != m_members.end() )
	{
		if( m_removeOrphans )
		{
			if( GraphComponent *graphComponent = IECore::runTimeCast<GraphComponent>( member ) )
			{
				graphComponent->parentChangedSignal().disconnect( boost::bind( &StandardSet::parentChanged, this, ::_1 ) );
			}
		}
		// we may be the only owner of member, in which
		// case it would die immediately upon removal
		// from m_members. so we have to make a temporary
		// reference to keep it alive long enough to emit
		// the memberRemovedSignal() - slots on the signal
		// can then take ownership if they wish.
		MemberPtr lifePreserver = member;
		m_members.erase( it );
		memberRemovedSignal()( this, member );
		return true;
	}

	return false;
}

size_t StandardSet::remove( const Set *other )
{
	size_t result = 0;
	for( size_t i = 0, e = other->size(); i < e; i++ )
	{
		result += remove( const_cast<Member *>( other->member( i ) ) );
	}
	return result;
}

void StandardSet::clear()
{
	while( m_members.size() )
	{
		remove( m_members.begin()->get() );
	}
}

void StandardSet::setRemoveOrphans( bool removeOrphans )
{
	if( removeOrphans == m_removeOrphans )
	{
		return;
	}

	m_removeOrphans = removeOrphans;
	for( auto &m : m_members )
	{
		GraphComponent *graphComponent = IECore::runTimeCast<GraphComponent>( m.get() );
		if( !graphComponent )
		{
			continue;
		}
		if( m_removeOrphans )
		{
			graphComponent->parentChangedSignal().connect( boost::bind( &StandardSet::parentChanged, this, ::_1 ) );
		}
		else
		{
			graphComponent->parentChangedSignal().disconnect( boost::bind( &StandardSet::parentChanged, this, ::_1 ) );
		}
	}
}

bool StandardSet::getRemoveOrphans() const
{
	return m_removeOrphans;
}

bool StandardSet::contains( const Member *object ) const
{
	// const cast is ugly but safe and it allows us to present the
	// appropriate public interface (you should be able to query membership
	// without non-const access to an object).
	return m_members.find( const_cast<IECore::RunTimeTyped *>( object ) )!=m_members.end();
}

Set::Member *StandardSet::member( size_t index )
{
	return m_members.get<1>()[index].get();
}

const Set::Member *StandardSet::member( size_t index ) const
{
	return m_members.get<1>()[index].get();
}

size_t StandardSet::size() const
{
	return m_members.size();
}

void StandardSet::parentChanged( GraphComponent *member )
{
	if( !member->parent() )
	{
		remove( member );
	}
}
