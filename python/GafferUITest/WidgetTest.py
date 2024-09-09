##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2015, Image Engine Design Inc. All rights reserved.
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
import weakref
import sys
import imath
import os

import IECore

import Gaffer
import GafferTest

import GafferUI
import GafferUITest

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

class TestWidget( GafferUI.Widget ) :

	def __init__( self, **kw ) :

		GafferUI.Widget.__init__( self, QtWidgets.QLabel( "hello" ), **kw )

class TestWidget2( GafferUI.Widget ) :

	def __init__( self ) :

		self.topLevelGafferWidget = TestWidget()

		GafferUI.Widget.__init__( self, self.topLevelGafferWidget )

class WidgetTest( GafferUITest.TestCase ) :

	def testOwner( self ) :

		w = TestWidget()
		self.assertTrue( GafferUI.Widget._owner( w._qtWidget() ) is w )

	def testParent( self ) :

		w = TestWidget()
		self.assertIsNone( w.parent() )

	def testCanDie( self ) :

		w = TestWidget()

		wr1 = weakref.ref( w )
		wr2 = weakref.ref( w._qtWidget() )

		del w
		self.assertIsNone( wr1() )
		self.assertIsNone( wr2() )

	def testAncestor( self ) :

		w = GafferUI.Window( "test" )
		l = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		p = GafferUI.SplitContainer()
		l.append( p )

		w.setChild( l )

		self.assertTrue( p.ancestor( GafferUI.ListContainer ) is l )
		self.assertTrue( p.ancestor( GafferUI.Window ) is w )
		self.assertIsNone( p.ancestor( GafferUI.Menu ) )

	def testIsAncestorOf( self ) :

		with GafferUI.Window( "test" ) as w :
			with GafferUI.SplitContainer() as p :
				with GafferUI.ListContainer() as l1 :
					b1 = GafferUI.Button()
				with GafferUI.ListContainer() as l2 :
					b2 = GafferUI.Button()

		self.assertTrue( l2.isAncestorOf( b2 ) )
		self.assertFalse( l1.isAncestorOf( b2 ) )
		self.assertTrue( p.isAncestorOf( b2 ) )
		self.assertTrue( w.isAncestorOf( b2 ) )

		self.assertFalse( b2.isAncestorOf( b1 ) )
		self.assertFalse( b2.isAncestorOf( l1 ) )
		self.assertFalse( b2.isAncestorOf( l2 ) )
		self.assertFalse( b2.isAncestorOf( p ) )
		self.assertFalse( b2.isAncestorOf( w ) )

		self.assertTrue( l1.isAncestorOf( b1 ) )
		self.assertFalse( l2.isAncestorOf( b1 ) )
		self.assertTrue( p.isAncestorOf( b1 ) )
		self.assertTrue( w.isAncestorOf( b1 ) )

	def testGafferWidgetAsTopLevel( self ) :

		w = TestWidget2()

		self.assertTrue( GafferUI.Widget._owner( w._qtWidget() ) is w )
		self.assertTrue( w.topLevelGafferWidget.parent() is w )
		self.assertTrue( GafferUI.Widget._owner( w.topLevelGafferWidget._qtWidget() ) is not w )

	def testToolTip( self ) :

		w = TestWidget()
		self.assertEqual( w.getToolTip(), "" )

		w = TestWidget( toolTip="hi" )
		self.assertEqual( w.getToolTip(), "hi" )

		w.setToolTip( "a" )
		self.assertEqual( w.getToolTip(), "a" )

	def testMarkdownToolTips( self ) :

		markdownToolTip = "# header\n\n- list 1\nlist 2"

		w = TestWidget()
		w.setToolTip( markdownToolTip )
		# We don't want any conversion to HTML to be "baked in" - we expect
		# to get back exactly the same thing as we saved.
		self.assertEqual( w.getToolTip(), markdownToolTip )

	def testEnabledState( self ) :

		w = TestWidget()
		self.assertEqual( w.getEnabled(), True )
		self.assertEqual( w.enabled(), True )

		w.setEnabled( False )
		self.assertEqual( w.getEnabled(), False )
		self.assertEqual( w.enabled(), False )

		w.setEnabled( True )
		self.assertEqual( w.getEnabled(), True )
		self.assertEqual( w.enabled(), True )

	def testDisabledWidgetsDontGetSignals( self ) :

		w = TestWidget()

		def f( w, event ) :

			WidgetTest.signalsEmitted += 1

		w.buttonPressSignal().connect( f )

		WidgetTest.signalsEmitted = 0

		event = QtGui.QMouseEvent( QtCore.QEvent.MouseButtonPress, QtCore.QPoint( 0, 0 ), QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier )

		QtWidgets.QApplication.instance().sendEvent( w._qtWidget(), event )
		self.assertEqual( WidgetTest.signalsEmitted, 1 )

		w.setEnabled( False )
		QtWidgets.QApplication.instance().sendEvent( w._qtWidget(), event )
		self.assertEqual( WidgetTest.signalsEmitted, 1 )

		w.setEnabled( True )
		QtWidgets.QApplication.instance().sendEvent( w._qtWidget(), event )
		self.assertEqual( WidgetTest.signalsEmitted, 2 )

	def testCanDieAfterUsingSignals( self ) :

		w = TestWidget()

		wr1 = weakref.ref( w )
		wr2 = weakref.ref( w._qtWidget() )

		w.buttonPressSignal()
		w.buttonReleaseSignal()
		w.mouseMoveSignal()
		w.wheelSignal()

		del w
		self.assertIsNone( wr1() )
		self.assertIsNone( wr2() )

	def testVisibility( self ) :

		with GafferUI.Window() as w :
			with GafferUI.ListContainer() as l :
				t = TestWidget()

		self.assertEqual( w.getVisible(), False )
		self.assertEqual( l.getVisible(), True )
		self.assertEqual( t.getVisible(), True )
		self.assertEqual( w.visible(), False )
		self.assertEqual( l.visible(), False )
		self.assertEqual( t.visible(), False )

		w.setVisible( True )
		self.assertEqual( w.getVisible(), True )
		self.assertEqual( l.getVisible(), True )
		self.assertEqual( t.getVisible(), True )
		self.assertEqual( w.visible(), True )
		self.assertEqual( l.visible(), True )
		self.assertEqual( t.visible(), True )

		w.setVisible( False )
		self.assertEqual( w.getVisible(), False )
		self.assertEqual( l.getVisible(), True )
		self.assertEqual( t.getVisible(), True )
		self.assertEqual( w.visible(), False )
		self.assertEqual( l.visible(), False )
		self.assertEqual( t.visible(), False )
		self.assertEqual( t.visible( relativeTo = l ), True )
		self.assertEqual( t.visible( relativeTo = w ), True )

		w.setVisible( True )
		t.setVisible( False )
		self.assertEqual( t.getVisible(), False )
		self.assertEqual( t.visible(), False )
		self.assertEqual( t.visible( relativeTo = l ), False )

	def testGetVisibleForNewWidgets( self ) :

		w = TestWidget()
		self.assertEqual( w.getVisible(), True )

	def testVisibilityOfParentlessWidgets( self ) :

		w = GafferUI.Window()
		t = TestWidget()

		# windows must be explicitly shown
		self.assertEqual( w.getVisible(), False )
		self.assertEqual( w.visible(), False )

		# widgets don't need to be explicitly shown but
		# must not be visible on screen until parented
		# to a window
		self.assertEqual( t.getVisible(), True )
		self.assertEqual( t.visible(), False )

		w.setVisible( True )
		self.assertEqual( w.getVisible(), True )
		self.assertEqual( w.visible(), True )

		w.setChild( t )
		self.assertEqual( t.getVisible(), True )
		self.assertEqual( t.visible(), True )

		# removing a widget from its parent must not
		# leave it visible on screen.
		w.removeChild( t )
		self.assertEqual( t.parent(), None )
		self.assertEqual( t.getVisible(), True )
		self.assertEqual( t.visible(), False )

	def testVisibilityWhenTransferringWidgets( self ) :

		w1 = GafferUI.Window()
		w1.setVisible( True )

		w2 = GafferUI.Window()
		w2.setVisible( True )

		v = TestWidget()
		self.assertEqual( v.getVisible(), True )
		self.assertEqual( v.visible(), False )

		h = TestWidget()
		self.assertEqual( h.getVisible(), True )
		h.setVisible( False )
		self.assertEqual( h.getVisible(), False )
		self.assertEqual( h.visible(), False )

		w1.setChild( v )
		self.assertEqual( v.getVisible(), True )
		self.assertEqual( v.visible(), True )

		self.assertEqual( h.getVisible(), False )
		self.assertEqual( h.visible(), False )

		w2.setChild( v )
		self.assertEqual( v.getVisible(), True )
		self.assertEqual( v.visible(), True )

		self.assertEqual( h.getVisible(), False )
		self.assertEqual( h.visible(), False )

		w1.setChild( h )
		self.assertEqual( v.getVisible(), True )
		self.assertEqual( v.visible(), True )

		self.assertEqual( h.getVisible(), False )
		self.assertEqual( h.visible(), False )

		w2.setChild( h )
		self.assertEqual( v.getVisible(), True )
		self.assertEqual( v.visible(), False )

		self.assertEqual( h.getVisible(), False )
		self.assertEqual( h.visible(), False )

	def testSignals( self ) :

		w = TestWidget()

		for s in [
			( "keyPressSignal", GafferUI.WidgetEventSignal ),
			( "keyReleaseSignal", GafferUI.WidgetEventSignal ),
			( "buttonPressSignal", GafferUI.WidgetEventSignal ),
			( "buttonReleaseSignal", GafferUI.WidgetEventSignal ),
			( "buttonDoubleClickSignal", GafferUI.WidgetEventSignal ),
			( "mouseMoveSignal", GafferUI.WidgetEventSignal ),
			( "enterSignal", GafferUI.WidgetSignal ),
			( "leaveSignal", GafferUI.WidgetSignal ),
			( "wheelSignal", GafferUI.WidgetEventSignal ),
			( "visibilityChangedSignal", GafferUI.WidgetSignal ),
			( "contextMenuSignal", GafferUI.WidgetSignal ),
			( "parentChangedSignal", GafferUI.WidgetSignal ),
		] :

			self.assertIsInstance( getattr( w, s[0] )(), s[1] )
			self.assertTrue( getattr( w, s[0] )() is getattr( w, s[0] )() )

	def testBound( self ) :

		w = GafferUI.Window( borderWidth = 8 )
		b = GafferUI.Button()
		w.setChild( b )
		w.setVisible( True )

		w.setPosition( imath.V2i( 100 ) )

		self.waitForIdle( 1000 )

		wb = w.bound()
		bb = b.bound()
		bbw = b.bound( relativeTo = w )

		self.assertIsInstance( wb, imath.Box2i )
		self.assertIsInstance( bb, imath.Box2i )
		self.assertIsInstance( bbw, imath.Box2i )

		self.assertEqual( bb.size(), bbw.size() )
		self.assertEqual( bbw.min(), bb.min() - wb.min() )
		self.assertEqual( b.size(), bb.size() )

	def testParentChangedSignal( self ) :

		w = TestWidget()
		window = GafferUI.Window()

		cs = GafferTest.CapturingSlot( w.parentChangedSignal() )
		self.assertEqual( len( cs ), 0 )

		window.setChild( w )
		self.assertEqual( len( cs ), 1 )
		self.assertEqual( cs[0], ( w, ) )

		window.setChild( None )
		self.assertEqual( len( cs ), 2 )
		self.assertEqual( cs[1], ( w, ) )

	def testHighlighting( self ) :

		w = TestWidget()
		self.assertEqual( w.getHighlighted(), False )

		w.setHighlighted( True )
		self.assertEqual( w.getHighlighted(), True )

		w.setHighlighted( False )
		self.assertEqual( w.getHighlighted(), False )

	@unittest.skipIf( os.name == "nt", "Skip failing Windows tests temporarily" )
	def testWidgetAt( self ) :

		with GafferUI.Window() as w1 :
			t1 = GafferUI.TextWidget( "hello" )

		with GafferUI.Window() as w2 :
			t2 = GafferUI.TextWidget( "hello" )

		w1.setVisible( True )
		w2.setVisible( True )

		w1.setPosition( imath.V2i( 100 ) )
		w2.setPosition( imath.V2i( 300 ) )

		self.waitForIdle( 10000 )

		self.assertTrue( GafferUI.Widget.widgetAt( w1.bound().center() ) is t1 )
		self.assertTrue( GafferUI.Widget.widgetAt( w2.bound().center() ) is t2 )
		self.assertTrue( GafferUI.Widget.widgetAt( w1.bound().center(), widgetType=GafferUI.Window ) is w1 )
		self.assertTrue( GafferUI.Widget.widgetAt( w2.bound().center(), widgetType=GafferUI.Window ) is w2 )

	def testMousePosition( self ) :

		w = GafferUI.Window( borderWidth = 8 )
		b = GafferUI.Button()
		w.setChild( b )
		w.setVisible( True )

		w.setPosition( imath.V2i( 100 ) )

		self.waitForIdle( 1000 )

		mouseGlobal = GafferUI.Widget.mousePosition()
		mouseLocal = GafferUI.Widget.mousePosition( relativeTo = b )

		self.assertEqual( mouseGlobal, mouseLocal + b.bound().min() )

	def testAddressAndObject( self ) :

		button = GafferUI.Button()
		address = GafferUI._qtAddress( button._qtWidget() )
		self.assertTrue( isinstance( address, int ) )
		widget = GafferUI._qtObject( address, QtWidgets.QPushButton )
		self.assertTrue( isinstance( widget, QtWidgets.QPushButton ) )

	def testSetVisibleWithNonBool( self ) :

		w = TestWidget()
		self.assertTrue( w.getVisible() is True )

		w.setVisible( 0 )
		self.assertTrue( w.getVisible() is False )

		w.setVisible( 1 )
		self.assertTrue( w.getVisible() is True )

	def testStyleProperties( self ) :

		w = GafferUI.Widget( QtWidgets.QLabel( "base" ))
		self.assertEqual( w._qtWidget().property( 'gafferClass' ), 'GafferUI.Widget' )

		w = TestWidget()
		self.assertEqual( w._qtWidget().property( 'gafferClass' ), 'GafferUITest.WidgetTest.TestWidget' )

		class TestWidgetChild( TestWidget ) :
			pass

		w = TestWidgetChild()
		self.assertEqual( w._qtWidget().property( 'gafferClasses' ), [
			'GafferUITest.WidgetTest.TestWidgetChild',
			'GafferUITest.WidgetTest.TestWidget',
			'GafferUI.Widget'
		] )

	def testPostConstructor( self ) :

		class BaseWidget( GafferUI.Widget ) :

			def __init__( self, **kw ) :

				GafferUI.Widget.__init__( self, GafferUI.TextWidget(), **kw )

			def _postConstructor( self ) :

				assert( self.derivedConstructed )
				self.postConstructed = True

		class DerivedWidget( BaseWidget ) :

			def __init__( self, **kw ) :

				BaseWidget.__init__( self, **kw )

				self.derivedConstructed = True

		w = DerivedWidget()
		self.assertTrue( w.postConstructed )

	def testDisplayTransform( self ) :

		with GafferUI.ListContainer() as parent :
			child = TestWidget()

		self.assertIsNone( parent.getDisplayTransform() )
		self.assertIsNone( child.getDisplayTransform() )
		self.assertIs( parent.displayTransform(), GafferUI.Widget.identityDisplayTransform )
		self.assertIs( child.displayTransform(), GafferUI.Widget.identityDisplayTransform )

		displayTransform1 = lambda x : x * 1
		displayTransform2 = lambda x : x * 2

		parent.setDisplayTransform( displayTransform1 )
		self.assertIs( parent.getDisplayTransform(), displayTransform1 )
		self.assertIsNone( child.getDisplayTransform() )
		self.assertIs( parent.displayTransform(), displayTransform1 )
		self.assertIs( child.displayTransform(), displayTransform1 )

		child.setDisplayTransform( displayTransform2 )
		self.assertIs( parent.getDisplayTransform(), displayTransform1 )
		self.assertIs( child.getDisplayTransform(), displayTransform2 )
		self.assertIs( parent.displayTransform(), displayTransform1 )
		self.assertIs( child.displayTransform(), displayTransform2 )

		parent.setDisplayTransform( None )
		self.assertIs( parent.getDisplayTransform(), None )
		self.assertIs( child.getDisplayTransform(), displayTransform2 )
		self.assertIs( parent.displayTransform(), GafferUI.Widget.identityDisplayTransform )
		self.assertIs( child.displayTransform(), displayTransform2 )

		widget = TestWidget( displayTransform = displayTransform1 )
		self.assertIs( widget.displayTransform(), displayTransform1 )

	def testDisplayTransformChanged( self ) :

		class CapturingWidget( GafferUI.Widget ) :

			def __init__( self, **kw ) :

				GafferUI.Widget.__init__( self, QtWidgets.QWidget(), **kw )

				# Add a child, to check that multiple QWidgets with the same
				# `Widget._owner()` don't result in multiple calls to
				# `_displayTransformChanged()`.
				self.__childQtWidget = QtWidgets.QWidget( self._qtWidget() )

				self.displayTransformChanges = []

			def _displayTransformChanged( self ) :

				GafferUI.Widget._displayTransformChanged( self )
				self.displayTransformChanges.append( self.displayTransform() )

		with GafferUI.ListContainer() as outer :
			with GafferUI.ListContainer() as inner :
				widget = CapturingWidget()

		displayTransform1 = lambda x : x * 1
		displayTransform2 = lambda x : x * 2

		# Change propagated to `widget`
		outer.setDisplayTransform( displayTransform1 )
		self.assertEqual( widget.displayTransformChanges, [ displayTransform1 ] )
		# No-op, so no change propagated.
		outer.setDisplayTransform( displayTransform1 )
		self.assertEqual( widget.displayTransformChanges, [ displayTransform1 ] )
		# Change propagated to `widget`.
		inner.setDisplayTransform( displayTransform2 )
		self.assertEqual( widget.displayTransformChanges, [ displayTransform1, displayTransform2 ] )
		# Change not propagated to `widget`, because it is overridden by
		# the transform on `inner`.
		outer.setDisplayTransform( GafferUI.Widget.identityDisplayTransform )
		self.assertEqual( widget.displayTransformChanges, [ displayTransform1, displayTransform2 ] )
		# Change is directly on `widget`, so notified regardless.
		widget.setDisplayTransform( GafferUI.Widget.identityDisplayTransform )
		self.assertEqual( widget.displayTransformChanges, [ displayTransform1, displayTransform2, GafferUI.Widget.identityDisplayTransform ] )

		# Check that changes are propagated when we parent one window
		# to another with a different transform.

		window1 = GafferUI.Window()
		window1.setDisplayTransform( displayTransform1 )

		with GafferUI.Window() as window2 :
			CapturingWidget()

		self.assertEqual( window2.getChild().displayTransformChanges, [] )

		window1.addChildWindow( window2 )
		self.assertEqual( window2.getChild().displayTransformChanges, [ displayTransform1 ] )

		# But not if the child window already has its own transform.

		with GafferUI.Window() as window3 :
			CapturingWidget()

		window3.setDisplayTransform( displayTransform2 )
		self.assertEqual( window3.getChild().displayTransformChanges, [ displayTransform2 ] )

		window1.addChildWindow( window3 )
		self.assertEqual( window3.getChild().displayTransformChanges, [ displayTransform2 ] )

	def testButtonPressSignalLine( self ) :

		w = TestWidget()

		def f( w, event ) :

			self.assertEqual( event.line.p0.x - int( event.line.p0.x ), 0.5 )
			self.assertEqual( event.line.p0.y - int( event.line.p0.y ), 0.5 )
			self.assertEqual( event.line.p1.x - int( event.line.p1.x ), 0.5 )
			self.assertEqual( event.line.p1.y - int( event.line.p1.y ), 0.5 )

		w.buttonPressSignal().connect( f )

		event = QtGui.QMouseEvent( QtCore.QEvent.MouseButtonPress, QtCore.QPoint( 10, 10 ), QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier )

		QtWidgets.QApplication.instance().sendEvent( w._qtWidget(), event )

if __name__ == "__main__":
	unittest.main()
