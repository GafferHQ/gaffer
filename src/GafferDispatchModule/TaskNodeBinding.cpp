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
#include "boost/python/suite/indexing/container_utils.hpp"

#include "TaskNodeBinding.h"

#include "GafferDispatchBindings/TaskNodeBinding.h"

#include "GafferDispatch/FrameMask.h"
#include "GafferDispatch/TaskList.h"
#include "GafferDispatch/TaskNode.h"

#include "GafferBindings/PlugBinding.h"

#include "Gaffer/Plug.h"
#include "Gaffer/Context.h"

using namespace boost::python;
using namespace IECore;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferDispatch;
using namespace GafferDispatchBindings;

namespace
{

ContextPtr taskContext( const TaskNode::Task &t, bool copy = true )
{
	if ( ConstContextPtr context = t.context() )
	{
		if ( copy )
		{
			return new Context( *context );
		}

		return boost::const_pointer_cast<Context>( context );
	}

	return nullptr;
}

TaskNode::TaskPlugPtr taskPlug( const TaskNode::Task &t )
{
	return const_cast<TaskNode::TaskPlug *>( t.plug() );
}

IECore::MurmurHash taskPlugHash( const TaskNode::TaskPlug &t )
{
	IECorePython::ScopedGILRelease gilRelease;
	return t.hash();
}

void taskPlugExecute( const TaskNode::TaskPlug &t )
{
	IECorePython::ScopedGILRelease gilRelease;
	t.execute();
}

void taskPlugExecuteSequence( const TaskNode::TaskPlug &t, const boost::python::object &frameList )
{
	std::vector<float> frames;
	boost::python::container_utils::extend_container( frames, frameList );
	IECorePython::ScopedGILRelease gilRelease;
	t.executeSequence( frames );
}

boost::python::list taskPlugPreTasks( const TaskNode::TaskPlug &t )
{
	GafferDispatch::TaskNode::Tasks tasks;
	{
		IECorePython::ScopedGILRelease gilRelease;
		t.preTasks( tasks );
	}
	boost::python::list result;
	for( GafferDispatch::TaskNode::Tasks::const_iterator tIt = tasks.begin(); tIt != tasks.end(); ++tIt )
	{
		result.append( *tIt );
	}
	return result;
}

boost::python::list taskPlugPostTasks( const TaskNode::TaskPlug &t )
{
	GafferDispatch::TaskNode::Tasks tasks;
	{
		IECorePython::ScopedGILRelease gilRelease;
		t.postTasks( tasks );
	}
	boost::python::list result;
	for( GafferDispatch::TaskNode::Tasks::const_iterator tIt = tasks.begin(); tIt != tasks.end(); ++tIt )
	{
		result.append( *tIt );
	}
	return result;
}

} // namespace

void GafferDispatchModule::bindTaskNode()
{
	using Wrapper = TaskNodeWrapper<TaskNode>;

	{
		scope s = TaskNodeClass<TaskNode, Wrapper>();

		class_<TaskNode::Task>( "Task", no_init )
			.def( init<TaskNode::Task>() )
			.def( init<GafferDispatch::TaskNode::TaskPlugPtr, const Gaffer::Context *>() )
			.def( init<GafferDispatch::TaskNodePtr, const Gaffer::Context *>() )
			.def( "plug", &taskPlug )
			.def( "context", &taskContext, ( boost::python::arg_( "_copy" ) = true ) )
			.def("__eq__", &TaskNode::Task::operator== )
		;

		PlugClass<TaskNode::TaskPlug>()
			.def( init<const char *, Plug::Direction, unsigned>(
					(
						boost::python::arg_( "name" )=GraphComponent::defaultName<TaskNode::TaskPlug>(),
						boost::python::arg_( "direction" )=Plug::In,
						boost::python::arg_( "flags" )=Plug::Default
					)
				)
			)
			.def( "hash", &taskPlugHash )
			.def( "execute", &taskPlugExecute )
			.def( "executeSequence", &taskPlugExecuteSequence )
			.def( "requiresSequenceExecution", &TaskNode::TaskPlug::requiresSequenceExecution )
			.def( "preTasks", &taskPlugPreTasks )
			.def( "postTasks", &taskPlugPostTasks )
			// Adjusting the name so that it correctly reflects
			// the nesting, and can be used by the PlugSerialiser.
			.attr( "__qualname__" ) = "TaskNode.TaskPlug"
		;
	}

	TaskNodeClass<TaskList>();
	TaskNodeClass<FrameMask>();

}
