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
import unittest
import imath

import IECore
import IECoreScene

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

		intensityTweak = Gaffer.TweakPlug( "intensity", imath.Color3f( 1, 0, 0 ) )
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
		s["t"]["tweaks"].addChild( Gaffer.TweakPlug( "test", 1.0 ) )
		s["t"]["tweaks"].addChild( Gaffer.TweakPlug( "test", imath.Color3f( 1, 2, 3 ) ) )

		ss = Gaffer.ScriptNode()
		ss.execute( s.serialise() )

		for i in range( 0, len( s["t"]["tweaks"] ) ) :
			for n in s["t"]["tweaks"][i].keys() :
				self.assertEqual( ss["t"]["tweaks"][i][n].getValue(), s["t"]["tweaks"][i][n].getValue() )

	def testLoadFromVersion0_52( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( pathlib.Path( __file__ ).parent / "scripts" / "lightTweaks-0.52.3.1.gfr" )
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
		s["fileName"].setValue( pathlib.Path( __file__ ).parent / "scripts" / "lightTweaks-0.52.3.1.gfr" )
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

		tweaks["tweaks"].addChild( Gaffer.TweakPlug( "c", Gaffer.Color3fPlug() ) )
		tweaks["tweaks"][0]["value"].setInput( textureShader["out"] )

		tweakedNetwork = tweaks["out"].attributes( "/plane" )["surface"]
		self.assertEqual( len( tweakedNetwork ), 2 )
		self.assertEqual( tweakedNetwork.input( ( "surface", "c" ) ), ( "texture", "out" ) )

		tweakedNetwork.removeShader( "texture" )
		self.assertEqual( tweakedNetwork, originalNetwork )

		textureShader["parameters"]["c"].setValue( imath.Color3f( 1, 2, 3 ) )
		tweakedNetwork = tweaks["out"].attributes( "/plane" )["surface"]
		self.assertEqual( tweakedNetwork.getShader( "texture" ).parameters["c"].value, imath.Color3f( 1, 2, 3 ) )

		tweaks["tweaks"][0]["mode"].setValue( Gaffer.TweakPlug.Mode.Multiply )
		with self.assertRaisesRegex( RuntimeError, "Mode must be \"Replace\" when inserting a connection" ) :
			tweaks["out"].attributes( "/plane" )

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

		tweaks["tweaks"].addChild( Gaffer.TweakPlug( "c", Gaffer.Color3fPlug() ) )
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
		self.assertEqual( originalNetwork.input( ( "surface", "c" ) ), ( "texture1", "out" ) )

		textureShader2 = GafferSceneTest.TestShader( "texture2" )

		tweaks = GafferScene.ShaderTweaks()
		tweaks["in"].setInput( assignment["out"] )
		tweaks["filter"].setInput( planeFilter["out"] )
		tweaks["shader"].setValue( "surface" )

		tweaks["tweaks"].addChild( Gaffer.TweakPlug( "c", Gaffer.Color3fPlug() ) )
		tweaks["tweaks"][0]["value"].setInput( textureShader2["out"] )

		tweakedNetwork = tweaks["out"].attributes( "/plane" )["surface"]
		self.assertEqual( len( tweakedNetwork ), 2 )
		self.assertEqual( tweakedNetwork.input( ( "surface", "c" ) ), ( "texture2", "out" ) )

		textureShader2["enabled"].setValue( False )
		tweakedNetwork = tweaks["out"].attributes( "/plane" )["surface"]
		self.assertEqual( len( tweakedNetwork ), 1 )
		self.assertFalse( tweakedNetwork.input( ( "surface", "c" ) ) )

		textureShader2["enabled"].setValue( True )
		tweaks["tweaks"][0]["enabled"].setValue( False )
		self.assertEqual( tweaks["out"].attributes( "/plane" )["surface"], originalNetwork )

	def testCantDoArithmeticOnConnection( self ) :

		plane = GafferScene.Plane()
		shader = GafferSceneTest.TestShader( "surface" )
		shader["type"].setValue( "surface" )

		textureShader = GafferSceneTest.TestShader( "texture1" )
		shader["parameters"]["c"].setInput( textureShader["out"] )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		assignment = GafferScene.ShaderAssignment()
		assignment["in"].setInput( plane["out"] )
		assignment["filter"].setInput( planeFilter["out"] )
		assignment["shader"].setInput( shader["out"] )

		tweaks = GafferScene.ShaderTweaks()
		tweaks["in"].setInput( assignment["out"] )
		tweaks["filter"].setInput( planeFilter["out"] )
		tweaks["shader"].setValue( "surface" )

		tweaks["tweaks"].addChild( Gaffer.TweakPlug( "c", Gaffer.Color3fPlug() ) )

		for mode in Gaffer.TweakPlug.Mode.values :

			if mode == Gaffer.TweakPlug.Mode.Replace :
				continue

			tweaks["tweaks"][0]["mode"].setValue( mode )
			with self.assertRaisesRegex( RuntimeError, "Mode must be \"Replace\" when a previous connection exists" ) :
				tweaks["out"].attributes( "/plane" )

	def testPromoteTweaksPlug( self ) :

		box = Gaffer.Box()

		box["plane"] = GafferScene.Plane()
		box["shader"] = GafferSceneTest.TestShader()
		box["shader"]["type"].setValue( "surface" )

		box["planeFilter"] = GafferScene.PathFilter()
		box["planeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		box["assignment"] = GafferScene.ShaderAssignment()
		box["assignment"]["in"].setInput( box["plane"]["out"] )
		box["assignment"]["filter"].setInput( box["planeFilter"]["out"] )
		box["assignment"]["shader"].setInput( box["shader"]["out"] )

		box["tweaks"] = GafferScene.ShaderTweaks()
		box["tweaks"]["in"].setInput( box["assignment"]["out"] )
		box["tweaks"]["filter"].setInput( box["planeFilter"]["out"] )
		box["tweaks"]["shader"].setValue( "surface" )

		p = Gaffer.PlugAlgo.promote( box["tweaks"]["tweaks"] )
		p.addChild( Gaffer.TweakPlug( "c", imath.Color3f( 0.1, 5, 9 ) ) )

		network = box["tweaks"]["out"].attributes( "/plane" )["surface"]
		self.assertEqual( network.getShader( "shader" ).parameters["c"].value, imath.Color3f( 0.1, 5, 9 ) )

	def testIgnoreMissing( self ) :

		l = GafferSceneTest.TestLight()
		l["parameters"]["intensity"].setValue( imath.Color3f( 1 ) )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		t = GafferScene.ShaderTweaks()
		t["in"].setInput( l["out"] )
		t["shader"].setValue( "light" )
		t["filter"].setInput( f["out"] )

		badTweak = Gaffer.TweakPlug( "badParameter", 1.0 )
		t["tweaks"].addChild( badTweak )

		with self.assertRaisesRegex( RuntimeError, "Cannot apply tweak with mode Replace to \"badParameter\" : This parameter does not exist" ) :
			t["out"].attributes( "/light" )

		inputShader = GafferSceneTest.TestShader()
		badTweak["value"].setInput( inputShader["out"]["r"] )

		with self.assertRaisesRegex( RuntimeError, "Cannot apply tweak \"badParameter\" because shader \"light\" does not have parameter \"badParameter\"" ) :
			t["out"].attributes( "/light" )

		badTweak["value"].setInput( None )

		t["ignoreMissing"].setValue( True )
		self.assertEqual( t["out"].attributes( "/light" ), t["in"].attributes( "/light" ) )

		badTweak["name"].setValue( "badShader.p" )
		self.assertEqual( t["out"].attributes( "/light" ), t["in"].attributes( "/light" ) )

		badTweak["value"].setInput( inputShader["out"]["r"] )
		badTweak["name"].setValue( "badParameter" )
		self.assertEqual( t["out"].attributes( "/light" ), t["in"].attributes( "/light" ) )
		self.assertEqual( t["out"].attributes( "/light" ), t["in"].attributes( "/light" ) )

		badTweak["name"].setValue( "badShader.p" )
		self.assertEqual( t["out"].attributes( "/light" ), t["in"].attributes( "/light" ) )

		t["ignoreMissing"].setValue( False )
		with self.assertRaisesRegex( Gaffer.ProcessException, "Cannot apply tweak \"badShader.p\" because shader \"badShader\" does not exist" ) :
			t["out"].attributes( "/light" )

	def testLocalise( self ) :

		plane = GafferScene.Plane()
		group = GafferScene.Group()
		group["in"][0].setInput( plane["out"] )

		shader = GafferSceneTest.TestShader( "surface" )
		shader["type"].setValue( "surface" )
		shader["parameters"]["c"].setValue( imath.Color3f( 1, 2, 3 ) )

		groupFilter = GafferScene.PathFilter()
		groupFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		assignment = GafferScene.ShaderAssignment()
		assignment["in"].setInput( group["out"] )
		assignment["filter"].setInput( groupFilter["out"] )
		assignment["shader"].setInput( shader["out"] )

		self.assertTrue( "surface" in assignment["out"].attributes( "/group" ) )
		self.assertTrue( "surface" not in assignment["out"].attributes( "/group/plane" ) )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )

		tweaks = GafferScene.ShaderTweaks()
		tweaks["in"].setInput( assignment["out"] )
		tweaks["shader"].setValue( "light" )
		tweaks["filter"].setInput( planeFilter["out"] )

		colorTweak = Gaffer.TweakPlug( "c", imath.Color3f( 3, 2, 1 ) )
		tweaks["tweaks"].addChild( colorTweak )

		self.assertEqual( tweaks["localise"].getValue(), False )

		self.assertScenesEqual( tweaks["out"], tweaks["in"] )

		tweaks["localise"].setValue( True )

		# We have no matching shader yet
		self.assertScenesEqual( tweaks["out"], tweaks["in"] )

		tweaks["shader"].setValue( "surf*" )

		groupAttr = tweaks["out"].attributes( "/group" )
		self.assertEqual(
			groupAttr["surface"].getShader( "surface" ).parameters["c"].value,
			imath.Color3f( 1, 2, 3 )
		)

		planeAttr = tweaks["out"].attributes( "/group/plane" )
		self.assertTrue( "surface" in planeAttr )
		self.assertEqual(
			planeAttr["surface"].getShader( "surface" ).parameters["c"].value,
			imath.Color3f( 3, 2, 1 )
		)

		# Test disabling tweak results in no localisation

		colorTweak["enabled"].setValue( False )
		self.assertTrue( "surface" not in tweaks["out"].attributes( "/group/plane" ) )

	def testRemove( self ) :

		light = GafferSceneTest.TestLight()
		self.assertIn( "intensity", light["out"].attributes( "/light" )["light"].outputShader().parameters )

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		tweaks = GafferScene.ShaderTweaks()
		tweaks["in"].setInput( light["out"] )
		tweaks["shader"].setValue( "light" )
		tweaks["filter"].setInput( pathFilter["out"] )

		tweaks["tweaks"].addChild(
			Gaffer.TweakPlug( "intensity", 2.0, mode = Gaffer.TweakPlug.Mode.Remove )
		)
		self.assertNotIn( "intensity", tweaks["out"].attributes( "/light" )["light"].outputShader().parameters )

if __name__ == "__main__":
	unittest.main()
