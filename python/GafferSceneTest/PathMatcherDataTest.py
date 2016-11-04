##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

class PathMatcherDataTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		d = GafferScene.PathMatcherData()
		self.assertEqual( d.value, GafferScene.PathMatcher() )

		d.value.addPath( "/a" )
		self.assertEqual( d.value, GafferScene.PathMatcher( [ "/a" ] ) )

		dd = d.copy()
		self.assertEqual( d.value, GafferScene.PathMatcher( [ "/a" ] ) )
		self.assertEqual( dd.value, GafferScene.PathMatcher( [ "/a" ] ) )

		dd.value.addPath( "/b" )
		self.assertEqual( d.value, GafferScene.PathMatcher( [ "/a" ] ) )
		self.assertEqual( dd.value, GafferScene.PathMatcher( [ "/a", "/b" ] ) )

	def testHash( self ) :

		d = GafferScene.PathMatcherData()

		h = []
		h.append( d.hash() )
		self.assertNotEqual( h[0], IECore.MurmurHash() )

		d.value.addPath( "/" )
		h.append( d.hash() )
		self.assertNotEqual( h[1], h[0] )

		d.value.removePath( "/" )
		h.append( d.hash() )
		self.assertEqual( h[2], h[0] )

		d.value.addPath( "/c/d" )
		h.append( d.hash() )
		self.assertNotEqual( h[3], h[2] )

		d.value.addPath( "/c" )
		h.append( d.hash() )
		self.assertNotEqual( h[4], h[3] )

	def testHierarchyAffectsHash( self ) :

		d1 = GafferScene.PathMatcherData()
		d1.value.addPath( "/b")
		d1.value.addPath( "/b/a")

		d2 = GafferScene.PathMatcherData()
		d2.value.addPath( "/a")
		d2.value.addPath( "/b")

		self.assertNotEqual( d1.hash(), d2.hash() )

	def testRepr( self ) :

		d1 = GafferScene.PathMatcherData(
			GafferScene.PathMatcher()
		)
		d2 = GafferScene.PathMatcherData(
			GafferScene.PathMatcher( [
				"/a/b",
				"/a/*"
			] )
		)

		d1c = eval( repr( d1 ) )
		d2c = eval( repr( d2 ) )

		self.assertEqual( d1, d1c )
		self.assertEqual( d2, d2c )

if __name__ == "__main__":
	unittest.main()
