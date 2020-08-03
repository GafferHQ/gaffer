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

import imath

import IECore

import Gaffer
import GafferTest
import GafferUI
import GafferUITest
import GafferScene
import GafferSceneTest
import GafferSceneUI

class SceneViewTest( GafferUITest.TestCase ) :

	def testFactory( self ) :

		sphere = GafferScene.Sphere()
		view = GafferUI.View.create( sphere["out"] )

		self.assertTrue( isinstance( view, GafferSceneUI.SceneView ) )
		self.assertTrue( view["in"].getInput().isSame( sphere["out"] ) )

	def testExpandSelection( self ) :

		# A
		# |__B
		# |__C
		#    |__D
		#	 |__E

		D = GafferScene.Sphere()
		D["name"].setValue( "D" )

		E = GafferScene.Sphere()
		E["name"].setValue( "E" )

		C = GafferScene.Group()
		C["name"].setValue( "C" )

		C["in"][0].setInput( D["out"] )
		C["in"][1].setInput( E["out"] )

		B = GafferScene.Sphere()
		B["name"].setValue( "B" )

		A = GafferScene.Group()
		A["name"].setValue( "A" )
		A["in"][0].setInput( B["out"] )
		A["in"][1].setInput( C["out"] )

		view = GafferUI.View.create( A["out"] )

		def setSelection( paths ) :
			GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( paths ) )

		def getSelection() :
			return set( GafferSceneUI.ContextAlgo.getSelectedPaths( view.getContext() ).paths() )

		setSelection( [ "/A" ] )
		self.assertEqual( getSelection(), set( [ "/A" ] ) )

		def setExpandedPaths( paths ) :
			GafferSceneUI.ContextAlgo.setExpandedPaths( view.getContext(), IECore.PathMatcher( paths ) )

		def getExpandedPaths() :
			return set( GafferSceneUI.ContextAlgo.getExpandedPaths( view.getContext() ).paths() )

		setExpandedPaths( [ "/" ] )
		self.assertEqual( getExpandedPaths(), set( [ "/" ] ) )

		# expand 1 level from root

		view.expandSelection()

		self.assertEqual( getExpandedPaths(), set( [ "/", "/A" ] ) )
		self.assertEqual( getSelection(), set( [ "/A/B", "/A/C" ] ) )

		# expand one level further, from /A/B only

		setSelection( [ "/A/C" ] )

		view.expandSelection()

		self.assertEqual( getExpandedPaths(), set( [ "/", "/A", "/A/C" ] ) )
		self.assertEqual( getSelection(), set( [ "/A/C/D", "/A/C/E" ] ) )

		# do a recursive expansion from the root. all leafs should be selected.
		# leaf items should not be expanded, because there are no children to show.

		setSelection( [ "/A" ] )
		setExpandedPaths( [ "/" ] )

		view.expandSelection( depth = 3 )
		self.assertEqual( getExpandedPaths(), set( [ "/", "/A", "/A/C" ] ) )
		self.assertEqual( getSelection(), set( [ "/A/B", "/A/C/D", "/A/C/E" ] ) )

		# do an expansion where the selection is already a leaf - nothing should change

		setSelection( [ "/A/C/D" ] )

		view.expandSelection( depth = 1 )
		self.assertEqual( getExpandedPaths(), set( [ "/", "/A", "/A/C" ] ) )
		self.assertEqual( getSelection(), set( [ "/A/C/D" ] ) )

		view.expandSelection( depth = 100000000 )
		self.assertEqual( getExpandedPaths(), set( [ "/", "/A", "/A/C" ] ) )
		self.assertEqual( getSelection(), set( [ "/A/C/D" ] ) )

		# do a recursive expansion where there's an already expanded location below the selection,
		# but it's not visible because a parent isn't expanded.

		setSelection( [ "/A" ] )
		setExpandedPaths( [ "/", "/A/C" ] )

		view.expandSelection( depth = 3 )

		self.assertEqual( getExpandedPaths(), set( [ "/", "/A", "/A/C" ] ) )
		self.assertEqual( getSelection(), set( [ "/A/B", "/A/C/D", "/A/C/E" ] ) )

		# do a single level expansion where a child was previously expanded, but not visible because
		# the parent wasn't.

		setSelection( [ "/A" ] )
		setExpandedPaths( [ "/", "/A/C" ] )

		view.expandSelection()

		self.assertEqual( getExpandedPaths(), set( [ "/", "/A", "/A/C" ] ) )
		self.assertEqual( getSelection(), set( [ "/A/B", "/A/C" ] ) )

		# try to do an expansion on the leaf level - it should refuse

		setSelection( [ "/A/C/E" ] )
		setExpandedPaths( [ "/", "/A", "/A/C" ] )

		view.expandSelection()

		self.assertEqual( getExpandedPaths(), set( [ "/", "/A", "/A/C" ] ) )
		self.assertEqual( getSelection(), set( [ "/A/C/E" ] ) )

		# try to collapse one level

		view.collapseSelection()

		self.assertEqual( getExpandedPaths(), set( [ "/", "/A" ] ) )
		self.assertEqual( getSelection(), set( [ "/A/C" ] ) )

		# try to collapse one more

		view.collapseSelection()

		self.assertEqual( getExpandedPaths(), set( [ "/" ] ) )
		self.assertEqual( getSelection(), set( [ "/A" ] ) )

		# now expand one level again

		view.expandSelection( depth = 1 )

		self.assertEqual( getExpandedPaths(), set( [ "/", "/A" ] ) )
		self.assertEqual( getSelection(), set( [ "/A/B", "/A/C" ] ) )

		# and expand again

		view.expandSelection( depth = 1 )

		self.assertEqual( getExpandedPaths(), set( [ "/", "/A", "/A/C" ] ) )
		self.assertEqual( getSelection(), set( [ "/A/B", "/A/C/D", "/A/C/E" ] ) )

		# and collapse

		view.collapseSelection()

		self.assertEqual( getExpandedPaths(), set( [ "/" ] ) )
		self.assertEqual( getSelection(), set( [ "/A", "/A/C" ] ) )

	def testLookThrough( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		script["camera"] = GafferScene.Camera()
		script["camera"]["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["sphere"]["out"] )
		script["group"]["in"][1].setInput( script["camera"]["out"] )

		with GafferUI.Window() as window :
			viewer = GafferUI.Viewer( script )

		window.setVisible( True )

		viewer.setNodeSet( Gaffer.StandardSet( [ script["group"] ] ) )
		view = viewer.view()
		self.assertTrue( isinstance( view, GafferSceneUI.SceneView ) )

		def setViewCameraTransform( matrix ) :

			view.viewportGadget().setCameraTransform( matrix )

		def getViewCameraTransform() :

			return view.viewportGadget().getCameraTransform()

		# Simulate the user translating the camera.
		setViewCameraTransform( imath.M44f().translate( imath.V3f( 100, 0, 0 ) ) )
		self.assertEqual( getViewCameraTransform(), imath.M44f().translate( imath.V3f( 100, 0, 0 ) ) )

		# Set the path for the look-through camera, but don't activate it - nothing should have changed.
		view["camera"]["lookThroughCamera"].setValue( "/group/camera" )
		self.assertEqual( getViewCameraTransform(), imath.M44f().translate( imath.V3f( 100, 0, 0 ) ) )

		# Enable the look-through - the camera should update.
		view["camera"]["lookThroughEnabled"].setValue( True )
		self.waitForIdle( 100 )
		self.assertEqual( getViewCameraTransform(), script["group"]["out"].transform( "/group/camera" ) )

		# Disable the look-through - the camera should revert to its previous position.
		view["camera"]["lookThroughEnabled"].setValue( False )
		self.waitForIdle( 100 )
		self.assertEqual( getViewCameraTransform(), imath.M44f().translate( imath.V3f( 100, 0, 0 ) ) )

		# Simulate the user moving the viewport camera, and then move the (now disabled) look-through
		# camera. The user movement should win out.
		setViewCameraTransform( imath.M44f().translate( imath.V3f( 200, 0, 0 ) ) )
		self.assertEqual( getViewCameraTransform(), imath.M44f().translate( imath.V3f( 200, 0, 0 ) ) )
		script["camera"]["transform"]["translate"].setValue( imath.V3f( 2, 0, 0 ) )
		self.waitForIdle( 100 )
		self.assertEqual( getViewCameraTransform(), imath.M44f().translate( imath.V3f( 200, 0, 0 ) ) )

		# Change the viewer context - since look-through is disabled the user camera should not move.
		viewer.getContext().setFrame( 10 )
		self.waitForIdle( 100 )
		self.assertEqual( getViewCameraTransform(), imath.M44f().translate( imath.V3f( 200, 0, 0 ) ) )

		# Work around "Internal C++ object (PySide.QtWidgets.QWidget) already deleted" error. In an
		# ideal world we'll fix this, but it's unrelated to what we're testing here.
		window.removeChild( viewer )

	def testFrame( self ) :

		script = Gaffer.ScriptNode()

		script["Sphere"] = GafferScene.Sphere()
		script["Sphere1"] = GafferScene.Sphere()
		script["Sphere"]["transform"]["translate"].setValue( imath.V3f( -10, 0, 0 ) )
		script["Sphere1"]["transform"]["translate"].setValue( imath.V3f( 10, 0, 0 ) )

		script["Group"] = GafferScene.Group()
		script["Group"]["in"][0].setInput( script["Sphere"]["out"] )
		script["Group"]["in"][1].setInput( script["Sphere1"]["out"] )

		view = GafferUI.View.create( script["Group"]["out"] )
		self.assertTrue( isinstance( view, GafferSceneUI.SceneView ) )
		self.assertTrue( view["in"].getInput().isSame( script["Group"]["out"] ) )

		def cameraContains( scene, objectPath ) :

			camera = view.viewportGadget().getCamera()
			screen = imath.Box2f( imath.V2f( 0 ), imath.V2f( camera.getResolution() ) )

			worldBound = scene.bound( objectPath ) * scene.fullTransform( objectPath )

			for p in [
				imath.V3f( worldBound.min().x, worldBound.min().y, worldBound.min().z ),
				imath.V3f( worldBound.min().x, worldBound.min().y, worldBound.max().z ),
				imath.V3f( worldBound.min().x, worldBound.max().y, worldBound.max().z ),
				imath.V3f( worldBound.min().x, worldBound.max().y, worldBound.min().z ),
				imath.V3f( worldBound.max().x, worldBound.max().y, worldBound.min().z ),
				imath.V3f( worldBound.max().x, worldBound.min().y, worldBound.min().z ),
				imath.V3f( worldBound.max().x, worldBound.min().y, worldBound.max().z ),
				imath.V3f( worldBound.max().x, worldBound.max().y, worldBound.max().z ),
			] :
				rp = view.viewportGadget().worldToRasterSpace( p )
				if not screen.intersects( rp ) :
					return False

			return True

		self.assertFalse( cameraContains( script["Group"]["out"], "/group" ) )
		self.assertFalse( cameraContains( script["Group"]["out"], "/group/sphere" ) )
		self.assertFalse( cameraContains( script["Group"]["out"], "/group/sphere1" ) )

		view.frame( IECore.PathMatcher( [ "/group/sphere" ] ), direction = imath.V3f( 0, 0, 1 ) )
		self.assertFalse( cameraContains( script["Group"]["out"], "/group" ) )
		self.assertTrue( cameraContains( script["Group"]["out"], "/group/sphere" ) )
		self.assertFalse( cameraContains( script["Group"]["out"], "/group/sphere1" ) )

		view.frame( IECore.PathMatcher( [ "/group/sphere1" ] ), direction = imath.V3f( 0, 0, 1 ) )
		self.assertFalse( cameraContains( script["Group"]["out"], "/group" ) )
		self.assertFalse( cameraContains( script["Group"]["out"], "/group/sphere" ) )
		self.assertTrue( cameraContains( script["Group"]["out"], "/group/sphere1" ) )

		view.frame( IECore.PathMatcher( [ "/group/sp*" ] ), direction = imath.V3f( 0, 0, 1 ) )
		self.assertTrue( cameraContains( script["Group"]["out"], "/group" ) )
		self.assertTrue( cameraContains( script["Group"]["out"], "/group/sphere" ) )
		self.assertTrue( cameraContains( script["Group"]["out"], "/group/sphere1" ) )

	def testClippingPlanesAndFOV( self ) :

		script = Gaffer.ScriptNode()
		script["camera"] = GafferScene.Camera()

		view = GafferUI.View.create( script["camera"]["out"] )

		def assertDefaultCamera() :

			# Force update
			view.viewportGadget().preRenderSignal()( view.viewportGadget() )

			self.assertEqual(
				view["camera"]["clippingPlanes"].getValue(),
				view.viewportGadget().getCamera().parameters()["clippingPlanes"].value
			)
			self.assertAlmostEqual(
				view["camera"]["fieldOfView"].getValue(),
				view.viewportGadget().getCamera().calculateFieldOfView()[0], places = 5
			)

		assertDefaultCamera()

		view["camera"]["clippingPlanes"].setValue( imath.V2f( 1, 10 ) )
		assertDefaultCamera()

		view["camera"]["fieldOfView"].setValue( 40 )
		assertDefaultCamera()

		def assertLookThroughCamera() :

			# Force update
			view.viewportGadget().preRenderSignal()( view.viewportGadget() )

			self.assertEqual(
				script["camera"]["clippingPlanes"].getValue(),
				view.viewportGadget().getCamera().parameters()["clippingPlanes"].value
			)
			self.assertAlmostEqual(
				script["camera"]["fieldOfView"].getValue(),
				view.viewportGadget().getCamera().calculateFieldOfView()[0], places = 5
			)

		# Quick hack - in order to compare FOV, we don't want the 40 border pixels added to the viewport
		# camera to be a significant part of the FOV.  Just set the resolution to be enormous so that the
		# border is insignificant
		view.viewportGadget().setViewport( imath.V2i( 10000000000000 ) )
		view["camera"]["lookThroughCamera"].setValue( "/camera" )
		view["camera"]["lookThroughEnabled"].setValue( True )

		assertLookThroughCamera()

		view["camera"]["lookThroughEnabled"].setValue( False )

		assertDefaultCamera()

		view["camera"]["lookThroughEnabled"].setValue( True )

		assertLookThroughCamera()

		view["camera"]["clippingPlanes"].setValue( imath.V2f( 10, 20 ) )
		view["camera"]["fieldOfView"].setValue( 60 )

		assertLookThroughCamera()

		view["camera"]["lookThroughEnabled"].setValue( False )

		assertDefaultCamera()

	def testInspectorEditability( self ) :

		# Required for animation
		s = Gaffer.ScriptNode()

		light = GafferSceneTest.TestLight()
		group = GafferScene.Group()
		editScope1 = Gaffer.EditScope()
		editScope2 = Gaffer.EditScope()

		s["light"] = light
		s["group"] = group
		s["editScope1"] = editScope1
		s["editScope2"] = editScope2

		group["in"][0].setInput( light["out"] )

		editScope1.setName( "EditScope1" )
		editScope1.setup( group["out"] )
		editScope1["in"].setInput( group["out"] )

		editScope2.setName( "EditScope2" )
		editScope2.setup( editScope1["out"] )
		editScope2["in"].setInput( editScope1["out"] )

		def inspector( scene, path, parameter, editScope, attribute="light" ) :

			history = GafferScene.SceneAlgo.history( scene["attributes"], path )
			attributeHistory = GafferScene.SceneAlgo.attributeHistory( history, attribute )
			return GafferSceneUI.SceneViewUI._ParameterInspector( attributeHistory, parameter, editScope )

		def assertOutcome( inspector, editable, edit = None, error = "", warning = "", acquire = True ) :

			self.assertEqual( inspector.editable(), editable )
			self.assertEqual( inspector.errorMessage(), error )
			self.assertEqual( inspector.warningMessage(), warning )
			if acquire :
				acquiredEdit = inspector.acquireEdit()
				self.assertEqual( acquiredEdit, edit, msg = "%s != %s" % (
					acquiredEdit.fullName() if acquiredEdit is not None else None,
					edit.fullName() if edit is not None else None
				) )

		# Should be able to edit light directly.

		i = inspector( group["out"], "/group/light", "intensity", None )
		assertOutcome( i, True, light["parameters"]["intensity"] )

		# Even if there is an edit scope in the way

		i = inspector( editScope1["out"], "/group/light", "intensity", None )
		assertOutcome( i, True, light["parameters"]["intensity"] )

		# We shouldn't be able to edit if we've been told to use an EditScope and it isn't in the history.

		i = inspector( group["out"], "/group/light", "intensity", editScope1 )
		assertOutcome( i, False, error = "The target Edit Scope 'EditScope1' is not in the scene history." )

		# If it is in the history though, and we're told to use it, then we will.

		i = inspector( editScope2["out"], "/group/light", "intensity", editScope2 )
		assertOutcome( i, True, acquire = False )
		self.assertIsNone(
			GafferScene.EditScopeAlgo.acquireParameterEdit(
				editScope2, "/group/light", "light", ( "", "intensity" ), createIfNecessary = False
			)
		)
		lightEditScope2Edit = i.acquireEdit()
		self.assertIsNotNone( lightEditScope2Edit )
		self.assertEqual(
			lightEditScope2Edit,
			GafferScene.EditScopeAlgo.acquireParameterEdit(
				editScope2, "/group/light", "light", ( "", "intensity" ), createIfNecessary = False
			)
		)

		# If there's an edit downstream of the EditScope we're asked to use,
		# then we're allowed to be editable still

		i = inspector( editScope2["out"], "/group/light", "intensity", editScope1 )
		lightEditScope1Edit = i.acquireEdit()
		self.assertIsNotNone( lightEditScope1Edit )
		self.assertTrue( i.editable() )
		self.assertEqual(
			lightEditScope1Edit,
			GafferScene.EditScopeAlgo.acquireParameterEdit(
				editScope1, "/group/light", "light", ( "", "intensity" ), createIfNecessary = False
			)
		)
		self.assertEqual( i.errorMessage(), "" )
		self.assertEqual( i.warningMessage(), "" )

		# If there is a source node inside an edit scope, make sure we use that

		editScope1["light2"] = GafferSceneTest.TestLight()
		editScope1["light2"]["name"].setValue( "light2" )
		editScope1["parentLight2"] = GafferScene.Parent()
		editScope1["parentLight2"]["parent"].setValue( "/" )
		editScope1["parentLight2"]["children"][0].setInput( editScope1["light2"]["out"] )
		editScope1["parentLight2"]["in"].setInput( editScope1["BoxIn"]["out"] )
		editScope1["LightEdits"]["in"].setInput( editScope1["parentLight2"]["out"] )

		i = inspector( editScope2["out"], "/light2", "intensity", editScope1 )
		assertOutcome( i, True, editScope1["light2"]["parameters"]["intensity"] )

		# If there is a tweak in the scope's processor make sure we use that

		light2Edit = GafferScene.EditScopeAlgo.acquireParameterEdit(
			editScope1, "/light2", "light", ( "", "intensity" ), createIfNecessary = True
		)
		light2Edit["enabled"].setValue( True )

		i = inspector( editScope2["out"], "/light2", "intensity", editScope1 )
		assertOutcome( i, True, light2Edit )

		# If there is a manual tweak downstream of the scope's scene processor, make sure we use that

		editScope1["tweakLight2"] = GafferScene.ShaderTweaks()
		editScope1["tweakLight2"]["in"].setInput( editScope1["LightEdits"]["out"] )
		editScope1["tweakLight2Filter"] = GafferScene.PathFilter()
		editScope1["tweakLight2Filter"]["paths"].setValue( IECore.StringVectorData( [ "/light2" ] ) )
		editScope1["tweakLight2"]["filter"].setInput( editScope1["tweakLight2Filter"]["out"] )
		editScope1["BoxOut"]["in"].setInput( editScope1["tweakLight2"]["out"] )

		editScope1["tweakLight2"]["shader"].setValue( "light" )
		editScopeShaderTweak = GafferScene.TweakPlug( "intensity", imath.Color3f( 1, 0, 0 ) )
		editScope1["tweakLight2"]["tweaks"].addChild( editScopeShaderTweak )

		i = inspector( editScope2["out"], "/light2", "intensity", editScope1 )
		assertOutcome( i, True, editScopeShaderTweak )

		# If there is a manual tweak outside of an edit scope make sure we use that with no scope

		independentLightTweak = GafferScene.ShaderTweaks()
		independentLightTweak["in"].setInput( editScope2["out"] )
		independentLightTweakFilter = GafferScene.PathFilter()
		independentLightTweakFilter["paths"].setValue( IECore.StringVectorData( [ "/group/light" ] ) )
		independentLightTweak["filter"].setInput( independentLightTweakFilter["out"] )

		independentLightTweak["shader"].setValue( "light" )
		independentTweakLight2 = GafferScene.TweakPlug( "intensity", imath.Color3f( 1, 1, 0 ) )
		independentLightTweak["tweaks"].addChild( independentTweakLight2 )

		i = inspector( independentLightTweak["out"], "/group/light", "intensity", None )
		assertOutcome( i, True, independentTweakLight2 )

		# Check we show the last input plug if the source plug is an output

		exposureCurve = Gaffer.Animation.acquire( light["parameters"]["exposure"] )
		exposureCurve.addKey( Gaffer.Animation.Key( time = 1, value = 2 ) )

		i = inspector( group["out"], "/group/light", "exposure", None )
		assertOutcome( i, True, light["parameters"]["exposure"] )

		i = inspector( editScope1["out"], "/group/light", "exposure", editScope1 )
		exposureTweak = i.acquireEdit()
		exposureTweakCurve = Gaffer.Animation.acquire( exposureTweak["value"] )
		exposureTweakCurve.addKey( Gaffer.Animation.Key( time = 2, value = 4 ) )

		i = inspector( editScope1["out"], "/group/light", "exposure", editScope1 )
		assertOutcome( i, True, exposureTweak )

		# Check warning/error messages

		i = inspector( independentLightTweak["out"], "/group/light", "intensity", editScope2 )
		assertOutcome( i, True, lightEditScope2Edit, warning = "Parameter has edits downstream in 'ShaderTweaks'." )

		editScope2["enabled"].setValue( False )

		i = inspector( independentLightTweak["out"], "/group/light", "intensity", editScope2 )
		assertOutcome( i, False, error = "The target Edit Scope 'EditScope2' is disabled." )

		editScope2["enabled"].setValue( True )
		Gaffer.MetadataAlgo.setReadOnly( editScope2, True )

		i = inspector( independentLightTweak["out"], "/light2", "intensity", editScope2 )
		self.assertFalse( i.editable() )
		assertOutcome( i, False, error = "'EditScope2' is locked." )

		Gaffer.MetadataAlgo.setReadOnly( editScope2, False )
		Gaffer.MetadataAlgo.setReadOnly( editScope2["LightEdits"]["edits"], True )

		i = inspector( independentLightTweak["out"], "/light2", "intensity", editScope2 )
		assertOutcome( i, False, error = "'EditScope2.LightEdits.edits' is locked." )

		Gaffer.MetadataAlgo.setReadOnly( editScope2["LightEdits"], True )

		i = inspector( independentLightTweak["out"], "/light2", "intensity", editScope2 )
		assertOutcome( i, False, error = "'EditScope2.LightEdits' is locked." )

		shaderAssignment = GafferScene.ShaderAssignment()
		s = GafferSceneTest.TestShader()
		s["type"].setValue( "test:surface" )
		shaderAssignment["shader"].setInput( s["out"] )
		shaderAssignment["in"].setInput( independentLightTweak["out"] )
		shaderAssignmentFilter = GafferScene.PathFilter()
		shaderAssignmentFilter["paths"].setValue( IECore.StringVectorData( [ "..." ] ) )

		i = inspector( shaderAssignment["out"], "/light2", "c", None, attribute="test:surface" )
		assertOutcome( i, True, warning = "Edits to 'TestShader' may affect other locations in the scene.", acquire = False )

if __name__ == "__main__":
	unittest.main()
