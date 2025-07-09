##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

import Gaffer
import GafferScene

__aliases = {
	"primitiveSolid" : "gl:primitive:solid",
	"primitiveWireframe" : "gl:primitive:wireframe",
	"primitiveWireframeColor" : "gl:primitive:wireframeColor",
	"primitiveWireframeWidth" : "gl:primitive:wireframeWidth",
	"primitiveOutline" : "gl:primitive:outline",
	"primitiveOutlineColor" : "gl:primitive:outlineColor",
	"primitiveOutlineWidth" : "gl:primitive:outlineWidth",
	"primitivePoint" : "gl:primitive:points",
	"primitivePointColor" : "gl:primitive:pointColor",
	"primitivePointWidth" : "gl:primitive:pointWidth",
	"primitiveBound" : "gl:primitive:bound",
	"primitiveBoundColor" : "gl:primitive:boundColor",
	"pointsPrimitiveUseGLPoints" : "gl:pointsPrimitive:useGLPoints",
	"pointsPrimitiveGLPointWidth" : "gl:pointsPrimitive:glPointWidth",
	"curvesPrimitiveUseGLLines" : "gl:curvesPrimitive:useGLLines",
	"curvesPrimitiveGLLineWidth" : "gl:curvesPrimitive:glLineWidth",
	"curvesPrimitiveIgnoreBasis" : "gl:curvesPrimitive:ignoreBasis",
	"visualiserScale" : "gl:visualiser:scale",
	"visualiserMaxTextureResolution" : "gl:visualiser:maxTextureResolution",
	"visualiserFrustum" : "gl:visualiser:frustum",
	"lightDrawingMode" : "gl:light:drawingMode",
	"lightFrustumScale" : "gl:light:frustumScale",
}

for k, v in __aliases.items() :
	Gaffer.Metadata.registerValue( GafferScene.OpenGLAttributes, "attributes", f"compatibility:childAlias:{k}", v )
