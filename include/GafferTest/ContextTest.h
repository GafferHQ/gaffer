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

#ifndef GAFFERTEST_CONTEXTTEST_H
#define GAFFERTEST_CONTEXTTEST_H

#include "GafferTest/Assert.h"
#include "GafferTest/Export.h"

#include "Gaffer/Context.h"

#include <tuple>

namespace GafferTest
{

template < typename T >
void testEditableScopeTyped( const typename T::ValueType &aVal, const typename T::ValueType &bVal )
{
	using V = typename T::ValueType;

	Gaffer::ContextPtr baseContext = new Gaffer::Context();
	baseContext->set( "a", aVal );
	baseContext->set( "b", bVal );

	// Test basic context functionality
	GAFFERTEST_ASSERT( baseContext->get<V>( "a" ) == aVal );
	GAFFERTEST_ASSERT( *baseContext->getIfExists<V>( "a" ) == aVal );
	GAFFERTEST_ASSERT( baseContext->get<V>( "b" ) == bVal );
	GAFFERTEST_ASSERT( *baseContext->getIfExists<V>( "b" ) == bVal );
	GAFFERTEST_ASSERT( baseContext->getIfExists<V>( "doesntExist" ) == nullptr );

	const typename T::Ptr aData = new T( aVal );
	const typename T::Ptr bData = new T( bVal );

	// Test setting with a TypedData
	baseContext->set( "a", bData.get() );
	baseContext->set( "b", bData.get() );
	GAFFERTEST_ASSERT( baseContext->get<V>( "a" ) == bVal );
	GAFFERTEST_ASSERT( baseContext->get<V>( "b" ) == bVal );

	// And set back again with a direct value
	baseContext->set( "a", aVal );
	GAFFERTEST_ASSERT( baseContext->get<V>( "a" ) == aVal );
	GAFFERTEST_ASSERT( baseContext->get<V>( "b" ) == bVal );

	// Test getting as a generic Data - this should work where set as Data, or directly from a value
	GAFFERTEST_ASSERT( baseContext->getAsData( "a" )->isEqualTo( aData.get() ) );
	GAFFERTEST_ASSERT( baseContext->getAsData( "b" )->isEqualTo( bData.get() ) );

	const V *aPointer = baseContext->getIfExists<V>( "a" );
	const V *bPointer = baseContext->getIfExists<V>( "b" );

	{
		// Scope an editable copy of the context
		Gaffer::Context::EditableScope scope( baseContext.get() );

		const Gaffer::Context *currentContext = Gaffer::Context::current();
		GAFFERTEST_ASSERT( currentContext != baseContext );

		// The editable copy should be identical to the original,
		// and the original should be unchanged.
		GAFFERTEST_ASSERT( baseContext->get<V>( "a" ) == aVal );
		GAFFERTEST_ASSERT( baseContext->get<V>( "b" ) == bVal );
		GAFFERTEST_ASSERT( currentContext->get<V>( "a" ) == aVal );
		GAFFERTEST_ASSERT( currentContext->get<V>( "b" ) == bVal );
		GAFFERTEST_ASSERT( currentContext->hash() == baseContext->hash() );

		// The copy should even be referencing the exact same data
		// as the original.
		GAFFERTEST_ASSERT( baseContext->getIfExists<V>( "a" ) == aPointer );
		GAFFERTEST_ASSERT( baseContext->getIfExists<V>( "b" ) == bPointer );
		GAFFERTEST_ASSERT( currentContext->getIfExists<V>( "a" ) == aPointer );
		GAFFERTEST_ASSERT( currentContext->getIfExists<V>( "b" ) == bPointer );

		// Editing the copy shouldn't affect the original
		scope.set( "c", &aVal );
		GAFFERTEST_ASSERT( baseContext->getIfExists<V>( "c" ) == nullptr );
		GAFFERTEST_ASSERT( currentContext->get<V>( "c" ) == aVal );
		GAFFERTEST_ASSERT( currentContext->hash() != baseContext->hash() );

		// Even if we're editing a variable that exists in
		// the original.
		scope.set( "a", &bVal );
		GAFFERTEST_ASSERT( baseContext->get<V>( "a" ) == aVal );
		GAFFERTEST_ASSERT( currentContext->get<V>( "a" ) == bVal );

		// And we should be able to remove a variable from the
		// copy without affecting the original too.
		scope.remove( "b" );
		GAFFERTEST_ASSERT( baseContext->get<V>( "b" ) == bVal );
		GAFFERTEST_ASSERT( currentContext->getIfExists<V>( "b" ) == nullptr );

		// And none of the edits should have affected the original
		// data at all.
		GAFFERTEST_ASSERT( baseContext->getIfExists<V>( "a" ) == aPointer );
		GAFFERTEST_ASSERT( baseContext->getIfExists<V>( "b" ) == bPointer );

		// Test setAllocated with Data
		scope.setAllocated( "a", aData.get() );
		scope.setAllocated( "b", aData.get() );
		GAFFERTEST_ASSERT( currentContext->get<V>( "a" ) == aVal );
		GAFFERTEST_ASSERT( currentContext->get<V>( "b" ) == aVal );
		GAFFERTEST_ASSERT( currentContext->getAsData( "a" )->isEqualTo( aData.get() ) );
		GAFFERTEST_ASSERT( currentContext->getAsData( "b" )->isEqualTo( aData.get() ) );

		// And setAllocated with a direct data
		scope.setAllocated( "b", bVal );
		GAFFERTEST_ASSERT( currentContext->get<V>( "a" ) == aVal );
		GAFFERTEST_ASSERT( currentContext->get<V>( "b" ) == bVal );

		// Test getting as a generic Data - this should work where set as Data, or directly from a value
		GAFFERTEST_ASSERT( currentContext->getAsData( "a" )->isEqualTo( aData.get() ) );
		GAFFERTEST_ASSERT( currentContext->getAsData( "b" )->isEqualTo( bData.get() ) );
	}

	// Check that setting with a pointer, or a value, or Data, has the same effect
	{
		Gaffer::Context::EditableScope x( baseContext.get() );
		Gaffer::Context::EditableScope y( baseContext.get() );
		Gaffer::Context::EditableScope z( baseContext.get() );

		x.set( "c", &aVal );
		y.setAllocated( "c", aVal );
		z.setAllocated( "c", aData.get() );

		GAFFERTEST_ASSERT( x.context()->get<V>( "c" ) == aVal );
		GAFFERTEST_ASSERT( y.context()->get<V>( "c" ) == aVal );
		GAFFERTEST_ASSERT( z.context()->get<V>( "c" ) == aVal );

		GAFFERTEST_ASSERT( x.context()->hash() == y.context()->hash() );
		GAFFERTEST_ASSERT( x.context()->hash() == z.context()->hash() );
		GAFFERTEST_ASSERT( x.context()->variableHash( "c" ) == y.context()->variableHash( "c" ) );
		GAFFERTEST_ASSERT( x.context()->variableHash( "c" ) == z.context()->variableHash( "c" ) );

		x.set( "c", &bVal );
		y.setAllocated( "c", bVal );
		z.setAllocated( "c", bData.get() );

		GAFFERTEST_ASSERT( x.context()->get<V>( "c" ) == bVal );
		GAFFERTEST_ASSERT( y.context()->get<V>( "c" ) == bVal );
		GAFFERTEST_ASSERT( z.context()->get<V>( "c" ) == bVal );

		GAFFERTEST_ASSERT( x.context()->hash() == y.context()->hash() );
		GAFFERTEST_ASSERT( x.context()->hash() == z.context()->hash() );
		GAFFERTEST_ASSERT( x.context()->variableHash( "c" ) == y.context()->variableHash( "c" ) );
		GAFFERTEST_ASSERT( x.context()->variableHash( "c" ) == z.context()->variableHash( "c" ) );
	}
}

GAFFERTEST_API void testManyContexts();
GAFFERTEST_API void testManySubstitutions();
GAFFERTEST_API void testManyEnvironmentSubstitutions();
GAFFERTEST_API void testScopingNullContext();
GAFFERTEST_API void testEditableScope();
GAFFERTEST_API std::tuple<int,int,int,int> countContextHash32Collisions( int contexts, int mode, int seed );
GAFFERTEST_API void testContextHashPerformance( int numEntries, int entrySize, bool startInitialized );
GAFFERTEST_API void testContextCopyPerformance( int numEntries, int entrySize );

} // namespace GafferTest

#endif // GAFFERTEST_CONTEXTTEST_H
