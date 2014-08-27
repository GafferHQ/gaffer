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

import IECore

import Gaffer
import GafferTest

class OrphanRemoverTest( GafferTest.TestCase ) :

	def test( self ) :

		p = Gaffer.GraphComponent()
		c1 = Gaffer.GraphComponent()
		c2 = Gaffer.GraphComponent()
		p["c1"] = c1
		p["c2"] = c2

		s = Gaffer.StandardSet( p.children() )
		b = Gaffer.Behaviours.OrphanRemover( s )

		self.assertEqual( len( s ), 2 )
		self.assertTrue( c1 in s )
		self.assertTrue( c2 in s )

		p.removeChild( c1 )

		self.assertEqual( len( s ), 1 )
		self.assertFalse( c1 in s )
		self.assertTrue( c2 in s )

		p["c1"] = c1

		self.assertEqual( len( s ), 1 )
		self.assertFalse( c1 in s )
		self.assertTrue( c2 in s )

		s.add( c1 )

		self.assertEqual( len( s ), 2 )
		self.assertTrue( c1 in s )
		self.assertTrue( c2 in s )

		p.removeChild( c1 )

		self.assertEqual( len( s ), 1 )
		self.assertFalse( c1 in s )
		self.assertTrue( c2 in s )

		p.removeChild( c2 )

		self.assertEqual( len( s ), 0 )
		self.assertFalse( c1 in s )
		self.assertFalse( c2 in s )

		c3 = Gaffer.GraphComponent()
		s.add( c3 )

		self.assertEqual( len( s ), 1 )
		self.assertFalse( c1 in s )
		self.assertFalse( c2 in s )
		self.assertTrue( c3 in s )

		p["c3"] = c3

		self.assertEqual( len( s ), 1 )
		self.assertFalse( c1 in s )
		self.assertFalse( c2 in s )
		self.assertTrue( c3 in s )

		p.removeChild( c3 )

		self.assertEqual( len( s ), 0 )
		self.assertFalse( c1 in s )
		self.assertFalse( c2 in s )
		self.assertFalse( c3 in s )

		p["c3"] = c3
		s.add( c3 )

		self.assertEqual( len( s ), 1 )
		self.assertFalse( c1 in s )
		self.assertFalse( c2 in s )
		self.assertTrue( c3 in s )

		del b
		p.removeChild( c3 )

		self.assertEqual( len( s ), 1 )
		self.assertFalse( c1 in s )
		self.assertFalse( c2 in s )
		self.assertTrue( c3 in s )

	def testImportFrom( self ) :

		from Gaffer.Behaviours import OrphanRemover

		self.assertTrue( OrphanRemover is Gaffer.Behaviours.OrphanRemover )

if __name__ == "__main__":
	unittest.main()
