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

#include "boost/function.hpp"
#include "boost/noncopyable.hpp"
#include "boost/variant.hpp"

namespace IECorePreview
{

namespace LRUCachePolicy
{

/// Not threadsafe. Either use from only a single thread
/// or protect with an external mutex. Key type must have
/// a `hash_value` implementation as described in the boost
/// documentation.
template<typename LRUCache>
class Serial;

/// Threadsafe, `get()` blocks if another thread is already
/// computing the value. Key type must have a `hash_value`
/// implementation as described in the boost documentation.
template<typename LRUCache>
class Parallel;

/// Threadsafe, `get()` collaborates on TBB tasks if another
/// thread is already computing the value. Key type must have
/// a `hash_value` implementation as described in the boost
/// documentation.
///
/// > Note : There is measurable overhead in the task collaboration
/// > mechanism, so if it is known that tasks will not be spawned for
/// > `GetterFunction( getterKey )` you may define a `bool spawnsTasks( const GetterKey & )`
/// > function that will be used to avoid the overhead.
template<typename LRUCache>
class TaskParallel;

} // namespace LRUCachePolicy

/// A mapping from keys to values, where values are computed from keys using a user
/// supplied function. Recently computed values are stored in the cache to accelerate
/// subsequent lookups. Each value has a cost associated with it, and the cache has
/// a maximum total cost above which it will remove the least recently accessed items.
///
/// The Value type must be default constructible, copy constructible and assignable.
/// Note that Values are returned by value, and erased by assigning a default constructed
/// value. In practice this means that a smart pointer is the best choice of Value.
///
/// The Policy determines the thread safety, eviction and performance characteristics
/// of the cache. See the documentation for each individual policy in the LRUCachePolicy
/// namespace.
///
/// The GetterKey may be used where the GetterFunction requires some auxiliary information
/// in addition to the Key. It must be implicitly castable to Key, and all GetterKeys
/// which yield the same Key must also yield the same results from the GetterFunction.
///
/// \ingroup utilityGroup
template<typename Key, typename Value, template <typename> class Policy=LRUCachePolicy::Parallel, typename GetterKey=Key>
class LRUCache : private boost::noncopyable
{
	public:

		typedef size_t Cost;
		typedef Key KeyType;

		/// The GetterFunction is responsible for computing the value and cost for a cache entry
		/// when given the key. It should throw a descriptive exception if it can't get the data for
		/// any reason.
		typedef boost::function<Value ( const GetterKey &key, Cost &cost )> GetterFunction;
		/// The optional RemovalCallback is called whenever an item is discarded from the cache.
		typedef boost::function<void ( const Key &key, const Value &data )> RemovalCallback;

		LRUCache( GetterFunction getter, Cost maxCost, RemovalCallback removalCallback = RemovalCallback(), bool cacheErrors = true );
		virtual ~LRUCache();

		/// Retrieves an item from the cache, computing it if necessary.
		/// The item is returned by value, as it may be removed from the
		/// cache at any time by operations on another thread, or may not
		/// even be stored in the cache if it exceeds the maximum cost.
		/// Throws if the item can not be computed.
		Value get( const GetterKey &key );

		/// Retrieves an item from the cache if it has been computed or set
		/// previously. Throws if a previous call to `get()` failed.
		boost::optional<Value> getIfCached( const Key &key );

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

		// Give Policy access to CacheEntry definitions.
		friend class Policy<LRUCache>;

		// A function for computing values, and one for notifying of removals.
		GetterFunction m_getter;
		RemovalCallback m_removalCallback;

		// Status of each item in the cache.
		enum Status
		{
			Uncached, // entry without valid value
			Cached, // entry with valid value
			Failed // m_getter failed when computing entry
		};

		// The type used to store a single cached item.
		struct CacheEntry
		{
			CacheEntry();

			// We use a boost::variant to compactly store
			// a union of the data needed for each Status.
			//
			// - Uncached : A boost::blank instance
			// - Cached : The Value itself
			// - Failed : The exception thrown by the GetterFn
			typedef boost::variant<boost::blank, Value, std::exception_ptr> State;

			State state;
			Cost cost; // the cost for this item

			Status status() const;

		};

		// Policy. This is responsible for
		// the internal storage for the cache.
		Policy<LRUCache> m_policy;

		Cost m_maxCost;
		bool m_cacheErrors;

		// Methods
		// =======

		// Updates the cached value and updates the current
		// total cost.
		bool setInternal( const Key &key, CacheEntry &cacheEntry, const Value &value, Cost cost );

		// Removes any cached value and updates the current total
		// cost.
		bool eraseInternal( const Key &key, CacheEntry &cacheEntry );

		// Removes items from the cache until the current cost is
		// at or below the specified limit.
		void limitCost( Cost cost );

};

} // namespace IECorePreview

#include "Gaffer/Private/IECorePreview/LRUCache.inl"

#endif // IECOREPREVIEW_LRUCACHE_H
