//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "IECore/SimpleTypedData.h"

namespace Gaffer
{

template<typename T, typename Enabler>
struct Context::Getter
{	
	typedef const T &ResultType;
	
	ResultType operator() ( const IECore::CompoundData *data, const IECore::InternedString &name )
	{
		return data->member<IECore::TypedData<T> >( name, true )->readable();		
	}
};

template<typename T>
struct Context::Getter<T, typename boost::enable_if<boost::is_base_of<IECore::Data, T> >::type>
{
	typedef const T *ResultType;
	
	ResultType operator() ( const IECore::CompoundData *data, const IECore::InternedString &name )
	{
		return data->member<T>( name, true );		
	}
};

template<typename T>
void Context::set( const IECore::InternedString &name, const T &value )
{
	IECore::TypedData<T> *d = m_data->member<IECore::TypedData<T> >( name );
	if( d )
	{
		if( d->readable() == value )
		{
			// no change so early out
			return;
		}
		else
		{
			// update in place to avoid allocations
			d->writable() = value;
		}			
	}
	else
	{
		m_data->writable()[name] = new IECore::TypedData<T>( value );
	}
	
	m_changedSignal( this, name );
}

template<typename T>
typename Context::Getter<T>::ResultType Context::get( const IECore::InternedString &name ) const
{
	return Getter<T>()( m_data.get(), name );
}
		
} // namespace Gaffer

#endif // GAFFER_CONTEXT_INL
