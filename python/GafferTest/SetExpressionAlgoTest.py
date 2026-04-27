##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

import IECore

import Gaffer
import GafferTest

class SetExpressionAlgoTest( GafferTest.TestCase ) :

	class MySetProvider( Gaffer.SetExpressionAlgo.SetProvider ) :

		def setNames( self ) :

			return IECore.InternedStringVectorData( [ "A", "B", "C", "D" ] )

		def paths( self, setName ) :

			if setName == "A" :
				return IECore.PathMatcher( [ "/a", "/a/a", "/a/b", "/a/c", "/b/a", "/c/a", "/1" ] )
			elif setName == "B" :
				return IECore.PathMatcher( [ "/b", "/a/b", "/b/b", "/b/c", "/c/b", "/1", "/2" ] )
			elif setName == "C" :
				return IECore.PathMatcher( [ "/c", "/a/c", "/b/c", "/c/a", "/c/b", "/c/c", "/1", "/2", "/3" ] )
			elif setName == "D" :
				return IECore.PathMatcher( [ "/d", "/1", "/2", "/3", "/4" ] )
			else :
				return IECore.PathMatcher()

		def hash( self, setName ) :

			if setName == "A" :
				return 1
			elif setName == "B" :
				return 2
			elif setName == "C" :
				return 3
			elif setName == "D" :
				return 4
			else :
				return 0

	def testSetProvider( self ) :

		s = SetExpressionAlgoTest.MySetProvider()

		self.assertEqual( Gaffer.SetExpressionAlgo.setExpressionHash( "A", s ), Gaffer.SetExpressionAlgo.setExpressionHash( "A", s ) )
		self.assertNotEqual( Gaffer.SetExpressionAlgo.setExpressionHash( "A", s ), Gaffer.SetExpressionAlgo.setExpressionHash( "B", s ) )
		self.assertEqual( Gaffer.SetExpressionAlgo.setExpressionHash( "EMPTY", s ), Gaffer.SetExpressionAlgo.setExpressionHash( "BOGUS", s ) )

		self.assertEqual( Gaffer.SetExpressionAlgo.evaluateSetExpression( "A", s ), s.paths( "A" ) )
		self.assertEqual( Gaffer.SetExpressionAlgo.evaluateSetExpression( "A", s ), IECore.PathMatcher( [ "/a", "/a/a", "/a/b", "/a/c", "/b/a", "/c/a", "/1" ] ) )
		self.assertEqual( Gaffer.SetExpressionAlgo.evaluateSetExpression( "B", s ), s.paths( "B" ) )
		self.assertEqual( Gaffer.SetExpressionAlgo.evaluateSetExpression( "B", s ), IECore.PathMatcher( [ "/b", "/a/b", "/b/b", "/b/c", "/c/b", "/1", "/2" ] ) )

		AplusB = s.paths( "A" )
		AplusB.addPaths( s.paths( "B") )
		self.assertEqual( Gaffer.SetExpressionAlgo.evaluateSetExpression( "A B", s ), AplusB )

		CminusA = s.paths( "C" )
		CminusA.removePaths( s.paths( "A" ) )
		self.assertEqual( Gaffer.SetExpressionAlgo.evaluateSetExpression( "C - A", s ), CminusA )

		self.assertEqual( Gaffer.SetExpressionAlgo.evaluateSetExpression( "EMPTY", s ), IECore.PathMatcher() )

		self.assertEqual( Gaffer.SetExpressionAlgo.evaluateSetExpression( "*", s ), IECore.PathMatcher( [ "/a", "/b", "/c", "/d", "/a/a", "/a/b", "/a/c", "/b/a", "/b/b", "/b/c", "/c/a", "/c/b", "c/c/", "/1", "/2", "/3", "/4" ] ) )

if __name__ == "__main__":
	unittest.main()
