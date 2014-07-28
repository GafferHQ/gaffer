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
	
	addChild( new IntPlug( "framesMode", Plug::In, CurrentFrame, CurrentFrame ) );
	addChild( new StringPlug( "frameRange", Plug::In, "" ) );
	addChild( new StringPlug( "jobName", Plug::In, "" ) );
	addChild( new StringPlug( "jobDirectory", Plug::In, "" ) );
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
	
	const ScriptNode *script = (*nodes.begin())->scriptNode();
	for ( std::vector<ExecutableNodePtr>::const_iterator nIt = nodes.begin(); nIt != nodes.end(); ++nIt )
	{
		const ScriptNode *currentScript = (*nIt)->scriptNode();
		if ( !currentScript || currentScript != script )
		{
			throw IECore::Exception( getName().string() + ": Dispatched nodes must all belong to the same ScriptNode." );
		}
	}
	
	if ( preDispatchSignal()( this, nodes ) )
	{
		/// \todo: communicate the cancellation to the user
		return;
	}
	
	const Context *context = Context::current();
	
	std::vector<FrameList::Frame> frames;
	FrameListPtr frameList = frameRange( script, context );
	frameList->asList( frames );
	
	size_t i = 0;
	ExecutableNode::Tasks tasks;
	tasks.reserve( nodes.size() * frames.size() );
	for ( std::vector<FrameList::Frame>::const_iterator fIt = frames.begin(); fIt != frames.end(); ++fIt )
	{
		for ( std::vector<ExecutableNodePtr>::const_iterator nIt = nodes.begin(); nIt != nodes.end(); ++nIt, ++i )
		{
			ContextPtr frameContext = new Context( *context, Context::Borrowed );
			frameContext->setFrame( *fIt );
			tasks.push_back( ExecutableNode::Task( *nIt, frameContext ) );
		}
	}
	
	TaskDescriptions taskDescriptions;
	uniqueTaskDescriptions( tasks, taskDescriptions );
	
	if ( !taskDescriptions.empty() )
	{
		doDispatch( taskDescriptions );
	}
	
	postDispatchSignal()( this, nodes );
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

StringPlug *Dispatcher::jobDirectoryPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const StringPlug *Dispatcher::jobDirectoryPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
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

// Returns the input Task if it was never seen before, or the previous Task that is equivalent to this one.
const ExecutableNode::Task &Dispatcher::uniqueTaskDescription( const ExecutableNode::Task &task, TaskDescriptions &uniqueDescriptions, DescriptionIteratorMap &existingDescriptions )
{
	ExecutableNode::Tasks requirements;
	task.node()->requirements( task.context(), requirements );

	TaskDescription	description;
	description.task = task;

	// first we recurse on the requirements, so we know that the first tasks to be added will be the ones without requirements and 
	// the final result should be a list of tasks that does not break requirement order.
	for( ExecutableNode::Tasks::iterator rIt = requirements.begin(); rIt != requirements.end(); rIt++ )
	{
		// override the current requirements in case they are duplicates already added to existingDescriptions
		description.requirements.insert( uniqueTaskDescription( *rIt, uniqueDescriptions, existingDescriptions ) );
	}

	IECore::MurmurHash noHash;
	const IECore::MurmurHash hash = task.hash();
	
	std::pair<DescriptionIteratorMap::iterator, bool> it = existingDescriptions.insert( DescriptionIteratorMap::value_type( hash, DescriptionIterators() ) );
	DescriptionIterators &iterators = it.first->second;
	if ( !it.second )
	{
		// same hash, find all TaskDescriptions with same node
		for ( DescriptionIterators::iterator dIt = iterators.begin(); dIt != iterators.end(); ++dIt )
		{
			TaskDescription &currentDescription = **dIt;
			if ( currentDescription.task.node() == task.node() )
			{
				// same node... does it compute anything?
				if ( hash == noHash )
				{
					// the node doesn't compute anything, so we match it based on the requirements...
					if ( currentDescription.requirements == description.requirements )
					{
						// same node, same requirements, return previously registered empty task instead
						return currentDescription.task;
					}
				}
				else	// Executable node that actually does something...
				{
					// if hash and node matches we want to compute the union of all the 
					// requirements and return the previously registered task
					currentDescription.requirements.insert( description.requirements.begin(), description.requirements.end() );
					return currentDescription.task;
				}
			}
		}
	}
	
	// no existing description matches this Task
	uniqueDescriptions.push_back( description );
	iterators.push_back( --uniqueDescriptions.end() );
	
	return task;
}

void Dispatcher::uniqueTaskDescriptions( const ExecutableNode::Tasks &tasks, TaskDescriptions &uniqueDescriptions )
{
	DescriptionIteratorMap existingDescriptions;
	
	uniqueDescriptions.clear();
	for( ExecutableNode::Tasks::const_iterator tit = tasks.begin(); tit != tasks.end(); ++tit )
	{
		uniqueTaskDescription( *tit, uniqueDescriptions, existingDescriptions );
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
	else if ( mode == ScriptRange )
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
