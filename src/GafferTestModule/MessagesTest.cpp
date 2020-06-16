//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Cinesite VFX Ltd. nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "boost/python.hpp"

#include "MessagesTest.h"

#include "GafferTest/Assert.h"

#include "Gaffer/Private/IECorePreview/Messages.h"

using namespace IECorePreview;
using namespace boost::python;

namespace
{

void testCopyPerformance( const Messages &m, size_t count )
{
	for( size_t i = 0; i < count; ++i )
	{
		Messages c = m;
		c.size();
	}
}

void testAddPerformance( size_t count )
{
	const std::string context = "testMessagesAddPerformance";
	const std::string message = "testMessagesAddPerformancetestMessagesAddPerformancetestMessagesAddPerformance";

	Messages m;
	for( size_t i = 0; i < count; ++i )
	{
		m.add( Message( IECore::MessageHandler::Level( i % 4 ), context, message ) );
	}
}

void testValueReuse()
{
	// Note, this is a somewhat 'internal' test, to verify we're not
	// over-copying. As such, it has an explicit understanding of
	// the underlying implementation.

	size_t numMessages = 102;
	size_t bucketSize = 100;

	Messages m;

	for( size_t i = 0; i < numMessages; ++ i )
	{
		m.add( Message( IECore::MessageHandler::Level( i % 5 ), "testValueReuse", std::to_string( i ) ) );
	}

	Messages c = m;

	// Messages should be shared once in the const buckets
	for( size_t i = 0; i < bucketSize; ++ i )
	{
		GAFFERTEST_ASSERT( &c[i] == &m[i] );
	}
}

void testConstness()
{
	Messages m;
	std::vector<Messages> c;

	const size_t numMessages = 25;

	c.push_back( m );
	for( size_t i = 1; i < numMessages; ++i )
	{
		m.add( Message( IECore::MessageHandler::Level( i % 5 ), "testMessagesConstness", std::to_string( i ) ) );
		c.push_back( m );
	}

	for( size_t i = 1; i < numMessages; ++i )
	{
		GAFFERTEST_ASSERT( c[i].size() == i );
		GAFFERTEST_ASSERT( c[i][i-1].message == std::to_string( i ) );
		GAFFERTEST_ASSERT( c.back()[i-1].message == std::to_string( i ) );
	}

	m.clear();

	for( size_t i = 1; i < numMessages; ++i )
	{
		GAFFERTEST_ASSERT( c[i].size() == i );
		GAFFERTEST_ASSERT( c[i][i-1].message == std::to_string( i ) );
		GAFFERTEST_ASSERT( c.back()[i-1].message == std::to_string( i ) );
	}
}

} // namespace

void GafferTestModule::bindMessagesTest()
{
	def( "testMessagesCopyPerformance", &testCopyPerformance );
	def( "testMessagesAddPerformance", &testAddPerformance );
	def( "testMessagesValueReuse", &testValueReuse );
	def( "testMessagesConstness", &testConstness );
}
