//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/PrimitiveVariablePaint.h"

#include "IECoreScene/Primitive.h"

#include "IECore/DataAlgo.h"
#include "IECore/NullObject.h"

#include "IECore/TypeTraits.h"
#include <unordered_set>

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

namespace {

IndexedIO::EntryID g_valueDataName( "valueData" );
IndexedIO::EntryID g_opacityDataName( "opacityData" );
IndexedIO::EntryID g_indicesDataName( "indicesData" );

} // namespace

GAFFER_NODE_DEFINE_TYPE( PrimitiveVariablePaint );

PrimitiveVariablePaint::PaintOperation::PaintOperation(
	IECore::DataPtr valueData,
	IECore::FloatVectorDataPtr opacityData,
	IECore::IntVectorDataPtr indicesData
)
	: m_valueData( valueData ), m_opacityData( opacityData ), m_indicesData( indicesData )
{
}

PrimitiveVariablePaint::PaintOperation::~PaintOperation()
{
}

bool PrimitiveVariablePaint::PaintOperation::isEqualTo( const IECore::Object *other ) const
{
	if( !Object::isEqualTo( other ) )
	{
		return false;
	}

	const PaintOperation *operation = static_cast<const PaintOperation *>( other );
	if( m_valueData || operation->m_valueData )
	{
		if( !( m_valueData && operation->m_valueData && m_valueData->isEqualTo( operation->m_valueData.get() ) ) )
		{
			return false;
		}
	}

	if( m_opacityData || operation->m_opacityData )
	{
		if( !( m_opacityData && operation->m_opacityData && m_opacityData->isEqualTo( operation->m_opacityData.get() ) ) )
		{
			return false;
		}
	}

	if( m_indicesData || operation->m_indicesData )
	{
		if( !( m_indicesData && operation->m_indicesData && m_indicesData->isEqualTo( operation->m_indicesData.get() ) ) )
		{
			return false;
		}
	}

	return true;
}

void PrimitiveVariablePaint::PaintOperation::hash( IECore::MurmurHash &h ) const
{
	Object::hash( h );
	if( m_valueData )
	{
		m_valueData->hash( h );
	}

	if( m_opacityData )
	{
		m_opacityData->hash( h );
	}

	if( m_indicesData )
	{
		m_indicesData->hash( h );
	}
}

void PrimitiveVariablePaint::PaintOperation::copyFrom( const IECore::Object *other, IECore::Object::CopyContext *context )
{
	Object::copyFrom( other, context );

	const PaintOperation *operation = static_cast<const PaintOperation *>( other );
	m_valueData = operation->m_valueData;
	m_opacityData = operation->m_opacityData;
	m_indicesData = operation->m_indicesData;
}

void PrimitiveVariablePaint::PaintOperation::save( IECore::Object::SaveContext *context ) const
{
	Object::save( context );

	IndexedIOPtr container = context->container( staticTypeName(), 1 );
	context->save( m_valueData.get(), container.get(), g_valueDataName );
	if( m_opacityData )
	{
		context->save( m_opacityData.get(), container.get(), g_opacityDataName );
	}
	if( m_indicesData )
	{
		context->save( m_indicesData.get(), container.get(), g_indicesDataName );
	}
}

void PrimitiveVariablePaint::PaintOperation::load( IECore::Object::LoadContextPtr context )
{
	Object::load( context );

	unsigned int version = 1;
	ConstIndexedIOPtr container = context->container( staticTypeName(), version );

	m_valueData = context->load<Data>( container.get(), g_valueDataName );

	if( container->hasEntry( g_opacityDataName ) )
	{
		m_opacityData = context->load<FloatVectorData>( container.get(), g_opacityDataName );
	}

	if( container->hasEntry( g_indicesDataName ) )
	{
		m_indicesData = context->load<IntVectorData>( container.get(), g_indicesDataName );
	}
}

void PrimitiveVariablePaint::PaintOperation::memoryUsage( IECore::Object::MemoryAccumulator &accumulator ) const
{
	Object::memoryUsage( accumulator );
	if( m_valueData )
	{
		accumulator.accumulate( m_valueData.get() );
	}
	if( m_opacityData )
	{
		accumulator.accumulate( m_opacityData.get() );
	}
	if( m_indicesData )
	{
		accumulator.accumulate( m_indicesData.get() );
	}
}

void PrimitiveVariablePaint::PaintOperation::apply( IECore::DataPtr &resultData, size_t outputSize ) const
{
	IECore::dispatch( m_valueData.get(),
		[outputSize, &resultData, this]( auto *typedValueData )
		{
			using SourceType = typename std::remove_const_t< std::remove_pointer_t<decltype( typedValueData )> >;

			if constexpr( TypeTraits::IsVectorTypedData< SourceType >::value )
			{
				if constexpr( std::is_same_v< typename SourceType::BaseType, float > )
				{

					using ValueType = typename SourceType::ValueType::value_type;

					// Avoid some types that don't support the same interfaces for blending and initializing
					// to zero. ( If anyone actually needs to paint quaternions or boxes, we could add special
					// case code to handle this correctly ).
					if constexpr( !TypeTraits::IsBox<ValueType>::value && !TypeTraits::IsQuat<ValueType>::value )
					{
						typename SourceType::Ptr typedResultData = IECore::runTimeCast<SourceType>( resultData );
						if( !typedResultData )
						{
							if( !resultData )
							{
								// If the result hasn't been filled with data yet, start from a vector of
								// zeros
								typedResultData = new SourceType();
								typedResultData->writable().resize( outputSize, ValueType( 0.0f ) );
								resultData = typedResultData;
							}
							else
							{
								throw IECore::Exception(
									fmt::format(
										"Cannot apply PaintOperation with value type {} to variable of type {}",
										typedValueData->typeName(), resultData->typeName()
									)
								);
							}
						}

						auto &resultVec = typedResultData->writable();
						auto &typedValue = typedValueData->readable();

						if( m_indicesData )
						{
							const std::vector<int> &indices = m_indicesData->readable();

							if( typedValue.size() != indices.size() )
							{
								throw IECore::Exception(
									fmt::format( "Value size {} does not match indices size {}", typedValue.size(), indices.size() )
								);
							}

							if( m_opacityData )
							{
								const std::vector<float> &opacity = m_opacityData->readable();

								if( opacity.size() != indices.size() )
								{
									throw IECore::Exception(
										fmt::format( "Opacity size {} does not match indices size {}", opacity.size(), indices.size() )
									);
								}

								for( size_t i = 0; i < indices.size(); i++ )
								{
									if( (size_t)indices[i] >= resultVec.size() )
									{
										throw IECore::Exception(
											fmt::format( "Invalid index {} in variable size {}", indices[i], outputSize )
										);
									}
									resultVec[ indices[i] ] = ( 1 - opacity[i] ) * resultVec[ indices[i] ] + typedValue[i];
								}
							}
							else
							{
								for( size_t i = 0; i < indices.size(); i++ )
								{
									if( (size_t)indices[i] >= resultVec.size() )
									{
										throw IECore::Exception(
											fmt::format( "Invalid index {} in variable size {}", indices[i], outputSize )
										);
									}
									resultVec[ indices[i] ] = typedValue[i];
								}
							}

						}
						else
						{
							// \todo - should we support some sort of reprojection for loading out of date paint? This
							// would require storing a reference P in the paint file
							if( typedValue.size() != outputSize )
							{
								throw IECore::Exception(
									fmt::format( "Value size {} does not match {}", typedValue.size(), outputSize )
								);
							}

							if( m_opacityData )
							{
								const std::vector<float> &opacity = m_opacityData->readable();

								if( opacity.size() != outputSize )
								{
									throw IECore::Exception(
										fmt::format( "Opacity size {} does not match {}", opacity.size(), outputSize )
									);
								}

								for( size_t i = 0; i < resultVec.size(); i++ )
								{
									resultVec[i] = ( 1 - opacity[i] ) * resultVec[i] + typedValue[i];
								}
							}
							else
							{
								resultVec = typedValue;
							}
						}

						return;
					}
				}
			}

			throw IECore::Exception( fmt::format(
				"Cannot apply type \"{}\"", typedValueData->typeName()
			) );
		}
	);

}

IE_CORE_DEFINEOBJECTTYPEDESCRIPTION( PrimitiveVariablePaint::PaintOperation );

size_t PrimitiveVariablePaint::g_firstPlugIndex = 0;

PrimitiveVariablePaint::PrimitiveVariablePaint( const std::string &name )
	:	Deformer( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new Plug( "primitiveVariables", Plug::In ) );
}

PrimitiveVariablePaint::~PrimitiveVariablePaint()
{
}

Gaffer::Plug *PrimitiveVariablePaint::primitiveVariablesPlug()
{
	return getChild<Gaffer::Plug>( g_firstPlugIndex + 0 );
}

const Gaffer::Plug *PrimitiveVariablePaint::primitiveVariablesPlug() const
{
	return getChild<Gaffer::Plug>( g_firstPlugIndex + 0 );
}

bool PrimitiveVariablePaint::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		Deformer::affectsProcessedObject( input ) ||
		primitiveVariablesPlug()->isAncestorOf( input )
	;
}

void PrimitiveVariablePaint::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Deformer::hashProcessedObject( path, context, h );

	for( NameValuePlug::Iterator it( primitiveVariablesPlug() ); !it.done(); ++it )
	{
		const NameValuePlug *primVarPlug = it->get();
		bool active = true;
		if( auto enabledPlug = primVarPlug->enabledPlug() )
		{
			active = enabledPlug->getValue();
		}
		if( active )
		{
			primVarPlug->namePlug()->hash( h );
			primVarPlug->valuePlug<Gaffer::ObjectPlug>()->hash( h );
		}
	}
}

IECore::ConstObjectPtr PrimitiveVariablePaint::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const Primitive *inputPrimitive = runTimeCast<const Primitive>( inputObject );
	if( !inputPrimitive )
	{
		return inputObject;
	}

	if( !inputPrimitive->arePrimitiveVariablesValid() )
	{
		throw IECore::Exception( "Cannot paint primitive with invalid primitive variables" );
	}

	PrimitivePtr result;
	for( NameValuePlug::Iterator it( primitiveVariablesPlug() ); !it.done(); ++it )
	{
		const NameValuePlug *primVarPlug = it->get();
		bool active = true;
		if( auto enabledPlug = primVarPlug->enabledPlug() )
		{
			active = enabledPlug->getValue();
		}
		if( !active )
		{
			continue;
		}

		IECore::ConstObjectPtr value = primVarPlug->valuePlug<Gaffer::ObjectPlug>()->getValue();
		if( value->typeId() == NullObjectTypeId )
		{
			continue;
		}

		const PaintOperation *typedValue = IECore::runTimeCast<const PaintOperation>( value.get() );
		if( !typedValue )
		{
			throw IECore::Exception( fmt::format( "Paint value must be of type PaintOperation, not {}.", value->typeName() ) );
		}

		std::string varName = primVarPlug->namePlug()->getValue();

		// TODO : Should we support interpolations other than Vertex? Should it be a plug on PrimitiveVariablePaint?
		// Or stored inside PaintOperation?
		PrimitiveVariable::Interpolation interp = PrimitiveVariable::Vertex;

		size_t variableSize = inputPrimitive->variableSize( interp );
		if( !result )
		{
			result = inputPrimitive->copy();
		}

		auto existingVar = result->variables.find( varName );
		if( existingVar != result->variables.end() && existingVar->second.interpolation != interp )
		{
			IECore::msg( IECore::Msg::Warning, "PrimitiveVariablePaint", fmt::format( "Interpolation mismatch for variable {} at location {}, overwriting instead of compositing.", varName, ScenePlug::pathToString( path ) ) );
			existingVar = result->variables.end();

		}

		DataPtr resultData;

		if( existingVar != result->variables.end() )
		{
			resultData = existingVar->second.expandedData();
		}

		try
		{
			typedValue->apply( resultData, variableSize );
		}
		catch( IECore::Exception &e )
		{
			throw IECore::Exception( fmt::format(
				"Invalid paint for variable {} at location {} : {}",
				varName,
				ScenePlug::pathToString( path ),
				e.what()
			) );
		}

		result->variables[varName] = PrimitiveVariable( interp, resultData );
	}

	if( !result )
	{
		return inputPrimitive;
	}

	return result;
}

bool PrimitiveVariablePaint::adjustBounds() const
{
	if( !Deformer::adjustBounds() )
	{
		return false;
	}

	for( NameValuePlug::Iterator it( primitiveVariablesPlug() ); !it.done(); ++it )
	{
		if( (*it)->namePlug()->getValue() == "P" )
		{
			return true;
		}
	}

	return false;
}
