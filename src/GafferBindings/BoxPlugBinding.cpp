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

#include "boost/python.hpp"
#include "boost/lexical_cast.hpp"

#include "GafferBindings/BoxPlugBinding.h"
#include "GafferBindings/PlugBinding.h"
#include "GafferBindings/ValuePlugBinding.h"
#include "GafferBindings/Serialiser.h"
#include "Gaffer/BoxPlug.h"

#include "IECorePython/RunTimeTypedBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

template<typename T>
static std::string serialiseValue( Serialiser &s, const T &value )
{
	object pythonValue( value );
	s.modulePath( pythonValue );
	return extract<std::string>( pythonValue.attr( "__repr__" )() );
}

template<typename T>
static std::string serialise( Serialiser &s, ConstGraphComponentPtr g )
{
	T *plug = const_cast<T *>( static_cast<const T *>( g.get() ) );
	std::string result = s.modulePath( g ) + "." + g->typeName() + "( \"" + g->getName() + "\", ";
	
	if( plug->direction()!=Plug::In )
	{
		result += "direction = " + serialisePlugDirection( plug->direction() ) + ", ";
	}
	
	if( plug->defaultValue()!=typename T::ValueType() )
	{
		result += "defaultValue = " + serialiseValue( s, plug->defaultValue() ) + ", ";
	}
		
	if( plug->getFlags() != Plug::Default )
	{
		result += "flags = " + serialisePlugFlags( plug->getFlags() ) + ", ";
	}
	
	std::string value = std::string( "( " ) +
		serialisePlugValue( s, plug->min() ) +
		", " +
		serialisePlugValue( s, plug->max() ) +
		" )";
	result += "value = " + value + ", ";
	
	result += ")";

	return result;
}

template<typename T>
static typename T::Ptr construct(
	const char *name,
	Plug::Direction direction,
	typename T::ValueType defaultValue,
	unsigned flags,
	object value
)
{
	typename T::Ptr result = new T( name, direction, defaultValue, flags );
	if( value!=object() )
	{
		extract<typename T::ValueType> valueExtractor( value );
		if( valueExtractor.check() )
		{
			typename T::ValueType v = valueExtractor();
			result->setValue( v );
		}
		else
		{
			tuple t = extract<tuple>( value )();
			size_t l = extract<size_t>( t.attr( "__len__" )() )();
			if( l!=2 )
			{
				PyErr_SetString( PyExc_ValueError, "Wrong number of items in value tuple." );			
				throw_error_already_set();
			}
			setPlugValue( result->min(), t[0] );
			setPlugValue( result->max(), t[1] );
		}
	}
	return result;
}

template<typename T>
static void bind()
{
	typedef typename T::ValueType V;
		
	IECorePython::RunTimeTypedClass<T>()
		.def( "__init__", make_constructor( construct<T>, default_call_policies(),
				(
					boost::python::arg_( "name" )=T::staticTypeName(),
					boost::python::arg_( "direction" )=Plug::In,
					boost::python::arg_( "defaultValue" )=V(),
					boost::python::arg_( "flags" )=Plug::Default,
					boost::python::arg_( "value" )=object()
				)
			)
		)
		.GAFFERBINDINGS_DEFPLUGWRAPPERFNS( T )
		.def( "defaultValue", &T::defaultValue )
		.def( "setValue", &T::setValue )
		.def( "getValue", &T::getValue )
	;

	Serialiser::registerSerialiser( T::staticTypeId(), serialise<T> );

}

void GafferBindings::bindBoxPlug()
{
	bind<Box2iPlug>();
	bind<Box3iPlug>();
	bind<Box2fPlug>();
	bind<Box3fPlug>();
}
