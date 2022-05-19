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

#include "GafferTest/ComputeNodeTest.h"

#include "GafferTest/Assert.h"
#include "GafferTest/MultiplyNode.h"

#include "IECore/Timer.h"

#include "tbb/parallel_for.h"

#include <thread>

using namespace tbb;
using namespace Gaffer;

namespace
{

struct Edit
{

	Edit( const std::atomic_bool &stop )
		:	m_stop( stop )
	{
	}

	void operator()()
	{
		while( !m_stop )
		{
			GafferTest::MultiplyNodePtr m = new GafferTest::MultiplyNode;
			m->op1Plug()->setValue( 10 );
			m->op1Plug()->setValue( 20 );
			std::this_thread::yield();
		}
	}

	private :

		const std::atomic_bool &m_stop;

};

struct Compute
{

	Compute()
		:	m_node1( new GafferTest::MultiplyNode ), m_node2( new GafferTest::MultiplyNode )
	{
		m_node1->op1Plug()->setValue( 3 );
		m_node1->op2Plug()->setValue( 3 );
		m_node2->op1Plug()->setInput( m_node1->productPlug() );
		m_node2->op2Plug()->setValue( 1 );
	}

	void operator()( const blocked_range<size_t> &r ) const
	{
		for( size_t i=r.begin(); i!=r.end(); ++i )
		{
			GAFFERTEST_ASSERT( m_node2->productPlug()->getValue() == 9 );
		}
	}

	private :

		GafferTest::MultiplyNodePtr m_node1;
		GafferTest::MultiplyNodePtr m_node2;

};

} // namespace

void GafferTest::testComputeNodeThreading()
{
	// Set up a background thread that creates and
	// deletes node graphs.
	std::atomic_bool stop( false );
	Edit edit( stop );
	std::thread thread( edit );

	// And then do some threaded computation on some
	// other threads. This should be OK, because the
	// graphs being edited are not the same as the one
	// being computed.
	Compute c;
	IECore::Timer t;
	parallel_for( blocked_range<size_t>( 0, 1000000 ), c );
	// Uncomment for timing information. Since this test
	// repeats a very small computation many times, its
	// a good benchmark for measuring overhead in the
	// ComputeNode/ValuePlug machinery itself.
	//std::cerr << t.stop() << std::endl;
	stop = true;
	thread.join();
}
