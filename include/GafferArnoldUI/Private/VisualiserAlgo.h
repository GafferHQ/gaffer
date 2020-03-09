//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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
//      * Neither the name of Cinesite VFX Ltd. nor the names of
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

#ifndef GAFFERARNOLDUI_VISUALISERALGO_H
#define GAFFERARNOLDUI_VISUALISERALGO_H

#include "GafferArnoldUI/Export.h"

#include "IECoreScene/ShaderNetwork.h"

namespace GafferArnoldUI
{

namespace Private
{

namespace VisualiserAlgo
{

// Shader network conversion
// =========================
//
// Attempts to conform the supplied shaderNetwork such that it only contains
// OSL shaders. Any Arnold shaders are re-mapped in-place to an OSL equivalent
// (where available). If any un-converted Arnold shaders remain, attempts are
// made to build a simple network using the first image shader found. If no
// image was found then the resulting mixed network is returned.
//
// Stand-in shaders are:
//
//  - Found in shaders/__viewer/ and prefixed with __arnold.
//  - Should have identical parameter names/types.
//  - Should have a single output called 'out'.
//  - Arnold bool params should be OSL ints.
//  - Any param name collisions with OSL reserved words should be suffixed
//    with an '_'.
//
GAFFERARNOLDUI_API IECoreScene::ShaderNetworkPtr conformToOSLNetwork(
	const IECoreScene::ShaderNetwork::Parameter &output,
	const IECoreScene::ShaderNetwork *shaderNetwork
);

} // namespace VisualiserAlgo

} // namespace Private

} // namespace GafferArnoldUI

#endif // GAFFERARNOLDUI_VISUALISERALGO_H
