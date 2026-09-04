##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

import itertools

import IECore

import GafferScene
import GafferSceneTest

class VisibilityQueryTest( GafferSceneTest.SceneTestCase ):

	def testEmptyLocation( self ) :

		sphere = GafferScene.Sphere()
		query = GafferScene.VisibilityQuery()
		query["scene"].setInput( sphere["out"] )
		self.assertEqual( query["location"].getValue(), "" )
		self.assertFalse( query["visible"].getValue() )

	def testNonexistentLocation( self ) :

		sphere = GafferScene.Sphere()
		query = GafferScene.VisibilityQuery()
		query["scene"].setInput( sphere["out"] )
		query["location"].setValue( "cube" )
		self.assertFalse( query["visible"].getValue() )

	def testVisible( self ) :

		sphere = GafferScene.Sphere()

		sphereAttributes = GafferScene.StandardAttributes()
		sphereAttributes["in"].setInput( sphere["out"] )

		group = GafferScene.Group()
		group["in"][0].setInput( sphereAttributes["out"] )

		groupFilter = GafferScene.PathFilter()
		groupFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		groupAttributes = GafferScene.StandardAttributes()
		groupAttributes["in"].setInput( group["out"] )
		groupAttributes["filter"].setInput( groupFilter["out"] )

		query = GafferScene.VisibilityQuery()
		query["scene"].setInput( groupAttributes["out"] )

		for groupVisibility, sphereVisibility in itertools.product( ( None, True, False ), repeat = 2 ) :

			with self.subTest( groupVisibility = groupVisibility, sphereVisibility = sphereVisibility ) :

				groupAttributes["attributes"]["scene:visible"]["enabled"].setValue( groupVisibility is not None )
				groupAttributes["attributes"]["scene:visible"]["value"].setValue( groupVisibility )

				sphereAttributes["attributes"]["scene:visible"]["enabled"].setValue( sphereVisibility is not None )
				sphereAttributes["attributes"]["scene:visible"]["value"].setValue( sphereVisibility )

				query["location"].setValue( "/group/sphere" )
				self.assertEqual(
					query["visible"].getValue(), sphereVisibility is not False and groupVisibility is not False
				)

				query["location"].setValue( "/group" )
				self.assertEqual(
					query["visible"].getValue(), groupVisibility is not False
				)

	def testInvisibleAncestors( self ) :

		sphere = GafferScene.Sphere()

		sphereAttributes = GafferScene.StandardAttributes()
		sphereAttributes["in"].setInput( sphere["out"] )

		group = GafferScene.Group()
		group["in"][0].setInput( sphereAttributes["out"] )
		group["in"][1].setInput( sphereAttributes["out"] )

		groupFilter = GafferScene.PathFilter()
		groupFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		groupAttributes = GafferScene.StandardAttributes()
		groupAttributes["in"].setInput( group["out"] )
		groupAttributes["filter"].setInput( groupFilter["out"] )

		query = GafferScene.VisibilityQuery()
		query["scene"].setInput( groupAttributes["out"] )

		for groupVisibility, sphereVisibility in itertools.product( ( None, True, False ), repeat = 2 ) :

			with self.subTest( groupVisibility = groupVisibility, sphereVisibility = sphereVisibility ) :

				groupAttributes["attributes"]["scene:visible"]["enabled"].setValue( groupVisibility is not None )
				groupAttributes["attributes"]["scene:visible"]["value"].setValue( groupVisibility )

				sphereAttributes["attributes"]["scene:visible"]["enabled"].setValue( sphereVisibility is not None )
				sphereAttributes["attributes"]["scene:visible"]["value"].setValue( sphereVisibility )

				expected = IECore.StringVectorData()
				if groupVisibility is False :
					expected.append( "/group" )

				query["location"].setValue( "/group" )
				self.assertEqual(
					query["invisibleAncestors"].getValue(), expected
				)

				for sphereName in ( "sphere", "sphere1" ) :

					sphereExpected = expected.copy()
					if sphereVisibility is False :
						sphereExpected.append( f"/group/{sphereName}" )

					query["location"].setValue( f"/group/{sphereName}" )
					self.assertEqual(
						query["invisibleAncestors"].getValue(), sphereExpected
					)
