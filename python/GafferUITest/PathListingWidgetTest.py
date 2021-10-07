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

		with GafferUI.Window() as window :
			w = GafferUI.PathListingWidget( p, displayMode = GafferUI.PathListingWidget.DisplayMode.Tree )
			_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )
		window.setVisible( True )

		self.assertTrue( w.getExpansion().isEmpty() )

		cs = GafferTest.CapturingSlot( w.expansionChangedSignal() )
		e = IECore.PathMatcher( [ "/1", "/2", "/2/4", "/1/5", "/3" ] )

		w.setExpansion( e )
		self.assertEqual( w.getExpansion(), e )
		self.assertEqual( len( cs ), 1 )

		del d["2"]
		p.pathChangedSignal()( p )
		self.waitForIdle( 100 )

		e.removePath( "/2" )
		e.removePath( "/2/4" )
		self.assertEqual( w.getExpansion(), e )

		w.setPath( Gaffer.DictPath( {}, "/" ) )
		self.assertTrue( w.getExpansion().isEmpty() )

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

	def testSelection( self ) :

		d = {}
		for i in range( 0, 10 ) :
			dd = {}
			for j in range( 0, 10 ) :
				dd[str(j)] = j
			d[str(i)] = dd

		p = Gaffer.DictPath( d, "/" )

		with GafferUI.Window() as window :
			w = GafferUI.PathListingWidget( p, allowMultipleSelection = True, displayMode = GafferUI.PathListingWidget.DisplayMode.Tree )
			_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )
		window.setVisible( True )

		self.assertTrue( w.getSelection().isEmpty() )

		cs = GafferTest.CapturingSlot( w.selectionChangedSignal() )
		s = IECore.PathMatcher( [ "/1", "/2", "/9", "/2/5", "/3/1" ] )

		w.setSelection( s )
		self.assertEqual( w.getSelection(), s )
		self.assertEqual( len( cs ), 1 )

		del d["2"]
		p.pathChangedSignal()( p )
		self.waitForIdle( 100 )

		s.removePath( "/2" )
		s.removePath( "/2/5" )
		self.assertEqual( w.getSelection(), s )

		w.setPath( Gaffer.DictPath( {}, "/" ) )
		self.assertTrue( w.getSelection().isEmpty() )

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
		w = GafferUI.PathListingWidget( p, allowMultipleSelection=True )
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )

		c = GafferTest.CapturingSlot( w.selectionChangedSignal() )
		self.assertEqual( len( c ), 0 )

		w.setSelectedPaths( [ Gaffer.DictPath( d, "/a" ), Gaffer.DictPath( d, "/b" ) ] )
		self.assertEqual( set( [ str( p ) for p in w.getSelectedPaths() ] ), set( [ "/a", "/b" ] ) )

		self.assertEqual( len( c ), 1 )

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

		# fake a change to the path
		p.pathChangedSignal()( p )

		# because the PathListingWidget only updates on idle events, we have
		# to run the event loop to get it to process the path changed signal.
		self.waitForIdle( 100 )

		# once it has processed things, the expansion should be exactly as it was.
		self.assertEqual( w.getPathExpanded( p1 ), True )

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

		# fake a change to the path
		p.pathChangedSignal()( p )

		# because the PathListingWidget only updates on idle events, we have
		# to run the event loop to get it to process the path changed signal.
		self.waitForIdle( 100 )

		# once it has processed things, the expansion should be exactly as it was.
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
		with GafferUI.Window() as window :
			widget = GafferUI.PathListingWidget(
				path,
				columns = [ GafferUI.PathListingWidget.defaultNameColumn ],
				sortable = False,
				displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
			)
			_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( widget._qtWidget() ) )
		window.setVisible( True )

		model = widget._qtWidget().model()
		self.assertEqual( model.rowCount(), 1 )
		self.assertEqual( model.columnCount(), 1 )

		# If we add a new child to the path, it should appear in the
		# model. And if we have a persistent index for the original child, that
		# should remain valid.
		aIndex = QtCore.QPersistentModelIndex( model.index( 0, 0 ) )
		root["b"] = Gaffer.GraphComponent()
		path.pathChangedSignal()( path )
		self.waitForIdle()

		self.assertEqual( model.rowCount(), 2 )
		self.assertEqual( model.columnCount(), 1 )
		self.assertTrue( aIndex.isValid() )
		self.assertEqual( aIndex.row(), 0 )

		# If we delete `a`, it should be gone from the model, but a
		# persistent index to `b` should remain valid.
		bIndex = QtCore.QPersistentModelIndex( model.index( 1, 0 ) )
		del root["a"]
		path.pathChangedSignal()( path )
		self.waitForIdle()

		self.assertEqual( model.rowCount(), 1 )
		self.assertEqual( model.columnCount(), 1 )
		self.assertFalse( aIndex.isValid() )
		self.assertTrue( bIndex.isValid() )
		self.assertEqual( model.rowCount( bIndex ), 0 )

		# If we add a child to `b`, the model should update to reflect
		# that too.
		root["b"]["c"] = Gaffer.GraphComponent()
		path.pathChangedSignal()( path )
		self.waitForIdle()

		self.assertTrue( bIndex.isValid() )
		self.assertEqual( model.rowCount( bIndex ), 1 )
		self.assertEqual( model.columnCount( bIndex ), 1 )
		self.assertEqual( model.data( model.index( 0, 0, bIndex ) ), "c" )

		# Likewise, we should be able to add and remove children from `c`
		# and see it reflected in the model.
		cIndex = QtCore.QPersistentModelIndex( model.index( 0, 0, bIndex ) )
		self.assertEqual( model.data( cIndex ), "c" )
		self.assertEqual( model.rowCount( cIndex ), 0 )

		root["b"]["c"]["d"] = Gaffer.GraphComponent()
		path.pathChangedSignal()( path )
		self.waitForIdle()

		self.assertTrue( cIndex.isValid() )
		self.assertEqual( model.rowCount( cIndex ), 1 )
		self.assertEqual( model.columnCount( cIndex ), 1 )
		self.assertEqual( model.data( model.index( 0, 0, cIndex ) ), "d" )

		dIndex = QtCore.QPersistentModelIndex( model.index( 0, 0, cIndex ) )
		del root["b"]["c"]["d"]
		path.pathChangedSignal()( path )
		self.waitForIdle()
		self.assertTrue( cIndex.isValid() )
		self.assertEqual( model.rowCount( cIndex ), 0 )
		self.assertFalse( dIndex.isValid() )

	def testModelSorting( self ) :

		# Make a widget with sorting enabled.

		root = Gaffer.GraphComponent()
		root["c"] = Gaffer.GraphComponent()
		root["b"] = Gaffer.GraphComponent()

		path = Gaffer.GraphComponentPath( root, "/" )
		with GafferUI.Window() as window :
			widget = GafferUI.PathListingWidget( path, columns = [ GafferUI.PathListingWidget.defaultNameColumn ], sortable = True )
			_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( widget._qtWidget() ) )
		window.setVisible( True )

		model = widget._qtWidget().model()
		self.assertEqual( model.rowCount(), 2 )
		self.assertEqual( model.columnCount(), 1 )

		# Check that the paths appear in sorted order.

		self.assertEqual( model.data( model.index( 0, 0 ) ), "b" )
		self.assertEqual( model.data( model.index( 1, 0 ) ), "c" )
		bIndex = QtCore.QPersistentModelIndex( model.index( 0, 0 ) )
		cIndex = QtCore.QPersistentModelIndex( model.index( 1, 0 ) )

		# And sorting is maintained when adding another path.

		root["a"] = Gaffer.GraphComponent()
		path.pathChangedSignal()( path )
		self.waitForIdle()

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

		# Make a widget showing a small hierarchy.

		root1 = Gaffer.GraphComponent()
		root1["c"] = Gaffer.GraphComponent()
		root1["c"]["d"] = Gaffer.GraphComponent()

		with GafferUI.Window() as window :
			widget = GafferUI.PathListingWidget(
				path = Gaffer.GraphComponentPath( root1, "/" ),
				columns = [ GafferUI.PathListingWidget.defaultNameColumn ],
			)
			_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( widget._qtWidget() ) )
		window.setVisible( True )

		path = Gaffer.GraphComponentPath( root1, "/" )
		self.assertEqual( path.property( "graphComponent:graphComponent" ), root1 )
		path.append( "c" )
		self.assertEqual( path.property( "graphComponent:graphComponent" ), root1["c"] )
		path.append( "d" )
		self.assertEqual( path.property( "graphComponent:graphComponent" ), root1["c"]["d"] )

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

		model = widget._qtWidget().model()
		dIndex = model.index( 0, 0, model.index( 0, 0 ) )
		assertIndexRefersTo( dIndex, root1["c"]["d"] )
		persistentDIndex = QtCore.QPersistentModelIndex( dIndex )
		assertIndexRefersTo( persistentDIndex, root1["c"]["d"] )

		# Replace the path with another one referencing an identical hierarchy.

		root2 = Gaffer.GraphComponent()
		root2["c"] = Gaffer.GraphComponent()
		root2["c"]["d"] = Gaffer.GraphComponent()

		widget.setPath( Gaffer.GraphComponentPath( root2, "/" ) )
		self.waitForIdle()

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

		with GafferUI.Window() as window :
			widget = GafferUI.PathListingWidget(
				path = Gaffer.GraphComponentPath( root, "/" ),
				columns = [ GafferUI.PathListingWidget.defaultNameColumn ],
			)
			_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( widget._qtWidget() ) )
			widget.setExpansion( IECore.PathMatcher( [ "/", "/c", "/c/d" ] ) )
		window.setVisible( True )

		# Fake a change to the path. Since nothing has truly changed,
		# the model should not signal any changes.

		changes = []
		def changed( *args ) :
			changes.append( args )

		widget._qtWidget().model().layoutChanged.connect( functools.partial( changed ) )
		widget._qtWidget().model().dataChanged.connect( functools.partial( changed ) )

		widget.getPath().pathChangedSignal()( widget.getPath() )
		self.waitForIdle()
		self.assertEqual( changes, [] )

	def testModelFirstQueryDoesntEmitDataChanged( self ) :

		for sortable in ( False, True ) :

			with GafferUI.Window() as window :
				widget = GafferUI.PathListingWidget(
					path = Gaffer.DictPath( { "c" : { "v" : 10 } }, "/" ),
					columns = [
						GafferUI.PathListingWidget.defaultNameColumn,
						GafferUI.PathListingWidget.StandardColumn( "Value", "dict:value" )
					],
					sortable = sortable
				)
				_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( widget._qtWidget() ) )
			window.setVisible( True )
			self.waitForIdle()

			changes = []
			def dataChanged( *args ) :
				changes.append( args )

			model = widget._qtWidget().model()
			model.dataChanged.connect( dataChanged )

			# We are testing a nested `dict["c"]["v"]` value because
			# the PathListingWidget will query the root items during
			# construction, and we want to be the first to query the
			# value.
			valueIndex = model.index( 0, 1, model.index( 0, 0 ) )
			self.assertEqual( model.data( valueIndex ), 10 )
			self.assertEqual( len( changes ), 0 )

	def testModelChangingData( self ) :

		root = {
			"a" : 10,
		}

		with GafferUI.Window() as window :
			widget = GafferUI.PathListingWidget(
				path = Gaffer.DictPath( root, "/" ),
				columns = [
					GafferUI.PathListingWidget.defaultNameColumn,
					GafferUI.PathListingWidget.StandardColumn( "Value", "dict:value" )
				],
			)
			_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( widget._qtWidget() ) )
		window.setVisible( True )

		model = widget._qtWidget().model()
		self.assertEqual( model.data( model.index( 0, 1, QtCore.QModelIndex() ) ), 10 )

		changes = []
		def dataChanged( *args ) :
			changes.append( args )

		model.dataChanged.connect( dataChanged )

		# Change value in column 1. Check that `dataChanged` is emitted
		# and we can query the new value.

		root["a"] = 20
		widget.getPath().pathChangedSignal()( widget.getPath() )
		self.waitForIdle()
		self.assertEqual( len( changes ), 1 )
		self.assertEqual( model.data( model.index( 0, 1, QtCore.QModelIndex() ) ), 20 )

		# Trigger an artificial update and assert that the data has not changed,
		# and `dataChanged` has not been emitted.

		widget.getPath().pathChangedSignal()( widget.getPath() )
		self.waitForIdle()
		self.assertEqual( len( changes ), 1 )
		self.assertEqual( model.data( model.index( 0, 1, QtCore.QModelIndex() ) ), 20 )

	def testModelDoesntUpdateUnexpandedPaths( self ) :

		class InfinitePath( Gaffer.Path ) :

			# `self.visitedPaths` is a PathMatcher that will be filled with all the
			# children visited by the PathModel.
			def __init__( self, path, root="/", filter=None, visitedPaths = None ) :

				Gaffer.Path.__init__( self, path, root, filter=filter )

				self.visitedPaths = visitedPaths if visitedPaths is not None else IECore.PathMatcher()
				self.visitedPaths.addPath( str( self ) )

			def isValid( self ) :

				return True

			def isLeaf( self ) :

				return False

			def copy( self ) :

				return InfinitePath( self[:], self.root(), self.getFilter(), self.visitedPaths )

			def _children( self ) :

				return [ InfinitePath( self[:] + [ x ], self.root(), self.getFilter(), self.visitedPaths ) for x in [ "a", "b" ] ]

		# Show the window with a small set of expanded paths.

		path1 = InfinitePath( "/" )

		with GafferUI.Window() as window :
			widget = GafferUI.PathListingWidget(
				path = path1,
				displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
			)
			_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( widget._qtWidget() ) )

		widget.setExpansion( IECore.PathMatcher( [
			"/", "/a/b", "/a/b/b", "/a/a/a"
		] ) )
		window.setVisible( True )
		self.waitForIdle()

		# Replace with a new path, to force the PathModel into evaluating
		# it to see if there are any changes. The PathModel should only
		# visit paths that have been visited before, because there is no
		# need to notify Qt of layout or data changes for items that haven't
		# been visited yet.

		path2 = InfinitePath( "/" )
		widget.setPath( path2 )
		self.waitForIdle()

		self.assertEqual( path2.visitedPaths, path1.visitedPaths )

if __name__ == "__main__":
	unittest.main()
