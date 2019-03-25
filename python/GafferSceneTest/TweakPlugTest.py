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

		parameters = IECore.CompoundData( { "b" : 2.0 } )
		tweaks.applyTweaks( parameters )
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

		tweaks.applyTweaks( network )

		self.assertEqual( network.getShader( "texture" ).parameters["sscale"].value, 11.0 )
		self.assertEqual( network.getShader( "surface" ).parameters["Kd"].value, 0.75 )

	def testThrowOnMissingShader( self ) :

		network = IECoreScene.ShaderNetwork(
			shaders = { "surface" : IECoreScene.Shader( "lambert", "ai:surface" ) },
		)

		tweaks = Gaffer.Plug()
		tweaks.addChild( GafferScene.TweakPlug( "missingShader", 0.5 ) )

		with self.assertRaisesRegexp( RuntimeError, "" ) :
			GafferScene.TweakPlug.applyTweaks( tweaks, network )

	def testWrongDataType( self ) :

		p = GafferScene.TweakPlug( "test", imath.Color3f( 1 ) )
		p["mode"].setValue( p.Mode.Multiply )
		self.assertIsInstance( p["value"], Gaffer.Color3fPlug )

		d = IECore.CompoundData( { "test" : 1 } )

		with self.assertRaisesRegexp( RuntimeError, "Cannot apply tweak to \"test\" : Value of type \"IntData\" does not match parameter of type \"Color3fData\"" ) :
			p.applyTweak( d )

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

if __name__ == "__main__":
	unittest.main()
