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

	def testInitialClippingPlanes( self ) :

		sphere = GafferScene.Sphere()
		view = GafferUI.View.create( sphere["out"] )
		view["camera"]["clippingPlanes"].setValue( imath.V2f( 1, 10 ) )

		view.viewportGadget().preRenderSignal()( view.viewportGadget() ) # Force update
		self.assertEqual(
			view.viewportGadget().getCamera().getClippingPlanes(),
			imath.V2f( 1, 10 )
		)

	def testClippingPlanesAndFOV( self ) :

		script = Gaffer.ScriptNode()
		script["camera"] = GafferScene.Camera()

		view = GafferUI.View.create( script["camera"]["out"] )

		def assertDefaultCamera() :

			# Force update
			view.viewportGadget().preRenderSignal()( view.viewportGadget() )

			self.assertEqual(
				view["camera"]["clippingPlanes"].getValue(),
				view.viewportGadget().getCamera().getClippingPlanes()
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

	def testClippingPlaneConstraints( self ) :

		sphere = GafferScene.Sphere()
		view = GafferUI.View.create( sphere["out"] )

		# Far must be greater than near

		view["camera"]["clippingPlanes"].setValue( imath.V2f( 10, 1 ) )
		self.assertEqual(
			view["camera"]["clippingPlanes"].getValue(),
			imath.V2f( 1, 10 )
		)

		view.viewportGadget().preRenderSignal()( view.viewportGadget() ) # Force update
		self.assertEqual(
			view.viewportGadget().getCamera().getClippingPlanes(),
			imath.V2f( 1, 10 )
		)

		# Values must be 0.0001 at a minimum

		view["camera"]["clippingPlanes"].setValue( imath.V2f( 0, 1 ) )
		self.assertEqual(
			view["camera"]["clippingPlanes"].getValue(),
			imath.V2f( 0.0001, 1 )
		)

		view.viewportGadget().preRenderSignal()( view.viewportGadget() ) # Force update
		self.assertEqual(
			view.viewportGadget().getCamera().getClippingPlanes(),
			imath.V2f( 0.0001, 1 )
		)

	def testChangingClippingPlanesUpdatesAllFreeCameras( self ) :

		sphere = GafferScene.Sphere()
		view = GafferUI.View.create( sphere["out"] )

		expectedClippingPlanes = view["camera"]["clippingPlanes"].getValue()
		view.viewportGadget().preRenderSignal()( view.viewportGadget() ) # Force update
		self.assertEqual( view.viewportGadget().getCamera().getClippingPlanes(), expectedClippingPlanes )

		view["camera"]["freeCamera"].setValue( "top" )
		view.viewportGadget().preRenderSignal()( view.viewportGadget() ) # Force update
		self.assertEqual( view.viewportGadget().getCamera().getClippingPlanes(), expectedClippingPlanes )
		self.assertEqual( view["camera"]["clippingPlanes"].getValue(), expectedClippingPlanes )

		expectedClippingPlanes = imath.V2f( 1, 10 )
		view["camera"]["clippingPlanes"].setValue( expectedClippingPlanes )
		view.viewportGadget().preRenderSignal()( view.viewportGadget() ) # Force update
		self.assertEqual( view.viewportGadget().getCamera().getClippingPlanes(), expectedClippingPlanes )
		self.assertEqual( view["camera"]["clippingPlanes"].getValue(), expectedClippingPlanes )

		view["camera"]["freeCamera"].setValue( "perspective" )
		view.viewportGadget().preRenderSignal()( view.viewportGadget() ) # Force update
		self.assertEqual( view.viewportGadget().getCamera().getClippingPlanes(), expectedClippingPlanes )
		self.assertEqual( view["camera"]["clippingPlanes"].getValue(), expectedClippingPlanes )

if __name__ == "__main__":
	unittest.main()
