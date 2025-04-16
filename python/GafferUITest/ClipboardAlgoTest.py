##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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
import GafferUI
from GafferUI import _GafferUI
import GafferUITest

class ClipboardAlgoTest( GafferUITest.TestCase ) :

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

		for i, columnPlug in enumerate( (
			Gaffer.StringPlug(),     # 0
			Gaffer.IntPlug(),        # 1
			Gaffer.IntPlug(),        # 2
			Gaffer.FloatPlug(),      # 3
			Gaffer.IntPlug(),        # 4
		) ) :
			rowsPlug.addColumn( columnPlug, "column%d" % i, adoptEnabledPlug = False )

		for i in range( 1, numRows + 1 ) :
			rowsPlug.addRow()["name"].setValue( "row%d" % i )
			rowsPlug[i]["cells"][0]["value"].setValue( "s%d" % ( i ) )
			rowsPlug[i]["cells"][2]["enabled"].setValue( i % 2 )
			for c in range( 1, 4 ) :
				rowsPlug[i]["cells"][c]["value"].setValue( i * pow( 10, c - 1 ) )

		return s

	def testClipboardAdaptorFromObjectMatrix( self ) :

		C = IECore.CompoundData
		B = IECore.BoolData
		I = IECore.IntData
		F = IECore.FloatData
		S = IECore.StringData

		for d in (
			"cat",
			1,
			None,
			[],
			[ 1, 2, 3 ],
			[ [ 1 ] ],
			[ [ 1, 4 ] ],
			# Mixed row value types
			Gaffer.ObjectMatrix( 1, 2, [
				C({ "enabled" : B( True ), "value" : I( 2 ) }),
				C({ "enabled" : B( True ), "value" : S( "2" ) })
			]),
			# Mixed row keys
			Gaffer.ObjectMatrix( 1, 2, [
				C({ "enabled" : B( True ), "value" : I( 2 ) }),
				C({ "znabled" : B( True ), "value" : I( 2 ) })
			]),
		) :
			with self.subTest( d = d ) :
				self.assertFalse( GafferUI.ClipboardAlgo._ClipboardAdaptor( d ).isValid() )

		for d in (
			# one row, one column
			Gaffer.ObjectMatrix( 1, 1, [ C({ "enabled" : B( True ), "value" : I( 1 ) }) ] ),
			# one row, two columns
			Gaffer.ObjectMatrix( 2, 1, [ C({ "enabled" : B( True ), "value" : I( 2 ) }), C({ "enabled" : B( True ), "value" : F( 2 ) }) ] ),
			# two rows, one column
			Gaffer.ObjectMatrix( 1, 2, [
				C({ "enabled" : B( True ), "value" : I( 3 ) }),
				C({ "enabled" : B( True ), "value" : I( 3 ) })
			] ),
			# two rows, two columns
			Gaffer.ObjectMatrix( 2, 2, [
				C({ "enabled" : B( True ), "value" : I( 4 ) }), C({ "enabled" : B( False ), "value" : F( 4 ) }),
				C({ "enabled" : B( True ), "value" : I( 4 ) }), C({ "enabled" : B( True ),  "value" : F( 4 ) })
			] ),
		) :
			with self.subTest( d = d ) :
				self.assertTrue( GafferUI.ClipboardAlgo._ClipboardAdaptor( d ).isValid() )

	def testSpreadsheetAdaptor( self ) :

		a = Gaffer.ApplicationRoot()
		script = Gaffer.ScriptNode()
		a["scripts"]["testScript"] = script
		script["s"] = self.__createSpreadsheet()
		rowsPlug = script["s"]["rows"]

		sw = GafferUI.ScriptWindow.acquire( script )
		w = GafferUI.PlugValueWidget.acquire( rowsPlug )
		cellsTable = w._RowsPlugValueWidget__cellsTable

		sourcePlugs = [ rowsPlug[1]["cells"][2], rowsPlug[1]["cells"][3] ]
		cellsTable.selectPlugs( sourcePlugs )

		adaptor = GafferUI.ClipboardAlgo._SpreadsheetAdaptor( cellsTable )
		self.assertTrue( adaptor.isValid() )
		self.assertEqual( adaptor.data().width(), 2 )
		self.assertEqual( adaptor.data().height(), 1 )
		sourceValues = [ IECore.CompoundData( { "enabled" : x["enabled"].getValue(), "value" : x["value"].getValue() } ) for x in sourcePlugs ]
		self.assertEqual( adaptor.data(), Gaffer.ObjectMatrix( 2, 1, sourceValues ) )

		# Copy cells to clipboard

		self.assertTrue( GafferUI.ClipboardAlgo.canCopy( cellsTable ) )
		GafferUI.ClipboardAlgo.copy( cellsTable )
		self.assertTrue( isinstance( a.getClipboardContents(), Gaffer.ObjectMatrix ) )
		self.assertEqual( a.getClipboardContents(), adaptor.data() )

		# Paste to cells in the next row

		targetPlugs = [ rowsPlug[2]["cells"][2], rowsPlug[2]["cells"][3] ]
		cellsTable.selectPlugs( targetPlugs )
		originalValues = [ IECore.CompoundData( { "enabled" : x["enabled"].getValue(), "value" : x["value"].getValue() } ) for x in targetPlugs ]

		self.assertTrue( GafferUI.ClipboardAlgo.canPaste( cellsTable ) )
		self.assertEqual( GafferUI.ClipboardAlgo.nonPasteableReason( cellsTable ), "" )
		GafferUI.ClipboardAlgo.paste( cellsTable )
		pastedValues = [ IECore.CompoundData( { "enabled" : x["enabled"].getValue(), "value" : x["value"].getValue() } ) for x in targetPlugs ]

		self.assertNotEqual( originalValues, pastedValues )
		self.assertEqual( sourceValues, pastedValues )

		# Extend selection to 4th column and paste again

		targetPlugs.append( rowsPlug[2]["cells"][4] )
		cellsTable.selectPlugs( targetPlugs )
		originalValues = [ IECore.CompoundData( { "enabled" : x["enabled"].getValue(), "value" : x["value"].getValue() } ) for x in targetPlugs ]

		self.assertTrue( GafferUI.ClipboardAlgo.canPaste( cellsTable ) )
		self.assertEqual( GafferUI.ClipboardAlgo.nonPasteableReason( cellsTable ), "" )
		GafferUI.ClipboardAlgo.paste( cellsTable )
		pastedValues = [ IECore.CompoundData( { "enabled" : x["enabled"].getValue(), "value" : x["value"].getValue() } ) for x in targetPlugs ]

		self.assertNotEqual( originalValues, pastedValues )
		self.assertNotEqual( originalValues[0], originalValues[2] )
		self.assertEqual( pastedValues[0], pastedValues[2] )

		# Spreadsheet applications often don't allow copy/pasting with a sparse selection
		# where all rows/columns aren't the same length, we also don't allow this.

		cellsTable.selectPlugs( [ rowsPlug[1]["cells"][2], rowsPlug[1]["cells"][3], rowsPlug[2]["cells"][2] ] )
		self.assertFalse( GafferUI.ClipboardAlgo.canPaste( cellsTable ) )
		adaptor = GafferUI.ClipboardAlgo._SpreadsheetAdaptor( cellsTable )
		self.assertFalse( adaptor.isValid() )
		self.assertFalse( GafferUI.ClipboardAlgo.canCopy( cellsTable ) )

	def testClipboardAdaptorValueExtrapolation( self ) :

		value00 = IECore.CompoundData( { "enabled" : IECore.BoolData( True ), "value" : IECore.IntData( 4 ) } )
		value10 = IECore.CompoundData( { "enabled" : IECore.BoolData( False ), "value" : IECore.IntData( 8 ) } )
		value01 = IECore.FloatData( 3 )
		value11 = IECore.FloatData( 6 )

		adaptor = GafferUI.ClipboardAlgo._ClipboardAdaptor(
			Gaffer.ObjectMatrix( 2, 2, [ value00, value01, value10, value11 ] )
		)
		self.assertTrue( adaptor.isValid() )

		for row, column, value in [
			( 0, 0, value00 ),
			( 0, 1, value01 ),
			( 1, 0, value10 ),
			( 1, 1, value11 ),
			( 0, 2, value00 ),
			( 0, 3, value01 ),
			( 2, 0, value00 ),
			( 2, 1, value01 ),
			( 3, 2, value10 ),
			( 3, 3, value11 ),
			( 5, 4, value10 ),
			( 5, 5, value11 ),
			( 100, 0, value00 ),
			( 0, 101, value01 ),
			( 1001, 1001, value11 )
		] :
			self.assertEqual( adaptor.value( row, column ), value )
			self.assertEqual( adaptor.value( row, column, extractValue = True ), value["value"] if isinstance( value, IECore.CompoundData ) else value )

	def testPathListingAdaptor( self ) :

		d = {
			"a" : 1,
			"b" : 2,
			"c" : 3,
			"d" : 4,
			"e" : 5
		}

		p = Gaffer.DictPath( d, "/" )

		w = GafferUI.PathListingWidget(
			p,
			columns = [
				GafferUI.PathListingWidget.defaultNameColumn,
				GafferUI.PathListingWidget.StandardColumn( "A", "dict:value" )
			],
			selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
		)

		# select non-contiguous cells in the same column

		s1 = [ IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/a", "/c", "/e" ] ) ]

		w.setSelection( s1 )
		self.assertEqual( w.getSelection(), s1 )

		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		adaptor = GafferUI.ClipboardAlgo._PathListingAdaptor( w )
		self.assertTrue( adaptor.isValid() )
		self.assertEqual(
			adaptor.data(),
			Gaffer.ObjectMatrix( 1, 3, [ IECore.IntData( x ) for x in [ 1, 3, 5 ] ] )
		)

		# select contiguous cells in the same column

		s2 = [ IECore.PathMatcher( [ "/b", "/c" ] ), IECore.PathMatcher( [] ) ]

		w.setSelection( s2 )
		self.assertEqual( w.getSelection(), s2 )

		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		adaptor = GafferUI.ClipboardAlgo._PathListingAdaptor( w )
		self.assertTrue( adaptor.isValid() )
		self.assertEqual(
			adaptor.data(),
			Gaffer.ObjectMatrix( 1, 2, [ IECore.StringData( x ) for x in [ "b", "c" ] ] )
		)

		# select the same row across both columns

		s3 = [ IECore.PathMatcher( [ "/e" ] ), IECore.PathMatcher( [ "/e" ] ) ]
		w.setSelection( s3 )
		self.assertEqual( w.getSelection(), s3 )

		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		adaptor = GafferUI.ClipboardAlgo._PathListingAdaptor( w )
		self.assertTrue( adaptor.isValid() )
		self.assertEqual(
			adaptor.data(),
			Gaffer.ObjectMatrix( 2, 1, [ IECore.StringData( "e" ), IECore.IntData( 5 ) ] )
		)

		# select non-contiguous rows

		s4 = [ IECore.PathMatcher( [ "/b", "/d" ] ), IECore.PathMatcher( [ "/b", "/d" ] ) ]
		w.setSelection( s4 )
		self.assertEqual( w.getSelection(), s4 )

		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		adaptor = GafferUI.ClipboardAlgo._PathListingAdaptor( w )
		self.assertTrue( adaptor.isValid() )

		self.assertEqual( adaptor.data().value( 0, 0 ), IECore.StringData( "b" ) )
		self.assertEqual( adaptor.data().value( 1, 0 ), IECore.IntData( 2 ) )
		self.assertEqual( adaptor.data().value( 0, 1 ), IECore.StringData( "d" ) )
		self.assertEqual( adaptor.data().value( 1, 1 ), IECore.IntData( 4 ) )

		# test selection of mixed data types, these would end up copied to the same column and the
		# result is not considered valid

		s5 = [ IECore.PathMatcher( [ "/a" ] ), IECore.PathMatcher( [ "/d" ] ) ]
		w.setSelection( s5 )
		self.assertEqual( w.getSelection(), s5 )

		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		adaptor = GafferUI.ClipboardAlgo._PathListingAdaptor( w )
		self.assertFalse( adaptor.isValid() )

	def testCopyFromPathListingWidgetPasteToSpreadsheet( self ) :

		script = Gaffer.ScriptNode()
		script["s"] = self.__createSpreadsheet()
		rowsPlug = script["s"]["rows"]

		sw = GafferUI.ScriptWindow.acquire( script )
		r = GafferUI.PlugValueWidget.acquire( rowsPlug )
		cellsTable = r._RowsPlugValueWidget__cellsTable

		d = {
			"a" : 101,
			"b" : 202,
			"c" : 303,
			"d" : 404,
			"e" : 505
		}

		p = Gaffer.DictPath( d, "/" )

		w = GafferUI.PathListingWidget(
			p,
			columns = [
				GafferUI.PathListingWidget.defaultNameColumn,
				GafferUI.PathListingWidget.StandardColumn( "A", "dict:value" )
			],
			selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
		)

		w.setSelection( [ IECore.PathMatcher( [ "/a", "/c", "/e" ] ), IECore.PathMatcher( [ "/a", "/c", "/e" ] ) ] )

		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		pathListingAdaptor = GafferUI.ClipboardAlgo._PathListingAdaptor( w )
		self.assertTrue( pathListingAdaptor.isValid() )

		targetPlugs = [
			rowsPlug[2]["cells"][0], rowsPlug[2]["cells"][1],
			rowsPlug[3]["cells"][0], rowsPlug[3]["cells"][1],
			rowsPlug[4]["cells"][0], rowsPlug[4]["cells"][2]
		]
		originalValues = [ x["value"].getValue() for x in targetPlugs ]

		cellsTable.selectPlugs( targetPlugs )

		spreadsheetAdaptor = GafferUI.ClipboardAlgo._SpreadsheetAdaptor( pathListingAdaptor.data() )
		self.assertTrue( spreadsheetAdaptor.canPaste( cellsTable ) )
		spreadsheetAdaptor.paste( cellsTable )

		pastedValues = [ x["value"].getValue() for x in targetPlugs ]
		self.assertNotEqual( pastedValues, originalValues )
		self.assertEqual( pastedValues, [ "a", 101, "c", 303, "e", 505 ] )

		# extend selection to more rows than we copied and paste again

		targetPlugs.extend( [
			rowsPlug[5]["cells"][0], rowsPlug[5]["cells"][1],
			rowsPlug[6]["cells"][0], rowsPlug[6]["cells"][1]
		] )

		cellsTable.selectPlugs( targetPlugs )
		spreadsheetAdaptor = GafferUI.ClipboardAlgo._SpreadsheetAdaptor( pathListingAdaptor.data() )
		self.assertTrue( spreadsheetAdaptor.canPaste( cellsTable ) )
		spreadsheetAdaptor.paste( cellsTable )

		# pasted values should repeat outside of the copied range

		self.assertEqual( [ x["value"].getValue() for x in targetPlugs ], [ "a", 101, "c", 303, "e", 505, "a", 101, "c", 303 ] )

if __name__ == "__main__":
	unittest.main()
