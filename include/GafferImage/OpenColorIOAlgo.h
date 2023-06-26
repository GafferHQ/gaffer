//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferImage/Export.h"

#include "Gaffer/Context.h"

#include "OpenColorIO/OpenColorTypes.h"

namespace GafferImage
{

namespace OpenColorIOAlgo
{

/// Specifying an OpenColorIO Config
/// ================================
///
/// The OpenColorIO config used by Gaffer is specified using the Gaffer context.
/// These functions are used to define that config.

/// Sets the config to use in `context`. If the filename is empty, the config
/// specified by the `$OCIO` environment variable will be used instead.
GAFFERIMAGE_API void setConfig( Gaffer::Context *context, const std::string &configFileName );
GAFFERIMAGE_API void setConfig( Gaffer::Context::EditableScope &context, const std::string *configFileName );
GAFFERIMAGE_API const std::string &getConfig( const Gaffer::Context *context );

/// Sets the colour space in which GafferImage stores colours for processing. Defaults to the `scene_linear` role.
GAFFERIMAGE_API void setWorkingSpace( Gaffer::Context *context, const std::string &colorSpace );
GAFFERIMAGE_API void setWorkingSpace( Gaffer::Context::EditableScope &context, const std::string *colorSpace );
GAFFERIMAGE_API const std::string &getWorkingSpace( const Gaffer::Context *context );

/// Adds an OCIO "string var" to be used in `context`. Note that OCIO also calls these
/// "environment vars" and "context vars" but they're all the same thing.
GAFFERIMAGE_API void addVariable( Gaffer::Context *context, const std::string &name, const std::string &value );
GAFFERIMAGE_API void addVariable( Gaffer::Context::EditableScope &context, const std::string &name, const std::string *value );
/// Gets the value of an OCIO "string var".
GAFFERIMAGE_API const std::string &getVariable( const Gaffer::Context *context, const std::string &name );
/// Removes an OCIO "string var".
GAFFERIMAGE_API void removeVariable( Gaffer::Context *context, const std::string &name );
GAFFERIMAGE_API void removeVariable( Gaffer::Context::EditableScope &context, const std::string &name );
/// Returns a list of the OCIO variables in the context.
GAFFERIMAGE_API std::vector<std::string> variables( const Gaffer::Context *context );

/// Acquiring an OpenColorIO Config
/// ===============================
///
/// These functions return OCIO Configs and Contexts as defined by the current Gaffer context.

using ConfigAndContext = std::pair<OCIO_NAMESPACE::ConstConfigRcPtr, OCIO_NAMESPACE::ConstContextRcPtr>;

GAFFERIMAGE_API OCIO_NAMESPACE::ConstConfigRcPtr currentConfig();
GAFFERIMAGE_API IECore::MurmurHash currentConfigHash();
GAFFERIMAGE_API ConfigAndContext currentConfigAndContext();
GAFFERIMAGE_API IECore::MurmurHash currentConfigAndContextHash();

} // namespace OpenColorIOAlgo

} // namespace GafferImageU
