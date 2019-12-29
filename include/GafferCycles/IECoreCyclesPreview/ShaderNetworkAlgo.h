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
#include "render/graph.h"
#include "render/light.h"
#include "render/shader.h"
#include "render/scene.h"

namespace IECoreCycles
{

namespace ShaderNetworkAlgo
{

IECORECYCLES_API ccl::ShaderInput  *input( ccl::ShaderNode *node, IECore::InternedString name );
IECORECYCLES_API ccl::ShaderOutput *output( ccl::ShaderNode *node, IECore::InternedString name );

IECORECYCLES_API ccl::Shader *convert( const IECoreScene::ShaderNetwork *shaderNetwork, const ccl::ShaderManager *shaderManager, const std::string &namePrefix = "" );
IECORECYCLES_API ccl::Light  *convert( const IECoreScene::ShaderNetwork *shaderNetwork );
IECORECYCLES_API ccl::Shader *convertAOV( const IECoreScene::ShaderNetwork *shaderNetwork, ccl::Shader *cshader, const ccl::ShaderManager *shaderManager, const std::string &namePrefix = "" );
IECORECYCLES_API ccl::Shader *setSingleSided( ccl::Shader *cshader );
IECORECYCLES_API ccl::Shader *createDefaultShader();

} // namespace ShaderNetworkAlgo

} // namespace IECoreCycles

#endif // IECORECYCLES_SHADERNETWORKALGO_H
