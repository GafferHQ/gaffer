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

import os
import pathlib
import subprocess
import shutil
import sys
import unittest

import IECore

import GafferDispatch
import GafferTest

class CopyFilesTest( GafferTest.TestCase ) :

	@classmethod
	def setUpClass( cls ) :

		GafferTest.TestCase.setUpClass()

		if sys.platform == "darwin" :
			cls.__ramDisk = pathlib.Path( "/Volumes/GafferTest" )
			assert( not cls.__ramDisk.exists() )
			image = subprocess.check_output( [ "hdiutil", "attach", "-nomount", "ram://1024" ] ).strip()
			subprocess.check_call( [ "diskutil", "erasevolume", "HFS+", "GafferTest", image ] )
		elif sys.platform == "linux" :
			cls.__ramDisk = pathlib.Path( "/dev/shm/GafferTest" )
			assert( not cls.__ramDisk.exists() )
			cls.__ramDisk.mkdir()
		else :
			cls.__ramDisk = None

	@classmethod
	def tearDownClass( cls ) :

		GafferTest.TestCase.tearDownClass()

		if sys.platform == "darwin" :
			subprocess.check_call( [ "hdiutil", "detach", cls.__ramDisk ] )
		elif sys.platform == "linux" :
			shutil.rmtree( cls.__ramDisk )

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		if self.__ramDisk is not None :
			self.__temporaryRAMDirectory = pathlib.Path( self.__ramDisk ) / "copyFilesTest"
			self.__temporaryRAMDirectory.mkdir()
		else :
			self.__temporaryRAMDirectory = None

	def tearDown( self ) :

		GafferTest.TestCase.tearDown( self )

		if self.__temporaryRAMDirectory is not None :
			shutil.rmtree( self.__temporaryRAMDirectory )

	def __sourceDirectories( self ) :

		# We run every test with two different source directories, with one
		# of them being on a RAM-based filesystem. This gives us test coverage
		# for the inability of `filesystem::rename()` to move files between file
		# systems.
		return [ self.temporaryDirectory() ] + [ self.__temporaryRAMDirectory ] if self.__temporaryRAMDirectory is not None else []

	def testMissingDestinationDirectory( self ) :

		for sourceDirectory in self.__sourceDirectories() :

			with self.subTest( sourceDirectory = sourceDirectory ) :

				source = sourceDirectory / "source.txt"
				source.write_text( "Test" )

				destination = self.temporaryDirectory() / "destination"

				node = GafferDispatch.CopyFiles()
				node["files"].setValue( IECore.StringVectorData( [ str( source ) ] ) )
				node["destination"].setValue( destination )
				node["task"].execute()

				self.assertTrue( destination.is_dir() )
				self.assertEqual( ( destination / "source.txt" ).read_text(), "Test" )

				shutil.rmtree( destination )

	def testDeleteSource( self ) :

		for sourceDirectory in self.__sourceDirectories() :

			with self.subTest( sourceDirectory = sourceDirectory ) :

				source = sourceDirectory / "source.txt"
				source.write_text( "Test" )

				destination = self.temporaryDirectory() / "destination"
				node = GafferDispatch.CopyFiles()

				node["files"].setValue( IECore.StringVectorData( [ str( source ) ] ) )
				node["destination"].setValue( destination )
				node["deleteSource"].setValue( True )
				node["task"].execute()

				self.assertTrue( destination.is_dir() )
				self.assertEqual( ( destination / "source.txt" ).read_text(), "Test" )
				self.assertFalse( source.exists() )

				shutil.rmtree( destination )

	def testOverwrite( self ) :

		for sourceDirectory in self.__sourceDirectories() :

			with self.subTest( sourceDirectory = sourceDirectory ) :

				source = sourceDirectory / "file.txt"
				source.write_text( "Test" )

				destinationDir = self.temporaryDirectory() / "destination"
				destinationDir.mkdir()

				destinationFile = destinationDir / source.name
				destinationFile.touch()

				node = GafferDispatch.CopyFiles()
				node["files"].setValue( IECore.StringVectorData( [ str( source ) ] ) )
				node["destination"].setValue( destinationDir )

				self.assertFalse( node["overwrite"].getValue() )

				with self.assertRaisesRegex( RuntimeError, "File exists" ) :
					node["task"].execute()
				self.assertEqual( destinationFile.read_text(), "" )

				node["overwrite"].setValue( True )
				node["task"].execute()

				self.assertEqual( destinationFile.read_text(), "Test" )

				shutil.rmtree( destinationDir )

	def testSourceNotDeletedIfCopyFails( self ) :

		for sourceDirectory in self.__sourceDirectories() :

			with self.subTest( sourceDirectory = sourceDirectory ) :

				source = sourceDirectory / "file.txt"
				source.write_text( "Test" )

				destinationDir = self.temporaryDirectory() / "destination"
				destinationDir.mkdir( mode = os.O_RDONLY, exist_ok = True )

				node = GafferDispatch.CopyFiles()
				node["files"].setValue( IECore.StringVectorData( [ str( source ) ] ) )
				node["destination"].setValue( destinationDir )
				node["overwrite"].setValue( True )
				node["deleteSource"].setValue( True )

				with self.assertRaisesRegex( RuntimeError, "Permission denied" ) :
					node["task"].execute()

				self.assertTrue( source.exists() )
				self.assertEqual( source.read_text(), "Test" )

	def testCopyDirectory( self ) :

		for sourceDirectory in self.__sourceDirectories() :

			with self.subTest( sourceDirectory = sourceDirectory ) :

				sourceDirectory = sourceDirectory / "myFiles"
				sourceDirectory.mkdir()
				( sourceDirectory / "a.txt" ).write_text( "Test A" )
				( sourceDirectory / "b.txt" ).write_text( "Test B" )
				( sourceDirectory / "subDir" ).mkdir()
				( sourceDirectory / "subDir" / "c.txt" ).write_text( "Test C" )

				destinationDir = self.temporaryDirectory() / "destination"

				node = GafferDispatch.CopyFiles()
				node["files"].setValue( IECore.StringVectorData( [ str( sourceDirectory ) ] ) )
				node["destination"].setValue( destinationDir )
				node["deleteSource"].setValue( True )
				node["task"].execute()

				self.assertEqual( ( destinationDir / "myFiles" / "a.txt" ).read_text(), "Test A" )
				self.assertEqual( ( destinationDir / "myFiles" / "b.txt" ).read_text(), "Test B" )
				self.assertEqual( ( destinationDir / "myFiles" / "subDir" / "c.txt" ).read_text(), "Test C" )

				self.assertFalse( sourceDirectory.exists() )

				shutil.rmtree( destinationDir )

if __name__ == "__main__":
	unittest.main()
