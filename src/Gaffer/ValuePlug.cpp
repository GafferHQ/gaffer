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
#include "Gaffer/Private/IECorePreview/ParallelAlgo.h"
#include "Gaffer/Process.h"

#include "boost/bind.hpp"
#include "boost/format.hpp"

#include "tbb/enumerable_thread_specific.h"

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
	const IECore::TypeId typeId = p->typeId();

	const ValuePlug *in = p->getInput<ValuePlug>();
	while( in && in->typeId() == typeId )
	{
		p = in;
		in = p->getInput<ValuePlug>();
	}

	return p;
}

const IECore::MurmurHash g_nullHash;

#if TBB_INTERFACE_VERSION < 10003

// A bug in TBB means that `TaskMutex::execute( f )` cannot guarantee that `f` is
// called on the current thread (see TaskMutex for details). This means that
// `LRUCache::get()` may end up invoking the cache getter on a different thread,
// but only when `CachePolicy==TaskCollaboration`. We use this horrible little
// workaround to ensure that we transfer over the correct ThreadState into the
// getter.
class ThreadStateFixer
{

	public :

		ThreadStateFixer( ValuePlug::CachePolicy cachePolicy )
			:	m_threadState( cachePolicy == ValuePlug::CachePolicy::TaskCollaboration ? &ThreadState::current() : nullptr )
		{
		}

		struct Scope : public ThreadState::Scope
		{
			Scope( const ThreadStateFixer &f )
				:	ThreadState::Scope( *f.m_threadState )
			{
			}
		};

	private :

		const ThreadState *m_threadState;

};

#else

// No-op version of ThreadStateFixer for use with modern TBB. All official
// Gaffer builds use this code path because GafferHQ/dependencies is following
// VFXPlatform reasonably closely.
struct ThreadStateFixer
{

	ThreadStateFixer( ValuePlug::CachePolicy cachePolicy )
	{
	}

	struct Scope
	{
		Scope( const ThreadStateFixer &f )
		{
		}
	};

};

#endif

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
	HashCacheKey( const ValuePlug *plug, const Context *context )
		:	plug( plug ), contextHash( context->hash() )
	{
	}

	bool operator == ( const HashCacheKey &other ) const
	{
		return other.plug == plug && other.contextHash == contextHash;
	}

	const ValuePlug *plug;
	IECore::MurmurHash contextHash;

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
	return result;
}

// Derives from HashCacheKey, adding on everything we need to
// construct a HashProcess. We access our caches via this augmented
// key so that we have all the information we need in our getter
// functions.
//
// Note the requirements the LRUCache places on a GetterKey like this :
// "it must be implicitly castable to Key, and all GetterKeys
// which yield the same Key must also yield the same results
// from the GetterFunction". We meet these requirements as follows :
//
// - `computeNode` and `cachePolicy` are properties of the plug which
//   is included in the HashCacheKey. We store them explicitly only
//   for convenience and performance.
// - `context` is represented in HashCacheKey via `contextHash`.
// - `destinationPlug` does not influence the results of the computation
//   in any way. It is merely used for error reporting.
struct HashProcessKey : public HashCacheKey
{
	HashProcessKey( const ValuePlug *plug, const ValuePlug *destinationPlug, const Context *context, const ComputeNode *computeNode, ValuePlug::CachePolicy cachePolicy )
		:	HashCacheKey( plug, context ),
			destinationPlug( destinationPlug ),
			computeNode( computeNode ),
			cachePolicy( cachePolicy ),
			threadStateFixer( cachePolicy )
	{
	}

	const ValuePlug *destinationPlug;
	const ComputeNode *computeNode;
	const ValuePlug::CachePolicy cachePolicy;
	const ThreadStateFixer threadStateFixer;
};

// Avoids LRUCache overhead for non-collaborative policies.
bool spawnsTasks( const HashProcessKey &key )
{
	return key.cachePolicy == ValuePlug::CachePolicy::TaskCollaboration;
}

} // namespace

class ValuePlug::HashProcess : public Process
{

	public :

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

			const ComputeNode *computeNode = IECore::runTimeCast<const ComputeNode>( p->node() );
			const HashProcessKey processKey( p, plug, Context::current(), computeNode, computeNode ? computeNode->hashCachePolicy( p ) : CachePolicy::Uncached );

			if( processKey.cachePolicy == CachePolicy::Uncached )
			{
				HashProcess process( processKey );
				return process.m_result;
			}
			else
			{
				// Perform any pending adjustments to our thread-local cache.

				ThreadData &threadData = g_threadData.local();
				if( threadData.clearCache )
				{
					threadData.cache.clear();
					threadData.clearCache = 0;
				}

				if( threadData.cache.getMaxCost() != g_cacheSizeLimit )
				{
					threadData.cache.setMaxCost( g_cacheSizeLimit );
				}

				// And then look up the result in our cache.

				try
				{
					return threadData.cache.get( processKey );
				}
				catch( ... )
				{
					ProcessException::wrapCurrentException( processKey.plug, Context::current(), staticType );
				}
			}
		}

		static size_t getCacheSizeLimit()
		{
			return g_cacheSizeLimit;
		}

		static void setCacheSizeLimit( size_t maxEntriesPerThread )
		{
			g_cacheSizeLimit = maxEntriesPerThread;
			g_globalCache.setMaxCost( g_cacheSizeLimit );
		}

		static void clearCache()
		{
			g_globalCache.clear();
			// The docs for enumerable_thread_specific aren't particularly clear
			// on whether or not it's ok to iterate an e_t_s while concurrently using
			// local(), which is what we do here. So far in practice it seems to be
			// OK.
			tbb::enumerable_thread_specific<ThreadData>::iterator it, eIt;
			for( it = g_threadData.begin(), eIt = g_threadData.end(); it != eIt; ++it )
			{
				// We can't clear the cache now, because it is most likely
				// in use by the owning thread. Instead we set this flag to
				// politely request that the thread clears the cache itself
				// at its earliest convenience - in the HashProcess constructor.
				// This delay in clearing is OK, because it is illegal to modify
				// a graph while a computation is being performed with it, and
				// we know that the plug requesting the clear will be removed
				// from the cache before the next computation starts.
				it->clearCache = 1;
			}
		}

		static const IECore::InternedString staticType;

	private :

		HashProcess( const HashProcessKey &key )
			:	Process( staticType, key.plug, key.destinationPlug )
		{
			try
			{
				if( !key.computeNode )
				{
					throw IECore::Exception( "Plug has no ComputeNode." );
				}

				key.computeNode->hash( key.plug, context(), m_result );

				if( m_result == g_nullHash )
				{
					throw IECore::Exception( "ComputeNode::hash() not implemented." );
				}
			}
			catch( ... )
			{
				handleException();
			}
		}

		static IECore::MurmurHash globalCacheGetter( const HashProcessKey &key, size_t &cost )
		{
			try
			{
				cost = 1;
				IECore::MurmurHash result;
				switch( key.cachePolicy )
				{
					case CachePolicy::TaskCollaboration :
					{
						ThreadStateFixer::Scope scope( key.threadStateFixer );
						HashProcess process( key );
						result = process.m_result;
						break;
					}
					case CachePolicy::TaskIsolation :
					{
						IECorePreview::ParallelAlgo::isolate(
							[&result, &key] {
								HashProcess process( key );
								result = process.m_result;
							}
						);
						break;
					}
					default :
						// Cache policy not valid for global cache.
						assert( false );
						break;
				}

				return result;
			}
			catch( const ProcessException &e )
			{
				// See comments in `ComputeProcess::cacheGetter()`
				e.rethrowUnwrapped();
			}
		}

		static IECore::MurmurHash localCacheGetter( const HashProcessKey &key, size_t &cost )
		{
			try
			{
				cost = 1;
				switch( key.cachePolicy )
				{
					case CachePolicy::TaskCollaboration :
					case CachePolicy::TaskIsolation :
						return g_globalCache.get( key );
					default :
					{
						assert( key.cachePolicy != CachePolicy::Uncached );
						HashProcess process( key );
						return process.m_result;
					}
				}
			}
			catch( const ProcessException &e )
			{
				// See comments in `ComputeProcess::cacheGetter()`
				e.rethrowUnwrapped();
			}
		}

		// Global cache. We use this for heavy hash computations that will spawn subtasks,
		// so that the work and the result is shared among all threads.
		typedef IECorePreview::LRUCache<HashCacheKey, IECore::MurmurHash, IECorePreview::LRUCachePolicy::TaskParallel, HashProcessKey> GlobalCache;
		static GlobalCache g_globalCache;

		// Per-thread cache. This is our default cache, used for hash computations that are
		// presumed to be lightweight. Using a per-thread cache limits the contention among
		// threads.
		typedef IECorePreview::LRUCache<HashCacheKey, IECore::MurmurHash, IECorePreview::LRUCachePolicy::Serial, HashProcessKey> Cache;

		struct ThreadData
		{
			ThreadData() : cache( localCacheGetter, g_cacheSizeLimit ), clearCache( 0 ) {}
			Cache cache;
			// Flag to request that hashCache be cleared.
			tbb::atomic<int> clearCache;
		};

		static tbb::enumerable_thread_specific<ThreadData, tbb::cache_aligned_allocator<ThreadData>, tbb::ets_key_per_instance > g_threadData;
		static tbb::atomic<size_t> g_cacheSizeLimit;

		IECore::MurmurHash m_result;

};

const IECore::InternedString ValuePlug::HashProcess::staticType( "computeNode:hash" );
tbb::enumerable_thread_specific<ValuePlug::HashProcess::ThreadData, tbb::cache_aligned_allocator<ValuePlug::HashProcess::ThreadData>, tbb::ets_key_per_instance > ValuePlug::HashProcess::g_threadData;
// Default limit corresponds to a cost of roughly 25Mb per thread.
tbb::atomic<size_t> ValuePlug::HashProcess::g_cacheSizeLimit = 128000;
ValuePlug::HashProcess::GlobalCache ValuePlug::HashProcess::g_globalCache( globalCacheGetter, g_cacheSizeLimit );

//////////////////////////////////////////////////////////////////////////
// The ComputeProcess manages the task of calling ComputeNode::compute()
// and storing a cache of recently computed results.
//////////////////////////////////////////////////////////////////////////

namespace
{

// Contains everything needed to create a ComputeProcess. We access our
// cache via this key so that we have all the information we need in our getter
// function.
struct ComputeProcessKey
{
	ComputeProcessKey( const ValuePlug *plug, const ValuePlug *destinationPlug, const ComputeNode *computeNode, ValuePlug::CachePolicy cachePolicy, const IECore::MurmurHash *precomputedHash )
		:	plug( plug ),
			destinationPlug( destinationPlug ),
			computeNode( computeNode ),
			cachePolicy( cachePolicy ),
			threadStateFixer( cachePolicy ),
			m_hash( precomputedHash ? *precomputedHash : IECore::MurmurHash() )
	{
	}

	const ValuePlug *plug;
	const ValuePlug *destinationPlug;
	const ComputeNode *computeNode;
	const ValuePlug::CachePolicy cachePolicy;
	const ThreadStateFixer threadStateFixer;

	operator const IECore::MurmurHash &() const
	{
		if( m_hash == g_nullHash )
		{
			m_hash = plug->hash();
		}
		return m_hash;
	}

	private :

		mutable IECore::MurmurHash m_hash;

};

// Avoids LRUCache overhead for non-collaborative policies.
bool spawnsTasks( const ComputeProcessKey &key )
{
	return key.cachePolicy == ValuePlug::CachePolicy::TaskCollaboration;
}

} // namespace

class ValuePlug::ComputeProcess : public Process
{

	public :

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

			if( !p->getInput() )
			{
				if( p->direction()==In || !IECore::runTimeCast<const ComputeNode>( p->node() ) )
				{
					// No input connection, and no means of computing
					// a value. There can only ever be a single value,
					// which is stored directly on the plug.
					return p->m_staticValue;
				}
			}

			// A plug with an input connection or an output plug on a ComputeNode. There can be many values -
			// one per context, computed via ComputeNode::compute(). Pull the value out of our cache, or compute
			// it with a ComputeProcess.

			const ComputeNode *computeNode = IECore::runTimeCast<const ComputeNode>( p->node() );
			const ComputeProcessKey processKey( p, plug, computeNode, computeNode ? computeNode->computeCachePolicy( p ) : CachePolicy::Uncached, precomputedHash );

			if( processKey.cachePolicy == CachePolicy::Uncached )
			{
				return ComputeProcess( processKey ).m_result;
			}
			else
			{
				IECore::ConstObjectPtr result;
				try
				{
					result = g_cache.get( processKey );
				}
				catch( ... )
				{
					// See comments in `cacheGetter()`
					ProcessException::wrapCurrentException( processKey.plug, Context::current(), staticType );
				}

				if( result )
				{
					return result;
				}
				else
				{
					// Legacy code path, necessary until all task-spawning computes have
					// declared an appropriate cache policy. We can't perform the compute
					// inside `cacheGetter()` because that is called from inside a lock. If
					// tasks were spawned without being isolated, TBB could steal an outer
					// task which tries to get the same item from the cache, leading to deadlock.
					assert( processKey.cachePolicy == CachePolicy::Legacy );
					ComputeProcess process( processKey );
					// Store the value in the cache, after first checking that this hasn't
					// been done already. The check is useful because it's common for an
					// upstream compute triggered by us to have already
					// done the work, and calling memoryUsage() can be very expensive for some
					// datatypes. A prime example of this is the attribute state passed around
					// in GafferScene - it's common for a selective filter to mean that the
					// attribute compute is implemented as a pass-through (thus an upstream node
					// will already have computed the same result) and the attribute data itself
					// consists of many small objects for which computing memory usage is slow.
					/// \todo Accessing the LRUCache multiple times like this does have an
					/// overhead, and at some point we'll need to address that.
					if( !g_cache.get( processKey ) )
					{
						g_cache.set( processKey, process.m_result, process.m_result->memoryUsage() );
					}
					return process.m_result;
				}
			}
		}

		static void receiveResult( const ValuePlug *plug, IECore::ConstObjectPtr result )
		{
			const Process *process = Process::current();
			if( !process || process->type() != staticType )
			{
				throw IECore::Exception( boost::str( boost::format( "Cannot set value for plug \"%s\" except during computation." ) % plug->fullName() ) );
			}

			const ComputeProcess *computeProcess = static_cast<const ComputeProcess *>( process );
			if( computeProcess->plug() != plug )
			{
				throw IECore::Exception( boost::str( boost::format( "Cannot set value for plug \"%s\" during computation for plug \"%s\"." ) % plug->fullName() % computeProcess->plug()->fullName() ) );
			}

			const_cast<ComputeProcess *>( computeProcess )->m_result = result;
		}

		static const IECore::InternedString staticType;

	private :

		ComputeProcess( const ComputeProcessKey &key )
			:	Process( staticType, key.plug, key.destinationPlug )
		{
			try
			{
				if( const ValuePlug *input = key.plug->getInput<ValuePlug>() )
				{
					// Cast is ok, because we know that the resulting setValue() call won't
					// actually modify the plug, but will just place the value in our m_result.
					const_cast<ValuePlug *>( key.plug )->setFrom( input );
				}
				else
				{
					if( !key.computeNode )
					{
						throw IECore::Exception( "Plug has no ComputeNode." );
					}
					// Cast is ok - see comment above.
					key.computeNode->compute( const_cast<ValuePlug *>( key.plug ), context() );
				}
				// The calls above should cause setValue() to be called on the result plug, which in
				// turn will call ValuePlug::setObjectValue(), which will then store the result in
				// the current ComputeProcess by calling receiveResult(). If that hasn't happened then
				// something has gone wrong and we should complain about it.
				if( !m_result )
				{
					throw IECore::Exception( "Compute did not set plug value." );
				}
			}
			catch( ... )
			{
				handleException();
			}
		}

		static IECore::ConstObjectPtr cacheGetter( const ComputeProcessKey &key, size_t &cost )
		{
			try
			{
				IECore::ConstObjectPtr result;
				switch( key.cachePolicy )
				{
					case CachePolicy::Standard :
					{
						ComputeProcess process( key );
						result = process.m_result;
						break;
					}
					case CachePolicy::TaskCollaboration :
					{
						ThreadStateFixer::Scope scope( key.threadStateFixer );
						ComputeProcess process( key );
						result = process.m_result;
						break;
					}
					case CachePolicy::TaskIsolation :
					{
						IECorePreview::ParallelAlgo::isolate(
							[&result, &key] {
								ComputeProcess process( key );
								result = process.m_result;
							}
						);
						break;
					}
					case CachePolicy::Uncached :
						// Should not have got here.
						assert( false );
						break;
					default :
						// Can't do the work inside the cache, because we don't know if
						// the compute will lead to deadlock. We'll do the work outside.
						break;
				}
				// Using max size for legacy policy so that our null result will never be
				// cached. This avoids `assert( processKey.cachePolicy == CachePolicy::Legacy )`
				// being triggered in `ComputeProcess::value()` when a plug with a legacy
				// policy implements a pass-through from a plug with non-legacy policy.
				cost = result ? result->memoryUsage() : std::numeric_limits<size_t>::max();
				return result;
			}
			catch( const ProcessException &processException )
			{
				// The LRUCache caches any exceptions thrown by its getter.
				// But the ProcessException thrown by `Process::handleException()`
				// is unsuitable for caching because :
				//
				// - There isn't a one-to-one mapping between processes and cache
				//   entries (different plugs can share the same entry).
				// - ProcessException stores the plug name for return from `what()`,
				//   but the plug may be renamed.
				// - ProcessException holds a reference to the plug, and we don't
				//   want the cache to extend the plug's lifetime.
				//
				// So we unwrap the exception here and rewrap it at the call site of
				// `LRUCache::get()`.
				processException.rethrowUnwrapped();
			}
		}

		// A cache mapping from ValuePlug::hash() to the result of the previous computation
		// for that hash. This allows us to cache results for faster repeat evaluation
		typedef IECorePreview::LRUCache<IECore::MurmurHash, IECore::ConstObjectPtr, IECorePreview::LRUCachePolicy::TaskParallel, ComputeProcessKey> Cache;
		static Cache g_cache;

		IECore::ConstObjectPtr m_result;

};

const IECore::InternedString ValuePlug::ComputeProcess::staticType( "computeNode:compute" );
ValuePlug::ComputeProcess::Cache ValuePlug::ComputeProcess::g_cache( cacheGetter, 1024 * 1024 * 1024 * 1 ); // 1 gig

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

GAFFER_PLUG_DEFINE_TYPE( ValuePlug );

/// \todo We may want to avoid repeatedly storing copies of the same default value
/// passed to this function. Perhaps by having a central map of unique values here,
/// or by doing it more intelligently in the derived classes (where we could avoid
/// even creating the values before figuring out if we've already got them somewhere).
ValuePlug::ValuePlug( const std::string &name, Direction direction,
	IECore::ConstObjectPtr defaultValue, unsigned flags )
	:	Plug( name, direction, flags ), m_defaultValue( defaultValue ), m_staticValue( defaultValue )
{
	assert( m_defaultValue );
	assert( m_staticValue );
}

ValuePlug::ValuePlug( const std::string &name, Direction direction, unsigned flags )
	:	Plug( name, direction, flags ), m_defaultValue( nullptr ), m_staticValue( nullptr )
{
}

ValuePlug::~ValuePlug()
{
	// Clear hash cache, so that a newly created plug that just
	// happens to reuse our address won't end up inadvertently also
	// reusing our cache entries.
	HashProcess::clearCache();
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
	for( PlugIterator it( this ); !it.done(); ++it )
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
		for( ValuePlugIterator it( this ); !it.done(); ++it )
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
		for( ValuePlugIterator it( this ); !it.done(); ++it )
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
		for( ValuePlugIterator it( this ); !it.done(); ++it )
		{
			if( !(*it)->isSetToDefault() )
			{
				return false;
			}
		}
		return true;
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
		for( ValuePlugIterator it( this ); !it.done(); ++it )
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

IECore::ConstObjectPtr ValuePlug::getObjectValue( const IECore::MurmurHash *precomputedHash ) const
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
	/// \todo We might want to investigate methods of doing a
	/// more fine grained clearing of only the dirtied plugs,
	/// rather than clearing the whole cache.
	HashProcess::clearCache();
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
