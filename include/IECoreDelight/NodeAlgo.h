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

#ifndef IECOREDELIGHT_NODEALGO_H
#define IECOREDELIGHT_NODEALGO_H

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

/// Converts the specified IECore::Object into an equivalent
/// NSI node with the specified handle, returning true on
/// success and false on failure.
IECOREDELIGHT_API bool convert( const IECore::Object *object, NSIContext_t context, const char *handle );
/// As above, but converting a moving object. If no motion converter
/// is available, the first sample is converted instead.
IECOREDELIGHT_API bool convert( const std::vector<const IECore::Object *> &samples, const std::vector<float> &sampleTimes, NSIContext_t context, const char *handle );

/// Signature of a function which can convert an IECore::Object
/// into an NSI node.
using Converter = bool (*)( const IECore::Object *, NSIContext_t, const char * );
using MotionConverter = bool (*)( const std::vector<const IECore::Object *> &samples, const std::vector<float> &sampleTimes, NSIContext_t constant, const char * );

/// Registers a converter for a specific type.
/// Use the ConverterDescription utility class in preference to
/// this, since it provides additional type safety.
IECOREDELIGHT_API void registerConverter( IECore::TypeId fromType, Converter converter, MotionConverter motionConverter = nullptr );

/// Class which registers a converter for type T automatically
/// when instantiated.
template<typename T>
class ConverterDescription
{

	public :

		/// Type-specific conversion functions.
		using Converter = bool (*)( const T *, NSIContext_t, const char * );
		using MotionConverter = bool (*)( const std::vector<const T *> &, const std::vector<float> &, NSIContext_t, const char * );

		ConverterDescription( Converter converter, MotionConverter motionConverter = nullptr )
		{
			registerConverter(
				T::staticTypeId(),
				reinterpret_cast<NodeAlgo::Converter>( converter ),
				reinterpret_cast<NodeAlgo::MotionConverter>( motionConverter )
			);
		}

};

/// Adds all PrimitiveVariables into a ParameterList for use with NSISetAttribute.
IECOREDELIGHT_API void primitiveVariableParameterList( const IECoreScene::Primitive *primitive, ParameterList &parameters, const IECore::IntVectorData *vertexIndices = nullptr );
/// As above, but splits out animated primitive variables into a separate vector of ParameterLists
/// for use with NSISetAttributeAtTime.
IECOREDELIGHT_API void primitiveVariableParameterLists( const std::vector<const IECoreScene::Primitive *> &primitives, ParameterList &staticParameters, std::vector<ParameterList> &animatedParameters, const IECore::IntVectorData *vertexIndices = nullptr );

} // namespace NodeAlgo

} // namespace IECoreDelight

#endif // IECOREDELIGHT_NODEALGO_H
