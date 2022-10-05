//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

#include "SignalsTest.h"

#include "GafferTest/Assert.h"

#include "Gaffer/Signals.h"

using namespace boost::python;
using namespace Gaffer;

namespace
{

void testConstructionPerformance()
{
	std::vector<Signals::Signal<void()>> signals( 1000000 );
	GAFFERTEST_ASSERTEQUAL( signals.size(), 1000000 );
}

void testConnectionPerformance()
{
	Signals::Signal<void()> signal;
	auto slot = [](){};

	for( int i = 0; i < 1000000; ++i )
	{
		signal.connect( slot );
	}

	GAFFERTEST_ASSERT( signal.numSlots() );
}

void testCallPerformance()
{
	Signals::Signal<void( int )> signal;

	int callsMade = 0;
	signal.connect( [&callsMade]( int i ){ callsMade += i; } );

	const int callsToMake = 10000000;
	for( int i = 0; i < callsToMake; ++i )
	{
		signal( 1 );
	}

	GAFFERTEST_ASSERTEQUAL( callsMade, callsToMake );
}

void testSelfDisconnectingSlot()
{
	// To be captured by our lambda slot. We use this to determine if the slot
	// has been destructed yet.

	auto sentinel = std::make_shared<bool>( true );

	// These are static, so that the lambda function will get away with
	// referencing them even if it has been destroyed.

	static auto weakSentinel = std::weak_ptr<bool>( sentinel );
	static int callCount = 0;
	static Signals::Connection connection;

	// Connect a lambda that owns the `sentinel` value, and asserts
	// that it remains alive for the duration of the slot call. Even
	// though the slot disconnects in the middle of the call.

	Signals::Signal<void()> signal;
	connection = signal.connect(
		[sentinel]() {
			GAFFERTEST_ASSERTEQUAL( callCount, 0 );
			GAFFERTEST_ASSERT( !weakSentinel.expired() );
			connection.disconnect();
			GAFFERTEST_ASSERT( !connection.connected() );
			GAFFERTEST_ASSERT( !weakSentinel.expired() );
			callCount += 1;
			GAFFERTEST_ASSERTEQUAL( callCount, 1 );
		}
	);

	// Drop our reference to the sentinel, and assert that the
	// slot is keeping it alive.

	sentinel = nullptr;
	GAFFERTEST_ASSERT( !weakSentinel.expired() );
	GAFFERTEST_ASSERT( connection.connected() );
	GAFFERTEST_ASSERTEQUAL( callCount, 0 );

	// Call the signal. We expect the sentinel to be alive for
	// the duration of the slot call, but to expire immediately
	// afterwards.

	signal();

	GAFFERTEST_ASSERT( weakSentinel.expired() );
	GAFFERTEST_ASSERT( !connection.connected() );
	GAFFERTEST_ASSERTEQUAL( callCount, 1 );
}

void testScopedConnectionMoveConstructor()
{
	static_assert( !std::is_copy_constructible_v<Signals::ScopedConnection> );

	Signals::Signal<void()> signal;

	Signals::Connection c = signal.connect( []{} );

	{
		Signals::ScopedConnection sc1( c );
		GAFFERTEST_ASSERT( c.connected() );
		GAFFERTEST_ASSERT( sc1.connected() );

		Signals::ScopedConnection sc2( std::move( sc1 ) );
		GAFFERTEST_ASSERT( c.connected() );
		GAFFERTEST_ASSERT( !sc1.connected() );
		GAFFERTEST_ASSERT( sc2.connected() );
	}

	GAFFERTEST_ASSERT( !c.connected() );
}

void testScopedConnectionMoveAssignment()
{
	static_assert( !std::is_copy_assignable_v<Signals::ScopedConnection> );

	Signals::Signal<void()> signal;

	Signals::Connection c = signal.connect( []{} );
	Signals::ScopedConnection sc1;

	{
		Signals::ScopedConnection sc2( c );
		GAFFERTEST_ASSERT( c.connected() );
		GAFFERTEST_ASSERT( !sc1.connected() );
		GAFFERTEST_ASSERT( sc2.connected() );

		sc1 = std::move( sc2 );
		GAFFERTEST_ASSERT( c.connected() );
		GAFFERTEST_ASSERT( !sc2.connected() );
		GAFFERTEST_ASSERT( sc1.connected() );
	}

	GAFFERTEST_ASSERT( c.connected() );
	GAFFERTEST_ASSERT( sc1.connected() );

	sc1 = Signals::Connection();
	GAFFERTEST_ASSERT( !c.connected() );
	GAFFERTEST_ASSERT( !sc1.connected() );
}

void testVectorOfScopedConnections()
{
	Signals::Signal<void()> signal;

	std::vector<Signals::Connection> connections;
	std::vector<Signals::ScopedConnection> scopedConnections;

	scopedConnections.reserve( 4 );
	const size_t initialCapacity = scopedConnections.capacity();

	// Will trigger reallocation/copying of `scopedConnections`, testing
	// move operations on ScopedConnection.
	while( scopedConnections.size() < initialCapacity * 4 )
	{
		Signals::Connection c = signal.connect( []{} );
		connections.push_back( c );
		scopedConnections.push_back( c );
	}

	for( auto &c : connections )
	{
		GAFFERTEST_ASSERT( c.connected() );
	}

	for( auto &c : scopedConnections )
	{
		GAFFERTEST_ASSERT( c.connected() );
	}

	scopedConnections.clear();

	for( auto &c : connections )
	{
		GAFFERTEST_ASSERT( !c.connected() );
	}
}

} // namespace

void GafferTestModule::bindSignalsTest()
{
	def( "testSignalConstructionPerformance", &testConstructionPerformance );
	def( "testSignalConnectionPerformance", &testConnectionPerformance );
	def( "testSignalCallPerformance", &testCallPerformance );
	def( "testSignalSelfDisconnectingSlot", &testSelfDisconnectingSlot );
	def( "testSignalScopedConnectionMoveConstructor", &testScopedConnectionMoveConstructor );
	def( "testSignalScopedConnectionMoveAssignment", &testScopedConnectionMoveAssignment );
	def( "testSignalVectorOfScopedConnections", &testVectorOfScopedConnections );
}
