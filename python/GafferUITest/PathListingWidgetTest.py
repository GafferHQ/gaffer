##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import functools
import time

import imath

import IECore

import Gaffer
import GafferTest

import GafferUI
from GafferUI import _GafferUI
import GafferUITest

from Qt import QtCore

class PathListingWidgetTest( GafferUITest.TestCase ) :

	def testExpandedPaths( self ) :

		d = {}
		for i in range( 0, 10 ) :
			dd = {}
			for j in range( 0, 10 ) :
				dd[str(j)] = j
			d[str(i)] = dd

		p = Gaffer.DictPath( d, "/" )

		w = GafferUI.PathListingWidget( p )
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )
		self.assertEqual( len( w.getExpandedPaths() ), 0 )

		p1 = Gaffer.DictPath( d, "/1" )
		self.assertEqual( w.getPathExpanded( p1 ), False )
		w.setPathExpanded( p1, True )
		self.assertEqual( w.getPathExpanded( p1 ), True )
		self.assertEqual( len( w.getExpandedPaths() ), 1 )
		self.assertEqual( str( list( w.getExpandedPaths() )[0] ), str( p1 ) )

		w.setPathExpanded( p1, False )
		self.assertEqual( w.getPathExpanded( p1 ), False )
		self.assertEqual( len( w.getExpandedPaths() ), 0 )

		p2 = Gaffer.DictPath( d, "/2" )
		p3 = Gaffer.DictPath( d, "/3" )
		w.setExpandedPaths( [ p1, p2 ] )
		self.assertEqual( w.getPathExpanded( p1 ), True )
		self.assertEqual( w.getPathExpanded( p2 ), True )
		self.assertEqual( w.getPathExpanded( p3 ), False )
		self.assertEqual( w.getExpandedPaths(), [ p1, p2 ] )

		w.setPath( Gaffer.DictPath( {}, "/" ) )
		self.assertEqual( len( w.getExpandedPaths() ), 0 )

	def testExpansion( self ) :

		d = {}
		for i in range( 0, 10 ) :
			dd = {}
			for j in range( 0, 10 ) :
				dd[str(j)] = j
			d[str(i)] = dd

		p = Gaffer.DictPath( d, "/" )
		w = GafferUI.PathListingWidget( p, displayMode = GafferUI.PathListingWidget.DisplayMode.Tree )
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )

		self.assertTrue( w.getExpansion().isEmpty() )

		cs = GafferTest.CapturingSlot( w.expansionChangedSignal() )
		e = IECore.PathMatcher( [ "/1", "/2", "/2/4", "/1/5", "/3" ] )

		w.setExpansion( e )
		self.assertEqual( w.getExpansion(), e )
		self.assertEqual( len( cs ), 1 )

		# Wait for asynchronous update to expand model. Then check
		# that the expected indices are expanded in the QTreeView.
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		self.assertEqual( self.__expansionFromQt( w ), e )

		# Delete a path that was expanded.
		d2 = d["2"]
		del d["2"]
		self.__emitPathChanged( w )
		# We don't expect this to affect the result of `getExpansion()` because
		# the expansion state is independent of the model contents.
		self.assertEqual( w.getExpansion(), e )
		# But it should affect what is mirrored in Qt.
		e2 = IECore.PathMatcher( e )
		e2.removePath( "/2" )
		e2.removePath( "/2/4" )
		self.assertEqual( self.__expansionFromQt( w ), e2 )

		# If we reintroduce the deleted path, it should be expanded again in Qt.
		# This behaviour is particularly convenient when switching between
		# different scenes in the HierarchyView, and matches the behaviour of
		# the SceneGadget.
		d["2"] = d2
		self.__emitPathChanged( w )
		self.assertEqual( self.__expansionFromQt( w ), e )

		# Now try to set expansion twice in succession, so the model doesn't have
		# chance to finish one update before starting the next.

		e1 = IECore.PathMatcher( [ "/9", "/9/10", "/8/6" ] )
		e2 = IECore.PathMatcher( [ "/9", "/9/9", "/5/6", "3" ] )
		w.setExpansion( e1 )
		w.setExpansion( e2 )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		self.assertEqual( self.__expansionFromQt( w ), e2 )

	def testExpansionByUser( self ) :

		w = GafferUI.PathListingWidget(
			Gaffer.DictPath( { "a" : { "b" : { "c" : 10 } } }, "/" ),
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
		)
		model = w._qtWidget().model()
		model.rowCount() # Trigger population of top level of the model
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( model ) )
		self.assertEqual( w.getExpansion(), IECore.PathMatcher() )

		cs = GafferTest.CapturingSlot( w.expansionChangedSignal() )
		w._qtWidget().setExpanded( model.index( 0, 0 ), True ) # Equivalent to a click by the user
		self.assertEqual( len( cs ), 1 )
		self.assertEqual( w.getExpansion(), IECore.PathMatcher( [ "/a" ] ) )

		w._qtWidget().setExpanded( model.index( 0, 0 ), False ) # Equivalent to a click by the user
		self.assertEqual( len( cs ), 2 )
		self.assertEqual( w.getExpansion(), IECore.PathMatcher() )

	def testSetExpansionClearsExpansionByUser( self ) :

		w = GafferUI.PathListingWidget(
			Gaffer.DictPath( { "a" : 1, "b" : 2, "c" : 3 }, "/" ),
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
		)
		model = w._qtWidget().model()
		model.rowCount() # Trigger population of top level of the model
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( model ) )
		self.assertEqual( w.getExpansion(), IECore.PathMatcher() )

		w._qtWidget().expand( model.index( 0, 0 ) ) # Equivalent to a click by the user
		self.assertEqual( w.getExpansion(), IECore.PathMatcher( [ "/a" ] ) )

		w.setExpansion( IECore.PathMatcher( [ "/b" ] ) )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( model ) )
		self.assertEqual( self.__expansionFromQt( w ), IECore.PathMatcher( [ "/b" ] ) )

		w._qtWidget().collapse( model.index( 1, 0 ) ) # Equivalent to a click by the user
		self.assertEqual( w.getExpansion(), IECore.PathMatcher() )
		w.setExpansion( IECore.PathMatcher( [ "/b" ] ) )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( model ) )
		self.assertEqual( self.__expansionFromQt( w ), IECore.PathMatcher( [ "/b" ] ) )

	def testExpansionSignalFrequency( self ) :

		d = {}
		for i in range( 0, 10 ) :
			dd = {}
			for j in range( 0, 10 ) :
				dd[str(j)] = j
			d[str(i)] = dd

		p = Gaffer.DictPath( d, "/" )
		w = GafferUI.PathListingWidget( p )
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )

		c = GafferTest.CapturingSlot( w.expansionChangedSignal() )
		self.assertEqual( len( c ), 0 )

		w.setPathExpanded( Gaffer.DictPath( d, "/1" ), True )
		self.assertEqual( len( c ), 1 )
		w.setPathExpanded( Gaffer.DictPath( d, "/1" ), True )
		self.assertEqual( len( c ), 1 )

		w.setPathExpanded( Gaffer.DictPath( d, "/2" ), True )
		self.assertEqual( len( c ), 2 )

		e = w.getExpandedPaths()
		self.assertEqual( len( e ), 2 )

		w.setExpandedPaths( [] )
		self.assertEqual( len( c ), 3 )

		w.setExpandedPaths( e )
		self.assertEqual( len( c ), 4 )

	def testRowSelection( self ) :

		d = {}
		for i in range( 0, 10 ) :
			dd = {}
			for j in range( 0, 10 ) :
				dd[str(j)] = j
			d[str(i)] = dd

		p = Gaffer.DictPath( d, "/" )

		w = GafferUI.PathListingWidget(
			p,
			selectionMode = GafferUI.PathListingWidget.SelectionMode.Rows,
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
		)
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )

		self.assertTrue( w.getSelection().isEmpty() )

		# Set selection. This should be immediately reflected in
		# the `selectionChangedSignal` and the result of `getSelection()`.

		cs = GafferTest.CapturingSlot( w.selectionChangedSignal() )
		s = IECore.PathMatcher( [ "/1", "/2", "/9", "/2/5", "/3/1" ] )

		w.setSelection( s )
		self.assertEqual( w.getSelection(), s )
		self.assertEqual( len( cs ), 1 )

		# Delete a path that was selected.
		d2 = d["2"]
		del d["2"]
		self.__emitPathChanged( w )
		# We don't expect this to affect the result of `getSelection()` because
		# the selection state is independent of the model contents.
		self.assertEqual( w.getSelection(), s )

		# Now try to set selection twice in succession, so the model doesn't have
		# chance to finish one update before starting the next.

		s1 = IECore.PathMatcher( [ "/9", "/9/10", "/8/6" ] )
		s2 = IECore.PathMatcher( [ "/9", "/9/9", "/5/6", "3" ] )
		w.setSelection( s1 )
		w.setSelection( s2 )
		self.assertEqual( w.getSelection(), s2 )

	def testCellsSelection( self ) :

		d = {}
		for i in range( 0, 10 ) :
			dd = {}
			for j in range( 0, 10 ) :
				dd[str(j)] = j
			d[str(i)] = dd

		p = Gaffer.DictPath( d, "/" )

		w = GafferUI.PathListingWidget(
			p,
			selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
		)
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )

		self.assertEqual( w.getColumns(), list( w.defaultFileSystemColumns ) )

		c = [ w.defaultNameColumn, w.StandardColumn( "h", "a" ) ]

		w.setColumns( c )
		self.assertEqual( w.getColumns(), c )

		self.assertEqual( len( w.getSelection() ), 2 )

		# Set selection. This should be immediately reflected in
		# the `selectionChangedSignal` and the result of `getSelection()`.

		cs = GafferTest.CapturingSlot( w.selectionChangedSignal() )
		s11 = IECore.PathMatcher( [ "/1", "/2", "/9", "/2/5", "/3/1" ] )
		s12 = IECore.PathMatcher( [ "/1", "/3", "/9", "/2/5", "/4/6" ] )

		w.setSelection( [ s11, s12 ] )
		self.assertEqual( w.getSelection(), [ s11, s12 ] )
		self.assertEqual( len( cs ), 1 )

		# Delete a path that was selected.
		d2 = d["2"]
		del d["2"]
		self.__emitPathChanged( w )
		# We don't expect this to affect the result of `getSelection()` because
		# the selection state is independent of the model contents.
		self.assertEqual( w.getSelection(), [ s11, s12 ] )

		# Now try to set selection twice in succession, so the model doesn't have
		# chance to finish one update before starting the next.

		s21 = IECore.PathMatcher( [ "/9", "/9/10", "/8/6" ] )
		s31 = IECore.PathMatcher( [ "/9", "/9/9", "/5/6", "3" ] )
		w.setSelection( [ s21, s12 ] )
		w.setSelection( [ s31, s12 ] )
		self.assertEqual( w.getSelection(), [ s31, s12 ] )

	def testRowSelectionScrolling( self ) :

		d = {}
		for i in range( 0, 10 ) :
			dd = {}
			for j in range( 0, 10 ) :
				dd[str(j)] = j
			d[str(i)] = dd

		p = Gaffer.DictPath( d, "/" )

		w = GafferUI.PathListingWidget(
			p,
			selectionMode = GafferUI.PathListingWidget.SelectionMode.Rows,
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
		)
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )

		self.assertTrue( w.getSelection().isEmpty() )
		self.assertTrue( w.getExpansion().isEmpty() )

		s = IECore.PathMatcher( [ "/1", "/2", "/9", "/2/5" ] )
		w.setSelection( s, expandNonLeaf = False, scrollToFirst = False )
		self.assertEqual( w.getSelection(), s )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		self.assertTrue( w.getExpansion().isEmpty() )

		s.addPath( "/3/5" )
		w.setSelection( s, expandNonLeaf = False, scrollToFirst = True )
		self.assertEqual( w.getSelection(), s )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		self.assertEqual( w.getExpansion(), IECore.PathMatcher( [ "/3" ] ) )

	def testCellSelectionScrolling( self ) :

		d = {}
		for i in range( 0, 10 ) :
			dd = {}
			for j in range( 0, 10 ) :
				dd[str(j)] = j
			d[str(i)] = dd

		p = Gaffer.DictPath( d, "/" )

		w = GafferUI.PathListingWidget(
			p,
			selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
		)
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )

		# The default widget has multiple columns preset for file browsing,
		# just use two to simply testing.
		c = [ w.defaultNameColumn, w.StandardColumn( "h", "a" ) ]
		w.setColumns( c )
		self.assertEqual( w.getColumns(), c )

		self.assertEqual( w.getSelection(), [IECore.PathMatcher()] * 2 )
		self.assertTrue( w.getExpansion().isEmpty() )

		s1 = IECore.PathMatcher( [ "/1", "/2", "/9", "/2/5" ] )
		s2 = IECore.PathMatcher( [ "/1", "/2", "/9", "/2/5" ] )
		w.setSelection( [ s1, s2 ], expandNonLeaf = False, scrollToFirst = False )
		self.assertEqual( w.getSelection(), [ s1, s2 ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		self.assertTrue( w.getExpansion().isEmpty() )

		s1.addPath( "/3/5" )
		w.setSelection( [ s1, s2 ], expandNonLeaf = False, scrollToFirst = True )
		self.assertEqual( w.getSelection(), [ s1, s2 ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		self.assertEqual( w.getExpansion(), IECore.PathMatcher( [ "/3" ] ) )

		s2.addPath( "/4/6" )
		w.setSelection( [ s1, s2 ], expandNonLeaf = False, scrollToFirst = True )
		self.assertEqual( w.getSelection(), [ s1, s2 ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		self.assertEqual( w.getExpansion(), IECore.PathMatcher( [ "/3", "/4" ] ) )

	def testRowSelectionExpansion( self ) :

		d = {}
		for i in range( 0, 10 ) :
			dd = {}
			for j in range( 0, 10 ) :
				dd[str(j)] = j
			d[str(i)] = dd

		p = Gaffer.DictPath( d, "/" )

		w = GafferUI.PathListingWidget(
			p,
			selectionMode = GafferUI.PathListingWidget.SelectionMode.Rows,
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
		)
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )

		self.assertTrue( w.getSelection().isEmpty() )
		self.assertTrue( w.getExpansion().isEmpty() )

		s = IECore.PathMatcher( [ "/1", "/2", "/9", "/2/5" ] )
		w.setSelection( s, expandNonLeaf = True, scrollToFirst = False )
		self.assertEqual( w.getSelection(), s )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		self.assertEqual( w.getExpansion(), IECore.PathMatcher( [ "/1", "/2", "/9" ] ) )

	def testCellSelectionExpansion( self ) :

		d = {}
		for i in range( 0, 10 ) :
			dd = {}
			for j in range( 0, 10 ) :
				dd[str(j)] = j
			d[str(i)] = dd

		p = Gaffer.DictPath( d, "/" )

		w = GafferUI.PathListingWidget(
			p,
			selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells,
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
		)
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )

		# The default widget has multiple columns preset for file browsing,
		# just use two to simply testing.
		c = [ w.defaultNameColumn, w.StandardColumn( "h", "a" ) ]
		w.setColumns( c )
		self.assertEqual( w.getColumns(), c )

		self.assertEqual( w.getSelection(), [IECore.PathMatcher()] * 2 )
		self.assertTrue( w.getExpansion().isEmpty() )

		s1 = IECore.PathMatcher( [ "/1", "/2", "/9", "/2/5" ] )
		s2 = IECore.PathMatcher( [ "/1", "/3", "/4", "/9", "/4/6" ] )
		w.setSelection( [ s1, s2 ], expandNonLeaf = True, scrollToFirst = False )
		self.assertEqual( w.getSelection(), [ s1, s2 ] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		self.assertEqual( w.getExpansion(), IECore.PathMatcher( [ "/1", "/2", "/3", "/4", "/9" ] ) )

	def testSelectionSignalFrequency( self ) :

		d = {
			"a" : {
				"e" : 10,
			},
			"b" : {
				"f" : "g",
			},
		}

		p = Gaffer.DictPath( d, "/" )
		w = GafferUI.PathListingWidget( p, selectionMode = GafferUI.PathListingWidget.SelectionMode.Rows )
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )

		c = GafferTest.CapturingSlot( w.selectionChangedSignal() )
		self.assertEqual( len( c ), 0 )

		w.setSelectedPaths( [ Gaffer.DictPath( d, "/a" ), Gaffer.DictPath( d, "/b" ) ] )
		self.assertEqual( set( [ str( p ) for p in w.getSelectedPaths() ] ), set( [ "/a", "/b" ] ) )

		self.assertEqual( len( c ), 1 )

	def testChangingDirectoryClearsRowSelection( self ) :

		path = Gaffer.DictPath( { "a" : { "b" : { "c" : 10 } } }, "/" )
		widget = GafferUI.PathListingWidget( path )

		widget.setSelection( IECore.PathMatcher( [ "/a" ] ) )
		self.assertEqual( widget.getSelection(), IECore.PathMatcher( [ "/a" ] ) )

		path.append( "a" )
		self.assertEqual( widget.getSelection(), IECore.PathMatcher() )

	def testChangingDirectoryClearsCellSelection( self ) :

		path = Gaffer.DictPath( { "a" : { "b" : { "c" : 10 } } }, "/" )
		widget = GafferUI.PathListingWidget(
			path,
			selectionMode = GafferUI.PathListingWidget.SelectionMode.Cells
		)
		# The default widget has multiple columns preset for file browsing,
		# just use two to simply testing.
		c = [ widget.defaultNameColumn, widget.StandardColumn( "h", "a" ) ]
		widget.setColumns( c )
		self.assertEqual( widget.getColumns(), c )

		widget.setSelection(
			[
				IECore.PathMatcher( [ "/a" ] ),
				IECore.PathMatcher( [ "/a/b" ] ),
			]
		)
		self.assertEqual(
			widget.getSelection(),
			[
				IECore.PathMatcher( [ "/a" ] ),
				IECore.PathMatcher( [ "/a/b" ] ),
			]
		)

		path.append( "a" )
		self.assertEqual(
			widget.getSelection(),
			[
				IECore.PathMatcher(),
				IECore.PathMatcher(),
			]
		)

	def testExpandedPathsWhenPathChanges( self ) :

		d = {
			"a" : {
				"e" : 10,
			},
			"b" : {
				"f" : "g",
			},
		}

		p = Gaffer.DictPath( d, "/" )
		p1 = Gaffer.DictPath( d, "/a" )
		w = GafferUI.PathListingWidget( p, displayMode = GafferUI.PathListingWidget.DisplayMode.Tree )
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )

		self.assertEqual( w.getPathExpanded( p1 ), False )
		w.setPathExpanded( p1, True )
		self.assertEqual( w.getPathExpanded( p1 ), True )

		# Fake a change to the path and check that the expansion is exactly as
		# it was.
		self.__emitPathChanged( w )
		self.assertEqual( w.getPathExpanded( p1 ), True )
		self.assertEqual( self.__expansionFromQt( w ), IECore.PathMatcher( [ "/a" ] ) )

	def testExpandedPathsWhenPathChangesWithSelection( self ) :

		d = {
			"a" : {
				"e" : 10,
			},
			"b" : {
				"f" : "g",
			},
		}

		p = Gaffer.DictPath( d, "/" )
		pa = Gaffer.DictPath( d, "/a" )
		pae = Gaffer.DictPath( d, "/a/e" )
		w = GafferUI.PathListingWidget( p, displayMode = GafferUI.PathListingWidget.DisplayMode.Tree )
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )

		self.assertEqual( w.getPathExpanded( pa ), False )
		self.assertEqual( w.getPathExpanded( pae ), False )

		w.setSelectedPaths( [ pa ], expandNonLeaf = False )
		self.assertEqual( w.getPathExpanded( pa ), False )
		self.assertEqual( w.getPathExpanded( pae ), False )

		# Fake a change to the path and check that the expansion is exactly as
		# it was.
		self.__emitPathChanged( w )
		self.assertEqual( w.getPathExpanded( pa ), False )
		self.assertEqual( w.getPathExpanded( pae ), False )

	def testHeaderVisibility( self ) :

		with GafferUI.ListContainer() as c :
			w = GafferUI.PathListingWidget( Gaffer.DictPath( {}, "/" ) )
			_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )

		self.assertTrue( w.getHeaderVisible() )

		w.setHeaderVisible( False )
		self.assertFalse( w.getHeaderVisible() )

		w.setHeaderVisible( True )
		self.assertTrue( w.getHeaderVisible() )

		c.setVisible( False )
		self.assertTrue( w.getHeaderVisible() )

		w.setHeaderVisible( False )
		self.assertFalse( w.getHeaderVisible() )

	def testDeeperExpandedPaths( self ) :

		p = Gaffer.DictPath( { "a" : { "b" : { "c" : { "d" : 10 } } } }, "/" )

		w = GafferUI.PathListingWidget( p )
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )

		w.setPathExpanded( p.copy().setFromString( "/a/b/c" ), True )
		self.assertTrue( w.getPathExpanded( p.copy().setFromString( "/a/b/c" ) ) )
		self.assertEqual( w.getExpansion(), IECore.PathMatcher( [ "/a/b/c" ] ) )

		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )

		# We don't expect `/a/b/c` to have been expanded in Qt yet, because the ancestors
		# aren't expanded and it won't be visible anyway.
		self.assertEqual( self.__expansionFromQt( w ), IECore.PathMatcher() )

	def testColumns( self ) :

		w = GafferUI.PathListingWidget( Gaffer.DictPath( {}, "/" ) )
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )

		self.assertEqual( w.getColumns(), list( w.defaultFileSystemColumns ) )

		c1 = [ w.defaultNameColumn, w.defaultFileSystemIconColumn ]
		c2 = [ w.defaultNameColumn, w.StandardColumn( "h", "a" ) ]

		w.setColumns( c1 )
		self.assertEqual( w.getColumns(), c1 )

		w.setColumns( c2 )
		self.assertEqual( w.getColumns(), c2 )

		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		updates = []
		w._qtWidget().model().updateFinished.connect( lambda : updates.append( True ) )

		# When a column signals it has been changed, the model should update.
		c2[1].changedSignal()( c2[1] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		self.assertEqual( len( updates ), 1 )

		# But not when that column has been removed from the model.
		w.setColumns( c1 )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		del updates[:]
		c2[1].changedSignal()( c2[1] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( w._qtWidget().model() ) )
		self.assertEqual( len( updates ), 0 )

	def testSortable( self ) :

		w = GafferUI.PathListingWidget( Gaffer.DictPath( {}, "/" ) )
		self.assertTrue( w.getSortable() )

		w.setSortable( False )
		self.assertFalse( w.getSortable() )

		w.setSortable( True )
		self.assertTrue( w.getSortable() )

	def testSetSelectedPathsAfterPathChange( self ) :

		d = {}
		p = Gaffer.DictPath( d, "/" )

		w = GafferUI.PathListingWidget( p )

		d["a"] = 10
		p.pathChangedSignal()( p )
		w.setSelectedPaths( [ p.copy().setFromString( "/a" ) ] )
		s = w.getSelectedPaths()
		self.assertEqual( len( s ), 1 )
		self.assertEqual( str( s[0] ), "/a" )

	# All tests prefixed with `testModel()` test the PathModel class
	# directly rather than testing it via the PathListingWidget layer.
	# They still construct a PathListingWidget to instantiate the model,
	# because we don't have Python bindings to allow us to use the model
	# in isolation.

	def testModel( self ) :

		root = Gaffer.GraphComponent()
		root["a"] = Gaffer.GraphComponent()

		path = Gaffer.GraphComponentPath( root, "/" )
		widget = GafferUI.PathListingWidget(
			path,
			columns = [ GafferUI.PathListingWidget.defaultNameColumn ],
			sortable = False,
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
		)
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( widget._qtWidget() ) )

		model = widget._qtWidget().model()
		self.__expandModel( model )
		self.assertEqual( model.rowCount(), 1 )
		self.assertEqual( model.columnCount(), 1 )

		# If we add a new child to the path, it should appear in the
		# model. And if we have a persistent index for the original child, that
		# should remain valid.
		aIndex = QtCore.QPersistentModelIndex( model.index( 0, 0 ) )
		root["b"] = Gaffer.GraphComponent()
		self.__emitPathChanged( widget )

		self.assertEqual( model.rowCount(), 2 )
		self.assertEqual( model.columnCount(), 1 )
		self.assertTrue( aIndex.isValid() )
		self.assertEqual( aIndex.row(), 0 )

		# If we delete `a`, it should be gone from the model, but a
		# persistent index to `b` should remain valid.
		bIndex = QtCore.QPersistentModelIndex( model.index( 1, 0 ) )
		del root["a"]
		self.__emitPathChanged( widget )

		self.assertEqual( model.rowCount(), 1 )
		self.assertEqual( model.columnCount(), 1 )
		self.assertFalse( aIndex.isValid() )
		self.assertTrue( bIndex.isValid() )
		self.assertEqual( model.rowCount( bIndex ), 0 )

		# If we add a child to `b`, the model should update to reflect
		# that too.
		root["b"]["c"] = Gaffer.GraphComponent()
		self.__emitPathChanged( widget )

		self.assertTrue( bIndex.isValid() )
		self.assertEqual( model.rowCount( bIndex ), 1 )
		self.assertEqual( model.columnCount( bIndex ), 1 )
		self.assertEqual( model.data( model.index( 0, 0, bIndex ) ), "c" )

		# We should be able to add and remove children from `c`
		# and see it reflected in the model.
		cIndex = QtCore.QPersistentModelIndex( model.index( 0, 0, bIndex ) )
		self.assertEqual( model.data( cIndex ), "c" )
		self.assertEqual( model.rowCount( cIndex ), 0 )

		root["b"]["c"]["d"] = Gaffer.GraphComponent()
		self.__emitPathChanged( widget )

		self.assertTrue( cIndex.isValid() )
		self.assertEqual( model.rowCount( cIndex ), 1 )
		self.assertEqual( model.columnCount( cIndex ), 1 )
		self.assertEqual( model.data( model.index( 0, 0, cIndex ) ), "d" )

		dIndex = QtCore.QPersistentModelIndex( model.index( 0, 0, cIndex ) )
		del root["b"]["c"]["d"]
		self.__emitPathChanged( widget )
		self.assertTrue( cIndex.isValid() )
		self.assertEqual( model.rowCount( cIndex ), 0 )
		self.assertFalse( dIndex.isValid() )

	def testModelSorting( self ) :

		# Make a widget with sorting enabled.

		root = Gaffer.GraphComponent()
		root["c"] = Gaffer.GraphComponent()
		root["b"] = Gaffer.GraphComponent()

		path = Gaffer.GraphComponentPath( root, "/" )
		widget = GafferUI.PathListingWidget( path, columns = [ GafferUI.PathListingWidget.defaultNameColumn ], sortable = True )
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( widget._qtWidget() ) )

		model = widget._qtWidget().model()
		self.__expandModel( model )
		self.assertEqual( model.rowCount(), 2 )
		self.assertEqual( model.columnCount(), 1 )

		# Check that the paths appear in sorted order.

		self.assertEqual( model.data( model.index( 0, 0 ) ), "b" )
		self.assertEqual( model.data( model.index( 1, 0 ) ), "c" )
		bIndex = QtCore.QPersistentModelIndex( model.index( 0, 0 ) )
		cIndex = QtCore.QPersistentModelIndex( model.index( 1, 0 ) )

		# And sorting is maintained when adding another path.

		root["a"] = Gaffer.GraphComponent()
		self.__emitPathChanged( widget )

		self.assertEqual( model.rowCount(), 3 )
		self.assertEqual( model.columnCount(), 1 )
		self.assertEqual( model.data( model.index( 0, 0 ) ), "a" )
		self.assertEqual( model.data( model.index( 1, 0 ) ), "b" )
		self.assertEqual( model.data( model.index( 2, 0 ) ), "c" )

		self.assertTrue( bIndex.isValid() )
		self.assertTrue( cIndex.isValid() )
		self.assertEqual( model.data( bIndex ), "b" )
		self.assertEqual( model.data( cIndex ), "c" )

		# Turning sorting off should revert to the order in
		# the path itself.

		aIndex = QtCore.QPersistentModelIndex( model.index( 0, 0 ) )
		widget.setSortable( False )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( model ) )

		self.assertEqual( model.rowCount(), 3 )
		self.assertEqual( model.columnCount(), 1 )

		self.assertTrue( aIndex.isValid() )
		self.assertTrue( bIndex.isValid() )
		self.assertTrue( cIndex.isValid() )
		self.assertEqual( model.data( aIndex ), "a" )
		self.assertEqual( model.data( bIndex ), "b" )
		self.assertEqual( model.data( cIndex ), "c" )

		self.assertEqual( model.data( model.index( 0, 0 ) ), "c" )
		self.assertEqual( model.data( model.index( 1, 0 ) ), "b" )
		self.assertEqual( model.data( model.index( 2, 0 ) ), "a" )

	def testModelPathSwap( self ) :

		# Make a model for a small hierarchy, and expand the
		# model fully.

		root1 = Gaffer.GraphComponent()
		root1["c"] = Gaffer.GraphComponent()
		root1["c"]["d"] = Gaffer.GraphComponent()

		widget = GafferUI.PathListingWidget(
			path = Gaffer.GraphComponentPath( root1, "/" ),
			columns = [ GafferUI.PathListingWidget.defaultNameColumn ],
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
		)
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( widget._qtWidget() ) )

		path = Gaffer.GraphComponentPath( root1, "/" )
		self.assertEqual( path.property( "graphComponent:graphComponent" ), root1 )
		path.append( "c" )
		self.assertEqual( path.property( "graphComponent:graphComponent" ), root1["c"] )
		path.append( "d" )
		self.assertEqual( path.property( "graphComponent:graphComponent" ), root1["c"]["d"] )

		model = widget._qtWidget().model()
		self.__expandModel( model )

		# Get an index for `/c/d` and check that we can retrieve
		# the right path for it.

		def assertIndexRefersTo( index, graphComponent ) :

			if isinstance( index, QtCore.QPersistentModelIndex ) :
				index = QtCore.QModelIndex( index )

			path = widget._PathListingWidget__pathForIndex( index )
			self.assertEqual(
				path.property( "graphComponent:graphComponent" ),
				graphComponent
			)

		dIndex = model.index( 0, 0, model.index( 0, 0 ) )
		assertIndexRefersTo( dIndex, root1["c"]["d"] )
		persistentDIndex = QtCore.QPersistentModelIndex( dIndex )
		assertIndexRefersTo( persistentDIndex, root1["c"]["d"] )

		# Replace the path with another one referencing an identical hierarchy.

		root2 = Gaffer.GraphComponent()
		root2["c"] = Gaffer.GraphComponent()
		root2["c"]["d"] = Gaffer.GraphComponent()

		widget.setPath( Gaffer.GraphComponentPath( root2, "/" ) )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( model ) )

		# Check that the model now references the new path and the
		# new hierarchy.

		dIndex = model.index( 0, 0, model.index( 0, 0 ) )
		assertIndexRefersTo( dIndex, root2["c"]["d"] )
		assertIndexRefersTo( persistentDIndex, root2["c"]["d"] )

	def testModelNoSignallingForUnchangedPaths( self ) :

		# Make a widget showing a small hierarchy.

		root = Gaffer.GraphComponent()
		root["c"] = Gaffer.GraphComponent()
		root["c"]["d"] = Gaffer.GraphComponent()

		widget = GafferUI.PathListingWidget(
			path = Gaffer.GraphComponentPath( root, "/" ),
			columns = [ GafferUI.PathListingWidget.defaultNameColumn ],
		)
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( widget._qtWidget() ) )
		self.__expandModel( widget._qtWidget().model(), queryData = True )

		# Fake a change to the path. Since nothing has truly changed,
		# the model should not signal any changes.

		changes = []
		def changed( *args ) :
			changes.append( args )

		widget._qtWidget().model().layoutChanged.connect( functools.partial( changed ) )
		widget._qtWidget().model().dataChanged.connect( functools.partial( changed ) )

		self.__emitPathChanged( widget )
		self.assertEqual( changes, [] )

	def testModelFirstQueryDoesntEmitDataChanged( self ) :

		for sortable in ( False, True ) :

			# Not making widget visible, so it doesn't make any
			# queries to the model (leaving just our queries and
			# those made by the attached tester).
			widget = GafferUI.PathListingWidget(
				path = Gaffer.DictPath( { "v" : 10 }, "/" ),
				columns = [
					GafferUI.PathListingWidget.defaultNameColumn,
					GafferUI.PathListingWidget.StandardColumn( "Value", "dict:value" )
				],
				sortable = sortable,
				displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
			)
			_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( widget._qtWidget() ) )

			if sortable :
				# Sort by "Value" column as sorting by defaultNameColumn
				# doesn't trigger a data update.
				widget._qtWidget().header().setSortIndicator( 1, QtCore.Qt.AscendingOrder )

			# Make initial child queries to populate the model with
			# items, but without evaluating data. We should start
			# without any rows on the root item.
			model = widget._qtWidget().model()
			self.assertEqual( model.rowCount(), 0 )
			# Meaning that we can't even get an index to the first row.
			self.assertFalse( model.index( 0, 0 ).isValid() )
			# But if we wait for the update we've just triggered then
			# we should see a row appear.
			_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( model ) )
			self.assertEqual( model.rowCount(), 1 )
			self.assertTrue( model.index( 0, 0 ).isValid() )

			# Set up recording for data changes.

			changes = []
			def dataChanged( *args ) :
				changes.append( args )

			model.dataChanged.connect( dataChanged )

			# We are testing the columns containing "dict:value".
			valueIndex = model.index( 0, 1 )
			if sortable :
				# Data will have been generated during sorting, so
				# we can query it immediately.
				self.assertEqual( model.data( valueIndex ), 10 )
				self.assertEqual( len( changes ), 0 )
			else :
				# Data not generated yet. The initial query will receive empty
				# data and should not trigger `dataChanged`.
				self.assertIsNone( model.data( valueIndex ) )
				self.assertEqual( len( changes ), 0 )
				# But the act of querying will have launched an async
				# update that should update the value and signal the
				# the change.
				_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( model ) )
				self.assertEqual( len( changes ), 1 )
				self.assertEqual( model.data( valueIndex ), 10 )

	def testModelChangingData( self ) :

		root = {
			"a" : 10,
		}

		widget = GafferUI.PathListingWidget(
			path = Gaffer.DictPath( root, "/" ),
			columns = [
				GafferUI.PathListingWidget.defaultNameColumn,
				GafferUI.PathListingWidget.StandardColumn( "Value", "dict:value" )
			],
		)
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( widget._qtWidget() ) )

		# Do initial query and wait for async update.

		model = widget._qtWidget().model()
		self.assertEqual( model.rowCount(), 0 )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( model ) )
		self.assertEqual( model.rowCount(), 1 )
		self.assertEqual( model.data( model.index( 0, 1, QtCore.QModelIndex() ) ), None )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( model ) )
		self.assertEqual( model.data( model.index( 0, 1, QtCore.QModelIndex() ) ), 10 )

		# Set up change tracking.

		changes = []
		def dataChanged( *args ) :
			changes.append( args )

		model.dataChanged.connect( dataChanged )

		# Change value in column 1. Check that `dataChanged` is emitted
		# and we can query the new value.

		root["a"] = 20
		self.__emitPathChanged( widget )
		self.assertEqual( len( changes ), 1 )
		self.assertEqual( model.data( model.index( 0, 1, QtCore.QModelIndex() ) ), 20 )

		# Trigger an artificial update and assert that the data has not changed,
		# and `dataChanged` has not been emitted.

		self.__emitPathChanged( widget )
		self.assertEqual( len( changes ), 1 )
		self.assertEqual( model.data( model.index( 0, 1, QtCore.QModelIndex() ) ), 20 )

	class InfinitePath( Gaffer.Path ) :

		# `self.visitedPaths` is a PathMatcher that will be filled with all the
		# children visited by the PathModel. Likewise `childrenCallPaths` is filled
		# with all the paths for which `_children()` is called.
		def __init__( self, path, root="/", filter=None, visitedPaths = None, childrenCallPaths = None ) :

			Gaffer.Path.__init__( self, path, root, filter=filter )

			self.visitedPaths = visitedPaths if visitedPaths is not None else IECore.PathMatcher()
			self.childrenCallPaths = childrenCallPaths if childrenCallPaths is not None else IECore.PathMatcher()

			self.visitedPaths.addPath( str( self ) )

		def isValid( self, canceller = None ) :

			return True

		def isLeaf( self, canceller = None ) :

			return False

		def copy( self ) :

			return PathListingWidgetTest.InfinitePath(
				self[:], self.root(), self.getFilter(), self.visitedPaths, self.childrenCallPaths
			)

		def _children( self, canceller = None ) :

			self.childrenCallPaths.addPath( str( self ) )

			return [
				PathListingWidgetTest.InfinitePath( self[:] + [ x ], self.root(), self.getFilter(), self.visitedPaths, self.childrenCallPaths )
				for x in [ "a", "b" ]
			]

	def testModelDoesntUpdateUnexpandedPaths( self ) :

		# Create an infinite model and expand it up to a fixed depth.

		path1 = self.InfinitePath( "/" )

		widget = GafferUI.PathListingWidget(
			path = path1,
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
		)

		# Not calling `_pathListingWidgetAttachTester()` for this test, as it
		# queries child items that would push us past our expected expansion depth.
		expansionDepth = 4
		self.__expandModel( widget._qtWidget().model(), depth = expansionDepth )
		self.assertEqual(
			max( len( p[1:].split( "/" ) ) for p in path1.visitedPaths.paths() ),
			expansionDepth
		)

		# Replace with a new path, to force the PathModel into evaluating
		# it to see if there are any changes. The PathModel should only
		# visit paths that have been visited before, because there is no
		# need to notify Qt of layout or data changes for items that haven't
		# been visited yet.

		path2 = self.InfinitePath( "/" )
		widget.setPath( path2 )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( widget._qtWidget().model() ) )

		self.assertEqual( path2.visitedPaths, path1.visitedPaths )

	def testChildrenAreCreatedWhenParentIsExpanded( self ) :

		# Create an infinite model and expand some specific parents.

		path = self.InfinitePath( "/" )

		widget = GafferUI.PathListingWidget(
			path = path,
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
		)

		widget.setExpansion( IECore.PathMatcher( [ "/", "/a", "/a/b" ] ) )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( widget._qtWidget().model() ) )

		# We want the children to have been created for those parents
		# during the first update, even without a specific query for
		# them. This means we're ready for the inevitable query from
		# the QTreeView without needing to launch a second update.

		self.assertEqual( path.childrenCallPaths, IECore.PathMatcher( [ "/", "/a", "/a/b" ] ) )

	def testLegacySelectionWithNonEmptyRootPath( self ) :

		d = { "a" : { "b" : 10 } }
		p = Gaffer.DictPath( d, "/a" )

		w = GafferUI.PathListingWidget( p )
		w.setSelectedPaths( [ p.copy().setFromString( "/a/b" ) ] )
		self.assertEqual( { str( s ) for s in w.getSelectedPaths() }, { "/a/b" } )

		d["a"]["c"] = 20
		p.pathChangedSignal()( p )

		w.setSelectedPaths( [ p.copy().setFromString( "/a/c" ) ] )
		self.assertEqual( { str( s ) for s in w.getSelectedPaths() }, { "/a/c" } )

	def testHidingCancellation( self ) :

		# Custom column that never returns from `cellData()`
		# (unless cancelled).
		class SleepingColumn( GafferUI.PathColumn ) :

			cellDataCalled = False

			def __init__( self ) :

				GafferUI.PathColumn.__init__( self )

			def cellData( self, path, canceller = None ) :

				SleepingColumn.cellDataCalled = True

				while True :
					time.sleep( 0.01 )
					IECore.Canceller.check( canceller )

			def headerData( self, canceller = None ) :

				return self.CellData( value = "Title" )

		with GafferUI.Window() as window :
			widget = GafferUI.PathListingWidget(
				Gaffer.DictPath( { "a" : 10 }, "/" ),
				columns = [
					GafferUI.PathListingWidget.defaultNameColumn,
					SleepingColumn(),
				]
			)

		# Trigger a background update by showing the widget.
		window.setVisible( True )
		self.waitForIdle( 20000 )
		self.assertTrue( SleepingColumn.cellDataCalled )

		# Cancel the update by hiding it.
		window.setVisible( False )

	def testColumnChangedOnlyDirtiesData( self ) :

		# Create an infinite model and expand it up to a fixed depth.

		childrenCallPaths = IECore.PathMatcher()
		path = self.InfinitePath( "/", childrenCallPaths = childrenCallPaths )

		widget = GafferUI.PathListingWidget(
			path = path,
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
			columns = [
				GafferUI.PathListingWidget.defaultNameColumn,
				GafferUI.PathListingWidget.StandardColumn( "Test", "test" )
			],
		)

		self.__expandModel( widget._qtWidget().model(), depth = 4 )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( widget._qtWidget().model() ) )
		self.assertFalse( childrenCallPaths.isEmpty() )

		# Simulate a column change. This should trigger an update, but shouldn't
		# need to reevaluate `path._children()` because columns only affect the
		# data in the model, not the hierarchy.

		childrenCallPaths.clear()
		widget.getColumns()[1].changedSignal()( widget.getColumns()[1] )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( widget._qtWidget().model() ) )
		self.assertTrue( childrenCallPaths.isEmpty() )

	def testColumnButtonPress( self ) :

		with GafferUI.Window() as window :
			widget = GafferUI.PathListingWidget(
				Gaffer.DictPath( { str( x ) : x for x in range( 0, 100 ) }, "/" ),
				columns = [ GafferUI.PathListingWidget.defaultNameColumn ],
			)

		cs = GafferTest.CapturingSlot( widget.getColumns()[0].buttonPressSignal() )

		window.setVisible( True )
		self.waitForIdle()
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( widget._qtWidget().model() ) )

		# Simulate click on PathListingWidget.

		center = widget.bound( window ).center()
		centerPath = widget.pathAt( center )
		self.assertIsInstance( centerPath, Gaffer.DictPath )

		widget.buttonPressSignal()(
			widget,
			GafferUI.ButtonEvent(
				GafferUI.ButtonEvent.Buttons.Left,
				GafferUI.ButtonEvent.Buttons.Left,
				IECore.LineSegment3f(
					imath.V3f( center.x, center.y, 0 ),
					imath.V3f( center.x, center.y, 1 ),
				)
			)
		)

		# Check that the column signal was emitted appropriately.

		self.assertEqual( len( cs ), 1 )
		self.assertEqual( cs[0][0], centerPath )
		self.assertIs( cs[0][1], widget )

	def testColumnSizeMode( self ) :

		columns = [
				GafferUI.PathListingWidget.defaultNameColumn,
				GafferUI.PathListingWidget.StandardColumn( "Test", "test", sizeMode = GafferUI.PathColumn.SizeMode.Interactive ),
				GafferUI.PathListingWidget.StandardColumn( "Test", "test", sizeMode = GafferUI.PathColumn.SizeMode.Stretch ),
			]

		widget = GafferUI.PathListingWidget(
			path = Gaffer.DictPath( {}, "/" ),
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
			columns = columns,
		)

		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( widget._qtWidget() ) )

		for i, c in enumerate( widget.getColumns() ) :
			self.assertEqual( columns[i].getSizeMode(), c.getSizeMode() )

		reorderedColumns = [ columns[1], columns[2], columns[0] ]
		widget.setColumns( reorderedColumns )

		for i, c in enumerate( widget.getColumns() ) :
			self.assertEqual( reorderedColumns[i].getSizeMode(), c.getSizeMode() )

	def testStretchLastColumnIsSetFromColumns( self ) :

		widget = GafferUI.PathListingWidget(
			path = Gaffer.DictPath( {}, "/" ),
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
			columns = [
				GafferUI.PathListingWidget.StandardColumn( "Test", "test", sizeMode = GafferUI.PathColumn.SizeMode.Stretch ),
				GafferUI.PathListingWidget.StandardColumn( "Test", "test" )
			],
		)
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( widget._qtWidget() ) )

		self.assertFalse( widget._qtWidget()._shouldStretchLastColumn() )
		widget.setColumns( [ GafferUI.PathListingWidget.StandardColumn( "Test", "test" ) ] )
		self.assertTrue( widget._qtWidget()._shouldStretchLastColumn() )

	def testModelNameSortingDoesntEmitDataChanged( self ) :

		path = self.InfinitePath( "/" )

		widget = GafferUI.PathListingWidget(
			path = path,
			displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
			sortable = False,
			columns = [
				GafferUI.PathListingWidget.defaultNameColumn,
				GafferUI.PathListingWidget.StandardColumn( "Test", "test" )
			],
		)

		expansionDepth = 4
		model = widget._qtWidget().model()

		self.__expandModel( model, depth = expansionDepth )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( model ) )

		changes = []
		def dataChanged( *args ) :
			changes.append( args )

		model.dataChanged.connect( dataChanged )

		# setting our widget to be sortable shouldn't result in any data changes
		# as we're sorting by the `name` column

		widget.setSortable( True )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( model ) )
		self.assertEqual( len( changes ), 0 )

		# by default we should be sorting by ascending order
		self.assertEqual( model.data( model.index( 0, 0 ) ), "a" )
		self.assertEqual( model.data( model.index( 1, 0 ) ), "b" )

		# likewise, changing the sort order of the `name` column shouldn't result
		# in data changes

		widget._qtWidget().header().setSortIndicator( 0, QtCore.Qt.DescendingOrder )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( model ) )
		self.assertEqual( len( changes ), 0 )

		# ensure descending sort order
		self.assertEqual( model.data( model.index( 0, 0 ) ), "b" )
		self.assertEqual( model.data( model.index( 1, 0 ) ), "a" )

		# but sorting by another column should result in data changes as we require
		# CellData to sort on

		widget._qtWidget().header().setSortIndicator( 1, QtCore.Qt.AscendingOrder )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( model ) )
		self.assertNotEqual( len( changes ), 0 )

		# The Test column has no data to sort on, so we return to the original ordering
		self.assertEqual( model.data( model.index( 0, 0 ) ), "a" )
		self.assertEqual( model.data( model.index( 1, 0 ) ), "b" )

	@staticmethod
	def __emitPathChanged( widget ) :

		widget.getPath().pathChangedSignal()( widget.getPath() )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( widget._qtWidget().model() ) )

	@classmethod
	def __expandModel( cls, model, index = None, queryData = False, depth = 10 ) :

		if depth <= 0 :
			return

		index = index if index is not None else QtCore.QModelIndex()
		model.rowCount( index )
		if queryData :
			model.data( index )
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( model ) )

		for row in range( 0, model.rowCount( index ) ) :
			cls.__expandModel( model, model.index( row, 0, index ), queryData, depth - 1 )

	@staticmethod
	def __expansionFromQt( widget ) :

		result = IECore.PathMatcher()
		for index in widget._qtWidget().model().persistentIndexList() :
			if widget._qtWidget().isExpanded( index ) :
				result.addPath(
					str( widget._PathListingWidget__pathForIndex( index ) )
				)

		return result

if __name__ == "__main__":
	unittest.main()
