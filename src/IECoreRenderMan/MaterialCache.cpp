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

#include "MaterialCache.h"

#include "ShaderNetworkAlgo.h"

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreRenderMan;

MaterialCache::MaterialCache( const Session *session )
	:	m_session( session )
{
}

ConstMaterialPtr MaterialCache::getMaterial( const IECoreScene::ShaderNetwork *network )
{
	Cache::accessor a;
	m_cache.insert( a, network->Object::hash() );
	if( !a->second )
	{
		std::vector<riley::ShadingNode> nodes = ShaderNetworkAlgo::convert( network );
		riley::MaterialId id = m_session->riley->CreateMaterial( riley::UserId(), { (uint32_t)nodes.size(), nodes.data() }, RtParamList() );
		a->second = new Material( id, m_session );
	}
	return a->second;
}

ConstDisplacementPtr MaterialCache::getDisplacement( const IECoreScene::ShaderNetwork *network )
{
	DisplacementCache::accessor a;
	m_displacementCache.insert( a, network->Object::hash() );
	if( !a->second )
	{
		std::vector<riley::ShadingNode> nodes = ShaderNetworkAlgo::convert( network );
		riley::DisplacementId id = m_session->riley->CreateDisplacement( riley::UserId(), { (uint32_t)nodes.size(), nodes.data() }, RtParamList() );
		a->second = new Displacement( id, m_session );
	}
	return a->second;
}

// Must not be called concurrently with anything.
void MaterialCache::clearUnused()
{
	vector<IECore::MurmurHash> toErase;
	for( const auto &m : m_cache )
	{
		if( m.second->refCount() == 1 )
		{
			// Only one reference - this is ours, so
			// nothing outside of the cache is using the
			// shader.
			toErase.push_back( m.first );
		}
	}
	for( const auto &e : toErase )
	{
		m_cache.erase( e );
	}

	toErase.clear();
	for( const auto &m : m_displacementCache )
	{
		if( m.second->refCount() == 1 )
		{
			toErase.push_back( m.first );
		}
	}
	for( const auto &e : toErase )
	{
		m_displacementCache.erase( e );
	}
}
