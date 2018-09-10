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

#ifndef IECORECYCLES_NODEALGO_H
#define IECORECYCLES_NODEALGO_H

#include <vector>

// Cycles
#include "render/camera.h"
#include "render/mesh.h"
#include "render/object.h"
#include "render/light.h"

#include "IECoreScene/Camera.h"

#include "IECore/Object.h"

// Change this to "IECoreCycles/Export.h" and remove the define when it goes into Cortex.
#include "GafferCycles/Export.h"
#define IECORECYCLES_API GAFFERCYCLES_API

namespace IECoreCycles
{

namespace NodeAlgo
{

/// A Cycles 'Object' is not necessarily a global thing for all objects, hence why Camera and Lights
/// are treated separately. They all however subclass from ccl::Node so they all are compatible with
/// Cycles' internal Node/Socket API to form connections or apply parameters.

/// Converts the specified IECoreScene::Camera into a ccl::Camera.
IECORECYCLES_API ccl::Camera *convert( const IECore::Object *object, const std::string &nodeName );
/// As above, but converting a moving object. If no motion converter
/// is available, the first sample is converted instead.
IECORECYCLES_API ccl::Camera *convert( const std::vector<const IECore::Object *> &samples, const std::string &nodeName );

/// Converts the specified IECoreScene::Light into a ccl::Light.
IECORECYCLES_API ccl::Light  *convert( const IECore::Object *object, const std::string &nodeName );
/// As above, but converting a moving object. If no motion converter
/// is available, the first sample is converted instead.
IECORECYCLES_API ccl::Light  *convert( const std::vector<const IECore::Object *> &samples, const std::string &nodeName );

/// Converts the specified IECoreScene::MeshPrimitive or CurvesPrimitive into a ccl::Mesh.
IECORECYCLES_API ccl::Mesh   *convert( const IECore::Object *object, const std::string &nodeName );
/// As above, but converting a moving object. If no motion converter
/// is available, the first sample is converted instead.
IECORECYCLES_API ccl::Mesh   *convert( const std::vector<const IECore::Object *> &samples, const std::string &nodeName );

/// Signature of a function which can convert into a Cycles Object/Node.
typedef ccl::Camera * (*Converter)( const IECore::Object *, const std::string &nodeName );
typedef ccl::Camera * (*MotionConverter)( const std::vector<const IECore::Object *> &samples, const std::string &nodeName );
typedef ccl::Light  * (*Converter)( const IECore::Object *, const std::string &nodeName );
typedef ccl::Light  * (*MotionConverter)( const std::vector<const IECore::Object *> &samples, const std::string &nodeName );
typedef ccl::Mesh   * (*Converter)( const IECore::Object *, const std::string &nodeName );
typedef ccl::Mesh   * (*MotionConverter)( const std::vector<const IECore::Object *> &samples, const std::string &nodeName );

/// Registers a converter for a specific type.
/// Use the ConverterDescription utility class in preference to
/// this, since it provides additional type safety.
IECORECYCLES_API void registerConverter( IECore::TypeId fromType, Converter converter, MotionConverter motionConverter = nullptr );

/// Class which registers a converter for type U to type T automatically
/// when instantiated.
template<typename T, U>
class ConverterDescription
{

	public :

		/// Type-specific conversion functions.
		typedef T * (*Converter)( const U *, const std::string& );
		typedef T * (*MotionConverter)( const std::vector<const U *> &, const std::string& );

		ConverterDescription( Converter converter, MotionConverter motionConverter = nullptr )
		{
			registerConverter(
				U::staticTypeId(),
				reinterpret_cast<NodeAlgo::Converter>( converter ),
				reinterpret_cast<NodeAlgo::MotionConverter>( motionConverter )
			);
		}

};

} // namespace NodeAlgo

} // namespace IECoreCycles

#endif // IECORECYCLES_NODEALGO_H
