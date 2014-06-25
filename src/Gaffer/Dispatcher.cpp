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

#include "Gaffer/CompoundPlug.h"
#include "Gaffer/Context.h"
#include "Gaffer/Dispatcher.h"
#include "Gaffer/ScriptNode.h"

using namespace IECore;
using namespace Gaffer;

size_t Dispatcher::g_firstPlugIndex = 0;
Dispatcher::DispatcherMap Dispatcher::g_dispatchers;
Dispatcher::DispatchSignal Dispatcher::g_preDispatchSignal;
Dispatcher::DispatchSignal Dispatcher::g_postDispatchSignal;

IE_CORE_DEFINERUNTIMETYPED( Dispatcher )

Dispatcher::Dispatcher( const std::string &name )
	: Node( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	
	addChild( new StringPlug( "jobName", Plug::In, "", Plug::Default & ~Plug::Serialisable ) );
	addChild( new StringPlug( "jobDirectory", Plug::In, "", Plug::Default & ~Plug::Serialisable ) );
}

Dispatcher::~Dispatcher()
{
}

void Dispatcher::dispatch( const std::vector<ExecutableNodePtr> &nodes ) const
{
	if ( nodes.empty() )
	{
		throw IECore::Exception( getName().string() + ": Must specify at least one node to dispatch." );
	}
	
	preDispatchSignal()( this, nodes );
	
	const Context *context = Context::current();
	
	size_t i = 0;
	ExecutableNode::Tasks tasks( nodes.size(), ExecutableNode::Task( NULL, new Context( *context, Context::Borrowed ) ) );
	for ( std::vector<ExecutableNodePtr>::const_iterator nIt = nodes.begin(); nIt != nodes.end(); ++nIt, ++i )
	{
		tasks[i].node = *nIt;
	}
	
	TaskDescriptions taskDescriptions;
	uniqueTasks( tasks, taskDescriptions );
	
	if ( !taskDescriptions.empty() )
	{
		doDispatch( taskDescriptions );
	}
	
	postDispatchSignal()( this, nodes );
}

StringPlug *Dispatcher::jobNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const StringPlug *Dispatcher::jobNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

StringPlug *Dispatcher::jobDirectoryPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const StringPlug *Dispatcher::jobDirectoryPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const std::string Dispatcher::jobDirectory( const Context *context ) const
{
	std::string jobDir = context->substitute( jobDirectoryPlug()->getValue() );
	
	boost::filesystem::path path( jobDir );
	path /= context->substitute( jobNamePlug()->getValue() );
	if ( path == "" )
	{
		return boost::filesystem::current_path().string();
	}
	
	boost::filesystem::create_directories( path );
	return path.string();
}

/*
 * Static functions
 */

Dispatcher::DispatchSignal &Dispatcher::preDispatchSignal()
{
	return g_preDispatchSignal;	
}

Dispatcher::DispatchSignal &Dispatcher::postDispatchSignal()
{
	return g_postDispatchSignal;	
}

void Dispatcher::setupPlugs( CompoundPlug *parentPlug )
{
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

/// Returns the input Task if it was never seen before, or the previous Task that is equivalent to this one.
/// It also populates flattenedTasks with unique tasks seen so far.
/// It uses seenTasks object as a temporary buffer.
const ExecutableNode::Task &Dispatcher::uniqueTask( const ExecutableNode::Task &task, TaskDescriptions &uniqueTasks, TaskSet &seenTasks )
{	
	ExecutableNode::Tasks requirements;
	task.node->executionRequirements( task.context, requirements );

	TaskDescription	taskDesc;
	taskDesc.task = task;

	// first we recurse on the requirements, so we know that the first tasks to be added will be the ones without requirements and 
	// the final result should be a list of tasks that does not break requirement order.
	for( ExecutableNode::Tasks::iterator rIt = requirements.begin(); rIt != requirements.end(); rIt++ )
	{
		// override the current requirements in case they are duplicates already added to 'seenTasks'
		taskDesc.requirements.insert( uniqueTask( *rIt, uniqueTasks, seenTasks ) );
	}

	IECore::MurmurHash noHash;
	IECore::MurmurHash hash = task.node->executionHash( task.context );

	std::pair< TaskSet::iterator,bool > tit = seenTasks.insert( TaskSet::value_type( hash, std::vector< size_t >() ) );
	if ( tit.second )
	{
		// hash never seen, the current task is added "as is".
		std::vector< size_t > &taskIndices = tit.first->second;
		taskIndices.push_back( uniqueTasks.size() );
		uniqueTasks.push_back( taskDesc );
	}
	else
	{
		// same hash, find all TaskDescriptions with same node
		std::vector< size_t > &taskIndices = tit.first->second;
		std::vector< size_t >::const_iterator dIt;

		for ( dIt = taskIndices.begin(); dIt != taskIndices.end(); dIt++ )
		{
			TaskDescription &seenTask = uniqueTasks[ *dIt ];
			if ( seenTask.task.node.get() == task.node.get() )
			{
				// same node... does it compute anything?
				if ( hash == noHash )
				{
					// the node doesn't compute anything, so we match it based on the requirements...
					if ( seenTask.requirements == taskDesc.requirements )
					{
						// same node, same requirements, return previously registered empty task instead
						return seenTask.task;
					}
				}
				else	// Executable node that actually does something...
				{
					// if hash and node matches we want to compute the union of all the 
					// requirements and return the previously registered task
					seenTask.requirements.insert( taskDesc.requirements.begin(), taskDesc.requirements.end() );
					return seenTask.task;
				}
			}
		}
		// similar Task not in the list, task is added "as is"
		taskIndices.push_back( uniqueTasks.size() );
		uniqueTasks.push_back( taskDesc );
	}
	return task;
}

void Dispatcher::uniqueTasks( const ExecutableNode::Tasks &tasks, TaskDescriptions &uniqueTasks )
{
	TaskSet seenTasks;
	
	uniqueTasks.clear();
	for( ExecutableNode::Tasks::const_iterator tit = tasks.begin(); tit != tasks.end(); ++tit )
	{
		uniqueTask( *tit, uniqueTasks, seenTasks );
	}
}
