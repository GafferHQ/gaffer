//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014-2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferTest/ContextTest.h"

#include "GafferTest/Assert.h"

#include "Gaffer/Context.h"

#include "IECore/Timer.h"

#include "boost/lexical_cast.hpp"
#include "tbb/parallel_for.h"
#include <unordered_set>

using namespace std;
using namespace boost;
using namespace IECore;
using namespace Gaffer;

// A test useful for assessing the performance
// of the Context class.
void GafferTest::testManyContexts()
{
	// our typical context doesn't have a huge number of keys - we'll
	// use a working set of 20 for this test.

	ContextPtr base = new Context();
	const int numKeys = 20;
	vector<InternedString> keys;
	for( int i = 0; i < numKeys; ++i )
	{
		InternedString key = string( "testKey" ) + lexical_cast<string>( i );
		keys.push_back( key );
		base->set( key, -1 - i );
	}
	const MurmurHash baseHash = base->hash();

	// then typically we create new temporary contexts based on that one,
	// change a value or two, and then continue.

	Timer t;
	for( int i = 0; i < 1000000; ++i )
	{
		ContextPtr tmp = new Context( *base, Context::Borrowed );
		tmp->set( keys[i%numKeys], i );
		GAFFERTEST_ASSERT( tmp->get<int>( keys[i%numKeys] ) == i );
		GAFFERTEST_ASSERT( tmp->hash() != baseHash );
	}
}

// Useful for assessing the performance of substitutions.
void GafferTest::testManySubstitutions()
{
	ContextPtr context = new Context();
	context->set( "foodType", std::string( "kipper" ) );
	context->set( "cookingMethod", std::string( "smoke" ) );

	const std::string phrase( "${cookingMethod} me a ${foodType}" );
	const std::string expectedResult( "smoke me a kipper" );

	Timer t;
	for( int i = 0; i < 1000000; ++i )
	{
		const std::string s = context->substitute( phrase );
		GAFFERTEST_ASSERT( s == expectedResult );
	}
}

// Useful for assessing the performance of environment variable substitutions.
void GafferTest::testManyEnvironmentSubstitutions()
{
	ContextPtr context = new Context();

	const std::string phrase( "${GAFFER_ROOT}" );
	const std::string expectedResult( getenv( "GAFFER_ROOT") );

	Timer t;
	for( int i = 0; i < 1000000; ++i )
	{
		const std::string s = context->substitute( phrase );
		GAFFERTEST_ASSERT( s == expectedResult );
	}
}

// Tests that scoping a null context is a no-op
void GafferTest::testScopingNullContext()
{
	ContextPtr context = new Context();
	context->set( "foodType", std::string( "kipper" ) );
	context->set( "cookingMethod", std::string( "smoke" ) );

	const std::string phrase( "${cookingMethod} me a ${foodType}" );
	const std::string expectedResult( "smoke me a kipper" );

	{
		Context::Scope scope( context.get() );
		const std::string s = Context::current()->substitute( phrase );
		GAFFERTEST_ASSERT( s == expectedResult );

		const Context *nullContext = nullptr;
		{
			Context::Scope scope( nullContext );
			const std::string s = Context::current()->substitute( phrase );
			GAFFERTEST_ASSERT( s == expectedResult );
		}
	}
}

void GafferTest::testEditableScope()
{
	// TODO - this test needs complete reworking once we stop using Data internally
	/*ContextPtr baseContext = new Context();
	baseContext->set( "a", 10 );
	baseContext->set( "b", 20 );

	const IntData *aData = baseContext->get<IntData>( "a" );
	size_t aRefCount = aData->refCount();

	const IntData *bData = baseContext->get<IntData>( "b" );
	size_t bRefCount = bData->refCount();

	{
		// Scope an editable copy of the context
		Context::EditableScope scope( baseContext.get() );

		const Context *currentContext = Context::current();
		GAFFERTEST_ASSERT( currentContext != baseContext );

		// The editable copy should be identical to the original,
		// and the original should be unchanged.
		GAFFERTEST_ASSERT( baseContext->get<int>( "a" ) == 10 );
		GAFFERTEST_ASSERT( baseContext->get<int>( "b" ) == 20 );
		GAFFERTEST_ASSERT( currentContext->get<int>( "a" ) == 10 );
		GAFFERTEST_ASSERT( currentContext->get<int>( "b" ) == 20 );
		GAFFERTEST_ASSERT( currentContext->hash() == baseContext->hash() );

		// The copy should even be referencing the exact same data
		// as the original.
		GAFFERTEST_ASSERT( baseContext->get<Data>( "a" ) == aData );
		GAFFERTEST_ASSERT( baseContext->get<Data>( "b" ) == bData );
		GAFFERTEST_ASSERT( currentContext->get<Data>( "a" ) == aData );
		GAFFERTEST_ASSERT( currentContext->get<Data>( "b" ) == bData );

		// But it shouldn't have affected the reference counts, because
		// we rely on the base context to maintain the lifetime for us
		// as an optimisation.
		GAFFERTEST_ASSERT( aData->refCount() == aRefCount );
		GAFFERTEST_ASSERT( bData->refCount() == bRefCount );

		// Editing the copy shouldn't affect the original
		scope.set( "c", 30 );
		GAFFERTEST_ASSERT( baseContext->get<int>( "c", -1 ) == -1 );
		GAFFERTEST_ASSERT( currentContext->get<int>( "c" ) == 30 );

		// Even if we're editing a variable that exists in
		// the original.
		scope.set( "a", 40 );
		GAFFERTEST_ASSERT( baseContext->get<int>( "a" ) == 10 );
		GAFFERTEST_ASSERT( currentContext->get<int>( "a" ) == 40 );

		// And we should be able to remove a variable from the
		// copy without affecting the original too.
		scope.remove( "b" );
		GAFFERTEST_ASSERT( baseContext->get<int>( "b" ) == 20 );
		GAFFERTEST_ASSERT( currentContext->get<int>( "b", -1 ) == -1 );

		// And none of the edits should have affected the original
		// data at all.
		GAFFERTEST_ASSERT( baseContext->get<Data>( "a" ) == aData );
		GAFFERTEST_ASSERT( baseContext->get<Data>( "b" ) == bData );
		GAFFERTEST_ASSERT( aData->refCount() == aRefCount );
		GAFFERTEST_ASSERT( bData->refCount() == bRefCount );
	}
	*/

}

// Create the number of contexts specified, and return counts for how many collisions there are
// in each of the four 32 bit sections of the context hash.  MurmurHash performs good mixing, so
// the four sections should be independent, and as long as collisions within each section occur only
// at the expected rate, the chance of a full collision across all 4 should be infinitesimal
// ( we don't want to check for collisions in the whole 128 bit hash, since it would take years
// for one to occur randomly )
// "mode" switches betwen 4 modes for creating contexts:
//   0 :  1 entry with a single increment int
//   1 :  40 fixed strings, plus a single incrementing int
//   2 :  20 random floats
//   3 :  an even mixture of the previous 3 modes
// "seed" can be used to perform different runs to get an average number.
// The goal is that regardless of how we create the contexts, they are all unique, and should therefore
// have an identical chance of collisions if our hashing performs ideally.
std::tuple<int,int,int,int> GafferTest::countContextHash32Collisions( int contexts, int mode, int seed )
{
	std::unordered_set<uint32_t> used[4];

	InternedString a( "a" );
	InternedString numberNames[40];
	for( int i = 0; i < 40; i++ )
	{
		numberNames[i] = InternedString( i );
	}

	unsigned int rand_seed = seed;
	int collisions[4] = {0,0,0,0};
	for( int i = 0; i < contexts; i++ )
	{
		int curMode = mode;
		int elementSeed = seed * contexts + i;
		if( curMode == 3 )
		{
			curMode = i % 3;
			elementSeed = seed * contexts + i / 3;
		}

		Context c;
		if( curMode == 0 )
		{
			c.set( a, elementSeed );
		}
		else if( curMode == 1 )
		{
			for( int j = 0; j < 40; j++ )
			{
				c.set( numberNames[j], j );
			}
			c.set( a, elementSeed );
		}
		else if( curMode == 2 )
		{
			for( int j = 0; j < 20; j++ )
			{
				c.set( numberNames[j], rand_r( &rand_seed ) );
			}
		}

		if( !used[0].insert( (uint32_t)( c.hash().h1() ) ).second )
		{
			collisions[0]++;
		}
		if( !used[1].insert( (uint32_t)( c.hash().h1() >> 32 ) ).second )
		{
			collisions[1]++;
		}
		if( !used[2].insert( (uint32_t)( c.hash().h2() ) ).second )
		{
			collisions[2]++;
		}
		if( !used[3].insert( (uint32_t)( c.hash().h2() >> 32 ) ).second )
		{
			collisions[3]++;
		}
	}

	return std::make_tuple( collisions[0], collisions[1], collisions[2], collisions[3] );
}

void GafferTest::testContextHashPerformance( int numEntries, int entrySize, bool startInitialized )
{
	// We usually deal with contexts that already have some stuff in them, so adding some entries
	// to the context makes this test more realistic
	ContextPtr baseContext = new Context();
	for( int i = 0; i < numEntries; i++ )
	{
		baseContext->set( InternedString( i ), std::string( entrySize, 'x') );
	}

	const InternedString varyingVarName = "varyVar";
	if( startInitialized )
	{
		baseContext->set( varyingVarName, -1 );
	}

	Context::Scope baseScope( baseContext.get() );

	const ThreadState &threadState = ThreadState::current();

	tbb::parallel_for( tbb::blocked_range<size_t>( 0, 10000000 ), [&threadState, &varyingVarName]( const tbb::blocked_range<size_t> &r )
		{
			for( size_t i = r.begin(); i != r.end(); ++i )
			{
				Context::EditableScope scope( threadState );
				scope.set( varyingVarName, (int)i );

				// This call is relied on by ValuePlug's HashCacheKey, so it is crucial that it be fast
				scope.context()->hash();
			}
		}
	);

}
