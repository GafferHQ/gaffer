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
import unittest
import imath

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class ShaderTweaksTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		l = GafferSceneTest.TestLight()
		l["parameters"]["intensity"].setValue( imath.Color3f( 1 ) )

		t = GafferScene.ShaderTweaks()
		t["in"].setInput( l["out"] )
		t["shader"].setValue( "light" )

		self.assertSceneValid( t["out"] )
		self.assertScenesEqual( t["out"], l["out"] )
		self.assertSceneHashesEqual( t["out"], l["out"] )
		self.assertEqual( l["out"].attributes( "/light" )["light"].outputShader().parameters["intensity"].value, imath.Color3f( 1 ) )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		t["filter"].setInput( f["out"] )

		self.assertSceneValid( t["out"] )
		self.assertScenesEqual( t["out"], l["out"] )
		self.assertSceneHashesEqual( t["out"], l["out"] )

		intensityTweak = GafferScene.TweakPlug( "intensity", imath.Color3f( 1, 0, 0 ) )
		t["tweaks"].addChild( intensityTweak )

		self.assertSceneValid( t["out"] )

		self.assertEqual( t["out"].attributes( "/light" )["light"].outputShader().parameters["intensity"].value, imath.Color3f( 1, 0, 0 ) )

		intensityTweak["value"].setValue( imath.Color3f( 100 ) )
		self.assertEqual( t["out"].attributes( "/light" )["light"].outputShader().parameters["intensity"].value, imath.Color3f( 100 ) )

		intensityTweak["enabled"].setValue( False )
		self.assertEqual( t["out"].attributes( "/light" )["light"].outputShader().parameters["intensity"].value, imath.Color3f( 1 ) )

		intensityTweak["enabled"].setValue( True )
		intensityTweak["mode"].setValue( intensityTweak.Mode.Add )
		self.assertEqual( t["out"].attributes( "/light" )["light"].outputShader().parameters["intensity"].value, imath.Color3f( 101 ) )

		intensityTweak["mode"].setValue( intensityTweak.Mode.Subtract )
		intensityTweak["value"].setValue( imath.Color3f( 0.1, 0.2, 0.3 ) )
		self.assertEqual( t["out"].attributes( "/light" )["light"].outputShader().parameters["intensity"].value, imath.Color3f( 0.9, 0.8, 0.7 ) )

		intensityTweak["mode"].setValue( intensityTweak.Mode.Multiply )
		l["parameters"]["intensity"].setValue( imath.Color3f( 2 ) )
		self.assertEqual( t["out"].attributes( "/light" )["light"].outputShader().parameters["intensity"].value, imath.Color3f( 0.2, 0.4, 0.6 ) )

		t["shader"].setValue( "" )
		self.assertScenesEqual( t["out"], l["out"] )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["t"] = GafferScene.ShaderTweaks()
		s["t"]["tweaks"].addChild( GafferScene.TweakPlug( "test", 1.0 ) )
		s["t"]["tweaks"].addChild( GafferScene.TweakPlug( "test", imath.Color3f( 1, 2, 3 ) ) )

		ss = Gaffer.ScriptNode()
		ss.execute( s.serialise() )

		for i in range( 0, len( s["t"]["tweaks"] ) ) :
			for n in s["t"]["tweaks"][i].keys() :
				self.assertEqual( ss["t"]["tweaks"][i][n].getValue(), s["t"]["tweaks"][i][n].getValue() )

	def testLoadFromVersion0_52( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.dirname( __file__ ) + "/scripts/lightTweaks-0.52.3.1.gfr" )
		s.load()

		self.assertIsInstance( s["LightTweaks1"], GafferScene.ShaderTweaks )
		self.assertIsInstance( s["LightTweaks2"], GafferScene.ShaderTweaks )

		self.assertEqual( s["LightTweaks1"]["shader"].getValue(), "light *:light" )
		self.assertEqual( s["LightTweaks2"]["shader"].getValue(), "light" )

		self.assertEqual(
			s["TestLight"]["out"].attributes( "/light" )["light"].outputShader().parameters["intensity"].value,
			imath.Color3f( 1, 1, 1 )
		)

		self.assertEqual(
			s["LightTweaks1"]["out"].attributes( "/light" )["light"].outputShader().parameters["intensity"].value,
			imath.Color3f( 1, 0, 0 )
		)

		self.assertEqual(
			s["LightTweaks2"]["out"].attributes( "/light" )["light"].outputShader().parameters["intensity"].value,
			imath.Color3f( 0.5, 0, 0 )
		)

	def testLoadAndResaveFromVersion0_52( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.dirname( __file__ ) + "/scripts/lightTweaks-0.52.3.1.gfr" )
		s.load()

		ss = s.serialise()
		self.assertNotIn( "GafferScene.LightTweaks", ss )
		self.assertEqual( ss.count( "GafferScene.ShaderTweaks" ), 2 )

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )

		self.assertSceneHashesEqual( s["LightTweaks2"]["out"], s2["LightTweaks2"]["out"] )
		self.assertScenesEqual( s["LightTweaks2"]["out"], s2["LightTweaks2"]["out"] )

	def testConnect( self ) :

		plane = GafferScene.Plane()
		shader = GafferSceneTest.TestShader( "surface" )
		shader["type"].setValue( "surface" )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		assignment = GafferScene.ShaderAssignment()
		assignment["in"].setInput( plane["out"] )
		assignment["filter"].setInput( planeFilter["out"] )
		assignment["shader"].setInput( shader["out"] )

		originalNetwork = assignment["out"].attributes( "/plane" )["surface"]
		self.assertEqual( len( originalNetwork ), 1 )

		textureShader = GafferSceneTest.TestShader( "texture" )

		tweaks = GafferScene.ShaderTweaks()
		tweaks["in"].setInput( assignment["out"] )
		tweaks["filter"].setInput( planeFilter["out"] )
		tweaks["shader"].setValue( "surface" )

		tweaks["tweaks"].addChild( GafferScene.TweakPlug( "c", Gaffer.Color3fPlug() ) )
		tweaks["tweaks"][0]["value"].setInput( textureShader["out"] )

		tweakedNetwork = tweaks["out"].attributes( "/plane" )["surface"]
		self.assertEqual( len( tweakedNetwork ), 2 )
		self.assertEqual( tweakedNetwork.input( ( "surface", "c" ) ), ( "texture", "" ) )

		tweakedNetwork.removeShader( "texture" )
		self.assertEqual( tweakedNetwork, originalNetwork )

		textureShader["parameters"]["c"].setValue( imath.Color3f( 1, 2, 3 ) )
		tweakedNetwork = tweaks["out"].attributes( "/plane" )["surface"]
		self.assertEqual( tweakedNetwork.getShader( "texture" ).parameters["c"].value, imath.Color3f( 1, 2, 3 ) )

	def testConnectSpecificOutputParameter( self ) :

		plane = GafferScene.Plane()
		shader = GafferSceneTest.TestShader( "surface" )
		shader["type"].setValue( "surface" )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		assignment = GafferScene.ShaderAssignment()
		assignment["in"].setInput( plane["out"] )
		assignment["filter"].setInput( planeFilter["out"] )
		assignment["shader"].setInput( shader["out"] )

		originalNetwork = assignment["out"].attributes( "/plane" )["surface"]
		self.assertEqual( len( originalNetwork ), 1 )

		textureShader = GafferSceneTest.TestShader( "texture" )
		textureShader["out"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )
		textureShader["out"]["color"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out )
		textureShader["out"]["opacity"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out )

		tweaks = GafferScene.ShaderTweaks()
		tweaks["in"].setInput( assignment["out"] )
		tweaks["filter"].setInput( planeFilter["out"] )
		tweaks["shader"].setValue( "surface" )

		tweaks["tweaks"].addChild( GafferScene.TweakPlug( "c", Gaffer.Color3fPlug() ) )
		tweaks["tweaks"][0]["value"].setInput( textureShader["out"]["opacity"] )

		tweakedNetwork = tweaks["out"].attributes( "/plane" )["surface"]
		self.assertEqual( len( tweakedNetwork ), 2 )
		self.assertEqual( tweakedNetwork.input( ( "surface", "c" ) ), ( "texture", "opacity" ) )

		tweakedNetwork.removeShader( "texture" )
		self.assertEqual( tweakedNetwork, originalNetwork )

		textureShader["parameters"]["c"].setValue( imath.Color3f( 1, 2, 3 ) )
		tweakedNetwork = tweaks["out"].attributes( "/plane" )["surface"]
		self.assertEqual( tweakedNetwork.getShader( "texture" ).parameters["c"].value, imath.Color3f( 1, 2, 3 ) )

	def testReconnect( self ) :

		plane = GafferScene.Plane()
		shader = GafferSceneTest.TestShader( "surface" )
		shader["type"].setValue( "surface" )

		textureShader1 = GafferSceneTest.TestShader( "texture1" )
		shader["parameters"]["c"].setInput( textureShader1["out"] )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		assignment = GafferScene.ShaderAssignment()
		assignment["in"].setInput( plane["out"] )
		assignment["filter"].setInput( planeFilter["out"] )
		assignment["shader"].setInput( shader["out"] )

		originalNetwork = assignment["out"].attributes( "/plane" )["surface"]
		self.assertEqual( len( originalNetwork ), 2 )
		self.assertEqual( originalNetwork.input( ( "surface", "c" ) ), ( "texture1", "" ) )

		textureShader2 = GafferSceneTest.TestShader( "texture2" )

		tweaks = GafferScene.ShaderTweaks()
		tweaks["in"].setInput( assignment["out"] )
		tweaks["filter"].setInput( planeFilter["out"] )
		tweaks["shader"].setValue( "surface" )

		tweaks["tweaks"].addChild( GafferScene.TweakPlug( "c", Gaffer.Color3fPlug() ) )
		tweaks["tweaks"][0]["value"].setInput( textureShader2["out"] )

		tweakedNetwork = tweaks["out"].attributes( "/plane" )["surface"]
		self.assertEqual( len( tweakedNetwork ), 2 )
		self.assertEqual( tweakedNetwork.input( ( "surface", "c" ) ), ( "texture2", "" ) )

if __name__ == "__main__":
	unittest.main()
