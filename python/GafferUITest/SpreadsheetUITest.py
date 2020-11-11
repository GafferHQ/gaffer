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

		sourceRows = [ s["rows"][r].children() for r in range( 2, 3 ) ]
		rowData = _ClipboardAlgo.valueMatrix( sourceRows )

		self.assertTrue( _ClipboardAlgo.canPasteRows( rowData, s["rows"] ) )

		s2 = Gaffer.Spreadsheet()
		s2["rows"].addColumn( Gaffer.IntPlug(), "intColumn", False )

		self.assertFalse( _ClipboardAlgo.canPasteRows( rowData, s2["rows"] ) )

	def testPasteRows( self ) :

		s = self.__createSpreadsheet( numRows = 5 )

		sourceRows = [ s["rows"][r].children() for r in range( 2, 4 ) ]
		sourceHashes = self.__cellPlugHashes( sourceRows )
		rowData = _ClipboardAlgo.valueMatrix( sourceRows )

		self.assertEqual( len( s["rows"].children() ), 6 )
		existingHashes = self.__cellPlugHashes( [ s["rows"][r].children() for r in range( 6 ) ] )

		_ClipboardAlgo.pasteRows( rowData, s["rows"] )

		self.assertEqual( len( s["rows"].children() ), 6 + 2 )
		newHashes = self.__cellPlugHashes( [ s["rows"][r].children() for r in range( 6 + 2 ) ] )

		self.assertEqual( newHashes, existingHashes + sourceHashes )

	def testClipboardRespectsReadOnly( self ) :

		s = self.__createSpreadsheet()

		Gaffer.MetadataAlgo.setReadOnly( s["rows"][2]["cells"][2]["value"], True )
		Gaffer.MetadataAlgo.setReadOnly( s["rows"][3]["cells"][2], True )
		Gaffer.MetadataAlgo.setReadOnly( s["rows"], True )
		Gaffer.MetadataAlgo.setReadOnly( s, True )

		sourceCells = [ [ s["rows"][r]["cells"][1] ] for r in range( 7 ) ]
		sourceHashes = self.__cellPlugHashes( sourceCells )
		data = _ClipboardAlgo.valueMatrix( sourceCells )

		destCells = [ [ s["rows"][r]["cells"][2] ] for r in range( 7 ) ]
		origHashes = self.__cellPlugHashes( destCells )

		self.assertFalse( _ClipboardAlgo.canPasteCells( data, destCells ) )

		Gaffer.MetadataAlgo.setReadOnly( s, False )
		self.assertFalse( _ClipboardAlgo.canPasteCells( data, destCells ) )

		Gaffer.MetadataAlgo.setReadOnly( s["rows"], False )
		self.assertTrue( _ClipboardAlgo.canPasteCells( data, destCells ) )

		origLockedValueHash = s["rows"][2]["cells"][2]["value"].hash()

		_ClipboardAlgo.pasteCells( data, destCells, 0 )
		updatedHashes = self.__cellPlugHashes( destCells )

		for i in ( 0, 1, 4, 5, 6 ) :
			self.assertEqual( updatedHashes[i][0], sourceHashes[i][0] )
		self.assertEqual( s["rows"][2]["cells"][2]["enabled"].hash(), s["rows"][2]["cells"][1]["enabled"].hash() )
		self.assertEqual( s["rows"][2]["cells"][2]["value"].hash(), origLockedValueHash )
		self.assertEqual( updatedHashes[3][0], origHashes[3][0] )

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

if __name__ == "__main__":
	unittest.main()
