##########################################################################
#
#  Copyright (c) 2014, John Haddon. All rights reserved.
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

import IECore

import GafferScene
import GafferSceneTest

class DuplicateTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		s = GafferScene.Sphere()
		d = GafferScene.Duplicate()
		d["in"].setInput( s["out"] )
		d["target"].setValue( "/sphere" )
		d["transform"]["translate"].setValue( IECore.V3f( 1, 0, 0 ) )

		self.assertSceneValid( d["out"] )

		self.assertEqual( d["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "sphere", "sphere1" ] ) )
		self.assertPathHashesEqual( s["out"], "/sphere", d["out"], "/sphere" )
		self.assertPathHashesEqual( d["out"], "/sphere", d["out"], "/sphere1", childPlugNamesToIgnore = ( "transform", ) )
		self.assertEqual( d["out"].transform( "/sphere1" ), IECore.M44f.createTranslated( IECore.V3f( 1, 0, 0 ) ) )

	def testMultipleCopies( self ) :

		s = GafferScene.Sphere()
		d = GafferScene.Duplicate()
		d["in"].setInput( s["out"] )
		d["target"].setValue( "/sphere" )
		d["transform"]["translate"].setValue( IECore.V3f( 1, 0, 0 ) )
		d["copies"].setValue( 10 )

		#self.assertSceneValid( d["out"] )

		self.assertEqual(
			d["out"].childNames( "/" ),
			IECore.InternedStringVectorData(
				[ "sphere" ] + [ "sphere%d" % x for x in range( 1, 11 ) ]
			)
		)

		for i in range( 1, 11 ) :
			path = "sphere%d" % i
			self.assertPathHashesEqual( d["out"], "/sphere", d["out"], path, childPlugNamesToIgnore = ( "transform", ) )
			self.assertEqual( d["out"].transform( path ), IECore.M44f.createTranslated( IECore.V3f( 1, 0, 0 ) * i ) )

	def testHierarchy( self ) :

		s = GafferScene.Sphere()
		g = GafferScene.Group()
		g["in"].setInput( s["out"] )

		d = GafferScene.Duplicate()
		d["in"].setInput( g["out"] )
		d["target"].setValue( "/group" )

		self.assertSceneValid( d["out"] )
		self.assertPathsEqual( d["out"], "/group", d["out"], "/group1" )
		self.assertPathHashesEqual( d["out"], "/group", d["out"], "/group1", childPlugNamesToIgnore = ( "transform", ) )
		self.assertPathsEqual( d["out"], "/group/sphere", d["out"], "/group1/sphere" )
		self.assertPathHashesEqual( d["out"], "/group/sphere", d["out"], "/group1/sphere" )

	def testInvalidTarget( self ) :

		s = GafferScene.Sphere()
		d = GafferScene.Duplicate()
		d["in"].setInput( s["out"] )
		d["target"].setValue( "/cube" )

		self.assertRaises( RuntimeError, d["out"].childNames, "/" )

if __name__ == "__main__":
	unittest.main()
