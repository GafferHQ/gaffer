//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2015, Image Engine Design Inc. All rights reserved.
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

#pragma once

#include "IECorePython/ScopedGILRelease.h"

namespace GafferBindings
{

namespace Detail
{

// Generally we copy the value when setting it from python, because the c++ side will
// reference it directly, and subsequent modifications on the python side would be
// disastrous. The copy parameter may be set to false by users who really know what
// they're doing, but generally it should probably be avoided.
template<typename T>
void setValue( typename T::Ptr p, typename T::ValuePtr v, bool copy=true )
{
	IECorePython::ScopedGILRelease r;
	if( !v )
	{
		throw std::invalid_argument( "Value must not be None." );
	}
	if( copy )
	{
		v = v->copy();
	}
	p->setValue( v );
}

// Generally we copy the value when returning to python, because in C++
// it's const, and we can only send non-const objects to python. Letting
// someone modify the actual value in python could cause all sorts of problems,
// because that value may be in the cache, and be returned as the result of
// subsequent computations. The copy argument is provided mainly for the tests,
// so that we can verify whether or not a returned value is shared with the
// result of another computation. There might be a performance case for using it
// in other scenarios, but in general copy==false should be avoided like the plague.
//
// Likewise, we expose the precomputedHash argument prefixed with an underscore to
// discourage its use - again it is mainly exposed for use only in the tests.
template<typename T>
IECore::ObjectPtr getValue( typename T::Ptr p, const IECore::MurmurHash *precomputedHash=nullptr, bool copy=true )
{
	// Must release GIL in case computation spawns threads which need
	// to reenter Python.
	IECorePython::ScopedGILRelease r;

	typename IECore::ConstObjectPtr v = p->getValue( precomputedHash );
	if( v )
	{
		if( copy )
		{
			return v->copy();
		}
		else
		{
			return boost::const_pointer_cast<IECore::Object>( v );
		}
	}
	return nullptr;
}

template<typename T>
typename T::ValuePtr defaultValue( typename T::Ptr p, bool copy )
{
	typename T::ConstValuePtr v = p->defaultValue();
	if( v )
	{
		return copy ? v->copy() : boost::const_pointer_cast<typename T::ValueType>( v );
	}
	return nullptr;
}

template<typename T>
typename T::Ptr construct(
	const char *name,
	Gaffer::Plug::Direction direction,
	typename T::ValuePtr defaultValue,
	unsigned flags
)
{
	if( !defaultValue )
	{
		throw std::invalid_argument( "Default value must not be None." );
	}
	typename T::Ptr result = new T( name, direction, defaultValue, flags );
	return result;
}

template<typename T>
typename T::ValueType::Ptr typedObjectPlugDefaultValue()
{
	using ValueType = typename T::ValueType;
	if constexpr( std::is_abstract_v<ValueType> )
	{
		// Can't construct `Object` so can't provide a default value.
		/// \todo Really we want to use `is_default_constructible_v` but
		/// that fails inexplicably for a bunch of TypedData types.
		return nullptr;
	}
	else
	{
		return new ValueType;
	}
}

} // namespace Detail

template<typename T, typename TWrapper>
TypedObjectPlugClass<T, TWrapper>::TypedObjectPlugClass( const char *docString )
	:	PlugClass<T, TWrapper>( docString )
{

	this->def( "__init__", make_constructor( Detail::construct<T>, boost::python::default_call_policies(),
			(
				boost::python::arg_( "name" )=Gaffer::GraphComponent::defaultName<T>(),
				boost::python::arg_( "direction" )=Gaffer::Plug::In,
				boost::python::arg_( "defaultValue" )=Detail::typedObjectPlugDefaultValue<T>(),
				boost::python::arg_( "flags" )=Gaffer::Plug::Default
			)
		)
	);
	this->def( "defaultValue", &Detail::defaultValue<T>, ( boost::python::arg_( "_copy" ) = true ) );
	this->def( "setValue", Detail::setValue<T>, ( boost::python::arg_( "value" ), boost::python::arg_( "_copy" ) = true ) );
	this->def( "getValue", Detail::getValue<T>, ( boost::python::arg_( "_precomputedHash" ) = boost::python::object(), boost::python::arg_( "_copy" ) = true ) );

	boost::python::scope s = *this;

	PyTypeObject *valueType = boost::python::converter::registry::query(
		boost::python::type_info( typeid( typename T::ValueType ) )
	)->get_class_object();

	s.attr( "ValueType" ) = boost::python::object( boost::python::handle<>( boost::python::borrowed( valueType ) ) );

}

} // namespace GafferBindings
