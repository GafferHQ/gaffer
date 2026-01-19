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

#include "Attributes.h"

#include "ParamListAlgo.h"
#include "Loader.h"

#include "IECoreScene/ShaderNetwork.h"

#include "IECore/SimpleTypedData.h"

#include "boost/algorithm/string.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/container/flat_map.hpp"

#include "fmt/format.h"

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreRenderMan;

namespace
{

// List generated from `$RMANTREE/lib/defaults/PRManPrimVars.args` using
// `contrib/scripts/renderManPrototypeAttributes.py`.
boost::container::flat_map<InternedString, RtUString> g_prototypeAttributes = {
	{ "ri:identifier:object", RtUString( "identifier:object" ) },
	{ "ri:stats:prototypeIdentifier", RtUString( "stats:prototypeIdentifier" ) },
	{ "ri:derivatives:extrapolate", RtUString( "derivatives:extrapolate" ) },
	{ "ri:trace:autobias", RtUString( "trace:autobias" ) },
	{ "ri:trace:bias", RtUString( "trace:bias" ) },
	{ "ri:trace:sssautobias", RtUString( "trace:sssautobias" ) },
	{ "ri:trace:sssbias", RtUString( "trace:sssbias" ) },
	{ "ri:trace:displacements", RtUString( "trace:displacements" ) },
	{ "ri:displacementbound:CoordinateSystem", RtUString( "displacementbound:CoordinateSystem" ) },
	{ "ri:displacementbound:offscreen", RtUString( "displacementbound:offscreen" ) },
	{ "ri:displacementbound:sphere", RtUString( "displacementbound:sphere" ) },
	{ "ri:displacement:ignorereferenceinstance", RtUString( "displacement:ignorereferenceinstance" ) },
	{ "ri:Ri:Orientation", RtUString( "Ri:Orientation" ) },
	{ "ri:dice:micropolygonlength", RtUString( "dice:micropolygonlength" ) },
	{ "ri:dice:offscreenstrategy", RtUString( "dice:offscreenstrategy" ) },
	{ "ri:dice:rasterorient", RtUString( "dice:rasterorient" ) },
	{ "ri:dice:referencecamera", RtUString( "dice:referencecamera" ) },
	{ "ri:dice:referenceinstance", RtUString( "dice:referenceinstance" ) },
	{ "ri:dice:strategy", RtUString( "dice:strategy" ) },
	{ "ri:dice:worlddistancelength", RtUString( "dice:worlddistancelength" ) },
	{ "ri:Ri:GeometricApproximationFocusFactor", RtUString( "Ri:GeometricApproximationFocusFactor" ) },
	{ "ri:dice:offscreenmultiplier", RtUString( "dice:offscreenmultiplier" ) },
	{ "ri:falloffpower", RtUString( "falloffpower" ) },
	{ "ri:curve:opacitysamples", RtUString( "curve:opacitysamples" ) },
	{ "ri:curve:widthaffectscurvature", RtUString( "curve:widthaffectscurvature" ) },
	{ "ri:dice:minlength", RtUString( "dice:minlength" ) },
	{ "ri:dice:minlengthspace", RtUString( "dice:minlengthspace" ) },
	{ "ri:Ri:Bound", RtUString( "Ri:Bound" ) },
	{ "ri:volume:aggregate", RtUString( "volume:aggregate" ) },
	{ "ri:volume:dsominmax", RtUString( "volume:dsominmax" ) },
	{ "ri:volume:fps", RtUString( "volume:fps" ) },
	{ "ri:volume:shutteroffset", RtUString( "volume:shutteroffset" ) },
	{ "ri:volume:velocityshuttercorrection", RtUString( "volume:velocityshuttercorrection" ) },
	{ "ri:volume:aggregaterespectvisibility", RtUString( "volume:aggregaterespectvisibility" ) },
	{ "ri:volume:dsovelocity", RtUString( "volume:dsovelocity" ) },
	{ "ri:dice:pretessellate", RtUString( "dice:pretessellate" ) },
	{ "ri:dice:watertight", RtUString( "dice:watertight" ) },
	{ "ri:shade:faceset", RtUString( "shade:faceset" ) },
	{ "ri:stitchbound:CoordinateSystem", RtUString( "stitchbound:CoordinateSystem" ) },
	{ "ri:stitchbound:sphere", RtUString( "stitchbound:sphere" ) },
	{ "ri:trimcurve:sense", RtUString( "trimcurve:sense" ) },
	{ "ri:polygon:concave", RtUString( "polygon:concave" ) },
	{ "ri:polygon:smoothdisplacement", RtUString( "polygon:smoothdisplacement" ) },
	{ "ri:polygon:smoothnormals", RtUString( "polygon:smoothnormals" ) },
	{ "ri:procedural:immediatesubdivide", RtUString( "procedural:immediatesubdivide" ) },
	{ "ri:procedural:reentrant", RtUString( "procedural:reentrant" ) }
};

const string g_renderManPrefix( "ri:" );
const IECore::InternedString g_automaticInstancingAttributeName( "gaffer:automaticInstancing" );
const InternedString g_doubleSidedAttributeName( "doubleSided" );
const InternedString g_lightMuteAttributeName( "light:mute" );
const InternedString g_renderManLightFilterAttributeName( "ri:lightFilter" );
const RtUString g_userMaterialId( "user:__materialid" );

const vector<InternedString> g_displacementAttributeNames = { "ri:displacement", "osl:displacement", "displacement" };
const vector<InternedString> g_lightAttributeNames = { "ri:light", "light" };
const vector<InternedString> g_surfaceAttributeNames = { "ri:surface", "surface" };

template<typename T>
T *attributeCast( const IECore::RunTimeTyped *v, const IECore::InternedString &name )
{
	if( !v )
	{
		return nullptr;
	}

	T *t = IECore::runTimeCast<T>( v );
	if( t )
	{
		return t;
	}

	IECore::msg( IECore::Msg::Warning, "IECoreRenderMan::Renderer", fmt::format( "Expected {} but got {} for attribute \"{}\".", T::staticTypeName(), v->typeName(), name.c_str() ) );
	return nullptr;
}

template<typename T>
T attributeCast( const IECore::RunTimeTyped *v, const IECore::InternedString &name, const T &defaultValue )
{
	using DataType = IECore::TypedData<T>;
	auto d = attributeCast<const DataType>( v, name );
	return d ? d->readable() : defaultValue;
}

template<typename T>
const T *attribute( const CompoundObject::ObjectMap &attributes, IECore::InternedString name )
{
	auto it = attributes.find( name );
	if( it == attributes.end() )
	{
		return nullptr;
	}

	return attributeCast<const T>( it->second.get(), name );
}

template<typename T>
T attributeValue( const CompoundObject::ObjectMap &attributes, IECore::InternedString name, const T &defaultValue )
{
	using DataType = IECore::TypedData<T>;
	const DataType *data = attribute<DataType>( attributes, name );
	return data ? data->readable() : defaultValue;
}

pair<InternedString, const ShaderNetwork *> shaderNetworkAttribute( const CompoundObject::ObjectMap &attributes, const vector<InternedString> &attributeNames )
{
	for( const auto &name : attributeNames )
	{
		if( const auto *shaderNetwork = attribute<ShaderNetwork>( attributes, name ) )
		{
			return { name, shaderNetwork };
		}
	}
	return { InternedString(), nullptr };
}

bool isMeshLight( const IECoreScene::ShaderNetwork *lightShader )
{
	const IECoreScene::Shader *outputShader = lightShader->outputShader();
	return outputShader && outputShader->getName() == "PxrMeshLight";
}

IECoreScene::ConstShaderNetworkPtr g_facingRatio = []() {

	ShaderNetworkPtr result = new ShaderNetwork;

	const InternedString facingRatioHandle = result->addShader(
		"facingRatio", new Shader( "PxrFacingRatio" )
	);
	const InternedString toFloat3Handle = result->addShader(
		"toFloat3", new Shader( "PxrToFloat3" )
	);
	const InternedString constantHandle = result->addShader(
		"constant", new Shader( "PxrConstant" )
	);

	result->addConnection( { { facingRatioHandle, "resultF" }, { toFloat3Handle, "input" } } );
	result->addConnection( { { toFloat3Handle, "resultRGB" }, { constantHandle, "emitColor" } } );
	result->setOutput( { "constant", "out" } );

	return result;

} ();

IECoreScene::ConstShaderNetworkPtr g_black = []() {

	ShaderNetworkPtr result = new ShaderNetwork;
	const InternedString blackHandle = result->addShader(
		"black", new Shader( "PxrBlack" )
	);
	result->setOutput( { blackHandle, "out" } );

	return result;

} ();

const std::string g_renderAttributePrefix( "render:" );
const std::string g_userAttributePrefix( "user:" );

} // namespace

Attributes::Attributes( const IECore::CompoundObject *attributes, MaterialCache *materialCache )
{
	// Convert shaders.

	const auto [surfaceName, surface] = shaderNetworkAttribute( attributes->members(), g_surfaceAttributeNames );
	m_surfaceMaterial = materialCache->getMaterial( surface ? surface : g_facingRatio.get(), surface ? surfaceName : InternedString(), attributes );

	const auto [displacementName, displacement] = shaderNetworkAttribute( attributes->members(), g_displacementAttributeNames );
	if( displacement )
	{
		m_displacement = materialCache->getDisplacement( displacement, displacementName, attributes );
	}

	m_lightShader = shaderNetworkAttribute( attributes->members(), g_lightAttributeNames ).second;
	if( m_lightShader && isMeshLight( m_lightShader.get() ) )
	{
		// Mesh lights default to having a black material so they don't appear
		// in indirect rays, but the user can override with a surface assignment
		// if they want further control. Other lights don't have materials.
		m_lightMaterial = materialCache->getMaterial( surface ? surface : g_black.get(), surface ? surfaceName : InternedString(), attributes );
	}

	if( surface )
	{
		// Set up material id for PxrCryptomatte. This can be overridden if desired
		// by specifying it in `attributes`, in which case it will be set again below.
		const string materialId = surface->Object::hash().toString();
		m_instanceAttributes.SetString( g_userMaterialId, RtUString( materialId.c_str() ) );
	}

	// Convert attributes into parameter lists for instances and prototypes, and
	// calculate a hash for how the latter affects automatic instancing.

	if( attributeValue<bool>( attributes->members(), g_automaticInstancingAttributeName, true ) )
	{
		m_prototypeHash.emplace( IECore::MurmurHash() );
		if( displacement )
		{
			displacement->hash( *m_prototypeHash );
		}
	}

	for( const auto &[name, value] : attributes->members() )
	{
		auto data = runTimeCast<const Data>( value.get() );
		if( !data )
		{
			continue;
		}

		if( name == g_lightMuteAttributeName )
		{
			ParamListAlgo::convertParameter( Loader::strings().k_lighting_mute, data, m_instanceAttributes );
		}
		else if( name == g_doubleSidedAttributeName )
		{
			int sides = attributeCast<bool>( value.get(), name, true ) ? 2 : 1;
			m_instanceAttributes.SetInteger( Loader::strings().k_Ri_Sides, sides );
		}
		else if( boost::starts_with( name.string(), g_userAttributePrefix ) )
		{
			ParamListAlgo::convertParameter( RtUString( name.c_str() ), data, m_instanceAttributes );
		}
		else if( boost::starts_with( name.string(), g_renderAttributePrefix ) )
		{
			const string withUserPrefix = g_userAttributePrefix + ( name.c_str() + g_renderAttributePrefix.size() );
			ParamListAlgo::convertParameter(
				RtUString( withUserPrefix.c_str() ), data, m_instanceAttributes
			);
		}

		if( !boost::starts_with( name.c_str(), g_renderManPrefix.c_str() ) )
		{
			continue;
		}

		auto it = g_prototypeAttributes.find( name );
		if( it != g_prototypeAttributes.end() )
		{
			ParamListAlgo::convertParameter( it->second, data, m_prototypeAttributes );
			if( m_prototypeHash )
			{
				/// \todo Make the hash match between non-specified attributes and attributes which
				/// are explicitly specified with their default values.
				data->hash( *m_prototypeHash );
			}
		}
		else
		{
			ParamListAlgo::convertParameter( RtUString( name.c_str() + g_renderManPrefix.size() ), data, m_instanceAttributes );

		}
	}

	m_lightFilter = attribute<ShaderNetwork>( attributes->members(), g_renderManLightFilterAttributeName );
}

Attributes::~Attributes()
{
}

const std::optional<IECore::MurmurHash> &Attributes::prototypeHash() const
{
	return m_prototypeHash;
}

const RtParamList &Attributes::prototypeAttributes() const
{
	return m_prototypeAttributes;
}

const RtParamList &Attributes::instanceAttributes() const
{
	return m_instanceAttributes;
}

const Material *Attributes::surfaceMaterial() const
{
	return m_surfaceMaterial.get();
}

const Material *Attributes::lightMaterial() const
{
	return m_lightMaterial.get();
}

const IECoreScene::ShaderNetwork *Attributes::lightShader() const
{
	return m_lightShader.get();
}

const IECoreScene::ShaderNetwork *Attributes::lightFilter() const
{
	return m_lightFilter.get();
}
