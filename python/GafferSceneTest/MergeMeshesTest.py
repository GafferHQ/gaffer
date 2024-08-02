##########################################################################
#
#  Copyright (c) 2024, Image Engine Design Inc. All rights reserved.
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
import imath
import inspect
import pathlib
import random

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest
import GafferTest

# Because we haven't yet figured out where else assertMeshesPraticallyEqual should live
import GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest

class MergeMeshesTest( GafferSceneTest.SceneTestCase ) :

	def listLocations( self, scenePlug ):

		result = []

		def visitLoc( path ):
			if path:
				result.append( path )
			for i in scenePlug.childNames( path ):
				childPath = path.copy()
				childPath.append( i )
				visitLoc( childPath )

		visitLoc( IECore.InternedStringVectorData() )
		return result

	def assertBoundingBoxesValid( self, scenePlug ):
		for i in self.listLocations( scenePlug ):
			o = scenePlug.object( i )
			refBound = scenePlug.childBounds( i )
			if type( o ) != IECore.NullObject:
				refBound.extendBy( GafferScene.SceneAlgo.bound( o ) )

			# Weird way of testing if scenePlug.bound is a superset of refBound
			targetBound = scenePlug.bound( i )
			testBox = targetBound
			testBox.extendBy( refBound )
			self.assertEqual( testBox, targetBound,
				msg = "For location %s" % GafferScene.ScenePlug.pathToString( i )
			)


	def testBasic( self ) :
		sphere = GafferScene.Sphere()

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ '/sphere' ] ) )

		duplicate = GafferScene.Duplicate()
		duplicate["in"].setInput( sphere["out"] )
		duplicate["filter"].setInput( sphereFilter["out"] )
		duplicate["copies"].setValue( 10 )

		testScene = GafferScene.Group()
		testScene["in"][0].setInput( duplicate["out"] )

		toMerge = [ '/group/sphere2', '/group/sphere3', '/group/sphere4' ]

		chooseFilter = GafferScene.PathFilter()
		chooseFilter["paths"].setValue( IECore.StringVectorData( toMerge ) )

		mergeMeshes = GafferScene.MergeMeshes()
		mergeMeshes["in"].setInput( testScene["out"] )
		mergeMeshes["filter"].setInput( chooseFilter["out"] )

		mergeMeshes["destination"].setValue( "${scene:path}" )

		# With the destination set to "scene:path", every mesh goes back to its current location,
		# so no changes are made
		self.assertScenesEqual( mergeMeshes["out"], mergeMeshes["in"] )

		# If we set the `source`, we're no longer operating in-place, and all the meshes get duplicated.
		mergeMeshes["source"].setInput( testScene["out"] )

		refDuplicate = GafferScene.Duplicate()
		refDuplicate["in"].setInput( testScene["out"] )
		refDuplicate["filter"].setInput( chooseFilter["out"] )

		self.assertScenesEqual( mergeMeshes["out"], refDuplicate["out"] )

		# Test some invalid destinations
		mergeMeshes["destination"].setValue( "/" )
		with self.assertRaisesRegex( RuntimeError, "Empty destination not allowed." ):
			GafferSceneTest.traverseScene( mergeMeshes["out"] )
		mergeMeshes["destination"].setValue( "/*" )

		# Note this regex matches any /group/sphere* - the check for a valid destination happens while we're
		# multithreading over the sources, and it's random which location we first notice has a bogus destination.
		# I think this little bit of non-determinism is probably tolerable? ( It always correctly identifies one
		# of the errors in the users setup, just not always the same one, if there are multiple errors to choose from. )
		with self.assertRaisesRegex( RuntimeError, r"Invalid destination `/\*` for source location '/group/sphere.'. Name `\*` is invalid \(because it contains filter wildcards\)" ):
			GafferSceneTest.traverseScene( mergeMeshes["out"] )

		# Merge everything into one location
		mergeMeshes["destination"].setToDefault()

		refObjectToScene = GafferScene.ObjectToScene()
		refObjectToScene["name"].setValue( "mergedMesh" )
		refObjectToScene["object"].setValue( IECoreScene.MeshAlgo.merge( [ testScene["out"].object( i ) for i in toMerge ] ) )

		refParent = GafferScene.Parent()
		refParent["parent"].setValue( "/" )
		refParent["in"].setInput( testScene["out"] )
		refParent["child"][0].setInput( refObjectToScene["out"] )

		self.assertScenesEqual( mergeMeshes["out"], refParent["out"] )

		mergeMeshes["destination"].setValue( "/group/mergedMesh" )
		refParent["parent"].setValue( "/group" )

		self.assertScenesEqual( mergeMeshes["out"], refParent["out"] )

		mergeMeshes["destination"].setValue( "/group/foo/mergedMesh" )

		refNewGroup = GafferScene.Group()
		refNewGroup["name"].setValue( "foo" )
		refNewGroup["in"][0].setInput( refObjectToScene["out"] )

		refParent["child"][0].setInput( refNewGroup["out"] )
		refParent["parent"].setValue( "/group/" )

		self.assertScenesEqual( mergeMeshes["out"], refParent["out"] )

		refParent["child"][0].setInput( refObjectToScene["out"] )
		mergeMeshes["destination"].setValue( "/group" )
		refParent["parent"].setValue( "/" )
		refObjectToScene["name"].setValue( "group" )

		self.assertScenesEqual( mergeMeshes["out"], refParent["out"] )

		# Test that attributes are carried through from locations that already existed
		allFilter = GafferScene.PathFilter()
		allFilter["paths"].setValue( IECore.StringVectorData( [ '/...' ] ) )

		customAttributes = GafferScene.CustomAttributes()
		customAttributes["attributes"].addChild( Gaffer.NameValuePlug( "test", Gaffer.StringPlug( "value", defaultValue = '${scene:path}' ) ) )
		customAttributes["in"].setInput( duplicate["out"] )
		customAttributes["filter"].setInput( allFilter["out"] )

		testScene["in"][0].setInput( customAttributes["out"] )
		mergeMeshes["destination"].setValue( "/mergedMesh" )

		for i in self.listLocations( mergeMeshes["out"] ):
			if mergeMeshes["in"].exists( i ):
				self.assertEqual( mergeMeshes["out"].attributes( i ), mergeMeshes["in"].attributes( i ) )

	# One of the more obvious very weird cases: two meshes, where one contains the other, and the destination
	# plug for each mesh is set to overwrite the other mesh.
	def testSwap( self ):

		bigCube = GafferScene.Cube()
		bigCube["name"].setValue( 'bigCube' )
		bigCube["transform"]["translate"].setValue( imath.V3f( 4, 5, 6 ) )
		bigCube["transform"]["rotate"].setValue( imath.V3f( 90, 0, 0 ) )
		bigCube["dimensions"].setValue( imath.V3f( 3, 3, 3 ) )

		smallCube = GafferScene.Cube()
		smallCube["name"].setValue( 'smallCube' )
		smallCube["transform"]["translate"].setValue( imath.V3f( 1, 2, 3 ) )
		smallCube["transform"]["rotate"].setValue( imath.V3f( 0, 90, 0 ) )

		parent = GafferScene.Parent()
		parent["in"].setInput( bigCube["out"] )
		parent["children"][0].setInput( smallCube["out"] )
		parent["parent"].setValue( '/bigCube' )

		filterAll = GafferScene.PathFilter()
		filterAll["paths"].setValue( IECore.StringVectorData( [ '/...' ] ) )

		mergeMeshes = GafferScene.MergeMeshes()
		mergeMeshes["in"].setInput( parent["out"] )
		mergeMeshes["filter"].setInput( filterAll["out"] )
		mergeMeshes["destExpression"] = Gaffer.Expression()
		mergeMeshes["destExpression"].setExpression(
			'parent["destination"] = "/bigCube" if (context.get( "scene:path", [] ) or [ "" ])[-1] == "smallCube" else "/bigCube/smallCube"',
			"python"
		)

		self.assertEqual( self.listLocations( mergeMeshes["out"] ), self.listLocations( mergeMeshes["in"] ) )

		# After swapping, the bounds get mixed together so that both locations have the total bound
		GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().betterAssertAlmostEqual(
			mergeMeshes["out"].bound( "/bigCube" ), mergeMeshes["in"].bound( "/bigCube" ),
			tolerance = 0.000001
		)
		# This is just the total bound in the local space of this location
		GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().betterAssertAlmostEqual(
			mergeMeshes["out"].bound( "/bigCube/smallCube" ),
			imath.Box3f( imath.V3f( -0.5, -3.5, -2.5 ), imath.V3f( 4.5, 0.5, 0.5 ) ),
			tolerance = 0.000001
		)

		freezeBefore = GafferScene.FreezeTransform()
		freezeBefore["in"].setInput( parent["out"] )
		freezeBefore["filter"].setInput( filterAll["out"] )

		freezeAfter = GafferScene.FreezeTransform()
		freezeAfter["in"].setInput( mergeMeshes["out"] )
		freezeAfter["filter"].setInput( filterAll["out"] )

		self.assertEqual( freezeBefore["out"].object( "/bigCube" ), freezeAfter["out"].object( "/bigCube/smallCube" ) )
		self.assertEqual( freezeBefore["out"].object( "/bigCube/smallCube" ), freezeAfter["out"].object( "/bigCube" ) )


	# Compute the bound we expect for the given sources tranformed to the given destination.
	# childBoundPlug may be set to the output plug without making this test overly circular -
	# we don't depend on the bound at this location, only at child locations
	def referenceBound( self, destPath, sources, inPlug, childBoundPlug ):

		result = childBoundPlug.childBounds( destPath )

		while not inPlug.exists( destPath ):
			destPath = IECore.InternedStringVectorData( destPath[:-1] )

		toDest = inPlug.fullTransform( destPath ).inverse()

		for s in sources:
			result.extendBy(
				inPlug.bound( s ) * ( inPlug.fullTransform( s ) * toDest )
			)

		return result

	# Check that the output sets match the input sets, with any paths that no longer exist pruned.
	def assertSetsMatchWithPruning( self, outPlug, inPlug, filterMatcher, destMatcher ):
		self.assertEqual( outPlug.setNames(), inPlug.setNames() )
		for sn in inPlug.setNames():
			# The set we expect is the input set, without any paths that are filtered out, but not used as destinations
			refSet = [
				i for i in inPlug.set( sn ).value.paths()
				if destMatcher.match( i ) & ( IECore.PathMatcher.Result.ExactMatch | IECore.PathMatcher.Result.DescendantMatch ) or not filterMatcher.match( i ) & ( IECore.PathMatcher.Result.AncestorMatch | IECore.PathMatcher.Result.ExactMatch )
			]
			self.assertEqual( outPlug.set( sn ).value.paths(), refSet, msg = "Set %s" % sn )

	def testWeirdestCornerCases( self ):
		bigSphere = GafferScene.Sphere()
		bigSphere["radius"].setValue( 2 )
		bigSphere["name"].setValue( "bigSphere" )

		smallSphere = GafferScene.Sphere()
		smallSphere["name"].setValue( "smallSphere" )

		parent = GafferScene.Parent()
		parent["in"].setInput( bigSphere["out"] )
		parent["child"][0].setInput( smallSphere["out"] )
		parent["parent"].setValue( "/" )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ '/smallSphere' ] ) )

		mergeMeshes = GafferScene.MergeMeshes()
		mergeMeshes["in"].setInput( parent["out"] )
		mergeMeshes["filter"].setInput( f["out"] )
		mergeMeshes["destination"].setValue( '/bigSphere/merged' )

		# Check that we don't discard the bound of a object at a location when adding new children ( this
		# unfortunately requires a pretty ugly special case in the code )
		self.assertEqual( mergeMeshes["out"].bound( "/bigSphere" ), imath.Box3f( imath.V3f( -2 ), imath.V3f( 2 ) ) )

		parent["parent"].setValue( "/bigSphere" )
		f["paths"].setValue( IECore.StringVectorData( [ '/bigSphere/smallSphere' ] ) )
		mergeMeshes["destination"].setValue( '/merged' )

		# This is definitely incorrect - by pruning a location under this location with both children and a mesh,
		# we end up with a bounding box that is incorrectly set empty.
		#
		# We accept this incorrect behaviour because Prune does the same thing when adjustBounds is set, and
		# there isn't really any good way of fixes this, without switching to storing the object bound as a
		# completely separate plug to the child bounds.
		self.assertEqual( mergeMeshes["out"].bound( "/bigSphere" ), imath.Box3f() )


	def makePathUnique( self, path, allLocations, filterMatcher, usedDestinations ):

		# ChildNamesMap isn't bound in Python, so hack up the bit of it we need

		while ( path in allLocations and
			not ( filterMatcher.match( path ) &
			( IECore.PathMatcher.Result.AncestorMatch | IECore.PathMatcher.Result.ExactMatch ) )
		) or path in usedDestinations:
			leafName = path[-1].value()
			if leafName[-1] == "1":
				leafName = leafName[:-1] + "2"
			elif leafName[-1] == "2":
				leafName = leafName[:-1] + "3"
			elif leafName[-1] == "3":
				leafName = leafName[:-1] + "4"
			else:
				leafName = leafName + "1"
			path = IECore.InternedStringVectorData( list( path )[:-1] + [leafName] )
		usedDestinations.append( path )

		return path

	def testReferenceSetup( self ) :

		random.seed( 42 )

		# Set up a moderately sized hierarchy using a Loop
		leafCube = GafferScene.Cube()

		loop = Gaffer.Loop()
		loop.setup( GafferScene.ScenePlug() )
		loop["in"].setInput( leafCube["out"] )

		rootFilter = GafferScene.PathFilter()
		rootFilter["paths"].setValue( IECore.StringVectorData( [ '/*' ] ) )

		transformLeft = GafferScene.Transform()
		transformLeft["in"].setInput( loop["previous"] )
		transformLeft["filter"].setInput( rootFilter["out"] )
		transformLeft["space"].setValue( GafferScene.Transform.Space.World )
		transformLeft["transform"]["rotate"].setValue( imath.V3f( -30, 0, 0 ) )

		transformRight = GafferScene.Transform()
		transformRight["in"].setInput( loop["previous"] )
		transformRight["filter"].setInput( rootFilter["out"] )
		transformRight["space"].setValue( GafferScene.Transform.Space.World )
		transformRight["transform"]["rotate"].setValue( imath.V3f( 30, 0, 0 ) )

		stemCube = GafferScene.Cube()

		group = GafferScene.Group()
		group["in"][0].setInput( transformLeft["out"] )
		group["in"][1].setInput( transformRight["out"] )
		group["in"][2].setInput( stemCube["out"] )
		group["transform"]["translate"].setValue( imath.V3f( 0, 1.26999998, 0 ) )
		group["transform"]["rotate"].setValue( imath.V3f( 0, 90, 0 ) )

		loop["next"].setInput( group["out"] )
		loop["iterations"].setValue( 5 )

		pathFilterAll = GafferScene.PathFilter( "PathFilterAll" )
		pathFilterAll["paths"].setValue( IECore.StringVectorData( [ '/...' ] ) )

		# Delete all primvars but P so the reference file stored on disk is smaller.
		deletePrimitiveVariables = GafferScene.DeletePrimitiveVariables()
		deletePrimitiveVariables["in"].setInput( loop["out"] )
		deletePrimitiveVariables["filter"].setInput( pathFilterAll["out"] )
		deletePrimitiveVariables["names"].setValue( 'P' )
		deletePrimitiveVariables["invertNames"].setValue( True )

		mergeMeshes = GafferScene.MergeMeshes()
		mergeMeshes["in"].setInput( deletePrimitiveVariables["out"] )
		mergeMeshes["filter"].setInput( pathFilterAll["out"] )
		mergeMeshes["destination"].setValue( '/merged' )

		reference = GafferScene.SceneReader()
		reference["fileName"].setValue( pathlib.Path( __file__ ).parent / "usdFiles" / "merged.usd" )

		self.assertScenesEqual( mergeMeshes["out"], reference["out"], checks = self.allSceneChecks - { "sets" } )

		allLocations = self.listLocations( mergeMeshes["in"] )
		possiblePruneLocations = [ i for i in allLocations if len( i ) > 3 ]

		# Define some sets
		setAll = GafferScene.Set()
		setAll["in"].setInput( deletePrimitiveVariables["out"])
		setAll["filter"].setInput( pathFilterAll["out"] )
		setAll["name"].setValue( "setAll" )

		pathFilterA = GafferScene.PathFilter( "PathFilterA" )
		pathFilterA["paths"].setValue( IECore.StringVectorData(
				random.sample( [ GafferScene.ScenePlug.pathToString(i) for i in possiblePruneLocations ], len( possiblePruneLocations ) // 3 )
		) )

		setA = GafferScene.Set()
		setA["in"].setInput( setAll["out"])
		setA["filter"].setInput( pathFilterA["out"] )
		setA["name"].setValue( "setA" )

		pathFilterB = GafferScene.PathFilter( "PathFilterB" )
		pathFilterB["paths"].setValue( IECore.StringVectorData(
				random.sample( [ GafferScene.ScenePlug.pathToString(i) for i in possiblePruneLocations ], len( possiblePruneLocations ) // 6 )
		) )

		setB = GafferScene.Set()
		setB["in"].setInput( setA["out"])
		setB["filter"].setInput( pathFilterB["out"] )
		setB["name"].setValue( "setB" )

		mergeMeshes["in"].setInput( setB["out"] )

		mergeMeshes["filter"].setInput( pathFilterA["out"] )

		refPrune = GafferScene.Prune()
		refPrune["in"].setInput( setB["out"] )
		refPrune["filter"].setInput( pathFilterA["out"] )
		refPrune["adjustBounds"].setValue( True )

		pathFilterMerged = GafferScene.PathFilter()
		pathFilterMerged["paths"].setValue( IECore.StringVectorData( [ "/merged" ] ) )

		mergedPrune = GafferScene.Prune()
		mergedPrune["in"].setInput( mergeMeshes["out"] )
		mergedPrune["filter"].setInput( pathFilterMerged["out"] )
		mergedPrune["adjustBounds"].setValue( True )

		# If we remove the location we merged everything to, then MergeMeshes has the same effect as a Prune node:
		# it removes all the filtered locations from the scene ( in particular, this exercises that we handle sets
		# correctly by removing the locations that no longer exist ).
		self.assertScenesEqual( mergedPrune["out"], refPrune["out"] )

		pathFilterALeaves = GafferScene.PathFilter()
		pathFilterALeaves["paths"].setValue( IECore.StringVectorData(
			[ i for i in pathFilterA["paths"].getValue() if i.split( "/" )[-1].startswith( "cube" ) ]
		) )

		refIsolate = GafferScene.Isolate()
		refIsolate["in"].setInput( setB["out"] )
		refIsolate["filter"].setInput( pathFilterALeaves["out"] )

		mergeAfterIsolate = GafferScene.MergeMeshes()
		mergeAfterIsolate["in"].setInput( refIsolate["out"] )
		mergeAfterIsolate["filter"].setInput( pathFilterAll["out"] )
		mergeAfterIsolate["destination"].setValue( "merged" )

		# The merged result with a filter is the same as if you isolated all the targeted leaves, and then merged
		# everything
		self.assertEqual( mergeMeshes["out"].object( "/merged" ), mergeAfterIsolate["out"].object( "/merged" ) )

		# Repeat those 2 tests using pathFilterB
		mergeMeshes["filter"].setInput( pathFilterB["out"] )
		refPrune["filter"].setInput( pathFilterB["out"] )
		self.assertScenesEqual( mergedPrune["out"], refPrune["out"] )

		pathFilterBLeaves = GafferScene.PathFilter()
		pathFilterBLeaves["paths"].setValue( IECore.StringVectorData(
			[ i for i in pathFilterB["paths"].getValue() if i.split( "/" )[-1].startswith( "cube" ) ]
		) )

		refIsolate["filter"].setInput( pathFilterBLeaves["out"] )
		self.assertEqual( mergeMeshes["out"].object( "/merged" ), mergeAfterIsolate["out"].object( "/merged" ) )

		# If the source is set, and we're not operating in place, the sets won't be modified at all
		mergeMeshes["source"].setInput( setB["out"] )

		self.assertEqual( mergeMeshes["out"].set( "setAll" ), mergeMeshes["in"].set( "setAll" ) )
		self.assertEqual( mergeMeshes["out"].set( "setA" ), mergeMeshes["in"].set( "setA" ) )
		self.assertEqual( mergeMeshes["out"].set( "setB" ), mergeMeshes["in"].set( "setB" ) )

		mergeMeshes["source"].setInput( None )

		mergeMeshes["filter"].setInput( pathFilterAll["out"] )

		# Test that parenting under an existing location should keep the transform of that location, and
		# position the vertices so that applying the transform leads to everything being correctly placed.
		# We test this at several different locations throughout the hierarchy, or in a brand new hierarchy.
		applyTransform = GafferScene.FreezeTransform()
		applyTransform["in"].setInput( mergeMeshes["out"] )
		applyTransform["filter"].setInput( pathFilterAll["out"] )

		# Check the expected result for a MergeMeshes with a constant destination.
		def validateSimple( path, refPath ):
			pathTokens = GafferScene.ScenePlug.stringToPath( path )

			self.assertEqual(
				self.listLocations( mergeMeshes["out"] ),
				[ IECore.InternedStringVectorData( pathTokens[:i + 1] ) for i in range( len( pathTokens ) ) ]
			)
			self.assertEqual(
				mergeMeshes["out"].fullTransform( path ),
				mergeMeshes["in"].fullTransform( refPath )
			)

			currentBound = reference["out"].bound( "/merged" ) * mergeMeshes["out"].fullTransform( path ).inverse()

			for i in range( len( pathTokens ), 1, -1 ):
				GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().betterAssertAlmostEqual(
					mergeMeshes["out"].bound( pathTokens[:i] ),
					currentBound,
					tolerance = 0.00001
				)
				currentBound = currentBound * mergeMeshes["out"].transform( pathTokens[:i] )

			GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().assertMeshesPracticallyEqual(
				applyTransform["out"].object( path ),
				reference["out"].object( "/merged" ), tolerance = 0.000001
			)

		mergeMeshes["destination"].setValue( '/group/group/group/group/group/cube/merged' )
		validateSimple( '/group/group/group/group/group/cube/merged', '/group/group/group/group/group/cube' )

		mergeMeshes["destination"].setValue( '/group/group/group/group/group/cube' )
		validateSimple( '/group/group/group/group/group/cube', '/group/group/group/group/group/cube' )

		mergeMeshes["destination"].setValue( '/group/group/group' )
		validateSimple( '/group/group/group', '/group/group/group' )

		mergeMeshes["destination"].setValue( '/group/group/group/merged' )
		validateSimple( '/group/group/group/merged', '/group/group/group' )

		mergeMeshes["destination"].setValue( '/foo/bar/merged' )
		self.assertEqual( self.listLocations( mergeMeshes["out"] ), [ GafferScene.ScenePlug.stringToPath(i) for i in [ '/foo', '/foo/bar', '/foo/bar/merged' ] ] )
		self.assertEqual( mergeMeshes["out"].fullTransform( '/foo/bar/merged' ), imath.M44f() )
		self.assertEqual( applyTransform["out"].object( '/foo/bar/merged' ), reference["out"].object( "/merged" ) )
		self.assertEqual( mergeMeshes["out"].bound( '/foo/bar/merged' ), reference["out"].bound( "/merged" ) )
		self.assertEqual( mergeMeshes["out"].bound( '/foo/bar' ), reference["out"].bound( "/merged" ) )
		self.assertEqual( mergeMeshes["out"].bound( '/foo' ), reference["out"].bound( "/merged" ) )

		mergeMeshes["destination"].setValue( '${scene:path}' )
		self.assertScenesEqual( mergeMeshes["out"], mergeMeshes["in"] )

		# If we connect source, then we're no longer operating in-place, and only add new locations,
		# without removing existing ones.
		mergeMeshes["source"].setInput( setB["out"] )

		# If we filter to everything, We get everything duplicated, except not the root, and the groups
		# become empty locations. Maybe it was silly to make a reference for this using a duplicate ...
		# we need to tweak it a fair bit to match - the difference with MergeObjects is that the newly
		# created locations will have no transforms or children.
		refDuplicate = GafferScene.Duplicate()
		refDuplicate["in"].setInput( setB["out"] )
		refDuplicate["filter"].setInput( pathFilterAll["out"] )

		bogusChildrenFilter = GafferScene.PathFilter()
		bogusChildrenFilter["paths"].setValue( IECore.StringVectorData( [
			'/root1', '/group1/*', '/.../group2/*', '/.../group3/*'
		] ) )

		refPruneBogusChildren = GafferScene.Prune()
		refPruneBogusChildren["in"].setInput( refDuplicate["out"] )
		refPruneBogusChildren["filter"].setInput( bogusChildrenFilter["out"] )

		refFreeezeFilter = GafferScene.PathFilter()
		refFreeezeFilter["paths"].setValue( IECore.StringVectorData( [ '.../cube3', '.../cube4', '.../group2', '.../group3', '/group1' ] ) )

		refFreeze = GafferScene.FreezeTransform()
		refFreeze["in"].setInput( refPruneBogusChildren["out"] )
		refFreeze["filter"].setInput( refFreeezeFilter["out"] )

		self.assertScenesEqual( mergeMeshes["out"], refFreeze["out"], checks = self.allSceneChecks - { "bound", "object", "transform", "sets" } )

		# If we fixed the precision of Duplicate, then we could probably just use the default checks of
		# assertScenesEqual, instead of using tolerances here
		for l in self.listLocations( mergeMeshes["out"] ):
			GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().betterAssertAlmostEqual(
				mergeMeshes["out"].transform( l ), refFreeze["out"].transform( l ), tolerance = 0.000001
			)
			GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().betterAssertAlmostEqual(
				mergeMeshes["out"].bound( l ), refFreeze["out"].bound( l ), tolerance = 0.000001
			)
			if not ( type( mergeMeshes["out"].object( l ) ) == IECore.NullObject ):
				GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().assertMeshesPracticallyEqual(
					mergeMeshes["out"].object( l ), refFreeze["out"].object( l ), tolerance = 0.000001
				)

		# Merge everything to one location while not operating in place

		mergeMeshes["destination"].setValue( '/merged' )

		postPruneFilter = GafferScene.PathFilter()
		postPruneFilter["paths"].setValue( IECore.StringVectorData( [ '/group' ] ) )

		postPrune = GafferScene.Prune()
		postPrune["in"].setInput( mergeMeshes["out"] )
		postPrune["filter"].setInput( postPruneFilter["out"] )

		# The new location has everything in it
		self.assertScenesEqual( postPrune["out"], reference["out"], checks = self.allSceneChecks - { "sets" } )

		# The existing locations are all still there
		postPruneFilter["paths"].setValue( IECore.StringVectorData( [ '/merged' ] ) )
		self.assertScenesEqual( postPrune["out"], mergeMeshes["in"], checks = self.allSceneChecks - { "bound" } )
		self.assertBoundingBoxesValid( mergeMeshes["out"] )


		# Now go back to operating in-place
		mergeMeshes["source"].setInput( None )

		# Start prepping for some more complex merges, where each source location gets a different destination.
		mergeMeshes["testDestinations"] = Gaffer.StringVectorDataPlug()

		mergeMeshes["destExpression"] = Gaffer.Expression()
		mergeMeshes["destExpression"].setExpression( inspect.cleandoc( """
			td = parent["testDestinations"]
			parent["destination"] = td[ context.get( "scene:path" ).hash().h1() % len( td ) ]
		""" ) )

		# One of the biggest tools here for testing complex merges is that in most cases, final vertex positions
		# are preserved, so if we merge everything down, we should still get the same mesh. Even if the hierarchy
		# is totally scrambled, merging everything to one location will still come out the same ... if things are
		# working.
		remerge = GafferScene.MergeMeshes()
		remerge["in"].setInput( mergeMeshes["out"] )
		remerge["filter"].setInput( pathFilterAll["out"] )
		remerge["destination"].setValue( "/merged" )

		# Test pseudo-randomly splitting to 2 different locations
		mergeMeshes["testDestinations"].setValue( IECore.StringVectorData( [ "/A", "/B" ] ) )

		self.assertEqual( mergeMeshes["out"].object( "/A" ).numFaces(), 180 )
		self.assertEqual( mergeMeshes["out"].object( "/B" ).numFaces(), 198 )
		GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().assertMeshesPracticallyEqual(
			remerge["out"].object( "/merged" ),
			reference["out"].object( "/merged" ), tolerance = 0.000001
		)
		self.assertBoundingBoxesValid( mergeMeshes["out"] )

		offsetFilter = GafferScene.PathFilter()
		offsetFilter["paths"].setValue( IECore.StringVectorData( [ '/*' ] ) )


		# To get matching reference for some of our tests, we need to compare to a merged mesh that
		# doesn't include meshes from some locations. To get this reference with minimal reliance
		# on MergeMeshes, we can DeleteObjects any locations we don't want.
		prunedReferenceFilter = GafferScene.PathFilter()

		prunedReferenceDelete = GafferScene.DeleteObject()
		prunedReferenceDelete["in"].setInput( setB["out"] )
		prunedReferenceDelete["filter"].setInput( prunedReferenceFilter["out"] )

		prunedReferenceMerge = GafferScene.MergeMeshes()
		prunedReferenceMerge["in"].setInput( prunedReferenceDelete["out"] )
		prunedReferenceMerge["destination"].setValue( "/merged" )
		prunedReferenceMerge["filter"].setInput( pathFilterAll["out"] )


		# Prep a reference where all the filtered meshes are present twice.
		# ( We use an offset to distinguish meshes connected to source from meshes connected to in,
		# because assertMeshesPracticallyEqual doesn't deal well with overlapping verts ).
		prunedReferenceOffset = GafferScene.Transform()
		prunedReferenceOffset["filter"].setInput( offsetFilter["out"] )
		prunedReferenceOffset["space"].setValue( GafferScene.Transform.Space.World )
		prunedReferenceOffset["in"].setInput( prunedReferenceMerge["out"] )
		prunedReferenceOffset["transform"]["translate"].setValue( imath.V3f( 5, 0, 0 ) )

		doubleRefGroup = GafferScene.Group()
		doubleRefGroup["in"][0].setInput( reference["out"] )
		doubleRefGroup["in"][1].setInput( prunedReferenceOffset["out"] )

		doubleRef = GafferScene.MergeMeshes()
		doubleRef["in"].setInput( doubleRefGroup["out"] )
		doubleRef["filter"].setInput( pathFilterAll["out"] )
		doubleRef["destination"].setValue( "/merged" )

		sourceOffset = GafferScene.Transform()
		sourceOffset["filter"].setInput( offsetFilter["out"] )
		sourceOffset["space"].setValue( GafferScene.Transform.Space.World )
		sourceOffset["in"].setInput( setB["out"] )
		sourceOffset["transform"]["translate"].setValue( imath.V3f( 5, 0, 0 ) )

		# Returned if a filter match value corresponds to being pruned by the parent, but not included in the filter
		def parentPruned( m ):
			return ( m & IECore.PathMatcher.Result.AncestorMatch ) and not ( m & IECore.PathMatcher.Result.ExactMatch )

		# Now getting to the real meat of this test - we'll test with several different shuffles of destinations,
		# and with different filters, and make sure things always come out reasonably.
		for subsetSize in [ 3, 7, len( allLocations ) ]:
			mergeMeshes["testDestinations"].setValue( IECore.StringVectorData(
				[ "/new", "/new/loc", "/group/group/group/group/group/cube", "/group/group1/group/group/group/cube/merged" ] +
				random.sample( [ GafferScene.ScenePlug.pathToString(i) for i in allLocations ], subsetSize )
			) )

			for f in [ pathFilterAll, pathFilterA, pathFilterB ]:

				if f == pathFilterAll:
					filteredLocations = allLocations
				else:
					filteredLocations = [ GafferScene.ScenePlug.stringToPath(i) for i in f["paths"].getValue() ]

				filterMatcher = IECore.PathMatcher( filteredLocations )

				mergeMeshes["filter"].setInput( f["out"] )

				destinationMap = {}

				# Prep a map of destinations and sources, so we can prepare our expected reference results
				c = Gaffer.Context( Gaffer.Context.current() )
				with c:
					for l in filteredLocations:
						c["scene:path"] = l
						destinationMap.setdefault( mergeMeshes["destination"].getValue(), [] ).append( GafferScene.ScenePlug.pathToString( l ) )

				destinationMatcher = IECore.PathMatcher( [ GafferScene.ScenePlug.stringToPath(i) for i in destinationMap.keys() ] )

				# "Abandoned" locations are locations that are not filtered, but their parents are.
				# They will not be merged to new location, but they will be removed from their original
				# locations
				abandonedLocations = [ GafferScene.ScenePlug.pathToString(i) for i in allLocations if parentPruned( filterMatcher.match( i ) ) ]
				prunedReferenceFilter["paths"].setValue( IECore.StringVectorData( abandonedLocations ) )

				# When we want a reference to compare to, we need a reference without abandoned locations,
				# so we have to use a reference path that also involves a merge. We can partially validate this
				# by validating against the reference file when there are no abandoned locations.
				if f == pathFilterAll:
					GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().assertMeshesPracticallyEqual(
						prunedReferenceMerge["out"].object( "/merged" ),
						reference["out"].object( "/merged" ), tolerance = 0.00001
					)
				# We can't compare to the remerge the reference mesh when there is a filter - it won't match
				# due to abandoned locations. But we can compare to a one-step reference merge that just skips
				# abandoned locations.
				GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().assertMeshesPracticallyEqual(
					remerge["out"].object( "/merged" ),
					prunedReferenceMerge["out"].object( "/merged" ), tolerance = 0.00001
				)

				self.assertBoundingBoxesValid( mergeMeshes["out"] )

				self.assertSetsMatchWithPruning( mergeMeshes["out"], mergeMeshes["in"], filterMatcher, destinationMatcher )

				# Test the bounds of the actual destination locations against our reference function.
				usedDestinations = []
				for dest, sources in destinationMap.items():

					# We need to figure out where this destination actually ends up in the hierarchy -
					# we will deduplicate names if they overlap with original locations that aren't filtered.
					uniqueDest = self.makePathUnique(
						GafferScene.ScenePlug.stringToPath( dest ), allLocations, filterMatcher, usedDestinations
					)

					refBound = self.referenceBound( uniqueDest, sources, mergeMeshes["in"], mergeMeshes["out"] )

					GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().betterAssertAlmostEqual( mergeMeshes["out"].bound( uniqueDest ), refBound, tolerance = 0.00001 )

				# If we attach a source so we're no longer working in place, all the target destinations should
				# get uniquified so that we end up with 2 full copies of the mesh.
				mergeMeshes["source"].setInput( sourceOffset["out"] )

				if f == pathFilterAll:
					prunedReferenceFilter["paths"].setValue( IECore.StringVectorData( [] ) )
				else:
					prunedReferenceFilter["paths"].setValue( IECore.StringVectorData( [ i for i in [ GafferScene.ScenePlug.pathToString( j ) for j in allLocations ] if not i in f["paths"].getValue()] ) )

				GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().assertMeshesPracticallyEqual(
					remerge["out"].object( "/merged" ),
					doubleRef["out"].object( "/merged" ), tolerance = 0.00001
				)
				self.assertBoundingBoxesValid( mergeMeshes["out"] )
				mergeMeshes["source"].setInput( None )

		# Reset values from the last loop iteration
		mergeMeshes["filter"].setInput( pathFilterAll["out"] )
		prunedReferenceFilter["paths"].setValue( IECore.StringVectorData( [] ) )

		# Replace Group locations with a location that contains the mesh itself. This isn't how we usually
		# expect scenes to be laid out - usually locations have either a mesh, or children, but not both.
		# But we do support it, and it does exercise some weird corner cases to test it.
		stemCube["name"].setValue( "group" )
		stemCube["transform"]["translate"].setValue( imath.V3f( 0, 1.26999998, 0 ) )
		stemCube["transform"]["rotate"].setValue( imath.V3f( 0, 90, 0 ) )

		parentToMesh = GafferScene.Parent()
		parentToMesh["parent"].setValue( "/group" )
		parentToMesh["in"].setInput( stemCube["out"] )
		parentToMesh["child"][0].setInput( transformLeft["out"] )
		parentToMesh["child"][1].setInput( transformRight["out"] )

		loop["next"].setInput( parentToMesh["out"] )

		mergeMeshes["testDestinations"].setValue( IECore.StringVectorData( [ "/merged" ] ) )

		GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().assertMeshesPracticallyEqual( mergeMeshes["out"].object( "/merged" ), reference["out"].object( "/merged" ) )
		self.assertBoundingBoxesValid( mergeMeshes["out"] )

		# A few more weird random scrambles for good luck
		for subsetSize in [ 3, 7, len( allLocations ) ]:
			mergeMeshes["testDestinations"].setValue( IECore.StringVectorData(
				[ "/new", "/new/loc", "/group/group/group/group/group/cube", "/group/group1/group/group/group/cube/merged" ] +
				random.sample( [ GafferScene.ScenePlug.pathToString(i) for i in allLocations ], subsetSize )
			) )
			GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().assertMeshesPracticallyEqual(
				remerge["out"].object( "/merged" ),
				reference["out"].object( "/merged" ), tolerance = 0.000002
			)
			self.assertBoundingBoxesValid( mergeMeshes["out"] )
			mergeMeshes["filter"].setInput( pathFilterA["out"] )
			self.assertBoundingBoxesValid( mergeMeshes["out"] )
			mergeMeshes["filter"].setInput( pathFilterB["out"] )
			self.assertBoundingBoxesValid( mergeMeshes["out"] )
			mergeMeshes["filter"].setInput( pathFilterAll["out"] )

		mergeMeshes["source"].setInput( sourceOffset["out"] )
		GafferSceneTest.IECoreScenePreviewTest.MeshAlgoTessellateTest().assertMeshesPracticallyEqual(
			remerge["out"].object( "/merged" ),
			doubleRef["out"].object( "/merged" ), tolerance = 0.00001
		)
		self.assertBoundingBoxesValid( mergeMeshes["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testPerformance( self ) :
		sphere = GafferScene.Sphere()

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ '/sphere' ] ) )

		duplicate = GafferScene.Duplicate()
		duplicate["in"].setInput( sphere["out"] )
		duplicate["filter"].setInput( sphereFilter["out"] )
		duplicate["copies"].setValue( 1000 )

		allFilter = GafferScene.PathFilter()
		allFilter["paths"].setValue( IECore.StringVectorData( [ "*" ] ) )

		mergeMeshes = GafferScene.MergeMeshes()
		mergeMeshes["in"].setInput( duplicate["out"] )
		mergeMeshes["filter"].setInput( allFilter["out"] )

		mergeMeshes["destination"].setValue( "/merged" )

		# Merging 1000 meshes makes sure that performance scales properly ( using the old IECoreScene::MeshAlgo::merge
		# takes 7 seconds instead of 0.02 seconds ).

		with GafferTest.TestRunner.PerformanceScope():
			mergeMeshes["out"].object( "/merged" )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testPerformanceUnprocessedLocations( self ) :
		plane = GafferScene.Plane()

		group = GafferScene.Group()
		group["in"][0].setInput( plane["out"] )

		group2 = GafferScene.Group()
		group2["in"][0].setInput( group["out"] )

		dupeFilter = GafferScene.PathFilter()
		dupeFilter["paths"].setValue( IECore.StringVectorData( [ '/group' ] ) )

		duplicate = GafferScene.Duplicate()
		duplicate["in"].setInput( group2["out"] )
		duplicate["filter"].setInput( dupeFilter["out"] )
		duplicate["copies"].setValue( 20000 )

		targetFilter = GafferScene.PathFilter()
		targetFilter["paths"].setValue( IECore.StringVectorData( [ "/group999/group/plane" ] ) )

		mergeMeshes = GafferScene.MergeMeshes()
		mergeMeshes["in"].setInput( duplicate["out"] )
		mergeMeshes["filter"].setInput( targetFilter["out"] )

		mergeMeshes["destination"].setValue( "/merged" )

		GafferSceneTest.traverseScene( mergeMeshes["in"] )

		with GafferTest.TestRunner.PerformanceScope():
			GafferSceneTest.traverseScene( mergeMeshes["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testPerformanceDeepPaths( self ) :
		plane = GafferScene.Plane()

		hierarchy = [ plane ]

		for i in range( 40 ):
			group = GafferScene.Group()
			group["in"][0].setInput( hierarchy[-1]["out"] )
			hierarchy.append( group )

		dupeFilter = GafferScene.PathFilter()
		dupeFilter["paths"].setValue( IECore.StringVectorData( [ '/group' ] ) )

		duplicate = GafferScene.Duplicate()
		duplicate["in"].setInput( hierarchy[-1]["out"] )
		duplicate["filter"].setInput( dupeFilter["out"] )
		duplicate["copies"].setValue( 200 )

		targetFilter = GafferScene.PathFilter()
		targetFilter["paths"].setValue( IECore.StringVectorData( [ "/..." ] ) )

		mergeMeshes = GafferScene.MergeMeshes()
		mergeMeshes["in"].setInput( duplicate["out"] )
		mergeMeshes["filter"].setInput( targetFilter["out"] )

		mergeMeshes["destination"].setValue( "${scene:path}" )

		GafferSceneTest.traverseScene( mergeMeshes["in"] )

		with GafferTest.TestRunner.PerformanceScope():
			GafferSceneTest.traverseScene( mergeMeshes["out"] )

if __name__ == "__main__":
	unittest.main()
