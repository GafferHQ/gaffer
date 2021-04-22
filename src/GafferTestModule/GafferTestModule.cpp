//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferBindings/DependencyNodeBinding.h"

#include "GafferTest/ComputeNodeTest.h"
#include "GafferTest/ContextTest.h"
#include "GafferTest/DownstreamIteratorTest.h"
#include "GafferTest/FilteredRecursiveChildIteratorTest.h"
#include "GafferTest/MetadataTest.h"
#include "GafferTest/MultiplyNode.h"
#include "GafferTest/RandomTest.h"
#include "GafferTest/RecursiveChildIteratorTest.h"

#include "LRUCacheTest.h"
#include "TaskMutexTest.h"
#include "ValuePlugTest.h"
#include "MessagesTest.h"

#include "IECorePython/ScopedGILRelease.h"

using namespace boost::python;
using namespace GafferTest;
using namespace GafferTestModule;

static void testMetadataThreadingWrapper()
{
	IECorePython::ScopedGILRelease gilRelease;
	testMetadataThreading();
}

static boost::python::tuple countContextHash32CollisionsWrapper( int entries, int mode, int seed )
{
	IECorePython::ScopedGILRelease gilRelease;
	auto result = countContextHash32Collisions( entries, mode, seed );
	return boost::python::make_tuple( std::get<0>(result), std::get<1>(result), std::get<2>(result), std::get<3>(result) );
}

BOOST_PYTHON_MODULE( _GafferTest )
{

	GafferBindings::DependencyNodeClass<MultiplyNode>()
		.def( init<const char *, bool>(
				(
					boost::python::arg_( "name" ),
					boost::python::arg_( "brokenAffects" )=false
				)
			)
		);


	def( "testRecursiveChildIterator", &testRecursiveChildIterator );
	def( "testFilteredRecursiveChildIterator", &testFilteredRecursiveChildIterator );
	def( "testMetadataThreading", &testMetadataThreadingWrapper );
	def( "testManyContexts", &testManyContexts );
	def( "testManySubstitutions", &testManySubstitutions );
	def( "testManyEnvironmentSubstitutions", &testManyEnvironmentSubstitutions );
	def( "testScopingNullContext", &testScopingNullContext );
	def( "testEditableScope", &testEditableScope );
	def( "countContextHash32Collisions", &countContextHash32CollisionsWrapper );
	def( "testContextHashPerformance", &testContextHashPerformance );
	def( "testContextCopyPerformance", &testContextCopyPerformance );
	def( "testCopyEditableScope", &testCopyEditableScope );
	def( "testContextHashValidation", &testContextHashValidation );
	def( "testComputeNodeThreading", &testComputeNodeThreading );
	def( "testDownstreamIterator", &testDownstreamIterator );
	def( "testRandomPerf", &testRandomPerf );

	bindTaskMutexTest();
	bindLRUCacheTest();
	bindValuePlugTest();
	bindMessagesTest();

}
