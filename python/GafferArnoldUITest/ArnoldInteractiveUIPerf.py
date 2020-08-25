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

import IECore
import imath
import math
import os
import time

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

class ArnoldInteractiveUIPerf( GafferUITest.TestCase ) :

	def testWeirdness( self ):
		Gaffer.ValuePlug.weirdPrep()


		script = Gaffer.ScriptNode()

		script["Camera"] = GafferScene.Camera()
		script["Group"] = GafferScene.Group()
		script["StandardOptions"] = GafferScene.StandardOptions()
		script["Outputs"] = GafferScene.Outputs()
		script["Outputs"]["outputs"].addChild( Gaffer.ValuePlug( "output1", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
		script["Outputs"]["outputs"]["output1"].addChild( Gaffer.StringPlug( "name", defaultValue = '' ) )
		script["Outputs"]["outputs"]["output1"].addChild( Gaffer.BoolPlug( "active", defaultValue = True ) )
		script["Outputs"]["outputs"]["output1"].addChild( Gaffer.StringPlug( "fileName", defaultValue = '' ) )
		script["Outputs"]["outputs"]["output1"].addChild( Gaffer.StringPlug( "type", defaultValue = '' ) )
		script["Outputs"]["outputs"]["output1"].addChild( Gaffer.StringPlug( "data", defaultValue = '' ) )
		script["Outputs"]["outputs"]["output1"].addChild( Gaffer.CompoundDataPlug( "parameters" ) )
		script["Outputs"]["outputs"]["output1"]["parameters"].addChild( Gaffer.NameValuePlug( "driverType", Gaffer.StringPlug( "value", defaultValue = 'ClientDisplayDriver' ), "driverType" ) )
		script["Outputs"]["outputs"]["output1"]["parameters"].addChild( Gaffer.NameValuePlug( "displayHost", Gaffer.StringPlug( "value", defaultValue = 'localhost' ), "displayHost" ) )
		script["Outputs"]["outputs"]["output1"]["parameters"].addChild( Gaffer.NameValuePlug( "displayPort", Gaffer.StringPlug( "value", defaultValue = str( GafferImage.Catalogue.displayDriverServer().portNumber() ) ) ) )
		script["Outputs"]["outputs"]["output1"]["parameters"].addChild( Gaffer.NameValuePlug( "remoteDisplayType", Gaffer.StringPlug( "value", defaultValue = 'GafferImage::GafferDisplayDriver' ) ) )
		script["Catalogue"] = GafferImage.Catalogue( "Catalogue" )
		script["ArnoldOptions"] = GafferArnold.ArnoldOptions()

		script["Sphere"] = GafferScene.Sphere()
		script["Sphere"]["radius"].setValue( 10 )

		script["ImageShader"] = GafferArnold.ArnoldShader()
		script["ImageShader"].loadShader( "image" )
		script["ImageShader"]["parameters"]["filename"].setValue( os.path.dirname( __file__ ) + "/../GafferImageTest/images/GafferChecker.exr" )
		script["ImageShader"]["parameters"]["sscale"].setValue( 16 )
		script["ImageShader"]["parameters"]["tscale"].setValue( 16 )

		script["ShaderAssignment"] = GafferScene.ShaderAssignment()
		script["ShaderAssignment"]["in"].setInput( script["Sphere"]["out"] )
		script["ShaderAssignment"]["shader"].setInput( script["ImageShader"]["out"] )

		script["Camera"]["transform"]["translate"]["z"].setValue( 5.936607360839844 )
		script["Group"]["in"][0].setInput( script["Camera"]["out"] )
		script["Group"]["in"][1].setInput( script["Sphere"]["out"] )
		script["StandardOptions"]["in"].setInput( script["Group"]["out"] )
		script["StandardOptions"]["options"]["renderCamera"]["value"].setValue( '/group/camera' )
		script["StandardOptions"]["options"]["renderCamera"]["enabled"].setValue( True )
		script["StandardOptions"]["options"]["renderResolution"]["value"].setValue( imath.V2i( 1000, 1000 ) )
		script["StandardOptions"]["options"]["renderResolution"]["enabled"].setValue( True )
		script["Outputs"]["in"].setInput( script["ArnoldOptions"]["out"] )
		script["Outputs"]["outputs"]["output1"]["name"].setValue( 'Interactive/Beauty' )
		script["Outputs"]["outputs"]["output1"]["fileName"].setValue( 'beauty' )
		script["Outputs"]["outputs"]["output1"]["type"].setValue( 'ieDisplay' )
		script["Outputs"]["outputs"]["output1"]["data"].setValue( 'rgba' )
		script["Catalogue"]["directory"].setValue( self.temporaryDirectory() + "/catalogues/test" )
		script["ArnoldOptions"]["in"].setInput( script["StandardOptions"]["out"] )
		script["ArnoldOptions"]["options"]["proceduralSearchPath"]["enabled"].setValue( True )
		script["ArnoldOptions"]["options"]["proceduralSearchPath"]["enabled"].setValue( True )
		script["ArnoldOptions"]["options"]["threads"]["value"].setValue( -6 )
		script["ArnoldOptions"]["options"]["threads"]["enabled"].setValue( True )

		script["Blur"] = GafferImage.Blur( "Blur" )
		script["Blur"]["in"].setInput( script["Catalogue"]["out"] )
		script["Blur"]["radius"]["x"].setValue( 1.0 )
		script["Blur"]["radius"]["y"].setValue( 1.0 )

		with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as h :
			script["InteractiveArnoldRender"] = GafferArnold.InteractiveArnoldRender( "InteractiveArnoldRender" )
			script["InteractiveArnoldRender"]["in"].setInput( script["Outputs"]["out"] )

			watchNode = script["Blur"]

			script['InteractiveArnoldRender']['state'].setValue( GafferScene.InteractiveRender.State.Running )

			tc = Gaffer.ScopedConnection( GafferImageTest.connectProcessTilesToPlugDirtiedSignal( watchNode["out"] ) )

			startTime = time.time()
			for i in range( 250 ):
				script["Camera"]["transform"]["translate"]["x"].setValue( math.sin( i * 0.1 ) )
				h.waitFor( 0.02 )

			endTime = time.time()

			print( "LOOP DURATION: ", endTime - startTime )

			script['InteractiveArnoldRender']['state'].setValue( GafferScene.InteractiveRender.State.Stopped )



if __name__ == "__main__":
	unittest.main()
