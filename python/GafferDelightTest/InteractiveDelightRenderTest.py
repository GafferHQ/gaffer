##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest
import GafferOSL
import GafferDelight

@unittest.skipIf( GafferTest.inCI(), "No license available in cloud" )
class InteractiveDelightRenderTest( GafferSceneTest.InteractiveRenderTest ) :

	renderer = "3Delight"

	# Disable this test for now as we don't have light linking support in
	# 3Delight, yet.
	@unittest.skip( "No light linking support just yet" )
	def testLightLinking( self ) :

		pass

	# Disable this test for now as we don't have light linking support in
	# 3Delight, yet.
	@unittest.skip( "No light linking support just yet" )
	def testHideLinkedLight( self ) :

		pass

	# Disable this test for now as we don't have light filter support in
	# 3Delight, yet.
	@unittest.skip( "No light filter support just yet" )
	def testLightFilters( self ) :

		pass

	# Disable this test for now as we don't have light filter support in
	# 3Delight, yet.
	@unittest.skip( "No light filter support just yet" )
	def testLightFiltersAndSetEdits( self ) :

		pass

	@unittest.skip( "Need to be able to close old driver _after_ opening new one" )
	def testEditCropWindow( self ) :

		pass

	def _createConstantShader( self ) :

		shader = GafferOSL.OSLShader()
		shader.loadShader( "Surface/Constant" )
		return shader, shader["parameters"]["Cs"], shader["out"]["out"]

	def _createTraceSetShader( self ) :

		return None, None, None

	def _cameraVisibilityAttribute( self ) :

		return "dl:visibility.camera"

	def _createMatteShader( self ) :

		shader = GafferOSL.OSLShader()
		shader.loadShader( "lambert" )
		return shader, shader["parameters"]["i_color"], shader["out"]["outColor"]

	def _createPointLight( self ) :

		light = GafferOSL.OSLLight()
		light["shape"].setValue( light.Shape.Sphere )
		light["radius"].setValue( 0.01 )
		light.loadShader( "pointLight" )
		light["attributes"].addChild( Gaffer.NameValuePlug( "dl:visibility.camera", False ) )

		return light, light["parameters"]["i_color"]

if __name__ == "__main__":
	unittest.main()
