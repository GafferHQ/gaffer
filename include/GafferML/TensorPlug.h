//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "GafferML/TypeIds.h"

#include "Gaffer/TypedObjectPlug.h"

#include "IECore/Data.h"

#include "onnxruntime_cxx_api.h"

#include <vector>

namespace GafferML
{

/// TODO : THINK ABOUT CONST PROPAGATION AND CACHING
/// WILL ALSO NEED THE OPTION OF JUST WRAPPING A VALUE DIRECTLY, WITH NO DATA BACKING
/// ADD TYPEID
/// MAKE CLASS
struct GAFFER_API TensorData : public IECore::Data
{

	IE_CORE_DECLAREEXTENSIONOBJECT( GafferML::TensorData, GafferML::TensorDataTypeId, IECore::Data );

	TensorData();

	TensorData( Ort::Value &&value )
		: value( std::move( value ) )
	{
	}

	template<typename T>
	TensorData( T data, const std::vector<int64_t> &shape )
		:	data( data ), value( nullptr )
	{
		Ort::MemoryInfo memoryInfo = Ort::MemoryInfo::CreateCpu( OrtArenaAllocator, OrtMemTypeDefault );
		value = Ort::Value::CreateTensor( memoryInfo.GetConst(), data->writable().data(), data->readable().size(), shape.data(), shape.size() );
	}

	IECore::ConstDataPtr data;
	Ort::Value value;

};

IE_CORE_DECLAREPTR( TensorData );

using TensorPlug = Gaffer::TypedObjectPlug<TensorData>;

IE_CORE_DECLAREPTR( TensorPlug );

} // namespace GafferML


// #if !defined( GafferML_EXPORTS ) && !defined( _MSC_VER )

// namespace Gaffer
// {

// extern template class Gaffer::TypedObjectPlug<GafferML::TensorData>;

// } // namespace Gaffer

//#endif
