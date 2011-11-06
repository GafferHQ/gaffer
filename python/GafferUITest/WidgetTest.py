##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

class TestWidget( GafferUI.Widget ) :

	def __init__( self, **kw ) :
	
		GafferUI.Widget.__init__( self, QtGui.QLabel( "hello" ), **kw )

class TestWidget2( GafferUI.Widget ) :

	def __init__( self ) :
	
		self.topLevelGafferWidget = TestWidget()
		
		GafferUI.Widget.__init__( self, self.topLevelGafferWidget )
		
class WidgetTest( unittest.TestCase ) :

	def testOwner( self ) :
	
		w = TestWidget()
		self.assert_( GafferUI.Widget._owner( w._qtWidget() ) is w )
		
	def testParent( self ) :
	
		w = TestWidget()
		self.assert_( w.parent() is None )
		
	def testCanDie( self ) :
	
		w = TestWidget()
		
		wr1 = weakref.ref( w )
		wr2 = weakref.ref( w._qtWidget() )
		
		del w
		self.assert_( wr1() is None )
		self.assert_( wr2() is None )
	
	def testAncestor( self ) :
	
		w = GafferUI.Window( "test" )
		l = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		p = GafferUI.SplitContainer()
		l.append( p )
		
		w.setChild( l )

		self.assert_( p.ancestor( GafferUI.ListContainer ) is l )
		self.assert_( p.ancestor( GafferUI.Window ) is w )
		self.assert_( p.ancestor( GafferUI.Menu ) is None )
	
	def testGafferWidgetAsTopLevel( self ) :
	
		w = TestWidget2()
		
		self.assert_( GafferUI.Widget._owner( w._qtWidget() ) is w )
		self.assert_( w.topLevelGafferWidget.parent() is w )
		self.assert_( GafferUI.Widget._owner( w.topLevelGafferWidget._qtWidget() ) is not w )
	
	def testToolTip( self ) :
	
		w = TestWidget()
		self.assertEqual( w.getToolTip(), "" )
		
		w = TestWidget( toolTip="hi" )
		self.assertEqual( w.getToolTip(), "hi" )
		
		w.setToolTip( "a" )
		self.assertEqual( w.getToolTip(), "a" )
	
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
	
		c = w.buttonPressSignal().connect( f )
		
		WidgetTest.signalsEmitted = 0
		
		event = QtGui.QMouseEvent( QtCore.QEvent.MouseButtonPress, QtCore.QPoint( 0, 0 ), QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier )
		
		QtGui.QApplication.instance().sendEvent( w._qtWidget(), event )
		self.assertEqual( WidgetTest.signalsEmitted, 1 )
		
		w.setEnabled( False )
		QtGui.QApplication.instance().sendEvent( w._qtWidget(), event )
		self.assertEqual( WidgetTest.signalsEmitted, 1 )

		w.setEnabled( True )
		QtGui.QApplication.instance().sendEvent( w._qtWidget(), event )
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
		self.assert_( wr1() is None )
		self.assert_( wr2() is None )
		
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
		
if __name__ == "__main__":
	unittest.main()
	
