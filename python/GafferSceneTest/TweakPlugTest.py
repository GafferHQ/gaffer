##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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
import six

import imath

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

class TweakPlugTest( GafferSceneTest.SceneTestCase ) :

	def testConstructor( self ) :

		p = GafferScene.TweakPlug( "test", 10.0, GafferScene.TweakPlug.Mode.Multiply, enabled = False )

		self.assertEqual( p["name"].defaultValue(), "" )
		self.assertEqual( p["name"].getValue(), "test" )

		self.assertIsInstance( p["value"], Gaffer.FloatPlug )
		self.assertEqual( p["value"].defaultValue(), 10 )
		self.assertEqual( p["value"].getValue(), 10 )

		self.assertEqual( p["mode"].defaultValue(), p.Mode.Replace )
		self.assertEqual( p["mode"].getValue(), p.Mode.Multiply )

		self.assertEqual( p["enabled"].defaultValue(), True )
		self.assertEqual( p["enabled"].getValue(), False )

	def testCreateCounterpart( self ) :

		p = GafferScene.TweakPlug( "test", 10.0, GafferScene.TweakPlug.Mode.Multiply )
		p2 = p.createCounterpart( "p2", Gaffer.Plug.Direction.In )

		self.assertIsInstance( p2, GafferScene.TweakPlug )
		self.assertEqual( p2.getName(), "p2" )
		self.assertEqual( p2.direction(), Gaffer.Plug.Direction.In )
		self.assertEqual( p2.keys(), p.keys() )
		for n in p2.keys() :
			self.assertIsInstance( p2[n], p[n].__class__ )

	def testTweakParameters( self ) :

		tweaks = GafferScene.TweaksPlug()

		tweaks.addChild( GafferScene.TweakPlug( "a", 1.0, GafferScene.TweakPlug.Mode.Replace ) )
		tweaks.addChild( GafferScene.TweakPlug( "b", 10.0, GafferScene.TweakPlug.Mode.Multiply ) )

		parameters = IECore.CompoundData( { "a" : 0.0, "b" : 2.0 } )
		self.assertTrue( tweaks.applyTweaks( parameters ) )
		self.assertEqual( parameters, IECore.CompoundData( { "a" : 1.0, "b" : 20.0 } ) )

	def testTweakNetwork( self ) :

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"texture" : IECoreScene.Shader( "image", "ai:shader", { "filename" : "test.tx", "sscale" : 1.0 } ),
				"surface" : IECoreScene.Shader( "lambert", "ai:surface", { "Kd" : 1.0 } )
			},
			output = "surface"
		)

		tweaks = GafferScene.TweaksPlug()
		tweaks.addChild( GafferScene.TweakPlug( "texture.sscale", 10.0, GafferScene.TweakPlug.Mode.Multiply ) )
		tweaks.addChild( GafferScene.TweakPlug( "texture.sscale", 1.0, GafferScene.TweakPlug.Mode.Add ) )
		tweaks.addChild( GafferScene.TweakPlug( "surface.Kd", 0.5, GafferScene.TweakPlug.Mode.Multiply ) )
		tweaks.addChild( GafferScene.TweakPlug( "Kd", 0.25, GafferScene.TweakPlug.Mode.Add ) )

		self.assertTrue( tweaks.applyTweaks( network ) )

		self.assertEqual( network.getShader( "texture" ).parameters["sscale"].value, 11.0 )
		self.assertEqual( network.getShader( "surface" ).parameters["Kd"].value, 0.75 )

	def testThrowOnMissingShader( self ) :

		network = IECoreScene.ShaderNetwork(
			shaders = { "surface" : IECoreScene.Shader( "lambert", "ai:surface" ) },
		)

		tweaks = Gaffer.Plug()
		tweaks.addChild( GafferScene.TweakPlug( "missingShader", 0.5 ) )

		with six.assertRaisesRegex( self, RuntimeError, "" ) :
			GafferScene.TweakPlug.applyTweaks( tweaks, network )

	def testWrongDataType( self ) :

		p = GafferScene.TweakPlug( "test", imath.Color3f( 1 ) )
		p["mode"].setValue( p.Mode.Multiply )
		self.assertIsInstance( p["value"], Gaffer.Color3fPlug )

		d = IECore.CompoundData( { "test" : 1 } )

		with six.assertRaisesRegex( self, RuntimeError, "Cannot apply tweak to \"test\" : Value of type \"IntData\" does not match parameter of type \"Color3fData\"" ) :
			p.applyTweak( d )

	def testMissingMode( self ) :

		p = GafferScene.TweaksPlug()
		p["t"] = GafferScene.TweakPlug( "test", 0.5, GafferScene.TweakPlug.Mode.Replace )

		d = IECore.CompoundData()
		with six.assertRaisesRegex( self, RuntimeError, "Cannot apply tweak with mode Replace to \"test\" : This parameter does not exist" ) :
			p.applyTweaks( d, missingMode = GafferScene.TweakPlug.MissingMode.Error )
		self.assertEqual( d, IECore.CompoundData() )

		d = IECore.CompoundData()
		self.assertFalse( p.applyTweaks( d, missingMode = GafferScene.TweakPlug.MissingMode.Ignore ) )
		self.assertEqual( d, IECore.CompoundData() )

		d = IECore.CompoundData()
		self.assertTrue( p.applyTweaks( d, missingMode = GafferScene.TweakPlug.MissingMode.IgnoreOrReplace ) )
		self.assertEqual( d, IECore.CompoundData( { "test" : 0.5 } ) )

		d = IECore.CompoundData()
		p["t"]["mode"].setValue( GafferScene.TweakPlug.Mode.Add )
		with six.assertRaisesRegex( self, RuntimeError, "Cannot apply tweak with mode Add to \"test\" : This parameter does not exist" ) :
			p.applyTweaks( d, missingMode = GafferScene.TweakPlug.MissingMode.Error )
		self.assertEqual( d, IECore.CompoundData() )

		with six.assertRaisesRegex( self, RuntimeError, "Cannot apply tweak with mode Add to \"test\" : This parameter does not exist" ) :
			p.applyTweaks( d, missingMode = GafferScene.TweakPlug.MissingMode.IgnoreOrReplace )
		self.assertEqual( d, IECore.CompoundData() )

		self.assertFalse( p.applyTweaks( d, missingMode = GafferScene.TweakPlug.MissingMode.Ignore ) )
		self.assertEqual( d, IECore.CompoundData() )

	def testTweaksPlug( self ) :

		p = GafferScene.TweaksPlug()
		self.assertFalse( p.acceptsChild( Gaffer.Plug() ) )
		self.assertFalse( p.acceptsInput( Gaffer.Plug() ) )

		p.addChild( GafferScene.TweakPlug( "x", 10.0, GafferScene.TweakPlug.Mode.Replace ) )

		p2 = p.createCounterpart( "p2", Gaffer.Plug.Direction.In )
		self.assertIsInstance( p2, GafferScene.TweaksPlug )
		self.assertEqual( p2.getName(), "p2" )
		self.assertEqual( p2.direction(), Gaffer.Plug.Direction.In )
		self.assertEqual( p2.keys(), p.keys() )

	def testOldSerialisation( self ) :

		# Old scripts call a constructor with an outdated signature as below.
		plug = GafferScene.TweakPlug( "exposure", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

	def testMissingModeForShaderNetwork( self ) :

		network = IECoreScene.ShaderNetwork(
			shaders = { "surface" : IECoreScene.Shader( "lambert", "ai:surface", { "Kd" : 0.25 } ) },
			output = "surface"
		)

		p = GafferScene.TweaksPlug()
		p["t"] = GafferScene.TweakPlug( "Ks", 0.5, GafferScene.TweakPlug.Mode.Replace )

		networkCopy = network.copy()
		with six.assertRaisesRegex( self, RuntimeError, "Cannot apply tweak with mode Replace to \"Ks\" : This parameter does not exist" ) :
			p.applyTweaks( networkCopy )

		with six.assertRaisesRegex( self, RuntimeError, "Cannot apply tweak with mode Replace to \"Ks\" : This parameter does not exist" ) :
			p.applyTweaks( networkCopy, missingMode = GafferScene.TweakPlug.MissingMode.Error )

		self.assertEqual( networkCopy, network )
		self.assertFalse( p.applyTweaks( networkCopy, missingMode = GafferScene.TweakPlug.MissingMode.Ignore ) )
		self.assertEqual( networkCopy, network )

		p["t"]["name"].setValue( "missingShader.parameterName" )

		with six.assertRaisesRegex( self, RuntimeError, "Cannot apply tweak \"missingShader.parameterName\" because shader \"missingShader\" does not exist" ) :
			p.applyTweaks( networkCopy )

		with six.assertRaisesRegex( self, RuntimeError, "Cannot apply tweak \"missingShader.parameterName\" because shader \"missingShader\" does not exist" ) :
			p.applyTweaks( networkCopy, missingMode = GafferScene.TweakPlug.MissingMode.Error )

		self.assertEqual( networkCopy, network )
		self.assertFalse( p.applyTweaks( networkCopy, missingMode = GafferScene.TweakPlug.MissingMode.Ignore ) )
		self.assertEqual( networkCopy, network )

	def testApplyReturnValues( self ) :

		parameters = IECore.CompoundData( { "a" : 0.0, "b" : 2.0 } )

		tweaks = GafferScene.TweaksPlug()

		# Test none to apply

		self.assertFalse( tweaks.applyTweaks( parameters ) )

		# Test none enabled

		tweaks.addChild( GafferScene.TweakPlug( "a", 1.0, GafferScene.TweakPlug.Mode.Replace, False ) )
		tweaks.addChild( GafferScene.TweakPlug( "b", 10.0, GafferScene.TweakPlug.Mode.Multiply, False ) )

		tweakedParameters = parameters.copy()
		self.assertFalse( tweaks.applyTweaks( parameters ) )
		self.assertEqual( tweakedParameters, parameters )

		# Test enabled

		tweaks[0]["enabled"].setValue( True )
		tweaks[1]["enabled"].setValue( True )

		self.assertTrue( tweaks.applyTweaks( parameters ) )

		# Test non-matching

		altParameters = IECore.CompoundData( { "c" : 0.0, "d" : 2.0 } )
		tweakedAltParameters = altParameters.copy()
		self.assertFalse( tweaks.applyTweaks( tweakedAltParameters, missingMode = GafferScene.TweakPlug.MissingMode.Ignore ) )
		self.assertEqual( tweakedAltParameters, altParameters )

		# Test empty names

		tweaks[0]["name"].setValue( "" )
		tweaks[1]["name"].setValue( "" )

		tweakedParameters = parameters.copy()
		self.assertFalse( tweaks.applyTweaks( parameters ) )
		self.assertEqual( tweakedParameters, parameters )

	def testApplyReturnValuesNetworkEdits( self ) :

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"surface" : IECoreScene.Shader( "lambert", "surface", { "c" : imath.Color3f( 1.0 ) } )
			},
			output = "surface"
		)

		textureShader = GafferSceneTest.TestShader( "texture" )

		tweaks = GafferScene.TweaksPlug()

		tweaks.addChild( GafferScene.TweakPlug( "c", Gaffer.Color3fPlug(), GafferScene.TweakPlug.Mode.Replace, False ) )
		tweaks[0]["value"].setInput( textureShader["out"] )

		# Test none to apply

		tweakedNetwork = network.copy()
		self.assertFalse( tweaks.applyTweaks( tweakedNetwork ) )
		self.assertEqual( tweakedNetwork, network )

		# Test enabled

		tweaks[0]["enabled"].setValue( True )

		tweakedNetwork = network.copy()
		self.assertTrue( tweaks.applyTweaks( tweakedNetwork ) )
		self.assertEqual( tweakedNetwork.inputConnections( "surface" ), [ ( ( "texture", "" ), ( "surface", "c" ) ) ] )

if __name__ == "__main__":
	unittest.main()
