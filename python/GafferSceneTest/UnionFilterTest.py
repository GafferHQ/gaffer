##########################################################################
#
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

import os
import unittest

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class UnionFilterTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		f1 = GafferScene.PathFilter()
		f1["paths"].setValue( IECore.StringVectorData( [
			"/a/b/c",
		] ) )

		f2 = GafferScene.PathFilter()
		f2["paths"].setValue( IECore.StringVectorData( [
			"/a/b/c/e/f/g",
		] ) )

		u = GafferScene.UnionFilter()
		self.assertEqual( u["out"].getValue(), IECore.PathMatcher.Result.NoMatch )

		h1 = u["out"].hash()

		u["in"][0].setInput( f1["out"] )
		h2 = u["out"].hash()
		self.assertNotEqual( h1, h2 )

		for path in [
			"/a",
			"/b",
			"/a/b",
			"/a/b/c",
			"/a/b/c/d",
		] :
			with Gaffer.Context() as c :
				c["scene:path"] = GafferScene.ScenePlug.stringToPath( path )
				self.assertEqual( u["out"].getValue(), f1["out"].getValue() )

		u["in"][1].setInput( f2["out"] )
		h3 = u["out"].hash()
		self.assertNotEqual( h2, h3 )

		for path, result in [
			( "/a", IECore.PathMatcher.Result.DescendantMatch ),
			( "/b", IECore.PathMatcher.Result.NoMatch ),
			( "/a/b", IECore.PathMatcher.Result.DescendantMatch ),
			( "/a/b/c", IECore.PathMatcher.Result.DescendantMatch | IECore.PathMatcher.Result.ExactMatch ),
			( "/a/b/c/d", IECore.PathMatcher.Result.AncestorMatch ),
			( "/a/b/c/e", IECore.PathMatcher.Result.AncestorMatch | IECore.PathMatcher.Result.DescendantMatch ),
			( "/a/b/c/e/f/g", IECore.PathMatcher.Result.AncestorMatch | IECore.PathMatcher.Result.ExactMatch ),
			( "/a/b/c/e/f/g/h", IECore.PathMatcher.Result.AncestorMatch ),
		] :
			with Gaffer.Context() as c :
				c["scene:path"] = GafferScene.ScenePlug.stringToPath( path )
				self.assertEqual( u["out"].getValue(), int( result ) )

		f2["paths"].setValue( IECore.StringVectorData( [
			"/a/b",
		] ) )

		h4 = u["out"].hash()
		self.assertNotEqual( h3, h4 )

	def testDirtiedSignal( self ) :

		u = GafferScene.UnionFilter( "u" )
		f1 = GafferScene.PathFilter( "f" )

		cs = GafferTest.CapturingSlot( u.plugDirtiedSignal() )

		u["in"][0].setInput( f1["out"] )

		self.assertEqual( [ x[0] for x in cs if x[0].direction() == x[0].Direction.Out ], [ u["out"] ] )

		del cs[:]

		f1["paths"].setValue( IECore.StringVectorData( [ "/a" ] ) )

		self.assertEqual( [ x[0] for x in cs if x[0].direction() == x[0].Direction.Out ], [ u["out"] ] )

	def testAcceptsInput( self ) :

		f = GafferScene.PathFilter()
		n = Gaffer.Node()
		n["out"] = f["out"].createCounterpart( "out", Gaffer.Plug.Direction.Out )

		u = GafferScene.UnionFilter()
		self.assertTrue( u["in"][0].acceptsInput( n["out"] ) )

	def testSceneAffects( self ) :

		p = GafferScene.Plane()
		s = GafferScene.Set()
		s["in"].setInput( p["out"] )

		a = GafferScene.StandardAttributes()
		a["in"].setInput( s["out"] )

		f = GafferScene.UnionFilter()
		a["filter"].setInput( f["out"] )

		pf = GafferScene.PathFilter()
		f["in"][0].setInput( pf["out"] )

		# PathFilter isn't sensitive to scene changes, so we shouldn't get
		# any dirtiness signalled for the attributes.

		cs = GafferTest.CapturingSlot( a.plugDirtiedSignal() )

		s["paths"].setValue( IECore.StringVectorData( [ "/p*" ] ) )

		self.assertTrue( a["out"]["set"] in set( [ c[0] for c in cs ] ) )
		self.assertTrue( a["out"]["attributes"] not in set( [ c[0] for c in cs ] ) )

		# Add on a SetFilter though, and we should get dirtiness signalled for
		# the attributes.

		sf = GafferScene.SetFilter()
		f["in"][1].setInput( sf["out"] )

		cs = GafferTest.CapturingSlot( a.plugDirtiedSignal() )

		s["paths"].setValue( IECore.StringVectorData( [ "/pla*" ] ) )

		self.assertTrue( a["out"]["set"] in set( [ c[0] for c in cs ] ) )
		self.assertTrue( a["out"]["attributes"] in set( [ c[0] for c in cs ] ) )

	def testAcceptsDots( self ) :

		sf = GafferScene.SetFilter()
		dot = Gaffer.Dot()
		dot.setup( sf["out"] )
		dot["in"].setInput( sf["out"] )

		uf = GafferScene.UnionFilter()
		self.assertTrue( uf["in"][0].acceptsInput( dot["out"] ) )

		dot["in"].setInput( None )
		self.assertTrue( uf["in"][0].acceptsInput( dot["out"] ) )

		uf["in"][0].setInput( dot["out"] )
		dot["in"].setInput( sf["out"] )

		a = GafferTest.AddNode()
		dot2 = Gaffer.Dot()
		dot2.setup( a["sum"] )
		dot2["in"].setInput( a["sum"] )

		self.assertFalse( uf["in"][0].acceptsInput( dot2["out"] ) )

	def testReferencePromotedPlug( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["f"] = GafferScene.UnionFilter()
		p = Gaffer.PlugAlgo.promote( s["b"]["f"]["in"][0] )
		p.setName( "p" )

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		s["f"] = GafferScene.PathFilter()

		s["r"]["p"].setInput( s["f"]["out"] )

	def testDisabling( self ) :

		pathFilterA = GafferScene.PathFilter()
		pathFilterB = GafferScene.PathFilter()

		pathFilterA["paths"].setValue( IECore.StringVectorData( [ "/a" ] ) )
		pathFilterB["paths"].setValue( IECore.StringVectorData( [ "/b" ] ) )

		unionFilter = GafferScene.UnionFilter()
		unionFilter["in"][0].setInput( pathFilterA["out"] )
		unionFilter["in"][1].setInput( pathFilterB["out"] )

		self.assertTrue( unionFilter.correspondingInput( unionFilter["out"] ).isSame( unionFilter["in"][0] ) )

		with Gaffer.Context() as c :
			c["scene:path"] = IECore.InternedStringVectorData( [ "a" ] )
			self.assertEqual( unionFilter["out"].getValue(), IECore.PathMatcher.Result.ExactMatch )
			c["scene:path"] = IECore.InternedStringVectorData( [ "b" ] )
			self.assertEqual( unionFilter["out"].getValue(), IECore.PathMatcher.Result.ExactMatch )

		unionFilter["enabled"].setValue( False )

		with Gaffer.Context() as c :
			c["scene:path"] = IECore.InternedStringVectorData( [ "a" ] )
			self.assertEqual( unionFilter["out"].getValue(), IECore.PathMatcher.Result.ExactMatch )
			c["scene:path"] = IECore.InternedStringVectorData( [ "b" ] )
			self.assertEqual( unionFilter["out"].getValue(), IECore.PathMatcher.Result.NoMatch )

if __name__ == "__main__":
	unittest.main()
