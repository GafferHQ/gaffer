//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#include "Gaffer/StandardSet.h"

#include "IECore/Exception.h"

using namespace Gaffer;

StandardSet::StandardSet()
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
	if( !m_memberAcceptanceSignal( this, member ) )
	{
		throw IECore::Exception( "Member is not eligible for inclusion in StandardSet." );
	}
	
	bool result = m_members.insert( member ).second;
	if( result )
	{
		memberAddedSignal()( this, member );
	}
	return result;
}

bool StandardSet::remove( MemberPtr member )
{
	bool result = m_members.erase( member );
	if( result )
	{
		memberRemovedSignal()( this, member );
	}
	return result;
}

void StandardSet::clear()
{
	while( m_members.size() )
	{
		remove( *(m_members.begin()) );
	}
}

bool StandardSet::contains( ConstMemberPtr object ) const
{
	// const cast is ugly but safe and it allows us to present the
	// appropriate public interface (you should be able to query membership
	// without non-const access to an object).
	return m_members.find( const_cast<IECore::RunTimeTyped *>( object.get() ) )!=m_members.end();
}

Set::MemberPtr StandardSet::member( size_t index )
{
	return m_members.get<1>()[index];
}

Set::ConstMemberPtr StandardSet::member( size_t index ) const
{
	return m_members.get<1>()[index];
}
		
size_t StandardSet::size() const
{
	return m_members.size();
}
