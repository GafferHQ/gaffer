##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

class BoxOutTest( GafferTest.TestCase ) :

	def testSetup( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.AddNode()

		s["b"]["o"] = Gaffer.BoxOut()
		self.assertEqual( s["b"]["o"]["name"].getValue(), "out" )
		self.assertEqual( s["b"]["o"]["name"].defaultValue(), "out" )

		s["b"]["o"]["name"].setValue( "sum" )
		s["b"]["o"].setup( s["b"]["n"]["sum"] )
		s["b"]["o"]["in"].setInput( s["b"]["n"]["sum"] )

		self.assertTrue( "sum" in s["b"] )
		self.assertTrue( s["b"]["sum"].source().isSame( s["b"]["n"]["sum"] ) )

	def testNameTracking( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.AddNode()

		s["b"]["o"] = Gaffer.BoxOut()
		s["b"]["o"]["name"].setValue( "test" )
		s["b"]["o"].setup( s["b"]["n"]["sum"] )
		promoted = s["b"]["o"].promotedPlug()

		self.assertEqual( s["b"]["o"]["name"].getValue(), "test" )
		self.assertEqual( promoted.getName(), s["b"]["o"]["name"].getValue() )

		with Gaffer.UndoScope( s ) :
			promoted.setName( "bob" )

		self.assertEqual( promoted.getName(), "bob" )
		self.assertEqual( s["b"]["o"]["name"].getValue(), "bob" )

		s.undo()

		self.assertEqual( s["b"]["o"]["name"].getValue(), "test" )
		self.assertEqual( promoted.getName(), s["b"]["o"]["name"].getValue() )

		with Gaffer.UndoScope( s ) :
			s["b"]["o"]["name"].setValue( "jim" )

		self.assertEqual( promoted.getName(), "jim" )
		self.assertEqual( s["b"]["o"]["name"].getValue(), "jim" )

		s.undo()

		self.assertEqual( s["b"]["o"]["name"].getValue(), "test" )
		self.assertEqual( promoted.getName(), s["b"]["o"]["name"].getValue() )

	def testDeleteRemovesPromotedPlugs( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.AddNode()

		s["b"]["o"] = Gaffer.BoxOut()
		s["b"]["o"].setup( s["b"]["n"]["sum"] )
		s["b"]["o"]["in"].setInput( s["b"]["n"]["sum"] )

		self.assertTrue( "out" in s["b"] )
		self.assertTrue( s["b"]["out"].source().isSame( s["b"]["n"]["sum"] ) )

		with Gaffer.UndoScope( s ) :
			del s["b"]["o"]

		self.assertFalse( "out" in s["b"] )

		s.undo()

		self.assertTrue( "out" in s["b"] )
		self.assertTrue( s["b"]["out"].source().isSame( s["b"]["n"]["sum"] ) )

	def testPaste( self ) :

		s = Gaffer.ScriptNode()
		s["b1"] = Gaffer.Box()
		s["b1"]["n"] = GafferTest.AddNode()

		s["b1"]["o"] = Gaffer.BoxOut()
		s["b1"]["o"]["name"].setValue( "test" )
		s["b1"]["o"].setup( s["b1"]["n"]["sum"] )
		s["b1"]["o"]["in"].setInput( s["b1"]["n"]["sum"] )

		s["b2"] = Gaffer.Box()
		s.execute(
			s.serialise( parent = s["b1"], filter = Gaffer.StandardSet( [ s["b1"]["n"], s["b1"]["o"] ] ) ),
			parent = s["b2"],
		)

		self.assertTrue( "test" in s["b2"] )
		self.assertTrue( s["b2"]["test"].source().isSame( s["b2"]["n"]["sum"] ) )

	def testMetadata( self ) :

		s = Gaffer.ScriptNode()
		s["b1"] = Gaffer.Box()
		s["b1"]["n"] = GafferTest.AddNode()

		Gaffer.Metadata.registerValue( s["b1"]["n"]["sum"], "test", "testValue" )
		Gaffer.Metadata.registerValue( s["b1"]["n"]["sum"], "layout:section", "sectionName" )

		s["b1"]["o"] = Gaffer.BoxIn()
		s["b1"]["o"].setup( s["b1"]["n"]["sum"] )

		self.assertEqual( Gaffer.Metadata.value( s["b1"]["o"].promotedPlug(), "test" ), "testValue" )
		self.assertNotIn( "layout:section", Gaffer.Metadata.registeredValues( s["b1"]["o"].promotedPlug(), Gaffer.Metadata.RegistrationTypes.Instance ) )

		s["b2"] = Gaffer.Box()
		s.execute(
			s.serialise( parent = s["b1"], filter = Gaffer.StandardSet( [ s["b1"]["o"] ] ) ),
			parent = s["b2"],
		)

		self.assertEqual( Gaffer.Metadata.value( s["b2"]["o"].promotedPlug(), "test" ), "testValue" )
		self.assertNotIn( "layout:section", Gaffer.Metadata.registeredValues( s["b2"]["o"].promotedPlug(), Gaffer.Metadata.RegistrationTypes.Instance ) )

	def testNoduleSectionMetadata( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.AddNode()

		Gaffer.Metadata.registerValue( s["b"]["n"]["sum"], "noduleLayout:section", "right" )

		s["b"]["o"] = Gaffer.BoxOut()
		s["b"]["o"].setup( s["b"]["n"]["sum"] )

		self.assertEqual( Gaffer.Metadata.value( s["b"]["o"].promotedPlug(), "noduleLayout:section" ), "right" )
		self.assertEqual( Gaffer.Metadata.value( s["b"]["o"].plug(), "noduleLayout:section" ), "left" )

	def testPromotedPlugRemovalDeletesBoxOut( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.AddNode()

		s["b"]["o"] = Gaffer.BoxOut()
		s["b"]["o"]["name"].setValue( "sum" )
		s["b"]["o"].setup( s["b"]["n"]["sum"] )
		s["b"]["o"]["in"].setInput( s["b"]["n"]["sum"] )

		def assertPreconditions() :

			self.assertTrue( "sum" in s["b"] )
			self.assertTrue( "o" in s["b"] )
			self.assertTrue( s["b"]["o"]["in"].getInput().isSame( s["b"]["n"]["sum"] ) )
			self.assertTrue( s["b"]["sum"].source().isSame( s["b"]["n"]["sum"] ) )

		assertPreconditions()

		with Gaffer.UndoScope( s ) :
			del s["b"]["sum"]

		def assertPostconditions() :

			self.assertFalse( "sum" in s["b"] )
			self.assertFalse( "o" in s["b"] )
			self.assertEqual( len( s["b"]["n"]["sum"].outputs() ), 0 )

		assertPostconditions()

		s.undo()

		assertPreconditions()

		s.redo()

		assertPostconditions()

	def testNonSerialisableInput( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["a"] = GafferTest.AddNode()
		s["b"]["a"]["sum"].setFlags( Gaffer.Plug.Flags.Serialisable, False )

		s["b"]["o"] = Gaffer.BoxOut()
		s["b"]["o"].setup( s["b"]["a"]["sum"] )
		s["b"]["o"]["in"].setInput( s["b"]["a"]["sum"] )
		promotedPlug = s["b"]["o"].promotedPlug()

		self.assertTrue( promotedPlug.source().isSame( s["b"]["a"]["sum"] ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( s2["b"][promotedPlug.getName()].source().isSame( s2["b"]["a"]["sum"] ) )

	def testSerialisationUsesSetup( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.BoxOut()
		s["b"].setup( Gaffer.IntPlug() )

		ss = s.serialise()
		self.assertIn( "setup", ss )
		self.assertNotIn( "setInput", ss )
		self.assertNotIn( "__out", ss )
		self.assertEqual( ss.count( "addChild" ), 1 )

	def testPassThrough( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["a"] = GafferTest.AddNode()

		s["b"]["i"] = Gaffer.BoxIn()
		s["b"]["i"].setup( s["b"]["a"]["op1"] )

		s["b"]["o"] = Gaffer.BoxOut()
		s["b"]["o"].setup( s["b"]["a"]["op1"] )
		self.assertTrue( isinstance( s["b"]["o"]["passThrough"], Gaffer.IntPlug ) )
		self.assertFalse( s["b"]["o"]["passThrough"].acceptsInput( s["b"]["a"]["sum"] ) )

		s["b"]["a"]["op1"].setInput( s["b"]["i"]["out"] )
		s["b"]["o"]["in"].setInput( s["b"]["a"]["sum"] )
		s["b"]["o"]["passThrough"].setInput( s["b"]["i"]["out"] )

		self.assertTrue( "enabled" in s["b"] )
		self.assertEqual( s["b"]["out"].source(), s["b"]["a"]["sum"] )
		s["b"]["enabled"].setValue( False )
		self.assertEqual( s["b"]["out"].source(), s["b"]["in"] )

		self.assertEqual( s["b"].correspondingInput( s["b"]["out"] ), s["b"]["in"] )

	def testPassThroughInputAcceptance( self ) :

		s = Gaffer.ScriptNode()

		s["a"] = GafferTest.AddNode()

		s["b"] = Gaffer.Box()
		s["b"]["a"] = GafferTest.AddNode()

		s["b"]["o"] = Gaffer.BoxOut()
		s["b"]["o"].setup( s["b"]["a"]["op1"] )

		# Don't accept input from any old node

		self.assertFalse( s["b"]["o"]["passThrough"].acceptsInput( s["b"]["a"]["sum"] ) )
		self.assertFalse( s["b"]["o"]["passThrough"].acceptsInput( s["a"]["sum"] ) )

		# Do accept input from BoxIn

		s["b"]["i"] = Gaffer.BoxIn()
		s["b"]["i"].setup( s["b"]["a"]["op1"] )

		self.assertTrue( s["b"]["o"]["passThrough"].acceptsInput( s["b"]["i"]["out"] ) )

		# Do accept input from unconnected Dot

		s["b"]["d"] = Gaffer.Dot()
		s["b"]["d"].setup( s["b"]["a"]["op1"] )
		self.assertTrue( s["b"]["o"]["passThrough"].acceptsInput( s["b"]["d"]["out"] ) )

		# And Dot connected to BoxIn

		s["b"]["d"]["in"].setInput( s["b"]["i"]["out"] )
		self.assertTrue( s["b"]["o"]["passThrough"].acceptsInput( s["b"]["d"]["out"] ) )

		# And Dot connected to unconnected Dot

		s["b"]["d2"] = Gaffer.Dot()
		s["b"]["d2"].setup( s["b"]["a"]["op1"] )
		s["b"]["d"]["in"].setInput( s["b"]["d2"]["out"] )
		self.assertTrue( s["b"]["o"]["passThrough"].acceptsInput( s["b"]["d"]["out"] ) )

		# But not Dot connected to something else

		s["b"]["d"]["in"].setInput( s["b"]["a"]["sum"] )
		self.assertFalse( s["b"]["o"]["passThrough"].acceptsInput( s["b"]["d"]["out"] ) )

	def testInsertAndPassThrough( self ) :

		s = Gaffer.ScriptNode()

		s["a1"] = GafferTest.AddNode()

		s["a2"] = GafferTest.AddNode()
		s["a2"]["op1"].setInput( s["a1"]["sum"] )
		s["a2"]["op2"].setValue( 10 )

		s["a3"] = GafferTest.AddNode()
		s["a3"]["op1"].setInput( s["a2"]["sum"] )

		Gaffer.Metadata.registerValue( s["a2"]["op1"], "nodule:type", "GafferUI::StandardNodule" )
		Gaffer.Metadata.registerValue( s["a2"]["sum"], "nodule:type", "GafferUI::StandardNodule" )

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["a2"] ] ) )
		Gaffer.BoxIO.insert( b )

		b["BoxOut"]["passThrough"].setInput( b["BoxIn"]["out"] )
		self.assertIn( "enabled", b )

		self.assertEqual( b["sum"].getValue(), 10 )
		b["enabled"].setValue( False )
		self.assertEqual( b["sum"].getValue(), 0 )

if __name__ == "__main__":
	unittest.main()
