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

import os
import unittest

import imath

import IECoreRenderMan
import GafferTest
import GafferSceneTest
import GafferRenderMan

@unittest.skipIf( GafferTest.inCI() and os.name == "nt", "RenderMan cannot get license on Windows.")
class RenderPassAdaptorTest( GafferSceneTest.RenderPassAdaptorTest ) :

	renderer = "RenderMan"

	shadowColor = imath.Color4f( 1, 1, 1, 0 )
	litColor = imath.Color4f( 0 )

	## \todo Remove once light linking is supported.
	@unittest.skip( "Light linking not supported yet" )
	def testReflectionCasterLightLinks( self ) :

		pass

	def _createDistantLight( self ) :

		light = GafferRenderMan.RenderManLight()
		light.loadShader( "PxrDistantLight" )
		light["parameters"]["exposure"].setValue( 2.0 )
		return light, light["parameters"]["lightColor"]

	def _createStandardShader( self ) :

		shader = GafferRenderMan.RenderManShader()
		shader.loadShader( "PxrSurface" )
		return shader, shader["parameters"]["diffuseColor"]

	def _createFlatShader( self ) :

		shader = GafferRenderMan.RenderManShader()
		shader.loadShader( "PxrConstant" )
		return shader, shader["parameters"]["emitColor"]

	def _createOptions( self ) :

		options = GafferRenderMan.RenderManOptions()
		options["options"]["ri:hider:maxsamples"]["enabled"].setValue( True )
		options["options"]["ri:hider:maxsamples"]["value"].setValue( 16 )
		return options

if __name__ == "__main__":
	unittest.main()
