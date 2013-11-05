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
		self.assertEqual( u["match"].getValue(), GafferScene.Filter.Result.NoMatch )
	
		h1 = u["match"].hash()
		
		u["in"][0].setInput( f1["match"] )
		h2 = u["match"].hash()
		self.assertNotEqual( h1, h2 )
		
		for path in [
			"/a",
			"/b",
			"/a/b",
			"/a/b/c",
			"/a/b/c/d",
		] :
			with Gaffer.Context() as c :
				c["scene:path"] = IECore.InternedStringVectorData( path[1:].split( "/" ) )
 				self.assertEqual( u["match"].getValue(), f1["match"].getValue() )

		u["in"][1].setInput( f2["match"] )
		h3 = u["match"].hash()
		self.assertNotEqual( h2, h3 )
		
		for path, result in [
			( "/a", u.Result.DescendantMatch ),
			( "/b", u.Result.NoMatch ),
			( "/a/b", u.Result.DescendantMatch ),
			( "/a/b/c", u.Result.DescendantMatch | u.Result.ExactMatch ),
			( "/a/b/c/d", u.Result.AncestorMatch ),
			( "/a/b/c/e", u.Result.AncestorMatch | u.Result.DescendantMatch ),
			( "/a/b/c/e/f/g", u.Result.AncestorMatch | u.Result.ExactMatch ),
			( "/a/b/c/e/f/g/h", u.Result.AncestorMatch ),
		] :
			with Gaffer.Context() as c :
				c["scene:path"] = IECore.InternedStringVectorData( path[1:].split( "/" ) )
 				self.assertEqual( u["match"].getValue(), int( result ) )

		f2["paths"].setValue( IECore.StringVectorData( [
			"/a/b",
		] ) )
		
		h4 = u["match"].hash()
		self.assertNotEqual( h3, h4 )
		
	def testDirtiedSignal( self ) :
	
		u = GafferScene.UnionFilter( "u" )
		f1 = GafferScene.PathFilter( "f" )
		
		cs = GafferTest.CapturingSlot( u.plugDirtiedSignal() )
		
		u["in"][0].setInput( f1["match"] )
		
		self.assertEqual( [ x[0].fullName() for x in cs if x[0].direction() == x[0].Direction.Out ], [ "u.match" ] )
		
		del cs[:]
		
		f1["paths"].setValue( IECore.StringVectorData( [ "/a" ] ) )
		
		self.assertEqual( [ x[0].fullName() for x in cs if x[0].direction() == x[0].Direction.Out ], [ "u.match" ] )
		
	def testAcceptsInput( self ) :
	
		f = GafferScene.PathFilter()
		n = Gaffer.Node()
		n["match"] = f["match"].createCounterpart( "match", Gaffer.Plug.Direction.Out )
		
		u = GafferScene.UnionFilter()
		self.assertFalse( u["in"][0].acceptsInput( n["match"] ) )
		
if __name__ == "__main__":
	unittest.main()
