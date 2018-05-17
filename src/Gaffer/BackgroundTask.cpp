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
#include "Gaffer/ScriptNode.h"

#include "IECore/MessageHandler.h"

#include "boost/multi_index/member.hpp"
#include "boost/multi_index/hashed_index.hpp"
#include "boost/multi_index_container.hpp"

#include "tbb/task.h"

using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

class FunctionTask : public tbb::task
{
	public :

		typedef std::function<void ()> Function;

		FunctionTask( const Function &f )
			: m_f( f )
		{
		}

		tbb::task *execute() override
		{
			m_f();
			return nullptr;
		}

	private :

		Function m_f;

};

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

typedef boost::multi_index::multi_index_container<
	ActiveTask,
	boost::multi_index::indexed_by<
		boost::multi_index::hashed_unique<
			boost::multi_index::member<ActiveTask, BackgroundTask *, &ActiveTask::task>
		>,
		boost::multi_index::hashed_non_unique<
			boost::multi_index::member<ActiveTask, ConstScriptNodePtr, &ActiveTask::subject>
		>
	>
> ActiveTasks;

ActiveTasks &activeTasks()
{
	static ActiveTasks a;
	return a;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// BackgroundTask
//////////////////////////////////////////////////////////////////////////

BackgroundTask::BackgroundTask( const Plug *subject, const Function &function )
	:	m_done( false )
{
	activeTasks().insert( ActiveTask{ this, scriptNode( subject ) } );

	tbb::task *functionTask = new( tbb::task::allocate_root() ) FunctionTask(
		[this, function] {
			try
			{
				function( m_canceller );
			}
			catch( const std::exception &e )
			{
				IECore::msg(
					IECore::Msg::Error,
					"BackgroundTask",
					e.what()
				);
			}
			catch( const IECore::Cancelled &e )
			{
				// No need to do anything
			}
			catch( ... )
			{
				IECore::msg(
					IECore::Msg::Error,
					"BackgroundTask",
					"Unknown error"
				);
			}
			std::unique_lock<std::mutex> lock( m_mutex );
			m_done = true;
			m_conditionVariable.notify_one();
		}
	);
	tbb::task::enqueue( *functionTask );
}

BackgroundTask::~BackgroundTask()
{
	cancelAndWait();
}

void BackgroundTask::cancel()
{
	m_canceller.cancel();
}

void BackgroundTask::wait()
{
	std::unique_lock<std::mutex> lock( m_mutex );
	m_conditionVariable.wait( lock, [this]{ return m_done == true; } );
	activeTasks().erase( this );
}

void BackgroundTask::cancelAndWait()
{
	m_canceller.cancel();
	wait();
}

bool BackgroundTask::done() const
{
	return m_done;
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
	auto range = a.get<1>().equal_range( s );
	for( auto it = range.first; it != range.second; )
	{
		// Cancellation invalidates iterator, so must increment first.
		auto nextIt = std::next( it );
		it->task->cancelAndWait();
		it = nextIt;
	}
}
