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
#      * Neither the name of Cinesite VFX Ltd. nor the names of
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

import GafferSceneTest
import GafferScene

class VisibleSetTest( GafferSceneTest.SceneTestCase ) :

	def testExpansions( self ) :

		e = GafferScene.VisibleSet()
		e.expansions = IECore.PathMatcher( [ "/a", "/b", "/a/b", "/b/c", "/c/d/e" ] )

		self.assertEqual( e.match( "/a" ), IECore.PathMatcher.Result.ExactMatch )
		self.assertEqual( e.match( "/b" ), IECore.PathMatcher.Result.ExactMatch )
		self.assertEqual( e.match( "/a/b" ), IECore.PathMatcher.Result.ExactMatch )
		self.assertEqual( e.match( "/b/c" ), IECore.PathMatcher.Result.ExactMatch )
		self.assertEqual( e.match( "/c/d/e" ), IECore.PathMatcher.Result.ExactMatch )

		self.assertEqual( e.match( "/" ), IECore.PathMatcher.Result.NoMatch )
		self.assertEqual( e.match( "/c" ), IECore.PathMatcher.Result.NoMatch )
		self.assertEqual( e.match( "/c/d" ), IECore.PathMatcher.Result.NoMatch )
		self.assertEqual( e.match( "/a/b/c" ), IECore.PathMatcher.Result.NoMatch )

	def testInclusions( self ) :

		e = GafferScene.VisibleSet()
		e.inclusions = IECore.PathMatcher( [ "/a", "/b/c" ] )

		# Paths specifically added as inclusions
		self.assertEqual( e.match( "/a" ), IECore.PathMatcher.Result.ExactMatch )
		self.assertEqual( e.match( "/b/c" ), IECore.PathMatcher.Result.ExactMatch )

		# Paths with included descendants
		self.assertEqual( e.match( "/" ), IECore.PathMatcher.Result.DescendantMatch )
		self.assertEqual( e.match( "/b" ), IECore.PathMatcher.Result.DescendantMatch )

		# Paths with included ancestors
		self.assertEqual( e.match( "/a/b" ), IECore.PathMatcher.Result.AncestorMatch )
		self.assertEqual( e.match( "/b/c/d/e" ), IECore.PathMatcher.Result.AncestorMatch )

		# Paths unrelated to those in inclusions
		self.assertEqual( e.match( "/c" ), IECore.PathMatcher.Result.NoMatch )
		self.assertEqual( e.match( "/a2" ), IECore.PathMatcher.Result.NoMatch )

	def testExpansionsCombineWithInclusions( self ) :

		e = GafferScene.VisibleSet()
		e.expansions = IECore.PathMatcher( [ "/a", "/b", "/a/b", "/b/c" ] )
		e.inclusions = IECore.PathMatcher( [ "/a", "/b/c", "/c" ] )

		self.assertTrue( e.match( "/a" ) & IECore.PathMatcher.Result.ExactMatch )
		self.assertTrue( e.match( "/a/b" ) & ( IECore.PathMatcher.Result.ExactMatch | IECore.PathMatcher.Result.AncestorMatch ) )
		self.assertTrue( e.match( "/b" ) & ( IECore.PathMatcher.Result.ExactMatch | IECore.PathMatcher.Result.DescendantMatch ) )
		self.assertTrue( e.match( "/c" ) & IECore.PathMatcher.Result.ExactMatch )
		self.assertTrue( e.match( "/c/d" ) & IECore.PathMatcher.Result.AncestorMatch )

	def testExclusionsOverrideExpansions( self ) :

		e = GafferScene.VisibleSet()
		e.expansions = IECore.PathMatcher( [ "/a", "/b", "/a/b", "/b/c", "/a/b/c" ] )

		# Excluding "/b" should only affect "/b" and its descendants
		e.exclusions = IECore.PathMatcher( [ "/b" ] )
		self.assertEqual( e.match( "/a" ), IECore.PathMatcher.Result.ExactMatch )
		self.assertEqual( e.match( "/a/b" ), IECore.PathMatcher.Result.ExactMatch )
		self.assertEqual( e.match( "/a/b/c" ), IECore.PathMatcher.Result.ExactMatch )

		self.assertEqual( e.match( "/b" ), IECore.PathMatcher.Result.NoMatch )
		self.assertEqual( e.match( "/b/c" ), IECore.PathMatcher.Result.NoMatch )

		# Removing the exclusion on "/b" should result in "/b" and "/b/c" matching
		e.exclusions.removePath( "/b" )
		self.assertEqual( e.match( "/a" ), IECore.PathMatcher.Result.ExactMatch )
		self.assertEqual( e.match( "/a/b" ), IECore.PathMatcher.Result.ExactMatch )
		self.assertEqual( e.match( "/a/b/c" ), IECore.PathMatcher.Result.ExactMatch )

		self.assertEqual( e.match( "/b" ), IECore.PathMatcher.Result.ExactMatch )
		self.assertEqual( e.match( "/b/c" ), IECore.PathMatcher.Result.ExactMatch )

		# Excluding "/a/b" should not affect "/a", but also exclude "/a/b/c"
		e.exclusions.addPath( "/a/b" )
		self.assertEqual( e.match( "/a" ), IECore.PathMatcher.Result.ExactMatch )

		self.assertEqual( e.match( "/a/b" ), IECore.PathMatcher.Result.NoMatch )
		self.assertEqual( e.match( "/a/b/c" ), IECore.PathMatcher.Result.NoMatch )

		self.assertEqual( e.match( "/b" ), IECore.PathMatcher.Result.ExactMatch )
		self.assertEqual( e.match( "/b/c" ), IECore.PathMatcher.Result.ExactMatch )

	def testExclusionsOverrideInclusions( self ) :

		e = GafferScene.VisibleSet()
		e.inclusions = IECore.PathMatcher( [ "/a", "/d", "/e/f" ] )

		# Excluding "/d" & "/e" should not affect "/a"
		e.exclusions = IECore.PathMatcher( [ "/d", "/e" ] )
		self.assertEqual( e.match( "/a" ), IECore.PathMatcher.Result.ExactMatch )

		self.assertEqual( e.match( "/d" ), IECore.PathMatcher.Result.NoMatch )
		self.assertEqual( e.match( "/d/e" ), IECore.PathMatcher.Result.NoMatch )
		self.assertEqual( e.match( "/e" ), IECore.PathMatcher.Result.NoMatch )

		# Removing the exclusion on "/d" should result in only "/e" not matching
		e.exclusions.removePath( "/d" )
		self.assertEqual( e.match( "/a" ), IECore.PathMatcher.Result.ExactMatch )
		self.assertEqual( e.match( "/d" ), IECore.PathMatcher.Result.ExactMatch )
		self.assertEqual( e.match( "/d/e" ), IECore.PathMatcher.Result.AncestorMatch )

		self.assertEqual( e.match( "/e" ), IECore.PathMatcher.Result.NoMatch )

if __name__ == "__main__":
	unittest.main()
