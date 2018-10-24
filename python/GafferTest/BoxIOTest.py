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
import os

import Gaffer
import GafferTest

class BoxIOTest( GafferTest.TestCase ) :

	def testInsertAndUndo( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n3"] = GafferTest.AddNode()

		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		s["n3"]["op1"].setInput( s["n2"]["sum"] )

		Gaffer.Metadata.registerValue( s["n1"]["sum"], "nodule:type", "GafferUI::StandardNodule" )
		Gaffer.Metadata.registerValue( s["n2"]["op1"], "nodule:type", "GafferUI::StandardNodule" )
		Gaffer.Metadata.registerValue( s["n2"]["sum"], "nodule:type", "GafferUI::StandardNodule" )
		Gaffer.Metadata.registerValue( s["n3"]["op1"], "nodule:type", "GafferUI::StandardNodule" )

		def assertPreconditions() :

			self.assertTrue( "n1" in s )
			self.assertTrue( "n2" in s )
			self.assertTrue( "n3" in s )

			self.assertTrue( s["n2"]["op1"].getInput().isSame( s["n1"]["sum"] ) )
			self.assertTrue( s["n3"]["op1"].getInput().isSame( s["n2"]["sum"] ) )

			self.assertEqual( s.children( Gaffer.Box ), () )

		assertPreconditions()

		with Gaffer.UndoScope( s ) :
			b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n2"] ] ) )
			Gaffer.BoxIO.insert( b )

		def assertPostconditions() :

			self.assertTrue( "n1" in s )
			self.assertFalse( "n2" in s )
			self.assertTrue( "n3" in s )

			self.assertEqual( set( s["Box"].keys() ), { "user", "n2", "BoxIn", "BoxOut", "op1", "sum" } )

			self.assertIsInstance( s["Box"]["n2"]["op1"].getInput().node(), Gaffer.BoxIn )
			self.assertTrue( s["Box"]["n2"]["op1"].source().isSame( s["n1"]["sum"] ) )

			self.assertEqual( len( s["Box"]["sum"].outputs() ), 1 )
			self.assertIsInstance( s["Box"]["n2"]["sum"].outputs()[0].node(), Gaffer.BoxOut )

			self.assertTrue( s["n3"]["op1"].source().isSame( s["Box"]["n2"]["sum"] ) )

		assertPostconditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostconditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostconditions()

	def testInsertWithNonSerialisableOutput( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["a"] = GafferTest.AddNode()
		s["b"]["a"]["sum"].setFlags( Gaffer.Plug.Flags.Serialisable, False )

		Gaffer.Metadata.registerValue( s["b"]["a"]["sum"], "nodule:type", "GafferUI::StandardNodule" )
		Gaffer.PlugAlgo.promote( s["b"]["a"]["sum"] )
		Gaffer.BoxIO.insert( s["b"] )

		self.assertIsInstance( s["b"]["sum"].getInput().node(), Gaffer.BoxOut )
		self.assertTrue( s["b"]["sum"].source().isSame( s["b"]["a"]["sum"] ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertIsInstance( s2["b"]["sum"].getInput().node(), Gaffer.BoxOut )
		self.assertTrue( s2["b"]["sum"].source().isSame( s2["b"]["a"]["sum"] ) )

	def testLoadOutsideBoxVersion0_52( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.dirname( __file__ ) + "/scripts/boxIOOutsideBoxVersion-0.52.0.0.gfr" )
		s.load()

		self.assertIsInstance( s["BoxIn"], Gaffer.BoxIn )
		self.assertIsInstance( s["BoxOut"], Gaffer.BoxOut )

	def testImportIntoBoxVersion0_52( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()

		s.executeFile( os.path.dirname( __file__ ) + "/scripts/boxIOOutsideBoxVersion-0.52.0.0.gfr", parent = s["b"] )
		self.assertIn( "in", s["b"] )
		self.assertIn( "out", s["b"] )

	def testCopyBareNodesIntoNewBox( self ) :

		s = Gaffer.ScriptNode()
		s["b1"] = Gaffer.Box()
		s["b1"]["i"] = Gaffer.BoxIn()
		s["b1"]["o"] = Gaffer.BoxOut()

		s["b2"] = Gaffer.Box()
		s.execute( s.serialise( parent = s["b1"] ), parent = s["b2"] )

		self.assertEqual( s["b2"].keys(), s["b1"].keys() )
		self.assertEqual( s["b2"]["i"].keys(), s["b1"]["i"].keys() )
		self.assertEqual( s["b2"]["o"].keys(), s["b1"]["o"].keys() )

if __name__ == "__main__":
	unittest.main()
