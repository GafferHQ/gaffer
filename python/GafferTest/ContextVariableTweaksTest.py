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

import unittest
import imath
import six

import IECore

import Gaffer
import GafferTest


class ContextVariableTweaksTest( GafferTest.TestCase ) :

	def test( self ) :

		n = GafferTest.StringInOutNode()
		self.assertHashesValid( n )

		t = Gaffer.ContextVariableTweaks()
		t.setup( n["out"] )
		t["in"].setInput( n["out"] )

		c = Gaffer.ContextVariables()
		c.setup( t["out"] )
		c["in"].setInput( t["out"] )

		n["in"].setValue( "$a" )
		self.assertEqual( c["out"].getValue(), "" )

		c["variables"].addChild( Gaffer.NameValuePlug( "a", IECore.StringData( "A" ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		self.assertEqual( c["out"].getValue(), "A" )

		tweak = Gaffer.TweakPlug( "a", "AA" )
		t["tweaks"].addChild( tweak )

		self.assertEqual( c["out"].getValue(), "AA" )

		tweak["value"].setValue( "BB" )
		self.assertEqual( c["out"].getValue(), "BB" )

		tweak["enabled"].setValue( False )
		self.assertEqual( c["out"].getValue(), "A" )

		tweak["enabled"].setValue( True )
		tweak["mode"].setValue( Gaffer.TweakPlug.Mode.Remove )
		self.assertEqual( c["out"].getValue(), "" )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["t"] = Gaffer.ContextVariableTweaks()
		s["t"]["tweaks"].addChild( Gaffer.TweakPlug( "test", 1.0 ) )
		s["t"]["tweaks"].addChild( Gaffer.TweakPlug( "test", imath.Color3f( 1, 2, 3 ) ) )

		ss = Gaffer.ScriptNode()
		ss.execute( s.serialise() )

		for i in range( 0, len( s["t"]["tweaks"] ) ) :
			for n in s["t"]["tweaks"][i].keys() :
				self.assertEqual( ss["t"]["tweaks"][i][n].getValue(), s["t"]["tweaks"][i][n].getValue() )

	def testIgnoreMissing( self ) :

		n = GafferTest.StringInOutNode()
		n["in"].setValue( "$a" )

		t = Gaffer.ContextVariableTweaks()
		t.setup( n["out"] )
		t["in"].setInput( n["out"] )

		c = Gaffer.ContextVariables()
		c.setup( t["out"] )
		c["in"].setInput( t["out"] )
		c["variables"].addChild( Gaffer.NameValuePlug( "a", IECore.StringData( "A" ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		self.assertEqual( c["out"].getValue(), "A" )

		tweak = Gaffer.TweakPlug( "missing", "AA" )
		t["tweaks"].addChild( tweak )

		with six.assertRaisesRegex( self, RuntimeError, "Cannot apply tweak with mode Replace to \"missing\" : This parameter does not exist" ) :
			c["out"].getValue()

		t["ignoreMissing"].setValue( True )
		self.assertEqual( c["out"].getValue(), "A" )

		tweak["name"].setValue( "a" )
		self.assertEqual( c["out"].getValue(), "AA" )

	def testCreateIfMissing( self ) :

		n = GafferTest.StringInOutNode()
		n["in"].setValue( "$a" )

		t = Gaffer.ContextVariableTweaks()
		t.setup( n["out"] )
		t["in"].setInput( n["out"] )

		c = Gaffer.ContextVariables()
		c.setup( t["out"] )
		c["in"].setInput( t["out"] )

		tweak = Gaffer.TweakPlug( "a", "AA" )
		tweak["mode"].setValue( Gaffer.TweakPlug.Mode.CreateIfMissing )
		t["tweaks"].addChild( tweak )

		self.assertEqual( c["out"].getValue(), "AA" )

		c["variables"].addChild( Gaffer.NameValuePlug( "a", IECore.StringData( "A" ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		self.assertEqual( c["out"].getValue(), "A" )


if __name__ == "__main__" :
	unittest.main()
