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

// we undefine NDEBUG so we can use assert() for our test cases.
/// \todo We might like to define our own assert which throws an
/// exception which is designed to be caught by the python test
/// runner and reported nicely.
#undef NDEBUG

#include <iostream>

#include "Gaffer/RecursiveChildIterator.h"

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

	RecursiveChildIterator it1( a );
	RecursiveChildIterator it2( a );
	
	assert( *it1 == b );
	assert( *it2 == b );
	assert( it1 == it2 );
	
	it1++;
	assert( *it1 == c );
	assert( *it2 == b );
	assert( it1 != it2 );
	
	it2++;
	assert( *it1 == c );
	assert( *it2 == c );
	assert( it1 == it2 );
	
	it1++;
	it2 = it1;
	assert( *it1 == d );
	assert( *it2 == d );
	assert( it1 == it2 );
		
	std::vector<GraphComponentPtr> visited;
	for( RecursiveChildIterator it( a ); it != it.end(); ++it )
	{
		visited.push_back( *it );
	}	
	
	assert( visited.size() == 6 );
	assert( visited[0] == b );
	assert( visited[1] == c );
	assert( visited[2] == d );
	assert( visited[3] == e );
	assert( visited[4] == g );
	assert( visited[5] == f );
	
}
