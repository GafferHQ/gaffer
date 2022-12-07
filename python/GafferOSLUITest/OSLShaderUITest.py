##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

import pathlib

import Gaffer
import GafferUI

import GafferOSL
import GafferOSLTest
import GafferOSLUI

class OSLShaderUITest( GafferOSLTest.OSLTestCase ) :

	def testChangingOutputNodules( self ) :

		shaderDirectory = pathlib.Path( __file__ ).parents[1] / "GafferOSLTest" / "shaders"
		surfaceShader = self.compileShader( shaderDirectory / "constant.osl" )
		utilityShader1 = self.compileShader( shaderDirectory / "version1.osl" )
		utilityShader2 = self.compileShader( shaderDirectory / "outputTypes.osl" )

		node = GafferOSL.OSLShader()
		nodeGadget = GafferUI.NodeGadget.create( node )

		node.loadShader( surfaceShader )
		self.assertTrue( isinstance( nodeGadget.nodule( node["out"] ), GafferUI.StandardNodule ) )

		node.loadShader( utilityShader1 )
		self.assertTrue( isinstance( nodeGadget.nodule( node["out"] ), GafferUI.CompoundNodule ) )
		self.assertTrue( isinstance( nodeGadget.nodule( node["out"]["c"] ), GafferUI.StandardNodule ) )

		node.loadShader( utilityShader2 )
		self.assertTrue( isinstance( nodeGadget.nodule( node["out"] ), GafferUI.CompoundNodule ) )
		self.assertTrue( isinstance( nodeGadget.nodule( node["out"]["i"] ), GafferUI.StandardNodule ) )
		self.assertTrue( isinstance( nodeGadget.nodule( node["out"]["f"] ), GafferUI.StandardNodule ) )

		node.loadShader( surfaceShader )
		self.assertTrue( isinstance( nodeGadget.nodule( node["out"] ), GafferUI.StandardNodule ) )

	def testParameterUserDefaults( self ) :

		s = GafferOSL.OSLShader()
		s.loadShader( "ObjectProcessing/InFloat" )

		self.assertEqual( s["parameters"]["name"].getValue(), "u" )
		self.assertEqual( s["parameters"]["defaultValue"].getValue(), 0 )

		Gaffer.NodeAlgo.applyUserDefaults( s )

		self.assertEqual( s["parameters"]["name"].getValue(), "u" )
		self.assertEqual( s["parameters"]["defaultValue"].getValue(), 0 )

		Gaffer.Metadata.registerValue( "osl:shader:ObjectProcessing/InFloat:name", "userDefault", "xx" )
		Gaffer.Metadata.registerValue( "osl:shader:ObjectProcessing/InFloat:defaultValue", "userDefault", 1 )

		Gaffer.NodeAlgo.applyUserDefaults( s )

		self.assertEqual( s["parameters"]["name"].getValue(), "xx" )
		self.assertEqual( s["parameters"]["defaultValue"].getValue(), 1 )

	def testSplineParameterUserDefaults( self ) :

		Gaffer.Metadata.registerValue(
			"osl:shader:Pattern/ColorSpline:spline.interpolation", "userDefault",
			Gaffer.SplineDefinitionInterpolation.Linear
		)

		s = GafferOSL.OSLShader()
		s.loadShader( "Pattern/ColorSpline" )
		Gaffer.NodeAlgo.applyUserDefaults( s )
		self.assertEqual( s["parameters"]["spline"]["interpolation"].getValue(), Gaffer.SplineDefinitionInterpolation.Linear )

		Gaffer.Metadata.registerValue(
			"osl:shader:Pattern/ColorSpline:spline.interpolation", "userDefault",
			Gaffer.SplineDefinitionInterpolation.MonotoneCubic
		)
		Gaffer.NodeAlgo.applyUserDefaults( s )
		self.assertEqual( s["parameters"]["spline"]["interpolation"].getValue(), Gaffer.SplineDefinitionInterpolation.MonotoneCubic )

	def tearDown( self ) :

		Gaffer.Metadata.deregisterValue( "osl:shader:ObjectProcessing/InFloat:name", "userDefault" )
		Gaffer.Metadata.deregisterValue( "osl:shader:ObjectProcessing/InFloat:defaultValue", "userDefault" )
		Gaffer.Metadata.deregisterValue( "osl:shader:Pattern/ColorSpline:spline.interpolation", "userDefault" )

if __name__ == "__main__":
	unittest.main()
