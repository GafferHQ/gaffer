##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

import pathlib
import unittest

import IECore

import Gaffer
import GafferDispatch
import GafferTest

class DeleteFilesTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		# Make a little directory structure to test against.

		for path in [
			"a",
			"b",
			"d/a",
			"d/b",
		] :
			path = self.temporaryDirectory() / path
			path.parent.mkdir( parents = True, exist_ok = True )
			path.touch()

	def testDeleteFiles( self ) :

		node = GafferDispatch.DeleteFiles()
		node["files"].setValue(
			IECore.StringVectorData( [
				str( self.temporaryDirectory() / "a" ),
				str( self.temporaryDirectory() / "d" / "a" ),
			] )
		)

		for file in node["files"].getValue() :
			self.assertTrue( pathlib.Path( file ).is_file() )

		node["task"].execute()
		for file in node["files"].getValue() :
			self.assertFalse( pathlib.Path( file ).exists() )

		self.assertTrue( ( self.temporaryDirectory() / "b" ).is_file() )
		self.assertTrue( ( self.temporaryDirectory() / "d" / "b" ).is_file() )

	def testDeleteDirectories( self ) :

		dir = self.temporaryDirectory() / "d"

		node = GafferDispatch.DeleteFiles()
		node["files"].setValue( IECore.StringVectorData( [ str( dir ) ] ) )

		self.assertTrue( dir.is_dir() )

		with self.assertRaisesRegex( Gaffer.ProcessException, "(Directory not empty|The directory is not empty)" ) :
			node["task"].execute()

		self.assertTrue( dir.is_dir() )

		node["deleteDirectories"].setValue( True )
		node["task"].execute()

		self.assertFalse( dir.exists() )

	def testHash( self ) :

		node = GafferDispatch.DeleteFiles()
		self.assertEqual( node["task"].hash(), IECore.MurmurHash() )

		node["files"].setValue( IECore.StringVectorData( [ "a" ] ) )
		self.assertNotEqual( node["task"].hash(), IECore.MurmurHash() )

if __name__ == "__main__":
	unittest.main()
