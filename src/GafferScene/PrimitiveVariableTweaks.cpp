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

#include "IECore/TypeTraits.h"
#include <unordered_set>

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

} // namespace

GAFFER_NODE_DEFINE_TYPE( PrimitiveVariableTweaks );

size_t PrimitiveVariableTweaks::g_firstPlugIndex = 0;

PrimitiveVariableTweaks::PrimitiveVariableTweaks( const std::string &name )
	:	Deformer( name )
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
		Deformer::affectsProcessedObject( input ) ||
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
		Deformer::hashProcessedObject( path, context, h );
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

	PrimitivePtr result = inputPrimitive->copy();

	SelectionMode selectionMode = (SelectionMode)selectionModePlug()->getValue();
	boost::dynamic_bitset<> mask;

	if(
		( selectionMode == SelectionMode::IdList || selectionMode == SelectionMode::IdListPrimitiveVariable ) &&
		targetInterpolation != PrimitiveVariable::Invalid && targetInterpolation != PrimitiveVariable::Constant
	)
	{
		ConstIntVectorDataPtr idList;
		ConstInt64VectorDataPtr idList64;
		if( selectionMode == SelectionMode::IdList )
		{
			idList64 = idListPlug()->getValue();
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
					idList64 = int64Data;
				}
				else if( const IntVectorData *intData = IECore::runTimeCast<IntVectorData>( idListVar->second.data.get() ) )
				{
					idList = intData;
				}
			}

			if( !( idList || idList64 ) )
			{
				throw IECore::Exception( fmt::format( "Invalid id list primitive variable \"{}\". A constant IntVector or Int64Vector is required.", idListVarName ) );
			}

		}

		const size_t variableSize = inputPrimitive->variableSize( targetInterpolation );
		mask.resize( variableSize, false );
		std::string idVarName = idPlug()->getValue();
		if( !idVarName.size() )
		{
			if( idList64 )
			{
				for( int64_t i : idList64->readable() )
				{
					if( i >= 0 && i < (int64_t)variableSize )
					{
						mask[i] = true;
					}
				}
			}
			else
			{
				for( int i : idList->readable() )
				{
					if( i >= 0 && i < (int64_t)variableSize )
					{
						mask.set( i, true );
					}
				}
			}
		}
		else
		{
			auto idVar = inputPrimitive->variables.find( idVarName );
			if( idVar == inputPrimitive->variables.end() )
			{
				throw IECore::Exception( fmt::format( "Id invalid, can't find primitive variable \"{}\".", idVarName ) );
			}

			if( !inputPrimitive->isPrimitiveVariableValid( idVar->second ) )
			{
				throw IECore::Exception( fmt::format( "Id primitive variable \"{}\" is not valid.", idVarName ) );
			}

			if( idVar->second.interpolation != targetInterpolation )
			{
				throw IECore::Exception( fmt::format(
					"Id variable \"{}\" : Interpolation `{}` doesn't match specified interpolation `{}`.",
					idVarName, interpolationToString( idVar->second.interpolation ), interpolationToString( targetInterpolation )
				) );
			}

			if( idVar->second.indices )
			{
				throw IECore::Exception( fmt::format( "Id variable \"{}\" is not allowed to be indexed.", idVarName ) );
			}

			std::unordered_set< int64_t > idSet;
			if( idList64 )
			{
				for( int64_t i : idList64->readable() )
				{
					idSet.insert( i );
				}
			}
			else
			{
				for( int i : idList->readable() )
				{
					idSet.insert( (int64_t)i );
				}
			}

			if( const IntVectorData *intIdsData = IECore::runTimeCast<IntVectorData>( idVar->second.data.get() ) )
			{
				const std::vector<int> &intIds = intIdsData->readable();
				for( size_t i = 0; i < intIds.size(); i++ )
				{
					if( idSet.count( intIds[i] ) )
					{
						mask.set( i, true );
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
						mask.set( i, true );
					}
				}
			}
			else
			{
				throw IECore::Exception( fmt::format( "Id invalid, can't find primitive variable \"{}\" of type IntVectorData or type Int64VectorData.", idVarName ) );
			}
		}
	}
	else if(
		selectionMode == SelectionMode::MaskPrimitiveVariable &&
		targetInterpolation != PrimitiveVariable::Invalid && targetInterpolation != PrimitiveVariable::Constant
	)
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
				"Mask primitive variable \"{}\" has wrong interpolation `{}`, expected `{}`.",
				maskVarName, interpolationToString( maskVar->second.interpolation ), interpolationToString( targetInterpolation )
			) );
		}

		IECore::dispatch( maskVar->second.data.get(),
			[&mask, &maskVar, &maskVarName]( auto *typedData )
			{
				using SourceType = typename std::remove_pointer_t<decltype( typedData )>;

				// This check should be unnecessary, but IsNumericBasedVectorTypedData fails to compile for
				// non-vector types.
				if constexpr( TypeTraits::IsVectorTypedData< SourceType >::value )
				{
					if constexpr( TypeTraits::IsNumericBasedVectorTypedData< SourceType >::value )
					{
						using ValueType = typename SourceType::ValueType::value_type;

						// There a few types that are numeric based, but it doesn't make sense to compare them
						// to zero.
						if constexpr( !TypeTraits::IsMatrix<ValueType>::value && !TypeTraits::IsQuat<ValueType>::value && !TypeTraits::IsBox<ValueType>::value )
						{
							PrimitiveVariable::IndexedView<ValueType> indexedView( maskVar->second );
							ValueType zeroValue( 0 );

							mask.reserve( indexedView.size() );
							for( size_t i = 0; i < indexedView.size(); i++ )
							{
								mask.push_back( indexedView[i] != zeroValue );
							}
							return;
						}
					}
				}

				throw IECore::Exception( fmt::format(
					"Mask primitive variable \"{}\" has invalid type \"{}\".",
					maskVarName, typedData->typeName()
				) );
			}
		);

	}

	for( const auto &tweak : TweakPlug::Range( *tweaksPlug() ) )
	{
		if( !tweak->enabledPlug()->getValue() )
		{
			continue;
		}

		std::string name = tweak->namePlug()->getValue();

		const TweakPlug::Mode mode = static_cast<TweakPlug::Mode>( tweak->modePlug()->getValue() );
		const TweakPlug::MissingMode missingMode =
			ignoreMissingPlug()->getValue() ? TweakPlug::MissingMode::Ignore : TweakPlug::MissingMode::Error;

		auto varIt = result->variables.find( name );
		TweakPlug::DataAndIndices source;
		PrimitiveVariable::Interpolation resultInterpolation = targetInterpolation;
		if( varIt != result->variables.end() )
		{
			if( !result->isPrimitiveVariableValid( varIt->second ) )
			{
				throw IECore::Exception( fmt::format( "Cannot tweak \"{}\" : Primitive variable not valid.", name ) );
			}

			source.data = varIt->second.data;
			source.indices = varIt->second.indices;

			if(
				mode != TweakPlug::Create && mode != TweakPlug::CreateIfMissing &&
				targetInterpolation != PrimitiveVariable::Invalid &&
				targetInterpolation != varIt->second.interpolation )
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
					"Cannot apply tweak to \"{}\" : Interpolation `{}` doesn't match primitive variable interpolation `{}`.",
					name, interpolationToString( targetInterpolation ), interpolationToString( varIt->second.interpolation )
				) );
			}

			// "Create" is the only mode that can change the interpolation of an existing primvar
			if( mode != TweakPlug::Create )
			{
				resultInterpolation = varIt->second.interpolation;
			}
		}

		if( resultInterpolation == PrimitiveVariable::Invalid )
		{
			// Some of these errors could be handled by TweakPlug, but since we don't know the interpolation to
			// use, we don't know whether to call applyTweak or applyElementwiseTweak, so we just deal with
			// these errors ourselves.
			if(
				mode == TweakPlug::Create || mode == TweakPlug::CreateIfMissing ||
				mode == TweakPlug::ListPrepend || mode == TweakPlug::ListAppend
			)
			{
				throw IECore::Exception( fmt::format(
					"Cannot create primitive variable \"{}\" when interpolation is set to `Any`."
					" Please select an interpolation.", name
				) );
			}
			else if(
				missingMode == Gaffer::TweakPlug::MissingMode::Ignore ||
				mode == TweakPlug::Remove || mode == Gaffer::TweakPlug::ListRemove
			)
			{
				continue;
			}
			else
			{
				throw IECore::Exception( fmt::format( "Cannot find primitive variable \"{}\" to tweak.", name ) );
			}

		}
		else if( resultInterpolation == PrimitiveVariable::Constant )
		{
			tweak->applyTweak(
				[&source]( const std::string &valueName, const bool withFallback )
				{
					return source.data.get();
				},
				[&result, &targetInterpolation]( const std::string &valueName, DataPtr newData )
				{
					if( newData )
					{
						result->variables[valueName] = PrimitiveVariable(
							PrimitiveVariable::Constant, std::move( newData )
						);
						return true;
					}
					else
					{
						return result->variables.erase( valueName ) > 0;
					}
				},
				missingMode
			);
		}
		else
		{
			tweak->applyElementwiseTweak(
				[&source]( const std::string &valueName, const bool withFallback )
				{
					return source;
				},
				[&result, &resultInterpolation]( const std::string &valueName, const TweakPlug::DataAndIndices &newPrimVar )
				{
					if( !newPrimVar.data )
					{
						return result->variables.erase( valueName ) > 0;
					}

					result->variables[valueName] = PrimitiveVariable( resultInterpolation, newPrimVar.data, newPrimVar.indices );
					return true;
				},
				result->variableSize( resultInterpolation ),
				mask.size() ? &mask : nullptr,
				missingMode
			);
		}
	}

	return result;
}

bool PrimitiveVariableTweaks::adjustBounds() const
{
	if( !Deformer::adjustBounds() )
	{
		return false;
	}


	for( const auto &tweak : TweakPlug::Range( *tweaksPlug() ) )
	{
		if( tweak->enabledPlug()->getValue() && tweak->namePlug()->getValue() == "P" )
		{
			return true;
		}
	}

	return false;
}
