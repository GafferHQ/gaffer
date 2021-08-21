##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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
import warnings
import weakref
import imath

import IECore

import Gaffer
import GafferUI
import GafferUITest

from Qt import QtGui
from Qt import QtWidgets

class TestWidget( GafferUI.Widget ) :

	def __init__( self ) :

		GafferUI.Widget.__init__( self, QtWidgets.QLabel( "hello" ) )

class WindowTest( GafferUITest.TestCase ) :

	def testTitle( self ) :

		w = GafferUI.Window()
		self.assertEqual( w.getTitle(), "GafferUI.Window" )

		w = GafferUI.Window( "myTitle" )
		self.assertEqual( w.getTitle(), "myTitle" )

		w.setTitle( "myOtherTitle" )
		self.assertEqual( w.getTitle(), "myOtherTitle" )

	def testChild( self ) :

		w = GafferUI.Window()
		self.assertEqual( w.getChild(), None )

		w.setChild( TestWidget() )
		self.assertIsNotNone( w.getChild() )
		self.assertIsInstance( w.getChild(), TestWidget )

		t = TestWidget()
		w.setChild( t )
		self.assertTrue( w.getChild() is t )
		self.assertTrue( w.getChild()._qtWidget() is t._qtWidget() )
		self.assertTrue( t.parent() is w )

		w.setChild( None )
		self.assertIsNone( w.getChild() )
		self.assertIsNone( t.parent() )

	def testReparent( self ) :

		w1 = GafferUI.Window()
		w2 = GafferUI.Window()

		t = TestWidget()

		w1.setChild( t )
		self.assertTrue( t.parent() is w1 )
		self.assertTrue( w1.getChild() is t )
		self.assertIsNone( w2.getChild() )
		self.assertTrue( GafferUI.Widget._owner( t._qtWidget() ) is t )

		w2.setChild( t )
		self.assertTrue( t.parent() is w2 )
		self.assertIsNone( w1.getChild() )
		self.assertTrue( w2.getChild() is t )
		self.assertTrue( GafferUI.Widget._owner( t._qtWidget() ) is t )

	def testWindowParent( self ) :

		parentWindow1 = GafferUI.Window()
		parentWindow2 = GafferUI.Window()
		childWindow = GafferUI.Window()
		childWindowWeakRef = weakref.ref( childWindow )

		self.assertIsNone( parentWindow1.parent() )
		self.assertIsNone( parentWindow2.parent() )
		self.assertIsNone( childWindow.parent() )

		parentWindow1.addChildWindow( childWindow )
		self.assertIsNone( parentWindow1.parent() )
		self.assertIsNone( parentWindow2.parent() )
		self.assertTrue( childWindow.parent() is parentWindow1 )

		parentWindow1.setVisible( True )
		childWindow.setVisible( True )
		self.waitForIdle( 1000 )

		parentWindow2.addChildWindow( childWindow )
		self.assertIsNone( parentWindow1.parent() )
		self.assertIsNone( parentWindow2.parent() )
		self.assertTrue( childWindow.parent() is parentWindow2 )

		parentWindow2.setVisible( True )
		self.waitForIdle( 1000 )

		parentWindow2.removeChild( childWindow )
		self.assertIsNone( parentWindow1.parent() )
		self.assertIsNone( parentWindow2.parent() )
		self.assertIsNone( childWindow.parent() )

		self.waitForIdle( 1000 )

		parentWindow1.addChildWindow( childWindow )
		self.assertTrue( childWindow.parent() is parentWindow1 )

		self.waitForIdle( 1000 )

		parentWindow1.removeChild( childWindow )

		del childWindow

		self.assertIsNone( childWindowWeakRef() )

	def testWindowHoldsReferenceToChildWindows( self ) :

		parentWindow = GafferUI.Window()
		childWindow = GafferUI.Window()
		childWindowWeakRef = weakref.ref( childWindow )

		parentWindow.addChildWindow( childWindow )

		del childWindow

		self.assertIsNotNone( childWindowWeakRef() )

		del parentWindow

		self.assertIsNone( childWindowWeakRef() )

	def testCloseMethod( self ) :

		self.__windowWasClosed = 0
		def closeFn( w ) :
			assert( isinstance( w, GafferUI.Window ) )
			self.__windowWasClosed += 1

		w = GafferUI.Window()

		w.setVisible( True )
		self.assertEqual( w.getVisible(), True )

		c = w.closedSignal().connect( closeFn )

		self.assertEqual( w.close(), True )
		self.assertEqual( w.getVisible(), False )
		self.assertEqual( self.__windowWasClosed, 1 )

	def testUserCloseAction( self ) :

		self.__windowWasClosed = 0
		def closeFn( w ) :
			assert( isinstance( w, GafferUI.Window ) )
			self.__windowWasClosed += 1

		w = GafferUI.Window()
		w.setVisible( True )
		self.assertEqual( w.getVisible(), True )

		c = w.closedSignal().connect( closeFn )

		# simulate user clicking on the x
		w._qtWidget().close()

		self.assertEqual( w.getVisible(), False )
		self.assertEqual( self.__windowWasClosed, 1 )

	def testCloseDenial( self ) :

		self.__windowWasClosed = 0
		def closeFn( w ) :
			assert( isinstance( w, GafferUI.Window ) )
			self.__windowWasClosed += 1

		class TestWindow( GafferUI.Window ) :

			def __init__( self ) :

				GafferUI.Window.__init__( self )

			def _acceptsClose( self ) :

				return False

		w = TestWindow()
		w.setVisible( True )
		self.assertEqual( w.getVisible(), True )

		c = w.closedSignal().connect( closeFn )

		self.assertEqual( w.close(), False )
		self.assertEqual( w.getVisible(), True )
		self.assertEqual( self.__windowWasClosed, 0 )

		# simulate user clicking on the x
		w._qtWidget().close()

		self.assertEqual( w.getVisible(), True )
		self.assertEqual( self.__windowWasClosed, 0 )

	def testAutomaticParenting( self ) :

		with GafferUI.Window() as w :

			d = GafferUI.Window()
			f = GafferUI.Frame()
			# should only accept one child
			self.assertRaises( Exception, GafferUI.Frame )
			# should accept any number of child windows though
			d2 = GafferUI.Window()

		self.assertTrue( d.parent() is w )
		self.assertTrue( f.parent() is w )
		self.assertTrue( d2.parent() is w )

	def testSizeMode( self ) :

		w = GafferUI.Window()
		self.assertEqual( w.getSizeMode(), w.SizeMode.Manual )

		w = GafferUI.Window( sizeMode=GafferUI.Window.SizeMode.Fixed )
		self.assertEqual( w.getSizeMode(), w.SizeMode.Fixed )

		w.setSizeMode( GafferUI.Window.SizeMode.Automatic )
		self.assertEqual( w.getSizeMode(), w.SizeMode.Automatic )

	def testResizeable( self ) :

		# The methods we are testing are deprecated, so we must
		# ignore the deprecation warnings they emit, as otherwise
		# they would become exceptions.
		with warnings.catch_warnings() :

			warnings.simplefilter( "ignore", DeprecationWarning )

			w = GafferUI.Window()
			self.assertTrue( w.getResizeable() )

			w.setResizeable( False )
			self.assertFalse( w.getResizeable() )

			w.setResizeable( True )
			self.assertTrue( w.getResizeable() )

	def testPosition( self ) :

		w = GafferUI.Window()
		w._qtWidget().resize( 200, 100 )
		self.assertEqual( ( w._qtWidget().width(), w._qtWidget().height() ), ( 200, 100 ) )

		w.setPosition( imath.V2i( 20, 30 ) )
		self.assertEqual( w.getPosition(), imath.V2i( 20, 30 ) )

		desktop = QtWidgets.QApplication.desktop()

		screenRect = desktop.availableGeometry( w._qtWidget() )
		windowRect = w._qtWidget().frameGeometry()

		# Smaller, off-screen bottom right

		w.setPosition( imath.V2i( screenRect.right() - 50, screenRect.bottom() - 75 ) )
		self.assertEqual(
			w.getPosition(),
			imath.V2i(
				screenRect.right() - windowRect.width() + 1,
				screenRect.bottom() - windowRect.height() + 1
			)
		)

		# Smaller, off-screen top left

		w.setPosition( imath.V2i( screenRect.left() - 25 , screenRect.top() - 15 ) )
		self.assertEqual( w.getPosition(), imath.V2i( screenRect.left(), screenRect.top() ) )

		# Bigger width only

		w._qtWidget().resize( screenRect.width() + 300, 200 )
		windowRect = w._qtWidget().frameGeometry()

		w.setPosition( imath.V2i( 100, 100 ) )
		self.assertEqual( w.getPosition(), imath.V2i( screenRect.left(), 100 ) )
		self.assertEqual( w._qtWidget().frameGeometry().size(), windowRect.size() )

		# Bigger

		w._qtWidget().resize( screenRect.width() + 300, screenRect.height() + 200 )
		windowRect = w._qtWidget().frameGeometry()

		w.setPosition( imath.V2i( 100, 100 ) )
		self.assertEqual( w.getPosition(), imath.V2i( screenRect.left(), screenRect.top() ) )
		self.assertEqual( w._qtWidget().frameGeometry().size(), windowRect.size() )

		# Force position

		w.setPosition( imath.V2i( 100, 100 ), forcePosition = True )
		self.assertEqual( w.getPosition(), imath.V2i( 100, 100 ) )
		self.assertEqual( w._qtWidget().frameGeometry().size(), windowRect.size() )

	def testChildWindowsMethod( self ) :

		w = GafferUI.Window()
		self.assertEqual( w.childWindows(), [] )

		wc1 = GafferUI.Window()
		w.addChildWindow( wc1 )
		self.assertEqual( w.childWindows(), [ wc1 ] )

		wc2 = GafferUI.Window()
		w.addChildWindow( wc2 )
		self.assertEqual( len( w.childWindows() ), 2 )
		self.assertIn( wc1, w.childWindows() )
		self.assertIn( wc2, w.childWindows() )

		c = w.childWindows()
		c.remove( wc1 )
		# editing the list itself should have no effect
		self.assertEqual( len( w.childWindows() ), 2 )
		self.assertIn( wc1, w.childWindows() )
		self.assertIn( wc2, w.childWindows() )

		w.removeChild( wc1 )
		self.assertEqual( w.childWindows(), [ wc2 ] )

	def testRemoveChildWindowOnClose( self ) :

		# removeOnClose == False

		parent = GafferUI.Window()
		child = GafferUI.Window()

		parent.addChildWindow( child )
		parent.setVisible( True )
		child.setVisible( True )

		child.close()
		self.waitForIdle()
		self.assertTrue( child in parent.childWindows() )

		# removeOnClose == True

		parent = GafferUI.Window()
		child = GafferUI.Window()

		parent.addChildWindow( child, removeOnClose = True )
		parent.setVisible( True )
		child.setVisible( True )

		child.close()
		self.waitForIdle()
		self.assertFalse( child in parent.childWindows() )

		w = weakref.ref( child )
		del child
		self.assertEqual( w(), None )

	def testRemoveOnCloseCrash( self ) :

		parent = GafferUI.Window()
		parent.setChild( GafferUI.Label( "\n".join( [ "Hello" * 10 ] * 10 ) ) )
		parent.setVisible( True )

		for i in range( 0, 50 ) :

			child = GafferUI.Window()
			child.setChild( GafferUI.Label( "World" ) )

			parent.addChildWindow( child, removeOnClose = True )
			child.setVisible( True )
			self.waitForIdle()

			qWindow = child._qtWidget().windowHandle()
			weakChild = weakref.ref( child )
			del child

			# Simulate a click on the close button of the QWindow for the child
			# window. This ripples down to the close handling in GafferUI.Window,
			# and should remove the child window cleanly.
			QtWidgets.QApplication.sendEvent( qWindow, QtGui.QCloseEvent() )
			self.waitForIdle( 1000 )
			self.assertEqual( parent.childWindows(), [] )
			self.assertEqual( weakChild(), None )

if __name__ == "__main__":
	unittest.main()
