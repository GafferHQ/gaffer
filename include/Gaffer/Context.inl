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

template<typename T, typename = std::enable_if_t<!std::is_pointer<T>::value > >
void Context::set( const IECore::InternedString &name, const T &value )
{
	typedef typename Gaffer::Detail::DataTraits<T>::DataType DataType;
	std::pair<Map::iterator, bool> insert = m_map.try_emplace( name );
	const Storage &storage = insert.first->second;
	if( !insert.second && storage.typeId == DataType::staticTypeId() && *((const T*)storage.value) == value )
	{
		// Already set to the value we want, we can skip
		return;
	}

	// Allocate a new typed Data, store it in m_allocMap so that it won't be deallocated,
	// and call internalSet to reference it in the main m_map
	typename DataType::Ptr d = new DataType( value );
	m_allocMap[name] = d;

	internalSet( insert.first, &d->readable(), nullptr );
}

template<typename T>
void Context::internalSet( Map::iterator it, const T *value, const IECore::MurmurHash *knownHash )
{
	typedef typename Gaffer::Detail::DataTraits<T>::DataType DataType;

	Storage &storage = it->second;
	storage.value = value;
	storage.typeId = DataType::staticTypeId();

	m_hashValid = false;
	if( knownHash )
	{
		storage.hash = *knownHash;
	}
	else
	{
		storage.hash = storage.entryHash<T>( it->first );
	}

	if( m_changedSignal )
	{
		(*m_changedSignal)( this, it->first );
	}
}

inline const void* Context::getPointerAndTypeId( const IECore::InternedString &name, IECore::TypeId &typeId ) const
{
	Map::const_iterator it = m_map.find( name );
	if( it == m_map.end() )
	{
		return nullptr;
	}

	typeId = it->second.typeId;
	return it->second.value;
}

template<typename T>
const T& Context::get( const IECore::InternedString &name ) const
{
	Map::const_iterator it = m_map.find( name );
	if( it == m_map.end() )
	{
		throw IECore::Exception( boost::str( boost::format( "Context has no entry named \"%s\"" ) % name.value() ) );
	}

	typedef typename Gaffer::Detail::DataTraits<T>::DataType DataType;
	if( it->second.typeId != DataType::staticTypeId() )
	{
		throw IECore::Exception( boost::str( boost::format( "Context entry is not of type \"%s\"" ) % DataType::staticTypeName() ) );
	}

	#ifndef NDEBUG
	validateVariableHash( it->second, name);
	#endif // NDEBUG

	return *((const T*)it->second.value );
}

template<typename T>
const T &Context::get( const IECore::InternedString &name, const T &defaultValue ) const
{
	Map::const_iterator it = m_map.find( name );
	if( it == m_map.end() )
	{
		return defaultValue;
	}

	typedef typename Gaffer::Detail::DataTraits<T>::DataType DataType;
	if( it->second.typeId != DataType::staticTypeId() )
	{
		throw IECore::Exception( boost::str( boost::format( "Context entry is not of type \"%s\"" ) % DataType::staticTypeName() ) );
	}

	#ifndef NDEBUG
	validateVariableHash( it->second, name);
	#endif // NDEBUG

	return *((const T*)it->second.value );
}

inline IECore::MurmurHash Context::variableHash( const IECore::InternedString &name ) const
{
	Map::const_iterator it = m_map.find( name );
	if( it == m_map.end() )
	{
		return IECore::MurmurHash();
	}
	return it->second.hash;
}

template<typename T>
const T* Context::getIfExists( const IECore::InternedString &name ) const
{
	Map::const_iterator it = m_map.find( name );
	if( it == m_map.end() )
	{
		return nullptr;
	}

	typedef typename Gaffer::Detail::DataTraits<T>::DataType DataType;
	if( it->second.typeId != DataType::staticTypeId() )
	{
		throw IECore::Exception( boost::str( boost::format( "Context entry is not of type \"%s\"" ) % DataType::staticTypeName() ) );
	}
	return (const T*)it->second.value;
}



template<typename T>
void Context::EditableScope::set( const IECore::InternedString &name, const T *value )
{
	m_context->internalSet( ((std::pair<Map::iterator,bool>)m_context->m_map.try_emplace( name )).first, value );
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
IECore::MurmurHash Context::Storage::entryHash( const IECore::InternedString &name )
{
	/// \todo Perhaps at some point the UI should use a different container for
	/// these "not computationally important" values, so we wouldn't have to set
	/// a zero value here so that it won't affect the total sum hash.
	// Using a hardcoded comparison of the first three characters because
	// it's quicker than `string::compare( 0, 3, "ui:" )`.
	const std::string &nameStr = name.string();
	if( nameStr.size() > 2 && nameStr[0] == 'u' && nameStr[1] == 'i' && nameStr[2] == ':' )
	{
		return IECore::MurmurHash( 0, 0 );
	}
	else
	{
		IECore::MurmurHash h;
		h.append( *((T*)value) );
		h.append( typeId );
		h.append( (uint64_t)&nameStr );
		return h;
	}
}

template<typename T>
IECore::DataPtr Context::TypeFunctionTable::makeDataTemplate( const void *raw )
{
	return new T( *((typename T::ValueType*)raw ) );
}

template<typename T>
void Context::TypeFunctionTable::internalSetDataTemplate( Context &c, const IECore::InternedString &name, const IECore::ConstDataPtr &value, AllocMap &allocMap, bool copy, const IECore::MurmurHash *knownHash )
{
	std::pair<Map::iterator, bool> insert = c.m_map.try_emplace( name );
	const Storage &storage = insert.first->second;
	if( !insert.second && storage.typeId == T::staticTypeId() && *((const typename T::ValueType*)storage.value) == ((const T*)value.get())->readable() )
	{
		// Already set to the value we want, we can skip
		return;
	}

	// Allocate a new typed Data, store it in m_allocMap so that it won't be deallocated,
	// and call internalSet to reference it in the main m_map
	const IECore::Data *d;
	if( copy )
	{
		d = allocMap.insert_or_assign( name, value->copy() ).first->second.get();
	}
	else
	{
		d = allocMap.insert_or_assign( name, value ).first->second.get();
	}
	c.internalSet( insert.first, &((T*)d)->readable(), knownHash );
}

template<typename T>
bool Context::TypeFunctionTable::typedEqualsTemplate( const void *rawA, const void *rawB )
{
	return *( (typename T::ValueType*)rawA ) == *( (typename T::ValueType*)rawB );
}

template<typename T>
IECore::MurmurHash Context::TypeFunctionTable::entryHashTemplate( Storage &s, const IECore::InternedString &name )
{
	return s.entryHash<typename T::ValueType>( name );
}

template< typename T >
void Context::TypeFunctionTable::registerType()
{
	FunctionTableEntry &e = theFunctionTable().m_typeMap[T::staticTypeId()];
	e.makeDataFunction = makeDataTemplate<T>;
	e.internalSetDataFunction = internalSetDataTemplate<T>;
	e.typedEqualsFunction = typedEqualsTemplate<T>;
	e.entryHashFunction = entryHashTemplate<T>;
}

template< typename T >
Context::ContextTypeDescription<T>::ContextTypeDescription()
{
	Context::TypeFunctionTable::registerType<T>();
}

} // namespace Gaffer

#endif // GAFFER_CONTEXT_INL
