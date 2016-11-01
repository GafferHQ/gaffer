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

#include "tbb/enumerable_thread_specific.h"

#include "boost/bind.hpp"
#include "boost/format.hpp"
#include "boost/unordered_map.hpp"

#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "Gaffer/ValuePlug.h"
#include "Gaffer/ComputeNode.h"
#include "Gaffer/Context.h"
#include "Gaffer/Action.h"
#include "Gaffer/Process.h"

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

} // namespace

//////////////////////////////////////////////////////////////////////////
// The HashProcess manages the task of calling ComputeNode::hash() and
// managing a cache of recently computed hashes.
//////////////////////////////////////////////////////////////////////////

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
			else if( p->direction() == In || !p->ancestor<ComputeNode>() )
			{
				// No input connection, and no means of computing
				// a value. There can only ever be a single value,
				// which is stored directly on the plug - so we return
				// the hash of that.
				return p->m_staticValue->hash();
			}

			// A plug with an input connection or an output plug on a ComputeNode. There can be many values -
			// one per context, computed by ComputeNode::hash(). First we see if we can retrieve the hash
			// from our cache, and if we can't we'll compute it using a HashProcess instance.

			ThreadData &threadData = g_threadData.local();
			if( !Process::current() )
			{
				// Starting a new root computation.
				if( ++(threadData.cacheClearCount) == 3200 )
				{
					// Prevent unbounded growth in the hash cache
					// if many computations are being performed
					// without any plugs being dirtied in between,
					// by clearing it after every Nth computation.
					// N == 3200 was observed to be 6x faster than
					// N == 100 for a procedural instancing scene at
					// a memory cost of about 100 mb.
					threadData.clearCache = 1;
				}
			}

			if( threadData.clearCache )
			{
				threadData.cache.clear();
				threadData.cacheClearCount = 0;
				threadData.clearCache = 0;
			}

			const CacheKey key( p, Context::current()->hash() );
			Cache::iterator it = threadData.cache.find( key );
			if( it != threadData.cache.end() )
			{
				return it->second;
			}

			HashProcess process( p, plug );
			threadData.cache[key] = process.m_result;
			return process.m_result;
		}

		static void clearCache()
		{
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

		HashProcess( const ValuePlug *plug, const ValuePlug *downstream )
			:	Process( staticType, plug, downstream )
		{
			try
			{
				const ComputeNode *n = plug->ancestor<ComputeNode>();
				if( !n )
				{
					throw IECore::Exception( boost::str( boost::format( "Unable to compute hash for Plug \"%s\" as it has no ComputeNode." ) % plug->fullName() ) );
				}

				n->hash( plug, Context::current(), m_result );

				if( m_result == IECore::MurmurHash() )
				{
					throw IECore::Exception( boost::str( boost::format( "ComputeNode::hash() not implemented for Plug \"%s\"." ) % plug->fullName() ) );
				}
			}
			catch( ... )
			{
				handleException();
			}
		}

		// During a single graph evaluation, we actually call ValuePlug::hash()
		// many times for the same plugs. First hash() is called for the terminating plug,
		// which will call hash() for all the upstream plugs, and then compute() is called
		// for the terminating plug, which will call getValue() on the upstream plugs. But
		// those upstream plugs will need to call their hash() again in getValue(), so their
		// value can be cached. This ripples on up the chain, leading to quadratic complexity
		// in the length of the chain of nodes - not good. Thanks is due to David Minor for
		// being the first to point this out.
		//
		// We address this problem by keeping a per-thread cache of hashes, indexed
		// by the plug the hash is for and the context the hash was performed in. The
		// typedefs below describe that data structure. We use Plug::dirty() to empty
		// the caches, because they are invalidated whenever an upstream value or
		// connection is changed. We also clear the cache unconditionally every N
		// computations, to prevent unbounded growth.
		typedef std::pair<const ValuePlug *, IECore::MurmurHash> CacheKey;
		typedef boost::unordered_map<CacheKey, IECore::MurmurHash> Cache;

		// To support multithreading, each thread has it's own state.
		struct ThreadData
		{
			ThreadData() : cacheClearCount( 0 ) {}
			int cacheClearCount;
			Cache cache;
			// Flag to request that hashCache be cleared.
			tbb::atomic<int> clearCache;
		};

		static tbb::enumerable_thread_specific<ThreadData, tbb::cache_aligned_allocator<ThreadData>, tbb::ets_key_per_instance > g_threadData;

		IECore::MurmurHash m_result;

};

const IECore::InternedString ValuePlug::HashProcess::staticType( "computeNode:hash" );
tbb::enumerable_thread_specific<ValuePlug::HashProcess::ThreadData, tbb::cache_aligned_allocator<ValuePlug::HashProcess::ThreadData>, tbb::ets_key_per_instance > ValuePlug::HashProcess::g_threadData;

//////////////////////////////////////////////////////////////////////////
// The ComputeProcess manages the task of calling ComputeNode::compute()
// and storing a cache of recently computed results.
//////////////////////////////////////////////////////////////////////////

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

			if( !p->getInput<Plug>() )
			{
				if( p->direction()==In || !p->ancestor<ComputeNode>() )
				{
					// No input connection, and no means of computing
					// a value. There can only ever be a single value,
					// which is stored directly on the plug.
					return p->m_staticValue;
				}
			}

			// A plug with an input connection or an output plug on a ComputeNode. There can be many values -
			// one per context, computed via ComputeNode::compute().

			if( p->getFlags( Plug::Cacheable ) )
			{
				// First see if we've done this computation already, and reuse the
				// result if we have.
				IECore::MurmurHash hash = precomputedHash ? *precomputedHash : p->hash();
				IECore::ConstObjectPtr result = g_cache.get( hash );
				if( result )
				{
					return result;
				}

				// Otherwise, use a ComputeProcess instance to do the work.
				ComputeProcess process( p, plug );
				// Store the value in the cache, after first checking that this hasn't
				// been done already. The check is useful because it's common for an
				// upstream compute triggered by to have already
				// done the work, and calling memoryUsage() can be very expensive for some
				// datatypes. A prime example of this is the attribute state passed around
				// in GafferScene - it's common for a selective filter to mean that the
				// attribute compute is implemented as a pass-through (thus an upstream node
				// will already have computed the same result) and the attribute data itself
				// consists of many small objects for which computing memory usage is slow.
				/// \todo Accessing the LRUCache multiple times like this does have an
				/// overhead, and at some point we'll need to address that.
				if( !g_cache.get( hash ) )
				{
					g_cache.set( hash, process.m_result, process.m_result->memoryUsage() );
				}
				return process.m_result;
			}
			else
			{
				// Plug has requested no caching, so we compute from scratch every
				// time.
				return ComputeProcess( p, plug ).m_result;
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

		ComputeProcess( const ValuePlug *plug, const ValuePlug *downstream )
			:	Process( staticType, plug, downstream )
		{
			try
			{
				if( const ValuePlug *input = plug->getInput<ValuePlug>() )
				{
					// Cast is ok, because we know that the resulting setValue() call won't
					// actually modify the plug, but will just place the value in our m_result.
					const_cast<ValuePlug *>( plug )->setFrom( input );
				}
				else
				{
					const ComputeNode *n = plug->ancestor<ComputeNode>();
					if( !n )
					{
						throw IECore::Exception( boost::str( boost::format( "Unable to compute value for Plug \"%s\" as it has no ComputeNode." ) % plug->fullName() ) );
					}
					// Cast is ok - see comment above.
					n->compute( const_cast<ValuePlug *>( plug ), Context::current() );
				}
				// The calls above should cause setValue() to be called on the result plug, which in
				// turn will call ValuePlug::setObjectValue(), which will then store the result in
				// the current ComputeProcess by calling receiveResult(). If that hasn't happened then
				// something has gone wrong and we should complain about it.
				if( !m_result )
				{
					throw IECore::Exception( boost::str( boost::format( "Value for Plug \"%s\" not set as expected." ) % plug->fullName() ) );
				}
			}
			catch( ... )
			{
				handleException();
			}
		}

		static IECore::ObjectPtr nullGetter( const IECore::MurmurHash &h, size_t &cost )
		{
			cost = 0;
			return NULL;
		}

		// A cache mapping from ValuePlug::hash() to the result of the previous computation
		// for that hash. This allows us to cache results for faster repeat evaluation
		typedef IECorePreview::LRUCache<IECore::MurmurHash, IECore::ConstObjectPtr> Cache;
		static Cache g_cache;

		IECore::ConstObjectPtr m_result;

};

const IECore::InternedString ValuePlug::ComputeProcess::staticType( "computeNode:compute" );
ValuePlug::ComputeProcess::Cache ValuePlug::ComputeProcess::g_cache( nullGetter, 1024 * 1024 * 1024 * 1 ); // 1 gig

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

		virtual GraphComponent *subject() const
		{
			return m_plug.get();
		}

		virtual void doAction()
		{
			m_plug->setValueInternal( m_doValue, true );
		}

		virtual void undoAction()
		{
			m_plug->setValueInternal( m_undoValue, true );
		}

		virtual bool canMerge( const Action *other ) const
		{
			if( !Action::canMerge( other ) )
			{
				return false;
			}
			const SetValueAction *setValueAction = IECore::runTimeCast<const SetValueAction>( other );
			return setValueAction && setValueAction->m_plug == m_plug;
		}

		virtual void merge( const Action *other )
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

IE_CORE_DEFINERUNTIMETYPED( ValuePlug );

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
	:	Plug( name, direction, flags ), m_defaultValue( NULL ), m_staticValue( NULL )
{
	// We expect to have children added/removed, so arrange to deal with that
	// appropriately. The other constructor above is for leaf plugs (this is
	// enforced in acceptsChild()) so we don't need to connect there.
	childAddedSignal().connect( boost::bind( &ValuePlug::childAddedOrRemoved, this ) );
	childRemovedSignal().connect( boost::bind( &ValuePlug::childAddedOrRemoved, this ) );
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

	if( m_staticValue != NULL )
	{
		return false;
	}

	if( this->isInstanceOf( (IECore::TypeId)CompoundPlugTypeId ) )
	{
		/// \todo Remove this special case when we remove
		/// CompoundPlug - it exists only for backwards
		/// compatibility for that class. When we do this,
		/// we'll be able to remove a lot of runTimeCasts in
		/// our other methods, because we'll know our children
		/// are all ValuePlugs.
		return true;
	}
	else
	{
		return IECore::runTimeCast<const ValuePlug>( potentialChild );
	}
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
	if( input.get() == getInput<Plug>() )
	{
		return;
	}

	// set value back to what it was before
	// we received a connection. we do that
	// before calling Plug::setInput, so that
	// we've got our new state set correctly before
	// the dirty signal is emitted. we don't emit
	// in the setValueInternal call, because we don't
	// want to double up on the signals that the Plug
	// is emitting for us in Plug::setInput().
	if( !input )
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
	if( getFlags( ReadOnly ) )
	{
		return false;
	}

	if( getInput<Plug>() )
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
		for( PlugIterator it( this ); !it.done(); ++it )
		{
			ValuePlug *valuePlug = IECore::runTimeCast<ValuePlug>( it->get() );
			if( !valuePlug || !valuePlug->settable() )
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
		ValuePlug *child = IECore::runTimeCast<ValuePlug>( it->get() );
		const ValuePlug *otherChild = IECore::runTimeCast<ValuePlug>( otherIt->get() );
		if( !child || !otherChild )
		{
			throw IECore::Exception( "Children are not ValuePlugs" );
		}
		child->setFrom( otherChild );
	}
}

void ValuePlug::setToDefault()
{
	if( m_defaultValue != NULL )
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
	if( m_defaultValue != NULL )
	{
		return getObjectValue()->isEqualTo( m_defaultValue.get() );
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
	bool haveInput = getInput<Plug>();
	if( direction()==In && !haveInput )
	{
		// input plug with no input connection. there can only ever be a single value,
		// which we store directly on the plug. when setting this we need to take care
		// of undo, and also of triggering the plugValueSet signal and propagating the
		// plugDirtiedSignal.

		if( getFlags( ReadOnly ) )
		{
			// We don't allow static values to be set on read only plugs, so we throw.
			// Note that it is perfectly acceptable to call setValue() on a read only
			// plug during a computation because the result is not written onto the
			// plug itself, so we don't make the check in the case that we call
			// receiveResult() below. This allows plugs which have inputs to be made
			// read only after having their input set.
			throw IECore::Exception( boost::str( boost::format( "Cannot set value for read only plug \"%s\"" ) % fullName() ) );
		}

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

void ValuePlug::childAddedOrRemoved()
{
	// Addition or removal of a child is considered to change its value,
	// so we emit the appropriate signal. This is mostly of use for the
	// SplinePlug and CompoundDataPlug, where points and data members
	// are added and removed by adding and removing plugs.
	emitPlugSet();
}

void ValuePlug::emitPlugSet()
{
	if( Node *n = node() )
	{
		ValuePlug *p = this;
		while( p )
		{
			n->plugSetSignal()( p );
			p = p->parent<ValuePlug>();
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
