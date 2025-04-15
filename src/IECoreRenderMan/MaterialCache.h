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

#pragma once

#include "IECoreScene/ShaderNetwork.h"

#include "IECore/RefCounted.h"

#include "RefCountedId.h"
#include "Session.h"

#include "tbb/concurrent_hash_map.h"

namespace IECoreRenderMan
{

using Material = RefCountedId<riley::MaterialId>;
IE_CORE_DECLAREPTR( Material );
using Displacement = RefCountedId<riley::DisplacementId>;
IE_CORE_DECLAREPTR( Displacement );
using LightShader = RefCountedId<riley::LightShaderId>;
IE_CORE_DECLAREPTR( LightShader );

class MaterialCache
{

	public :

		MaterialCache( Session *session );

		// Can be called concurrently with other calls to `get()`
		ConstMaterialPtr getMaterial( const IECoreScene::ShaderNetwork *network );
		ConstDisplacementPtr getDisplacement( const IECoreScene::ShaderNetwork *network );
		ConstLightShaderPtr getLightShader( const IECoreScene::ShaderNetwork *network, const IECoreScene::ShaderNetwork *lightFilter );

		// Must not be called concurrently with anything.
		void clearUnused();

	private :

		Session *m_session;

		using Cache = tbb::concurrent_hash_map<IECore::MurmurHash, ConstMaterialPtr>;
		Cache m_cache;

		using DisplacementCache = tbb::concurrent_hash_map<IECore::MurmurHash, ConstDisplacementPtr>;
		DisplacementCache m_displacementCache;

		using LightShaderCache = tbb::concurrent_hash_map<IECore::MurmurHash, ConstLightShaderPtr>;
		LightShaderCache m_lightShaderCache;

};

} // namespace IECoreRenderMan
