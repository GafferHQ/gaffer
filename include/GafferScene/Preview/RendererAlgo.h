//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERSCENE_PREVIEW_RENDERERALGO_H
#define GAFFERSCENE_PREVIEW_RENDERERALGO_H

#include "boost/container/flat_map.hpp"

#include "IECore/VectorTypedData.h"

#include "GafferScene/Export.h"
#include "GafferScene/PathMatcher.h"
#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

namespace GafferScene
{

IE_CORE_FORWARDDECLARE( ScenePlug )

namespace Preview
{

namespace RendererAlgo
{

void outputOptions( const IECore::CompoundObject *globals, IECoreScenePreview::Renderer *renderer );
void outputOptions( const IECore::CompoundObject *globals, const IECore::CompoundObject *previousGlobals, IECoreScenePreview::Renderer *renderer );

void outputOutputs( const IECore::CompoundObject *globals, IECoreScenePreview::Renderer *renderer );
void outputOutputs( const IECore::CompoundObject *globals, const IECore::CompoundObject *previousGlobals, IECoreScenePreview::Renderer *renderer );

/// Utility class to handle all the set computations needed for a render.
class GAFFERSCENE_API RenderSets : boost::noncopyable
{

	public :

		RenderSets();
		RenderSets( const ScenePlug *scene );

		enum Changed
		{
			NothingChanged = 0,
			CamerasSetChanged = 1,
			LightsSetChanged = 2,
			RenderSetsChanged = 4
		};

		/// Returns a bitmask describing which sets
		/// changed.
		unsigned update( const ScenePlug *scene );
		void clear();

		const PathMatcher &camerasSet() const;
		const PathMatcher &lightsSet() const;

		IECore::ConstInternedStringVectorDataPtr setsAttribute( const std::vector<IECore::InternedString> &path ) const;

	private :

		struct Set
		{
			IECore::InternedString unprefixedName; // With "render:" stripped off
			IECore::MurmurHash hash;
			PathMatcher set;
		};

		typedef boost::container::flat_map<IECore::InternedString, Set> Sets;

		struct Updater;

		// Stores all the "render:" sets.
		Sets m_sets;
		Set m_camerasSet;
		Set m_lightsSet;

};

void outputCameras( const ScenePlug *scene, const IECore::CompoundObject *globals, const RenderSets &renderSets, IECoreScenePreview::Renderer *renderer );
void outputLights( const ScenePlug *scene, const IECore::CompoundObject *globals, const RenderSets &renderSets, IECoreScenePreview::Renderer *renderer );
void outputObjects( const ScenePlug *scene, const IECore::CompoundObject *globals, const RenderSets &renderSets, IECoreScenePreview::Renderer *renderer );

/// Applies the resolution, aspect ratio etc from the globals to the camera.
void applyCameraGlobals( IECore::Camera *camera, const IECore::CompoundObject *globals );

} // namespace RendererAlgo

/// \todo Remove this temporary backwards compatibility.
using namespace RendererAlgo;

} // namespace Preview

} // namespace GafferScene

#endif // GAFFERSCENE_PREVIEW_RENDERERALGO_H
