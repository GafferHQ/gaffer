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

#include "Gaffer/Plug.h"
#include "Gaffer/Context.h"
#include "GafferBindings/PlugBinding.h"

#include "GafferDispatch/ExecutableNode.h"
#include "GafferDispatchBindings/ExecutableNodeBinding.h"

using namespace boost::python;
using namespace IECore;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferDispatch;

namespace
{

unsigned long taskHash( const ExecutableNode::Task &t )
{
	const IECore::MurmurHash h = t.hash();
	return tbb::tbb_hasher( h.toString() );
}

ContextPtr taskContext( const ExecutableNode::Task &t, bool copy = true )
{
	if ( ConstContextPtr context = t.context() )
	{
		if ( copy )
		{
			return new Context( *context );
		}

		return boost::const_pointer_cast<Context>( context );
	}

	return NULL;
}

ExecutableNodePtr taskNode( const ExecutableNode::Task &t )
{
	if ( ConstExecutableNodePtr node = t.node() )
	{
		return boost::const_pointer_cast<ExecutableNode>( node );
	}

	return NULL;
}

IECore::MurmurHash taskPlugHash( const ExecutableNode::TaskPlug &t )
{
	IECorePython::ScopedGILRelease gilRelease;
	return t.hash();
}

void taskPlugExecute( const ExecutableNode::TaskPlug &t )
{
	IECorePython::ScopedGILRelease gilRelease;
	t.execute();
}

void taskPlugExecuteSequence( const ExecutableNode::TaskPlug &t, const boost::python::object &frameList )
{
	std::vector<float> frames;
	boost::python::container_utils::extend_container( frames, frameList );
	IECorePython::ScopedGILRelease gilRelease;
	t.executeSequence( frames );
}

boost::python::list taskPlugPreTasks( const ExecutableNode::TaskPlug &t )
{
	GafferDispatch::ExecutableNode::Tasks tasks;
	t.preTasks( tasks );
	boost::python::list result;
	for( GafferDispatch::ExecutableNode::Tasks::const_iterator tIt = tasks.begin(); tIt != tasks.end(); ++tIt )
	{
		result.append( *tIt );
	}
	return result;
}

boost::python::list taskPlugPostTasks( const ExecutableNode::TaskPlug &t )
{
	GafferDispatch::ExecutableNode::Tasks tasks;
	t.postTasks( tasks );
	boost::python::list result;
	for( GafferDispatch::ExecutableNode::Tasks::const_iterator tIt = tasks.begin(); tIt != tasks.end(); ++tIt )
	{
		result.append( *tIt );
	}
	return result;
}

} // namespace

void GafferDispatchBindings::bindExecutableNode()
{
	typedef ExecutableNodeWrapper<ExecutableNode> Wrapper;

	scope s = ExecutableNodeClass<ExecutableNode, Wrapper>();

	class_<ExecutableNode::Task>( "Task", no_init )
		.def( init<ExecutableNode::Task>() )
		.def( init<GafferDispatch::ExecutableNodePtr, const Gaffer::Context *>() )
		.def( "node", &taskNode )
		.def( "context", &taskContext, ( boost::python::arg_( "_copy" ) = true ) )
		.def("__eq__", &ExecutableNode::Task::operator== )
		.def("__hash__", &taskHash )
	;

	PlugClass<ExecutableNode::TaskPlug>()
		.def( init<const char *, Plug::Direction, unsigned>(
				(
					boost::python::arg_( "name" )=GraphComponent::defaultName<ExecutableNode::TaskPlug>(),
					boost::python::arg_( "direction" )=Plug::In,
					boost::python::arg_( "flags" )=Plug::Default
				)
			)
		)
		.def( "hash", &taskPlugHash )
		.def( "execute", &taskPlugExecute )
		.def( "executeSequence", &taskPlugExecuteSequence )
		.def( "requiresSequenceExecution", &ExecutableNode::TaskPlug::requiresSequenceExecution )
		.def( "preTasks", &taskPlugPreTasks )
		.def( "postTasks", &taskPlugPostTasks )
		// Adjusting the name so that it correctly reflects
		// the nesting, and can be used by the PlugSerialiser.
		.attr( "__name__" ) = "ExecutableNode.TaskPlug"
	;

}
