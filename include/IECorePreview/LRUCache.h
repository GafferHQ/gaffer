//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2007-2014, Image Engine Design Inc. All rights reserved.
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

#ifndef IECOREPREVIEW_LRUCACHE_H
#define IECOREPREVIEW_LRUCACHE_H

#include <vector>

#include "tbb/spin_mutex.h"

#include "boost/noncopyable.hpp"
#include "boost/function.hpp"
#include "boost/unordered_map.hpp"

namespace IECorePreview
{

/// A mapping from keys to values, where values are computed from keys using a user
/// supplied function. Recently computed values are stored in the cache to accelerate
/// subsequent lookups. Each value has a cost associated with it, and the cache has
/// a maximum total cost above which it will remove the (approximately) least recently
/// accessed items.
///
/// The Key type must be hashable using boost::hash().
///
/// The Value type must be default constructible, copy constructible and assignable.
/// Note that Values are returned by value, and erased by assigning a default constructed
/// value. In practice this means that a smart pointer is the best choice of Value.
///
/// \threading It is safe to call the methods of LRUCache from concurrent threads.
/// \ingroup utilityGroup
template<typename Key, typename Value>
class LRUCache : private boost::noncopyable
{
	public:

		typedef size_t Cost;

		/// The GetterFunction is responsible for computing the value and cost for a cache entry
		/// when given the key. It should throw a descriptive exception if it can't get the data for
		/// any reason. It is unsafe to access the LRUCache itself from the GetterFunction.
		typedef boost::function<Value ( const Key &key, Cost &cost )> GetterFunction;
		/// The optional RemovalCallback is called whenever an item is discarded from the cache.
		///  It is unsafe to access the LRUCache itself from the RemovalCallback.
		typedef boost::function<void ( const Key &key, const Value &data )> RemovalCallback;

		LRUCache( GetterFunction getter, Cost maxCost = 500 );
		LRUCache( GetterFunction getter, RemovalCallback removalCallback, Cost maxCost );
		virtual ~LRUCache();

		/// Retrieves an item from the cache, computing it if necessary.
		/// The item is returned by value, as it may be removed from the
		/// cache at any time by operations on another thread, or may not
		/// even be stored in the cache if it exceeds the maximum cost.
		/// Throws if the item can not be computed.
		Value get( const Key &key );

		/// Adds an item to the cache directly, bypassing the GetterFunction.
		/// Returns true for success and false on failure - failure can occur
		/// if the cost exceeds the maximum cost for the cache. Note that even
		/// when true is returned, the item may be removed from the cache by a
		/// subsequent (or concurrent) operation.
		bool set( const Key &key, const Value &value, Cost cost );

		/// Returns true if the object is in the cache. Note that the
		/// return value may be invalidated immediately by operations performed
		/// by another thread.
		bool cached( const Key &key ) const;

		/// Erases the item if it was cached. Returns true if it was cached
		/// and false if it wasn't cached and therefore wasn't removed.
		bool erase( const Key &key );

		/// Erases all cached items. Note that when this returns, the cache
		/// may have been repopulated with items if other threads have called
		/// set() or get() concurrently.
		void clear();

		/// Sets the maximum cost of the items held in the cache, discarding any
		/// items if necessary to meet the new limit.
		void setMaxCost( Cost maxCost );

		/// Returns the maximum cost.
		Cost getMaxCost() const;

		/// Returns the current cost of all cached items.
		Cost currentCost() const;

	private :

		// Data
		//////////////////////////////////////////////////////////////////////////

		// A function for computing values, and one for notifying of removals.
		GetterFunction m_getter;
		RemovalCallback m_removalCallback;

		// Status of each item in the cache.
		enum Status
		{
			New, // brand new unpopulated entry
			Cached, // entry complete with value
			TooCostly, // entry cost exceeds m_maxCost and therefore isn't stored
			Failed // m_getter failed when computing entry
		};

		// CacheEntry implementation - a single item of the cache.
		struct CacheEntry
		{
			CacheEntry(); // status == New
			CacheEntry( const CacheEntry &other );

			Value value; // value for this item
			Cost cost; // the cost for this item

			char status; // status of this item
			bool recentlyUsed;
		};

		// Map from keys to items - this forms the basis of
		// our cache.
		typedef boost::unordered_map<Key, CacheEntry> Map;
		typedef typename Map::value_type MapValue;

		// In various use cases we need to support
		// concurrent access from many threads, and it's
		// important that we do this efficiently. Our
		// map type is not threadsafe, and a global mutex
		// would be inefficient, so we take a binned approach.
		// We store N internal maps, and use the hash of the
		// key to determine which particular map that key
		// should be stored in. This means that provided
		// different threads are accessing different map
		// values, they don't contend for a mutex at all.
		struct Bin
		{
			typedef tbb::spin_mutex Mutex;
			Map map;
			Mutex mutex;
		};

		typedef std::vector<boost::shared_ptr<Bin> > Bins;
		Bins m_bins;

		// Handle class to abstract away the binned
		// storage strategy. Internally holds an iterator
		// into one of the maps and holds the lock for
		// that map. All access to the bins must be
		// made through this class.
		class Handle : public boost::noncopyable
		{

			public :

				Handle()
					:	m_cache( NULL ), m_binIndex( 0 )
				{
				}

				Handle( LRUCache *cache )
					:	m_cache( NULL ), m_binIndex( 0 )
				{
					begin( cache );
				}

				Handle( LRUCache *cache, const Key &key, bool createIfMissing = false )
					:	m_cache( NULL ), m_binIndex( 0 )
				{
					acquire( cache, key, createIfMissing );
				}

				~Handle()
				{
					release();
				}

				bool begin( LRUCache *cache )
				{
					for( size_t i = 0, e = cache->m_bins.size(); i < e; ++i )
					{
						release();
						m_cache = cache;
						m_binIndex = i;
						m_cache->m_bins[m_binIndex]->mutex.lock();
						m_it = m_cache->m_bins[m_binIndex]->map.begin();
						if( m_it != m_cache->m_bins[m_binIndex]->map.end() )
						{
							return true;
						}
					}
					release();
					return false;
				}

				bool acquire( LRUCache *cache, const Key &key, bool createIfMissing = false )
				{
					release();
					m_cache = cache;
					m_binIndex = binIndex( key );
					m_cache->m_bins[m_binIndex]->mutex.lock();
					if( createIfMissing )
					{
						m_it = m_cache->m_bins[m_binIndex]->map.insert( MapValue( key, CacheEntry() ) ).first;
						return true;
					}
					else
					{
						m_it = m_cache->m_bins[m_binIndex]->map.find( key );
						if( m_it != m_cache->m_bins[m_binIndex]->map.end() )
						{
							return true;
						}
						else
						{
							release();
							return false;
						}
					}
				}

				void release()
				{
					if( m_cache )
					{
						m_cache->m_bins[m_binIndex]->mutex.unlock();
						m_cache = NULL;
					}
				}

				void increment()
				{
					m_it++;
					while( m_it == m_cache->m_bins[m_binIndex]->map.end() && m_binIndex < m_cache->m_bins.size() - 1 )
					{
						m_cache->m_bins[m_binIndex]->mutex.unlock();
						m_binIndex++;
						m_cache->m_bins[m_binIndex]->mutex.lock();
						m_it = m_cache->m_bins[m_binIndex]->map.begin();
					}
				}

				void erase()
				{
					m_cache->m_bins[m_binIndex]->map.erase( m_it );
				}

				void eraseAndIncrement()
				{
					Iterator nextIt = m_it; nextIt++;
					size_t nextBinIndex = m_binIndex;
					while( nextIt == m_cache->m_bins[nextBinIndex]->map.end() && nextBinIndex < m_cache->m_bins.size() - 1 )
					{
						if( nextBinIndex != m_binIndex )
						{
							m_cache->m_bins[nextBinIndex]->mutex.unlock();
						}
						nextBinIndex++;
						m_cache->m_bins[nextBinIndex]->mutex.lock();
						nextIt = m_cache->m_bins[nextBinIndex]->map.begin();
					}

					m_cache->m_bins[m_binIndex]->map.erase( m_it );

					if( nextBinIndex != m_binIndex )
					{
						m_cache->m_bins[m_binIndex]->mutex.unlock();
						m_binIndex = nextBinIndex;
					}

					m_it = nextIt;
				}

				bool valid()
				{
					return m_cache && m_it != m_cache->m_bins[m_binIndex]->map.end();
				}

				MapValue &operator*()
				{
					return *m_it;
				}

				MapValue *operator->()
				{
					return &(*m_it);
				}

			private :

				typedef typename Map::iterator Iterator;

				LRUCache *m_cache;
				size_t m_binIndex;
				Iterator m_it;

				size_t binIndex( const Key &key ) const
				{
					return boost::hash<Key>()( key ) % m_cache->m_bins.size();
				}

		};

		// Total cost. We store the current cost atomically so it can be updated
		// concurrently by multiple threads.
		typedef tbb::atomic<Cost> AtomicCost;
		AtomicCost m_currentCost;
		Cost m_maxCost;

		// These methods set/erase a cached value, updating the current
		// cost appropriately. The caller must hold the lock for the bin
		// containing the value.
		bool setInternal( MapValue &mapValue, const Value &value, Cost cost );
		bool eraseInternal( MapValue &mapValue );

		// When our current cost goes over the limit, we must discard
		// cached values until the cost is back under the threshold.
		// We do this by cycling through our cache using a "second chance"
		// algorithm to determine what to remove. No locks must be held
		// when calling limitCost().
		tbb::spin_mutex m_limitCostMutex;
		Key m_limitCostSweepPosition;
		void limitCost();

		static void nullRemovalCallback( const Key &key, const Value &value );

};

} // namespace IECore

#include "IECorePreview/LRUCache.inl"

#endif // IECOREPREVIEW_LRUCACHE_H
