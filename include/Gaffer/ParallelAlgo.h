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

#ifndef GAFFER_PARALLELALGO_H
#define GAFFER_PARALLELALGO_H

#include "Gaffer/Export.h"
#include "Gaffer/Signals.h"

#include <functional>
#include <memory>

namespace Gaffer
{

class BackgroundTask;
class Plug;

namespace ParallelAlgo
{

/// Runs the specified function asynchronously on the main UI thread.
///
/// > Note : This function will throw unless the GafferUI module has
/// > been imported.
///
/// > Caution : If calling a member function, you _must_ guarantee that
/// > the class instance will still be alive when the member function is
/// > called. Typically this means binding `this` via a smart pointer.
using UIThreadFunction = std::function<void ()>;
GAFFER_API void callOnUIThread( const UIThreadFunction &function );

/// Push/pop a handler to service requests made to `callOnUIThread()`. We
/// register the default handler in GafferUI.EventLoop.py.
///
/// > Note : This is an implementation detail. It is only exposed to allow
/// > emulation of the UI in unit tests, and theoretically to allow an
/// > alternative UI framework to be connected.
using UIThreadCallHandler = std::function<void ( const UIThreadFunction & )>;
GAFFER_API void pushUIThreadCallHandler( const UIThreadCallHandler &handler );
GAFFER_API void popUIThreadCallHandler();

/// Runs the specified function asynchronously on a background thread,
/// using a copy of the current Context from the calling thread. This
/// context contains an `IECore::Canceller` controlled by the returned
/// `BackgroundTask`, allowing the background work to be cancelled
/// explicitly. Implicit cancellation is also performed using the `subject`
/// argument : see the `BackgroundTask` documentation for details.
using BackgroundFunction = std::function<void ()>;
GAFFER_API std::unique_ptr<BackgroundTask> callOnBackgroundThread( const Plug *subject, BackgroundFunction function );

} // namespace ParallelAlgo

} // namespace Gaffer

#endif // GAFFER_PARALLELALGO_H
