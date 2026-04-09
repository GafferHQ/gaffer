//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, John Haddon. All rights reserved.
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

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "IECoreDelight/Export.h"

#include "IECoreScene/Primitive.h"

#include "IECore/Object.h"
#include "IECore/VectorTypedData.h"

#include <vector>

#include <nsi.h>

namespace IECoreDelight
{

class ParameterList;

namespace NodeAlgo
{

/// Converts the specified `IECore::Object` samples into an equivalent
/// NSI node with the specified handle, returning true on
/// success and false on failure.
IECOREDELIGHT_API bool convert( const IECoreScenePreview::Renderer::ObjectSamples &samples, const IECoreScenePreview::Renderer::SampleTimes &sampleTimes, NSIContext_t context, const char *handle );

/// Signature of a function which can convert `IECore::Object` samples into an
/// NSI node.
using Converter = std::function<bool ( const IECoreScenePreview::Renderer::ObjectSamples &samples, const IECoreScenePreview::Renderer::SampleTimes &sampleTimes, NSIContext_t context, const char *handle )>;

/// Registers a converter for a specific type.
/// Use the ConverterDescription utility class in preference to
/// this, since it provides additional type safety.
IECOREDELIGHT_API void registerConverter( IECore::TypeId fromType, Converter converter );

/// Class which registers a converter for type T automatically
/// when instantiated.
template<typename T>
class ConverterDescription
{

	public :

		/// Type-specific conversion functions.
		using TypedSamples = IECoreScenePreview::Renderer::Samples<const T *>;
		using TypedConverter = bool (*)( const TypedSamples &, const IECoreScenePreview::Renderer::SampleTimes &, NSIContext_t, const char * );

		ConverterDescription( TypedConverter converter )
		{
			registerConverter(
				T::staticTypeId(),
				[converter] ( const IECoreScenePreview::Renderer::ObjectSamples &samples, const IECoreScenePreview::Renderer::SampleTimes &times, NSIContext_t context, const char *handle )
				{
					return converter( IECoreScenePreview::Renderer::staticSamplesCast<const T *>( samples ), times, context, handle );
				}
			);
		}

};

/// Adds all static PrimitiveVariables into a ParameterList for use with
/// `NSISetAttribute()`, and all animated PrimitiveVariables into a separate vector
/// of ParameterLists for use with `NSISetAttributeAtTime()`.
IECOREDELIGHT_API void primitiveVariableParameterLists( const IECoreScenePreview::Renderer::Samples<const IECoreScene::Primitive *> &primitives, ParameterList &staticParameters, std::vector<ParameterList> &animatedParameters, const IECore::IntVectorData *vertexIndices = nullptr );

} // namespace NodeAlgo

} // namespace IECoreDelight
