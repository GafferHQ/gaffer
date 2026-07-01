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

#include "GafferScene/ScenePlug.h"
#include "GafferScene/Private/RendererAlgo.h"

#include "IECoreScene/PointInstancer.h"

/// Utilities to aid in rendering PointInstancers.
namespace GafferScene::Private::PointInstancerAlgo
{

/// Returns a combined `SceneAlgo::hierarchyHash()` of all prototypes referenced by any PointInstancer
/// at the current location. If there is no PointInstancer, returns an empty hash.
GAFFERSCENE_API IECore::MurmurHash prototypesHash( const ScenePlug *scene );

/// Generates the list of `Renderer::Prototypes` ready for passing to `Renderer::pointInstancer()`.
GAFFERSCENE_API std::vector<IECoreScenePreview::Renderer::Prototype> prototypes( const IECoreScene::PointInstancer *instancer, const RendererAlgo::RenderOptions &renderOptions, const ScenePlug *scene, IECoreScenePreview::Renderer *renderer );

/// Flattens a PointInstancer so that it refers only to leaf-level locations. Adds additional points
/// as necessary whenever an input prototype contains multiple leaf locations. Also transfers transforms
/// from the prototypes onto the points, so we don't need to pass prototype transforms to the Renderer.
/// Omits invisible points, since there is no point passing them to the renderer.
GAFFERSCENE_API IECoreScene::PointInstancerPtr flatten( const IECoreScene::PointInstancer *instancer, const RendererAlgo::RenderOptions &renderOptions, const ScenePlug *scene );

} // namespace GafferScene::Private::PointInstancerAlgo
