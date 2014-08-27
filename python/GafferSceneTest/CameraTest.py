##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferScene
import GafferSceneTest

class CameraTest( GafferSceneTest.SceneTestCase ) :

	def testConstruct( self ) :

		p = GafferScene.Camera()
		self.assertEqual( p.getName(), "Camera" )
		self.assertEqual( p["name"].getValue(), "camera" )

	def testCompute( self ) :

		p = GafferScene.Camera()
		p["projection"].setValue( "perspective" )
		p["fieldOfView"].setValue( 45 )

		self.assertEqual( p["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( p["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( p["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "camera" ] ) )

		self.assertEqual( p["out"].transform( "/camera" ), IECore.M44f() )
		self.assertEqual( p["out"].childNames( "/camera" ), IECore.InternedStringVectorData() )

		o = p["out"].object( "/camera" )
		self.failUnless( isinstance( o, IECore.Camera ) )
		self.assertEqual( o.parameters()["projection"].value, "perspective" )
		self.assertEqual( o.parameters()["projection:fov"].value, 45 )

		self.assertSceneValid( p["out"] )

	def testHashes( self ) :

		p = GafferScene.Camera()
		p["projection"].setValue( "perspective" )
		p["fieldOfView"].setValue( 45 )

		for path in [ "/", "/camera" ] :
			c = Gaffer.Context()
			c["scene:path"] = IECore.InternedStringVectorData( path[1:].split( "/" ) )
			with c :
				# we ignore the enabled plug because it isn't hashed (instead it's value
				# is used to decide how the hash should be computed).
				self.assertHashesValid( p, inputsToIgnore = [ p["enabled"] ] )

	def testBound( self ) :

		p = GafferScene.Camera()
		p["projection"].setValue( "perspective" )
		p["fieldOfView"].setValue( 45 )

		self.failIf( p["out"].bound( "/" ).isEmpty() )
		self.failIf( p["out"].bound( "/camera" ).isEmpty() )

	def testClippingPlanes( self ) :

		p = GafferScene.Camera()
		o = p["out"].object( "/camera" )
		self.assertEqual( o.parameters()["clippingPlanes"].value, IECore.V2f( 0.01, 100000 ) )

		p["clippingPlanes"].setValue( IECore.V2f( 1, 10 ) )
		o = p["out"].object( "/camera" )
		self.assertEqual( o.parameters()["clippingPlanes"].value, IECore.V2f( 1, 10 ) )

	def testEnableBehaviour( self ) :

		c = GafferScene.Camera()
		self.assertTrue( c.enabledPlug().isSame( c["enabled"] ) )
		self.assertEqual( c.correspondingInput( c["out"] ), None )
		self.assertEqual( c.correspondingInput( c["enabled"] ), None )
		self.assertEqual( c.correspondingInput( c["projection"] ), None )
		self.assertEqual( c.correspondingInput( c["fieldOfView"] ), None )

	def testCameraSet( self ) :

		c = GafferScene.Camera()

		cameraSet = c["out"]["globals"].getValue()["gaffer:sets"]["__cameras"]
		self.assertEqual(
			cameraSet,
			GafferScene.PathMatcherData(
				GafferScene.PathMatcher( [ "/camera" ] )
			)
		)

		c["name"].setValue( "renderCam" )

		cameraSet = c["out"]["globals"].getValue()["gaffer:sets"]["__cameras"]
		self.assertEqual(
			cameraSet,
			GafferScene.PathMatcherData(
				GafferScene.PathMatcher( [ "/renderCam" ] )
			)
		)

if __name__ == "__main__":
	unittest.main()
