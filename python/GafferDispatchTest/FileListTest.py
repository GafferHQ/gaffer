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

import GafferDispatch
import GafferTest

class FileListTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		# Make a little directory structure to test against.

		for path in [
			"a1",
			"a2",
			"b1",
			"b2",
			"d1/a",
			"d1/b",
			"d2/sd1/a",
			"d2/sd1/b",
			"d2/sd2/a",
			"e",
			"e.tiff",
			"f.TIFF",
			"g.jpg",
		] :
			path = self.temporaryDirectory() / path
			path.parent.mkdir( parents = True, exist_ok = True )
			path.touch()

	def testUnspecifiedDirectory( self ) :

		node = GafferDispatch.FileList()
		self.assertEqual( node["directory"].getValue(), "" )
		self.assertEqual( node["out"].getValue(), IECore.StringVectorData() )

	def testSimpleInclusions( self ) :

		node = GafferDispatch.FileList()
		node["directory"].setValue( self.temporaryDirectory() )
		node["absolute"].setValue( False )

		self.assertEqual(
			node["out"].getValue(),
			IECore.StringVectorData( sorted( [
				p.name for p in self.temporaryDirectory().glob( "*" )
			] ) )
		)

		node["inclusions"].setValue( "a*" )
		self.assertEqual(
			node["out"].getValue(),
			IECore.StringVectorData( sorted( [
				p.name for p in self.temporaryDirectory().glob( "a*" )
			] ) )
		)

		node["inclusions"].setValue( "a* d*" )
		self.assertEqual(
			node["out"].getValue(),
			IECore.StringVectorData( sorted( [
				p.name for p in self.temporaryDirectory().glob( "a*" )
			] + [
				p.name for p in self.temporaryDirectory().glob( "d*" )
			] ) )
		)

	def testRecursiveInclusions( self ) :

		node = GafferDispatch.FileList()
		node["directory"].setValue( self.temporaryDirectory() )
		node["absolute"].setValue( False )

		node["inclusions"].setValue( ".../a*" )
		self.assertEqual(
			node["out"].getValue(),
			IECore.StringVectorData( [ "a1", "a2", "d1/a", "d2/sd1/a", "d2/sd2/a" ] )
		)

	def testExclusions( self ) :

		node = GafferDispatch.FileList()
		node["directory"].setValue( self.temporaryDirectory() )
		node["inclusions"].setValue( "..." )
		node["exclusions"].setValue( "d*" )
		node["absolute"].setValue( False )
		self.assertEqual(
			node["out"].getValue(),
			IECore.StringVectorData( [ "a1", "a2", "b1", "b2", "e", "e.tiff", "f.TIFF", "g.jpg" ] )
		)

	def testSearchSubdirectories( self ) :

		node = GafferDispatch.FileList()
		node["directory"].setValue( self.temporaryDirectory() )
		node["absolute"].setValue( False )

		node["inclusions"].setValue( "a*" )
		node["searchSubdirectories"].setValue( True )
		self.assertEqual(
			node["out"].getValue(),
			IECore.StringVectorData( [ "a1", "a2", "d1/a", "d2/sd1/a", "d2/sd2/a" ] )
		)

	def testDisable( self ) :

		node = GafferDispatch.FileList()
		node["directory"].setValue( self.temporaryDirectory() )
		self.assertTrue( len( node["out"].getValue() ) )

		node["enabled"].setValue( False )
		self.assertEqual( node["out"].getValue(), IECore.StringVectorData() )

	def testExtensions( self ) :

		node = GafferDispatch.FileList()
		node["directory"].setValue( self.temporaryDirectory() )
		node["extensions"].setValue( "tiff" )
		node["absolute"].setValue( False )
		self.assertEqual( node["out"].getValue(), IECore.StringVectorData( [ "e.tiff", "f.TIFF" ] ) )

		node["extensions"].setValue( "tiff jpg" )
		self.assertEqual( node["out"].getValue(), IECore.StringVectorData( [ "e.tiff", "f.TIFF", "g.jpg" ] ) )

	def testFilePatternExtensions( self ) :

		node = GafferDispatch.FileList()
		node["directory"].setValue( self.temporaryDirectory() )
		node["inclusions"].setValue( "*.tiff *.jpg" )
		node["absolute"].setValue( False )
		self.assertEqual( node["out"].getValue(), IECore.StringVectorData( [ "e.tiff", "g.jpg" ] ) )

	def testRefresh( self ) :

		node = GafferDispatch.FileList()
		node["directory"].setValue( self.temporaryDirectory() )
		node["absolute"].setValue( False )
		self.assertIn( "a1", node["out"].getValue() )

		( self.temporaryDirectory() / "a1" ).unlink()
		self.assertIn( "a1", node["out"].getValue() )

		node["refreshCount"].setValue( 1 )
		self.assertNotIn( "a1", node["out"].getValue() )

	def testAbsolute( self ) :

		node = GafferDispatch.FileList()
		node["directory"].setValue( self.temporaryDirectory() )
		self.assertTrue( node["absolute"].getValue() )

		absolutePaths = [ pathlib.Path( p ) for p in node["out"] ]
		for path in absolutePaths :
			self.assertTrue( path.is_absolute() )

		node["absolute"].setValue( False )
		relativePaths = [ pathlib.Path( p ) for p in node["out"] ]
		for path in relativePaths :
			self.assertFalse( path.is_absolute() )

		for absolutePath, relativePath in zip( absolutePaths, relativePaths ) :
			self.assertEqual( absolutePath, relativePath.absolute() )

	def testSequenceMode( self ) :

		directory = self.temporaryDirectory() / "sequenceMode"
		directory.mkdir()

		sequencePath = directory / f"test.####.exr"

		sequenceFilePaths = []
		for i in range( 0, 5 ) :
			sequenceFilePath = directory / f"test.{i:04}.exr"
			sequenceFilePath.touch()
			sequenceFilePaths.append( sequenceFilePath )

		filePath = directory / "test.exr"
		filePath.touch()

		node = GafferDispatch.FileList()
		node["directory"].setValue( directory )

		self.assertEqual( node["sequenceMode"].getValue(), node.SequenceMode.Files )
		self.assertEqual(
			node["out"].getValue(),
			IECore.StringVectorData( [ x.as_posix() for x in sequenceFilePaths + [ filePath ] ] )
		)

		node["sequenceMode"].setValue( node.SequenceMode.Sequences )
		self.assertEqual(
			node["out"].getValue(),
			IECore.StringVectorData( [ sequencePath.as_posix() ] )
		)

		node["sequenceMode"].setValue( node.SequenceMode.FilesAndSequences )
		self.assertEqual(
			node["out"].getValue(),
			IECore.StringVectorData( [ filePath.as_posix(), sequencePath.as_posix() ] )
		)

if __name__ == "__main__":
	unittest.main()
