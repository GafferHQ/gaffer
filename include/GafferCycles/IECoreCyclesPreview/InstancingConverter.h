//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

#ifndef IECORECYCLES_INSTANCINGCONVERTER_H
#define IECORECYCLES_INSTANCINGCONVERTER_H

#include "GafferCycles/IECoreCyclesPreview/Export.h"

#include "IECoreScene/Primitive.h"

// Cycles
#include "render/object.h"

namespace IECoreCycles
{

/// A class for managing the conversion of a series of IECore::Primitives to
/// ccl::Object, automatically returning instances when a previously converted
/// primitive is processed again.
class IECORECYCLES_API InstancingConverter : public IECore::RefCounted
{

	public :

		IE_CORE_DECLAREMEMBERPTR( InstancingConverter );

		/// Constructs a new converter. The converter expects that any
		/// ccl::Objects it creates will remain alive for the lifetime of the
		/// InstancingConverter itself - it is the responsibility of the
		/// caller to ensure that this is the case.
		InstancingConverter();
		~InstancingConverter() override;

		/// Returns the Primitive converted to an appropriate ccl::Object type, returning
		/// a ccl::Object if an identical primitive has already been processed. Interally
		/// Cycles will have a pointer to the shared ccl::Mesh type. Primitive identity is 
		/// determined by comparing hashes.
		ccl::Object *convert( const IECoreScene::Primitive *primitive, const std::string &nodeName );
		/// As above, but allowing the user to pass an additional hash representing
		/// modifications that will be made to the ccl::Object after conversion.
		ccl::Object *convert( const IECoreScene::Primitive *primitive, const IECore::MurmurHash &additionalHash, const std::string &nodeName );

		/// Motion blurred versions of the above conversion functions.
		ccl::Object *convert( const std::vector<const IECoreScene::Primitive *> &samples, const std::string &nodeName );
		ccl::Object *convert( const std::vector<const IECoreScene::Primitive *> &samples, const IECore::MurmurHash &additionalHash, const std::string &nodeName );

	private :

		struct MemberData;
		MemberData *m_data;

};

IE_CORE_DECLAREPTR( InstancingConverter );

} // namespace IECoreCycles

#endif // IECORECYCLES_INSTANCINGCONVERTER_H
