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

#include "Gaffer/Node.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/CompoundPlug.h"

#include "GafferTest/FilteredRecursiveChildIteratorTest.h"

using namespace Gaffer;

void GafferTest::testFilteredRecursiveChildIterator()
{
	NodePtr a = new Node( "a" );
	NodePtr b = new Node( "b" );
	FloatPlugPtr c = new FloatPlug( "c" );
	NodePtr d = new Node( "d" );
	NodePtr e = new Node( "e" );
	CompoundPlugPtr f = new CompoundPlug( "f" );
	FloatPlugPtr g = new FloatPlug( "g" );
	FloatPlugPtr h = new FloatPlug( "h", Plug::Out );
	
	a->addChild( b );
	a->addChild( d );
	a->addChild( e );
	
	b->addChild( c );
	
	e->addChild( f );
	e->addChild( h );
	
	f->addChild( g );
	
	// a - b - c
	//   - d
	//   - e - f - g
	//       - h

	std::vector<NodePtr> nodes;
	for( RecursiveNodeIterator it( a ); it != it.end(); it++ )
	{
		nodes.push_back( *it );
	}
		
	assert( nodes.size() == 3 );
	assert( nodes[0] == b );
	assert( nodes[1] == d );
	assert( nodes[2] == e );
	
	std::vector<PlugPtr> plugs;
	for( RecursivePlugIterator it( a ); it != it.end(); it++ )
	{
		plugs.push_back( *it );
	}
		
	assert( plugs.size() == 8 ); // there's also the user plug per node
	assert( plugs[0] == a->userPlug() );
	assert( plugs[1] == b->userPlug() );
	assert( plugs[2] == c );
	assert( plugs[3] == d->userPlug() );
	assert( plugs[4] == e->userPlug() );
	assert( plugs[5] == f );
	assert( plugs[6] == g );
	assert( plugs[7] == h );
	
	plugs.clear();
	for( RecursiveFloatPlugIterator it( a ); it != it.end(); it++ )
	{
		plugs.push_back( *it );
	}
	
	assert( plugs.size() == 3 ); // there's also the user plug per node
	assert( plugs[0] == c );
	assert( plugs[1] == g );
	assert( plugs[2] == h );
	
	plugs.clear();
	for( RecursiveOutputFloatPlugIterator it( a ); it != it.end(); it++ )
	{
		plugs.push_back( *it );
	}
	
	assert( plugs.size() == 1 ); // there's also the user plug per node
	assert( plugs[0] == h );

}
