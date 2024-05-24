##########################################################################
#
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
import gc

import GafferUI
import GafferTest
import GafferUITest

class TextWidgetTest( GafferUITest.TestCase ) :

	def testLifespan( self ) :

		w = GafferUI.TextWidget()
		r = weakref.ref( w )

		self.assertTrue( r() is w )

		del w

		self.assertIsNone( r() )

	def testTextChangedSignal( self ) :

		self.emissions = 0
		def f( w ) :
			self.emissions += 1

		w = GafferUI.TextWidget()
		w.textChangedSignal().connect( f, scoped = False )

		w.setText( "hello" )
		self.assertEqual( w.getText(), "hello" )

		self.assertEqual( self.emissions, 1 )

	def testDisplayMode( self ) :

		w = GafferUI.TextWidget()
		self.assertEqual( w.getDisplayMode(), w.DisplayMode.Normal )

		w = GafferUI.TextWidget( displayMode = GafferUI.TextWidget.DisplayMode.Password )
		self.assertEqual( w.getDisplayMode(), w.DisplayMode.Password )

		w.setDisplayMode( GafferUI.TextWidget.DisplayMode.Normal )
		self.assertEqual( w.getDisplayMode(), w.DisplayMode.Normal )

	def testSelection( self ) :

		w = GafferUI.TextWidget()
		self.assertEqual( w.getSelection(), ( 0, 0 ) )
		self.assertEqual( w.selectedText(), "" )

		w.setText( "hello" )
		w.setSelection( 1, 4 )
		self.assertEqual( w.getText()[slice( *w.getSelection() )], "hello"[1:4] )
		self.assertEqual( w.selectedText(), "ell" )

		w.setSelection( 0, -2 )
		self.assertEqual( w.getText()[slice( *w.getSelection() )], "hello"[0:-2] )
		self.assertEqual( w.selectedText(), "hel" )

		w.setSelection( 0, None )
		self.assertEqual( w.getText()[slice( *w.getSelection() )], "hello"[0:] )
		self.assertEqual( w.selectedText(), "hello" )

		w.setSelection( None, -2 )
		self.assertEqual( w.getText()[slice( *w.getSelection() )], "hello"[:-2] )
		self.assertEqual( w.selectedText(), "hel" )

		w.setSelection( 0, 0 )
		self.assertEqual( w.getText()[slice( *w.getSelection() )], "" )
		self.assertEqual( w.getSelection(), ( 0, 0 ) )
		self.assertEqual( w.selectedText(), "" )

		c = GafferTest.CapturingSlot( w.selectionChangedSignal() )

		w.setSelection( 0, 2 )
		self.assertEqual( len( c ), 1 )
		self.assertTrue( c[0][0] is w )

	def testCharacterWidth( self ) :

		w = GafferUI.TextWidget()
		self.assertEqual( w.getPreferredCharacterWidth(), 20 )
		self.assertEqual( w.getFixedCharacterWidth(), None )

		w.setFixedCharacterWidth( 4 )
		self.assertEqual( w.getPreferredCharacterWidth(), 20 )
		self.assertEqual( w.getFixedCharacterWidth(), 4 )

		w.setPreferredCharacterWidth( 10 )
		self.assertEqual( w.getPreferredCharacterWidth(), 10 )
		self.assertEqual( w.getFixedCharacterWidth(), 4 )

		w.setFixedCharacterWidth( None )
		self.assertEqual( w.getPreferredCharacterWidth(), 10 )
		self.assertEqual( w.getFixedCharacterWidth(), None )

	def testErrored( self ) :

		w = GafferUI.TextWidget()
		self.assertEqual( w.getErrored(), False )

		w.setErrored( True )
		self.assertEqual( w.getErrored(), True )

		w.setErrored( False )
		self.assertEqual( w.getErrored(), False )

	def testFixedCharacterWidth( self ) :

		window = GafferUI.Window()
		textWidget = GafferUI.TextWidget()
		window.addChild( textWidget )
		window.setVisible( True )

		# initial value
		textWidget.setFixedCharacterWidth( 5 )

		oldWidth = textWidget.size().x

		# changing the initial value
		textWidget.setFixedCharacterWidth( 2 )

		self.waitForIdle( 1000 )

		newWidth = textWidget.size().x

		# checking if the geometry has been updated for the new character width
		self.assertEqual( newWidth == oldWidth, False )

if __name__ == "__main__":
	unittest.main()
