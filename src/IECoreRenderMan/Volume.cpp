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

#include "Volume.h"

#include "Loader.h"
#include "GeometryAlgo.h"
#include "Transform.h"

using namespace std;
using namespace IECoreRenderMan;

namespace
{

std::mutex g_geometryPrototypeMutex;

} // namespace

Volume::Volume( const std::string &name, const ConstGeometryPrototypePtr &geometryPrototype, const Attributes *attributes, LightLinker *lightLinker, const Session *session, const IECoreVDB::VDBObject *vdbObject )
	:	Object( name, geometryPrototype, attributes, lightLinker, session )
{
	// Store the same information that GeometryPrototypeCache will have used
	// to make the prototype, for use later in `fixupTransformEdit()`.
	GeometryAlgo::convert( { vdbObject }, { 0.0f }, m_primVars );
	m_primVars.RtParamList::Inherit( attributes->prototypeAttributes() );
}

void Volume::transform( const IECoreScenePreview::Renderer::TransformSamples &samples, const IECoreScenePreview::Renderer::SampleTimes &times )
{
	AnimatedTransform animatedTransform( samples, times );
	const riley::GeometryInstanceResult result = m_session->riley->ModifyGeometryInstance(
		/* group = */ riley::GeometryPrototypeId::InvalidId(),
		m_geometryInstance,
		/* material = */ nullptr,
		/* coordsys = */ nullptr,
		&animatedTransform,
		/* attributes = */ nullptr
	);

	fixupTransformEdit( result );
}

void Volume::fixupTransformEdit( riley::GeometryInstanceResult editResult )
{
	switch( editResult )
	{
		case riley::GeometryInstanceResult::k_Success :
			// This is what we'd get from any other renderer we know of.
			break;
		case riley::GeometryInstanceResult::k_ResendPrimVars : {
			// But RenderMan requires a call to `ModifyGeometryPrototype()`
			// as a crutch to trigger a rebuild of the volume aggregate.
			// Since multiple instances might be wanting to do this, we need to mutex
			// the edits.
			std::lock_guard lock( g_geometryPrototypeMutex );
			auto d = m_attributes->displacement();
			m_session->riley->ModifyGeometryPrototype( Loader::strings().k_Ri_Volume, m_geometryPrototype->id(), d ? &d->id() : nullptr, &m_primVars );
			break;
		}
		case riley::GeometryInstanceResult::k_Error :
			IECore::msg( IECore::Msg::Warning, "RenderManObject::transform", "Unexpected edit failure" );
			break;
	}
}
