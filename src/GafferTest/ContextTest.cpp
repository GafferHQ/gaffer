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
	ContextPtr baseContext = new Context();
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

}

void GafferTest::testNewContextAPIBasics()
{

	// These are not a very complete tests ( more complete tests are added in Gaffer 0.60
	// for the actual new code ). But this confirms that the Gaffer 0.59 forward
	// compatibility shims all compile and call through to the correct functions.
	ContextPtr baseContext = new Context();
	GAFFERTEST_ASSERT( baseContext->getIfExists<int>( "a" ) == nullptr );
	GAFFERTEST_ASSERT( baseContext->getAsData( "a", nullptr ) == nullptr );
	GAFFERTEST_ASSERT( ((IntData*)baseContext->getAsData( "a", new IntData( 5 ) ).get())->readable() == 5 );
	try
	{
		baseContext->getAsData( "a" );
		GAFFERTEST_ASSERT( false );
	}
	catch( IECore::Exception &e )
	{
		// We correctly threw an exception
	}

	baseContext->set( "a", 10 );
	GAFFERTEST_ASSERT( *baseContext->getIfExists<int>( "a" ) == 10 );
	GAFFERTEST_ASSERT( ((IntData*)baseContext->getAsData( "a", nullptr ).get())->readable() == 10 );
	GAFFERTEST_ASSERT( ((IntData*)baseContext->getAsData( "a", new IntData( 5 ) ).get())->readable() == 10 );
	GAFFERTEST_ASSERT( ((IntData*)baseContext->getAsData( "a" ).get())->readable() == 10 );

	Context::EditableScope scope( baseContext.get() );

	int q = 15;
	scope.set( "b", &q );
	GAFFERTEST_ASSERT( scope.context()->get<int>( "b" ) == 15 );
	scope.setAllocated( "b", 20 );
	GAFFERTEST_ASSERT( scope.context()->get<int>( "b" ) == 20 );
	IntDataPtr intData = new IntData( 25 );
	scope.setAllocated( "b", intData.get() );
	GAFFERTEST_ASSERT( scope.context()->get<int>( "b" ) == 25 );

	float fps = 42.0f;
	scope.setFramesPerSecond( &fps );
	GAFFERTEST_ASSERT( scope.context()->getFramesPerSecond() == 42.0f );
}
