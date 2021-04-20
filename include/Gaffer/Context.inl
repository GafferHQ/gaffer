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

#include "IECore/SimpleTypedData.h"

#include "boost/format.hpp"

namespace Gaffer
{

namespace Detail
{

// Class to dictate what IECore::Data subclass we
// use to hold the type T. This is necessary because
// unfortunately we can't just use TypedData<T> when
// T is an Imath::Vec - then we need to use
// GeometricTypedData<T>.
/// \todo Consider how to better address this in Cortex.
/// We could just simply provide DataTraits in Cortex,
/// but this GeometricTypedData problem has tripped us
/// up in several scenarios already due to non-obviousness.
/// Is it worth considering removing GeometricTypedData
/// and redundantly storing GeometricInterpretation for
/// all data types? It would certainly be simpler.
template<typename T>
struct DataTraits
{

	typedef IECore::TypedData<T> DataType;

};

template<typename T>
struct DataTraits<Imath::Vec2<T> >
{

	typedef IECore::GeometricTypedData<Imath::Vec2<T> > DataType;

};

template<typename T>
struct DataTraits<Imath::Vec3<T> >
{

	typedef IECore::GeometricTypedData<Imath::Vec3<T> > DataType;

};

} // namespace Detail

template<typename T>
Context::Value::Value( const IECore::InternedString &name, const T *value )
	:	m_typeId( Detail::DataTraits<T>::DataType::staticTypeId() ),
		m_value( value )
{
	const std::string &nameStr = name.string();
	if( nameStr.size() > 2 && nameStr[0] == 'u' && nameStr[1] == 'i' && nameStr[2] == ':' )
	{
		m_hash = IECore::MurmurHash( 0, 0 );
	}
	else
	{
		m_hash.append( *value );
		m_hash.append( m_typeId );
		m_hash.append( (uint64_t)&nameStr );
	}
}

template<typename T>
inline const T &Context::Value::value() const
{
	using DataType = typename Gaffer::Detail::DataTraits<T>::DataType;
	if( m_typeId == DataType::staticTypeId() )
	{
		return *static_cast<const T *>( m_value );
	}
	throw IECore::Exception( boost::str( boost::format( "Context variable is not of type \"%s\"" ) % DataType::staticTypeName() ) );
}

template<typename T>
void Context::Value::registerType()
{
	using ValueType = typename T::ValueType;
	TypeFunctions &functions = typeMap()[T::staticTypeId()];
	functions.makeData = []( const Value &value, const void **dataValue ) -> IECore::DataPtr {
		typename T::Ptr result = new T( *static_cast<const ValueType *>( value.rawValue() ) );
		if( dataValue )
		{
			*dataValue = &result->readable();
		}
		return result;
	};
	functions.isEqual = [] ( const Value &a, const Value &b ) {
		// Type of both `a` and `b` has been checked already in `operator ==`.
		return (*static_cast<const ValueType *>( a.rawValue() )) == (*static_cast<const ValueType *>( b.rawValue() ));
	};
	functions.constructor = [] ( const IECore::InternedString &name, const IECore::Data *data ) {
		return Value( name, &static_cast<const T *>( data )->readable() );
	};
	functions.value = [] ( const IECore::Data *data ) -> const void * {
		return &static_cast<const T *>( data )->readable();
	};
}

template<typename T, typename = std::enable_if_t<!std::is_pointer<T>::value > >
void Context::set( const IECore::InternedString &name, const T &value )
{
	// Allocate a new typed Data, store it in m_allocMap so that it won't be deallocated,
	// and call internalSet to reference it in the main m_map
	typedef typename Gaffer::Detail::DataTraits<T>::DataType DataType;
	typename DataType::Ptr d = new DataType( value );
	m_allocMap[name] = d;
	internalSet( name, Value( name, &d->readable() ) );
}

void Context::internalSet( const IECore::InternedString &name, const Value &value )
{
	m_map.insert_or_assign( name, value );
	m_hashValid = false;

	if( m_changedSignal )
	{
		(*m_changedSignal)( this, name );
	}
}

inline const Context::Value &Context::internalGet( const IECore::InternedString &name ) const
{
	const Value *result = internalGetIfExists( name );
	if( !result )
	{
		throw IECore::Exception( boost::str( boost::format( "Context has no variable named \"%s\"" ) % name.value() ) );
	}
	return *result;
}

inline const Context::Value *Context::internalGetIfExists( const IECore::InternedString &name ) const
{
	Map::const_iterator it = m_map.find( name );
	return it != m_map.end() ? &it->second : nullptr;
}

template<typename T>
const T &Context::get( const IECore::InternedString &name ) const
{
	return internalGet( name ).value<T>();
}

template<typename T>
const T &Context::get( const IECore::InternedString &name, const T &defaultValue ) const
{
	if( const Value *value = internalGetIfExists( name ) )
	{
		return internalGet( name ).value<T>();
	}
	return defaultValue;
}

inline IECore::MurmurHash Context::variableHash( const IECore::InternedString &name ) const
{
	if( const Value *value = internalGetIfExists( name ) )
	{
		return value->hash();
	}
	return IECore::MurmurHash();
}

template<typename T>
const T *Context::getIfExists( const IECore::InternedString &name ) const
{
	if( const Value *value = internalGetIfExists( name ) )
	{
		return &value->value<T>();
	}
	return nullptr;
}

template<typename T>
void Context::EditableScope::set( const IECore::InternedString &name, const T *value )
{
	m_context->internalSet( name, Value( name, value ) );
}

// DEPRECATED
template<typename T, typename = std::enable_if_t<!std::is_pointer<T>::value > >
void Context::EditableScope::set( const IECore::InternedString &name, const T &value )
{
	m_context->set( name, value );
}

template<typename T, typename = std::enable_if_t<!std::is_pointer<T>::value > >
void Context::EditableScope::setAllocated( const IECore::InternedString &name, const T &value )
{
	m_context->set( name, value );
}

const IECore::Canceller *Context::canceller() const
{
	return m_canceller;
}

class Context::SubstitutionProvider : public IECore::StringAlgo::VariableProvider
{

	public :

		SubstitutionProvider( const Context *context );

		int frame() const override;
		const std::string &variable( const boost::string_view &name, bool &recurse ) const override;

	private :

		const Context *m_context;
		mutable std::string m_formattedString;

};

template< typename T >
Context::TypeDescription<T>::TypeDescription()
{
	Context::Value::registerType<T>();
}

} // namespace Gaffer

#endif // GAFFER_CONTEXT_INL
