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
import weakref

import IECore

import Gaffer
import GafferUI
import GafferUITest

QtGui = GafferUI._qtImport( "QtGui" )

class TestWidget( GafferUI.Widget ) :

	def __init__( self ) :

		GafferUI.Widget.__init__( self, QtGui.QLabel( "hello" ) )

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
		self.assert_( not w.getChild() is None )
		self.assert_( isinstance( w.getChild(), TestWidget ) )

		t = TestWidget()
		w.setChild( t )
		self.assert_( w.getChild() is t )
		self.assert_( w.getChild()._qtWidget() is t._qtWidget() )
		self.assert_( t.parent() is w )

		w.setChild( None )
		self.assert_( w.getChild() is None )
		self.assert_( t.parent() is None )

	def testReparent( self ) :

		w1 = GafferUI.Window()
		w2 = GafferUI.Window()

		t = TestWidget()

		w1.setChild( t )
		self.assert_( t.parent() is w1 )
		self.assert_( w1.getChild() is t )
		self.assert_( w2.getChild() is None )
		self.assert_( GafferUI.Widget._owner( t._qtWidget() ) is t )

		w2.setChild( t )
		self.assert_( t.parent() is w2 )
		self.assert_( w1.getChild() is None )
		self.assert_( w2.getChild() is t )
		self.assert_( GafferUI.Widget._owner( t._qtWidget() ) is t )

	def testWindowParent( self ) :

		parentWindow1 = GafferUI.Window()
		parentWindow2 = GafferUI.Window()
		childWindow = GafferUI.Window()
		childWindowWeakRef = weakref.ref( childWindow )

		self.failUnless( parentWindow1.parent() is None )
		self.failUnless( parentWindow2.parent() is None )
		self.failUnless( childWindow.parent() is None )

		parentWindow1.addChildWindow( childWindow )
		self.failUnless( parentWindow1.parent() is None )
		self.failUnless( parentWindow2.parent() is None )
		self.failUnless( childWindow.parent() is parentWindow1 )

		parentWindow2.addChildWindow( childWindow )
		self.failUnless( parentWindow1.parent() is None )
		self.failUnless( parentWindow2.parent() is None )
		self.failUnless( childWindow.parent() is parentWindow2 )

		parentWindow2.removeChild( childWindow )
		self.failUnless( parentWindow1.parent() is None )
		self.failUnless( parentWindow2.parent() is None )
		self.failUnless( childWindow.parent() is None )

		del childWindow

		self.failUnless( childWindowWeakRef() is None )

	def testWindowHoldsReferenceToChildWindows( self ) :

		parentWindow = GafferUI.Window()
		childWindow = GafferUI.Window()
		childWindowWeakRef = weakref.ref( childWindow )

		parentWindow.addChildWindow( childWindow )

		del childWindow

		self.failUnless( childWindowWeakRef() is not None )

		del parentWindow

		self.failUnless( childWindowWeakRef() is None )

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

		self.failUnless( d.parent() is w )
		self.failUnless( f.parent() is w )
		self.failUnless( d2.parent() is w )

	def testSizeMode( self ) :

		w = GafferUI.Window()
		self.assertEqual( w.getSizeMode(), w.SizeMode.Manual )

		w = GafferUI.Window( sizeMode=GafferUI.Window.SizeMode.Fixed )
		self.assertEqual( w.getSizeMode(), w.SizeMode.Fixed )

		w.setSizeMode( GafferUI.Window.SizeMode.Automatic )
		self.assertEqual( w.getSizeMode(), w.SizeMode.Automatic )

	def testResizeable( self ) :

		w = GafferUI.Window()
		self.failUnless( w.getResizeable() )

		w.setResizeable( False )
		self.failIf( w.getResizeable() )

		w.setResizeable( True )
		self.failUnless( w.getResizeable() )

	def testPosition( self ) :

		w = GafferUI.Window()
		w.setPosition( IECore.V2i( 10, 20 ) )
		self.assertEqual( w.getPosition(), IECore.V2i( 10, 20 ) )

	def testChildWindowsMethod( self ) :

		w = GafferUI.Window()
		self.assertEqual( w.childWindows(), [] )

		wc1 = GafferUI.Window()
		w.addChildWindow( wc1 )
		self.assertEqual( w.childWindows(), [ wc1 ] )

		wc2 = GafferUI.Window()
		w.addChildWindow( wc2 )
		self.assertEqual( len( w.childWindows() ), 2 )
		self.failUnless( wc1 in w.childWindows() )
		self.failUnless( wc2 in w.childWindows() )

		c = w.childWindows()
		c.remove( wc1 )
		# editing the list itself should have no effect
		self.assertEqual( len( w.childWindows() ), 2 )
		self.failUnless( wc1 in w.childWindows() )
		self.failUnless( wc2 in w.childWindows() )

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

if __name__ == "__main__":
	unittest.main()

