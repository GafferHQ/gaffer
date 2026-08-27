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

#pragma once

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "IECoreArnold/Export.h"

#include "IECore/Object.h"

#include "ai_nodes.h"

namespace IECoreArnold
{

namespace NodeAlgo
{

/// Converts the specified IECore::Object samples into an
/// equivalent moving Arnold object. If no motion converter
/// is available, then returns a standard conversion of the
/// first sample.
IECOREARNOLD_API AtNode *convert( const IECoreScenePreview::Renderer::ObjectSamples &samples, float motionStart, float motionEnd, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode = nullptr, const std::string &messageContext = "NodeAlgo::convert" );
/// Convenience function for the case of a single sample.
IECOREARNOLD_API AtNode *convert( const IECore::Object *object, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode = nullptr, const std::string &messageContext = "NodeAlgo::convert" );

/// Signature of a function which can convert a `IECore::Objects`
/// into Arnold nodes.
using Converter = std::function<AtNode *( const IECoreScenePreview::Renderer::ObjectSamples &samples, float motionStart, float motionEnd, AtUniverse *universe, const std::string &nodeName, const AtNode *parent, const std::string &messageContext )>;

/// Registers a converter for a specific type.
/// Use the ConverterDescription utility class in preference to
/// this, since it provides additional type safety.
IECOREARNOLD_API void registerConverter( IECore::TypeId fromType, Converter converter );

/// Class which registers a converter for type T automatically
/// when instantiated.
template<typename T>
class ConverterDescription
{

	public :

		/// Type-specific conversion functions.
		using TypedObjectSamples = IECoreScenePreview::Renderer::Samples<const T *>;
		using TypedConverter = AtNode *(*)( const TypedObjectSamples &, float, float, AtUniverse *, const std::string &, const AtNode *, const std::string & );

		ConverterDescription( TypedConverter converter )
		{
			registerConverter(
				T::staticTypeId(),
				[converter] ( const IECoreScenePreview::Renderer::ObjectSamples &samples, float motionStart, float motionEnd, AtUniverse *universe, const std::string &nodeName, const AtNode *parent, const std::string &messageContext )
				{
					return converter( IECoreScenePreview::Renderer::staticSamplesCast<const T *>( samples ), motionStart, motionEnd, universe, nodeName, parent, messageContext );
				}
			);
		}

};

} // namespace NodeAlgo

} // namespace IECoreArnold
