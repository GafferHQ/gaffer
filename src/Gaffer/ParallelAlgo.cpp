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

#include "Gaffer/ParallelAlgo.h"

#include "Gaffer/BackgroundTask.h"
#include "Gaffer/Context.h"
#include "Gaffer/Monitor.h"

#include <mutex>
#include <stack>

using namespace Gaffer;

namespace
{

using UIThreadCallHandlers = std::stack<ParallelAlgo::UIThreadCallHandler>;

std::unique_lock<std::mutex> lockUIThreadCallHandlers( UIThreadCallHandlers *&handlers )
{
	static std::mutex g_mutex;
	static UIThreadCallHandlers g_handlers;
	handlers = &g_handlers;
	return std::unique_lock<std::mutex>( g_mutex );
}

} // namespace

void ParallelAlgo::callOnUIThread( const UIThreadFunction &function )
{
	UIThreadCallHandlers *handlers = nullptr;
	UIThreadCallHandler h;

	{
		auto lock = lockUIThreadCallHandlers( handlers );
		if( handlers->size() )
		{
			h = handlers->top();
		}
		else
		{
			IECore::msg( IECore::Msg::Error, "ParallelAlgo::callOnUIThread", "No UIThreadCallHandler installed" );
			return;
		}
	}

	h( function );
}

void ParallelAlgo::pushUIThreadCallHandler( const UIThreadCallHandler &handler )
{
	UIThreadCallHandlers *handlers = nullptr;
	auto lock = lockUIThreadCallHandlers( handlers );
	handlers->push( handler );
}

void ParallelAlgo::popUIThreadCallHandler()
{
	UIThreadCallHandlers *handlers = nullptr;
	auto lock = lockUIThreadCallHandlers( handlers );
	if( handlers->size() )
	{
		handlers->pop();
	}
	else
	{
		throw IECore::Exception( "No UIThreadCallHandler to pop" );
	}
}

GAFFER_API std::unique_ptr<BackgroundTask> ParallelAlgo::callOnBackgroundThread( const Plug *subject, BackgroundFunction function )
{
	ContextPtr backgroundContext = new Context( *Context::current() );
	Monitor::MonitorSet backgroundMonitors = Monitor::current();

	return std::make_unique<BackgroundTask>(

		subject,

		[backgroundContext, backgroundMonitors, function] ( const IECore::Canceller &canceller ) {

			Context::EditableScope contextScope( backgroundContext.get() );
			contextScope.setCanceller( &canceller );
			Monitor::Scope monitorScope( backgroundMonitors );

			function();

		}

	);
}
