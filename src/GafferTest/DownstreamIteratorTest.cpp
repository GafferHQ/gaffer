//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "GafferTest/DownstreamIteratorTest.h"

#include "GafferTest/Assert.h"

#include "Gaffer/DownstreamIterator.h"
#include "Gaffer/Random.h"

using namespace Gaffer;

void GafferTest::testDownstreamIterator()
{

	//   a
	//   |
	//   b
	//  / \.
	// c   d
	//      \.
	//		 e

	Random::Ptr a = new Random( "a" );
	Random::Ptr b = new Random( "b" );
	Random::Ptr c = new Random( "c" );
	Random::Ptr d = new Random( "d" );
	Random::Ptr e = new Random( "e" );

	b->floatRangePlug()->getChild( 0 )->setInput( a->outFloatPlug() );
	c->floatRangePlug()->getChild( 0 )->setInput( b->outFloatPlug() );
	d->floatRangePlug()->getChild( 0 )->setInput( b->outFloatPlug() );
	e->floatRangePlug()->getChild( 0 )->setInput( d->outFloatPlug() );

	DownstreamIterator it1( a->floatRangePlug()->getChild( 0 ) );
	DownstreamIterator it2( a->floatRangePlug()->getChild( 0 ) );

	GAFFERTEST_ASSERT( &*it1 == a->outFloatPlug() );
	GAFFERTEST_ASSERT( &*it2 == a->outFloatPlug() );
	GAFFERTEST_ASSERT( it1.upstream() == a->floatRangePlug()->getChild( 0 ) );
	GAFFERTEST_ASSERT( it2.upstream() == a->floatRangePlug()->getChild( 0 ) );
	GAFFERTEST_ASSERT( it1 == it2 );
	GAFFERTEST_ASSERT( !it1.done() );
	GAFFERTEST_ASSERT( !it2.done() );

	it1++;

	GAFFERTEST_ASSERT( &*it1 == b->floatRangePlug()->getChild( 0 ) );
	GAFFERTEST_ASSERT( &*it2 == a->outFloatPlug() );
	GAFFERTEST_ASSERT( it1.upstream() == a->outFloatPlug() );
	GAFFERTEST_ASSERT( it2.upstream() == a->floatRangePlug()->getChild( 0 ) );
	GAFFERTEST_ASSERT( it1 != it2 );
	GAFFERTEST_ASSERT( !it1.done() );
	GAFFERTEST_ASSERT( !it2.done() );

	it2 = it1;

	GAFFERTEST_ASSERT( &*it1 == b->floatRangePlug()->getChild( 0 ) );
	GAFFERTEST_ASSERT( &*it2 == b->floatRangePlug()->getChild( 0 ) );
	GAFFERTEST_ASSERT( it1.upstream() == a->outFloatPlug() );
	GAFFERTEST_ASSERT( it2.upstream() == a->outFloatPlug() );
	GAFFERTEST_ASSERT( it1 == it2 );
	GAFFERTEST_ASSERT( !it1.done() );
	GAFFERTEST_ASSERT( !it2.done() );

	std::vector<const Plug *> visited;
	for( DownstreamIterator it( a->floatRangePlug()->getChild( 0 ) ); !it.done(); ++it )
	{
		visited.push_back( &*it );
	}

	GAFFERTEST_ASSERT( visited.size() == 9 );
	GAFFERTEST_ASSERT( visited[0] == a->outFloatPlug() );
	GAFFERTEST_ASSERT( visited[1] == b->floatRangePlug()->getChild( 0 ) );
	GAFFERTEST_ASSERT( visited[2] == b->outFloatPlug() );
	GAFFERTEST_ASSERT( visited[3] == c->floatRangePlug()->getChild( 0 ) );
	GAFFERTEST_ASSERT( visited[4] == c->outFloatPlug() );
	GAFFERTEST_ASSERT( visited[5] == d->floatRangePlug()->getChild( 0 ) );
	GAFFERTEST_ASSERT( visited[6] == d->outFloatPlug() );
	GAFFERTEST_ASSERT( visited[7] == e->floatRangePlug()->getChild( 0 ) );
	GAFFERTEST_ASSERT( visited[8] == e->outFloatPlug() );

	// test pruning

	visited.clear();
	for( DownstreamIterator it( a->floatRangePlug()->getChild( 0 ) ); !it.done(); ++it )
	{
		visited.push_back( &*it );
		if( &*it == d->floatRangePlug()->getChild( 0 ) || &*it == c->outFloatPlug() )
		{
			it.prune();
		}
	}

	GAFFERTEST_ASSERT( visited.size() == 6 );
	GAFFERTEST_ASSERT( visited[0] == a->outFloatPlug() );
	GAFFERTEST_ASSERT( visited[1] == b->floatRangePlug()->getChild( 0 ) );
	GAFFERTEST_ASSERT( visited[2] == b->outFloatPlug() );
	GAFFERTEST_ASSERT( visited[3] == c->floatRangePlug()->getChild( 0 ) );
	GAFFERTEST_ASSERT( visited[4] == c->outFloatPlug() );
	GAFFERTEST_ASSERT( visited[5] == d->floatRangePlug()->getChild( 0 ) );

}
