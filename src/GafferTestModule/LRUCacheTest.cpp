//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "LRUCacheTest.h"

#include "GafferTest/Assert.h"

#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "IECore/Canceller.h"

#include "tbb/parallel_for.h"

using namespace IECorePreview;
using namespace boost::python;

namespace
{

// Nasty template jiggery-pokery that allows us to dispatch the same
// test code for difference LRUCache policies.
template<template<template<typename> class> class F>
struct DispatchTest
{

	template<typename... Args>
	void operator()( const std::string &policy, Args&&... args )
	{
		if( policy == "serial" )
		{
			F<LRUCachePolicy::Serial> f( std::forward<Args>( args )... );
			// Use an arena to limit any parallel TBB work to 1
			// thread, since Serial policy is not threadsafe.
			tbb::task_arena arena( 1 );
			arena.execute(
				[&f]{ f(); }
			);
		}
		else if( policy == "parallel" )
		{
			F<LRUCachePolicy::Parallel> f( std::forward<Args>( args )... ); f();
		}
		else if( policy == "taskParallel" )
		{
			F<LRUCachePolicy::TaskParallel> f( std::forward<Args>( args )... ); f();
		}
		else
		{
			GAFFERTEST_ASSERT( false );
		}
	}

};

template<template<typename> class Policy>
struct TestLRUCache
{

	TestLRUCache( int numIterations, int numValues, int maxCost, int clearFrequency )
		:	m_numIterations( numIterations ), m_numValues( numValues ), m_maxCost( maxCost ), m_clearFrequency( clearFrequency )
	{
	}

	void operator()()
	{
		typedef LRUCache<int, int, Policy> Cache;
		Cache cache(
			[]( int key, size_t &cost ) { cost = 1; return key; },
			m_maxCost
		);

		tbb::parallel_for(
			tbb::blocked_range<size_t>( 0, m_numIterations ),
			[&]( const tbb::blocked_range<size_t> &r ) {
				for( size_t i=r.begin(); i!=r.end(); ++i )
				{
					const int k = i % m_numValues;
					const int v = cache.get( k );
					GAFFERTEST_ASSERTEQUAL( v, k );

					if( m_clearFrequency && (i % m_clearFrequency == 0) )
					{
						cache.clear();
					}
				}
			}
		);
	}

	private :

		const int m_numIterations;
		const int m_numValues;
		const int m_maxCost;
		const int m_clearFrequency;

};

void testLRUCache( const std::string &policy, int numIterations, int numValues, int maxCost, int clearFrequency )
{
	DispatchTest<TestLRUCache>()( policy, numIterations, numValues, maxCost, clearFrequency );
}

template<template<typename> class Policy>
struct TestLRUCacheRemovalCallback
{

	void operator()()
	{
		std::vector<std::pair<int, int>> removed;

		typedef LRUCache<int, int, Policy> Cache;
		Cache cache(
			// Getter
			[]( int key, size_t &cost ) {
				cost = 1; return key * 2;
			},
			/* maxCost = */ 5,
			// Removal callback
			[&removed]( int key, int value ) {
				removed.push_back(
					std::make_pair( key, value )
				);
			}
		);

		GAFFERTEST_ASSERTEQUAL( cache.get( 1 ), 2 );
		GAFFERTEST_ASSERTEQUAL( removed.size(), 0 );

		GAFFERTEST_ASSERTEQUAL( cache.get( 2 ), 4 );
		GAFFERTEST_ASSERTEQUAL( removed.size(), 0 );

		GAFFERTEST_ASSERTEQUAL( cache.get( 3 ), 6 );
		GAFFERTEST_ASSERTEQUAL( removed.size(), 0 );

		GAFFERTEST_ASSERTEQUAL( cache.get( 4 ), 8 );
		GAFFERTEST_ASSERTEQUAL( removed.size(), 0 );

		GAFFERTEST_ASSERTEQUAL( cache.get( 5 ), 10 );
		GAFFERTEST_ASSERTEQUAL( removed.size(), 0 );

		GAFFERTEST_ASSERTEQUAL( cache.get( 6 ), 12 );
		GAFFERTEST_ASSERTEQUAL( removed.size(), 1 );

		GAFFERTEST_ASSERTEQUAL( cache.get( 7 ), 14 );
		GAFFERTEST_ASSERTEQUAL( removed.size(), 2 );

		cache.clear();

		GAFFERTEST_ASSERTEQUAL( removed.size(), 7 );

		for( int i = 1; i < 8; ++i )
		{
			GAFFERTEST_ASSERTEQUAL(
				std::count(
					removed.begin(), removed.end(),
					std::make_pair( i, i * 2 )
				),
				1
			);
		}
	}

};

void testLRUCacheRemovalCallback( const std::string &policy )
{
	DispatchTest<TestLRUCacheRemovalCallback>()( policy );
}

template<template<typename> class Policy>
struct TestLRUCacheContentionForOneItem
{

	void operator()()
	{
		typedef LRUCache<int, int, Policy> Cache;
		Cache cache(
			[]( int key, size_t &cost ) { cost = 1; return key; },
			100
		);

		tbb::parallel_for(
			tbb::blocked_range<size_t>( 0, 10000000 ),
			[&]( const tbb::blocked_range<size_t> &r ) {
				for( size_t i = r.begin(); i < r.end(); ++i )
				{
					GAFFERTEST_ASSERTEQUAL( cache.get( 1 ), 1 );
				}
			}
		);
	}


};

void testLRUCacheContentionForOneItem( const std::string &policy )
{
	DispatchTest<TestLRUCacheContentionForOneItem>()( policy );
}

template<template<typename> class Policy>
struct TestLRUCacheRecursion
{

	TestLRUCacheRecursion( int numIterations, int numValues, int maxCost )
		:	m_numIterations( numIterations ), m_numValues( numValues ), m_maxCost( maxCost )
	{
	}

	void operator()()
	{
		typedef LRUCache<int, int, Policy> Cache;
		typedef std::unique_ptr<Cache> CachePtr;

		CachePtr cache;
		cache.reset(
			new Cache(
				// Getter that calls back into the cache with a different key.
				[&cache]( int key, size_t &cost ) {
					cost = 1;
					switch( key )
					{
						case 0 :
							return 0;
						case 1 :
						case 2 :
							return 1;
						default :
							return cache->get( key - 1 ) + cache->get( key - 2 );
					}
				},
				m_maxCost
			)
		);

		GAFFERTEST_ASSERTEQUAL( cache->get( 40 ), 102334155 );
		cache->clear();

		tbb::parallel_for(
			tbb::blocked_range<size_t>( 0, m_numIterations ),
			[&]( const tbb::blocked_range<size_t> &r ) {
				for( size_t i = r.begin(); i < r.end(); ++i )
				{
					cache->get( i % m_numValues );
				}
			}
		);

	}

	private :

		const int m_numIterations;
		const int m_numValues;
		const int m_maxCost;

};

void testLRUCacheRecursion( const std::string &policy, int numIterations, size_t numValues, int maxCost )
{
	DispatchTest<TestLRUCacheRecursion>()( policy, numIterations, numValues, maxCost );
}

template<template<typename> class Policy>
struct TestLRUCacheRecursionOnOneItem
{

	void operator()()
	{
		typedef LRUCache<int, int, Policy> Cache;
		typedef std::unique_ptr<Cache> CachePtr;
		int recursionDepth = 0;

		CachePtr cache;
		cache.reset(
			new Cache(
				// Getter that calls back into the cache with the _same_
				// key, up to a certain limit, and then actually returns
				// a value. This is basically insane, but it models
				// situations that can occur in Gaffer.
				[&cache, &recursionDepth]( int key, size_t &cost ) {
					cost = 1;
					if( ++recursionDepth == 100 )
					{
						return key;
					}
					else
					{
						return cache->get( key );
					}
				},
				// Max cost is small enough that we'll be trying to evict
				// keys while unwinding the recursion.
				20
			)
		);

		GAFFERTEST_ASSERTEQUAL( cache->currentCost(), 0 );
		GAFFERTEST_ASSERTEQUAL( cache->get( 1 ), 1 );
		GAFFERTEST_ASSERTEQUAL( recursionDepth, 100 );
		GAFFERTEST_ASSERTEQUAL( cache->currentCost(), 1 );
	}

};

void testLRUCacheRecursionOnOneItem( const std::string &policy )
{
	DispatchTest<TestLRUCacheRecursionOnOneItem>()( policy );
}

template<template<typename> class Policy>
struct TestLRUCacheClearFromGet
{

	void operator()()
	{
		typedef IECorePreview::LRUCache<int, int, Policy> Cache;
		typedef std::unique_ptr<Cache> CachePtr;

		CachePtr cache;
		cache.reset(
			new Cache(
				// Calling `clear()` from inside a getter is basically insane. But it can happen
				// in Gaffer, because `get()` might trigger arbitrary python, arbitrary python
				// might trigger garbage collection, garbage collection might destroy a plug,
				// and destroying a plug clears the cache.
				[&cache]( int key, size_t &cost ) { cache->clear(); cost = 1; return key; },
				100
			)
		);

		GAFFERTEST_ASSERTEQUAL( cache->get( 0 ), 0 );
	}

};

void testLRUCacheClearFromGet( const std::string &policy )
{
	DispatchTest<TestLRUCacheClearFromGet>()( policy );
}

template<template<typename> class Policy>
struct TestLRUCacheExceptions
{

	void operator()()
	{
		std::vector<int> calls;

		typedef IECorePreview::LRUCache<int, int, Policy> Cache;
		Cache cache(
			[&calls]( int key, size_t &cost ) {
				calls.push_back( key );
				throw IECore::Exception( boost::str(
					boost::format( "Get failed for %1%" ) % key
				) );
				return 0;
			},
			1000
		);

		// Check that the exception thrown by the getter propagates back out to us.

		bool caughtException = false;
		try
		{
			cache.get( 10 );
		}
		catch( const IECore::Exception &e )
		{
			caughtException = true;
			GAFFERTEST_ASSERTEQUAL(
				e.what(),
				std::string( "Get failed for 10" )
			);
		}

		GAFFERTEST_ASSERT( caughtException );
		GAFFERTEST_ASSERTEQUAL( calls.size(), 1 );
		GAFFERTEST_ASSERTEQUAL( calls.back(), 10 );

		// Check that calling a second time gives us the same error, but without
		// calling the getter again.

		caughtException = false;
		try
		{
			cache.get( 10 );
		}
		catch( const IECore::Exception &e )
		{
			caughtException = true;
			GAFFERTEST_ASSERTEQUAL(
				e.what(),
				std::string( "Get failed for 10" )
			);
		}

		GAFFERTEST_ASSERT( caughtException );
		GAFFERTEST_ASSERTEQUAL( calls.size(), 1 );

		// Check that clear erases exceptions, so that the getter will be called again.

		cache.clear();

		caughtException = false;
		try
		{
			cache.get( 10 );
		}
		catch( const IECore::Exception &e )
		{
			caughtException = true;
			GAFFERTEST_ASSERTEQUAL(
				e.what(),
				std::string( "Get failed for 10" )
			);
		}

		GAFFERTEST_ASSERT( caughtException );
		GAFFERTEST_ASSERTEQUAL( calls.size(), 2 );
		GAFFERTEST_ASSERTEQUAL( calls.back(), 10 );

		// And check that erase does the same.
		cache.erase( 10 );

		caughtException = false;
		try
		{
			cache.get( 10 );
		}
		catch( const IECore::Exception &e )
		{
			caughtException = true;
			GAFFERTEST_ASSERTEQUAL(
				e.what(),
				std::string( "Get failed for 10" )
			);
		}

		GAFFERTEST_ASSERT( caughtException );
		GAFFERTEST_ASSERTEQUAL( calls.size(), 3 );
		GAFFERTEST_ASSERTEQUAL( calls.back(), 10 );

		// Check that if we don't cache errors, then it gets called twice
		calls.clear();
		Cache noErrorsCache(
			[&calls]( int key, size_t &cost ) {
				calls.push_back( key );
				throw IECore::Exception( boost::str(
					boost::format( "Get failed for %1%" ) % key
				) );
				return 0;
			},
			1000,
			typename Cache::RemovalCallback(),
			/* cacheErrors = */ false
		);

		caughtException = false;
		try
		{
			noErrorsCache.get( 10 );
		}
		catch( const IECore::Exception &e )
		{
			caughtException = true;
			GAFFERTEST_ASSERTEQUAL(
				e.what(),
				std::string( "Get failed for 10" )
			);
		}

		GAFFERTEST_ASSERT( caughtException );
		GAFFERTEST_ASSERTEQUAL( calls.size(), 1 );

		caughtException = false;
		try
		{
			noErrorsCache.get( 10 );
		}
		catch( const IECore::Exception &e )
		{
			caughtException = true;
			GAFFERTEST_ASSERTEQUAL(
				e.what(),
				std::string( "Get failed for 10" )
			);
		}

		GAFFERTEST_ASSERT( caughtException );
		GAFFERTEST_ASSERTEQUAL( calls.size(), 2 );
	}

};

void testLRUCacheExceptions( const std::string &policy )
{
	DispatchTest<TestLRUCacheExceptions>()( policy );
}

template<template<typename> class Policy>
struct TestLRUCacheCancellation
{

	void operator()()
	{
		std::vector<int> calls;

		typedef std::unique_ptr<IECore::Canceller> CancellerPtr;
		CancellerPtr canceller;
		canceller.reset( new IECore::Canceller() );

		typedef IECorePreview::LRUCache<int, int, Policy> Cache;
		Cache cache(
			[&calls, &canceller]( int key, size_t &cost ) {
				calls.push_back( key );
				IECore::Canceller::check( canceller.get() );
				return key;
			},
			1000
		);

		// Check normal operation

		GAFFERTEST_ASSERTEQUAL( cache.get( 1 ), 1 );
		GAFFERTEST_ASSERTEQUAL( cache.get( 2 ), 2 );

		GAFFERTEST_ASSERTEQUAL( calls.size(), 2 );
		GAFFERTEST_ASSERTEQUAL( calls[0], 1 );
		GAFFERTEST_ASSERTEQUAL( calls[1], 2 );

		// Check cancellation is not handled in the same way as a normal
		// exception, and will simply get the value again for subsequent
		// lookups.

		canceller->cancel();

		bool caughtCancel = false;
		int val = -1;
		try
		{
			val = cache.get( 3 );
		}
		catch( IECore::Cancelled const &c )
		{
			caughtCancel = true;
		}

		GAFFERTEST_ASSERT( caughtCancel );
		GAFFERTEST_ASSERTEQUAL( val, -1 );

		GAFFERTEST_ASSERTEQUAL( calls.size(), 3 );
		GAFFERTEST_ASSERTEQUAL( calls.back(), 3 );

		// reset and check that we get called again

		canceller.reset( new IECore::Canceller() );

		val = cache.get( 3 );

		GAFFERTEST_ASSERTEQUAL( val, 3 );
		GAFFERTEST_ASSERTEQUAL( calls.size(), 4 );
		GAFFERTEST_ASSERTEQUAL( calls.back(), 3 );

	}

};

void testLRUCacheCancellation( const std::string &policy )
{
	DispatchTest<TestLRUCacheCancellation>()( policy );
}

} // namespace

void GafferTestModule::bindLRUCacheTest()
{
	def( "testLRUCache", &testLRUCache, ( arg( "numIterations" ), arg( "numValues" ), arg( "maxCost" ), arg( "clearFrequency" ) = 0 ) );
	def( "testLRUCacheRemovalCallback", &testLRUCacheRemovalCallback );
	def( "testLRUCacheContentionForOneItem", &testLRUCacheContentionForOneItem );
	def( "testLRUCacheRecursion", &testLRUCacheRecursion, ( arg( "numIterations" ), arg( "numValues" ), arg( "maxCost" ) ) );
	def( "testLRUCacheRecursionOnOneItem", &testLRUCacheRecursionOnOneItem );
	def( "testLRUCacheClearFromGet", &testLRUCacheClearFromGet );
	def( "testLRUCacheExceptions", &testLRUCacheExceptions );
	def( "testLRUCacheCancellation", &testLRUCacheCancellation );
}
