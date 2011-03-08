//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#include "boost/python.hpp"
#include "boost/lexical_cast.hpp"

#include "GafferBindings/NumericPlugBinding.h"
#include "GafferBindings/PlugBinding.h"
#include "GafferBindings/Serialiser.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/Node.h"

#include "IECorePython/Wrapper.h"
#include "IECorePython/RunTimeTypedBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

template<typename T>
static std::string serialise( Serialiser &s, ConstGraphComponentPtr g )
{
	typename T::ConstPtr plug = IECore::staticPointerCast<const T>( g );
	std::string result = s.modulePath( g ) + "." + g->typeName() + "( \"" + g->getName() + "\", ";
	
	if( plug->direction()!=Plug::In )
	{
		result += "direction = " + serialisePlugDirection( plug->direction() ) + ", ";
	}
	
	if( plug->defaultValue()!=typename T::ValueType() )
	{
		result += "defaultValue = " + boost::lexical_cast<std::string>( plug->defaultValue() ) + ", ";
	}
	
	if( plug->hasMinValue() )
	{
		result += "minValue = " + boost::lexical_cast<std::string>( plug->minValue() ) + ", ";
	}
	
	if( plug->hasMaxValue() )
	{
		result += "maxValue = " + boost::lexical_cast<std::string>( plug->maxValue() ) + ", ";
	}
	
	if( plug->getFlags() )
	{
		result += "flags = " + serialisePlugFlags( plug->getFlags() ) + ", ";
	}
	
	bool connected = false;
	ConstPlugPtr srcPlug = plug->template getInput<Plug>();
	if( srcPlug )
	{
		std::string srcNodeName = s.add( srcPlug->node() );
		if( srcNodeName!="" )
		{
			connected = true;
			result += "input = " + srcNodeName + "[\"" + srcPlug->getName() + "\"]";
		}
	}
	
	if( !connected && plug->direction()==Plug::In )
	{
		typename T::Ptr p = IECore::constPointerCast<T>( plug );
		typename T::ValueType value = p->getValue();
		if( value!=plug->defaultValue() )
		{
			result += "value = " + boost::lexical_cast<std::string>( value ) + ", ";
		}
	}
	
	result += ")";

	return result;
}

template<typename T>
static typename T::Ptr construct(
	const char *name,
	Plug::Direction direction,
	typename T::ValueType defaultValue,
	typename T::ValueType minValue,
	typename T::ValueType maxValue,
	unsigned flags,
	PlugPtr input,
	object value
)
{
	typename T::Ptr result = new T( name, direction, defaultValue, minValue, maxValue, flags );
	if( input && value!=object() )
	{
		throw std::invalid_argument( "Must specify only one of input or value." );
	}
	if( input )
	{
		result->setInput( input );
	}
	else if( value!=object() )
	{
		typename T::ValueType v = extract<typename T::ValueType>( value )();
		result->setValue( v );
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
					boost::python::arg_( "minValue" )=Imath::limits<V>::min(),
					boost::python::arg_( "maxValue" )=Imath::limits<V>::max(),
					boost::python::arg_( "flags" )=Plug::None,
					boost::python::arg_( "input" )=PlugPtr( 0 ),
					boost::python::arg_( "value" )=object()
				)
			)
		)
		.def( "defaultValue", &T::defaultValue )
		.def( "hasMinValue", &T::hasMinValue )
		.def( "hasMaxValue", &T::hasMaxValue )
		.def( "minValue", &T::minValue )
		.def( "maxValue", &T::maxValue )
		.def( "setValue", &T::setValue )
		.def( "getValue", &T::getValue )
	;

	Serialiser::registerSerialiser( T::staticTypeId(), serialise<T> );

}

void GafferBindings::bindNumericPlug()
{
	bind<FloatPlug>();
	bind<IntPlug>();
}
