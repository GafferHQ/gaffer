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
PlugPtr acquireTypedPropertyPlug( const SdrShaderProperty &property, Plug *candidate )
{
	using ValueType = typename PlugType::ValueType;
	using USDValueType = typename IECoreUSD::CortexTypeTraits<ValueType>::USDType;

	ValueType defaultValue = ValueType();
	VtValue defaultVtValue = property.GetDefaultValue();
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

	return new PlugType( property.GetName().GetString(), direction( property ), defaultValue );
}

template<typename PlugType>
PlugPtr acquireCompoundNumericPropertyPlug( const SdrShaderProperty &property, Plug *candidate )
{
	IECore::GeometricData::Interpretation interpretation = ::interpretation( property.GetTypeAsSdfType().first.GetRole() );

	using ValueType = typename PlugType::ValueType;
	using USDValueType = typename IECoreUSD::CortexTypeTraits<ValueType>::USDType;

	ValueType defaultValue( 0.0f );
	VtValue defaultVtValue = property.GetDefaultValue();
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
		property.GetName().GetString(), direction( property ), defaultValue,
		ValueType( std::numeric_limits<float>::lowest() ), ValueType( std::numeric_limits<float>::max() ),
		Plug::Default, interpretation
	);
}

PlugPtr acquireAssetPropertyPlug( const SdrShaderProperty &property, Plug *candidate )
{
	string defaultValue;
	VtValue defaultVtValue = property.GetDefaultValue();
	if( !defaultVtValue.IsEmpty() )
	{
		defaultValue = defaultVtValue.Get<SdfAssetPath>().GetAssetPath();
	}

	StringPlug *existingPlug = runTimeCast<StringPlug>( candidate );
	if( existingPlug && existingPlug->defaultValue() == defaultValue )
	{
		return existingPlug;
	}

	return new StringPlug( property.GetName().GetString(), direction( property ), defaultValue );
}

PlugPtr acquireTokenPropertyPlug( const SdrShaderProperty &property, Plug *candidate )
{
	// Sdr uses the `token` type to represent terminals, vstructs
	// and unknown types. As I understand it, these don't carry values,
	// so the Plug base class is the best way of representing them
	// in Gaffer.
	if( candidate && candidate->typeId() == Plug::staticTypeId() )
	{
		return candidate;
	}

	return new Plug( property.GetName().GetString(), direction( property ) );
}

Plug *loadShaderProperty( const SdrShaderProperty &property, Plug *parent )
{
	// We host properties from bolt-on schemas in OptionalValuePlugs, so users
	// can opt in and out of authoring them.
	const bool optional =
		boost::starts_with( property.GetName().GetString(), "shaping:" ) ||
		boost::starts_with( property.GetName().GetString(), "shadow:" )
	;

	Plug *candidatePlug = parent->getChild<Plug>( property.GetName().GetString() );
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
	const SdfValueTypeName type = property.GetTypeAsSdfType().first;
	if( type == SdfValueTypeNames->Bool )
	{
		acquiredPlug = acquireTypedPropertyPlug<BoolPlug>( property, candidatePlug );
	}
	else if( type == SdfValueTypeNames->Int )
	{
		acquiredPlug = acquireTypedPropertyPlug<IntPlug>( property, candidatePlug );
	}
	else if( type == SdfValueTypeNames->Float )
	{
		acquiredPlug = acquireTypedPropertyPlug<FloatPlug>( property, candidatePlug );
	}
	else if( type == SdfValueTypeNames->Float2 )
	{
		acquiredPlug = acquireCompoundNumericPropertyPlug<V2fPlug>( property, candidatePlug );
	}
	else if(
		type == SdfValueTypeNames->Point3f ||
		type == SdfValueTypeNames->Vector3f ||
		type == SdfValueTypeNames->Normal3f ||
		type == SdfValueTypeNames->Float3
	)
	{
		acquiredPlug = acquireCompoundNumericPropertyPlug<V3fPlug>( property, candidatePlug );
	}
	else if( type == SdfValueTypeNames->Color3f )
	{
		acquiredPlug = acquireCompoundNumericPropertyPlug<Color3fPlug>( property, candidatePlug );
	}
	else if( type == SdfValueTypeNames->Float4 )
	{
		acquiredPlug = acquireCompoundNumericPropertyPlug<Color4fPlug>( property, candidatePlug );
	}
	else if( type == SdfValueTypeNames->String )
	{
		acquiredPlug = acquireTypedPropertyPlug<StringPlug>( property, candidatePlug );
	}
	else if( type == SdfValueTypeNames->Asset )
	{
		acquiredPlug = acquireAssetPropertyPlug( property, candidatePlug );
	}
	else if( type == SdfValueTypeNames->Token )
	{
		acquiredPlug = acquireTokenPropertyPlug( property, candidatePlug );
	}
	else
	{
		IECore::msg(
			IECore::Msg::Warning, "USDShader",
			fmt::format(
				"Unable to load property \"{}\" of type \"{}\"",
				property.GetName().GetString(), type.GetAsToken().GetString()
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
				throw IECore::Exception( fmt::format( "Cannot create OptionalValuePlug for property `{}`", property.GetName().GetString() ) );
			}
			PlugAlgo::replacePlug(
				parent, new OptionalValuePlug(
					property.GetName().GetString(), acquiredValuePlug, /* enabledPlugDefaultValue = */ false,
					direction( property )
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
	SdrRegistry &registry = SdrRegistry::GetInstance();
	SdrShaderNodeConstPtr shader = registry.GetShaderNodeByName( shaderName );

	if( !shader )
	{
		throw Exception( fmt::format( "Shader \"{}\" not found in SdrRegistry", shaderName ) );
	}

	namePlug()->setValue( shaderName );
	typePlug()->setValue( "surface" );

	Plug *parametersPlug = this->parametersPlug()->source();

	if( !keepExistingValues )
	{
		parametersPlug->clearChildren();
		outPlug()->clearChildren();
	}

	std::unordered_set<const Plug *> validPlugs;
	for( const auto &name : shader->GetInputNames() )
	{
		SdrShaderPropertyConstPtr property = shader->GetShaderInput( name );
		validPlugs.insert( loadShaderProperty( *property, parametersPlug ) );
	}

	for( int i = parametersPlug->children().size() - 1; i >= 0; --i )
	{
		Plug *child = parametersPlug->getChild<Plug>( i );
		if( validPlugs.find( child ) == validPlugs.end() )
		{
			parametersPlug->removeChild( child );
		}
	}

	Plug *outPlug = this->outPlug();
	for( const auto &name : shader->GetOutputNames() )
	{
		SdrShaderPropertyConstPtr property = shader->GetShaderOutput( name );
		validPlugs.insert( loadShaderProperty( *property, outPlug ) );
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
