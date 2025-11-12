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
/// through a graph of ComputeNodes via TensorPlugs.
class GAFFERML_API Tensor : public IECore::Object
{

	public :

		/// Enum to be used in `IntPlug` values when a node requires a tensor type to be specified.
		/// Values currently match one-to-one with `ONNXTensorElementDataType`, but have Python
		/// bindings and are guaranteed to remain stable for serialisation in .gfr files.
		enum class ElementType
		{
			Undefined = ONNX_TENSOR_ELEMENT_DATA_TYPE_UNDEFINED,
			Float = ONNX_TENSOR_ELEMENT_DATA_TYPE_FLOAT,
			Float16 = ONNX_TENSOR_ELEMENT_DATA_TYPE_FLOAT16,
			Double = ONNX_TENSOR_ELEMENT_DATA_TYPE_DOUBLE,
			Bool = ONNX_TENSOR_ELEMENT_DATA_TYPE_BOOL,
			UInt16 = ONNX_TENSOR_ELEMENT_DATA_TYPE_UINT16,
			Int16 = ONNX_TENSOR_ELEMENT_DATA_TYPE_INT16,
			UInt32 = ONNX_TENSOR_ELEMENT_DATA_TYPE_UINT32,
			Int32 = ONNX_TENSOR_ELEMENT_DATA_TYPE_INT32,
			UInt64 = ONNX_TENSOR_ELEMENT_DATA_TYPE_UINT64,
			Int64 = ONNX_TENSOR_ELEMENT_DATA_TYPE_INT64,
			String = ONNX_TENSOR_ELEMENT_DATA_TYPE_STRING
		};

		Tensor();
		Tensor( Ort::Value &&value );

		/// Constructs from varieties of `IECore::TypedData`. The Tensor references `data` directly
		/// without copying, so it must not be modified after being passed to the constructor.
		/// If `shape` is not specified, then it will be inferred automatically from the data layout.
		Tensor( const IECore::ConstDataPtr &data, std::vector<int64_t> shape = std::vector<int64_t>() );

		IE_CORE_DECLAREEXTENSIONOBJECT( GafferML::Tensor, GafferML::TensorTypeId, IECore::Object );

		/// Only const access to the `Ort::Value` is provided. This lets us
		/// implement `Object::copy()` extremely cheaply, which is important
		/// when accessing a Tensor value from a Python Expression.
		const Ort::Value &value() const;

		/// Convenience accessors
		/// =====================
		///
		/// These don't do anything that can't be achieved directly with
		/// `value()` and the Ort API, but are provided for symmetry with
		/// the Python bindings.

		std::vector<int64_t> shape() const;

		/// Conversion to `IECore::Data`
		/// ============================

		IECore::DataPtr asData();
		IECore::ConstDataPtr asData() const;

	private :

		struct State : public IECore::RefCounted
		{
			State( Ort::Value &&value, IECore::ConstDataPtr data = nullptr );
			Ort::Value value;
			// If we were constructed from TypedData, then this keeps it alive for
			// as long as `value` references it. If we constructed from
			// `Ort::Value` directly, then this is null and `value` owns its own
			// data.
			IECore::ConstDataPtr data;
		};
		IE_CORE_DECLAREPTR( State );

		ConstStatePtr m_state;

};

IE_CORE_DECLAREPTR( Tensor );

} // namespace GafferML
