//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#pragma once

#include "Gaffer/Export.h"
#include "Gaffer/Plug.h"

#include "IECore/RefCounted.h"

#include "boost/container/flat_set.hpp"
#include "boost/noncopyable.hpp"

#include <stack>

namespace Gaffer
{

class Context;
class Process;
IE_CORE_FORWARDDECLARE( Monitor );

/// ThreadState provides the foundations for multi-threaded compute
/// in Gaffer. Typically you will not interact with ThreadStates directly,
/// but will instead use the specialised APIs provided by the Process,
/// Context and Monitor classes. The exception to this is when using
/// task-based TBB algorithms, in which case it is necessary to manually
/// transfer the current ThreadState from the calling code to the tasks
/// running on its behalf. For example :
///
/// ```
/// const ThreadState &threadState = ThreadState::current();
/// tbb::parallel_for(
/// 	tbb::blocked_range<size_t>( ... ),
/// 	[&threadState] ( const tbb::blocked_range<size_t> &r )
/// 	{
/// 		ThreadState::Scope threadStateScope( threadState );
/// 		...
/// 	}
/// );
/// ```
class GAFFER_API ThreadState
{

	public :

		/// Constructs a default thread state, with no current Process,
		/// no active monitors, and a default constructed Context.
		ThreadState();

		class GAFFER_API Scope : public boost::noncopyable
		{

			public :

				/// Scopes a copy of `state` on the current
				/// thread. When a process spawns TBB tasks, each
				/// task _must_ use this to transfer `ThreadState::current()`
				/// from the calling thread to the thread executing
				/// the task.
				Scope( const ThreadState &state );
				/// Pops the ThreadState that was pushed by the
				/// constructor.
				~Scope();

			protected :

				/// Pushes a copy of the current ThreadState onto
				/// the stack for this thread. Passing `push = false`
				/// yields a no-op.
				Scope( bool push = true );

				/// The ThreadState being managed by this scope.
				/// Will be null if the constructor is called with
				/// `push = false`.
				ThreadState *m_threadState;

			private :

				std::stack<ThreadState> *m_stack;

		};

		static const ThreadState &current();

		const Context *context() const { return m_context; }
		const Process *process() const { return m_process; }

	private :

		friend class Process;
		friend class Context;
		friend class Monitor;

		using MonitorSet = boost::container::flat_set<MonitorPtr>;

		const Context *m_context;
		const Process *m_process;
		const MonitorSet *m_monitors;
		bool m_mightForceMonitoring;

		static const MonitorSet g_defaultMonitors;
		static const ThreadState g_defaultState;

};

} // namespace Gaffer
