//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferUSD/USDShader.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/OptionalValuePlug.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/StringPlug.h"

#include "IECoreUSD/DataAlgo.h"
#include "IECoreUSD/TypeTraits.h"

#include "IECoreScene/ShaderNetwork.h"

#include "IECore/MessageHandler.h"

#include "pxr/usd/sdf/types.h"
#include "pxr/usd/sdf/valueTypeName.h"
#include "pxr/usd/sdr/registry.h"
#include "pxr/usd/sdr/shaderNode.h"
#include "pxr/usd/sdr/shaderProperty.h"
#include "pxr/usd/usd/schemaRegistry.h"
#include "pxr/usd/usdLux/boundableLightBase.h"
#include "pxr/usd/usdLux/nonboundableLightBase.h"

#include "boost/algorithm/string/predicate.hpp"

#include "fmt/format.h"

using namespace std;
using namespace pxr;
using namespace boost;
using namespace Imath;
using namespace IECore;
using namespace GafferScene;
using namespace GafferUSD;
using namespace Gaffer;

namespace
{

/// \todo This is an improved copy of a function in IECoreUSD/DataAlgo.cpp - move this
/// one to IECoreUSD and expose it publicly.
GeometricData::Interpretation interpretation( TfToken role )
{
	if( role == SdfValueRoleNames->Point )
	{
		return GeometricData::Point;
	}
	else if( role == SdfValueRoleNames->Vector )
	{
		return GeometricData::Vector;
	}
	else if( role == SdfValueRoleNames->Normal )
	{
		return GeometricData::Normal;
	}
	else if( role == SdfValueRoleNames->TextureCoordinate )
	{
		return GeometricData::UV;
	}
	else if( role == SdfValueRoleNames->Color )
	{
		return GeometricData::Color;
	}
	return GeometricData::None;
}

Plug::Direction direction( const SdrShaderProperty &property )
{
	return property.IsOutput() ? Plug::Out : Plug::In;
}

// The various `acquire*PropertyPlug()` methods have similar semantics to other
// `acquire()` methods in Gaffer - they either reuse a pre-existing plug that is
// suitable, or they create a new one. But they differ in that the caller is
// responsible for passing in the candidate for reuse, and also for storing any
// newly created plug.

template<typename PlugType>
PlugPtr acquireTypedPlug( InternedString name, Plug::Direction direction, VtValue defaultVtValue, Plug *candidate )
{
	using ValueType = typename PlugType::ValueType;
	using USDValueType = typename IECoreUSD::CortexTypeTraits<ValueType>::USDType;

	ValueType defaultValue = ValueType();
	if( !defaultVtValue.IsHolding<USDValueType>() )
	{
		// Workaround for various UsdLuxLight `bool` inputs which somehow
		// get reported with `int` default values.
		defaultVtValue = defaultVtValue.Cast<USDValueType>();
	}
	if( !defaultVtValue.IsEmpty() )
	{
		defaultValue = IECoreUSD::DataAlgo::fromUSD( defaultVtValue.Get<USDValueType>() );
	}

	PlugType *existingPlug = runTimeCast<PlugType>( candidate );
	if( existingPlug && existingPlug->defaultValue() == defaultValue )
	{
		return existingPlug;
	}

	return new PlugType( name, direction, defaultValue );
}

template<typename PlugType>
PlugPtr acquireCompoundNumericPlug( InternedString name, const SdfValueTypeName &type, Plug::Direction direction, const VtValue &defaultVtValue, Plug *candidate )
{
	IECore::GeometricData::Interpretation interpretation = ::interpretation( type.GetRole() );

	using ValueType = typename PlugType::ValueType;
	using USDValueType = typename IECoreUSD::CortexTypeTraits<ValueType>::USDType;

	ValueType defaultValue( 0.0f );
	if( !defaultVtValue.IsEmpty() )
	{
		defaultValue = IECoreUSD::DataAlgo::fromUSD( defaultVtValue.Get<USDValueType>() );
	}

	PlugType *existingPlug = runTimeCast<PlugType>( candidate );
	if(
		existingPlug &&
		existingPlug->defaultValue() == defaultValue &&
		existingPlug->interpretation() == interpretation
	)
	{
		return existingPlug;
	}

	return new PlugType(
		name, direction, defaultValue,
		ValueType( std::numeric_limits<float>::lowest() ), ValueType( std::numeric_limits<float>::max() ),
		Plug::Default, interpretation
	);
}

PlugPtr acquireAssetPlug( InternedString name, Plug::Direction direction, VtValue defaultVtValue, Plug *candidate )
{
	string defaultValue;
	if( !defaultVtValue.IsEmpty() )
	{
		defaultValue = defaultVtValue.Get<SdfAssetPath>().GetAssetPath();
	}

	StringPlug *existingPlug = runTimeCast<StringPlug>( candidate );
	if( existingPlug && existingPlug->defaultValue() == defaultValue )
	{
		return existingPlug;
	}

	return new StringPlug( name, direction, defaultValue );
}

PlugPtr acquirePlug( InternedString name, Plug::Direction direction, Plug *candidate )
{
	if( candidate && candidate->typeId() == Plug::staticTypeId() )
	{
		return candidate;
	}

	return new Plug( name, direction );
}

Plug *loadParameter( InternedString name, const SdfValueTypeName &type, Plug::Direction direction, const VtValue &defaultValue, Plug *parent, bool optional = false )
{
	Plug *candidatePlug = parent->getChild<Plug>( name );
	if( candidatePlug && optional )
	{
		if( auto optionalPlug = runTimeCast<OptionalValuePlug>( candidatePlug ) )
		{
			candidatePlug = optionalPlug->valuePlug();
		}
		else
		{
			candidatePlug = nullptr;
		}
	}

	PlugPtr acquiredPlug;

	if( type == SdfValueTypeNames->Bool )
	{
		acquiredPlug = acquireTypedPlug<BoolPlug>( name, direction, defaultValue, candidatePlug );
	}
	else if( type == SdfValueTypeNames->Int )
	{
		acquiredPlug = acquireTypedPlug<IntPlug>( name, direction, defaultValue, candidatePlug );
	}
	else if( type == SdfValueTypeNames->Float )
	{
		acquiredPlug = acquireTypedPlug<FloatPlug>( name, direction, defaultValue, candidatePlug );
	}
	else if( type == SdfValueTypeNames->Float2 )
	{
		acquiredPlug = acquireCompoundNumericPlug<V2fPlug>( name, type, direction, defaultValue, candidatePlug );
	}
	else if(
		type == SdfValueTypeNames->Point3f ||
		type == SdfValueTypeNames->Vector3f ||
		type == SdfValueTypeNames->Normal3f ||
		type == SdfValueTypeNames->Float3
	)
	{
		acquiredPlug = acquireCompoundNumericPlug<V3fPlug>( name, type, direction, defaultValue, candidatePlug );
	}
	else if( type == SdfValueTypeNames->Color3f )
	{
		acquiredPlug = acquireCompoundNumericPlug<Color3fPlug>( name, type, direction, defaultValue, candidatePlug );
	}
	else if( type == SdfValueTypeNames->Float4 )
	{
		acquiredPlug = acquireCompoundNumericPlug<Color4fPlug>( name, type, direction, defaultValue, candidatePlug );
	}
	else if( type == SdfValueTypeNames->String || type == SdfValueTypeNames->Token )
	{
		acquiredPlug = acquireTypedPlug<StringPlug>( name, direction, defaultValue, candidatePlug );
	}
	else if( type == SdfValueTypeNames->Asset )
	{
		acquiredPlug = acquireAssetPlug( name, direction, defaultValue, candidatePlug );
	}
	else if( type == SdfValueTypeNames->Opaque )
	{
		acquiredPlug = acquirePlug( name, direction, candidatePlug );
	}
	else
	{
		IECore::msg(
			IECore::Msg::Warning, "USDShader",
			fmt::format(
				"Unable to load parameter \"{}\" of type \"{}\"",
				name.string(), type.GetAsToken().GetString()
			)
		);
		return nullptr;
	}

	assert( acquiredPlug );

	if( acquiredPlug != candidatePlug )
	{
		// We created a new plug, and need to parent it in.
		if( optional )
		{
			ValuePlugPtr acquiredValuePlug = runTimeCast<ValuePlug>( acquiredPlug );
			if( !acquiredValuePlug )
			{
				throw IECore::Exception( fmt::format( "Cannot create OptionalValuePlug for parameter `{}`", name.string() ) );
			}
			PlugAlgo::replacePlug(
				parent, new OptionalValuePlug(
					name, acquiredValuePlug, /* enabledPlugDefaultValue = */ false,
					direction
				)
			);
		}
		else
		{
			PlugAlgo::replacePlug( parent, acquiredPlug );
		}
	}

	return optional ? acquiredPlug->parent<Plug>() : acquiredPlug.get();
}

Plug *loadShaderProperty( const SdrShaderProperty &property, Plug *parent )
{
	SdfValueTypeName sdfType = property.GetTypeAsSdfType().first;
	if(
		property.GetType() == SdrPropertyTypes->Terminal ||
		property.GetType() == SdrPropertyTypes->Vstruct
	)
	{
		// The Sdf type will be Token, but that doesn't really communicate the
		// fact that these properties don't actually carry data. We use Opaque
		// for the purposes of communicating that to `loadParameter()`.
		sdfType = SdfValueTypeNames->Opaque;
	}

	return loadParameter( property.GetName().GetString(), sdfType, ::direction( property ), property.GetDefaultValue(), parent );
}

Plug *loadPrimDefinitionAttribute( const UsdPrimDefinition::Attribute &attribute, InternedString name, Plug *parent, bool optional )
{
	VtValue defaultValue;
	attribute.GetFallbackValue( &defaultValue );
	return loadParameter( name, attribute.GetTypeName(), Plug::Direction::In, defaultValue, parent, optional );
}

const IECore::InternedString g_surface( "surface" );
const IECore::InternedString g_displacement( "displacement" );

} // namespace

GAFFER_NODE_DEFINE_TYPE( USDShader );

USDShader::USDShader( const std::string &name )
	:	GafferScene::Shader( name )
{
	addChild( new Plug( "out", Plug::Out ) );
}

USDShader::~USDShader()
{
}

void USDShader::loadShader( const std::string &shaderName, bool keepExistingValues )
{
	// Find the shader definition either in the SchemaRegistry or the SdrRegistry.
	// UsdLux lights are available from either, but we prefer the SchemaRegistry
	// because it includes the attributes from auto-apply schemas that are used
	// for renderer-specific light extensions.

	const TfToken shaderNameToken( shaderName );

	UsdSchemaRegistry &schemaRegistry = UsdSchemaRegistry::GetInstance();
	vector<const UsdPrimDefinition *> primDefinitions;
	vector<TfToken> autoAppliedPropertyNames;
	if( auto primDefinition = schemaRegistry.FindConcretePrimDefinition( shaderNameToken ) )
	{
		primDefinitions.push_back( primDefinition );
		// The main prim definition contains properties from auto-applied API schemas, but doesn't
		// provide a direct way of querying which they are. Make our own list, because we want to
		// represent them using OptionalValuePlugs.
		for( const auto &[apiSchema, autoAppliedTo] : schemaRegistry.GetAutoApplyAPISchemas() )
		{
			if( std::find( autoAppliedTo.begin(), autoAppliedTo.end(), shaderNameToken ) != autoAppliedTo.end() )
			{
				auto apiDefinition = schemaRegistry.FindAppliedAPIPrimDefinition( apiSchema );
				autoAppliedPropertyNames.insert(
					autoAppliedPropertyNames.end(),
					apiDefinition->GetPropertyNames().begin(), apiDefinition->GetPropertyNames().end()
				);
			}
		}

		const TfType schemaType = schemaRegistry.GetTypeFromName( shaderNameToken );
		if( schemaType.IsA<UsdLuxBoundableLightBase>() || schemaType.IsA<UsdLuxNonboundableLightBase>() )
		{
			primDefinitions.push_back( schemaRegistry.FindAppliedAPIPrimDefinition( TfToken( "ShadowAPI" ) ) );
			primDefinitions.push_back( schemaRegistry.FindAppliedAPIPrimDefinition( TfToken( "ShapingAPI" ) ) );
		}
	}

	SdrShaderNodeConstPtr shader = nullptr;
	if( primDefinitions.empty() )
	{
		SdrRegistry &registry = SdrRegistry::GetInstance();
		shader = registry.GetShaderNodeByName( shaderName );
		if( !shader )
		{
			throw Exception( fmt::format( "Shader \"{}\" not found in SdrRegistry or UsdSchemaRegistry", shaderName ) );
		}
	}

	// Set name and type and delete old parameters if necessary.

	namePlug()->setValue( shaderName );
	typePlug()->setValue( "surface" );

	Plug *parametersPlug = this->parametersPlug()->source();
	Plug *outPlug = this->outPlug();

	if( !keepExistingValues )
	{
		parametersPlug->clearChildren();
		outPlug->clearChildren();
	}

	// Load parameters.

	std::unordered_set<const Plug *> validPlugs;
	if( primDefinitions.size() )
	{
		for( size_t i = 0; i < primDefinitions.size(); ++i )
		{
			for( const auto &name : primDefinitions[i]->GetPropertyNames() )
			{
				if( !boost::starts_with( name.GetString(), "inputs:" ) )
				{
					continue;
				}
				if( auto attribute = primDefinitions[i]->GetAttributeDefinition( name ) )
				{
					const bool optional = i > 0 || std::find( autoAppliedPropertyNames.begin(), autoAppliedPropertyNames.end(), name ) != autoAppliedPropertyNames.end();
					validPlugs.insert(
						loadPrimDefinitionAttribute( attribute, attribute.GetName().GetText() + strlen( "inputs:" ), parametersPlug, optional )
					);
				}
			}
		}
	}
	else
	{
		assert( shader );
		for( const auto &name : shader->GetInputNames() )
		{
			SdrShaderPropertyConstPtr property = shader->GetShaderInput( name );
			validPlugs.insert( loadShaderProperty( *property, parametersPlug ) );
		}
		for( const auto &name : shader->GetOutputNames() )
		{
			SdrShaderPropertyConstPtr property = shader->GetShaderOutput( name );
			validPlugs.insert( loadShaderProperty( *property, outPlug ) );
		}
	}

	// Remove old parameters we no longer need.

	for( int i = parametersPlug->children().size() - 1; i >= 0; --i )
	{
		Plug *child = parametersPlug->getChild<Plug>( i );
		if( validPlugs.find( child ) == validPlugs.end() )
		{
			parametersPlug->removeChild( child );
		}
	}

	for( int i = outPlug->children().size() - 1; i >= 0; --i )
	{
		Plug *child = outPlug->getChild<Plug>( i );
		if( validPlugs.find( child ) == validPlugs.end() )
		{
			outPlug->removeChild( child );
		}
	}
}

IECore::ConstCompoundObjectPtr USDShader::attributes( const Gaffer::Plug *output ) const
{
	IECore::ConstCompoundObjectPtr result = Shader::attributes( output );
	if( output->getName() == g_displacement )
	{
		// UsdPreviewSurface has separate surface and displacement outputs.
		// Rename attribute for the displacement case.
		if( auto network = result->member<IECoreScene::ShaderNetwork>( g_surface ) )
		{
			IECore::CompoundObjectPtr copy = result->copy();
			// Cast OK as we never modify, and `copy` is returned as `const`.
			copy->members()[g_displacement] = const_cast<IECoreScene::ShaderNetwork *>( network );
			copy->members().erase( g_surface );
			result = copy;
		}
	}
	return result;
}
