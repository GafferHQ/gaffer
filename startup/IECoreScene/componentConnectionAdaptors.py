##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import IECore
import IECoreScene

# This file registers adaptors for connections between scalars and the child
# components of vector and color parameters in shaders. These adaptors are
# necessary for exporting to USD, where component-level connections are not
# supported. They may also be necessary for rendering in certain renderers
# where component-level connections are not supported.

# Cycles
# ======

for c in "rgb" :
	IECoreScene.ShaderNetworkAlgo.registerSplitAdapter(
		"cycles", c, IECoreScene.Shader( "separate_rgb", "cycles:shader" ), "color", c
	)

for c in "xyz" :
	IECoreScene.ShaderNetworkAlgo.registerSplitAdapter(
		"cycles", c, IECoreScene.Shader( "separate_xyz", "cycles:shader" ), "vector", c
	)

IECoreScene.ShaderNetworkAlgo.registerJoinAdapter(
	"cycles", IECore.Color3fData, IECoreScene.Shader( "combine_rgb", "cycles:shader" ), ( "r", "g", "b" ), "image"
)

IECoreScene.ShaderNetworkAlgo.registerJoinAdapter(
	"cycles", IECore.V3fData, IECoreScene.Shader( "combine_xyz", "cycles:shader" ), ( "x", "y", "z" ), "vector"
)

# Arnold
# ======

for c, mode in zip( "rgbaxyz", "rgbargb" ) :

	IECoreScene.ShaderNetworkAlgo.registerSplitAdapter(
			"ai", c, IECoreScene.Shader( "rgba_to_float", "ai:shader", { "mode" : mode } ), "input", "out"
		)

IECoreScene.ShaderNetworkAlgo.registerJoinAdapter(
	"ai", IECore.V3fData.staticTypeId(), IECoreScene.Shader( "float_to_rgb", "ai:shader" ), ( "r", "g", "b" ), "out"
)

IECoreScene.ShaderNetworkAlgo.registerJoinAdapter(
	"ai", IECore.Color3fData.staticTypeId(), IECoreScene.Shader( "float_to_rgb", "ai:shader" ), ( "r", "g", "b" ), "out"
)

IECoreScene.ShaderNetworkAlgo.registerJoinAdapter(
	"ai", IECore.Color4fData.staticTypeId(), IECoreScene.Shader( "float_to_rgba", "ai:shader" ), ( "r", "g", "b", "a" ), "out"
)
