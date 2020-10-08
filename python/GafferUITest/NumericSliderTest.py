##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import GafferTest
import GafferUI
import GafferUITest

class NumericSliderTest( GafferUITest.TestCase ) :

	def testConstruction( self ) :

		s = GafferUI.NumericSlider( value = 0, min = 0, max = 1 )

		self.assertEqual( s.getPosition(), 0 )
		self.assertEqual( s.getValue(), 0 )
		self.assertEqual( s.getRange(), ( 0, 1, 0, 1 ) )

	def testSetValue( self ) :

		s = GafferUI.NumericSlider( value = 0, min = 0, max = 2 )

		self.assertEqual( s.getPosition(), 0 )
		self.assertEqual( s.getValue(), 0 )

		s.setValue( 0.5 )
		self.assertEqual( s.getPosition(), 0.25 )
		self.assertEqual( s.getValue(), 0.5 )

	def testSetRange( self ) :

		s = GafferUI.NumericSlider( value = 1, min = 0, max = 2 )

		self.assertEqual( s.getPosition(), 0.5 )
		self.assertEqual( s.getValue(), 1 )

		s.setRange( 0, 1 )
		self.assertEqual( s.getPosition(), 1 )
		self.assertEqual( s.getValue(), 1 )

	def testSetZeroRange( self ) :

		s = GafferUI.NumericSlider( value = 1, min = 1, max = 2 )

		self.assertEqual( s.getPosition(), 0 )
		self.assertEqual( s.getValue(), 1 )

		s.setRange( 1, 1 )
		self.assertEqual( s.getValue(), 1 )

	def testSetPosition( self ) :

		s = GafferUI.NumericSlider( value = 0, min = 0, max = 2 )

		self.assertEqual( s.getPosition(), 0 )
		self.assertEqual( s.getValue(), 0 )

		s.setPosition( 0.5 )
		self.assertEqual( s.getPosition(), 0.5 )
		self.assertEqual( s.getValue(), 1 )

	def testValuesOutsideRangeAreClamped( self ) :

		s = GafferUI.NumericSlider( value = 0.1, min = 0, max = 2 )

		cs = GafferTest.CapturingSlot( s.valueChangedSignal(), s.positionChangedSignal() )

		s.setValue( 3 )
		self.assertEqual( s.getValue(), 2 )
		self.assertEqual( s.getPosition(), 1 )

		self.assertEqual( len( cs ), 2 )

		s.setValue( 3 )
		self.assertEqual( s.getValue(), 2 )
		self.assertEqual( s.getPosition(), 1 )

		# second attempt was clamped to same position as before, so shouldn't
		# signal any changes.
		self.assertEqual( len( cs ), 2 )

	def testPositionsOutsideRangeAreClamped( self ) :

		s = GafferUI.NumericSlider( value = 0.1, min = 0, max = 2 )

		cs = GafferTest.CapturingSlot( s.valueChangedSignal(), s.positionChangedSignal() )

		s.setPosition( 2 )
		self.assertEqual( s.getValue(), 2 )
		self.assertEqual( s.getPosition(), 1 )

		self.assertEqual( len( cs ), 2 )

		s.setPosition( 2 )
		self.assertEqual( s.getValue(), 2 )
		self.assertEqual( s.getPosition(), 1 )

		# second attempt was clamped to same position as before, so shouldn't
		# signal any changes.
		self.assertEqual( len( cs ), 2 )

	def testHardRange( self ) :

		s = GafferUI.NumericSlider( value = 0.1, min = 0, max = 2, hardMin=-1, hardMax=3 )
		self.assertEqual( s.getRange(), ( 0, 2, -1, 3 ) )

		cs = GafferTest.CapturingSlot( s.valueChangedSignal(), s.positionChangedSignal() )

		s.setValue( 3 )
		self.assertEqual( s.getValue(), 3 )
		self.assertEqual( s.getPosition(), 1.5 )
		self.assertEqual( len( cs ), 2 )

		s.setValue( 3.5 )
		self.assertEqual( s.getValue(), 3 )
		self.assertEqual( s.getPosition(), 1.5 )
		self.assertEqual( len( cs ), 2 )

		s.setValue( -1 )
		self.assertEqual( s.getValue(), -1 )
		self.assertEqual( s.getPosition(), -0.5)
		self.assertEqual( len( cs ), 4 )

		s.setValue( -2 )
		self.assertEqual( s.getValue(), -1 )
		self.assertEqual( s.getPosition(), -0.5)
		self.assertEqual( len( cs ), 4 )

	def testSetRangeClampsValue( self ) :

		s = GafferUI.NumericSlider( value = 0.5, min = 0, max = 2 )

		self.assertEqual( s.getPosition(), 0.25 )
		self.assertEqual( s.getValue(), 0.5 )

		s.setRange( 1, 2 )
		self.assertEqual( s.getPosition(), 0 )
		self.assertEqual( s.getValue(), 1 )

	def testMultipleValues( self ) :

		self.assertRaises( Exception, GafferUI.NumericSlider, value = 0, values = [ 1, 2 ] )

		s = GafferUI.NumericSlider( values = [ 1, 1.5 ], min = 0, max = 2 )
		self.assertEqual( s.getValues(), [ 1, 1.5 ] )
		self.assertEqual( s.getPositions(), [ 0.5, 0.75 ] )
		self.assertRaises( ValueError, s.getValue )

if __name__ == "__main__":
	unittest.main()
