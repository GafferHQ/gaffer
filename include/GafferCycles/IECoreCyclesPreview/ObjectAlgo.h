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

#ifndef IECORECYCLES_OBJECTALGO_H
#define IECORECYCLES_OBJECTALGO_H

#include "GafferCycles/IECoreCyclesPreview/Export.h"

#include "IECore/Object.h"

#include <vector>

// Cycles
#include "render/object.h"
// Currently only VDBs need scene to get to the image manager
#include "render/scene.h"

namespace IECoreCycles
{

namespace ObjectAlgo
{

/// A Cycles 'Object' is not necessarily a global thing for all objects, hence why Camera and Lights
/// are treated separately. They all however subclass from ccl::Node so they all are compatible with
/// Cycles' internal Node/Socket API to form connections or apply parameters.

/// Converts the specified IECore::Object into a ccl::Object.
IECORECYCLES_API ccl::Object *convert( const IECore::Object *object, const std::string &nodeName, ccl::Scene *scene = nullptr );
/// As above, but converting a moving object. If no motion converter
/// is available, the first sample is converted instead.
IECORECYCLES_API ccl::Object *convert( const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const int frame, const std::string &nodeName, ccl::Scene *scene = nullptr );

/// Signature of a function which can convert into a Cycles Object.
typedef ccl::Object * (*Converter)( const IECore::Object *, const std::string &nodeName, ccl::Scene *scene );
/// Signature of a function which can convert a series of IECore::Object
/// samples into a moving Cycles object.
typedef ccl::Object * (*MotionConverter)( const std::vector<const IECore::Object *> &samples, const std::vector<float> &times, const int frameIdx, const std::string &nodeName, ccl::Scene *scene );

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
		typedef ccl::Object *(*Converter)( const T *, const std::string&, ccl::Scene* );
		typedef ccl::Object *(*MotionConverter)( const std::vector<const T *> &, const std::vector<float> &, const int, const std::string&, ccl::Scene* );

		ConverterDescription( Converter converter, MotionConverter motionConverter = nullptr )
		{
			registerConverter(
				T::staticTypeId(),
				reinterpret_cast<ObjectAlgo::Converter>( converter ),
				reinterpret_cast<ObjectAlgo::MotionConverter>( motionConverter )
			);
		}

};

} // namespace ObjectAlgo

} // namespace IECoreCycles

#endif // IECORECYCLES_OBJECTALGO_H
