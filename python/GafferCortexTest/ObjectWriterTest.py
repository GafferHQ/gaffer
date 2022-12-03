##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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
import pathlib
import unittest

import IECore
import IECoreImage

import Gaffer
import GafferCortex
import GafferTest

class ObjectWriterTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__exrFilePath = self.temporaryDirectory() / "checker.exr"
		self.__tifFilePath = self.temporaryDirectory() / "checker.tif"
		self.__exrSequence = IECore.FileSequence( f'{self.temporaryDirectory() / "checker.####.exr"} 1-4' )

	def test( self ) :

		checkerPath = pathlib.Path( os.environ["GAFFER_ROOT"] ) / "python" / "GafferCortexTest" / "images" / "checker.exr"
		checker = IECore.Reader.create( str( checkerPath ) ).read()

		node = GafferCortex.ObjectWriter()
		node["fileName"].setValue( self.__exrFilePath )
		node["in"].setValue( checker )

		self.assertEqual( node["fileName"].getValue(), self.__exrFilePath.as_posix() )
		self.assertEqual( node["in"].getValue(), checker )

		# check that there are plugs for the writer parameters,
		# but not for the fileName parameter.

		writer = IECore.Writer.create( checker, str( self.__exrFilePath ) )

		for k in writer.parameters().keys() :
			if k != "fileName" and k != "object" :
				self.assertIn( k, node["parameters"] )

		self.assertNotIn( "fileName", node["parameters"] )

		# check that saving it works

		self.assertFalse( self.__exrFilePath.exists() )
		with Gaffer.Context() :
			node["task"].execute()
		self.assertTrue( self.__exrFilePath.exists() )

	def testChangingFileType( self ) :

		checkerPath = pathlib.Path( os.environ["GAFFER_ROOT"] ) / "python" / "GafferCortexTest" / "images" / "checker.exr"
		checker = IECore.Reader.create( str( checkerPath ) ).read()

		node = GafferCortex.ObjectWriter()
		node["fileName"].setValue( self.__exrFilePath )
		node["in"].setValue( checker )

		node["fileName"].setValue( self.__tifFilePath )

		with Gaffer.Context() :
			node["task"].execute()
		self.assertTrue( self.__tifFilePath.exists() )

		image = IECoreImage.ImageReader( str( self.__tifFilePath ) ).read()
		self.assertIn( "tiff:Compression", image.blindData() )

	def testExtraneousPlugsAfterSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferCortex.ObjectWriter()
		s["n"]["fileName"].setValue( self.__exrFilePath )

		self.assertIn( "parameters", s["n"] )
		self.assertNotIn( "parameters1", s["n"] )

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertIn( "parameters", s["n"] )
		self.assertNotIn( "parameters1", s["n"] )

	def testStringSubstitutions( self ) :

		checkerPath = pathlib.Path( os.environ["GAFFER_ROOT"] ) / "python" / "GafferCortexTest" / "images" / "checker.exr"
		checker = IECore.Reader.create( str( checkerPath ) ).read()

		node = GafferCortex.ObjectWriter()
		node["fileName"].setValue( self.__exrSequence.fileName )
		node["in"].setValue( checker )

		contexts = []
		for i in self.__exrSequence.frameList.asList() :
			context = Gaffer.Context()
			context.setFrame( i )
			with context :
				node["task"].execute()

		for f in self.__exrSequence.fileNames() :
			self.assertTrue( pathlib.Path( f ).exists() )

	def testHash( self ) :

		c = Gaffer.Context()
		c.setFrame( 1 )
		c2 = Gaffer.Context()
		c2.setFrame( 2 )

		s = Gaffer.ScriptNode()
		s["n"] = GafferCortex.ObjectWriter()

		# no file produces no effect
		with c :
			self.assertEqual( s["n"]["task"].hash(), IECore.MurmurHash() )

		# no input object produces no effect
		with c :
			s["n"]["fileName"].setValue( self.__exrFilePath )
			self.assertEqual( s["n"]["task"].hash(), IECore.MurmurHash() )

		# now theres a file and object, we get some output
		with c :
			s["o"] = GafferTest.CachingTestNode()
			s["n"]["in"].setInput( s["o"]["out"] )
			self.assertNotEqual( s["n"]["task"].hash(), IECore.MurmurHash() )

		# output doesn't vary by time
		with c :
			h1 = s["n"]["task"].hash()
		with c2 :
			h2 = s["n"]["task"].hash()

		self.assertEqual( h1, h2 )

		# output varies by time since the file name does
		s["n"]["fileName"].setValue( self.__exrSequence.fileName )
		with c :
			h1 = s["n"]["task"].hash()
		with c2 :
			h2 = s["n"]["task"].hash()

		self.assertNotEqual( h1, h2 )

if __name__ == "__main__":
	unittest.main()
