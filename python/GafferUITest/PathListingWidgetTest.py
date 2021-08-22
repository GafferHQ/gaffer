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

import IECore

import Gaffer
import GafferTest

import GafferUI
from GafferUI import _GafferUI
import GafferUITest

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

		w = GafferUI.PathListingWidget( p )
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )

		self.assertTrue( w.getExpansion().isEmpty() )

		cs = GafferTest.CapturingSlot( w.expansionChangedSignal() )
		e = IECore.PathMatcher( [ "/1", "/2", "/2" ] )

		w.setExpansion( e )
		self.assertEqual( w.getExpansion(), e )
		self.assertEqual( len( cs ), 1 )

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

		w = GafferUI.PathListingWidget( p, allowMultipleSelection = True )
		_GafferUI._pathListingWidgetAttachTester( GafferUI._qtAddress( w._qtWidget() ) )
		self.assertTrue( w.getSelection().isEmpty() )

		cs = GafferTest.CapturingSlot( w.selectionChangedSignal() )
		s = IECore.PathMatcher( [ "/1", "/2/5", "/3/1" ] )

		w.setSelection( s )
		self.assertEqual( w.getSelection(), s )
		self.assertEqual( len( cs ), 1 )

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

if __name__ == "__main__":
	unittest.main()
