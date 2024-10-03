##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI
import GafferUITest
import GafferScene
import GafferSceneUI

class HierarchyViewTest( GafferUITest.TestCase ) :

	def assertExpanded( self, script, path, expanded ) :

		expandedPaths = GafferSceneUI.ScriptNodeAlgo.getVisibleSet( script ).expansions
		self.assertEqual(
			bool( expandedPaths.match( path ) & IECore.PathMatcher.Result.ExactMatch ),
			expanded
		)

	def testNoUnwantedExpansion( self ) :

		# Make a small scene, and view it with a HierarchyView editor.

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["plane"]["out"] )

		HierarchyView = GafferSceneUI.HierarchyView( script )
		script.selection().add( script["group"] )

		self.waitForIdle( 1000 )
		self.assertExpanded( script, "/group", False )

		# Expand the root, and select /group.

		GafferSceneUI.ScriptNodeAlgo.setVisibleSet( script, GafferScene.VisibleSet( expansions = IECore.PathMatcher( [ "/" ] ) ) )
		GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( script, IECore.PathMatcher( [ "/group" ] ) )

		self.waitForIdle( 1000 )

		self.assertExpanded( script, "/", True )
		self.assertExpanded( script, "/group", False )

		# Tweak the scene to change the name of a
		# non-expanded location. We expect the expansion to
		# remain the same.

		script["plane"]["name"].setValue( "jane" )

		self.waitForIdle( 1000 )
		self.assertExpanded( script, "/", True )
		self.assertExpanded( script, "/group", False )

	def testDeselectAndReselectNode( self ) :

		script = Gaffer.ScriptNode()
		script["plane"] = GafferScene.Plane()
		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["plane"]["out"] )

		with GafferUI.Window() as w :
			HierarchyView = GafferSceneUI.HierarchyView( script )

		w.setVisible( True )

		HierarchyView.setNodeSet( Gaffer.StandardSet( { script["group"] } ) )

		groupPathMatcher = IECore.PathMatcher( [ "/group" ] )
		planePathMatcher = IECore.PathMatcher( [ "/group/plane" ] )
		GafferSceneUI.ScriptNodeAlgo.setVisibleSet( script, GafferScene.VisibleSet( expansions = groupPathMatcher ) )
		GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( script, planePathMatcher )

		def assertExpectedState() :

			self.waitForIdle( 10000 )

			self.assertEqual(
				GafferSceneUI.ScriptNodeAlgo.getVisibleSet( script ).expansions,
				groupPathMatcher
			)
			self.assertEqual(
				GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( script ),
				planePathMatcher
			)

		assertExpectedState()

		HierarchyView.setNodeSet( Gaffer.StandardSet() )
		assertExpectedState()

		HierarchyView.setNodeSet( Gaffer.StandardSet( { script["group"] } ) )
		assertExpectedState()

if __name__ == "__main__":
	unittest.main()
