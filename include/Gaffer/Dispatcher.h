//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//	  * Redistributions of source code must retain the above
//		copyright notice, this list of conditions and the following
//		disclaimer.
//
//	  * Redistributions in binary form must reproduce the above
//		copyright notice, this list of conditions and the following
//		disclaimer in the documentation and/or other materials provided with
//		the distribution.
//
//	  * Neither the name of John Haddon nor the names of
//		any other contributors to this software may be used to endorse or
//		promote products derived from this software without specific prior
//		written permission.
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

#ifndef GAFFER_DISPATCHER_H
#define GAFFER_DISPATCHER_H

#include <string>
#include <vector>
#include <map>
#include <set>

#include "boost/signals.hpp"

#include "IECore/CompoundData.h"
#include "IECore/FrameList.h"
#include "IECore/RunTimeTyped.h"

#include "Gaffer/NumericPlug.h"
#include "Gaffer/TypedPlug.h"
#include "Gaffer/ExecutableNode.h"

#include "GafferBindings/DispatcherBinding.h" // to enable friend declaration for TaskBatch.

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Dispatcher )
IE_CORE_FORWARDDECLARE( CompoundPlug )

namespace Detail
{

struct PreDispatchSignalCombiner
{
	typedef bool result_type;

	template<typename InputIterator>
	bool operator()( InputIterator first, InputIterator last ) const
	{
		while ( first != last )
		{
			if( *first )
			{
				return true;
			}

			++first;
		}

		return false;
	}
};

} // namespace Detail

/// Abstract base class which defines an interface for scheduling the execution
/// of Context specific Tasks from ExecutableNodes which exist within a ScriptNode.
/// Dispatchers can also modify ExecutableNodes during construction, adding
/// plugs which affect Task execution.
class Dispatcher : public Node
{
	public :

		Dispatcher( const std::string &name=defaultName<Dispatcher>() );
		virtual ~Dispatcher();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::Dispatcher, DispatcherTypeId, Node );

		typedef boost::signal<bool (const Dispatcher *, const std::vector<ExecutableNodePtr> &), Detail::PreDispatchSignalCombiner> PreDispatchSignal;
		typedef boost::signal<void (const Dispatcher *, const std::vector<ExecutableNodePtr> &, bool)> PostDispatchSignal;

		//! @name Dispatch Signals
		/// These signals are emitted on dispatch events for any registered Dispatcher instance.
		////////////////////////////////////////////////////////////////////////////////////////
		//@{
		/// Called when any dispatcher is about to dispatch nodes. Slots should have the
		/// signature `bool slot( dispatcher, nodes )`, and may return True to cancel
		/// the dispatch, or False to allow it to continue.
		static PreDispatchSignal &preDispatchSignal();
		/// Called after any dispatcher has finished dispatching nodes. Slots should have the
		/// signature `void slot( dispatcher, nodes, bool )`. The third argument will be True
		/// if the process was successful, and False otherwise.
		static PostDispatchSignal &postDispatchSignal();
		//@}

		/// Calls doDispatch, taking care to trigger the dispatch signals at the appropriate times.
		/// Note that this will throw unless all of the nodes are either ExecutableNodes or Boxes.
		void dispatch( const std::vector<NodePtr> &nodes ) const;

		enum FramesMode
		{
			CurrentFrame,
			FullRange,
			CustomRange
		};

		//! @name Frame range
		/// Dispatchers define a frame range for execution.
		///////////////////////////////////////////////////
		//@{
		/// Returns a FramesMode for getting the active frame range.
		IntPlug *framesModePlug();
		const IntPlug *framesModePlug() const;
		/// Returns frame range to be used when framesModePlug is set to CustomRange.
		StringPlug *frameRangePlug();
		const StringPlug *frameRangePlug() const;
		//@}

		//! @name Dispatcher Jobs
		/// Utility functions which derived classes may use when dispatching jobs.
		//////////////////////////////////////////////////////////////////////////
		//@{
		/// Returns the name of the next job to dispatch.
		StringPlug *jobNamePlug();
		const StringPlug *jobNamePlug() const;
		/// Returns the plug which specifies the directory used by dispatchers to store temporary
		/// files on a per-job basis.
		StringPlug *jobsDirectoryPlug();
		const StringPlug *jobsDirectoryPlug() const;
		/// At the start of dispatch(), a directory is created under jobsDirectoryPlug + jobNamePlug
		/// which the dispatcher writes temporary files to. This method returns the most recent created directory.
		const std::string jobDirectory() const;
		//@}

		//! @name Registration
		/// Utility functions for registering and retrieving Dispatchers.
		/////////////////////////////////////////////////////////////////
		//@{
		/// Register a named Dispatcher instance.
		static void registerDispatcher( const std::string &name, DispatcherPtr dispatcher );
		/// Fills the vector with the names of all the registered Dispatchers.
		static void dispatcherNames( std::vector<std::string> &names );
		/// Returns a registered Dispatcher by name.
		static const Dispatcher *dispatcher( const std::string &name );
		//@}

	protected :

		friend class ExecutableNode;

		IE_CORE_FORWARDDECLARE( TaskBatch )

		typedef std::vector<TaskBatchPtr> TaskBatches;

		/// Representation of a Task and its requirements.
		class TaskBatch : public IECore::RefCounted
		{
			public :

				TaskBatch();
				TaskBatch( const ExecutableNode::Task &task );
				TaskBatch( const TaskBatch &other );

				IE_CORE_DECLAREMEMBERPTR( TaskBatch );

				void execute() const;

				const ExecutableNode *node() const;
				const Context *context() const;

				std::vector<float> &frames();
				const std::vector<float> &frames() const;

				std::vector<TaskBatchPtr> &requirements();
				const std::vector<TaskBatchPtr> &requirements() const;

				IECore::CompoundData *blindData();
				const IECore::CompoundData *blindData() const;

			private :

				ConstExecutableNodePtr m_node;
				ConstContextPtr m_context;
				IECore::CompoundDataPtr m_blindData;
				std::vector<float> m_frames;
				TaskBatches m_requirements;

		};

		/// Derived classes should implement doDispatch to dispatch the execution of
		/// the given TaskBatches, taking care to respect each set of requirements,
		/// executing required Tasks as well when necessary. Note that it is possible
		/// for an individual TaskBatch to appear multiple times within the graph of
		/// TaskBatches. It is the responsibility of derived classes to track which
		/// batches have been dispatched in order to prevent duplicate work.
		virtual void doDispatch( const TaskBatch *batch ) const = 0;

		//! @name ExecutableNode Customization
		/// Dispatchers are able to create custom plugs on ExecutableNodes when they are constructed.
		/////////////////////////////////////////////////////////////////////////////////////////////
		//@{
		/// Adds the custom plugs from all registered Dispatchers to the given CompoundPlug.
		static void setupPlugs( CompoundPlug *parentPlug );
		/// Called by setupPlugs for each Dispatcher instance. It is recommended that each registered
		/// instance store its plugs contained within a dedicated CompoundPlug, named according to the
		/// registration name. Derived classes must implement doSetupPlugs in a way that gracefully
		/// accepts situations where the plugs already exist (i.e. nodes loaded from a script may
		/// already have the necessary dispatcher plugs). One way to avoid this issue is to always
		/// create non-dynamic plugs. Since setupPlugs is called from the ExecutableNode constructor,
		/// the non-dynamic plugs will always be created according to the current definition, and will
		/// not be serialized into scripts. Note that this suggestion requires the error tolerant script
		/// loading from issue #746. The downside of using non-dynamic plugs is that loading a script
		/// before all Dispatchers have been registered could result in lost settings.
		virtual void doSetupPlugs( CompoundPlug *parentPlug ) const = 0;
		//@}

	private :

		std::string createJobDirectory( const Context *context ) const;
		mutable std::string m_jobDirectory;

		typedef std::map< std::string, DispatcherPtr > DispatcherMap;

		typedef std::map<IECore::MurmurHash, TaskBatchPtr> BatchMap;
		typedef std::map<IECore::MurmurHash, TaskBatchPtr> TaskToBatchMap;

		IECore::FrameListPtr frameRange( const ScriptNode *script, const Context *context ) const;

		// Utility functions that recursively collect all nodes and their execution requirements,
		// arranging them into a graph of TaskBatches. Tasks will be grouped by executionHash,
		// and the requirements will be a union of the requirements from all equivalent Tasks.
		// Tasks with otherwise identical Contexts also be grouped into batches of frames. Nodes
		// which require sequence execution will be grouped together as well.
		static TaskBatchPtr batchTasks( const ExecutableNode::Tasks &tasks );
		static void batchTasksWalk( TaskBatchPtr parent, const ExecutableNode::Task &task, BatchMap &currentBatches, TaskToBatchMap &tasksToBatches );
		static TaskBatchPtr acquireBatch( const ExecutableNode::Task &task, BatchMap &currentBatches, TaskToBatchMap &tasksToBatches );
		static IECore::MurmurHash batchHash( const ExecutableNode::Task &task );

		static size_t g_firstPlugIndex;
		static DispatcherMap g_dispatchers;
		static PreDispatchSignal g_preDispatchSignal;
		static PostDispatchSignal g_postDispatchSignal;

		friend void GafferBindings::bindDispatcher();
};

} // namespace Gaffer

#endif // GAFFER_DISPATCHER_H
