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

#ifndef GAFFER_BACKGROUNDTASK_H
#define GAFFER_BACKGROUNDTASK_H

#include "Gaffer/Export.h"

#include "IECore/Canceller.h"

#include "boost/noncopyable.hpp"

#include <condition_variable>
#include <functional>
#include <memory>
#include <mutex>

namespace Gaffer
{

class GraphComponent;
class Plug;

/// Gaffer's node graphs naturally support multiple concurrent computes
/// (or more generally, `Processes`). But such computes cannot be made
/// concurrently with edits to the node graph. This poses a problem in
/// GUI applications, where we wish to allow the user to continue to use
/// the UI and edit the graph while we perform incremental computes and
/// update the Viewer in the background.
///
/// BackgroundTask solves this problem by providing a synchronisation
/// mechanism between background computes and edits. This mechanism
/// automatically cancels all affected background operations before an
/// edit is performed, leaving the UI to restart the background tasks
/// once the edit has been completed.
class GAFFER_API BackgroundTask : public boost::noncopyable
{

	public :

		typedef std::function<void ( const IECore::Canceller &canceller )> Function;

		/// Launches a background task to run `function`, which is expected
		/// to perform asynchronous computes using the `subject` plug.
		/// The `function` is passed an `IECore::Canceller` object which must
		/// be checked periodically via `IECore::Canceller::check()`.
		///
		/// > Note : Gaffer's responsiveness to asynchronous edits is entirely
		/// > dependent on prompt responses to cancellation requests.
		BackgroundTask( const Plug *subject, const Function &function );
		/// Calls `cancelAndWait()`. This allows the lifetime of the
		/// BackgroundTask to be used to protect access to resources
		//  required by the background function.
		~BackgroundTask();

		/// Cancels the background call.
		void cancel();
		/// Blocks until the background call returns, either through
		/// cancellation or running to completion.
		void wait();
		/// Utility to call `cancel()` then `wait()`.
		void cancelAndWait();

		/// Returns true once the background call as finished, either
		/// through cancellation or running to completion.
		bool done() const;

	private :

		// Called by `Action` to ensure that any related tasks are cancelled
		// before an edit is made to `actionSubject`.
		static void cancelAffectedTasks( const GraphComponent *actionSubject );
		friend class Action;
		friend class ScriptNode;

		// Function to be executed.
		Function m_function;

		// Control structure for the TBB task we use to execute
		// `m_function`. This is shared with the TBB task.
		struct TaskData;
		std::shared_ptr<TaskData> m_taskData;

};

} // namespace Gaffer

#endif // GAFFER_BACKGROUNDTASK_H
