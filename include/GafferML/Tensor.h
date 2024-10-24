//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//      * Neither the name of John Haddon nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
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

#include "GafferML/Export.h"
#include "GafferML/TypeIds.h"

#include "IECore/Data.h"

#include "onnxruntime_cxx_api.h"

#include <vector>

namespace GafferML
{

/// Thin wrapper around an `Ort::Value`, allowing it to be passed
/// through a node graph via TensorPlugs.
class GAFFERML_API Tensor : public IECore::Object
{

	public :

		Tensor();
		Tensor( Ort::Value &&value );

		/// TODO : MAKE TAKE CONST DATA ONLY. MOVE TEMPLATE SHENANIGANS INSIDE CPP?
		template<typename T>
		Tensor( T data, const std::vector<int64_t> &shape );

		IE_CORE_DECLAREEXTENSIONOBJECT( GafferML::Tensor, GafferML::TensorTypeId, IECore::Object );

		/// Only const access to the `Ort::Value` is provided, as modifying a
		/// a `GafferML::Tensor` would corrupt values stored in Gaffer's compute
		/// cache.
		/// TODO : MAYBE THE CONSTNESS IS MORE ABOUT COPYING WITHOUT NEEDING TO
		/// WORRY ABOUT COPY-ON-WRITE AT ALL?
		const Ort::Value &value() const;

	private :

		// If we were constructed from TypedData, then this keeps it alive for
		// as long as `m_value` references it. If we constructed from
		// `Ort::Value` directly, then this is null and `m_value` owns its own
		// data.
		IECore::ConstDataPtr m_data;
		Ort::Value m_value;

};

IE_CORE_DECLAREPTR( Tensor );

} // namespace GafferML

#include "GafferML/Tensor.inl"
