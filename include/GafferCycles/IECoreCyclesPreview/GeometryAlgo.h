//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Alex Fuller. All rights reserved.
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

#include "GafferCycles/IECoreCyclesPreview/Export.h"

#include "IECoreScene/Primitive.h"
#include "IECoreScene/PrimitiveVariable.h"

#include "IECore/Object.h"

#include "IECoreVDB/VDBObject.h"

#include <vector>

// Cycles
IECORE_PUSH_DEFAULT_VISIBILITY
#include "scene/geometry.h"
#include "scene/volume.h"
#include "scene/scene.h"
#include "session/session.h"
IECORE_POP_DEFAULT_VISIBILITY

namespace IECoreCycles
{

namespace GeometryAlgo
{

/// Converts animated samples of an `IECore::Object` into an equivalent `ccl::Geometry` object.
IECORECYCLES_API ccl::Geometry *convert( const IECoreScenePreview::Renderer::ObjectSamples &samples, const IECoreScenePreview::Renderer::SampleTimes &times, ccl::Scene *scene );

/// Converts a primitive variable to a `ccl::Attribute` inside of a `ccl::AttributeSet`.
IECORECYCLES_API void convertPrimitiveVariable( const std::string &name, const IECoreScene::PrimitiveVariable &primitiveVariable, ccl::AttributeSet &attributes, ccl::AttributeElement attributeElement );

/// Converts motion for "P" primitive variable.
IECORECYCLES_API void convertMotion( const IECoreScenePreview::Renderer::Samples<const IECoreScene::Primitive *> &samples, size_t primarySampleIndex, ccl::Geometry &geometry );

/// Converts voxel grids from a VDB object.
IECORECYCLES_API void convertVoxelGrids( const IECoreVDB::VDBObject *vdbObject, ccl::Volume *geometry, ccl::Scene *scene, int precision, float clipping );

/// Signature of a function which can convert a series of `IECore::Object`
/// samples into a moving `ccl:Geometry` object. The `primarySampleIndex`
/// argument indicates which sample should be used for the main conversion, and
/// the converter should defer to `convertMotion()` to convert the positions of
/// the remaining motion samples to ATTR_STD_MOTION_VERTEX_POSITION.
using Converter = std::function<ccl::Geometry *( const IECoreScenePreview::Renderer::ObjectSamples &samples, const IECoreScenePreview::Renderer::SampleTimes &times, size_t primarySampleIndex, ccl::Scene *scene )>;

/// Registers a converter for a specific type.
/// Use the ConverterDescription utility class in preference to
/// this, since it provides additional type safety.
IECORECYCLES_API void registerConverter( IECore::TypeId fromType, Converter converter );

/// Class which registers a converter for type T automatically
/// when instantiated.
template<typename T>
class ConverterDescription
{

	public :

		/// Type-specific conversion function.
		using TypedSamples = IECoreScenePreview::Renderer::Samples<const T *>;
		using TypedConverter = ccl::Geometry *(*)( const TypedSamples &, const IECoreScenePreview::Renderer::SampleTimes &, size_t, ccl::Scene * );

		ConverterDescription( TypedConverter converter )
		{
			registerConverter(
				T::staticTypeId(),
				[converter] ( const IECoreScenePreview::Renderer::ObjectSamples &samples, const IECoreScenePreview::Renderer::SampleTimes &times, size_t primarySampleIndex, ccl::Scene *scene )
				{
					return converter( IECoreScenePreview::Renderer::staticSamplesCast<const T *>( samples ), times, primarySampleIndex, scene );
				}
			);
		}

};

} // namespace GeometryAlgo

} // namespace IECoreCycles
