//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#include "GafferDispatch/TaskNode.h"

#include "GafferDispatch/Dispatcher.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"
#include "Gaffer/Dot.h"
#include "Gaffer/Process.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/SubGraph.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferDispatch;

//////////////////////////////////////////////////////////////////////////
// Task implementation
//////////////////////////////////////////////////////////////////////////

TaskNode::Task::Task( ConstTaskPlugPtr plug, const Gaffer::Context *context )
	:	m_plug( plug ), m_context( new Context( *context ) )
{
}

TaskNode::Task::Task( TaskNodePtr n, const Context *c ) : m_plug( n->taskPlug() ), m_context( new Context( *c ) )
{
}

const TaskNode::TaskPlug *TaskNode::Task::plug() const
{
	return m_plug.get();
}

const Context *TaskNode::Task::context() const
{
	return m_context.get();
}

bool TaskNode::Task::operator == ( const Task &rhs ) const
{
	return m_plug == rhs.m_plug && *m_context == *rhs.m_context;
}

//////////////////////////////////////////////////////////////////////////
// TaskPlug implementation.
//////////////////////////////////////////////////////////////////////////

namespace
{

class TaskNodeProcess : public Gaffer::Process
{

	public :

		TaskNodeProcess( const IECore::InternedString &type, const TaskNode::TaskPlug *plug )
			:	Process( type, plug->source(), plug )
		{
		}

		const TaskNode *taskNode() const
		{
			const TaskNode *n = runTimeCast<const TaskNode>( plug()->node() );
			if( !n )
			{
				throw IECore::Exception( boost::str( boost::format( "TaskPlug \"%s\" has no TaskNode." ) % plug()->fullName() ) );
			}
			return n;
		}

		void handleException()
		{
			Gaffer::Process::handleException();
		}

		static InternedString hashProcessType;
		static InternedString executeProcessType;
		static InternedString executeSequenceProcessType;
		static InternedString requiresSequenceExecutionProcessType;
		static InternedString preTasksProcessType;
		static InternedString postTasksProcessType;

};

InternedString TaskNodeProcess::hashProcessType( "taskNode:hash" );
InternedString TaskNodeProcess::executeProcessType( "taskNode:execute" );
InternedString TaskNodeProcess::executeSequenceProcessType( "taskNode:executeSequence" );
InternedString TaskNodeProcess::requiresSequenceExecutionProcessType( "taskNode:requiresSequenceExecution" );
InternedString TaskNodeProcess::preTasksProcessType( "taskNode:preTasks" );
InternedString TaskNodeProcess::postTasksProcessType( "taskNode:postTasks" );

} // namespace

GAFFER_PLUG_DEFINE_TYPE( TaskNode::TaskPlug );

TaskNode::TaskPlug::TaskPlug( const std::string &name, Direction direction, unsigned flags )
	:	Plug( name, direction, flags )
{
}

bool TaskNode::TaskPlug::acceptsChild( const Gaffer::GraphComponent *potentialChild ) const
{
	return false;
}

bool TaskNode::TaskPlug::acceptsInput( const Plug *input ) const
{
	if( !Plug::acceptsInput( input ) )
	{
		return false;
	}

	if( !input )
	{
		return true;
	}

	if( input->isInstanceOf( staticTypeId() ) )
	{
		return true;
	}

	// Ideally we'd return false right now, but we must
	// provide backwards compatibility with old scripts
	// where the task plugs were just represented
	// as standard Plugs, and may have been promoted to
	// Boxes and Dots in that form.
	const ScriptNode *script = ancestor<ScriptNode>();
	if( !script || !script->isExecuting() )
	{
		return false;
	}

	if( input->typeId() == Plug::staticTypeId() )
	{
		const Plug *sourcePlug = input->source();
		if( sourcePlug->isInstanceOf( staticTypeId() ) )
		{
			return true;
		}
		const Node *sourceNode = sourcePlug->node();
		return runTimeCast<const SubGraph>( sourceNode ) || runTimeCast<const Dot>( sourceNode );
	}

	return false;
}

PlugPtr TaskNode::TaskPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	return new TaskPlug( name, direction, getFlags() );
}

IECore::MurmurHash TaskNode::TaskPlug::hash() const
{
	TaskNodeProcess p( TaskNodeProcess::hashProcessType, this );
	try
	{
		return p.taskNode()->hash( p.context() );
	}
	catch( ... )
	{
		p.handleException();
		return MurmurHash();
	}
}

void TaskNode::TaskPlug::execute() const
{
	TaskNodeProcess p( TaskNodeProcess::executeProcessType, this );
	try
	{
		p.taskNode()->execute();
	}
	catch( ... )
	{
		p.handleException();
		return;
	}
}

void TaskNode::TaskPlug::executeSequence( const std::vector<float> &frames ) const
{
	TaskNodeProcess p( TaskNodeProcess::executeSequenceProcessType, this );
	try
	{
		p.taskNode()->executeSequence( frames );
	}
	catch( ... )
	{
		p.handleException();
		return;
	}
}

bool TaskNode::TaskPlug::requiresSequenceExecution() const
{
	TaskNodeProcess p( TaskNodeProcess::requiresSequenceExecutionProcessType, this );
	try
	{
		return p.taskNode()->requiresSequenceExecution();
	}
	catch( ... )
	{
		p.handleException();
		return false;
	}
}

void TaskNode::TaskPlug::preTasks( Tasks &tasks ) const
{
	TaskNodeProcess p( TaskNodeProcess::preTasksProcessType, this );
	try
	{
		p.taskNode()->preTasks( p.context(), tasks );
	}
	catch( ... )
	{
		p.handleException();
		return;
	}
}

void TaskNode::TaskPlug::postTasks( Tasks &tasks ) const
{
	TaskNodeProcess p( TaskNodeProcess::postTasksProcessType, this );
	try
	{
		p.taskNode()->postTasks( p.context(), tasks );
	}
	catch( ... )
	{
		p.handleException();
		return;
	}
}

//////////////////////////////////////////////////////////////////////////
// TaskNode implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( TaskNode )

size_t TaskNode::g_firstPlugIndex;

TaskNode::TaskNode( const std::string &name )
	:	DependencyNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ArrayPlug( "preTasks", Plug::In, new TaskPlug( "preTask0" ) ) );
	addChild( new ArrayPlug( "postTasks", Plug::In, new TaskPlug( "postTask0" ) ) );
	addChild( new TaskPlug( "task", Plug::Out ) );

	PlugPtr dispatcherPlug = new Plug( "dispatcher", Plug::In );
	addChild( dispatcherPlug );

	Dispatcher::setupPlugs( dispatcherPlug.get() );
}

TaskNode::~TaskNode()
{
}

ArrayPlug *TaskNode::preTasksPlug()
{
	return getChild<ArrayPlug>( g_firstPlugIndex );
}

const ArrayPlug *TaskNode::preTasksPlug() const
{
	return getChild<ArrayPlug>( g_firstPlugIndex );
}

ArrayPlug *TaskNode::postTasksPlug()
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 1 );
}

const ArrayPlug *TaskNode::postTasksPlug() const
{
	return getChild<ArrayPlug>( g_firstPlugIndex + 1 );
}

TaskNode::TaskPlug *TaskNode::taskPlug()
{
	return getChild<TaskPlug>( g_firstPlugIndex + 2 );
}

const TaskNode::TaskPlug *TaskNode::taskPlug() const
{
	return getChild<TaskPlug>( g_firstPlugIndex + 2 );
}

Plug *TaskNode::dispatcherPlug()
{
	return getChild<Plug>( g_firstPlugIndex + 3 );
}

const Plug *TaskNode::dispatcherPlug() const
{
	return getChild<Plug>( g_firstPlugIndex + 3 );
}

void TaskNode::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	DependencyNode::affects( input, outputs );

	if( affectsTask( input ) )
	{
		outputs.push_back( taskPlug() );
	}
}

bool TaskNode::affectsTask( const Plug *input ) const
{
	if(
		input->direction() != Plug::In ||
		userPlug()->isAncestorOf( input ) ||
		postTasksPlug()->isAncestorOf( input ) ||
		input == taskPlug()
	)
	{
		return false;
	}
	return true;
}

void TaskNode::preTasks( const Context *context, Tasks &tasks ) const
{
	for( TaskPlug::Iterator cIt( preTasksPlug() ); !cIt.done(); ++cIt )
	{
		tasks.push_back( Task( *cIt, context ) );
	}
}

void TaskNode::postTasks( const Context *context, Tasks &tasks ) const
{
	for( TaskPlug::Iterator cIt( postTasksPlug() ); !cIt.done(); ++cIt )
	{
		tasks.push_back( Task( *cIt, context ) );
	}
}

IECore::MurmurHash TaskNode::hash( const Context *context ) const
{
	IECore::MurmurHash h;
	h.append( typeId() );
	return h;
}

void TaskNode::execute() const
{
}

void TaskNode::executeSequence( const std::vector<float> &frames ) const
{
	Context::EditableScope timeScope( Context::current() );

	for ( std::vector<float>::const_iterator it = frames.begin(); it != frames.end(); ++it )
	{
		timeScope.setFrame( *it );
		execute();
	}
}

bool TaskNode::requiresSequenceExecution() const
{
	return false;
}
