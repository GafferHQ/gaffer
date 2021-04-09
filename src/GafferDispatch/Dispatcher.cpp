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
#include "boost/filesystem.hpp"

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

} // namespace

//////////////////////////////////////////////////////////////////////////
// Dispatcher
//////////////////////////////////////////////////////////////////////////

static InternedString g_frame( "frame" );
static InternedString g_batchSize( "batchSize" );
static InternedString g_immediatePlugName( "immediate" );
static InternedString g_postTaskIndexBlindDataName( "dispatcher:postTaskIndex" );
static InternedString g_immediateBlindDataName( "dispatcher:immediate" );
static InternedString g_sizeBlindDataName( "dispatcher:size" );
static InternedString g_executedBlindDataName( "dispatcher:executed" );
static InternedString g_visitedBlindDataName( "dispatcher:visited" );
static InternedString g_jobDirectoryContextEntry( "dispatcher:jobDirectory" );
static InternedString g_scriptFileNameContextEntry( "dispatcher:scriptFileName" );
static IECore::BoolDataPtr g_trueBoolData = new BoolData( true );

size_t Dispatcher::g_firstPlugIndex = 0;
Dispatcher::PreDispatchSignal Dispatcher::g_preDispatchSignal;
Dispatcher::DispatchSignal Dispatcher::g_dispatchSignal;
Dispatcher::PostDispatchSignal Dispatcher::g_postDispatchSignal;
std::string Dispatcher::g_defaultDispatcherType = "";

GAFFER_NODE_DEFINE_TYPE( Dispatcher )

Dispatcher::Dispatcher( const std::string &name )
	: Node( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "framesMode", Plug::In, CurrentFrame, CurrentFrame ) );
	addChild( new StringPlug( "frameRange", Plug::In, "1-100x10" ) );
	addChild( new StringPlug( "jobName", Plug::In, "" ) );
	addChild( new StringPlug( "jobsDirectory", Plug::In, "" ) );
}

Dispatcher::~Dispatcher()
{
}

IntPlug *Dispatcher::framesModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const IntPlug *Dispatcher::framesModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

StringPlug *Dispatcher::frameRangePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const StringPlug *Dispatcher::frameRangePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

StringPlug *Dispatcher::jobNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const StringPlug *Dispatcher::jobNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

StringPlug *Dispatcher::jobsDirectoryPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const StringPlug *Dispatcher::jobsDirectoryPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const std::string Dispatcher::jobDirectory() const
{
	return m_jobDirectory;
}

void Dispatcher::createJobDirectory( const Gaffer::ScriptNode *script, Gaffer::Context *context ) const
{
	boost::filesystem::path jobDirectory( context->substitute( jobsDirectoryPlug()->getValue() ) );
	jobDirectory /= context->substitute( jobNamePlug()->getValue() );

	if( jobDirectory == "" )
	{
		const string outerJobDirectory = context->get<string>( g_jobDirectoryContextEntry, "" );
		const string outerScriptFileName = context->get<string>( g_scriptFileNameContextEntry, "" );
		const Process *outerProcess = Process::current();
		InternedString outerProcessType = outerProcess ? outerProcess->type() : "";
		if(
			outerJobDirectory.size() && outerScriptFileName.size() &&
			( outerProcessType == "taskNode:execute" || outerProcessType == "taskNode:executeSequence" ) &&
			outerProcess->plug()->ancestor<ScriptNode>() == script
		)
		{
			// We're being run inside a task executing in another dispatch
			// for the same script. Borrow the job directory created by that dispatch.
			/// \todo Should there be a more explicit way of saying "borrow
			/// the outer directory"? Perhaps dispatchers should have a
			/// plug specifying that they are to do a nested dispatch?
			/// Consider this at the same time as we consider hosting
			/// dispatchers directly in the graph.
			m_jobDirectory = outerJobDirectory;
			return;
		}

		/// \todo I think it would be better to throw here, rather than
		/// litter the current directory.
		jobDirectory = boost::filesystem::current_path().string();
	}

	boost::filesystem::create_directories( jobDirectory );

	// To distinguish between multiple jobs with the same settings
	// we use a unique numeric subdirectory per job. Start by finding
	// the highest existing numbered directory entry. Doing this with
	// a directory iterator is much quicker than calling `is_directory()`
	// in a loop.

	long i = -1;
	for( const auto &d : boost::filesystem::directory_iterator( jobDirectory ) )
	{
		i = std::max( i, strtol( d.path().filename().c_str(), nullptr, 10 ) );
	}

	// Now create the next directory. We do this in a loop until we
	// successfully create a directory of our own, because we
	// may be in a race against other processes.

	boost::format formatter( "%06d" );
	boost::filesystem::path numberedJobDirectory;
	while( true )
	{
		++i;
		numberedJobDirectory = jobDirectory / ( formatter % i ).str();
		if( boost::filesystem::create_directory( numberedJobDirectory ) )
		{
			break;
		}
	}

	m_jobDirectory = numberedJobDirectory.string();
	context->set( g_jobDirectoryContextEntry, m_jobDirectory );

	// Now figure out where we'll save the script in that directory, and
	// advertise it via the context. We'll do the actual saving later.

	boost::filesystem::path scriptFileName = script->fileNamePlug()->getValue();
	if( scriptFileName.size() )
	{
		scriptFileName = numberedJobDirectory / scriptFileName.filename();
	}
	else
	{
		scriptFileName = numberedJobDirectory / "untitled.gfr";
	}

	context->set( g_scriptFileNameContextEntry, scriptFileName.string() );
}

/*
 * Static functions
 */

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
	for ( CreatorMap::const_iterator it = m.begin(); it != m.end(); ++it )
	{
		if ( it->second.second )
		{
			it->second.second( parentPlug );
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
	catch ( IECore::Exception &e )
	{
		throw IECore::Exception( "Dispatcher: Custom Frame Range is not a valid IECore::FrameList" );
	}
}

//////////////////////////////////////////////////////////////////////////
// TaskBatch implementation
//////////////////////////////////////////////////////////////////////////

Dispatcher::TaskBatch::TaskBatch()
	:	m_blindData( new CompoundData )
{
}

Dispatcher::TaskBatch::TaskBatch( TaskNode::ConstTaskPlugPtr plug, Gaffer::ConstContextPtr context )
	:	m_plug( plug ), m_context( new Context( *context ) ), m_blindData( new CompoundData )
{
	// Frames must be determined by our `frames()` field, so
	// remove any possibility of accidentally using the frame
	// from the context.
	m_context->remove( "frame" );
}

Dispatcher::TaskBatch::TaskBatch( ConstTaskNodePtr node, Gaffer::ConstContextPtr context )
	:	TaskBatch( node->taskPlug(), context )
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

std::vector<float> &Dispatcher::TaskBatch::frames()
{
	return m_frames;
}

const std::vector<float> &Dispatcher::TaskBatch::frames() const
{
	return m_frames;
}

std::vector<Dispatcher::TaskBatchPtr> &Dispatcher::TaskBatch::preTasks()
{
	return m_preTasks;
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

	private :

		TaskBatchPtr batchTasksWalk( TaskNode::Task task, const std::set<const TaskBatch *> &ancestors = std::set<const TaskBatch *>() )
		{
			// Find source task, taking into account
			// Switches and ContextProcessors.
			{
				Context::Scope scopedTaskContext( task.context() );
				const Plug *sourcePlug; ConstContextPtr sourceContext;
				tie( sourcePlug, sourceContext ) = computedSource( task.plug() );
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
				throw IECore::Exception( ( boost::format( "Dispatched tasks cannot have cyclic dependencies but %s is involved in a cycle." ) % batch->plug()->relativeName( batch->plug()->ancestor<ScriptNode>() ) ).str() );
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
			for( TaskNode::Tasks::const_iterator it = postTasks.begin(); it != postTasks.end(); ++it )
			{
				if( auto postBatch = batchTasksWalk( *it ) )
				{
					postBatches.push_back( postBatch );
				}
			}

			// Collect all the batches the preTasks belong in,
			// and add them as preTasks for our batch.

			std::set<const TaskBatch *> preTaskAncestors( ancestors );
			preTaskAncestors.insert( batch.get() );
			for( TaskBatches::const_iterator it = postBatches.begin(), eIt = postBatches.end(); it != eIt; ++it )
			{
				preTaskAncestors.insert( it->get() );
			}

			for( TaskNode::Tasks::const_iterator it = preTasks.begin(); it != preTasks.end(); ++it )
			{
				if( auto preBatch = batchTasksWalk( *it, preTaskAncestors ) )
				{
					addPreTask( batch.get(), preBatch );
				}
			}

			// As far as TaskBatch and doDispatch() are concerned, there
			// is no such thing as a postTask, so we emulate them by making
			// this batch a preTask of each of the postTask batches. We also
			// add the postTask batches as preTasks for the root, so that they
			// are reachable from doDispatch().
			for( TaskBatches::const_iterator it = postBatches.begin(), eIt = postBatches.end(); it != eIt; ++it )
			{
				addPreTask( it->get(), batch, /* forPostTask =  */ true );
				addPreTask( m_rootBatch.get(), *it );
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
				taskHash.append( contextHash( task.context() ) );
			}
			// Prevent identical tasks from different nodes from being
			// coalesced.
			taskHash.append( (uint64_t)task.plug() );

			const TaskToBatchMap::const_iterator it = m_tasksToBatches.find( taskHash );
			if( it != m_tasksToBatches.end() )
			{
				return it->second;
			}

			// We haven't seen this task before, so we need to find
			// an appropriate batch to put it in. This may be one of
			// our current batches, or we may need to make a new one
			// entirely if the current batch is full.

			const bool requiresSequenceExecution = task.plug()->requiresSequenceExecution();

			TaskBatchPtr batch = nullptr;
			const MurmurHash batchMapHash = batchHash( task );
			BatchMap::iterator bIt = m_currentBatches.find( batchMapHash );
			if( bIt != m_currentBatches.end() )
			{
				TaskBatchPtr candidateBatch = bIt->second;
				// Unfortunately we have to track batch size separately from `batch->frames().size()`,
				// because no-ops don't update `frames()`, but _do_ count towards batch size.
				IntDataPtr batchSizeData = candidateBatch->blindData()->member<IntData>( g_sizeBlindDataName );
				const IntPlug *batchSizePlug = dispatcherPlug( task )->getChild<const IntPlug>( g_batchSize );
				const int batchSizeLimit = ( batchSizePlug ) ? batchSizePlug->getValue() : 1;
				if( requiresSequenceExecution || ( batchSizeData->readable() < batchSizeLimit ) )
				{
					batch = candidateBatch;
					batchSizeData->writable()++;
				}
			}

			if( !batch )
			{
				batch = new TaskBatch( task.plug(), task.context() );
				batch->blindData()->writable()[g_sizeBlindDataName] = new IntData( 1 );
				m_currentBatches[batchMapHash] = batch;
			}

			// Now we have an appropriate batch, update it to include
			// the frame for our task, and any other relevant information.

			if( !taskIsNoOp )
			{
				float frame = task.context()->getFrame();
				std::vector<float> &frames = batch->frames();
				if( requiresSequenceExecution )
				{
					frames.insert( std::lower_bound( frames.begin(), frames.end(), frame ), frame );
				}
				else
				{
					frames.push_back( frame );
				}
			}

			const BoolPlug *immediatePlug = dispatcherPlug( task )->getChild<const BoolPlug>( g_immediatePlugName );
			if( immediatePlug && immediatePlug->getValue() )
			{
				batch->blindData()->writable()[g_immediateBlindDataName] = g_trueBoolData;
			}

			// Remember which batch we stored this task in, for
			// the next time someone asks for it.
			m_tasksToBatches[taskHash] = batch;

			return batch;
		}

		// Hash used to determine how to coalesce tasks into batches.
		// If `batchHash( task1 ) == batchHash( task2 )` then the two
		// tasks can be placed in the same batch.
		IECore::MurmurHash batchHash( const TaskNode::Task &task )
		{
			MurmurHash result;
			result.append( (uint64_t)task.plug() );
			// We ignore the frame because the whole point of batching
			// is to allow multiple frames to be placed in the same
			// batch if the context is otherwise identical.
			result.append( contextHash( task.context(), /* ignoreFrame = */ true ) );
			return result;
		}

		IECore::MurmurHash contextHash( const Context *context, bool ignoreFrame = false ) const
		{
			IECore::MurmurHash result;
			std::vector<IECore::InternedString> names;
			context->names( names );
			for( std::vector<IECore::InternedString>::const_iterator it = names.begin(); it != names.end(); ++it )
			{
				// Ignore the UI values since they should be irrelevant
				// to execution.
				if( boost::starts_with( it->string(), "ui:" ) )
				{
					continue;
				}
				if( ignoreFrame && *it == g_frame )
				{
					continue;
				}

				result.append( *it );
				context->get<const IECore::Data>( *it )->hash( result );
			}
			return result;
		}

		void addPreTask( TaskBatch *batch, TaskBatchPtr preTask, bool forPostTask = false )
		{
			TaskBatches &preTasks = batch->preTasks();
			if( std::find( preTasks.begin(), preTasks.end(), preTask ) == preTasks.end() )
			{
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
					IntDataPtr postTaskIndex = batch->blindData()->member<IntData>(
						g_postTaskIndexBlindDataName, /* throwExceptions = */ false, /* createIfMissing = */ true
					);
					preTasks.insert( preTasks.begin() + postTaskIndex->readable(), preTask );
					postTaskIndex->writable()++;
				}
				else
				{
					preTasks.push_back( preTask );
				}
			}
		}

		const Gaffer::Plug *dispatcherPlug( const TaskNode::Task &task )
		{
			return static_cast<const TaskNode *>( task.plug()->node() )->dispatcherPlug();
		}

		typedef std::map<IECore::MurmurHash, TaskBatchPtr> BatchMap;
		typedef std::map<IECore::MurmurHash, TaskBatchPtr> TaskToBatchMap;

		TaskBatchPtr m_rootBatch;
		BatchMap m_currentBatches;
		TaskToBatchMap m_tasksToBatches;

};

//////////////////////////////////////////////////////////////////////////
// Dispatcher::dispatch()
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

void Dispatcher::dispatch( const std::vector<NodePtr> &nodes ) const
{
	// clear job directory, so that if our node validation fails,
	// jobDirectory() won't return the result from the previous dispatch.
	m_jobDirectory = "";

	// validate the nodes we've been given

	if ( nodes.empty() )
	{
		throw IECore::Exception( getName().string() + ": Must specify at least one node to dispatch." );
	}

	std::vector<TaskNodePtr> taskNodes;
	const ScriptNode *script = (*nodes.begin())->scriptNode();
	for ( std::vector<NodePtr>::const_iterator nIt = nodes.begin(); nIt != nodes.end(); ++nIt )
	{
		const ScriptNode *currentScript = (*nIt)->scriptNode();
		if ( !currentScript || currentScript != script )
		{
			throw IECore::Exception( getName().string() + ": Dispatched nodes must all belong to the same ScriptNode." );
		}

		if ( TaskNode *taskNode = runTimeCast<TaskNode>( nIt->get() ) )
		{
			taskNodes.push_back( taskNode );
		}
		else if ( const SubGraph *subGraph = runTimeCast<const SubGraph>( nIt->get() ) )
		{
			for( auto &plug : TaskNode::TaskPlug::RecursiveOutputRange( *subGraph ) )
			{
				Node *sourceNode = plug->source()->node();
				if ( TaskNode *taskNode = runTimeCast<TaskNode>( sourceNode ) )
				{
					taskNodes.push_back( taskNode );
				}
			}
		}
		else
		{
			throw IECore::Exception( getName().string() + ": Dispatched nodes must be TaskNodes or SubGraphs containing TaskNodes." );
		}
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
	for( std::vector<FrameList::Frame>::const_iterator fIt = frames.begin(); fIt != frames.end(); ++fIt )
	{
		for( std::vector<TaskNodePtr>::const_iterator nIt = taskNodes.begin(); nIt != taskNodes.end(); ++nIt )
		{
			jobContext->setFrame( *fIt );
			batcher.addTask( TaskNode::Task( *nIt, Context::current() ) );
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
	if( !boost::filesystem::exists( scriptFileName ) )
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
	if( batch->blindData()->member<BoolData>( g_visitedBlindDataName ) )
	{
		return;
	}

	immediate = immediate || batch->blindData()->member<BoolData>( g_immediateBlindDataName );

	TaskBatches &preTasks = batch->preTasks();
	for( TaskBatches::iterator it = preTasks.begin(); it != preTasks.end(); )
	{
		executeAndPruneImmediateBatches( it->get(), immediate );
		if( (*it)->blindData()->member<BoolData>( g_executedBlindDataName ) )
		{
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
		batch->blindData()->writable()[g_executedBlindDataName] = g_trueBoolData;
	}

	batch->blindData()->writable()[g_visitedBlindDataName] = g_trueBoolData;
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

std::vector<DispatcherPtr> Dispatcher::createMatching( const IECore::StringAlgo::MatchPattern &pattern )
{
	std::vector<DispatcherPtr> dispatchers;

	const CreatorMap &m = creators();
	for( const auto &it : m )
	{
		if( IECore::StringAlgo::matchMultiple( it.first, pattern ) )
		{
			dispatchers.push_back( it.second.first() );
		}
	}

	return dispatchers;
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
	for ( CreatorMap::const_iterator it = m.begin(); it!=m.end(); ++it )
	{
		dispatcherTypes.push_back( it->first );
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
