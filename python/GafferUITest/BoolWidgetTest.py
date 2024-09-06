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

import GafferUI
import GafferUITest

class BoolWidgetTest( GafferUITest.TestCase ) :

	def testLifespan( self ) :

		w = GafferUI.BoolWidget()
		r = weakref.ref( w )

		self.assertTrue( r() is w )

		del w

		self.assertTrue( r() is None )

	def testStateChangedSignal( self ) :

		self.emissions = 0
		def f( w ) :
			self.emissions += 1

		w = GafferUI.BoolWidget()
		w.stateChangedSignal().connect( f )

		w.setState( True )
		self.assertEqual( w.getState(), True )

		self.assertEqual( self.emissions, 1 )

	def testState( self ) :

		w = GafferUI.BoolWidget()
		self.assertEqual( w.getState(), False )

		w.setState( True )
		self.assertEqual( w.getState(), True )

		w.setState( False )
		self.assertEqual( w.getState(), False )

	def testText( self ) :

		w = GafferUI.BoolWidget( "a" )
		self.assertEqual( w.getText(), "a" )

		w.setText( "b" )
		self.assertEqual( w.getText(), "b" )

		self.assertIsInstance( w.getText(), str )

	def testDisplayMode( self ) :

		w = GafferUI.BoolWidget()
		self.assertEqual( w.getDisplayMode(), w.DisplayMode.CheckBox )

		w.setDisplayMode( w.DisplayMode.Switch )
		self.assertEqual( w.getDisplayMode(), w.DisplayMode.Switch )

		w.setDisplayMode( w.DisplayMode.CheckBox )
		self.assertEqual( w.getDisplayMode(), w.DisplayMode.CheckBox )

		w = GafferUI.BoolWidget( displayMode = GafferUI.BoolWidget.DisplayMode.Switch )
		self.assertEqual( w.getDisplayMode(), w.DisplayMode.Switch )

	def testIndeterminateState( self ) :

		w = GafferUI.BoolWidget()

		w.setState( w.State.Indeterminate )
		self.assertEqual( w.getState(), w.State.Indeterminate )

		w.setState( False )
		self.assertIs( w.getState(), False )

		w.setState( True )
		self.assertIs( w.getState(), True )

		# We don't want users to be able to set the
		# indeterminate state. It is a display-only
		# value.

		w._qtWidget().click()
		self.assertIs( w.getState(), False )

		w._qtWidget().click()
		self.assertIs( w.getState(), True )

		w._qtWidget().click()
		self.assertIs( w.getState(), False )

		# When in the indeterminate state, we expect
		# a click to take us into the True state.

		w.setState( w.State.Indeterminate )
		w._qtWidget().click()
		self.assertIs( w.getState(), True )

if __name__ == "__main__":
	unittest.main()
