//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2007-2014, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2012, John Haddon. All rights reserved.
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
//     * Neither the name of Image Engine Design nor the names of any
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

#pragma once

#include "Gaffer/Private/IECorePreview/TaskMutex.h"

#include "IECore/Canceller.h"
#include "IECore/Exception.h"

#include "boost/multi_index/hashed_index.hpp"
#include "boost/multi_index/member.hpp"
#include "boost/multi_index/sequenced_index.hpp"
#include "boost/multi_index_container.hpp"
#include "boost/unordered_map.hpp"

#include "tbb/spin_mutex.h"
#include "tbb/spin_rw_mutex.h"

#include <cassert>
#include <iostream>
#include <tuple>
#include <vector>

namespace IECorePreview
{

// Policies
// =======================================================================
//
// The policies are responsible for implementing the principle
// data structures of the cache. Conceptually they contain a mapping from
// Key to CacheEntry and a separate list sorted in least-recently-used order.
// In practice, any data structure can be used provided the interface
// described below is presented. The required interface is documented
// on the Serial policy only for simplicity.
namespace LRUCachePolicy
{

enum AcquireMode
{
	FindReadable,
	FindWritable,
	// Writability of handle is determined
	// by CacheEntry status - writable if
	// Uncached and read only otherwise.
	Insert,
	InsertWritable
};


// Uses a boost::multi_index_container to implement a map
// and list in a single container. This gives much improved
// performance over separate containers because it halves the
// allocations needed, and moving items within the list doesn't
// require any allocation at all. We keep the list in exact LRU
// order.
template<typename LRUCache>
class Serial
{

	public :

		using CacheEntry = typename LRUCache::CacheEntry;
		using Key = typename LRUCache::KeyType;

		struct Item
		{
			Item( const Key &key )
				:	key( key ), handleCount( 0 )
			{
			}

			Key key;
			// multi_index_containers have const elements
			// so you can't modify something being used as
			// as key. we know that cacheEntry is not used
			// as a key, so can safely make it mutable to
			// get non-const access to it.
			mutable CacheEntry cacheEntry;
			mutable size_t handleCount;
		};

		using MapAndList = boost::multi_index_container<
			Item,
			boost::multi_index::indexed_by<
				// First index is equivalent to std::unordered_map,
				// using Item::key as the key.
				boost::multi_index::hashed_unique<
					boost::multi_index::member<Item, Key, &Item::key>
				>,
				// Second index is equivalent to std::list.
				boost::multi_index::sequenced<>
			>
		>;

		using MapIterator = typename MapAndList::iterator;
		using List = typename MapAndList::template nth_index<1>::type;

		Serial()
			:	currentCost( 0 )
		{
		}

		// The Handle class provides controlled access to
		// a CacheEntry stored within the policy. Handles
		// provide read and possibly write access to the
		// CacheEntry, depending on how they have been
		// acquired. The Handle must be kept alive for as
		// long as the CacheEntry is accessed.
		struct Handle : private boost::noncopyable
		{

			Handle()
				:	m_inited( false )
			{
			}

			~Handle()
			{
				release();
			}

			// Read access to the underlying cache entry.
			const CacheEntry &readable()
			{
				return m_it->cacheEntry;
			}

			// Write access to the underlying cache entry.
			// Note that write access is not always permitted
			// - see documentation for `isWritable()`.
			CacheEntry &writable()
			{
				return m_it->cacheEntry;
			}

			// Returns true if it is OK to call `writable()`.
			// This is typically determined by the AcquireMode
			// passed to `acquire()`, with special cases for
			// recursion.
			bool isWritable() const
			{
				// Because this policy is serial, it would technically
				// always be OK to write. But we return false for recursive
				// calls to avoid unnecessary overhead updating the LRU list
				// for inner calls.
				/// \todo Is this distinction worth it, and do we really need
				/// to support recursion on a single item in the Serial policy?
				/// This is a remnant of a more complex system that allowed recursion
				/// in the TaskParallel policy, but that has since been removed.
				return m_it->handleCount == 1;
			}

			// Executes the functor F. This is used to
			// execute the GetterFunction, and allows the
			// TaskParallel policy to support work sharing.
			template<typename F>
			void execute( F &&f )
			{
				f();
			}

			void release()
			{
				if( m_inited )
				{
					assert( m_it->handleCount );
					m_it->handleCount--;
					m_inited = false;
				}
			}

			private :

				void init( MapIterator it )
				{
					assert( !m_inited );
					m_it = it;
					m_it->handleCount++;
					m_inited = true;
				}

				friend class Serial;
				MapIterator m_it;
				bool m_inited;

		};

		// Acquires a handle for the given key. Whether the
		// handle is writable or not is determined by the AcquireMode.
		// Returns true on success and false if no entry was
		// found.
		bool acquire( const Key &key, Handle &handle, AcquireMode mode, const IECore::Canceller *canceller )
		{
			if( mode == Insert || mode == InsertWritable )
			{
				// Inserting via the map index automatically puts the new item
				// at the back of the list.
				std::pair<MapIterator, bool> i = m_mapAndList.insert( Item( key ) );
				handle.init( i.first );
				return true;
			}
			else
			{
				assert( mode == FindReadable || mode == FindWritable );
				MapIterator it = m_mapAndList.find( key );
				if( it == m_mapAndList.end() )
				{
					return false;
				}
				handle.init( it );
				return true;
			}
		}

		// Marks the CacheEntry referred to by the handle as recently
		// used.
		void push( Handle &handle )
		{
			List &list = m_mapAndList.template get<1>();
			list.relocate( list.end(), list.iterator_to( *(handle.m_it) ) );
		}

		// Pops a copy of the least recently used CacheEntry from the policy,
		// removing it from the internal storage. Returns true for success
		// and false for failure.
		bool pop( Key &key, CacheEntry &cacheEntry )
		{
			List &list = m_mapAndList.template get<1>();

			// Find the first item that doesn't have a handle
			// referring to it. Although we don't support threaded
			// access, there may still be existing handles if the
			// GetterFunction has reentered the cache with a call
			// to `get( someOtherKey )`, and this inner call has
			// then entered `limitCost()`.
			typename List::iterator it = list.begin();
			while( it != list.end() && it->handleCount )
			{
				++it;
			}

			if( it == list.end() )
			{
				return false;
			}

			const Item &item = *it;

			key = item.key;
			cacheEntry = item.cacheEntry;

			list.erase( it );

			return true;
		}

		typename LRUCache::Cost currentCost;

	private :

		MapAndList m_mapAndList;

};

// Uses a binned map to allow concurrent map operations, and
// uses a second-chance algorithm to avoid the serial operations
// associated with managing an LRU list.
template<typename LRUCache>
class Parallel
{

	public :

		using CacheEntry = typename LRUCache::CacheEntry;
		using Key = typename LRUCache::KeyType;
		using AtomicCost = std::atomic<typename LRUCache::Cost>;

		struct Item
		{
			Item() : recentlyUsed() {}
			Item( const Key &key ) : key( key ), recentlyUsed() {}
			Item( const Item &other ) : key( other.key ), cacheEntry( other.cacheEntry ), recentlyUsed() {}
			Key key;
			mutable CacheEntry cacheEntry;
			// Mutex to protect cacheEntry.
			using Mutex = tbb::spin_rw_mutex;
			mutable Mutex mutex;
			// Flag used in second-chance algorithm.
			mutable std::atomic_bool recentlyUsed;
		};

		// We would love to use one of TBB's concurrent containers as
		// our map, but we need the ability to insert, erase and iterate
		// concurrently. The concurrent_unordered_map doesn't provide
		// concurrent erase, and the concurrent_hash_map doesn't provide
		// concurrent iteration. Instead we choose a non-threadsafe
		// container, but split our storage into multiple bins with a
		// container in each bin. This way concurrent operations do not
		// contend on a lock unless they happen to target the same bin.
		using Map = boost::multi_index::multi_index_container<
			Item,
			boost::multi_index::indexed_by<
				// Equivalent to std::unordered_map, using Item::key
				// as the key. This actually has a couple of benefits
				// over std::unordered_map :
				//
				// - Insertion does not invalidate existing iterators.
				//   This allows us to store m_popIterator.
				// - Lookup can be performed using types other than the
				//   key. This provides the possibility of creating a
				//   prehashed key prior to taking a Bin lock, although
				//   this is not implemented here yet.
				boost::multi_index::hashed_unique<
					boost::multi_index::member<Item, Key, &Item::key>
				>
			>
		>;

		using MapIterator = typename Map::iterator;

		struct Bin
		{
			Bin() {}
			Bin( const Bin &other ) : map( other.map ) {}
			Bin &operator = ( const Bin &other ) { map = other.map; return *this; }
			Map map;
			using Mutex = tbb::spin_rw_mutex;
			Mutex mutex;
		};

		using Bins = std::vector<Bin>;

		Parallel()
		{
			m_bins.resize( std::thread::hardware_concurrency() );
			m_popBinIndex = 0;
			m_popIterator = m_bins[0].map.begin();
			currentCost = 0;
		}

		struct Handle : private boost::noncopyable
		{

			Handle()
				:	m_item( nullptr ), m_writable( false )
			{
			}

			~Handle()
			{
			}

			const CacheEntry &readable()
			{
				return m_item->cacheEntry;
			}

			CacheEntry &writable()
			{
				assert( m_writable );
				return m_item->cacheEntry;
			}

			bool isWritable() const
			{
				return m_writable;
			}

			template<typename F>
			void execute( F &&f )
			{
				f();
			}

			void release()
			{
				if( m_item )
				{
					m_itemLock.release();
					m_item = nullptr;
				}
			}

			private :

				bool acquire( Bin &bin, const Key &key, AcquireMode mode, const IECore::Canceller *canceller )
				{
					assert( !m_item );

					// Acquiring a handle requires taking two
					// locks, first the lock for the Bin, and
					// second the lock for the Item. We must be
					// careful to avoid deadlock in the case of
					// a GetterFunction which reenters the cache.

					typename Bin::Mutex::scoped_lock binLock;
					while( true )
					{
						// Acquire a lock on the bin, and get an iterator
						// from the key. We optimistically assume the item
						// may already be in the cache and first do a find()
						// using a bin read lock. This gives us much better
						// performance when many threads contend for items
						// that are already in the cache.
						binLock.acquire( bin.mutex, /* write = */ false );
						MapIterator it = bin.map.find( key );
						bool inserted = false;
						if( it == bin.map.end() )
						{
							if( mode != Insert && mode != InsertWritable )
							{
								return false;
							}
							binLock.upgrade_to_writer();
							std::tie<MapIterator, bool>( it, inserted ) = bin.map.insert( Item( key ) );
						}
						// Now try to get a lock on the item we want to
						// acquire. When we've just inserted a new item
						// we take a write lock directly, because we know
						// we'll need to write to the new item. When insertion
						// found a pre-existing item we optimistically take
						// just a read lock, because it is faster when
						// many threads just need to read from the same
						// cached item.
						m_writable = inserted || mode == FindWritable || mode == InsertWritable;

						if( m_itemLock.try_acquire( it->mutex, /* write = */ m_writable ) )
						{
							if( !m_writable && mode == Insert && it->cacheEntry.status() == LRUCache::Uncached )
							{
								// We found an old item that doesn't have a
								// value. This can either be because it was
								// erased but hasn't been popped yet, or because
								// the item was too big to fit in the cache. We
								// need to get writer status so it can be
								// updated in `get()`, but we can't use the obvious
								// `m_itemLock.upgrade_to_writer()` call as it can
								// lead to deadlock. So we must retry using
								// InsertWritable instead.
								mode = InsertWritable;
								m_itemLock.release();
								binLock.release();
								continue;
							}
							// Success!
							m_item = &*it;
							return true;
						}
						else
						{
							// The Item lock is held by another thread.
							// We must release the Bin lock and retry. This
							// avoids deadlock when the GetterFunction holding
							// the Item lock calls back into the cache and tries to
							// access another item in the same Bin.
							binLock.release();
						}
						// Check for cancellation before trying again. We could
						// be waiting a while, and our caller may have lost interest
						// in the meantime.
						IECore::Canceller::check( canceller );
					}
				}

				friend class Parallel;

				const Item *m_item;
				typename Item::Mutex::scoped_lock m_itemLock;
				bool m_writable;

		};

		bool acquire( const Key &key, Handle &handle, AcquireMode mode, const IECore::Canceller *canceller )
		{
			return handle.acquire( bin( key ), key, mode, canceller );
		}

		void push( Handle &handle )
		{
			// Simply mark the item as having been used
			// recently. We will then give it a second chance
			// in pop(), so it will not be evicted immediately.
			// We don't need the handle to be writable to write
			// here, because `recentlyUsed` is atomic.
			handle.m_item->recentlyUsed.store( true, std::memory_order_release );
		}

		bool pop( Key &key, CacheEntry &cacheEntry )
		{
			// Popping works by iterating the map until an item
			// that has not been recently used is found. We store
			// the current iteration position as m_popIterator and
			// protect it with m_popMutex, taking the position that
			// it is sufficient for only one thread to be limiting
			// cost at any given time.
			PopMutex::scoped_lock lock;
			if( !lock.try_acquire( m_popMutex ) )
			{
				return false;
			}

			Bin *bin = &m_bins[m_popBinIndex];
			typename Bin::Mutex::scoped_lock binLock( bin->mutex );

			typename Item::Mutex::scoped_lock itemLock;
			int numFullIterations = 0;
			while( true )
			{
				// If we're at the end of this bin, advance to
				// the next non-empty one.
				const MapIterator emptySentinel = bin->map.end();
				while( m_popIterator == bin->map.end() )
				{
					binLock.release();
					m_popBinIndex = ( m_popBinIndex + 1 ) % m_bins.size();
					bin = &m_bins[m_popBinIndex];
					binLock.acquire( bin->mutex );
					m_popIterator = bin->map.begin();
					if( m_popIterator == emptySentinel )
					{
						// We've come full circle and all bins were empty.
						return false;
					}
					else if( m_popBinIndex == 0 )
					{
						if( numFullIterations++ > 50 )
						{
							// We're not empty, but we've been around and around
							// without finding anything to pop. This could happen
							// if other threads are frantically setting
							// the `recentlyUsed` flag or if `clear()` is
							// called from `get()`, while `get()` holds the lock
							// on the only item we could pop.
							return false;
						}
					}
				}

				if( itemLock.try_acquire( m_popIterator->mutex ) )
				{
					if( !m_popIterator->recentlyUsed.load( std::memory_order_acquire ) )
					{
						// Pop this item.
						key = m_popIterator->key;
						cacheEntry = m_popIterator->cacheEntry;
						// Now erase it from the bin.
						// We must release the lock on the Item before erasing it,
						// because we cannot release a lock on a mutex that is
						// already destroyed. We know that no other thread can
						// gain access to the item though, because they must
						// acquire the Bin lock to do so, and we still hold the
						// Bin lock.
						itemLock.release();
						m_popIterator = bin->map.erase( m_popIterator );
						return true;
					}
					else
					{
						// Item has been used recently. Flag it so we
						// can pop it next time round, unless another
						// thread resets the flag.
						m_popIterator->recentlyUsed.store( false, std::memory_order_release );
						itemLock.release();
					}
				}
				else
				{
					// Failed to acquire the item lock. Some other
					// thread is busy with this item, so we consider
					// it to be recently used and just skip over it.
				}

				++m_popIterator;
			}
		}

		AtomicCost currentCost;

	private :

		Bins m_bins;

		Bin &bin( const Key &key )
		{
			// Note : `testLRUCacheUncacheableItem()` requires keys to share
			// a bin, and needs updating if the indexing strategy changes.
			size_t binIndex = boost::hash<Key>()( key ) % m_bins.size();
			return m_bins[binIndex];
		};

		using PopMutex = tbb::spin_mutex;
		PopMutex m_popMutex;
		size_t m_popBinIndex;
		MapIterator m_popIterator;

};


/// Used to determine if `GetterFunction( key )` will spawn tasks.
/// If it is specialised to return false for certain keys, then
/// some significant TBB task sharing overhead is avoided.
template<typename Key>
bool spawnsTasks( const Key &key )
{
	return true;
}

/// Thread-safe policy that uses TaskMutex so that threads waiting on
/// the cache can still perform useful work.
/// \todo This uses the same binned approach to map storage as the
/// standard Parallel policy. Can we share the code by introducing some
/// sort of ConcurrentBinnedMap? Alternatively, should we just replace
/// the Parallel policy with the TaskParallel one?
template<typename LRUCache>
class TaskParallel
{

	public :

		using CacheEntry = typename LRUCache::CacheEntry;
		using Key = typename LRUCache::KeyType;
		using AtomicCost = std::atomic<typename LRUCache::Cost>;

		struct Item
		{
			Item() : recentlyUsed() {}
			Item( const Key &key ) : key( key ), recentlyUsed() {}
			Item( const Item &other ) : key( other.key ), cacheEntry( other.cacheEntry ), recentlyUsed() {}
			Key key;
			mutable CacheEntry cacheEntry;
			// Mutex to protect cacheEntry.
			using Mutex = TaskMutex;
			mutable Mutex mutex;
			// Flag used in second-chance algorithm.
			mutable std::atomic_bool recentlyUsed;
		};

		// We would love to use one of TBB's concurrent containers as
		// our map, but we need the ability to insert, erase and iterate
		// concurrently. The concurrent_unordered_map doesn't provide
		// concurrent erase, and the concurrent_hash_map doesn't provide
		// concurrent iteration. Instead we choose a non-threadsafe
		// container, but split our storage into multiple bins with a
		// container in each bin. This way concurrent operations do not
		// contend on a lock unless they happen to target the same bin.
		using Map = boost::multi_index::multi_index_container<
			Item,
			boost::multi_index::indexed_by<
				// Equivalent to std::unordered_map, using Item::key
				// as the key. This actually has a couple of benefits
				// over std::unordered_map :
				//
				// - Insertion does not invalidate existing iterators.
				//   This allows us to store m_popIterator.
				// - Lookup can be performed using types other than the
				//   key. This provides the possibility of creating a
				//   prehashed key prior to taking a Bin lock, although
				//   this is not implemented here yet.
				boost::multi_index::hashed_unique<
					boost::multi_index::member<Item, Key, &Item::key>
				>
			>
		>;

		using MapIterator = typename Map::iterator;

		struct Bin
		{
			Bin() {}
			Bin( const Bin &other ) : map( other.map ) {}
			Bin &operator = ( const Bin &other ) { map = other.map; return *this; }
			Map map;
			using Mutex = tbb::spin_rw_mutex;
			Mutex mutex;
		};

		using Bins = std::vector<Bin>;

		TaskParallel()
		{
			m_bins.resize( std::thread::hardware_concurrency() );
			m_popBinIndex = 0;
			m_popIterator = m_bins[0].map.begin();
			currentCost = 0;
		}

		struct Handle : private boost::noncopyable
		{

			Handle()
				:	m_item( nullptr ), m_spawnsTasks( false )
			{
			}

			~Handle()
			{
			}

			const CacheEntry &readable()
			{
				return m_item->cacheEntry;
			}

			CacheEntry &writable()
			{
				assert( m_itemLock.isWriter() );
				return m_item->cacheEntry;
			}

			bool isWritable() const
			{
				return m_itemLock.isWriter();
			}

			template<typename F>
			void execute( F &&f )
			{
				if( m_spawnsTasks )
				{
					// The getter function will spawn tasks. Execute
					// it via the TaskMutex, so that other threads trying
					// to access this cache item can help out. This also
					// means that the getter is executed inside a task_arena,
					// preventing it from stealing outer tasks that might try
					// to get this item from the cache, leading to deadlock.
					m_itemLock.execute( f );
				}
				else
				{
					// The getter won't do anything involving TBB tasks.
					// Avoid the overhead of executing via the TaskMutex.
					f();
				}
			}

			void release()
			{
				if( m_item )
				{
					m_itemLock.release();
					m_item = nullptr;
				}
			}

			private :

				bool acquire( Bin &bin, const Key &key, AcquireMode mode, bool spawnsTasks, const IECore::Canceller *canceller )
				{
					assert( !m_item );

					// Acquiring a handle requires taking two
					// locks, first the lock for the Bin, and
					// second the lock for the Item. We must be
					// careful to avoid deadlock in the case of
					// a GetterFunction which reenters the cache.

					typename Bin::Mutex::scoped_lock binLock;
					while( true )
					{
						// Acquire a lock on the bin, and get an iterator
						// from the key. We optimistically assume the item
						// may already be in the cache and first do a find()
						// using a bin read lock. This gives us much better
						// performance when many threads contend for items
						// that are already in the cache.
						binLock.acquire( bin.mutex, /* write = */ false );
						MapIterator it = bin.map.find( key );
						bool inserted = false;
						if( it == bin.map.end() )
						{
							if( mode != Insert && mode != InsertWritable )
							{
								return false;
							}
							binLock.upgrade_to_writer();
							std::tie<MapIterator, bool>( it, inserted ) = bin.map.insert( Item( key ) );
						}

						// Now try to get a lock on the item we want to
						// acquire. When we've just inserted a new item
						// we take a write lock directly, because we know
						// we'll need to write to the new item. When insertion
						// found a pre-existing item we optimistically take
						// just a read lock, because it is faster when
						// many threads just need to read from the same
						// cached item.
						const bool acquired = m_itemLock.acquireOr(
							it->mutex, /* write = */ inserted || mode == FindWritable || mode == InsertWritable,
							// Work accepter
							[&binLock, canceller] ( bool workAvailable ) {
								// Release the bin lock prior to accepting work, because
								// the work might involve recursion back into the cache,
								// thus requiring the bin lock.
								binLock.release();
								// Only accept work if our caller still wants
								// the result. Note : Once we've accepted the
								// work, the caller has no ability to recall us.
								// The only canceller being checked at that
								// point will be the one passed to the
								// `LRUCache::get()` call that we work in
								// service of. This isn't ideal, as it can cause
								// UI stalls if one UI element is waiting to
								// cancel an operation, but it's tasks have been
								// "captured" by collaboration on a compute
								// started by another UI element (which hasn't
								// requested cancellation).  One alternative is
								// that we would only accept work if our
								// canceller matches the one in use by the
								// original caller. This would rule out
								// collaboration between UI elements, but would
								// still allow diamond dependencies in graph
								// evaluation to use collaboration.
								return (!canceller || !canceller->cancelled());
							}
						);

						if( acquired )
						{
							if(
								!m_itemLock.isWriter() &&
								mode == Insert && it->cacheEntry.status() == LRUCache::Uncached
							)
							{
								// We found an old item that doesn't have a
								// value. This can either be because it was
								// erased but hasn't been popped yet, or because
								// the item was too big to fit in the cache. We
								// need to get writer status so it can be
								// updated in `get()`, but we can't use the obvious
								// `m_itemLock.upgradeToWriter()` call as it can
								// lead to deadlock. So we must retry using
								// InsertWritable instead.
								mode = InsertWritable;
								m_itemLock.release();
								binLock.release();
								continue;
							}
							// Success!
							m_item = &*it;
							m_spawnsTasks = spawnsTasks;
							return true;
						}

						IECore::Canceller::check( canceller );
					}
				}

				friend class TaskParallel;

				const Item *m_item;
				typename Item::Mutex::ScopedLock m_itemLock;
				bool m_spawnsTasks;

		};

		/// Templated so that we can be called with the GetterKey as
		/// well as the regular Key.
		template<typename K>
		bool acquire( const K &key, Handle &handle, AcquireMode mode, const IECore::Canceller *canceller )
		{
			return handle.acquire(
				bin( key ), key, mode,
				/// Only accept work for Insert mode, because that is
				/// the one used by `get()`. We don't want to attempt
				/// to do work in `set()`, because there will be no work
				/// to do. `TaskMutex::ScopedLock::execute()` has significant
				/// overhead, so we also want to avoid it if tasks won't
				/// be spawned for a particular key.
				mode == AcquireMode::Insert && spawnsTasks( key ),
				canceller
			);
		}

		void push( Handle &handle )
		{
			// Simply mark the item as having been used
			// recently. We will then give it a second chance
			// in pop(), so it will not be evicted immediately.
			// We don't need the handle to be writable to write
			// here, because `recentlyUsed` is atomic.
			handle.m_item->recentlyUsed.store( true, std::memory_order_release );
		}

		bool pop( Key &key, CacheEntry &cacheEntry )
		{
			// Popping works by iterating the map until an item
			// that has not been recently used is found. We store
			// the current iteration position as m_popIterator and
			// protect it with m_popMutex, taking the position that
			// it is sufficient for only one thread to be limiting
			// cost at any given time.
			PopMutex::scoped_lock lock;
			if( !lock.try_acquire( m_popMutex ) )
			{
				return false;
			}

			Bin *bin = &m_bins[m_popBinIndex];
			typename Bin::Mutex::scoped_lock binLock( bin->mutex );

			typename Item::Mutex::ScopedLock itemLock;
			int numFullIterations = 0;
			while( true )
			{
				// If we're at the end of this bin, advance to
				// the next non-empty one.
				const MapIterator emptySentinel = bin->map.end();
				while( m_popIterator == bin->map.end() )
				{
					binLock.release();
					m_popBinIndex = ( m_popBinIndex + 1 ) % m_bins.size();
					bin = &m_bins[m_popBinIndex];
					binLock.acquire( bin->mutex );
					m_popIterator = bin->map.begin();
					if( m_popIterator == emptySentinel )
					{
						// We've come full circle and all bins were empty.
						return false;
					}
					else if( m_popBinIndex == 0 )
					{
						if( numFullIterations++ > 50 )
						{
							// We're not empty, but we've been around and around
							// without finding anything to pop. This could happen
							// if other threads are frantically setting
							// the `recentlyUsed` flag or if `clear()` is
							// called from `get()`, while `get()` holds the lock
							// on the only item we could pop.
							return false;
						}
					}
				}

				if( itemLock.tryAcquire( m_popIterator->mutex ) )
				{
					if( !m_popIterator->recentlyUsed.load( std::memory_order_acquire ) )
					{
						// Pop this item.
						key = m_popIterator->key;
						cacheEntry = m_popIterator->cacheEntry;
						// Now erase it from the bin.
						// We must release the lock on the Item before erasing it,
						// because we cannot release a lock on a mutex that is
						// already destroyed. We know that no other thread can
						// gain access to the item though, because they must
						// acquire the Bin lock to do so, and we still hold the
						// Bin lock.
						itemLock.release();
						m_popIterator = bin->map.erase( m_popIterator );
						return true;
					}
					else
					{
						// Item has been used recently. Flag it so we
						// can pop it next time round, unless another
						// thread resets the flag.
						m_popIterator->recentlyUsed.store( false, std::memory_order_release );
						itemLock.release();
					}
				}
				else
				{
					// Failed to acquire the item lock. Some other
					// thread is busy with this item, so we consider
					// it to be recently used and just skip over it.
				}

				++m_popIterator;
			}
		}

		AtomicCost currentCost;

	private :

		Bins m_bins;

		Bin &bin( const Key &key )
		{
			// Note : `testLRUCacheUncacheableItem()` requires keys to share
			// a bin, and needs updating if the indexing strategy changes.
			size_t binIndex = boost::hash<Key>()( key ) % m_bins.size();
			return m_bins[binIndex];
		};

		using PopMutex = tbb::spin_mutex;
		PopMutex m_popMutex;
		size_t m_popBinIndex;
		MapIterator m_popIterator;

};

} // namespace LRUCachePolicy

// CacheEntry
// =======================================================================

template<typename Key, typename Value, template <typename> class Policy, typename GetterKey>
LRUCache<Key, Value, Policy, GetterKey>::CacheEntry::CacheEntry()
	:	cost( 0 )
{
}

template<typename Key, typename Value, template <typename> class Policy, typename GetterKey>
typename LRUCache<Key, Value, Policy, GetterKey>::Status LRUCache<Key, Value, Policy, GetterKey>::CacheEntry::status() const
{
	return static_cast<Status>( state.which() );
}

// LRUCache
// =======================================================================

template<typename Key, typename Value, template <typename> class Policy, typename GetterKey>
LRUCache<Key, Value, Policy, GetterKey>::LRUCache( GetterFunction getter, Cost maxCost, RemovalCallback removalCallback, bool cacheErrors )
	:	m_getter( getter ), m_removalCallback( removalCallback ), m_maxCost( maxCost ), m_cacheErrors( cacheErrors )
{
}

template<typename Key, typename Value, template <typename> class Policy, typename GetterKey>
LRUCache<Key, Value, Policy, GetterKey>::~LRUCache()
{
}

template<typename Key, typename Value, template <typename> class Policy, typename GetterKey>
void LRUCache<Key, Value, Policy, GetterKey>::clear()
{
	Key key;
	CacheEntry cacheEntry;
	while( m_policy.pop( key, cacheEntry ) )
	{
		eraseInternal( key, cacheEntry );
	}
}

template<typename Key, typename Value, template <typename> class Policy, typename GetterKey>
void LRUCache<Key, Value, Policy, GetterKey>::setMaxCost( Cost maxCost )
{
	if( maxCost >= m_maxCost )
	{
		m_maxCost = maxCost;
	}
	else
	{
		m_maxCost = maxCost;
		limitCost( maxCost );
	}

}

template<typename Key, typename Value, template <typename> class Policy, typename GetterKey>
typename LRUCache<Key, Value, Policy, GetterKey>::Cost LRUCache<Key, Value, Policy, GetterKey>::getMaxCost() const
{
	return m_maxCost;
}

template<typename Key, typename Value, template <typename> class Policy, typename GetterKey>
typename LRUCache<Key, Value, Policy, GetterKey>::Cost LRUCache<Key, Value, Policy, GetterKey>::currentCost() const
{
	return m_policy.currentCost;
}

template<typename Key, typename Value, template <typename> class Policy, typename GetterKey>
Value LRUCache<Key, Value, Policy, GetterKey>::get( const GetterKey &key, const IECore::Canceller *canceller )
{
	typename Policy<LRUCache>::Handle handle;
	m_policy.acquire( key, handle, LRUCachePolicy::Insert, canceller );
	const CacheEntry &cacheEntry = handle.readable();
	const Status status = cacheEntry.status();

	if( status==Uncached )
	{
		Value value = Value();
		Cost cost = 0;
		try
		{
			handle.execute( [this, &value, &key, &cost, canceller] { value = m_getter( key, cost, canceller ); } );
		}
		catch( IECore::Cancelled const & )
		{
			throw;
		}
		catch( ... )
		{
			if( handle.isWritable() && m_cacheErrors )
			{
				handle.writable().state = std::current_exception();
			}
			throw;
		}

		if( handle.isWritable() )
		{
			assert( cacheEntry.status() != Cached ); // this would indicate that another thread somehow
			assert( cacheEntry.status() != Failed ); // loaded the same thing as us, which is not the intention.

			setInternal( key, handle.writable(), value, cost );
			m_policy.push( handle );

			handle.release();
			limitCost( m_maxCost );
		}

		return value;
	}
	else if( status==Cached )
	{
		m_policy.push( handle );
		return boost::get<Value>( cacheEntry.state );
	}
	else
	{
		std::rethrow_exception( boost::get<std::exception_ptr>( cacheEntry.state ) );
	}
}

template<typename Key, typename Value, template <typename> class Policy, typename GetterKey>
std::optional<Value> LRUCache<Key, Value, Policy, GetterKey>::getIfCached( const Key &key )
{
	typename Policy<LRUCache>::Handle handle;
	if( !m_policy.acquire( key, handle, LRUCachePolicy::FindReadable, /* canceller = */ nullptr ) )
	{
		return std::nullopt;
	}

	const CacheEntry &cacheEntry = handle.readable();
	const Status status = cacheEntry.status();

	if( status==Uncached )
	{
		return std::nullopt;
	}
	else if( status==Cached )
	{
		m_policy.push( handle );
		return boost::get<Value>( cacheEntry.state );
	}
	else
	{
		std::rethrow_exception( boost::get<std::exception_ptr>( cacheEntry.state ) );
	}
}

template<typename Key, typename Value, template <typename> class Policy, typename GetterKey>
bool LRUCache<Key, Value, Policy, GetterKey>::set( const Key &key, const Value &value, Cost cost )
{
	typename Policy<LRUCache>::Handle handle;
	m_policy.acquire( key, handle, LRUCachePolicy::InsertWritable, /* canceller = */ nullptr );
	assert( handle.isWritable() );
	bool result = setInternal( key, handle.writable(), value, cost );
	m_policy.push( handle );
	handle.release();
	limitCost( m_maxCost );
	return result;
}

template<typename Key, typename Value, template <typename> class Policy, typename GetterKey>
template<typename CostFunction>
bool LRUCache<Key, Value, Policy, GetterKey>::setIfUncached( const Key &key, const Value &value, CostFunction &&costFunction )
{
	typename Policy<LRUCache>::Handle handle;
	m_policy.acquire( key, handle, LRUCachePolicy::Insert, /* canceller = */ nullptr );
	const CacheEntry &cacheEntry = handle.readable();
	const Status status = cacheEntry.status();

	bool result = false;
	if( status == Uncached && handle.isWritable() )
	{
		result = setInternal( key, handle.writable(), value, costFunction( value ) );
		m_policy.push( handle );

		handle.release();
		limitCost( m_maxCost );
	}
	return result;
}

template<typename Key, typename Value, template <typename> class Policy, typename GetterKey>
bool LRUCache<Key, Value, Policy, GetterKey>::setInternal( const Key &key, CacheEntry &cacheEntry, const Value &value, Cost cost )
{
	eraseInternal( key, cacheEntry );

	if( cost > m_maxCost )
	{
		return false;
	}

	cacheEntry.state = value;
	cacheEntry.cost = cost;

	m_policy.currentCost += cost;

	return true;
}

template<typename Key, typename Value, template <typename> class Policy, typename GetterKey>
bool LRUCache<Key, Value, Policy, GetterKey>::cached( const Key &key ) const
{
	typename Policy<LRUCache>::Handle handle;
	// Preferring const_cast over forcing all policies to implement
	// a ConstHandle and const acquire() variant.
	if( !const_cast<Policy<LRUCache> &>( m_policy ).acquire( key, handle, LRUCachePolicy::FindReadable, /* canceller = */ nullptr ) )
	{
		return false;
	}

	return handle.readable().status() == Cached;
}

template<typename Key, typename Value, template <typename> class Policy, typename GetterKey>
bool LRUCache<Key, Value, Policy, GetterKey>::erase( const Key &key )
{
	typename Policy<LRUCache>::Handle handle;
	if( !m_policy.acquire( key, handle, LRUCachePolicy::FindWritable, /* canceller = */ nullptr ) )
	{
		return false;
	}

	assert( handle.isWritable() );
	return eraseInternal( key, handle.writable() );
}

template<typename Key, typename Value, template <typename> class Policy, typename GetterKey>
bool LRUCache<Key, Value, Policy, GetterKey>::eraseInternal( const Key &key, CacheEntry &cacheEntry )
{
	const Status status = cacheEntry.status();
	if( status == Cached )
	{
		if( m_removalCallback )
		{
			m_removalCallback( key, boost::get<Value>( cacheEntry.state ) );
		}
		m_policy.currentCost -= cacheEntry.cost;
	}

	cacheEntry.state = boost::blank();
	return status == Cached;
}

template<typename Key, typename Value, template <typename> class Policy, typename GetterKey>
void LRUCache<Key, Value, Policy, GetterKey>::limitCost( Cost cost )
{
	Key key;
	CacheEntry cacheEntry;
	while( m_policy.currentCost > cost )
	{
		if( !m_policy.pop( key, cacheEntry ) )
		{
			// Policy was unable to pop, so we give up.
			// This behaviour is used by the Parallel and TaskParallel
			// policies to avoid a single thread being stuck with
			// all the cleanup while other threads continually add
			// items. They can "pass the baton" via m_popMutex` on
			// each iteration of our loop; if one thread fails to
			// acquire the mutex, it knows that another thread will
			// be taking up the work.
			//
			// We cannot achieve the same thing outside the policy
			// by simply capping the maximum number of iterations
			// here, because that leads to abandoned cleanup if we
			// are the last or only thread to access the cache.
			break;
		}

		eraseInternal( key, cacheEntry );
	}
}

} // namespace IECorePreview
