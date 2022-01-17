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

#include "boost/signals.hpp"

using namespace boost::python;

namespace
{

void testConstructionPerformance()
{
	std::vector<boost::signal<void()>> signals( 1000000 );
	GAFFERTEST_ASSERTEQUAL( signals.size(), 1000000 );
}

void testConnectionPerformance()
{
	boost::signal<void()> signal;
	auto slot = [](){};

	for( int i = 0; i < 1000000; ++i )
	{
		signal.connect( slot );
	}

	GAFFERTEST_ASSERT( signal.num_slots() );
}

void testCallPerformance()
{
	boost::signal<void( int )> signal;

	int callsMade = 0;
	signal.connect( [&callsMade]( int i ){ callsMade += i; } );

	const int callsToMake = 10000000;
	for( int i = 0; i < callsToMake; ++i )
	{
		signal( 1 );
	}

	GAFFERTEST_ASSERTEQUAL( callsMade, callsToMake );
}

void testDisconnectMatchingLambda()
{
	boost::signal<void()> signal;

	auto slot1 = [](){};
	auto slot2 = [](){};

	auto connection1 = signal.connect( slot1 );
	auto connection2 = signal.connect( slot2 );
	GAFFERTEST_ASSERTEQUAL( signal.num_slots(), 2 );

	signal.disconnect( slot1 );
	GAFFERTEST_ASSERTEQUAL( signal.num_slots(), 1 );
	GAFFERTEST_ASSERT( !connection1.connected() );
	GAFFERTEST_ASSERT( connection2.connected() );

	signal.disconnect( slot2 );
	GAFFERTEST_ASSERTEQUAL( signal.num_slots(), 0 );
	GAFFERTEST_ASSERT( signal.empty() );
	GAFFERTEST_ASSERT( !connection1.connected() );
	GAFFERTEST_ASSERT( !connection2.connected() );

}

void testSlot( const char *arg1 )
{
}

void testDisconnectMatchingBind()
{
	boost::signal<void()> signal;

	auto connection1 = signal.connect( boost::bind( testSlot, "hello" ) );
	auto connection2 = signal.connect( boost::bind( testSlot, "there" ) );
	GAFFERTEST_ASSERTEQUAL( signal.num_slots(), 2 );

	signal.disconnect( boost::bind( testSlot, "there" ) );
	GAFFERTEST_ASSERTEQUAL( signal.num_slots(), 1 );
	GAFFERTEST_ASSERT( connection1.connected() );
	GAFFERTEST_ASSERT( !connection2.connected() );

	signal.disconnect( boost::bind( testSlot, "hello" ) );
	GAFFERTEST_ASSERTEQUAL( signal.num_slots(), 0 );
	GAFFERTEST_ASSERT( signal.empty() );
	GAFFERTEST_ASSERT( !connection1.connected() );
	GAFFERTEST_ASSERT( !connection2.connected() );
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
	static boost::signals::connection connection;

	// Connect a lambda that owns the `sentinel` value, and asserts
	// that it remains alive for the duration of the slot call. Even
	// though the slot disconnects in the middle of the call.

	boost::signal<void()> signal;
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

} // namespace

void GafferTestModule::bindSignalsTest()
{
	def( "testSignalConstructionPerformance", &testConstructionPerformance );
	def( "testSignalConnectionPerformance", &testConnectionPerformance );
	def( "testSignalCallPerformance", &testCallPerformance );
	def( "testSignalDisconnectMatchingLambda", &testDisconnectMatchingLambda );
	def( "testSignalDisconnectMatchingBind", &testDisconnectMatchingBind );
	def( "testSignalSelfDisconnectingSlot", &testSelfDisconnectingSlot );
}
