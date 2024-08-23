##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import pathlib
import imath

import IECore

import Gaffer
import GafferTest

class ArrayPlugTest( GafferTest.TestCase ) :

	def test( self ) :

		a = GafferTest.AddNode()
		n = GafferTest.ArrayPlugNode()

		self.assertTrue( "e1" in n["in"] )
		self.assertTrue( "e2" not in n["in"] )
		self.assertEqual( len( n["in"] ), 1 )
		self.assertTrue( n["in"]["e1"].isSame( n["in"][0] ) )

		n["in"][0].setInput( a["sum"] )

		self.assertEqual( len( n["in"] ), 2 )
		self.assertTrue( "e1" in n["in"] )
		self.assertTrue( "e2" in n["in"] )

		n["in"][0].setInput( None )
		self.assertTrue( "e1" in n["in"] )
		self.assertTrue( "e2" not in n["in"] )
		self.assertEqual( len( n["in"] ), 1 )

	def testConnectionGaps( self ) :

		a = GafferTest.AddNode()
		n = GafferTest.ArrayPlugNode()

		n["in"][0].setInput( a["sum"] )
		n["in"][1].setInput( a["sum"] )
		n["in"][2].setInput( a["sum"] )

		self.assertEqual( len( n["in"] ), 4 )

		self.assertEqual( n["in"]["e1"].getInput(), a["sum"] )
		self.assertEqual( n["in"]["e2"].getInput(), a["sum"] )
		self.assertEqual( n["in"]["e3"].getInput(), a["sum"] )
		self.assertIsNone( n["in"]["e4"].getInput() )

		n["in"][1].setInput( None )

		self.assertEqual( len( n["in"] ), 4 )

		self.assertEqual( n["in"]["e1"].getInput(), a["sum"] )
		self.assertIsNone( n["in"]["e2"].getInput() )
		self.assertEqual( n["in"]["e3"].getInput(), a["sum"] )
		self.assertIsNone( n["in"]["e4"].getInput() )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["a"] = GafferTest.AddNode()
		s["n"] = GafferTest.ArrayPlugNode()

		s["n"]["in"][0].setInput( s["a"]["sum"] )
		s["n"]["in"][1].setInput( s["a"]["sum"] )
		s["n"]["in"][2].setInput( s["a"]["sum"] )
		s["n"]["in"][1].setInput( None )

		self.assertEqual( len( s["n"]["in"] ), 4 )
		self.assertTrue( s["n"]["in"]["e1"].isSame( s["n"]["in"][0] ) )
		self.assertTrue( s["n"]["in"]["e2"].isSame( s["n"]["in"][1] ) )
		self.assertTrue( s["n"]["in"]["e3"].isSame( s["n"]["in"][2] ) )
		self.assertTrue( s["n"]["in"]["e4"].isSame( s["n"]["in"][3] ) )

		self.assertEqual( s["n"]["in"]["e1"].getInput(), s["a"]["sum"] )
		self.assertIsNone( s["n"]["in"]["e2"].getInput() )
		self.assertEqual( s["n"]["in"]["e3"].getInput(), s["a"]["sum"] )
		self.assertIsNone( s["n"]["in"]["e4"].getInput() )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( len( s2["n"]["in"] ), 4 )
		self.assertTrue( s2["n"]["in"]["e1"].isSame( s2["n"]["in"][0] ) )
		self.assertTrue( s2["n"]["in"]["e2"].isSame( s2["n"]["in"][1] ) )
		self.assertTrue( s2["n"]["in"]["e3"].isSame( s2["n"]["in"][2] ) )
		self.assertTrue( s2["n"]["in"]["e4"].isSame( s2["n"]["in"][3] ) )

		self.assertEqual( s2["n"]["in"]["e1"].getInput(), s2["a"]["sum"] )
		self.assertIsNone( s2["n"]["in"]["e2"].getInput() )
		self.assertEqual( s2["n"]["in"]["e3"].getInput(), s2["a"]["sum"] )
		self.assertIsNone( s2["n"]["in"]["e4"].getInput() )

	def testMaximumInputs( self ) :

		a = GafferTest.AddNode()
		n = GafferTest.ArrayPlugNode()

		# connect all inputs

		for i in range( 0, 6 ) :
			n["in"][i].setInput( a["sum"] )

		self.assertEqual( len( n["in"] ), 6 )
		for i in range( 0, 6 ) :
			self.assertTrue( n["in"][i].getInput().isSame( a["sum"] ) )

		# check that removing the one before the last
		# leaves the last in place.

		n["in"][4].setInput( None )
		self.assertEqual( len( n["in"] ), 6 )
		for i in range( 0, 6 ) :
			if i != 4 :
				self.assertTrue( n["in"][i].getInput().isSame( a["sum"] ) )
			else :
				self.assertTrue( n["in"][i].getInput() is None )

	def testMakeConnectionAndUndoAndRedo( self ) :

		s = Gaffer.ScriptNode()
		s["a"] = GafferTest.AddNode()
		s["n"] = GafferTest.ArrayPlugNode()

		with Gaffer.UndoScope( s ) :
			s["n"]["in"][0].setInput( s["a"]["sum"] )

		self.assertEqual( len( s["n"]["in"] ), 2 )
		self.assertTrue( s["n"]["in"][0].isSame( s["n"]["in"]["e1"] ) )
		self.assertTrue( s["n"]["in"][1].isSame( s["n"]["in"]["e2"] ) )

		s.undo()

		self.assertEqual( len( s["n"]["in"] ), 1 )
		self.assertTrue( s["n"]["in"][0].isSame( s["n"]["in"]["e1"] ) )

		s.redo()

		self.assertEqual( len( s["n"]["in"] ), 2 )
		self.assertTrue( s["n"]["in"][0].isSame( s["n"]["in"]["e1"] ) )
		self.assertTrue( s["n"]["in"][1].isSame( s["n"]["in"]["e2"] ) )

		s.undo()

		self.assertEqual( len( s["n"]["in"] ), 1 )
		self.assertTrue( s["n"]["in"][0].isSame( s["n"]["in"]["e1"] ) )
		self.assertTrue( "in" in s["n"] )
		self.assertFalse( "in1" in s["n"] )

	def testMinimumInputs( self ) :

		a = GafferTest.AddNode()
		n = Gaffer.Node()
		n["in"] = Gaffer.ArrayPlug( "in", elementPrototype = Gaffer.IntPlug( "e1" ), minSize=3 )

		self.assertEqual( len( n["in"] ), 3 )

		# connecting to the middle input shouldn't create
		# any new inputs, because there is still one free on the end
		n["in"]["e2"].setInput( a["sum"] )
		self.assertEqual( len( n["in"] ), 3 )

		# connecting to the last input should create a new
		# one - there should always be one free input on the
		# end (until the maximum is reached).
		n["in"]["e3"].setInput( a["sum"] )

		self.assertEqual( len( n["in"] ), 4 )

		n["in"]["e3"].setInput( None )

		self.assertEqual( len( n["in"] ), 3 )

	def testDeleteAndUndoAndRedo( self ) :

		s = Gaffer.ScriptNode()
		s["a"] = GafferTest.AddNode()
		s["n"] = GafferTest.ArrayPlugNode()

		s["n"]["in"]["e1"].setInput( s["a"]["sum"] )
		s["n"]["in"]["e2"].setInput( s["a"]["sum"] )
		s["n"]["in"]["e3"].setInput( s["a"]["sum"] )

		self.assertEqual( len( s["n"]["in"] ), 4 )
		self.assertTrue( s["n"]["in"]["e1"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"]["e2"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"]["e3"].getInput().isSame( s["a"]["sum"] ) )

		with Gaffer.UndoScope( s ) :
			s.deleteNodes( s, Gaffer.StandardSet( [ s["n"] ] ) )

		self.assertFalse( "n" in s )

		s.undo()

		self.assertEqual( len( s["n"]["in"] ), 4 )
		self.assertTrue( s["n"]["in"]["e1"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"]["e2"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"]["e3"].getInput().isSame( s["a"]["sum"] ) )

		s.redo()

		self.assertFalse( "n" in s )

		s.undo()

		self.assertEqual( len( s["n"]["in"] ), 4 )
		self.assertTrue( s["n"]["in"]["e1"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"]["e2"].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"]["e3"].getInput().isSame( s["a"]["sum"] ) )

	def testDeleteInputNodeAndUndoAndRedo( self ) :

		s = Gaffer.ScriptNode()
		s["a"] = GafferTest.AddNode()
		s["n"] = GafferTest.ArrayPlugNode()

		s["n"]["in"][0].setInput( s["a"]["sum"] )
		s["n"]["in"][1].setInput( s["a"]["sum"] )
		s["n"]["in"][2].setInput( s["a"]["sum"] )

		n = s["n"]

		self.assertEqual( len( s["n"]["in"] ), 4 )
		self.assertTrue( s["n"]["in"][0].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"][1].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"][2].getInput().isSame( s["a"]["sum"] ) )

		with Gaffer.UndoScope( s ) :
			s.deleteNodes( s, Gaffer.StandardSet( [ s["a"] ] ) )

		self.assertFalse( "a" in s )

		s.undo()

		self.assertEqual( len( s["n"]["in"] ), 4 )
		self.assertTrue( s["n"]["in"][0].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"][1].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"][2].getInput().isSame( s["a"]["sum"] ) )

		s.redo()

		self.assertFalse( "a" in s )

		s.undo()

		self.assertEqual( len( s["n"]["in"] ), 4 )
		self.assertTrue( s["n"]["in"][0].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"][1].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["in"][2].getInput().isSame( s["a"]["sum"] ) )

	def testFixedLengthDynamic( self ) :

		s = Gaffer.ScriptNode()

		s["a"] = GafferTest.AddNode()
		s["n"] = Gaffer.Node()
		s["n"]["a"] = Gaffer.ArrayPlug( "a", elementPrototype = Gaffer.IntPlug(), minSize = 4, maxSize = 4, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["a"][1].setInput( s["a"]["sum"] )
		s["n"]["a"][2].setInput( s["a"]["sum"] )

		self.assertEqual( s["n"]["a"].minSize(), 4 )
		self.assertEqual( s["n"]["a"].maxSize(), 4 )
		self.assertEqual( len( s["n"]["a"] ), 4 )
		self.assertTrue( s["n"]["a"][0].getInput() is None )
		self.assertTrue( s["n"]["a"][1].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["a"][1].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["n"]["a"][3].getInput() is None )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["n"]["a"].minSize(), 4 )
		self.assertEqual( s2["n"]["a"].maxSize(), 4 )
		self.assertEqual( len( s2["n"]["a"] ), 4 )
		self.assertTrue( s2["n"]["a"][0].getInput() is None )
		self.assertTrue( s2["n"]["a"][1].getInput().isSame( s2["a"]["sum"] ) )
		self.assertTrue( s2["n"]["a"][1].getInput().isSame( s2["a"]["sum"] ) )
		self.assertTrue( s2["n"]["a"][3].getInput() is None )

	def testPythonElement( self ) :

		class PythonElement( Gaffer.Plug ) :

			def __init__( self, name = "PythonElement", direction = Gaffer.Plug.Direction.In, flags = Gaffer.Plug.Flags.Default ) :

				Gaffer.Plug.__init__( self, name, direction, flags )

			def createCounterpart(  self, name, direction ) :

				return PythonElement( name, direction, self.getFlags() )

		n = Gaffer.Node()
		n["a"] = Gaffer.ArrayPlug( elementPrototype = PythonElement() )

		self.assertEqual( len( n["a"] ), 1 )
		self.assertTrue( isinstance( n["a"][0], PythonElement ) )

		p = PythonElement()
		n["a"][0].setInput( p )

		self.assertEqual( len( n["a"] ), 2 )
		self.assertTrue( isinstance( n["a"][1], PythonElement ) )

	def testTopLevelConnection( self ) :

		n = Gaffer.Node()

		n["a"] = Gaffer.ArrayPlug( elementPrototype = Gaffer.IntPlug() )
		n["b"] = Gaffer.ArrayPlug( elementPrototype = Gaffer.IntPlug() )
		n["b"].setInput( n["a"] )

		def assertInput( plug, input ) :

			self.assertEqual( len( plug ), len( input ) )
			for i in range( 0, len( plug ) ) :
				self.assertTrue( plug[i].getInput().isSame( input[i] ) )

		assertInput( n["b"], n["a"] )

		a = GafferTest.AddNode()

		n["a"][0].setInput( a["sum"] )
		self.assertEqual( len( n["a"] ), 2 )
		assertInput( n["b"], n["a"] )

		n["a"][1].setInput( a["sum"] )
		self.assertEqual( len( n["a"] ), 3 )
		assertInput( n["b"], n["a"] )

		n["a"][0].setInput( None )
		self.assertEqual( len( n["a"] ), 3 )
		assertInput( n["b"], n["a"] )

	def testArrayPlugCopiesColors( self ) :

		n = Gaffer.Node()

		n2 = Gaffer.Node()

		n2.addChild(Gaffer.IntPlug("test"))

		connectionColor = imath.Color3f( 0.1 , 0.2 , 0.3 )
		noodleColor = imath.Color3f( 0.4, 0.5 , 0.6 )

		element = Gaffer.IntPlug()
		Gaffer.Metadata.registerValue( element, "connectionGadget:color", connectionColor )
		Gaffer.Metadata.registerValue( element, "nodule:color", noodleColor )

		n["a"] = Gaffer.ArrayPlug( elementPrototype = element )
		n["a"][0].setInput(n2["test"])

		self.assertEqual( Gaffer.Metadata.value( n["a"][1], "connectionGadget:color" ), connectionColor )
		self.assertEqual( Gaffer.Metadata.value( n["a"][1], "nodule:color" ), noodleColor )

	def testOnlyOneChildType( self ) :

		p = Gaffer.ArrayPlug( elementPrototype = Gaffer.IntPlug() )
		self.assertTrue( p.acceptsChild( Gaffer.IntPlug() ) )
		self.assertFalse( p.acceptsChild( Gaffer.FloatPlug() ) )

	def testDenyInputFromNonArrayPlugs( self ) :

		a = Gaffer.ArrayPlug( elementPrototype = Gaffer.IntPlug() )
		p = Gaffer.V2iPlug()
		self.assertFalse( a.acceptsInput( p ) )

	def testPartialConnections( self ) :

		n = Gaffer.Node()
		n["p"] = Gaffer.ArrayPlug( elementPrototype = Gaffer.V3fPlug( "e" ) )
		self.assertEqual( len( n["p"] ), 1 )

		p = Gaffer.FloatPlug()
		n["p"][0]["x"].setInput( p )
		self.assertEqual( len( n["p"] ), 2 )

		n["p"][0]["y"].setInput( p )
		self.assertEqual( len( n["p"] ), 2 )

		n["p"][1]["y"].setInput( p )
		self.assertEqual( len( n["p"] ), 3 )

		n["p"][2]["z"].setInput( p )
		self.assertEqual( len( n["p"] ), 4 )

		n["p"][1]["y"].setInput( None )
		self.assertEqual( len( n["p"] ), 4 )

		n["p"][2]["z"].setInput( None )
		self.assertEqual( len( n["p"] ), 2 )

	def testResizeWhenInputsChange( self ) :

		s = Gaffer.ScriptNode()

		s["a"] = GafferTest.AddNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["p"] = Gaffer.ArrayPlug( elementPrototype = Gaffer.IntPlug(), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, resizeWhenInputsChange = False )
		self.assertEqual( s["n"]["user"]["p"].resizeWhenInputsChange(), False )

		self.assertEqual( len( s["n"]["user"]["p"] ), 1 )
		s["n"]["user"]["p"][0].setInput( s["a"]["sum"] )
		self.assertEqual( len( s["n"]["user"]["p"] ), 1 )
		s["n"]["user"]["p"][0].setInput( None )
		self.assertEqual( len( s["n"]["user"]["p"] ), 1 )

		p = s["n"]["user"]["p"].createCounterpart( "p", Gaffer.Plug.Direction.In )
		self.assertEqual( p.resizeWhenInputsChange(), False )

	def testNext( self ) :

		a = GafferTest.AddNode()

		n = Gaffer.Node()
		n["a1"] = Gaffer.ArrayPlug( elementPrototype = Gaffer.IntPlug() )
		n["a2"] = Gaffer.ArrayPlug( elementPrototype = Gaffer.IntPlug(), maxSize = 3, resizeWhenInputsChange = False )

		self.assertEqual( len( n["a1"] ), 1 )
		self.assertEqual( len( n["a2"] ), 1 )
		self.assertEqual( n["a1"].next(), n["a1"][0] )
		self.assertEqual( n["a2"].next(), n["a2"][0] )

		n["a1"][0].setInput( a["sum"] )
		n["a2"][0].setInput( a["sum"] )

		self.assertEqual( len( n["a1"] ), 2 )
		self.assertEqual( len( n["a2"] ), 1 )
		self.assertEqual( n["a1"].next(), n["a1"][1] )
		self.assertEqual( n["a2"].next(), n["a2"][1] )
		self.assertEqual( len( n["a2"] ), 2 )

		self.assertEqual( n["a1"].next(), n["a1"][1] )
		self.assertEqual( n["a2"].next(), n["a2"][1] )

		n["a2"].next().setInput( a["sum"] )
		n["a2"].next().setInput( a["sum"] )
		self.assertEqual( len( n["a2"] ), 3 )

		self.assertEqual( n["a2"].next(), None )

	def testNextWithZeroLengthArray( self ) :

		plug = Gaffer.ArrayPlug( elementPrototype = Gaffer.IntPlug(), minSize = 0 )
		element = plug.next()
		self.assertIsInstance( element, Gaffer.IntPlug )
		self.assertEqual( len( plug ), 1 )
		self.assertTrue( element.parent().isSame( plug ) )

	def testResize( self ) :

		p = Gaffer.ArrayPlug( elementPrototype = Gaffer.IntPlug(), minSize = 1, maxSize = 3, resizeWhenInputsChange = False )
		self.assertEqual( len( p ), p.minSize() )

		p.resize( 2 )
		self.assertEqual( len( p ), 2 )
		self.assertIsInstance( p[1], Gaffer.IntPlug )

		p.resize( 3 )
		self.assertEqual( len( p ), 3 )
		self.assertIsInstance( p[2], Gaffer.IntPlug )

		with self.assertRaises( RuntimeError ) :
			p.resize( p.minSize() - 1 )

		with self.assertRaises( RuntimeError ) :
			p.resize( p.maxSize() + 1 )

	def testRemoveInputDuringResize( self ) :

		node = Gaffer.Node()
		node["user"]["p"] = Gaffer.IntPlug()
		node["user"]["array"] = Gaffer.ArrayPlug( elementPrototype = Gaffer.IntPlug(), resizeWhenInputsChange = True )
		node["user"]["array"].resize( 4 )
		node["user"]["array"][2].setInput( node["user"]["p"] )

		node["user"]["array"].resize( 1 )
		self.assertEqual( len( node["user"]["array"] ), 1 )

	def testResizeOutputPlug( self ) :

		array = Gaffer.ArrayPlug( element = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out ), direction = Gaffer.Plug.Direction.Out )
		array.resize( 2 )

	def testSerialisationUsesIndices( self ) :

		s = Gaffer.ScriptNode()

		s["a"] = GafferTest.AddNode()
		s["n"] = GafferTest.ArrayPlugNode()
		s["n"]["in"][0].setInput( s["a"]["sum"] )
		s["n"]["in"][1].setInput( s["a"]["sum"] )

		ss = s.serialise()
		self.assertNotIn( "[\"" + s["n"]["in"][0].getName() + "\"]", ss )
		self.assertNotIn( "[\"" + s["n"]["in"][1].getName() + "\"]", ss )
		self.assertIn( "[0].setInput", ss )
		self.assertIn( "[1].setInput", ss )

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )

		self.assertEqual( s2["n"]["in"][0].getInput(), s2["a"]["sum"] )
		self.assertEqual( s2["n"]["in"][1].getInput(), s2["a"]["sum"] )

	def testCreateCounterpart( self ) :

		p1 = Gaffer.ArrayPlug( "p1", elementPrototype = Gaffer.IntPlug(), minSize = 2, maxSize = 4, resizeWhenInputsChange = False )
		p1.resize( 3 )

		p2 = p1.createCounterpart( "p2", Gaffer.Plug.Direction.In )
		self.assertEqual( len( p2 ), len( p1 ) )
		self.assertTrue( p1.elementPrototype( _copy = False ).isSame( p2.elementPrototype( _copy = False ) ) )

	def testZeroLength( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["p"] = Gaffer.ArrayPlug(
			elementPrototype = Gaffer.IntPlug( "e0" ), minSize = 0,
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
		)

		self.assertEqual( len( s["n"]["user"]["p"] ), 0 )

		s["n"]["user"]["p"].resize( 2 )
		self.assertEqual( len( s["n"]["user"]["p"] ), 2 )
		for element in s["n"]["user"]["p"] :
			self.assertIsInstance( element, Gaffer.IntPlug )

		s["n"]["user"]["p"].resize( 0 )
		self.assertEqual( len( s["n"]["user"]["p"] ), 0 )

		s["n"]["user"]["p"].resize( 10 )
		self.assertEqual( len( s["n"]["user"]["p"] ), 10 )
		for element in s["n"]["user"]["p"] :
			self.assertIsInstance( element, Gaffer.IntPlug )

	def testZeroLengthSerialisation( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["p"] = Gaffer.ArrayPlug(
			elementPrototype = Gaffer.IntPlug( "e0" ), minSize = 0,
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
		)

		self.assertEqual( len( s["n"]["user"]["p"] ), 0 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( len( s2["n"]["user"]["p"] ), 0 )

		s2["n"]["user"]["p"].resize( 2 )
		self.assertEqual( len( s2["n"]["user"]["p"] ), 2 )
		for element in s2["n"]["user"]["p"] :
			self.assertIsInstance( element, Gaffer.IntPlug )

	def testLoadFromVersion1_4( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue(
			pathlib.Path( __file__ ).parent / "scripts" / "arrayPlug-1.4.10.0.gfr"
		)
		s.load()

		self.assertEqual( len( s["n"]["user"]["p"] ), 4 )
		for element in s["n"]["user"]["p"] :
			self.assertIsInstance( element, Gaffer.IntPlug )

		self.assertEqual( s["n"]["user"]["p"][0].getValue(), 0 )
		self.assertEqual( s["n"]["user"]["p"][1].getValue(), 1 )
		self.assertTrue( s["n"]["user"]["p"][2].getInput().isSame( s["a"]["sum"] ) )
		self.assertEqual( s["n"]["user"]["p"][3].getValue(), 3 )
		self.assertIsInstance( s["n"]["user"]["p"].elementPrototype(), Gaffer.IntPlug )

		s["n"]["user"]["p"].resize( 1 )
		self.assertEqual( len( s["n"]["user"]["p"] ), 1 )
		self.assertIsInstance( s["n"]["user"]["p"][0], Gaffer.IntPlug )

		s["n"]["user"]["p"].resize( 2 )
		self.assertEqual( len( s["n"]["user"]["p"] ), 2 )
		for element in s["n"]["user"]["p"] :
			self.assertIsInstance( element, Gaffer.IntPlug )

if __name__ == "__main__":
	unittest.main()
