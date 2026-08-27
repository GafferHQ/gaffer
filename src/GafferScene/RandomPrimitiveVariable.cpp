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
//      * Neither the name of Image Engine Design Inc nor the names of
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

#include "GafferScene/RandomPrimitiveVariable.h"

#include "Gaffer/PlugAlgo.h"

#include "IECoreScene/Primitive.h"

#include "IECore/DataAlgo.h"
#include "IECore/GeometricTypedData.h"
#include "IECore/VectorTypedData.h"
#include "IECore/TypeTraits.h"

#include "Imath/ImathFun.h"

#include "tbb/parallel_for.h"

#include "fmt/ranges.h"

#include <cmath>
#include <functional>
#include <numeric>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

// 32-bit float can represent the first 2^24 integers exactly,
// so converting them to float and then scaling gives us an
// unbiased result.
float unitFloat( uint64_t uniformInteger )
{
	return (float)( uniformInteger >> 40 ) * ( 1.0f / 16777216.0f );
}

struct UniformIntDistribution
{

	using ResultType = IntVectorData;

	const V2i range;

	// Distributions take a per-point seed in the form of
	// a MurmurHash, and return the value for that point.
	int operator() ( const IECore::MurmurHash &seed ) const
	{
		const uint64_t span = (uint64_t)( range.y - range.x ) + 1;
		const uint64_t r = seed.h1() >> 32;
		return range.x + (int)( ( r * span ) >> 32 );
	}

};

struct UniformFloatDistribution
{

	using ResultType = FloatVectorData;

	const V2f range;

	float operator() ( const IECore::MurmurHash &seed ) const
	{
		const float u = unitFloat( seed.h1() );
		return lerp( range[0], range[1], u );
	}

};

struct GaussianDistribution
{

	using ResultType = FloatVectorData;

	const float mean;
	const float deviation;

	float operator() ( const MurmurHash &seed ) const
	{
		// Box-Muller transform.
		const float u1 = std::max( unitFloat( seed.h1() ), 1e-7f ); // avoid `log( 0 )`
		const float u2 = unitFloat( seed.h2() );
		const float z = std::sqrt( -2.0f * std::log( u1 ) ) * std::cos( 2.0f * (float)M_PI * u2 );
		return mean + z * deviation;
	}

};

// We could support any VectorTypedData, but to avoid
// code bloat we just use these ones, matching the
// RandomChoice node.
template<typename T>
using IsSupportedWeightedChoiceType = std::disjunction<
	std::is_same<T, BoolVectorData>,
	std::is_same<T, IntVectorData>,
	std::is_same<T, FloatVectorData>,
	std::is_same<T, V2iVectorData>,
	std::is_same<T, V3fVectorData>,
	std::is_same<T, Color3fVectorData>,
	std::is_same<T, StringVectorData>
>;

template<typename T>
struct WeightedChoiceDistribution
{

	using ResultType = T;

	WeightedChoiceDistribution( const T *values, const vector<float> &weights )
		:	m_values( values->readable() ), m_weights( weights )
	{
		if( m_weights.size() != m_values.size() )
		{
			throw IECore::Exception( fmt::format(
				"Length of `choices.weights` does not match length of `choices.values` "
				"({} but should be {}).",
				m_weights.size(), m_values.size()
			) );
		}

		m_weightsSum = accumulate( m_weights.begin(), m_weights.end(), 0.0f );
	}

	typename T::ValueType::value_type operator() ( const MurmurHash &seed ) const
	{
		// We could build a vector of cumulative weights in our constructor
		// and then do binary search, but experience with the RandomChoice
		// node suggests that simple linear search wins for the numbers of
		// choices we use in practice.
		const float r = unitFloat( seed.h1() ) * m_weightsSum;
		float s = 0;
		for( size_t i = 0; i < m_weights.size(); ++i )
		{
			s += m_weights[i];
			if( s >= r )
			{
				return m_values[i];
			}
		}
		throw IECore::Exception( "Out of weight range" );
	}

	private :

		const typename T::ValueType &m_values;
		const vector<float> &m_weights;
		float m_weightsSum;

};

struct HollowSphereDistribution
{

	using ResultType = V3fVectorData;

	const float radius;

	V3f operator() ( const IECore::MurmurHash &seed ) const
	{
		const float u1 = unitFloat( seed.h1() );
		const float u2 = unitFloat( seed.h2() );
		const float z = 1.0f - 2.0f * u1;
		const float r = std::sqrt( std::max( 0.0f, 1.0f - z * z ) );
		const float phi = 2.0f * (float)M_PI * u2;
		return V3f( r * std::cos( phi ), r * std::sin( phi ), z ) * radius;
	}

};

// Technically we could support any VectorTypedData for the seed, but this leads
// to code bloat, so we just support the subset we think is likely to actually
// be useful.
template<typename T>
using IsSupportedSeedType = std::disjunction<
	std::is_same<T, IntVectorData>,
	std::is_same<T, Int64VectorData>,
	std::is_same<T, FloatVectorData>,
	std::is_same<T, V2fVectorData>,
	std::is_same<T, V3fVectorData>,
	std::is_same<T, StringVectorData>
>;

using SeedFunction = std::function<MurmurHash ( size_t )>;

// We create a SeedFunction up front to avoid dispatching on the `seedVariable` type
// inside `dispatchDistribution()`. This avoid code bloat due to combinatorial
// explosion of templates.
SeedFunction createSeedFunction( int seed, const PrimitiveVariable *seedVariable )
{
	if( !seedVariable )
	{
		return [seed] ( size_t i ) {
			MurmurHash h;
			h.append( seed );
			h.append( i );
			return h;
		};
	}

	return IECore::dispatch(

		seedVariable->data.get(),

		[&] ( auto *seedData ) -> SeedFunction {

			using DataType = remove_const_t<remove_pointer_t<decltype( seedData )>>;

			if constexpr( IsSupportedSeedType<DataType>::value )
			{
				using SeedElementType = typename DataType::ValueType::value_type;
				return [seed, seedView = PrimitiveVariable::IndexedView<SeedElementType>( *seedVariable )] ( size_t i ) {
					MurmurHash h;
					h.append( seed );
					h.append( seedView[i] );
					return h;
				};
			}
			else
			{
				throw IECore::Exception( fmt::format( "Unsupported seed data type {}", seedData->typeName() ) );
			}

		}

	);
}

template<typename Distribution>
DataPtr dispatchDistribution( const Distribution &distribution, size_t size, int seed, const PrimitiveVariable *seedVariable )
{
	typename Distribution::ResultType::Ptr data = new typename Distribution::ResultType;
	auto &writableData = data->writable();
	writableData.resize( size );

	SeedFunction seedFunction = createSeedFunction( seed, seedVariable );

	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );
	tbb::parallel_for(

		tbb::blocked_range<size_t>( 0, size ),
		[&] ( const tbb::blocked_range<size_t> &range ) {

			for( size_t i = range.begin(); i < range.end(); ++i )
			{
				writableData[i] = distribution( seedFunction( i ) );
			}
		},

		taskGroupContext

	);

	return data;
}

DataPtr dispatchWeightedChoiceDistribution(
	const Data *values, const vector<float> &weights,
	size_t variableSize, int seed, const PrimitiveVariable *seedVariable
)
{
	return dispatch(

		values,

		[&] ( const auto *data ) -> DataPtr {

			using DataType = remove_const_t<remove_pointer_t<decltype( data )>>;
			if constexpr( IsSupportedWeightedChoiceType<DataType>::value )
			{
				using ElementType = typename DataType::ValueType::value_type;
				if constexpr( sizeof( ElementType ) <= sizeof( int ) )
				{
					return dispatchDistribution(
						WeightedChoiceDistribution( data, weights ), variableSize, seed, seedVariable
					);
				}
				else
				{
					// More efficient space-wise to use indices to reference
					// in to the list of values.
					IntVectorDataPtr indices = new IntVectorData;
					indices->writable().resize( weights.size() );
					std::iota( indices->writable().begin(), indices->writable().end(), 0 );
					return dispatchDistribution(
						WeightedChoiceDistribution<IntVectorData>( indices.get(), weights ), variableSize, seed, seedVariable
					);
				}
			}

			return nullptr;
		}

	);
}

} // namespace

GAFFER_NODE_DEFINE_TYPE( RandomPrimitiveVariable );

size_t RandomPrimitiveVariable::g_firstPlugIndex = 0;

RandomPrimitiveVariable::RandomPrimitiveVariable( const std::string &name )
	:	Deformer( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "name", Plug::In, "random" ) );
	addChild( new IntPlug( "interpolation", Plug::In, (int)PrimitiveVariable::Vertex, (int)PrimitiveVariable::Uniform, (int)PrimitiveVariable::Vertex ) );
	addChild( new IntPlug( "seed", Plug::In, 0 ) );
	addChild( new StringPlug( "seedPrimitiveVariable" ) );
	addChild( new IntPlug( "distribution", Plug::In, (int)UniformFloat, (int)UniformInt, (int)HollowSphere ) );
	addChild( new V2iPlug( "intRange", Plug::In, V2i( 0, 10 ) ) );
	addChild( new V2fPlug( "floatRange", Plug::In, V2f( 0, 1 ) ) );
	addChild( new FloatPlug( "mean", Plug::In, 0.5f ) );
	addChild( new FloatPlug( "deviation", Plug::In, 0.25f, 0.0f ) );
	addChild( new ValuePlug( "choices" ) );
	choicesPlug()->addChild( new FloatVectorDataPlug( "weights" ) );
	addChild( new FloatPlug( "radius", Plug::In, 1.0f, 0.0f ) );
	addChild( new IntPlug( "interpretation", Plug::In, (int)GeometricData::Vector, (int)GeometricData::Point, (int)GeometricData::Vector ) );
}

RandomPrimitiveVariable::~RandomPrimitiveVariable()
{
}

Gaffer::StringPlug *RandomPrimitiveVariable::namePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *RandomPrimitiveVariable::namePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *RandomPrimitiveVariable::interpolationPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *RandomPrimitiveVariable::interpolationPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug *RandomPrimitiveVariable::seedPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *RandomPrimitiveVariable::seedPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *RandomPrimitiveVariable::seedPrimitiveVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *RandomPrimitiveVariable::seedPrimitiveVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::IntPlug *RandomPrimitiveVariable::distributionPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::IntPlug *RandomPrimitiveVariable::distributionPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 4 );
}

Gaffer::V2iPlug *RandomPrimitiveVariable::intRangePlug()
{
	return getChild<V2iPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::V2iPlug *RandomPrimitiveVariable::intRangePlug() const
{
	return getChild<V2iPlug>( g_firstPlugIndex + 5 );
}

Gaffer::V2fPlug *RandomPrimitiveVariable::floatRangePlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::V2fPlug *RandomPrimitiveVariable::floatRangePlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 6 );
}

Gaffer::FloatPlug *RandomPrimitiveVariable::meanPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::FloatPlug *RandomPrimitiveVariable::meanPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 7 );
}

Gaffer::FloatPlug *RandomPrimitiveVariable::deviationPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::FloatPlug *RandomPrimitiveVariable::deviationPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 8 );
}

Gaffer::ValuePlug *RandomPrimitiveVariable::choicesPlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 9 );
}

const Gaffer::ValuePlug *RandomPrimitiveVariable::choicesPlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 9 );
}

Gaffer::FloatVectorDataPlug *RandomPrimitiveVariable::choicesWeightsPlug()
{
	return choicesPlug()->getChild<FloatVectorDataPlug>( "weights" );
}

const Gaffer::FloatVectorDataPlug *RandomPrimitiveVariable::choicesWeightsPlug() const
{
	return choicesPlug()->getChild<FloatVectorDataPlug>( "weights" );
}

Gaffer::FloatPlug *RandomPrimitiveVariable::radiusPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 10 );
}

const Gaffer::FloatPlug *RandomPrimitiveVariable::radiusPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 10 );
}

Gaffer::IntPlug *RandomPrimitiveVariable::interpretationPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 11 );
}

const Gaffer::IntPlug *RandomPrimitiveVariable::interpretationPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 11 );
}

void RandomPrimitiveVariable::setup( const Gaffer::ValuePlug *plug )
{
	choicesPlug()->setChild( "values", plug->createCounterpart( "values", Plug::In ) );
}

bool RandomPrimitiveVariable::adjustBounds() const
{
	return Deformer::adjustBounds() && namePlug()->getValue() == "P";
}

bool RandomPrimitiveVariable::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		ObjectProcessor::affectsProcessedObject( input ) ||
		input == namePlug() ||
		input == interpolationPlug() ||
		input == seedPrimitiveVariablePlug() ||
		input == seedPlug() ||
		input == distributionPlug() ||
		input->parent<Plug>() == intRangePlug() ||
		input->parent<Plug>() == floatRangePlug() ||
		input == meanPlug() ||
		input == deviationPlug() ||
		input->parent<Plug>() == choicesPlug() ||
		input == radiusPlug() ||
		input == interpretationPlug()
	;
}

void RandomPrimitiveVariable::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ObjectProcessor::hashProcessedObject( path, context, h );

	namePlug()->hash( h );
	interpolationPlug()->hash( h );
	seedPrimitiveVariablePlug()->hash( h );
	seedPlug()->hash( h );

	const Distribution distribution = (Distribution)distributionPlug()->getValue();
	h.append( (int)distribution );
	switch( distribution )
	{
		case UniformInt :
			intRangePlug()->hash( h );
			break;
		case UniformFloat :
			floatRangePlug()->hash( h );
			break;
		case Gaussian :
			meanPlug()->hash( h );
			deviationPlug()->hash( h );
			break;
		case WeightedChoice :
			choicesPlug()->hash( h );
			break;
		case HollowSphere :
			radiusPlug()->hash( h );
			interpretationPlug()->hash( h );
			break;
	}
}

IECore::ConstObjectPtr RandomPrimitiveVariable::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const Primitive *primitive = runTimeCast<const Primitive>( inputObject );
	const std::string name = namePlug()->getValue();
	if( !primitive || name.empty() )
	{
		return inputObject;
	}

	const PrimitiveVariable::Interpolation interpolation = (PrimitiveVariable::Interpolation)interpolationPlug()->getValue();
	const size_t variableSize = primitive->variableSize( interpolation );

	const PrimitiveVariable *seedVariable = nullptr;
	const std::string seedVariableName = seedPrimitiveVariablePlug()->getValue();
	if( !seedVariableName.empty() )
	{
		auto it = primitive->variables.find( seedVariableName );
		if( it == primitive->variables.end() )
		{
			throw IECore::Exception( fmt::format( "Seed primitive variable \"{}\" does not exist", seedVariableName ) );
		}
		if( it->second.interpolation != interpolation )
		{
			throw IECore::Exception( fmt::format( "Seed primitive variable \"{}\" has wrong interpolation", seedVariableName ) );
		}
		seedVariable = &it->second;
	}

	const int seed = seedPlug()->getValue();
	const Distribution distribution = (Distribution)distributionPlug()->getValue();

	PrimitiveVariable primitiveVariable( interpolation, nullptr );
	switch( distribution )
	{
		case UniformInt :
		{
			primitiveVariable.data = dispatchDistribution( UniformIntDistribution{ intRangePlug()->getValue() }, variableSize, seed, seedVariable );
			break;
		}
		case UniformFloat :
		{
			primitiveVariable.data = dispatchDistribution( UniformFloatDistribution{ floatRangePlug()->getValue() }, variableSize, seed, seedVariable );
			break;
		}
		case Gaussian :
		{
			primitiveVariable.data = dispatchDistribution(
				GaussianDistribution{ meanPlug()->getValue(), deviationPlug()->getValue() },
				variableSize, seed, seedVariable
			);
			break;
		}
		case WeightedChoice :
		{
			if( auto valuesPlug = choicesValuesPlug() )
			{
				ConstDataPtr valuesData = PlugAlgo::getValueAsData( valuesPlug );
				ConstFloatVectorDataPtr weightsData = choicesWeightsPlug()->getValue();
				DataPtr data = dispatchWeightedChoiceDistribution(
					valuesData.get(), weightsData->readable(),
					variableSize, seed, seedVariable
				);
				if( data->typeId() != valuesData->typeId() )
				{
					primitiveVariable.indices = assertedStaticCast<IntVectorData>( data );
					// Cast OK as we don't mutate the data and it will be const once we've
					// returned it.
					primitiveVariable.data = boost::const_pointer_cast<Data>( valuesData );
				}
				else
				{
					primitiveVariable.data = data;
				}
			}
			break;
		}
		case HollowSphere :
		{
			primitiveVariable.data = dispatchDistribution(
				HollowSphereDistribution{ radiusPlug()->getValue() },
				variableSize, seed, seedVariable
			);
			static_cast<V3fVectorData *>( primitiveVariable.data.get() )->setInterpretation(
				(GeometricData::Interpretation)interpretationPlug()->getValue()
			);
			break;
		}
	}

	if( !primitiveVariable.data )
	{
		return primitive;
	}

	PrimitivePtr result = primitive->copy();
	result->variables[name] = primitiveVariable;
	return result;
}

Gaffer::ValuePlug::CachePolicy RandomPrimitiveVariable::processedObjectComputeCachePolicy() const
{
	return ValuePlug::CachePolicy::TaskCollaboration;
}
