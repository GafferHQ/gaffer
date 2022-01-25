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
import warnings

import GafferUI
import GafferUITest

class SelectionMenuTest( GafferUITest.TestCase ) :

	def testAccessors( self ) :

		# The SelectionMenu class is deprecated, but we still want to
		# run the tests for it for as long as it is still in Gaffer.
		# So we temporarily suppress the warnings that it will emit
		# when used.
		with warnings.catch_warnings() :

			warnings.simplefilter( "ignore", DeprecationWarning )

			s = GafferUI.SelectionMenu()

			# adding new items
			s.addItem( "Test1" )
			s.addItem( "Test2" )
			s.addItem( "Test3" )
			self.assertEqual( s.getTotal(), 3 )

			# changing and checking the current item
			s.setCurrentIndex( 1 )
			self.assertEqual( s.getCurrentItem(), "Test2" )
			self.assertEqual( s.getItem(s.getCurrentIndex()), "Test2" )

			# removing item
			s.removeIndex( 0 )
			self.assertEqual ( s.getTotal(), 2 )

	def testInsert( self ) :

		with warnings.catch_warnings() :

			warnings.simplefilter( "ignore", DeprecationWarning )

			s = GafferUI.SelectionMenu()

			# adding new items
			s.addItem( "Test1" )
			s.addItem( "Test2" )
			s.addItem( "Test3" )
			self.assertEqual( s.getTotal(), 3 )

			# insert an item and check it
			s.insertItem( 1, "Test4")
			self.assertEqual( s.getItem(1), "Test4" )

	def testCurrentIndexChangedSignal( self ):

		with warnings.catch_warnings() :

			warnings.simplefilter( "ignore", DeprecationWarning )

			s = GafferUI.SelectionMenu()

			self.emissions = 0
			def f( w ) :
				self.emissions += 1

			s.currentIndexChangedSignal().connect( f, scoped = False )

			s.addItem("Test1")
			s.addItem("Test2")

			self.assertEqual(self.emissions, 1)

	def testNoQString( self ) :

		with warnings.catch_warnings() :

			warnings.simplefilter( "ignore", DeprecationWarning )

			s = GafferUI.SelectionMenu()
			s.addItem( "Test" )

			self.assertIsInstance( s.getCurrentItem(), str )
			self.assertIsInstance( s.getItem( 0 ), str )

if __name__ == "__main__":
	unittest.main()
