//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Alex Fuller. All rights reserved.
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

#ifndef IECORECYCLES_SHADERNETWORKALGO_H
#define IECORECYCLES_SHADERNETWORKALGO_H

#include "GafferCycles/IECoreCyclesPreview/Export.h"

#include "IECoreScene/ShaderNetwork.h"

// Cycles
IECORE_PUSH_DEFAULT_VISIBILITY
#include "scene/shader_graph.h"
#include "scene/light.h"
#include "scene/shader.h"
#include "scene/scene.h"
IECORE_POP_DEFAULT_VISIBILITY

namespace IECoreCycles
{

namespace ShaderNetworkAlgo
{

IECORECYCLES_API ccl::ShaderInput  *input( ccl::ShaderNode *node, IECore::InternedString name );
IECORECYCLES_API ccl::ShaderOutput *output( ccl::ShaderNode *node, IECore::InternedString name );


IECORECYCLES_API ccl::ShaderGraph *convertGraph( const IECoreScene::ShaderNetwork *surfaceShader,
                                                 const IECoreScene::ShaderNetwork *displacementShader,
                                                 const IECoreScene::ShaderNetwork *volumeShader,
                                                 ccl::ShaderManager *shaderManager,
                                                 const std::string &namePrefix = "" );

IECORECYCLES_API ccl::Shader *convert( const IECoreScene::ShaderNetwork *surfaceShader,
                                       const IECoreScene::ShaderNetwork *displacementShader,
                                       const IECoreScene::ShaderNetwork *volumeShader,
                                       ccl::ShaderManager *shaderManager,
                                       const std::string &namePrefix = "" );
IECORECYCLES_API void convertAOV( const IECoreScene::ShaderNetwork *shaderNetwork, ccl::ShaderGraph *graph, ccl::ShaderManager *shaderManager, const std::string &namePrefix = "" );
IECORECYCLES_API void setSingleSided( ccl::ShaderGraph *graph );
IECORECYCLES_API ccl::Shader *createDefaultShader();
IECORECYCLES_API bool hasOSL( const ccl::Shader *cshader );

// Light conversion
// ----------------
//
// Cycles represents lights as a `ccl::Light` node containing a type and various sockets representing
// the light properties. A `shader` socket is used to connect a shader specifying emission across the
// light surface. Notably, `ccl::Light` only has a single `strength` parameter rather than the more user-friendly
// intensity/exposure/color/colorTemperature parameters you might expect.
//
// We represent lights as a `IECoreScene::ShaderNetwork`, where the output shader defines the light and
// each parameter can have input shaders. We support "virtual" parameters for `intensity`, `exposure` and `color`,
// combinining them in to the single `strength` parameter in Cycles. Where these parameters have input connections,
// we instead combine them into a Cycles shader suitable for providing emission to the `shader` socket.

// Converts all non-connected light parameters on to the provided `cyclesLight` node.
IECORECYCLES_API void convertLight( const IECoreScene::ShaderNetwork *light, ccl::Light *cyclesLight );
// Builds a ShaderNetwork suitable for connection to the `shader` socket on a `ccl::Light`.
/// \todo It's not 100% clear why we need this separate method rather than having `convertLight()` just
/// create and assign the shader itself. It _does_ allow CyclesRenderer to reuse shaders between lights via
/// the ShaderCache, and it _might_ also be necessary for the deferred assignment of shaders that
/// `ShaderCache::updateShaders()` performs.
IECORECYCLES_API IECoreScene::ShaderNetworkPtr convertLightShader( const IECoreScene::ShaderNetwork *light );

} // namespace ShaderNetworkAlgo

} // namespace IECoreCycles

#endif // IECORECYCLES_SHADERNETWORKALGO_H
