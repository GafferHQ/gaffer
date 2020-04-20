##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import GafferTest

class DeleteContextVariablesTest( GafferTest.TestCase ) :

	def test( self ) :

		n = GafferTest.StringInOutNode()

		d = Gaffer.DeleteContextVariables()
		d.setup( Gaffer.StringPlug() )
		d["in"].setInput( n["out"] )

		c = Gaffer.ContextVariables()
		c.setup( Gaffer.StringPlug() )
		c["in"].setInput( d["out"] )

		n["in"].setValue( "$a" )
		self.assertEqual( c["out"].getValue(), "" )

		c["variables"].addChild( Gaffer.NameValuePlug( "a", IECore.StringData( "A" ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		self.assertEqual( c["out"].getValue(), "A" )

		d["variables"].setValue( "a" )
		self.assertEqual( c["out"].getValue(), "" )

	def testPatternMatching( self ) :

		n = GafferTest.StringInOutNode()
		self.assertHashesValid( n )

		d = Gaffer.DeleteContextVariables()
		d.setup( Gaffer.StringPlug() )
		d["in"].setInput( n["out"] )

		c = Gaffer.ContextVariables()
		c.setup( Gaffer.StringPlug() )
		c["in"].setInput( d["out"] )


		n["in"].setValue( "$a1_$a2_$b1_$b2_$c1_$c2" )
		self.assertEqual( c["out"].getValue(), "_____" )

		c["variables"].addChild( Gaffer.NameValuePlug( "a1", IECore.StringData( "A1" ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic) )
		c["variables"].addChild( Gaffer.NameValuePlug( "a2", IECore.StringData( "A2" ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic) )
		c["variables"].addChild( Gaffer.NameValuePlug( "b1", IECore.StringData( "B1" ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic) )
		c["variables"].addChild( Gaffer.NameValuePlug( "b2", IECore.StringData( "B2" ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic) )
		c["variables"].addChild( Gaffer.NameValuePlug( "c1", IECore.StringData( "C1" ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic) )
		c["variables"].addChild( Gaffer.NameValuePlug( "c2", IECore.StringData( "C2" ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic) )
		self.assertEqual( c["out"].getValue(), "A1_A2_B1_B2_C1_C2" )

		d["variables"].setValue( "a* c*" )

		self.assertEqual( c["out"].getValue(), "__B1_B2__" )

	def testDirtyPropagation( self ) :

		n = GafferTest.StringInOutNode()

		d = Gaffer.DeleteContextVariables()
		d.setup( Gaffer.StringPlug() )
		d["in"].setInput( n["out"] )

		# deleting a variable should dirty the output:
		dirtied = GafferTest.CapturingSlot( d.plugDirtiedSignal() )
		d["variables"].setValue( "a" )
		self.assertIn( d["out"], [ p[0] for p in dirtied ] )

if __name__ == "__main__":
	unittest.main()
