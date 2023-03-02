//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#pragma once

#include "IECorePython/ScopedGILRelease.h"

#include "boost/python/suite/indexing/container_utils.hpp"

namespace GafferDispatchBindings
{

namespace Detail
{

struct TaskNodeAccessor
{

template<typename T>
static bool affectsTask( T &n, const Gaffer::Plug *plug )
{
	return n.T::affectsTask( plug );
}

template<typename T>
static boost::python::list preTasks( T &n, Gaffer::Context *context )
{
	GafferDispatch::TaskNode::Tasks tasks;
	n.T::preTasks( context, tasks );
	boost::python::list result;
	for( GafferDispatch::TaskNode::Tasks::const_iterator tIt = tasks.begin(); tIt != tasks.end(); ++tIt )
	{
		result.append( *tIt );
	}
	return result;
}

template<typename T>
static boost::python::list postTasks( T &n, Gaffer::Context *context )
{
	GafferDispatch::TaskNode::Tasks tasks;
	n.T::postTasks( context, tasks );
	boost::python::list result;
	for( GafferDispatch::TaskNode::Tasks::const_iterator tIt = tasks.begin(); tIt != tasks.end(); ++tIt )
	{
		result.append( *tIt );
	}
	return result;
}

template<typename T>
static IECore::MurmurHash hash( T &n, const Gaffer::Context *context )
{
	return n.T::hash( context );
}

template<typename T>
static void execute( T &n )
{
	IECorePython::ScopedGILRelease gilRelease;
	n.T::execute();
}

template<typename T>
static void executeSequence( T &n, const boost::python::object &frameList )
{
	std::vector<float> frames;
	boost::python::container_utils::extend_container( frames, frameList );
	IECorePython::ScopedGILRelease gilRelease;
	n.T::executeSequence( frames );
}

template<typename T>
static bool requiresSequenceExecution( T &n )
{
	return n.T::requiresSequenceExecution();
}

};

} // namespace Detail

template<typename T, typename Ptr>
TaskNodeClass<T, Ptr>::TaskNodeClass( const char *docString )
	:	GafferBindings::DependencyNodeClass<T, Ptr>( docString )
{
	this->def( "affectsTask", &Detail::TaskNodeAccessor::affectsTask<T> );
	this->def( "preTasks", &Detail::TaskNodeAccessor::preTasks<T> );
	this->def( "postTasks", &Detail::TaskNodeAccessor::postTasks<T> );
	this->def( "hash", &Detail::TaskNodeAccessor::hash<T> );
	this->def( "execute", &Detail::TaskNodeAccessor::execute<T> );
	this->def( "executeSequence", &Detail::TaskNodeAccessor::executeSequence<T> );
	this->def( "requiresSequenceExecution", &Detail::TaskNodeAccessor::requiresSequenceExecution<T> );
}

} // namespace GafferDispatchBindings
