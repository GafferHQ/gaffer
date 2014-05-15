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

#ifndef GAFFERBINDINGS_EXECUTABLENODEBINDING_INL
#define GAFFERBINDINGS_EXECUTABLENODEBINDING_INL

#include "boost/python/suite/indexing/container_utils.hpp"

#include "IECorePython/ScopedGILRelease.h"

namespace GafferBindings
{

namespace Detail
{

template<typename T>
boost::python::list executionRequirements( T &n, Gaffer::Context *context )
{
	Gaffer::ExecutableNode::Tasks tasks;
	n.executionRequirements( context, tasks );
	boost::python::list result;
	for( Gaffer::ExecutableNode::Tasks::const_iterator tIt = tasks.begin(); tIt != tasks.end(); ++tIt )
	{
		result.append( *tIt );
	}
	return result;
}

template<typename T>
void execute( T &n, const boost::python::list &contextsList )
{
	Gaffer::ExecutableNode::Contexts contexts;
	boost::python::container_utils::extend_container( contexts, contextsList );
	IECorePython::ScopedGILRelease gilRelease;
	n.execute( contexts );
}

} // namespace Detail

template<typename T, typename Ptr>
ExecutableNodeClass<T, Ptr>::ExecutableNodeClass( const char *docString )
	:	NodeClass<T, Ptr>( docString )
{
	def( "executionRequirements", &Detail::executionRequirements<T> );
	def( "executionHash", &T::executionHash );
	def( "execute", &Detail::execute<T> );	
}

} // namespace GafferBindings

#endif // GAFFERBINDINGS_EXECUTABLENODEBINDING_INL
