//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERIMAGEUI_OPENCOLORIOALGO_H
#define GAFFERIMAGEUI_OPENCOLORIOALGO_H

#include "GafferImageUI/Export.h"

#include "OpenColorIO/OpenColorIO.h"

#include "IECoreGL/Shader.h"

namespace GafferImageUI
{

namespace OpenColorIOAlgo
{

// Given a OpenColorIO processor, return a shader appropriate for applying this color transform to a framebuffer.
// The shader has a frameBufferTexture uniform so it is appropriate to use with ViewportGadget::setPostProcessShader.
// There are also additional uniforms:
//   bool unpremultiply : temporarily unpremultiply while applying the color transform
//   bool clipping : mark regions outside 0 - 1
//   color multiply : apply a multiplier before the color transform
//   color power : apply a power curve before the color transform
//   bool soloChannel : Set to 0-3 to pick channels RGBA, or -2 for luminance.  Default -1 uses all channels as a color.
GAFFERIMAGEUI_API IECoreGL::Shader::SetupPtr displayTransformToFramebufferShader( const OCIO_NAMESPACE::Processor *processor );

} // namespace OpenColorIOAlgo

} // namespace GafferImageUI

#endif // GAFFERIMAGEUI_OPENCOLORIOALGO_H
