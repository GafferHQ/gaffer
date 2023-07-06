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
		e.expansions = IECore.PathMatcher( [ "/a", "/b", "/a/b", "/b/c", "/a/b/c", "/c/d/e", "/c/d", "/d" ] )

		for path in [ "/a", "/a/b", "/a/b/c", "/b", "/b/c", "/d" ] :

			self.assertEqual( e.visibility( path ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )

		# Although "/c/d" is a member of `expansions` it is not visible as its parent "/c" is not expanded.
		self.assertEqual( e.visibility( "/c/d" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.None_, False ) )

		# Likewise, "/c/d/e" is not visible as its ancestor "/c" is not expanded.
		self.assertEqual( e.visibility( "/c/d/e" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.None_, False ) )

		# While "/c" has descendants in `expansions`, they are not visible as "/c" itself is not in `expansions`
		self.assertEqual( e.visibility( "/c" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, False ) )

		# While "/" is not a member of `expansions`, it still returns a match as it meets the default minimumExpansionDepth of 0
		self.assertEqual( e.visibility( "/" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )

	def testInclusions( self ) :

		e = GafferScene.VisibleSet()
		e.inclusions = IECore.PathMatcher( [ "/a", "/b/c/d" ] )

		# Paths specifically added as inclusions are visible and have visible descendants.
		self.assertEqual( e.visibility( "/a" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/b/c/d" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )

		# Paths with included descendants
		self.assertEqual( e.visibility( "/" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/b" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )

		# "/b/c" should not be drawn as "/b" is not included or expanded, but has a visible descendant "/b/c/d"
		self.assertEqual( e.visibility( "/b/c" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.None_, True ) )

		# Paths with included ancestors. These locations are visible and have visible descendants
		self.assertEqual( e.visibility( "/a/b" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/b/c/d/e" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )

		# Paths unrelated to those in inclusions
		self.assertEqual( e.visibility( "/c/d" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.None_, False ) )
		self.assertEqual( e.visibility( "/a2/b2" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.None_, False ) )

	def testExpansionsCombineWithInclusions( self ) :

		e = GafferScene.VisibleSet()
		e.expansions = IECore.PathMatcher( [ "/a", "/b", "/a/b" ] )
		e.inclusions = IECore.PathMatcher( [ "/a", "/b/c", "/c" ] )

		for path in [ "/a", "/a/b", "/b", "/b/c", "/c", "/c/d" ] :

			self.assertEqual( e.visibility( path ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )

		# Expanding "/d/e/f" without also expanding its ancestors results in only "/d" being visible.
		e.expansions.addPath( "/d/e/f" )
		self.assertEqual( e.visibility( "/d" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, False ) )
		self.assertEqual( e.visibility( "/d/e" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.None_, False ) )
		self.assertEqual( e.visibility( "/d/e/f" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.None_, False ) )

		# Including "/d/g/h" without including its ancestors should not affect "/d/e/f"
		e.inclusions.addPath( "/d/g/h" )
		self.assertEqual( e.visibility( "/d" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/d/g" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.None_, True ) )
		self.assertEqual( e.visibility( "/d/g/h" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/d/e/f" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.None_, False ) )

	def testExclusionsOverrideExpansions( self ) :

		e = GafferScene.VisibleSet()
		e.expansions = IECore.PathMatcher( [ "/a", "/b", "/a/b", "/b/c", "/a/b/c" ] )

		# Excluding "/b" should only affect "/b" and its descendants
		e.exclusions = IECore.PathMatcher( [ "/b" ] )
		self.assertEqual( e.visibility( "/a" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/a/b" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/a/b/c" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )

		self.assertEqual( e.visibility( "/b" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.ExcludedBounds, False ) )
		self.assertEqual( e.visibility( "/b/c" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.None_, False ) )

		# Removing the exclusion on "/b" should result in "/b" and "/b/c" becoming visible
		e.exclusions.removePath( "/b" )
		self.assertEqual( e.visibility( "/a" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/a/b" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/a/b/c" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )

		self.assertEqual( e.visibility( "/b" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/b/c" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )

		e.exclusions.addPath( "/a/b" )
		# "/a" is still visible and may have visible descendants as it is expanded
		self.assertEqual( e.visibility( "/a" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		# "/a/b" should draw as excluded bounds as "/a" is expanded, and have no visible descendants
		self.assertEqual( e.visibility( "/a/b" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.ExcludedBounds, False ) )
		# "/a/b/c" should not draw
		self.assertEqual( e.visibility( "/a/b/c" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.None_, False ) )
		# collapsing "/a" should cause "/a/b" to not draw
		e.expansions.removePath( "/a" )
		self.assertEqual( e.visibility( "/a/b" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.None_, False ) )

		# Excluding "/a/b" should not have affected "/b" or its descendants
		self.assertEqual( e.visibility( "/b" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/b/c" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )

	def testExclusionsOverrideInclusions( self ) :

		e = GafferScene.VisibleSet()
		e.inclusions = IECore.PathMatcher( [ "/a", "/d", "/e/f" ] )

		# Excluding "/d" & "/e" should not affect "/a"
		e.exclusions = IECore.PathMatcher( [ "/d", "/e" ] )
		self.assertEqual( e.visibility( "/a" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/d" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.ExcludedBounds, False )  )
		self.assertEqual( e.visibility( "/d/e" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.None_, False ) )
		self.assertEqual( e.visibility( "/e" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.ExcludedBounds, False ) )

		# Removing the exclusion on "/d" should result in only "/e" not matching
		e.exclusions.removePath( "/d" )
		self.assertEqual( e.visibility( "/a" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/d" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/d/e" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/e" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.ExcludedBounds, False ) )

	def testMinimumExpansionDepth( self ) :

		e = GafferScene.VisibleSet()

		self.assertEqual( e.visibility( "/a" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, False ) )
		self.assertEqual( e.visibility( "/a", minimumExpansionDepth = 1 ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/a/b", minimumExpansionDepth = 1 ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, False ) )

		self.assertEqual( e.visibility( "/a/b", minimumExpansionDepth = 2 ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/a/b/c", minimumExpansionDepth = 2 ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, False ) )
		self.assertEqual( e.visibility( "/a/b/c/d", minimumExpansionDepth = 2 ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.None_, False ) )

	def testInclusionsCombineWithMinimumExpansionDepth( self ) :

		e = GafferScene.VisibleSet()

		self.assertEqual( e.visibility( "/a/b", minimumExpansionDepth = 1 ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, False ) )
		self.assertEqual( e.visibility( "/a/b/c", minimumExpansionDepth = 1 ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.None_, False ) )

		e.inclusions.addPath( "/a/b/c" )
		self.assertEqual( e.visibility( "/a/b", minimumExpansionDepth = 1 ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/a/b/c", minimumExpansionDepth = 1 ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )

	def testExpansionsCombineWithMinimumExpansionDepth( self ) :

		e = GafferScene.VisibleSet()

		self.assertEqual( e.visibility( "/d/e", minimumExpansionDepth = 1 ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, False ) )
		self.assertEqual( e.visibility( "/d/e/f", minimumExpansionDepth = 1 ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.None_, False ) )

		e.expansions.addPath( "/d/e" )
		self.assertEqual( e.visibility( "/d/e", minimumExpansionDepth = 1 ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/d/e/f", minimumExpansionDepth = 1 ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, False ) )

		self.assertEqual( e.visibility( "/d/e" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.None_, False ) )

	def testExclusionsOverrideMinimumExpansionDepth( self ) :

		e = GafferScene.VisibleSet()

		self.assertEqual( e.visibility( "/a", minimumExpansionDepth = 2 ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )
		self.assertEqual( e.visibility( "/a/b", minimumExpansionDepth = 2 ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )

		e.exclusions.addPath( "/a" )
		self.assertEqual( e.visibility( "/a", minimumExpansionDepth = 2 ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.ExcludedBounds, False ) )
		self.assertEqual( e.visibility( "/a/b", minimumExpansionDepth = 2 ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.None_, False ) )

if __name__ == "__main__":
	unittest.main()
