##########################################################################
#
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

class SliderTest( GafferUITest.TestCase ) :

	def testConstructor( self ) :

		s = GafferUI.Slider()
		self.assertEqual( s.getPosition(), 0.5 )
		self.assertEqual( s.getPositions(), [ 0.5 ] )

		s = GafferUI.Slider( position = 1 )
		self.assertEqual( s.getPosition(), 1 )
		self.assertEqual( s.getPositions(), [ 1 ] )

		s = GafferUI.Slider( positions = [ 0, 1 ] )
		self.assertRaises( ValueError, s.getPosition )
		self.assertEqual( s.getPositions(), [ 0, 1 ] )

		self.assertRaises( Exception, GafferUI.Slider, position = 1, positions = [ 1, 2 ] )

	def testPositionAccessors( self ) :

		s = GafferUI.Slider( position = 1 )

		self.assertEqual( s.getPosition(), 1 )
		self.assertEqual( s.getPositions(), [ 1 ] )

		s.setPosition( 2 )

		self.assertEqual( s.getPosition(), 2 )
		self.assertEqual( s.getPositions(), [ 2 ] )

		s.setPositions( [ 2, 3 ] )

		self.assertRaises( ValueError, s.getPosition )
		self.assertEqual( s.getPositions(), [ 2, 3 ] )

	def testSelectedIndex( self ) :

		s = GafferUI.Slider( positions = [ 1, 2 ] )
		self.assertEqual( s.getSelectedIndex(), None )

		s.setSelectedIndex( 0 )
		self.assertEqual( s.getSelectedIndex(), 0 )
		s.setSelectedIndex( 1 )
		self.assertEqual( s.getSelectedIndex(), 1 )

		self.assertRaises( IndexError, s.setSelectedIndex, -1 )
		self.assertRaises( IndexError, s.setSelectedIndex, 2 )

		s.setSelectedIndex( None )
		self.assertEqual( s.getSelectedIndex(), None )

		cs = GafferTest.CapturingSlot( s.selectedIndexChangedSignal() )

		s.setSelectedIndex( 1 )
		self.assertEqual( len( cs ), 1 )
		self.assertTrue( cs[0][0] is s )

		s.setSelectedIndex( 1 )
		self.assertEqual( len( cs ), 1 )
		self.assertTrue( cs[0][0] is s )

		s.setSelectedIndex( 0 )
		self.assertEqual( len( cs ), 2 )
		self.assertTrue( cs[0][0] is s )
		self.assertTrue( cs[1][0] is s )

if __name__ == "__main__":
	unittest.main()
