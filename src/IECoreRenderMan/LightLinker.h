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

#pragma once

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "IECoreScene/ShaderNetwork.h"

#include <map>
#include <mutex>
#include <set>
#include <unordered_set>

namespace IECoreRenderMan
{

class Light;
class LightFilter;

/// Light filters aren't first-class objects in Riley. Instead they are just
/// extra shaders bolted on to the shader owned by the light. So we need our own
/// centralised tracking to update the lights when the filters are edited.
class LightLinker
{

	public :

		// Interface used by Light and LightFilter
		// =======================================
		//
		// These methods are used to keep the LightLinker up to date with
		// changes made to lights and filters, and may all be called
		// concurrently.

		IECoreScene::ConstShaderNetworkPtr registerFilterLinks( Light *light, const IECoreScenePreview::Renderer::ConstObjectSetPtr &lightFilters );
		void deregisterFilterLinks( Light *light, const IECoreScenePreview::Renderer::ConstObjectSetPtr &lightFilters );
		void dirtyLightFilter( const LightFilter *lightFilter );

		// Interface used by Renderer
		// ==========================

		// Called prior to rendering to synchronise any pending changes to
		// light filters. Should not be called concurrently with other methods.
		void updateDirtyLinks();

	private :

		static IECoreScene::ConstShaderNetworkPtr lightFilterShader( const IECoreScenePreview::Renderer::ObjectSet *filters );

		// Data structure for tracking dependencies between light filters and
		// lights. The goal is to be able to efficiently update all affected
		// Lights when the shader changes on a LightFilter. We don't use a naive
		// mapping directly from LightFilters to sets of affected Lights because
		// the number of connections scales quadratically (`N * N` connections)
		// when N lights depend on the same N filters. Instead our tracking is
		// based around the ObjectSets used to perform the linking. We track
		// which ObjectSets each filter is a member of, and which lights are
		// affected by each ObjectSet, giving a total of `N + N` connections.
		// When a filter is modified, we dirty the ObjectSet, and to perform our
		// update we update all the lights affected by the dirty sets.

		// Forms the basis for our tracking, giving us the identity of each
		// ObjectSet but without keeping the ObjectInterface members alive
		// longer than necessary.
		using WeakObjectSetPtr = std::weak_ptr<const IECoreScenePreview::Renderer::ObjectSet>;

		// Stores information for each unique set of LightFilters - which
		// lights they are linked to, and their combined shader.
		struct FilterSet
		{
			IECoreScene::ConstShaderNetworkPtr lightFilterShader;
			std::unordered_set<Light *> affectedLights;
		};

		/// Maps from ObjectSet to the information provided by FilterSet.
		/// \todo Use `unordered_map` (or `concurrent_unordered_map`) when `std::owner_hash()`
		/// becomes available (in C++26).
		using FilterSets = std::map<WeakObjectSetPtr, FilterSet, std::owner_less<WeakObjectSetPtr>>;
		std::mutex m_filterSetsMutex;
		FilterSets m_filterSets;

		// Stores the dirty filter sets to be handled in `updateDirtyLinks()`.
		/// \todo Use `unordered_set` (or `concurrent_unordered_set`) when `std::owner_hash()`
		/// becomes available (in C++26).
		using DirtyFilterSets = std::set<WeakObjectSetPtr, std::owner_less<WeakObjectSetPtr>>;
		std::mutex m_dirtyFilterSetsMutex;
		DirtyFilterSets m_dirtyFilterSets;

};

} // namespace IECoreRenderMan
