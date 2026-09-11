//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/PrimitiveVariableType.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/Primitive.h"

#include "IECore/Canceller.h"
#include "IECore/DataAlgo.h"
#include "IECore/GeometricTypedData.h"
#include "IECore/TypeTraits.h"

#include "tbb/blocked_range.h"
#include "tbb/parallel_for.h"

#include "fmt/format.h"

#include <functional>

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

template<typename T>
using DataElementType = std::conditional_t<
	TypeTraits::IsVectorTypedData<T>::value,
	typename TypeTraits::VectorValueType<T>::type,
	typename TypeTraits::ValueType<T>::type
>;

template<typename T>
constexpr size_t componentCount()
{
	static_assert( TypeTraits::HasBaseType<T>::value, "Data must have a base type" );
	return sizeof( DataElementType<T> ) / sizeof( typename T::BaseType );
}

DataPtr convertInterpretation( const Data *data, GeometricData::Interpretation interpretation )
{
	if(
		!IECore::trait<TypeTraits::IsGeometricTypedData>( data ) ||
		IECore::getGeometricInterpretation( data ) == interpretation
	)
	{
		return nullptr;
	}

	DataPtr result = data->copy();
	IECore::setGeometricInterpretation( result.get(), interpretation );
	return result;
}

template<typename S, typename T>
T convertComponent( S v )
{
	if constexpr( std::is_integral_v<S> && std::is_integral_v<T> )
	{
		if constexpr( std::is_signed_v<S> && std::is_signed_v<T> )
		{
			if( static_cast<std::intmax_t>( v ) < static_cast<std::intmax_t>( std::numeric_limits<T>::lowest() ) )
			{
				return std::numeric_limits<T>::lowest();
			}
			else if( static_cast<std::intmax_t>( v ) > static_cast<std::intmax_t>( std::numeric_limits<T>::max() ) )
			{
				return std::numeric_limits<T>::max();
			}
		}
		else
		{
			if constexpr( std::is_signed_v<S> )
			{
				// Signed source, unsigned destination
				if( v < 0 )
				{
					return 0;
				}
			}

			if( static_cast<std::uintmax_t>( v ) > static_cast<std::uintmax_t>( std::numeric_limits<T>::max() ) )
			{
				return std::numeric_limits<T>::max();
			}
		}
	}
	else if constexpr( !std::is_integral_v<S> && std::is_integral_v<T> )
	{
		if( std::isnan( v ) )
		{
			throw IECore::Exception( "PrimitiveVariableType : Unable to convert NaN to integer." );
		}
		else if( v <= static_cast<S>( std::numeric_limits<T>::lowest() ) )
		{
			return std::numeric_limits<T>::lowest();
		}
		else if( v >= static_cast<S>( std::numeric_limits<T>::max() ) )
		{
			return std::numeric_limits<T>::max();
		}
	}

	return static_cast<T>( v );
}

// Calls `f( begin, end )` in parallel. Implemented as a non-templated function to
// avoid duplicating TBB-related code for each instantiation of `convertElements()`.
void parallelProcessElements( const size_t size, const Canceller *canceller, const std::function<void ( size_t, size_t )> &f )
{
	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );
	tbb::parallel_for(
		tbb::blocked_range<size_t>( 0, size, 10000 ),
		[&] ( const tbb::blocked_range<size_t> &range )
		{
			Canceller::check( canceller );
			f( range.begin(), range.end() );
		},
		taskGroupContext
	);
}

template<typename S, typename T>
void convertElements( const S *source, const size_t sourceComponents, T *target, const size_t targetComponents, const size_t size, const Canceller *canceller )
{
	parallelProcessElements( size, canceller, [&] ( const size_t begin, const size_t end ) {

		if( sourceComponents == 1 )
		{
			for( size_t i = begin; i < end; ++i )
			{
				const T v = convertComponent<S, T>( source[i] );
				for( size_t c = 0; c < targetComponents; ++c )
				{
					// A single source is copied to all components of the target.
					target[i * targetComponents + c] = v;
				}
			}
		}
		else
		{
			for( size_t i = begin; i < end; ++i )
			{
				for( size_t c = 0; c < targetComponents; ++c )
				{
					// Components are converted one for one, dropping any
					// the target doesn't have and filling the remaining with 0.
					target[i * targetComponents + c] = convertComponent<S, T>( c < sourceComponents ? source[i * sourceComponents + c] : S( 0 ) );
				}
			}
		}

	} );
}

template<typename T, typename S>
DataPtr convertTypeAndInterpretation( const S *sourceData, std::optional<GeometricData::Interpretation> interpretation, const Canceller *canceller )
{
	if( sourceData->typeId() == T::staticTypeId() )
	{
		return interpretation ? convertInterpretation( sourceData, interpretation.value() ) : nullptr;
	}

	GeometricData::Interpretation sourceInterpretation = GeometricData::None;
	if constexpr( TypeTraits::IsGeometricTypedData<S>::value )
	{
		sourceInterpretation = sourceData->getInterpretation();
	}

	typename T::Ptr targetData = new T;
	if constexpr( TypeTraits::IsGeometricTypedData<T>::value )
	{
		targetData->setInterpretation( interpretation.value_or( sourceInterpretation ) );
	}

	size_t size = 1;
	if constexpr( TypeTraits::IsVectorTypedData<T>::value )
	{
		size = sourceData->readable().size();
		if( !size )
		{
			return targetData;
		}
		targetData->writable().resize( size );
	}

	convertElements(
		sourceData->baseReadable(), componentCount<S>(),
		targetData->baseWritable(), componentCount<T>(),
		size, canceller
	);

	return targetData;
}

template<typename T>
constexpr bool isConvertible()
{
	if constexpr( TypeTraits::IsNumericBasedTypedData<T>::value )
	{
		using D = DataElementType<T>;
		return
			std::is_same_v<D, typename T::BaseType> ||
			TypeTraits::IsVec<D>::value ||
			TypeTraits::IsColor<D>::value
		;
	}
	else
	{
		return false;
	}
}

template<typename T>
DataPtr convertTo( const Data *data, const std::string &name, std::optional<GeometricData::Interpretation> interpretation, const Canceller *canceller )
{
	return dispatch(

		data,

		[&] ( const auto *typedData ) -> DataPtr {

			using SourceDataType = std::remove_const_t<std::remove_pointer_t<decltype( typedData )>>;

			if constexpr( isConvertible<SourceDataType>() )
			{
				if constexpr( TypeTraits::IsVectorTypedData<SourceDataType>::value )
				{
					using DataType = std::conditional_t<
						TypeTraits::IsVec<T>::value,
						GeometricTypedData<std::vector<T>>,
						TypedData<std::vector<T>>
					>;
					return convertTypeAndInterpretation<DataType>( typedData, interpretation, canceller );
				}
				else
				{
					using DataType = std::conditional_t<
						TypeTraits::IsVec<T>::value,
						GeometricTypedData<T>,
						TypedData<T>
					>;
					return convertTypeAndInterpretation<DataType>( typedData, interpretation, canceller );
				}
			}
			else
			{
				throw IECore::Exception( fmt::format(
					"PrimitiveVariableType : Primitive variable \"{}\" has unsupported type \"{}\".", name, data->typeName()
				) );
			}

		}

	);
}

DataPtr convertData( const Data *data, const std::string &name, PrimitiveVariableType::Type targetType, std::optional<GeometricData::Interpretation> interpretation, const Canceller *canceller )
{
	switch( targetType )
	{
		case PrimitiveVariableType::Type::UChar :
			return convertTo<unsigned char>( data, name, interpretation, canceller );

		case PrimitiveVariableType::Type::Int :
			return convertTo<int>( data, name, interpretation, canceller );

		case PrimitiveVariableType::Type::UInt :
			return convertTo<unsigned int>( data, name, interpretation, canceller );

		case PrimitiveVariableType::Type::Int64 :
			return convertTo<int64_t>( data, name, interpretation, canceller );

		case PrimitiveVariableType::Type::UInt64 :
			return convertTo<uint64_t>( data, name, interpretation, canceller );

		case PrimitiveVariableType::Type::Half :
			return convertTo<half>( data, name, interpretation, canceller );

		case PrimitiveVariableType::Type::Float :
			return convertTo<float>( data, name, interpretation, canceller );

		case PrimitiveVariableType::Type::Double :
			return convertTo<double>( data, name, interpretation, canceller );

		case PrimitiveVariableType::Type::V2i :
			return convertTo<Imath::V2i>( data, name, interpretation, canceller );

		case PrimitiveVariableType::Type::V2f :
			return convertTo<Imath::V2f>( data, name, interpretation, canceller );

		case PrimitiveVariableType::Type::V2d :
			return convertTo<Imath::V2d>( data, name, interpretation, canceller );

		case PrimitiveVariableType::Type::V3i :
			return convertTo<Imath::V3i>( data, name, interpretation, canceller );

		case PrimitiveVariableType::Type::V3f :
			return convertTo<Imath::V3f>( data, name, interpretation, canceller );

		case PrimitiveVariableType::Type::V3d :
			return convertTo<Imath::V3d>( data, name, interpretation, canceller );

		case PrimitiveVariableType::Type::Color3f :
			return convertTo<Imath::Color3f>( data, name, interpretation, canceller );

		case PrimitiveVariableType::Type::Color4f :
			return convertTo<Imath::Color4f>( data, name, interpretation, canceller );

		default :
			throw IECore::InvalidArgumentException( fmt::format( "PrimitiveVariableType : Invalid target type {}", (int)targetType ) );
	}
}

} // namespace

GAFFER_NODE_DEFINE_TYPE( PrimitiveVariableType );

size_t PrimitiveVariableType::g_firstPlugIndex = 0;

PrimitiveVariableType::PrimitiveVariableType( const std::string &name )
	:	ObjectProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "primitiveVariables" ) );
	addChild( new OptionalValuePlug( "type", new IntPlug( "value", Plug::In, (int)Type::Float, (int)Type::First, (int)Type::Last ) ) );
	addChild( new OptionalValuePlug( "interpretation", new IntPlug( "value", Plug::In, (int)GeometricData::None, (int)GeometricData::None, (int)GeometricData::UV ) ) );
}

PrimitiveVariableType::~PrimitiveVariableType()
{
}

Gaffer::StringPlug *PrimitiveVariableType::primitiveVariablesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *PrimitiveVariableType::primitiveVariablesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::OptionalValuePlug *PrimitiveVariableType::typePlug()
{
	return getChild<OptionalValuePlug>( g_firstPlugIndex + 1 );
}

const Gaffer::OptionalValuePlug *PrimitiveVariableType::typePlug() const
{
	return getChild<OptionalValuePlug>( g_firstPlugIndex + 1 );
}

Gaffer::OptionalValuePlug *PrimitiveVariableType::interpretationPlug()
{
	return getChild<OptionalValuePlug>( g_firstPlugIndex + 2 );
}

const Gaffer::OptionalValuePlug *PrimitiveVariableType::interpretationPlug() const
{
	return getChild<OptionalValuePlug>( g_firstPlugIndex + 2 );
}

Gaffer::ValuePlug::CachePolicy PrimitiveVariableType::processedObjectComputeCachePolicy() const
{
	return ValuePlug::CachePolicy::TaskCollaboration;
}

bool PrimitiveVariableType::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		ObjectProcessor::affectsProcessedObject( input ) ||
		input == primitiveVariablesPlug() ||
		input->parent() == typePlug() ||
		input->parent() == interpretationPlug()
	;
}

void PrimitiveVariableType::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const std::string primitiveVariables = primitiveVariablesPlug()->getValue();
	const bool typeEnabled = typePlug()->enabledPlug()->getValue();
	const bool interpretationEnabled = interpretationPlug()->enabledPlug()->getValue();

	if( primitiveVariables.empty() || ( !typeEnabled && !interpretationEnabled ) )
	{
		h = inPlug()->objectPlug()->hash();
		return;
	}

	ObjectProcessor::hashProcessedObject( path, context, h );
	h.append( primitiveVariables );

	h.append( typeEnabled );
	if( typeEnabled )
	{
		typePlug()->valuePlug()->hash( h );
	}

	h.append( interpretationEnabled );
	if( interpretationEnabled )
	{
		interpretationPlug()->valuePlug()->hash( h );
	}
}

IECore::ConstObjectPtr PrimitiveVariableType::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	auto primitive = runTimeCast<const Primitive>( inputObject );
	if( !primitive )
	{
		return inputObject;
	}

	const std::string primitiveVariables = primitiveVariablesPlug()->getValue();

	std::optional<Type> type;
	if( typePlug()->enabledPlug()->getValue() )
	{
		type = (Type)typePlug()->valuePlug<IntPlug>()->getValue();
	}

	std::optional<GeometricData::Interpretation> interpretation;
	if( interpretationPlug()->enabledPlug()->getValue() )
	{
		interpretation = (GeometricData::Interpretation)interpretationPlug()->valuePlug<IntPlug>()->getValue();
	}

	if( primitiveVariables.empty() || ( !type && !interpretation ) )
	{
		return inputObject;
	}

	PrimitivePtr result;
	for( const auto &[name, primitiveVariable] : primitive->variables )
	{
		if( !StringAlgo::matchMultiple( name, primitiveVariables ) )
		{
			continue;
		}

		DataPtr data = type ?
			convertData( primitiveVariable.data.get(), name, *type, interpretation, context->canceller() ) :
			convertInterpretation( primitiveVariable.data.get(), *interpretation )
		;
		if( !data )
		{
			continue;
		}

		if( !result )
		{
			result = primitive->copy();
		}
		result->variables[name].data = data;
	}

	return result ? result.get() : inputObject;
}
