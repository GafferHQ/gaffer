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

#include "GafferML/Tensor.h"

#include "IECore/DataAlgo.h"
#include "IECore/TypeTraits.h"
#include "IECore/VectorTypedData.h"

#include "fmt/format.h"

using namespace std;
using namespace IECore;
using namespace GafferML;

namespace
{

// The Ort C++ API defines `TypeToTensorType<T>::type` for all C++ types
// (int, float etc) that are supported in tensors. But it leaves it
// completely undefined for other types. HasTensorType allows us to detect
// the supported types.

template<typename T, typename Enabler = void>
struct HasTensorType : std::false_type {};

template<typename T>
struct HasTensorType<T, std::enable_if_t<sizeof( Ort::TypeToTensorType<T> ) != 0>> : std::true_type {};

// ShapeTraits allows us to automatically determine the tensor layout for
// types like Imath::Vec3 etc.
template<typename T>
struct ShapeTraits
{
	static constexpr std::array<int64_t, 0> shape = {};
};

template<typename T>
struct ShapeTraits<Imath::Vec2<T>>
{
	static constexpr std::array<int64_t, 1> shape = { 2 };
};

template<typename T>
struct ShapeTraits<Imath::Vec3<T>>
{
	static constexpr std::array<int64_t, 1> shape = { 3 };
};

template<typename T>
struct ShapeTraits<Imath::Color4<T>>
{
	static constexpr std::array<int64_t, 1> shape = { 4 };
};

template<typename T>
struct ShapeTraits<Imath::Box<T>>
{
	static constexpr std::array<int64_t, 2> shape = { 2, T::dimensions() };
};

template<typename F>
void dispatchTensorData( const Ort::Value &value, F &&functor )
{
	const auto elementType = value.GetTensorTypeAndShapeInfo().GetElementType();
	switch( elementType )
	{
		case ONNX_TENSOR_ELEMENT_DATA_TYPE_FLOAT :
			functor( value.GetTensorData<float>() );
			break;
		case ONNX_TENSOR_ELEMENT_DATA_TYPE_DOUBLE :
			functor( value.GetTensorData<double>() );
			break;
		case ONNX_TENSOR_ELEMENT_DATA_TYPE_BOOL :
			functor( value.GetTensorData<bool>() );
			break;
		case ONNX_TENSOR_ELEMENT_DATA_TYPE_UINT16 :
			functor( value.GetTensorData<uint16_t>() );
			break;
		case ONNX_TENSOR_ELEMENT_DATA_TYPE_INT16 :
			functor( value.GetTensorData<int16_t>() );
			break;
		case ONNX_TENSOR_ELEMENT_DATA_TYPE_UINT32 :
			functor( value.GetTensorData<uint32_t>() );
			break;
		case ONNX_TENSOR_ELEMENT_DATA_TYPE_INT32 :
			functor( value.GetTensorData<int32_t>() );
			break;
		case ONNX_TENSOR_ELEMENT_DATA_TYPE_UINT64 :
			functor( value.GetTensorData<uint64_t>() );
			break;
		case ONNX_TENSOR_ELEMENT_DATA_TYPE_INT64 :
			functor( value.GetTensorData<int64_t>() );
			break;
		default :
			throw IECore::Exception( fmt::format( "Unsupported element type {}", elementType ) );
	}
}

DataPtr dataFromValue( const Ort::Value &value )
{
	DataPtr result;
	dispatchTensorData(
		value,
		[&] ( const auto *data ) {

			using ElementType = remove_const_t<remove_pointer_t<decltype( data )>>;
			using DataType = TypedData<vector<ElementType>>;
			using PtrType = typename DataType::Ptr;

			PtrType d = new DataType;
			const size_t count = value.GetTensorTypeAndShapeInfo().GetElementCount();
			d->writable().insert( d->writable().end(), data, data + count );
			result = d;

		}
	);
	return result;
}

} // namespace

IE_CORE_DEFINEOBJECTTYPEDESCRIPTION( Tensor );

Tensor::State::State( Ort::Value &&value, IECore::ConstDataPtr data )
	:	value( std::move( value ) ), data( data )
{
	if( value && !value.IsTensor() )
	{
		/// \todo Maybe we'll loosen this restriction at some point,
		/// or maybe we'll create wrappers for the other Value types.
		/// For the moment we just want to know if something unexpected
		/// happens.
		throw IECore::Exception( "Ort::Value is not a tensor" );
	}
}

Tensor::Tensor()
	:	m_state( new State( Ort::Value( nullptr ) ) )
{
}

Tensor::Tensor( Ort::Value &&value )
	:	m_state( new State( std::move( value ) ) )
{
}

Tensor::Tensor( const IECore::ConstDataPtr &data, std::vector<int64_t> shape )
{
	IECore::dispatch(
		data.get(),
		[&] ( auto typedData ) -> void {

			using DataType = remove_const_t<remove_pointer_t<decltype( typedData )>>;
			using BaseType = typename DataType::BaseType;

			if( !shape.size() )
			{
				// Automatically infer shape from type.
				if constexpr( TypeTraits::IsVectorTypedData<DataType>::value )
				{
					shape.push_back( typedData->readable().size() );
					using ShapeT = ShapeTraits<typename DataType::ValueType::value_type>;
					shape.insert( shape.end(), begin( ShapeT::shape ), end( ShapeT::shape ) );
				}
				else
				{
					using ShapeT = ShapeTraits<typename DataType::ValueType>;
					shape.insert( shape.end(), begin( ShapeT::shape ), end( ShapeT::shape ) );
				}
			}

			if constexpr( std::is_same_v<DataType, BoolVectorData> )
			{
				// Special case for the vector of bool fiasco.
				Ort::AllocatorWithDefaultOptions allocator;
				Ort::Value value = Ort::Value::CreateTensor(
					allocator, shape.data(), shape.size(), ONNX_TENSOR_ELEMENT_DATA_TYPE_BOOL
				);
				std::copy( typedData->readable().begin(), typedData->readable().end(), value.GetTensorMutableData<bool>() );
				m_state = new State{ std::move( value ), nullptr };
			}
			else if constexpr( HasTensorType<BaseType>::value )
			{
				Ort::MemoryInfo memoryInfo = Ort::MemoryInfo::CreateCpu( OrtArenaAllocator, OrtMemTypeDefault );
				m_state = new State{
					Ort::Value::CreateTensor(
						memoryInfo.GetConst(),
						// `const_cast()` is OK because we only provide const access to the
						// `Ort::Value` after construction.
						const_cast<DataType *>( typedData )->baseWritable(), typedData->baseSize(),
						shape.data(), shape.size()
					),
					data
				};
			}
			else
			{
				throw IECore::Exception( fmt::format( "Unsupported data type `{}`", DataType::staticTypeName() ) );
			}

		}
	);
}

bool Tensor::isEqualTo( const IECore::Object *other ) const
{
	if( !Object::isEqualTo( other ) )
	{
		return false;
	}

	auto otherTensor = static_cast<const Tensor *>( other );
	if( m_state == otherTensor->m_state )
	{
		return true;
	}
	else if( !m_state->value && !otherTensor->m_state->value )
	{
		return true;
	}
	else if( !m_state->value || !otherTensor->m_state->value )
	{
		return false;
	}
	else if( shape() != otherTensor->shape() )
	{
		return false;
	}

	// Everything else is equal. Need to compare tensor data now.

	if( m_state->data && otherTensor->m_state->data )
	{
		// If both tensors are backed by `IECore::Data`, then compare that.
		// This has a fast path for when the underlying data is shared.
		return m_state->data->isEqualTo( otherTensor->m_state->data.get() );
	}

	// Compare the buffers ourselves.

	if(
		m_state->value.GetTensorTypeAndShapeInfo().GetElementType() !=
		otherTensor->m_state->value.GetTensorTypeAndShapeInfo().GetElementType()
	)
	{
		return false;
	}

	bool equal;
	dispatchTensorData(
		m_state->value,
		[&] ( const auto *data ) {

			using ElementType = remove_const_t<remove_pointer_t<decltype( data )>>;
			const auto *otherData = otherTensor->m_state->value.GetTensorData<ElementType>();
			const size_t count = m_state->value.GetTensorTypeAndShapeInfo().GetElementCount();
			equal = memcmp( data, otherData, count * sizeof( *data ) ) == 0;
		}
	);

	return equal;
}

void Tensor::hash( IECore::MurmurHash &h ) const
{
	Object::hash( h );

	if( !m_state->value )
	{
		return;
	}

	dispatchTensorData(
		m_state->value,
		[&] ( const auto *data ) {
			const size_t count = m_state->value.GetTensorTypeAndShapeInfo().GetElementCount();
			h.append( data, count );
		}
	);

	auto s = shape();
	h.append( s.data(), s.size() );
}

void Tensor::copyFrom( const IECore::Object *other, IECore::Object::CopyContext *context )
{
	Object::copyFrom( other, context );
	// Because our public API only provides const access to the value,
	// our copy can be extremely cheap, and just share ownership with
	// the original.
	m_state = static_cast<const Tensor *>( other )->m_state;
}

void Tensor::save( IECore::Object::SaveContext *context ) const
{
	Object::save( context );
	throw IECore::NotImplementedException( "Tensor::save" );
}

void Tensor::load( IECore::Object::LoadContextPtr context )
{
	Object::load( context );
	throw IECore::NotImplementedException( "Tensor::load" );
}

void Tensor::memoryUsage( IECore::Object::MemoryAccumulator &accumulator ) const
{
	Object::memoryUsage( accumulator );

	if( m_state->data )
	{
		// Register the memory used by data if we have it. This can
		// be shared with other objects, in which case the MemoryAccumulator
		// is smart enough not to double-count it.
		accumulator.accumulate( m_state->data.get() );
	}
	else if( m_state->value )
	{
		// Ort::Value owns the data. Calculate memory usage.
		dispatchTensorData(
			m_state->value,
			[&] ( const auto *data ) {

				const size_t count = m_state->value.GetTensorTypeAndShapeInfo().GetElementCount();
				accumulator.accumulate( m_state.get(), count * sizeof( *data ) );
			}
		);
	}
}

const Ort::Value &Tensor::value() const
{
	return m_state->value;
}

std::vector<int64_t> Tensor::shape() const
{
	if( !m_state->value )
	{
		throw IECore::Exception( "Null tensor" );
	}
	return m_state->value.GetTensorTypeAndShapeInfo().GetShape();
}

IECore::DataPtr Tensor::asData()
{
	if( !m_state->value )
	{
		return nullptr;
	}

	if( m_state->data )
	{
		return m_state->data->copy();
	}
	return dataFromValue( m_state->value );
}

IECore::ConstDataPtr Tensor::asData() const
{
	if( !m_state->value )
	{
		return nullptr;
	}

	if( m_state->data )
	{
		return m_state->data;
	}
	return dataFromValue( m_state->value );
}
