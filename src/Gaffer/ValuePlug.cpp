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

#include "boost/format.hpp"

#include "Gaffer/ValuePlug.h"
#include "Gaffer/Node.h"
#include "Gaffer/Context.h"

using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Storage implementation
//////////////////////////////////////////////////////////////////////////

struct Storage : IECore::RefCounted
{
	
	IE_CORE_DECLAREMEMBERPTR( Storage )
	
	Storage( Plug *plug )
		:	m_plug( plug ), m_written( false )
	{
	}
	
	Plug *m_plug;
	IECore::ObjectPtr m_storage;
	bool m_written;
		
};

IE_CORE_DECLAREPTR( Storage );

typedef std::stack<StoragePtr> StorageStack;
typedef tbb::enumerable_thread_specific<StorageStack> ThreadSpecificStorageStack;

static ThreadSpecificStorageStack g_threadStorage;

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
		if( Node *n = node() )
		{
			n->plugDirtiedSignal()( this );
		}
		propagateDirtiness();
	}
	else
	{
		/// \todo Need to revert to default value	
	}
}
			
IECore::ObjectPtr &ValuePlug::storage( bool update )
{
	bool haveInput = getInput<Plug>();
	if( direction()==In && !haveInput )
	{
		// input plug with no input connection. there can only ever be a single value,
		// so we store it directly on the plug.
		return m_staticStorage;
	}

	// an input plug with an input connection or an output plug. there can be many values -
	// one per context. we therefore store them transiently on the StorageStack.
	
	StorageStack &threadStorage = g_threadStorage.local();

	if( update )
	{
		// push some new storage.
		StoragePtr s = new Storage( this );
		threadStorage.push( s );
		if( haveInput )
		{
			setFromInput();
		}
		else
		{
			assert( direction()==Out );
			Node *n = node();
			if( !n )
			{
				throw IECore::Exception( boost::str( boost::format( "Unable to compute value for orphan Plug \"%s\"." ) % fullName() ) );			
			}
			n->compute( this, Context::current() );
		}
			
		return s->m_storage;
	}
	else
	{	
		while( threadStorage.size() && threadStorage.top()->m_plug!=this )
		{
			threadStorage.pop(); //!!! MAKE THIS SOUND LIKE IT MAKES SENSE!
		}
		
		Storage *s = threadStorage.top().get();
		// return storage previously pushed
		if( !threadStorage.size() )
		{
			throw IECore::Exception( boost::str( boost::format( "Cannot access storage for plug \"%s\" because there is no current computation." ) % fullName() ) );					
		}
		if( s->m_plug != this )
		{
			throw IECore::Exception( boost::str( boost::format( "Cannot access storage for plug \"%s\" because plug \"%s\" is the current computation." ) % fullName() % s->m_plug->fullName() ) );						
		}
		s->m_written = true; /// !!! RENAME THIS OR HAVE TWO STORAGE FUNCTIONS OR SOMETHING
		return s->m_storage;
	}
}

void ValuePlug::valueSet()
{
	//THIS IS A HACK AND TOTALLY UNRELIABLE! WE HAVE TO RESTRUCTURE TO AVOID THINGS DANGLING ON THE STACK!
	//I THINK getValue() and setValue() at the ValuePlug level is the way to go.
	
	StorageStack &threadStorage = g_threadStorage.local();
	if( threadStorage.size() > 1 || ( threadStorage.size() && !threadStorage.top()->m_written ) )
	{
		// don't signal anything during a compute
		return;
	}
		
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
				n->plugDirtiedSignal()( const_cast<ValuePlug *>( *it ) );
				const_cast<ValuePlug *>( *it )->propagateDirtiness();
			}
		}
	}
	
	for( OutputContainer::const_iterator it=outputs().begin(); it!=outputs().end(); it++ )
	{
		ValuePlugPtr o = IECore::runTimeCast<ValuePlug>( *it );
		if( o )
		{
			n->plugDirtiedSignal()( o );
			o->propagateDirtiness();
		}
	}
}