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
import six

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class AttributeTweaksTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		l = GafferSceneTest.TestLight()
		l["visualiserAttributes"]["scale"]["enabled"].setValue( True )
		l["visualiserAttributes"]["scale"]["value"].setValue( 5 )

		t = GafferScene.AttributeTweaks()
		t["in"].setInput( l["out"] )

		self.assertSceneValid( t["out"] )
		self.assertScenesEqual( t["out"], l["out"] )
		self.assertSceneHashesEqual( t["out"], l["out"] )
		self.assertEqual( l["out"].attributes( "/light" )["gl:visualiser:scale"], IECore.FloatData( 5.0 ) )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		t["filter"].setInput( f["out"] )

		self.assertSceneValid( t["out"] )
		self.assertScenesEqual( t["out"], l["out"] )
		self.assertSceneHashesEqual( t["out"], l["out"] )

		scaleTweak = Gaffer.TweakPlug( "gl:visualiser:scale", 10.0 )
		t["tweaks"].addChild( scaleTweak )

		self.assertSceneValid( t["out"] )

		self.assertEqual( t["out"].attributes( "/light" )["gl:visualiser:scale"], IECore.FloatData( 10.0 ) )

		scaleTweak["value"].setValue( 20 )
		self.assertEqual( t["out"].attributes( "/light" )["gl:visualiser:scale"], IECore.FloatData( 20.0 ) )

		scaleTweak["enabled"].setValue( False )
		self.assertEqual( t["out"].attributes( "/light" )["gl:visualiser:scale"], IECore.FloatData( 5.0 ) )

		scaleTweak["enabled"].setValue( True )
		scaleTweak["mode"].setValue( scaleTweak.Mode.Add )
		self.assertEqual( t["out"].attributes( "/light" )["gl:visualiser:scale"], IECore.FloatData( 25.0 ) )

		scaleTweak["mode"].setValue( scaleTweak.Mode.Subtract )
		scaleTweak["value"].setValue( 1 )
		self.assertEqual( t["out"].attributes( "/light" )["gl:visualiser:scale"], IECore.FloatData( 4.0 ) )

		scaleTweak["mode"].setValue( scaleTweak.Mode.Multiply )
		scaleTweak["value"].setValue( 3 )
		self.assertEqual( t["out"].attributes( "/light" )["gl:visualiser:scale"], IECore.FloatData( 15.0 ) )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["t"] = GafferScene.AttributeTweaks()
		s["t"]["tweaks"].addChild( Gaffer.TweakPlug( "test", 1.0 ) )
		s["t"]["tweaks"].addChild( Gaffer.TweakPlug( "test", imath.Color3f( 1, 2, 3 ) ) )

		ss = Gaffer.ScriptNode()
		ss.execute( s.serialise() )

		for i in range( 0, len( s["t"]["tweaks"] ) ) :
			for n in s["t"]["tweaks"][i].keys() :
				self.assertEqual( ss["t"]["tweaks"][i][n].getValue(), s["t"]["tweaks"][i][n].getValue() )

	def testIgnoreMissing( self ) :

		l = GafferSceneTest.TestLight()
		l["visualiserAttributes"]["scale"]["enabled"].setValue( True )
		l["visualiserAttributes"]["scale"]["value"].setValue( 5.0 )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		t = GafferScene.AttributeTweaks()
		t["in"].setInput( l["out"] )
		t["filter"].setInput( f["out"] )

		tweak = Gaffer.TweakPlug( "badAttribute", 1.0 )
		t["tweaks"].addChild( tweak )

		with six.assertRaisesRegex( self, RuntimeError, "Cannot apply tweak with mode Replace to \"badAttribute\" : This parameter does not exist" ) :
			t["out"].attributes( "/light" )

		t["ignoreMissing"].setValue( True )
		self.assertEqual( t["out"].attributes( "/light" ), t["in"].attributes( "/light" ) )

		tweak["name"].setValue( "gl:visualiser:scale" )
		self.assertIn( "gl:visualiser:scale", t["out"].attributes( "/light" ) )
		self.assertEqual( t["out"].attributes( "/light" )["gl:visualiser:scale"], IECore.FloatData( 1.0 ) )

		tweak["name"].setValue( "badAttribute.p" )
		self.assertEqual( t["out"].attributes( "/light" ), t["in"].attributes( "/light" ) )

	def testLocalise( self ) :

		plane = GafferScene.Plane()
		group = GafferScene.Group()
		group["in"][0].setInput( plane["out"] )

		attributes = GafferScene.StandardAttributes()
		attributes["attributes"]["transformBlurSegments"]["enabled"].setValue( True )
		attributes["attributes"]["transformBlurSegments"]["value"].setValue( 5 )

		groupFilter = GafferScene.PathFilter()
		groupFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		attributes["in"].setInput( group["out"] )
		attributes["filter"].setInput( groupFilter["out"] )

		self.assertIn( "gaffer:transformBlurSegments", attributes["out"].attributes( "/group" ) )
		self.assertNotIn( "gaffer:transformBlurSegments", attributes["out"].attributes( "/group/plane" ) )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )

		tweaks = GafferScene.AttributeTweaks()
		tweaks["in"].setInput( attributes["out"] )
		tweaks["filter"].setInput( planeFilter["out"] )

		segmentsTweak = Gaffer.TweakPlug( "gaffer:transformBlurSegments", 2 )
		tweaks["tweaks"].addChild( segmentsTweak )

		self.assertEqual( tweaks["localise"].getValue(), False )
		with six.assertRaisesRegex( self, RuntimeError, "Cannot apply tweak with mode Replace to \"gaffer:transformBlurSegments\" : This parameter does not exist" ) :
			tweaks["out"].attributes( "/group/plane" )

		tweaks["localise"].setValue( True )

		groupAttr = tweaks["out"].attributes( "/group" )
		self.assertEqual( groupAttr["gaffer:transformBlurSegments"], IECore.IntData( 5 ) )

		planeAttr = tweaks["out"].attributes( "/group/plane" )
		self.assertIn( "gaffer:transformBlurSegments", planeAttr )
		self.assertEqual( planeAttr["gaffer:transformBlurSegments"], IECore.IntData( 2 ) )

		# Test disabling tweak results in no localisation

		segmentsTweak["enabled"].setValue( False )
		self.assertNotIn( "gaffer:transformBlurSegments", tweaks["out"].attributes( "/group/plane" ) )

	def testCreateMode( self ) :

		plane = GafferScene.Plane()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		tweaks = GafferScene.AttributeTweaks()
		tweaks["in"].setInput( plane["out"] )
		tweaks["filter"].setInput( planeFilter["out"] )

		self.assertNotIn( "test:attribute", tweaks["out"].attributes( "/plane" ) )

		testTweak = Gaffer.TweakPlug( "test:attribute", 2 )
		testTweak["mode"].setValue( Gaffer.TweakPlug.Mode.Create )
		tweaks["tweaks"].addChild( testTweak )

		self.assertEqual( tweaks["out"].attributes( "/plane" )["test:attribute"], IECore.IntData( 2 ) )


if __name__ == "__main__" :
	unittest.main()
