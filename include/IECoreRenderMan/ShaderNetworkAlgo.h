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

#include <functional>

namespace IECoreRenderMan::ShaderNetworkAlgo
{

std::vector<riley::ShadingNode> convert( const IECoreScene::ShaderNetwork *network );

/// Merges multiple light filters into a single PxrCombinerLightFilter according
/// to the rules documented for the `combineMode` parameter. The Riley API only
/// allows a single filter per light, so it becomes the responsibility of every
/// host to do this combining.
IECoreScene::ConstShaderNetworkPtr combineLightFilters( const std::vector<const IECoreScene::ShaderNetwork *> networks );

/// Converts any UsdPreviewSurface and UsdLux shaders into native RenderMan shaders. This conversion
/// is performed automatically by `convert()` and is mainly just exposed for the unit tests.
IECORERENDERMAN_API void convertUSDShaders( IECoreScene::ShaderNetwork *shaderNetwork );

/// Returns the matrix needed to transform a Pxr*Light to match a UsdLux shader.
IECORERENDERMAN_API Imath::M44f usdLightTransform( const IECoreScene::Shader *lightShader );

struct VStructAction
{
	enum class Type { None, Connect, Set };
	Type type = Type::None;
	double value = 0;
};

/// A function which returns the value of a shader parameter.
using ParameterValueFunction = std::function<IECore::ConstDataPtr ( IECore::InternedString )>;
/// A function which returns true if a shader parameter has an input connection.
using ParameterIsConnectedFunction = std::function<bool ( IECore::InternedString )>;

/// Evaluates a vstruct expression, returning the action that should be taken.
/// `valueFunction` and `isConnectedFunction` abstract away access to the
/// ShaderNetwork that would typically back these queries - primarily to
/// simplify testing.
IECORERENDERMAN_API VStructAction evaluateVStructConditional( const std::string &expression, const ParameterValueFunction &valueFunction, const ParameterIsConnectedFunction &isConnectedFunction );

/// Resolves connections and values for vstruct members. Exposed primarily for testing,
/// as `convert()` resolves vstructs internally anyway.
IECORERENDERMAN_API void resolveVStructs( IECoreScene::ShaderNetwork *shaderNetwork );

} // namespace IECoreRenderMan::ShaderNetworkAlgo
