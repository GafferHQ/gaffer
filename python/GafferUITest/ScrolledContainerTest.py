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
import GafferUI
import GafferUITest

class ScrolledContainerTest( GafferUITest.TestCase ) :

	@GafferTest.expectedFailure
	def testChildAccessors( self ) :

		s = GafferUI.ScrolledContainer()
		b = GafferUI.Button()

		s.setChild( b )
		self.assertEqual( s.getChild(), b )
		self.assertEqual( b.parent(), s )

		s.setChild( None )
		self.assertEqual( s.getChild(), None )
		self.assertEqual( b.parent(), None )

		s.setChild( b )
		self.assertEqual( s.getChild(), b )
		self.assertEqual( b.parent(), s )

		s.removeChild( b )
		self.assertEqual( s.getChild(), None )
		self.assertEqual( b.parent(), None )

	def testTransferChild( self ) :

		s = GafferUI.ScrolledContainer()
		l = GafferUI.ListContainer()
		b = GafferUI.Button()

		l.append( b )
		self.assertEqual( len( l ), 1 )

		s.setChild( b )
		self.assertTrue( b.parent() is s )
		self.assertTrue( s.getChild() is b )
		self.assertEqual( len( l ), 0 )

if __name__ == "__main__":
	unittest.main()
