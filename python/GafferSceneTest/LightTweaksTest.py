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

import unittest

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class LightTweaksTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		l = GafferSceneTest.TestLight()
		l["parameters"]["intensity"].setValue( IECore.Color3f( 1 ) )

		t = GafferScene.LightTweaks()
		t["in"].setInput( l["out"] )

		self.assertSceneValid( t["out"] )
		self.assertScenesEqual( t["out"], l["out"] )
		self.assertSceneHashesEqual( t["out"], l["out"] )
		self.assertEqual( l["out"].attributes( "/light" )["light"][0].parameters["intensity"].value, IECore.Color3f( 1 ) )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		t["filter"].setInput( f["out"] )

		self.assertSceneValid( t["out"] )
		self.assertScenesEqual( t["out"], l["out"] )
		self.assertSceneHashesEqual( t["out"], l["out"] )

		intensityTweak = t.TweakPlug( "intensity", IECore.Color3f( 1, 0, 0 ) )
		t["tweaks"].addChild( intensityTweak )

		self.assertSceneValid( t["out"] )

		self.assertEqual( t["out"].attributes( "/light" )["light"][0].parameters["intensity"].value, IECore.Color3f( 1, 0, 0 ) )

		intensityTweak["value"].setValue( IECore.Color3f( 100 ) )
		self.assertEqual( t["out"].attributes( "/light" )["light"][0].parameters["intensity"].value, IECore.Color3f( 100 ) )

		intensityTweak["enabled"].setValue( False )
		self.assertEqual( t["out"].attributes( "/light" )["light"][0].parameters["intensity"].value, IECore.Color3f( 1 ) )

		intensityTweak["enabled"].setValue( True )
		intensityTweak["mode"].setValue( intensityTweak.Mode.Add )
		self.assertEqual( t["out"].attributes( "/light" )["light"][0].parameters["intensity"].value, IECore.Color3f( 101 ) )

		intensityTweak["mode"].setValue( intensityTweak.Mode.Subtract )
		intensityTweak["value"].setValue( IECore.Color3f( 0.1, 0.2, 0.3 ) )
		self.assertEqual( t["out"].attributes( "/light" )["light"][0].parameters["intensity"].value, IECore.Color3f( 0.9, 0.8, 0.7 ) )

		intensityTweak["mode"].setValue( intensityTweak.Mode.Multiply )
		l["parameters"]["intensity"].setValue( IECore.Color3f( 2 ) )
		self.assertEqual( t["out"].attributes( "/light" )["light"][0].parameters["intensity"].value, IECore.Color3f( 0.2, 0.4, 0.6 ) )

		t["type"].setValue( "" )
		self.assertScenesEqual( t["out"], l["out"] )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["t"] = GafferScene.LightTweaks()
		s["t"]["tweaks"].addChild( GafferScene.LightTweaks.TweakPlug( "test", 1.0 ) )
		s["t"]["tweaks"].addChild( GafferScene.LightTweaks.TweakPlug( "test", IECore.Color3f( 1, 2, 3 ) ) )

		ss = Gaffer.ScriptNode()
		ss.execute( s.serialise() )

		for i in range( 0, len( s["t"]["tweaks"] ) ) :
			for n in s["t"]["tweaks"][i].keys() :
				self.assertEqual( ss["t"]["tweaks"][i][n].getValue(), s["t"]["tweaks"][i][n].getValue() )

if __name__ == "__main__":
	unittest.main()
