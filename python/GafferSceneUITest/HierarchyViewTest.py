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

	def assertExpanded( self, context, path, expanded ) :

		expandedPaths = GafferSceneUI.ContextAlgo.getExpandedPaths( context )
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
		self.assertExpanded( script.context(), "/group", False )

		# Expand the root, and select /group.

		GafferSceneUI.ContextAlgo.setExpandedPaths( script.context(), IECore.PathMatcher( [ "/" ] ) )
		GafferSceneUI.ContextAlgo.setSelectedPaths( script.context(), IECore.PathMatcher( [ "/group" ] ) )

		self.waitForIdle( 1000 )

		self.assertExpanded( script.context(), "/", True )
		self.assertExpanded( script.context(), "/group", False )

		# Tweak the scene to change the name of a
		# non-expanded location. We expect the expansion to
		# remain the same.

		script["plane"]["name"].setValue( "jane" )

		self.waitForIdle( 1000 )
		self.assertExpanded( script.context(), "/", True )
		self.assertExpanded( script.context(), "/group", False )

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
		GafferSceneUI.ContextAlgo.setExpandedPaths( script.context(), groupPathMatcher )
		GafferSceneUI.ContextAlgo.setSelectedPaths( script.context(), planePathMatcher )

		def assertExpectedState() :

			self.waitForIdle( 10000 )

			self.assertEqual(
				GafferSceneUI.ContextAlgo.getExpandedPaths( script.context() ),
				groupPathMatcher
			)
			self.assertEqual(
				GafferSceneUI.ContextAlgo.getSelectedPaths( script.context() ),
				planePathMatcher
			)

		assertExpectedState()

		HierarchyView.setNodeSet( Gaffer.StandardSet() )
		assertExpectedState()

		HierarchyView.setNodeSet( Gaffer.StandardSet( { script["group"] } ) )
		assertExpectedState()

if __name__ == "__main__":
	unittest.main()
