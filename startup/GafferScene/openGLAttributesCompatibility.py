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
	"gl:primitive:solid" : "primitiveSolid",
	"gl:primitive:wireframe" : "primitiveWireframe",
	"gl:primitive:wireframeColor" : "primitiveWireframeColor",
	"gl:primitive:wireframeWidth" : "primitiveWireframeWidth",
	"gl:primitive:outline" : "primitiveOutline",
	"gl:primitive:outlineColor" : "primitiveOutlineColor",
	"gl:primitive:outlineWidth" : "primitiveOutlineWidth",
	"gl:primitive:points" : "primitivePoint",
	"gl:primitive:pointColor" : "primitivePointColor",
	"gl:primitive:pointWidth" : "primitivePointWidth",
	"gl:primitive:bound" : "primitiveBound",
	"gl:primitive:boundColor" : "primitiveBoundColor",
	"gl:pointsPrimitive:useGLPoints" : "pointsPrimitiveUseGLPoints",
	"gl:pointsPrimitive:glPointWidth" : "pointsPrimitiveGLPointWidth",
	"gl:curvesPrimitive:useGLLines" : "curvesPrimitiveUseGLLines",
	"gl:curvesPrimitive:glLineWidth" : "curvesPrimitiveGLLineWidth",
	"gl:curvesPrimitive:ignoreBasis" : "curvesPrimitiveIgnoreBasis",
	"gl:visualiser:scale" : "visualiserScale",
	"gl:visualiser:maxTextureResolution" : "visualiserMaxTextureResolution",
	"gl:visualiser:frustum" : "visualiserFrustum",
	"gl:light:drawingMode" : "lightDrawingMode",
	"gl:light:frustumScale" : "lightFrustumScale",
}

# Provide compatibility for OpenGLAttributes plugs renamed in Gaffer 1.6
for k, v in __aliases.items() :
	Gaffer.Metadata.registerValue( GafferScene.OpenGLAttributes, "attributes", f"compatibility:childAlias:{k}", v )
