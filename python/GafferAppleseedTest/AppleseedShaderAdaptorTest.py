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

import os

import IECore

import GafferScene
import GafferSceneTest
import GafferOSL
import GafferOSLTest
import GafferAppleseed

class AppleseedShaderAdaptorTest( GafferOSLTest.OSLTestCase ) :

	def testDirtyPropagation( self ) :

		adaptor = GafferAppleseed.AppleseedShaderAdaptor()
		self.assertEqual( adaptor.affects( adaptor["in"]["attributes"] ), [ adaptor["out"]["attributes"] ] )

	def testAdaption( self ) :

		sphere = GafferScene.Sphere()

		shader = GafferOSL.OSLShader()
		shader.loadShader( "color/as_blackbody" )

		assignment = GafferScene.ShaderAssignment()
		assignment["in"].setInput( sphere["out"] )
		assignment["shader"].setInput( shader["out"] )
		self.assertEqual( assignment["out"].attributes( "/sphere" ).keys(), [ "osl:shader" ] )

		adaptor = GafferAppleseed.AppleseedShaderAdaptor()
		adaptor["in"].setInput( assignment["out"] )

		self.assertEqual( adaptor["out"].attributes( "/sphere" ).keys(), [ "osl:surface" ] )

		network = adaptor["out"].attributes( "/sphere" )["osl:surface"]
		self.assertEqual( len( network ), 3 )
		self.assertEqual( network[0].name, "color/as_blackbody" )
		self.assertEqual( network[0].type, "osl:shader" )

		self.assertEqual( network[1].name, "surface/as_emission_surface" )
		self.assertEqual( network[1].type, "osl:shader" )
		self.assertEqual( network[1].parameters["Color"].value, "link:" + network[0].parameters["__handle"].value + ".ColorOut" )

		self.assertEqual( network[2].name, "material/as_material_builder" )
		self.assertEqual( network[2].type, "osl:surface" )
		self.assertEqual( network[2].parameters["BSDF"].value, "link:" + network[1].parameters["__handle"].value + ".BSDF" )

	def testAdaptionOfEmptyShader( self ) :

		sphere = GafferScene.Sphere()

		shader = GafferOSL.OSLShader()
		shader.loadShader( self.compileShader( os.path.dirname( __file__ ) + "/shaders/empty.osl" ) )

		assignment = GafferScene.ShaderAssignment()
		assignment["in"].setInput( sphere["out"] )
		assignment["shader"].setInput( shader["out"] )
		self.assertEqual( assignment["out"].attributes( "/sphere" ).keys(), [ "osl:shader" ] )

		adaptor = GafferAppleseed.AppleseedShaderAdaptor()
		adaptor["in"].setInput( assignment["out"] )

		self.assertEqual( adaptor["out"].attributes( "/sphere" ).keys(), [ "osl:surface" ] )

		network = adaptor["out"].attributes( "/sphere" )["osl:surface"]
		self.assertEqual( len( network ), 2 )
		self.assertEqual( network[0].name, "surface/as_emission_surface" )
		self.assertEqual( network[0].type, "osl:shader" )
		self.assertEqual( network[0].parameters["Color"].value, IECore.Color3f( 1, 0, 0 ) )

		self.assertEqual( network[1].name, "material/as_material_builder" )
		self.assertEqual( network[1].type, "osl:surface" )
		self.assertEqual( network[1].parameters["BSDF"].value, "link:" + network[0].parameters["__handle"].value + ".BSDF" )

if __name__ == "__main__":
	unittest.main()
