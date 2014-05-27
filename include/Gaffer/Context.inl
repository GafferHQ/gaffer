//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012-2013, John Haddon. All rights reserved.
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

#ifndef GAFFER_CONTEXT_INL
#define GAFFER_CONTEXT_INL

#include "boost/format.hpp"

#include "IECore/SimpleTypedData.h"

namespace Gaffer
{

template<typename T, typename Enabler>
struct Context::Accessor
{	
	typedef const T &ResultType;
	
	/// Returns true if the value has changed
	bool set( Storage &storage, const T &value )
	{
		const IECore::TypedData<T> *d = IECore::runTimeCast<const IECore::TypedData<T> >( storage.data );
		if( d )
		{
			if( d->readable() == value )
			{
				// no change so early out
				return false;
			}
			else if( storage.ownership == Copied )
			{
				// update in place to avoid allocations. the cast is ok
				// because we created the value for our own use in the first
				// place. storage.data is const to remind us not to mess
				// with values we receive as Shared or Borrowed, but since this
				// is Copied, we're free to do as we please.
				const_cast<IECore::TypedData<T> *>( d )->writable() = value;
				return true;
			}			
		}
		
		// data wasn't of the right type or we didn't have sole ownership.
		// remove the old value and replace it with a new one.
		if( storage.data && storage.ownership != Borrowed )
		{
			storage.data->removeRef();
		}
		
		storage.data = new IECore::TypedData<T>( value );
		storage.data->addRef();
		storage.ownership = Copied;
		
		return true;
	}
	
	ResultType get( const IECore::Data *data )
	{
		if( !data->isInstanceOf( IECore::TypedData<T>::staticTypeId() ) )
		{
			throw IECore::Exception( boost::str( boost::format( "Context entry is not of type \"%s\"" ) % IECore::TypedData<T>::staticTypeName() ) );
		}
		return static_cast<const IECore::TypedData<T> *>( data )->readable();
	}
};

template<typename T>
struct Context::Accessor<T, typename boost::enable_if<boost::is_base_of<IECore::Data, typename boost::remove_pointer<T>::type > >::type>
{
	typedef typename boost::remove_pointer<T>::type ValueType;
	typedef const ValueType *ResultType;
	
	bool set( Storage &storage, const T &value )
	{
		const ValueType *d = IECore::runTimeCast<const ValueType>( storage.data );
		if( d && d->isEqualTo( value ) )
		{
			return false;
		}
		
		if( storage.data && storage.ownership != Borrowed )
		{
			storage.data->removeRef();
		}
		
		IECore::DataPtr valueCopy = value->copy();
		storage.data = valueCopy.get();
		storage.data->addRef();
		storage.ownership = Copied;
		
		return true;
	}
	
	ResultType get( const IECore::Data *data )
	{
		if( !data->isInstanceOf( T::staticTypeId() ) )
		{
			throw IECore::Exception( boost::str( boost::format( "Context entry is not of type \"%s\"" ) % T::staticTypeName() ) );
		}
		return static_cast<const T *>( data );
	}
};

template<typename T>
void Context::set( const IECore::InternedString &name, const T &value )
{
	Storage &s = m_map[name];
	if( Accessor<T>().set( s, value ) )
	{
		if( m_changedSignal )
		{
			(*m_changedSignal)( this, name );		
		}
	}
}

template<typename T>
typename Context::Accessor<T>::ResultType Context::get( const IECore::InternedString &name ) const
{
	Map::const_iterator it = m_map.find( name );
	if( it == m_map.end() )
	{
		throw IECore::Exception( boost::str( boost::format( "Context has no entry named \"%s\"" ) % name.value() ) );
	}
	return Accessor<T>().get( it->second.data );
}

template<typename T>
typename Context::Accessor<T>::ResultType Context::get( const IECore::InternedString &name, typename Accessor<T>::ResultType defaultValue ) const
{
	Map::const_iterator it = m_map.find( name );
	if( it == m_map.end() )
	{
		return defaultValue;
	}
	return Accessor<T>().get( it->second.data );
}
		
} // namespace Gaffer

#endif // GAFFER_CONTEXT_INL
