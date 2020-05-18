##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

import inspect
import six
import unittest

import imath

import IECore

import Gaffer
import GafferTest

class SpreadsheetTest( GafferTest.TestCase ) :

	def testConstructor( self ) :

		self.assertEqual( Gaffer.Spreadsheet().getName(), "Spreadsheet" )

		s = Gaffer.Spreadsheet( "s" )
		self.assertEqual( s.getName(), "s" )

		# Check default row

		self.assertEqual( len( s["rows"] ), 1 )
		self.assertEqual( s["rows"][0].getName(), "default" )
		self.assertEqual( s["rows"][0]["name"].getValue(), "" )
		self.assertEqual( s["rows"][0]["enabled"].getValue(), True )
		self.assertIsInstance( s["rows"][0], Gaffer.Spreadsheet.RowPlug )

		# Check we have no columns

		self.assertEqual( len( s["rows"][0]["cells"] ), 0 )
		self.assertEqual( len( s["out"] ), 0 )

	def testEditColumnsAndRows( self ) :

		s = Gaffer.Spreadsheet()

		columnIndex = s["rows"].addColumn( Gaffer.IntPlug( "myInt" ) )
		self.assertEqual( columnIndex, 0 )
		self.assertEqual( len( s["rows"][0]["cells"] ), 1 )
		self.assertIsInstance( s["rows"][0]["cells"][0], Gaffer.Spreadsheet.CellPlug )
		self.assertEqual( s["rows"][0]["cells"][0].getName(), "myInt" )
		self.assertIsInstance( s["rows"][0]["cells"][0]["value"], Gaffer.IntPlug )
		self.assertEqual( s["rows"][0]["cells"][0]["enabled"].getValue(), True )
		self.assertEqual( s["rows"][0]["cells"][0]["value"].getValue(), 0 )
		self.assertEqual( len( s["out"] ), 1 )
		self.assertEqual( s["out"][0].getName(), "myInt" )
		self.assertIsInstance( s["out"][0], Gaffer.IntPlug )
		self.assertEqual( s["out"][0].direction(), Gaffer.Plug.Direction.Out )

		columnIndex = s["rows"].addColumn( Gaffer.FloatPlug( "myFloat", defaultValue = 1 ) )
		self.assertEqual( columnIndex, 1 )
		self.assertEqual( len( s["rows"][0]["cells"] ), 2 )
		self.assertIsInstance( s["rows"][0]["cells"][1], Gaffer.Spreadsheet.CellPlug )
		self.assertEqual( s["rows"][0]["cells"][1].getName(), "myFloat" )
		self.assertIsInstance( s["rows"][0]["cells"][1]["value"], Gaffer.FloatPlug )
		self.assertEqual( s["rows"][0]["cells"][1]["enabled"].getValue(), True )
		self.assertEqual( s["rows"][0]["cells"][1]["value"].getValue(), 1 )
		self.assertEqual( len( s["out"] ), 2 )
		self.assertEqual( s["out"][1].getName(), "myFloat" )
		self.assertIsInstance( s["out"][1], Gaffer.FloatPlug )
		self.assertEqual( s["out"][1].direction(), Gaffer.Plug.Direction.Out )

		row = s["rows"].addRow()
		self.assertIsInstance( row, Gaffer.Spreadsheet.RowPlug )
		self.assertEqual( row.parent(), s["rows"] )
		self.assertEqual( row.getName(), "row1" )
		self.assertEqual( len( row["cells"] ), 2 )
		self.assertEqual( row["cells"][0].getName(), "myInt" )
		self.assertEqual( row["cells"][1].getName(), "myFloat" )
		self.assertIsInstance( row["cells"][0], Gaffer.Spreadsheet.CellPlug )
		self.assertIsInstance( row["cells"][1], Gaffer.Spreadsheet.CellPlug )
		self.assertEqual( row["cells"][0]["enabled"].getValue(), True )
		self.assertEqual( row["cells"][0]["value"].getValue(), 0 )
		self.assertEqual( row["cells"][1]["enabled"].getValue(), True )
		self.assertEqual( row["cells"][1]["value"].getValue(), 1 )

		s["rows"].removeColumn( columnIndex )
		self.assertEqual( len( s["rows"][0]["cells"] ), 1 )
		self.assertEqual( s["rows"][0]["cells"][0].getName(), "myInt" )
		self.assertEqual( len( s["out"] ), 1 )
		self.assertEqual( s["out"][0].getName(), "myInt" )

	def testRemoveMiddleColumn( self ) :

		s = Gaffer.ScriptNode()

		s["s"] = Gaffer.Spreadsheet()
		s["s"]["rows"].addRow()

		c1 = s["s"]["rows"].addColumn( Gaffer.IntPlug( "c1" ) )
		c2 = s["s"]["rows"].addColumn( Gaffer.FloatPlug( "c2" ) )
		c3 = s["s"]["rows"].addColumn( Gaffer.StringPlug( "c3" ) )

		def assertPreconditions() :

			for row in s["s"]["rows"] :
				self.assertEqual( row["cells"].keys(), [ "c1", "c2", "c3" ] )
				self.assertIsInstance( row["cells"]["c1"]["value"], Gaffer.IntPlug )
				self.assertIsInstance( row["cells"]["c2"]["value"], Gaffer.FloatPlug )
				self.assertIsInstance( row["cells"]["c3"]["value"], Gaffer.StringPlug )

			self.assertEqual( s["s"]["out"].keys(), [ "c1", "c2", "c3" ] )
			self.assertIsInstance( s["s"]["out"]["c1"], Gaffer.IntPlug )
			self.assertIsInstance( s["s"]["out"]["c2"], Gaffer.FloatPlug )
			self.assertIsInstance( s["s"]["out"]["c3"], Gaffer.StringPlug )

		assertPreconditions()

		with Gaffer.UndoScope( s ) :
			s["s"]["rows"].removeColumn( c2 )

		def assertPostConditions() :

			for row in s["s"]["rows"] :
				self.assertEqual( row["cells"].keys(), [ "c1", "c3" ] )
				self.assertIsInstance( row["cells"]["c1"]["value"], Gaffer.IntPlug )
				self.assertIsInstance( row["cells"]["c3"]["value"], Gaffer.StringPlug )

			self.assertEqual( s["s"]["out"].keys(), [ "c1", "c3" ] )
			self.assertIsInstance( s["s"]["out"]["c1"], Gaffer.IntPlug )
			self.assertIsInstance( s["s"]["out"]["c3"], Gaffer.StringPlug )

		assertPostConditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostConditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostConditions()


	def testOutput( self ) :

		s = Gaffer.Spreadsheet()

		s["rows"].addColumn( Gaffer.IntPlug( "column1" ) )
		s["rows"].addColumn( Gaffer.IntPlug( "column2" ) )

		defaultRow = s["rows"].defaultRow()
		row1 = s["rows"].addRow()
		row1["name"].setValue( "row1" )
		row2 = s["rows"].addRow()
		row2["name"].setValue( "row2" )

		defaultRow["cells"]["column1"]["value"].setValue( 1 )
		defaultRow["cells"]["column2"]["value"].setValue( 2 )
		row1["cells"]["column1"]["value"].setValue( 3 )
		row1["cells"]["column2"]["value"].setValue( 4 )
		row2["cells"]["column1"]["value"].setValue( 5 )
		row2["cells"]["column2"]["value"].setValue( 6 )

		for selector in ( "", "woteva", "row1", "row2" ) :

			s["selector"].setValue( selector )
			expectedRow = s["rows"].getChild( selector ) or s["rows"].defaultRow()

			for out in s["out"] :

				s["enabled"].setValue( True )
				self.assertEqual( out.getValue(), expectedRow["cells"][out.getName()]["value"].getValue() )

				s["enabled"].setValue( False )
				self.assertEqual( out.getValue(), s["rows"].defaultRow()["cells"][out.getName()]["value"].getValue() )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()

		s["s"] = Gaffer.Spreadsheet()
		s["s"]["rows"].addColumn( Gaffer.IntPlug( "column1" ) )
		s["s"]["rows"].addColumn( Gaffer.IntPlug( "column2" ) )
		s["s"]["rows"].addRow()
		s["s"]["rows"].addRow()

		s["s"]["rows"][0]["cells"]["column1"]["value"].setValue( 10 )
		s["s"]["rows"][1]["cells"]["column1"]["value"].setValue( 20 )
		s["s"]["rows"][1]["cells"]["column1"]["enabled"].setValue( False )
		s["s"]["rows"][1]["name"].setValue( "rrr" )
		s["s"]["rows"][2]["name"].setValue( "zzz" )
		s["s"]["rows"][2]["cells"]["column1"]["value"].setValue( 30 )
		s["s"]["rows"][2]["cells"]["column2"]["value"].setValue( 40 )

		ss = s.serialise()
		self.assertEqual( ss.count( "addChild" ), 1 )
		self.assertEqual( ss.count( "addColumn" ), 2 )
		self.assertEqual( ss.count( "addRows" ), 1 )

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )

		self.assertEqual( s2["s"]["rows"].keys(), s["s"]["rows"].keys() )
		for r in s2["s"]["rows"].keys() :
			self.assertEqual( s2["s"]["rows"][r]["name"].getValue(), s["s"]["rows"][r]["name"].getValue() )
			self.assertEqual( s2["s"]["rows"][r]["enabled"].getValue(), s["s"]["rows"][r]["enabled"].getValue() )
			self.assertEqual( s2["s"]["rows"][r]["cells"].keys(), s["s"]["rows"][r]["cells"].keys() )
			for c in s2["s"]["rows"][r]["cells"].keys() :
				self.assertEqual( s2["s"]["rows"][r]["cells"][c]["enabled"].getValue(), s["s"]["rows"][r]["cells"][c]["enabled"].getValue() )
				self.assertEqual( s2["s"]["rows"][r]["cells"][c]["value"].getValue(), s["s"]["rows"][r]["cells"][c]["value"].getValue() )

	def testNestedPlugs( self ) :

		s = Gaffer.Spreadsheet()
		s["rows"].addColumn( Gaffer.TransformPlug( "transform" ) )
		r = s["rows"].addRow()

		self.assertEqual(
			s.correspondingInput( s["out"]["transform"]["translate"]["x"] ),
			s["rows"][0]["cells"]["transform"]["value"]["translate"]["x"]
		)

		r["name"].setValue( "n" )
		r["cells"]["transform"]["value"]["translate"].setValue( imath.V3f( 1, 2, 3 ) )

		self.assertEqual( s["out"]["transform"]["translate"].getValue(), imath.V3f( 0 ) )
		s["selector"].setValue( "n" )
		self.assertEqual( s["out"]["transform"]["translate"].getValue(), imath.V3f( 1, 2, 3 ) )

	def testDirtyPropagation( self ) :

		s = Gaffer.Spreadsheet()
		s["rows"].addColumn( Gaffer.V3fPlug( "v" ) )
		s["rows"].addColumn( Gaffer.FloatPlug( "f" ) )
		r = s["rows"].addRow()

		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )

		s["enabled"].setValue( False )
		self.assertTrue( set( s["out"].children() ).issubset( { x[0] for x in cs } ) )
		del cs[:]

		r["cells"]["v"]["value"]["x"].setValue( 2 )
		self.assertIn( s["out"]["v"]["x"], { x[0] for x in cs } )
		self.assertNotIn( s["out"]["v"]["z"], { x[0] for x in cs } )
		self.assertNotIn( s["out"]["f"], { x[0] for x in cs } )
		del cs[:]

		r["cells"]["v"]["enabled"].setValue( False )
		self.assertTrue( set( s["out"]["v"].children() ).issubset( { x[0] for x in cs } ) )
		self.assertNotIn( s["out"]["f"], { x[0] for x in cs } )
		del cs[:]

		s["rows"].addRow()
		self.assertTrue( set( s["out"].children() ).issubset( { x[0] for x in cs } ) )
		del cs[:]

		s["rows"].removeChild( s["rows"][-1] )
		self.assertTrue( set( s["out"].children() ).issubset( { x[0] for x in cs } ) )
		del cs[:]

	def testDisablingRows( self ) :

		s = Gaffer.Spreadsheet()
		s["selector"].setValue( "a" )
		s["rows"].addColumn( Gaffer.IntPlug( "i" ) )

		r = s["rows"].addRow()
		r["name"].setValue( "a" )
		r["cells"]["i"]["value"].setValue( 2 )
		self.assertEqual( s["out"]["i"].getValue(), 2 )

		r["enabled"].setValue( False )
		self.assertEqual( s["out"]["i"].getValue(), 0 )

	def testCorrespondingInput( self ) :

		s = Gaffer.Spreadsheet()
		s["rows"].addColumn( Gaffer.IntPlug( "column1" ) )
		s["rows"].addRows( 2 )

		self.assertEqual( s.correspondingInput( s["out"]["column1"] ), s["rows"].defaultRow()["cells"]["column1"]["value"] )
		self.assertEqual( s.correspondingInput( s["out"] ), None )

	def testPromotion( self ) :

		def assertCellEqual( cellPlug1, cellPlug2 ) :

			self.assertEqual( cellPlug1.getName(), cellPlug2.getName() )
			self.assertIsInstance( cellPlug1, Gaffer.Spreadsheet.CellPlug )
			self.assertIsInstance( cellPlug2, Gaffer.Spreadsheet.CellPlug )

			self.assertEqual( cellPlug1["enabled"].getValue(), cellPlug2["enabled"].getValue() )
			self.assertEqual( cellPlug1["value"].getValue(), cellPlug2["value"].getValue() )

		def assertRowEqual( rowPlug1, rowPlug2 ) :

			self.assertEqual( rowPlug1.getName(), rowPlug2.getName() )
			self.assertIsInstance( rowPlug1, Gaffer.Spreadsheet.RowPlug )
			self.assertIsInstance( rowPlug2, Gaffer.Spreadsheet.RowPlug )
			self.assertEqual( rowPlug1["name"].getValue(), rowPlug2["name"].getValue() )
			self.assertEqual( rowPlug1["enabled"].getValue(), rowPlug2["enabled"].getValue() )
			self.assertEqual( rowPlug1["cells"].keys(), rowPlug2["cells"].keys() )

			for k in rowPlug1["cells"].keys() :
				assertCellEqual( rowPlug1["cells"][k], rowPlug2["cells"][k] )

		def assertRowsEqual( rowsPlug1, rowsPlug2 ) :

			self.assertIsInstance( rowsPlug1, Gaffer.Spreadsheet.RowsPlug )
			self.assertIsInstance( rowsPlug2, Gaffer.Spreadsheet.RowsPlug )
			self.assertEqual( rowsPlug1.keys(), rowsPlug2.keys() )

			for k in rowsPlug1.keys() :
				assertRowEqual( rowsPlug1[k], rowsPlug2[k] )

		def assertOutputsValid( spreadsheet ) :

			self.assertEqual( spreadsheet["rows"].defaultRow()["cells"].keys(), spreadsheet["out"].keys() )
			for o in spreadsheet["out"] :
				self.assertEqual(
					spreadsheet.correspondingInput( o ),
					spreadsheet["rows"].defaultRow()["cells"][o.getName()]["value"]
				)

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()

		# Make a Spreadsheet with some existing cells
		# and promote the "rows" plug.

		s["b"]["s1"] = Gaffer.Spreadsheet()
		s["b"]["s1"]["rows"].addColumn( Gaffer.IntPlug( "i" ) )
		s["b"]["s1"]["rows"].addRow()["cells"][0]["value"].setValue( 10 )
		s["b"]["s1"]["rows"].addRow()["cells"][0]["value"].setValue( 20 )

		p1 = Gaffer.PlugAlgo.promote( s["b"]["s1"]["rows"] )
		assertRowsEqual( p1, s["b"]["s1"]["rows"] )
		assertOutputsValid( s["b"]["s1"] )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( s["b"]["s1"]["rows"] ) )

		# Promote the "rows" plug on an empty spreadsheet,
		# and add some cells.

		s["b"]["s2"] = Gaffer.Spreadsheet()
		p2 = Gaffer.PlugAlgo.promote( s["b"]["s2"]["rows"] )
		assertRowsEqual( p2, s["b"]["s2"]["rows"] )
		assertOutputsValid( s["b"]["s2"] )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( s["b"]["s2"]["rows"] ) )

		p2.addColumn( Gaffer.IntPlug( "i" ) )
		p2.addRow()["cells"][0]["value"].setValue( 10 )
		p2.addRow()["cells"][0]["value"].setValue( 20 )
		assertRowsEqual( p2, s["b"]["s2"]["rows"] )
		assertOutputsValid( s["b"]["s2"] )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( s["b"]["s2"]["rows"] ) )

		p2.addColumn( Gaffer.IntPlug( "j" ) )
		assertRowsEqual( p2, s["b"]["s2"]["rows"] )
		assertOutputsValid( s["b"]["s2"] )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( s["b"]["s2"]["rows"] ) )

		# Remove a column

		p2.removeColumn( 0 )
		assertRowsEqual( p2, s["b"]["s2"]["rows"] )
		assertOutputsValid( s["b"]["s2"] )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( s["b"]["s2"]["rows"] ) )

		# Serialise and reload, and check all is well

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		assertRowsEqual( s2["b"]["s1"]["rows"], s["b"]["s1"]["rows"] )
		assertRowsEqual( s2["b"]["s2"]["rows"], s["b"]["s2"]["rows"] )

		assertOutputsValid( s["b"]["s1"] )
		assertOutputsValid( s["b"]["s2"] )

	def testNoRedundantSetInputCalls( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()

		s["b"]["s"] = Gaffer.Spreadsheet()
		s["b"]["s"]["rows"].addColumn( Gaffer.IntPlug( "i" ) )
		s["b"]["s"]["rows"].addRows( 2 )

		Gaffer.PlugAlgo.promote( s["b"]["s"]["rows"] )

		# We should only need a single `setInput()` call
		# on `rows` to serialise all the connections
		# for the entire spreadsheet.

		ss = s.serialise()
		self.assertEqual( ss.count( "setInput" ), 1 )

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )

		self.assertEqual( s2["b"]["s"]["rows"].getInput(), s2["b"]["rows"] )

	def testActiveRowNames( self ) :

		s = Gaffer.Spreadsheet()
		for i in range( 1, 4 ) :
			s["rows"].addRow()["name"].setValue( str( i ) )

		self.assertEqual( s["activeRowNames"].getValue(), IECore.StringVectorData( [ "1", "2", "3" ] ) )

		s["rows"][1]["enabled"].setValue( False )
		self.assertEqual( s["activeRowNames"].getValue(), IECore.StringVectorData( [ "2", "3" ] ) )

		s["rows"][2]["name"].setValue( "two" )
		self.assertEqual( s["activeRowNames"].getValue(), IECore.StringVectorData( [ "two", "3" ] ) )

	def testAddColumnUsingDynamicPlug( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = Gaffer.Spreadsheet()
		s["s"]["rows"].addColumn( Gaffer.Color3fPlug( "c", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["s"]["rows"].addColumn( Gaffer.IntPlug( "i", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["s"]["rows"][0]["cells"].keys(), s["s"]["rows"][0]["cells"].keys() )
		self.assertEqual( s2["s"]["out"].keys(), s["s"]["out"].keys() )

		self.assertEqual( s2.serialise(), s.serialise() )

	def testActiveInput( self ) :

		s = Gaffer.Spreadsheet()
		s["rows"].addColumn( Gaffer.V3fPlug( "v" ) )
		s["rows"].addColumn( Gaffer.IntPlug( "i" ) )
		s["rows"].addRow()["name"].setValue( "a" )
		s["rows"].addRow()["name"].setValue( "b" )
		s["selector"].setValue( "${testSelector}" )

		with Gaffer.Context() as c :

			self.assertEqual( s.activeInPlug( s["out"]["v"] ), s["rows"].defaultRow()["cells"]["v"]["value"] )
			self.assertEqual( s.activeInPlug( s["out"]["v"]["x"] ), s["rows"].defaultRow()["cells"]["v"]["value"]["x"] )
			self.assertEqual( s.activeInPlug( s["out"]["i"] ), s["rows"].defaultRow()["cells"]["i"]["value"] )

			c["testSelector"] = "a"
			self.assertEqual( s.activeInPlug( s["out"]["v"] ), s["rows"][1]["cells"]["v"]["value"] )
			self.assertEqual( s.activeInPlug( s["out"]["v"]["x"] ), s["rows"][1]["cells"]["v"]["value"]["x"] )
			self.assertEqual( s.activeInPlug( s["out"]["i"] ), s["rows"][1]["cells"]["i"]["value"] )

			c["testSelector"] = "b"
			self.assertEqual( s.activeInPlug( s["out"]["v"] ), s["rows"][2]["cells"]["v"]["value"] )
			self.assertEqual( s.activeInPlug( s["out"]["v"]["x"] ), s["rows"][2]["cells"]["v"]["value"]["x"] )
			self.assertEqual( s.activeInPlug( s["out"]["i"] ), s["rows"][2]["cells"]["i"]["value"] )

			c["testSelector"] = "x"
			self.assertEqual( s.activeInPlug( s["out"]["v"] ), s["rows"].defaultRow()["cells"]["v"]["value"] )
			self.assertEqual( s.activeInPlug( s["out"]["v"]["x"] ), s["rows"].defaultRow()["cells"]["v"]["value"]["x"] )
			self.assertEqual( s.activeInPlug( s["out"]["i"] ), s["rows"].defaultRow()["cells"]["i"]["value"] )

	def testAddColumnWithName( self ) :

		s = Gaffer.Spreadsheet()
		i = s["rows"].addColumn( Gaffer.IntPlug( "x" ), name = "y" )
		self.assertEqual( s["rows"].defaultRow()["cells"][0].getName(), "y" )
		self.assertEqual( s["out"][0].getName(), "y" )

	def testAddColumnCopiesCurrentValue( self ) :

		p = Gaffer.IntPlug( defaultValue = 1, minValue = -10, maxValue = 10 )
		p.setValue( 3 )

		s = Gaffer.Spreadsheet()
		s["rows"].addRow()
		s["rows"].addColumn( p )

		for row in s["rows"] :
			self.assertEqual( row["cells"][0]["value"].defaultValue(), p.defaultValue() )
			self.assertEqual( row["cells"][0]["value"].minValue(), p.minValue() )
			self.assertEqual( row["cells"][0]["value"].maxValue(), p.maxValue() )
			self.assertEqual( row["cells"][0]["value"].getValue(), p.getValue() )

	def testRemoveRow( self ) :

		s = Gaffer.Spreadsheet()
		s2 = Gaffer.Spreadsheet( "other" )

		defaultRow = s["rows"].defaultRow()
		row1 = s["rows"].addRow()
		row2 = s["rows"].addRow()
		otherRow = s2["rows"].addRow()
		self.assertEqual( len( s["rows"] ), 3 )

		with six.assertRaisesRegex( self, RuntimeError, 'Cannot remove default row from "Spreadsheet.rows"' ) :
			s["rows"].removeRow( defaultRow )

		self.assertEqual( len( s["rows"] ), 3 )

		with six.assertRaisesRegex( self, RuntimeError, 'Row "other.rows.row1" is not a child of "Spreadsheet.rows"' ) :
			s["rows"].removeRow( otherRow )

		self.assertEqual( len( s["rows"] ), 3 )

		s["rows"].removeRow( row1 )
		self.assertEqual( s["rows"].children(), ( defaultRow, row2 ) )

	def testComputeDuringColumnAdditionandDeletion( self ) :

		script = Gaffer.ScriptNode()
		script["sheet"] = Gaffer.Spreadsheet()

		values = []
		exceptions = []
		def outputAddedOrRemoved( parent, child ) :

			try :
				values.append( child.getValue() )
			except Exception as e :
				exceptions.append( e )

		script["sheet"]["out"].childAddedSignal().connect( outputAddedOrRemoved, scoped = False )
		script["sheet"]["out"].childRemovedSignal().connect( outputAddedOrRemoved, scoped = False )

		with Gaffer.UndoScope( script ) :
			script["sheet"]["rows"].addColumn( Gaffer.StringPlug( "column1" ) )

		with Gaffer.UndoScope( script ) :
			script["sheet"]["rows"].removeColumn( 0 )

		script.undo()
		script.undo()
		script.redo()
		script.redo()

		self.assertEqual( len( values ), 6 )
		self.assertEqual( len( exceptions ), 0 )

	def testDeleteRowsAndSerialise( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = Gaffer.Spreadsheet()
		s["s"]["rows"].addRows( 3 )
		s["s"]["rows"].addColumn( Gaffer.IntPlug( "v" ) )

		for i in range( 0, 4 ) :
			s["s"]["rows"][i]["cells"]["v"]["value"].setValue( i )

		s["s"]["rows"].removeRow( s["s"]["rows"][1] )

		ss = Gaffer.ScriptNode()
		ss.execute( s.serialise() )

		for i, v in [
			( 0, 0 ),
			( 1, 2 ),
			( 2, 3 ),
		] :
			self.assertEqual( ss["s"]["rows"][i]["cells"]["v"]["value"].getValue(), v )

	def testWildcards( self ) :

		s = Gaffer.Spreadsheet()

		s["rows"].addColumn( Gaffer.IntPlug( "v" ) )

		row1 = s["rows"].addRow()
		row2 = s["rows"].addRow()

		row1["cells"]["v"]["value"].setValue( 1 )
		row2["cells"]["v"]["value"].setValue( 2 )

		s["selector"].setValue( "cat" )
		self.assertEqual( s["out"]["v"].getValue(), 0 )

		row1["name"].setValue( "cat" )
		self.assertEqual( s["out"]["v"].getValue(), 1 )

		row2["name"].setValue( "cat" )
		self.assertEqual( s["out"]["v"].getValue(), 1 )

		row1["name"].setValue( "ca*" )
		self.assertEqual( s["out"]["v"].getValue(), 1 )

		row1["name"].setValue( "dog" )
		self.assertEqual( s["out"]["v"].getValue(), 2 )

		row2["name"].setValue( "ca*" )
		self.assertEqual( s["out"]["v"].getValue(), 2 )

	def testSelectorVariablesRemovedFromRowNameContext( self ) :

		s = Gaffer.ScriptNode()

		s["s"] = Gaffer.Spreadsheet()
		s["s"]["rows"].addColumn( Gaffer.StringPlug( "v" ) )

		# `row` will only be selected if the context is not
		# cleaned up when evaluating the row name. If it is
		# selected then the spreadsheet will output "unexpectedVariable"
		# instead of the "" we expect.

		row = s["s"]["rows"].addRow()
		row["cells"]["v"]["value"].setValue( "unexpectedVariable" )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( inspect.cleandoc(
			"""
			a = context.get( "A" )
			b = context.get( "B" )
			parent["s"]["rows"]["row1"]["name"] = "*" if ( a or b ) else ""
			"""
		) )

		s["s"]["selector"].setValue( "${A}" )

		with Gaffer.Context() as c :
			c["A"] = "${B}"
			c["B"] = "boo"
			self.assertEqual( s["s"]["out"]["v"].getValue(), "" )
			self.assertEqual( s["s"]["out"]["v"].getValue(), "" )

	def testRowAccessor( self ) :

		s = Gaffer.ScriptNode()

		s["s"] = Gaffer.Spreadsheet()
		self.assertEqual( s["s"]["rows"].row( "" ), None )
		self.assertEqual( s["s"]["rows"].row( "x" ), None )
		self.assertEqual( s["s"]["rows"].row( "y" ), None )
		self.assertEqual( s["s"]["rows"].row( "z" ), None )

		with Gaffer.UndoScope( s ) :
			row1 = s["s"]["rows"].addRow()
			row1["name"].setValue( "x" )
			row2 = s["s"]["rows"].addRow()
			row2["name"].setValue( "y" )

		self.assertEqual( s["s"]["rows"].row( "" ), None )
		self.assertEqual( s["s"]["rows"].row( "x" ), row1 )
		self.assertEqual( s["s"]["rows"].row( "y" ), row2 )
		self.assertEqual( s["s"]["rows"].row( "z" ), None )

		with Gaffer.UndoScope( s ) :
			row2["name"].setValue( "z" )

		self.assertEqual( s["s"]["rows"].row( "" ), None )
		self.assertEqual( s["s"]["rows"].row( "x" ), row1 )
		self.assertEqual( s["s"]["rows"].row( "y" ), None )
		self.assertEqual( s["s"]["rows"].row( "z" ), row2 )

		with Gaffer.UndoScope( s ) :
			row3 = s["s"]["rows"].addRow()
			row3["name"].setValue( "y" )

		self.assertEqual( s["s"]["rows"].row( "" ), None )
		self.assertEqual( s["s"]["rows"].row( "x" ), row1 )
		self.assertEqual( s["s"]["rows"].row( "y" ), row3 )
		self.assertEqual( s["s"]["rows"].row( "z" ), row2 )

		s.undo()

		self.assertEqual( s["s"]["rows"].row( "" ), None )
		self.assertEqual( s["s"]["rows"].row( "x" ), row1 )
		self.assertEqual( s["s"]["rows"].row( "y" ), None )
		self.assertEqual( s["s"]["rows"].row( "z" ), row2 )

		s.undo()

		self.assertEqual( s["s"]["rows"].row( "" ), None )
		self.assertEqual( s["s"]["rows"].row( "x" ), row1 )
		self.assertEqual( s["s"]["rows"].row( "y" ), row2 )
		self.assertEqual( s["s"]["rows"].row( "z" ), None )

		s.undo()

		self.assertEqual( s["s"]["rows"].row( "" ), None )
		self.assertEqual( s["s"]["rows"].row( "x" ), None )
		self.assertEqual( s["s"]["rows"].row( "y" ), None )
		self.assertEqual( s["s"]["rows"].row( "z" ), None )

	def testRowAccessorWithEmptyName( self ) :

		s = Gaffer.Spreadsheet()
		self.assertEqual( s["rows"].row( "" ), None )
		r = s["rows"].addRow()
		self.assertEqual( s["rows"].row( "" ), r )
		r["name"].setValue( "n" )
		self.assertEqual( s["rows"].row( "" ), None )

	def testRowAccessorWithDuplicateNames( self ) :

		s = Gaffer.Spreadsheet()
		row1 = s["rows"].addRow()
		row2 = s["rows"].addRow()
		row3 = s["rows"].addRow()

		self.assertEqual( s["rows"].row( "" ), row1 )
		s["rows"].removeRow( row1 )
		self.assertEqual( s["rows"].row( "" ), row2 )
		s["rows"].removeRow( row2 )
		self.assertEqual( s["rows"].row( "" ), row3 )

	def testRowAccessorWithNoParent( self ) :

		rows = Gaffer.Spreadsheet.RowsPlug()
		row1 = rows.addRow()
		row2 = rows.addRow()
		row1["name"].setValue( "x" )
		row2["name"].setValue( "y" )

		self.assertEqual( rows.row( "x" ), row1 )
		self.assertEqual( rows.row( "y" ), row2 )

		row1["name"].setValue( "z" )
		row2["name"].setValue( "w" )

		self.assertEqual( rows.row( "x" ), None )
		self.assertEqual( rows.row( "y" ), None )
		self.assertEqual( rows.row( "z" ), row1 )
		self.assertEqual( rows.row( "w" ), row2 )

	def testRowAccessorWithPromotion( self ) :

		box = Gaffer.Box()
		box["s"] = Gaffer.Spreadsheet()
		rows = Gaffer.PlugAlgo.promote( box["s"]["rows"] )

		row1 = rows.addRow()
		row2 = rows.addRow()
		row1["name"].setValue( "x" )
		row2["name"].setValue( "y" )

		self.assertEqual( rows.row( "x" ), row1 )
		self.assertEqual( rows.row( "y" ), row2 )
		self.assertEqual( rows.row( "z" ), None )

		self.assertEqual( box["s"]["rows"].row( "x" ).source(), row1 )
		self.assertEqual( box["s"]["rows"].row( "y" ).source(), row2 )
		self.assertEqual( box["s"]["rows"].row( "z" ), None )

	def testRowAccessorWithComputedNames( self ) :

		n = GafferTest.StringInOutNode()
		n["in"].setValue( "x" )

		s = Gaffer.Spreadsheet()
		r = s["rows"].addRow()
		r["name"].setInput( n["out"] )

		self.assertEqual( s["rows"].row( "x" ), None )

	def testRowAccessorWithWildcards( self ) :

		s = Gaffer.Spreadsheet()
		r = s["rows"].addRow()
		r["name"].setValue( "abc*[0-9]" )
		self.assertEqual( s["rows"].row( "abc*[0-9]" ), r )

	def testAdoptedEnabledPlug( self ) :

		s = Gaffer.Spreadsheet()
		s["rows"].addColumn( Gaffer.NameValuePlug( "name", "defaultValue", defaultEnabled = True ), name = "c1", adoptEnabledPlug = True )
		row1 = s["rows"].addRow()
		row1["name"].setValue( "row1" )
		row2 = s["rows"].addRow()
		row2["name"].setValue( "row2" )

		for row in Gaffer.Spreadsheet.RowPlug.Range( s["rows"] ) :
			self.assertNotIn( "enabled", row["cells"]["c1"] )
			self.assertEqual( row["cells"]["c1"].enabledPlug(), row["cells"]["c1"]["value"]["enabled"] )
			self.assertEqual( row["cells"]["c1"].enabledPlug().getValue(), True )

		row1["cells"]["c1"]["value"]["value"].setValue( "row1Value" )
		row2["cells"]["c1"]["value"]["value"].setValue( "row2Value" )

		s["selector"].setValue( "row1" )
		self.assertEqual( s["out"]["c1"]["value"].getValue(), "row1Value" )
		self.assertEqual( s["out"]["c1"]["enabled"].getValue(), True )

		s["selector"].setValue( "row2" )
		self.assertEqual( s["out"]["c1"]["value"].getValue(), "row2Value" )
		self.assertEqual( s["out"]["c1"]["enabled"].getValue(), True )

		s["selector"].setValue( "notARow" )
		self.assertEqual( s["out"]["c1"]["value"].getValue(), "defaultValue" )
		self.assertEqual( s["out"]["c1"]["enabled"].getValue(), True )

		s["selector"].setValue( "row1" )
		row1["cells"]["c1"].enabledPlug().setValue( False )
		self.assertEqual( s["out"]["c1"]["value"].getValue(), "defaultValue" )
		self.assertEqual( s["out"]["c1"]["enabled"].getValue(), True )

		s["rows"]["default"]["cells"]["c1"].enabledPlug().setValue( False )
		self.assertEqual( s["out"]["c1"]["value"].getValue(), "defaultValue" )
		self.assertEqual( s["out"]["c1"]["enabled"].getValue(), False )

	def testAdoptedEnabledPlugChecks( self ) :

		s = Gaffer.Spreadsheet()
		with six.assertRaisesRegex( self, RuntimeError, 'Value plug has no "enabled" plug to adopt' ) :
			s["rows"].addColumn( Gaffer.IntPlug(), adoptEnabledPlug = True )

	def testAdoptedEnabledPlugSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = Gaffer.Spreadsheet()
		s["s"]["rows"].addColumn( Gaffer.NameValuePlug( "n", "v", defaultEnabled = True ), name = "c1", adoptEnabledPlug = True )
		s["s"]["rows"].addRow()

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		for row in Gaffer.Spreadsheet.RowPlug.Range( s2["s"]["rows"] ) :
			self.assertNotIn( "enabled", row["cells"]["c1"] )
			self.assertEqual( row["cells"]["c1"].enabledPlug(), row["cells"]["c1"]["value"]["enabled"] )
			self.assertEqual( row["cells"]["c1"].enabledPlug().getValue(), True )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testAddRowPerformance( self ) :

		s = Gaffer.Spreadsheet()
		for i in range( 0, 10000 ) :
			s["rows"].addRow()

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testAddRowsPerformance( self ) :

		s = Gaffer.Spreadsheet()
		s["rows"].addRows( 10000 )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testSavePerformance( self ) :

		s = Gaffer.ScriptNode()

		s["s"] = Gaffer.Spreadsheet()
		s["s"]["rows"].addColumn( Gaffer.IntPlug( "v" ) )
		for i in range( 0, 10000 ) :
			s["s"]["rows"].addRow()["cells"]["v"]["value"].setValue( i )

		with GafferTest.TestRunner.PerformanceScope() :
			s.serialise()

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testLoadPerformance( self ) :

		s = Gaffer.ScriptNode()

		s["s"] = Gaffer.Spreadsheet()
		s["s"]["rows"].addColumn( Gaffer.IntPlug( "v" ) )
		for i in range( 0, 10000 ) :
			s["s"]["rows"].addRow()["cells"]["v"]["value"].setValue( i )

		serialised = s.serialise()
		s = Gaffer.ScriptNode()
		with GafferTest.TestRunner.PerformanceScope() :
			s.execute( serialised )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testRowIndexPerformance( self ) :

		s = Gaffer.Spreadsheet()
		s["selector"].setValue( "${index}" )

		numRows = 10000

		s["rows"].addColumn( Gaffer.IntPlug( "v" ) )
		for i in range( 0, numRows ) :
			row = s["rows"].addRow()
			row["name"].setValue( str( i ) )
			row["cells"]["v"]["value"].setValue( i )

		c = Gaffer.Context()
		out = s["out"]["v"]
		with c :
			with GafferTest.TestRunner.PerformanceScope() :
				for i in range( 0, numRows ) :
					c["index"] = i
					self.assertEqual( out.getValue(), i )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testRowAccessorPerformance( self ) :

		s = Gaffer.Spreadsheet()
		rows = s["rows"]

		for i in range( 0, 10000 ) :
			name = "row{}".format( i )
			r = rows.addRow()
			r["name"].setValue( name )
			self.assertEqual( rows.row( name ), r )

if __name__ == "__main__":
	unittest.main()
