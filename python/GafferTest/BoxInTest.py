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

class BoxInTest( GafferTest.TestCase ) :

	def testSetup( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.AddNode()

		s["b"]["i"] = Gaffer.BoxIn()
		self.assertEqual( s["b"]["i"]["name"].getValue(), "in" )
		self.assertEqual( s["b"]["i"]["name"].defaultValue(), "in" )

		s["b"]["i"]["name"].setValue( "op1" )
		s["b"]["i"].setup( s["b"]["n"]["op1"] )
		s["b"]["n"]["op1"].setInput( s["b"]["i"]["out"] )

		self.assertTrue( "op1" in s["b"] )
		self.assertTrue( s["b"]["n"]["op1"].source().isSame( s["b"]["op1"] ) )

	def testNameTracking( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.AddNode()

		s["b"]["i"] = Gaffer.BoxIn()
		s["b"]["i"]["name"].setValue( "test" )
		s["b"]["i"].setup( s["b"]["n"]["op1"] )
		promoted = s["b"]["i"].promotedPlug()

		self.assertEqual( s["b"]["i"]["name"].getValue(), "test" )
		self.assertEqual( promoted.getName(), s["b"]["i"]["name"].getValue() )

		with Gaffer.UndoContext( s ) :
			promoted.setName( "bob" )

		self.assertEqual( promoted.getName(), "bob" )
		self.assertEqual( s["b"]["i"]["name"].getValue(), "bob" )

		s.undo()

		self.assertEqual( s["b"]["i"]["name"].getValue(), "test" )
		self.assertEqual( promoted.getName(), s["b"]["i"]["name"].getValue() )

		with Gaffer.UndoContext( s ) :
			s["b"]["i"]["name"].setValue( "jim" )

		self.assertEqual( promoted.getName(), "jim" )
		self.assertEqual( s["b"]["i"]["name"].getValue(), "jim" )

		s.undo()

		self.assertEqual( s["b"]["i"]["name"].getValue(), "test" )
		self.assertEqual( promoted.getName(), s["b"]["i"]["name"].getValue() )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.AddNode()

		s["b"]["i"] = Gaffer.BoxIn()
		s["b"]["i"]["name"].setValue( "op1" )
		s["b"]["i"].setup( s["b"]["n"]["op1"] )
		s["b"]["n"]["op1"].setInput( s["b"]["i"]["out"] )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( "op1" in s2["b"] )
		self.assertTrue( s2["b"]["n"]["op1"].source().isSame( s2["b"]["op1"] ) )

	def testDeleteRemovesPromotedPlugs( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.AddNode()

		s["b"]["i"] = Gaffer.BoxIn()
		s["b"]["i"]["name"].setValue( "op1" )
		s["b"]["i"].setup( s["b"]["n"]["op1"] )
		s["b"]["n"]["op1"].setInput( s["b"]["i"]["out"] )

		self.assertTrue( "op1" in s["b"] )
		self.assertTrue( s["b"]["n"]["op1"].source().isSame( s["b"]["op1"] ) )

		with Gaffer.UndoContext( s ) :
			del s["b"]["i"]

		self.assertFalse( "op1" in s["b"] )
		self.assertTrue( s["b"]["n"]["op1"].getInput() is None )

		s.undo()

		self.assertTrue( "op1" in s["b"] )
		self.assertTrue( s["b"]["n"]["op1"].source().isSame( s["b"]["op1"] ) )

	def testDuplicateNames( self ) :

		b = Gaffer.Box()
		b["n1"] = GafferTest.AddNode()
		b["n2"] = GafferTest.AddNode()

		b["i1"] = Gaffer.BoxIn()
		b["i2"] = Gaffer.BoxIn()

		b["i1"].setup( b["n1"]["op1"] )
		b["i2"].setup( b["n2"]["op1"] )

		self.assertEqual( b["i1"].promotedPlug().getName(), "in" )
		self.assertEqual( b["i1"]["name"].getValue(), "in" )

		self.assertEqual( b["i2"].promotedPlug().getName(), "in1" )
		self.assertEqual( b["i2"]["name"].getValue(), "in1" )

		b["i2"]["name"].setValue( "in" )
		self.assertEqual( b["i2"].promotedPlug().getName(), "in1" )
		self.assertEqual( b["i2"]["name"].getValue(), "in1" )

	def testPaste( self ) :

		s = Gaffer.ScriptNode()
		s["b1"] = Gaffer.Box()
		s["b1"]["n"] = GafferTest.AddNode()

		s["b1"]["i"] = Gaffer.BoxIn()
		s["b1"]["i"]["name"].setValue( "test" )
		s["b1"]["i"].setup( s["b1"]["n"]["op1"] )
		s["b1"]["n"]["op1"].setInput( s["b1"]["i"]["out"] )

		s["b2"] = Gaffer.Box()
		s.execute(
			s.serialise( parent = s["b1"], filter = Gaffer.StandardSet( [ s["b1"]["n"], s["b1"]["i"] ] ) ),
			parent = s["b2"],
		)

		self.assertTrue( "test" in s["b2"] )
		self.assertTrue( s["b2"]["n"]["op1"].source().isSame( s["b2"]["test"] ) )

	def testMetadata( self ) :

		s = Gaffer.ScriptNode()
		s["b1"] = Gaffer.Box()
		s["b1"]["n"] = GafferTest.AddNode()

		Gaffer.Metadata.registerValue( s["b1"]["n"]["op1"], "test", "testValue" )
		Gaffer.Metadata.registerValue( s["b1"]["n"]["op1"], "layout:section", "sectionName" )

		s["b1"]["i"] = Gaffer.BoxIn()
		s["b1"]["i"].setup( s["b1"]["n"]["op1"] )

		self.assertEqual( Gaffer.Metadata.value( s["b1"]["i"].promotedPlug(), "test" ), "testValue" )
		self.assertEqual( Gaffer.Metadata.value( s["b1"]["i"].promotedPlug(), "layout:section" ), None )

		s["b2"] = Gaffer.Box()
		s.execute(
			s.serialise( parent = s["b1"], filter = Gaffer.StandardSet( [ s["b1"]["i"] ] ) ),
			parent = s["b2"],
		)

		self.assertEqual( Gaffer.Metadata.value( s["b2"]["i"].promotedPlug(), "test" ), "testValue" )
		self.assertEqual( Gaffer.Metadata.value( s["b2"]["i"].promotedPlug(), "layout:section" ), None )

	def testNoduleSectionMetadata( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.AddNode()

		Gaffer.Metadata.registerValue( s["b"]["n"]["op1"], "noduleLayout:section", "left" )

		s["b"]["i"] = Gaffer.BoxIn()
		s["b"]["i"].setup( s["b"]["n"]["op1"] )

		self.assertEqual( Gaffer.Metadata.value( s["b"]["i"].promotedPlug(), "noduleLayout:section" ), "left" )
		self.assertEqual( Gaffer.Metadata.value( s["b"]["i"].plug(), "noduleLayout:section" ), "right" )

	def testPromotedPlugRemovalDeletesBoxIn( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.AddNode()

		s["b"]["i"] = Gaffer.BoxIn()
		s["b"]["i"]["name"].setValue( "op1" )
		s["b"]["i"].setup( s["b"]["n"]["op1"] )
		s["b"]["n"]["op1"].setInput( s["b"]["i"]["out"] )

		def assertPreconditions() :

			self.assertTrue( "op1" in s["b"] )
			self.assertTrue( "i" in s["b"] )
			self.assertTrue( len( s["b"]["i"]["out"].outputs() ), 1 )
			self.assertTrue( s["b"]["n"]["op1"].source().isSame( s["b"]["op1"] ) )

		assertPreconditions()

		with Gaffer.UndoContext( s ) :
			del s["b"]["op1"]

		def assertPostconditions() :

			self.assertFalse( "op1" in s["b"] )
			self.assertFalse( "i" in s["b"] )
			self.assertTrue( s["b"]["n"]["op1"].getInput() is None )

		assertPostconditions()

		s.undo()

		assertPreconditions()

		s.redo()

		assertPostconditions()

	def testUndoCreation( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["a"] = GafferTest.AddNode()

		def assertPreconditions() :

			self.assertEqual( len( s["b"].children( Gaffer.Node ) ), 0 )
			self.assertEqual( len( s["b"].children( Gaffer.Plug ) ), 1 )
			self.assertEqual( len( s["a"]["sum"].outputs() ), 0 )

		assertPreconditions()

		with Gaffer.UndoContext( s ) :

			s["b"]["i"] = Gaffer.BoxIn()
			s["b"]["i"].setup( s["a"]["sum"] )
			s["b"]["i"].promotedPlug().setInput( s["a"]["sum"] )

		def assertPostconditions() :

			self.assertEqual( len( s["b"].children( Gaffer.Node ) ), 1 )
			self.assertEqual( len( s["b"].children( Gaffer.Plug ) ), 2 )
			self.assertTrue( isinstance( s["b"]["i"], Gaffer.BoxIn ) )
			self.assertTrue( s["b"]["i"]["out"].source().isSame( s["a"]["sum"] ) )

		assertPostconditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostconditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostconditions()

	def testPromote( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.AddNode()

		Gaffer.Metadata.registerValue( s["b"]["n"]["op2"], "nodule:type", "" )

		Gaffer.BoxIO.promote( s["b"]["n"]["op1"] )
		Gaffer.BoxIO.promote( s["b"]["n"]["op2"] )
		Gaffer.BoxIO.promote( s["b"]["n"]["sum"] )

		self.assertTrue( isinstance( s["b"]["n"]["op1"].getInput().node(), Gaffer.BoxIn ) )
		self.assertTrue( s["b"]["n"]["op1"].source().node().isSame( s["b"] ) )
		self.assertTrue( s["b"]["n"]["op2"].getInput().node().isSame( s["b"] ) )
		self.assertEqual( len( s["b"]["n"]["sum"].outputs() ), 1 )
		self.assertTrue( isinstance( s["b"]["n"]["sum"].outputs()[0].parent(), Gaffer.BoxOut ) )

	def testInsert( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.AddNode()

		op1Promoted = Gaffer.PlugAlgo.promote( s["b"]["n"]["op1"] )
		sumPromoted = Gaffer.PlugAlgo.promote( s["b"]["n"]["sum"] )
		s["b"]["n"]["op2"].setInput( s["b"]["n"]["op1"].getInput() )
		self.assertEqual( len( s["b"].children( Gaffer.BoxIO ) ), 0 )

		self.assertEqual( Gaffer.BoxIO.canInsert( s["b"] ), True )
		Gaffer.BoxIO.insert( s["b"] )

		self.assertEqual( len( s["b"].children( Gaffer.BoxIn ) ), 1 )
		self.assertEqual( len( s["b"].children( Gaffer.BoxOut ) ), 1 )

		self.assertTrue( isinstance( s["b"]["n"]["op1"].getInput().node(), Gaffer.BoxIn ) )
		self.assertTrue( isinstance( s["b"]["n"]["op2"].getInput().node(), Gaffer.BoxIn ) )
		self.assertTrue( s["b"]["n"]["op1"].source().isSame( op1Promoted ) )
		self.assertTrue( s["b"]["n"]["op2"].source().isSame( op1Promoted ) )

		self.assertEqual( len( s["b"]["n"]["sum"].outputs() ), 1 )
		self.assertTrue( isinstance( s["b"]["n"]["sum"].outputs()[0].parent(), Gaffer.BoxOut ) )
		self.assertTrue( sumPromoted.source().isSame( s["b"]["n"]["sum"] ) )

		self.assertEqual( Gaffer.BoxIO.canInsert( s["b"] ), False )

if __name__ == "__main__":
	unittest.main()
