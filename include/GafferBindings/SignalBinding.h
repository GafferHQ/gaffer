//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERBINDINGS_SIGNALBINDING_H
#define GAFFERBINDINGS_SIGNALBINDING_H

#include "boost/python.hpp"

#include "GafferBindings/Export.h"
#include "GafferBindings/ConnectionBinding.h"

namespace GafferBindings
{

template<typename Signal>
struct DefaultSignalCaller;

template<typename Signal>
struct DefaultSlotCaller;

/// This template class is used to bind boost::signal types specified
/// by the Signal template parameter. The SignalCaller template parameter is
/// a struct type which has a static call() method which can take arguments
/// from python and call the signal. The SlotCaller template parameter is
/// a functor type which is used to call the python objects which are connected
/// to the signal as slots.
template<typename Signal, typename SignalCaller=DefaultSignalCaller<Signal>, typename SlotCaller=DefaultSlotCaller<Signal> >
class SignalClass : public boost::python::class_<Signal, boost::noncopyable>
{

	public :

		SignalClass( const char *className, const char *docString = NULL );

};

/// This function binds a series of generic signals taking and returning python objects, with
/// combiners being provided as python callables.
GAFFERBINDINGS_API void bindSignal();

} // namespace GafferBindings

#include "GafferBindings/SignalBinding.inl"

#endif // GAFFERBINDINGS_SIGNALBINDING_H
