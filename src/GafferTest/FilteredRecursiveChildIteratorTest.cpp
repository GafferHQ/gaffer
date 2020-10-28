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

#include "GafferTest/FilteredRecursiveChildIteratorTest.h"

#include "GafferTest/Assert.h"

#include "Gaffer/Node.h"
#include "Gaffer/NumericPlug.h"

using namespace Gaffer;

void GafferTest::testFilteredRecursiveChildIterator()
{
	NodePtr a = new Node( "a" );
	NodePtr b = new Node( "b" );
	FloatPlugPtr c = new FloatPlug( "c" );
	NodePtr d = new Node( "d" );
	NodePtr e = new Node( "e" );
	ValuePlugPtr f = new ValuePlug( "f" );
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
	for( Node::RecursiveIterator it( a.get() ); !it.done(); it++ )
	{
		nodes.push_back( *it );
	}

	GAFFERTEST_ASSERT( nodes.size() == 3 );
	GAFFERTEST_ASSERT( nodes[0] == b );
	GAFFERTEST_ASSERT( nodes[1] == d );
	GAFFERTEST_ASSERT( nodes[2] == e );

	// This demonstrates the use of both the main predicate and also the
	// recursion predicate in the FilteredRecursiveChildIterator. The main
	// predicate specifies that we will only visit plugs, but the recursion
	// predicate specifies that we'll recurse over everything to find them.
	//////////////////////////////////////////////////////////////////////////

	typedef FilteredRecursiveChildIterator<PlugPredicate<>, TypePredicate<GraphComponent> > DeepRecursivePlugIterator;
	std::vector<PlugPtr> plugs;
	for( DeepRecursivePlugIterator it( a.get() ); !it.done(); it++ )
	{
		plugs.push_back( *it );
	}

	GAFFERTEST_ASSERT( plugs.size() == 8 ); // there's also the user plug per node
	GAFFERTEST_ASSERT( plugs[0] == a->userPlug() );
	GAFFERTEST_ASSERT( plugs[1] == b->userPlug() );
	GAFFERTEST_ASSERT( plugs[2] == c );
	GAFFERTEST_ASSERT( plugs[3] == d->userPlug() );
	GAFFERTEST_ASSERT( plugs[4] == e->userPlug() );
	GAFFERTEST_ASSERT( plugs[5] == f );
	GAFFERTEST_ASSERT( plugs[6] == g );
	GAFFERTEST_ASSERT( plugs[7] == h );

	typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, FloatPlug>, TypePredicate<GraphComponent> > DeepRecursiveFloatPlugIterator;
	plugs.clear();
	for( DeepRecursiveFloatPlugIterator it( a.get() ); !it.done(); it++ )
	{
		plugs.push_back( *it );
	}

	GAFFERTEST_ASSERT( plugs.size() == 3 );
	GAFFERTEST_ASSERT( plugs[0] == c );
	GAFFERTEST_ASSERT( plugs[1] == g );
	GAFFERTEST_ASSERT( plugs[2] == h );

	typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, FloatPlug>, TypePredicate<GraphComponent> > DeepRecursiveOutputFloatPlugIterator;
	plugs.clear();
	for( DeepRecursiveOutputFloatPlugIterator it( a.get() ); !it.done(); it++ )
	{
		plugs.push_back( *it );
	}

	GAFFERTEST_ASSERT( plugs.size() == 1 );
	GAFFERTEST_ASSERT( plugs[0] == h );

	// This demonstrates the use of a more restrictive recursion predicate
	// which only allows recursion into plugs - this allows us to avoid
	// recursing to plugs owned by child nodes of the node we're interested in.
	//////////////////////////////////////////////////////////////////////////

	typedef FilteredRecursiveChildIterator<PlugPredicate<>, PlugPredicate<> > ShallowRecursivePlugIterator;
	plugs.clear();
	for( ShallowRecursivePlugIterator it( a.get() ); !it.done(); it++ )
	{
		plugs.push_back( *it );
	}
	GAFFERTEST_ASSERT( plugs.size() == 1 ); // there's also the user plug per node
	GAFFERTEST_ASSERT( plugs[0] == a->userPlug() );

	plugs.clear();
	for( ShallowRecursivePlugIterator it( b.get() ); !it.done(); it++ )
	{
		plugs.push_back( *it );
	}
	GAFFERTEST_ASSERT( plugs.size() == 2 ); // there's also the user plug per node
	GAFFERTEST_ASSERT( plugs[0] == b->userPlug() );
	GAFFERTEST_ASSERT( plugs[1] == c );

	plugs.clear();
	for( ShallowRecursivePlugIterator it( e.get() ); !it.done(); it++ )
	{
		plugs.push_back( *it );
	}
	GAFFERTEST_ASSERT( plugs.size() == 4 );
	GAFFERTEST_ASSERT( plugs[0] == e->userPlug() );
	GAFFERTEST_ASSERT( plugs[1] == f );
	GAFFERTEST_ASSERT( plugs[2] == g );
	GAFFERTEST_ASSERT( plugs[3] == h );
}
