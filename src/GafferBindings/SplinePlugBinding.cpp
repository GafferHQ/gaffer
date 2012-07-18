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

#include "GafferBindings/SplinePlugBinding.h"
#include "GafferBindings/Serialiser.h"
#include "GafferBindings/PlugBinding.h"
#include "GafferBindings/ValuePlugBinding.h"
#include "Gaffer/Node.h"
#include "Gaffer/SplinePlug.h"
#include "Gaffer/TypedPlug.h"

#include "IECorePython/RunTimeTypedBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

template<typename T>
static std::string serialise( Serialiser &s, ConstGraphComponentPtr g )
{
	typename T::Ptr plug = IECore::constPointerCast<T>( IECore::staticPointerCast<const T>( g ) );
	std::string result = s.modulePath( g ) + "." + g->typeName() + "( \"" + g->getName() + "\", ";
		
	if( plug->direction()!=Plug::In )
	{
		result += "direction = " + serialisePlugDirection( plug->direction() ) + ", ";
	}
	
	object pythonPlug( plug );
	if( plug->defaultValue()!=typename T::ValueType() )
	{
		object pythonValue = pythonPlug.attr( "defaultValue" )();
		s.modulePath( pythonValue );
		std::string value = extract<std::string>( pythonValue.attr( "__repr__" )() );
		result += "defaultValue = " + value + ", ";
	}
	
	if( plug->getFlags() != Plug::Default )
	{
		result += "flags = " + serialisePlugFlags( plug->getFlags() ) + ", ";
	}
	
	result += "basisMatrix = " + serialisePlugValue( s, plug->basisMatrixPlug() ) + ", ";
	result += "basisStep = " + serialisePlugValue( s, plug->basisStepPlug() ) + ", ";
	
	unsigned numPoints = plug->numPoints();
	if( numPoints )
	{
		result += "points = ( ";
	
		for( unsigned i=0; i<numPoints; i++ )
		{
			result += "( " + serialisePlugValue( s, plug->pointXPlug( i ) ) + ", " +
				serialisePlugValue( s, plug->pointYPlug( i ) ) + " ), ";
		}
	
		result += "), ";
	}
	
	result += ")";

	return result;
}

template<typename T>
static typename T::Ptr construct(
	const char *name,
	Plug::Direction direction,
	typename T::ValueType defaultValue,
	unsigned flags,
	object basisMatrix,
	object basisStep,
	object points
)
{
	typename T::Ptr result = new T( name, direction, defaultValue, flags );
	
	if( basisMatrix!=object() )
	{
		setPlugValue( result->basisMatrixPlug(), basisMatrix );
	}
	if( basisStep!=object() )
	{
		setPlugValue( result->basisStepPlug(), basisStep );
	}
	
	if( points!=object() )
	{
		result->clearPoints();
		size_t s = extract<size_t>( points.attr( "__len__" )() );
		for( size_t i=0; i<s; i++ )
		{
			tuple t = extract<tuple>( points[i] );
			unsigned pi = result->addPoint();
			setPlugValue( result->pointXPlug( pi ), t[0] );
			setPlugValue( result->pointYPlug( pi ), t[1] );
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
					boost::python::arg_( "basisMatrix" )=object(),
					boost::python::arg_( "basisStep" )=object(),
					boost::python::arg_( "points" )=object()
				)
			)
		)
		.GAFFERBINDINGS_DEFPLUGWRAPPERFNS( T )
		.def( "defaultValue", &T::defaultValue, return_value_policy<copy_const_reference>() )
		.def( "setValue", &T::setValue )
		.def( "getValue", &T::getValue )
		.def( "numPoints", &T::numPoints )
		.def( "addPoint", &T::addPoint )
		.def( "removePoint", &T::removePoint )
		.def( "clearPoints", &T::clearPoints )
		.def( "pointPlug", (CompoundPlugPtr (T::*)( unsigned ))&T::pointPlug )
		.def( "pointXPlug", (typename T::XPlugType::Ptr (T::*)( unsigned ))&T::pointXPlug )
		.def( "pointYPlug", (typename T::YPlugType::Ptr (T::*)( unsigned ))&T::pointYPlug )
	;
	
	Serialiser::registerSerialiser( T::staticTypeId(), serialise<T> );
}

void GafferBindings::bindSplinePlug()
{
	bind<SplineffPlug>();
	bind<SplinefColor3fPlug>();
}
