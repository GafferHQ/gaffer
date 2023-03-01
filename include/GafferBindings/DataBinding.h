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

#include "boost/python.hpp"

#include "GafferBindings/Export.h"

#include "IECore/Data.h"

namespace GafferBindings
{

/// Converts an IECore::Data instance to Python. Simple data is "unwrapped" and
/// returned as an instance of the internal type. For instance, Color3fData is
/// converted to Color3f. This avoids the unintuitive hoop jumping of using the
/// .value field in python all the time. Vector data and all other complex types
/// are simply returned as they are, on the grounds that there's not a better type
/// to represent them in Python.
/// \todo It might be too late, but consider how this could be put to use
/// in Cortex itself.
GAFFERBINDINGS_API boost::python::object dataToPython( IECore::Data *data, boost::python::object nullValue = boost::python::object() );
/// As above, but since the data is const (and python has no const), requiring
/// an argument specifying whether or not to copy the data.
GAFFERBINDINGS_API boost::python::object dataToPython( const IECore::Data *data, bool copy, boost::python::object nullValue = boost::python::object() );

} // namespace GafferBindings
