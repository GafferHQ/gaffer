##########################################################################
#
#  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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
import six

import imath

import IECore

import Gaffer
import GafferUITest
import GafferScene
import GafferSceneUI

class TransformToolTest( GafferUITest.TestCase ) :

	def testSelectionEditability( self ) :

		script = Gaffer.ScriptNode()

		script["box"] = Gaffer.Box()
		script["box"]["plane"] = GafferScene.Plane()
		Gaffer.PlugAlgo.promote( script["box"]["plane"]["out"] )

		# Box is editable, so all fields of the selection should be useable.

		selection = GafferSceneUI.TransformTool.Selection( script["box"]["out"], "/plane", script.context(), None )

		self.assertEqual( selection.scene(), script["box"]["out"] )
		self.assertEqual( selection.path(), "/plane" )
		self.assertEqual( selection.context(), script.context() )
		self.assertEqual( selection.upstreamScene(), script["box"]["plane"]["out"] )
		self.assertEqual( selection.upstreamPath(), "/plane" )
		self.assertEqual( selection.upstreamContext()["scene:path"], IECore.InternedStringVectorData( [ "plane" ] ) )
		self.assertTrue( selection.editable() )
		self.assertEqual( selection.editTarget(), script["box"]["plane"]["transform"] )
		self.assertEqual( selection.transformSpace(), imath.M44f() )

		# Reference internals are not editable, so attempts to access invalid
		# fields should throw.

		referenceFileName = os.path.join( self.temporaryDirectory(), "test.grf" )
		script["box"].exportForReference( referenceFileName )

		script["reference"] = Gaffer.Reference()
		script["reference"].load( referenceFileName )

		selection = GafferSceneUI.TransformTool.Selection( script["reference"]["out"], "/plane", script.context(), None )

		self.assertEqual( selection.scene(), script["reference"]["out"] )
		self.assertEqual( selection.path(), "/plane" )
		self.assertEqual( selection.context(), script.context() )
		self.assertEqual( selection.upstreamScene(), script["reference"]["plane"]["out"] )
		self.assertEqual( selection.upstreamPath(), "/plane" )
		self.assertEqual( selection.upstreamContext()["scene:path"], IECore.InternedStringVectorData( [ "plane" ] ) )
		self.assertFalse( selection.editable() )
		with six.assertRaisesRegex( self, RuntimeError, "Selection is not editable" ) :
			selection.editTarget()
		with six.assertRaisesRegex( self, RuntimeError, "Selection is not editable" ) :
			selection.transformSpace()

	def testSelectionEditScopes( self ) :

		# Start with an EditScope that isn't even connected.

		plane = GafferScene.Plane()

		editScope = Gaffer.EditScope()
		editScope.setup( plane["out"] )

		selection = GafferSceneUI.TransformTool.Selection( plane["out"], "/plane", Gaffer.Context(), None )
		self.assertTrue( selection.editable() )
		self.assertEqual( selection.editTarget(), plane["transform"] )
		self.assertIsNone( selection.editScope() )

		selection = GafferSceneUI.TransformTool.Selection( plane["out"], "/plane", Gaffer.Context(), editScope )
		self.assertFalse( selection.editable() )
		self.assertEqual( selection.warning(), "EditScope not in history" )
		self.assertRaises( RuntimeError, selection.acquireTransformEdit )
		self.assertRaises( RuntimeError, selection.transformSpace )
		self.assertEqual( selection.editScope(), editScope )

		# Connect it and it should start to work, even if there is a downstream
		# Transform node.

		editScope["in"].setInput( plane["out"] )
		transform = GafferScene.Transform()
		transform["in"].setInput( editScope["out"] )

		selection = GafferSceneUI.TransformTool.Selection( transform["out"], "/plane", Gaffer.Context(), editScope )
		self.assertTrue( selection.editable() )
		self.assertEqual( selection.warning(), "" )
		self.assertEqual( selection.upstreamScene(), editScope["out"] )
		self.assertEqual( selection.editScope(), editScope )

		# Disable the EditScope and the selection should become non-editable.

		editScope["enabled"].setValue( False )
		selection = GafferSceneUI.TransformTool.Selection( transform["out"], "/plane", Gaffer.Context(), editScope )
		self.assertFalse( selection.editable() )
		self.assertEqual( selection.warning(), "EditScope disabled" )
		self.assertEqual( selection.editScope(), editScope )

		editScope["enabled"].setValue( True )
		selection = GafferSceneUI.TransformTool.Selection( transform["out"], "/plane", Gaffer.Context(), editScope )
		self.assertTrue( selection.editable() )
		self.assertEqual( selection.warning(), "" )
		self.assertEqual( selection.editScope(), editScope )

		# Make the downstream node author a transform that would override the
		# EditScope. The selection should become non-editable again.

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )
		transform["filter"].setInput( pathFilter["out"] )

		selection = GafferSceneUI.TransformTool.Selection( transform["out"], "/plane", Gaffer.Context(), editScope )
		self.assertFalse( selection.editable() )
		self.assertEqual( selection.warning(), "EditScope overridden downstream" )
		self.assertEqual( selection.upstreamScene(), transform["out"] )

		# Disable the downstream node and we should be back in business.

		transform["enabled"].setValue( False )
		selection = GafferSceneUI.TransformTool.Selection( transform["out"], "/plane", Gaffer.Context(), editScope )
		self.assertTrue( selection.editable() )
		self.assertEqual( selection.warning(), "" )
		self.assertEqual( selection.upstreamScene(), editScope["out"] )

		# Ensure that we use any existing node within an EditScope in preference
		# to creating a new tweak node

		plane2 = GafferScene.Plane()
		plane2["name"].setValue( "otherPlane" )
		editScope["plane2"] = plane2

		editScope["parent"] = GafferScene.Parent()
		editScope["parent"]["parent"].setValue( "/" )
		editScope["parent"]["in"].setInput( editScope["BoxOut"]["in"].getInput() )
		editScope["parent"]["children"][0].setInput( plane2["out"] )
		editScope["BoxOut"]["in"].setInput( editScope["parent"]["out"] )

		selection = GafferSceneUI.TransformTool.Selection( transform["out"], "/otherPlane", Gaffer.Context(), editScope )

		self.assertTrue( selection.editable() )
		self.assertEqual( selection.warning(), "" )
		self.assertEqual( selection.upstreamScene(), plane2["out"] )
		self.assertEqual( selection.editScope(), editScope )
		self.assertEqual( selection.editTarget(), plane2["transform"] )

		# Ensure we handle being inside the chosen edit scope

		selection = GafferSceneUI.TransformTool.Selection( editScope["parent"]["out"], "/plane", Gaffer.Context(), editScope )
		self.assertFalse( selection.editable() )
		self.assertEqual( selection.warning(), "EditScope output not in history" )

	def testNestedEditScopes( self ) :

		outerScope = Gaffer.EditScope()
		outerScope.setup( GafferScene.ScenePlug() )
		innerScope = Gaffer.EditScope()
		outerScope["Inner"] = innerScope
		innerScope.setup( outerScope["BoxIn"]["out"] )
		innerScope["in"].setInput( outerScope["BoxIn"]["out"] )
		innerScope["parent"] = GafferScene.Parent()
		innerScope["parent"]["parent"].setValue( "/" )
		innerScope["parent"]["in"].setInput( innerScope["BoxIn"]["out"] )
		innerScope["BoxOut"]["in"].setInput( innerScope["parent"]["out"] )
		innerScope["plane"] = GafferScene.Plane()
		innerScope["parent"]["children"][0].setInput( innerScope["plane"]["out"] )
		outerScope["BoxOut"]["in"].setInput( innerScope["out"] )

		selection = GafferSceneUI.TransformTool.Selection( outerScope["out"], "/plane", Gaffer.Context(), innerScope )
		self.assertTrue( selection.editable() )
		self.assertEqual( selection.editTarget(), innerScope["plane"]["transform"] )
		self.assertEqual( selection.editScope(), innerScope )

		selection = GafferSceneUI.TransformTool.Selection( outerScope["out"], "/plane", Gaffer.Context(), outerScope )
		self.assertTrue( selection.editable() )
		self.assertEqual( selection.editTarget(), outerScope )
		self.assertEqual( selection.editScope(), outerScope )

	def testSceneReaderSelectionEditability( self ) :

		sceneReader = GafferScene.SceneReader()
		sceneReader["fileName"].setValue( "${GAFFER_ROOT}/python/GafferSceneTest/alembicFiles/groupedPlane.abc" )

		selection = GafferSceneUI.TransformTool.Selection( sceneReader["out"], "/group/plane", Gaffer.Context(), None )
		self.assertTrue( selection.editable() )
		self.assertEqual( selection.path(), "/group" )
		self.assertEqual( selection.editTarget(), sceneReader["transform"] )

		selection = GafferSceneUI.TransformTool.Selection( sceneReader["out"], "/group", Gaffer.Context(), None )
		self.assertTrue( selection.editable() )
		self.assertEqual( selection.path(), "/group" )
		self.assertEqual( selection.editTarget(), sceneReader["transform"] )

	def testInvalidSelection( self ) :

		plane = GafferScene.Plane()
		selection = GafferSceneUI.TransformTool.Selection( plane["out"], "/cube", Gaffer.Context(), None )
		self.assertFalse( selection.editable() )
		self.assertEqual( selection.warning(), "Location does not exist" )

	def testAcquireTransformEdit( self ) :

		plane = GafferScene.Plane()

		selection = GafferSceneUI.TransformTool.Selection( plane["out"], "/plane", Gaffer.Context(), None )
		edit = selection.acquireTransformEdit()
		self.assertEqual( edit.translate, plane["transform"]["translate"] )
		self.assertEqual( edit.rotate, plane["transform"]["rotate"] )
		self.assertEqual( edit.scale, plane["transform"]["scale"] )
		self.assertEqual( edit.pivot, plane["transform"]["pivot"] )

		editScope = Gaffer.EditScope()
		editScope.setup( plane["out"] )
		editScope["in"].setInput( plane["out"] )

		selection = GafferSceneUI.TransformTool.Selection( editScope["out"], "/plane", Gaffer.Context(), editScope )
		self.assertIsNone( selection.acquireTransformEdit( createIfNecessary = False ) )
		edit = selection.acquireTransformEdit()
		self.assertTrue( editScope.isAncestorOf( edit.translate ) )

	def testDontEditUpstreamOfReference( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()

		script["box"] = Gaffer.Box()
		script["box"]["filter"] = GafferScene.PathFilter()
		script["box"]["filter"]["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )
		script["box"]["transform"] = GafferScene.Transform()
		script["box"]["transform"]["filter"].setInput( script["box"]["filter"]["out"] )
		Gaffer.PlugAlgo.promote( script["box"]["transform"]["in"] )
		Gaffer.PlugAlgo.promote( script["box"]["transform"]["out"] )
		script["box"]["in"].setInput( script["plane"]["out"] )

		# Box is editable

		selection = GafferSceneUI.TransformTool.Selection( script["box"]["out"], "/plane", script.context(), None )

		self.assertEqual( selection.upstreamScene(), script["box"]["transform"]["out"] )
		self.assertEqual( selection.upstreamPath(), "/plane" )
		self.assertEqual( selection.upstreamContext()["scene:path"], IECore.InternedStringVectorData( [ "plane" ] ) )
		self.assertTrue( selection.editable() )
		self.assertEqual( selection.editTarget(), script["box"]["transform"]["transform"] )

		# Reference internals are not editable, so we can't edit the transform any more.
		# Make sure we don't accidentally traverse through the reference and try to edit
		# the Plane directly.

		referenceFileName = os.path.join( self.temporaryDirectory(), "test.grf" )
		script["box"].exportForReference( referenceFileName )

		script["reference"] = Gaffer.Reference()
		script["reference"].load( referenceFileName )
		script["reference"]["in"].setInput( script["plane"]["out"] )

		selection = GafferSceneUI.TransformTool.Selection( script["reference"]["out"], "/plane", script.context(), None )

		self.assertEqual( selection.upstreamScene(), script["reference"]["transform"]["out"] )
		self.assertEqual( selection.upstreamPath(), "/plane" )
		self.assertEqual( selection.upstreamContext()["scene:path"], IECore.InternedStringVectorData( [ "plane" ] ) )
		self.assertFalse( selection.editable() )

if __name__ == "__main__":
	unittest.main()
