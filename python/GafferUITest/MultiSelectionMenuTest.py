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

import os
import unittest
import IECore
import Gaffer
import GafferUI
import GafferUITest
import sys

class MultiSelectionMenuTest( GafferUITest.TestCase ) :

	def testSliceAssignment( self ) :

		w = GafferUI.MultiSelectionMenu( allowMultipleSelection = True )
		w.append("A")
		w.append("B")
		w.setSelection( [ "A" ] )

		# Test that if we replace the data but choose to keep the status of any
		# duplicate entries that their status doesn't change.
		newData = ["C", "E", "A"]
		w[:] = newData

		# Assert the size and order
		self.assertEqual( "C", w[0] )
		self.assertEqual( "E", w[1] )
		self.assertEqual( "A", w[2] )
		self.assertEqual( len(w), 3 )
		self.assertEqual( w.getSelection(), ["A"] )

	def testDelAndInOperators( self ) :

		w = GafferUI.MultiSelectionMenu()
		w.append("A")
		w.append("B")
		w.append("C")
		w.append("E")
		del w[1]
		self.assertTrue( "A" in w )
		self.assertTrue( "B" not in w )
		self.assertTrue( "C" in w )
		self.assertTrue( "E" in w )
		del w[1:3]
		self.assertEqual( len(w), 1 )
		self.assertTrue( "A" in w )
		del w[:]
		self.assertEqual( len(w), 0 )

	def testBracketOperators( self ) :

		w = GafferUI.MultiSelectionMenu()
		w.append("A")
		w.append("B")
		w.append("C")
		self.assertEqual( w[1], "B" )

		w[1] = "D"
		self.assertEqual( w[1], "D" )
		self.assertEqual( w.index("D"), 1 )

	def testAppendRemoveInsert( self ) :

		w = GafferUI.MultiSelectionMenu()
		w.append("A")
		w.append("B")
		w.append("C")

		# Check that the elements were inserted and the order kept.
		self.assertEqual( w[:], [ "A", "B", "C" ] )

		# Check that duplicates are not inserted and the order preserved.
		w.insert( 1, "C" )
		self.assertEqual( w[:], [ "A", "B", "C" ] )

		# Test removal.
		w.remove("B")
		self.assertFalse( "B" in w )

		# Check the order again.
		self.assertEqual( w[:], [ "A", "C" ] )

		# Check insertion.
		w.insert( 0, "E" )
		self.assertEqual( w[:], [ "E", "A", "C" ] )

	def testSelected( self ) :

		# Test that in multiple selection mode we can select multiple items!
		w = GafferUI.MultiSelectionMenu( allowMultipleSelection = True )
		w.append("A")
		w.append("B")
		w.append("D")

		# Check the return type
		self.assertTrue( isinstance( w.getSelection(), list ) )

		w.setSelection( ["A"] )
		self.assertEqual( w.getSelection(), ["A"] )

		# Test an item which doesn't exist. We expect an exception to be raised.
		try :
			w.setSelection( "C" )
			self.assertTrue( False )
		except :
			self.assertTrue( True )

		# Test the setting of a single variable.
		w.setSelection( "D" )
		self.assertEqual( w.getSelection(), ["D"] )

		# Test the appending of a single variable.
		w.addSelection( "A" )
		self.assertEqual( w.getSelection(), ["A", "D"] )

		# Test the appending of a multiple variables.
		w.setSelection( [] )
		self.assertEqual( w.getSelection(), [] )
		w.addSelection( ["A", "D"] )
		self.assertEqual( w.getSelection(), ["A", "D"] )

		# Test the setting of multiple variables.
		w.setSelection( ["A", "B"] )
		self.assertTrue( "A" in w.getSelection() )
		self.assertTrue( "B" in w.getSelection() )

		# Now test single item selection
		w = GafferUI.MultiSelectionMenu( allowMultipleSelection = False )
		w.append("A")
		w.append("B")
		w.append("C")

		# Test that we can use both arrays and single variables.
		# Also make sure that only one item can be selected because we are
		# not using multiple selection mode.
		w.setSelection( ["B"] )
		self.assertEqual( w.getSelection(), ["B"] )
		w.setSelection( "A" )
		self.assertEqual( w.getSelection(), ["A"] )

	def testEnabled( self ) :
		w = GafferUI.MultiSelectionMenu()
		w.append("A")
		w.append("B")

		# Test the return type
		self.assertTrue( isinstance( w.getEnabledItems(), list ) )

		# Test that a single element can be enabled.
		w.setEnabledItems( "A" )
		self.assertEqual( w.getEnabledItems(), ["A"] )
		self.assertEqual( w.getEnabledItems(), ["A"] )

		# Test that multiple elements can be enabled.
		w.setEnabledItems( ["A", "B"] )
		self.assertTrue( "A" in w.getEnabledItems() )
		self.assertTrue( "B" in w.getEnabledItems() )

if __name__ == "__main__":
	unittest.main()
