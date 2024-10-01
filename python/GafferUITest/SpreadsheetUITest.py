##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Cinesite VFX Ltd. nor the names of
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

import Gaffer
import GafferUI
import GafferUITest

import IECore

import itertools
import unittest

import GafferUI.SpreadsheetUI._ClipboardAlgo as _ClipboardAlgo

class SpreadsheetUITest( GafferUITest.TestCase ) :

	@staticmethod
	def __createSpreadsheet( numRows = 10 ) :

		s = Gaffer.Spreadsheet()

		rowsPlug = s["rows"]

		# N = row number, starting at 1
		# Rows named 'rowN'
		# Column 0 - string - 'sN'
		# Column 1 - int - N
		# Column 2 - int - 10N - even rows disabled
		# Column 3 - float - 100N
		# Column 4 - int - 1000N
		# Column 5 - compound plug
		# Column 6 - Non-adopted NameValuePlug
		# Column 7 - Adopted NameValuePlug

		compoundPlug = Gaffer.ValuePlug()
		compoundPlug["a"] = Gaffer.FloatPlug()
		compoundPlug["b"] = Gaffer.StringPlug()
		nameValuePlug = Gaffer.NameValuePlug( "nvp", IECore.FloatData( 0 ), True )

		for i, columnPlug in enumerate( (
			Gaffer.StringPlug(),     # 0
			Gaffer.IntPlug(),        # 1
			Gaffer.IntPlug(),        # 2
			Gaffer.FloatPlug(),      # 3
			Gaffer.IntPlug(),        # 4
			compoundPlug,            # 5
			nameValuePlug            # 6
		) ) :
			rowsPlug.addColumn( columnPlug, "column%d" % i, adoptEnabledPlug = False )

		rowsPlug.addColumn( nameValuePlug, "column7", adoptEnabledPlug = True )

		for i in range( 1, numRows + 1 ) :
			rowsPlug.addRow()["name"].setValue( "row%d" % i )
			rowsPlug[i]["cells"][0]["value"].setValue( "s%d" % ( i ) )
			rowsPlug[i]["cells"][2]["enabled"].setValue( i % 2 )
			for c in range( 1, 5 ) :
				rowsPlug[i]["cells"][c]["value"].setValue( i * pow( 10, c - 1 ) )
			rowsPlug[i]["cells"][5]["value"]["a"].setValue( i * 0.1 )
			rowsPlug[i]["cells"][5]["value"]["b"].setValue( "string %f" % ( i * 0.1 ) )
			rowsPlug[i]["cells"][6]["value"]["value"].setValue( i * 0.01 )

		return s

	# Provides a way to easily check the resulting value hierarchy under a cell plug.
	@staticmethod
	def __cellPlugHashes( cellPlugMatrix ) :

		return [ [ c.hash() for c in row ] for row in cellPlugMatrix ]

	def testCellPlugMatrix( self ) :

		s = self.__createSpreadsheet()

		self.assertEqual( _ClipboardAlgo.createPlugMatrixFromCells( [] ), [] )

		self.assertEqual(
			_ClipboardAlgo.createPlugMatrixFromCells( [ s["rows"][1]["cells"][2] ] ),
			[ [ s["rows"][1]["cells"][2] ] ]
		)

		columns = [ 2, 0, 3 ]
		rows = ( 0, 4, 2, 5 )

		plugs = []
		for r in rows :
			for c in columns :
				plugs.append( s["rows"][r]["cells"][c] )
				columns.append( columns.pop( 0 ) )

		expected = [ [ s["rows"][r]["cells"][c] for c in sorted(columns) ] for r in sorted(rows) ]

		self.assertEqual( _ClipboardAlgo.createPlugMatrixFromCells( plugs ), expected )

	def testCanCopyPlugs( self ) :

		s = self.__createSpreadsheet()

		self.assertFalse( _ClipboardAlgo.canCopyPlugs( [] ) )
		self.assertFalse( _ClipboardAlgo.canCopyPlugs( [ [] ] ) )

		# Single cell

		self.assertTrue( _ClipboardAlgo.canCopyPlugs( [
			[ s["rows"][1]["cells"][0] ]
		] ) )

		# Two rows (contigious)

		self.assertTrue( _ClipboardAlgo.canCopyPlugs( [
			[ s["rows"][1]["cells"][0] ],
			[ s["rows"][2]["cells"][0] ]
		] ) )

		# Three rows (non-contiguous)

		self.assertTrue( _ClipboardAlgo.canCopyPlugs( [
			[ s["rows"][1]["cells"][0] ],
			[ s["rows"][3]["cells"][0] ],
			[ s["rows"][5]["cells"][0] ]
		] ) )

		# Two columns (contiguous)

		self.assertTrue( _ClipboardAlgo.canCopyPlugs( [
			[ s["rows"][1]["cells"][0], s["rows"][1]["cells"][1] ]
		] ) )

		# Three columns (non-contiguous)

		self.assertTrue( _ClipboardAlgo.canCopyPlugs( [
			[ s["rows"][1]["cells"][0], s["rows"][1]["cells"][1], s["rows"][1]["cells"][3] ]
		] ) )

		# Three rows, two columns (non-contiguous)

		self.assertTrue( _ClipboardAlgo.canCopyPlugs( [
			[ s["rows"][1]["cells"][0], s["rows"][1]["cells"][2] ],
			[ s["rows"][3]["cells"][0], s["rows"][3]["cells"][2] ],
			[ s["rows"][4]["cells"][0], s["rows"][4]["cells"][2] ],
		] ) )

		# Non-contiguous but compatible column types

		self.assertTrue( _ClipboardAlgo.canCopyPlugs( [
			[ s["rows"][1]["cells"][1], s["rows"][1]["cells"][4] ],
			[ s["rows"][4]["cells"][2], s["rows"][4]["cells"][4] ],
		] ) )

		# Mixed column types

		self.assertFalse( _ClipboardAlgo.canCopyPlugs( [
			[ s["rows"][1]["cells"][0], s["rows"][1]["cells"][1] ],
			[ s["rows"][4]["cells"][1], s["rows"][4]["cells"][2] ],
		] ) )

		# Inconsistent column counts

		self.assertFalse( _ClipboardAlgo.canCopyPlugs( [
			[ s["rows"][1]["cells"][0], s["rows"][1]["cells"][1] ],
			[ s["rows"][4]["cells"][1] ]
		] ) )

	def testIsValueMatrix( self ) :

		O = IECore.ObjectVector
		C = IECore.CompoundData
		B = IECore.BoolData
		I = IECore.IntData
		F = IECore.FloatData

		for d in (
			"cat",
			1,
			None,
			[],
			[ 1, 2, 3 ],
			[ [ 1 ] ],
			[ [ 1, 4 ] ],
			# Incorrect cell data type
			O([
				O([ O([ I( 1 ), I( 2 ) ]) ])
			]),
			# Mixed row value types
			O([
				O([ C({ "enabled" : B( True ), "value" : I( 2 ) }) ]),
				O([ C({ "enabled" : B( True ), "value" : F( 2 ) }) ])
			]),
			# Mixed row keys
			O([
				O([ C({ "enabled" : B( True ), "value" : I( 2 ) }) ]),
				O([ C({ "znabled" : B( True ), "value" : I( 2 ) }) ])
			]),
		) :
			self.assertFalse( _ClipboardAlgo.isValueMatrix( d ) )

		for d in (
			# one row, one column
			O([ O([ C({ "enabled" : B( True ), "value" : I( 1 ) }) ]) ]),
			# one row, two columns
			O([ O([ C({ "enabled" : B( True ), "value" : I( 2 ) }), C({ "enabled" : B( True ), "value" : F( 2 ) }) ]) ]),
			# two rows, one column
			O([
				O([ C({ "enabled" : B( True ), "value" : I( 3 ) }) ]),
				O([ C({ "enabled" : B( True ), "value" : I( 3 ) }) ])
			]),
			# two rows, two columns
			O([
				O([ C({ "enabled" : B( True ), "value" : I( 4 ) }), C({ "enabled" : B( False ), "value" : F( 4 ) }) ]),
				O([ C({ "enabled" : B( True ), "value" : I( 4 ) }), C({ "enabled" : B( True ),  "value" : F( 4 ) }) ])
			]),
		) :
			self.assertTrue( _ClipboardAlgo.isValueMatrix( d ) )

	def testValueMatrix( self ) :

		s = self.__createSpreadsheet()

		plugs = [
			[
				s["rows"][1]["cells"][0], s["rows"][1]["cells"][1], s["rows"][1]["cells"][2],
				s["rows"][1]["cells"][3], s["rows"][1]["cells"][4]
			],
			[
				s["rows"][2]["cells"][0], s["rows"][2]["cells"][1], s["rows"][2]["cells"][2],
				s["rows"][2]["cells"][3], s["rows"][2]["cells"][4]
			]
		]

		expected = IECore.ObjectVector( [
			IECore.ObjectVector( [
				IECore.CompoundData( { "enabled" : c["enabled"].getValue(), "value" : c["value"].getValue() } ) for c in r
			] ) for r in plugs
		] )

		data = _ClipboardAlgo.valueMatrix( plugs )

		self.assertTrue( _ClipboardAlgo.isValueMatrix( data ) )
		self.assertEqual( data, expected )

		# Test inerleaved compatible (int) columns

		plugs = [ [ s["rows"][r]["cells"][ ( r % 2 ) + 1 ] ] for r in ( 1, 2 ) ]

		expected = IECore.ObjectVector( [
			IECore.ObjectVector( [
				IECore.CompoundData( {
					"enabled" : s["rows"][r]["cells"][ ( r % 2 ) + 1 ]["enabled"].getValue(),
					"value" : s["rows"][r]["cells"][ ( r % 2 ) + 1 ]["value"].getValue()
				} )
			] ) for r in ( 1, 2 )
		] )

		self.assertEqual( _ClipboardAlgo.valueMatrix( plugs ), expected )

	def testCanPasteCells( self ) :

		s = self.__createSpreadsheet()

		# Single Column

		plugs = [ [ s["rows"][r]["cells"][1] ] for r in ( 1, 2 ) ]
		data = _ClipboardAlgo.valueMatrix( plugs )

		# Bad data

		self.assertFalse( _ClipboardAlgo.canPasteCells( "I'm a duck", plugs ) )

		self.assertTrue( _ClipboardAlgo.canPasteCells( data, plugs ) )

		#   - fewer rows

		self.assertTrue( _ClipboardAlgo.canPasteCells( data, [ [ s["rows"][4]["cells"][1] ] ] ) )

		#   - row wrap with more rows

		self.assertTrue( _ClipboardAlgo.canPasteCells( data, [ [ s["rows"][r]["cells"][1] ] for r in range( 1, 5 ) ] ) )

		#   - different column, same type

		self.assertTrue( _ClipboardAlgo.canPasteCells( data, [ [ s["rows"][r]["cells"][2] ] for r in range( 1, 5 ) ] ) )

		#   - different columns, same type

		self.assertTrue( _ClipboardAlgo.canPasteCells( data, [ [ s["rows"][r]["cells"][ ( r % 2 ) + 1 ] ] for r in range( 1, 5 ) ] ) )

		#   - invalid column type

		self.assertFalse( _ClipboardAlgo.canPasteCells( data, [ [ s["rows"][r]["cells"][0] ] for r in range( 1, 5 ) ] ) )

		#   - different columns, one invalid type

		self.assertFalse( _ClipboardAlgo.canPasteCells( data, [ [ s["rows"][r]["cells"][ ( r % 2 ) ] ] for r in range( 1, 5 ) ] ) )

		#   - column wrap with multiple valid target columns

		self.assertTrue( _ClipboardAlgo.canPasteCells( data, [ [ s["rows"][r]["cells"][c] for c in ( 1, 2, 4 ) ] for r in range( 1, 5 ) ] ) )

		# Multiple Columns

		plugs = [ [ s["rows"][r]["cells"][c] for c in range( 3 ) ] for r in ( 1, 2 ) ]
		data = _ClipboardAlgo.valueMatrix( plugs )

		self.assertTrue( _ClipboardAlgo.canPasteCells( data, plugs ) )

		#   - fewer rows

		self.assertTrue(
			_ClipboardAlgo.canPasteCells( data, [ [ s["rows"][4]["cells"][c] for c in range( 3 ) ] ] )
		)

		#   - row wrap with more rows

		self.assertTrue(
			_ClipboardAlgo.canPasteCells( data, [ [ s["rows"][r]["cells"][c] for c in range( 3 ) ] for r in range( 1, 3 ) ] )
		)

		#  - invalid column types

		self.assertFalse(
			_ClipboardAlgo.canPasteCells( data, [ [ s["rows"][r]["cells"][c] for c in range( 3 + 1 ) ] for r in range( 1, 3 ) ] )
		)

		#  - valid column subset

		self.assertTrue(
			_ClipboardAlgo.canPasteCells( data, [ [ s["rows"][r]["cells"][0] ] for r in range( 1, 3 ) ] )
		)

		#  - column wrap with additional colunms

		plugs = [ [ s["rows"][r]["cells"][c] for c in ( 1, 2 ) ] for r in ( 1, 2 ) ]
		data = _ClipboardAlgo.valueMatrix( plugs )

		self.assertTrue(
			_ClipboardAlgo.canPasteCells( data, [ [ s["rows"][r]["cells"][c] for c in ( 1, 2, 4 ) ] for r in range( 1, 2 ) ] )
		)

	def testPasteCells( self ) :

		# Single column

		s = self.__createSpreadsheet()

		sourceCells = [ [ s["rows"][r]["cells"][1] ] for r in range( 1, 5 ) ]
		sourceHashes = self.__cellPlugHashes( sourceCells )

		data = _ClipboardAlgo.valueMatrix( sourceCells )

		#   - matching dest

		destCells = [ [ s["rows"][r]["cells"][2] ] for r in range( 1, 5 ) ]
		self.assertNotEqual( self.__cellPlugHashes( destCells ), sourceHashes )

		_ClipboardAlgo.pasteCells( data, destCells, 0 )
		self.assertEqual( self.__cellPlugHashes( destCells ), sourceHashes )

		#  - column wrap

		s = self.__createSpreadsheet()

		destCells = [ [ s["rows"][r]["cells"][c] for c in ( 2, 4 ) ] for r in range( 1, 5 ) ]
		expected = [ [ r[0], r[0] ] for r in sourceHashes ]
		self.assertNotEqual( self.__cellPlugHashes( destCells ), expected )

		_ClipboardAlgo.pasteCells( data, destCells, 0 )
		self.assertEqual( self.__cellPlugHashes( destCells ), expected )

		# - row wrap

		s = self.__createSpreadsheet()

		destCells = [ [ s["rows"][r]["cells"][2] ] for r in range( 1, 9 ) ]
		expected = sourceHashes[:] + sourceHashes[:4]
		self.assertNotEqual( self.__cellPlugHashes( destCells ), expected )

		_ClipboardAlgo.pasteCells( data, destCells, 0 )
		self.assertEqual( self.__cellPlugHashes( destCells ), expected )

		# - interleaved paste across 2 matching column types

		s = self.__createSpreadsheet()

		destCells = [ [ s["rows"][r]["cells"][ ( r % 2 ) + 1 ] ] for r in range( 1, 5 ) ]
		self.assertNotEqual( self.__cellPlugHashes( destCells ), sourceHashes )

		_ClipboardAlgo.pasteCells( data, destCells, 0 )
		self.assertEqual( self.__cellPlugHashes( destCells ), sourceHashes )

		# Multi-column + row wrap

		s = self.__createSpreadsheet()

		sourceCells = [ [ s["rows"][r]["cells"][c] for c in range( len(s["rows"][0]["cells"]) ) ] for r in range( 1, 3 ) ]
		sourceHashes = self.__cellPlugHashes( sourceCells )

		data = _ClipboardAlgo.valueMatrix( sourceCells )

		destCells = [ [ s["rows"][r]["cells"][c] for c in range( len(s["rows"][0]["cells"]) ) ] for r in range( 5, 9 ) ]
		self.assertNotEqual( self.__cellPlugHashes( destCells ), sourceHashes )

		_ClipboardAlgo.pasteCells( data, destCells, 0 )

		expected = sourceHashes[:] + sourceHashes[:]
		self.assertEqual( self.__cellPlugHashes( destCells ), expected )

	def testCanPasteRows( self ) :

		s = self.__createSpreadsheet()

		subsetValueMatrix = _ClipboardAlgo.valueMatrix( [ [ s["rows"][r]["cells"][c] for c in range(2) ] for r in range( 2, 4 ) ] )
		self.assertFalse( _ClipboardAlgo.canPasteRows( subsetValueMatrix, s["rows"] ) )

		rowData = _ClipboardAlgo.copyRows( [ s["rows"][r] for r in ( 2, 3 ) ] )

		self.assertTrue( _ClipboardAlgo.canPasteRows( rowData, s["rows"] ) )

		s2 = Gaffer.Spreadsheet()
		s2["rows"].addColumn( Gaffer.IntPlug(), "intColumn", False )

		self.assertFalse( _ClipboardAlgo.canPasteRows( rowData, s2["rows"] ) )

	def testPasteRows( self ) :

		s = self.__createSpreadsheet( numRows = 5 )

		sourceRows = [ [ s["rows"][r] ] for r in range( 2, 4 ) ]
		sourceHashes = self.__cellPlugHashes( sourceRows )
		rowData = _ClipboardAlgo.valueMatrix( sourceRows )

		self.assertEqual( len( s["rows"].children() ), 6 )
		existingHashes = self.__cellPlugHashes( [ [ s["rows"][r] ] for r in range( 6 ) ] )

		_ClipboardAlgo.pasteRows( rowData, s["rows"] )

		self.assertEqual( len( s["rows"].children() ), 6 + 2 )
		newHashes = self.__cellPlugHashes( [ [ s["rows"][r] ] for r in range( 6 + 2 ) ] )

		self.assertEqual( newHashes, existingHashes + sourceHashes )

	def testPastedRowsMatchByColumn( self ) :

		s1 = Gaffer.Spreadsheet()
		s1["rows"].addColumn( Gaffer.StringPlug( defaultValue = "s1String" ), "string" )
		s1["rows"].addColumn( Gaffer.IntPlug( defaultValue = 1 ), "int" )
		s1["rows"].addColumn( Gaffer.FloatPlug( defaultValue = 3.0 ), "float" )
		s1["rows"].addRow()

		s2 = Gaffer.Spreadsheet()
		s2["rows"].addColumn( Gaffer.FloatPlug( defaultValue = 5.0 ), "float" )
		s2["rows"].addColumn( Gaffer.StringPlug( defaultValue = "s2String" ), "string" )
		s2["rows"].addColumn( Gaffer.IntPlug( defaultValue = 6 ), "int" )
		s2["rows"].addColumn( Gaffer.IntPlug( defaultValue = 7 ), "anotherInt" )

		# Fewer columns -> more columns

		data = _ClipboardAlgo.copyRows( [ s1["rows"][1] ] )
		self.assertTrue( _ClipboardAlgo.canPasteRows( data, s2["rows"] ) )
		_ClipboardAlgo.pasteRows( data, s2["rows"] )

		s1r1 = s1["rows"][1]["cells"]
		s2d = s2["rows"].defaultRow()["cells"]
		expectedHashes = self.__cellPlugHashes( [ [ s1r1["float"], s1r1["string"], s1r1["int"], s2d["anotherInt"] ] ] )
		self.assertEqual( self.__cellPlugHashes( [ s2["rows"][1]["cells"].children() ] ), expectedHashes )

		# More columns -> fewer columns

		s2["rows"].addRow()

		data = _ClipboardAlgo.copyRows( [ s2["rows"][2] ] )
		self.assertTrue( _ClipboardAlgo.canPasteRows( data, s1["rows"] ) )
		_ClipboardAlgo.pasteRows( data, s1["rows"] )

		s2r2 = s2["rows"][2]["cells"]
		expectedHashes = self.__cellPlugHashes( [ [ s2r2["string"], s2r2["int"], s2r2["float"] ] ] )
		self.assertEqual( self.__cellPlugHashes( [ s1["rows"][2]["cells"].children() ] ), expectedHashes )

		# Conflicting match

		s1["rows"].addColumn( Gaffer.StringPlug(), "mismatched" )
		s2["rows"].addColumn( Gaffer.IntPlug(), "mismatched" )

		data = _ClipboardAlgo.copyRows( [ s1["rows"][2] ] )
		self.assertFalse( _ClipboardAlgo.canPasteRows( data, s2["rows"] ) )

		# No Matches

		s3 =  Gaffer.Spreadsheet()
		s3["rows"].addColumn( Gaffer.IntPlug(), "a" )
		s3["rows"].addRow()

		s4 =  Gaffer.Spreadsheet()
		s4["rows"].addColumn( Gaffer.IntPlug(), "b" )
		s4["rows"].addRow()

		data = _ClipboardAlgo.valueMatrix( [ [ s3["rows"][1] ] ] )
		self.assertFalse( _ClipboardAlgo.canPasteRows( data, s4["rows"] ) )

		# Test match with value coercion

		s4["rows"].addColumn( Gaffer.FloatPlug( defaultValue = 5.0 ), "a" )
		self.assertTrue( _ClipboardAlgo.canPasteRows( data, s4["rows"] ) )
		_ClipboardAlgo.pasteRows( data, s4["rows"] )
		self.assertEqual( s4["rows"][2]["cells"]["a"]["value"].getValue(), 0.0 )

	def testClipboardRespectsReadOnly( self ) :

		s = Gaffer.Spreadsheet()
		s["rows"].addColumn( Gaffer.V3fPlug() )
		s["rows"].addColumn( Gaffer.NameValuePlug( "v", Gaffer.V3fPlug(), True ) )
		s["rows"].addRows( 8 )

		targets = (
			s["rows"][2]["cells"][1]["value"]["value"][1],
			s["rows"][2]["cells"][1]["value"]["enabled"],
			s["rows"][2]["cells"][1]["value"],
			s["rows"][3]["cells"][1],
			s["rows"],
			s
		)

		# We shouldn't consider the NVP's name ever, so this can stay locked
		Gaffer.MetadataAlgo.setReadOnly( s["rows"][2]["cells"][1]["value"]["name"], True )

		for t in targets :
			Gaffer.MetadataAlgo.setReadOnly( t, True )

		sourceCells = [ [ s["rows"][r]["cells"][0] ] for r in range( 7 ) ]
		data = _ClipboardAlgo.valueMatrix( sourceCells )
		destCells = [ [ s["rows"][r]["cells"][1] ] for r in range( 7 ) ]

		for t in reversed( targets ) :
			self.assertFalse( _ClipboardAlgo.canPasteCells( data, destCells ) )
			Gaffer.MetadataAlgo.setReadOnly( t, False )

		self.assertTrue( _ClipboardAlgo.canPasteCells( data, destCells ) )

	def testPasteCellsSetsKeyframe( self ) :

		s = self.__createSpreadsheet()
		script = Gaffer.ScriptNode()
		script["s"] = s

		targetPlug = s["rows"][2]["cells"][1]["value"]
		curve = Gaffer.Animation.acquire( targetPlug )
		curve.addKey( Gaffer.Animation.Key( 0, 1001 ) )
		self.assertFalse( curve.hasKey( 1002 ) )

		data = _ClipboardAlgo.valueMatrix( [ [ s["rows"][5]["cells"][1]["value"] ] ] )
		_ClipboardAlgo.pasteCells( data, [ [ targetPlug ] ], 1002 )

		self.assertTrue( curve.hasKey( 1002 ) )
		key = curve.getKey( 1002 )
		self.assertEqual( key.getValue(), 5 )

	def testNameValuePlugs( self ) :

		s = Gaffer.Spreadsheet()
		s["rows"].addColumn( Gaffer.NameValuePlug( "a", Gaffer.IntPlug( defaultValue = 1 ) ) )
		s["rows"].addColumn( Gaffer.NameValuePlug( "b", Gaffer.IntPlug( defaultValue = 2 ) ) )
		row = s["rows"].addRow()

		def assertNVPEqual( plug, name, enabled, value ) :
			self.assertEqual( plug["name"].getValue(), name )
			self.assertEqual( plug["value"].getValue(), value )
			if enabled is not None :
				self.assertEqual( plug["enabled"].getValue(), enabled )

		assertNVPEqual( row["cells"][0]["value"], "a", None, 1 )
		assertNVPEqual( row["cells"][1]["value"], "b", None, 2 )

		data = _ClipboardAlgo.valueMatrix( [ [ row["cells"][1] ] ] )
		_ClipboardAlgo.pasteCells( data, [ [ row["cells"][0] ] ], 0 )

		assertNVPEqual( row["cells"][0]["value"], "a", None, 2 )
		assertNVPEqual( row["cells"][1]["value"], "b", None, 2 )

		s["rows"].addColumn( Gaffer.NameValuePlug( "c", Gaffer.IntPlug( defaultValue = 3 ), True ) )
		s["rows"].addColumn( Gaffer.NameValuePlug( "d", Gaffer.IntPlug( defaultValue = 4 ), False ) )

		assertNVPEqual( row["cells"][2]["value"], "c", True, 3 )
		assertNVPEqual( row["cells"][3]["value"], "d", False, 4 )

		data = _ClipboardAlgo.valueMatrix( [ [ row["cells"][3] ] ] )
		_ClipboardAlgo.pasteCells( data, [ [ row["cells"][2] ] ], 0 )

		assertNVPEqual( row["cells"][2]["value"], "c", False, 4 )
		assertNVPEqual( row["cells"][3]["value"], "d", False, 4 )

		# Test cross-pasting between plugs with/without enabled plugs

		data = _ClipboardAlgo.valueMatrix( [ [ row["cells"][3] ] ] )
		_ClipboardAlgo.pasteCells( data, [ [ row["cells"][0] ] ], 0 )

		assertNVPEqual( row["cells"][0]["value"], "a", None, 4 )

		data = _ClipboardAlgo.valueMatrix( [ [ row["cells"][1] ] ] )
		_ClipboardAlgo.pasteCells( data, [ [ row["cells"][2] ] ], 0 )

		assertNVPEqual( row["cells"][2]["value"], "c", False, 2 )

		# Test cross-pasting between ValuePlugs and NameValuePlugs

		s["rows"].addColumn( Gaffer.IntPlug( defaultValue = 5 ) )

		data = _ClipboardAlgo.valueMatrix( [ [ row["cells"][4] ] ] )
		_ClipboardAlgo.pasteCells( data, [ [ row["cells"][1], row["cells"][2] ] ], 0 )

		assertNVPEqual( row["cells"][1]["value"], "b", None, 5 )
		assertNVPEqual( row["cells"][2]["value"], "c", False, 5 )

		row["cells"][2]["value"]["value"].setValue( 3 )

		data = _ClipboardAlgo.valueMatrix( [ [ row["cells"][2] ] ] )
		_ClipboardAlgo.pasteCells( data, [ [ row["cells"][4] ] ], 0 )

		self.assertEqual( row["cells"][4]["value"].getValue(), 3 )

	def testCellEnabled( self ) :

		# Test that cell enabled states are correctly remapped when
		# cross-pasting between simple, adopted and unadopted columns.

		s = Gaffer.Spreadsheet()
		s["rows"].addColumn( Gaffer.IntPlug(), "valueOnly" )
		s["rows"].addColumn( Gaffer.NameValuePlug( "a", Gaffer.IntPlug( defaultValue = 1 ), True ), "adopted", adoptEnabledPlug = True )
		s["rows"].addColumn( Gaffer.NameValuePlug( "u", Gaffer.IntPlug( defaultValue = 2 ), True ), "unadopted", adoptEnabledPlug = False )
		row = s["rows"].addRow()

		def resetEnabledState() :
			for cell in row["cells"].children() :
				cell.enabledPlug().setValue( True )
			row["cells"]["unadopted"]["value"]["enabled"].setValue( True )

		def assertPostCondition( valueOnly, adopted, unadopted, unadoptedEnabled ) :
			self.assertEqual( row["cells"]["valueOnly"].enabledPlug().getValue(), valueOnly )
			self.assertEqual( row["cells"]["adopted"].enabledPlug().getValue(), adopted )
			self.assertEqual( row["cells"]["unadopted"].enabledPlug().getValue(), unadopted )
			self.assertEqual( row["cells"]["unadopted"]["value"]["enabled"].getValue(), unadoptedEnabled )

		self.assertEqual( row["cells"]["valueOnly"].enabledPlug(), row["cells"]["valueOnly"]["enabled"] )
		self.assertEqual( row["cells"]["adopted"].enabledPlug(), row["cells"]["adopted"]["value"]["enabled"] )
		self.assertEqual( row["cells"]["unadopted"].enabledPlug(), row["cells"]["unadopted"]["enabled"] )
		self.assertEqual( row["cells"]["unadopted"]["value"]["enabled"].getValue(), True )

		for source, targets, expected in (
			( "valueOnly", ( "adopted", "unadopted" ),   ( False, False, False, True ) ),
			( "adopted",   ( "valueOnly", "unadopted" ), ( False, False, False, False ) ),
			( "unadopted", ( "valueOnly", "adopted" ),   ( False, False, False, True ) )
		) :

			resetEnabledState()
			row["cells"][ source ].enabledPlug().setValue( False )

			data = _ClipboardAlgo.valueMatrix( [ [ row["cells"][ source ] ] ] )
			_ClipboardAlgo.pasteCells( data, [ [ row["cells"][ t ] for t in targets ] ], 0 )

			assertPostCondition( *expected )

	def testIntToFloatConversion( self ) :

		s = Gaffer.Spreadsheet()
		s["rows"].addColumn( Gaffer.FloatPlug( defaultValue = 1.0 ) )
		s["rows"].addColumn( Gaffer.IntPlug( defaultValue = 2 ) )
		row = s["rows"].addRow()

		self.assertEqual( s["rows"][1]["cells"][0]["value"].getValue(), 1.0 )
		self.assertEqual( s["rows"][1]["cells"][1]["value"].getValue(), 2 )

		data = _ClipboardAlgo.valueMatrix( [ [ row["cells"][1] ] ] )
		_ClipboardAlgo.pasteCells( data, [ [ row["cells"][0] ] ], 0 )

		self.assertEqual( s["rows"][1]["cells"][0]["value"].getValue(), 2.0 )
		self.assertEqual( s["rows"][1]["cells"][1]["value"].getValue(), 2 )

	def testStringConversion( self ) :

		s = Gaffer.Spreadsheet()
		s["rows"].addColumn( Gaffer.StringPlug() )
		s["rows"].addColumn( Gaffer.StringVectorDataPlug( "v", defaultValue = IECore.StringVectorData() ) )
		row = s["rows"].addRow()

		bothColumns = [ s["rows"][1]["cells"].children() ]

		data = IECore.StringData( "string" )
		self.assertTrue( _ClipboardAlgo.canPasteCells( data, bothColumns ) )
		_ClipboardAlgo.pasteCells( data, bothColumns, 0 )
		self.assertEqual( s["rows"][1]["cells"][0]["value"].getValue(), "string" )
		self.assertEqual( s["rows"][1]["cells"][1]["value"].getValue(), IECore.StringVectorData( [ "string" ] ) )

		for data in (
			IECore.StringVectorData( [] ),
			IECore.StringVectorData( [ "one" ] )
		) :
			self.assertTrue( _ClipboardAlgo.canPasteCells( data, bothColumns ) )
			_ClipboardAlgo.pasteCells( data, bothColumns, 0 )
			self.assertEqual( s["rows"][1]["cells"][0]["value"].getValue(), data[0] if data else "" )
			self.assertEqual( s["rows"][1]["cells"][1]["value"].getValue(), data )

		data = IECore.StringVectorData( [ "one", "two" ] )
		self.assertTrue( _ClipboardAlgo.canPasteCells( data, bothColumns ) )
		_ClipboardAlgo.pasteCells( data, bothColumns, 0 )
		self.assertEqual( s["rows"][1]["cells"][0]["value"].getValue(), " ".join( data ) )
		self.assertEqual( s["rows"][1]["cells"][1]["value"].getValue(), data )

	def testPasteBasicValues( self ) :

		s = Gaffer.Spreadsheet()
		s["rows"].addColumn( Gaffer.IntPlug( defaultValue = 1 ) )
		s["rows"].addColumn( Gaffer.NameValuePlug( "i", Gaffer.IntPlug( defaultValue = 2 ) ) )
		row = s["rows"].addRow()

		data = IECore.IntData( 3 )

		plugMatrix = [ s["rows"][1]["cells"].children() ]
		self.assertTrue( _ClipboardAlgo.canPasteCells( data, plugMatrix ) )

		_ClipboardAlgo.pasteCells( data, plugMatrix, 0 )

		self.assertEqual( row["cells"][0]["value"].getValue(), 3 )
		self.assertEqual( row["cells"][1]["value"]["value"].getValue(), 3 )

	def testCantPasteWithConnections( self ) :

		s = Gaffer.Spreadsheet()
		s["rows"].addColumn( Gaffer.IntPlug() )
		s["rows"].addRow()

		self.assertTrue( _ClipboardAlgo.canPasteCells( IECore.IntData( 1 ), [ s["rows"][1]["cells"].children() ] ) )

		p = Gaffer.IntPlug()
		s["rows"][1]["cells"][0]["value"].setInput( p )

		self.assertFalse( _ClipboardAlgo.canPasteCells( IECore.IntData( 1 ), [ s["rows"][1]["cells"].children() ] ) )

	def testColumnOrder( self ) :

		s = Gaffer.Spreadsheet()

		rowsPlug = s["rows"]

		def visualOrder():
			widget = GafferUI.SpreadsheetUI._RowsPlugValueWidget( rowsPlug )
			qtHeader = widget._RowsPlugValueWidget__defaultTable._qtWidget().horizontalHeader()
			return [ qtHeader.visualIndex( i ) for i in range( len( rowsPlug[0]["cells"] ) ) ]

		for i in range( 4 ):
			rowsPlug.addColumn( Gaffer.IntPlug(), "column%d" % i, adoptEnabledPlug = False )

		self.assertEqual( visualOrder(), [ 0, 1, 2, 3 ] )

		# Test setting a column index on some columns
		Gaffer.Metadata.registerValue( rowsPlug[0]["cells"][2], 'spreadsheet:columnIndex', 1 )
		Gaffer.Metadata.registerValue( rowsPlug[0]["cells"][3], 'spreadsheet:columnIndex', 0 )

		self.assertEqual( visualOrder(), [ 2, 3, 1, 0 ] )

		# Test setting a column index on all columns
		Gaffer.Metadata.registerValue( rowsPlug[0]["cells"][0], 'spreadsheet:columnIndex', 3 )
		Gaffer.Metadata.registerValue( rowsPlug[0]["cells"][1], 'spreadsheet:columnIndex', 2 )

		self.assertEqual( visualOrder(), [ 3, 2, 1, 0 ] )

		# We should be able to use the order of the columnIndex values even if they are larger
		# than the number of columns
		Gaffer.Metadata.registerValue( rowsPlug[0]["cells"][0], 'spreadsheet:columnIndex', 1002 )
		Gaffer.Metadata.registerValue( rowsPlug[0]["cells"][1], 'spreadsheet:columnIndex', 1001 )
		Gaffer.Metadata.registerValue( rowsPlug[0]["cells"][2], 'spreadsheet:columnIndex', 1003 )
		Gaffer.Metadata.registerValue( rowsPlug[0]["cells"][3], 'spreadsheet:columnIndex', 1000 )

		self.assertEqual( visualOrder(), [ 2, 1, 3, 0 ] )

		# Test deleting a column while the UI exists
		Gaffer.Metadata.registerValue( rowsPlug[0]["cells"][0], 'spreadsheet:columnIndex', 1 )
		Gaffer.Metadata.registerValue( rowsPlug[0]["cells"][1], 'spreadsheet:columnIndex', 2 )
		Gaffer.Metadata.registerValue( rowsPlug[0]["cells"][2], 'spreadsheet:columnIndex', 3 )
		Gaffer.Metadata.registerValue( rowsPlug[0]["cells"][3], 'spreadsheet:columnIndex', 0 )

		widget = GafferUI.SpreadsheetUI._RowsPlugValueWidget( rowsPlug )
		qtHeader = widget._RowsPlugValueWidget__defaultTable._qtWidget().horizontalHeader()
		self.assertEqual( [ qtHeader.visualIndex( i ) for i in range( len( rowsPlug[0]["cells"] ) ) ], [ 1, 2, 3, 0 ] )

		del rowsPlug[0]["cells"][2]
		self.assertEqual( [ qtHeader.visualIndex( i ) for i in range( len( rowsPlug[0]["cells"] ) ) ], [ 1, 2, 0 ] )

	def testColumnOrderPermutations( self ) :

		for l in range( 2, 7 ):
			s = Gaffer.Spreadsheet()

			rowsPlug = s["rows"]

			for i in range( l ):
				rowsPlug.addColumn( Gaffer.IntPlug(), "column%d" % i, adoptEnabledPlug = False )

			# Test every possible order of columns
			for p in itertools.permutations( range( l ) ):

				for i in range( l ):
					Gaffer.Metadata.registerValue( rowsPlug[0]["cells"][i], 'spreadsheet:columnIndex', p[i] )

				widget = GafferUI.SpreadsheetUI._RowsPlugValueWidget( rowsPlug )
				qtHeader = widget._RowsPlugValueWidget__defaultTable._qtWidget().horizontalHeader()

				self.assertEqual( [ qtHeader.visualIndex( i ) for i in range( l ) ], list( p ) )

	def testRowMetadata( self ) :

		s = Gaffer.Spreadsheet()
		s["rows"].addColumn( Gaffer.IntPlug( "a" ) )
		s["rows"].addColumn( Gaffer.IntPlug( "b" ) )
		s["rows"].addRow()

		Gaffer.Metadata.registerValue( s["rows"].defaultRow()["name"], "plugValueWidget:type", "Test" )
		Gaffer.Metadata.registerValue( s["rows"].defaultRow()["cells"]["a"]["value"], "plugValueWidget:type", "Test2" )
		Gaffer.Metadata.registerValue( s["rows"].defaultRow()["cells"]["b"]["value"], "plugValueWidget:type", "Test3" )

		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["name"], "plugValueWidget:type" ), "Test" )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["a"]["value"], "plugValueWidget:type" ), "Test2" )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["b"]["value"], "plugValueWidget:type" ), "Test3" )

	def testRowMetadataNotPromotedRedundantly( self ) :

		Gaffer.Metadata.registerValue( Gaffer.IntPlug, "plugAlgoTest:b", "testValueB" )
		self.addCleanup( Gaffer.Metadata.deregisterValue, Gaffer.IntPlug, "plugAlgoTest:b" )

		# Metadata is automatically inherited from the default row to the other rows
		# so that we can avoid lots of redundant registrations.

		box = Gaffer.Box()
		box["spreadsheet"] = Gaffer.Spreadsheet()
		box["spreadsheet"]["rows"].addColumn( Gaffer.StringPlug( "column1" ) )
		box["spreadsheet"]["rows"].addRows( 1 )
		Gaffer.Metadata.registerValue(
			box["spreadsheet"]["rows"][0]["cells"]["column1"]["value"],
			"plugValueWidget:type", "GafferUI.MultiLineStringPlugValueWidget"
		)
		self.assertEqual( Gaffer.Metadata.value( box["spreadsheet"]["rows"][0]["cells"]["column1"]["value"], "plugValueWidget:type" ), "GafferUI.MultiLineStringPlugValueWidget" )
		self.assertEqual( Gaffer.Metadata.value( box["spreadsheet"]["rows"][1]["cells"]["column1"]["value"], "plugValueWidget:type" ), "GafferUI.MultiLineStringPlugValueWidget" )

		# So we want to avoid promoting that metadata redundantly for the non-default rows.

		promoted = Gaffer.PlugAlgo.promote( box["spreadsheet"]["rows"] )
		self.assertEqual( Gaffer.Metadata.value( promoted[0]["cells"]["column1"]["value"], "plugValueWidget:type" ), "GafferUI.MultiLineStringPlugValueWidget" )
		self.assertEqual( Gaffer.Metadata.value( promoted[0]["cells"]["column1"]["value"], "plugValueWidget:type", Gaffer.Metadata.RegistrationTypes.Instance ), "GafferUI.MultiLineStringPlugValueWidget" )
		self.assertEqual( Gaffer.Metadata.value( promoted[1]["cells"]["column1"]["value"], "plugValueWidget:type" ), "GafferUI.MultiLineStringPlugValueWidget" )
		self.assertIsNone( Gaffer.Metadata.value( promoted[1]["cells"]["column1"]["value"], "plugValueWidget:type", Gaffer.Metadata.RegistrationTypes.Instance ) )

		# And we don't want any other metadata to be copied for the non-default rows.

		for plug in Gaffer.Plug.RecursiveRange( promoted[1] ) :
			self.assertEqual( Gaffer.Metadata.registeredValues( plug, Gaffer.Metadata.RegistrationTypes.Instance ), [] )

	def testMetadataAlgoRemovesNonDefaultRowMetadata( self ) :

		spreadsheet = Gaffer.Spreadsheet()
		spreadsheet["rows"].addColumn( Gaffer.StringPlug( "column1" ) )
		spreadsheet["rows"].addRows( 1 )

		# Create Spreadsheet where non-default row has its own metadata that conflicts with the values
		# that should be mirrored from the default row. It used to be possible for the user to get into
		# this situation because we redundantly promoted metadata onto the non-default rows.

		Gaffer.Metadata.registerValue( spreadsheet["rows"][0]["cells"][0], "spreadsheet:columnWidth", 100 )
		Gaffer.Metadata.registerValue( spreadsheet["rows"][1]["cells"][0], "spreadsheet:columnWidth", 200 )
		Gaffer.Metadata.registerValue( spreadsheet["rows"][0]["cells"][0], "spreadsheet:columnLabel", "Label 1" )
		Gaffer.Metadata.registerValue( spreadsheet["rows"][1]["cells"][0], "spreadsheet:columnLabel", "Label 2" )

		# Even though the non-default-row values are different to the default row ones, we still want
		# `deregisterRedundantValues()` to clean them up, because having different column widths/labels
		# on different rows is logically impossible.

		Gaffer.MetadataAlgo.deregisterRedundantValues( spreadsheet["rows"] )

		for row in spreadsheet["rows"] :
			self.assertEqual( Gaffer.Metadata.value( row["cells"][0], "spreadsheet:columnWidth" ), 100 )
			self.assertEqual( Gaffer.Metadata.value( row["cells"][0], "spreadsheet:columnLabel" ), "Label 1" )

		self.assertEqual(
			Gaffer.Metadata.registeredValues( spreadsheet["rows"][1]["cells"][0], Gaffer.Metadata.RegistrationTypes.Instance ),
			[]
		)

	def testMetadataForwarding( self ) :

		s = Gaffer.Spreadsheet()
		s["rows"].addColumn( Gaffer.StringPlug( "a" ) )
		s["rows"].addColumn( Gaffer.StringPlug( "b" ) )
		s["rows"].addRows( 1 )

		n = Gaffer.Node()
		n.addChild( Gaffer.StringPlug( "a" ) )

		n["a"].setInput( s["out"]["a"] )

		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["a"]["value"], "plugValueWidget:type" ), None )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["b"]["value"], "plugValueWidget:type" ), None )

		Gaffer.Metadata.registerValue( n["a"], "plugValueWidget:type", "Test" )

		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["a"]["value"], "plugValueWidget:type" ), "Test" )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["b"]["value"], "plugValueWidget:type" ), None )

		Gaffer.Metadata.registerValue( s["rows"].defaultRow()["cells"]["b"]["value"], "plugValueWidget:type", "Test2" )

		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["a"]["value"], "plugValueWidget:type" ), "Test" )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["b"]["value"], "plugValueWidget:type" ), "Test2" )

		Gaffer.Metadata.registerValue( s["rows"].defaultRow()["cells"]["a"]["value"], "plugValueWidget:type", "Test2" )

		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["a"]["value"], "plugValueWidget:type" ), "Test2" )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["b"]["value"], "plugValueWidget:type" ), "Test2" )

	def testPresetForwarding( self ) :

		s = Gaffer.Spreadsheet()
		s["rows"].addColumn( Gaffer.StringPlug( "a" ) )
		s["rows"].addColumn( Gaffer.StringPlug( "b" ) )
		s["rows"].addRows( 1 )

		n = Gaffer.Node()
		n.addChild( Gaffer.StringPlug( "a" ) )
		n.addChild( Gaffer.StringPlug( "b" ) )

		n["a"].setInput( s["out"]["a"] )
		n["b"].setInput( s["out"]["b"] )

		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["a"]["value"], "presetNames" ), IECore.StringVectorData( [] ) )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["a"]["value"], "presetValues" ), IECore.StringVectorData( [] ) )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["b"]["value"], "presetNames" ), IECore.StringVectorData( [] ) )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["b"]["value"], "presetValues" ), IECore.StringVectorData( [] ) )

		self.assertEqual( Gaffer.Metadata.value( s["rows"].defaultRow()["cells"]["a"]["value"], "presetNames" ), None )
		self.assertEqual( Gaffer.Metadata.value( s["rows"].defaultRow()["cells"]["a"]["value"], "presetValues" ), None )
		self.assertEqual( Gaffer.Metadata.value( s["rows"].defaultRow()["cells"]["b"]["value"], "presetNames" ), None )
		self.assertEqual( Gaffer.Metadata.value( s["rows"].defaultRow()["cells"]["b"]["value"], "presetValues" ), None )

		# Registering only "presetNames" on the destination plug doesn't forward to the cell.
		Gaffer.Metadata.registerValue( n["a"], "presetNames", IECore.StringVectorData( [ "Test", "Test2" ] ) )

		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["a"]["value"], "presetNames" ), IECore.StringVectorData( [] ) )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["a"]["value"], "presetValues" ), IECore.StringVectorData( [] ) )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["b"]["value"], "presetNames" ), IECore.StringVectorData( [] ) )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["b"]["value"], "presetValues" ), IECore.StringVectorData( [] ) )

		self.assertEqual( Gaffer.Metadata.value( s["rows"].defaultRow()["cells"]["a"]["value"], "presetNames" ), None )
		self.assertEqual( Gaffer.Metadata.value( s["rows"].defaultRow()["cells"]["a"]["value"], "presetValues" ), None )
		self.assertEqual( Gaffer.Metadata.value( s["rows"].defaultRow()["cells"]["b"]["value"], "presetNames" ), None )
		self.assertEqual( Gaffer.Metadata.value( s["rows"].defaultRow()["cells"]["b"]["value"], "presetValues" ), None )

		# Registering "presetValues" alongside "presetNames" will forward.
		Gaffer.Metadata.registerValue( n["a"], "presetValues", IECore.StringVectorData( [ "test", "test2" ] ) )

		self.assertEqual( Gaffer.Metadata.value( s["rows"].defaultRow()["cells"]["a"]["value"], "presetNames" ), IECore.StringVectorData( [ "Test", "Test2" ] ) )
		self.assertEqual( Gaffer.Metadata.value( s["rows"].defaultRow()["cells"]["a"]["value"], "presetValues" ), IECore.StringVectorData( [ "test", "test2" ] ) )
		self.assertEqual( Gaffer.Metadata.value( s["rows"].defaultRow()["cells"]["b"]["value"], "presetNames" ), None )
		self.assertEqual( Gaffer.Metadata.value( s["rows"].defaultRow()["cells"]["b"]["value"], "presetValues" ), None )

		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["a"]["value"], "presetNames" ), IECore.StringVectorData( [ "Test", "Test2" ] ) )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["a"]["value"], "presetValues" ), IECore.StringVectorData( [ "test", "test2" ] ) )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["b"]["value"], "presetNames" ), IECore.StringVectorData( [] ) )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["b"]["value"], "presetValues" ), IECore.StringVectorData( [] ) )

		# Registering "preset:" metadata also forwards, and combines with "presetNames" & "presetValues"
		Gaffer.Metadata.registerValue( n["a"], "preset:Test3", "test3" )
		Gaffer.Metadata.registerValue( n["b"], "preset:Test", "test" )

		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["a"]["value"], "presetNames" ), IECore.StringVectorData( [ "Test3", "Test", "Test2" ] ) )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["a"]["value"], "presetValues" ), IECore.StringVectorData( [ "test3", "test", "test2" ] ) )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["b"]["value"], "presetNames" ), IECore.StringVectorData( [ "Test" ] ) )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["b"]["value"], "presetValues" ), IECore.StringVectorData( [ "test" ] ) )

		self.assertEqual( Gaffer.Metadata.value( s["rows"].defaultRow()["cells"]["a"]["value"], "presetNames" ), IECore.StringVectorData( [ "Test3", "Test", "Test2" ] ) )
		self.assertEqual( Gaffer.Metadata.value( s["rows"].defaultRow()["cells"]["a"]["value"], "presetValues" ), IECore.StringVectorData( [ "test3", "test", "test2" ] ) )
		self.assertEqual( Gaffer.Metadata.value( s["rows"].defaultRow()["cells"]["b"]["value"], "presetNames" ), IECore.StringVectorData( [ "Test" ] ) )
		self.assertEqual( Gaffer.Metadata.value( s["rows"].defaultRow()["cells"]["b"]["value"], "presetValues" ), IECore.StringVectorData( [ "test" ] ) )

		# Registering either metadata on the default row will override the metadata from the destination.
		Gaffer.Metadata.registerValue( s["rows"].defaultRow()["cells"]["b"]["value"], "preset:TestDefault", "testDefault" )
		Gaffer.Metadata.registerValue( s["rows"].defaultRow()["cells"]["b"]["value"], "presetNames", IECore.StringVectorData( [ "TestDefault2", "TestDefault3" ] ) )
		Gaffer.Metadata.registerValue( s["rows"].defaultRow()["cells"]["b"]["value"], "presetValues", IECore.StringVectorData( [ "testDefault2", "testDefault3" ] ) )

		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["b"]["value"], "presetNames" ), IECore.StringVectorData( [ "TestDefault", "TestDefault2", "TestDefault3" ] ) )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["b"]["value"], "presetValues" ), IECore.StringVectorData( [ "testDefault", "testDefault2", "testDefault3" ] ) )

		# Registering "presetNames" and "presetValues" on the default row will override the destination presets.
		Gaffer.Metadata.registerValue( s["rows"].defaultRow()["cells"]["a"]["value"], "presetNames", IECore.StringVectorData( [ "TestDefault2", "TestDefault3" ] ) )
		Gaffer.Metadata.registerValue( s["rows"].defaultRow()["cells"]["a"]["value"], "presetValues", IECore.StringVectorData( [ "testDefault2", "testDefault3" ] ) )

		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["a"]["value"], "presetNames" ), IECore.StringVectorData( [ "TestDefault2", "TestDefault3" ] ) )
		self.assertEqual( Gaffer.Metadata.value( s["rows"][1]["cells"]["a"]["value"], "presetValues" ), IECore.StringVectorData( [ "testDefault2", "testDefault3" ] ) )

if __name__ == "__main__":
	unittest.main()
