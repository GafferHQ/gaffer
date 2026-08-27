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

#include "GafferScene/SceneStats.h"

#include "GafferScene/SceneAlgo.h"

#include "Gaffer/Action.h"
#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/PlugType.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/TypedObjectPlug.h"
#include "Gaffer/TypedPlug.h"

#include "IECore/CompoundData.h"
#include "IECore/DataAlgo.h"
#include "IECore/NullObject.h"
#include "IECore/SimpleTypedData.h"

#include "boost/bind.hpp"

#include "tbb/enumerable_thread_specific.h"

#include <atomic>
#include <vector>

using namespace std;
using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

// If `plug` is a supported type, downcasts it to its true type and
// calls `functor( plug, args )`. Otherwise, does nothing.
/// \todo This is copied from Collect.cpp (but with only a subset of
/// the supported types). Should we consolidate them somewhere?
template<typename F>
void dispatchPlugFunction( const ValuePlug *plug, F &&functor )
{
	switch( (int)plug->typeId() )
	{
		case BoolPlugTypeId :
			functor( static_cast<const BoolPlug *>( plug ) );
			break;
		case IntPlugTypeId :
			functor( static_cast<const IntPlug *>( plug ) );
			break;
		case FloatPlugTypeId :
			functor( static_cast<const FloatPlug *>( plug ) );
			break;
		case V2iPlugTypeId :
			functor( static_cast<const V2iPlug *>( plug ) );
			break;
		case V3iPlugTypeId :
			functor( static_cast<const V3iPlug *>( plug ) );
			break;
		case V2fPlugTypeId :
			functor( static_cast<const V2fPlug *>( plug ) );
			break;
		case V3fPlugTypeId :
			functor( static_cast<const V3fPlug *>( plug ) );
			break;
		case Color3fPlugTypeId :
			functor( static_cast<const Color3fPlug *>( plug ) );
			break;
		case Color4fPlugTypeId :
			functor( static_cast<const Color4fPlug *>( plug ) );
			break;
		default :
			break;
	}
}

template<typename InputPlugType>
struct StatsTraits
{
	using SumDataType = TypedData<typename InputPlugType::ValueType>;
	using MinMaxDataType = TypedData<typename InputPlugType::ValueType>;
	using AverageDataType = TypedData<typename InputPlugType::ValueType>;
};

template<>
struct StatsTraits<BoolPlug>
{
	using SumDataType = IntData;
	using MinMaxDataType = BoolData;
	using AverageDataType = FloatData;
};

template<>
struct StatsTraits<IntPlug>
{
	using SumDataType = IntData;
	using MinMaxDataType = IntData;
	using AverageDataType = FloatData;
};

template<typename T>
struct StatsTraits<CompoundNumericPlug<Vec2<T>>>
{
	using SumDataType = GeometricTypedData<Vec2<T>>;
	using MinMaxDataType = GeometricTypedData<Vec2<T>>;
	using AverageDataType = GeometricTypedData<Vec2<float>>;
};

template<typename T>
struct StatsTraits<CompoundNumericPlug<Vec3<T>>>
{
	using SumDataType = GeometricTypedData<Vec3<T>>;
	using MinMaxDataType = GeometricTypedData<Vec3<T>>;
	using AverageDataType = GeometricTypedData<Vec3<float>>;
};

/// \todo This and `vectorAwareMax()` are borrowed from `TweakPlug.cpp`. Is
/// there anywhere we could share them? Or could we remove them and work on
/// `TypedData::baseWritable()` instead?
template<typename T>
T vectorAwareMin( const T &v1, const T &v2 )
{
	if constexpr( IECore::TypeTraits::IsVec<T>::value || IECore::TypeTraits::IsColor<T>::value )
	{
		T result;
		for( size_t i = 0; i < T::dimensions(); ++i )
		{
			result[i] = std::min( v1[i], v2[i] );
		}
		return result;
	}
	else
	{
		return std::min( v1, v2 );
	}
}

template<typename T>
T vectorAwareMax( const T &v1, const T &v2 )
{
	if constexpr( IECore::TypeTraits::IsVec<T>::value || IECore::TypeTraits::IsColor<T>::value )
	{
		T result;
		for( size_t i = 0; i < T::dimensions(); ++i )
		{
			result[i] = std::max( v1[i], v2[i] );
		}
		return result;
	}
	else
	{
		return std::max( v1, v2 );
	}
}

// Utility class for accumulating statistics from repeated
// evaluations of a plug.
struct PlugStats
{

	template<typename InputPlugType>
	void update( const InputPlugType *inputPlug )
	{
		using SumDataType = typename StatsTraits<InputPlugType>::SumDataType;
		using MinMaxDataType = typename StatsTraits<InputPlugType>::MinMaxDataType;
		if( !sum )
		{
			sum = new SumDataType( inputPlug->getValue() );
			min = new MinMaxDataType( inputPlug->getValue() );
			max = new MinMaxDataType( inputPlug->getValue() );
		}
		else
		{
			static_cast<SumDataType *>( sum.get() )->writable() += inputPlug->getValue();
			auto typedMin = static_cast<MinMaxDataType *>( min.get() );
			typedMin->writable() = vectorAwareMin( typedMin->readable(), inputPlug->getValue() );
			auto typedMax = static_cast<MinMaxDataType *>( max.get() );
			typedMax->writable() = vectorAwareMax( typedMax->readable(), inputPlug->getValue() );
		}
		count++;
	}

	template<typename InputPlugType>
	void update( const InputPlugType *inputPlug, const PlugStats &other )
	{
		if( !sum )
		{
			*this = other;
			return;
		}
		else
		{
			using SumDataType = typename StatsTraits<InputPlugType>::SumDataType;
			using MinMaxDataType = typename StatsTraits<InputPlugType>::MinMaxDataType;
			static_cast<SumDataType *>( sum.get() )->writable() += static_cast<const SumDataType *>( other.sum.get() )->readable();
			static_cast<MinMaxDataType *>( min.get() )->writable() = vectorAwareMin(
				static_cast<const MinMaxDataType *>( min.get() )->readable(),
				static_cast<const MinMaxDataType *>( other.min.get() )->readable()
			);
			static_cast<MinMaxDataType *>( max.get() )->writable() = vectorAwareMax(
				static_cast<const MinMaxDataType *>( max.get() )->readable(),
				static_cast<const MinMaxDataType *>( other.max.get() )->readable()
			);
			count += other.count;
		}
	}

	template<typename InputPlugType>
	void finalise()
	{
		if( !sum )
		{
			return;
		}
		using SumDataType = typename StatsTraits<InputPlugType>::SumDataType;
		using AverageDataType = typename StatsTraits<InputPlugType>::AverageDataType;
		using AverageValueType = typename AverageDataType::ValueType;
		const auto &sumValue = static_cast<const SumDataType *>( sum.get() )->readable();
		average = new AverageDataType( AverageValueType( sumValue ) / float( count ) );
	}

	IECore::DataPtr sum;
	IECore::DataPtr min;
	IECore::DataPtr max;
	IECore::DataPtr average;
	size_t count = 0;

};

// Holds a map from name to PlugStats in a form suitable for storage
// on a plug.
struct StatsData : public IECore::Data
{

	static IECore::MurmurHash hash( const ValuePlug *queriesPlug )
	{
		IECore::MurmurHash result;
		for( const OptionalValuePlugPtr &queryPlug : OptionalValuePlug::Range( *queriesPlug ) )
		{
			result.append( queryPlug->getName() );
			if( queryPlug->enabledPlug()->getValue() )
			{
				queryPlug->hash( result );
			}
		}
		return result;
	}

	void update( const ValuePlug *queriesPlug )
	{
		for( const auto &queryPlug : OptionalValuePlug::Range( *queriesPlug ) )
		{
			if( queryPlug->enabledPlug()->getValue() )
			{
				dispatchPlugFunction(
					queryPlug->valuePlug(), [&] ( auto *plug ) { map[queryPlug->getName()].update( plug ); }
				);
			}
		}
	}

	void update( const ValuePlug *queriesPlug, const StatsData &other )
	{
		for( const auto &queryPlug : OptionalValuePlug::Range( *queriesPlug ) )
		{
			dispatchPlugFunction(
				queryPlug->valuePlug(), [&] ( auto *plug ) {
					auto it = other.map.find( queryPlug->getName() );
					if( it != other.map.end() )
					{
						map[queryPlug->getName()].update( plug, it->second );
					}
				}
			);
		}
	}

	void finalise( const ValuePlug *queriesPlug )
	{
		for( const auto &queryPlug : OptionalValuePlug::Range( *queriesPlug ) )
		{
			dispatchPlugFunction(
				queryPlug->valuePlug(), [&] ( auto *plug ) {
					using InputPlugType = remove_const_t<remove_pointer_t<decltype( plug )>>;
					auto it = map.find( queryPlug->getName() );
					if( it != map.end() )
					{
						it->second.finalise<InputPlugType>();
					}
				}
			);
		}
	}

	IE_CORE_DECLAREMEMBERPTR( StatsData )
	using Map = std::unordered_map<InternedString, PlugStats>;
	Map map;

};

const InternedString g_average( "average" );
const InternedString g_count( "count" );
const InternedString g_min( "min" );
const InternedString g_max( "max" );
const InternedString g_sum( "sum" );

} // namespace

//////////////////////////////////////////////////////////////////////////
// SceneStats
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( SceneStats )

size_t SceneStats::g_firstPlugIndex = 0;

SceneStats::SceneStats( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "scene" ) );
	addChild( new FilterPlug( "filter" ) );
	// Rejecting inputs to avoid unwanted connections being made in the GraphEditor
	// when we don't yet have any queries.
	addChild( new ValuePlug( "queries", Plug::In, Plug::Default & ~Plug::AcceptsInputs ) );
	addChild( new ValuePlug( "out", Plug::Out ) );
	addChild( new ObjectPlug( "__statsData", Plug::Out, NullObject::defaultNullObject() ) );
}

SceneStats::~SceneStats()
{
}

GafferScene::ScenePlug *SceneStats::scenePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const GafferScene::ScenePlug *SceneStats::scenePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

GafferScene::FilterPlug *SceneStats::filterPlug()
{
	return getChild<FilterPlug>( g_firstPlugIndex + 1 );
}

const GafferScene::FilterPlug *SceneStats::filterPlug() const
{
	return getChild<FilterPlug>( g_firstPlugIndex + 1 );
}

Gaffer::ValuePlug *SceneStats::queriesPlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 2 );
}

const Gaffer::ValuePlug *SceneStats::queriesPlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 2 );
}

Gaffer::ValuePlug *SceneStats::outPlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 3 );
}

const Gaffer::ValuePlug *SceneStats::outPlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 3 );
}

Gaffer::ObjectPlug *SceneStats::statsDataPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::ObjectPlug *SceneStats::statsDataPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 4 );
}

Gaffer::OptionalValuePlug *SceneStats::addQuery( const Gaffer::ValuePlug *plug, const std::string &name )
{
	const std::string actualName = name.empty() ? plug->getName().string() : name;
	ValuePlugPtr valuePlug = boost::static_pointer_cast<ValuePlug>( plug->createCounterpart( actualName, Plug::In ) );
	OptionalValuePlugPtr inChild = new OptionalValuePlug( actualName, valuePlug, true );

	PlugPtr outChild = new ValuePlug( actualName, Plug::Out );
	dispatchPlugFunction(
		plug, [&] ( auto *plug ) {
			using InputPlugType = remove_const_t<remove_pointer_t<decltype( plug )>>;
			using SumType = typename StatsTraits<InputPlugType>::SumDataType::ValueType;
			using SumPlugType = typename PlugType<SumType>::Type;
			outChild->addChild( new SumPlugType( g_sum, Plug::Out ) );
			using MinMaxType = typename StatsTraits<InputPlugType>::MinMaxDataType::ValueType;
			using MinMaxPlugType = typename PlugType<MinMaxType>::Type;
			outChild->addChild( new MinMaxPlugType( g_min, Plug::Out ) );
			outChild->addChild( new MinMaxPlugType( g_max, Plug::Out ) );
			outChild->addChild( new IntPlug( g_count, Plug::Out ) );
			using AverageType = typename StatsTraits<InputPlugType>::AverageDataType::ValueType;
			using AveragePlugType = typename PlugType<AverageType>::Type;
			outChild->addChild( new AveragePlugType( g_average, Plug::Out ) );
		}
	);

	queriesPlug()->addChild( inChild );
	outPlug()->addChild( outChild );

	inChild->nameChangedSignal().connect( boost::bind( &SceneStats::queryNameChanged, this, ::_1, ::_2 ) );

	return inChild.get();
}

void SceneStats::removeQuery( Gaffer::ValuePlug *plug )
{
	ValuePlug *out = outPlug()->getChild<ValuePlug>( plug->getName() );
	queriesPlug()->removeChild( plug );
	outPlug()->removeChild( out );
}

void SceneStats::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input->parent<Plug>() == scenePlug() )
	{
		filterPlug()->sceneAffects( input, outputs );
		outputs.push_back( statsDataPlug() );
	}

	if( input == filterPlug() )
	{
		outputs.push_back( statsDataPlug() );
	}

	if( queriesPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( statsDataPlug() );
	}

	if( input == statsDataPlug() )
	{
		for( const auto &output : ValuePlug::RecursiveRange( *outPlug() ) )
		{
			if( output->children().empty() )
			{
				outputs.push_back( output.get() );
			}
		}
	}
}

void SceneStats::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == statsDataPlug() )
	{
		ComputeNode::hash( output, context, h );

		std::atomic<uint64_t> h1( 0 ), h2( 0 );
		auto functor = [&]( const ScenePlug *scene, const ScenePlug::ScenePath &path ) -> bool
		{
			IECore::MurmurHash locationHash = StatsData::hash( queriesPlug() );
			h1 += locationHash.h1();
			h2 += locationHash.h2();
			return true;
		};
		SceneAlgo::filteredParallelTraverse( scenePlug(), filterPlug(), functor );
		h.append( IECore::MurmurHash( h1.load(), h2.load() ) );
	}
	else if( outPlug()->isAncestorOf( output ) )
	{
		ComputeNode::hash( output, context, h );
		statsDataPlug()->hash( h );
		// We also use the plug's name in the compute, but ComputeNode
		// includes that in the hash for us anyway.
	}
	else
	{
		ComputeNode::hash( output, context, h );
	}
}

void SceneStats::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == statsDataPlug() )
	{
		tbb::enumerable_thread_specific<StatsData> threadStats;

		auto functor = [&]( const ScenePlug *scene, const ScenePlug::ScenePath &path ) -> bool
		{
			threadStats.local().update( queriesPlug() );
			return true;
		};
		/// \todo Because we're computing stats for all locations in one go,
		/// we lose all the work done so far if we're cancelled part way through.
		/// Consider instead computing aggregate stats for each location (and its
		/// descendants) using an internal plug. Then when restarting after cancellation,
		/// we can reuse cached results for any locations that were processed fully the
		/// first time.
		SceneAlgo::filteredParallelTraverse( scenePlug(), filterPlug(), functor );

		StatsData::Ptr result = new StatsData;
		for( const auto &statsData : threadStats )
		{
			result->update( queriesPlug(), statsData );
		}
		result->finalise( queriesPlug() );

		static_cast<ObjectPlug *>( output )->setValue( result );
	}
	else if( outPlug()->isAncestorOf( output ) )
	{
		auto [topOutput, statOutput] = outPlugAncestors( output );

		StatsData::ConstPtr data = boost::static_pointer_cast<const StatsData>( statsDataPlug()->getValue() );
		auto it = data->map.find( topOutput->getName() );
		if( it == data->map.end() )
		{
			// We didn't collect anything.
			output->setToDefault();
		}
		else
		{
			const auto &stats = it->second;
			if( statOutput->getName() == g_count )
			{
				static_cast<IntPlug *>( output )->setValue( stats.count );
			}
			else if( statOutput->getName() == g_sum )
			{
				PlugAlgo::setValueFromData( statOutput, output, stats.sum.get() );
			}
			else if( statOutput->getName() == g_min )
			{
				PlugAlgo::setValueFromData( statOutput, output, stats.min.get() );
			}
			else if( statOutput->getName() == g_max )
			{
				PlugAlgo::setValueFromData( statOutput, output, stats.max.get() );
			}
			else if( statOutput->getName() == g_average )
			{
				PlugAlgo::setValueFromData( statOutput, output, stats.average.get() );
			}
		}
	}
	else
	{
		ComputeNode::compute( output, context );
	}
}

void SceneStats::queryNameChanged( const GraphComponent *query, IECore::InternedString oldName )
{
	if( query->parent() != queriesPlug() )
	{
		// Query was removed, so we are no longer managing
		// name changes.
		return;
	}

	const ScriptNode *script = scriptNode();
	if(
		script &&
		( script->currentActionStage() == Action::Undo || script->currentActionStage() == Action::Redo )
	)
	{
		// Our name synchronisation will have been recorded the first time round,
		// so we can just let it do/undo as normal.
		return;
	}

	if( auto out = outPlug()->getChild<Plug>( oldName ) )
	{
		out->setName( query->getName() );
	}
	else
	{
		IECore::msg( IECore::Msg::Warning, "SceneStats::queryNameChanged", "No output called \"{}\"", oldName.string() );
	}
}

std::tuple<const ValuePlug *, const ValuePlug *> SceneStats::outPlugAncestors( const Gaffer::ValuePlug *output ) const
{
	const ValuePlug *parentPlug = output->parent<ValuePlug>();
	while( parentPlug->parent() != outPlug() )
	{
		output = parentPlug;
		parentPlug = output->parent<ValuePlug>();
	}

	return { parentPlug, output };
}
