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

#include "Export.h"

#include "IECoreScene/ShaderNetwork.h"

#include "Riley.h"

namespace IECoreRenderMan::ShaderNetworkAlgo
{

std::vector<riley::ShadingNode> convert( const IECoreScene::ShaderNetwork *network );

/// Merges multiple light filters into a single PxrCombinerLightFilter according
/// to the rules documented for the `combineMode` parameter. The Riley API only
/// allows a single filter per light, so it becomes the responsibility of every
/// host to do this combining.
IECoreScene::ConstShaderNetworkPtr combineLightFilters( const std::vector<const IECoreScene::ShaderNetwork *> networks );

/// Converts any UsdPreviewSurface shaders into native RenderMan shaders. This conversion
/// is performed automatically by `preprocessedNetwork()` and is mainly just exposed for the unit
/// tests.
IECORERENDERMAN_API void convertUSDShaders( IECoreScene::ShaderNetwork *shaderNetwork );

} // namespace IECoreRenderMan::ShaderNetworkAlgo
