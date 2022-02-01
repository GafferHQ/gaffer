##########################################################################
#
#  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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

class NumericBookmarkSetTest( GafferTest.TestCase ) :

	def testAccessors( self ) :

		s = Gaffer.ScriptNode()

		b = Gaffer.NumericBookmarkSet( s, 1 )

		self.assertEqual( b.getBookmark(), 1 )

		for i in range( 1, 10 ) :
			b.setBookmark( i )
			self.assertEqual( b.getBookmark(), i )

		for i in ( 0, 10 ) :
			with self.assertRaises( RuntimeError ) :
				b.setBookmark( i )

	def testBookmarkUpdates( self ) :

		s = Gaffer.ScriptNode()

		s["a"] = Gaffer.Node()
		s["b"] = Gaffer.Node()
		s["c"] = Gaffer.Node()

		b = Gaffer.NumericBookmarkSet( s, 1 )
		self.assertEqual( b.size(), 0 )

		Gaffer.MetadataAlgo.setNumericBookmark( s, 1, s["a"] )
		self.assertEqual( set(b), { s["a"] } )

		Gaffer.MetadataAlgo.setNumericBookmark( s, 1, s["b"] )
		self.assertEqual( set(b), { s["b"] } )

		Gaffer.MetadataAlgo.setNumericBookmark( s, 1, None )
		self.assertEqual( b.size(), 0 )

		Gaffer.MetadataAlgo.setNumericBookmark( s, 2, s["c"] )

		b2 = Gaffer.NumericBookmarkSet( s, 2 )
		self.assertEqual( set(b2), { s["c"] } )

		Gaffer.MetadataAlgo.setNumericBookmark( s, 2, s["a"] )
		self.assertEqual( set(b2), { s["a"] } )

	def testSignals( self ) :

		s = Gaffer.ScriptNode()

		s["a"] = Gaffer.Node()
		s["b"] = Gaffer.Node()

		mirror = set()

		def added( _, member ) :
			mirror.add( member )

		def removed( _, member ) :
			mirror.remove( member )

		b = Gaffer.NumericBookmarkSet( s, 1 )

		b.memberAddedSignal().connect( added, scoped = False )
		b.memberRemovedSignal().connect( removed, scoped = False )

		self.assertEqual( set(b), mirror )

		Gaffer.MetadataAlgo.setNumericBookmark( s, 1, s["a"] )
		self.assertEqual( set(b), mirror )

		Gaffer.MetadataAlgo.setNumericBookmark( s, 1, s["b"] )
		self.assertEqual( set(b), mirror )

	def testSignalOrder( self ) :

		s = Gaffer.ScriptNode()

		s["a"] = Gaffer.Node()
		s["b"] = Gaffer.Node()

		b = Gaffer.NumericBookmarkSet( s, 1 )

		callbackFailures = { "added" : 0, "removed" : 0 }

		# Check we have no members when one is removed as we're
		# defined as only ever containing one node. We can't assert
		# here as the exception gets eaten and the test passes anyway
		def removed( _, member ) :
			if set(b) != set() :
				callbackFailures["removed"] += 1

		cr = b.memberRemovedSignal().connect( removed, scoped = True )

		Gaffer.MetadataAlgo.setNumericBookmark( s, 1, s["a"] )
		Gaffer.MetadataAlgo.setNumericBookmark( s, 1, s["b"] )

		self.assertEqual( callbackFailures["removed"], 0 )

		# Check member is added before signal, same deal re: asserts
		def added( _, member ) :
			if set(b) != { s["a"] } :
				callbackFailures["added"] += 1

		ca = b.memberAddedSignal().connect( added, scoped = True )

		Gaffer.MetadataAlgo.setNumericBookmark( s, 1, s["a"] )
		self.assertEqual( callbackFailures["added"], 0 )

if __name__ == "__main__":
	unittest.main()
