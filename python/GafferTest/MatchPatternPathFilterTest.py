##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

class MatchPatternPathFilterTest( GafferTest.TestCase ) :

	def test( self ) :

		p = Gaffer.DictPath(
			{
				".hiddenFile" : "a",
				"a.exr" : "b",
				"b.tif" : "c",
			},
			"/",
		)

		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [ "/.hiddenFile", "/a.exr", "/b.tif" ] ) )

		p.setFilter( Gaffer.MatchPatternPathFilter( [ "*.exr" ] ) )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [ "/a.exr" ] ) )

		p.setFilter( Gaffer.MatchPatternPathFilter( [ "*" ] ) )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [ "/.hiddenFile", "/a.exr", "/b.tif" ] ) )

		p.setFilter( Gaffer.MatchPatternPathFilter( [ ".*" ] ) )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [ "/.hiddenFile" ] ) )

	def testAttributeName( self ) :

		p = Gaffer.DictPath(
			{
				"b" : "aardvark",
				"a" : "bison",
			},
			"/"
		)

		p.setFilter( Gaffer.MatchPatternPathFilter( [ "a*" ] ) )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [ "/a" ] ) )

		p.setFilter( Gaffer.MatchPatternPathFilter( [ "a*" ], "dict:value" ) )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [ "/b" ] ) )

	def testPatternAccessors( self ) :

		f = Gaffer.MatchPatternPathFilter( [ "a", "b", "c" ] )
		self.assertEqual( f.getMatchPatterns(), [ "a", "b", "c" ] )

		f.setMatchPatterns( [ "d", "e" ] )
		self.assertEqual( f.getMatchPatterns(), [ "d", "e" ] )

	def testInverted( self ) :

		p = Gaffer.DictPath(
			{
				"a" : "aardvark",
				"b" : "bison",
			},
			"/"
		)

		f = Gaffer.MatchPatternPathFilter( [ "a*" ] )
		p.setFilter( f )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [ "/a" ] ) )

		f.setInverted( True )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [ "/b" ] ) )

if __name__ == "__main__":
	unittest.main()
