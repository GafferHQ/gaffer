//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

#include "LightLinker.h"

#include "IECoreRenderMan/ShaderNetworkAlgo.h"

#include "Light.h"
#include "LightFilter.h"

#include "fmt/format.h"

using namespace std;
using namespace Imath;
using namespace IECoreRenderMan;

LightLinker::LightLinker()
{
	m_lightSets.groupNamePrefix = "lightGroup";
	m_shadowSets.groupNamePrefix = "shadowGroup";
}

IECoreScene::ConstShaderNetworkPtr LightLinker::registerFilterLinks( Light *light, const IECoreScenePreview::Renderer::ConstObjectSetPtr &lightFilters )
{
	std::lock_guard lock( m_filterSetsMutex );

	auto [it, inserted] = m_filterSets.emplace( lightFilters, FilterSet() );
	if( inserted )
	{
		it->second.lightFilterShader = lightFilterShader( lightFilters.get() );
		for( const auto &s : *lightFilters )
		{
			// We need to protect against concurrent access to
			// `setMemberships()` by another call to `registerFilterLinks()` but
			// we don't need a different lock for that - our lock on
			// `m_filterSetsMutex` is sufficient for that.
			static_cast<LightFilter *>( s.get() )->setMemberships().insert( lightFilters );
		}
	}

	[[maybe_unused]] const bool lightInserted = it->second.affectedLights.insert( light ).second;
	assert( lightInserted );

	return it->second.lightFilterShader;
}

void LightLinker::deregisterFilterLinks( Light *light, const IECoreScenePreview::Renderer::ConstObjectSetPtr &lightFilters )
{
	std::lock_guard lock( m_filterSetsMutex );

	auto it = m_filterSets.find( lightFilters );
	assert( it != m_filterSets.end() );
	[[maybe_unused]] bool erased = it->second.affectedLights.erase( light );
	assert( erased );
	if( it->second.affectedLights.empty() )
	{
		m_filterSets.erase( it );
	}
}

void LightLinker::dirtyLightFilter( const LightFilter *lightFilter )
{
	std::lock_guard lock( m_dirtyFilterSetsMutex );
	// Technically we would need a separate lock here to protect against
	// races on `setMemberships()` with `registerFilterLinks()`. But in practice
	// links are never made concurrently with edits to light filter attributes
	// so we don't bother.
	m_dirtyFilterSets.insert( lightFilter->setMemberships().begin(), lightFilter->setMemberships().end() );
}

const RtUString LightLinker::registerLightSet( SetType setType, const IECoreScenePreview::Renderer::ConstObjectSetPtr &lights )
{
	std::lock_guard lock( m_lightAndShadowSetsMutex );
	LightSets &lightSets = setType == SetType::Light ? m_lightSets : m_shadowSets;
	LightSet &lightSet = lightSets.map[lights];
	lightSet.useCount++;
	if( lightSet.useCount == 1 )
	{
		const string groupName = fmt::format( "{}{}", lightSets.groupNamePrefix, lightSets.nextGroupIndex++ );
		lightSet.groupName = RtUString( groupName.c_str() );
		m_lightLinksDirty = true;
	}

	return lightSet.groupName;
}

void LightLinker::deregisterLightSet( SetType setType, const IECoreScenePreview::Renderer::ConstObjectSetPtr &lights )
{
	std::lock_guard lock( m_lightAndShadowSetsMutex );
	LightSets &lightSets = setType == SetType::Light ? m_lightSets : m_shadowSets;
	auto it = lightSets.map.find( lights );
	assert( it != lightSets.map.end() );
	assert( it->second.useCount );
	it->second.useCount--;
	if( !it->second.useCount )
	{
		lightSets.map.erase( it );
	}
}

void LightLinker::updateDirtyLinks()
{
	updateDirtyFilterLinks();
	updateDirtyLightLinks();
}

void LightLinker::updateDirtyFilterLinks()
{
	// Not taking any locks, because we're not advertised as being
	// concurrency-safe.

	for( const auto &weakSet : m_dirtyFilterSets )
	{
		auto set = weakSet.lock();
		if( !set )
		{
			// After the set was dirtied, all affected lights must
			// have been linked to a different set.
			m_filterSets.erase( set );
			continue;
		}

		auto it = m_filterSets.find( set );
		assert( it != m_filterSets.end() );
		it->second.lightFilterShader = lightFilterShader( set.get() );
		for( auto light : it->second.affectedLights )
		{
			light->updateLightFilterShader( it->second.lightFilterShader );
		}
	}

	m_dirtyFilterSets.clear();
}

IECoreScene::ConstShaderNetworkPtr LightLinker::lightFilterShader( const IECoreScenePreview::Renderer::ObjectSet *filters )
{
	vector<const IECoreScene::ShaderNetwork *> networks;
	for( const auto &s : *filters )
	{
		auto lightFilter = static_cast<const LightFilter *>( s.get() );
		if( !lightFilter->shader() )
		{
			continue;
		}
		networks.push_back( lightFilter->shader() );
	}
	return ShaderNetworkAlgo::combineLightFilters( networks );
}

void LightLinker::updateDirtyLightLinks()
{
	std::lock_guard lock( m_lightAndShadowSetsMutex );
	if( !m_lightLinksDirty )
	{
		return;
	}

	// For all lights currently in a linking set, calculate the right value
	// for their `grouping:membership` attribute by concatenating the light
	// group names. There are a couple of compromises here :
	//
	// - If a light is removed from all groups, it won't get updated at all
	//   and will retain its old memberships even though those groups are
	//   no longer used. This seems fairly harmless though.
	// - We are updating all lights any time linking changes.
	//
	// Both these could be addressed, but at the expense of tracking more
	// complex state.
	/// \todo See if the more complex tracking is warranted in typical
	/// production scenarios.

	struct LightData
	{
		string groupMemberships;
		string shadowSubsets;
	};
	std::unordered_map<Light *, LightData> lightData;

	for( const auto &[objectSet, lightSet] : m_lightSets.map )
	{
		for( auto &light : *objectSet )
		{
			auto &data = lightData[static_cast<Light *>( light.get() )];
			if( data.groupMemberships.size() )
			{
				data.groupMemberships += " ";
			}
			data.groupMemberships += lightSet.groupName.CStr();
		}
	}

	// Likewise, calculate the right value for the `shadowSubset` parameters.

	for( const auto &[objectSet, shadowSet] : m_shadowSets.map )
	{
		for( auto &light : *objectSet )
		{
			auto &data = lightData[static_cast<Light *>( light.get() )];
			if( data.shadowSubsets.size() )
			{
				data.shadowSubsets += " ";
			}
			data.shadowSubsets += shadowSet.groupName.CStr();
		}
	}

	// Push the updated data to the lights.

	for( auto &[light, data] : lightData )
	{
		light->updateLinking(
			RtUString( data.groupMemberships.c_str() ),
			RtUString( ( "defaultShadowGroup " + data.shadowSubsets ).c_str() )
		);
	}

	m_lightLinksDirty = false;
}
