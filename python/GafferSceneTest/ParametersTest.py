##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

class ParametersTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		camera = GafferScene.Camera()
		procedural = GafferScene.ExternalProcedural()
		group = GafferScene.Group()

		group["in"][0].setInput( camera["out"] )
		group["in"][1].setInput( procedural["out"] )

		parameters = GafferScene.Parameters()
		parameters["in"].setInput( group["out"] )

		self.assertSceneValid( parameters["out"] )
		self.assertScenesEqual( parameters["out"], group["out"] )
		self.assertSceneHashesEqual( parameters["out"], group["out"] )

		parameters["parameters"].addChild( Gaffer.NameValuePlug( "test", 10 ) )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/*" ] ) )
		parameters["filter"].setInput( filter["out"] )

		self.assertSceneValid( parameters["out"] )
		self.assertScenesEqual( parameters["out"], group["out"], checks = self.allSceneChecks - { "object" } )
		self.assertSceneHashesEqual( parameters["out"], group["out"], checks = self.allSceneChecks - { "object" } )

		cameraIn = group["out"].object( "/group/camera" )
		cameraOut = parameters["out"].object( "/group/camera" )
		self.assertNotEqual( cameraIn, cameraOut )
		self.assertEqual( cameraOut.parameters()["test"], IECore.IntData( 10 ) )
		del cameraOut.parameters()["test"]
		self.assertEqual( cameraIn, cameraOut )
		self.assertTrue( isinstance( cameraOut, IECoreScene.Camera ) )

		proceduralIn = group["out"].object( "/group/procedural" )
		proceduralOut = parameters["out"].object( "/group/procedural" )
		self.assertNotEqual( proceduralIn, proceduralOut )
		self.assertEqual( proceduralOut.parameters()["test"], IECore.IntData( 10 ) )
		del proceduralOut.parameters()["test"]
		self.assertEqual( proceduralIn, proceduralOut )
		self.assertTrue( isinstance( proceduralOut, IECoreScene.ExternalProcedural ) )

	def testAffects( self ) :

		parameters = GafferScene.Parameters()
		p = Gaffer.NameValuePlug( "test", 10, True )
		parameters["parameters"].addChild( p )

		self.assertEqual( parameters.affects( p["name"] ), [ parameters["__processedObject"] ] )
		self.assertEqual( parameters.affects( p["enabled"] ), [ parameters["__processedObject"] ] )
		self.assertEqual( parameters.affects( p["value"] ), [ parameters["__processedObject"] ] )

if __name__ == "__main__":
	unittest.main()
