##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

import imath
import unittest

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class OptionTweaksTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		options = GafferScene.CustomOptions()
		options["options"].addChild( Gaffer.NameValuePlug( "test", IECore.IntData( 10 ) ) )

		tweaks = GafferScene.OptionTweaks()
		tweaks["in"].setInput( options["out"] )

		self.assertSceneValid( tweaks["out"] )
		self.assertScenesEqual( tweaks["out"], options["out"] )
		self.assertSceneHashesEqual( tweaks["out"], options["out"] )
		self.assertEqual( options["out"]["globals"].getValue()["option:test"], IECore.IntData( 10 ) )

		testTweak = Gaffer.TweakPlug( "test", 5 )
		tweaks["tweaks"].addChild( testTweak )

		self.assertSceneValid( tweaks["out"] )

		self.assertEqual( tweaks["out"]["globals"].getValue()["option:test"], IECore.IntData( 5 ) )

		testTweak["value"].setValue( 2 )
		self.assertEqual( tweaks["out"]["globals"].getValue()["option:test"], IECore.IntData( 2 ) )

		testTweak["enabled"].setValue( False )
		self.assertEqual( tweaks["out"]["globals"].getValue()["option:test"], IECore.IntData( 10 ) )

		testTweak["enabled"].setValue( True )
		testTweak["mode"].setValue( testTweak.Mode.Add )
		self.assertEqual( tweaks["out"]["globals"].getValue()["option:test"], IECore.IntData( 12 ) )

		testTweak["mode"].setValue( testTweak.Mode.Subtract )
		testTweak["value"].setValue( 1 )
		self.assertEqual( tweaks["out"]["globals"].getValue()["option:test"], IECore.IntData( 9 ) )

		testTweak["mode"].setValue( testTweak.Mode.Multiply )
		testTweak["value"].setValue( 3 )
		self.assertEqual( tweaks["out"]["globals"].getValue()["option:test"], IECore.IntData( 30 ) )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["t"] = GafferScene.OptionTweaks()
		s["t"]["tweaks"].addChild( Gaffer.TweakPlug( "test", 1.0 ) )
		s["t"]["tweaks"].addChild( Gaffer.TweakPlug( "test", imath.Color3f( 1, 2, 3 ) ) )

		ss = Gaffer.ScriptNode()
		ss.execute( s.serialise() )

		self.assertEqual( len( ss["t"]["tweaks"].children() ), len( s["t"]["tweaks"].children() ) )

		for i in range( 0, len( s["t"]["tweaks"] ) ) :
			for n in s["t"]["tweaks"][i].keys() :
				self.assertEqual( ss["t"]["tweaks"][i][n].getValue(), s["t"]["tweaks"][i][n].getValue() )

	def testIgnoreMissing( self ) :

		options = GafferScene.CustomOptions()
		options["options"].addChild( Gaffer.NameValuePlug( "test", IECore.IntData( 10 ) ) )

		tweaks = GafferScene.OptionTweaks()
		tweaks["in"].setInput( options["out"] )

		tweak = Gaffer.TweakPlug( "badOption", 1 )
		tweaks["tweaks"].addChild( tweak )

		with self.assertRaisesRegex( RuntimeError, "Cannot apply tweak with mode Replace to \"badOption\" : This parameter does not exist" ) :
			tweaks["out"]["globals"].getValue()

		tweaks["ignoreMissing"].setValue( True )
		self.assertNotIn( "option:badOption", tweaks["out"]["globals"].getValue() )
		self.assertEqual( tweaks["out"]["globals"].getValue(), tweaks["in"]["globals"].getValue() )

		tweak["name"].setValue( "test" )
		self.assertEqual( tweaks["out"]["globals"].getValue()["option:test"], IECore.IntData( 1 ) )

		tweak["name"].setValue( "badOption.p" )
		self.assertNotIn( "option:badOption.p", tweaks["out"]["globals"].getValue() )
		self.assertEqual( tweaks["out"]["globals"].getValue(), tweaks["in"]["globals"].getValue() )

	def testCreateMode( self ) :

		options = GafferScene.CustomOptions()

		tweaks = GafferScene.OptionTweaks()
		tweaks["in"].setInput( options["out"] )

		self.assertNotIn( "option:test", tweaks["out"]["globals"].getValue() )

		testTweak = Gaffer.TweakPlug( "test", 10 )
		testTweak["mode"].setValue( Gaffer.TweakPlug.Mode.Create )
		tweaks["tweaks"].addChild( testTweak )

		self.assertEqual( tweaks["out"]["globals"].getValue()["option:test"], IECore.IntData( 10 ) )


if __name__ == "__main__" :
	unittest.main()
