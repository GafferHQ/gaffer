//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Alex Fuller. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "GafferCycles/IECoreCyclesPreview/Export.h"

#include "IECore/CompoundData.h"

#include <string>

/// This namespace contains all components of the core library.
namespace IECoreCycles
{

/// Returns the value of the `CYCLES_ROOT` environment variable, or
/// and empty string if the variable is not defined.
IECORECYCLES_API const char *cyclesRoot();

/// Initialises the library using the CYCLES_ROOT environment
/// variable, which should point to the root of a Cycles installation.
IECORECYCLES_API bool init();

/// Returns the major version for the IECore library
IECORECYCLES_API int majorVersion();
/// Returns the minor version for the IECore library
IECORECYCLES_API int minorVersion();
/// Returns the patch version for the IECore library
IECORECYCLES_API int patchVersion();
/// Returns a string of the form "major.minor.patch"
IECORECYCLES_API const std::string &versionString();

/// Returns all device data (for python bindings)
IECORECYCLES_API const IECore::CompoundData *devices();
/// Returns all node data (for python bindings)
IECORECYCLES_API const IECore::CompoundData *nodes();
/// Returns all shader data (for python bindings)
IECORECYCLES_API const IECore::CompoundData *shaders();
/// Returns all light data (for python bindings)
IECORECYCLES_API const IECore::CompoundData *lights();
/// Returns all pass data (for python bindings)
IECORECYCLES_API const IECore::CompoundData *passes();
/// Returns if OpenImageDenoise has been compiled in Cycles
IECORECYCLES_API bool openImageDenoiseSupported();
/// Returns if OptixDenoise has been compiled in Cycles
IECORECYCLES_API bool optixDenoiseSupported();

}
