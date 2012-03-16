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

#include "GafferBindings/TypedObjectPlugBinding.h"
#include "GafferBindings/Serialiser.h"
#include "GafferBindings/PlugBinding.h"
#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/Node.h"

#include "IECorePython/Wrapper.h"
#include "IECorePython/RunTimeTypedBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

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

template<typename T>
static typename T::Ptr construct(
	const char *name,
	Plug::Direction direction,
	typename T::ValuePtr defaultValue,
	unsigned flags,
	PlugPtr input
)
{
	typename T::Ptr result = new T( name, direction, defaultValue, flags );
	if( input )
	{
		result->setInput( input );
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
					boost::python::arg_( "flags" )=Plug::None,
					boost::python::arg_( "input" )=PlugPtr( 0 )
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
}
