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

#include "Gaffer/SubGraph.h"
#include "Gaffer/Dot.h"
#include "Gaffer/Context.h"
#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Process.h"

#include "GafferDispatch/Dispatcher.h"
#include "GafferDispatch/TaskNode.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferDispatch;

//////////////////////////////////////////////////////////////////////////
// Task implementation
//////////////////////////////////////////////////////////////////////////

TaskNode::Task::Task( ConstTaskPlugPtr plug, const Gaffer::Context *context )
	:	m_plug( plug ), m_context( new Context( *context ) )
{
	Context::Scope scopedContext( m_context.get() );
	m_hash = m_plug->hash();
}

TaskNode::Task::Task( const Task &t ) : m_plug( t.m_plug ), m_context( t.m_context ), m_hash( t.m_hash )
{
}

TaskNode::Task::Task( TaskNodePtr n, const Context *c ) : m_plug( n->taskPlug() ), m_context( new Context( *c ) )
{
	Context::Scope scopedContext( m_context.get() );
	m_hash = m_plug->hash();
}

const TaskNode::TaskPlug *TaskNode::Task::plug() const
{
	return m_plug.get();
}

const TaskNode *TaskNode::Task::node() const
{
	return runTimeCast<const TaskNode>( m_plug->node() );
}

const Context *TaskNode::Task::context() const
{
	return m_context.get();
}

const MurmurHash TaskNode::Task::hash() const
{
	return m_hash;
}

bool TaskNode::Task::operator == ( const Task &rhs ) const
{
	return ( m_hash == rhs.m_hash );
}

bool TaskNode::Task::operator < ( const Task &rhs ) const
{
	return ( m_hash < rhs.m_hash );
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
			:	Process( type, plug->source<Plug>(), plug )
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

IE_CORE_DEFINERUNTIMETYPED( TaskNode::TaskPlug );

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
	if( input->typeId() == Plug::staticTypeId() )
	{
		const Plug *sourcePlug = input->source<Plug>();
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
	return p.taskNode()->hash( Context::current() );
}

void TaskNode::TaskPlug::execute() const
{
	TaskNodeProcess p( TaskNodeProcess::executeProcessType, this );
	return p.taskNode()->execute();
}

void TaskNode::TaskPlug::executeSequence( const std::vector<float> &frames ) const
{
	TaskNodeProcess p( TaskNodeProcess::executeSequenceProcessType, this );
	return p.taskNode()->executeSequence( frames );
}

bool TaskNode::TaskPlug::requiresSequenceExecution() const
{
	TaskNodeProcess p( TaskNodeProcess::requiresSequenceExecutionProcessType, this );
	return p.taskNode()->requiresSequenceExecution();
}

void TaskNode::TaskPlug::preTasks( Tasks &tasks ) const
{
	TaskNodeProcess p( TaskNodeProcess::preTasksProcessType, this );
	return p.taskNode()->preTasks( Context::current(), tasks );
}

void TaskNode::TaskPlug::postTasks( Tasks &tasks ) const
{
	TaskNodeProcess p( TaskNodeProcess::postTasksProcessType, this );
	return p.taskNode()->postTasks( Context::current(), tasks );
}

//////////////////////////////////////////////////////////////////////////
// TaskNode implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( TaskNode )

size_t TaskNode::g_firstPlugIndex;

TaskNode::TaskNode( const std::string &name )
	:	Node( name )
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

void TaskNode::preTasks( const Context *context, Tasks &tasks ) const
{
	for( PlugIterator cIt( preTasksPlug() ); !cIt.done(); ++cIt )
	{
		Plug *source = (*cIt)->source<Plug>();
		if( source != *cIt )
		{
			if( TaskNodePtr n = runTimeCast<TaskNode>( source->node() ) )
			{
				tasks.push_back( Task( n, context ) );
			}
		}
	}
}

void TaskNode::postTasks( const Context *context, Tasks &tasks ) const
{
	for( PlugIterator cIt( postTasksPlug() ); !cIt.done(); ++cIt )
	{
		Plug *source = (*cIt)->source<Plug>();
		if( source != *cIt )
		{
			if( TaskNodePtr n = runTimeCast<TaskNode>( source->node() ) )
			{
				tasks.push_back( Task( n, context ) );
			}
		}
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
	ContextPtr context = new Context( *Context::current(), Context::Borrowed );
	Context::Scope scopedContext( context.get() );

	for ( std::vector<float>::const_iterator it = frames.begin(); it != frames.end(); ++it )
	{
		context->setFrame( *it );
		execute();
	}
}

bool TaskNode::requiresSequenceExecution() const
{
	return false;
}
