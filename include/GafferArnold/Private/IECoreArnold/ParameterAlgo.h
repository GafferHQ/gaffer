//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#ifndef IECOREARNOLD_PARAMETERALGO_H
#define IECOREARNOLD_PARAMETERALGO_H

#include "GafferArnold/Export.h"

#include "IECore/CompoundData.h"

#include "ai.h"

namespace IECoreArnold
{

namespace ParameterAlgo
{

GAFFERARNOLD_API void setParameter( AtNode *node, const AtParamEntry *parameter, const IECore::Data *value );
GAFFERARNOLD_API void setParameter( AtNode *node, AtString name, const IECore::Data *value );
GAFFERARNOLD_API void setParameter( AtNode *node, const char *name, const IECore::Data *value );
GAFFERARNOLD_API void setParameters( AtNode *node, const IECore::CompoundDataMap &values );

GAFFERARNOLD_API IECore::DataPtr getParameter( AtNode *node, const AtParamEntry *parameter );
GAFFERARNOLD_API IECore::DataPtr getParameter( AtNode *node, const AtUserParamEntry *parameter );
GAFFERARNOLD_API IECore::DataPtr getParameter( AtNode *node, AtString name );
GAFFERARNOLD_API IECore::DataPtr getParameter( AtNode *node, const char *name );
GAFFERARNOLD_API void getParameters( AtNode *node, IECore::CompoundDataMap &values );

/// Returns the Arnold parameter type (AI_TYPE_INT etc) suitable for
/// storing Cortex data of the specified type, setting array to true
/// or false depending on whether or not the Arnold type will be an
/// array. Returns AI_TYPE_NONE if there is no suitable Arnold type.
GAFFERARNOLD_API int parameterType( IECore::TypeId dataType, bool &array );
GAFFERARNOLD_API int parameterType( const IECore::Data *data, bool &array );

/// If the equivalent Arnold type for the data is already known, then it may be passed directly.
/// If not it will be inferred using parameterType().
GAFFERARNOLD_API AtArray *dataToArray( const IECore::Data *data, int aiType = AI_TYPE_NONE );
GAFFERARNOLD_API AtArray *dataToArray( const std::vector<const IECore::Data *> &samples, int aiType = AI_TYPE_NONE );

} // namespace ParameterAlgo

} // namespace IECoreArnold

#endif // IECOREARNOLD_PARAMETERALGO_H
