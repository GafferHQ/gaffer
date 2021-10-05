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

def __loadShaderWrapper( originalLoadShader ) :

	def loadRenamedShader( self, shaderName, **kwargs ) :
		renamed = {
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
			# `mx_invert_float` was renamed to `mx_invert_float_float` in
			# https://github.com/AcademySoftwareFoundation/OpenShadingLanguage/pull/909.
			# It seems likely that this was a mistake, given that the equivalent
			# shader in the MaterialX repo is just `mx_invert_float`. But to
			# keep old scenes loading we have to do the conversion. If in future we
			# switch to the MaterialX implementation, we will just have to
			# reverse the renaming here.
			"MaterialX/mx_invert_float" : "MaterialX/mx_invert_float_float",
		}.get( shaderName, shaderName )

		return originalLoadShader( self, renamed, **kwargs )

	return loadRenamedShader

GafferOSL.OSLShader.loadShader = __loadShaderWrapper( GafferOSL.OSLShader.loadShader )
