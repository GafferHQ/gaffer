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

import os
import unittest

import IECore

import Gaffer
import GafferTest
import GafferCortex

class OpMatcherTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__sequence = IECore.FileSequence( self.temporaryDirectory() + "/a.#.exr 1-10" )
		for f in self.__sequence.fileNames() :
			os.system( "touch %s" % f )

	@unittest.expectedFailure
	def testFile( self ) :

		# we need a suitable op as part of the gaffer install before we
		# can have this test pass.

		matcher = GafferCortex.OpMatcher.defaultInstance()

		exrFile = os.path.dirname( __file__ ) + "/images/checker.exr"
		path = Gaffer.FileSystemPath( exrFile )

		ops = matcher.matches( path )
		self.assertTrue( len( ops ) )

	def testSequences( self ) :

		matcher = GafferCortex.OpMatcher.defaultInstance()

		path = Gaffer.SequencePath( str( self.__sequence ) )
		ops = matcher.matches( path )

		sequenceRenumber = None
		for op, parameter in ops :
			if isinstance( op, IECore.SequenceRenumberOp ) :
				sequenceRenumber = op

		self.assertIsNotNone( sequenceRenumber )
		self.assertEqual( sequenceRenumber["src"].getTypedValue(), str( self.__sequence ) )

	def testDefaultInstance( self ) :

		self.assertIsInstance(GafferCortex.OpMatcher.defaultInstance(), GafferCortex.OpMatcher )
		self.assertTrue( GafferCortex.OpMatcher.defaultInstance() is GafferCortex.OpMatcher.defaultInstance() )
		self.assertTrue( GafferCortex.OpMatcher.defaultInstance( IECore.ClassLoader.defaultOpLoader() ) is GafferCortex.OpMatcher.defaultInstance() )

		alternativeClassLoader = IECore.ClassLoader( IECore.SearchPath( [ "wherever", "i", "want" ] ) )

		self.assertTrue( GafferCortex.OpMatcher.defaultInstance( alternativeClassLoader ) is GafferCortex.OpMatcher.defaultInstance( alternativeClassLoader ) )
		self.assertTrue( GafferCortex.OpMatcher.defaultInstance( alternativeClassLoader ) is not GafferCortex.OpMatcher.defaultInstance() )

if __name__ == "__main__":
	unittest.main()
