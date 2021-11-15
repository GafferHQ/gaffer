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

#ifndef IECOREARNOLD_NODEALGO_H
#define IECOREARNOLD_NODEALGO_H

#include "IECoreArnold/Export.h"

#include "IECore/Object.h"

#include "ai_nodes.h"

namespace IECoreArnold
{

namespace NodeAlgo
{

/// Converts the specified IECore::Object into an equivalent
/// Arnold object, returning nullptr if no conversion is
/// available.
IECOREARNOLD_API AtNode *convert( const IECore::Object *object, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode = nullptr );
/// Converts the specified IECore::Object samples into an
/// equivalent moving Arnold object. If no motion converter
/// is available, then returns a standard conversion of the
/// first sample.
IECOREARNOLD_API AtNode *convert( const std::vector<const IECore::Object *> &samples, float motionStart, float motionEnd, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode = nullptr );

/// Signature of a function which can convert an IECore::Object
/// into an Arnold object.
typedef AtNode * (*Converter)( const IECore::Object *, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode );
/// Signature of a function which can convert a series of IECore::Object
/// samples into a moving Arnold object.
typedef AtNode * (*MotionConverter)( const std::vector<const IECore::Object *> &samples, float motionStart, float motionEnd, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode );

/// Registers a converter for a specific type.
/// Use the ConverterDescription utility class in preference to
/// this, since it provides additional type safety.
IECOREARNOLD_API void registerConverter( IECore::TypeId fromType, Converter converter, MotionConverter motionConverter = nullptr );

/// Class which registers a converter for type T automatically
/// when instantiated.
template<typename T>
class ConverterDescription
{

	public :

		/// Type-specific conversion functions.
		typedef AtNode *(*Converter)( const T *, AtUniverse *, const std::string&, const AtNode* );
		typedef AtNode *(*MotionConverter)( const std::vector<const T *> &, float, float, AtUniverse *, const std::string&, const AtNode* );

		ConverterDescription( Converter converter, MotionConverter motionConverter = nullptr )
		{
			registerConverter(
				T::staticTypeId(),
				reinterpret_cast<NodeAlgo::Converter>( converter ),
				reinterpret_cast<NodeAlgo::MotionConverter>( motionConverter )
			);
		}

};

} // namespace NodeAlgo

} // namespace IECoreArnold

#endif // IECOREARNOLD_NODEALGO_H
