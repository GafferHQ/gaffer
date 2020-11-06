##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Cinesite VFX Ltd. nor the names of
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

import GafferTest
import GafferUI
import GafferUITest

class NumericWidgetTest( GafferUITest.TestCase ) :

	def testLifespan( self ) :

		w = GafferUI.NumericWidget( 0 )
		r = weakref.ref( w )

		self.assertTrue( r() is w )

		del w

		self.assertTrue( r() is None )

	def testValueChangedSignal( self ) :

		w = GafferUI.NumericWidget( 1 )
		signals = GafferTest.CapturingSlot( w.valueChangedSignal() )

		w.setValue( 10 )
		self.assertEqual( w.getValue(), 10 )

		self.assertEqual( [ s[1] for s in signals ], [ GafferUI.NumericWidget.ValueChangedReason.SetValue ] )

	def testType( self ) :

		w = GafferUI.NumericWidget( 1.0 )
		w.setText( "2" )
		self.assertEqual( w.getValue(), 2.0 )
		self.assertIsInstance( w.getValue(), float )

		w = GafferUI.NumericWidget( 1 )
		w.setText( "2" )
		self.assertEqual( w.getValue(), 2 )
		self.assertIsInstance( w.getValue(), int )

	def testMaths( self ) :

		for text, expected, type_ in (
			( "3", 3, float ),
			( " 3", 3, int ),
			( "-3.1", -3.1, float ),
			( "-3", -3, int ),
			( "1+1", 2, int ),
			( " 1 +1", 2, int ),
			( "1+ 1", 2, int ),
			( "1 + 1", 2, int ),
			( " 1 + 1", 2, int ),
			( "1 + 1 ", 2, int ),
			( " 1 + 1 ", 2, int ),
			( "-1 +2", 1, int ),
			( "1-4", -3, int ),
			( "-4+ 2", -2, int ),
			( "-4+-2", -6, int ),
			( "1+-2", -1, int ),
			( "1--1", 2, int ),
			( " 1 / 2", 0, int ),
			( "1/2", 0.5, float ),
			( " 2*3", 6, int ),
			( "-2 * 3.1", -6.2, float ),
			( " -2 *3.1 ", -6.2, float ),
			( "3%2", 1, int ),
			( "2.5 % 2", 0.5, float ),
			( "1/0", 1, int ),
			( "5/0", 5.0, float ),
			( "03/1", 3.0, float ),
			( "03/1", 3, int ),
			( "3/01", 3.0, float ),
			( "3/01", 3, int ),
			( "1 / ", 1, int ),
			( "2 +", 2, int ),
			( "3.0*", 3.0, float ),
		) :
			w = GafferUI.NumericWidget( type_( 0 ) )
			w._qtWidget().setText( text )
			self.assertEqual( w.getValue(), expected )
			self.assertIsInstance( w.getValue(), type_ )

if __name__ == "__main__":
	unittest.main()
