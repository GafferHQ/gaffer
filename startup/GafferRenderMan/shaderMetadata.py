##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

# Defines metadata overrides for pass-through behaviours during network
# generation. See `startup/GafferRenderManUI/shaderMetadata.py` for
# metadata that only affects the operation of the UI.

for target, correspondingInput in [

	( "osl:displacement:PxrDisplace:result", "dispVector" ),
	( "osl:shader:PxrAdjustNormal:resultN", "inputNormal" ),
	( "osl:shader:PxrArithmetic:resultRGB", "input1" ),
	( "osl:shader:PxrAttribute:resultRGB", "defaultColor" ),
	( "osl:shader:PxrAttribute:resultF", "defaultFloat" ),
	( "osl:shader:PxrAttribute:resultI", "defaultInt" ),
	( "osl:shader:PxrBlend:resultRGB", "topRGB" ),
	( "osl:shader:PxrBump:resultN", "inputN" ),
	( "osl:shader:PxrBumpMixer:resultN", "surfaceGradient1" ),
	( "osl:shader:PxrChecker:resultRGB", "colorA" ),
	( "osl:shader:PxrClamp:resultRGB", "inputRGB" ),
	( "osl:shader:PxrColorCorrect:resultRGB", "inputRGB" ),
	( "osl:shader:PxrColorGrade:resultRGB", "inputColor" ),
	( "osl:shader:PxrColorSpace:resultRGB", "inputColor" ),
	( "osl:shader:PxrCross:resultXYZ", "vector1" ),
	( "osl:shader:PxrDirt:resultRGB", "occluded" ),
	( "osl:shader:PxrDispScalarLayer:resultF", "baseLayerDispScalar" ),
	( "osl:shader:PxrDispTransform:resultXYZ", "dispVector" ),
	( "osl:shader:PxrDispVectorLayer:resultXYZ", "baseLayerDispVector" ),
	( "osl:shader:PxrExposure:resultRGB", "inputRGB" ),
	( "osl:shader:PxrFlakes:resultN", "inputNormal" ),
	( "osl:shader:PxrGamma:resultRGB", "inputRGB" ),
	( "osl:shader:PxrGrid:resultRGB", "colorTile" ),
	( "osl:shader:PxrHairColor:resultDiff", "Color" ),
	( "osl:shader:PxrHSL:resultRGB", "inputRGB" ),
	( "osl:shader:PxrInvert:resultRGB", "inputRGB" ),
	( "osl:shader:PxrLayeredBlend:resultRGB", "backgroundRGB" ),
	( "osl:shader:PxrLayerMixer:pxrMaterialOut", "baselayer" ),
	( "osl:shader:PxrMatteID:resultAOV", "inputAOV" ),
	( "osl:shader:PxrMetallicWorkflow:resultDiffuseRGB", "baseColor" ),
	( "osl:shader:PxrMix:resultRGB", "color1" ),
	( "osl:shader:PxrNgToNormal:resultN", "surfaceGradient" ),
	( "osl:shader:PxrNormalMap:resultN", "inputRGB"),
	( "osl:shader:PxrPrimvar:resultRGB", "defaultColor" ),
	( "osl:shader:PxrPrimvar:resultF", "defaultFloat" ),
	( "osl:shader:PxrPrimvar:resultP", "defaultFloat3" ),
	( "osl:shader:PxrRemap:resultRGB", "inputRGB" ),
	( "osl:shader:PxrRGBToNg:resultNG", "inputColor" ),
	( "osl:shader:PxrSetRange:resultRGB", "input" ),
	( "osl:shader:PxrSplineMap:resultF", "input" ),
	( "osl:shader:PxrTangentField:resultXYZ", "inputVector" ),
	( "osl:shader:PxrTee:resultRGB", "inputRGB" ),
	( "osl:shader:PxrThinFilm:resultRGB", "inputRGB" ),
	( "osl:shader:PxrThreshold:resultRGB", "inputRGB" ),
	( "osl:shader:PxrToFloat3:resultRGB", "input" ),
	( "osl:shader:PxrVary:resultRGB", "inputRGB" ),
	( "osl:shader:PxrWireframe:Cout", "wireColor" ),
	( "ri:shader:PxrBakePointCloud:resultRGB", "inputRGB" ),
	( "ri:shader:PxrBakeTexture:resultRGB", "inputRGB" ),
	( "ri:surface:LamaAdd:bxdf_out", "material1" ),
	( "ri:surface:LamaLayer:bxdf_out", "materialBase" ),
	( "ri:surface:LamaMix:bxdf_out", "material1" ),

] :
	Gaffer.Metadata.registerValue( target, "correspondingInput", correspondingInput )
