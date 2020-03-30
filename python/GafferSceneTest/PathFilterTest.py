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
import GafferTest
import GafferScene
import GafferSceneTest

class PathFilterTest( GafferSceneTest.SceneTestCase ) :

	def testConstruct( self ) :

		f = GafferScene.PathFilter()

	def testAffects( self ) :

		f = GafferScene.PathFilter()
		cs = GafferTest.CapturingSlot( f.plugDirtiedSignal() )
		f["paths"].setValue( IECore.StringVectorData( [ "/a" ] ) )
		self.assertTrue( f["out"] in [ x[0] for x in cs ] )

	def testMatch( self ) :

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/a", "/red", "/b/c/d" ] ) )

		for path, result in [
			( "/a",  IECore.PathMatcher.Result.ExactMatch ),
			( "/red", IECore.PathMatcher.Result.ExactMatch ),
			( "/re", IECore.PathMatcher.Result.NoMatch ),
			( "/redThing", IECore.PathMatcher.Result.NoMatch ),
			( "/b/c/d", IECore.PathMatcher.Result.ExactMatch ),
			( "/c", IECore.PathMatcher.Result.NoMatch ),
			( "/a/b", IECore.PathMatcher.Result.AncestorMatch ),
			( "/blue", IECore.PathMatcher.Result.NoMatch ),
			( "/b/c", IECore.PathMatcher.Result.DescendantMatch ),
		] :

			with Gaffer.Context() as c :
				c["scene:path"] = GafferScene.ScenePlug.stringToPath( path )
				self.assertEqual( f["out"].getValue(), int( result ) )

	def testNullPaths( self ) :

		f = GafferScene.PathFilter()
		with Gaffer.Context() as c :
			c["scene:path"] = IECore.InternedStringVectorData( [ "a" ] )
			self.assertEqual( f["out"].getValue(), int( IECore.PathMatcher.Result.NoMatch ) )

	def testInputsAccepted( self ) :

		f = GafferScene.PathFilter()
		p = Gaffer.StringVectorDataPlug( direction = Gaffer.Plug.Direction.Out, defaultValue = IECore.StringVectorData() )
		self.failUnless( f["paths"].acceptsInput( p ) )

		self.failUnless( f["paths"].getFlags( Gaffer.Plug.Flags.Serialisable ) )

	def testBox( self ) :

		s = Gaffer.ScriptNode()

		s["p"] = GafferScene.Plane()
		s["a"] = GafferScene.Attributes()
		s["a"]["in"].setInput( s["p"]["out"] )

		s["f"] = GafferScene.PathFilter()
		s["a"]["filter"].setInput( s["f"]["out"] )

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["a"] ] ) )

	def testCopyPaste( self ) :

		s = Gaffer.ScriptNode()

		s["f"] = GafferScene.PathFilter()
		s["a"] = GafferScene.Attributes()
		s["a"]["filter"].setInput( s["f"]["out"] )

		ss = s.serialise( s, Gaffer.StandardSet( [ s["a"] ] ) )

		s.execute( ss )

		self.assertTrue( isinstance( s["a1"], GafferScene.Attributes ) )
		self.assertEqual( s["a1"]["filter"].getInput(), None )

	def testPathPlugPromotion( self ) :

		s = Gaffer.ScriptNode()

		s["f"] = GafferScene.PathFilter()
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["f"] ] ) )

		p = Gaffer.PlugAlgo.promote( b["f"]["paths"] )
		p.setValue( IECore.StringVectorData( [ "/a", "/red", "/b/c/d" ] ) )

		for path, result in [
			( "/a",  IECore.PathMatcher.Result.ExactMatch ),
			( "/red", IECore.PathMatcher.Result.ExactMatch ),
			( "/re", IECore.PathMatcher.Result.NoMatch ),
			( "/redThing", IECore.PathMatcher.Result.NoMatch ),
			( "/b/c/d", IECore.PathMatcher.Result.ExactMatch ),
			( "/c", IECore.PathMatcher.Result.NoMatch ),
			( "/a/b", IECore.PathMatcher.Result.AncestorMatch ),
			( "/blue", IECore.PathMatcher.Result.NoMatch ),
			( "/b/c", IECore.PathMatcher.Result.DescendantMatch ),
		] :

			with Gaffer.Context() as c :
				c["scene:path"] = GafferScene.ScenePlug.stringToPath( path )
				self.assertEqual( b["f"]["out"].getValue(), int( result ) )

	def testPathPlugExpression( self ) :

		s = Gaffer.ScriptNode()

		s["f"] = GafferScene.PathFilter()

		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			"import IECore\n"
			"passName = context.get( 'passName', '' )\n"
			"if passName == 'foreground' :\n"
			"	paths = IECore.StringVectorData( [ '/a' ] )\n"
			"else :\n"
			"	paths = IECore.StringVectorData( [ '/b' ] )\n"
			"parent['f']['paths'] = paths"
		)

		with Gaffer.Context() as c :
			c["scene:path"] = IECore.InternedStringVectorData( [ "a" ])
			self.assertEqual( s["f"]["out"].getValue(), IECore.PathMatcher.Result.NoMatch )
			c["passName"] = "foreground"
			self.assertEqual( s["f"]["out"].getValue(), IECore.PathMatcher.Result.ExactMatch )

	def testEnabled( self ) :

		f = GafferScene.PathFilter()
		self.assertTrue( f.enabledPlug().isSame( f["enabled"] ) )
		self.assertTrue( isinstance( f.enabledPlug(), Gaffer.BoolPlug ) )
		self.assertEqual( f.enabledPlug().defaultValue(), True )
		self.assertEqual( f.enabledPlug().getValue(), True )
		self.assertEqual( f.correspondingInput( f["out"] ), None )

		f["paths"].setValue( IECore.StringVectorData( [ "/a" ] ) )

		with Gaffer.Context() as c :

			c["scene:path"] = IECore.InternedStringVectorData( [ "a" ] )
			self.assertEqual( f["out"].getValue(), IECore.PathMatcher.Result.ExactMatch )

			f["enabled"].setValue( False )
			self.assertEqual( f["out"].getValue(), IECore.PathMatcher.Result.NoMatch )

		a = f.affects( f["enabled"] )
		self.assertTrue( f["out"] in a )

	def testEmptyStringMatchesNothing( self ) :

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "" ] ) )

		with Gaffer.Context() as c :

			c["scene:path"] = IECore.InternedStringVectorData( [ "a" ] )
			self.assertEqual( f["out"].getValue(), IECore.PathMatcher.Result.NoMatch )

	def testRoots( self ) :

		#  /outerGroup
		#     /sphere
		#     /cube
		#     /innerGroup/
		#         /sphere
		#         /cube
		#  /sphere

		sphere = GafferScene.Sphere()
		cube = GafferScene.Cube()

		innerGroup = GafferScene.Group()
		innerGroup["in"][0].setInput( sphere["out"] )
		innerGroup["in"][1].setInput( cube["out"] )
		innerGroup["name"].setValue( "innerGroup" )

		outerGroup = GafferScene.Group()
		outerGroup["in"][0].setInput( sphere["out"] )
		outerGroup["in"][1].setInput( cube["out"] )
		outerGroup["in"][2].setInput( innerGroup["out"] )
		outerGroup["name"].setValue( "outerGroup" )

		parent = GafferScene.Parent()
		parent["in"].setInput( outerGroup["out"] )
		parent["children"][0].setInput( sphere["out"] )
		parent["parent"].setValue( "/" )

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		def assertMatchingPaths( scene, filter, expectedPaths ) :

			matchingPaths = IECore.PathMatcher()
			GafferScene.SceneAlgo.matchingPaths( filter, scene, matchingPaths )
			self.assertEqual( set( matchingPaths.paths() ), expectedPaths )

		assertMatchingPaths(
			parent["out"], pathFilter["out"],
			{ "/sphere" }
		)

		rootsFilter = GafferScene.PathFilter()
		pathFilter["roots"].setInput( rootsFilter["out"] )

		assertMatchingPaths(
			parent["out"], pathFilter["out"],
			set()
		)

		rootsFilter["paths"].setValue( IECore.StringVectorData( [ "/" ] ) )
		assertMatchingPaths(
			parent["out"], pathFilter["out"],
			{ "/sphere" }
		)

		rootsFilter["paths"].setValue( IECore.StringVectorData( [ "/", "/outerGroup" ] ) )
		assertMatchingPaths(
			parent["out"], pathFilter["out"],
			{ "/sphere", "/outerGroup/sphere" }
		)

		rootsFilter["paths"].setValue( IECore.StringVectorData( [ "/", "/outerGroup", "/outerGroup/innerGroup" ] ) )
		assertMatchingPaths(
			parent["out"], pathFilter["out"],
			{ "/sphere", "/outerGroup/sphere", "/outerGroup/innerGroup/sphere" }
		)

		rootsFilter["paths"].setValue( IECore.StringVectorData( [ "/outerGroup", "/outerGroup/innerGroup" ] ) )
		assertMatchingPaths(
			parent["out"], pathFilter["out"],
			{ "/outerGroup/sphere", "/outerGroup/innerGroup/sphere" }
		)

	def testSpecificRootsMatches( self ) :

		rootsFilter = GafferScene.PathFilter()
		rootsFilter["paths"].setValue( IECore.StringVectorData( [ "/", "/nested/root" ] ) )

		pathFilter = GafferScene.PathFilter()
		pathFilter["roots"].setInput( rootsFilter["out"] )
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/matchLocation" ] ) )

		with Gaffer.Context() as c :

			for path, expectedResult in [

				( "/", IECore.PathMatcher.Result.DescendantMatch ),
				( "/nested", IECore.PathMatcher.Result.DescendantMatch ),
				( "/nested/root", IECore.PathMatcher.Result.DescendantMatch ),
				( "/nested/root/matchLocation", IECore.PathMatcher.Result.ExactMatch ),
				( "/nested/root/matchLocation/childLocation", IECore.PathMatcher.Result.AncestorMatch ),
				( "/matchLocation", IECore.PathMatcher.Result.ExactMatch ),
				( "/matchLocation/childLocation", IECore.PathMatcher.Result.AncestorMatch ),
				( "/matchLocation/childLocation/grandChildLocation", IECore.PathMatcher.Result.AncestorMatch ),

			] :

				c["scene:path"] = GafferScene.ScenePlug.stringToPath( path )
				self.assertEqual( pathFilter["out"].getValue(), expectedResult )

	def testRootsWithEmptyPaths( self ) :

		rootsFilter = GafferScene.PathFilter()
		rootsFilter["paths"].setValue( IECore.StringVectorData( [ "/path/to/root" ] ) )

		pathFilter = GafferScene.PathFilter()
		pathFilter["roots"].setInput( rootsFilter["out"] )

		with Gaffer.Context() as c :

			c["scene:path"] = IECore.InternedStringVectorData( [ "path", "to" ] )
			self.assertEqual( pathFilter["out"].getValue(), IECore.PathMatcher.Result.NoMatch )

	def testRootsWithEllipsis( self ) :

		rootsFilter = GafferScene.PathFilter()

		pathFilter = GafferScene.PathFilter()
		pathFilter["roots"].setInput( rootsFilter["out"] )

		# Regular roots, paths with ellipsis

		rootsFilter["paths"].setValue( IECore.StringVectorData( [ "/", "/nested/root" ] ) )
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/.../matchLocation" ] ) )

		with Gaffer.Context() as c :

			for path, expectedResult in [

				( "/", IECore.PathMatcher.Result.DescendantMatch ),
				( "/nested", IECore.PathMatcher.Result.DescendantMatch ),
				( "/nested/root", IECore.PathMatcher.Result.DescendantMatch ),
				( "/nested/root/matchLocation", IECore.PathMatcher.Result.ExactMatch | IECore.PathMatcher.Result.DescendantMatch ),
				( "/nested/root/matchLocation/childLocation", IECore.PathMatcher.Result.AncestorMatch | IECore.PathMatcher.Result.DescendantMatch ),
				( "/nested/root/anything", IECore.PathMatcher.Result.DescendantMatch ),
				( "/matchLocation", IECore.PathMatcher.Result.ExactMatch | IECore.PathMatcher.Result.DescendantMatch ),
				( "/matchLocation/childLocation", IECore.PathMatcher.Result.AncestorMatch | IECore.PathMatcher.Result.DescendantMatch ),
				( "/matchLocation/childLocation/grandChildLocation", IECore.PathMatcher.Result.AncestorMatch | IECore.PathMatcher.Result.DescendantMatch ),
				( "/matchLocation/anything", IECore.PathMatcher.Result.AncestorMatch | IECore.PathMatcher.Result.DescendantMatch ),

			] :

				c["scene:path"] = GafferScene.ScenePlug.stringToPath( path )
				self.assertEqual( pathFilter["out"].getValue(), expectedResult )

		# Regular paths, roots with ellipsis

		rootsFilter["paths"].setValue( IECore.StringVectorData( [ "/", "/.../nestedRoot" ] ) )
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/matchLocation" ] ) )

		with Gaffer.Context() as c :

			for path, expectedResult in [

				( "/", IECore.PathMatcher.Result.DescendantMatch ),
				( "/nestedRoot", IECore.PathMatcher.Result.DescendantMatch ),
				( "/nestedRoot/matchLocation", IECore.PathMatcher.Result.ExactMatch | IECore.PathMatcher.Result.DescendantMatch ),
				( "/nestedRoot/matchLocation/childLocation", IECore.PathMatcher.Result.AncestorMatch | IECore.PathMatcher.Result.DescendantMatch ),
				( "/deeply/nestedRoot", IECore.PathMatcher.Result.DescendantMatch ),
				( "/deeply/nestedRoot/matchLocation", IECore.PathMatcher.Result.ExactMatch | IECore.PathMatcher.Result.DescendantMatch ),
				( "/matchLocation", IECore.PathMatcher.Result.ExactMatch | IECore.PathMatcher.Result.DescendantMatch ),
				( "/matchLocation/childLocation", IECore.PathMatcher.Result.AncestorMatch | IECore.PathMatcher.Result.DescendantMatch ),
				( "/matchLocation/childLocation/grandChildLocation", IECore.PathMatcher.Result.AncestorMatch | IECore.PathMatcher.Result.DescendantMatch ),

			] :

				c["scene:path"] = GafferScene.ScenePlug.stringToPath( path )
				self.assertEqual( pathFilter["out"].getValue(), expectedResult )

if __name__ == "__main__":
	unittest.main()
