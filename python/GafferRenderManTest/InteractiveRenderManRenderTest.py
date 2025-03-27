##########################################################################
#
#  Copyright (c) 2018, John Haddon. All rights reserved.
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

import IECoreRenderMan
import GafferTest
import GafferSceneTest
import GafferRenderMan

@unittest.skipIf( GafferTest.inCI() and os.name == "nt", "RenderMan cannot get license on Windows.")
class InteractiveRenderManRenderTest( GafferSceneTest.InteractiveRenderTest ) :

	renderer = "RenderMan"

	@unittest.skip( "Feature not supported yet" )
	def testLightFilters( self ) :

		pass

	@unittest.skip( "Feature not supported yet" )
	def testLightFiltersAndSetEdits( self ) :

		pass

	@unittest.skip( "Feature not supported yet" )
	def testHideLinkedLight( self ) :

		pass

	@unittest.skip( "Feature not supported yet" )
	def testLightLinking( self ) :

		pass

	@unittest.skip( "Crop window doesn't change data window" )
	def testEditCropWindow( self ) :

		# RenderMan doesn't reopen the display drivers when the crop
		# window decreases in size, only when it increases. This will
		# cause the base class test to fail, even though we are passing
		# edits and RenderMan is only re-rendering the requested area.
		pass

	def _createConstantShader( self ) :

		shader = GafferRenderMan.RenderManShader()
		shader.loadShader( "PxrConstant" )
		return shader, shader["parameters"]["emitColor"], shader["out"]

	def _createTraceSetShader( self ) :

		return None, None, None

	def _cameraVisibilityAttribute( self ) :

		return "ri:visibility:camera"

	def _createMatteShader( self ) :

		shader = GafferRenderMan.RenderManShader()
		shader.loadShader( "PxrDiffuse" )
		return shader, shader["parameters"]["diffuseColor"], shader["out"]

	def _createPointLight( self ) :

		light = GafferRenderMan.RenderManLight()
		light.loadShader( "PxrSphereLight" )

		return light, light["parameters"]["lightColor"]

if __name__ == "__main__":
	unittest.main()
