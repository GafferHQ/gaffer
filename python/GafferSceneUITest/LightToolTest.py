##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

import unittest
import imath
import math

import IECore

import Gaffer
import GafferUI
import GafferTest
import GafferUITest
import GafferScene
import GafferSceneUI
import GafferSceneTest

class LightToolTest( GafferUITest.TestCase ) :

	def setUp( self ) :

		GafferUITest.TestCase.setUp( self )

		Gaffer.Metadata.registerValue( "light:testLight", "type", "spot" )
		Gaffer.Metadata.registerValue( "light:testLight", "coneAngleParameter", "coneAngle" )
		Gaffer.Metadata.registerValue( "light:testLight", "penumbraAngleParameter", "penumbraAngle" )

	def testSpotLightHandleVisibility( self ) :

		script = Gaffer.ScriptNode()

		script["spotLight1"] = GafferSceneTest.TestLight()
		script["spotLight2"] = GafferSceneTest.TestLight()

		for n in [ "spotLight1", "spotLight2" ] :
			script[n]["parameters"].addChild( Gaffer.FloatPlug( "coneAngle" ) )
			script[n]["parameters"].addChild( Gaffer.FloatPlug( "penumbraAngle" ) )

		script["light1"] = GafferSceneTest.TestLight()

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["spotLight1"]["out"] )
		script["group"]["in"][1].setInput( script["spotLight2"]["out"] )
		script["group"]["in"][2].setInput( script["light1"]["out"] )

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["group"]["out"] )

		tool = GafferSceneUI.LightTool( view )
		tool["active"].setValue( True )

		handles = { v.getName() : v for v in view.viewportGadget()["HandlesGadget"].children() }

		self.assertIn( "westConeAngleParameter", handles )
		self.assertIn( "westPenumbraAngleParameter", handles )
		self.assertIn( "southConeAngleParameter", handles )
		self.assertIn( "southPenumbraAngleParameter", handles )
		self.assertIn( "eastConeAngleParameter", handles )
		self.assertIn( "eastPenumbraAngleParameter", handles )
		self.assertIn( "northConeAngleParameter", handles )
		self.assertIn( "northPenumbraAngleParameter", handles )

		# \todo We should test that the handles are visible with a spotlight selection
		# and not visible with a non-spotlight selection. Currently handles come in as
		# `GraphComponent` which prevents testing that.

	def testDeleteNodeCrash( self ) :

		# Make a spotlight and get the LightTool to edit it.

		script = Gaffer.ScriptNode()

		script["spotLight"] = GafferSceneTest.TestLight()
		script["spotLight"]["parameters"].addChild( Gaffer.FloatPlug( "coneAngle", defaultValue = 10 ) )
		script["spotLight"]["parameters"].addChild( Gaffer.FloatPlug( "penumbraAngle", defaultValue = 1 ) )

		script["shaderAssignment"] = GafferScene.ShaderAssignment()
		script["shaderAssignment"]["in"].setInput( script["spotLight"]["out"] )

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["shaderAssignment"]["out"] )

		tool = GafferSceneUI.LightTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/light" ] ) )

		with GafferUI.Window() as window :
			gadgetWidget = GafferUI.GadgetWidget( view.viewportGadget() )
		window.setVisible( True )

		# Wait for the viewport to be rendered.

		preRenderSlot = GafferTest.CapturingSlot( view.viewportGadget().preRenderSignal() )
		while not len( preRenderSlot ) :
			self.waitForIdle( 1000 )

		# Delete the node being viewed.

		del script["shaderAssignment"]

		# Wait for the viewport to be rendered again. This used to crash, so
		# we're pretty happy if it doesn't.

		del preRenderSlot[:]
		with IECore.CapturingMessageHandler() as mh :
			while not len( preRenderSlot ) :
				self.waitForIdle( 1000 )

		# Ignore unrelated message from BackgroundTask. This needs a separate fix.
		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].message, "Unable to find ScriptNode for SceneView.__preprocessor.out" )

if __name__ == "__main__" :
	unittest.main()
