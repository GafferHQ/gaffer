//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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
#include "GafferBindings/PlugBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

// generally we copy the value when setting it from python, because the c++ side will
// reference it directly, and subsequent modifications on the python side would be
// disastrous. the copy parameter may be set to false by users who really know what
// they're doing, but generally it should probably be avoided.
template<typename T>
static void setValue( typename T::Ptr p, typename T::ValuePtr v, bool copy=true )
{
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

// generally we copy the value when returning to python, because in C++
// it's const, and we can only send non-const objects to python. letting
// someone modify the actual value in python could cause all sorts of problems,
// because that value may be in the cache, and be returned as the result of
// subsequent computations. the copy argument is provided mainly for the tests,
// so that we can verify whether or not a returned value is shared with the
// result of another computation. there might be a performance case for using it
// in other scenarios, but in general copy==false should be avoided like the plague.
template<typename T>
static IECore::ObjectPtr getValue( typename T::Ptr p, bool copy=true )
{
	typename IECore::ConstObjectPtr v = p->getValue();
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
	return 0;
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
static typename T::Ptr construct(
	const char *name,
	Plug::Direction direction,
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
static void bind()
{

	scope s = PlugClass<T>()
		.def( "__init__", make_constructor( construct<T>, default_call_policies(),
				(
					boost::python::arg_( "name" )=GraphComponent::defaultName<T>(),
					boost::python::arg_( "direction" )=Plug::In,
					boost::python::arg_( "defaultValue" ),
					boost::python::arg_( "flags" )=Plug::Default
				)
			)
		)
		.def( "defaultValue", &defaultValue<T> )
		.def( "setValue", setValue<T>, ( boost::python::arg_( "value" ), boost::python::arg_( "_copy" ) = true ) )
		.def( "getValue", getValue<T>, ( boost::python::arg_( "_copy" ) = true ) )
	;

	PyTypeObject *valueType = boost::python::converter::registry::query(
		boost::python::type_info( typeid( typename T::ValueType ) )
	)->get_class_object();

	s.attr( "ValueType" ) = object( handle<>( borrowed( valueType ) ) );

}

void GafferBindings::bindTypedObjectPlug()
{
	bind<ObjectPlug>();
	bind<BoolVectorDataPlug>();
	bind<IntVectorDataPlug>();
	bind<FloatVectorDataPlug>();
	bind<StringVectorDataPlug>();
	bind<InternedStringVectorDataPlug>();
	bind<V3fVectorDataPlug>();
	bind<Color3fVectorDataPlug>();
	bind<ObjectVectorPlug>();
	bind<CompoundObjectPlug>();
}
