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

#ifndef IECOREPREVIEW_LRUCACHE_INL
#define IECOREPREVIEW_LRUCACHE_INL

#include <cassert>

#include "tbb/tbb_thread.h"

#include "IECore/Exception.h"

namespace IECorePreview
{

template<typename Key, typename Value>
LRUCache<Key, Value>::CacheEntry::CacheEntry()
	:	value(), cost( 0 ), status( New ), recentlyUsed( false )
{
}

template<typename Key, typename Value>
LRUCache<Key, Value>::CacheEntry::CacheEntry( const CacheEntry &other )
	:	value( other.value ), cost( other.cost ), status( other.status ), recentlyUsed( other.recentlyUsed )
{
}

template<typename Key, typename Value>
LRUCache<Key, Value>::LRUCache( GetterFunction getter, Cost maxCost )
	:	m_getter( getter ), m_removalCallback( nullRemovalCallback ), m_maxCost( maxCost )
{
	m_currentCost = 0;
	for( size_t i = 0, e = tbb::tbb_thread::hardware_concurrency(); i < e; ++i )
	{
		m_bins.push_back( boost::shared_ptr<Bin>( new Bin ) );
	}
}

template<typename Key, typename Value>
LRUCache<Key, Value>::LRUCache( GetterFunction getter, RemovalCallback removalCallback, Cost maxCost )
	:	m_getter( getter ), m_removalCallback( removalCallback ), m_maxCost( maxCost )
{
	m_currentCost = 0;
	for( size_t i = 0, e = tbb::tbb_thread::hardware_concurrency(); i < e; ++i )
	{
		m_bins.push_back( boost::shared_ptr<Bin>( new Bin ) );
	}
}

template<typename Key, typename Value>
LRUCache<Key, Value>::~LRUCache()
{
}

template<typename Key, typename Value>
void LRUCache<Key, Value>::clear()
{
	Handle handle;
	handle.begin( this );
	while( handle.valid() )
	{
		eraseInternal( *handle );
		handle.eraseAndIncrement();
	}
}

template<typename Key, typename Value>
void LRUCache<Key, Value>::setMaxCost( Cost maxCost )
{
	m_maxCost = maxCost;
	limitCost();
}

template<typename Key, typename Value>
typename LRUCache<Key, Value>::Cost LRUCache<Key, Value>::getMaxCost() const
{
	return m_maxCost;
}

template<typename Key, typename Value>
typename LRUCache<Key, Value>::Cost LRUCache<Key, Value>::currentCost() const
{
	return m_currentCost;
}

template<typename Key, typename Value>
Value LRUCache<Key, Value>::get( const Key& key )
{
	Handle handle;
	if( !handle.acquire( this, key, /* write = */ false, /* createIfMissing = */ true ) )
	{
		// We found an existing entry, and have a read lock for it.
		// If the value is cached already and the recentlyUsed flag
		// is already set, we have no need of a write lock at all.
		// This gives us a significant performance boost when the
		// cache is heavily contended on the same already-cached
		// items.
		const CacheEntry &cacheEntry = handle->second;
		if( cacheEntry.status == Cached && cacheEntry.recentlyUsed )
		{
			return cacheEntry.value;
		}
		else
		{
			// Upgrade to writer and fall through to general case below.
			handle.upgradeToWriter();
		}
	}

	// We have a write lock, and the item may or may not be
	// cached already.

	CacheEntry &cacheEntry = handle->second;

	if( cacheEntry.status==New || cacheEntry.status==TooCostly )
	{
		assert( cacheEntry.value==Value() );

		Value value = Value();
		Cost cost = 0;
		try
		{
			value = m_getter( key, cost );
		}
		catch( ... )
		{
			cacheEntry.status = Failed;
			throw;
		}

		assert( cacheEntry.status != Cached ); // this would indicate that another thread somehow
		assert( cacheEntry.status != Failed ); // loaded the same thing as us, which is not the intention.

		setInternal( *handle, value, cost );

		assert( cacheEntry.status == Cached || cacheEntry.status == TooCostly );

		handle.release();
		limitCost();

		return value;
	}
	else if( cacheEntry.status==Cached )
	{
		Value result = cacheEntry.value;
		cacheEntry.recentlyUsed = true;
		return result;
	}
	else
	{
		assert( cacheEntry.status==Failed );
		throw IECore::Exception( "Previous attempt to get item failed." );
	}
}

template<typename Key, typename Value>
bool LRUCache<Key, Value>::set( const Key &key, const Value &value, Cost cost )
{
	Handle handle;
	handle.acquire( this, key, /* write = */ true, /* createIfMissing = */ true );

	const bool result = setInternal( *handle, value, cost );

	handle.release();
	limitCost();

	return result;
}

template<typename Key, typename Value>
bool LRUCache<Key, Value>::cached( const Key &key ) const
{
	Handle handle;
	handle.acquire( const_cast<LRUCache *>( this ), key, /* write = */ false, /* createIfMissing = */ false );
	return handle.valid() && handle->second.status == Cached;
}

template<typename Key, typename Value>
bool LRUCache<Key, Value>::erase( const Key &key )
{
	Handle handle;
	handle.acquire( this, key, /* write = */ true, /* createIfMissing = */ false );
	if( handle.valid() )
	{
		eraseInternal( *handle );
		handle.erase();
		return true;
	}
	return false;
}

template<typename Key, typename Value>
bool LRUCache<Key, Value>::setInternal( MapValue &mapValue, const Value &value, Cost cost )
{
	// Erase the old value, adjusting the current cost.
	eraseInternal( mapValue );

	// Store the new value if we can, and again adjust
	// the current cost.
	CacheEntry &cacheEntry = mapValue.second;
	bool result = true;
	if( cost <= m_maxCost )
	{
		cacheEntry.value = value;
		cacheEntry.cost = cost;
		cacheEntry.status = Cached;
		cacheEntry.recentlyUsed = true;
		m_currentCost += cost;
	}
	else
	{
		cacheEntry.status = TooCostly;
		cacheEntry.recentlyUsed = false;
		result = false;
	}

	return result;
}

template<typename Key, typename Value>
bool LRUCache<Key, Value>::eraseInternal( MapValue &mapValue )
{
	CacheEntry &cacheEntry = mapValue.second;
	const Status originalStatus = (Status)cacheEntry.status;

	if( originalStatus == Cached )
	{
		m_removalCallback( mapValue.first, cacheEntry.value );
		m_currentCost -= cacheEntry.cost;
		cacheEntry.value = Value();
	}

	return originalStatus == Cached;
}

template<typename Key, typename Value>
void LRUCache<Key, Value>::limitCost()
{
	tbb::spin_mutex::scoped_lock lock;
	if( !lock.try_acquire( m_limitCostMutex ) )
	{
		// Another thread is busy limiting the
		// cost, so we don't need to.
		return;
	}

	Handle handle;
	handle.acquire( this, m_limitCostSweepPosition, /* write = */ true, /* createIfMissing = */ false );
	if( !handle.valid() )
	{
		// This is our first sweep, or the entry
		// was erased by clear() or erase(). Just
		// start at the beginning.
		handle.begin( this );
	}

	size_t numFullCycles = 0;
	while( m_currentCost > m_maxCost && handle.valid() && numFullCycles < 100 )
	{
		if( !handle->second.recentlyUsed )
		{
			eraseInternal( *handle );
			handle.eraseAndIncrement();
		}
		else
		{
			// We'll erase this guy text time round,
			// if he hasn't been used by some other
			// thread by then.
			handle->second.recentlyUsed = false;
			handle.increment();
		}
		if( !handle.valid() )
		{
			// We're at the end but may not have
			// reduced the cost sufficiently yet,
			// so wrap around.
			handle.begin( this );
			// In theory, our thread could end up
			// in an endless cycle if other threads
			// are busy pushing values into the cache
			// faster than we can remove them. So we
			// count the number of full cycles we've
			// performed, and abort if it's getting
			// costly - this will force another
			// thread to pick up the work, so we can
			// return to our caller.
			numFullCycles++;
		}
	}

	// Remember where we were so we can start in
	// the same place next time around.
	if( handle.valid() )
	{
		m_limitCostSweepPosition = handle->first;
	}
}

template<typename Key, typename Value>
void LRUCache<Key, Value>::nullRemovalCallback( const Key &key, const Value &value )
{
}

} // namespace IECorePreview

#endif // IECOREPREVIEW_LRUCACHE_INL
