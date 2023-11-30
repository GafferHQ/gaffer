//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

#pragma once

#include "GafferDispatch/Export.h"
#include "GafferDispatch/TaskNode.h"

#include "Gaffer/NumericPlug.h"
#include "Gaffer/Signals.h"

#include "IECore/CompoundData.h"
#include "IECore/FrameList.h"
#include "IECore/RunTimeTyped.h"
#include "IECore/StringAlgo.h"

#include <filesystem>
#include <functional>
#include <map>
#include <set>
#include <string>
#include <unordered_set>
#include <vector>

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

} // namespace Gaffer

namespace GafferDispatch
{

namespace Detail
{

struct PreDispatchSignalCombiner
{
	using result_type = bool;

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

IE_CORE_FORWARDDECLARE( Dispatcher )

/// Abstract base class which defines an interface for scheduling the execution
/// of Context specific Tasks from TaskNodes which exist within a ScriptNode.
/// Dispatchers can also modify TaskNodes during construction, adding
/// plugs which affect Task execution.
class GAFFERDISPATCH_API Dispatcher : public Gaffer::Node
{
	public :

		explicit Dispatcher( const std::string &name=defaultName<Dispatcher>() );
		~Dispatcher() override;

		GAFFER_NODE_DECLARE_TYPE( GafferDispatch::Dispatcher, DispatcherTypeId, Gaffer::Node );

		using PreDispatchSignal = Gaffer::Signals::Signal<bool ( const Dispatcher *, const std::vector<TaskNodePtr> & ), Detail::PreDispatchSignalCombiner>;
		using DispatchSignal = Gaffer::Signals::Signal<void ( const Dispatcher *, const std::vector<TaskNodePtr> & ), Gaffer::Signals::CatchingCombiner<void>>;
		using PostDispatchSignal = Gaffer::Signals::Signal<void ( const Dispatcher *, const std::vector<TaskNodePtr> &, bool ), Gaffer::Signals::CatchingCombiner<void>>;
		//! @name Dispatch Signals
		/// These signals are emitted on dispatch events for any registered Dispatcher instance.
		////////////////////////////////////////////////////////////////////////////////////////
		//@{
		/// Called when any dispatcher might begin to dispatch nodes. Slots should have the
		/// signature `bool slot( dispatcher, nodes )`, and may return True to cancel
		/// the dispatch, or False to allow it to continue.
		static PreDispatchSignal &preDispatchSignal();
		/// Called when any dispatcher is going to dispatch nodes. Slots should have the
		/// signature `bool slot( dispatcher, nodes )`. This differs from the preDispatchSignal
		/// in that it is triggered when dispatching is imminent and non-cancellable.
		static DispatchSignal &dispatchSignal();
		/// Called after any dispatcher has finished dispatching nodes, or after a pending dispatch
		/// has been cancelled by the preDispatchSignal slots. Slots should have the signature
		/// `void slot( dispatcher, nodes, bool )`. The third argument will be True if the process
		/// was successful, and False otherwise.
		static PostDispatchSignal &postDispatchSignal();
		//@}

		/// Calls doDispatch, taking care to trigger the dispatch signals at the appropriate times.
		/// Note that this will throw unless all of the nodes are either TaskNodes or Boxes,
		/// and it will also throw if cycles are detected in the resulting TaskBatch graph.
		/// \todo Replace this with a version taking vector<TaskPlugPtr>. This will plug the
		/// type safety issue whereby currently any old node can be passed to dispatch.
		/// Alternatively, perhaps the tasks to dispatch should be specified via connections
		/// into a "tasks" ArrayPlug, so dispatchers can optionally live directly in the node
		/// graph.
		void dispatch( const std::vector<Gaffer::NodePtr> &nodes ) const;

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
		Gaffer::IntPlug *framesModePlug();
		const Gaffer::IntPlug *framesModePlug() const;
		/// Returns frame range to be used when framesModePlug is set to CustomRange.
		Gaffer::StringPlug *frameRangePlug();
		const Gaffer::StringPlug *frameRangePlug() const;
		/// Returns the FrameList that will be used during dispatch() to create the TaskBatches.
		/// Derived classes which reimplement this must call the base class first.
		virtual IECore::FrameListPtr frameRange( const Gaffer::ScriptNode *script, const Gaffer::Context *context ) const;
		//@}

		//! @name Dispatcher Jobs
		/// Utility functions which derived classes may use when dispatching jobs.
		//////////////////////////////////////////////////////////////////////////
		//@{
		/// Returns the name of the next job to dispatch.
		Gaffer::StringPlug *jobNamePlug();
		const Gaffer::StringPlug *jobNamePlug() const;
		/// Returns the plug which specifies the directory used by dispatchers to store temporary
		/// files on a per-job basis.
		Gaffer::StringPlug *jobsDirectoryPlug();
		const Gaffer::StringPlug *jobsDirectoryPlug() const;
		/// At the start of dispatch(), a directory is created under `jobsDirectoryPlug / jobNamePlug`
		/// which the dispatcher writes temporary files to. This method returns the most recent created directory.
		const std::filesystem::path jobDirectory() const;
		//@}

		/// A function which creates a Dispatcher.
		using Creator = std::function<DispatcherPtr ()>;
		/// SetupPlugsFn may be registered along with a Dispatcher Creator. It will be called by setupPlugs,
		/// along with all other registered SetupPlugsFns. It is recommended that each registered dispatcher
		/// store its plugs contained within a dedicated parent Plug, named according to the registration
		/// type. The SetupPlugsFn must be implemented in a way that gracefully accepts situations where the
		/// plugs already exist (i.e. nodes loaded from a script may already have the necessary dispatcher plugs).
		/// One way to avoid this issue is to always create non-dynamic plugs. Since setupPlugs is called from
		/// the TaskNode constructor, the non-dynamic plugs will always be created according to the current
		/// definition, and will not be serialized into scripts. The downside of using non-dynamic plugs is that
		/// loading a script before all Dispatchers have been registered could result in lost settings.
		using SetupPlugsFn = std::function<void (Gaffer::Plug *)>;

		//! @name Registration
		/// Utility functions for registering and retrieving Dispatchers.
		/////////////////////////////////////////////////////////////////
		//@{
		/// Create a registered Dispatcher of the specified type.
		static DispatcherPtr create( const std::string &dispatcherType );
		static const std::string &getDefaultDispatcherType();
		static void setDefaultDispatcherType( const std::string &dispatcherType );
		/// Register a Dispatcher creation function.
		static void registerDispatcher( const std::string &dispatcherType, Creator creator, SetupPlugsFn setupPlugsFn = nullptr );
		/// Fills the vector with the names of all the registered Dispatcher creators.
		static void registeredDispatchers( std::vector<std::string> &dispatcherTypes );
		/// Removes a dispatcher from the registry
		static void deregisterDispatcher( const std::string &dispatcherType );
		//@}

	protected :

		friend class TaskNode;

		IE_CORE_FORWARDDECLARE( TaskBatch )

		using TaskBatches = std::vector<TaskBatchPtr>;

		/// A batch of tasks to be executed together, along
		/// with references to batches of preTasks which must
		/// be executed first. This DAG is the primary
		/// data structure used in the dispatch process.
		///
		/// All tasks within a batch are from the same plug
		/// and have identical contexts except for the frame
		/// number.
		class GAFFERDISPATCH_API TaskBatch : public IECore::RefCounted
		{
			public :

				TaskBatch();
				TaskBatch( TaskNode::ConstTaskPlugPtr plug, Gaffer::ConstContextPtr context );
				/// \deprecated
				TaskBatch( ConstTaskNodePtr node, Gaffer::ConstContextPtr context );

				IE_CORE_DECLAREMEMBERPTR( TaskBatch );

				void execute() const;

				const TaskNode::TaskPlug *plug() const;
				/// \deprecated.
				const TaskNode *node() const;
				const Gaffer::Context *context() const;

				const std::vector<float> &frames() const;
				const TaskBatches &preTasks() const;

				IECore::CompoundData *blindData();
				const IECore::CompoundData *blindData() const;

			private :

				friend class Dispatcher;

				TaskNode::ConstTaskPlugPtr m_plug;
				Gaffer::ContextPtr m_context;
				IECore::CompoundDataPtr m_blindData;
				std::vector<float> m_frames;
				// We want to store pretasks in the order we discover them,
				// so our primary storage is a vector.
				TaskBatches m_preTasks;
				// But we also need to perform quick membership
				// queries, for which we use a secondary set.
				std::unordered_set<const TaskBatch *> m_preTasksSet;

		};

		/// Must be implemented by derived classes to execute the DAG of task batches,
		/// taking care that all Batch::preTasks() are executed before the batch itself.
		/// Note that it is possible for an individual TaskBatch to appear multiple
		/// times within the graph. It is the responsibility of derived classes to track which
		/// batches have been dispatched in order to prevent duplicate work.
		virtual void doDispatch( const TaskBatch *batch ) const = 0;

		//! @name TaskNode Customization
		/// Dispatchers are able to create custom plugs on TaskNodes when they are constructed.
		/////////////////////////////////////////////////////////////////////////////////////////////
		//@{
		/// Adds the custom plugs from all registered Dispatchers to the given parent Plug.
		static void setupPlugs( Gaffer::Plug *parentPlug );
		//@}

	private :

		void createJobDirectory( const Gaffer::ScriptNode *script, Gaffer::Context *context ) const;
		mutable std::filesystem::path m_jobDirectory;

		void executeAndPruneImmediateBatches( TaskBatch *batch, bool immediate = false ) const;

		using CreatorMap = std::map<std::string, std::pair<Creator, SetupPlugsFn>>;
		static CreatorMap &creators();

		class Batcher;

		static size_t g_firstPlugIndex;
		static PreDispatchSignal g_preDispatchSignal;
		static DispatchSignal g_dispatchSignal;
		static PostDispatchSignal g_postDispatchSignal;
		static std::string g_defaultDispatcherType;

};

} // namespace GafferDispatch
