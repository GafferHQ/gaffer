//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/ValuePlug.h"
#include "Gaffer/Node.h"
#include "Gaffer/Context.h"
#include "Gaffer/Action.h"

using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Computation implementation
// The computation class is responsible for managing the transient storage
// necessary for computed results, and for managing the call to Node::compute().
// One day it may also be responsible for managing a cache of previous
// results and maybe even shipping some computations off over the network
// to a special computation server of some sort.
//////////////////////////////////////////////////////////////////////////

class ValuePlug::Computation
{
	
	public :
	
		Computation( const ValuePlug *resultPlug )
			:	m_resultPlug( resultPlug ), m_resultWritten( false )
		{
			g_threadComputations.local().push( this );
		
			if( m_resultPlug->getInput<Plug>() )
			{
				// cast is ok, because we know that the resulting setValue() call won't
				// actually modify the plug, but will just place the value in our m_resultValue.
				const_cast<ValuePlug *>( m_resultPlug )->setFromInput();
			}
			else
			{
				assert( m_resultPlug->direction()==Out );
				const Node *n = m_resultPlug->node();
				if( !n )
				{
					throw IECore::Exception( boost::str( boost::format( "Unable to compute value for orphan Plug \"%s\"." ) % m_resultPlug->fullName() ) );			
				}
				// cast is ok, because we know that the resulting setValue() call won't
				// actually modify the plug, but will just place the value in our m_resultValue.
				n->compute( const_cast<ValuePlug *>( m_resultPlug ), Context::current() );
			}
			
			// the call to compute() or setFromInput() above should cause setValue() to be called
			// on the result plug, which in turn will call ValuePlug::setObjectValue, which will
			// then store the result in the current computation.
			
		}
		
		~Computation()
		{
			g_threadComputations.local().pop();
		}
	
		static Computation *current()
		{
			ComputationStack &s = g_threadComputations.local();
			if( !s.size() )
			{
				return 0;
			}
			return s.top();
		}
	
	/// \todo Make accessors
	//private :
	
		const ValuePlug *m_resultPlug;
		IECore::ConstObjectPtr m_resultValue;
		bool m_resultWritten;

		typedef std::stack<Computation *> ComputationStack;
		typedef tbb::enumerable_thread_specific<ComputationStack> ThreadSpecificComputationStack;

		static ThreadSpecificComputationStack g_threadComputations;
		
};

ValuePlug::Computation::ThreadSpecificComputationStack ValuePlug::Computation::g_threadComputations;

//////////////////////////////////////////////////////////////////////////
// ValuePlug implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( ValuePlug );

ValuePlug::ValuePlug( const std::string &name, Direction direction, unsigned flags )
	:	Plug( name, direction, flags )
{
}

ValuePlug::~ValuePlug()
{
}

bool ValuePlug::acceptsInput( ConstPlugPtr input ) const
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
	Plug::setInput( input );
	if( input )
	{
		emitDirtiness();
		propagateDirtiness();
	}
	else
	{
		/// \todo Need to revert to default value	
	}
}

IECore::ConstObjectPtr ValuePlug::getObjectValue() const
{
	bool haveInput = getInput<Plug>();
	if( direction()==In && !haveInput )
	{
		// input plug with no input connection. there can only ever be a single value,
		// which is stored directly on the plug.
		return m_staticValue;
	}
	
	// an input plug with an input connection or an output plug. there can be many values -
	// one per context. the computation class is responsible for providing storage for the result
	// and also actually managing the computation.
	Computation computation( this );

	if( !computation.m_resultWritten )
	{
		throw IECore::Exception( boost::str( boost::format( "Value for Plug \"%s\" not set as expected." ) % fullName() ) );			
	}
	
	return computation.m_resultValue;
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
		if( ( (bool)value != (bool)m_staticValue ) ||
			( value && value->isNotEqualTo( m_staticValue ) )
		)
		{
			Action::enact( 
				this,
				boost::bind( &ValuePlug::setValueInternal, Ptr( this ), value ),
				boost::bind( &ValuePlug::setValueInternal, Ptr( this ), m_staticValue )
			);
		}		
		return;
	}

	// an input plug with an input connection or an output plug. we must be currently in a computation
	// triggered by getObjectValue() for a setObjectValue() call to be valid. we never trigger plugValueSet
	// or plugDirtiedSignals during computation.
	
	Computation *computation = Computation::current();
	if( !computation )
	{
		throw IECore::Exception( boost::str( boost::format( "Cannot set value for plug \"%s\" except during computation." ) % fullName() ) );					
	}
	
	if( computation->m_resultPlug != this )
	{
		throw IECore::Exception( boost::str( boost::format( "Cannot set value for plug \"%s\" during computation for plug \"%s\"." ) % fullName() % computation->m_resultPlug->fullName() ) );						
	}
	
	computation->m_resultValue = value;
	computation->m_resultWritten = true;
}

void ValuePlug::setValueInternal( IECore::ConstObjectPtr value )
{
	m_staticValue = value;
	Node *n = node();
	if( n )
	{
		// it is important that we emit the plug set signal before
		// we emit dirty signals for any dependent plugs. this is
		// because the node may wish to perform some internal setup when plugs
		// are set, and listeners on output plugs may pull to get new
		// output values as soon as the dirty signal is emitted. 
		n->plugSetSignal()( this );
	}
	propagateDirtiness();
}

void ValuePlug::emitDirtiness( Node *n )
{
	n = n ? n : node();
	if( !n )
	{
		return;
	}
	
	ValuePlug *p = this;
	while( p )
	{
		n->plugDirtiedSignal()( p );
		p = p->parent<ValuePlug>();
	}
}

void ValuePlug::propagateDirtiness()
{
	Node *n = node();
	if( n )
	{
		if( direction()==In )
		{
			Node::AffectedPlugsContainer affected;
			n->affects( this, affected );
			for( Node::AffectedPlugsContainer::const_iterator it=affected.begin(); it!=affected.end(); it++ )
			{
				const_cast<ValuePlug *>( *it )->emitDirtiness( n );
				const_cast<ValuePlug *>( *it )->propagateDirtiness();
			}
		}
	}
	
	for( OutputContainer::const_iterator it=outputs().begin(); it!=outputs().end(); it++ )
	{
		ValuePlugPtr o = IECore::runTimeCast<ValuePlug>( *it );
		if( o )
		{
			o->emitDirtiness();
			o->propagateDirtiness();
		}
	}
}