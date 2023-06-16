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

template<typename PlugType>
Plug *loadTypedProperty( const SdrShaderProperty &property, Plug *parent )
{
	using ValueType = typename PlugType::ValueType;
	using USDValueType = typename IECoreUSD::CortexTypeTraits<ValueType>::USDType;

	InternedString name = property.GetName().GetString();
	PlugType *existingPlug = parent->getChild<PlugType>( name );

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

	if( existingPlug && existingPlug->defaultValue() == defaultValue )
	{
		return existingPlug;
	}

	typename PlugType::Ptr plug = new PlugType( name, parent->direction(), defaultValue );
	PlugAlgo::replacePlug( parent, plug );
	return plug.get();
}

template<typename PlugType>
Plug *loadCompoundNumericProperty( const SdrShaderProperty &property, Plug *parent )
{
	InternedString name = property.GetName().GetString();
	PlugType *existingPlug = parent->getChild<PlugType>( name );

	IECore::GeometricData::Interpretation interpretation = ::interpretation( property.GetTypeAsSdfType().first.GetRole() );

	using ValueType = typename PlugType::ValueType;
	using USDValueType = typename IECoreUSD::CortexTypeTraits<ValueType>::USDType;

	ValueType defaultValue( 0.0f );
	VtValue defaultVtValue = property.GetDefaultValue();
	if( !defaultVtValue.IsEmpty() )
	{
		defaultValue = IECoreUSD::DataAlgo::fromUSD( defaultVtValue.Get<USDValueType>() );
	}

	if(
		existingPlug &&
		existingPlug->defaultValue() == defaultValue &&
		existingPlug->interpretation() == interpretation
	)
	{
		return existingPlug;
	}

	typename PlugType::Ptr plug = new PlugType(
		name, parent->direction(), defaultValue,
		ValueType( std::numeric_limits<float>::lowest() ), ValueType( std::numeric_limits<float>::max() ),
		Plug::Default, interpretation
	);
	PlugAlgo::replacePlug( parent, plug );
	return plug.get();
}

Plug *loadAssetProperty( const SdrShaderProperty &property, Plug *parent )
{
	InternedString name = property.GetName().GetString();
	StringPlug *existingPlug = parent->getChild<StringPlug>( name );

	string defaultValue;
	VtValue defaultVtValue = property.GetDefaultValue();
	if( !defaultVtValue.IsEmpty() )
	{
		defaultValue = defaultVtValue.Get<SdfAssetPath>().GetAssetPath();
	}

	if( existingPlug && existingPlug->defaultValue() == defaultValue )
	{
		return existingPlug;
	}

	StringPlugPtr plug = new StringPlug( name, parent->direction(), defaultValue );
	PlugAlgo::replacePlug( parent, plug );
	return plug.get();
}

Plug *loadTokenProperty( const SdrShaderProperty &property, Plug *parent )
{
	// Sdr uses the `token` type to represent terminals, vstructs
	// and unknown types. As I understand it, these don't carry values,
	// so the Plug base class is the best way of representing them
	// in Gaffer.
	InternedString name = property.GetName().GetString();
	Plug *existingPlug = parent->getChild<Plug>( name );

	if( existingPlug && existingPlug->typeId() == Plug::staticTypeId() )
	{
		return existingPlug;
	}

	PlugPtr plug = new Plug( name, parent->direction() );
	PlugAlgo::replacePlug( parent, plug );
	return plug.get();
}

Plug *loadShaderProperty( const SdrShaderProperty &property, Plug *parent )
{
	const SdfValueTypeName type = property.GetTypeAsSdfType().first;
	if( type == SdfValueTypeNames->Bool )
	{
		return loadTypedProperty<BoolPlug>( property, parent );
	}
	else if( type == SdfValueTypeNames->Int )
	{
		return loadTypedProperty<IntPlug>( property, parent );
	}
	else if( type == SdfValueTypeNames->Float )
	{
		return loadTypedProperty<FloatPlug>( property, parent );
	}
	else if( type == SdfValueTypeNames->Float2 )
	{
		return loadCompoundNumericProperty<V2fPlug>( property, parent );
	}
	else if(
		type == SdfValueTypeNames->Point3f ||
		type == SdfValueTypeNames->Vector3f ||
		type == SdfValueTypeNames->Normal3f ||
		type == SdfValueTypeNames->Float3
	)
	{
		return loadCompoundNumericProperty<V3fPlug>( property, parent );
	}
	else if( type == SdfValueTypeNames->Color3f )
	{
		return loadCompoundNumericProperty<Color3fPlug>( property, parent );
	}
	else if( type == SdfValueTypeNames->Float4 )
	{
		return loadCompoundNumericProperty<Color4fPlug>( property, parent );
	}
	else if( type == SdfValueTypeNames->String )
	{
		return loadTypedProperty<StringPlug>( property, parent );
	}
	else if( type == SdfValueTypeNames->Asset )
	{
		return loadAssetProperty( property, parent );
	}
	else if( type == SdfValueTypeNames->Token )
	{
		return loadTokenProperty( property, parent );
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
