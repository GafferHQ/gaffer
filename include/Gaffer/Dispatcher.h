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
#include "IECore/RunTimeTyped.h"
#include "Gaffer/TypeIds.h"
#include "Gaffer/ExecutableNode.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Dispatcher )
IE_CORE_FORWARDDECLARE( CompoundPlug )

/// Abstract base class which defines an interface for scheduling the execution
/// of Context specific Tasks from ExecutableNodes. Dispatchers can also modify
/// ExecutableNodes during construction, adding plugs which affect Task execution.
class Dispatcher : public Node
{
	public :

		Dispatcher( const std::string &name=defaultName<Dispatcher>() );
		virtual ~Dispatcher();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::Dispatcher, DispatcherTypeId, Node );

		typedef boost::signal<void (const Dispatcher *, const std::vector<ExecutableNodePtr> &)> DispatchSignal;
		
		//! @name Dispatch Signals
		/// These signals are emitted on dispatch events for any registered Dispatcher instance.
		////////////////////////////////////////////////////////////////////////////////////////
		//@{
		/// Called when any dispatcher is about to dispatch nodes.
		static DispatchSignal &preDispatchSignal();
		/// Called after any dispatcher has finished dispatching nodes.
		static DispatchSignal &postDispatchSignal();
		//@}
		
		/// Calls doDispatch, taking care to trigger the dispatch signals at the appropriate times.
		void dispatch( const std::vector<ExecutableNodePtr> &nodes ) const;

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

		/// Derived classes should implement doDispatch to dispatch the execution of the given
		/// ExecutableNodes, taking care to respect each set of ExecutableNode requirements,
		/// executing required Tasks as well when necessary.
		virtual void doDispatch( const std::vector<ExecutableNodePtr> &nodes ) const = 0;
		
		//! @name ExecutableNode Customization
		/// Dispatchers are able to create custom plugs on ExecutableNodes when they are constructed.
		/////////////////////////////////////////////////////////////////////////////////////////////
		//@{
		/// Adds the custom plugs from all registered Dispatchers to the given CompoundPlug.
		static void addAllPlugs( CompoundPlug *dispatcherPlug );
		/// Called by addAllPlugs for each Dispatcher instance. Derived classes must implement
		/// addPlugs in a way that gracefully accepts situations where the plugs already exist.
		/// (i.e. nodes loaded from a script may already have the necessary dispatcher plugs).
		virtual void addPlugs( CompoundPlug *dispatcherPlug ) const = 0;
		//@}
		
		/// Representation of a Task and its requirements.
		struct TaskDescription 
		{
			ExecutableNode::Task task;
			std::set<ExecutableNode::Task> requirements;
		};
		
		typedef std::vector< Dispatcher::TaskDescription > TaskDescriptions;
		
		/// Utility function that recursively collects all nodes and their execution requirements,
		/// flattening them into a list of unique TaskDescriptions. For nodes that return a default
		/// hash, this function will create a separate Task for each unique set of requirements.
		/// For all other nodes, Tasks will be grouped by executionHash, and the requirements will be
		/// a union of the requirements from all equivalent Tasks.
		static void uniqueTasks( const ExecutableNode::Tasks &tasks, TaskDescriptions &uniqueTasks );

	private :

		typedef std::map< std::string, DispatcherPtr > DispatcherMap;
		typedef std::map< IECore::MurmurHash, std::vector< size_t > > TaskSet;
		
		static const ExecutableNode::Task &uniqueTask( const ExecutableNode::Task &task, TaskDescriptions &uniqueTasks, TaskSet &seenTasks );
		
		static DispatcherMap g_dispatchers;
		static DispatchSignal g_preDispatchSignal;
		static DispatchSignal g_postDispatchSignal;
};

} // namespace Gaffer

#endif // GAFFER_DISPATCHER_H
