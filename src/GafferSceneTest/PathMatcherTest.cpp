//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "boost/assign/list_of.hpp"

#include "GafferTest/Assert.h"

#include "GafferScene/PathMatcher.h"
#include "GafferScene/ScenePlug.h"

#include "GafferSceneTest/PathMatcherTest.h"

using namespace std;
using namespace boost;
using namespace IECore;
using namespace GafferScene;

void GafferSceneTest::testPathMatcherRawIterator()
{
	vector<InternedString> root;
	vector<InternedString> a = assign::list_of( "a" );
	vector<InternedString> ab = assign::list_of( "a" )( "b" );
	vector<InternedString> abc = assign::list_of( "a" )( "b" )( "c" );

	PathMatcher m;
	PathMatcher::RawIterator it = m.begin();
	GAFFERTEST_ASSERT( it == m.end() );

	m.addPath( abc );
	it = m.begin();
	GAFFERTEST_ASSERT( *it == root );
	GAFFERTEST_ASSERT( it.exactMatch() == false );
	GAFFERTEST_ASSERT( it != m.end() );
	++it;
	GAFFERTEST_ASSERT( *it == a );
	GAFFERTEST_ASSERT( it.exactMatch() == false );
	GAFFERTEST_ASSERT( it != m.end() );
	++it;
	GAFFERTEST_ASSERT( *it == ab );
	GAFFERTEST_ASSERT( it.exactMatch() == false );
	GAFFERTEST_ASSERT( it != m.end() );
	++it;
	GAFFERTEST_ASSERT( *it == abc );
	GAFFERTEST_ASSERT( it.exactMatch() == true );
	GAFFERTEST_ASSERT( it != m.end() );
	++it;
	GAFFERTEST_ASSERT( it == m.end() );
}

void GafferSceneTest::testPathMatcherIteratorPrune()
{
	vector<InternedString> root;
	vector<InternedString> abc = assign::list_of( "a" )( "b" )( "c" );

	// Prune an empty iterator range.
	PathMatcher m;
	PathMatcher::Iterator it = m.begin();
	GAFFERTEST_ASSERT( it == m.end() );
	it.prune();
	GAFFERTEST_ASSERT( it == m.end() );

	// Prune the root iterator itself.
	m.addPath( root );
	it = m.begin();
	GAFFERTEST_ASSERT( *it == root );
	GAFFERTEST_ASSERT( it != m.end() );
	it.prune();
	GAFFERTEST_ASSERT( *it == root );
	GAFFERTEST_ASSERT( it != m.end() );
	++it;
	GAFFERTEST_ASSERT( it == m.end() );

	// As above, but actually with some
	// descendants to be pruned.
	m.addPath( abc );
	it = m.begin();
	GAFFERTEST_ASSERT( *it == root );
	GAFFERTEST_ASSERT( it != m.end() );
	it.prune();
	GAFFERTEST_ASSERT( *it == root );
	GAFFERTEST_ASSERT( it != m.end() );
	++it;
	GAFFERTEST_ASSERT( it == m.end() );

}

void GafferSceneTest::testPathMatcherFind()
{
	vector<InternedString> root;
	vector<InternedString> a = assign::list_of( "a" );
	vector<InternedString> ab = assign::list_of( "a" )( "b" );
	vector<InternedString> abc = assign::list_of( "a" )( "b" )( "c" );
	vector<InternedString> abcd = assign::list_of( "a" )( "b" )( "c" )( "d" );

	PathMatcher m;
	PathMatcher::RawIterator it = m.find( root );
	GAFFERTEST_ASSERT( it == m.end() );

	it = m.find( ab );
	GAFFERTEST_ASSERT( it == m.end() );

	m.addPath( abc );

	it = m.find( root );
	GAFFERTEST_ASSERT( it == m.begin() );
	GAFFERTEST_ASSERT( it != m.end() );
	GAFFERTEST_ASSERT( *it == root );
	++it;
	GAFFERTEST_ASSERT( *it == a );
	++it;
	GAFFERTEST_ASSERT( *it == ab );
	++it;
	GAFFERTEST_ASSERT( *it == abc );
	++it;
	GAFFERTEST_ASSERT( it == m.end() );

	it = m.find( ab );
	GAFFERTEST_ASSERT( it != m.end() );
	GAFFERTEST_ASSERT( *it == ab );
	++it;
	GAFFERTEST_ASSERT( *it == abc );
	++it;
	GAFFERTEST_ASSERT( it == m.end() );

	it = m.find( abcd );
	GAFFERTEST_ASSERT( it == m.end() );

}
