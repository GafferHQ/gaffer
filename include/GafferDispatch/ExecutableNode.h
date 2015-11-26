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

#ifndef GAFFERDISPATCH_EXECUTABLENODE_H
#define GAFFERDISPATCH_EXECUTABLENODE_H

#include "IECore/MurmurHash.h"

#include "Gaffer/Node.h"
#include "Gaffer/Plug.h"

#include "GafferDispatch/TypeIds.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Context )
IE_CORE_FORWARDDECLARE( ArrayPlug )

} // namespace Gaffer

namespace GafferDispatch
{

IE_CORE_FORWARDDECLARE( ExecutableNode )

/// A base class for nodes with external side effects such as the creation of files, rendering, etc.
/// ExecutableNodes can be chained together with other ExecutableNodes to define a required execution
/// order. Typically ExecutableNodes should be executed by Dispatcher classes that can query the
/// required execution order and schedule Tasks appropriately.
class ExecutableNode : public Gaffer::Node
{

	public :

		/// Defines the execution of an ExecutableNode in a specific Context.
		class Task
		{
			public :

				Task( const Task &t );
				/// Constructs a task representing the execution of
				/// node n in context c. A copy of the context is
				/// taken.
				Task( ExecutableNodePtr n, const Gaffer::Context *c );
				/// Returns the node to be executed.
				const ExecutableNode *node() const;
				/// Returns the context to execute the node in.
				const Gaffer::Context *context() const;
				/// A hash uniquely representing the side effects
				/// of the task. This is stored from ExecutableNode::hash()
				/// during construction, so editing the node or upstream
				/// graph will invalidate the hash (and therefore the task).
				const IECore::MurmurHash hash() const;
				bool operator == ( const Task &rhs ) const;
				bool operator < ( const Task &rhs ) const;

			private :

				ConstExecutableNodePtr m_node;
				Gaffer::ConstContextPtr m_context;
				IECore::MurmurHash m_hash;

		};

		typedef std::vector<Task> Tasks;
		typedef std::vector<Gaffer::ConstContextPtr> Contexts;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferDispatch::ExecutableNode, ExecutableNodeTypeId, Gaffer::Node );

		ExecutableNode( const std::string &name=defaultName<ExecutableNode>() );
		virtual ~ExecutableNode();

		/// The plug type used to connect ExecutableNodes
		/// together to define order of execution.
		class TaskPlug : public Gaffer::Plug
		{

			public :

				IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferDispatch::ExecutableNode::TaskPlug, ExecutableNodeTaskPlugTypeId, Gaffer::Plug );

				TaskPlug( const std::string &name=defaultName<TaskPlug>(), Direction direction=In, unsigned flags=Default );

				virtual bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const;
				virtual bool acceptsInput( const Gaffer::Plug *input ) const;
				virtual Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const;

		};

		typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, TaskPlug> > TaskPlugIterator;
		IE_CORE_DECLAREPTR( TaskPlug )

		/// Input plugs to which upstream tasks may be connected to cause them
		/// to be executed before this node.
		Gaffer::ArrayPlug *preTasksPlug();
		const Gaffer::ArrayPlug *preTasksPlug() const;

		/// Input plugs to which tasks may be connected to cause them to be executed
		/// after this node, potentially in parallel with downstream tasks.
		Gaffer::ArrayPlug *postTasksPlug();
		const Gaffer::ArrayPlug *postTasksPlug() const;

		/// Output plug which can be connected to downstream preTasks plugs to cause
		/// this node to be executed before the downstream nodes.
		TaskPlug *taskPlug();
		const TaskPlug *taskPlug() const;

		/// Parent plug used by Dispatchers to expose per-node dispatcher settings.
		/// See the "ExecutableNode Customization" section of the Gaffer::Dispatcher
		/// documentation for more details.
		Gaffer::Plug *dispatcherPlug();
		const Gaffer::Plug *dispatcherPlug() const;

		/// Fills tasks with all Tasks that must be completed before execute
		/// can be called with the given context. The default implementation collects
		/// the upstream Tasks connected into the preTasksPlug().
		/// \todo Remove the context argument and use the current context instead.
		virtual void preTasks( const Gaffer::Context *context, Tasks &tasks ) const;

		/// Fills tasks with Tasks that must be executed following the execution
		/// of this node in the given context. The default implementation collects
		/// the tasks connected into the postTasksPlug().
		/// \todo Remove the context argument and use the current context instead.
		virtual void postTasks( const Gaffer::Context *context, Tasks &tasks ) const;

		/// Returns a hash that uniquely represents the side effects (e.g. files created)
		/// of calling execute with the given context. Derived nodes should call the base
		/// implementation and append to the returned hash. Nodes can indicate that they
		/// don't cause side effects for the given context by returning a default hash.
		/// \todo Remove the context argument and use the current context instead.
		virtual IECore::MurmurHash hash( const Gaffer::Context *context ) const = 0;

		/// Executes this node using the current Context.
		virtual void execute() const = 0;

		/// Executes this node by copying the current Context and varying it over the sequence of frames.
		/// The default implementation modifies the current Context and calls execute() for each frame.
		/// Derived classes which need more specialized behaviour should re-implement executeSequence()
		/// along with requiresSequenceExecution().
		virtual void executeSequence( const std::vector<float> &frames ) const;

		/// Returns true if the node must execute a sequence of frames all at once.
		/// The default implementation returns false.
		virtual bool requiresSequenceExecution() const;

	private :

		static size_t g_firstPlugIndex;

};

} // namespace GafferDispatch

#endif // GAFFERDISPATCH_EXECUTABLENODE_H
