//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

#include "IECore/RefCounted.h"

#include "Attributes.h"
#include "GeometryPrototypeCache.h"
#include "Session.h"

#include "tbb/concurrent_unordered_map.h"

#include <mutex>

namespace IECoreRenderMan
{

class PointInstancerCache
{

	public :

		PointInstancerCache( Session *session, GeometryPrototypeCache *geometryPrototypeCache );

		struct PointInstancer : public IECore::RefCounted
		{

			~PointInstancer() override;

			// Group below which instances are parented.
			GeometryPrototypePtr group;

			private :

				friend class PointInstancerCache;

				Session *m_session;
				std::vector<GeometryPrototypePtr> m_prototypeGeometries; // Maintains lifetime of prototypes
				std::vector<AttributesPtr> m_prototypeAttributes; // Maintains lifetime of attributes
				std::vector<riley::GeometryInstanceId> m_instances; // Maintains lifetime of instances

		};
		IE_CORE_DECLAREPTR( PointInstancer );

		// Can be called concurrently with other calls to `get()`.
		ConstPointInstancerPtr get(
			const IECoreScenePreview::Renderer::PointInstancerSamples &samples,
			const IECoreScenePreview::Renderer::SampleTimes &sampleTimes,
			const std::vector<IECoreScenePreview::Renderer::Prototype> &prototypes,
			const Attributes *attributes, const std::string &messageContext
		);

		// Must not be called concurrently with anything.
		void clearUnused();

	private :

		Session *m_session;
		GeometryPrototypeCache *m_geometryPrototypeCache;

		struct CacheEntry
		{
			std::once_flag onceFlag;
			PointInstancerPtr instancer;
		};
		using Cache = tbb::concurrent_unordered_map<IECore::MurmurHash, CacheEntry>;
		Cache m_cache;

};

} // namespace IECoreRenderMan
