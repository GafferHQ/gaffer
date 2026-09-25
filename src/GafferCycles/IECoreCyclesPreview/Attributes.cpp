//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "GafferCycles/IECoreCyclesPreview/ShaderNetworkAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

#include "SceneAlgo.h"

#include "IECoreVDB/VDBObject.h"

#include "IECoreScene/MeshPrimitive.h"

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "scene/mesh.h"
#include "scene/volume.h"
IECORE_POP_DEFAULT_VISIBILITY

#include "boost/algorithm/string/predicate.hpp"
#include "boost/container/flat_map.hpp"

using namespace std;
using namespace Imath;
using namespace IECoreCycles;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

template<typename T>
T *reportedCast( const IECore::RunTimeTyped *v, const char *type, const IECore::InternedString &name )
{
	T *t = IECore::runTimeCast<T>( v );
	if( t )
	{
		return t;
	}

	IECore::msg( IECore::Msg::Warning, "IECoreCycles::Renderer",
		fmt::format(
			"Expected {} but got {} for {} \"{}\".",
			T::staticTypeName(), v->typeName(), type, name.c_str()
		)
	);
	return nullptr;
}

template<typename T>
const T *attribute( const IECore::InternedString &name, const IECore::CompoundObject *attributes, const T *defaultValue = nullptr )
{
	if( !attributes )
	{
		return defaultValue;
	}

	IECore::CompoundObject::ObjectMap::const_iterator it = attributes->members().find( name );
	if( it == attributes->members().end() )
	{
		return defaultValue;
	}

	if( auto r = reportedCast<const T>( it->second.get(), "attribute", name ) )
	{
		return r;
	}

	return defaultValue;
}

template<typename T>
T attributeValue( const IECore::InternedString &name, const IECore::CompoundObject *attributes, const T &defaultValue )
{
	using DataType = IECore::TypedData<T>;
	const DataType *data = attribute<DataType>( name, attributes );
	return data ? data->readable() : defaultValue;
}

template<typename T>
std::optional<T> optionalAttribute( const IECore::InternedString &name, const IECore::CompoundObject *attributes )
{
	using DataType = IECore::TypedData<T>;
	const DataType *data = attribute<DataType>( name, attributes );
	return data ? data->readable() : std::optional<T>();
}

// Standard Attributes
IECore::InternedString g_doubleSidedAttributeName( "doubleSided" );
IECore::InternedString g_visibilityAttributeName( "visibility" );
IECore::InternedString g_transformBlurAttributeName( "transformBlur" );
IECore::InternedString g_transformBlurSegmentsAttributeName( "transformBlurSegments" );
IECore::InternedString g_deformationBlurAttributeName( "deformationBlur" );
IECore::InternedString g_deformationBlurSegmentsAttributeName( "deformationBlurSegments" );
IECore::InternedString g_displayColorAttributeName( "render:displayColor" );
IECore::InternedString g_lightAttributeName( "light" );
IECore::InternedString g_muteLightAttributeName( "light:mute" );
IECore::InternedString g_automaticInstancingAttributeName( "gaffer:automaticInstancing" );
// Cycles Attributes
IECore::InternedString g_cclVisibilityAttributeName( "cycles:visibility" );
IECore::InternedString g_useHoldoutAttributeName( "cycles:use_holdout" );
IECore::InternedString g_isShadowCatcherAttributeName( "cycles:is_shadow_catcher" );
IECore::InternedString g_shadowTerminatorShadingOffsetAttributeName( "cycles:shadow_terminator_shading_offset" );
IECore::InternedString g_shadowTerminatorGeometryOffsetAttributeName( "cycles:shadow_terminator_geometry_offset" );
IECore::InternedString g_maxLevelAttributeName( "cycles:max_level" );
IECore::InternedString g_dicingRateAttributeName( "cycles:dicing_rate" );
IECore::InternedString g_adaptiveSpaceAttributeName( "cycles:adaptive_space" );

std::array<IECore::InternedString, 2> g_adaptiveSpaceEnumNames = { {
	"pixel",
	"object",
} };

ccl::Mesh::SubdivisionAdaptiveSpace nameToAdaptiveSpaceEnum( const IECore::InternedString &name )
{
#define MAP_NAME(enumName, enum) if(name == enumName) return enum;
	MAP_NAME(g_adaptiveSpaceEnumNames[0], ccl::Mesh::SubdivisionAdaptiveSpace::SUBDIVISION_ADAPTIVE_SPACE_PIXEL);
	MAP_NAME(g_adaptiveSpaceEnumNames[1], ccl::Mesh::SubdivisionAdaptiveSpace::SUBDIVISION_ADAPTIVE_SPACE_OBJECT);
#undef MAP_NAME

	return ccl::Mesh::SubdivisionAdaptiveSpace::SUBDIVISION_ADAPTIVE_SPACE_PIXEL;
}

// Cycles Light
IECore::InternedString g_cyclesLightAttributeName( "cycles:light" );
// Shader Assignment
IECore::InternedString g_cyclesSurfaceShaderAttributeName( "cycles:surface" );
IECore::InternedString g_oslSurfaceShaderAttributeName( "osl:surface" );
IECore::InternedString g_oslShaderAttributeName( "osl:shader" );
IECore::InternedString g_cyclesVolumeShaderAttributeName( "cycles:volume" );
IECore::InternedString g_surfaceShaderAttributeName( "surface" );
IECore::InternedString g_cyclesDisplacementShaderAttributeName( "cycles:displacement" );
// Ray visibility
IECore::InternedString g_cameraVisibilityAttributeName( "cycles:visibility:camera" );
IECore::InternedString g_diffuseVisibilityAttributeName( "cycles:visibility:diffuse" );
IECore::InternedString g_glossyVisibilityAttributeName( "cycles:visibility:glossy" );
IECore::InternedString g_transmissionVisibilityAttributeName( "cycles:visibility:transmission" );
IECore::InternedString g_shadowVisibilityAttributeName( "cycles:visibility:shadow" );
IECore::InternedString g_scatterVisibilityAttributeName( "cycles:visibility:scatter" );
IECore::InternedString g_USDRayVisibilityBlindDataKey( "__USDRayVisibility" );
// Caustics
IECore::InternedString g_isCausticsCasterAttributeName( "cycles:is_caustics_caster" );
IECore::InternedString g_isCausticsReceiverAttributeName( "cycles:is_caustics_receiver" );

// Cryptomatte asset
IECore::InternedString g_cryptomatteAssetAttributeName( "cycles:asset_name" );

// Light-group
IECore::InternedString g_lightGroupAttributeName( "cycles:lightgroup" );

// Volume
IECore::InternedString g_volumeClippingAttributeName( "cycles:volume_clipping" );
IECore::InternedString g_volumeStepSizeAttributeName( "cycles:volume_step_size" );
IECore::InternedString g_volumeObjectSpaceAttributeName( "cycles:volume_object_space" );
IECore::InternedString g_volumeVelocityScaleAttributeName( "cycles:volume_velocity_scale");
IECore::InternedString g_volumePrecisionAttributeName( "cycles:volume_precision" );

// Shader
IECore::InternedString g_shaderEmissionSamplingMethodAttributeName( "cycles:shader:emission_sampling_method" );
IECore::ConstStringDataPtr g_shaderEmissionSamplingMethodAttributeDefault = new IECore::StringData( "auto" );
IECore::InternedString g_shaderUseTransparentShadowAttributeName( "cycles:shader:use_transparent_shadow" );
IECore::InternedString g_shaderVolumeSamplingMethodAttributeName( "cycles:shader:volume_sampling_method" );
IECore::ConstStringDataPtr g_shaderVolumeSamplingMethodAttributeDefault = new IECore::StringData( "multiple_importance" );
IECore::InternedString g_shaderVolumeInterpolationMethodAttributeName( "cycles:shader:volume_interpolation_method" );
IECore::ConstStringDataPtr g_shaderVolumeInterpolationMethodAttributeDefault = new IECore::StringData( "linear" );
IECore::InternedString g_shaderVolumeStepRateAttributeName( "cycles:shader:volume_step_rate" );
IECore::InternedString g_shaderDisplacementMethodAttributeName( "cycles:shader:displacement_method" );

std::array<IECore::InternedString, 2> g_volumePrecisionEnumNames = { {
	"full",
	"half",
} };

int nameToVolumePrecisionEnum( const IECore::InternedString &name )
{
#define MAP_NAME(enumName, enum) if(name == enumName) return enum;
	MAP_NAME(g_volumePrecisionEnumNames[0], 0);
	MAP_NAME(g_volumePrecisionEnumNames[1], 16);
#undef MAP_NAME

	return 0;
}

ccl::DisplacementMethod displacementMethodFromString( const string &name )
{
	if( name == "bump" )
	{
		return ccl::DisplacementMethod::DISPLACE_BUMP;
	}
	else if( name == "both" )
	{
		return ccl::DisplacementMethod::DISPLACE_BOTH;
	}
	return ccl::DisplacementMethod::DISPLACE_TRUE;
}

const char *customAttributeName( const std::string &attributeName, bool &hasPrecedence )
{
	if( boost::starts_with( attributeName, "user:" ) )
	{
		hasPrecedence = false;
		return attributeName.c_str();
	}
	else if( boost::starts_with( attributeName, "render:" ) )
	{
		hasPrecedence = true;
		return attributeName.c_str() + 7;
	}

	// Not a custom attribute
	return nullptr;
}

IECoreScene::ConstShaderNetworkPtr g_facingRatio = []() {

	IECoreScene::ShaderNetworkPtr result = new IECoreScene::ShaderNetwork;

	const IECore::InternedString geometryHandle = result->addShader(
		"geometry", new IECoreScene::Shader( "geometry" )
	);
	const IECore::InternedString vectorMathHandle = result->addShader(
		"vectorMath", new IECoreScene::Shader(
			"vector_math", "shader",
			{
				{ "math_type", new IECore::StringData( "dot_product" ) }
			}
		)
	);

	result->addConnection( { { geometryHandle, "normal" }, { vectorMathHandle, "vector1" } } );
	result->addConnection( { { geometryHandle, "incoming" }, { vectorMathHandle, "vector2" } } );
	result->setOutput( { vectorMathHandle, "value" } );

	return result;

} ();

} // namespace


//////////////////////////////////////////////////////////////////////////
// Shader implementation
//////////////////////////////////////////////////////////////////////////

Shader::Shader( ccl::Shader *shader, const IECore::MurmurHash &h )
	:	m_shader( shader ), m_hash( h )
{
}

Shader::~Shader()
{
	// Cycles will delete the shader
}

void Shader::hash( IECore::MurmurHash &h ) const
{
	h.append( m_hash );
}

ccl::Shader *Shader::shader() const
{
	return m_shader;
}

//////////////////////////////////////////////////////////////////////////
// ShaderCache implementation
//////////////////////////////////////////////////////////////////////////

ShaderCache::ShaderCache( ccl::Scene *scene )
	:	m_scene( scene )
{
}

ShaderPtr ShaderCache::get( const IECoreScene::ShaderNetwork *surfaceShader )
{
	return get( surfaceShader, nullptr, nullptr, nullptr );
}

ShaderPtr ShaderCache::get(
	const IECoreScene::ShaderNetwork *surfaceShader,
	const IECoreScene::ShaderNetwork *displacementShader,
	const IECoreScene::ShaderNetwork *volumeShader,
	const IECore::CompoundObject *attributes
)
{
	IECore::MurmurHash h; // Cache key
	IECore::MurmurHash hSubst;
	IECore::MurmurHash hSubstDisp;
	IECore::MurmurHash hSubstVol;
	vector<IECore::MurmurHash> hSubstAovs;
	vector<const IECoreScene::ShaderNetwork*> aovShaders;

	// Attributes hash

	std::optional<bool> useTransparentShadow = optionalAttribute<bool>( g_shaderUseTransparentShadowAttributeName, attributes );
	IECore::ConstDataPtr emissionSamplingMethod = attribute<IECore::StringData>( g_shaderEmissionSamplingMethodAttributeName, attributes, g_shaderEmissionSamplingMethodAttributeDefault.get() );

	if( useTransparentShadow )
	{
		h.append( *useTransparentShadow );
	}
	emissionSamplingMethod->hash( h );

	// Surface hash

	const bool singleSided = !attributeValue<bool>( g_doubleSidedAttributeName, attributes, true );

	if( surfaceShader )
	{
		h.append( surfaceShader->Object::hash() );
		h.append( singleSided );
		if( attributes )
		{
			surfaceShader->hashSubstitutions( attributes, hSubst );
			h.append( hSubst );
		}
	}

	// Displacement hash

	ccl::DisplacementMethod displacementMethod = ccl::DisplacementMethod::DISPLACE_BUMP;
	if( displacementShader )
	{
		displacementShader->hash( h );
		if( attributes )
		{
			displacementShader->hashSubstitutions( attributes, hSubstDisp );
			h.append( hSubstDisp );
		}
		// Only look up the displacement shader attribute when we have a displacement shader,
		// so that differences in the attribute don't needlessly change our hash when they're
		// not relevant to the final shader.
		displacementMethod = displacementMethodFromString(
			attributeValue<string>( g_shaderDisplacementMethodAttributeName, attributes, "bump" )
		);
		h.append( displacementMethod );
	}

	// Volume hash

	IECore::ConstDataPtr volumeSamplingMethod = attribute<IECore::StringData>( g_shaderVolumeSamplingMethodAttributeName, attributes, g_shaderVolumeSamplingMethodAttributeDefault.get() );
	IECore::ConstDataPtr volumeInterpolationMethod =  attribute<IECore::StringData>( g_shaderVolumeInterpolationMethodAttributeName, attributes, g_shaderVolumeInterpolationMethodAttributeDefault.get() );
	std::optional<float> volumeStepRate = optionalAttribute<float>( g_shaderVolumeStepRateAttributeName, attributes );

	if( volumeShader )
	{
		IECore::MurmurHash volh = volumeShader->Object::hash();
		if( attributes )
		{
			volumeShader->hashSubstitutions( attributes, hSubstVol );
			volh.append( hSubstVol );
		}
		h.append( volh );
		volumeSamplingMethod->hash( h );
		volumeInterpolationMethod->hash( h );
		if( volumeStepRate )
		{
			h.append( *volumeStepRate );
		}
	}

	// AOV hash
	if( attributes && ( surfaceShader || volumeShader ) )
	{
		for( const auto &member : attributes->members() )
		{
			if( boost::starts_with( member.first.string(), "cycles:aov:" ) )
			{
				const IECoreScene::ShaderNetwork *aovShader = IECore::runTimeCast<IECoreScene::ShaderNetwork>( member.second.get() );
				if( aovShader )
				{
					IECore::MurmurHash aovh = aovShader->Object::hash();
					IECore::MurmurHash hSubstAov;
					aovShader->hashSubstitutions( attributes, hSubstAov );
					aovh.append( hSubstAov );
					h.append( aovh );
					hSubstAovs.push_back( hSubstAov );
					aovShaders.push_back( aovShader );
				}
			}
		}
	}

	Cache::const_accessor readAccessor;
	if( m_cache.find( readAccessor, h ) )
	{
		return readAccessor->second;
	}

	Cache::accessor writeAccessor;
	if( m_cache.insert( writeAccessor, h) )
	{
		const std::string namePrefix = "shader:" + writeAccessor->first.toString() + ":";

		if( surfaceShader || volumeShader )
		{
			// Substitute surface (if needed)
			IECoreScene::ShaderNetworkPtr substitutedSurfaceShader;
			if( surfaceShader && hSubst != IECore::MurmurHash() )
			{
				substitutedSurfaceShader = surfaceShader->copy();
				substitutedSurfaceShader->applySubstitutions( attributes );
				surfaceShader = substitutedSurfaceShader.get();
			}
			// Substitute displacement (if needed)
			IECoreScene::ShaderNetworkPtr substitutedDisplacementShader;
			if( displacementShader && hSubstDisp != IECore::MurmurHash() )
			{
				substitutedDisplacementShader = displacementShader->copy();
				substitutedDisplacementShader->applySubstitutions( attributes );
				displacementShader = substitutedDisplacementShader.get();
			}
			// Substitute volume (if needed)
			IECoreScene::ShaderNetworkPtr substitutedVolumeShader;
			if( volumeShader && hSubstVol != IECore::MurmurHash() )
			{
				substitutedVolumeShader = volumeShader->copy();
				substitutedVolumeShader->applySubstitutions( attributes );
				volumeShader = substitutedVolumeShader.get();
			}
			// Get all the possible AOV shaders
			vector<IECoreScene::ShaderNetworkPtr> substitutedAOVShaders;
			for( size_t i = 0; i < hSubstAovs.size(); ++i )
			{
				if( hSubstAovs[i] != IECore::MurmurHash() )
				{
					substitutedAOVShaders.push_back( aovShaders[i]->copy() );
					substitutedAOVShaders.back()->applySubstitutions( attributes );
					aovShaders[i] = substitutedAOVShaders.back().get();
				}
			}

			// Make the `ccl::ShaderGraph`.

			std::unique_ptr<ccl::ShaderGraph> graph = ShaderNetworkAlgo::convertGraph(
				surfaceShader, displacementShader, volumeShader, m_scene, namePrefix
			);

			if( surfaceShader && singleSided )
			{
				ShaderNetworkAlgo::setSingleSided( graph.get() );
			}

			for( const IECoreScene::ShaderNetwork *aovShader : aovShaders )
			{
				ShaderNetworkAlgo::convertAOV( aovShader, graph.get(), m_scene, namePrefix );
			}

			// Make the `ccl::Shader` to house the graph. We reference this via
			// raw pointer, because Cycles doesn't support the deletion of
			// Shader nodes.

			ccl::Shader *shader = SceneAlgo::createNodeWithLock<ccl::Shader>( m_scene );
			if( auto nameSource = surfaceShader ? surfaceShader : volumeShader )
			{
				shader->name = ccl::ustring( namePrefix + nameSource->getOutput().shader.string() );
			}

			shader->set_displacement_method( displacementMethod );
			SocketAlgo::setSocket( shader, shader->get_emission_sampling_method_socket(), emissionSamplingMethod.get() );
			shader->set_use_transparent_shadow( useTransparentShadow ? useTransparentShadow.value() : true );

			if( volumeShader )
			{
				SocketAlgo::setSocket( shader, shader->get_volume_sampling_method_socket(), volumeSamplingMethod.get() );
				SocketAlgo::setSocket( shader, shader->get_volume_interpolation_method_socket(), volumeInterpolationMethod.get() );
				shader->set_volume_step_rate( volumeStepRate ? volumeStepRate.value() : 1.0f );
			}

			shader->set_graph( std::move( graph ) );

			SceneAlgo::tagUpdateWithLock( shader, m_scene );

			writeAccessor->second = new IECoreCycles::Shader( shader, h );
		}
	}

	return writeAccessor->second;
}

void ShaderCache::clearUnused()
{
	// TODO: Cycles currently doesn't delete unused shaders anyways and it's problematic
	// to delete them in a live render, so we just retain all shaders created, Cycles
	// will delete them all once the session is finished.
	return;
}

//////////////////////////////////////////////////////////////////////////
// Attributes implementation
//////////////////////////////////////////////////////////////////////////

Attributes::Attributes( const IECore::CompoundObject *attributes, ShaderCache *shaderCache )
	:	m_visibility( ~0 ),
		m_useHoldout( false ),
		m_isShadowCatcher( false ),
		m_shadowTerminatorShadingOffset( 0.0f ),
		m_shadowTerminatorGeometryOffset( 0.0f ),
		m_maxLevel( 1 ),
		m_dicingRate( 1.0f ),
		m_adaptiveSpace( "pixel" ),
		m_color( Color3f( 1.0f ) ),
		m_volume( attributes ),
		m_assetName( "" ),
		m_lightGroup( "" ),
		m_isCausticsCaster( false ),
		m_isCausticsReceiver( false )
{
	updateVisibility( g_cameraVisibilityAttributeName,       (int)ccl::PATH_RAY_CAMERA,         attributes );
	updateVisibility( g_diffuseVisibilityAttributeName,      (int)ccl::PATH_RAY_DIFFUSE,        attributes );
	updateVisibility( g_glossyVisibilityAttributeName,       (int)ccl::PATH_RAY_GLOSSY,         attributes );
	updateVisibility( g_transmissionVisibilityAttributeName, (int)ccl::PATH_RAY_TRANSMIT,       attributes );
	updateVisibility( g_shadowVisibilityAttributeName,       (int)ccl::PATH_RAY_SHADOW,         attributes );
	updateVisibility( g_scatterVisibilityAttributeName,      (int)ccl::PATH_RAY_VOLUME_SCATTER, attributes );

	m_useHoldout = attributeValue<bool>( g_useHoldoutAttributeName, attributes, m_useHoldout );
	m_isShadowCatcher = attributeValue<bool>( g_isShadowCatcherAttributeName, attributes, m_isShadowCatcher );
	m_shadowTerminatorShadingOffset = attributeValue<float>( g_shadowTerminatorShadingOffsetAttributeName, attributes, m_shadowTerminatorShadingOffset );
	m_shadowTerminatorGeometryOffset = attributeValue<float>( g_shadowTerminatorGeometryOffsetAttributeName, attributes, m_shadowTerminatorGeometryOffset );
	m_maxLevel = attributeValue<int>( g_maxLevelAttributeName, attributes, m_maxLevel );
	m_dicingRate = attributeValue<float>( g_dicingRateAttributeName, attributes, m_dicingRate );
	m_adaptiveSpace = attributeValue<std::string>( g_adaptiveSpaceAttributeName, attributes, m_adaptiveSpace );
	m_color = attributeValue<Color3f>( g_displayColorAttributeName, attributes, m_color );
	m_lightGroup = attributeValue<std::string>( g_lightGroupAttributeName, attributes, m_lightGroup );
	m_assetName = attributeValue<std::string>( g_cryptomatteAssetAttributeName, attributes, m_assetName );
	m_isCausticsCaster = attributeValue<bool>( g_isCausticsCasterAttributeName, attributes, m_isCausticsCaster );
	m_isCausticsReceiver = attributeValue<bool>( g_isCausticsReceiverAttributeName, attributes, m_isCausticsReceiver );
	m_automaticInstancing = attributeValue<bool>( g_automaticInstancingAttributeName, attributes, true );

	// Surface shader
	const IECoreScene::ShaderNetwork *volumeShaderAttribute = attribute<IECoreScene::ShaderNetwork>( g_cyclesVolumeShaderAttributeName, attributes );
	const IECoreScene::ShaderNetwork *surfaceShaderAttribute = attribute<IECoreScene::ShaderNetwork>( g_cyclesSurfaceShaderAttributeName, attributes );
	surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<IECoreScene::ShaderNetwork>( g_oslSurfaceShaderAttributeName, attributes );
	surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<IECoreScene::ShaderNetwork>( g_oslShaderAttributeName, attributes );
	surfaceShaderAttribute = surfaceShaderAttribute ? surfaceShaderAttribute : attribute<IECoreScene::ShaderNetwork>( g_surfaceShaderAttributeName, attributes );
	if( !surfaceShaderAttribute && !volumeShaderAttribute )
	{
		surfaceShaderAttribute = g_facingRatio.get();
	}
	const IECoreScene::ShaderNetwork *displacementShaderAttribute = attribute<IECoreScene::ShaderNetwork>( g_cyclesDisplacementShaderAttributeName, attributes );

	m_shader = shaderCache->get( surfaceShaderAttribute, displacementShaderAttribute, volumeShaderAttribute, attributes );

	// Light shader

	m_muteLight = attributeValue<bool>( g_muteLightAttributeName, attributes, false );
	m_lightAttribute = attribute<IECoreScene::ShaderNetwork>( g_cyclesLightAttributeName, attributes );
	m_lightAttribute = m_lightAttribute ? m_lightAttribute : attribute<IECoreScene::ShaderNetwork>( g_lightAttributeName, attributes );
	if( m_lightAttribute )
	{
		IECoreScene::ShaderNetworkPtr converted = m_lightAttribute->copy();
		ShaderNetworkAlgo::convertUSDShaders( converted.get() );
		m_lightAttribute = converted;

		IECoreScene::ShaderNetworkPtr lightShader = ShaderNetworkAlgo::convertLightShader( m_lightAttribute.get() );
		m_lightShader = shaderCache->get( lightShader.get(), nullptr, nullptr, attributes );

		// Cycles requires lights to be set as shadow catchers in order to contribute shadows to the
		// shadow pass, so we disregard the attribute and override lights to always be shadow catchers.
		m_isShadowCatcher = true;

		if( auto rayVisibility = m_lightAttribute->outputShader()->blindData()->member<IECore::IntData>( g_USDRayVisibilityBlindDataKey ) )
		{
			// If the light has been converted from a USD light, we override diffuse and glossy visibility
			// based on the USD light's diffuse and specular parameters. See ShaderNetworkAlgo::transferUSDLightParameters()
			constexpr int rayMask = (int)( ccl::PATH_RAY_DIFFUSE | ccl::PATH_RAY_GLOSSY );
			m_visibility = ( m_visibility & ~rayMask ) | ( rayVisibility->readable() & rayMask );
		}
	}

	// Custom attributes

	using CustomAttributesMap = boost::container::flat_map<IECore::InternedString, IECore::ConstDataPtr>;
	CustomAttributesMap customMap;

	for( IECore::CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; ++it )
	{
		bool hasPrecedence = false;
		if( const char *name = customAttributeName( it->first.string(), hasPrecedence ) )
		{
			if( const IECore::Data *data = IECore::runTimeCast<const IECore::Data>( it->second.get() ) )
			{
				auto inserted = customMap.insert( CustomAttributesMap::value_type( name, nullptr ) );
				if( hasPrecedence || inserted.second )
				{
					inserted.first->second = data;
				}
			}
		}
	}

	for( const auto &attr : customMap )
	{
		ccl::ParamValue paramValue = SocketAlgo::setParamValue( attr.first, attr.second.get() );
		if( paramValue.data() )
		{
			m_custom.push_back( paramValue );
		}
		else
		{
			IECore::msg(
				IECore::Msg::Warning, "IECoreCycles::Renderer",
				fmt::format(
					"Custom attribute \"{}\" has unsupported type \"{}\".",
					attr.first.string(), attr.second->typeName()
				)
			);
		}
	}
}

bool Attributes::canInstanceGeometry( const IECore::Object *object ) const
{
	if( !IECore::runTimeCast<const IECoreScene::VisibleRenderable>( object ) || !m_automaticInstancing )
	{
		return false;
	}

	if( const IECoreScene::MeshPrimitive *mesh = IECore::runTimeCast<const IECoreScene::MeshPrimitive>( object ) )
	{
		if( mesh->interpolation() == "catmullClark" )
		{
			return m_adaptiveSpace == "object";
		}
		else
		{
			return true;
		}
	}

	return true;
}

void Attributes::applyObject( ccl::Object *object, ccl::Scene *scene ) const
{
	object->set_visibility( m_visibility );
	object->set_use_holdout( m_useHoldout );
	object->set_is_shadow_catcher( m_isShadowCatcher );
	object->set_shadow_terminator_shading_offset( m_shadowTerminatorShadingOffset );
	object->set_shadow_terminator_geometry_offset( m_shadowTerminatorGeometryOffset );
	object->set_color( SocketAlgo::setColor( m_color ) );
	object->set_asset_name( ccl::ustring( m_assetName.c_str() ) );
	object->set_is_caustics_caster( m_isCausticsCaster );
	object->set_is_caustics_receiver( m_isCausticsReceiver );
	object->set_lightgroup( ccl::ustring( m_lightGroup.c_str() ) );
	object->attributes = m_custom;

	SceneAlgo::tagUpdateWithLock( object, scene );
}

void Attributes::hashGeometry( const IECore::Object *object, IECore::MurmurHash &h ) const
{
	if( auto mesh = IECore::runTimeCast<const IECoreScene::MeshPrimitive>( object ) )
	{
		if( mesh->interpolation() == "catmullClark" )
		{
			hashSubdivision( h );
		}
	}
	else if( IECore::runTimeCast<const IECoreVDB::VDBObject>( object ) )
	{
		m_volume.hash( h );
	}
	h.append( m_shader->shader()->graph->displacement_hash );
}

void Attributes::hashGeometry( const ccl::Geometry *geometry, IECore::MurmurHash &h ) const
{
	if( geometry->is_mesh() )
	{
		if( static_cast<const ccl::Mesh *>( geometry )->get_num_subd_faces() )
		{
			hashSubdivision( h );
		}
	}
	else if( geometry->is_volume() )
	{
		m_volume.hash( h );
	}
	h.append( m_shader->shader()->graph->displacement_hash );
}

void Attributes::hashSubdivision( IECore::MurmurHash &h ) const
{
	h.append( m_dicingRate );
	h.append( m_maxLevel );
	h.append( m_adaptiveSpace );
}

void Attributes::applyGeometry( ccl::Geometry *geometry, ccl::Scene *scene ) const
{
	if( geometry->is_mesh() )
	{
		auto mesh = static_cast<ccl::Mesh *>( geometry );
		if( mesh->get_num_subd_faces() )
		{
			mesh->set_subd_dicing_rate( m_dicingRate );
			mesh->set_subd_max_level( m_maxLevel );
			mesh->set_subd_adaptive_space( nameToAdaptiveSpaceEnum( m_adaptiveSpace ) );
			SceneAlgo::tagUpdateWithLock( geometry, scene, /* rebuild = */ true );
		}
	}
	else if( geometry->is_volume() )
	{
		m_volume.apply( static_cast<ccl::Volume *>( geometry ) );
		SceneAlgo::tagUpdateWithLock( geometry, scene, false );
	}
}

void Attributes::hashShader( IECore::MurmurHash &h ) const
{
	m_shader->hash( h );
}

void Attributes::applyShader( ccl::Geometry *geometry, ccl::Scene *scene ) const
{
	const ccl::array<ccl::Node *> oldShaders = geometry->get_used_shaders();
	if( !oldShaders.size() || oldShaders[0] != m_shader->shader() )
	{
		ccl::array<ccl::Node *> shaders;
		shaders.push_back_slow( m_shader->shader() );
		{
			// We need the scene lock because `tag_used()` will modify the
			// scene.
			std::scoped_lock sceneLock( scene->mutex );
			m_shader->shader()->tag_used( scene );
			// But we also use the lock for `set_used_shaders()`, to protect
			// the non-atomic increment made in `ccl::Node::reference()`.
			// > Note : because we instance geometry, two objects
			// > might be fighting over what shader the geometry should have.
			// > This needs fixing in its own right, but until then, the lock
			// > at least prevents concurrent access.
			geometry->set_used_shaders( shaders );

			if( geometry->is_mesh() )
			{
				auto mesh = static_cast<ccl::Mesh *>( geometry );
				/// \todo I don't know why this is necessary, but without it the new
				/// assignment doesn't seem to be transferred to the render device.
				mesh->tag_shader_modified();
			}
			else if(
				geometry->is_volume() && geometry->is_modified() &&
				static_cast<ccl::Volume *>( geometry )->get_triangles().size()
			)
			{
				// We've replaced an existing shader on a volume
				// from which Cycles has already built a mesh, so
				// we cheekily clear the modified tag to prevent
				// the volume from disappearing.
				/// \todo I suspect we need something similar for meshes,
				/// to prevent unnecessary BVH rebuilds.
				geometry->clear_modified();
			}
		}
	}
}

void Attributes::applyLight( ccl::Light *light, ccl::Scene *scene ) const
{
	if( m_lightAttribute )
	{
		ShaderNetworkAlgo::convertLight( m_lightAttribute.get(), light );
		ccl::array<ccl::Node *> shaders;
		shaders.push_back_slow( m_lightShader->shader() );
		{
			// We need the scene lock for `set_used_shaders()`, to protect
			// the non-atomic increment made in `ccl::Node::reference()`.
			std::scoped_lock sceneLock( scene->mutex );
			light->set_used_shaders( shaders );
		}

		light->set_is_enabled( !m_muteLight );
	}
	else
	{
		// No `cycles:light` shader assignment. Most likely a light
		// intended for another renderer, so we turn off the Cycles
		// light.
		light->set_is_enabled( false );
	}

	if( !light->get_is_enabled() )
	{
		// Alas, `ccl::LightManager::test_enabled_lights()` will
		// re-enable the light unless we also set its strength to zero.
		light->set_strength( ccl::zero_float3() );
	}

	SceneAlgo::tagUpdateWithLock( light, scene );
}

int Attributes::getVolumePrecision() const
{
	return m_volume.precision ? nameToVolumePrecisionEnum( m_volume.precision.value() ) : 0;
}

float Attributes::getVolumeClipping() const
{
	return m_volume.clipping ? m_volume.clipping.value() : 0.001f;
}

void Attributes::updateVisibility( const IECore::InternedString &name, int rayType, const IECore::CompoundObject *attributes )
{
	if( const IECore::BoolData *d = attribute<IECore::BoolData>( name, attributes ) )
	{
		if( d->readable() )
		{
			m_visibility |= rayType;
		}
		else
		{
			m_visibility = m_visibility & ~rayType;
		}
	}
}

Attributes::Volume::Volume( const IECore::CompoundObject *attributes )
{
	clipping = optionalAttribute<float>( g_volumeClippingAttributeName, attributes );
	stepSize = optionalAttribute<float>( g_volumeStepSizeAttributeName, attributes );
	objectSpace = optionalAttribute<bool>( g_volumeObjectSpaceAttributeName, attributes );
	velocityScale = optionalAttribute<float>( g_volumeVelocityScaleAttributeName, attributes );
	precision = optionalAttribute<string>( g_volumePrecisionAttributeName, attributes );
}


void Attributes::Volume::hash( IECore::MurmurHash &h ) const
{
	if( clipping && clipping.value() != 0.001f )
	{
		h.append( clipping.value() );
	}
	if( stepSize && stepSize.value() != 0.0f )
	{
		h.append( stepSize.value() );
	}
	if( objectSpace && objectSpace.value() != false )
	{
		h.append( objectSpace.value() );
	}
	if( velocityScale && velocityScale.value() != 1.0f )
	{
		h.append( velocityScale.value() );
	}
	if( precision && precision.value() != g_volumePrecisionEnumNames[0].c_str() )
	{
		h.append( precision.value() );
	}
}

void Attributes::Volume::apply( ccl::Volume *volume ) const
{
	if( stepSize )
	{
		volume->set_step_size( stepSize.value() );
	}
	if( objectSpace )
	{
		volume->set_object_space( objectSpace.value() );
	}
	if( velocityScale )
	{
		volume->set_velocity_scale( velocityScale.value() );
	}
}
