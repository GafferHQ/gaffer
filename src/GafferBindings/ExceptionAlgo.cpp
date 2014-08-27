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

#include "IECore/Exception.h"

#include "GafferBindings/ExceptionAlgo.h"

using namespace boost::python;

namespace GafferBindings
{

std::string formatPythonException( bool withStacktrace, int *lineNumber )
{
	PyObject *exceptionPyObject, *valuePyObject, *tracebackPyObject;
	PyErr_Fetch( &exceptionPyObject, &valuePyObject, &tracebackPyObject );
	PyErr_NormalizeException( &exceptionPyObject, &valuePyObject, &tracebackPyObject );

	object exception( ( handle<>( exceptionPyObject ) ) );
	object value( ( handle<>( valuePyObject ) ) );
	object traceback( ( handle<>( tracebackPyObject ) ) );

	object tracebackModule( import( "traceback" ) );

	if( lineNumber )
	{
		*lineNumber = extract<int>( traceback.attr( "tb_lineno" ) );
	}

	object formattedList;
	if( withStacktrace )
	{
		formattedList = tracebackModule.attr( "format_exception" )( exception, value, traceback );
	}
	else
	{
		formattedList = tracebackModule.attr( "format_exception_only" )( exception, value );
	}


	object formatted = str( "" ).join( formattedList );
	std::string s = extract<std::string>( formatted );

	return s;
}

void translatePythonException( bool withStacktrace )
{
	throw IECore::Exception( formatPythonException( withStacktrace ) );
}

} // namespace GafferBindings
