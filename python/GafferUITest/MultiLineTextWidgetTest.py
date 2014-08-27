##########################################################################
#
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import GafferUI
import GafferTest
import GafferUITest

class MultiLineTextWidgetTest( GafferUITest.TestCase ) :

	def testLifespan( self ) :

		w = GafferUI.MultiLineTextWidget()
		r = weakref.ref( w )

		self.failUnless( r() is w )

		del w

		self.failUnless( r() is None )

	def testEditable( self ) :

		w = GafferUI.MultiLineTextWidget( editable=False )
		self.assertEqual( w.getEditable(), False )

		w.setEditable( True )
		self.assertEqual( w.getEditable(), True )

	def testTextChangedSignal( self ) :

		w = GafferUI.MultiLineTextWidget()
		c = GafferTest.CapturingSlot( w.textChangedSignal() )

		w.setText( "hi" )
		self.assertEqual( len( c ), 1 )
		self.assertEqual( c[0], ( w, ) )

		# shouldn't do anything as text is the same
		w.setText( "hi" )
		self.assertEqual( len( c ), 1 )
		self.assertEqual( c[0], ( w, ) )

	def testWrapMode( self ) :

		w = GafferUI.MultiLineTextWidget()
		self.assertEqual( w.getWrapMode(), w.WrapMode.WordOrCharacter )

		for wm in w.WrapMode.values() :
			w.setWrapMode( wm )
			self.assertEqual( w.getWrapMode(), wm )

	def testCursorPosition( self ) :

		w = GafferUI.MultiLineTextWidget()
		self.assertEqual( w.getCursorPosition(), 0 )

		w.setText( "hello" )
		self.assertEqual( w.getCursorPosition(), 0 )

		w.setCursorPosition( 1 )
		self.assertEqual( w.getCursorPosition(), 1 )

	def testInsertText( self ) :

		w = GafferUI.MultiLineTextWidget()

		w.setText( "12" )
		w.setCursorPosition( 1 )

		w.insertText( "abc" )
		self.assertEqual( w.getText(), "1abc2" )

if __name__ == "__main__":
	unittest.main()
