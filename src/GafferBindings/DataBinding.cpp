//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#include "IECore/DespatchTypedData.h"

#include "GafferBindings/DataBinding.h"

using namespace boost::python;
using namespace IECore;

namespace
{

struct SimpleTypedDataGetter
{
	typedef object ReturnType;

	template<typename T>
	object operator()( T *data )
	{
		return object( data->readable() );
	}
};

boost::python::object dataToPythonInternal( IECore::Data *data, bool copy, boost::python::object nullValue )
{
	if( !data )
	{
		return nullValue;
	}

	try
	{
		return despatchTypedData<SimpleTypedDataGetter, TypeTraits::IsSimpleTypedData>( data );
	}
	catch( const InvalidArgumentException &e )
	{
		// In an ideal world, we wouldn't be using exception handling to detect
		// the cases where IsSimpleTypedData is false. We _could_ use a null error
		// handler for the despatchTypedData() call, except for two annoying facts :
		//
		//	- Error handlers don't get to return a value
		//  - The error handler isn't used if a totally unknown datatype is
		//    found, and Gaffer adds new datatypes.
		//
		// It might be nice to fix that in Cortex.
		return object( copy ? data->copy() : DataPtr( data ) );
	}
}

} // namespace

namespace GafferBindings
{

boost::python::object dataToPython( IECore::Data *data, boost::python::object nullValue )
{
	return dataToPythonInternal( data, false, nullValue );
}

boost::python::object dataToPython( const IECore::Data *data, bool copy, boost::python::object nullValue )
{
	return dataToPythonInternal( const_cast<Data *>( data ), copy, nullValue );
}

} // namespace GafferBindings
