##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Limited. All rights reserved.
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
import GafferScene
import GafferSceneTest
import GafferSceneUI

class InspectorColumnTest( GafferUITest.TestCase ) :

	class TestEditor( GafferSceneUI.SceneEditor ) :

		def __init__( self, scriptNode, **kw ) :

			self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 4 )

			GafferSceneUI.SceneEditor.__init__( self, self.__column, scriptNode, **kw )

		def addPathListing( self, pathListing ) :

			self.__column.addChild( pathListing )

		def __repr__( self ) :

			return "GafferSceneUITest.InspectorColumnTest.TestEditor( scriptNode )"

	def __testScene( self, script ) :

		script["sphere"] = GafferScene.Sphere()

		script["customAttributes"] = GafferScene.CustomAttributes()
		script["customAttributes"]["in"].setInput( script["sphere"]["out"] )
		script["customAttributes"]["attributes"].addChild( Gaffer.NameValuePlug( "test:string", "sphere" ) )
		script["customAttributes"]["attributes"].addChild( Gaffer.NameValuePlug( "test:int", 100 ) )
		script["customAttributes"]["attributes"].addChild( Gaffer.NameValuePlug( "test:float", 1.0 ) )
		script["customAttributes"]["attributes"].addChild( Gaffer.NameValuePlug( "test:bool", False ) )
		script["customAttributes"]["attributes"].addChild( Gaffer.NameValuePlug( "test:stringVector", IECore.StringVectorData( [ "sphere", "vector" ] ) ) )

		script["cube"] = GafferScene.Cube()

		script["customCubeAttributes"] = GafferScene.CustomAttributes()
		script["customCubeAttributes"]["in"].setInput( script["cube"]["out"] )
		script["customCubeAttributes"]["attributes"].addChild( Gaffer.NameValuePlug( "test:string", "cube" ) )
		script["customCubeAttributes"]["attributes"].addChild( Gaffer.NameValuePlug( "test:int", 200 ) )
		script["customCubeAttributes"]["attributes"].addChild( Gaffer.NameValuePlug( "test:float", 2.0 ) )
		script["customCubeAttributes"]["attributes"].addChild( Gaffer.NameValuePlug( "test:bool", True ) )
		script["customCubeAttributes"]["attributes"].addChild( Gaffer.NameValuePlug( "test:stringVector", IECore.StringVectorData( [ "cube", "vector" ] ) ) )

		script["parent"] = GafferScene.Parent()
		script["parent"]["in"].setInput( script["customAttributes"]["out"] )
		script["parent"]["children"][0].setInput( script["customCubeAttributes"]["out"] )
		script["parent"]["parent"].setValue( "/" )

	def __testSpreadsheet( self ) :

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

			for i in range( 1, 11 ) :
				rowsPlug.addRow()["name"].setValue( "row%d" % i )
				rowsPlug[i]["cells"][0]["value"].setValue( "s%d" % ( i ) )
				rowsPlug[i]["cells"][2]["enabled"].setValue( i % 2 )
				for c in range( 1, 4 ) :
					rowsPlug[i]["cells"][c]["value"].setValue( i * pow( 10, c - 1 ) )

			return s

	def testInspectorColumnConstructors( self ) :

		light = GafferSceneTest.TestLight()

		inspector = GafferSceneUI.Private.AttributeInspector( light["out"], None, "gl:visualiser:scale" )

		c = GafferSceneUI.Private.InspectorColumn( inspector, "label", "help!" )
		self.assertEqual( c.inspector(), inspector )
		self.assertEqual( c.getSizeMode(), GafferUI.PathColumn.SizeMode.Default )
		self.assertEqual( c.headerData().value, "Label" )
		self.assertEqual( c.headerData().toolTip, "help!" )

		c = GafferSceneUI.Private.InspectorColumn( inspector, "Fancy ( Label )", "" )
		self.assertEqual( c.inspector(), inspector )
		self.assertEqual( c.getSizeMode(), GafferUI.PathColumn.SizeMode.Default )
		self.assertEqual( c.headerData().value, "Fancy ( Label )" )
		self.assertEqual( c.headerData().toolTip, "" )

		c = GafferSceneUI.Private.InspectorColumn( inspector )
		self.assertEqual( c.inspector(), inspector )
		self.assertEqual( c.getSizeMode(), GafferUI.PathColumn.SizeMode.Default )
		self.assertEqual( c.headerData().value, "Gl:visualiser:scale" )
		self.assertEqual( c.headerData().toolTip, "" )

		c = GafferSceneUI.Private.InspectorColumn(
			inspector,
			GafferUI.PathColumn.CellData( value = "Fancy ( Label )", toolTip = "help!" ),
			GafferUI.PathColumn.SizeMode.Stretch
		)
		self.assertEqual( c.inspector(), inspector )
		self.assertEqual( c.getSizeMode(), GafferUI.PathColumn.SizeMode.Stretch )
		self.assertEqual( c.headerData().value, "Fancy ( Label )" )
		self.assertEqual( c.headerData().toolTip, "help!" )

	def testObjectMatrixFromSelection( self ) :

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

		# Select non-contiguous cells in the same column

		s1 = [ IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/a", "/c", "/e" ] ) ]

		w.setSelection( s1 )
		self.assertEqual( w.getSelection(), s1 )
		expected = IECore.ObjectMatrix( 3, 1 )
		for i, x in enumerate( [ 1, 3, 5 ] ) :
			expected[i, 0] = IECore.IntData( x )

		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		self.assertTrue( GafferSceneUI._InspectorColumn._canCopySelectedValues( w ) )
		self.assertEqual(
			GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w ),
			expected
		)

		# Select contiguous cells in the same column

		s2 = [ IECore.PathMatcher( [ "/b", "/c" ] ), IECore.PathMatcher( [] ) ]

		w.setSelection( s2 )
		self.assertEqual( w.getSelection(), s2 )
		expected = IECore.ObjectMatrix( 2, 1 )
		for i, x in enumerate( [ "b", "c" ] ) :
			expected[i, 0] = IECore.StringData( x )

		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		self.assertTrue( GafferSceneUI._InspectorColumn._canCopySelectedValues( w ) )
		self.assertEqual(
			GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w ),
			expected
		)

		# Select the same row across both columns

		s3 = [ IECore.PathMatcher( [ "/e" ] ), IECore.PathMatcher( [ "/e" ] ) ]
		w.setSelection( s3 )
		self.assertEqual( w.getSelection(), s3 )

		expected = IECore.ObjectMatrix( 1, 2 )
		expected[0, 0] = IECore.StringData( "e" )
		expected[0, 1] = IECore.IntData( 5 )

		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		self.assertTrue( GafferSceneUI._InspectorColumn._canCopySelectedValues( w ) )
		self.assertEqual(
			GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w ),
			expected
		)

		# Select non-contiguous rows

		s4 = [ IECore.PathMatcher( [ "/b", "/d" ] ), IECore.PathMatcher( [ "/b", "/d" ] ) ]
		w.setSelection( s4 )
		self.assertEqual( w.getSelection(), s4 )

		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		self.assertTrue( GafferSceneUI._InspectorColumn._canCopySelectedValues( w ) )
		data = GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w )
		self.assertTrue( isinstance( data, IECore.ObjectMatrix ) )

		self.assertEqual( data[ 0, 0 ], IECore.StringData( "b" ) )
		self.assertEqual( data[ 0, 1 ], IECore.IntData( 2 ) )
		self.assertEqual( data[ 1, 0 ], IECore.StringData( "d" ) )
		self.assertEqual( data[ 1, 1 ], IECore.IntData( 4 ) )

		# Select mixed data types, these would end up copied to the same ObjectMatrix column

		s5 = [ IECore.PathMatcher( [ "/a", "/c" ] ), IECore.PathMatcher( [ "/b", "/d" ] ) ]
		w.setSelection( s5 )
		self.assertEqual( w.getSelection(), s5 )

		expected = IECore.ObjectMatrix( 4, 1 )
		expected[0, 0] = IECore.StringData( "a" )
		expected[1, 0] = IECore.IntData( 2 )
		expected[2, 0] = IECore.StringData( "c" )
		expected[3, 0] = IECore.IntData( 4 )

		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		self.assertTrue( GafferSceneUI._InspectorColumn._canCopySelectedValues( w ) )
		self.assertEqual(
			GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w ),
			expected
		)

		# Select two cells in one row and one cell in another, this is not copyable.

		s6 = [ IECore.PathMatcher( [ "/a" ] ), IECore.PathMatcher( [ "/a", "/d" ] ) ]
		w.setSelection( s6 )
		self.assertEqual( w.getSelection(), s6 )

		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		self.assertFalse( GafferSceneUI._InspectorColumn._canCopySelectedValues( w ) )
		self.assertEqual( GafferSceneUI._InspectorColumn._nonCopyableReason( w ), "Each row in the selection must contain the same number of cells." )

	def testClipboardPaste( self ) :

		a = Gaffer.ApplicationRoot()
		s = Gaffer.ScriptNode()
		a["scripts"]["testScript"] = s
		self.__testScene( s )

		w = GafferUI.PathListingWidget(
			GafferScene.ScenePath( s["parent"]["out"], Gaffer.Context(), "/" ),
			columns = [
				GafferSceneUI.Private.InspectorColumn( GafferSceneUI.Private.AttributeInspector( s["parent"]["out"], None, "test:string" ) ),
				GafferSceneUI.Private.InspectorColumn( GafferSceneUI.Private.AttributeInspector( s["parent"]["out"], None, "test:int" ) ),
				GafferSceneUI.Private.InspectorColumn( GafferSceneUI.Private.AttributeInspector( s["parent"]["out"], None, "test:float" ) ),
			],
			selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
		)

		e = InspectorColumnTest.TestEditor( s )
		e.addPathListing( w )

		# Inconsistent row selection is not copyable

		w.setSelection( [ IECore.PathMatcher( [ "/sphere", "/cube" ] ), IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertFalse( GafferSceneUI._InspectorColumn._canCopySelectedValues( w ) )
		self.assertEqual( GafferSceneUI._InspectorColumn._nonCopyableReason( w ), "Each row in the selection must contain the same number of cells." )

		# Consistent selection is copyable

		w.setSelection( [ IECore.PathMatcher( [ "/sphere", "/cube" ] ), IECore.PathMatcher( [ "/sphere", "/cube" ] ), IECore.PathMatcher( [] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertTrue( GafferSceneUI._InspectorColumn._canCopySelectedValues( w ) )
		self.assertEqual( GafferSceneUI._InspectorColumn._nonCopyableReason( w ), "" )

		# Test copy single value

		w.setSelection( [ IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertTrue( GafferSceneUI._InspectorColumn._canCopySelectedValues( w ) )
		self.assertEqual(
			GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w ),
			IECore.IntData( 100 )
		)

		GafferSceneUI._InspectorColumn._copySelectedValues( w )

		w.setSelection( [ IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/cube" ] ), IECore.PathMatcher( [] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertTrue( GafferSceneUI._InspectorColumn._canCopySelectedValues( w ) )
		self.assertEqual(
			GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w ),
			IECore.IntData( 200 )
		)

		self.assertEqual( GafferSceneUI._InspectorColumn._nonPasteableReason( w ), "" )
		self.assertTrue( GafferSceneUI._InspectorColumn._canPasteValues( w ) )
		GafferSceneUI._InspectorColumn._pasteValues( w )

		self.assertTrue( GafferSceneUI._InspectorColumn._canCopySelectedValues( w ) )
		self.assertEqual(
			GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w ),
			IECore.IntData( 100 )
		)

		# Test copy multiple values

		w.setSelection( [ IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [ "/sphere" ] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertTrue( GafferSceneUI._InspectorColumn._canCopySelectedValues( w ) )
		GafferSceneUI._InspectorColumn._copySelectedValues( w )
		sourceData = GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w )
		self.assertTrue( isinstance( a.getClipboardContents(), IECore.ObjectMatrix ) )
		self.assertEqual(
			a.getClipboardContents(),
			sourceData
		)

		w.setSelection( [ IECore.PathMatcher( [ "/cube" ] ), IECore.PathMatcher( [ "/cube" ] ), IECore.PathMatcher( [ "/cube" ] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertTrue( GafferSceneUI._InspectorColumn._canCopySelectedValues( w ) )
		self.assertNotEqual(
			GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w ),
			sourceData
		)

		self.assertEqual( GafferSceneUI._InspectorColumn._nonPasteableReason( w ), "" )
		self.assertTrue( GafferSceneUI._InspectorColumn._canPasteValues( w ) )
		GafferSceneUI._InspectorColumn._pasteValues( w )

		self.assertEqual(
			GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w ),
			sourceData
		)

	def testPasteObjectMatrixWithNone( self ) :

		a = Gaffer.ApplicationRoot()
		s = Gaffer.ScriptNode()
		a["scripts"]["testScript"] = s
		self.__testScene( s )

		w = GafferUI.PathListingWidget(
			GafferScene.ScenePath( s["parent"]["out"], Gaffer.Context(), "/" ),
			columns = [
				GafferSceneUI.Private.InspectorColumn( GafferSceneUI.Private.AttributeInspector( s["parent"]["out"], None, "test:string" ) ),
				GafferSceneUI.Private.InspectorColumn( GafferSceneUI.Private.AttributeInspector( s["parent"]["out"], None, "test:int" ) ),
				GafferSceneUI.Private.InspectorColumn( GafferSceneUI.Private.AttributeInspector( s["parent"]["out"], None, "test:float" ) ),
			],
			selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
		)

		e = InspectorColumnTest.TestEditor( s )
		e.addPathListing( w )

		# Paste initial values so we can later test that a paste containing None does not overwrite.

		pasteData = IECore.ObjectMatrix( [ [ IECore.StringData( "foo" ), IECore.IntData( 123 ), IECore.FloatData( 123.0 ) ] ] )
		a.setClipboardContents( pasteData )

		w.setSelection( [ IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [ "/sphere" ] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertTrue( GafferSceneUI._InspectorColumn._canPasteValues( w ) )
		GafferSceneUI._InspectorColumn._pasteValues( w )

		self.assertEqual(
			GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w ),
			pasteData
		)

		# Paste a new ObjectMatrix with None for the middle column. Paste should update the other columns,
		# but preserve the existing value of the middle column.

		pasteData = IECore.ObjectMatrix( [ [ IECore.StringData( "bar" ), None, IECore.FloatData( 456.0 ) ] ] )
		a.setClipboardContents( pasteData )

		self.assertTrue( GafferSceneUI._InspectorColumn._canPasteValues( w ) )
		GafferSceneUI._InspectorColumn._pasteValues( w )

		self.assertEqual(
			GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w ),
			IECore.ObjectMatrix( [ [ IECore.StringData( "bar" ), IECore.IntData( 123 ), IECore.FloatData( 456.0 ) ] ] )
		)

	def testClipboardValueConversion( self ) :

		a = Gaffer.ApplicationRoot()
		s = Gaffer.ScriptNode()
		a["scripts"]["testScript"] = s
		self.__testScene( s )

		w = GafferUI.PathListingWidget(
			GafferScene.ScenePath( s["parent"]["out"], Gaffer.Context(), "/" ),
			columns = [
				GafferSceneUI.Private.InspectorColumn( GafferSceneUI.Private.AttributeInspector( s["parent"]["out"], None, "test:string" ) ),
				GafferSceneUI.Private.InspectorColumn( GafferSceneUI.Private.AttributeInspector( s["parent"]["out"], None, "test:int" ) ),
				GafferSceneUI.Private.InspectorColumn( GafferSceneUI.Private.AttributeInspector( s["parent"]["out"], None, "test:float" ) ),
				GafferSceneUI.Private.InspectorColumn( GafferSceneUI.Private.AttributeInspector( s["parent"]["out"], None, "test:bool" ) ),
			],
			selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
		)

		e = InspectorColumnTest.TestEditor( s )
		e.addPathListing( w )

		# Test StringData cannot be converted to IntData

		w.setSelection( [ IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [] ), IECore.PathMatcher( [] ), IECore.PathMatcher( [] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		GafferSceneUI._InspectorColumn._copySelectedValues( w )

		w.setSelection( [ IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [] ), IECore.PathMatcher( [] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertEqual( GafferSceneUI._InspectorColumn._nonPasteableReason( w ), 'Data of type "StringData" is not compatible.' )
		self.assertFalse( GafferSceneUI._InspectorColumn._canPasteValues( w ) )

		# Test IntData can be converted to FloatData and BoolData

		GafferSceneUI._InspectorColumn._copySelectedValues( w )

		w.setSelection( [ IECore.PathMatcher( [] ), IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [ "/sphere" ] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertEqual( GafferSceneUI._InspectorColumn._nonPasteableReason( w ), "" )
		self.assertTrue( GafferSceneUI._InspectorColumn._canPasteValues( w ) )

		self.assertEqual(
			GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w ),
			IECore.ObjectMatrix( [ [ IECore.FloatData( 1.0 ), IECore.BoolData( False ) ] ] )
		)

		GafferSceneUI._InspectorColumn._pasteValues( w )
		self.assertEqual(
			GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w ),
			IECore.ObjectMatrix( [ [ IECore.FloatData( 100.0 ), IECore.BoolData( True ) ] ] )
		)

		# Test BoolData can be converted to FloatData and IntData

		w.setSelection( [ IECore.PathMatcher( [] ), IECore.PathMatcher( [] ), IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/sphere" ] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		GafferSceneUI._InspectorColumn._copySelectedValues( w )

		w.setSelection( [ IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertEqual( GafferSceneUI._InspectorColumn._nonPasteableReason( w ), "" )
		self.assertTrue( GafferSceneUI._InspectorColumn._canPasteValues( w ) )

		GafferSceneUI._InspectorColumn._pasteValues( w )
		self.assertEqual(
			GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w ),
			IECore.ObjectMatrix( [ [ IECore.IntData( 1 ), IECore.FloatData( 1.0 ) ] ] )
		)

	def testClipboardStringConversion( self ) :

		a = Gaffer.ApplicationRoot()
		s = Gaffer.ScriptNode()
		a["scripts"]["testScript"] = s
		self.__testScene( s )

		w = GafferUI.PathListingWidget(
			GafferScene.ScenePath( s["parent"]["out"], Gaffer.Context(), "/" ),
			columns = [
				GafferSceneUI.Private.InspectorColumn( GafferSceneUI.Private.AttributeInspector( s["parent"]["out"], None, "test:string" ) ),
				GafferSceneUI.Private.InspectorColumn( GafferSceneUI.Private.AttributeInspector( s["parent"]["out"], None, "test:stringVector" ) ),
			],
			selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
		)

		e = InspectorColumnTest.TestEditor( s )
		e.addPathListing( w )

		# Test StringData can be converted to StringVectorData

		w.setSelection( [ IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		GafferSceneUI._InspectorColumn._copySelectedValues( w )

		w.setSelection( [ IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/cube" ] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertEqual( GafferSceneUI._InspectorColumn._nonPasteableReason( w ), "" )
		self.assertTrue( GafferSceneUI._InspectorColumn._canPasteValues( w ) )

		self.assertEqual(
			GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w ),
			IECore.StringVectorData( [ "cube", "vector" ] )
		)

		GafferSceneUI._InspectorColumn._pasteValues( w )

		self.assertEqual(
			GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w ),
			IECore.StringVectorData( [ "sphere" ] )
		)

		# Test StringVectorData can be converted to StringData

		w.setSelection( [ IECore.PathMatcher( [ "" ] ), IECore.PathMatcher( [ "/sphere" ] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		GafferSceneUI._InspectorColumn._copySelectedValues( w )
		self.assertEqual(
			GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w ),
			IECore.StringVectorData( [ "sphere", "vector" ] )
		)

		w.setSelection( [ IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertEqual( GafferSceneUI._InspectorColumn._nonPasteableReason( w ), "" )
		self.assertTrue( GafferSceneUI._InspectorColumn._canPasteValues( w ) )

		GafferSceneUI._InspectorColumn._pasteValues( w )
		self.assertEqual(
			GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w ),
			IECore.StringData( "sphere vector" )
		)

		# Test space separated StringData conversion to StringVectorData

		GafferSceneUI._InspectorColumn._copySelectedValues( w )

		w.setSelection( [ IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/cube" ] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertEqual( GafferSceneUI._InspectorColumn._nonPasteableReason( w ), "" )
		self.assertTrue( GafferSceneUI._InspectorColumn._canPasteValues( w ) )

		GafferSceneUI._InspectorColumn._pasteValues( w )
		self.assertEqual(
			GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w ),
			IECore.StringVectorData( [ "sphere", "vector" ] )
		)

	def testCopyFromPathListingWidgetPasteToSpreadsheet( self ) :

		script = Gaffer.ScriptNode()
		script["s"] = self.__testSpreadsheet()

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
		data = GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w )
		self.assertTrue( isinstance( data, IECore.ObjectMatrix ) )

		targetPlugs = [
			rowsPlug[2]["cells"][0], rowsPlug[2]["cells"][1],
			rowsPlug[3]["cells"][0], rowsPlug[3]["cells"][1],
			rowsPlug[4]["cells"][0], rowsPlug[4]["cells"][2]
		]
		originalValues = [ x["value"].getValue() for x in targetPlugs ]

		plugMatrix = GafferUI.SpreadsheetUI._ClipboardAlgo.createPlugMatrixFromCells( targetPlugs )
		self.assertTrue( GafferUI.SpreadsheetUI._ClipboardAlgo.canPasteCells( data, plugMatrix ) )
		GafferUI.SpreadsheetUI._ClipboardAlgo.pasteCells( data, plugMatrix, 0 )

		pastedValues = [ x["value"].getValue() for x in targetPlugs ]
		self.assertNotEqual( pastedValues, originalValues )
		self.assertEqual( pastedValues, [ "a", 101, "c", 303, "e", 505 ] )

		# extend selection to more rows than we copied and paste again

		targetPlugs.extend( [
			rowsPlug[5]["cells"][0], rowsPlug[5]["cells"][1],
			rowsPlug[6]["cells"][0], rowsPlug[6]["cells"][1]
		] )

		plugMatrix = GafferUI.SpreadsheetUI._ClipboardAlgo.createPlugMatrixFromCells( targetPlugs )
		self.assertTrue( GafferUI.SpreadsheetUI._ClipboardAlgo.canPasteCells( data, plugMatrix ) )
		GafferUI.SpreadsheetUI._ClipboardAlgo.pasteCells( data, plugMatrix, 0 )

		# pasted values should repeat outside of the copied range

		self.assertEqual( [ x["value"].getValue() for x in targetPlugs ], [ "a", 101, "c", 303, "e", 505, "a", 101, "c", 303 ] )

	def testCopyFromSpreadsheetPasteToPathListingWidget( self ) :

		a = Gaffer.ApplicationRoot()
		s = Gaffer.ScriptNode()
		a["scripts"]["testScript"] = s
		self.__testScene( s )

		w = GafferUI.PathListingWidget(
			GafferScene.ScenePath( s["parent"]["out"], Gaffer.Context(), "/" ),
			columns = [
				GafferSceneUI.Private.InspectorColumn( GafferSceneUI.Private.AttributeInspector( s["parent"]["out"], None, "test:string" ) ),
				GafferSceneUI.Private.InspectorColumn( GafferSceneUI.Private.AttributeInspector( s["parent"]["out"], None, "test:int" ) ),
				GafferSceneUI.Private.InspectorColumn( GafferSceneUI.Private.AttributeInspector( s["parent"]["out"], None, "test:float" ) ),
			],
			selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
		)

		e = InspectorColumnTest.TestEditor( s )
		e.addPathListing( w )

		s["s"] = self.__testSpreadsheet()
		rowsPlug = s["s"]["rows"]

		sourcePlugs = [
			rowsPlug[2]["cells"][0], rowsPlug[2]["cells"][1], rowsPlug[2]["cells"][3],
			rowsPlug[4]["cells"][0], rowsPlug[4]["cells"][1], rowsPlug[4]["cells"][3],
		]
		plugMatrix = GafferUI.SpreadsheetUI._ClipboardAlgo.createPlugMatrixFromCells( sourcePlugs )
		self.assertTrue( GafferUI.SpreadsheetUI._ClipboardAlgo.canCopyPlugs( plugMatrix ) )
		GafferUI.SpreadsheetUI._ClipboardAlgo.copyPlugs( plugMatrix )

		w.setSelection( [ IECore.PathMatcher( [ "/sphere", "/cube" ] ), IECore.PathMatcher( [ "/sphere", "/cube" ] ), IECore.PathMatcher( [ "/sphere", "/cube" ] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		originalValues = GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w )

		self.assertTrue( GafferSceneUI._InspectorColumn._canPasteValues( w ) )
		GafferSceneUI._InspectorColumn._pasteValues( w )

		valuesAfterPaste = GafferSceneUI._InspectorColumn._dataFromPathListingOrReason( w )
		self.assertNotEqual( valuesAfterPaste, originalValues )
		self.assertEqual(
			valuesAfterPaste,
			IECore.ObjectMatrix( [
				[ IECore.StringData( "s2" ), IECore.IntData( 2 ), IECore.FloatData( 200 ) ],
				[ IECore.StringData( "s4" ), IECore.IntData( 4 ), IECore.FloatData( 400 ) ]
			] )
		)

	def testInspect( self ) :

		plane = GafferScene.Plane()
		customAttributes = GafferScene.CustomAttributes()
		customAttributes["in"].setInput( plane["out"] )
		customAttributes["attributes"].addChild( Gaffer.NameValuePlug( "user:test", 10 ) )

		inspector = GafferSceneUI.Private.AttributeInspector( customAttributes["out"], None, "user:test" )
		column = GafferSceneUI.Private.InspectorColumn( inspector, "label", "help!" )

		path = GafferScene.ScenePath( customAttributes["out"], Gaffer.Context(), "/plane" )
		inspection = column.inspect( path )
		self.assertIsInstance( inspection, GafferSceneUI.Private.Inspector.Result )
		self.assertEqual( inspection.source(), customAttributes["attributes"][0] )
		self.assertEqual( inspection.value(), IECore.IntData( 10 ) )

if __name__ == "__main__":
	unittest.main()
