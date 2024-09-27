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

import unittest

import imath

import GafferSceneTest
import GafferCycles

class RenderPassAdaptorTest( GafferSceneTest.RenderPassAdaptorTest ) :

	renderer = "Cycles"

	## \todo Default camera is facing down +ve Z but should be facing
	# down -ve Z.
	reverseCamera = True

	# Cycles outputs black shadows on a white background.
	shadowColor = imath.Color4f( 0 )
	litColor = imath.Color4f( 1, 1, 1, 0 )

	@unittest.skip( "Light linking not supported" )
	def testReflectionCasterLightLinks( self ) :

		pass

	def _createDistantLight( self ) :

		light = GafferCycles.CyclesLight()
		light.loadShader( "distant_light" )
		return light, light["parameters"]["color"]

	def _createStandardShader( self ) :

		shader = GafferCycles.CyclesShader()
		shader.loadShader( "principled_bsdf" )
		return shader, shader["parameters"]["base_color"]

	def _createFlatShader( self ) :

		shader = GafferCycles.CyclesShader()
		shader.loadShader( "emission" )
		shader["parameters"]["strength"].setValue( 1 )
		return shader, shader["parameters"]["color"]

	def _createOptions( self ) :

		options = GafferCycles.CyclesOptions()
		options["options"]["samples"]["enabled"].setValue( True )
		options["options"]["samples"]["value"].setValue( 20 )
		return options

if __name__ == "__main__":
	unittest.main()
