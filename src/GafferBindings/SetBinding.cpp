//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#include "boost/python.hpp"
#include "boost/python/suite/indexing/container_utils.hpp"

#include "GafferBindings/SignalBinding.h"
#include "GafferBindings/CatchingSlotCaller.h"

#include "Gaffer/Set.h"

#include "IECorePython/RunTimeTypedBinding.h"

using namespace Gaffer;

namespace GafferBindings
{

namespace Detail
{

boost::python::object setMembers( Set &s )
{
	boost::python::object result( boost::python::handle<>( PySet_New( 0 ) ) );
	for( Set::MemberContainer::const_iterator it=s.members().begin(); it!=s.members().end(); it++ )
	{
		result.attr( "add" )( *it );
	}
	return result;
}

boost::python::object sequencedSetMembers( Set &s )
{
	Set::SequencedIndex &i = s.sequencedMembers();
	boost::python::list l;
	for( Set::SequencedIndex::const_iterator it = i.begin(); it!=i.end(); it++ )
	{
		l.append( *it );
	}
	return boost::python::tuple( l );
}

SetPtr setConstructor( boost::python::object o )
{
	SetPtr result = new Set;
	std::vector<Set::MemberPtr> members;
	boost::python::container_utils::extend_container( members, o );
	result->add( members.begin(), members.end() );
	return result;
}

static size_t addFromSequence( Set &s, boost::python::object o )
{
	std::vector<Set::MemberPtr> members;
	boost::python::container_utils::extend_container( members, o );
	return s.add( members.begin(), members.end() );
}

static size_t removeFromSequence( Set &s, boost::python::object o )
{
	std::vector<Set::MemberPtr> members;
	boost::python::container_utils::extend_container( members, o );
	return s.remove( members.begin(), members.end() );
}

struct MemberAcceptanceSlotCaller
{
	bool operator()( boost::python::object slot, ConstSetPtr s, IECore::ConstRunTimeTypedPtr m )
	{
		try
		{
			return slot( IECore::constPointerCast<Set>( s ), IECore::constPointerCast<IECore::RunTimeTyped>( m ) );
		}
		catch( const boost::python::error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // clears the error status
		}
		return false;
	}
};

} // namespace Detail

void bindSet()
{
	
	boost::python::scope s = IECorePython::RunTimeTypedClass<Set>()
		.def( boost::python::init<>() )
		.def( "__init__", boost::python::make_constructor( Detail::setConstructor ) )
		.def( "add", &Detail::addFromSequence )
		.def( "add", (bool (Set::*)( Set::MemberPtr ) )&Set::add )
		.def( "remove", &Detail::removeFromSequence )
		.def( "remove", (bool (Set::*)( Set::MemberPtr ) )&Set::remove )
		.def( "clear", &Set::clear )
		.def( "contains", &Set::contains )
		.def( "size", &Set::size )
		.def( "lastAdded", (Set::MemberPtr (Set::*)())&Set::lastAdded )
		.def( "__contains__", &Set::contains )
		.def( "__len__", &Set::size )
		.def( "members", &Detail::setMembers )
		.def( "sequencedMembers", &Detail::sequencedSetMembers )
		.def( "memberAddedSignal", &Set::memberAddedSignal, boost::python::return_internal_reference<1>() )
		.def( "memberRemovedSignal", &Set::memberRemovedSignal, boost::python::return_internal_reference<1>() )
		.def( "memberAcceptanceSignal", &Set::memberAcceptanceSignal, boost::python::return_internal_reference<1>() )
	;	

	SignalBinder<Set::MemberSignal, DefaultSignalCaller<Set::MemberSignal>, CatchingSlotCaller<Set::MemberSignal> >::bind( "MemberSignal" );
	SignalBinder<Set::MemberAcceptanceSignal, DefaultSignalCaller<Set::MemberAcceptanceSignal>, Detail::MemberAcceptanceSlotCaller>::bind( "MemberAcceptanceSignal" );
	
}

} // namespace GafferBindings
