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

import GafferCycles
import GafferSceneTest

class CyclesRenderTest( GafferSceneTest.RenderTest ) :

	renderer = "Cycles"

	def _createDiffuseShader( self ) :

		shader = GafferCycles.CyclesShader()
		shader.loadShader( "diffuse_bsdf" )
		return shader, shader["parameters"]["color"], shader["out"]["BSDF"]

	def _createPointLight( self ) :

		light = GafferCycles.CyclesLight()
		light.loadShader( "point_light" )
		return light, light["parameters"]["color"]

	def _createDistantLight( self ) :

		light = GafferCycles.CyclesLight()
		light.loadShader( "distant_light" )
		return light, light["parameters"]["color"]

	def _cameraVisibilityAttribute( self ) :

		return "cycles:visibility:camera"

	def _createOptions( self ) :

		# Options that speed up the render, which can otherwise take
		# longer than we might want.

		options = GafferCycles.CyclesOptions()

		options["options"]["cycles:integrator:max_bounce"]["enabled"].setValue( True )
		options["options"]["cycles:integrator:max_bounce"]["value"].setValue( 0 )

		options["options"]["cycles:session:samples"]["enabled"].setValue( True )
		options["options"]["cycles:session:samples"]["value"].setValue( 8 )

		return options

if __name__ == "__main__":
	unittest.main()
