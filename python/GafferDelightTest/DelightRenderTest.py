##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

import GafferDelight
import GafferOSL
import GafferSceneTest

class DelightRenderTest( GafferSceneTest.RenderTest ) :

	renderer = "3Delight"
	sceneDescriptionSuffix = ".nsi"
	# Apparent bug in 3Delight's EXR driver writes M44f as Box2f.
	unsupportedOutputMetadataTypes = [ IECore.M44fData ]
	pointInstancerSupported = True

	@unittest.skip( "No light linking support just yet" )
	def testLightLinking( self ) :

		pass

	@unittest.skip( "No light linking support just yet" )
	def testLightLinkingWithExclusions( self ) :

		pass

	@unittest.skip( "No shadow linking support just yet" )
	def testShadowLinking( self ) :

		pass

	@unittest.skip( "No shadow linking support just yet" )
	def testShadowLinkingExclusions( self ) :

		pass

	@unittest.skip( "Instance IDs only work with encapsulated instancers. We don't have encapsulation support yet in our 3Delight backend" )
	def testInstanceIDOutput( self ) :

		pass

	def _createConstantShader( self ) :

		shader = GafferOSL.OSLShader()
		shader.loadShader( "Surface/Constant" )
		return shader, shader["parameters"]["Cs"], shader["out"]["out"]

	def _createOptions( self ) :

		# Improve anti-aliasing for motion-blur tests.

		options = GafferDelight.DelightOptions()

		options["options"]["dl:oversampling"]["enabled"].setValue( True )
		options["options"]["dl:oversampling"]["value"].setValue( 16 )

		return options

if __name__ == "__main__":
	unittest.main()
