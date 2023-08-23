//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/ValuePlug.h"

#include "Gaffer/Action.h"
#include "Gaffer/ComputeNode.h"
#include "Gaffer/Context.h"
#include "Gaffer/Private/IECorePreview/LRUCache.h"
#include "Gaffer/Process.h"

#include "IECore/MessageHandler.h"

#include "boost/bind/bind.hpp"

#include "tbb/enumerable_thread_specific.h"

#include "fmt/format.h"

#include <atomic>
#include <unordered_set>

using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

// Before using the HashProcess/ComputeProcess classes to get a hash or
// a value, we first traverse back down the chain of input plugs to the
// start, or till we find a plug of a different type. This traversal is
/// much quicker than using the Process classes for every step in the chain
/// and avoids the creation of lots of unnecessary cache entries.
inline const ValuePlug *sourcePlug( const ValuePlug *p )
{
	const ValuePlug *in = p->getInput<ValuePlug>();
	if( !in )
	{
		return p;
	}

	const IECore::TypeId typeId = p->typeId();
	while( in && in->typeId() == typeId )
	{
		p = in;
		in = p->getInput<ValuePlug>();
	}

	return p;
}

const IECore::MurmurHash g_nullHash;

// We only use the lower half of possible dirty count values.
// The upper half is reserved for a debug "checked" mode where we compute
// alternate values that are invalidated whenever any plug changes, in
// order to catch inaccuracies in the cache
const uint64_t DIRTY_COUNT_RANGE_MAX = std::numeric_limits<uint64_t>::max() / 2;

} // namespace

//////////////////////////////////////////////////////////////////////////
// The HashProcess manages the task of calling ComputeNode::hash() and
// managing a cache of recently computed hashes.
//////////////////////////////////////////////////////////////////////////

namespace
{

// Key used to index into a cache of hashes. This is specified by
// the plug the hash was for and the context it was hashed in.
struct HashCacheKey
{
	HashCacheKey() {};
	HashCacheKey( const ValuePlug *plug, const Context *context, uint64_t dirtyCount )
		:	plug( plug ), contextHash( context->hash() ), dirtyCount( dirtyCount )
	{
	}

	bool operator == ( const HashCacheKey &other ) const
	{
		return other.plug == plug && other.contextHash == contextHash && dirtyCount == other.dirtyCount;
	}

	// TODO : REMOVE. WE DON'T WANT TO USE A MAP ANYWAY.
	bool operator < ( const HashCacheKey &other ) const
	{
		if( plug < other.plug )
		{
			return true;
		}
		else if( other.plug < plug )
		{
			return false;
		}
		else if( contextHash < other.contextHash )
		{
			return true;
		}
		else if( other.contextHash < contextHash )
		{
			return false;
		}
		return dirtyCount < other.dirtyCount;
	}

	/// \todo Could we merge all three fields into a single
	/// MurmurHash, or would hash collisions be too likely?
	const ValuePlug *plug;
	IECore::MurmurHash contextHash;
	uint64_t dirtyCount;
};

// `hash_value( HashCacheKey )` is a requirement of the LRUCache,
// because it uses boost containers internally. This is the reason
// that HashCacheKey isn't a nested class of HashProcess, as the
// necessary friendship declaration would require moving things to
// ValuePlug.h.
size_t hash_value( const HashCacheKey &key )
{
	size_t result = 0;
	boost::hash_combine( result, key.plug );
	boost::hash_combine( result, key.contextHash );
	boost::hash_combine( result, key.dirtyCount );
	return result;
}

size_t tbb_hasher( const HashCacheKey &key ) // TODO : SHOULD MAYBE BE STD::HASH?
{
	return hash_value( key );
}

ValuePlug::HashCacheMode defaultHashCacheMode()
{
	/// \todo Remove
	if( const char *e = getenv( "GAFFER_HASHCACHE_MODE" ) )
	{
		if( !strcmp( e, "Legacy" ) )
		{
			IECore::msg( IECore::Msg::Warning, "Gaffer", "GAFFER_HASHCACHE_MODE is Legacy. Interactive performance will be affected." );
			return ValuePlug::HashCacheMode::Legacy;
		}
		else if( !strcmp( e, "Checked" ) )
		{
			IECore::msg( IECore::Msg::Warning, "Gaffer", "GAFFER_HASHCACHE_MODE is Checked. Performance will be slow.  Use this setting only for debugging, not in production." );
			return ValuePlug::HashCacheMode::Checked;
		}
		else if( !strcmp( e, "Standard" ) )
		{
			return ValuePlug::HashCacheMode::Standard;
		}
		else
		{
			IECore::msg( IECore::Msg::Warning, "ValuePlug", "Invalid value for GAFFER_HASHCACHE_MODE. Must be Standard, Checked or Legacy." );
		}
	}
	return ValuePlug::HashCacheMode::Standard;
}

} // namespace

class ValuePlug::HashProcess : public Process
{

	public :

		// Interface used by ValuePlug.

		static IECore::MurmurHash hash( const ValuePlug *plug )
		{
			const ValuePlug *p = sourcePlug( plug );

			if( const ValuePlug *input = p->getInput<ValuePlug>() )
			{
				// We know that the input is of a different type to the plug,
				// because that is guaranteed by sourcePlug(). Get the hash from
				// the input and add a little extra something to represent the
				// conversion that m_resultPlug->setFrom( input ) will perform,
				// to break apart the cache entries.
				IECore::MurmurHash h = input->hash();
				h.append( input->typeId() );
				h.append( plug->typeId() );
				return h;
			}
			else if( p->direction() == In || !IECore::runTimeCast<const ComputeNode>( p->node() ) )
			{
				// No input connection, and no means of computing
				// a value. There can only ever be a single value,
				// which is stored directly on the plug - so we return
				// the hash of that.
				return p->m_staticValue->hash();
			}

			// A plug with an input connection or an output plug on a ComputeNode. There can be many values -
			// one per context, computed by ComputeNode::hash(). Pull the value from our cache, or compute it
			// using a HashProcess instance.

			Plug::flushDirtyPropagationScope(); // Ensure any pending calls to `dirty()` are made before we look up `m_dirtyCount`.

			const ComputeNode *computeNode = IECore::runTimeCast<const ComputeNode>( p->node() );
			const ThreadState &threadState = ThreadState::current();
			const Context *currentContext = threadState.context();
			const CachePolicy cachePolicy = computeNode ? computeNode->hashCachePolicy( p ) : CachePolicy::Uncached;

			if( cachePolicy == CachePolicy::Uncached )
			{
				return HashProcess( p, plug, computeNode ).run();
			}

			// Perform any pending adjustments to our thread-local cache.

			ThreadData &threadData = g_threadData.local();
			if( threadData.clearCache.load( std::memory_order_acquire ) )
			{
				threadData.cache.clear();
				threadData.clearCache.store( 0, std::memory_order_release );
			}

			if( threadData.cache.getMaxCost() != g_cacheSizeLimit )
			{
				threadData.cache.setMaxCost( g_cacheSizeLimit );
			}

			// Then get our hash. We do this using this `acquireHash()` functor so that
			// we can repeat the process for `Checked` mode.

			const bool forceMonitoring = Process::forceMonitoring( threadState, plug, staticType );

			auto acquireHash = [&]( const HashCacheKey &cacheKey ) {

				// Before we use this key, check that the dirty count hasn't maxed out
				if(
					cacheKey.dirtyCount == DIRTY_COUNT_RANGE_MAX ||
					cacheKey.dirtyCount == DIRTY_COUNT_RANGE_MAX + 1 + DIRTY_COUNT_RANGE_MAX
				)
				{
					throw IECore::Exception(  "Dirty count exceeded max. Either you've left Gaffer running for 100 million years, or a strange bug is incrementing dirty counts way too fast." );
				}

				// Check for an already-cached value in our thread-local cache, and return it if we have one.
				if( !forceMonitoring )
				{
					if( auto result = threadData.cache.getIfCached( cacheKey ) )
					{
						return *result;
					}
				}

				// No value in local cache, so either compute it directly or get it via
				// the global cache if it's expensive enough to warrant collaboration.
				IECore::MurmurHash result;
				if( cachePolicy == CachePolicy::Legacy || cachePolicy == CachePolicy::Standard )
				{
					result = HashProcess( p, plug, computeNode ).run();
				}
				else
				{
					std::optional<IECore::MurmurHash> cachedValue;
					if( !forceMonitoring )
					{
						cachedValue = g_cache.getIfCached( cacheKey );
					}
					if( cachedValue )
					{
						result = *cachedValue;
					}
					else
					{
						result = Process::acquireCollaborativeResult<HashProcess>( cacheKey, p, plug, computeNode );
					}
				}
				// Update local cache and return result
				threadData.cache.setIfUncached( cacheKey, result, cacheCostFunction );
				return result;
			};

			const HashCacheKey cacheKey( p, currentContext, p->m_dirtyCount );
			if( g_hashCacheMode == HashCacheMode::Standard )
			{
				return acquireHash( cacheKey );
			}
			else if( g_hashCacheMode == HashCacheMode::Checked )
			{
				HashCacheKey legacyCacheKey( cacheKey );
				legacyCacheKey.dirtyCount = g_legacyGlobalDirtyCount + DIRTY_COUNT_RANGE_MAX + 1;
				const IECore::MurmurHash check = acquireHash( legacyCacheKey );
				const IECore::MurmurHash result = acquireHash( cacheKey );

				if( result != check )
				{
					// This isn't exactly a process exception, but we want to treat it the same, in
					// terms of associating it with a plug. Creating a ProcessException is the simplest
					// approach, which can be done by throwing and then immediately wrapping.
					try
					{
						throw IECore::Exception(  "Detected undeclared dependency. Fix DependencyNode::affects() implementation." );
					}
					catch( ... )
					{
						ProcessException::wrapCurrentException( p, currentContext, staticType );
					}
				}
				return result;
			}
			else
			{
				// HashCacheMode::Legacy
				HashCacheKey legacyCacheKey( cacheKey );
				legacyCacheKey.dirtyCount = g_legacyGlobalDirtyCount + DIRTY_COUNT_RANGE_MAX + 1;
				return acquireHash( legacyCacheKey );
			}
		}

		static size_t getCacheSizeLimit()
		{
			return g_cacheSizeLimit;
		}

		static void setCacheSizeLimit( size_t maxEntriesPerThread )
		{
			g_cacheSizeLimit = maxEntriesPerThread;
			g_cache.setMaxCost( g_cacheSizeLimit );
		}

		static void clearCache( bool now = false )
		{
			g_cache.clear();
			// It's not documented explicitly, but it is safe to iterate over an
			// `enumerable_thread_specific` while `local()` is being called on
			// other threads, because the underlying container is a
			// `concurrent_vector`.
			tbb::enumerable_thread_specific<ThreadData>::iterator it, eIt;
			for( it = g_threadData.begin(), eIt = g_threadData.end(); it != eIt; ++it )
			{
				if( now )
				{
					// Not thread-safe - caller is responsible for ensuring there
					// are no concurrent computes.
					it->cache.clear();
				}
				else
				{
					// We can't clear the cache now, because it is most likely
					// in use by the owning thread. Instead we set this flag to
					// politely request that the thread clears the cache itself
					// at its earliest convenience - in the HashProcess constructor.
					it->clearCache.store( 1, std::memory_order_release );
				}
			}
		}

		static size_t totalCacheUsage()
		{
			size_t usage = g_cache.currentCost();
			tbb::enumerable_thread_specific<ThreadData>::iterator it, eIt;
			for( it = g_threadData.begin(), eIt = g_threadData.end(); it != eIt; ++it )
			{
				usage += it->cache.currentCost();
			}
			return usage;
		}

		static void dirtyLegacyCache()
		{
			if( g_hashCacheMode != HashCacheMode::Standard )
			{
				uint64_t count = g_legacyGlobalDirtyCount;
				uint64_t newCount;
				do
				{
					newCount = std::min( DIRTY_COUNT_RANGE_MAX, count + 1 );
				} while( !g_legacyGlobalDirtyCount.compare_exchange_weak( count, newCount ) );
			}
		}

		static void setHashCacheMode( ValuePlug::HashCacheMode hashCacheMode )
		{
			g_hashCacheMode = hashCacheMode;
			clearCache();
		}

		static ValuePlug::HashCacheMode getHashCacheMode()
		{
			return g_hashCacheMode;
		}

		static const IECore::InternedString staticType;

		// Interface required by `Process::acquireCollaborativeResult()`.

		HashProcess( const ValuePlug *plug, const ValuePlug *destinationPlug, const ComputeNode *computeNode )
			:	Process( staticType, plug, destinationPlug ), m_computeNode( computeNode )
		{
		}

		using ResultType = IECore::MurmurHash;

		ResultType run() const
		{
			try
			{
				if( !m_computeNode )
				{
					throw IECore::Exception( "Plug has no ComputeNode." );
				}

				IECore::MurmurHash result;
				m_computeNode->hash( static_cast<const ValuePlug *>( plug() ), context(), result );

				if( result == g_nullHash )
				{
					throw IECore::Exception( "ComputeNode::hash() not implemented." );
				}

				return result;
			}
			catch( ... )
			{
				handleException();
			}
		}

		using CacheType = IECorePreview::LRUCache<HashCacheKey, IECore::MurmurHash, IECorePreview::LRUCachePolicy::Parallel>;
		static CacheType g_cache;

		static size_t cacheCostFunction( const IECore::MurmurHash &value )
		{
			return 1;
		}

	private :

		const ComputeNode *m_computeNode;

		static std::atomic<uint64_t> g_legacyGlobalDirtyCount;
		static HashCacheMode g_hashCacheMode;

		struct ThreadData
		{
			// Using a null `GetterFunction` because it will never get called, because we only ever call `getIfCached()`.
			ThreadData() : cache( CacheType::GetterFunction(), g_cacheSizeLimit, CacheType::RemovalCallback(), /* cacheErrors = */ false ), clearCache( 0 ) {}
			using CacheType = IECorePreview::LRUCache<HashCacheKey, IECore::MurmurHash, IECorePreview::LRUCachePolicy::Serial>;
			CacheType cache;
			// Flag to request that hashCache be cleared.
			std::atomic_int clearCache;
		};

		static tbb::enumerable_thread_specific<ThreadData, tbb::cache_aligned_allocator<ThreadData>, tbb::ets_key_per_instance > g_threadData;
		static std::atomic_size_t g_cacheSizeLimit;

};

const IECore::InternedString ValuePlug::HashProcess::staticType( ValuePlug::hashProcessType() );
tbb::enumerable_thread_specific<ValuePlug::HashProcess::ThreadData, tbb::cache_aligned_allocator<ValuePlug::HashProcess::ThreadData>, tbb::ets_key_per_instance > ValuePlug::HashProcess::g_threadData;
// Default limit corresponds to a cost of roughly 25Mb per thread.
std::atomic_size_t ValuePlug::HashProcess::g_cacheSizeLimit( 128000 );
// Using a null `GetterFunction` because it will never get called, because we only ever call `getIfCached()`.
ValuePlug::HashProcess::CacheType ValuePlug::HashProcess::g_cache( CacheType::GetterFunction(), g_cacheSizeLimit, CacheType::RemovalCallback(), /* cacheErrors = */ false );
std::atomic<uint64_t> ValuePlug::HashProcess::g_legacyGlobalDirtyCount( 0 );
ValuePlug::HashCacheMode ValuePlug::HashProcess::g_hashCacheMode( defaultHashCacheMode() );

//////////////////////////////////////////////////////////////////////////
// The ComputeProcess manages the task of calling ComputeNode::compute()
// and storing a cache of recently computed results.
//////////////////////////////////////////////////////////////////////////

class ValuePlug::ComputeProcess : public Process
{

	public :

		// Interface used by ValuePlug.

		static size_t getCacheMemoryLimit()
		{
			return g_cache.getMaxCost();
		}

		static void setCacheMemoryLimit( size_t bytes )
		{
			return g_cache.setMaxCost( bytes );
		}

		static size_t cacheMemoryUsage()
		{
			return g_cache.currentCost();
		}

		static void clearCache()
		{
			g_cache.clear();
		}

		static IECore::ConstObjectPtr value( const ValuePlug *plug, const IECore::MurmurHash *precomputedHash )
		{
			const ValuePlug *p = sourcePlug( plug );
			const ComputeNode *computeNode = IECore::runTimeCast<const ComputeNode>( p->node() );

			if( !p->getInput() )
			{
				if( p->direction()==In || !computeNode )
				{
					// No input connection, and no means of computing
					// a value. There can only ever be a single value,
					// which is stored directly on the plug.
					return p->m_staticValue;
				}
			}

			// A plug with an input connection or an output plug on a ComputeNode. There can be many values -
			// one per context, computed via `ComputeNode::compute()` or `Plug::setFrom()`. Determine our
			// cache policy for the result.

			CachePolicy cachePolicy = CachePolicy::Uncached;
			if( p->getInput() )
			{
				// Type conversion will be implemented by `setFrom()`.
				// \todo Determine if caching is actually worthwhile for this.
				cachePolicy = CachePolicy::Legacy;
			}
			else if( computeNode )
			{
				// We'll be calling `compute()`.
				cachePolicy = computeNode->computeCachePolicy( p );
			}

			// If caching is off then its just a case of using a ComputeProcess
			// to do the work.

			if( cachePolicy == CachePolicy::Uncached )
			{
				return ComputeProcess( p, plug, computeNode ).run();
			}

			const ThreadState &threadState = ThreadState::current();

			// If caching is on, then we first check for an already-cached value
			// and return it if we have one. The cache is accessed via the
			// plug's hash.
			//
			// > Note : We call `plug->ValuePlug::hash()` rather than
			// > `plug->hash()` because we only want to represent the result of
			// > the private `getValueInternal()` method. Overrides such as
			// > `StringPlug::hash()` account for additional processing (such as
			// > substitutions) performed in public `getValue()` methods _after_
			// > calling `getValueInternal()`.
			const IECore::MurmurHash hash = p->ValuePlug::hash();

			if( !Process::forceMonitoring( threadState, plug, staticType ) )
			{
				if( auto result = g_cache.getIfCached( hash ) )
				{
					// Move avoids unnecessary additional addRef/removeRef.
					return std::move( *result );
				}
			}

			// The value isn't in the cache, so we'll need to compute it,
			// taking account of the cache policy.

			if( cachePolicy == CachePolicy::Legacy )
			{
				// Do the compute ourselves, without worrying if the same
				// compute is in flight elsewhere. We assume the compute is
				// lightweight enough and unlikely enough to be shared that in
				// the worst case it's OK to do it redundantly on a few threads
				// before it gets cached.
				IECore::ConstObjectPtr result = ComputeProcess( p, plug, computeNode ).run();
				// Store the value in the cache, but only if it isn't there already.
				// The check is useful because it's common for an upstream compute
				// triggered by us to have already done the work, and calling
				// `memoryUsage()` can be very expensive for some datatypes. A prime
				// example of this is the attribute state passed around in
				// GafferScene - it's common for a selective filter to mean that the
				// attribute compute is implemented as a pass-through (thus an
				// upstream node will already have computed the same result) and the
				// attribute data itself consists of many small objects for which
				// computing memory usage is slow.
				g_cache.setIfUncached( hash, result, cacheCostFunction );
				return result;
			}
			else
			{
				return acquireCollaborativeResult<ComputeProcess>(
					hash, p, plug, computeNode
				);
			}
		}

		static void receiveResult( const ValuePlug *plug, IECore::ConstObjectPtr result )
		{
			const Process *process = Process::current();
			if( !process || process->type() != staticType )
			{
				throw IECore::Exception( fmt::format( "Cannot set value for plug \"{}\" except during computation.", plug->fullName() ) );
			}

			const ComputeProcess *computeProcess = static_cast<const ComputeProcess *>( process );
			if( computeProcess->plug() != plug )
			{
				throw IECore::Exception( fmt::format( "Cannot set value for plug \"{}\" during computation for plug \"{}\".", plug->fullName(), computeProcess->plug()->fullName() ) );
			}

			const_cast<ComputeProcess *>( computeProcess )->m_result = result;
		}

		static const IECore::InternedString staticType;

		// Interface required by `Process::acquireCollaborativeResult()`.

		ComputeProcess( const ValuePlug *plug, const ValuePlug *destinationPlug, const ComputeNode *computeNode )
			:	Process( staticType, plug, destinationPlug ), m_computeNode( computeNode )
		{
		}

		IECore::ConstObjectPtr run() const
		{
			try
			{
				// Cast is safe because our constructor takes ValuePlugs.
				const ValuePlug *valuePlug = static_cast<const ValuePlug *>( plug() );
				if( const ValuePlug *input = valuePlug->getInput<ValuePlug>() )
				{
					// Cast is ok, because we know that the resulting setValue() call won't
					// actually modify the plug, but will just place the value in our m_result.
					const_cast<ValuePlug *>( valuePlug )->setFrom( input );
				}
				else
				{
					if( !m_computeNode )
					{
						throw IECore::Exception( "Plug has no ComputeNode." );
					}
					// Cast is ok - see comment above.
					m_computeNode->compute( const_cast<ValuePlug *>( valuePlug ), context() );
				}
				// The calls above should cause setValue() to be called on the result plug, which in
				// turn will call ValuePlug::setObjectValue(), which will then store the result in
				// the current ComputeProcess by calling receiveResult(). If that hasn't happened then
				// something has gone wrong and we should complain about it.
				if( !m_result )
				{
					throw IECore::Exception( "Compute did not set plug value." );
				}
				return m_result;
			}
			catch( ... )
			{
				handleException();
			}
		}

		using ResultType = IECore::ConstObjectPtr;
		using CacheType = IECorePreview::LRUCache<IECore::MurmurHash, IECore::ConstObjectPtr, IECorePreview::LRUCachePolicy::Parallel>;
		static CacheType g_cache;

		static size_t cacheCostFunction( const IECore::ConstObjectPtr &v )
		{
			return v->memoryUsage();
		}

	private :

		const ComputeNode *m_computeNode;
		IECore::ConstObjectPtr m_result;

};

const IECore::InternedString ValuePlug::ComputeProcess::staticType( ValuePlug::computeProcessType() );
// Using a null `GetterFunction` because it will never get called, because we only ever call `getIfCached()`.
ValuePlug::ComputeProcess::CacheType ValuePlug::ComputeProcess::g_cache( CacheType::GetterFunction(), 1024 * 1024 * 1024 * 1, CacheType::RemovalCallback(), /* cacheErrors = */ false ); // 1 gig

//////////////////////////////////////////////////////////////////////////
// SetValueAction implementation
//////////////////////////////////////////////////////////////////////////

class ValuePlug::SetValueAction : public Gaffer::Action
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::ValuePlug::SetValueAction, SetValueActionTypeId, Gaffer::Action );

		SetValueAction( ValuePlugPtr plug, IECore::ConstObjectPtr value )
			:	m_plug( plug ), m_doValue( value ), m_undoValue( plug->m_staticValue )
		{
		}

	protected :

		GraphComponent *subject() const override
		{
			return m_plug.get();
		}

		void doAction() override
		{
			Action::doAction();
			m_plug->setValueInternal( m_doValue, true );
		}

		void undoAction() override
		{
			Action::undoAction();
			m_plug->setValueInternal( m_undoValue, true );
		}

		bool canMerge( const Action *other ) const override
		{
			if( !Action::canMerge( other ) )
			{
				return false;
			}
			const SetValueAction *setValueAction = IECore::runTimeCast<const SetValueAction>( other );
			return setValueAction && setValueAction->m_plug == m_plug;
		}

		void merge( const Action *other ) override
		{
			const SetValueAction *setValueAction = static_cast<const SetValueAction *>( other );
			m_doValue = setValueAction->m_doValue;
		}

	private :

		ValuePlugPtr m_plug;
		IECore::ConstObjectPtr m_doValue;
		IECore::ConstObjectPtr m_undoValue;

};

IE_CORE_DEFINERUNTIMETYPED( ValuePlug::SetValueAction );

//////////////////////////////////////////////////////////////////////////
// ValuePlug implementation
//////////////////////////////////////////////////////////////////////////

namespace
{

std::atomic<uint64_t> g_dirtyCountEpoch( 0 );

} // namespace

GAFFER_PLUG_DEFINE_TYPE( ValuePlug );

/// \todo We may want to avoid repeatedly storing copies of the same default value
/// passed to this function. Perhaps by having a central map of unique values here,
/// or by doing it more intelligently in the derived classes (where we could avoid
/// even creating the values before figuring out if we've already got them somewhere).
ValuePlug::ValuePlug( const std::string &name, Direction direction,
	IECore::ConstObjectPtr defaultValue, unsigned flags )
	:	Plug( name, direction, flags ), m_defaultValue( defaultValue ), m_staticValue( defaultValue ), m_dirtyCount( g_dirtyCountEpoch )
{
	assert( m_defaultValue );
	assert( m_staticValue );
}

ValuePlug::ValuePlug( const std::string &name, Direction direction, unsigned flags )
	:	Plug( name, direction, flags ), m_defaultValue( nullptr ), m_staticValue( nullptr ), m_dirtyCount( g_dirtyCountEpoch )
{
}

ValuePlug::~ValuePlug()
{
	// We're dying, but there may still be hash cache entries for
	// our address. We need to ensure that a new plug that reuses
	// our address will not pick up these stale entries. So we
	// update `g_dirtyCountEpoch` so that new plugs will be initialised
	// with a count greater than ours. We do this atomically because
	// although each graph should only be edited on one thread, it is
	// permitted to edit multiple graphs in parallel.

	uint64_t epoch = g_dirtyCountEpoch;
	uint64_t newDirtyCount = std::min( DIRTY_COUNT_RANGE_MAX, m_dirtyCount + 1 );
	while( !g_dirtyCountEpoch.compare_exchange_weak( epoch, std::max( epoch, newDirtyCount ) ) )
	{
		// Nothing to do here.
	}

	// Legacy mode doesn't use `m_dirtyCount` or `g_dirtyCountEpoch`, so needs
	// dirtying separately.
	HashProcess::dirtyLegacyCache();
}

bool ValuePlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	if( !Plug::acceptsChild( potentialChild ) )
	{
		return false;
	}

	if( m_staticValue != nullptr )
	{
		return false;
	}

	return IECore::runTimeCast<const ValuePlug>( potentialChild );
}

bool ValuePlug::acceptsInput( const Plug *input ) const
{
	if( !Plug::acceptsInput( input ) )
	{
		return false;
	}
	if( input )
	{
		return input->isInstanceOf( staticTypeId() );
	}
	return true;
}

void ValuePlug::setInput( PlugPtr input )
{
	// set value back to what it was before
	// we received a connection. we do that
	// before calling Plug::setInput, so that
	// we've got our new state set correctly before
	// the dirty signal is emitted. we don't emit
	// in the setValueInternal call, because we don't
	// want to double up on the signals that the Plug
	// is emitting for us in Plug::setInput().
	if( getInput() && !input )
	{
		setValueInternal( m_staticValue, false );
	}

	Plug::setInput( input );
}

PlugPtr ValuePlug::createCounterpart( const std::string &name, Direction direction ) const
{
	PlugPtr result = new ValuePlug( name, direction, getFlags() );
	for( Plug::Iterator it( this ); !it.done(); ++it )
	{
		result->addChild( (*it)->createCounterpart( (*it)->getName(), direction ) );
	}
	return result;
}

bool ValuePlug::settable() const
{
	if( getInput() )
	{
		return false;
	}

	if( const Process *process = Process::current() )
	{
		return process->type() == ComputeProcess::staticType && process->plug() == this;
	}
	else
	{
		if( direction() != Plug::In )
		{
			return false;
		}
		for( ValuePlug::Iterator it( this ); !it.done(); ++it )
		{
			if( !(*it)->settable() )
			{
				return false;
			}
		}
		return true;
	}
}

void ValuePlug::setFrom( const ValuePlug *other )
{
	const ValuePlug *typedOther = IECore::runTimeCast<const ValuePlug>( other );
	if( !typedOther )
	{
		throw IECore::Exception( "Unsupported plug type" );
	}

	ChildContainer::const_iterator it, otherIt;
	for( it = children().begin(), otherIt = typedOther->children().begin(); it!=children().end() && otherIt!=typedOther->children().end(); it++, otherIt++ )
	{
		// We use `runTimeCast()` here as a concession to NameValuePlug,
		// which egregiously ignores the wishes of our `acceptsChild()`
		// implementation. See `NameValuePlug::acceptsChild()` for more
		// details.
		ValuePlug *child = IECore::runTimeCast<ValuePlug>( it->get() );
		const ValuePlug *otherChild = IECore::runTimeCast<ValuePlug>( otherIt->get() );
		if( child && otherChild )
		{
			child->setFrom( otherChild );
		}
	}
}

void ValuePlug::setToDefault()
{
	if( m_defaultValue != nullptr )
	{
		setObjectValue( m_defaultValue );
	}
	else
	{
		for( ValuePlug::Iterator it( this ); !it.done(); ++it )
		{
			(*it)->setToDefault();
		}
	}
}

bool ValuePlug::isSetToDefault() const
{
	if( m_defaultValue != nullptr )
	{
		const ValuePlug *s = source<ValuePlug>();
		if( s->direction() == Plug::Out && IECore::runTimeCast<const ComputeNode>( s->node() ) )
		{
			// Value is computed, and therefore can vary by context. There is no
			// single "current value", so no true concept of whether or not it's at
			// the default.
			return false;
		}
		return
			s->m_staticValue == m_defaultValue ||
			s->m_staticValue->isEqualTo( m_defaultValue.get() );
		;
	}
	else
	{
		for( ValuePlug::Iterator it( this ); !it.done(); ++it )
		{
			if( !(*it)->isSetToDefault() )
			{
				return false;
			}
		}
		return true;
	}
}

void ValuePlug::resetDefault()
{
	if( m_defaultValue != nullptr )
	{
		IECore::ConstObjectPtr newDefault = getObjectValue();
		IECore::ConstObjectPtr oldDefault = m_defaultValue;
		Action::enact(
			this,
			[this, newDefault] () {
				this->m_defaultValue = newDefault;
				propagateDirtiness( this );
			},
			[this, oldDefault] () {
				this->m_defaultValue = oldDefault;
				propagateDirtiness( this );
			}
		);
	}
	else
	{
		for( auto c : ValuePlug::Range( *this ) )
		{
			c->resetDefault();
		}
	}
}

IECore::MurmurHash ValuePlug::defaultHash() const
{
	if( m_defaultValue != nullptr )
	{
		return m_defaultValue->hash();
	}
	else
	{
		IECore::MurmurHash h;
		for( ValuePlug::Iterator it( this ); !it.done(); ++it )
		{
			h.append( (*it)->defaultHash() );
		}
		return h;
	}
}

IECore::MurmurHash ValuePlug::hash() const
{
	if( !m_staticValue )
	{
		// We don't store or compute our own value - we're just
		// being used as a parent for other ValuePlugs. So
		// return the combined hashes of our children.
		IECore::MurmurHash result;
		for( ValuePlug::Iterator it( this ); !it.done(); ++it )
		{
			(*it)->hash( result );
		}
		return result;
	}

	return HashProcess::hash( this );
}

void ValuePlug::hash( IECore::MurmurHash &h ) const
{
	h.append( hash() );
}

const IECore::Object *ValuePlug::defaultObjectValue() const
{
	return m_defaultValue.get();
}

IECore::ConstObjectPtr ValuePlug::getValueInternal( const IECore::MurmurHash *precomputedHash ) const
{
	return ComputeProcess::value( this, precomputedHash );
}

void ValuePlug::setObjectValue( IECore::ConstObjectPtr value )
{
	bool haveInput = getInput();
	if( direction()==In && !haveInput )
	{
		// input plug with no input connection. there can only ever be a single value,
		// which we store directly on the plug. when setting this we need to take care
		// of undo, and also of triggering the plugValueSet signal and propagating the
		// plugDirtiedSignal.

		if( value->isNotEqualTo( m_staticValue.get() ) )
		{
			Action::enact( new SetValueAction( this, value ) );
		}

		return;
	}

	// An input plug with an input connection or an output plug. We must be currently in a computation
	// triggered by getObjectValue() for a setObjectValue() call to be valid (receiveResult will check this).
	// We never trigger plugValueSet or plugDirtiedSignals during computation.
	ComputeProcess::receiveResult( this, value );
}

void ValuePlug::setValueInternal( IECore::ConstObjectPtr value, bool propagateDirtiness )
{
	m_staticValue = value;

	// it is important that we emit the plug set signal before
	// we emit dirty signals. this is because the node may wish to
	// perform some internal setup when plugs are set, and listeners
	// on output plugs may pull to get new output values as soon as
	// the dirty signal is emitted.
	emitPlugSet();

	if( propagateDirtiness )
	{
		Plug::propagateDirtiness( this );
	}
}

void ValuePlug::emitPlugSet()
{
	if( Node *n = node() )
	{
		Plug *p = this;
		while( p )
		{
			n->plugSetSignal()( p );
			p = p->parent<Plug>();
		}
	}

	// take a copy of the outputs, owning a reference - because who
	// knows what will be added and removed by the connected slots.
	std::vector<PlugPtr> o( outputs().begin(), outputs().end() );
	for( std::vector<PlugPtr>::const_iterator it=o.begin(), eIt=o.end(); it!=eIt; ++it )
	{
		if( ValuePlug *output = IECore::runTimeCast<ValuePlug>( it->get() ) )
		{
			output->emitPlugSet();
		}
	}
}

void ValuePlug::parentChanged( Gaffer::GraphComponent *oldParent )
{
	Plug::parentChanged( oldParent );

	// Addition or removal of a child is considered to change a plug's value,
	// so we emit the appropriate signal. This is mostly of use for the
	// SplinePlug and CompoundDataPlug, where points and data members
	// are added and removed by adding and removing plugs.
	if( auto p = IECore::runTimeCast<ValuePlug>( oldParent ) )
	{
		p->emitPlugSet();
	}
	if( auto p = parent<ValuePlug>() )
	{
		p->emitPlugSet();
	}
}

void ValuePlug::dirty()
{
	// All entries in the hash cache for this plug are now invalid.
	// Increment `m_dirtyCount` so that we won't try to reuse them.
	// The invalid entries will be evicted by the LRU rules in due
	// course.
	m_dirtyCount = std::min( DIRTY_COUNT_RANGE_MAX, m_dirtyCount + 1 );

	HashProcess::dirtyLegacyCache();
}

size_t ValuePlug::getCacheMemoryLimit()
{
	return ComputeProcess::getCacheMemoryLimit();
}

void ValuePlug::setCacheMemoryLimit( size_t bytes )
{
	ComputeProcess::setCacheMemoryLimit( bytes );
}

size_t ValuePlug::cacheMemoryUsage()
{
	return ComputeProcess::cacheMemoryUsage();
}

void ValuePlug::clearCache()
{
	ComputeProcess::clearCache();
}

size_t ValuePlug::getHashCacheSizeLimit()
{
	return HashProcess::getCacheSizeLimit();
}

void ValuePlug::setHashCacheSizeLimit( size_t maxEntriesPerThread )
{
	HashProcess::setCacheSizeLimit( maxEntriesPerThread );
}

void ValuePlug::clearHashCache( bool now )
{
	HashProcess::clearCache( now );
}

size_t ValuePlug::hashCacheTotalUsage()
{
	return HashProcess::totalCacheUsage();
}

void ValuePlug::setHashCacheMode( ValuePlug::HashCacheMode hashCacheMode )
{
	HashProcess::setHashCacheMode( hashCacheMode );
}

ValuePlug::HashCacheMode ValuePlug::getHashCacheMode()
{
	return HashProcess::getHashCacheMode();
}

const IECore::InternedString &ValuePlug::hashProcessType()
{
	static IECore::InternedString g_hashProcessType( "computeNode:hash" );
	return g_hashProcessType;
}

const IECore::InternedString &ValuePlug::computeProcessType()
{
	static IECore::InternedString g_computeProcessType( "computeNode:compute" );
	return g_computeProcessType;
}
