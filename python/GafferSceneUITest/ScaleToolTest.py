##########################################################################
#
#  Copyright (c) 2017, John Haddon. All rights reserved.
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

import imath

import IECore

import Gaffer
import GafferUITest
import GafferScene
import GafferSceneUI

class ScaleToolTest( GafferUITest.TestCase ) :

	def test( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["plane"]["out"] )

		tool = GafferSceneUI.ScaleTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/plane" ] ) )

		with Gaffer.UndoScope( script ) :
			tool.scale( imath.V3f( 2, 1, 1 ) )

		self.assertEqual( script["plane"]["transform"]["scale"].getValue(), imath.V3f( 2, 1, 1 ) )

		with Gaffer.UndoScope( script ) :
			tool.scale( imath.V3f( 1, 0.5, 1 ) )

		self.assertEqual( script["plane"]["transform"]["scale"].getValue(), imath.V3f( 2, 0.5, 1 ) )

		script.undo()
		self.assertEqual( script["plane"]["transform"]["scale"].getValue(), imath.V3f( 2, 1, 1 ) )

		script.undo()
		self.assertEqual( script["plane"]["transform"]["scale"].getValue(), imath.V3f( 1, 1, 1 ) )

	def testHandles( self ) :

		script = Gaffer.ScriptNode()
		script["plane"] = GafferScene.Plane()

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["plane"]["out"] )

		tool = GafferSceneUI.ScaleTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/plane" ] ) )
		self.assertEqual( tool.handlesTransform(), imath.M44f() )

		script["plane"]["transform"]["pivot"].setValue( imath.V3f( 1, 0, 0 ) )
		self.assertEqual(
			tool.handlesTransform(),
			imath.M44f().translate( imath.V3f( 1, 0, 0 ) )
		)

		script["plane"]["transform"]["translate"].setValue( imath.V3f( 0, 1, 0 ) )
		self.assertEqual(
			tool.handlesTransform(),
			imath.M44f().translate( imath.V3f( 1, 1, 0 ) )
		)

		script["plane"]["transform"]["scale"].setValue( imath.V3f( 1, -2, 3 ) )
		self.assertTrue(
			tool.handlesTransform().equalWithAbsError(
				imath.M44f().translate( imath.V3f( 1, 1, 0 ) ).scale( imath.V3f( 1, -1, 1 ) ),
				0.000001
			)
		)

	def testEditScopes( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		script["sphere"]["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		script["editScope"] = Gaffer.EditScope()
		script["editScope"].setup( script["sphere"]["out"] )
		script["editScope"]["in"].setInput( script["sphere"]["out"] )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["editScope"]["out"] )
		view["editScope"].setInput( script["editScope"]["out"] )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/sphere" ] ) )

		tool = GafferSceneUI.ScaleTool( view )
		tool["active"].setValue( True )

		self.assertEqual( tool.handlesTransform(), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )
		self.assertEqual( len( tool.selection() ), 1 )
		self.assertTrue( tool.selection()[0].editable() )
		self.assertFalse( GafferScene.EditScopeAlgo.hasTransformEdit( script["editScope"], "/sphere" ) )
		self.assertEqual( script["editScope"]["out"].transform( "/sphere" ), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )

		tool.scale( imath.V3f( 2, 2, 2 ) )
		self.assertEqual( tool.handlesTransform(), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )
		self.assertEqual( len( tool.selection() ), 1 )
		self.assertTrue( tool.selection()[0].editable() )
		self.assertTrue( GafferScene.EditScopeAlgo.hasTransformEdit( script["editScope"], "/sphere" ) )
		self.assertEqual( script["editScope"]["out"].transform( "/sphere" ), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ).scale( imath.V3f( 2, 2, 2 ) ) )

	def testHandleOriginsRespectPointConstraint( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()

		cubeTranslate = imath.V3f( 5, 5, 0 )
		script["cube"] = GafferScene.Cube()
		script["cube"]["transform"]["translate"].setValue( cubeTranslate )

		script["parent"] = GafferScene.Parent()
		script["parent"]["in"].setInput( script["sphere"]["out"] )
		script["parent"]["children"][0].setInput( script["cube"]["out"] )
		script["parent"]["parent"].setValue( "/" )

		script["sphereFilter"] = GafferScene.PathFilter()
		script["sphereFilter"]["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		script["constraint"] = GafferScene.PointConstraint()
		script["constraint"]["in"].setInput( script["parent"]["out"] )
		script["constraint"]["filter"].setInput( script["sphereFilter"]["out"] )
		script["constraint"]["target"].setValue( "/cube" )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["constraint"]["out"] )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/sphere" ] ) )

		tool = GafferSceneUI.ScaleTool( view )
		tool["active"].setValue( True )

		self.assertEqual( tool.handlesTransform(), imath.M44f().translate( cubeTranslate ) )

if __name__ == "__main__":
	unittest.main()
