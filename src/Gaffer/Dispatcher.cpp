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

#include "boost/filesystem.hpp"

#include "IECore/FrameRange.h"
#include "IECore/MessageHandler.h"

#include "Gaffer/Box.h"
#include "Gaffer/CompoundPlug.h"
#include "Gaffer/Context.h"
#include "Gaffer/Dispatcher.h"
#include "Gaffer/ScriptNode.h"

using namespace IECore;
using namespace Gaffer;

static InternedString g_frame( "frame" );
static InternedString g_batchSize( "batchSize" );

size_t Dispatcher::g_firstPlugIndex = 0;
Dispatcher::DispatcherMap Dispatcher::g_dispatchers;
Dispatcher::PreDispatchSignal Dispatcher::g_preDispatchSignal;
Dispatcher::PostDispatchSignal Dispatcher::g_postDispatchSignal;

IE_CORE_DEFINERUNTIMETYPED( Dispatcher )

Dispatcher::Dispatcher( const std::string &name )
	: Node( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "framesMode", Plug::In, CurrentFrame, CurrentFrame ) );
	addChild( new StringPlug( "frameRange", Plug::In, "" ) );
	addChild( new StringPlug( "jobName", Plug::In, "" ) );
	addChild( new StringPlug( "jobsDirectory", Plug::In, "" ) );
}

Dispatcher::~Dispatcher()
{
}

namespace
{

/// Guard class for calling a dispatcher's preDispatchSignal(), then guaranteeing postDispatchSignal() gets called
class DispatcherSignalGuard
{
public:
	DispatcherSignalGuard( const Dispatcher* d, const std::vector<ExecutableNodePtr> &executables ) : m_dispatchSuccessful( false ), m_executables( executables ), m_dispatcher( d )
	{
		m_cancelledByPreDispatch = m_dispatcher->preDispatchSignal()( m_dispatcher, m_executables );
	}

	~DispatcherSignalGuard()
	{
		try
		{
			m_dispatcher->postDispatchSignal()( m_dispatcher, m_executables, (m_dispatchSuccessful && ( !m_cancelledByPreDispatch )) );
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

	const std::vector<ExecutableNodePtr> &m_executables;
	const Dispatcher* m_dispatcher;
};

}

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

	std::vector<ExecutableNodePtr> executables;
	const ScriptNode *script = (*nodes.begin())->scriptNode();
	for ( std::vector<NodePtr>::const_iterator nIt = nodes.begin(); nIt != nodes.end(); ++nIt )
	{
		const ScriptNode *currentScript = (*nIt)->scriptNode();
		if ( !currentScript || currentScript != script )
		{
			throw IECore::Exception( getName().string() + ": Dispatched nodes must all belong to the same ScriptNode." );
		}

		if ( ExecutableNode *executable = runTimeCast<ExecutableNode>( nIt->get() ) )
		{
			executables.push_back( executable );
		}
		else if ( const Box *box = runTimeCast<const Box>( nIt->get() ) )
		{
			for ( RecursiveOutputPlugIterator plugIt( box ); plugIt != plugIt.end(); ++plugIt )
			{
				Node *sourceNode = plugIt->get()->source<Plug>()->node();
				if ( ExecutableNode *executable = runTimeCast<ExecutableNode>( sourceNode ) )
				{
					executables.push_back( executable );
				}
			}
		}
		else
		{
			throw IECore::Exception( getName().string() + ": Dispatched nodes must be ExecutableNodes or Boxes containing ExecutableNodes." );
		}
	}

	// create the job directory now, so it's available in preDispatchSignal().
	const Context *context = Context::current();
	m_jobDirectory = createJobDirectory( context );

	// this object calls this->preDispatchSignal() in its constructor and this->postDispatchSignal()
	// in its destructor, thereby guaranteeing that we always call this->postDispatchSignal().

	DispatcherSignalGuard signalGuard( this, executables );
	if ( signalGuard.cancelledByPreDispatch() )
	{
		return;
	}

	std::vector<FrameList::Frame> frames;
	FrameListPtr frameList = frameRange( script, context );
	frameList->asList( frames );

	size_t i = 0;
	ExecutableNode::Tasks tasks;
	tasks.reserve( executables.size() * frames.size() );
	for ( std::vector<FrameList::Frame>::const_iterator fIt = frames.begin(); fIt != frames.end(); ++fIt )
	{
		for ( std::vector<ExecutableNodePtr>::const_iterator nIt = executables.begin(); nIt != executables.end(); ++nIt, ++i )
		{
			ContextPtr frameContext = new Context( *context, Context::Borrowed );
			frameContext->setFrame( *fIt );
			tasks.push_back( ExecutableNode::Task( *nIt, frameContext ) );
		}
	}

	TaskBatchPtr rootBatch = batchTasks( tasks );

	if ( !rootBatch->requirements().empty() )
	{
		doDispatch( rootBatch.get() );
	}

	// inform the guard that the process has been completed, so it can pass this info to
	// postDispatchSignal():

	signalGuard.success();
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

void Dispatcher::setupPlugs( CompoundPlug *parentPlug )
{
	if ( const ExecutableNode *node = parentPlug->ancestor<const ExecutableNode>() )
	{
		/// \todo: this will always return true until we sort out issue #915
		if ( !node->requiresSequenceExecution() )
		{
			parentPlug->addChild( new IntPlug( g_batchSize, Plug::In, 1 ) );
		}
	}

	for ( DispatcherMap::const_iterator cit = g_dispatchers.begin(); cit != g_dispatchers.end(); cit++ )
	{
		cit->second->doSetupPlugs( parentPlug );
	}
}

void Dispatcher::dispatcherNames( std::vector<std::string> &names )
{
	names.clear();
	names.reserve( g_dispatchers.size() );
	for ( DispatcherMap::const_iterator cit = g_dispatchers.begin(); cit != g_dispatchers.end(); cit++ )
	{
		names.push_back( cit->first );
	}
}

void Dispatcher::registerDispatcher( const std::string &name, DispatcherPtr dispatcher )
{
	g_dispatchers[name] = dispatcher;
}

const Dispatcher *Dispatcher::dispatcher( const std::string &name )
{
	DispatcherMap::const_iterator cit = g_dispatchers.find( name );
	if ( cit == g_dispatchers.end() )
	{
		throw Exception( "\"" + name + "\" is not a registered Dispatcher." );
	}
	return cit->second.get();
}


Dispatcher::TaskBatchPtr Dispatcher::batchTasks( const ExecutableNode::Tasks &tasks )
{
	TaskBatchPtr root = new TaskBatch;

	BatchMap currentBatches;
	TaskToBatchMap tasksToBatches;

	for ( ExecutableNode::Tasks::const_iterator it = tasks.begin(); it != tasks.end(); ++it )
	{
		batchTasksWalk( root, *it, currentBatches, tasksToBatches );
	}

	return root;
}

void Dispatcher::batchTasksWalk( Dispatcher::TaskBatchPtr parent, const ExecutableNode::Task &task, BatchMap &currentBatches, TaskToBatchMap &tasksToBatches )
{
	TaskBatchPtr batch = acquireBatch( task, currentBatches, tasksToBatches );

	TaskBatches &parentRequirements = parent->requirements();
	if ( ( batch != parent ) && std::find( parentRequirements.begin(), parentRequirements.end(), batch ) == parentRequirements.end() )
	{
		parentRequirements.push_back( batch );
	}

	ExecutableNode::Tasks taskRequirements;
	task.node()->requirements( task.context(), taskRequirements );

	for ( ExecutableNode::Tasks::const_iterator it = taskRequirements.begin(); it != taskRequirements.end(); ++it )
	{
		batchTasksWalk( batch, *it, currentBatches, tasksToBatches );
	}
}

Dispatcher::TaskBatchPtr Dispatcher::acquireBatch( const ExecutableNode::Task &task, BatchMap &currentBatches, TaskToBatchMap &tasksToBatches )
{
	MurmurHash taskHash = task.hash();
	TaskToBatchMap::iterator it = tasksToBatches.find( taskHash );
	if ( it != tasksToBatches.end() )
	{
		return it->second;
	}

	MurmurHash hash = batchHash( task );
	BatchMap::iterator bIt = currentBatches.find( hash );
	if ( bIt != currentBatches.end() )
	{
		TaskBatchPtr batch = bIt->second;

		std::vector<float> &frames = batch->frames();
		const CompoundPlug *dispatcherPlug = task.node()->dispatcherPlug();
		const IntPlug *batchSizePlug = dispatcherPlug->getChild<const IntPlug>( g_batchSize );
		size_t batchSize = ( batchSizePlug ) ? batchSizePlug->getValue() : 1;

		if ( task.node()->requiresSequenceExecution() || ( frames.size() < batchSize ) )
		{
			if ( task.hash() != MurmurHash() )
			{
				float frame = task.context()->getFrame();
				if ( std::find( frames.begin(), frames.end(), frame ) == frames.end() )
				{
					if ( task.node()->requiresSequenceExecution() )
					{
						frames.insert( std::lower_bound( frames.begin(), frames.end(), frame ), frame );
					}
					else
					{
						frames.push_back( frame );
					}
				}
			}

			if ( taskHash != MurmurHash() )
			{
				tasksToBatches[taskHash] = batch;
			}
			
			return batch;
		}
	}

	TaskBatchPtr batch = new TaskBatch( task );
	currentBatches[hash] = batch;
	if ( taskHash != MurmurHash() )
	{
		tasksToBatches[taskHash] = batch;
	}
	
	return batch;
}

IECore::MurmurHash Dispatcher::batchHash( const ExecutableNode::Task &task )
{
	MurmurHash result;
	result.append( (uint64_t)task.node() );

	if ( task.hash() == MurmurHash() )
	{
		return result;
	}

	const Context *context = task.context();
	std::vector<IECore::InternedString> names;
	context->names( names );
	for ( std::vector<IECore::InternedString>::const_iterator it = names.begin(); it != names.end(); ++it )
	{
		// ignore the frame and the ui values
		if ( ( *it != g_frame ) && it->string().compare( 0, 3, "ui:" ) )
		{
			result.append( *it );
			if ( const IECore::Data *data = context->get<const IECore::Data>( *it ) )
			{
				data->hash( result );
			}
		}
	}

	return result;
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
	: m_node(), m_context(), m_frames(), m_requirements()
{
	m_blindData = new CompoundData;
}

Dispatcher::TaskBatch::TaskBatch( const ExecutableNode::Task &task )
	: m_node( task.node() ), m_context( task.context() ), m_frames(), m_requirements()
{
	m_blindData = new CompoundData;

	if ( task.hash() != MurmurHash() )
	{
		m_frames.push_back( task.context()->getFrame() );
	}
}

Dispatcher::TaskBatch::TaskBatch( const TaskBatch &other )
	: m_node( other.m_node ), m_context( other.m_context ), m_blindData( other.m_blindData ), m_frames( other.m_frames ), m_requirements( other.m_requirements )
{
}

void Dispatcher::TaskBatch::execute() const
{
	if ( m_frames.empty() )
	{
		return;
	}

	Context::Scope scopedContext( m_context.get() );
	m_node->executeSequence( m_frames );
}

const ExecutableNode *Dispatcher::TaskBatch::node() const
{
	return m_node.get();
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

std::vector<Dispatcher::TaskBatchPtr> &Dispatcher::TaskBatch::requirements()
{
	return m_requirements;
}

const std::vector<Dispatcher::TaskBatchPtr> &Dispatcher::TaskBatch::requirements() const
{
	return m_requirements;
}

CompoundData *Dispatcher::TaskBatch::blindData()
{
	return m_blindData.get();
}

const CompoundData *Dispatcher::TaskBatch::blindData() const
{
	return m_blindData.get();
}
