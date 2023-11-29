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

#include "GafferDispatch/Dispatcher.h"

#include "Gaffer/Context.h"
#include "Gaffer/ContextProcessor.h"
#include "Gaffer/Process.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/SubGraph.h"
#include "Gaffer/Switch.h"

#include "IECore/FrameRange.h"
#include "IECore/MessageHandler.h"

#include "boost/algorithm/string/predicate.hpp"

#include "fmt/format.h"

#include <unordered_map>

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferDispatch;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

/// \todo Consider moving this to PlugAlgo and using it in
/// `Shader::NetworkBuilder::effectiveParameter()`.
tuple<const Plug *, ConstContextPtr> computedSource( const Plug *plug )
{
	plug = plug->source();

	if( auto sw = runTimeCast<const Switch>( plug->node() ) )
	{
		if(
			sw->outPlug() &&
			( plug == sw->outPlug() || sw->outPlug()->isAncestorOf( plug ) )
		)
		{
			if( auto activeInPlug = sw->activeInPlug( plug ) )
			{
				return computedSource( activeInPlug );
			}
		}
	}
	else if( auto contextProcessor = runTimeCast<const ContextProcessor>( plug->node() ) )
	{
		if(
			contextProcessor->outPlug() &&
			( plug == contextProcessor->outPlug() || contextProcessor->outPlug()->isAncestorOf( plug ) )
		)
		{
			ConstContextPtr context = contextProcessor->inPlugContext();
			Context::Scope scopedContext( context.get() );
			return computedSource( contextProcessor->inPlug() );
		}
	}

	return make_tuple( plug, Context::current() );
}

const InternedString g_frame( "frame" );

// TaskBatch contexts are identical to the contexts of their corresponding
// Tasks, except that they omit the `frame` variable. We need to construct a
// _lot_ of them during dispatch, and many TaskBatches have identical contexts.
// So we use BatchContextPool to eliminate the copying overhead by constructing
// only a single instance of each unique context.
struct BatchContextPool
{

	ConstContextPtr acquireUnique( const Context *taskContext )
	{
		// Get the hash of the `taskContext`, but omitting the frame value.
		// The "sum of variable hashes" approach mirrors what `Context::hash()`
		// does itself, and means that `ui:` prefixed variables have no effect.
		m_names.clear();
		taskContext->names( m_names );
		uint64_t sumH1 = 0, sumH2 = 0;
		for( const auto &name : m_names )
		{
			if( name == g_frame )
			{
				continue;
			}
			const MurmurHash vh = taskContext->variableHash( name );
			sumH1 += vh.h1();
			sumH2 += vh.h2();
		}

		auto [it, inserted] = m_contexts.insert( { MurmurHash( sumH1, sumH2 ), nullptr } );
		if( inserted )
		{
			ContextPtr batchContext = new Context( *taskContext );
			batchContext->remove( g_frame );
			it->second = batchContext;
		}

		return it->second;
	}

	private :

		std::unordered_map<IECore::MurmurHash, ConstContextPtr> m_contexts;
		// Scratch space to avoid allocations every time we query names.
		std::vector<InternedString> m_names;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Dispatcher
//////////////////////////////////////////////////////////////////////////

namespace
{

const InternedString g_batchSize( "batchSize" );
const InternedString g_immediatePlugName( "immediate" );
const InternedString g_jobDirectoryContextEntry( "dispatcher:jobDirectory" );
const InternedString g_scriptFileNameContextEntry( "dispatcher:scriptFileName" );

} // namespace

size_t Dispatcher::g_firstPlugIndex = 0;
Dispatcher::PreDispatchSignal Dispatcher::g_preDispatchSignal;
Dispatcher::DispatchSignal Dispatcher::g_dispatchSignal;
Dispatcher::PostDispatchSignal Dispatcher::g_postDispatchSignal;
std::string Dispatcher::g_defaultDispatcherType = "";

GAFFER_NODE_DEFINE_TYPE( Dispatcher )

Dispatcher::Dispatcher( const std::string &name )
	: TaskNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ArrayPlug( "tasks", Plug::In, new TaskPlug( "task0" ) ) );
	addChild( new IntPlug( "framesMode", Plug::In, CurrentFrame, CurrentFrame ) );
	addChild( new StringPlug( "frameRange", Plug::In, "1-100x10" ) );
	addChild( new StringPlug( "jobName", Plug::In, "" ) );
	addChild( new StringPlug( "jobsDirectory", Plug::In, "" ) );
}

Dispatcher::~Dispatcher()
{
}

Gaffer::ArrayPlug *Dispatcher::tasksPlug()
{
	return getChild<ArrayPlug>( g_firstPlugIndex );
}

const Gaffer::ArrayPlug *Dispatcher::tasksPlug() const
{
	return getChild<ArrayPlug>( g_firstPlugIndex );
}

IntPlug *Dispatcher::framesModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const IntPlug *Dispatcher::framesModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

StringPlug *Dispatcher::frameRangePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const StringPlug *Dispatcher::frameRangePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

StringPlug *Dispatcher::jobNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const StringPlug *Dispatcher::jobNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

StringPlug *Dispatcher::jobsDirectoryPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const StringPlug *Dispatcher::jobsDirectoryPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const std::filesystem::path Dispatcher::jobDirectory() const
{
	return m_jobDirectory;
}

void Dispatcher::createJobDirectory( const Gaffer::ScriptNode *script, Gaffer::Context *context ) const
{
	std::filesystem::path jobDirectory( jobsDirectoryPlug()->getValue() );
	std::string jobName = jobNamePlug()->getValue();
	if( !jobName.empty() )
	{
		jobDirectory /= jobName;
	}

	const std::filesystem::path outerJobDirectory( context->get<string>( g_jobDirectoryContextEntry, "" ) );
	if( !outerJobDirectory.empty() )
	{
		// We're nested inside another dispatch process. Reuse the job directory if we can.
		if( jobDirectory.empty() || jobDirectory == outerJobDirectory.parent_path() )
		{
			m_jobDirectory = outerJobDirectory;
			return;
		}
	}

	if( jobDirectory.empty() )
	{
		/// \todo I think it would be better to throw here, rather than
		/// litter the current directory.
		jobDirectory = std::filesystem::current_path();
	}

	std::filesystem::create_directories( jobDirectory );

	// To distinguish between multiple jobs with the same settings
	// we use a unique numeric subdirectory per job. Start by finding
	// the highest existing numbered directory entry. Doing this with
	// a directory iterator is much quicker than calling `is_directory()`
	// in a loop.

	long i = -1;
	for( const auto &d : std::filesystem::directory_iterator( jobDirectory ) )
	{
		i = std::max( i, strtol( d.path().filename().string().c_str(), nullptr, 10 ) );
	}

	// Now create the next directory. We do this in a loop until we
	// successfully create a directory of our own, because we
	// may be in a race against other processes.

	std::filesystem::path numberedJobDirectory;
	while( true )
	{
		++i;
		numberedJobDirectory = jobDirectory / fmt::format( "{:06}", i );
		if( std::filesystem::create_directory( numberedJobDirectory ) )
		{
			break;
		}
	}

	m_jobDirectory = numberedJobDirectory;
	context->set( g_jobDirectoryContextEntry, m_jobDirectory.generic_string() );

	// Now figure out where we'll save the script in that directory, and
	// advertise it via the context. We'll do the actual saving later.

	std::filesystem::path scriptFileName = script->fileNamePlug()->getValue();
	if( !scriptFileName.empty() )
	{
		scriptFileName = numberedJobDirectory / scriptFileName.filename();
	}
	else
	{
		scriptFileName = numberedJobDirectory / "untitled.gfr";
	}

	context->set( g_scriptFileNameContextEntry, scriptFileName.generic_string() );
}

// Static functions
// ================

Dispatcher::PreDispatchSignal &Dispatcher::preDispatchSignal()
{
	return g_preDispatchSignal;
}

Dispatcher::DispatchSignal &Dispatcher::dispatchSignal()
{
	return g_dispatchSignal;
}

Dispatcher::PostDispatchSignal &Dispatcher::postDispatchSignal()
{
	return g_postDispatchSignal;
}

void Dispatcher::setupPlugs( Plug *parentPlug )
{
	parentPlug->addChild( new IntPlug( g_batchSize, Plug::In, 1 ) );
	parentPlug->addChild( new BoolPlug( g_immediatePlugName, Plug::In, false ) );

	const CreatorMap &m = creators();
	for( const auto &[name, creator] : m )
	{
		if( creator.second )
		{
			creator.second( parentPlug );
		}
	}
}

FrameListPtr Dispatcher::frameRange( const ScriptNode *script, const Context *context ) const
{
	FramesMode mode = (FramesMode)framesModePlug()->getValue();
	if ( mode == CurrentFrame )
	{
		FrameList::Frame frame = (FrameList::Frame)context->getFrame();
		return new FrameRange( frame, frame );
	}
	else if ( mode == FullRange )
	{
		return new FrameRange( script->frameStartPlug()->getValue(), script->frameEndPlug()->getValue() );
	}

	// must be CustomRange

	try
	{
		return FrameList::parse( context->substitute( frameRangePlug()->getValue() ) );
	}
	catch ( IECore::Exception & )
	{
		throw IECore::Exception( "Dispatcher: Custom Frame Range is not a valid IECore::FrameList" );
	}
}

//////////////////////////////////////////////////////////////////////////
// TaskBatch implementation
//////////////////////////////////////////////////////////////////////////

Dispatcher::TaskBatch::TaskBatch()
	:	TaskBatch( nullptr, nullptr )
{
}

Dispatcher::TaskBatch::TaskBatch( TaskNode::ConstTaskPlugPtr plug, Gaffer::ConstContextPtr context )
	:	m_plug( plug ), m_context( context ), m_blindData( new CompoundData ),
		m_size( 0 ), m_postTaskIndex( 0 ), m_immediate( false ), m_visited( false ), m_executed( false )
{
}

void Dispatcher::TaskBatch::execute() const
{
	if ( m_frames.empty() )
	{
		return;
	}

	Context::Scope scopedContext( m_context.get() );
	m_plug->executeSequence( m_frames );
}

const TaskNode::TaskPlug *Dispatcher::TaskBatch::plug() const
{
	return m_plug.get();
}

const TaskNode *Dispatcher::TaskBatch::node() const
{
	return m_plug ? runTimeCast<const TaskNode>( m_plug->node() ) : nullptr;
}

const Context *Dispatcher::TaskBatch::context() const
{
	return m_context.get();
}

const std::vector<float> &Dispatcher::TaskBatch::frames() const
{
	return m_frames;
}

const std::vector<Dispatcher::TaskBatchPtr> &Dispatcher::TaskBatch::preTasks() const
{
	return m_preTasks;
}

CompoundData *Dispatcher::TaskBatch::blindData()
{
	return m_blindData.get();
}

const CompoundData *Dispatcher::TaskBatch::blindData() const
{
	return m_blindData.get();
}

//////////////////////////////////////////////////////////////////////////
// Batcher class. This is an internal utility class for constructing
// the DAG of TaskBatches to be dispatched. It is a separate class so
// that it can track the necessary temporary state as member data.
//////////////////////////////////////////////////////////////////////////

class Dispatcher::Batcher
{

	public :

		Batcher()
			:	m_rootBatch( new TaskBatch() )
		{
		}

		void addTask( const TaskNode::Task &task )
		{
			if( auto batch = batchTasksWalk( task ) )
			{
				addPreTask( m_rootBatch.get(), batch );
			}
		}

		TaskBatch *rootBatch()
		{
			return m_rootBatch.get();
		}

		// Returns a hash representing all the tasks that will be
		// executed, but _not_ the dependencies between them. This
		// is used by `Dispatcher::hash()`.
		IECore::MurmurHash hash() const
		{
			IECore::MurmurHash h;
			for( const auto &[taskHash, taskBatch] : m_tasksToBatches )
			{
				// `unordered_map` doesn't guarantee deterministic order, so
				// we use the "sum of hashes" trick to get a stable hash.
				h = MurmurHash( h.h1() + taskHash.h1(), h.h2() + taskHash.h2() );
			}
			return h;
		}

	private :

		TaskBatchPtr batchTasksWalk( TaskNode::Task task, const std::set<const TaskBatch *> &ancestors = std::set<const TaskBatch *>() )
		{
			// Find source task, taking into account
			// Switches and ContextProcessors.
			{
				Context::Scope scopedTaskContext( task.context() );
				auto [sourcePlug, sourceContext] = computedSource( task.plug() );
				if( auto sourceTaskPlug = runTimeCast<const TaskNode::TaskPlug>( sourcePlug ) )
				{
					task = TaskNode::Task( sourceTaskPlug, sourceContext ? sourceContext.get() : task.context() );
				}
				else
				{
					return nullptr;
				}
			}

			if( task.plug()->direction() != Plug::Out )
			{
				return nullptr;
			}

			// Acquire a batch with this task placed in it,
			// and check that we haven't discovered a cyclic
			// dependency.
			TaskBatchPtr batch = acquireBatch( task );
			if( ancestors.find( batch.get() ) != ancestors.end() )
			{
				throw IECore::Exception( fmt::format(
					"Dispatched tasks cannot have cyclic dependencies but {} is involved in a cycle.",
					batch->plug()->relativeName( batch->plug()->ancestor<ScriptNode>() )
				) );
			}

			// Ask the task what preTasks and postTasks it would like.
			TaskNode::Tasks preTasks;
			TaskNode::Tasks postTasks;
			{
				Context::Scope scopedTaskContext( task.context() );
				task.plug()->preTasks( preTasks );
				task.plug()->postTasks( postTasks );
			}

			// Collect all the batches the postTasks belong in.
			// We grab these first because they need to be included
			// in the ancestors for cycle detection when getting
			// the preTask batches.
			TaskBatches postBatches;
			for( const auto &postTask : postTasks )
			{
				if( auto postBatch = batchTasksWalk( postTask ) )
				{
					postBatches.push_back( postBatch );
				}
			}

			// Collect all the batches the preTasks belong in,
			// and add them as preTasks for our batch.

			std::set<const TaskBatch *> preTaskAncestors( ancestors );
			preTaskAncestors.insert( batch.get() );
			for( const auto &postBatch : postBatches )
			{
				preTaskAncestors.insert( postBatch.get() );
			}

			for( const auto &preTask : preTasks )
			{
				if( auto preBatch = batchTasksWalk( preTask, preTaskAncestors ) )
				{
					addPreTask( batch.get(), preBatch );
				}
			}

			// As far as TaskBatch and doDispatch() are concerned, there
			// is no such thing as a postTask, so we emulate them by making
			// this batch a preTask of each of the postTask batches. We also
			// add the postTask batches as preTasks for the root, so that they
			// are reachable from doDispatch().
			for( const auto &postBatch : postBatches )
			{
				addPreTask( postBatch.get(), batch, /* forPostTask =  */ true );
				addPreTask( m_rootBatch.get(), postBatch );
			}

			return batch;
		}

		TaskBatchPtr acquireBatch( const TaskNode::Task &task )
		{
			// Several plugs will be evaluated that may vary by context,
			// so we need to be in the correct context for this task
			// \todo should we be removing `frame` from the context?
			Context::Scope scopedTaskContext( task.context() );

			// See if we've previously visited this task, and therefore
			// have placed it in a batch already, which we can return
			// unchanged. The `taskHash` is used as the unique identity of
			// the task.
			MurmurHash taskHash = task.plug()->hash();
			const bool taskIsNoOp = taskHash == IECore::MurmurHash();
			if( taskIsNoOp )
			{
				// Prevent no-ops from coalescing into a single batch, as this
				// would break parallelism - see `DispatcherTest.testNoOpDoesntBreakFrameParallelism()`
				taskHash.append( task.context()->hash() );
			}
			// Prevent identical tasks from different nodes from being
			// coalesced.
			taskHash.append( (uint64_t)task.plug() );

			TaskBatchPtr &batchForTask = m_tasksToBatches[taskHash];
			if( batchForTask )
			{
				return batchForTask;
			}

			// We haven't seen this task before, so we need to find
			// an appropriate batch to put it in. This may be one of
			// our current batches, or we may need to make a new one
			// entirely if the current batch is full.

			const bool requiresSequenceExecution = task.plug()->requiresSequenceExecution();

			ConstContextPtr batchContext = m_batchContextPool.acquireUnique( task.context() );
			MurmurHash batchMapHash = batchContext->hash();
			batchMapHash.append( (uint64_t)task.plug() );

			TaskBatchPtr &batch = m_currentBatches[batchMapHash];
			if( batch && !requiresSequenceExecution )
			{
				const IntPlug *batchSizePlug = dispatcherPlug( task )->getChild<const IntPlug>( g_batchSize );
				const int batchSizeLimit = ( batchSizePlug ) ? batchSizePlug->getValue() : 1;
				if( batch->m_size >= (size_t)batchSizeLimit )
				{
					// The current batch is full, so we'll need to make a new one.
					batch = nullptr;
				}
			}

			if( !batch )
			{
				batch = new TaskBatch( task.plug(), batchContext );
			}

			// Now we have an appropriate batch, update it to include
			// the frame for our task, and any other relevant information.

			if( !taskIsNoOp )
			{
				float frame = task.context()->getFrame();
				std::vector<float> &frames = batch->m_frames;
				if( requiresSequenceExecution )
				{
					frames.insert( std::lower_bound( frames.begin(), frames.end(), frame ), frame );
				}
				else
				{
					frames.push_back( frame );
				}
			}

			batch->m_size++;

			const BoolPlug *immediatePlug = dispatcherPlug( task )->getChild<const BoolPlug>( g_immediatePlugName );
			if( immediatePlug && immediatePlug->getValue() )
			{
				batch->m_immediate = true;
			}

			// Remember which batch we stored this task in, for
			// the next time someone asks for it.
			batchForTask = batch;

			return batch;
		}

		void addPreTask( TaskBatch *batch, TaskBatchPtr preTask, bool forPostTask = false )
		{
			// Check that `preTask` isn't already in `batch->m_preTasks`,
			// returning if it is.

			const size_t setThreshold = 1000;
			TaskBatches &preTasks = batch->m_preTasks;
			if( preTasks.size() < setThreshold )
			{
				// Linear search is cheaper than set lookups for smallish
				// numbers of preTasks.
				if( std::find( preTasks.begin(), preTasks.end(), preTask ) != preTasks.end() )
				{
					return;
				}
			}
			else
			{
				// But for large numbers of preTasks we switch to testing
				// a set for membership for improved performance.
				if( batch->m_preTasksSet.empty() )
				{
					for( const auto &p : preTasks )
					{
						batch->m_preTasksSet.insert( p.get() );
					}
				}
				if( !batch->m_preTasksSet.insert( preTask.get() ).second )
				{
					return;
				}
			}

			// Add to preTasks.

			if( forPostTask )
			{
				// We're adding the preTask because the batch is a postTask
				// of it, but the batch may already have it's own standard
				// preTasks. There's no strict requirement that we separate
				// out these two types of preTasks (indeed a good dispatcher might
				// execute them in parallel), but for simple dispatchers
				// it's more intuitive to users if we separate them so the
				// standard preTasks come second.
				//
				// See `DispatcherTest.testPostTaskWithPreTasks()` for an
				// example.
				preTasks.insert( preTasks.begin() + batch->m_postTaskIndex, preTask );
				batch->m_postTaskIndex++;
			}
			else
			{
				preTasks.push_back( preTask );
			}
		}

		const Gaffer::Plug *dispatcherPlug( const TaskNode::Task &task )
		{
			return static_cast<const TaskNode *>( task.plug()->node() )->dispatcherPlug();
		}

		using BatchMap = std::unordered_map<IECore::MurmurHash, TaskBatchPtr>;
		using TaskToBatchMap = std::unordered_map<IECore::MurmurHash, TaskBatchPtr>;

		TaskBatchPtr m_rootBatch;
		BatchMap m_currentBatches;
		TaskToBatchMap m_tasksToBatches;
		BatchContextPool m_batchContextPool;

};

//////////////////////////////////////////////////////////////////////////
// Dispatcher TaskNode implementation
//////////////////////////////////////////////////////////////////////////

namespace
{

/// Guard class for calling a dispatcher's preDispatchSignal(), then guaranteeing postDispatchSignal() gets called
class DispatcherSignalGuard
{

	public:

		DispatcherSignalGuard( const Dispatcher* d, const std::vector<TaskNodePtr> &taskNodes ) : m_dispatchSuccessful( false ), m_taskNodes( taskNodes ), m_dispatcher( d )
		{
			m_cancelledByPreDispatch = Dispatcher::preDispatchSignal()( m_dispatcher, m_taskNodes );
		}

		~DispatcherSignalGuard()
		{
			Dispatcher::postDispatchSignal()( m_dispatcher, m_taskNodes, (m_dispatchSuccessful && ( !m_cancelledByPreDispatch )) );
		}

		bool cancelledByPreDispatch( )
		{
			return m_cancelledByPreDispatch;
		}

		void success()
		{
			m_dispatchSuccessful = true;
		}

	private:

		bool m_cancelledByPreDispatch;
		bool m_dispatchSuccessful;

		const std::vector<TaskNodePtr> &m_taskNodes;
		const Dispatcher* m_dispatcher;

};

} // namespace

void Dispatcher::preTasks( const Gaffer::Context *context, Tasks &tasks ) const
{
	vector<int64_t> frames;
	frameRange( scriptNode(), context )->asList( frames );

	tasks.reserve( frames.size() * preTasksPlug()->children().size() );
	for( auto frame : frames )
	{
		ContextPtr frameContext = new Context( *context );
		frameContext->setFrame( frame );
		for( const auto &p : TaskPlug::Range( *preTasksPlug() ) )
		{
			tasks.emplace_back( p, frameContext.get() );
		}
	}
}

void Dispatcher::postTasks( const Gaffer::Context *context, Tasks &tasks ) const
{
	vector<int64_t> frames;
	frameRange()->asList( frames );

	tasks.reserve( frames.size() * postTasksPlug()->children().size() );
	for( auto frame : frames )
	{
		ContextPtr frameContext = new Context( *context );
		frameContext->setFrame( frame );
		for( const auto &p : TaskPlug::Range( *postTasksPlug() ) )
		{
			tasks.emplace_back( p, frameContext.get() );
		}
	}
}

IECore::MurmurHash Dispatcher::hash( const Gaffer::Context *context ) const
{
	MurmurHash h = TaskNode::hash( context );

	std::vector<int64_t> frames;
	frameRange( scriptNode(), context )->asList( frames );

	Context::EditableScope jobContext( context );

	Batcher batcher;
	for( auto frame : frames )
	{
		jobContext.setFrame( frame );
		for( auto &task : TaskNode::TaskPlug::Range( *tasksPlug() ) )
		{
			batcher.addTask( TaskNode::Task( task, Context::current() ) );
		}
	}

	h.append( batcher.hash() );

	return h;
}

void Dispatcher::execute() const
{
	// clear job directory, so that if our node validation fails,
	// jobDirectory() won't return the result from the previous dispatch.
	m_jobDirectory = "";

	// Validate the tasks to be dispatched

	std::vector<TaskNodePtr> taskNodes;

	const ScriptNode *script = scriptNode();
	for( const auto &taskPlug : TaskPlug::Range( *tasksPlug() ) )
	{
		if( !taskPlug->getInput() )
		{
			continue;
		}

		if( const ScriptNode *s = taskPlug->source()->ancestor<ScriptNode>() )
		{
			if( script && s != script )
			{
				throw IECore::Exception( fmt::format( "{} does not belong to ScriptNode {}.", taskPlug->fullName(), script->fullName() ) );
			}
			script = s;
		}
		else
		{
			throw IECore::Exception( fmt::format( "{} does not belong to a ScriptNode.", taskPlug->fullName() ) );
		}

		if( TaskNode *taskNode = runTimeCast<TaskNode>( taskPlug->source()->node() ) )
		{
			taskNodes.push_back( taskNode );
		}
		else
		{
			throw IECore::Exception( fmt::format( "{} does not belong to a TaskNode.", taskPlug->fullName() ) );
		}
	}

	if( taskNodes.empty() )
	{
		return;
	}

	// create the job directory now, so it's available in preDispatchSignal().
	/// \todo: move directory creation between preDispatchSignal() and dispatchSignal() - a cancelled
	/// dispatch should not create anything on disk.

	ContextPtr jobContext = new Context( *Context::current() );
	Context::Scope jobScope( jobContext.get() );
	createJobDirectory( script, jobContext.get() );

	// this object calls this->preDispatchSignal() in its constructor and this->postDispatchSignal()
	// in its destructor, thereby guaranteeing that we always call this->postDispatchSignal().

	DispatcherSignalGuard signalGuard( this, taskNodes );
	if ( signalGuard.cancelledByPreDispatch() )
	{
		return;
	}

	dispatchSignal()( this, taskNodes );

	std::vector<FrameList::Frame> frames;
	FrameListPtr frameList = frameRange( script, Context::current() );
	frameList->asList( frames );

	Batcher batcher;
	for( const auto &frame : frames )
	{
		for( const auto &taskNode : taskNodes )
		{
			jobContext->setFrame( frame );
			batcher.addTask( TaskNode::Task( taskNode->taskPlug(), Context::current() ) );
		}
	}

	executeAndPruneImmediateBatches( batcher.rootBatch() );

	// Save the script. If we're in a nested dispatch, this may have been done already by
	// the outer dispatch, hence the call to `exists()`. Performing the saving here is
	// unsatisfactory for a couple of reasons :
	//
	// - It is _after_ the execution of immediate tasks because currently at Image Engine, some immediate tasks
	//   modify the node graph and expect those modifications to be saved in the script. This is definitely
	//   not kosher - `TaskNode::execute()` is `const` for a reason, and TaskNodes should never modify the graph.
	//   Among other things, such rogue nodes preclude us from being able to multithread dispatch in the future.
	//   Nevertheless, we need to continue to support this for now.
	// - Some dispatchers don't need the script to be saved at all, or even need a job directory (a LocalDispatcher
	//   in foreground mode for instance). We would prefer not to litter the filesystem in these cases.
	//
	// One solution may be to defer the creation of the job directory and the script until it is
	// first required, either by `doDispatch()` or a TaskNode. We'd do this by creating the
	// "dispatcher:jobDirectory" and "dispatcher:scriptFileName" context variables upfront as normal,
	// but not actually updating the filesystem until a call to a utility method is made. The main issue
	// to resolve there is the generation of a unique directory name without actually creating the
	// directory. We could use some sort of UUID for this, but there is some concern that this will be less
	// useable/friendly than the existing sequential naming.
	const std::string scriptFileName = jobContext->get<string>( g_scriptFileNameContextEntry );
	if( !std::filesystem::exists( scriptFileName ) )
	{
		script->serialiseToFile( scriptFileName );
	}

	if( !batcher.rootBatch()->preTasks().empty() )
	{
		doDispatch( batcher.rootBatch() );
	}

	// inform the guard that the process has been completed, so it can pass this info to
	// postDispatchSignal():

	signalGuard.success();
}

void Dispatcher::executeAndPruneImmediateBatches( TaskBatch *batch, bool immediate ) const
{
	if( batch->m_visited )
	{
		return;
	}

	immediate = immediate || batch->m_immediate;

	TaskBatches &preTasks = batch->m_preTasks;
	for( TaskBatches::iterator it = preTasks.begin(); it != preTasks.end(); )
	{
		executeAndPruneImmediateBatches( it->get(), immediate );
		if( (*it)->m_executed )
		{
			batch->m_preTasksSet.erase( it->get() );
			it = preTasks.erase( it );
		}
		else
		{
			++it;
		}
	}

	if( immediate )
	{
		batch->execute();
		batch->m_executed = true;
	}

	batch->m_visited = true;
}

//////////////////////////////////////////////////////////////////////////
// Registration
//////////////////////////////////////////////////////////////////////////

DispatcherPtr Dispatcher::create( const std::string &dispatcherType )
{
	const CreatorMap &m = creators();
	CreatorMap::const_iterator it = m.find( dispatcherType );
	if( it == m.end() )
	{
		return nullptr;
	}

	return it->second.first();
}

const std::string &Dispatcher::getDefaultDispatcherType()
{
	return g_defaultDispatcherType;
}

void Dispatcher::setDefaultDispatcherType( const std::string &dispatcherType )
{
	g_defaultDispatcherType = dispatcherType;
}

void Dispatcher::registerDispatcher( const std::string &dispatcherType, Creator creator, SetupPlugsFn setupPlugsFn )
{
	creators()[dispatcherType] = std::pair<Creator, SetupPlugsFn>( creator, setupPlugsFn );
}

void Dispatcher::registeredDispatchers( std::vector<std::string> &dispatcherTypes )
{
	const CreatorMap &m = creators();
	for( const auto &[name, creator] : m )
	{
		dispatcherTypes.push_back( name );
	}
}

void Dispatcher::deregisterDispatcher( const std::string &dispatcherType )
{
	creators().erase( dispatcherType );
}

Dispatcher::CreatorMap &Dispatcher::creators()
{
	static CreatorMap m;
	return m;
}
