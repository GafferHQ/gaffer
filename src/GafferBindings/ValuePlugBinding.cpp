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

#include "IECore/MurmurHash.h"
#include "IECorePython/Wrapper.h"
#include "IECorePython/RunTimeTypedBinding.h"

#include "GafferBindings/ValuePlugBinding.h"
#include "GafferBindings/PlugBinding.h"
#include "Gaffer/ValuePlug.h"
#include "Gaffer/Node.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

std::string GafferBindings::serialisePlugValue( Serialiser &s, PlugPtr plug )
{
	std::string input = serialisePlugInput( s, plug );
	if( input!="" )
	{
		return input;
	}

	if( plug->isInstanceOf( ValuePlug::staticTypeId() ) )
	{
		object pythonPlug( plug );
		if( PyObject_HasAttrString( pythonPlug.ptr(), "getValue" ) )
		{
			object pythonValue = pythonPlug.attr( "getValue" )();
			s.modulePath( pythonValue ); // to get the import statement for the module in the serialisation
			std::string value = extract<std::string>( pythonValue.attr( "__repr__" )() );
			return value;
		}
	}
	
	return "";
}

void GafferBindings::setPlugValue( PlugPtr plug, boost::python::object value )
{
	object pythonPlug( plug );

	extract<PlugPtr> inputExtractor( value );
	if( inputExtractor.check() )
	{
		pythonPlug.attr( "setInput" )( value );
	}
	else
	{
		pythonPlug.attr( "setValue" )( value );
	}			
}

void GafferBindings::bindValuePlug()
{
	IECorePython::RunTimeTypedClass<ValuePlug>()
		.GAFFERBINDINGS_DEFPLUGWRAPPERFNS( ValuePlug )
		.def( "setToDefault", &ValuePlug::setToDefault )
		.def( "hash", (IECore::MurmurHash (ValuePlug::*)() const)&ValuePlug::hash )
		.def( "hash", (void (ValuePlug::*)( IECore::MurmurHash & ) const)&ValuePlug::hash )
		.def( "getCacheMemoryLimit", &ValuePlug::getCacheMemoryLimit )
		.staticmethod( "getCacheMemoryLimit" )
		.def( "setCacheMemoryLimit", &ValuePlug::setCacheMemoryLimit )
		.staticmethod( "setCacheMemoryLimit" )
	;
}
