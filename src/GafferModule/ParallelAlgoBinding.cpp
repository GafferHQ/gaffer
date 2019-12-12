//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#include "boost/python.hpp"

#include "ParallelAlgoBinding.h"

#include "GafferBindings/SignalBinding.h"

#include "Gaffer/BackgroundTask.h"
#include "Gaffer/ParallelAlgo.h"
#include "Gaffer/Plug.h"

#include "IECorePython/ExceptionAlgo.h"
#include "IECorePython/ScopedGILRelease.h"

using namespace Gaffer;
using namespace GafferBindings;
using namespace boost::python;

namespace
{

BackgroundTask *backgroundTaskConstructor( const Plug *subject, object f )
{
	auto fPtr = std::make_shared<boost::python::object>( f );
	return new BackgroundTask(
		subject,
		[fPtr]( const IECore::Canceller &canceller ) mutable {
			IECorePython::ScopedGILLock gilLock;
			try
			{
				(*fPtr)( boost::ref( canceller ) );
				// We are likely to be the last owner of the python
				// function object. Make sure we release it while we
				// still hold the GIL.
				fPtr.reset();
			}
			catch( boost::python::error_already_set &e )
			{
				fPtr.reset();
				IECorePython::ExceptionAlgo::translatePythonException();
			}
		}
	);
}

void backgroundTaskCancel( BackgroundTask &b )
{
	IECorePython::ScopedGILRelease gilRelease;
	b.cancel();
}

void backgroundTaskWait( BackgroundTask &b )
{
	IECorePython::ScopedGILRelease gilRelease;
	b.wait();
}

bool backgroundTaskWaitFor( BackgroundTask &b, float seconds )
{
	IECorePython::ScopedGILRelease gilRelease;
	return b.waitFor( seconds );
}

void backgroundTaskCancelAndWait( BackgroundTask &b )
{
	IECorePython::ScopedGILRelease gilRelease;
	b.cancelAndWait();
}

BackgroundTask::Status backgroundTaskStatus( const BackgroundTask &b )
{
	IECorePython::ScopedGILRelease gilRelease;
	return b.status();
}

struct GILReleaseUIThreadFunction
{

	GILReleaseUIThreadFunction( ParallelAlgo::UIThreadFunction function )
		:	m_function( function )
	{
	}

	void operator()()
	{
		IECorePython::ScopedGILRelease gilRelease;
		m_function();
	}

	private :

		ParallelAlgo::UIThreadFunction m_function;

};

void callOnUIThread( boost::python::object f )
{
	auto fPtr = std::make_shared<boost::python::object>( f );

	IECorePython::ScopedGILRelease gilRelease;

	Gaffer::ParallelAlgo::callOnUIThread(
		[fPtr]() mutable {
			IECorePython::ScopedGILLock gilLock;
			try
			{
				(*fPtr)();
				// We are likely to be the last owner of the python
				// function object. Make sure we release it while we
				// still hold the GIL.
				fPtr.reset();
			}
			catch( boost::python::error_already_set &e )
			{
				fPtr.reset();
				IECorePython::ExceptionAlgo::translatePythonException();
			}
		}
	);
}

void pushUIThreadCallHandler( boost::python::object handler )
{
	// The lambda below needs to own a reference to `handler`,
	// and in turn will be owned by the ParallelAlgo C++ API.
	// Wrap `handler` so we acquire the GIL when the lambda is
	// destroyed from C++.
	auto handlerPtr = std::shared_ptr<boost::python::object>(
		new boost::python::object( handler ),
		[]( boost::python::object *o ) {
			IECorePython::ScopedGILLock gilLock;
			delete o;
		}
	);

	IECorePython::ScopedGILRelease gilRelease;

	Gaffer::ParallelAlgo::pushUIThreadCallHandler(
		[handlerPtr] ( const ParallelAlgo::UIThreadFunction &function ) {
			IECorePython::ScopedGILLock gilLock;
			boost::python::object pythonFunction = make_function(
				GILReleaseUIThreadFunction( function ),
				boost::python::default_call_policies(),
				boost::mpl::vector<void>()
			);
			(*handlerPtr)( pythonFunction );
		}
	);
}

void popUIThreadCallHandler()
{
	IECorePython::ScopedGILRelease gilRelease;
	ParallelAlgo::popUIThreadCallHandler();
}

std::shared_ptr<BackgroundTask> callOnBackgroundThread( const Plug *subject, boost::python::object f )
{
	// The BackgroundTask we return will own the python function we
	// pass to it. Wrap the function so that the GIL is acquired
	// before the python object is destroyed.
	auto fPtr = std::shared_ptr<boost::python::object>(
		new boost::python::object( f ),
		[]( boost::python::object *o ) {
			IECorePython::ScopedGILLock gilLock;
			delete o;
		}
	);

	auto backgroundTask = ParallelAlgo::callOnBackgroundThread(
		subject,
		[fPtr]() mutable {
			IECorePython::ScopedGILLock gilLock;
			try
			{
				(*fPtr)();
			}
			catch( boost::python::error_already_set &e )
			{
				IECorePython::ExceptionAlgo::translatePythonException();
			}
		}
	);

	return std::shared_ptr<BackgroundTask>(
		backgroundTask.release(),
		// Custom deleter. We need to release
		// the GIL when deleting, because the destructor
		// waits on the background task, and the background
		// task might need the GIL in order to complete.
		[]( BackgroundTask *t ) {
			IECorePython::ScopedGILRelease gilRelease;
			delete t;
		}
	);
}

} // namespace

void GafferModule::bindParallelAlgo()
{

	{
		scope s = class_<BackgroundTask, boost::noncopyable>( "BackgroundTask", no_init )
			.def( "__init__", make_constructor( &backgroundTaskConstructor, default_call_policies() ) )
			.def( "cancel", &backgroundTaskCancel )
			.def( "wait", &backgroundTaskWait )
			.def( "waitFor", &backgroundTaskWaitFor )
			.def( "cancelAndWait", &backgroundTaskCancelAndWait )
			.def( "status", &backgroundTaskStatus )
		;

		enum_<BackgroundTask::Status>( "Status" )
			.value( "Pending", BackgroundTask::Pending )
			.value( "Running", BackgroundTask::Running )
			.value( "Completed", BackgroundTask::Completed )
			.value( "Cancelled", BackgroundTask::Cancelled )
			.value( "Errored", BackgroundTask::Errored )
		;
	}

	register_ptr_to_python<std::shared_ptr<BackgroundTask>>();

	object module( borrowed( PyImport_AddModule( "Gaffer.ParallelAlgo" ) ) );
	scope().attr( "ParallelAlgo" ) = module;
	scope moduleScope( module );

	def( "callOnUIThread", &callOnUIThread );
	def( "pushUIThreadCallHandler", &pushUIThreadCallHandler );
	def( "popUIThreadCallHandler", &popUIThreadCallHandler );
	def( "callOnBackgroundThread", &callOnBackgroundThread );

}
