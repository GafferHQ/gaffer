//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#include "boost/lexical_cast.hpp"

#include "IECore/Timer.h"

#include "Gaffer/Context.h"

#include "GafferTest/Assert.h"
#include "GafferTest/ContextTest.h"

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
		base->set( key, i );
	}
	
	// then typically we create new temporary contexts based on that one,
	// change a value or two, and then continue.
			
	Timer t;
	for( int i = 0; i < 100000; ++i )
	{
		ContextPtr tmp = new Context( *base, Context::Borrowed );
		tmp->set( keys[i%numKeys], i );
		GAFFERTEST_ASSERT( tmp->get<int>( keys[i%numKeys] ) == i );
	}
	
	// uncomment to get timing information
	//std::cerr << t.stop() << std::endl;
}
