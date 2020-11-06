##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

class CameraToolTest( GafferUITest.TestCase ) :

	def testCameraEditability( self ) :

		script = Gaffer.ScriptNode()
		script["camera"] = GafferScene.Camera()

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["camera"]["out"] )

		def assertCameraEditable( cameraEditable ) :

			# Force update, since everything is done lazily in the SceneView
			view.viewportGadget().preRenderSignal()( view.viewportGadget() )

			self.assertEqual(
				view.viewportGadget().getCameraEditable(),
				cameraEditable
			)

		assertCameraEditable( True )

		view["camera"]["lookThroughEnabled"].setValue( True )
		view["camera"]["lookThroughCamera"].setValue( "/camera" )
		assertCameraEditable( False )

		tool = GafferSceneUI.CameraTool( view )
		tool["active"].setValue( True )
		assertCameraEditable( True )

		tool["active"].setValue( False )
		assertCameraEditable( False )

		tool["active"].setValue( True )
		assertCameraEditable( True )

		Gaffer.MetadataAlgo.setReadOnly( script["camera"]["transform"]["scale"], True )
		assertCameraEditable( True )

		Gaffer.MetadataAlgo.setReadOnly( script["camera"]["transform"]["translate"]["x"], True )
		assertCameraEditable( False )
		Gaffer.MetadataAlgo.setReadOnly( script["camera"]["transform"]["translate"]["x"], False )
		assertCameraEditable( True )

		Gaffer.MetadataAlgo.setReadOnly( script["camera"]["transform"]["rotate"]["x"], True )
		assertCameraEditable( False )
		Gaffer.MetadataAlgo.setReadOnly( script["camera"]["transform"]["rotate"]["x"], False )
		assertCameraEditable( True )

	def testEditTransform( self ) :

		script = Gaffer.ScriptNode()
		script["camera"] = GafferScene.Camera()

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["camera"]["out"] )

		view["camera"]["lookThroughEnabled"].setValue( True )
		view["camera"]["lookThroughCamera"].setValue( "/camera" )

		tool = GafferSceneUI.CameraTool( view )
		tool["active"].setValue( True )

		view.viewportGadget().setCameraTransform(
			imath.M44f().translate( imath.V3f( 1, 2, 3 ) )
		)

		self.assertEqual( script.undoAvailable(), True )
		self.assertEqual(
			script["camera"]["transform"]["translate"].getValue(),
			imath.V3f( 1, 2, 3 )
		)

		script.undo()
		self.assertEqual( script.undoAvailable(), False )
		self.assertEqual(
			script["camera"]["transform"]["translate"].getValue(),
			imath.V3f( 0 )
		)

		script.redo()
		self.assertEqual( script.undoAvailable(), True )
		self.assertEqual(
			script["camera"]["transform"]["translate"].getValue(),
			imath.V3f( 1, 2, 3 )
		)

	def testNestedTransform( self ) :

		script = Gaffer.ScriptNode()
		script["camera"] = GafferScene.Camera()
		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["camera"]["out"] )
		script["group"]["transform"]["rotate"]["y"].setValue( 90 )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["group"]["out"] )

		view["camera"]["lookThroughEnabled"].setValue( True )
		view["camera"]["lookThroughCamera"].setValue( "/group/camera" )

		tool = GafferSceneUI.CameraTool( view )
		tool["active"].setValue( True )

		cameraTransform = imath.M44f().translate( imath.V3f( 1, 2, 3 ) )
		view.viewportGadget().setCameraTransform( cameraTransform )

		self.assertTrue(
			cameraTransform.equalWithAbsError(
				script["group"]["out"].fullTransform( "/group/camera" ),
				0.00001
			)
		)

	def testSwitchBackToDefaultCamera( self ) :

		script = Gaffer.ScriptNode()
		script["camera"] = GafferScene.Camera()
		script["camera"]["fieldOfView"].setValue( 15 )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["camera"]["out"] )

		# Force update, since everything is done lazily in the SceneView
		view.viewportGadget().preRenderSignal()( view.viewportGadget() )

		# Remember what the default camera looks like
		defaultCamera = view.viewportGadget().getCamera()
		defaultCameraTransform = imath.M44f().translate( imath.V3f( 10, 11, 12 ) )
		defaultCenterOfInterest = 2.5
		view.viewportGadget().setCameraTransform( defaultCameraTransform )
		view.viewportGadget().setCenterOfInterest( defaultCenterOfInterest )

		# Look through a scene camera
		view["camera"]["lookThroughCamera"].setValue( "/camera" )
		view["camera"]["lookThroughEnabled"].setValue( True )

		view.viewportGadget().preRenderSignal()( view.viewportGadget() )
		self.assertNotEqual( view.viewportGadget().getCamera(), defaultCamera )
		self.assertEqual( view.viewportGadget().getCameraTransform(), script["camera"]["out"].fullTransform( "/camera" ) )

		# Make an edit with the CameraTool, and change the transform and
		# center of interest.

		tool = GafferSceneUI.CameraTool( view )
		tool["active"].setValue( True )

		view.viewportGadget().frame( imath.Box3f( imath.V3f( -1000 ), imath.V3f( 1000 ) ) )
		self.assertNotEqual( view.viewportGadget().getCenterOfInterest(), defaultCenterOfInterest )

		# Switch back out of the tool and make sure the default camera
		# is restored.

		view["camera"]["lookThroughEnabled"].setValue( False )
		view.viewportGadget().preRenderSignal()( view.viewportGadget() )

		self.assertEqual( view.viewportGadget().getCamera(), defaultCamera )
		self.assertEqual( view.viewportGadget().getCameraTransform(), defaultCameraTransform )
		self.assertEqual( view.viewportGadget().getCenterOfInterest(), defaultCenterOfInterest )

	def testCenterOfInterestAndUndo( self ) :

		script = Gaffer.ScriptNode()
		script["camera"] = GafferScene.Camera()

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["camera"]["out"] )
		view["camera"]["lookThroughCamera"].setValue( "/camera" )
		view["camera"]["lookThroughEnabled"].setValue( True )

		tool = GafferSceneUI.CameraTool( view )
		tool["active"].setValue( True )

		centerOfInterest1 = view.viewportGadget().getCenterOfInterest()

		with Gaffer.UndoScope( script ) :
			view.viewportGadget().frame( imath.Box3f( imath.V3f( 0 ), imath.V3f( 1 ) ) )

		centerOfInterest2 = view.viewportGadget().getCenterOfInterest()

		with Gaffer.UndoScope( script ) :
			view.viewportGadget().frame( imath.Box3f( imath.V3f( 0 ), imath.V3f( 10 ) ) )

		centerOfInterest3 = view.viewportGadget().getCenterOfInterest()

		def assertCenterOfInterestEqual( centerOfInterest ) :

			# Force update, since everything is done lazily in the SceneView
			view.viewportGadget().preRenderSignal()( view.viewportGadget() )
			self.assertEqual(
				view.viewportGadget().getCenterOfInterest(),
				centerOfInterest
			)

		script.undo()
		assertCenterOfInterestEqual( centerOfInterest2 )

		script.undo()
		assertCenterOfInterestEqual( centerOfInterest1 )

		script.redo()
		assertCenterOfInterestEqual( centerOfInterest2 )

		script.redo()
		assertCenterOfInterestEqual( centerOfInterest3 )

	def testTransformNode( self ) :

		script = Gaffer.ScriptNode()

		script["camera"] = GafferScene.Camera()
		script["camera"]["transform"]["translate"]["z"].setValue( 1 )
		script["camera"]["transform"]["rotate"]["y"].setValue( 90 )

		script["filter"] = GafferScene.PathFilter()
		script["filter"]["paths"].setValue( IECore.StringVectorData( [ "/camera" ] ) )

		script["transform"] = GafferScene.Transform()
		script["transform"]["in"].setInput( script["camera"]["out"] )
		script["transform"]["filter"].setInput( script["filter"]["out"] )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["transform"]["out"] )

		view["camera"]["lookThroughEnabled"].setValue( True )
		view["camera"]["lookThroughCamera"].setValue( "/camera" )

		tool = GafferSceneUI.CameraTool( view )
		tool["active"].setValue( True )

		cameraTransform = imath.M44f().translate( imath.V3f( 1, 2, 3 ) ) * imath.M44f().rotate( IECore.degreesToRadians( imath.V3f( 15, 90, 0 ) ) )

		for space in GafferScene.Transform.Space.values.values() :

			script["transform"]["space"].setValue( space )
			view.viewportGadget().preRenderSignal()( view.viewportGadget() )
			view.viewportGadget().setCameraTransform( cameraTransform )

			self.assertTrue(
				cameraTransform.equalWithAbsError(
					script["transform"]["out"].fullTransform( "/camera" ),
					0.00001
				)
			)

	def testEditScopes( self ) :

		script = Gaffer.ScriptNode()
		script["camera"] = GafferScene.Camera()

		script["editScope"] = Gaffer.EditScope()
		script["editScope"].setup( script["camera"]["out"] )
		script["editScope"]["in"].setInput( script["camera"]["out"] )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["editScope"]["out"] )

		view["camera"]["lookThroughEnabled"].setValue( True )
		view["camera"]["lookThroughCamera"].setValue( "/camera" )

		tool = GafferSceneUI.CameraTool( view )
		tool["active"].setValue( True )

		script["camera"]["transform"]["translate"].setValue( imath.V3f( 1, 2, 3 ) )
		script["camera"]["transform"]["rotate"].setValue( imath.V3f( 1, 2, 3 ) )

		# Without EditScope, should edit Camera node directly.

		cameraTransform = imath.M44f().translate( imath.V3f( 10, 5, 1 ) ).rotate( imath.V3f( math.pi / 4 ) )
		view.viewportGadget().setCameraTransform( cameraTransform )

		self.assertFalse( GafferScene.EditScopeAlgo.hasTransformEdit( script["editScope"], "/camera" ) )
		self.assertTrue(
			script["camera"]["out"].transform( "/camera" ).equalWithAbsError(
				cameraTransform, 0.00001
			),
		)

		# With EditScope

		view["editScope"].setInput( script["editScope"]["out"] )

		cameraTransform.translate( imath.V3f( 1, 2, 3 ) )
		view.viewportGadget().setCameraTransform(
			cameraTransform
		)

		self.assertTrue( GafferScene.EditScopeAlgo.hasTransformEdit( script["editScope"], "/camera" ) )
		self.assertTrue(
			script["editScope"]["out"].transform( "/camera" ).equalWithAbsError(
				cameraTransform, 0.00001
			),
		)
		self.assertTrue( GafferScene.EditScopeAlgo.hasTransformEdit( script["editScope"], "/camera" ) )

	def testNoUnecessaryHistoryCalls( self ) :

		script = Gaffer.ScriptNode()
		script["camera"] = GafferScene.Camera()

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["camera"]["out"] )

		view["camera"]["lookThroughEnabled"].setValue( True )
		view["camera"]["lookThroughCamera"].setValue( "/camera" )

		tool = GafferSceneUI.CameraTool( view )
		tool["active"].setValue( True )

		# Force CameraTool update, since it is done lazily just prior to render.
		view.viewportGadget().preRenderSignal()( view.viewportGadget() )

		with Gaffer.ContextMonitor() as cm :

			view.viewportGadget().setCameraTransform(
				imath.M44f().translate( imath.V3f( 1, 2, 3 ) )
			)

			# Force update
			view.viewportGadget().preRenderSignal()( view.viewportGadget() )

		# We do not want the CameraTool to have performed a `SceneAlgo::history`
		# query during the edit, as they can be expensive and aren't suitable
		# for repeated use during drags etc.
		self.assertNotIn( GafferScene.SceneAlgo.historyIDContextName(), cm.combinedStatistics().variableNames() )

		self.assertEqual(
			script["camera"]["transform"]["translate"].getValue(),
			imath.V3f( 1, 2, 3 )
		)

if __name__ == "__main__":
	unittest.main()
