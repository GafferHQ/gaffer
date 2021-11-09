##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferOSL
import GafferOSLTest

class OSLLightTest( GafferOSLTest.OSLTestCase ) :

	def testShader( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/constant.osl" )

		node = GafferOSL.OSLLight()
		self.assertIsInstance( node, GafferScene.Light )

		node.loadShader( shader )
		self.assertEqual( node["parameters"].keys(), [ "Cs" ] )

		cs = GafferTest.CapturingSlot( node.plugDirtiedSignal() )
		node["parameters"]["Cs"].setValue( imath.Color3f( 1, 0, 0 ) )
		self.assertIn( node["out"]["attributes"], { x[0] for x in cs } )

		a = node["out"].attributes( "/light" )
		self.assertIn( "osl:light", a )

	def testSerialisation( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/constant.osl" )

		script = Gaffer.ScriptNode()
		script["n"] = GafferOSL.OSLLight()
		script["n"].loadShader( shader )
		script["n"]["parameters"]["Cs"].setValue( imath.Color3f( 0, 1, 0 ) )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		self.assertEqual( script["n"]["parameters"]["Cs"].getValue(), script2["n"]["parameters"]["Cs"].getValue() )

		self.assertScenesEqual( script["n"]["out"], script2["n"]["out"] )

	def testShape( self ) :

		node = GafferOSL.OSLLight()
		self.assertEqual( node["out"].object( "/light" ), IECoreScene.DiskPrimitive( 0.01 ) )

		node["radius"].setValue( 2 )
		self.assertEqual( node["out"].object( "/light" ), IECoreScene.DiskPrimitive( 2 ) )

		node["shape"].setValue( node.Shape.Sphere )
		self.assertEqual( node["out"].object( "/light" ), IECoreScene.SpherePrimitive( 2 ) )

		node["shape"].setValue( node.Shape.Geometry )
		node["geometryType"].setValue( "teapot" )
		node["geometryBound"].setValue( imath.Box3f( imath.V3f( -0.5 ), imath.V3f( 0.5 ) ) )
		node["geometryParameters"].addChild( Gaffer.NameValuePlug( "color", imath.Color3f( 1, 0, 0 ) ) )

		self.assertEqual(
			node["out"].object( "/light" ),
			GafferScene.Private.IECoreScenePreview.Geometry(
				"teapot",
				imath.Box3f( imath.V3f( -0.5 ), imath.V3f( 0.5 ) ),
				{
					"color" : imath.Color3f( 1, 0, 0 ),
				}
			)
		)

	def testNetwork( self ) :

		constantShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/constant.osl" )
		addShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/add.osl" )

		lightNode = GafferOSL.OSLLight()
		lightNode.loadShader( constantShader )

		shaderNode = GafferOSL.OSLShader( "shader" )
		shaderNode.loadShader( addShader )

		lightNode["parameters"]["Cs"].setInput( shaderNode["out"]["out"] )

		network = lightNode["out"].attributes( "/light" )["osl:light"]
		self.assertEqual( len( network ), 2 )
		self.assertEqual(
			network.inputConnections( network.getOutput().shader ),
			[ network.Connection( ( "shader", "out" ), ( network.getOutput().shader, "Cs" ) ) ]
		)

	def testAttributes( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/constant.osl" )

		node = GafferOSL.OSLLight()
		node.loadShader( shader )

		m = Gaffer.NameValuePlug( "render:test", 10 )
		node["attributes"].addChild( m )
		self.assertEqual( node["out"].attributes( "/light" )["render:test"].value, 10 )

		m["value"].setValue( 20 )
		self.assertEqual( node["out"].attributes( "/light" )["render:test"].value, 20 )

		node["visualiserAttributes"]["maxTextureResolution"]["enabled"].setValue( True )
		node["visualiserAttributes"]["maxTextureResolution"]["value"].setValue( 512 )
		self.assertEqual( node["out"].attributes( "/light" )["gl:visualiser:maxTextureResolution"].value, 512 )

if __name__ == "__main__":
	unittest.main()
