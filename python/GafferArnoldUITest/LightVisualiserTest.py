##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Cinesite VFX Ltd. nor the names of
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

import IECore

import Gaffer
import GafferArnold
import GafferScene
import GafferSceneUITest
import GafferTest

@unittest.skipIf( GafferTest.inCI(), "OpenGL not set up" )
class LightVisualiserTest( GafferSceneUITest.SceneUITestCase ) :

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testDrawPerformanceQuad( self ) :

		script = Gaffer.ScriptNode()

		script["quad"] = GafferArnold.ArnoldLight()
		script["quad"].loadShader( "quad_light" )

		instancerOut = self.setupInstancer( script["quad"]["out"] )

		self.benchmarkRender( instancerOut )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testDrawPerformanceSpot( self ) :

		script = Gaffer.ScriptNode()

		script["spot"] = GafferArnold.ArnoldLight()
		script["spot"].loadShader( "spot_light" )

		script["light_decay"] = GafferArnold.ArnoldShader( "light_decay" )
		script["light_decay"].loadShader( "light_decay" )
		script["gobo"] = GafferArnold.ArnoldShader( "gobo" )
		script["gobo"].loadShader( "gobo" )
		script["barndoor"] = GafferArnold.ArnoldShader( "barndoor" )
		script["barndoor"].loadShader( "barndoor" )
		script["ShaderAssignment1"] = GafferScene.ShaderAssignment( "ShaderAssignment1" )
		script["ShaderAssignment2"] = GafferScene.ShaderAssignment( "ShaderAssignment2" )
		script["ShaderAssignment3"] = GafferScene.ShaderAssignment( "ShaderAssignment3" )
		script["PathFilter4"] = GafferScene.PathFilter( "PathFilter4" )
		script["light_decay"]["parameters"]["use_near_atten"].setValue( True )
		script["light_decay"]["parameters"]["use_far_atten"].setValue( True )
		script["light_decay"]["parameters"]["near_start"].setValue( 1.0 )
		script["light_decay"]["parameters"]["near_end"].setValue( 2.0 )
		script["light_decay"]["parameters"]["far_start"].setValue( 4.0 )
		script["light_decay"]["parameters"]["far_end"].setValue( 5.0 )
		script["gobo"]["parameters"]["density"].setValue( 0.30000001192092896 )
		script["gobo"]["parameters"]["swrap"].setValue( 'periodic' )
		script["gobo"]["parameters"]["twrap"].setValue( 'periodic' )
		script["barndoor"]["parameters"]["barndoor_left_top"].setValue( 0.20000000298023224 )
		script["barndoor"]["parameters"]["barndoor_left_bottom"].setValue( 0.30000001192092896 )
		script["ShaderAssignment1"]["filter"].setInput( script["PathFilter4"]["out"] )
		script["ShaderAssignment1"]["shader"].setInput( script["light_decay"]["out"] )
		script["ShaderAssignment2"]["in"].setInput( script["ShaderAssignment1"]["out"] )
		script["ShaderAssignment2"]["filter"].setInput( script["PathFilter4"]["out"] )
		script["ShaderAssignment2"]["shader"].setInput( script["gobo"]["out"] )
		script["ShaderAssignment3"]["in"].setInput( script["ShaderAssignment2"]["out"] )
		script["ShaderAssignment3"]["filter"].setInput( script["PathFilter4"]["out"] )
		script["ShaderAssignment3"]["shader"].setInput( script["barndoor"]["out"] )
		script["PathFilter4"]["paths"].setValue( IECore.StringVectorData( [ '/*' ] ) )

		instancerOut = self.setupInstancer( script["spot"]["out"] )

		self.benchmarkRender( instancerOut )

if __name__ == "__main__":
	unittest.main()

