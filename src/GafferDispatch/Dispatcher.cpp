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

#include "boost/filesystem.hpp"

#include "IECore/FrameRange.h"
#include "IECore/MessageHandler.h"

#include "Gaffer/Context.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/SubGraph.h"

#include "GafferDispatch/Dispatcher.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferDispatch;

static InternedString g_frame( "frame" );
static InternedString g_batchSize( "batchSize" );
static InternedString g_immediatePlugName( "immediate" );
static InternedString g_postTaskIndexBlindDataName( "dispatcher:postTaskIndex" );
static InternedString g_immediateBlindDataName( "dispatcher:immediate" );
static InternedString g_executedBlindDataName( "dispatcher:executed" );
static InternedString g_visitedBlindDataName( "dispatcher:visited" );
static InternedString g_jobDirectoryContextEntry( "dispatcher:jobDirectory" );
static IECore::BoolDataPtr g_trueBoolData = new BoolData( true );

size_t Dispatcher::g_firstPlugIndex = 0;
Dispatcher::PreDispatchSignal Dispatcher::g_preDispatchSignal;
Dispatcher::PostDispatchSignal Dispatcher::g_postDispatchSignal;
std::string Dispatcher::g_defaultDispatcherType = "";

IE_CORE_DEFINERUNTIMETYPED( Dispatcher )

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

std::string Dispatcher::createJobDirectory( const Context *context ) const
{
	boost::filesystem::path jobDirectory( context->substitute( jobsDirectoryPlug()->getValue() ) );
	jobDirectory /= context->substitute( jobNamePlug()->getValue() );

	if ( jobDirectory == "" )
	{
		jobDirectory = boost::filesystem::current_path().string();
	}

	boost::filesystem::path result;
	for( int i=0; ; ++i )
	{
		result = jobDirectory / ( boost::format("%06d") % i ).str();
		if( boost::filesystem::is_directory( result ) )
		{
			continue;
		}
		boost::filesystem::create_directories( result );
		return result.string();
	}
}

/*
 * Static functions
 */

Dispatcher::PreDispatchSignal &Dispatcher::preDispatchSignal()
{
	return g_preDispatchSignal;
}

Dispatcher::PostDispatchSignal &Dispatcher::postDispatchSignal()
{
	return g_postDispatchSignal;
}

void Dispatcher::setupPlugs( Plug *parentPlug )
{
	if ( const TaskNode *node = parentPlug->ancestor<const TaskNode>() )
	{
		/// \todo: this will always return true until we sort out issue #915.
		/// But since requiresSequenceExecution() could feasibly return different
		/// values in different contexts, perhaps the conditional is bogus
		/// anyway, and if anything we should just grey out the plug in the UI?
		if( !node->taskPlug()->requiresSequenceExecution() )
		{
			parentPlug->addChild( new IntPlug( g_batchSize, Plug::In, 1 ) );
		}
	}

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
	:	m_plug( plug ), m_context( context ), m_blindData( new CompoundData )
{
}

Dispatcher::TaskBatch::TaskBatch( ConstTaskNodePtr node, Gaffer::ConstContextPtr context )
	:	m_plug( node->taskPlug() ), m_context( context ), m_blindData( new CompoundData )
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
	return m_plug ? runTimeCast<const TaskNode>( m_plug->node() ) : NULL;
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
			addPreTask( m_rootBatch.get(), batchTasksWalk( task ) );
		}

		TaskBatch *rootBatch()
		{
			return m_rootBatch.get();
		}

	private :

		TaskBatchPtr batchTasksWalk( const TaskNode::Task &task, const std::set<const TaskBatch *> &ancestors = std::set<const TaskBatch *>() )
		{
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
				postBatches.push_back( batchTasksWalk( *it ) );
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
				addPreTask( batch.get(), batchTasksWalk( *it, preTaskAncestors ) );
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
			// See if we've previously visited this task, and therefore
			// have placed it in a batch already, which we can return
			// unchanged.
			MurmurHash taskToBatchMapHash = task.hash();
			taskToBatchMapHash.append( (uint64_t)task.node() );
			if( task.hash() == MurmurHash() )
			{
				// Make sure we don't coalesce all no-ops into a single
				// batch. See comments in batchHash().
				taskToBatchMapHash.append( task.context()->getFrame() );
			}
			const TaskToBatchMap::const_iterator it = m_tasksToBatches.find( taskToBatchMapHash );
			if( it != m_tasksToBatches.end() )
			{
				return it->second;
			}

			// We haven't seen this task before, so we need to find
			// an appropriate batch to put it in. This may be one of
			// our current batches, or we may need to make a new one
			// entirely.

			TaskBatchPtr batch = NULL;
			const MurmurHash batchMapHash = batchHash( task );
			BatchMap::iterator bIt = m_currentBatches.find( batchMapHash );
			if( bIt != m_currentBatches.end() )
			{
				TaskBatchPtr candidateBatch = bIt->second;
				const IntPlug *batchSizePlug = task.node()->dispatcherPlug()->getChild<const IntPlug>( g_batchSize );
				const size_t batchSize = ( batchSizePlug ) ? batchSizePlug->getValue() : 1;
				if( task.plug()->requiresSequenceExecution() || ( candidateBatch->frames().size() < batchSize ) )
				{
					batch = candidateBatch;
				}
			}

			if( !batch )
			{
				batch = new TaskBatch( task.plug(), task.context() );
				m_currentBatches[batchMapHash] = batch;
			}

			// Now we have an appropriate batch, update it to include
			// the frame for our task, and any other relevant information.

			if( task.hash() != MurmurHash() )
			{
				float frame = task.context()->getFrame();
				std::vector<float> &frames = batch->frames();
				if( std::find( frames.begin(), frames.end(), frame ) == frames.end() )
				{
					if( task.plug()->requiresSequenceExecution() )
					{
						frames.insert( std::lower_bound( frames.begin(), frames.end(), frame ), frame );
					}
					else
					{
						frames.push_back( frame );
					}
				}
			}

			const BoolPlug *immediatePlug = task.node()->dispatcherPlug()->getChild<const BoolPlug>( g_immediatePlugName );
			if( immediatePlug && immediatePlug->getValue() )
			{
				/// \todo Should we be scoping a context for this, to allow the plug to
				/// have expressions on it? If so, should we be doing the same before
				/// calling requiresSequenceExecution()? Or should we instead require that
				/// they always be constant?
				batch->blindData()->writable()[g_immediateBlindDataName] = g_trueBoolData;
			}

			// Remember which batch we stored this task in, for
			// the next time someone asks for it.
			m_tasksToBatches[taskToBatchMapHash] = batch;

			return batch;
		}

		// Hash used to determine how to coalesce tasks into batches.
		// If `batchHash( task1 ) == batchHash( task2 )` then the two
		// tasks can be placed in the same batch.
		IECore::MurmurHash batchHash( const TaskNode::Task &task )
		{
			MurmurHash result;
			result.append( (uint64_t)task.node() );

			const Context *context = task.context();
			std::vector<IECore::InternedString> names;
			context->names( names );
			for( std::vector<IECore::InternedString>::const_iterator it = names.begin(); it != names.end(); ++it )
			{
				// Ignore the UI values since they should be irrelevant
				// to execution.
				if( it->string().compare( 0, 3, "ui:" ) == 0 )
				{
					continue;
				}
				// Ignore the frame, since the whole point of batching
				// is to allow multiple frames to be placed in the same
				// batch if the context is otherwise identical.
				///
				// There is one exception to this though - if the task is
				// a no-op, then we don't want to coalesce, because then
				// every single frame of the no-op would be placed in the
				// same batch, and all downstream frames would then be forced
				// to depend unnecessarily on all upstream frames.
				if( *it == g_frame && task.hash() != MurmurHash() )
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
			m_cancelledByPreDispatch = m_dispatcher->preDispatchSignal()( m_dispatcher, m_taskNodes );
		}

		~DispatcherSignalGuard()
		{
			try
			{
				m_dispatcher->postDispatchSignal()( m_dispatcher, m_taskNodes, (m_dispatchSuccessful && ( !m_cancelledByPreDispatch )) );
			}
			catch( const std::exception& e )
			{
				IECore::msg( IECore::Msg::Error, "postDispatchSignal exception:", e.what() );
			}
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
			for ( RecursiveOutputPlugIterator plugIt( subGraph ); !plugIt.done(); ++plugIt )
			{
				Node *sourceNode = plugIt->get()->source<Plug>()->node();
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
	ContextPtr context = new Context( *Context::current(), Context::Borrowed );
	m_jobDirectory = createJobDirectory( context.get() );
	context->set( g_jobDirectoryContextEntry, m_jobDirectory );

	// this object calls this->preDispatchSignal() in its constructor and this->postDispatchSignal()
	// in its destructor, thereby guaranteeing that we always call this->postDispatchSignal().

	DispatcherSignalGuard signalGuard( this, taskNodes );
	if ( signalGuard.cancelledByPreDispatch() )
	{
		return;
	}

	std::vector<FrameList::Frame> frames;
	FrameListPtr frameList = frameRange( script, context.get() );
	frameList->asList( frames );

	Batcher batcher;
	for( std::vector<FrameList::Frame>::const_iterator fIt = frames.begin(); fIt != frames.end(); ++fIt )
	{
		for( std::vector<TaskNodePtr>::const_iterator nIt = taskNodes.begin(); nIt != taskNodes.end(); ++nIt )
		{
			context->setFrame( *fIt );
			batcher.addTask( TaskNode::Task( *nIt, context.get() ) );
		}
	}

	executeAndPruneImmediateBatches( batcher.rootBatch() );

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
		return 0;
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
	for ( CreatorMap::const_iterator it = m.begin(); it!=m.end(); ++it )
	{
		dispatcherTypes.push_back( it->first );
	}
}

Dispatcher::CreatorMap &Dispatcher::creators()
{
	static CreatorMap m;
	return m;
}
