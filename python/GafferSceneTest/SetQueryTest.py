##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

import inspect
import unittest

import imath

import IECore

import Gaffer
import GafferTest

import GafferScene
import GafferSceneTest

class SetQueryTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		# /outerGroup           { A }
		#     /plane            { B }
		#     /innerGroup       { C }
		#         /sphere		{ E, D, A }

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "E D A" )

		innerGroup = GafferScene.Group()
		innerGroup["name"].setValue( "innerGroup" )
		innerGroup["in"][0].setInput( sphere["out"] )

		innerGroupFilter = GafferScene.PathFilter()
		innerGroupFilter["paths"].setValue( IECore.StringVectorData( [ "/innerGroup" ] ) )

		innerGroupSet = GafferScene.Set()
		innerGroupSet["in"].setInput( innerGroup["out"] )
		innerGroupSet["filter"].setInput( innerGroupFilter["out"] )
		innerGroupSet["mode"].setValue( innerGroupSet.Mode.Add )
		innerGroupSet["name"].setValue( "C" )

		plane = GafferScene.Plane()
		plane["sets"].setValue( "B" )

		outerGroup = GafferScene.Group()
		outerGroup["name"].setValue( "outerGroup" )
		outerGroup["in"][0].setInput( plane["out"] )
		outerGroup["in"][1].setInput( innerGroupSet["out"] )

		outerGroupFilter = GafferScene.PathFilter()
		outerGroupFilter["paths"].setValue( IECore.StringVectorData( [ "/outerGroup" ] ) )

		outerGroupSet = GafferScene.Set()
		outerGroupSet["in"].setInput( outerGroup["out"] )
		outerGroupSet["filter"].setInput( outerGroupFilter["out"] )
		outerGroupSet["mode"].setValue( outerGroupSet.Mode.Add )
		outerGroupSet["name"].setValue( "A" )

		# Query

		setQuery = GafferScene.SetQuery()
		setQuery["scene"].setInput( outerGroupSet["out"] )

		for sets, location, inherit, matches in [
			( "A B C D", "/", False, [] ),
			( "A B C D", "/outerGroup", False, [ "A" ] ),
			( "A B C D", "/outerGroup", True, [ "A" ] ),
			( "B C D", "/outerGroup", False, [] ),
			( "A B C D", "/outerGroup/plane", False, [ "B" ] ),
			( "A B C D", "/outerGroup/plane", True, [ "A", "B" ] ),
			( "A B C D", "/outerGroup/innerGroup", False, [ "C" ] ),
			( "A B C D", "/outerGroup/innerGroup", True, [ "A", "C" ] ),
			( "C D", "/outerGroup/innerGroup/sphere", False, [ "D" ] ),
			( "C D", "/outerGroup/innerGroup/sphere", True, [ "C", "D" ] ),
			( "A B", "/outerGroup/innerGroup/sphere", True, [ "A" ] ),
			( "C", "/outerGroup/innerGroup/sphere", False, [] ),
			# Order of matches should be defined by the order of the query.
			( "D E", "/outerGroup/innerGroup/sphere", False, [ "D", "E" ] ),
			( "E D", "/outerGroup/innerGroup/sphere", False, [ "E", "D" ] ),
			# The order of matches expanded from wildcards should be alphabetical,
			# because that's more reliable and useful than the poorly defined
			# ordering of `scene.setNames` itself.
			( "*", "/outerGroup/innerGroup/sphere", False, [ "A", "D", "E" ] ),
			( "[ED]", "/outerGroup/innerGroup/sphere", False, [ "D", "E" ] ),
			# But that alphabetical ordering only applies within the group of
			# sets expanded from that wildcarded name. So if two names use wildcards,
			# the order of those names still counts.
			( "D* E*", "/outerGroup/innerGroup/sphere", False, [ "D", "E" ] ),
			( "E* D*", "/outerGroup/innerGroup/sphere", False, [ "E", "D" ] ),
			# Likewise, if some names use wildcards and others don't.
			( "D* E", "/outerGroup/innerGroup/sphere", False, [ "D", "E" ] ),
			( "E D*", "/outerGroup/innerGroup/sphere", False, [ "E", "D" ] ),
			# The same set shouldn't appear in the output multiple times, even
			# if it is listed multiple times.
			( "D D D", "/outerGroup/innerGroup/sphere", False, [ "D" ] ),
			# No matter how the duplication occurred.
			( "D A D", "/outerGroup/innerGroup/sphere", False, [ "D", "A" ] ),
			( "D* *D", "/outerGroup/innerGroup/sphere", False, [ "D" ] ),
			( "[D] D", "/outerGroup/innerGroup/sphere", False, [ "D" ] ),
			# Order of inheritance of set membership is irrelevant to result.
			# Result is always ordered according to original query.
			( "A C", "/outerGroup/innerGroup", True, [ "A", "C" ] ),
			( "C A", "/outerGroup/innerGroup", True, [ "C", "A" ] ),
			( "*", "/outerGroup/innerGroup", True, [ "A", "C" ] ),
			( "B A Z", "/outerGroup/plane", True, [ "B", "A" ] ),
			( "B E A D Y", "/outerGroup/innerGroup/sphere", True, [ "E", "A", "D" ] ),
			( "A B L E", "/outerGroup/innerGroup/sphere", True, [ "A", "E" ] ),
		] :

			# Sanity check test input
			self.assertTrue( setQuery["scene"].exists( location ) )

			# Check query output
			setQuery["location"].setValue( location )
			setQuery["sets"].setValue( sets )
			setQuery["inherit"].setValue( inherit )
			self.assertEqual( setQuery["matches"].getValue(), IECore.StringVectorData( matches ) )
			self.assertEqual( setQuery["firstMatch"].getValue(), matches[0] if matches else "" )

	def testChangingSetContents( self ) :

		plane = GafferScene.Plane()

		pathFilter = GafferScene.PathFilter()

		set = GafferScene.Set()
		set["in"].setInput( plane["out"] )
		set["filter"].setInput( pathFilter["out"] )
		set["name"].setValue( "A" )

		setQuery = GafferScene.SetQuery()
		setQuery["scene"].setInput( set["out"] )
		setQuery["location"].setValue( "/plane" )
		setQuery["sets"].setValue( "A" )

		self.assertEqual( setQuery["matches"].getValue(), IECore.StringVectorData() )
		self.assertEqual( setQuery["firstMatch"].getValue(), "" )

		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		self.assertEqual( setQuery["matches"].getValue(), IECore.StringVectorData( [ "A" ] ) )
		self.assertEqual( setQuery["firstMatch"].getValue(), "A" )

	def testCantVaryInheritsOrSetsPerLocation( self ) :

		# Our recursive implementation via `__matchesInternal` means
		# that every location must be using the same value of `inherits`
		# and `sets`. For this reason, we make sure that `${scene:path}`
		# isn't available to them.

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["plane"]["out"] )

		script["query"] = GafferScene.SetQuery()
		script["query"]["scene"].setInput( script["group"]["out"] )
		script["query"]["location"].setValue( "/group/plane" )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			path = context["scene:path"]
			parent["query"]["inherit"] = path.size() > 1
			"""
		) )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Context has no variable named "scene:path"' ) :
			script["query"]["firstMatch"].getValue()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			path = context["scene:path"]
			parent["query"]["sets"] = "A" if path.size() > 1 else "B"
			"""
		) )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Context has no variable named "scene:path"' ) :
			script["query"]["firstMatch"].getValue()

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testScaling( self ) :

		# A naive implementation of SetQuery would scale poorly with
		# scene complexity. This test queries set memberships at
		# every location of a ~200,000 location scene.

		numAssets = 200

		# /asset0
		#    /plane
		#       /instances          { asset0 }
		#           /sphere
		#               0 .. N
		# /asset1
		#    /plane
		#       /instances          { asset1 }
		#           /sphere
		#               0 .. N
		#
		# ...
		#
		# /asset<numAssets>
		#    /plane
		#       /instances           { asset999 }
		#           /sphere
		#               0 .. N

		plane = GafferScene.Plane()
		plane["divisions"].setValue( imath.V2i( 100, 10 ) )
		sphere = GafferScene.Sphere()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane["out"] )
		instancer["filter"].setInput( planeFilter["out"] )
		instancer["prototypes"].setInput( sphere["out"] )

		instancesFilter = GafferScene.PathFilter()
		instancesFilter["paths"].setValue( IECore.StringVectorData( [ "/plane/instances" ] ) )

		setNode = GafferScene.Set()
		setNode["in"].setInput( instancer["out"] )
		setNode["filter"].setInput( instancesFilter["out"] )
		setNode["name"].setValue( "${collect:rootName}" )

		collectScenes = GafferScene.CollectScenes()
		collectScenes["in"].setInput( setNode["out"] )
		collectScenes["rootNames"].setValue(
			IECore.StringVectorData( [ "asset{}".format( i ) for i in range( 0, numAssets ) ] )
		)

		setNames = [ str( s ) for s in collectScenes["out"].setNames() ]
		self.assertEqual( setNames, [ "asset{}".format( i ) for i in range( 0, numAssets ) ] )
		self.assertEqual(
			collectScenes["out"].set( "asset9" ).value,
			IECore.PathMatcher( [ "/asset9/plane/instances" ] )
		)

		# Arrange to query set memberships for every single location in the scene,
		# recording them in an attribute on that location. A naive approach would
		# query all `numAssets` sets for every location, which would perform extremely
		# poorly.

		setQuery = GafferScene.SetQuery()
		setQuery["scene"].setInput( collectScenes["out"] )
		setQuery["location"].setValue( "${scene:path}" )
		setQuery["sets"].setValue( " ".join( setNames ) )
		setQuery["inherit"].setValue( True )

		allFilter = GafferScene.PathFilter()
		allFilter["paths"].setValue( IECore.StringVectorData( [ "..." ] ) )

		attributes = GafferScene.CustomAttributes()
		attributes["in"].setInput( collectScenes["out"] )
		attributes["filter"].setInput( allFilter["out"] )
		attributes["attributes"]["firstMatch"] = Gaffer.NameValuePlug( "firstMatch", "" )
		attributes["attributes"]["firstMatch"]["value"].setInput( setQuery["firstMatch"] )

		# See how long that takes

		with GafferTest.TestRunner.PerformanceScope() :
			GafferSceneTest.traverseScene( attributes["out"] )

		# Check that we made the scene we think we made

		self.assertEqual(
			attributes["out"].attributes( "/asset9/plane/instances/sphere/100" )["firstMatch"],
			IECore.StringData( "asset9" )
		)

	def testAsSpreadsheetSelector( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "A" )

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "B" )

		group = GafferScene.Group()
		group["in"][0].setInput( plane["out"] )
		group["in"][1].setInput( sphere["out"] )

		childrenFilter = GafferScene.PathFilter()
		childrenFilter["paths"].setValue( IECore.StringVectorData( [ "/group/*" ] ) )

		attributes = GafferScene.StandardAttributes()
		attributes["in"].setInput( group["out"] )
		attributes["filter"].setInput( childrenFilter["out"] )
		attributes["attributes"]["displayColor"]["enabled"].setValue( True )

		setQuery = GafferScene.SetQuery()
		setQuery["scene"].setInput( group["out"] )
		setQuery["location"].setValue( "${scene:path}" )

		spreadsheet = Gaffer.Spreadsheet()
		spreadsheet["selector"].setInput( setQuery["firstMatch"] )
		spreadsheet["rows"].addColumn( attributes["attributes"]["displayColor"]["value"], name = "displayColor" )
		attributes["attributes"]["displayColor"]["value"].setInput( spreadsheet["out"]["displayColor"] )

		rowA = spreadsheet["rows"].addRow()
		rowB = spreadsheet["rows"].addRow()
		rowA["name"].setValue( "A" )
		rowA["cells"]["displayColor"]["value"].setValue( imath.Color3f( 1, 0, 0 ) )
		rowB["name"].setValue( "B" )
		rowB["cells"]["displayColor"]["value"].setValue( imath.Color3f( 0, 1, 0 ) )

		setQuery["sets"].setInput( spreadsheet["enabledRowNames"] )

		self.assertEqual( attributes["out"].attributes( "/group/plane" )["render:displayColor"].value, imath.Color3f( 1, 0, 0 ) )
		self.assertEqual( attributes["out"].attributes( "/group/sphere" )["render:displayColor"].value, imath.Color3f( 0, 1, 0 ) )

	def testEmptyLocationGivesEmptyResult( self ) :

		plane = GafferScene.Plane()

		rootFilter = GafferScene.PathFilter()
		rootFilter["paths"].setValue( IECore.StringVectorData( [ "/" ] ) )

		set = GafferScene.Set()
		set["in"].setInput( plane["out"] )
		set["filter"].setInput( rootFilter["out"] )
		set["name"].setValue( "A" )

		setQuery = GafferScene.SetQuery()
		setQuery["scene"].setInput( set["out"] )
		setQuery["sets"].setValue( "A" )

		self.assertEqual( setQuery["location"].getValue(), "" )
		self.assertEqual( setQuery["matches"].getValue(), IECore.StringVectorData() )
		self.assertEqual( setQuery["firstMatch"].getValue(), "" )

		setQuery["location"].setValue( "/" )
		self.assertEqual( setQuery["matches"].getValue(), IECore.StringVectorData( [ "A" ] ) )
		self.assertEqual( setQuery["firstMatch"].getValue(), "A" )

if __name__ == "__main__":
	unittest.main()
