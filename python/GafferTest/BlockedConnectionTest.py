##########################################################################
#
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferTest

class BlockedConnectionTest( GafferTest.TestCase ) :

	def test( self ) :

		self.numCalls = 0
		def f() :
			self.numCalls += 1

		s = Gaffer.Signals.Signal0()
		c = s.connect( f )

		s()
		self.assertEqual( self.numCalls, 1 )

		with Gaffer.Signals.BlockedConnection( c ) :
			s()

		self.assertEqual( self.numCalls, 1 )

		s()
		self.assertEqual( self.numCalls, 2 )

	def testReentrant( self ) :

		self.numCalls = 0
		def f() :
			self.numCalls += 1

		s = Gaffer.Signals.Signal0()
		c = s.connect( f )

		s()
		self.assertEqual( self.numCalls, 1 )

		with Gaffer.Signals.BlockedConnection( c ) :
			s()
			self.assertEqual( self.numCalls, 1 )
			with Gaffer.Signals.BlockedConnection( c ) :
				s()

		self.assertEqual( self.numCalls, 1 )

		s()
		self.assertEqual( self.numCalls, 2 )

		with Gaffer.Signals.BlockedConnection( c ) :
			s()
			self.assertEqual( self.numCalls, 2 )
			with Gaffer.Signals.BlockedConnection( c ) :
				s()

		self.assertEqual( self.numCalls, 2 )

		s()
		self.assertEqual( self.numCalls, 3 )

if __name__ == "__main__":
	unittest.main()
