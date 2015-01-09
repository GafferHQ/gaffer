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

#include <stack>

#include "tbb/enumerable_thread_specific.h"

#include "boost/bind.hpp"
#include "boost/format.hpp"
#include "boost/unordered_map.hpp"

#include "IECore/LRUCache.h"

#include "Gaffer/ValuePlug.h"
#include "Gaffer/ComputeNode.h"
#include "Gaffer/Context.h"
#include "Gaffer/Action.h"

using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
//
// The computation class is responsible for managing calls to
// ComputeNode::hash(), ComputNode::compute() and Plug::setFrom()
// in order to acquire the output values for plugs. It manages a
// per-thread stack of current computations, and caches the results of
// previous computations to avoid repeating work.
//
// In the future we might consider abstracting the basic concept of
// a computation and allowing different implementations - perhaps even
// network based ones.
//
//////////////////////////////////////////////////////////////////////////

class ValuePlug::Computation
{

	public :

		const ValuePlug *resultPlug() const
		{
			return m_resultPlug;
		}

		static IECore::MurmurHash hash( const ValuePlug *plug )
		{
			const ValuePlug *p = sourcePlug( plug );

			if( !p->getInput<Plug>() )
			{
				if( p->direction() == In || !p->ancestor<ComputeNode>() )
				{
					// no input connection, and no means of computing
					// a value. there can only ever be a single value,
					// which is stored directly on the plug - so we return
					// the hash of that.
					return p->m_staticValue->hash();
				}
			}

			// a plug with an input connection or an output plug on a ComputeNode. there can be many values -
			// one per context. the computation class is responsible for figuring out the hash.
			Computation computation( p );
			try
			{
				return computation.hash();
			}
			catch( const std::exception &e )
			{
				computation.m_threadData->errorSource = computation.m_threadData->errorSource ? computation.m_threadData->errorSource : p;
				emitError( plug, p, computation.m_threadData->errorSource, e.what() );
				throw;
			}
			catch( ... )
			{
				computation.m_threadData->errorSource = computation.m_threadData->errorSource ? computation.m_threadData->errorSource : p;
				emitError( plug, p, computation.m_threadData->errorSource, "Unknown error" );
				throw;
			}
		}

		static IECore::ConstObjectPtr value( const ValuePlug *plug, const IECore::MurmurHash *precomputedHash )
		{
			const ValuePlug *p = sourcePlug( plug );

			if( !p->getInput<Plug>() )
			{
				if( p->direction()==In || !p->ancestor<ComputeNode>() )
				{
					// no input connection, and no means of computing
					// a value. there can only ever be a single value,
					// which is stored directly on the plug.
					return p->m_staticValue;
				}
			}

			// an plug with an input connection or an output plug on a ComputeNode. there can be many values -
			// one per context. the computation class is responsible for providing storage for the result
			// and also actually managing the computation.
			Computation computation( p, precomputedHash );
			try
			{
				return computation.value();
			}
			catch( const std::exception &e )
			{
				computation.m_threadData->errorSource = computation.m_threadData->errorSource ? computation.m_threadData->errorSource : p;
				emitError( plug, p, computation.m_threadData->errorSource, e.what() );
				throw;
			}
			catch( ... )
			{
				computation.m_threadData->errorSource = computation.m_threadData->errorSource ? computation.m_threadData->errorSource : p;
				emitError( plug, p, computation.m_threadData->errorSource, "Unknown error" );
				throw;
			}
		}

		static void receiveResult( const ValuePlug *plug, IECore::ConstObjectPtr result )
		{
			Computation *computation = Computation::current();
			if( !computation )
			{
				throw IECore::Exception( boost::str( boost::format( "Cannot set value for plug \"%s\" except during computation." ) % plug->fullName() ) );
			}

			if( computation->m_resultPlug != plug )
			{
				throw IECore::Exception( boost::str( boost::format( "Cannot set value for plug \"%s\" during computation for plug \"%s\"." ) % plug->fullName() % computation->m_resultPlug->fullName() ) );
			}

			computation->m_resultValue = result;
		}

		static Computation *current()
		{
			ComputationStack &s = g_threadData.local().computationStack;
			if( !s.size() )
			{
				return 0;
			}
			return s.top();
		}

		static size_t getCacheMemoryLimit()
		{
			return g_valueCache.getMaxCost();
		}

		static void setCacheMemoryLimit( size_t bytes )
		{
			return g_valueCache.setMaxCost( bytes );
		}

		static size_t cacheMemoryUsage()
		{
			return g_valueCache.currentCost();
		}

	private :

		Computation( const ValuePlug *resultPlug, const IECore::MurmurHash *precomputedHash = NULL )
			:	m_resultPlug( resultPlug ), m_precomputedHash( precomputedHash ), m_resultValue( NULL ), m_threadData( &g_threadData.local() )
		{
			m_threadData->computationStack.push( this );
		}

		~Computation()
		{
			m_threadData->computationStack.pop();
			if( m_threadData->computationStack.empty() )
			{
				m_threadData->hashCache.clear();
				m_threadData->errorSource = NULL;
			}
		}

		// Before using the Computation class to get a hash or a value,
		// we first traverse back down the chain of input plugs to the
		// start, or till we find a plug of a different type. This
		// traversal is much quicker than using the Computation class
		// for every step in the chain.
		static inline const ValuePlug *sourcePlug( const ValuePlug *p )
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

		IECore::MurmurHash hash() const
		{
			if( m_precomputedHash )
			{
				return *m_precomputedHash;
			}

			HashCache &hashCache = m_threadData->hashCache;
			HashCacheKey key( m_resultPlug, Context::current()->hash() );
			HashCache::iterator it = hashCache.find( key );
			if( it != hashCache.end() )
			{
				return it->second;
			}

			IECore::MurmurHash h = hashInternal();
			hashCache[key] = h;
			return h;
		}

		IECore::ConstObjectPtr value()
		{
			// do the cache lookup/computation.
			if( m_resultPlug->getFlags( Plug::Cacheable ) )
			{
				IECore::MurmurHash hash = this->hash();
				m_resultValue = g_valueCache.get( hash );
				if( !m_resultValue )
				{
					computeOrSetFromInput();

					// Store the value in the cache, after first checking that this hasn't
					// been done already. The check is useful because it's common for an
					// upstream compute triggered by computeOrSetFromInput() to have already
					// done the work, and calling memoryUsage() can be very expensive for some
					// datatypes. A prime example of this is the attribute state passed around
					// in GafferScene - it's common for a selective filter to mean that the
					// attribute compute is implemented as a pass-through (thus an upstream node
					// will already have computed the same result) and the attribute data itself
					// consists of many small objects for which computing memory usage is slow.
					/// \todo Accessing the LRUCache multiple times like this does have an
					/// overhead, and at some point we'll need to address that.
					/// Perhaps we can augment our HashCache to also store computed values
					/// temporarily - because the HashCache is per-thread, this would avoid
					/// the locking associated with LRUCache::get().
					if( !g_valueCache.get( hash ) )
					{
						g_valueCache.set( hash, m_resultValue, m_resultValue->memoryUsage() );
					}
				}
			}
			else
			{
				// plug has requested no caching, so we compute from scratch every
				// time.
				computeOrSetFromInput();
			}

			return m_resultValue;
		}

		// Calculates the hash for m_resultPlug - not using any cache at all.
		IECore::MurmurHash hashInternal() const
		{
			if( const ValuePlug *input = m_resultPlug->getInput<ValuePlug>() )
			{
				// We know that the input is of a different type to m_resultPlug,
				// because that is guaranteed by sourcePlug(). Get the hash from
				// the input and add a little extra something to represent the
				// conversion that m_resultPlug->setFrom( input ) will perform,
				// to break apart the cache entries.
				IECore::MurmurHash h = input->hash();
				h.append( input->typeId() );
				h.append( m_resultPlug->typeId() );
				return h;
			}
			else
			{
				const ComputeNode *n = m_resultPlug->ancestor<ComputeNode>();
				if( !n )
				{
					throw IECore::Exception( boost::str( boost::format( "Unable to compute hash for Plug \"%s\" as it has no ComputeNode." ) % m_resultPlug->fullName() ) );
				}

				IECore::MurmurHash h;
				n->hash( m_resultPlug, Context::current(), h );
				if( h == IECore::MurmurHash() )
				{
					throw IECore::Exception( boost::str( boost::format( "ComputeNode::hash() not implemented for Plug \"%s\"." ) % m_resultPlug->fullName() ) );
				}

				return h;
			}
		}

		// Fills in m_resultValue by calling ComputeNode::compute() or ValuePlug::setFrom().
		// Throws if the result was not successfully retrieved.
		void computeOrSetFromInput()
		{
			if( const ValuePlug *input = m_resultPlug->getInput<ValuePlug>() )
			{
				// cast is ok, because we know that the resulting setValue() call won't
				// actually modify the plug, but will just place the value in our m_resultValue.
				const_cast<ValuePlug *>( m_resultPlug )->setFrom( input );
			}
			else
			{
				const ComputeNode *n = m_resultPlug->ancestor<ComputeNode>();
				if( !n )
				{
					throw IECore::Exception( boost::str( boost::format( "Unable to compute value for Plug \"%s\" as it has no ComputeNode." ) % m_resultPlug->fullName() ) );
				}
				// cast is ok - see comment above.
				n->compute( const_cast<ValuePlug *>( m_resultPlug ), Context::current() );
			}

			// the calls above should cause setValue() to be called on the result plug, which in
			// turn will call ValuePlug::setObjectValue(), which will then store the result in
			// the current computation by calling receiveResult(). If that hasn't happened then
			// something has gone wrong and we should complain about it.
			if( !m_resultValue )
			{
				throw IECore::Exception( boost::str( boost::format( "Value for Plug \"%s\" not set as expected." ) % m_resultPlug->fullName() ) );
			}
		}

		// Emits Node::errorSignal() for all plugs between plug and sourcePlug (inclusive).
		static void emitError( const ValuePlug *plug, const ValuePlug *sourcePlug, const Plug *errorSource, const char *error )
		{
			while( plug )
			{
				if( plug->direction() == Plug::Out )
				{
					if( const Node *node = plug->node() )
					{
						node->errorSignal()( plug, errorSource, error );
					}
				}
				plug = plug != sourcePlug ? plug->getInput<ValuePlug>() : NULL;
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
		// We address this problem by keeping a small per-thread cache of hashes, indexed
		// by the plug the hash is for and the context the hash was performed in. The
		// typedefs below describe that data structure. Note that the entries in this cache
		// are short lived - we flush the cache upon completion of each evaluation of the
		// graph, as subsequent changes to plug values and connections invalidate our entries.
		typedef std::pair<const ValuePlug *, IECore::MurmurHash> HashCacheKey;
		typedef boost::unordered_map<HashCacheKey, IECore::MurmurHash> HashCache;

		// A computation starts with a call to ValuePlug::getValue(), but the compute()
		// that triggers will make calls to getValue() on upstream plugs too. We use this
		// stack to keep track of the current computation - each upstream evaluation pushes
		// a new entry on to the stack, and the full graph evaluation is complete when we pop
		// the last entry.
		typedef std::stack<Computation *> ComputationStack;

		// To support multithreading, each thread has it's own state.
		struct ThreadData
		{
			ThreadData() :	errorSource( NULL ) {}
			HashCache hashCache;
			ComputationStack computationStack;
			const Plug *errorSource;
		};

		static tbb::enumerable_thread_specific<ThreadData> g_threadData;

		const ValuePlug *m_resultPlug;
		const IECore::MurmurHash *m_precomputedHash;
		IECore::ConstObjectPtr m_resultValue;
		ThreadData *m_threadData;

		static IECore::ObjectPtr nullGetter( const IECore::MurmurHash &h, size_t &cost )
		{
			cost = 0;
			return NULL;
		}

		// A cache mapping from ValuePlug::hash() to the result of the previous computation
		// for that hash. This allows us to cache results for faster repeat evaluation. Unlike
		// the HashCache, the ValueCache persists from one graph evaluation to the next.
		typedef IECore::LRUCache<IECore::MurmurHash, IECore::ConstObjectPtr> ValueCache;
		static ValueCache g_valueCache;

};

tbb::enumerable_thread_specific<ValuePlug::Computation::ThreadData> ValuePlug::Computation::g_threadData;
ValuePlug::Computation::ValueCache ValuePlug::Computation::g_valueCache( nullGetter, 1024 * 1024 * 500 );

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
	IECore::ConstObjectPtr initialValue, unsigned flags )
	:	Plug( name, direction, flags ), m_staticValue( initialValue )
{
	assert( m_staticValue );
}

ValuePlug::ValuePlug( const std::string &name, Direction direction, unsigned flags )
	:	Plug( name, direction, flags ), m_staticValue( 0 )
{
}

ValuePlug::~ValuePlug()
{
}

bool ValuePlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	if( !Plug::acceptsChild( potentialChild ) )
	{
		return false;
	}
	/// \todo Check that child is a ValuePlug - the
	/// only reason we're not doing that is for backwards
	/// compatibility with CompoundPlug.
	return m_staticValue == NULL;
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
	for( PlugIterator it( this ); it != it.end(); ++it )
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

	if( Computation *c = Computation::current() )
	{
		return c->resultPlug() == this;
	}
	else
	{
		if( direction() != Plug::In )
		{
			return false;
		}
		for( PlugIterator it( this ); it!=it.end(); ++it )
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
	for( ValuePlugIterator it( this ); it != it.end(); ++it )
	{
		(*it)->setToDefault();
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
		for( ValuePlugIterator it( this ); it!=it.end(); it++ )
		{
			(*it)->hash( result );
		}
		return result;
	}

	return Computation::hash( this );
}

void ValuePlug::hash( IECore::MurmurHash &h ) const
{
	h.append( hash() );
}

IECore::ConstObjectPtr ValuePlug::getObjectValue( const IECore::MurmurHash *precomputedHash ) const
{
	return Computation::value( this, precomputedHash );
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

	// an input plug with an input connection or an output plug. we must be currently in a computation
	// triggered by getObjectValue() for a setObjectValue() call to be valid (receiveResult will check this).
	// we never trigger plugValueSet or plugDirtiedSignals during computation.
	Computation::receiveResult( this, value );
}

bool ValuePlug::inCompute() const
{
	return Computation::current();
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
		DependencyNode::propagateDirtiness( this );
	}
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

size_t ValuePlug::getCacheMemoryLimit()
{
	return Computation::getCacheMemoryLimit();
}

void ValuePlug::setCacheMemoryLimit( size_t bytes )
{
	Computation::setCacheMemoryLimit( bytes );
}

size_t ValuePlug::cacheMemoryUsage()
{
	return Computation::cacheMemoryUsage();
}
