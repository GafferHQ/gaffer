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

#include "boost/python.hpp"
#include "boost/lexical_cast.hpp"

#include "IECorePython/RunTimeTypedBinding.h"
#include "IECorePython/ScopedGILRelease.h"

#include "Gaffer/NumericPlug.h"
#include "Gaffer/Node.h"

#include "GafferBindings/NumericPlugBinding.h"
#include "GafferBindings/PlugBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

template<typename T>
static std::string repr( const T *plug )
{
	std::string result = Serialisation::classPath( plug ) + "( \"" + plug->getName().string() + "\", ";
	
	if( plug->direction()!=Plug::In )
	{
		result += "direction = " + PlugSerialiser::directionRepr( plug->direction() ) + ", ";
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
	
	if( plug->getFlags() != Plug::Default )
	{
		result += "flags = " + PlugSerialiser::flagsRepr( plug->getFlags() ) + ", ";
	}
		
	result += ")";

	return result;
}


template<typename T>
static void setValue( T *plug, const typename T::ValueType value )
{
	// we use a GIL release here to prevent a lock in the case where this triggers a graph
	// evaluation which decides to go back into python on another thread:
	IECorePython::ScopedGILRelease r;
	plug->setValue( value );
}


template<typename T>
static void bind()
{
	typedef typename T::ValueType V;
	
	IECorePython::RunTimeTypedClass<T>()
		.def( init<const char *, Plug::Direction, typename T::ValueType, typename T::ValueType, typename T::ValueType, unsigned>(
				(
					boost::python::arg_( "name" )=GraphComponent::defaultName<T>(),
					boost::python::arg_( "direction" )=Plug::In,
					boost::python::arg_( "defaultValue" )=V(),
					boost::python::arg_( "minValue" )=Imath::limits<V>::min(),
					boost::python::arg_( "maxValue" )=Imath::limits<V>::max(),
					boost::python::arg_( "flags" )=Plug::Default
				)
			)
		)
		.GAFFERBINDINGS_DEFPLUGWRAPPERFNS( T )
		.def( "defaultValue", &T::defaultValue )
		.def( "hasMinValue", &T::hasMinValue )
		.def( "hasMaxValue", &T::hasMaxValue )
		.def( "minValue", &T::minValue )
		.def( "maxValue", &T::maxValue )
		.def( "setValue", setValue<T> )
		.def( "getValue", &T::getValue )
		.def( "__repr__", &repr<T> )
	;

}

void GafferBindings::bindNumericPlug()
{
	bind<FloatPlug>();
	bind<IntPlug>();
}
