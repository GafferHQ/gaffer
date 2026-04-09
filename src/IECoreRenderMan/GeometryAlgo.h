//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, John Haddon. All rights reserved.
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

#include "IECoreScene/Primitive.h"

#include "IECore/Object.h"
#include "IECore/VectorTypedData.h"

#include "RiTypesHelper.h"

#include <vector>

namespace IECoreRenderMan::GeometryAlgo
{

/// Geometry conversion
/// ===================

/// Converts the specified `IECore::Object` samples into arguments for
/// `Riley::CreateGeometryPrototype()`. Fills `primVars` and returns the
/// geometry `type`. Returns an empty string if no converter is available.
RtUString convert( const IECoreScenePreview::Renderer::ObjectSamples &samples, const IECoreScenePreview::Renderer::SampleTimes &sampleTimes, RtPrimVarList &primVars, const std::string &messageContext = "GeometryAlgo::convert" );

/// Signature of a function which implements `convert()` for a particular type.
using Converter = std::function<RtUString ( const IECoreScenePreview::Renderer::ObjectSamples &samples, const IECoreScenePreview::Renderer::SampleTimes &sampleTimes, RtPrimVarList &primVars, const std::string &messageContext )>;

/// Registers a converter for a specific type. Use the ConverterDescription
/// utility class in preference to this, since it provides additional type
/// safety.
void registerConverter( IECore::TypeId fromType, Converter converter );

/// Class which registers a converter for type T automatically
/// when instantiated.
template<typename T>
class ConverterDescription
{

	public :

		/// Type-specific conversion functions.
		using TypedObjectSamples = IECoreScenePreview::Renderer::Samples<const T *>;
		using TypedConverter = RtUString (*)( const TypedObjectSamples &samples, const IECoreScenePreview::Renderer::SampleTimes &sampleTimes, RtPrimVarList &primVars, const std::string &messageContext );

		ConverterDescription( TypedConverter converter )
		{
			registerConverter(
				T::staticTypeId(),
				[converter] ( const IECoreScenePreview::Renderer::ObjectSamples &samples, const IECoreScenePreview::Renderer::SampleTimes &sampleTimes, RtPrimVarList &primVars, const std::string &messageContext )
				{
					return converter( IECoreScenePreview::Renderer::staticSamplesCast<const T *>( samples ), sampleTimes, primVars, messageContext );
				}
			);
		}

};

/// Primitive conversion helpers
/// ============================

using PrimitiveSamples = IECoreScenePreview::Renderer::Samples<const IECoreScene::Primitive *>;

/// Primitive converters should call this function before doing their own type-specific conversion.
void convertPrimitive( const PrimitiveSamples &samples, const IECoreScenePreview::Renderer::SampleTimes &sampleTimes, RtPrimVarList &primVarList, const std::string &messageContext );

} // namespace IECoreRenderMan::GeometryAlgo
