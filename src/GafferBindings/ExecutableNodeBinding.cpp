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

#include "boost/python.hpp"
#include "boost/python/extract.hpp"

#include "IECorePython/Wrapper.h"
#include "IECorePython/RunTimeTypedBinding.h"

#include "Gaffer/Plug.h"
#include "Gaffer/Context.h"
#include "Gaffer/ExecutableNode.h"
#include "GafferBindings/NodeBinding.h"
#include "GafferBindings/ExecutableNodeBinding.h"

using namespace boost::python;
using namespace IECore;
using namespace IECorePython;
using namespace GafferBindings;
using namespace Gaffer;

static unsigned long taskHash( const ExecutableNode::Task &t )
{
	const IECore::MurmurHash h = t.hash();
	return tbb::tbb_hasher( h.toString() );
}

static ContextPtr taskContext( const ExecutableNode::Task &t, bool copy = true )
{
	if ( ConstContextPtr context = t.context() )
	{
		if ( copy )
		{
			return new Context( *context );
		}

		return boost::const_pointer_cast<Context>( context );
	}

	return 0;
}

static ExecutableNodePtr taskNode( const ExecutableNode::Task &t )
{
	if ( ConstExecutableNodePtr node = t.node() )
	{
		return boost::const_pointer_cast<ExecutableNode>( node );
	}

	return 0;
}

void GafferBindings::bindExecutableNode()
{
	typedef ExecutableNodeWrapper<ExecutableNode> Wrapper;

	scope s = ExecutableNodeClass<ExecutableNode, Wrapper>();

	class_<ExecutableNode::Task>( "Task", no_init )
		.def( init<ExecutableNode::Task>() )
		.def( init<Gaffer::ExecutableNodePtr,Gaffer::ContextPtr>() )
		.def( "node", &taskNode )
		.def( "context", &taskContext, ( boost::python::arg_( "_copy" ) = true ) )
		.def("__eq__", &ExecutableNode::Task::operator== )
		.def("__hash__", &taskHash )
	;
}
