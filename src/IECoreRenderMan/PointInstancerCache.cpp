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

#include "PointInstancerCache.h"

#include "Loader.h"
#include "Transform.h"

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreRenderMan;

PointInstancerCache::PointInstancer::~PointInstancer()
{
	if( m_session->renderType == IECoreScenePreview::Renderer::Interactive )
	{
		// Delete instances before the prototypes they refer to.
		for( const auto &id : m_instances )
		{
			m_session->riley->DeleteGeometryInstance( group->id(), id );
		}
		m_prototypeGeometries.clear();
		m_prototypeAttributes.clear();
	}
}

PointInstancerCache::PointInstancerCache( Session *session, GeometryPrototypeCache *geometryPrototypeCache )
	:	m_session( session ), m_geometryPrototypeCache( geometryPrototypeCache )
{
}

PointInstancerCache::ConstPointInstancerPtr PointInstancerCache::get(
	const IECoreScenePreview::Renderer::PointInstancerSamples &samples,
	const IECoreScenePreview::Renderer::SampleTimes &sampleTimes,
	const std::vector<IECoreScenePreview::Renderer::Prototype> &prototypes,
	const Attributes *attributes, const std::string &messageContext
)
{
	auto converter = [&] ( PointInstancerPtr &result ) {

		result = new PointInstancer;
		result->m_session = m_session;

		riley::DisplacementId displacement;
		if( auto d = attributes->displacement() )
		{
			displacement = d->id();
		}

		result->m_prototypeGeometries.reserve( prototypes.size() );
		result->m_prototypeAttributes.reserve( prototypes.size() );
		for( size_t prototypeIndex = 0; prototypeIndex < prototypes.size(); ++prototypeIndex )
		{
			const auto &prototype = prototypes[prototypeIndex];
			result->m_prototypeAttributes.push_back( boost::static_pointer_cast<Attributes>( prototypes[prototypeIndex].attributes ) );
			result->m_prototypeGeometries.push_back(
				m_geometryPrototypeCache->get(
					prototype.samples, prototype.times, result->m_prototypeAttributes.back().get(),
					/* messageContext = */ fmt::format( "{}:prototype{}", messageContext, prototypeIndex )
				)
			);
		}

		result->group = new GeometryPrototype(
			m_session->riley->CreateGeometryPrototype( riley::UserId(), Loader::strings().k_Ri_Group, displacement, RtPrimVarList() ),
			m_session
		);

		vector<IECoreScene::PointInstancer::TransformQuery> sampleQueries;
		for( const auto &sample : samples )
		{
			sampleQueries.push_back( IECoreScene::PointInstancer::TransformQuery( *sample ) );
		}

		auto prototypeIndices = samples[0]->getPrototypeIndex();

		IECoreScenePreview::Renderer::TransformSamples transformSamples;
		transformSamples.resize( samples.size() );
		result->m_instances.reserve( samples[0]->getNumPoints() );
		for( size_t instanceIndex = 0, e = samples[0]->getNumPoints(); instanceIndex < e; ++instanceIndex )
		{
			for( size_t sampleIndex = 0; sampleIndex < sampleQueries.size(); ++sampleIndex )
			{
				transformSamples[sampleIndex] = sampleQueries[sampleIndex].transform( instanceIndex );
			}

			const size_t prototypeIndex = prototypeIndices ? prototypeIndices[instanceIndex] : 0;
			if( !result->m_prototypeGeometries[prototypeIndex] )
			{
				continue;
			}

			/// \todo Investigate `Riley::CreateGeometryInstances()` (plural) to see if
			/// it offers any performance advantage.
			result->m_instances.push_back(
				m_session->riley->CreateGeometryInstance(
					riley::UserId(), result->group->id(), result->m_prototypeGeometries[prototypeIndex]->id(),
					result->m_prototypeAttributes[prototypeIndex]->material()->id(), riley::CoordinateSystemList(),
					AnimatedTransform( transformSamples, sampleTimes ),
					result->m_prototypeAttributes[prototypeIndex]->instanceAttributes()
				)
			);
		}
	};

	if( !attributes->prototypeHash() )
	{
		// Automatic instancing disabled.
		PointInstancerPtr result;
		converter( result );
		return result;
	}

	IECore::MurmurHash h;
	for( const auto &sample : samples )
	{
		sample->hash( h );
	}
	h.append( sampleTimes.data(), sampleTimes.size() );

	for( const auto &prototype : prototypes )
	{
		for( const auto &sample : prototype.samples )
		{
			sample->hash( h );
		}
		h.append( prototype.times.data(), prototype.times.size() );
		h.append( static_cast<const Attributes *>( prototype.attributes.get() )->instanceAttributesHash() );
		h.append( static_cast<const Attributes *>( prototype.attributes.get() )->material()->id().AsUInt32() );
	}

	auto [it, inserted] = m_cache.emplace(
		std::piecewise_construct, std::forward_as_tuple( h ), std::make_tuple()
	);
	std::call_once( it->second.onceFlag, converter, it->second.instancer );

	return it->second.instancer;
}

void PointInstancerCache::clearUnused()
{
	for( auto it = m_cache.begin(); it != m_cache.end(); )
	{
		if( it->second.instancer->refCount() == 1 )
		{
			// Only one reference - this is ours, so nothing outside of the
			// cache is using the instancer.
			it = m_cache.unsafe_erase( it );
		}
		else
		{
			++it;
		}
	}
}
