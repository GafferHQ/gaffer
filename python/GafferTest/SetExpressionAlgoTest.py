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

	def testSimplify( self ) :

		s = SetExpressionAlgoTest.MySetProvider()

		for expression, result in [
			( "", "" ),
			( "A", "A" ),
			( "A A", "A" ),
			( "A B", "A B" ),
			( "A A*", "A A*" ),
			( "((A))", "A" ),
			( "A & A", "A" ),
			( "A in A", "A" ),
			( "A containing A", "A" ),

			( "A - A", "" ),
			( "A - B", "A - B" ),
			( "(A & B) - A", "" ),
			( "(A & B) - B", "" ),
			( "(A & B) - C", "(A & B) - C" ),
			( "(A in B) - A", "" ),
			( "(A in B) - B", "(A in B) - B" ),
			( "(A in B) - C", "(A in B) - C" ),
			( "(A containing B) - A", "" ),
			( "(A containing B) - B", "(A containing B) - B" ),
			( "(A containing B) - C", "(A containing B) - C" ),
			( "(A B) - A", "B - A" ),
			( "(A B) - B", "A - B" ),
			( "(A B) - C", "(A B) - C" ),

			( "A B A B", "A B" ),
			( "(A B) (A B)", "A B" ),
			( "((A B) (C A))", "A B C" ),
			( "B A C A C B", "B A C" ),
			( "((A B) (C (D E)))", "A B C D E" ),

			( "A & B A & B", "A & B" ),
			( "A & B B & A", "A & B" ),
			( "A & B & B & A", "A & B" ),
			( "(A & (B & C))", "A & B & C" ),
			( "(A B) & (A B C)", "A B" ),
			( "(A B B C) & (A B A C C D)", "A B C" ),
			( "(A & (A B))", "A" ),
			( "A (A & B)", "A" ),
			( "A A & B", "A" ),
			( "B (A & B)", "B" ),
			( "B A & B", "B" ),

			( "(A in B) & A", "A in B" ),
			( "(A in B) & B", "(A in B) & B" ),
			( "(A containing B) & A", "A containing B" ),
			( "(A containing B) & B", "(A containing B) & B" ),

			( "(A in B) - (A B)", "" ),
			( "(A in B) - (A C)", "" ),
			( "(A in B) - (B C)", "(A in B) - (B C)" ),
			( "(A in B) (A in B)", "A in B" ),
			( "(A in B) (B in A)", "(A in B) (B in A)" ),
			( "(A in B) (A & B) (A in B)", "(A in B) A & B" ),
			( "(A in B) containing (B in A)", "(A in B) containing (B in A)" ),
			( "(A in B) containing (A in B)", "A in B" ),
			( "(A in B) in (B in A)", "(A in B) in (B in A)" ),
			( "(A in B) in (A in B)", "A in B" ),
			( "(A in B) in C", "(A in B) in C" ),
			( "(A in B) (C in D)", "(A in B) (C in D)" ),
			## \todo Consider simplifying the below to "(A C D) in B".
			( "(((A in B) (C in B)) (D in B))", "(A in B) (C in B) (D in B)" ),

			( "(A containing B) (A containing B)", "A containing B" ),
			( "(A containing B) (B containing A)", "(A containing B) (B containing A)" ),
			( "(A containing B) (A in B) (A containing B)", "(A containing B) (A in B)" ),
			( "(A containing B) (A in B) (A containing B) (A in B)", "(A containing B) (A in B)" ),
			( "A containing B in B containing A", "(A containing B) in (B containing A)" ),
			( "A containing B in A containing B", "A containing B" ),

			( "((A in B) containing B) - A", "" ),
			( "((A in B) containing B) - B", "((A in B) containing B) - B" ),
			( "((A in B) containing B) - C", "((A in B) containing B) - C" ),

			( "((A - B) containing B) - A", "" ),
			( "((A - B) containing B) - B", "((A - B) containing B) - B" ),
			( "((A - B) containing B) - C", "((A - B) containing B) - C" ),

			( "((A & B) containing B) - A", "" ),
			( "((A & B) containing B) - B", "" ),
			( "((A & B) containing B) - C", "((A & B) containing B) - C" ),
			( "((A & B) containing B) - (A C)", "" ),
			( "((A & B) containing B) - (A & B)", "" ),
			( "((A & B) containing B) - (A - B)", "((A & B) containing B) - (A - B)" ),

			( "(((A & D) & (B in C)) containing B) - A", "" ),
			( "(A (A - B) (A & B) (A in B) (A containing B)) - A", "" ),
			( "(A (A - B) (A & B) (A in B) (A containing B)) - B", "A - B" ),

			( "A - B - C", "A - (B C)" ),
			( "A - (B - C)", "A - (B - C)" ),
			( "A (B - C)", "A B - C" ),
			( "A - B - C - B", "A - (B C)" ),
			( "A - (A B C)", "" ),
			( "A - (A - B)", "A - (A - B)" ),

			( "A - (B - C) - B", "A - B" ),
			( "A - (B - C) - D", "A - (B - C D)" ),
			( "(A - B) - (C B)", "A - (C B)" ),
			( "(A - B) - (C D)", "A - (B C D)" ),
			( "(((A - B) - C) - D)", "A - (B C D)" ),

			( "A - (B & C)", "A - (B & C)" ),
			( "A - (B & C) - B", "A - B" ),
			( "A - (B (B & C))", "A - B" ),

			( "A B - C A B", "A B" ),
			( "A - C B - C", "A - C B - C" ),
			( "(A - C) (B - C)", "A - C B - C" ),

			( "(A B) - A - B", "" ),
			( "(A B) - (A B)", "" ),
			( "(A B) - (B A)", "" ),
			( "(A B) - (A C)", "B - (A C)"),
			( "(A B) - (C A B)", "" ),
			( "(A B) - (A - B)", "(A B) - (A - B)" ),
			( "(A B) - (A & B)", "(A B) - (A & B)" ),
			( "(A B) - (A in B)", "(A B) - (A in B)" ),
			( "(A B) - (A containing B)", "(A B) - (A containing B)" ),

			( "(A B C) - A - B", "C - (A B)" ),
			( "(A B C) - A", "(B C) - A" ),
			( "(A B C) - (A B C)", "" ),
			( "(A B C) - (C A B)", "" ),
			( "(A B C D) - B", "(A C D) - B" ),
			( "(A B C) - (B & A)", "(A B C) - (B & A)"),
			( "(A (B C)) - B", "(A C) - B" ),
			( "(A (B C)) - C", "(A B) - C" ),

			( "((A B) - C) - D", "(A B) - (C D)" ),
			( "((A - B) - C) - D", "A - (B C D)" ),
			( "A - B - C D", "A - (B C) D" ),

			( "(A & B) - (A & B)", "" ),
			( "(A & B) - (B & A)", "" ),
			( "(A & B) - (A & C)", "(A & B) - (A & C)" ),
			( "(A & B) - (A C)", "" ),
			( "(A & B) - (A B)", "" ),
			( "(A & B) - (C B)", "" ),
			( "(((A & B) & (C in D)) containing E) - A", "" ),
			( "((A & B) (A & C)) - A", "" ),
			( "A & B - C - C", "A & B - C" ),
			( "(A A & B) - A", "" ),
			( "(A A & B) - (A & B)", "A - (A & B)" ),

			( "A /a - /a", "A" ),
			( "A /b - /a", "A /b - /a" ),
			( "(A /a) - /a", "A - /a" ),
			( "(A /a) - A", "/a - A" ),
			( "(A /a) - (B /a)", "A - (B /a)" ),
			( "(A /a) - (B /b)", "(A /a) - (B /b)" ),

			( "(A & (B in C)) - A", "" ),
			( "(A & (B in C)) - B", "" ),
			( "(A & (B in C)) - C", "(A & (B in C)) - C" ),

			( "((A & B) containing C) - A", "" ),
			( "((A & B) containing C) - B", "" ),
			( "((A & B) containing C) - C", "((A & B) containing C) - C" ),
			( "((A & B) containing C) - (A B)", "" ),
			( "((A & B) containing C) - (A & B)", "" ),
			( "((A & B) containing C) - (A - B)", "((A & B) containing C) - (A - B)" ),

			( "((A & B) C) - A", "C - A" ),
			( "((A & B) C) - B", "C - B" ),
			( "((A & B) C) - C", "(A & B) - C" ),

			( "C in (((D A B A) - A) & B)", "C in ((D B) - A & B)" ),
		] :
			with self.subTest( expression = expression, result = result ) :
				simplified = Gaffer.SetExpressionAlgo.simplify( expression )
				self.assertEqual( simplified, result )
				# Our simplified expression cannot be further simplified.
				self.assertEqual( Gaffer.SetExpressionAlgo.simplify( simplified ), simplified )
				# Our simplified expression should evaluate to the same result as the original.
				self.assertEqual( Gaffer.SetExpressionAlgo.evaluateSetExpression( expression, s ), Gaffer.SetExpressionAlgo.evaluateSetExpression( simplified, s ) )

	def testInclude( self ) :

		s = SetExpressionAlgoTest.MySetProvider()

		for base, inclusions, result in [
			( "", "", "" ),
			( "A", "A", "A" ),
			( "", "A", "A" ),
			( "A", "", "A" ),
			( "A*", "A", "A* A" ),
			( "A", "A*", "A A*" ),
			( "", "A B", "A B"),
			( "A B", "", "A B"),
			( "A | B", "A B", "A B" ),
			( "A | B", "B A", "B A" ),
			( "B A", "A B", "A B" ),
			( "B A", "B | A", "B A" ),
			( "B A", "B | A B", "B A" ),
			( "B B A", "A B", "A B" ),
			( "B B A A", "A", "B A" ),
			( "B (B A) A", "B", "A B" ),

			( "A B C", "C", "A B C" ),
			( "A B C", "D", "A B C D" ),
			( "A B C", "C D", "A B C D" ),
			( "A B C", "A & B", "A B C" ),
			( "A B", "C & D", "A B C & D" ),
			( "A B C", "C & D", "A B C" ),
			( "A B", "C - D", "A B C - D" ),
			( "A B C", "C - D", "A B C" ),
			( "A B", "C in D", "A B (C in D)" ),
			( "A B C", "C in D", "A B C" ),
			( "A B C", "D in C", "A B C (D in C)" ),
			( "A B", "C containing D", "A B (C containing D)" ),
			( "A B C", "C containing D", "A B C" ),
			( "A B C", "D containing C", "A B C (D containing C)" ),

			( "A - A", "A", "A" ),
			( "A - A", "A & B", "A & B" ),
			( "A - A", "A in B", "A in B" ),
			( "A - A", "A containing B", "A containing B" ),
			( "A - A", "B", "B" ),
			( "A - A", "B - C", "B - C" ),

			( "A - B", "A", "A" ),
			( "A - B", "B", "A B" ),
			( "A - B", "B - C", "A - B B - C" ),
			( "A - B", "B & C", "A - B B & C" ),
			( "A - B", "B in C", "A - B (B in C)" ),
			( "A - B", "B containing C", "A - B (B containing C)" ),

			( "A & B", "A", "A" ),
			( "A & B", "B", "B" ),
			( "A & B", "C", "A & B C" ),
			( "A & B", "A B", "A B" ),
			( "A & B", "A & B", "A & B" ),
			( "A & B", "B & A", "A & B" ),

			( "A in B", "A", "A" ),
			( "A in B", "B", "(A in B) B" ),
			( "A in B", "C", "(A in B) C" ),
			( "A in B", "A in B", "A in B" ),
			( "A in B", "B in A", "(A in B) (B in A)" ),
			( "A in B", "C in D", "(A in B) (C in D)" ),
			## \todo Consider simplifying the below to "(A C) in B".
			( "A in B", "C in B", "(A in B) (C in B)" ),
			( "A in B", "(A in B) (C in D)", "(A in B) (C in D)" ),

			( "A containing B", "A", "A" ),
			( "A containing B", "B", "(A containing B) B" ),
			( "A containing B", "C", "(A containing B) C" ),
			( "A containing B", "A containing B", "A containing B" ),
			( "A containing B", "B containing A", "(A containing B) (B containing A)" ),
			( "A containing B", "B containing C", "(A containing B) (B containing C)" ),
			## \todo Consider simplifying the below to "(A C) containing B".
			( "A containing B", "C containing B", "(A containing B) (C containing B)" ),
			( "A containing B", "(A containing B) (B containing C)", "(A containing B) (B containing C)" ),

			( "A - B C", "A", "C A" ),
			( "A - B C", "B", "A C B" ),
			( "A - B C", "C", "A - B C" ),
			( "A - B C", "D", "A - B C D" ),
			( "A - B C", "A B", "C A B" ),
			( "A - B C", "A C", "A C" ),
			( "A - B C", "B C", "A B C" ),
			( "A - B C", "C B", "A C B" ),
			( "A - B C", "A D", "C A D" ),
			( "A - B C", "B D", "A C B D" ),
			( "A - B C", "C D", "A - B C D" ),

			( "A - (B C)", "A", "A" ),
			( "A - (B C)", "B", "A - C B" ),
			( "A - (B C)", "C", "A - B C" ),
			( "A - (B C)", "D", "A - (B C) D" ),
			( "A - (B C)", "A B", "A B" ),
			( "A - (B C)", "A C", "A C" ),
			( "A - (B C)", "B C", "A B C" ),
			( "A - (B C)", "C B", "A C B" ),
			( "A - (B C)", "A D", "A D" ),
			( "A - (B C)", "B D", "A - C B D" ),
			( "A - (B C)", "C D", "A - B C D" ),

			( "A - (B - C)", "A", "A" ),
			( "A - (B - C)", "B", "A B" ),
			( "A - (B - C)", "C", "A - B C" ),
			( "A - (B - C)", "D", "A - (B - C) D" ),
			( "A - (B - C)", "A B", "A B" ),
			( "A - (B - C)", "A C", "A C" ),
			( "A - (B - C)", "B C", "A B C" ),
			( "A - (B - C)", "C B", "A C B" ),
			( "A - (B - C)", "A D", "A D" ),
			( "A - (B - C)", "B D", "A B D" ),

			( "A - (B & C)", "A", "A" ),
			( "A - (B & C)", "B", "A B" ),
			( "A - (B & C)", "C", "A C" ),
			( "A - (B & C)", "D", "A - (B & C) D" ),
			( "A - (B & C)", "B C", "A B C" ),
			( "A - (B & C)", "B & C", "A B & C" ),

			( "A - (B in C)", "A", "A" ),
			( "A - (B in C)", "B", "A B" ),
			( "A - (B in C)", "C", "A - (B in C) C" ),
			( "A - (B in C)", "D", "A - (B in C) D" ),
			( "A - (B in C)", "B in C", "A (B in C)" ),
			( "A - (B in C)", "B containing C", "A - (B in C) (B containing C)" ),
			( "A - (B in C)", "(B in C) (C containing D)", "A (B in C) (C containing D)" ),
			( "A - (B in C)", "B in C C containing D", "A - (B in C) (B in (C containing D))" ),

			( "A - (B containing C)", "A", "A" ),
			( "A - (B containing C)", "B", "A B" ),
			( "A - (B containing C)", "C", "A - (B containing C) C" ),
			( "A - (B containing C)", "D", "A - (B containing C) D" ),
			( "A - (B containing C)", "B in C", "A - (B containing C) (B in C)" ),
			( "A - (B containing C)", "B containing C", "A (B containing C)" ),

			( "(A B) - C", "A", "B - C A" ),
			( "(A B) - C", "B", "A - C B" ),
			( "(A B) - C", "C", "A B C" ),
			( "(A B) - C", "D", "(A B) - C D" ),
			( "(A B) - C", "A B", "A B" ),
			( "(A B) - C", "A C", "B A C" ),
			( "(A B) - C", "B C", "A B C" ),

			( "(A B) - C D", "A", "B - C D A" ),
			( "(A B) - C D", "B", "A - C D B" ),
			( "(A B) - C D", "C", "A B D C" ),
			( "(A B) - C D", "D", "(A B) - C D" ),
			( "(A B) - C D", "E", "(A B) - C D E" ),
			( "(A B) - C D", "A B", "D A B" ),
			( "(A B) - C D", "A C", "B D A C" ),
			( "(A B) - C D", "A D", "B - C A D" ),
			( "(A B) - C D", "B C", "A D B C" ),
			( "(A B) - C D", "B D", "A - C B D" ),

			( "(A B) - (C D)", "A", "B - (C D) A" ),
			( "(A B) - (C D)", "B", "A - (C D) B" ),
			( "(A B) - (C D)", "C", "(A B) - D C" ),
			( "(A B) - (C D)", "D", "(A B) - C D" ),
			( "(A B) - (C D)", "E", "(A B) - (C D) E" ),
			( "(A B) - (C D)", "A B", "A B" ),
			( "(A B) - (C D)", "C D", "A B C D" ),
			( "(A B) - (C D)", "A C", "B - D A C" ),
			( "(A B) - (C D)", "A D", "B - C A D" ),
			( "(A B) - (C D)", "B C", "A - D B C" ),
			( "(A B) - (C D)", "B D", "A - C B D" ),

			( "(A B) - (A C)", "A", "B - C A" ),
			( "(A B) - (A C)", "B", "B" ),
			( "(A B) - (A C)", "A B", "A B" ),
			( "(A B) - (A C)", "A C", "B A C" ),
			( "(A B) - (A C)", "B C", "B C" ),

			( "(A & B) - C", "A", "A" ),
			( "(A & B) - C", "B", "B" ),
			( "(A & B) - C", "C", "A & B C" ),
			( "(A & B) - C", "D", "(A & B) - C D" ),
			( "(A & B) - C", "A B", "A B" ),
			( "(A & B) - C", "A C", "A C" ),
			( "(A & B) - C", "B C", "B C" ),
			( "(A & B) - C", "A D", "A D" ),
			( "(A & B) - C", "B D", "B D" ),
			( "(A & B) - C", "C D", "A & B C D" ),

			( "A & B - C", "A", "A" ),
			( "A & B - C", "B", "B" ),
			( "A & B - C", "C", "A & B C" ),
			( "A & B - C", "D", "A & B - C D" ),

			( "(A B) & C", "A", "B & C A" ),
			( "(A B) & C", "B", "A & C B" ),
			( "(A B) & C", "C", "C" ),
			( "(A B) & C", "D", "(A B) & C D" ),
			( "(A B) & C", "A B", "A B" ),
			( "(A B) & C", "A C", "A C" ),
			( "(A B) & C", "B C", "B C" ),
			( "(A B) & C", "A B C", "A B C" ),

			( "(A B) & (C D)", "A", "B & (C D) A" ),
			( "(A B) & (C D)", "B", "A & (C D) B" ),
			( "(A B) & (C D)", "C", "(A B) & D C" ),
			( "(A B) & (C D)", "D", "(A B) & C D" ),
			( "(A B) & (C D)", "E", "(A B) & (C D) E" ),
			( "(A B) & (C D)", "A B", "A B" ),
			( "(A B) & (C D)", "A C", "B & D A C" ),
			( "(A B) & (C D)", "B C", "A & D B C" ),
			( "(A B) & (C D)", "A B C", "A B C" ),

			( "(A B) - A", "A", "B A" ),
			( "(A B) - A", "B", "B" ),
			( "(A B) - A", "C", "B - A C" ),

			( "A in (B C containing (D - (E & F))) G & (H in I J) - K", "A", "A" ),
			( "A in (B C containing (D - (E & F))) G & (H in I J) - K", "B", "(A in (((B C) containing (D - (E & F))) G & (H in (I J)) - K)) B" ),
			( "A in (B C containing (D - (E & F))) G & (H in I J) - K", "C", "(A in (((B C) containing (D - (E & F))) G & (H in (I J)) - K)) C" ),
			( "A in (B C containing (D - (E & F))) G & (H in I J) - K", "D", "(A in (((B C) containing (D - (E & F))) G & (H in (I J)) - K)) D" ),
			( "A in (B C containing (D - (E & F))) G & (H in I J) - K", "E", "(A in (((B C) containing (D - (E & F))) G & (H in (I J)) - K)) E" ),
			( "A in (B C containing (D - (E & F))) G & (H in I J) - K", "F", "(A in (((B C) containing (D - (E & F))) G & (H in (I J)) - K)) F" ),
			( "A in (B C containing (D - (E & F))) G & (H in I J) - K", "G", "(A in (((B C) containing (D - (E & F))) G & (H in (I J)) - K)) G" ),
			( "A in (B C containing (D - (E & F))) G & (H in I J) - K", "H", "(A in (((B C) containing (D - (E & F))) G & (H in (I J)) - K)) H" ),
			( "A in (B C containing (D - (E & F))) G & (H in I J) - K", "I", "(A in (((B C) containing (D - (E & F))) G & (H in (I J)) - K)) I" ),
			( "A in (B C containing (D - (E & F))) G & (H in I J) - K", "J", "(A in (((B C) containing (D - (E & F))) G & (H in (I J)) - K)) J" ),
			( "A in (B C containing (D - (E & F))) G & (H in I J) - K", "K", "(A in (((B C) containing (D - (E & F))) G & (H in (I J)) - K)) K" ),
			( "A in (B C containing (D - (E & F))) G & (H in I J) - K", "L", "(A in (((B C) containing (D - (E & F))) G & (H in (I J)) - K)) L" ),

			( "(A in (B C containing (D - (E & F)))) G & (H in I J) - K", "A", "G & (H in (I J)) - K A" ),
			( "(A in (B C containing (D - (E & F)))) G & (H in I J) - K", "B", "(A in ((B C) containing (D - (E & F)))) G & (H in (I J)) - K B" ),
			( "(A in (B C containing (D - (E & F)))) G & (H in I J) - K", "C", "(A in ((B C) containing (D - (E & F)))) G & (H in (I J)) - K C" ),
			( "(A in (B C containing (D - (E & F)))) G & (H in I J) - K", "D", "(A in ((B C) containing (D - (E & F)))) G & (H in (I J)) - K D" ),
			( "(A in (B C containing (D - (E & F)))) G & (H in I J) - K", "E", "(A in ((B C) containing (D - (E & F)))) G & (H in (I J)) - K E" ),
			( "(A in (B C containing (D - (E & F)))) G & (H in I J) - K", "F", "(A in ((B C) containing (D - (E & F)))) G & (H in (I J)) - K F" ),
			( "(A in (B C containing (D - (E & F)))) G & (H in I J) - K", "G", "(A in ((B C) containing (D - (E & F)))) G" ),
			( "(A in (B C containing (D - (E & F)))) G & (H in I J) - K", "H", "(A in ((B C) containing (D - (E & F)))) H" ),
			( "(A in (B C containing (D - (E & F)))) G & (H in I J) - K", "I", "(A in ((B C) containing (D - (E & F)))) G & (H in (I J)) - K I" ),
			( "(A in (B C containing (D - (E & F)))) G & (H in I J) - K", "J", "(A in ((B C) containing (D - (E & F)))) G & (H in (I J)) - K J" ),
			( "(A in (B C containing (D - (E & F)))) G & (H in I J) - K", "K", "(A in ((B C) containing (D - (E & F)))) G & (H in (I J)) K" ),
			( "(A in (B C containing (D - (E & F)))) G & (H in I J) - K", "L", "(A in ((B C) containing (D - (E & F)))) G & (H in (I J)) - K L" ),

			( "A", "/a", "A /a" ),
			( "A /a", "/a", "A /a" ),
			( "A - /a", "/a", "A /a" ),
			( "A /a", "/b", "A /a /b" ),

		] :
			with self.subTest( base = base, inclusions = inclusions, result = result ) :

				included = Gaffer.SetExpressionAlgo.include( base, inclusions )
				self.assertEqual( included, result )
				# The new set expression should be already simplified.
				self.assertEqual( included, Gaffer.SetExpressionAlgo.simplify( included ) )
				# Including `inclusions` a second time should result in no change to the expression.
				self.assertEqual( included, Gaffer.SetExpressionAlgo.include( included, inclusions ) )

				# Test that the modified set expression matches the expected paths.
				testPaths = Gaffer.SetExpressionAlgo.evaluateSetExpression( base, s )
				testPaths.addPaths( Gaffer.SetExpressionAlgo.evaluateSetExpression( inclusions, s ) )
				self.assertEqual( Gaffer.SetExpressionAlgo.evaluateSetExpression( included, s ), testPaths )

	def testExclude( self ) :

		s = SetExpressionAlgoTest.MySetProvider()

		for base, exclusions, result in [
			( "", "", "" ),
			( "A", "A", "" ),
			( "", "A", "" ),
			( "A", "", "A" ),
			( "A*", "A", "A* - A" ),
			( "A", "A*", "A - A*" ),
			( "", "A B", ""),
			( "A B", "", "A B"),
			( "A B", "A B", "" ),
			( "A B", "B A", "" ),
			( "A B", "B A C", "" ),
			( "A B", "A", "B - A" ),
			( "A B", "B", "A - B" ),
			( "A B", "B B", "A - B" ),
			( "A B B", "B", "A - B" ),
			( "A B A B", "B", "A - B" ),
			( "A (B A) B", "B", "A - B" ),

			( "A B C", "A", "(B C) - A" ),
			( "A B C", "B", "(A C) - B" ),
			( "A B C", "C", "(A B) - C" ),
			( "A B C", "D", "(A B C) - D" ),
			( "A B C", "B C", "A - (B C)" ),
			( "A B C", "A C", "B - (A C)" ),
			( "A B C", "A B", "C - (A B)" ),
			( "A B C", "C D", "(A B) - (C D)" ),
			( "A B C", "C & D", "(A B C) - (C & D)" ),
			( "A B C", "C in D", "(A B C) - (C in D)" ),
			( "A B C", "D in C", "(A B C) - (D in C)" ),
			( "A B C", "C containing D", "(A B C) - (C containing D)" ),
			( "A B C", "D containing C", "(A B C) - (D containing C)" ),

			( "A - B", "A", "" ),
			( "A - B", "A & B", "A - B" ),
			( "A - B", "A in B", "A - (B (A in B))" ),
			( "A - B", "A containing B", "A - (B (A containing B))" ),
			( "A - B", "A B", "" ),
			( "A - B", "A - B", "" ),
			( "A - B", "B", "A - B" ),
			( "A - B", "C", "A - (B C)" ),
			( "A - B", "C - D", "A - (B C - D)" ),
			( "A - B", "C & D", "A - (B C & D)" ),
			( "A - B", "C in D", "A - (B (C in D))" ),
			( "A - B", "C containing D", "A - (B (C containing D))" ),

			( "A & B", "A", "" ),
			( "A & B", "B", "" ),
			( "A & B", "C", "(A & B) - C" ),
			( "A & B", "A B", "" ),
			( "A & B", "A & B", "" ),
			( "A & B", "B & A", "" ),
			( "A & B", "A in B", "(A & B) - (A in B)" ),
			( "A & B", "A containing B", "(A & B) - (A containing B)" ),

			( "A in B", "A", "" ),
			( "A in B", "B", "(A in B) - B" ),
			( "A in B", "C", "(A in B) - C" ),
			( "A in B", "A B", "" ),
			( "A in B", "B in A", "(A in B) - (B in A)" ),
			( "A in B", "(A in B) (C in D)", "" ),

			( "A containing B", "A", "" ),
			( "A containing B", "B", "(A containing B) - B" ),
			( "A containing B", "C", "(A containing B) - C" ),
			( "A containing B", "A B", "" ),
			( "A containing B", "A & B", "(A containing B) - (A & B)" ),
			( "A containing B", "B & A", "(A containing B) - (B & A)" ),
			( "A containing B", "A in B", "(A containing B) - (A in B)" ),
			( "A containing B", "B in A", "(A containing B) - (B in A)" ),
			( "A containing B", "B containing A", "(A containing B) - (B containing A)" ),
			( "A containing B", "B containing C", "(A containing B) - (B containing C)" ),
			( "A containing B", "(A containing B) (B containing C)", "" ),

			( "A - B C", "A", "C - A" ),
			( "A - B C", "B", "(A C) - B" ),
			( "A - B C", "C", "A - (B C)" ),
			( "A - B C", "D", "(A - B C) - D" ),
			( "A - B C", "A B", "C - (A B)" ),
			( "A - B C", "A C", "" ),
			( "A - B C", "B C", "A - (B C)" ),
			( "A - B C", "A D", "C - (A D)" ),
			( "A - B C", "B D", "(A C) - (B D)" ),
			( "A - B C", "C D", "A - (B C D)" ),

			( "A - (B C)", "A", "" ),
			( "A - (B C)", "B", "A - (C B)" ),
			( "A - (B C)", "C", "A - (B C)" ),
			( "A - (B C)", "D", "A - (B C D)" ),
			( "A - (B C)", "A B", "" ),
			( "A - (B C)", "A C", "" ),
			( "A - (B C)", "A D", "" ),
			( "A - (B C)", "B C", "A - (B C)" ),
			( "A - (B C)", "B D", "A - (C B D)" ),

			( "(A - (B - C))", "A", "" ),
			( "(A - (B - C))", "B", "A - B" ),
			( "(A - (B - C))", "C", "A - (B C)" ),
			( "(A - (B - C))", "D", "A - (B - C D)" ),
			( "(A - (B - C))", "B C", "A - (B C)" ),
			( "(A - (B - C))", "B - C", "A - (B - C)" ),
			( "(A - (B - C))", "B & C", "A - (B - C B & C)" ),

			( "(A - (B & C))", "A", "" ),
			( "(A - (B & C))", "B", "A - B" ),
			( "(A - (B & C))", "C", "A - C" ),
			( "(A - (B & C))", "D", "A - (B & C D)" ),
			( "(A - (B & C))", "A & B", "A - (B & C A & B)" ),
			( "(A - (B & C))", "B & C", "A - (B & C)" ),
			( "(A - (B & C))", "C & B", "A - (C & B)" ),
			## \todo Consider simplifying the below to "A - (B & (C D))".
			( "(A - (B & C))", "B & D", "A - (B & C B & D)" ),
			( "(A - (B & C))", "A & C", "A - (B & C A & C)" ),

			( "(A - (B in C))", "A", "" ),
			( "(A - (B in C))", "B", "A - B" ),
			( "(A - (B in C))", "C", "A - ((B in C) C)" ),
			( "(A - (B in C))", "D", "A - ((B in C) D)" ),
			( "(A - (B in C))", "B in C", "A - (B in C)" ),
			( "(A - (B in C))", "C in B", "A - ((B in C) (C in B))" ),

			( "(A - (B containing C))", "A", "" ),
			( "(A - (B containing C))", "B", "A - B" ),
			( "(A - (B containing C))", "C", "A - ((B containing C) C)" ),
			( "(A - (B containing C))", "D", "A - ((B containing C) D)" ),
			( "(A - (B containing C))", "B containing C", "A - (B containing C)" ),
			( "(A - (B containing C))", "C containing B", "A - ((B containing C) (C containing B))" ),

			( "(A B) - C", "A", "B - (C A)" ),
			( "(A B) - C", "B", "A - (C B)" ),
			( "(A B) - C", "C", "(A B) - C" ),
			( "(A B) - C", "D", "(A B) - (C D)" ),

			( "(A B) - C D", "A", "(B - C D) - A" ),
			( "(A B) - C D", "B", "(A - C D) - B" ),
			( "(A B) - C D", "C", "(A B D) - C" ),
			( "(A B) - C D", "D", "(A B) - (C D)" ),
			( "(A B) - C D", "E", "((A B) - C D) - E" ),

			( "(A B) - (C D)", "A", "B - (C D A)" ),
			( "(A B) - (C D)", "B", "A - (C D B)" ),
			( "(A B) - (C D)", "C", "(A B) - (D C)" ),
			( "(A B) - (C D)", "D", "(A B) - (C D)" ),
			( "(A B) - (C D)", "E", "(A B) - (C D E)" ),
			( "(A B) - (C D)", "A B", "" ),
			( "(A B) - (C D)", "C D", "(A B) - (C D)" ),
			( "(A B) - (C D)", "C D E", "(A B) - (C D E)" ),
			( "(A B) - (C D)", "A C", "B - (D A C)" ),
			( "(A B) - (C D)", "B D", "A - (C B D)" ),

			( "(A B) - (A C)", "A", "B - (C A)" ),
			( "(A B) - (A C)", "B", "" ),
			( "(A B) - (A C)", "C", "B - (A C)" ),
			( "(A B) - (A C)", "D", "B - (A C D)" ),
			( "(A B) - (A C)", "A C", "B - (A C)" ),
			( "(A B) - (A C)", "B C", "" ),

			( "(A & B) - C", "A", "" ),
			( "(A & B) - C", "B", "" ),
			( "(A & B) - C", "C", "(A & B) - C" ),
			( "(A & B) - C", "D", "(A & B) - (C D)" ),
			( "(A & B) - C", "A & B", "" ),
			( "(A & B) - C", "B & A", "" ),

			( "A & B - C", "A", "" ),
			( "A & B - C", "B", "" ),
			( "A & B - C", "C", "(A & B) - C" ),

			( "A & (B C)", "A", "" ),
			( "A & (B C)", "B", "(A & C) - B" ),
			( "A & (B C)", "C", "(A & B) - C" ),
			( "A & (B C)", "D", "(A & (B C)) - D" ),
			( "A & (B C)", "A B", "" ),
			( "A & (B C)", "B C", "" ),

			( "(A B) & C", "A", "(B & C) - A" ),
			( "(A B) & C", "B", "(A & C) - B" ),
			( "(A B) & C", "C", "" ),
			( "(A B) & C", "D", "((A B) & C) - D" ),
			( "(A B) & C", "A B", "" ),
			( "(A B) & C", "A B C", "" ),
			( "(A B) & C", "A D", "(B & C) - (A D)" ),

			( "A B in C", "A", "(B in C) - A" ),
			( "A B in C", "B", "(A in C) - B" ),
			( "A B in C", "C", "((A B) in C) - C" ),
			( "A B in C", "A B", "" ),
			( "A B in C", "A C", "(B in C) - (A C)" ),

			( "A (B in C)", "A", "(B in C) - A" ),
			( "A (B in C)", "B", "A - B" ),
			( "A (B in C)", "C", "(A (B in C)) - C" ),
			( "A (B in C)", "A B", "" ),
			( "A (B in C)", "A C", "(B in C) - (A C)" ),
			( "A (B in C)", "B C", "A - (B C)" ),
			( "A (B in C)", "A B C", "" ),

			( "A | B containing C", "A", "(B containing C) - A" ),
			( "A | B containing C", "B", "(A containing C) - B" ),
			( "A | B containing C", "C", "((A B) containing C) - C" ),
			( "A | B containing C", "D", "((A B) containing C) - D" ),
			( "A | B containing C", "A B", "" ),
			( "A | B containing C", "A C", "(B containing C) - (A C)" ),
			( "A | B containing C", "B C", "(A containing C) - (B C)" ),
			( "A | B containing C", "A B C", "" ),

			( "A | (B containing C)", "A", "(B containing C) - A" ),
			( "A | (B containing C)", "B", "A - B" ),
			( "A | (B containing C)", "C", "(A (B containing C)) - C" ),
			( "A | (B containing C)", "D", "(A (B containing C)) - D" ),
			( "A | (B containing C)", "A B", "" ),
			( "A | (B containing C)", "A C", "(B containing C) - (A C)" ),
			( "A | (B containing C)", "B C", "A - (B C)" ),
			( "A | (B containing C)", "A B C", "" ),

		] :
			with self.subTest( base = base, exclusions = exclusions, result = result ) :

				excluded = Gaffer.SetExpressionAlgo.exclude( base, exclusions )
				self.assertEqual( excluded, result )
				# The new set expression should be already simplified.
				self.assertEqual( excluded, Gaffer.SetExpressionAlgo.simplify( excluded ) )
				# Excluding `exclusions` a second time should result in no change to the expression.
				self.assertEqual( excluded, Gaffer.SetExpressionAlgo.exclude( excluded, exclusions ) )

				# Test that the modified set expression matches the expected paths.
				testPaths = Gaffer.SetExpressionAlgo.evaluateSetExpression( base, s )
				testPaths.removePaths( Gaffer.SetExpressionAlgo.evaluateSetExpression( exclusions, s ) )
				self.assertEqual( Gaffer.SetExpressionAlgo.evaluateSetExpression( excluded, s ), testPaths )

	def testIncludeAndExcludeSelf( self ) :

		for expression in (
			"",
			"A",
			"A B",
			"A - B",
			"A & B",
			"A in B",
			"A containing B",
			"(A - (B - C))",
			"(((A - B) - C) - D)",
			"(A - (B & C))",
			"(A - (B in C))",
			"(A - (B containing C))",
			"(A B) (C D)",
			"(A B) - (C D)",
			"(A B) & (C D)",
			"(A B) in (C D)",
			"(A B) containing (C D)",
			"(A & B) (C & D)",
			"(A & B) - (C & D)",
			"(A & B) in (C & D)",
			"(A & B) containing (C & D)",
			"A | B in C",
			"A | B containing C",
			"A & B in C",
			"A & B containing C",
			"A (B in C)",
			"A (B containing C)",
			"(((A & B) & (C in D)) containing E) - A",
			"A /pathA",
			"/pathA /pathB",
		) :
			with self.subTest( expression = expression ) :
				self.assertEqual( Gaffer.SetExpressionAlgo.exclude( expression, expression ), "" )
				self.assertEqual( Gaffer.SetExpressionAlgo.include( expression, expression ), Gaffer.SetExpressionAlgo.simplify( expression ) )

if __name__ == "__main__":
	unittest.main()
