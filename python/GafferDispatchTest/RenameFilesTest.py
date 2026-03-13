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

import unittest

import IECore

import Gaffer
import GafferDispatch
import GafferTest

class RenameFilesTest( GafferTest.TestCase ) :

	def testSourceVariable( self ) :

		path1 = self.temporaryDirectory() / "test1"
		path2 = self.temporaryDirectory() / "test2"
		path1.touch()
		path2.touch()

		spreadsheet = Gaffer.Spreadsheet()
		spreadsheet["selector"].setValue( "${source}" )
		spreadsheet["rows"].addColumn( Gaffer.StringPlug( "name" ) )
		spreadsheet["rows"].addRows( 2 )
		spreadsheet["rows"][0]["name"].setValue( str( path1 ) )
		spreadsheet["rows"][0]["cells"]["name"]["value"].setValue( "apple" )
		spreadsheet["rows"][1]["name"].setValue( str( path2 ) )
		spreadsheet["rows"][1]["cells"]["name"]["value"].setValue( "pear" )

		rename = GafferDispatch.RenameFiles()
		rename["files"].setValue( IECore.StringVectorData( [ str( path1 ), str( path2 ) ] ) )
		rename["name"].setInput( spreadsheet["out"]["name"] )
		rename["task"].execute()

		self.assertEqual(
			{ p.name for p in self.temporaryDirectory().glob( "*" ) },
			{ "apple", "pear" }
		)

	def testStemAndExtensionVariables( self ) :

		path = self.temporaryDirectory() / "test.tar"
		path.touch()

		rename = GafferDispatch.RenameFiles()
		rename["files"].setValue( IECore.StringVectorData( [ str( path ) ] ) )
		rename["name"].setValue( "${source:stem}Suffix${source:extension}.gz" )
		rename["task"].execute()

		self.assertEqual(
			[ p.name for p in self.temporaryDirectory().glob( "*" ) ],
			[ "testSuffix.tar.gz" ]
		)

	def testChangeAffixes( self ) :

		path = self.temporaryDirectory() / "prefixMiddleSuffix.ext"
		path.touch()

		rename = GafferDispatch.RenameFiles()
		rename["files"].setValue( IECore.StringVectorData( [ str( path ) ] ) )
		rename["deletePrefix"].setValue( "prefix" )
		rename["deleteSuffix"].setValue( "Suffix" )
		rename["addPrefix"].setValue( "newBeginning" )
		rename["addSuffix"].setValue( "NewEnding" )
		rename["task"].execute()

		self.assertEqual(
			[ p.name for p in self.temporaryDirectory().glob( "*" ) ],
			[ "newBeginningMiddleNewEnding.ext" ]
		)

	def testFindReplace( self ) :

		path = self.temporaryDirectory() / "aBaBaBA.abc"
		path.touch()

		rename = GafferDispatch.RenameFiles()
		rename["files"].setValue( IECore.StringVectorData( [ str( path ) ] ) )
		rename["find"].setValue( "a" )
		rename["replace"].setValue( "C" )
		rename["task"].execute()

		self.assertEqual(
			[ p.name for p in self.temporaryDirectory().glob( "*" ) ],
			[ "CBCBCBA.abc" ]
		)

	def testRegularExpressions( self ) :

		path = self.temporaryDirectory() / "abc123.ext"
		path.touch()

		rename = GafferDispatch.RenameFiles()
		rename["files"].setValue( IECore.StringVectorData( [ str( path ) ] ) )
		rename["find"].setValue( "a*c" )
		rename["replace"].setValue( "{0}d" )
		rename["useRegularExpressions"].setValue( True )
		rename["task"].execute()

		self.assertEqual(
			[ p.name for p in self.temporaryDirectory().glob( "*" ) ],
			[ "abcd123.ext" ]
		)

	def testNameOverridesEverything( self ) :

		path = self.temporaryDirectory() / "prefixMiddleSuffix.ext"
		path.touch()

		rename = GafferDispatch.RenameFiles()
		rename["files"].setValue( IECore.StringVectorData( [ str( path ) ] ) )
		rename["name"].setValue( "newName.abc" )
		rename["deletePrefix"].setValue( "prefix" )
		rename["deleteSuffix"].setValue( "Suffix" )
		rename["find"].setValue( "Middle" )
		rename["replace"].setValue( "NewMiddle" )
		rename["addPrefix"].setValue( "newPrefix" )
		rename["addSuffix"].setValue( "NewSuffix" )
		rename["task"].execute()

		self.assertEqual(
			[ p.name for p in self.temporaryDirectory().glob( "*" ) ],
			[ "newName.abc" ]
		)

	def testConflictingNames( self ) :

		source1 = self.temporaryDirectory() / "path1"
		source1.write_text( "1" )

		source2 = self.temporaryDirectory() / "path2"
		source2.write_text( "2" )

		destination = self.temporaryDirectory() / "path"

		rename = GafferDispatch.RenameFiles()
		rename["files"].setValue( IECore.StringVectorData( [ str( source1 ), str( source2 ) ] ) )
		rename["name"].setValue( "path" )

		with self.assertRaisesRegex( RuntimeError, f'.*Destination ".*/{destination.name}" has multiple source files : ".*/{source1.name}" and ".*/{source2.name}"' ) :
			rename["task"].execute()

		self.assertFalse( destination.exists() )
		self.assertEqual( source1.read_text(), "1" )
		self.assertEqual( source2.read_text(), "2" )

	def testMissingSourceFile( self ) :

		source = self.temporaryDirectory() / "missing"

		rename = GafferDispatch.RenameFiles()
		rename["files"].setValue( IECore.StringVectorData( [ str( source ) ] ) )
		rename["name"].setValue( "renamed" )

		with self.assertRaisesRegex( RuntimeError, f'.*(No such file|cannot find the file).*missing' ) :
			rename["task"].execute()

	def testOneSourceOverwritingAnother( self ) :

		fileA = self.temporaryDirectory() / "fileA"
		fileA.write_text( "A" )

		fileB = self.temporaryDirectory() / "fileB"
		fileB.write_text( "B" )

		rename = GafferDispatch.RenameFiles()
		rename["files"].setValue( IECore.StringVectorData( [ str( fileA ), str( fileB ) ] ) )
		rename["deleteSuffix"].setValue( "A" )
		rename["addSuffix"].setValue( "B" )

		with self.assertRaisesRegex( RuntimeError, f'.*Renaming of ".*/{fileA.name}" would overwrite source ".*/{fileB.name}"' ) :
			rename["task"].execute()

		self.assertEqual( fileA.read_text(), "A" )
		self.assertEqual( fileB.read_text(), "B" )

	def testOverwriteExistingFile( self ) :

		fileA = self.temporaryDirectory() / "fileA"
		fileA.write_text( "A" )

		fileB = self.temporaryDirectory() / "fileB"
		fileB.write_text( "B" )

		rename = GafferDispatch.RenameFiles()
		rename["files"].setValue( IECore.StringVectorData( [ str( fileA ) ] ) )
		rename["name"].setValue( "fileB" )

		with self.assertRaisesRegex( RuntimeError, f'.*Can not overwrite destination ".*/{fileB.name}" unless `overwrite` plug is set.' ) :
			rename["task"].execute()

		self.assertEqual( fileA.read_text(), "A" )
		self.assertEqual( fileB.read_text(), "B" )

		rename["overwrite"].setValue( True )
		rename["task"].execute()

		self.assertFalse( fileA.exists() )
		self.assertEqual( fileB.read_text(), "A" )

	def testReplaceExtension( self ) :

		file = self.temporaryDirectory() / "test.tiff"
		file.touch()

		rename = GafferDispatch.RenameFiles()
		rename["files"].setValue( IECore.StringVectorData( [ str( file ) ] ) )
		rename["replaceExtension"].setValue( True )
		rename["extension"].setValue( "jpeg" )
		rename["task"].execute()

		self.assertFalse( file.exists() )
		self.assertTrue( file.with_suffix( ".jpeg" ).exists() )

	def testRemoveExtension( self ) :

		file = self.temporaryDirectory() / "test.txt"
		file.touch()

		rename = GafferDispatch.RenameFiles()
		rename["files"].setValue( IECore.StringVectorData( [ str( file ) ] ) )
		rename["replaceExtension"].setValue( True )
		rename["task"].execute()

		self.assertFalse( file.exists() )
		self.assertTrue( file.with_suffix( "" ).exists() )

if __name__ == "__main__":
	unittest.main()
