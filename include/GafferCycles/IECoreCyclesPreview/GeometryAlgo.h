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

#include "GafferCycles/IECoreCyclesPreview/Export.h"

#include "IECoreScene/PrimitiveVariable.h"

#include "IECore/Object.h"

#include "IECoreVDB/VDBObject.h"

#include <vector>

// Cycles
IECORE_PUSH_DEFAULT_VISIBILITY
#include "scene/geometry.h"
#include "scene/volume.h"
// Currently only VDBs need scene to get to the image manager
#include "scene/scene.h"
IECORE_POP_DEFAULT_VISIBILITY

namespace IECoreCycles
{

namespace GeometryAlgo
{

/// Converts the specified `IECore::Object` into `ccl::Geometry`.
IECORECYCLES_API ccl::Geometry *convert( const IECore::Object *object, const std::string &nodeName );
/// As above, but converting a moving object. If no motion converter
/// is available, the first sample is converted instead.
IECORECYCLES_API ccl::Geometry *convert( const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const int frame, const std::string &nodeName );

/// Converts a primitive variable to a `ccl::Attribute` inside of a `ccl::AttributeSet`.
IECORECYCLES_API void convertPrimitiveVariable( const std::string &name, const IECoreScene::PrimitiveVariable &primitiveVariable, ccl::AttributeSet &attributes, ccl::AttributeElement attributeElement );

/// Converts voxel grids from a VDB object.
IECORECYCLES_API void convertVoxelGrids( const IECoreVDB::VDBObject *vdbObject, ccl::Volume *geometry, ccl::Scene *scene, const float frame = 0.0f, const int precision_ = 0 );

/// Signature of a function which can convert to `ccl:Geometry`.
/// \todo There's really no need to pass the node name here, because it's not a unique handle that
/// needs to be provided when creating the Geometry (like it is in Arnold). The caller can just set the name
/// afterwards if they want to.
using Converter = ccl::Geometry *(*)( const IECore::Object *, const std::string & );
/// Signature of a function which can convert a series of IECore::Object
/// samples into a moving `ccl:Geometry` object.
using MotionConverter = ccl::Geometry *(*)( const std::vector<const IECore::Object *> &, const std::vector<float> &, const int, const std::string & );

/// Registers a converter for a specific type.
/// Use the ConverterDescription utility class in preference to
/// this, since it provides additional type safety.
IECORECYCLES_API void registerConverter( IECore::TypeId fromType, Converter converter, MotionConverter motionConverter = nullptr );

/// Class which registers a converter for type T automatically
/// when instantiated.
template<typename T>
class ConverterDescription
{

	public :

		/// Type-specific conversion functions.
		using Converter = ccl::Geometry *(*)( const T *, const std::string & );
		using MotionConverter = ccl::Geometry *(*)( const std::vector<const T *> &, const std::vector<float> &, const int, const std::string & );

		ConverterDescription( Converter converter, MotionConverter motionConverter = nullptr )
		{
			registerConverter(
				T::staticTypeId(),
				reinterpret_cast<GeometryAlgo::Converter>( converter ),
				reinterpret_cast<GeometryAlgo::MotionConverter>( motionConverter )
			);
		}

};

} // namespace GeometryAlgo

} // namespace IECoreCycles
