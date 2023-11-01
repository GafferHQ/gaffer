//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#include "boost/python.hpp"

#include "ProcessTest.h"

#include "GafferTest/Assert.h"

#include "Gaffer/Context.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/Private/IECorePreview/LRUCache.h"
#include "Gaffer/Process.h"

#include "IECorePython/ScopedGILRelease.h"

#include "tbb/parallel_for_each.h"

using namespace boost::python;
using namespace IECore;
using namespace Gaffer;

namespace
{

struct Dependencies : public IECore::RefCounted
{
	IE_CORE_DECLAREMEMBERPTR( Dependencies );
	using Map = std::map<int, ConstPtr>;
	Map map;
};

// Test Process
// ============
//
// This Process subclass is used primarily to test the collaboration mechanism
// provided by `Process::acquireCollaborativeResult()`. The result is an integer
// which is given to the TestProcess directly, and which also provides the cache
// key. The upstream dependencies are also given verbatim to TestProcess as a
// nested dictionary of integers mapping from the result for each dependency to
// the dictionary for _its_ upstream dependencies. Non-negative results are
// computed using `acquireCollaborativeResult()` and negative results are
// computed by constructing a TestProcess directly. This mechanism lets us
// create a variety of process graphs very explicitly from ProcessTestCase.
class TestProcess : public Process
{

	public :

		TestProcess( const Plug *plug, int result, const Dependencies::ConstPtr &dependencies )
			:	Process( g_staticType, plug, plug ), m_result( result ), m_dependencies( dependencies )
		{
		}

		using ResultType = int;

		ResultType run() const
		{
			const ThreadState &threadState = ThreadState::current();
			tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );

			tbb::parallel_for_each(

				m_dependencies->map.begin(), m_dependencies->map.end(),

				[&] ( const Dependencies::Map::value_type &dependency ) {

					ThreadState::Scope scope( threadState );
					const int expectedResult = dependency.first;

					const Plug *p = plug();
					if( const Plug *input = p->getInput() )
					{
						// Compute the dependencies using the plug's input if it
						// has one, otherwise using this plug. The only reason
						// for using an input is get more fine-grained information
						// from the Monitors used in the unit tests (because they
						// capture statistics per plug).
						p = input;
					}

					int actualResult;
					if( expectedResult >= 0 )
					{
						actualResult = Process::acquireCollaborativeResult<TestProcess>( expectedResult, p, expectedResult, dependency.second );
					}
					else
					{
						actualResult = TestProcess( p, expectedResult, dependency.second ).run();
					}
					GAFFERTEST_ASSERTEQUAL( actualResult, expectedResult );

				},

				taskGroupContext

			);

			return m_result;
		}

		using CacheType = IECorePreview::LRUCache<int, int, IECorePreview::LRUCachePolicy::Parallel>;
		static CacheType g_cache;

		static size_t cacheCostFunction( int value )
		{
			return 1;
		}

	private :

		const int m_result;
		const Dependencies::ConstPtr m_dependencies;

		static const IECore::InternedString g_staticType;

};

TestProcess::CacheType TestProcess::g_cache( TestProcess::CacheType::GetterFunction(), 100000 );
// Spoof type so that we can use PerformanceMonitor to check we get the processes we expect in ProcessTest.py.
const IECore::InternedString TestProcess::g_staticType( "computeNode:compute" );

Dependencies::ConstPtr dependenciesFromDict( dict dependenciesDict, std::unordered_map<const PyObject *, Dependencies::ConstPtr> &converted )
{
	auto it = converted.find( dependenciesDict.ptr() );
	if( it != converted.end() )
	{
		return it->second;
	}

	Dependencies::Ptr result = new Dependencies;
	auto items = dependenciesDict.items();
	for( size_t i = 0, l = len( items ); i < l; ++i )
	{
		int v = extract<int>( items[i][0] );
		dict d = extract<dict>( items[i][1] );
		result->map[v] = dependenciesFromDict( d, converted );
	}

	converted[dependenciesDict.ptr()] = result;
	return result;
}

void runTestProcess( const Plug *plug, int expectedResult, dict dependenciesDict )
{
	std::unordered_map<const PyObject *, Dependencies::ConstPtr> convertedDependencies;
	Dependencies::ConstPtr dependencies = dependenciesFromDict( dependenciesDict, convertedDependencies );

	Context::EditableScope context( Context::current() );
	int result = TestProcess( plug, expectedResult, dependencies ).run();
	GAFFERTEST_ASSERTEQUAL( result, expectedResult );
}

void clearTestProcessCache()
{
	TestProcess::g_cache.clear();
}

} // namespace

void GafferTestModule::bindProcessTest()
{
	def( "runTestProcess", &runTestProcess );
	def( "clearTestProcessCache", &clearTestProcessCache );
}
