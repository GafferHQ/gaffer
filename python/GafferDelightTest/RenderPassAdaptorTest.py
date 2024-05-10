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

import IECore

import GafferTest
import GafferSceneTest
import GafferOSL
import GafferUSD

class RenderPassAdaptorTest( GafferSceneTest.RenderPassAdaptorTest ) :

	renderer = "3Delight"

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.ignoreMessage( IECore.Msg.Level.Warning, "DelightRenderer", "Attribute \"linkedLights\" not supported" )

	@unittest.skip( "Light linking not supported" )
	def testReflectionCasterLightLinks( self ) :

		pass

	def _createDistantLight( self ) :

		light = GafferUSD.USDLight()
		light.loadShader( "DistantLight" )
		return light, light["parameters"]["color"]

	def _createStandardShader( self ) :

		shader = GafferOSL.OSLShader()
		shader.loadShader( "dlPrincipled" )
		return shader, shader["parameters"]["i_color"]

	def _createFlatShader( self ) :

		shader = GafferOSL.OSLShader()
		shader.loadShader( "Surface/Constant" )
		return shader, shader["parameters"]["Cs"]

if __name__ == "__main__":
	unittest.main()
