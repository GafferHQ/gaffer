##########################################################################
#
#  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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

class FilterQueryTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		# /group
		#     /grid
		#          /gridLines
		#          /centerLines
		#          /borderLines
		#     /plane
		#     /sphere

		grid = GafferScene.Grid()
		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		group = GafferScene.Group()
		group["in"][0].setInput( grid["out"] )
		group["in"][1].setInput( plane["out"] )
		group["in"][2].setInput( sphere["out"] )

		pathFilter = GafferScene.PathFilter()

		query = GafferScene.FilterQuery()
		query["scene"].setInput( group["out"] )
		query["filter"].setInput( pathFilter["out"] )

		allPaths = IECore.PathMatcher()
		GafferScene.SceneAlgo.matchingPaths(
			IECore.PathMatcher( [ "/..." ] ),
			group["out"],
			allPaths
		)
		self.assertEqual( allPaths.size(), 8 )

		for pattern in [
			"/",
			"/group",
			"/group/grid",
			"/group/grid/gridLines",
			"/group/*",
			"/group/grid/*",
			"/group/...",
			"/noMatch"
		] :

			pathFilter["paths"].setValue( IECore.StringVectorData( [ pattern ] ) )
			for pathString in allPaths.paths() :

				path = GafferScene.ScenePlug.stringToPath( pathString )
				with Gaffer.Context() as c :
					c["scene:path"] = path
					match = pathFilter["out"].match( group["out"] )

				query["location"].setValue( pathString )
				self.assertEqual( query["exactMatch"].getValue(), bool( match & IECore.PathMatcher.Result.ExactMatch ) )
				self.assertEqual( query["descendantMatch"].getValue(), bool( match & IECore.PathMatcher.Result.DescendantMatch ) )
				self.assertEqual( query["ancestorMatch"].getValue(), bool( match & IECore.PathMatcher.Result.AncestorMatch ) )

				ancestor = query["closestAncestor"].getValue()
				if ancestor == "" :
					self.assertFalse( match & IECore.PathMatcher.Result.ExactMatch )
					self.assertFalse( match & IECore.PathMatcher.Result.AncestorMatch )
				else :
					ancestor = GafferScene.ScenePlug.stringToPath( ancestor )
					with Gaffer.Context() as c :
						c["scene:path"] = ancestor
						self.assertTrue( pathFilter["out"].match( group["out"] ) & IECore.PathMatcher.Result.ExactMatch )
						for i in range( len( ancestor ), len( path ) ) :
							c["scene:path"] = path[:i+1]
							self.assertFalse( pathFilter["out"].match( group["out"] ) & IECore.PathMatcher.Result.ExactMatch )

	def testEmptyLocation( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "test" )

		setFilter = GafferScene.SetFilter()
		setFilter["setExpression"].setValue( "test" )

		query = GafferScene.FilterQuery()
		query["scene"].setInput( plane["out"] )
		query["filter"].setInput( setFilter["out"] )

		self.assertEqual( query["exactMatch"].getValue(), False )
		self.assertEqual( query["descendantMatch"].getValue(), False )
		self.assertEqual( query["ancestorMatch"].getValue(), False )
		self.assertEqual( query["closestAncestor"].getValue(), "" )

	def testNonExistentLocation( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "test" )

		setFilter = GafferScene.SetFilter()
		setFilter["setExpression"].setValue( "test" )

		query = GafferScene.FilterQuery()
		query["scene"].setInput( plane["out"] )
		query["filter"].setInput( setFilter["out"] )
		query["location"].setValue( "/sphere" )

		self.assertEqual( query["exactMatch"].getValue(), False )
		self.assertEqual( query["descendantMatch"].getValue(), False )
		self.assertEqual( query["ancestorMatch"].getValue(), False )
		self.assertEqual( query["closestAncestor"].getValue(), "" )

	def testNonExistentLocationWithAncestors( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "test" )

		setFilter = GafferScene.SetFilter()
		setFilter["setExpression"].setValue( "test" )

		query = GafferScene.FilterQuery()
		query["scene"].setInput( plane["out"] )
		query["filter"].setInput( setFilter["out"] )
		query["location"].setValue( "/plane/this/does/not/exist" )

		self.assertEqual( query["exactMatch"].getValue(), False )
		self.assertEqual( query["descendantMatch"].getValue(), False )
		self.assertEqual( query["ancestorMatch"].getValue(), False )
		self.assertEqual( query["closestAncestor"].getValue(), "" )

	def testChangingSet( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "setA" )

		setFilter = GafferScene.SetFilter()
		setFilter["setExpression"].setValue( "setA" )

		query = GafferScene.FilterQuery()
		query["scene"].setInput( sphere["out"] )
		query["filter"].setInput( setFilter["out"] )
		query["location"].setValue( "/sphere" )

		self.assertEqual( query["exactMatch"].getValue(), True )
		self.assertEqual( query["closestAncestor"].getValue(), "/sphere" )

		sphere["sets"].setValue( "setB" )

		self.assertEqual( query["exactMatch"].getValue(), False )
		self.assertEqual( query["closestAncestor"].getValue(), "" )

if __name__ == "__main__":
	unittest.main()
