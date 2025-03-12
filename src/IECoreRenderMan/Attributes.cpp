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

#include "IECoreScene/ShaderNetwork.h"

#include "IECore/SimpleTypedData.h"

#include "RixPredefinedStrings.hpp"

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
const InternedString g_displacementAttributeName( "displacement" );
const InternedString g_doubleSidedAttributeName( "doubleSided" );
const InternedString g_lightMuteAttributeName( "light:mute" );
const InternedString g_lightShaderAttributeName( "light" );
const InternedString g_oslDisplacementAttributeName( "osl:displacement" );
const InternedString g_renderManDisplacementAttributeName( "ri:displacement" );
const InternedString g_renderManLightShaderAttributeName( "ri:light" );
const InternedString g_renderManSurfaceAttributeName( "ri:surface" );
const InternedString g_surfaceAttributeName( "surface" );
const RtUString g_userMaterialId( "user:__materialid" );

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
	const InternedString facingRatioHandle = result->addShader(
		"black", new Shader( "PxrBlack" )
	);
	result->setOutput( { "black", "out" } );

	return result;

} ();

} // namespace

Attributes::Attributes( const IECore::CompoundObject *attributes, MaterialCache *materialCache )
{
	// Convert shaders.

	const ShaderNetwork *surface = attribute<ShaderNetwork>( attributes->members(), g_renderManSurfaceAttributeName );
	surface = surface ? surface : attribute<ShaderNetwork>( attributes->members(), g_surfaceAttributeName );
	m_surfaceMaterial = materialCache->getMaterial( surface ? surface : g_facingRatio.get() );

	const ShaderNetwork *displacement = attribute<ShaderNetwork>( attributes->members(), g_renderManDisplacementAttributeName );
	displacement = displacement ? displacement : attribute<ShaderNetwork>( attributes->members(), g_oslDisplacementAttributeName );
	displacement = displacement ? displacement : attribute<ShaderNetwork>( attributes->members(), g_displacementAttributeName );
	if( displacement )
	{
		m_displacement = materialCache->getDisplacement( displacement );
	}

	m_lightShader = attribute<ShaderNetwork>( attributes->members(), g_renderManLightShaderAttributeName );
	m_lightShader = m_lightShader ? m_lightShader : attribute<ShaderNetwork>( attributes->members(), g_lightShaderAttributeName );
	if( m_lightShader && isMeshLight( m_lightShader.get() ) )
	{
		// Mesh lights default to having a black material so they don't appear
		// in indirect rays, but the user can override with a surface assignment
		// if they want further control. Other lights don't have materials.
		m_lightMaterial = materialCache->getMaterial( surface ? surface : g_black.get() );
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
			ParamListAlgo::convertParameter( Rix::k_lighting_mute, data, m_instanceAttributes );
		}
		else if( name == g_doubleSidedAttributeName )
		{
			int sides = attributeCast<bool>( value.get(), name, true ) ? 2 : 1;
			m_instanceAttributes.SetInteger( Rix::k_Ri_Sides, sides );
		}
		else if( boost::starts_with( name.c_str(), "user:" ) )
		{
			ParamListAlgo::convertParameter( RtUString( name.c_str() ), data, m_instanceAttributes );
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
