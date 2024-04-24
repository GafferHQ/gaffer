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

import Gaffer
import GafferCycles

class __ParametersPlugProxy( object ) :

	__renames = {
		"principled_bsdf" : {
			"emission" : "emission_color",
			"specular" : "specular_ior_level",
			"subsurface" : "subsurface_weight",
			"transmission" : "transmission_weight",
			"clearcoat" : "coat_weight",
			"sheen" : "sheen_weight",
		}
	}

	def __init__( self, parametersPlug ) :

		self.__parametersPlug = parametersPlug

	def __getitem__( self, key ) :

		renames = self.__renames.get(
			self.__parametersPlug.parent()["name"].getValue()
		)
		key = renames.get( key, key ) if renames is not None else key
		return self.__parametersPlug[key]

def __cyclesShaderGetItem( originalGetItem ) :

	def getItem( self, key ) :

		result = originalGetItem( self, key )
		if key == "parameters" :
			scriptNode = self.ancestor( Gaffer.ScriptNode )
			if scriptNode is not None and scriptNode.isExecuting() :
				return __ParametersPlugProxy( result )

		return result

	return getItem

GafferCycles.CyclesShader.__getitem__ = __cyclesShaderGetItem( GafferCycles.CyclesShader.__getitem__ )

# The parameter defaults advertised by Cycles do not always match the actual defaults used by Blender.
# Register user defaults with Blender's values where it makes sense.
Gaffer.Metadata.registerValue( "cycles:surface:principled_bsdf:specular_ior_level", "userDefault", 0.5 )
