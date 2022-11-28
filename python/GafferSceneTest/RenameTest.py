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

import unittest

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class RenameTest( GafferSceneTest.SceneTestCase ) :

	def testPassThrough( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "setA" )

		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )

		# No filter

		rename = GafferScene.Rename()
		rename["in"].setInput( group["out"] )
		rename["name"].setValue( "newName" )

		self.assertTrue( rename["out"].exists( "/group/sphere" ) )
		self.assertScenesEqual( rename["out"], rename["in"] )
		self.assertSceneHashesEqual( rename["out"], rename["in"] )

		# Filter, but not matching anything yet

		pathFilter = GafferScene.PathFilter()
		rename["filter"].setInput( pathFilter["out"] )

		self.assertTrue( rename["out"].exists( "/group/sphere" ) )
		self.assertScenesEqual( rename["out"], rename["in"] )
		self.assertSceneHashesEqual( rename["out"], rename["in"] )

		# Filter matching something, but node disabled

		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )
		rename["enabled"].setValue( False )

		self.assertTrue( rename["out"].exists( "/group/sphere" ) )
		self.assertScenesEqual( rename["out"], rename["in"] )
		self.assertSceneHashesEqual( rename["out"], rename["in"] )

	def testBasicRename( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "setA" )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		rename = GafferScene.Rename()
		rename["in"].setInput( sphere["out"] )
		rename["filter"].setInput( sphereFilter["out"] )
		rename["name"].setValue( "ball" )

		self.assertSceneValid( rename["out"] )
		self.assertEqual( rename["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "ball" ] ) )
		self.assertPathsEqual( rename["out"], "/ball", rename["in"], "/sphere" )
		self.assertPathHashesEqual( rename["out"], "/ball", rename["in"], "/sphere" )
		self.assertEqual( rename["out"].set( "setA" ).value, IECore.PathMatcher( [ "/ball" ] ) )

	def testEmptyName( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "setA" )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		rename = GafferScene.Rename()
		rename["in"].setInput( sphere["out"] )
		rename["filter"].setInput( sphereFilter["out"] )
		rename["name"].setValue( "" )

		self.assertSceneValid( rename["out"] )
		self.assertScenesEqual( rename["out"], rename["in"] )

	def testClashingNames( self ) :

		# - group
		#     - sphere
		#     - cube

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "setA" )

		cube = GafferScene.Cube()
		cube["sets"].setValue( "setB" )

		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( cube["out"] )
		self.assertEqual( group["out"].childNames( "/group" ), IECore.InternedStringVectorData( [ "sphere", "cube" ] ) )

		# Rename "sphere" to "cube". We can't have two locations with the same
		# name, and we don't want to affect the original "cube" location in any
		# way because the filter doesn't touch it. So we must add a numeric
		# suffix to the location being renamed.

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )

		rename = GafferScene.Rename()
		rename["in"].setInput( group["out"] )
		rename["filter"].setInput( sphereFilter["out"] )
		rename["name"].setValue( "cube" )

		self.assertSceneValid( rename["out"] )

		self.assertEqual( rename["out"].childNames( "/group" ), IECore.InternedStringVectorData( [ "cube1", "cube" ] ) )
		self.assertPathsEqual( rename["out"], "/group/cube1", rename["in"], "/group/sphere" )
		self.assertPathHashesEqual( rename["out"], "/group/cube1", rename["in"], "/group/sphere" )
		self.assertPathsEqual( rename["out"], "/group/cube", rename["in"], "/group/cube" )
		self.assertPathHashesEqual( rename["out"], "/group/cube", rename["in"], "/group/cube" )

		self.assertEqual( rename["out"].set( "setA" ).value, IECore.PathMatcher( [ "/group/cube1" ] ) )
		self.assertEqual( rename["out"].set( "setB" ).value, IECore.PathMatcher( [ "/group/cube" ] ) )

	def __nameSpreadsheet( self, names ) :

		spreadsheet = Gaffer.Spreadsheet()
		spreadsheet["selector"].setValue( "${scene:path}" )
		spreadsheet["rows"].addColumn( Gaffer.StringPlug( "newName" ) )

		for inPath, outName in names.items() :
			row = spreadsheet["rows"].addRow()
			row["name"].setValue( inPath )
			row["cells"]["newName"]["value"].setValue( outName )

		return spreadsheet

	def testCanSwapNames( self ) :

		# - group
		#     - sphere
		#     - cube

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "setA" )

		cube = GafferScene.Cube()
		cube["sets"].setValue( "setB" )

		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( cube["out"] )
		self.assertEqual( group["out"].childNames( "/group" ), IECore.InternedStringVectorData( [ "sphere", "cube" ] ) )

		# Rename "sphere" to "cube" and "cube" to "sphere".

		allFilter = GafferScene.PathFilter()
		allFilter["paths"].setValue( IECore.StringVectorData( [ "/group/*" ] ) )

		spreadsheet = self.__nameSpreadsheet( {
			"/group/sphere" : "cube",
			"/group/cube" : "sphere",
		} )

		rename = GafferScene.Rename()
		rename["in"].setInput( group["out"] )
		rename["filter"].setInput( allFilter["out"] )
		rename["name"].setInput( spreadsheet["out"]["newName"] )

		self.assertSceneValid( rename["out"] )

		self.assertEqual( rename["out"].childNames( "/group" ), IECore.InternedStringVectorData( [ "cube", "sphere" ] ) )
		self.assertPathsEqual( rename["out"], "/group/cube", rename["in"], "/group/sphere" )
		self.assertPathHashesEqual( rename["out"], "/group/cube", rename["in"], "/group/sphere" )
		self.assertPathsEqual( rename["out"], "/group/sphere", rename["in"], "/group/cube" )
		self.assertPathHashesEqual( rename["out"], "/group/sphere", rename["in"], "/group/cube" )

		self.assertEqual( rename["out"].set( "setA" ).value, IECore.PathMatcher( [ "/group/cube" ] ) )
		self.assertEqual( rename["out"].set( "setB" ).value, IECore.PathMatcher( [ "/group/sphere" ] ) )

	def testRenameParentAndChild( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "setA" )

		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		self.assertEqual( group["out"].childNames( "/group" ), IECore.InternedStringVectorData( [ "sphere" ] ) )

		# Rename "sphere" to "cube" and "cube" to "sphere".

		allFilter = GafferScene.PathFilter()
		allFilter["paths"].setValue( IECore.StringVectorData( [ "/..." ] ) )

		spreadsheet = self.__nameSpreadsheet( {
			"/group/sphere" : "newSphere",
			"/group" : "newGroup",
		} )

		rename = GafferScene.Rename()
		rename["in"].setInput( group["out"] )
		rename["filter"].setInput( allFilter["out"] )
		rename["name"].setInput( spreadsheet["out"]["newName"] )

		self.assertSceneValid( rename["out"] )

		self.assertEqual( rename["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "newGroup" ] ) )
		self.assertPathsEqual( rename["out"], "/newGroup", rename["in"], "/group", checks = self.allPathChecks - { "childNames" } )
		self.assertPathHashesEqual( rename["out"], "/newGroup", rename["in"], "/group", checks = self.allPathChecks - { "childNames" } )

		self.assertEqual( rename["out"].childNames( "/newGroup" ), IECore.InternedStringVectorData( [ "newSphere" ] ) )
		self.assertPathsEqual( rename["out"], "/newGroup/newSphere", rename["in"], "/group/sphere" )
		self.assertPathHashesEqual( rename["out"], "/newGroup/newSphere", rename["in"], "/group/sphere" )

		self.assertEqual( rename["out"].set( "setA" ).value, IECore.PathMatcher( [ "/newGroup/newSphere" ] ) )

	def testRenameAncestorOfSetMembers( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "setA" )

		collectScenes = GafferScene.CollectScenes()
		collectScenes["in"].setInput( sphere["out"] )
		collectScenes["rootNames"].setValue( IECore.StringVectorData( [ "/a/b/c" ] ) )

		pathFilter = GafferScene.PathFilter()

		rename = GafferScene.Rename()
		rename["in"].setInput( collectScenes["out"] )
		rename["filter"].setInput( pathFilter["out"] )
		rename["name"].setValue( "z" )

		self.assertSceneValid( rename["out"] )

		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/a" ] ) )
		self.assertEqual( rename["out"].set( "setA" ).value, IECore.PathMatcher( [ "/z/b/c/sphere" ] ) )

		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/a/b" ] ) )
		self.assertEqual( rename["out"].set( "setA" ).value, IECore.PathMatcher( [ "/a/z/c/sphere" ] ) )

		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/a/b/c" ] ) )
		self.assertEqual( rename["out"].set( "setA" ).value, IECore.PathMatcher( [ "/a/b/z/sphere" ] ) )

	def testFilterMatchingRenamedLocation( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "setA" )

		innerGroup = GafferScene.Group( "InnerGroup" )
		innerGroup["name"].setValue( "inner" )
		innerGroup["in"][0].setInput( sphere["out"] )

		outerGroup = GafferScene.Group( "OuterGroup" )
		outerGroup["name"].setValue( "outer" )
		outerGroup["in"][0].setInput( innerGroup["out"] )

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [
			"/outer/inner",
			"/outer/newInner/sphere", # Exists in output scene, but _not_ input scene
		] ) )

		rename = GafferScene.Rename()
		rename["in"].setInput( outerGroup["out"] )
		rename["filter"].setInput( pathFilter["out"] )
		rename["name"].setValue( "newInner" )

		self.assertSceneValid( rename["out"] )

		self.assertPathsEqual( rename["out"], "/outer", rename["in"], "/outer", checks = self.allPathChecks - { "childNames" } )
		self.assertPathHashesEqual( rename["out"], "/outer", rename["in"], "/outer", checks = self.allPathChecks - { "childNames" } )

		self.assertPathsEqual( rename["out"], "/outer/newInner", rename["in"], "/outer/inner" )
		self.assertPathHashesEqual( rename["out"], "/outer/newInner", rename["in"], "/outer/inner" )

		self.assertPathsEqual( rename["out"], "/outer/newInner/sphere", rename["in"], "/outer/inner/sphere" )
		self.assertPathHashesEqual( rename["out"], "/outer/newInner/sphere", rename["in"], "/outer/inner/sphere" )

		self.assertEqual( rename["out"].set( "setA" ).value, IECore.PathMatcher( [ "/outer/newInner/sphere" ] ) )

	def testSetProcessing( self ) :

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( "${GAFFER_ROOT}/resources/gafferBot/caches/gafferBot.scc" )

		allFilter = GafferScene.PathFilter()
		allFilter["paths"].setValue( IECore.StringVectorData( [ "/..." ] ) )

		rename = GafferScene.Rename()
		rename["in"].setInput( reader["out"] )
		rename["filter"].setInput( allFilter["out"] )
		rename["name"].setValue( "weAreAllIndividuals" )

		# This is a fairly effective way of testing the thread-safety and determinism
		# of the set processing.
		setName = "ObjectType:MeshPrimitive"
		self.assertIn( setName, rename["out"].setNames() )
		hashes = set()
		for i in range( 0, 100 ) :
			Gaffer.ValuePlug.clearCache()
			Gaffer.ValuePlug.clearHashCache()
			hashes.add( rename["out"].setHash( setName ) )
			self.assertEqual( rename["out"].set( setName ).value.size(), rename["in"].set( setName ).value.size() )

		self.assertEqual( len( hashes ), 1 )

	def testMixedSetProcessing( self ) :

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( "${GAFFER_ROOT}/resources/gafferBot/caches/gafferBot.scc" )

		# Matches locations such that each leaf location will have a mixture of
		# renamed and non-renamed ancestors.
		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/.../*_GRP" ] ) )

		rename = GafferScene.Rename()
		rename["in"].setInput( reader["out"] )
		rename["filter"].setInput( pathFilter["out"] )
		rename["find"].setValue( "_GRP" )
		rename["replace"].setValue( "_GROUP" )

		setName = "ObjectType:MeshPrimitive"

		self.assertEqual(
			rename["out"].set( setName ).value,
			IECore.PathMatcher( [
				p.replace( "_GRP", "_GROUP" )
				for p in rename["in"].set( setName ).value.paths()
			] )
		)

		# Repeat, but with the filter also matching some locations
		# that won't end up being renamed (because the find/replace doesn't match).

		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/.../*_GRP", "/.../*_REN" ] ) )

		self.assertEqual(
			rename["out"].set( setName ).value,
			IECore.PathMatcher( [
				p.replace( "_GRP", "_GROUP" )
				for p in rename["in"].set( setName ).value.paths()
			] )
		)

		# Now rename those locations too.

		rename["find"].setValue( "(_GRP|_REN)" )
		rename["replace"].setValue( "{1}R" )
		rename["useRegularExpressions"].setValue( True )

		self.assertEqual(
			rename["out"].set( setName ).value,
			IECore.PathMatcher( [
				p.replace( "_GRP", "_GRPR" ).replace( "_REN", "_RENR" )
				for p in rename["in"].set( setName ).value.paths()
			] )
		)

		# All the set members were leaf objects. Try the same
		# with a set consisting of some leaf and some non-leaf
		# members.

		setFilter = GafferScene.PathFilter()
		setFilter["paths"].setValue( IECore.StringVectorData( [
			"/GAFFERBOT/C_torso_GRP/C_head_GRP",
			"/GAFFERBOT/C_torso_GRP/L_legUpper_GRP/L_legLower_GRP",
			"/GAFFERBOT/C_torso_GRP/L_armUpper_GRP",
			"/GAFFERBOT/C_torso_GRP/L_armUpper_GRP/L_armUpper_CPT"
		] ) )

		setNode = GafferScene.Set()
		setNode["in"].setInput( reader["out"] )
		setNode["filter"].setInput( setFilter["out"] )
		setNode["name"].setValue( setName )
		setNode["mode"].setValue( setNode.Mode.Add )
		rename["in"].setInput( setNode["out"] )

		self.assertEqual( rename["in"].set( setName ).value.size(), reader["out"].set( setName ).value.size() + 4 )

		self.assertEqual(
			rename["out"].set( setName ).value,
			IECore.PathMatcher( [
				p.replace( "_GRP", "_GRPR" ).replace( "_REN", "_RENR" )
				for p in rename["in"].set( setName ).value.paths()
			] )
		)

		# Repeat, but without the original leaf set members.

		setNode["mode"].setValue( setNode.Mode.Create )
		self.assertEqual( rename["in"].set( setName ).value.size(), 4 )

		self.assertEqual(
			rename["out"].set( setName ).value,
			IECore.PathMatcher( [
				p.replace( "_GRP", "_GRPR" ).replace( "_REN", "_RENR" )
				for p in rename["in"].set( setName ).value.paths()
			] )
		)

		# And then repeat but without renaming leaf locations.

		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/.../*_GRP" ] ) )
		self.assertEqual(
			rename["out"].set( setName ).value,
			IECore.PathMatcher( [
				p.replace( "_GRP", "_GRPR" )
				for p in rename["in"].set( setName ).value.paths()
			] )
		)

	def testNameProcessing( self ) :

		sphere = GafferScene.Sphere()

		allFilter = GafferScene.PathFilter()
		allFilter["paths"].setValue( IECore.StringVectorData( [ "/*" ] ) )

		rename = GafferScene.Rename()
		rename["in"].setInput( sphere["out"] )
		rename["filter"].setInput( allFilter["out"] )

		def outputName( inputName, **kw ) :

			sphere["name"].setValue( inputName )

			for plug in Gaffer.ValuePlug.InputRange( rename ) :
				if plug.getInput() is None :
					plug.setToDefault()

			for name, value in kw.items() :
				rename[name].setValue( value )

			return str( rename["out"].childNames( "/" )[0] )

		def assertRename( inputName, expectedOutputName, **kw ) :

			self.assertEqual( outputName( inputName, **kw ), expectedOutputName )
			self.assertSceneValid( rename["out"] )

		# If `name` is specified, then all other options are ignored.

		assertRename( "sphere", "ball", name = "ball" )
		assertRename( "sphere", "ball", name = "ball", deletePrefix = "sph" )
		assertRename( "sphere", "ball", name = "ball", addPrefix = "aaa" )
		assertRename( "sphere", "ball", name = "ball", deleteSuffix = "ere" )
		assertRename( "sphere", "ball", name = "ball", addSuffix = "zzz" )
		assertRename( "sphere", "ball", name = "ball", find = "s", replace = "t" )

		# Prefixes can be added and removed.

		assertRename( "bigSphereRolling", "Sphere", deletePrefix = "big", deleteSuffix = "Rolling" )
		assertRename( "bigBallRolling", "Ball", deletePrefix = "big", deleteSuffix = "Rolling" )
		assertRename( "bigSphereRolling", "littleSphereBouncing", deletePrefix = "big", addPrefix = "little", deleteSuffix = "Rolling", addSuffix = "Bouncing" )
		assertRename( "bigBallRolling", "littleBallBouncing", deletePrefix = "big", addPrefix = "little", deleteSuffix = "Rolling", addSuffix = "Bouncing" )

		# Strings can be found and replaced.

		assertRename( "bigSphereRolling", "bigBallRolling", find = "Sphere", replace = "Ball" )
		assertRename( "littleSphereBouncing", "littleBallBouncing", find = "Sphere", replace = "Ball" )
		assertRename( "ababab", "acacac", find = "b", replace = "c" )

		# Strings can be found and replaced using regular expressions.

		assertRename( "01_sphere10", "01_sphere10", find = r"[0-9]{2}", replace = "" )
		assertRename( "01_sphere10", "_sphere", find = r"[0-9]{2}", replace = "", useRegularExpressions = True )
		assertRename( "a_b_c_d_a", "a_z_z_z_a", find = r"[b-d]", replace = "z", useRegularExpressions = True )

		# You can reference captured groups in the replacement string, using
		# Python's formatting syntax (which is the same as `std::format`).

		assertRename( "a_b_c", "c_b_a", find = r"(.+)_(.+)_(.+)", replace = "{3}_{2}_{1}", useRegularExpressions = True )
		assertRename( "sphere10", "sphere", find = r"[[:digit:]]+", replace = "", useRegularExpressions = True )
		assertRename( "sphere10", "sphere10", find = r"[[:digit:]]{3}", replace = "", useRegularExpressions = True )
		assertRename( "sphere10", "sphere0010", find = r"[[:digit:]]+", replace = "{:0>4}", useRegularExpressions = True )
		assertRename( "ab", "ab", find = "(a)(b)", replace = "{0}", useRegularExpressions = True )

		# If you reference more capture groups than there are, then you
		# are greeted by an exception.

		with self.assertRaisesRegex(
			Gaffer.ProcessException,
			r".*Error applying replacement `\{2\}` : argument not found"
		) :
			outputName( "abc", find = "(a)", replace = "{2}", useRegularExpressions = True )

		# Likewise, if you try to use a type-specific formatter.

		with self.assertRaisesRegex(
			Gaffer.ProcessException,
			r".*Error applying replacement `\{1:\+\}` : format specifier requires numeric argument"
		) :
			outputName( "abc", find = "(a)", replace = "{1:+}", useRegularExpressions = True )

		# If the regular expression doesn't match anything, then the name
		# should be unchanged.

		assertRename( "abc", "abc", find = "x", replace = "y", useRegularExpressions = True )

		# If deletion/replacement yield an empty name, then we alert the
		# user by renaming to "invalidName". We can't be having empty names.

		assertRename( "aaa", "invalidName", deletePrefix = "aaa" )
		assertRename( "aaa", "invalidName", deleteSuffix = "aaa" )
		assertRename( "aaa", "invalidName", deletePrefix = "aa", deleteSuffix = "a" )
		assertRename( "aaa", "invalidName", find = "a", replace = "" )

		# But if there's no deletion/replacement and the `name` plug is
		# simply empty, we take that to be a no-op. This keeps the node
		# acting as a pass-through until the plugs are at non-default values.

		assertRename( "aaa", "aaa", name = "" )

	def testSpreadsheetWithDisabledCell( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "setA" )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		spreadsheet = self.__nameSpreadsheet( {
			"/sphere" : "newSphere",
		} )

		rename = GafferScene.Rename()
		rename["in"].setInput( sphere["out"] )
		rename["filter"].setInput( sphereFilter["out"] )
		rename["name"].setInput( spreadsheet["out"]["newName"] )

		self.assertSceneValid( rename["out"] )
		self.assertEqual( rename["out"].childNames( "/" )[0], "newSphere" )

		spreadsheet["rows"][1]["enabled"].setValue( False )
		self.assertSceneValid( rename["out"] )
		self.assertEqual( rename["out"].childNames( "/" )[0], "sphere" )

		spreadsheet["rows"].defaultRow()["cells"]["newName"]["value"].setValue( "spreadsheetDefault" )
		self.assertSceneValid( rename["out"] )
		self.assertEqual( rename["out"].childNames( "/" )[0], "spreadsheetDefault" )

		spreadsheet["rows"][1]["enabled"].setValue( True )
		self.assertSceneValid( rename["out"] )
		self.assertEqual( rename["out"].childNames( "/" )[0], "newSphere" )

		spreadsheet["rows"][1]["cells"]["newName"]["enabled"].setValue( False )
		self.assertSceneValid( rename["out"] )
		self.assertEqual( rename["out"].childNames( "/" )[0], "spreadsheetDefault" )

		spreadsheet["rows"].defaultRow()["cells"]["newName"]["value"].setValue( "" )
		self.assertSceneValid( rename["out"] )
		self.assertEqual( rename["out"].childNames( "/" )[0], "sphere" )

		spreadsheet["rows"][1]["cells"]["newName"]["enabled"].setValue( True )
		self.assertSceneValid( rename["out"] )
		self.assertEqual( rename["out"].childNames( "/" )[0], "newSphere" )

	def testSetPassThroughWithCacheEviction( self ) :

		# This reproduces a deadlock that was once triggered by performing the
		# Legacy policy compute for `sphere.out.set` behind the lock for the
		# TaskCollaboration compute on `rename.out.set`. The test doesn't
		# assert anything, because we are just happy if it completes at all.

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "setA" )

		rename = GafferScene.Rename()
		rename["in"].setInput( sphere["out"] )

		rename["out"].set( "setA" )
		Gaffer.ValuePlug.clearCache()
		rename["out"].set( "setA" )

if __name__ == "__main__":
	unittest.main()
