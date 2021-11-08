##########################################################################
#
#  Copyright (c) 2020, Image Engine Design Inc. All rights reserved.
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
import math
import os
import unittest

import IECore
import IECoreScene

import Gaffer
import GafferArnold
import GafferImage
import GafferImageUI
import GafferScene
import GafferSceneTest
import GafferTest
import GafferUI
import GafferUITest
import GafferImageTest

from Qt import QtCore

@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
class InteractiveArnoldRenderPerformanceTest( GafferUITest.TestCase ) :

	# Arnold outputs licensing warnings that would cause failures
	failureMessageLevel = IECore.MessageHandler.Level.Error

	def runInteractive( self, useUI, useBlur, resolution ):

		script = Gaffer.ScriptNode()

		script["Camera"] = GafferScene.Camera()
		script["Camera"]["transform"]["translate"]["z"].setValue( 6 )

		script["Sphere"] = GafferScene.Sphere( "Sphere" )
		script["Sphere"]["radius"].setValue( 10 )

		script["ImageShader"] = GafferArnold.ArnoldShader()
		script["ImageShader"].loadShader( "image" )
		script["ImageShader"]["parameters"]["filename"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/GafferChecker.exr" )
		script["ImageShader"]["parameters"]["sscale"].setValue( 16 )
		script["ImageShader"]["parameters"]["tscale"].setValue( 16 )

		script["ShaderAssignment"] = GafferScene.ShaderAssignment()
		script["ShaderAssignment"]["in"].setInput( script["Sphere"]["out"] )
		script["ShaderAssignment"]["shader"].setInput( script["ImageShader"]["out"] )

		script["Group"] = GafferScene.Group()
		script["Group"]["in"][0].setInput( script["Camera"]["out"] )
		script["Group"]["in"][1].setInput( script["ShaderAssignment"]["out"] )

		script["StandardOptions"] = GafferScene.StandardOptions()
		script["StandardOptions"]["in"].setInput( script["Group"]["out"] )
		script["StandardOptions"]["options"]["renderCamera"]["value"].setValue( '/group/camera' )
		script["StandardOptions"]["options"]["renderCamera"]["enabled"].setValue( True )
		script["StandardOptions"]["options"]["renderResolution"]["value"].setValue( imath.V2i( resolution, resolution ) )
		script["StandardOptions"]["options"]["renderResolution"]["enabled"].setValue( True )

		script["ArnoldOptions"] = GafferArnold.ArnoldOptions( "ArnoldOptions" )
		script["ArnoldOptions"]["in"].setInput( script["StandardOptions"]["out"] )
		# Make sure we leave some CPU available for Gaffer
		script["ArnoldOptions"]["options"]["threads"]["value"].setValue( -1 )
		script["ArnoldOptions"]["options"]["threads"]["enabled"].setValue( True )

		script["Outputs"] = GafferScene.Outputs()
		script["Outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				"Interactive/Beauty",
				"ieDisplay",
				"rgba",
				{
					"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
					"driverType" : 'ClientDisplayDriver',
					"displayHost" : 'localhost',
					"displayPort" : str( GafferImage.Catalogue.displayDriverServer().portNumber() ),
					"remoteDisplayType" : 'GafferImage::GafferDisplayDriver',
					"filter" : 'box',
				}
			)
		)
		script["Outputs"]["in"].setInput( script["ArnoldOptions"]["out"] )

		script["InteractiveArnoldRender"] = GafferArnold.InteractiveArnoldRender()
		script["InteractiveArnoldRender"]["in"].setInput( script["Outputs"]["out"] )

		script["Catalogue"] = GafferImage.Catalogue( "Catalogue" )
		script["Catalogue"]["directory"].setValue( self.temporaryDirectory() + "/catalogues/test" )

		script["Blur"] = GafferImage.Blur( "Blur" )
		script["Blur"]["in"].setInput( script["Catalogue"]["out"] )
		script["Blur"]["radius"]["x"].setValue( 1.0 )
		script["Blur"]["radius"]["y"].setValue( 1.0 )

		watchNode = script["Blur"] if useBlur else script["Catalogue"]

		if useUI:

			with GafferUI.Window() as window :
				window.setFullScreen( True )
				viewer = GafferUI.Viewer( script )

			window.setVisible( True )
			viewer.setNodeSet( Gaffer.StandardSet( [ watchNode ] ) )


			script['InteractiveArnoldRender']['state'].setValue( GafferScene.InteractiveRender.State.Running )
			self.waitForIdle( 10 )

			viewer.view().viewportGadget().frame( viewer.view().viewportGadget().getPrimaryChild().bound(), imath.V3f( 0, 0, 1 ) )

			frameCounter = {'i' : 0}
			def testFunc():
				frameCounter['i'] += 1
				script["Camera"]["transform"]["translate"]["x"].setValue( math.sin( frameCounter['i'] * 0.1 ) )
				if frameCounter['i'] >= 50:
					GafferUI.EventLoop.mainEventLoop().stop()

			timer = QtCore.QTimer()
			timer.setInterval( 20 )
			timer.timeout.connect( testFunc )

			GafferImageUI.ImageGadget.resetTileUpdateCount()
			timer.start()

			with GafferTest.TestRunner.PerformanceScope() as ps:
				GafferUI.EventLoop.mainEventLoop().start()
				ps.setNumIterations( GafferImageUI.ImageGadget.tileUpdateCount() )

			script['InteractiveArnoldRender']['state'].setValue( GafferScene.InteractiveRender.State.Stopped )

			del window, viewer, timer
			self.waitForIdle( 10 )

		else:
			with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as h :

				with IECore.CapturingMessageHandler() as mh :
					script['InteractiveArnoldRender']['state'].setValue( GafferScene.InteractiveRender.State.Running )
					h.waitFor( 2 )
				arnoldStartupErrors = mh.messages

				tc = Gaffer.ScopedConnection( GafferImageTest.connectProcessTilesToPlugDirtiedSignal( watchNode["out"] ) )

				with GafferTest.TestRunner.PerformanceScope() as ps:
					with Gaffer.PerformanceMonitor() as m:
						for i in range( 250 ):
							script["Camera"]["transform"]["translate"]["x"].setValue( math.sin( ( i + 1 ) * 0.1 ) )
							h.waitFor( 0.02 )

					ps.setNumIterations( m.plugStatistics( watchNode["out"]["channelData"].source() ).computeCount )


				script['InteractiveArnoldRender']['state'].setValue( GafferScene.InteractiveRender.State.Stopped )


	# NOTE: These tests should be a lot more effective in terms of measuring exact performance
	# if the "repeat" parameter is turned up, but I've currently set it to just 1 because:
	# * I wanted to minimize the time spent on the UI tests
	# * The non-UI tests for a mysterious reason run faster the first time, so adding more repetitions doesn't
	#   affect the minimum result

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testPerf( self ) :

		self.runInteractive( False, False, 2000 )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testPerfWithBlur( self ) :
		self.runInteractive( False, True, 1000 )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testUIPerf( self ) :

		self.runInteractive( True, False, 2000 )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testUIPerfWithBlur( self ) :
		self.runInteractive( True, True, 1000 )


if __name__ == "__main__":
	unittest.main()
