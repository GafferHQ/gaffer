##########################################################################
#
#  Copyright (c) 2011-2013, John Haddon. All rights reserved.
#  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
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

import GafferUI
import GafferUITest

class TabbedContainerTest( GafferUITest.TestCase ) :

	def test( self ) :

		t = GafferUI.TabbedContainer()
		self.assertEqual( len( t ), 0 )

		self.assertEqual( t.getCurrent(), None )

		c = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )

		t.append( c )
		self.assertEqual( len( t ), 1 )
		self.assert_( t[0] is c )
		self.assert_( t.getCurrent() is c )

	def testOwner( self ) :

		t = GafferUI.TabbedContainer()

		self.failUnless( GafferUI.Widget._owner( t._qtWidget() ) is t )

	def testCornerWidget( self ) :

		t = GafferUI.TabbedContainer()
		self.failUnless( t.getCornerWidget() is None )

		b = GafferUI.Button( "baby" )
		t.setCornerWidget( b )
		self.failUnless( t.getCornerWidget() is b )
		self.failUnless( b.parent() is t )

		b2 = GafferUI.Button( "b" )
		t.setCornerWidget( b2 )
		self.failUnless( t.getCornerWidget() is b2 )
		self.failUnless( b2.parent() is t )
		self.failUnless( b.parent() is None )

	def testIndex( self ) :

		t = GafferUI.TabbedContainer()
		b1 = GafferUI.Button()
		b2 = GafferUI.Button()

		t.append( b1 )
		t.append( b2 )

		self.assertEqual( t.index( b1 ), 0 )
		self.assertEqual( t.index( b2 ), 1 )

		b3 = GafferUI.Button()

		self.assertRaises( ValueError, t.index, b3 )

	def testMoveTracking( self ) :

		t = GafferUI.TabbedContainer()
		t._qtWidget().tabBar().setMovable( True )

		b1 = GafferUI.Button()
		b2 = GafferUI.Button()
		b3 = GafferUI.Button()

		t.append( b1 )
		t.append( b2 )
		t.append( b3 )

		self.assertEqual( t.index( b1 ), 0 )
		self.assertEqual( t.index( b2 ), 1 )
		self.assertEqual( t.index( b3 ), 2 )

		t._qtWidget().tabBar().moveTab( 0, 1 )

		self.assertEqual( t.index( b1 ), 1 )
		self.assertEqual( t.index( b2 ), 0 )
		self.assertEqual( t.index( b3 ), 2 )

		t._qtWidget().tabBar().moveTab( 2, 0 )

		self.assertEqual( t.index( b1 ), 2 )
		self.assertEqual( t.index( b2 ), 1 )
		self.assertEqual( t.index( b3 ), 0 )

	def testCurrentChangedSignal( self ) :

		tc = GafferUI.TabbedContainer()

		def s( t, c ) :

			self.failUnless( t is tc )
			self.__current = c

		c = tc.currentChangedSignal().connect( s )
		self.__current = None

		self.failUnless( tc.getCurrent() is None )

		b1 = GafferUI.Button()
		tc.append( b1 )
		self.failUnless( self.__current is b1 )
		self.failUnless( tc.getCurrent() is b1 )

		b2 = GafferUI.Button()
		tc.append( b2 )
		self.failUnless( self.__current is b1 )
		self.failUnless( tc.getCurrent() is b1 )

		tc.setCurrent( b2 )
		self.failUnless( self.__current is b2 )
		self.failUnless( tc.getCurrent() is b2 )

		tc.remove( b1 )
		self.failUnless( self.__current is b2 )
		self.failUnless( tc.getCurrent() is b2 )

		tc.remove( b2 )
		self.failUnless( self.__current is None )
		self.failUnless( tc.getCurrent() is None )

	def testDel( self ) :

		with GafferUI.TabbedContainer() as t :

			b1 = GafferUI.Button()
			b2 = GafferUI.Button()
			b3 = GafferUI.Button()

		self.assertEqual( len( t ), 3 )
		for b in ( b1, b2, b3 ) :
			self.failUnless( b.parent() is t )

		del t[0]
		self.assertEqual( len( t ), 2 )
		for b in ( b2, b3 ) :
			self.failUnless( b.parent() is t )
		self.failUnless( b1.parent() is None )

		del t[:]
		self.assertEqual( len( t ), 0 )
		for b in ( b1, b2, b3 ) :
			self.failUnless( b.parent() is None )

	def testTabsVisible( self ) :

		t = GafferUI.TabbedContainer()
		self.assertEqual( t.getTabsVisible(), True )

		t.setTabsVisible( False )
		self.assertEqual( t.getTabsVisible(), False )

		t.setTabsVisible( True )
		self.assertEqual( t.getTabsVisible(), True )

	def testParent( self ) :

		t = GafferUI.TabbedContainer()
		b = GafferUI.Button()

		t.append( b )
		self.assertEqual( b.parent(), t )

	def testVisibilityWhenTransferringWidgets( self ) :

		t = GafferUI.TabbedContainer()
		b = GafferUI.Button()
		l = GafferUI.ListContainer()

		l.append( b )
		self.assertEqual( b.parent(), l )
		self.assertEqual( b.getVisible(), True )

		t.append( b )
		self.assertEqual( len( l ), 0 )
		self.assertEqual( b.parent(), t )
		self.assertEqual( b.getVisible(), True )

	def testTransferCornerWidget( self ) :

		t = GafferUI.TabbedContainer()
		l = GafferUI.ListContainer()
		b = GafferUI.Button()

		l.append( b )
		self.assertEqual( len( l ), 1 )
		self.assertEqual( b.parent(), l )

		t.setCornerWidget( b )
		self.assertEqual( len( l ), 0 )
		self.assertEqual( b.parent(), t )

	def testInsert( self ) :

		t = GafferUI.TabbedContainer()

		b1 = GafferUI.Button()
		b2 = GafferUI.Button()
		b3 = GafferUI.Button()

		t.insert( 0, b1, "B1" )
		self.assertTrue( t[0] is b1 )
		self.assertEqual( t.index( b1 ), 0 )
		self.assertEqual( t.getLabel( b1 ), "B1" )

		t.insert( 1, b2, "B2" )
		self.assertTrue( t[0] is b1 )
		self.assertTrue( t[1] is b2 )
		self.assertEqual( t.index( b1 ), 0 )
		self.assertEqual( t.index( b2 ), 1 )
		self.assertEqual( t.getLabel( b1 ), "B1" )
		self.assertEqual( t.getLabel( b2 ), "B2" )

		t.insert( 1, b3, "B3" )
		self.assertTrue( t[0] is b1 )
		self.assertTrue( t[1] is b3 )
		self.assertTrue( t[2] is b2 )
		self.assertEqual( t.index( b1 ), 0 )
		self.assertEqual( t.index( b2 ), 2 )
		self.assertEqual( t.index( b3 ), 1 )
		self.assertEqual( t.getLabel( b1 ), "B1" )
		self.assertEqual( t.getLabel( b2 ), "B2" )
		self.assertEqual( t.getLabel( b3 ), "B3" )

	def testLabellingDuringAutoParenting( self ) :

		with GafferUI.TabbedContainer() as t :

			one = GafferUI.ListContainer( parenting = { "label" : "One" } )
			two = GafferUI.ListContainer( parenting = { "label" : "Two" } )

		self.assertEqual( t.getLabel( one ), "One" )
		self.assertEqual( t.getLabel( two ), "Two" )

	def testReveal( self ) :

		with GafferUI.TabbedContainer() as t1 :
			with GafferUI.TabbedContainer() as t2 :
				with GafferUI.ListContainer() as c1 :
					l1 = GafferUI.Label( "l1" )
				with GafferUI.ListContainer() as c2 :
					l2 = GafferUI.Label( "l2" )
			with GafferUI.TabbedContainer() as t3 :
				with GafferUI.ListContainer() as c3 :
					l3 = GafferUI.Label( "l3" )
				with GafferUI.ListContainer() as c4 :
					l4 = GafferUI.Label( "l4" )

		l1.reveal()
		self.assertTrue( t1.getCurrent() is t2 )
		self.assertTrue( t2.getCurrent() is c1 )

		l3.reveal()
		self.assertTrue( t1.getCurrent() is t3 )
		self.assertTrue( t3.getCurrent() is c3 )

	def tearDown( self ) :

		self.__current = None
		GafferUITest.TestCase.tearDown( self )

if __name__ == "__main__":
	unittest.main()
