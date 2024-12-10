//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/PrimitiveVariableTweaks.h"

#include "IECoreScene/Primitive.h"

#include "IECore/DataAlgo.h"

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

namespace {

// Rather startling that this doesn't already exist, but it seems that there isn't anywhere else where we
// report exceptions with interpolations in C++.
std::string interpolationToString( PrimitiveVariable::Interpolation i )
{
	switch( i )
	{
		case PrimitiveVariable::Constant:
			return "Constant";
		case PrimitiveVariable::Uniform:
			return "Uniform";
		case PrimitiveVariable::Vertex:
			return "Vertex";
		case PrimitiveVariable::Varying:
			return "Varying";
		case PrimitiveVariable::FaceVarying:
			return "FaceVarying";
		default:
			return "Invalid";
	};
}

template <typename T>
void removeUnusedElements( std::vector<int> &indices, std::vector<T> &data )
{
	std::vector<int> used( data.size(), -1 );

	for( const int &i : indices )
	{
		used[i] = 1;
	}

	int accum = 0;
	for( int &i : used )
	{
		if( i != -1 )
		{
			i = accum;
			accum += 1;
		}
	}

	if( accum == (int)data.size() )
	{
		// All elements were used
		return;
	}

	std::vector<T> result;
	result.reserve( accum );
	for( size_t j = 0; j < data.size(); j++ )
	{
		if( used[j] != -1 )
		{
			result.push_back( data[j] );
		}
	}

	for( int &i : indices )
	{
		i = used[i];
	}

	data.swap( result );
}

template< typename T>
bool constexpr hasZeroConstructor()
{
	// Some types, like V3f and Color3f, won't default initialize unless we explicitly
	// pass 0 to the constructor. Other types don't have a constructor that accepts 0,
	// so we need to distinguish the two somehow. Currently, I'm using a blacklist of
	// types that don't need to be initialized to zero ... my rationale is that if a new
	// type is added, I would rather get a compile error than get uninitialized memory.
	return !(
		TypeTraits::IsBox< T >::value ||
		TypeTraits::IsMatrix< T >::value ||
		TypeTraits::IsQuat< T >::value ||
		std::is_same_v< T, InternedString > || // I don't think InternedString primvars can exist, but the dispatch still covers this type
		std::is_same_v< T, std::string >
	);
}

void applyTweakToPrimVars(
	Primitive *prim, PrimitiveVariable::Interpolation targetInterpolation,
	const std::string &name, TweakPlug::Mode mode, IECore::DataPtr tweakData, bool ignoreMissing,
	const Int64VectorData *idList
)
{
	if( name.empty() )
	{
		return;
	}

	if( mode == Gaffer::TweakPlug::Remove )
	{
		prim->variables.erase( name );
		return;
	}

	auto primVarIt = prim->variables.find( name );
	bool hasSource = primVarIt != prim->variables.end();

	if( !prim->arePrimitiveVariablesValid() )
	{
		throw IECore::Exception( "Primitive variable tweak failed - input primitive variables are not valid." );
	}

	if( !hasSource && mode == Gaffer::TweakPlug::ListRemove )
	{
		// For consistency with the usual operation of TweakPlug, we consider this a success, whether
		// or not ignoreMissing is set.
		return;
	}

	// There are several combinations of parameters that could result in "just create a fresh primvar"
	if(
		// Most obviously, the user could have selected Create
		mode == Gaffer::TweakPlug::Create || mode == Gaffer::TweakPlug::CreateIfMissing ||

		// Or if they are adding to a list that doesn't exist
		( !hasSource && ( mode == Gaffer::TweakPlug::ListAppend || mode == Gaffer::TweakPlug::ListPrepend ) )
	)
	{
		if( mode == Gaffer::TweakPlug::CreateIfMissing && hasSource )
		{
			// Don't need to create in this mode if there's already something there
			return;
		}

		if( targetInterpolation == PrimitiveVariable::Invalid )
		{
			throw IECore::Exception( fmt::format( "Cannot create primitive variable {} when \"interpolation\" is set to \"Any\". Please select an interpolation.", name ) );
		}
		else if( targetInterpolation == PrimitiveVariable::Constant )
		{
			prim->variables[name] = PrimitiveVariable( PrimitiveVariable::Constant, tweakData );
			return;
		}

		// Make a fresh primvar using the supplied value as every element of the vector

		const size_t variableSize = prim->variableSize( targetInterpolation );

		prim->variables[name] = IECore::dispatch( tweakData.get(),
			[&targetInterpolation, &variableSize, &name, &idList]( const auto *typedTweakData ) -> PrimitiveVariable
			{
				using DataType = typename std::remove_const_t<std::remove_pointer_t<decltype( typedTweakData )> >;
				using ValueType = typename DataType::ValueType;

				if constexpr(
					TypeTraits::IsTypedData< DataType >::value &&
					!TypeTraits::IsVectorTypedData< DataType >::value &&

					// A bunch of things we're not allowed to make vectors of
					!TypeTraits::IsTransformationMatrix< ValueType >::value &&
					!TypeTraits::IsSpline< ValueType >::value &&
					!std::is_same_v< ValueType, PathMatcher > &&
					!std::is_same_v< ValueType, boost::posix_time::ptime >
				)
				{
					constexpr bool isGeometric = TypeTraits::IsGeometricTypedData< DataType >::value;
					using VectorDataType = std::conditional_t<
						isGeometric,
						IECore::GeometricTypedData< std::vector< ValueType > >,
						IECore::TypedData< std::vector< ValueType > >
					>;

					typename VectorDataType::Ptr vectorData = new VectorDataType();

					if( idList )
					{
						// If there is an idList, we will only give the specified value to the targeted ids.
						// Everything else just gets default initialized.

						// Some types, like V3f and Color3f, won't default initialize unless we explicitly
						// pass 0 to the constructor. Other types don't have a constructor that accepts 0,
						// so we need to distinguish the two somehow. Currently, I'm using a blacklist of
						// types that don't need to be initialized to zero ... my rationale is that if a new
						// type is added, I would rather get a compile error than get uninitialized memory.
						if constexpr( !hasZeroConstructor< ValueType >() )
						{
							vectorData->writable().resize( variableSize, ValueType() );
						}
						else
						{
							vectorData->writable().resize( variableSize, ValueType( 0 ) );
						}
					}
					else
					{
						// If there is no idList, we can immediately set everything to the correct value.
						vectorData->writable().resize( variableSize, typedTweakData->readable() );
					}

					if constexpr( isGeometric )
					{
						vectorData->setInterpretation( typedTweakData->getInterpretation() );
					}

					return PrimitiveVariable( targetInterpolation, std::move( vectorData ) );
				}
				else
				{
					throw IECore::Exception( fmt::format(
						"Invalid type \"{}\" for non-constant primitive variable tweak \"{}\".",
						typedTweakData->typeName(), name
					) );
				}
			}
		);

		if( idList )
		{
			// Since we have an idList and we're only giving the specified value to part of the new primvar,
			// we continue through the rest of this function as if we were in replace mode.
			primVarIt = prim->variables.find( name );
			hasSource = true;
			mode = Gaffer::TweakPlug::Replace;
		}
		else
		{
			return;
		}
	}


	if( !hasSource )
	{
		if( ignoreMissing )
		{
			return;
		}
		else
		{
			throw IECore::Exception( fmt::format( "Cannot apply tweak with mode {} to \"{}\" : This parameter does not exist.", TweakPlug::modeToString( mode ), name ) );
		}
	}

	PrimitiveVariable &targetVar = primVarIt->second;

	if( targetInterpolation != PrimitiveVariable::Invalid && targetVar.interpolation != targetInterpolation )
	{
		// \todo - Throwing an exception here is probably not the most useful to users. More useful options might
		// be "ignore primvars that don't match" or "resample primvars so they do match" ... but we're not sure
		// which is right, and we don't want to add additional options to control this unless it's absolutely
		// needed. For now, making it an exception makes it easier to modify this behaviour in the future.
		//
		// Note that one case where the correct behaviour is pretty easy to define is if we are in mode Uniform
		// or Vertex, and we encounter a primvar with FaceVarying interpolation. The correct behaviour there is
		// is pretty clearly to apply the tweak to all FaceVertices corresponding to the selected Faces or Vertices.
		// We haven't implemented this yet, but it would be pretty straightforward to make things behave properly
		// instead of throwing in that specific case at least.
		throw IECore::Exception( fmt::format(
			"Cannot apply tweak to \"{}\" : Interpolation \"{}\" doesn't match primitive variable interpolation \"{}\".",
			name, interpolationToString( targetInterpolation ), interpolationToString( targetVar.interpolation )
		) );
	}

	if( targetVar.interpolation == PrimitiveVariable::Constant )
	{
		IECore::dispatch( targetVar.data.get(),
			[&tweakData, &targetVar, &mode, &name]( auto *typedData )
			{
				using SourceType = typename std::remove_pointer_t<decltype( typedData )>;

				if constexpr( TypeTraits::IsTypedData< SourceType >::value )
				{
					auto &result = typedData->writable();

					const SourceType* tweakDataTyped = IECore::runTimeCast< SourceType >( tweakData.get() );

					if( !tweakDataTyped )
					{
						throw IECore::Exception( fmt::format(
							"Cannot apply tweak to \"{}\" : Variable data of type \"{}\" does not match "
							"parameter of type \"{}\".", name, typedData->typeName(), tweakData->typeName()
						) );
					}

					result = TweakPlug::applyValueTweak( result, tweakDataTyped->readable(), mode, name );
				}
			}
		);
		return;
	}

	IECore::dispatch( targetVar.data.get(),
		[&tweakData, &targetVar, &mode, &name, &idList]( auto *typedData )
		{
			using SourceType = typename std::remove_pointer_t<decltype( typedData )>;
			if constexpr( TypeTraits::IsVectorTypedData< SourceType >::value )
			{
				auto &result = typedData->writable();
				using ElementType = typename SourceType::ValueType::value_type;
				using ElementDataType = IECore::TypedData< ElementType >;

				const ElementDataType* tweakDataTyped = IECore::runTimeCast< ElementDataType >( tweakData.get() );
				if( !tweakDataTyped )
				{
					throw IECore::Exception(
						fmt::format(
							"Cannot apply tweak to \"{}\" : Parameter should be of type \"{}\" in order to apply "
							"to an element of \"{}\", but got \"{}\" instead.",
							name, ElementDataType::staticTypeName(), typedData->typeName(), tweakData->typeName()
						)
					);
				}

				auto &tweak = tweakDataTyped->readable();

				if( idList && targetVar.indices )
				{
					// OK, this is a somewhat complex special case - we are only tweaking some data, based
					// on indices, but some indices currently refer to the same data. If we end up tweaking
					// only some of the indices that currently refer to the same data, then we're splitting
					// it into two different values, and need to add a new piece of data to hold the new
					// value.

					result.reserve( result.size() + idList->readable().size() );

					std::vector<int> &indices = targetVar.indices->writable();
					std::unordered_map< int, int > tweakedIndices;

					for( int64_t i : idList->readable() )
					{
						if( i >= 0 && i <= (int64_t)indices.size() )
						{
							auto[ it, inserted ] = tweakedIndices.try_emplace( indices[i], result.size() );
							if( inserted )
							{
								result.push_back( TweakPlug::applyValueTweak<ElementType>( result[indices[i]], tweak, mode, name ) );
							}
							indices[i] = it->second;
						}
					}

					// If we actually ended up tweaking all indices that used a piece of data, that data is now
					// abandoned, so we should now do a scan to remove unused data.
					removeUnusedElements( indices, result );
				}
				else if( idList )
				{
					// If there are no indices, then we just modify the data the ids point to
					for( int64_t i : idList->readable() )
					{
						if( i >= 0 && i <= (int64_t)result.size() )
						{
							result[i] = TweakPlug::applyValueTweak<ElementType>( result[i], tweak, mode, name );
						}
					}
				}
				else
				{
					// If there is no id list given, we're just modifying all the data, and it doesn't matter
					// whether or not there are indices.

					// I probably should have paid more attention to what r-value references are in general,
					// but in this case it seems like a pretty safe way to force this to work with the
					// vector-of-bool weirdness
					for( auto &&i : result )
					{
						i = TweakPlug::applyValueTweak<ElementType>( i, tweak, mode, name );
					}
				}
			}
			else
			{
				throw IECore::Exception( fmt::format(
					"Found invalid primitive variable \"{}\" : Expected vector typed data, got \"{}\".",
					name, typedData->typeName()
				) );
			}
		}
	);
}

} // namespace

GAFFER_NODE_DEFINE_TYPE( PrimitiveVariableTweaks );

size_t PrimitiveVariableTweaks::g_firstPlugIndex = 0;

PrimitiveVariableTweaks::PrimitiveVariableTweaks( const std::string &name )
	:	ObjectProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "interpolation", Plug::In, PrimitiveVariable::Invalid, PrimitiveVariable::Invalid, PrimitiveVariable::FaceVarying ) );
	addChild( new IntPlug( "selectionMode", Plug::In, (int)SelectionMode::All, (int)SelectionMode::All, (int)SelectionMode::MaskPrimitiveVariable ) );
	addChild( new Int64VectorDataPlug( "idList", Plug::In ) );
	addChild( new StringPlug( "idListVariable", Plug::In, "" ) );
	addChild( new StringPlug( "id", Plug::In, "" ) );
	addChild( new StringPlug( "maskVariable", Plug::In, "" ) );
	addChild( new BoolPlug( "ignoreMissing", Plug::In, false ) );
	addChild( new TweaksPlug( "tweaks" ) );
}

PrimitiveVariableTweaks::~PrimitiveVariableTweaks()
{
}

Gaffer::IntPlug *PrimitiveVariableTweaks::interpolationPlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 0 );
}

const Gaffer::IntPlug *PrimitiveVariableTweaks::interpolationPlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 0 );
}

Gaffer::IntPlug *PrimitiveVariableTweaks::selectionModePlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *PrimitiveVariableTweaks::selectionModePlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::Int64VectorDataPlug *PrimitiveVariableTweaks::idListPlug()
{
	return getChild<Gaffer::Int64VectorDataPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::Int64VectorDataPlug *PrimitiveVariableTweaks::idListPlug() const
{
	return getChild<Gaffer::Int64VectorDataPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *PrimitiveVariableTweaks::idListVariablePlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *PrimitiveVariableTweaks::idListVariablePlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *PrimitiveVariableTweaks::idPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *PrimitiveVariableTweaks::idPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 4 );
}

Gaffer::StringPlug *PrimitiveVariableTweaks::maskVariablePlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::StringPlug *PrimitiveVariableTweaks::maskVariablePlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 5 );
}

Gaffer::BoolPlug *PrimitiveVariableTweaks::ignoreMissingPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::BoolPlug *PrimitiveVariableTweaks::ignoreMissingPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 6 );
}

Gaffer::TweaksPlug *PrimitiveVariableTweaks::tweaksPlug()
{
	return getChild<Gaffer::TweaksPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::TweaksPlug *PrimitiveVariableTweaks::tweaksPlug() const
{
	return getChild<Gaffer::TweaksPlug>( g_firstPlugIndex + 7 );
}

bool PrimitiveVariableTweaks::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		ObjectProcessor::affectsProcessedObject( input ) ||
		input == interpolationPlug() ||
		input == selectionModePlug() ||
		input == idListPlug() ||
		input == idListVariablePlug() ||
		input == idPlug() ||
		input == maskVariablePlug() ||
		input == ignoreMissingPlug() ||
		tweaksPlug()->isAncestorOf( input )
	;
}

void PrimitiveVariableTweaks::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( tweaksPlug()->children().empty() )
	{
		h = inPlug()->objectPlug()->hash();
	}
	else
	{
		ObjectProcessor::hashProcessedObject( path, context, h );
		interpolationPlug()->hash( h );
		selectionModePlug()->hash( h );
		idListPlug()->hash( h );
		idListVariablePlug()->hash( h );
		idPlug()->hash( h );
		maskVariablePlug()->hash( h );
		ignoreMissingPlug()->hash( h );
		tweaksPlug()->hash( h );
	}
}

IECore::ConstObjectPtr PrimitiveVariableTweaks::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const Primitive *inputPrimitive = runTimeCast<const Primitive>( inputObject );
	if( !inputPrimitive || tweaksPlug()->children().empty() )
	{
		return inputObject;
	}

	PrimitiveVariable::Interpolation targetInterpolation = (PrimitiveVariable::Interpolation)interpolationPlug()->getValue();

	const bool ignoreMissing = ignoreMissingPlug()->getValue();

	PrimitivePtr result = inputPrimitive->copy();

	SelectionMode selectionMode = (SelectionMode)selectionModePlug()->getValue();
	ConstInt64VectorDataPtr idList;
	if( ( selectionMode == SelectionMode::IdList || selectionMode == SelectionMode::IdListPrimitiveVariable ) && targetInterpolation != PrimitiveVariable::Invalid )
	{
		if( selectionMode == SelectionMode::IdList )
		{
			idList = idListPlug()->getValue();
		}
		else
		{
			std::string idListVarName = idListVariablePlug()->getValue();
			auto idListVar = inputPrimitive->variables.find( idListVarName );
			if( idListVar == inputPrimitive->variables.end() )
			{
				throw IECore::Exception( fmt::format( "Can't find id list primitive variable \"{}\".", idListVarName ) );

			}

			if( idListVar->second.interpolation == PrimitiveVariable::Interpolation::Constant )
			{
				if( const Int64VectorData *int64Data = IECore::runTimeCast<Int64VectorData>( idListVar->second.data.get() ) )
				{
					idList = int64Data;
				}
				else if( const IntVectorData *intData = IECore::runTimeCast<IntVectorData>( idListVar->second.data.get() ) )
				{
					// For simplicity elsewhere, just convert to an Int64VectorData instead of supporting both types
					Int64VectorDataPtr convertedData = new Int64VectorData();
					auto &converted = convertedData->writable();
					converted.reserve( intData->readable().size() );
					for( int i : intData->readable() )
					{
						converted.push_back( i );
					}

					idList = convertedData;
				}
			}

			if( !idList )
			{
				throw IECore::Exception( fmt::format( "Invalid id list primitive variable \"{}\". A constant IntVector or Int64Vector is required.", idListVarName ) );
			}

		}

		std::string idVarName = idPlug()->getValue();
		if( idVarName.size() )
		{
			Int64VectorDataPtr mappedIdListData = new Int64VectorData();
			std::vector< int64_t > &mappedIdList = mappedIdListData->writable();
			mappedIdList.reserve( idList->readable().size() );

			std::unordered_set< int64_t > idSet( idList->readable().begin(), idList->readable().end() );

			auto idVar = inputPrimitive->variables.find( idVarName );
			if( idVar == inputPrimitive->variables.end() )
			{
				throw IECore::Exception( fmt::format( "Id invalid, can't find primitive variable \"{}\".", idVarName ) );
			}

			if( idVar->second.interpolation != targetInterpolation )
			{
				throw IECore::Exception( fmt::format(
					"Id variable \"{}\" : Interpolation \"{}\" doesn't match specified interpolation \"{}\".",
					idVarName, interpolationToString( idVar->second.interpolation ), interpolationToString( targetInterpolation )
				) );
			}

			if( idVar->second.indices )
			{
				throw IECore::Exception( fmt::format( "Id variable \"{}\" is not allowed to be indexed.", idVarName ) );
			}

			if( const IntVectorData *intIdsData = IECore::runTimeCast<IntVectorData>( idVar->second.data.get() ) )
			{
				const std::vector<int> &intIds = intIdsData->readable();
				for( size_t i = 0; i < intIds.size(); i++ )
				{
					if( idSet.count( intIds[i] ) )
					{
						mappedIdList.push_back( i );
					}
				}
			}
			else if( const Int64VectorData *int64IdsData = IECore::runTimeCast<Int64VectorData>( idVar->second.data.get() ) )
			{
				const std::vector<int64_t> &intIds = int64IdsData->readable();
				for( size_t i = 0; i < intIds.size(); i++ )
				{
					if( idSet.count( intIds[i] ) )
					{
						mappedIdList.push_back( i );
					}
				}
			}
			else
			{
				throw IECore::Exception( fmt::format( "Id invalid, can't find primitive variable \"{}\" of type IntVectorData or type Int64VectorData.", idVarName ) );
			}

			idList = mappedIdListData;
		}
	}
	else if( selectionMode == SelectionMode::MaskPrimitiveVariable && targetInterpolation != PrimitiveVariable::Invalid )
	{
		std::string maskVarName = maskVariablePlug()->getValue();
		auto maskVar = inputPrimitive->variables.find( maskVarName );

		if( maskVar == inputPrimitive->variables.end() )
		{
			throw IECore::Exception( fmt::format( "Can't find mask primitive variable \"{}\".", maskVarName ) );
		}

		if( maskVar->second.interpolation != targetInterpolation )
		{
			throw IECore::Exception( fmt::format(
				"Mask primitive variable \"{}\" has wrong interpolation \"{}\", expected \"{}\".",
				maskVarName, interpolationToString( maskVar->second.interpolation ), interpolationToString( targetInterpolation )
			) );
		}

		// It would be a bit more efficient to directly use the mask to set elements, but to avoid a combinatorial
		// increase in the number of code paths, we just convert the mask into a list of ids to be tweaked.
		Int64VectorDataPtr idListTranslatedData = new Int64VectorData();
		std::vector< int64_t > &idListTranslated = idListTranslatedData->writable();

		IECore::dispatch( maskVar->second.data.get(),
			[&idListTranslated, &maskVar, &maskVarName]( auto *typedData )
			{
				using SourceType = typename std::remove_pointer_t<decltype( typedData )>;

				if constexpr( TypeTraits::IsVectorTypedData< SourceType >::value )
				{
					using ValueType = typename SourceType::ValueType::value_type;

					if constexpr( hasZeroConstructor<ValueType>() )
					{
						PrimitiveVariable::IndexedView<ValueType> indexedView( maskVar->second );
						ValueType defaultValue( 0 );

						for( size_t i = 0; i < indexedView.size(); i++ )
						{
							if( indexedView[i] != defaultValue )
							{
								idListTranslated.push_back( i );
							}
						}
						return;
					}
				}

				throw IECore::Exception( fmt::format(
					"Mask primitive variable \"{}\" has invalid type \"{}\".",
					maskVarName, typedData->typeName()
				) );
			}
		);

		idList = idListTranslatedData;

	}

	for( const auto &tweak : TweakPlug::Range( *tweaksPlug() ) )
	{
		// This reproduces most of the logic from TweakPlug::applyTweak, but for PrimVars instead of Data
		if( !tweak->enabledPlug()->getValue() )
		{
			continue;
		}

		std::string name = tweak->namePlug()->getValue();

		IECore::DataPtr tweakData = Gaffer::PlugAlgo::getValueAsData( tweak->valuePlug() );
		if( !tweakData )
		{
			throw IECore::Exception(
				fmt::format( "Cannot apply tweak to \"{}\" : Value plug has unsupported type \"{}\".", name, tweak->valuePlug()->typeName() )
			);
		}

		applyTweakToPrimVars(
			result.get(), targetInterpolation,
			name, static_cast<TweakPlug::Mode>( tweak->modePlug()->getValue() ),
			std::move( tweakData ), ignoreMissing, idList.get()
		);
	}

	return result;
}
