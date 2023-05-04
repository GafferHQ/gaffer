//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/BackgroundTask.h"

#include "Gaffer/ApplicationRoot.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/ThreadState.h"

#include "IECore/MessageHandler.h"

#include "boost/multi_index/member.hpp"
#include "boost/multi_index/hashed_index.hpp"
#include "boost/multi_index_container.hpp"

#include "tbb/task_arena.h"

using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

const ScriptNode *scriptNode( const GraphComponent *subject )
{
	if( !subject )
	{
		return nullptr;
	}
	else if( auto s = runTimeCast<const ScriptNode>( subject ) )
	{
		return s;
	}
	else if( auto s = subject->ancestor<ScriptNode>() )
	{
		return s;
	}
	else
	{
		// Unfortunately the GafferUI::View classes house internal
		// nodes which live outside any ScriptNode, but must still
		// take part in cancellation. This hack recovers the ScriptNode
		// for the node the view is currently connected to.
		while( subject )
		{
			if( subject->isInstanceOf( "GafferUI::View" ) )
			{
				return scriptNode( subject->getChild<Plug>( "in" )->getInput() );
			}
			subject = subject->parent();
		}
		return nullptr;
	}
}

struct ActiveTask
{
	BackgroundTask *task;
	// Held via Ptr to keep the script alive
	// for the duration of the task.
	ConstScriptNodePtr subject;
};

using ActiveTasks = boost::multi_index::multi_index_container<
	ActiveTask,
	boost::multi_index::indexed_by<
		boost::multi_index::hashed_unique<
			boost::multi_index::member<ActiveTask, BackgroundTask *, &ActiveTask::task>
		>,
		boost::multi_index::hashed_non_unique<
			boost::multi_index::member<ActiveTask, ConstScriptNodePtr, &ActiveTask::subject>
		>
	>
>;

ActiveTasks &activeTasks()
{
	static ActiveTasks a;
	return a;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// BackgroundTask
//////////////////////////////////////////////////////////////////////////

struct BackgroundTask::TaskData : public boost::noncopyable
{
	TaskData( Function *function )
		:	function( function ), status( Pending )
	{
	}

	Function *function;
	IECore::Canceller canceller;
	std::mutex mutex; // Protects `conditionVariable` and `status`
	std::condition_variable conditionVariable;
	Status status;
};

BackgroundTask::BackgroundTask( const Plug *subject, const Function &function )
	:	m_function( function ), m_taskData( std::make_shared<TaskData>( &m_function ) )
{
	activeTasks().insert( ActiveTask{ this, scriptNode( subject ) } );

	// Enqueue task into current arena.
	tbb::task_arena( tbb::task_arena::attach() ).enqueue(
		[taskData = m_taskData] {

			// Early out if we were cancelled before the task
			// even started.
			std::unique_lock<std::mutex> lock( taskData->mutex );
			if( taskData->status == Cancelled )
			{
				return;
			}

			// Otherwise do the work.

			taskData->status = Running;
			lock.unlock();

			// Reset thread state rather then inherit the random
			// one that TBB task-stealing might present us with.
			const ThreadState defaultThreadState;
			ThreadState::Scope threadStateScope( defaultThreadState );

			Status status;
			try
			{
				(*taskData->function)( taskData->canceller );
				status = Completed;
			}
			catch( const std::exception &e )
			{
				IECore::msg(
					IECore::Msg::Error,
					"BackgroundTask",
					e.what()
				);
				status = Errored;
			}
			catch( const IECore::Cancelled & )
			{
				// No need to do anything
				status = Cancelled;
			}
			catch( ... )
			{
				IECore::msg(
					IECore::Msg::Error,
					"BackgroundTask",
					"Unknown error"
				);
				status = Errored;
			}

			lock.lock();
			taskData->status = status;
			taskData->conditionVariable.notify_one();
		}
	);
}

BackgroundTask::~BackgroundTask()
{
	cancelAndWait();
}

void BackgroundTask::cancel()
{
	std::unique_lock<std::mutex> lock( m_taskData->mutex );
	if( m_taskData->status == Pending )
	{
		m_taskData->status = Cancelled;
	}
	m_taskData->canceller.cancel();
}

void BackgroundTask::wait()
{
	std::unique_lock<std::mutex> lock( m_taskData->mutex );
	m_taskData->conditionVariable.wait(
		lock,
		[this]{
			switch( this->m_taskData->status )
			{
				case Completed :
				case Cancelled :
				case Errored :
					return true;
				default :
					return false;
			}
		}
	);
	activeTasks().erase( this );
}

bool BackgroundTask::waitFor( float seconds )
{
	using namespace std::chrono;

	// `wait_for( duration<float> )` seems to be unreliable,
	// so we cast to milliseconds first.
	milliseconds timeoutDuration = duration_cast<milliseconds>( duration<float>( seconds ) );

	std::unique_lock<std::mutex> lock( m_taskData->mutex );
	const bool completed = m_taskData->conditionVariable.wait_for(
		lock,
		timeoutDuration,
		[this]{
			switch( this->m_taskData->status )
			{
				case Completed :
				case Cancelled :
				case Errored :
					return true;
				default :
					return false;
			}
		}
	);

	if( completed )
	{
		activeTasks().erase( this );
	}
	return completed;
}

void BackgroundTask::cancelAndWait()
{
	cancel();
	wait();
}

BackgroundTask::Status BackgroundTask::status() const
{
	std::unique_lock<std::mutex> lock( m_taskData->mutex );
	return m_taskData->status;
}

void BackgroundTask::cancelAffectedTasks( const GraphComponent *actionSubject )
{
	const ActiveTasks &a = activeTasks();
	if( !a.size() )
	{
		return;
	}

	// Here our goal is to cancel any tasks which will be affected
	// by the edit about to be made to `actionSubject`. In theory
	// the most accurate thing to do might be to limit cancellation
	// to only the downstream affected plugs for `actionSubject`, but
	// for now we content ourselves with a cruder approach : we simply
	// cancel all tasks from the same ScriptNode.
	/// \todo Investigate fancier approaches.

	const ScriptNode *s = scriptNode( actionSubject );
	if( !s )
	{
		if( auto application = actionSubject->ancestor<ApplicationRoot>() )
		{
			// No ScriptNode, but still under an ApplicationRoot, most likely
			// on the Preferences node. Cancel _everything_, so that preferences
			// plugs can be used as inputs to other nodes.
			for( const auto &s : ScriptNode::Range( *application->scripts() ) )
			{
				cancelAffectedTasks( s.get() );
			}
		}
		return;
	}

	auto range = a.get<1>().equal_range( s );

	// Call cancel for everything first.
	for( auto it = range.first; it != range.second; ++it )
	{
		it->task->cancel();
	}
	// And then perform all the waits. This way the wait on one
	// task doesn't delay the start of cancellation for the next.
	for( auto it = range.first; it != range.second; )
	{
		// Wait invalidates iterator, so must increment first.
		auto nextIt = std::next( it );
		it->task->wait();
		it = nextIt;
	}
}
