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

#include "GafferBindings/PlugBinding.h"
#include "GafferBindings/TransformPlugBinding.h"
#include "Gaffer/TransformPlug.h"

#include "IECorePython/RunTimeTypedBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

/*
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
}*/

void GafferBindings::bindTransformPlug()
{	
	IECorePython::RunTimeTypedClass<TransformPlug>()
		.def(
			init< const std::string &, Gaffer::Plug::Direction, unsigned >
			(
				(
					arg( "name" ) = Gaffer::TransformPlug::staticTypeName(),
					arg( "direction" ) = Gaffer::Plug::In,
					arg( "flags" ) = Gaffer::Plug::Default
				)
			)
		)
		.GAFFERBINDINGS_DEFPLUGWRAPPERFNS( TransformPlug )
		.def( "matrix", &TransformPlug::matrix )
	;
	
	//Serialiser::registerSerialiser( T::staticTypeId(), serialise<T> );
}
