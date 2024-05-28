##########################################################################
#
#  Copyright (c) 2024, Image Engine Design Inc. All rights reserved.
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
import unittest
import imath

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

class ShaderTweakProxyTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		plane = GafferScene.Plane()
		shader = GafferSceneTest.TestShader( "surface" )
		shader["type"].setValue( "surface" )

		textureShader1 = GafferSceneTest.TestShader( "texture1" )

		textureShader2 = GafferSceneTest.TestShader( "texture2" )

		shader["parameters"]["c"].setInput( textureShader1["out"] )
		textureShader1["parameters"]["c"].setInput( textureShader2["out"] )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		assignment = GafferScene.ShaderAssignment()
		assignment["in"].setInput( plane["out"] )
		assignment["filter"].setInput( planeFilter["out"] )
		assignment["shader"].setInput( shader["out"] )

		# Check the untweaked network
		originalNetwork = assignment["out"].attributes( "/plane" )["surface"]
		self.assertEqual( len( originalNetwork ), 3 )
		self.assertEqual( originalNetwork.input( ( "surface", "c" ) ), ( "texture1", "out" ) )

		tweakShader = GafferSceneTest.TestShader( "tweakShader" )

		tweaks = GafferScene.ShaderTweaks()
		tweaks["in"].setInput( assignment["out"] )
		tweaks["filter"].setInput( planeFilter["out"] )
		tweaks["shader"].setValue( "surface" )

		tweaks["tweaks"].addChild( Gaffer.TweakPlug( "c", Gaffer.Color3fPlug() ) )
		tweaks["tweaks"][0]["value"].setInput( tweakShader["out"] )

		# If we replace the upstream network with a tweak, now we have just 2 nodes
		tweakedNetwork = tweaks["out"].attributes( "/plane" )["surface"]
		self.assertEqual( len( tweakedNetwork ), 2 )
		self.assertEqual( tweakedNetwork.input( ( "surface", "c" ) ), ( "tweakShader", "out" ) )

		autoProxy = GafferScene.ShaderTweakProxy()
		autoProxy.setupAutoProxy( Gaffer.Color3fPlug() )

		# Using an auto proxy with no tweak shaders inserted recreates the original network
		tweaks["tweaks"][0]["value"].setInput( autoProxy["out"]["auto"] )
		self.assertEqual( tweaks["out"].attributes( "/plane" )["surface"], originalNetwork )

		# Test adding a tweak shader in the middle of the network using the proxy
		tweakShader["parameters"]["c"].setInput( autoProxy["out"]["auto"] )
		tweaks["tweaks"][0]["value"].setInput( tweakShader["out"] )
		tweakedNetwork = tweaks["out"].attributes( "/plane" )["surface"]
		self.assertEqual( len( tweakedNetwork ), 4 )
		self.assertEqual( tweakedNetwork.input( ( "surface", "c" ) ), ( "tweakShader", "out" ) )
		self.assertEqual( tweakedNetwork.input( ( "tweakShader", "c" ) ), ( "texture1", "out" ) )

		# If we target the end of the network where there is no input, then the tweak gets inserted fine,
		# and there is no input to the tweak, since there's nothing upstream
		tweaks["tweaks"][0]["name"].setValue( "texture2.c" )
		tweakedNetwork = tweaks["out"].attributes( "/plane" )["surface"]
		self.assertEqual( len( tweakedNetwork ), 4 )
		self.assertEqual( tweakedNetwork.input( ( "surface", "c" ) ), ( "texture1", "out" ) )
		self.assertEqual( tweakedNetwork.input( ( "texture1", "c" ) ), ( "texture2", "out" ) )
		self.assertEqual( tweakedNetwork.input( ( "texture2", "c" ) ), ( "tweakShader", "out" ) )
		self.assertEqual( tweakedNetwork.input( ( "tweakShader", "c" ) ), ( "", "" ) )

		# Test using an auto-proxy on a parameter with no input ( it should apply the value to what the
		# auto-proxy is connected to )
		textureShader2["parameters"]["c"].setValue( imath.Color3f( 5, 6, 7 ) )
		tweaks["tweaks"][0]["name"].setValue( "texture2.c" )
		tweakedNetwork = tweaks["out"].attributes( "/plane" )["surface"]
		self.assertEqual( tweakedNetwork.getShader( "tweakShader" ).parameters["c"].value, imath.Color3f( 5, 6, 7 ) )

		# Test proxying a specific node using a named handle
		tweaks["tweaks"][0]["name"].setValue( "c" )

		specificProxy = GafferScene.ShaderTweakProxy()
		specificProxy.loadShader( "test:testShader" )

		specificProxy["parameters"]["targetShader"].setValue( "texture2" )

		tweakShader["parameters"]["c"].setInput( specificProxy["out"]["out"] )

		tweakedNetwork = tweaks["out"].attributes( "/plane" )["surface"]
		self.assertEqual( len( tweakedNetwork ), 3 )
		self.assertEqual( tweakedNetwork.input( ( "surface", "c" ) ), ( "tweakShader", "out" ) )
		self.assertEqual( tweakedNetwork.input( ( "tweakShader", "c" ) ), ( "texture2", "out" ) )

		# Test error if we try to make a cycle
		tweaks["tweaks"][0]["name"].setValue( "texture2.c" )
		specificProxy["parameters"]["targetShader"].setValue( "texture1" )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Cannot use "texture1" in ShaderTweakProxy when tweaking "texture2", this would create cycle in shader network' ):
			tweaks["out"].attributes( "/plane" )

	def testAutoProxyValueTransferToComponent( self ) :

		plane = GafferScene.Plane()
		shader = GafferSceneTest.TestShader( "surface" )
		shader["type"].setValue( "surface" )
		shader["parameters"]["i"].setValue( 42 )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		assignment = GafferScene.ShaderAssignment()
		assignment["in"].setInput( plane["out"] )
		assignment["filter"].setInput( planeFilter["out"] )
		assignment["shader"].setInput( shader["out"] )

		tweakShader = GafferSceneTest.TestShader( "tweakShader" )

		tweaks = GafferScene.ShaderTweaks()
		tweaks["in"].setInput( assignment["out"] )
		tweaks["filter"].setInput( planeFilter["out"] )
		tweaks["shader"].setValue( "surface" )

		tweaks["tweaks"].addChild( Gaffer.TweakPlug( "i", Gaffer.IntPlug() ) )
		tweaks["tweaks"][0]["value"].setInput( tweakShader["out"]["r"] )

		autoProxy = GafferScene.ShaderTweakProxy()
		autoProxy.setupAutoProxy( Gaffer.IntPlug() )

		tweakShader["parameters"]["c"]["g"].setInput( autoProxy["out"]["auto"] )

		# This is quite a special case - there is no input to the parameter we are tweaking, so there is no
		# connection to transfer, so we would expect the auto proxy to transfer the value - however the auto
		# proxy output is connected to a subcomponent.
		#
		# The correct result is that the green component of tweakShader.c should be set to 42, transferring the value
		# that was set. However, we have not yet added support for this fairly obscure case, so instead this test
		# documents the current behaviour, which is to throw a semi-helpful exception.

		with self.assertRaisesRegex( Gaffer.ProcessException, 'CompoundData has no child named "c.g"' ):
			tweaks["out"].attributes( "/plane" )["surface"]

	def testInvalidInShaderAssignment( self ) :

		plane = GafferScene.Plane()

		autoProxy = GafferScene.ShaderTweakProxy()
		autoProxy.setupAutoProxy( Gaffer.Color3fPlug() )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		assignment = GafferScene.ShaderAssignment()
		assignment["in"].setInput( plane["out"] )
		assignment["filter"].setInput( planeFilter["out"] )
		assignment["shader"].setInput( autoProxy["out"]["auto"] )

		# Using a proxy in a shader assignment is invalid
		with self.assertRaisesRegex( Gaffer.ProcessException, "ShaderTweakProxy only works with ShaderTweaks" ):
			assignment["out"].attributes( "/plane" )


if __name__ == "__main__":
	unittest.main()
