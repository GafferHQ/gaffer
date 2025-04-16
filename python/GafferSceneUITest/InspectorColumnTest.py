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

	def testClipboardAlgoPaste( self ) :

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

		# Inconsistent selection is not copyable

		w.setSelection( [ IECore.PathMatcher( [ "/sphere", "/cube" ] ), IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertFalse( GafferUI.ClipboardAlgo.canCopy( w ) )

		# Consistent selection is copyable

		w.setSelection( [ IECore.PathMatcher( [ "/sphere", "/cube" ] ), IECore.PathMatcher( [ "/sphere", "/cube" ] ), IECore.PathMatcher( [] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertTrue( GafferUI.ClipboardAlgo.canCopy( w ) )

		# Test copy single value

		w.setSelection( [ IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		adaptor = GafferUI.ClipboardAlgo._PathListingAdaptor( w )
		self.assertTrue( adaptor.isValid() )
		self.assertEqual(
			adaptor.data(),
			Gaffer.ObjectMatrix( 1, 1, [ IECore.IntData( 100 ) ] )
		)

		GafferUI.ClipboardAlgo.copy( w )

		w.setSelection( [ IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/cube" ] ), IECore.PathMatcher( [] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		adaptor = GafferUI.ClipboardAlgo._PathListingAdaptor( w )
		self.assertEqual(
			adaptor.data(),
			Gaffer.ObjectMatrix( 1, 1, [ IECore.IntData( 200 ) ] )
		)

		self.assertEqual( GafferUI.ClipboardAlgo.nonPasteableReason( w ), "" )
		self.assertTrue( GafferUI.ClipboardAlgo.canPaste( w ) )
		GafferUI.ClipboardAlgo.paste( w )

		adaptor = GafferUI.ClipboardAlgo._PathListingAdaptor( w )
		self.assertEqual(
			adaptor.data(),
			Gaffer.ObjectMatrix( 1, 1, [ IECore.IntData( 100 ) ] )
		)

		# Test copy multiple values

		w.setSelection( [ IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [ "/sphere" ] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		GafferUI.ClipboardAlgo.copy( w )
		sourceData = GafferUI.ClipboardAlgo._PathListingAdaptor( w ).data()
		self.assertTrue( isinstance( a.getClipboardContents(), Gaffer.ObjectMatrix ) )
		self.assertEqual(
			a.getClipboardContents(),
			sourceData
		)

		w.setSelection( [ IECore.PathMatcher( [ "/cube" ] ), IECore.PathMatcher( [ "/cube" ] ), IECore.PathMatcher( [ "/cube" ] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertNotEqual(
			GafferUI.ClipboardAlgo._PathListingAdaptor( w ).data(),
			sourceData
		)

		self.assertEqual( GafferUI.ClipboardAlgo.nonPasteableReason( w ), "" )
		self.assertTrue( GafferUI.ClipboardAlgo.canPaste( w ) )
		GafferUI.ClipboardAlgo.paste( w )

		adaptor = GafferUI.ClipboardAlgo._PathListingAdaptor( w )
		self.assertEqual(
			adaptor.data(),
			sourceData
		)

	def testClipboardAlgoValueConversion( self ) :

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

		GafferUI.ClipboardAlgo.copy( w )

		w.setSelection( [ IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [] ), IECore.PathMatcher( [] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertEqual( GafferUI.ClipboardAlgo.nonPasteableReason( w ), 'Data of type "StringData" is not compatible.' )
		self.assertFalse( GafferUI.ClipboardAlgo.canPaste( w ) )

		# Test IntData can be converted to FloatData and BoolData

		GafferUI.ClipboardAlgo.copy( w )

		w.setSelection( [ IECore.PathMatcher( [] ), IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [ "/sphere" ] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertEqual( GafferUI.ClipboardAlgo.nonPasteableReason( w ), "" )
		self.assertTrue( GafferUI.ClipboardAlgo.canPaste( w ) )

		adaptor = GafferUI.ClipboardAlgo._PathListingAdaptor( w )
		self.assertEqual(
			adaptor.data(),
			Gaffer.ObjectMatrix( 2, 1, [ IECore.FloatData( 1.0 ), IECore.BoolData( False ) ] )
		)

		GafferUI.ClipboardAlgo.paste( w )
		adaptor = GafferUI.ClipboardAlgo._PathListingAdaptor( w )
		self.assertEqual(
			adaptor.data(),
			Gaffer.ObjectMatrix( 2, 1, [ IECore.FloatData( 100.0 ), IECore.BoolData( True ) ] )
		)

		# Test BoolData can be converted to FloatData and IntData

		w.setSelection( [ IECore.PathMatcher( [] ), IECore.PathMatcher( [] ), IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/sphere" ] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		GafferUI.ClipboardAlgo.copy( w )

		w.setSelection( [ IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertEqual( GafferUI.ClipboardAlgo.nonPasteableReason( w ), "" )
		self.assertTrue( GafferUI.ClipboardAlgo.canPaste( w ) )

		GafferUI.ClipboardAlgo.paste( w )
		adaptor = GafferUI.ClipboardAlgo._PathListingAdaptor( w )
		self.assertEqual(
			adaptor.data(),
			Gaffer.ObjectMatrix( 2, 1, [ IECore.IntData( 1 ), IECore.FloatData( 1.0 ) ] )
		)

	def testClipboardAlgoStringConversion( self ) :

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

		GafferUI.ClipboardAlgo.copy( w )

		w.setSelection( [ IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/cube" ] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertEqual( GafferUI.ClipboardAlgo.nonPasteableReason( w ), "" )
		self.assertTrue( GafferUI.ClipboardAlgo.canPaste( w ) )

		self.assertEqual(
			GafferUI.ClipboardAlgo._PathListingAdaptor( w ).data(),
			Gaffer.ObjectMatrix( 1, 1, [ IECore.StringVectorData( [ "cube", "vector" ] ) ] )
		)

		GafferUI.ClipboardAlgo.paste( w )

		adaptor = GafferUI.ClipboardAlgo._PathListingAdaptor( w )
		self.assertEqual(
			GafferUI.ClipboardAlgo._PathListingAdaptor( w ).data(),
			Gaffer.ObjectMatrix( 1, 1, [ IECore.StringVectorData( [ "sphere" ] ) ] )
		)

		# Test StringVectorData can be converted to StringData

		w.setSelection( [ IECore.PathMatcher( [ "" ] ), IECore.PathMatcher( [ "/sphere" ] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		GafferUI.ClipboardAlgo.copy( w )
		self.assertEqual(
			GafferUI.ClipboardAlgo._PathListingAdaptor( w ).data(),
			Gaffer.ObjectMatrix( 1, 1, [ IECore.StringVectorData( [ "sphere", "vector" ] ) ] )
		)

		w.setSelection( [ IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertEqual( GafferUI.ClipboardAlgo.nonPasteableReason( w ), "" )
		self.assertTrue( GafferUI.ClipboardAlgo.canPaste( w ) )

		GafferUI.ClipboardAlgo.paste( w )
		self.assertEqual(
			GafferUI.ClipboardAlgo._PathListingAdaptor( w ).data(),
			Gaffer.ObjectMatrix( 1, 1, [ IECore.StringData( "sphere vector" ) ] )
		)

		# Test space separated StringData conversion to StringVectorData

		GafferUI.ClipboardAlgo.copy( w )

		w.setSelection( [ IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/cube" ] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertEqual( GafferUI.ClipboardAlgo.nonPasteableReason( w ), "" )
		self.assertTrue( GafferUI.ClipboardAlgo.canPaste( w ) )

		GafferUI.ClipboardAlgo.paste( w )
		self.assertEqual(
			GafferUI.ClipboardAlgo._PathListingAdaptor( w ).data(),
			Gaffer.ObjectMatrix( 1, 1, [ IECore.StringVectorData( [ "sphere", "vector" ] ) ] )
		)

	def testClipboardAlgoWithNonInspectorColumn( self ) :

		a = Gaffer.ApplicationRoot()
		s = Gaffer.ScriptNode()
		a["scripts"]["testScript"] = s
		self.__testScene( s )

		w = GafferUI.PathListingWidget(
			GafferScene.ScenePath( s["parent"]["out"], Gaffer.Context(), "/" ),
			columns = [
				GafferUI.PathListingWidget.defaultNameColumn,
				GafferSceneUI.Private.InspectorColumn( GafferSceneUI.Private.AttributeInspector( s["parent"]["out"], None, "test:string" ) ),
			],
			selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
		)

		e = InspectorColumnTest.TestEditor( s )
		e.addPathListing( w )

		# Values can be copied from other column types and pasted to an InspectorColumn

		w.setSelection( [ IECore.PathMatcher( [ "/sphere" ] ), IECore.PathMatcher( [] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		GafferUI.ClipboardAlgo.copy( w )

		w.setSelection( [ IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/cube" ] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertEqual( GafferUI.ClipboardAlgo.nonPasteableReason( w ), "" )
		self.assertTrue( GafferUI.ClipboardAlgo.canPaste( w ) )

		GafferUI.ClipboardAlgo.paste( w )
		self.assertEqual(
			GafferUI.ClipboardAlgo._PathListingAdaptor( w ).data(),
			Gaffer.ObjectMatrix( 1, 1, [ IECore.StringData( "sphere" ) ] )
		)

		# Cannot paste when a column other than an InspectorColumn is in the selection

		w.setSelection( [ IECore.PathMatcher( [ "/cube" ] ), IECore.PathMatcher( [ "/cube" ] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertEqual( GafferUI.ClipboardAlgo.nonPasteableReason( w ), 'Column "Name" does not support pasting.' )
		self.assertFalse( GafferUI.ClipboardAlgo.canPaste( w ) )

		w.setSelection( [ IECore.PathMatcher( [] ), IECore.PathMatcher( [ "/cube" ] ) ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		self.assertEqual( GafferUI.ClipboardAlgo.nonPasteableReason( w ), "" )
		self.assertTrue( GafferUI.ClipboardAlgo.canPaste( w ) )

if __name__ == "__main__":
	unittest.main()
