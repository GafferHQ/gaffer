##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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
import GafferUITest

from Qt import QtWidgets

class TestWidget( GafferUI.Widget ) :

	def __init__( self, s, **kw ) :

		GafferUI.Widget.__init__( self, QtWidgets.QLabel( s ), **kw )

		self.s = s

class ListContainerTest( GafferUITest.TestCase ) :

	def testConstruction( self ) :

		c = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		self.assertEqual( c.orientation(), GafferUI.ListContainer.Orientation.Vertical )
		self.assertEqual( len( c ), 0 )

		c = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )
		self.assertEqual( c.orientation(), GafferUI.ListContainer.Orientation.Horizontal )
		self.assertEqual( len( c ), 0 )

	def testItems( self ) :

		c = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		self.assertEqual( len( c ), 0 )

		ca = TestWidget( "a" )
		cb = TestWidget( "b" )
		cc = TestWidget( "c" )
		self.assertIsNone( ca.parent() )
		self.assertIsNone( cb.parent() )
		self.assertIsNone( cc.parent() )

		c.append( ca )
		self.assertEqual( len( c ), 1 )
		self.assertEqual( c[0], ca )
		self.assertTrue( ca.parent() is c )

		c.append( cb )
		self.assertEqual( len( c ), 2 )
		self.assertEqual( c[0], ca )
		self.assertEqual( c[1], cb )
		self.assertTrue( ca.parent() is c )
		self.assertTrue( cb.parent() is c )

		c.append( cc )
		self.assertEqual( len( c ), 3 )
		self.assertEqual( c[0], ca )
		self.assertEqual( c[1], cb )
		self.assertEqual( c[2], cc )
		self.assertTrue( ca.parent() is c )
		self.assertTrue( cb.parent() is c )
		self.assertTrue( cc.parent() is c )

		del c[0]
		self.assertEqual( len( c ), 2 )
		self.assertIsNone( ca.parent() )
		self.assertTrue( cb.parent() is c )
		self.assertTrue( cc.parent() is c )
		self.assertEqual( c[0], cb )
		self.assertEqual( c[1], cc )

		c.remove( cc )
		self.assertEqual( len( c ), 1 )
		self.assertIsNone( ca.parent() )
		self.assertTrue( cb.parent() is c )
		self.assertIsNone( cc.parent() )
		self.assertEqual( c[0], cb )

	def testReparenting( self ) :

		c1 = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		self.assertEqual( len( c1 ), 0 )
		c2 = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		self.assertEqual( len( c2 ), 0 )

		ca = TestWidget( "a" )
		self.assertIsNone( ca.parent() )

		c1.append( ca )
		self.assertTrue( ca.parent() is c1 )
		self.assertEqual( len( c1 ), 1 )
		self.assertEqual( len( c2 ), 0 )
		c2.append( ca )
		self.assertTrue( ca.parent() is c2 )
		self.assertEqual( len( c1 ), 0 )
		self.assertEqual( len( c2 ), 1 )

	def testSliceDel( self ) :

		c = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )

		ca = TestWidget( "a" )
		cb = TestWidget( "b" )
		cc = TestWidget( "c" )
		self.assertIsNone( ca.parent() )
		self.assertIsNone( cb.parent() )
		self.assertIsNone( cc.parent() )

		c.append( ca )
		self.assertTrue( ca.parent() is c )

		c.append( cb )
		self.assertTrue( cb.parent() is c )

		c.append( cc )
		self.assertTrue( cc.parent() is c )

		self.assertEqual( len( c ), 3 )

		del c[0:2]
		self.assertEqual( len( c ), 1 )
		self.assertIsNone( ca.parent() )
		self.assertIsNone( cb.parent() )
		self.assertTrue( cc.parent() is c )

	def testSliceDelWithOpenRange( self ) :

		c = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		with c :
			ca = TestWidget( "a" )
			cb = TestWidget( "b" )
			cc = TestWidget( "c" )

		self.assertEqual( c[:], [ ca, cb, cc ] )

		del c[:2]

		self.assertEqual( c[:], [ cc ] )

	def testEnabled( self ) :

		c = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		w = TestWidget( "a" )
		c.append( w )

		self.assertEqual( c.getEnabled(), True )
		self.assertEqual( c.enabled(), True )
		self.assertEqual( w.getEnabled(), True )
		self.assertEqual( w.enabled(), True )

		c.setEnabled( False )

		self.assertEqual( c.getEnabled(), False )
		self.assertEqual( c.enabled(),False )

		self.assertEqual( w.enabled(), False )
		self.assertEqual( w.getEnabled(), True ) # because it's not explicitly disabled

		w.setEnabled( True ) # changes nothing because the disabled state is on the parent
		self.assertEqual( w.enabled(), False )
		self.assertEqual( w.getEnabled(), True )

		c.setEnabled( True )

		self.assertEqual( c.enabled(), True )
		self.assertEqual( c.getEnabled(), True )
		self.assertEqual( w.enabled(), True )
		self.assertEqual( w.getEnabled(), True )

	def testSliceGetItem( self ) :

		c = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		with c :
			ca = TestWidget( "a" )
			cb = TestWidget( "b" )
			cc = TestWidget( "c" )

		self.assertEqual( c[:2], [ ca, cb ] )

	def testSetItem( self ) :

		c = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		with c :
			ca = TestWidget( "a" )
			cb = TestWidget( "b" )
			cc = TestWidget( "c" )

		self.assertEqual( c[:], [ ca, cb, cc ] )
		self.assertEqual( c.index( ca ), 0 )
		self.assertEqual( c.index( cb ), 1 )
		self.assertEqual( c.index( cc ), 2 )
		self.assertRaises( ValueError, c.index, c )

		cd = TestWidget( "d" )

		c[0] = cd

		self.assertEqual( c[:], [ cd, cb, cc ] )
		self.assertEqual( c.index( cd ), 0 )
		self.assertEqual( c.index( cb ), 1 )
		self.assertEqual( c.index( cc ), 2 )
		self.assertRaises( ValueError, c.index, ca )

		self.assertIsNone( ca.parent() )
		self.assertTrue( cb.parent() is c )
		self.assertTrue( cc.parent() is c )
		self.assertTrue( cd.parent() is c )

	def testSliceSetItem( self ) :

		c = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		with c :
			ca = TestWidget( "a" )
			cb = TestWidget( "b" )
			cc = TestWidget( "c" )

		self.assertEqual( c[:], [ ca, cb, cc ] )

		cd = TestWidget( "d" )
		ce = TestWidget( "e" )

		c[:2] = [ cd, ce ]

		self.assertEqual( c[:], [ cd, ce, cc ] )

		self.assertIsNone( ca.parent() )
		self.assertIsNone( cb.parent() )
		self.assertTrue( cd.parent() is c )
		self.assertTrue( ce.parent() is c )
		self.assertTrue( cc.parent() is c )

	def testSliceSetItemOnEmptyContainer( self ) :

		c = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		ca = TestWidget( "a" )

		c[:] = [ ca ]
		self.assertEqual( c[:], [ ca ] )

	def testSliceSetItemWithEmptySlice( self ) :

		c = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )

		with c :
			ca = TestWidget( "a" )
			cb = TestWidget( "b" )

		self.assertEqual( c[:], [ ca, cb ] )

		cc = TestWidget( "c" )
		cd = TestWidget( "d" )

		c[1:1] = [ cc, cd ]

		self.assertEqual( c[:], [ ca, cc, cd, cb ] )

	def testExpand( self ) :

		c = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		with c :
			ca = TestWidget( "a" )
			cb = TestWidget( "b", parenting = { "expand" : True } )
			cc = TestWidget( "c", parenting = { "expand" : True } )

		self.assertEqual( c.getExpand( ca ), False )
		self.assertEqual( c.getExpand( cb ), True )
		self.assertEqual( c.getExpand( cc ), True )

		c.setExpand( ca, True )
		c.setExpand( cb, False )

		self.assertEqual( c.getExpand( ca ), True )
		self.assertEqual( c.getExpand( cb ), False )
		self.assertEqual( c.getExpand( cc ), True )

		# setItem should keep the expand status for the new widget
		cd = TestWidget( "d" )
		c[0] = cd

		self.assertEqual( c.getExpand( cd ), True )
		self.assertEqual( c.getExpand( cb ), False )
		self.assertEqual( c.getExpand( cc ), True )

	def testDelDoesntAffectSubChildren( self ) :

		c1 = GafferUI.ListContainer()
		c2 = GafferUI.ListContainer()
		b = GafferUI.Button()

		c2.append( b )
		self.assertEqual( len( c2 ), 1 )

		c1.append( c2 )
		self.assertEqual( len( c1 ), 1 )

		del c1[:]
		self.assertEqual( len( c1 ), 0 )
		self.assertEqual( len( c2 ), 1 )
		self.assertTrue( b.parent() is c2 )

	def testDelDoesntAffectVisibility( self ) :

		with GafferUI.Window() as w :
			with GafferUI.ListContainer() as l :
				b = GafferUI.Button()

		self.assertEqual( b.getVisible(), True )
		del l[:]

		l2 = GafferUI.ListContainer()
		l2.append( b )
		self.assertEqual( b.getVisible(), True )

	def testFocusOrder( self ) :

		l = GafferUI.ListContainer()

		c = []
		for i in range( 0, 10 ) :
			c.append( GafferUI.TextWidget() )

		l[:] = c

		for i in range( 0, 9 ) :
			self.assertTrue( l[i]._qtWidget().nextInFocusChain() is l[i+1]._qtWidget() )

	def testSliceSetItemAtEnd( self ) :

		c = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		c.append( TestWidget( "a" ) )

		c[1:] = [ TestWidget( "b" ) ]
		self.assertEqual( c[0].s, "a" )
		self.assertEqual( c[1].s, "b" )

if __name__ == "__main__":
	unittest.main()
