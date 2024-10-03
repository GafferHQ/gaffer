##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferTest
import imath
import IECore

class DotTest( GafferTest.TestCase ) :

	def test( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()

		s["d"] = Gaffer.Dot()
		s["d"].setup( s["n2"]["op1"] )

		s["d"]["in"].setInput( s["n1"]["sum"] )
		s["n2"]["op1"].setInput( s["d"]["out"] )

		self.assertTrue( s["n2"]["op1"].source().isSame( s["n1"]["sum"] ) )

	def testUndo( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()

		s["d"] = Gaffer.Dot()
		self.assertTrue( "in" not in s["d"] )
		self.assertTrue( "out" not in s["d"] )

		with Gaffer.UndoScope( s ) :
			s["d"].setup( s["n2"]["op1"] )
			s["d"]["in"].setInput( s["n1"]["sum"] )
			s["n2"]["op1"].setInput( s["d"]["out"] )

		self.assertTrue( s["n2"]["op1"].source().isSame( s["n1"]["sum"] ) )

		s.undo()

		self.assertTrue( "in" not in s["d"] )
		self.assertTrue( "out" not in s["d"] )

		s.redo()

		self.assertTrue( s["n2"]["op1"].source().isSame( s["n1"]["sum"] ) )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()

		s["d"] = Gaffer.Dot()
		s["d"].setup( s["n2"]["op1"] )

		s["d"]["in"].setInput( s["n1"]["sum"] )
		s["n2"]["op1"].setInput( s["d"]["out"] )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( s2["n2"]["op1"].source().isSame( s2["n1"]["sum"] ) )

	def testSerialisationWithNonSerialisableConnections( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()

		s["n1"]["sum"].setFlags( Gaffer.Plug.Flags.Serialisable, False )

		s["d"] = Gaffer.Dot()
		s["d"].setup( s["n1"]["sum"] )

		s["d"]["in"].setInput( s["n1"]["sum"] )
		s["n2"]["op1"].setInput( s["d"]["out"] )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( s2["n2"]["op1"].source().isSame( s2["n1"]["sum"] ) )

	def testDeletion( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()

		s["d"] = Gaffer.Dot()
		s["d"].setup( s["n2"]["op1"] )

		s["d"]["in"].setInput( s["n1"]["sum"] )
		s["n2"]["op1"].setInput( s["d"]["out"] )

		s.deleteNodes( filter = Gaffer.StandardSet( [ s["d"] ] ) )

		self.assertTrue( s["n2"]["op1"].getInput().isSame( s["n1"]["sum"] ) )

	def testArrayPlug( self ) :

		n1 = Gaffer.Node()
		n1["a"] = Gaffer.ArrayPlug( elementPrototype = Gaffer.IntPlug() )

		n2 = Gaffer.Node()
		n2["a"] = Gaffer.ArrayPlug( elementPrototype = Gaffer.IntPlug() )

		d = Gaffer.Dot()
		d.setup( n1["a"] )
		d["in"].setInput( n1["a"] )
		n2["a"].setInput( d["out"] )

		self.assertEqual( len( d["out"] ), 1 )
		self.assertTrue( d["out"].source().isSame( n1["a"] ) )
		self.assertTrue( d["out"][0].source().isSame( n1["a"][0] ) )

		i = Gaffer.IntPlug()
		n1["a"][0].setInput( i )

		self.assertEqual( len( n1["a"] ), 2 )
		self.assertEqual( len( d["in"] ), 2 )
		self.assertEqual( len( d["out"] ), 2 )
		self.assertTrue( d["out"].source().isSame( n1["a"] ) )
		self.assertTrue( d["out"][0].source().isSame( i ) )
		self.assertTrue( d["out"][1].source().isSame( n1["a"][1] ) )

	def testSetupCopiesPlugColorMetadata( self ):

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["d"] = Gaffer.Dot()

		plug = s["n1"]["op1"]

		connectionColor = imath.Color3f( 0.1 , 0.2 , 0.3 )
		noodleColor = imath.Color3f( 0.4, 0.5 , 0.6 )

		Gaffer.Metadata.registerValue( plug, "connectionGadget:color", connectionColor )
		Gaffer.Metadata.registerValue( plug, "nodule:color", noodleColor )

		s["d"].setup( s["n1"]["op1"] )

		self.assertEqual( Gaffer.Metadata.value( s["d"]["in"], "connectionGadget:color" ), connectionColor )
		self.assertEqual( Gaffer.Metadata.value( s["d"]["in"], "nodule:color" ), noodleColor )

		self.assertEqual( Gaffer.Metadata.value( s["d"]["out"], "connectionGadget:color" ), connectionColor )
		self.assertEqual( Gaffer.Metadata.value( s["d"]["out"], "nodule:color" ), noodleColor )

	def testSerialisationUsesSetup( self ) :

		s1 = Gaffer.ScriptNode()
		s1["d"] = Gaffer.Dot()
		s1["d"].setup( Gaffer.IntPlug() )

		ss = s1.serialise()
		self.assertIn( "setup", ss )
		self.assertEqual( ss.count( "addChild" ), 1 )
		self.assertNotIn( "Dynamic", ss )
		self.assertNotIn( "setInput", ss )

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )
		self.assertIn( "in", s2["d"] )
		self.assertIn( "out", s2["d"] )
		self.assertIsInstance( s2["d"]["in"], Gaffer.IntPlug )
		self.assertIsInstance( s2["d"]["out"], Gaffer.IntPlug )

	def testPlugMetadataSerialisation( self ) :

		s1 = Gaffer.ScriptNode()
		s1["d"] = Gaffer.Dot()
		s1["d"].setup( Gaffer.IntPlug() )

		Gaffer.Metadata.registerValue( s1["d"]["in"], "test", 1 )
		Gaffer.Metadata.registerValue( s1["d"]["out"], "test", 2 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s1.serialise() )

		self.assertEqual( Gaffer.Metadata.value( s2["d"]["in"], "test" ), 1 )
		self.assertEqual( Gaffer.Metadata.value( s2["d"]["out"], "test" ), 2 )

if __name__ == "__main__":
	unittest.main()
