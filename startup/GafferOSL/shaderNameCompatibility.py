##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

import GafferOSL

__nameMapping = {
	"Utility/VectorToColor" : "Conversion/VectorToColor",
	"Utility/BuildColor" : "Conversion/FloatToColor",
	"Utility/SplitColor" : "Conversion/ColorToFloat",
	"Utility/BuildPoint" : "Conversion/FloatToVector",
	"Utility/SplitPoint" : "Conversion/VectorToFloat",
	"Maths/FloatMix" : "Maths/MixFloat",
	"Maths/VectorMix" : "Maths/MixVector",
	"Maths/FloatAdd" : "Maths/AddFloat",
	"Maths/FloatMultiply" : "Maths/MultiplyFloat",
	"Maths/VectorAdd" : "Maths/AddVector",
	"Maths/VectorMultiply" : "Maths/ScaleVector",
	# A whole bunch of MaterialX shaders were renamed from `mx_<op>_<type>`
	# to `mx_<op>_<type>_<type>` here :
	#
	#     https://github.com/AcademySoftwareFoundation/OpenShadingLanguage/pull/909.
	#
	# It seems likely that this was a mistake, given that the equivalent
	# shaders in the MaterialX repo are just `mx_<op>_<type>`. But to
	# keep old scenes loading we have to do the conversion. If in future we
	# switch to the MaterialX implementation, we will just have to
	# reverse the renaming here.
	"MaterialX/mx_add_color" : "MaterialX/mx_add_color_color",
	"MaterialX/mx_add_color2" : "MaterialX/mx_add_color2_color2",
	"MaterialX/mx_add_color4" : "MaterialX/mx_add_color4_color4",
	"MaterialX/mx_add_float" : "MaterialX/mx_add_float_float",
	"MaterialX/mx_add_surfaceshader" : "MaterialX/mx_add_surfaceshader_surfaceshader",
	"MaterialX/mx_add_vector" : "MaterialX/mx_add_vector_vector",
	"MaterialX/mx_add_vector2" : "MaterialX/mx_add_vector2_vector2",
	"MaterialX/mx_add_vector4" : "MaterialX/mx_add_vector4_vector4",
	"MaterialX/mx_clamp_color" : "MaterialX/mx_clamp_color_color",
	"MaterialX/mx_clamp_color2" : "MaterialX/mx_clamp_color2_color2",
	"MaterialX/mx_clamp_color4" : "MaterialX/mx_clamp_color4_color4",
	"MaterialX/mx_clamp_float" : "MaterialX/mx_clamp_float_float",
	"MaterialX/mx_clamp_vector" : "MaterialX/mx_clamp_vector_vector",
	"MaterialX/mx_clamp_vector2" : "MaterialX/mx_clamp_vector2_vector2",
	"MaterialX/mx_clamp_vector4" : "MaterialX/mx_clamp_vector4_vector4",
	"MaterialX/mx_contrast_color" : "MaterialX/mx_contrast_color_color",
	"MaterialX/mx_contrast_color2" : "MaterialX/mx_contrast_color2_color2",
	"MaterialX/mx_contrast_color4" : "MaterialX/mx_contrast_color4_color4",
	"MaterialX/mx_contrast_float" : "MaterialX/mx_contrast_float_float",
	"MaterialX/mx_contrast_vector" : "MaterialX/mx_contrast_vector_vector",
	"MaterialX/mx_contrast_vector2" : "MaterialX/mx_contrast_vector2_vector2",
	"MaterialX/mx_contrast_vector4" : "MaterialX/mx_contrast_vector4_vector4",
	"MaterialX/mx_divide_color" : "MaterialX/mx_divide_color_color",
	"MaterialX/mx_divide_color2" : "MaterialX/mx_divide_color2_color2",
	"MaterialX/mx_divide_color4" : "MaterialX/mx_divide_color4_color4",
	"MaterialX/mx_divide_float" : "MaterialX/mx_divide_float_float",
	"MaterialX/mx_divide_vector" : "MaterialX/mx_divide_vector_vector",
	"MaterialX/mx_divide_vector2" : "MaterialX/mx_divide_vector2_vector2",
	"MaterialX/mx_divide_vector4" : "MaterialX/mx_divide_vector4_vector4",
	"MaterialX/mx_invert_color" : "MaterialX/mx_invert_color_color",
	"MaterialX/mx_invert_color2" : "MaterialX/mx_invert_color2_color2",
	"MaterialX/mx_invert_color4" : "MaterialX/mx_invert_color4_color4",
	"MaterialX/mx_invert_float" : "MaterialX/mx_invert_float_float",
	"MaterialX/mx_invert_vector" : "MaterialX/mx_invert_vector_vector",
	"MaterialX/mx_invert_vector2" : "MaterialX/mx_invert_vector2_vector2",
	"MaterialX/mx_invert_vector4" : "MaterialX/mx_invert_vector4_vector4",
	"MaterialX/mx_max_color" : "MaterialX/mx_max_color_color",
	"MaterialX/mx_max_color2" : "MaterialX/mx_max_color2_color2",
	"MaterialX/mx_max_color4" : "MaterialX/mx_max_color4_color4",
	"MaterialX/mx_max_float" : "MaterialX/mx_max_float_float",
	"MaterialX/mx_max_vector" : "MaterialX/mx_max_vector_vector",
	"MaterialX/mx_max_vector2" : "MaterialX/mx_max_vector2_vector2",
	"MaterialX/mx_max_vector4" : "MaterialX/mx_max_vector4_vector4",
	"MaterialX/mx_min_color" : "MaterialX/mx_min_color_color",
	"MaterialX/mx_min_color2" : "MaterialX/mx_min_color2_color2",
	"MaterialX/mx_min_color4" : "MaterialX/mx_min_color4_color4",
	"MaterialX/mx_min_float" : "MaterialX/mx_min_float_float",
	"MaterialX/mx_min_vector" : "MaterialX/mx_min_vector_vector",
	"MaterialX/mx_min_vector2" : "MaterialX/mx_min_vector2_vector2",
	"MaterialX/mx_min_vector4" : "MaterialX/mx_min_vector4_vector4",
	"MaterialX/mx_modulo_color" : "MaterialX/mx_modulo_color_color",
	"MaterialX/mx_modulo_color2" : "MaterialX/mx_modulo_color2_color2",
	"MaterialX/mx_modulo_color4" : "MaterialX/mx_modulo_color4_color4",
	"MaterialX/mx_modulo_float" : "MaterialX/mx_modulo_float_float",
	"MaterialX/mx_modulo_vector" : "MaterialX/mx_modulo_vector_vector",
	"MaterialX/mx_modulo_vector2" : "MaterialX/mx_modulo_vector2_vector2",
	"MaterialX/mx_modulo_vector4" : "MaterialX/mx_modulo_vector4_vector4",
	"MaterialX/mx_multiply_color" : "MaterialX/mx_multiply_color_color",
	"MaterialX/mx_multiply_color2" : "MaterialX/mx_multiply_color2_color2",
	"MaterialX/mx_multiply_color4" : "MaterialX/mx_multiply_color4_color4",
	"MaterialX/mx_multiply_float" : "MaterialX/mx_multiply_float_float",
	"MaterialX/mx_multiply_vector" : "MaterialX/mx_multiply_vector_vector",
	"MaterialX/mx_multiply_vector2" : "MaterialX/mx_multiply_vector2_vector2",
	"MaterialX/mx_multiply_vector4" : "MaterialX/mx_multiply_vector4_vector4",
	"MaterialX/mx_remap_color" : "MaterialX/mx_remap_color_color",
	"MaterialX/mx_remap_color2" : "MaterialX/mx_remap_color2_color2",
	"MaterialX/mx_remap_color4" : "MaterialX/mx_remap_color4_color4",
	"MaterialX/mx_remap_float" : "MaterialX/mx_remap_float_float",
	"MaterialX/mx_remap_vector" : "MaterialX/mx_remap_vector_vector",
	"MaterialX/mx_remap_vector2" : "MaterialX/mx_remap_vector2_vector2",
	"MaterialX/mx_remap_vector4" : "MaterialX/mx_remap_vector4_vector4",
	"MaterialX/mx_smoothstep_color" : "MaterialX/mx_smoothstep_color_color",
	"MaterialX/mx_smoothstep_color2" : "MaterialX/mx_smoothstep_color2_color2",
	"MaterialX/mx_smoothstep_color4" : "MaterialX/mx_smoothstep_color4_color4",
	"MaterialX/mx_smoothstep_float" : "MaterialX/mx_smoothstep_float_float",
	"MaterialX/mx_smoothstep_vector" : "MaterialX/mx_smoothstep_vector_vector",
	"MaterialX/mx_smoothstep_vector2" : "MaterialX/mx_smoothstep_vector2_vector2",
	"MaterialX/mx_smoothstep_vector4" : "MaterialX/mx_smoothstep_vector4_vector4",
	"MaterialX/mx_subtract_color" : "MaterialX/mx_subtract_color_color",
	"MaterialX/mx_subtract_color2" : "MaterialX/mx_subtract_color2_color2",
	"MaterialX/mx_subtract_color4" : "MaterialX/mx_subtract_color4_color4",
	"MaterialX/mx_subtract_float" : "MaterialX/mx_subtract_float_float",
	"MaterialX/mx_subtract_vector" : "MaterialX/mx_subtract_vector_vector",
	"MaterialX/mx_subtract_vector2" : "MaterialX/mx_subtract_vector2_vector2",
	"MaterialX/mx_subtract_vector4" : "MaterialX/mx_subtract_vector4_vector4",
}

def __loadShaderWrapper( originalLoadShader ) :

	def loadRenamedShader( self, shaderName, **kwargs ) :
		renamed = __nameMapping.get( shaderName, shaderName )
		return originalLoadShader( self, renamed, **kwargs )

	return loadRenamedShader

GafferOSL.OSLShader.loadShader = __loadShaderWrapper( GafferOSL.OSLShader.loadShader )
