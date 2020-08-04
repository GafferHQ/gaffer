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

import math

import imath

import IECore

import Gaffer
import GafferUITest
import GafferScene
import GafferSceneUI

class RotateToolTest( GafferUITest.TestCase ) :

	def testRotate( self ) :

		script = Gaffer.ScriptNode()
		script["cube"] = GafferScene.Cube()

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["cube"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/cube" ] ) )

		tool = GafferSceneUI.RotateTool( view )
		tool["active"].setValue( True )

		for i in range( 0, 6 ) :
			tool.rotate( imath.Eulerf( 0, 90, 0 ) )
			self.assertAlmostEqual( script["cube"]["transform"]["rotate"]["y"].getValue(), (i + 1) * 90, delta = 0.0001 )

	def testInteractionWithGroupRotation( self ) :

		script = Gaffer.ScriptNode()

		script["cube"] = GafferScene.Cube()
		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["cube"]["out"] )

		# Rotates the X axis onto the negative Z axis
		script["group"]["transform"]["rotate"]["y"].setValue( 90 )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["group"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group/cube" ] ) )

		tool = GafferSceneUI.RotateTool( view )
		tool["active"].setValue( True )

		# Rotates 90 degrees using the Z handle. This will
		# rotate about the X axis in world space, because the
		# handle orientation has been affected by the group
		# transform (because default orientation is Parent).
		tool.rotate( imath.Eulerf( 0, 0, 90 ) )

		# We expect this to have aligned the cube's local X axis onto
		# the Y axis in world space, and the local Y axis onto the world
		# Z axis.
		self.assertTrue(
			imath.V3f( 0, 1, 0 ).equalWithAbsError(
				imath.V3f( 1, 0, 0 ) * script["group"]["out"].fullTransform( "/group/cube" ),
				0.000001
			)
		)
		self.assertTrue(
			imath.V3f( 0, 0, 1 ).equalWithAbsError(
				imath.V3f( 0, 1, 0 ) * script["group"]["out"].fullTransform( "/group/cube" ),
				0.000001
			)
		)

	def testOrientation( self ) :

		script = Gaffer.ScriptNode()

		script["cube"] = GafferScene.Cube()
		script["cube"]["transform"]["rotate"]["y"].setValue( 90 )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["cube"]["out"] )
		script["group"]["transform"]["rotate"]["y"].setValue( 90 )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["group"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group/cube" ] ) )

		tool = GafferSceneUI.RotateTool( view )
		tool["active"].setValue( True )

		# Local

		tool["orientation"].setValue( tool.Orientation.Local )

		with Gaffer.UndoScope( script ) :
			tool.rotate( imath.Eulerf( 0, 0, 90 ) )

		self.assertTrue(
			imath.V3f( 0, 1, 0 ).equalWithAbsError(
				imath.V3f( 1, 0, 0 ) * script["group"]["out"].fullTransform( "/group/cube" ),
				0.000001
			)
		)
		script.undo()

		# Parent

		tool["orientation"].setValue( tool.Orientation.Parent )

		with Gaffer.UndoScope( script ) :
			tool.rotate( imath.Eulerf( 90, 0, 0 ) )

		self.assertTrue(
			imath.V3f( 0, 1, 0 ).equalWithAbsError(
				imath.V3f( 1, 0, 0 ) * script["group"]["out"].fullTransform( "/group/cube" ),
				0.000001
			)
		)
		script.undo()

		# World

		tool["orientation"].setValue( tool.Orientation.World )

		with Gaffer.UndoScope( script ) :
			tool.rotate( imath.Eulerf( 0, 0, 90 ) )

		self.assertTrue(
			imath.V3f( 0, -1, 0 ).equalWithAbsError(
				imath.V3f( 1, 0, 0 ) * script["group"]["out"].fullTransform( "/group/cube" ),
				0.000001
			)
		)

	def testTransformWithRotation( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()

		script["transformFilter"] = GafferScene.PathFilter()
		script["transformFilter"]["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		script["transform"] = GafferScene.Transform()
		script["transform"]["in"].setInput( script["plane"]["out"] )
		script["transform"]["filter"].setInput( script["transformFilter"]["out"] )
		script["transform"]["transform"]["rotate"]["y"].setValue( 90 )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["transform"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/plane" ] ) )

		tool = GafferSceneUI.RotateTool( view )
		tool["active"].setValue( True )

		tool.rotate( imath.Eulerf( 90, 0, 0 ) )

		self.assertTrue(
			imath.V3f( 0, 1, 0 ).equalWithAbsError(
				imath.V3f( 1, 0, 0 ) * script["transform"]["out"].fullTransform( "/plane" ),
				0.000001
			)
		)

		self.assertTrue(
			imath.V3f( 0, 0, 1 ).equalWithAbsError(
				imath.V3f( 0, 1, 0 ) * script["transform"]["out"].fullTransform( "/plane" ),
				0.000001
			)
		)

	def testPivotAffectsHandlesTransform( self ) :

		script = Gaffer.ScriptNode()
		script["cube"] = GafferScene.Cube()

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["cube"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/cube" ] ) )

		tool = GafferSceneUI.RotateTool( view )
		tool["active"].setValue( True )

		self.assertEqual( tool.handlesTransform(), imath.M44f() )

		script["cube"]["transform"]["pivot"].setValue( imath.V3f( 1, 0, 0 ) )

		self.assertEqual(
			tool.handlesTransform(),
			imath.M44f().translate(
				script["cube"]["transform"]["pivot"].getValue()
			)
		)

		script["cube"]["transform"]["translate"].setValue( imath.V3f( 1, 2, -1 ) )

		self.assertEqual(
			tool.handlesTransform(),
			imath.M44f().translate(
				script["cube"]["transform"]["pivot"].getValue() +
				script["cube"]["transform"]["translate"].getValue()
			)
		)

	def testPivotAndExistingTransform( self ) :

		script = Gaffer.ScriptNode()

		script["cube"] = GafferScene.Cube()

		script["transformFilter"] = GafferScene.PathFilter()
		script["transformFilter"]["paths"].setValue( IECore.StringVectorData( [ "/cube" ] ) )

		script["transform"] = GafferScene.Transform()
		script["transform"]["in"].setInput( script["cube"]["out"] )
		script["transform"]["filter"].setInput( script["transformFilter"]["out"] )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["transform"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/cube" ] ) )

		tool = GafferSceneUI.RotateTool( view )
		tool["active"].setValue( True )

		# Start with default pivot

		self.assertEqual(
			imath.V3f( 0 ) * tool.handlesTransform(),
			imath.V3f( 0, 0, 0 ),
		)

		# Offset it

		script["transform"]["transform"]["pivot"].setValue( imath.V3f( 1, 0, 0 ) )

		self.assertEqual(
			imath.V3f( 0 ) * tool.handlesTransform(),
			imath.V3f( 1, 0, 0 ),
		)

		# Now add an existing transform on the cube, prior
		# to it entering the transform node we're editing.
		# The pivot's world space position should be affected
		# because the Transform node is operating in Local space.

		script["cube"]["transform"]["rotate"]["y"].setValue( 90 )

		self.assertTrue(
			imath.V3f( 0, 0, -1 ).equalWithAbsError(
				imath.V3f( 0 ) * tool.handlesTransform(),
				0.0000001,
			)
		)

		# But if we edit in World space, then the existing transform
		# should have no relevance.

		script["transform"]["space"].setValue( script["transform"].Space.World )

		self.assertEqual(
			imath.V3f( 0 ) * tool.handlesTransform(),
			imath.V3f( 1, 0, 0 ),
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

		tool = GafferSceneUI.RotateTool( view )
		tool["active"].setValue( True )

		self.assertEqual( tool.handlesTransform(), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )
		self.assertEqual( len( tool.selection() ), 1 )
		self.assertTrue( tool.selection()[0].editable() )
		self.assertFalse( GafferScene.EditScopeAlgo.hasTransformEdit( script["editScope"], "/sphere" ) )
		self.assertEqual( script["editScope"]["out"].transform( "/sphere" ), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )

		tool.rotate( imath.Eulerf( 0, 90, 0 ) )
		self.assertEqual( tool.handlesTransform(), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )
		self.assertEqual( len( tool.selection() ), 1 )
		self.assertTrue( tool.selection()[0].editable() )
		self.assertTrue( GafferScene.EditScopeAlgo.hasTransformEdit( script["editScope"], "/sphere" ) )

		self.assertEqual(
			script["editScope"]["out"].transform( "/sphere" ),
			imath.M44f().translate( imath.V3f( 1, 0, 0 ) ).rotate( imath.V3f( 0, math.pi / 2, 0 ) ),
		)

	def testInteractionWithPointConstraint( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()

		script["cube"] = GafferScene.Cube()
		script["cube"]["transform"]["translate"].setValue( imath.V3f( 5, 5, 0 ) )

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

		tool = GafferSceneUI.RotateTool( view )
		tool["active"].setValue( True )

		for orientation in ( tool.Orientation.Local, tool.Orientation.Parent, tool.Orientation.World ) :
			tool["orientation"].setValue( orientation )
			self.assertEqual( tool.handlesTransform(), imath.M44f().translate( script["cube"]["transform"]["translate"].getValue() ) )

	def testInteractionWithParentConstraint( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()

		script["cube"] = GafferScene.Cube()
		script["cube"]["transform"]["translate"].setValue( imath.V3f( 5, 5, 0 ) )
		script["cube"]["transform"]["rotate"]["x"].setValue( 90 )

		script["parent"] = GafferScene.Parent()
		script["parent"]["in"].setInput( script["sphere"]["out"] )
		script["parent"]["children"][0].setInput( script["cube"]["out"] )
		script["parent"]["parent"].setValue( "/" )

		script["sphereFilter"] = GafferScene.PathFilter()
		script["sphereFilter"]["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		script["constraint"] = GafferScene.ParentConstraint()
		script["constraint"]["in"].setInput( script["parent"]["out"] )
		script["constraint"]["filter"].setInput( script["sphereFilter"]["out"] )
		script["constraint"]["target"].setValue( "/cube" )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["constraint"]["out"] )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/sphere" ] ) )

		tool = GafferSceneUI.RotateTool( view )
		tool["active"].setValue( True )

		tool["orientation"].setValue( tool.Orientation.Parent )
		self.assertEqual( tool.handlesTransform(), imath.M44f().translate( script["cube"]["transform"]["translate"].getValue() ) )

		tool["orientation"].setValue( tool.Orientation.Local )
		self.assertEqual( tool.handlesTransform(), script["constraint"]["out"].transform( "/sphere" ) )

		tool.rotate( imath.Eulerf( 0, 90, 0 ) )
		self.assertEqual( script["sphere"]["transform"]["rotate"].getValue(), imath.V3f( 0, 90, 0 ) )

if __name__ == "__main__":
	unittest.main()
