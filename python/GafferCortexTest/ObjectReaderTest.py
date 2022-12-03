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
import IECoreImage # To register ImageReader

import Gaffer
import GafferTest
import GafferCortex

class ObjectReaderTest( GafferTest.TestCase ) :

	def test( self ) :

		filePath = pathlib.Path( os.environ["GAFFER_ROOT"] ) / "python" / "GafferCortexTest" / "images" / "checker.exr"

		node = GafferCortex.ObjectReader()
		node["fileName"].setValue( filePath )
		self.assertEqual( node["fileName"].getValue(), filePath.as_posix() )

		reader = IECore.Reader.create( str( filePath ) )

		# check that the result is the same as loading it ourselves
		self.assertEqual( reader.read(), node["out"].getValue() )

	def testChangingFileType( self ) :

		imageFilePath = pathlib.Path( os.environ["GAFFER_ROOT"] ) / "python" / "GafferCortexTest" / "images" / "checker.exr"
		cobFilePath = pathlib.Path( os.environ["GAFFER_ROOT"] ) / "python" / "GafferCortexTest" / "cobs" / "string.cob"

		node = GafferCortex.ObjectReader()
		node["fileName"].setValue( imageFilePath )
		reader = IECore.Reader.create( str( imageFilePath ) )
		self.assertEqual( reader.read(), node["out"].getValue() )

		node["fileName"].setValue( cobFilePath )
		reader = IECore.Reader.create( str( cobFilePath ) )
		self.assertEqual( reader.read(), node["out"].getValue() )

	def testReadAfterSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferCortex.ObjectReader()
		s["n"]["fileName"].setValue( pathlib.Path( __file__ ).parent / "images" / "checker.exr" )

		r = s["n"]["out"].getValue()

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["n"]["out"].getValue(), r )

	def testReadNoFilename( self ) :

		r = GafferCortex.ObjectReader()
		self.assertEqual( r["out"].getValue(), r["out"].defaultValue() )

if __name__ == "__main__":
	unittest.main()
