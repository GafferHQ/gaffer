##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
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
import sys
import StringIO

import IECore

import Gaffer
import GafferUI
import GafferUITest

class EventSignalCombinerTest( GafferUITest.TestCase ) :

	def trueSlot( self, gadget, event ) :

		self.trueSlotCalled = True
		return True

	def falseSlot( self, gadget, event ) :

		self.falseSlotCalled = True
		return False

	def exceptionSlot( self, gadget, event ) :

		self.exceptionSlotCalled = True
		raise Exception( "oops" )

	def setUp( self ) :

		GafferUITest.TestCase.setUp( self )

		self.falseSlotCalled = False
		self.trueSlotCalled = False
		self.exceptionSlotCalled = False

	def testShortCutting( self ) :

		s = GafferUI.Gadget.ButtonSignal()
		c1 = s.connect( self.trueSlot )
		c2 = s.connect( self.falseSlot )

		self.assertEqual( self.trueSlotCalled, False )
		self.assertEqual( self.falseSlotCalled, False )

		self.assertEqual( s( None, GafferUI.ButtonEvent() ), True )

		self.assertEqual( self.trueSlotCalled, True )
		self.assertEqual( self.falseSlotCalled, False )

	def testNoShortCutting( self ) :

		s = GafferUI.Gadget.ButtonSignal()
		c1 = s.connect( self.falseSlot )
		c2 = s.connect( self.trueSlot )

		self.assertEqual( self.trueSlotCalled, False )
		self.assertEqual( self.falseSlotCalled, False )

		self.assertEqual( s( None, GafferUI.ButtonEvent() ), True )

		self.assertEqual( self.trueSlotCalled, True )
		self.assertEqual( self.falseSlotCalled, True )

	def testExceptionHandling( self ) :

		# We don't want exceptions in one slot to prevent the
		# invocation of other slots. But we do want the errors from
		# those slots being printed to stderr.

		s = GafferUI.Gadget.ButtonSignal()
		c1 = s.connect( self.exceptionSlot )
		c2 = s.connect( self.trueSlot )

		self.assertEqual( self.exceptionSlotCalled, False )
		self.assertEqual( self.trueSlotCalled, False )

		tmpStdErr = StringIO.StringIO()
		sys.stderr = tmpStdErr
		try :
			self.assertEqual( s( None, GafferUI.ButtonEvent() ), True )
		finally :
			sys.stderr = sys.__stderr__

		self.assertIn( "oops", tmpStdErr.getvalue() )
		self.assertEqual( self.exceptionSlotCalled, True )
		self.assertEqual( self.trueSlotCalled, True )

if __name__ == "__main__":
	unittest.main()
