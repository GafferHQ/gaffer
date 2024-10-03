##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

class PatternMatchTest( GafferTest.TestCase ) :

	def test( self ) :

		node = Gaffer.PatternMatch()

		for string, pattern, expectedResult in [
			( "a", "a", True ),
			( "a", "b", False ),
			( "b", "b", True ),
			( "a", "b a", True ),
			( "a1", "a[0-9]", True ),
			( "ab", "a[0-9]", False ),
			( "a", "*", True ),
		] :
			with self.subTest( string = string, pattern = pattern ) :
				node["string"].setValue( string )
				node["pattern"].setValue( pattern )
				self.assertEqual( node["match"].getValue(), expectedResult )

	def testDisabling( self ) :

		node = Gaffer.PatternMatch()
		self.assertTrue( node["match"].getValue() )
		node["enabled"].setValue( False )
		self.assertFalse( node["match"].getValue() )

if __name__ == "__main__":
	unittest.main()
