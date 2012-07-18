//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

#include "IECore/MessageHandler.h"
#include "IECore/NullObject.h"
#include "IECorePython/RunTimeTypedBinding.h"

#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/Node.h"

#include "GafferBindings/TypedObjectPlugBinding.h"
#include "GafferBindings/Serialiser.h"
#include "GafferBindings/PlugBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

/// \todo This is very similar to serialisePlugValue(), and also similar to 
/// code in TypedPlugBinding which calls IECorePython::repr(). I think they
/// could probably all be rationalised into one thing somehow.
static std::string serialiseValue( Serialiser &s, IECore::ConstObjectPtr value )
{
	object o( IECore::constPointerCast<IECore::Object>( value ) );
	s.modulePath( o );
	object r = o.attr( "__repr__" )();
	extract<std::string> resultExtractor( r );
	std::string result = resultExtractor();
	if( result.size() && result[0] == '<' )
	{
		// looks like the repr function hasn't been defined properly
		// for this type.
		return "";
	}
	return result;
}

/// \todo Should we be able to serialise values and default values?
template<typename T>
static std::string serialise( Serialiser &s, ConstGraphComponentPtr g )
{	
	typename T::ConstPtr plug = IECore::staticPointerCast<const T>( g );
	std::string result = s.modulePath( g ) + "." + g->typeName() + "( \"" + g->getName() + "\", ";
	
	if( plug->direction()!=Plug::In )
	{
		result += "direction = " + serialisePlugDirection( plug->direction() ) + ", ";
	}
	
	std::string defaultValue = serialiseValue( s, plug->defaultValue() );
	if( defaultValue.size() )
	{
		result += "defaultValue = " + defaultValue + ", ";
	}
	else
	{
		IECore::msg(
			IECore::Msg::Error,
			"TypedObjectPlug serialiser",
			boost::format( "Default value for plug \"%s\" cannot be serialised" ) % g->fullName()	
		);
	}
	
	if( plug->getFlags() != Plug::Default )
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
		/// \todo Remove this cast when we merge the branch where getValue() is
		/// correctly const.
		typename T::Ptr p = IECore::constPointerCast<T>( plug );
		std::string value = serialiseValue( s, p->getValue() );
		if( value.size() )
		{
			result += "value = " + value + ", ";
		}
		else
		{
			IECore::msg(
				IECore::Msg::Error,
				"TypedObjectPlug serialiser",
				boost::format( "Value for plug \"%s\" cannot be serialised" ) % g->fullName()	
			);
		}
	}
	
	result += ")";

	return result;
}

template<typename T>
static typename T::ValuePtr getValue( typename T::Ptr p )
{
	typename T::ConstValuePtr v = p->getValue();
	if( v )
	{
		return v->copy();
	}
	return 0;
}

/// \todo This has a lot in common with construct() functions in the other Plug
/// bindings - can they not be consolidated somehow?
template<typename T>
static typename T::Ptr construct(
	const char *name,
	Plug::Direction direction,
	typename T::ValuePtr defaultValue,
	unsigned flags,
	PlugPtr input,
	IECore::ObjectPtr value	
)
{
	typename T::Ptr result = new T( name, direction, defaultValue, flags );
	if( input && value!=IECore::NullObject::defaultNullObject() )
	{
		throw std::invalid_argument( "Must specify only one of input or value." );
	}
	if( input )
	{
		result->setInput( input );
	}
	else if( value!=IECore::NullObject::defaultNullObject() )
	{
		result->setValue( IECore::runTimeCast<typename T::ValueType>( value ) );
	}
	return result;
}

template<typename T>
static typename T::ValuePtr defaultValue( typename T::Ptr p )
{
	typename T::ConstValuePtr v = p->defaultValue();
	if( v )
	{
		return v->copy();
	}
	return 0;
}

template<typename T>
static void bind()
{
	typedef typename T::ValuePtr V;
	
	IECorePython::RunTimeTypedClass<T>()
		.def( "__init__", make_constructor( construct<T>, default_call_policies(), 
				(
					boost::python::arg_( "name" )=T::staticTypeName(),
					boost::python::arg_( "direction" )=Plug::In,
					boost::python::arg_( "defaultValue" )=typename T::ValuePtr(),
					boost::python::arg_( "flags" )=Plug::Default,
					boost::python::arg_( "input" )=PlugPtr( 0 ),
					// we're using NullObject as the "value not specified" default
					// argument because None is a valid value.
					boost::python::arg_( "value" )=IECore::NullObject::defaultNullObject()
				)
			)
		)
		.GAFFERBINDINGS_DEFPLUGWRAPPERFNS( T )
		.def( "defaultValue", &defaultValue<T> )
		.def( "setValue", &T::setValue )
		.def( "getValue", getValue<T>, "Returns a copy of the value." )
	;

	Serialiser::registerSerialiser( T::staticTypeId(), serialise<T> );

}

void GafferBindings::bindTypedObjectPlug()
{
	bind<ObjectPlug>();
	bind<BoolVectorDataPlug>();
	bind<IntVectorDataPlug>();
	bind<FloatVectorDataPlug>();
	bind<StringVectorDataPlug>();
	bind<V3fVectorDataPlug>();
	bind<ObjectVectorPlug>();
	bind<PrimitivePlug>();
}
