//////////////////////////////////////////////////////////////////////////
//
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

#include "Gaffer/RecursiveChildIterator.h"

#include "GafferTest/Assert.h"
#include "GafferTest/RecursiveChildIteratorTest.h"

using namespace Gaffer;

void GafferTest::testRecursiveChildIterator()
{
	GraphComponentPtr a = new GraphComponent( "a" );
	GraphComponentPtr b = new GraphComponent( "b" );
	GraphComponentPtr c = new GraphComponent( "c" );
	GraphComponentPtr d = new GraphComponent( "d" );
	GraphComponentPtr e = new GraphComponent( "e" );
	GraphComponentPtr f = new GraphComponent( "f" );
	GraphComponentPtr g = new GraphComponent( "g" );

	a->addChild( b );
	a->addChild( c );
	a->addChild( d );

	d->addChild( e );
	d->addChild( f );

	e->addChild( g );

	// a - b
	//   - c
	//   - d - e - g
	//       - f

	RecursiveChildIterator it1( a.get() );
	RecursiveChildIterator it2( a.get() );

	GAFFERTEST_ASSERT( *it1 == b );
	GAFFERTEST_ASSERT( *it2 == b );
	GAFFERTEST_ASSERT( it1 == it2 );

	it1++;
	GAFFERTEST_ASSERT( *it1 == c );
	GAFFERTEST_ASSERT( *it2 == b );
	GAFFERTEST_ASSERT( it1 != it2 );

	it2++;
	GAFFERTEST_ASSERT( *it1 == c );
	GAFFERTEST_ASSERT( *it2 == c );
	GAFFERTEST_ASSERT( it1 == it2 );

	it1++;
	it2 = it1;
	GAFFERTEST_ASSERT( *it1 == d );
	GAFFERTEST_ASSERT( *it2 == d );
	GAFFERTEST_ASSERT( it1 == it2 );

	std::vector<GraphComponentPtr> visited;
	for( RecursiveChildIterator it( a.get() ); it != it.end(); ++it )
	{
		visited.push_back( *it );
	}

	GAFFERTEST_ASSERT( visited.size() == 6 );
	GAFFERTEST_ASSERT( visited[0] == b );
	GAFFERTEST_ASSERT( visited[1] == c );
	GAFFERTEST_ASSERT( visited[2] == d );
	GAFFERTEST_ASSERT( visited[3] == e );
	GAFFERTEST_ASSERT( visited[4] == g );
	GAFFERTEST_ASSERT( visited[5] == f );

	// test pruning

	visited.clear();
	for( RecursiveChildIterator it( a.get() ); it != it.end(); ++it )
	{
		if( *it == e || *it == b )
		{
			it.prune();
		}
		visited.push_back( *it );
	}

	GAFFERTEST_ASSERT( visited.size() == 5 );
	GAFFERTEST_ASSERT( visited[0] == b );
	GAFFERTEST_ASSERT( visited[1] == c );
	GAFFERTEST_ASSERT( visited[2] == d );
	GAFFERTEST_ASSERT( visited[3] == e );
	GAFFERTEST_ASSERT( visited[4] == f );

	visited.clear();
	for( RecursiveChildIterator it( a.get() ); it != it.end(); ++it )
	{
		if( *it == b || *it == d )
		{
			it.prune();
		}
		visited.push_back( *it );
	}

	GAFFERTEST_ASSERT( visited.size() == 3 );
	GAFFERTEST_ASSERT( visited[0] == b );
	GAFFERTEST_ASSERT( visited[1] == c );
	GAFFERTEST_ASSERT( visited[2] == d );

}
