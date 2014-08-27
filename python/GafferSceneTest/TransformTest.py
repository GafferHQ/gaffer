##########################################################################
#
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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
import GafferTest
import GafferScene
import GafferSceneTest

class TransformTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		sphere = IECore.SpherePrimitive()
		input = GafferSceneTest.CompoundObjectSource()
		input["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( sphere.bound() ),
				"children" : {
					"group" : {
						"bound" : IECore.Box3fData( sphere.bound() ),
						"children" : {
							"sphere" : {
								"bound" : IECore.Box3fData( sphere.bound() ),
								"object" : sphere,
							},
						},
					},
				},
			} ),
		)

		self.assertSceneValid( input["out"] )

		transform = GafferScene.Transform()
		transform["in"].setInput( input["out"] )

		# by default transform should do nothing

		self.assertSceneValid( transform["out"] )
		self.assertScenesEqual( transform["out"], input["out"] )

		# even when setting a transform it should do nothing, as
		# it requires a filter before operating (applying the same transform
		# at every location is really not very useful).

		transform["transform"]["translate"].setValue( IECore.V3f( 1, 2, 3 ) )

		self.assertSceneValid( transform["out"] )
		self.assertScenesEqual( transform["out"], input["out"] )

		# applying a filter should cause things to happen

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )
		transform["filter"].setInput( filter["match"] )

		self.assertSceneValid( transform["out"] )

		self.assertEqual( transform["out"].transform( "/group/sphere" ), IECore.M44f.createTranslated( IECore.V3f( 1, 2, 3 ) ) )
		self.assertEqual( transform["out"].transform( "/group" ), IECore.M44f() )

		self.assertEqual( transform["out"].bound( "/group/sphere" ), IECore.Box3f( IECore.V3f( -1 ), IECore.V3f( 1 ) ) )
		self.assertEqual( transform["out"].bound( "/group" ), IECore.Box3f( IECore.V3f( 0, 1, 2 ), IECore.V3f( 2, 3, 4 ) ) )
		self.assertEqual( transform["out"].bound( "/" ), IECore.Box3f( IECore.V3f( 0, 1, 2 ), IECore.V3f( 2, 3, 4 ) ) )

	def testEnableBehaviour( self ) :

		t = GafferScene.Transform()
		self.assertTrue( t.enabledPlug().isSame( t["enabled"] ) )
		self.assertTrue( t.correspondingInput( t["out"] ).isSame( t["in"] ) )
		self.assertEqual( t.correspondingInput( t["in"] ), None )
		self.assertEqual( t.correspondingInput( t["enabled"] ), None )

	def testSpace( self ) :

		sphere = GafferScene.Sphere()
		sphere["transform"]["translate"].setValue( IECore.V3f( 1, 0, 0 ) )

		transform = GafferScene.Transform()
		transform["in"].setInput( sphere["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )
		transform["filter"].setInput( filter["match"] )

		self.assertEqual( transform["space"].getValue(), GafferScene.Transform.Space.World )

		transform["transform"]["rotate"]["y"].setValue( 90 )
		self.assertTrue(
			IECore.V3f( 0, 0, -1 ).equalWithAbsError(
				IECore.V3f( 0 ) * transform["out"].fullTransform( "/sphere" ),
				0.000001
			)
		)

		transform["space"].setValue( GafferScene.Transform.Space.Object )
		self.assertTrue(
			IECore.V3f( 1, 0, 0 ).equalWithAbsError(
				IECore.V3f( 0 ) * transform["out"].fullTransform( "/sphere" ),
				0.000001
			)
		)
if __name__ == "__main__":
	unittest.main()
