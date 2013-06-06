//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "boost/python/list.hpp"
#include "IECorePython/ScopedGILRelease.h"
#include "Gaffer/Executable.h"

namespace GafferBindings
{

template< typename PythonClass, typename NodeClass >
void ExecutableBinding<PythonClass,NodeClass>::bind( PythonClass &c )
{
	c.def( "executionRequirements", &ExecutableBinding<PythonClass,NodeClass>::executionRequirements )
	 .def( "executionHash", &NodeClass::executionHash )
	 .def( "execute", &ExecutableBinding<PythonClass,NodeClass>::execute );
}

template< typename PythonClass, typename NodeClass >
boost::python::list ExecutableBinding<PythonClass,NodeClass>::executionRequirements( NodeClass &n, Gaffer::ContextPtr context )
{
	Gaffer::Executable::Tasks tasks;
	n.executionRequirements( context, tasks );
	boost::python::list result;
	for ( Gaffer::Executable::Tasks::const_iterator tIt = tasks.begin(); tIt != tasks.end(); tIt++ )
	{
		result.append( *tIt );
	}
	return result;
}

template< typename PythonClass, typename NodeClass >
void ExecutableBinding<PythonClass,NodeClass>::execute( NodeClass &n, const boost::python::list &contextList )
{
	Gaffer::Executable::Contexts contexts;
	size_t len = boost::python::len(contextList);
	contexts.reserve( len );
	for ( size_t i = 0; i < len; i++ )
	{
		contexts.push_back( boost::python::extract<Gaffer::ConstContextPtr>( contextList[i] ) );
	}
	IECorePython::ScopedGILRelease gilRelease;
	n.execute( contexts );
}

} // namespace GafferBindings
