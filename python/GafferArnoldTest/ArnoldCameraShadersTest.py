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

import GafferTest
import GafferScene
import GafferSceneTest
import GafferOSL
import GafferArnold

class ArnoldCameraShadersTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		sphere = GafferScene.Sphere()
		camera = GafferScene.Camera()

		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( camera["out"] )

		noise = GafferArnold.ArnoldShader()
		noise.loadShader( "noise" )

		flat = GafferArnold.ArnoldShader()
		flat.loadShader( "flat" )

		cameraShaders = GafferArnold.ArnoldCameraShaders()
		cameraShaders["filterMap"].setInput( flat["out"] )
		cameraShaders["uvRemap"].setInput( noise["out"] )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )

		cameraFilter = GafferScene.PathFilter()
		cameraFilter["paths"].setValue( IECore.StringVectorData( [ "/group/camera" ] ) )

		assignment = GafferScene.ShaderAssignment()
		assignment["in"].setInput( group["out"] )
		assignment["shader"].setInput( flat["out"] )
		assignment["filter"].setInput( sphereFilter["out"] )

		cameraShadersAssignment = GafferScene.ShaderAssignment()
		cameraShadersAssignment["in"].setInput( group["out"] )
		cameraShadersAssignment["shader"].setInput( cameraShaders["out"] )
		cameraShadersAssignment["filter"].setInput( cameraFilter["out"] )

		self.assertEqual(
			cameraShadersAssignment["out"].attributes( "/group/camera" )["ai:filtermap"],
			assignment["out"].attributes( "/group/sphere" )["ai:surface"],
		)

		self.assertEqual(
			cameraShadersAssignment["out"].attributes( "/group/camera" )["ai:uv_remap"].outputShader().name,
			"noise"
		)

		cameraShaders["enabled"].setValue( False )
		self.assertNotIn( "ai:filtermap", cameraShadersAssignment["out"].attributes( "/group/camera" ) )
		self.assertNotIn( "ai:uv_remap", cameraShadersAssignment["out"].attributes( "/group/camera" ) )

if __name__ == "__main__":
	unittest.main()
