//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFERBINDINGS_EXCEPTIONALGO_H
#define GAFFERBINDINGS_EXCEPTIONALGO_H

#include "GafferBindings/Export.h"

namespace GafferBindings
{

namespace ExceptionAlgo
{

/// Formats the current python exception using the traceback module,
/// and returns it in the form of a string. If lineNumber is provided, it
/// will be filled with the number of the line where the error occurred.
GAFFERBINDINGS_API std::string formatPythonException( bool withStacktrace = true, int *lineNumber = NULL );

/// Can be called to translate the current python exception into
/// an IECore::Exception. Typically this would be called after catching
/// boost::python::error_already_set.
/// \todo Maybe this should be moved to IECorePython?
GAFFERBINDINGS_API void translatePythonException( bool withStacktrace = true );

} // namespace ExceptionAlgo

/// \todo Remove this temporary backwards compatibility.
using namespace ExceptionAlgo;

} // namespace GafferBindings

#endif // GAFFERBINDINGS_EXCEPTIONALGO_H
