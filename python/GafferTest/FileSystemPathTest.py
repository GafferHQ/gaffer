##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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
import time
import datetime
import os
if os.name is not "nt" :
	import pwd
	import grp
else :
	from . import _WindowsUtils

import IECore

import Gaffer
import GafferTest

class FileSystemPathTest( GafferTest.TestCase ) :

	def test( self ) :

		p = Gaffer.FileSystemPath( __file__ )

		self.assertTrue( p.isValid() )
		self.assertTrue( p.isLeaf() )

		while len( p ) :

			del p[-1]
			self.assertTrue( p.isValid() )
			self.assertFalse( p.isLeaf() )

	def testIsLeaf( self ) :

		path = Gaffer.FileSystemPath( "/this/path/doesnt/exist" )
		self.assertFalse( path.isLeaf() )

	def testConstructWithFilter( self ) :

		p = Gaffer.FileSystemPath( __file__ )
		self.assertIsNone( p.getFilter() )

		f = Gaffer.FileNamePathFilter( [ "*.exr" ] )
		p = Gaffer.FileSystemPath( __file__, filter = f )
		self.assertTrue( p.getFilter().isSame( f ) )

	@unittest.skipIf( os.name == "nt", "Windows does not support symbolic links." )
	def testBrokenSymbolicLinks( self ) :

		os.symlink( self.temporaryDirectory() + "/nonExistent", self.temporaryDirectory() + "/broken" )

		# we do want symlinks to appear in children, even if they're broken
		d = Gaffer.FileSystemPath( self.temporaryDirectory() )
		c = d.children()
		self.assertEqual( len( c ), 1 )

		l = c[0]
		self.assertEqual( str( l ), self.temporaryDirectory() + "/broken" )

		# we also want broken symlinks to report themselves as "valid",
		# because having a path return a child and then claim the child
		# is invalid seems rather useless. admittedly this is a bit of
		# a compromise.
		self.assertEqual( l.isValid(), True )

		# since we said it was valid, it ought to have some info
		self.assertIsNotNone( l.info() )

	@unittest.skipIf( os.name == "nt", "Windows does not support symbolic links." )
	def testSymLinkInfo( self ) :

		with open( self.temporaryDirectory() + "/a", "w" ) as f :
			f.write( "AAAA" )

		os.symlink( self.temporaryDirectory() + "/a", self.temporaryDirectory() + "/l" )

		# symlinks should report the info for the file
		# they point to.
		a = Gaffer.FileSystemPath( self.temporaryDirectory() + "/a" )
		l = Gaffer.FileSystemPath( self.temporaryDirectory() + "/l" )
		aInfo = a.info()
		self.assertEqual( aInfo["fileSystem:size"], l.info()["fileSystem:size"] )
		# unless they're broken
		os.remove( str( a ) )
		self.assertNotEqual( aInfo["fileSystem:size"], l.info()["fileSystem:size"] )

	def testCopy( self ) :

		p = Gaffer.FileSystemPath( self.temporaryDirectory() )
		p2 = p.copy()

		self.assertEqual( p, p2 )
		self.assertEqual( str( p ), str( p2 ) )
		self.assertEqual( p.nativeString(), p2.nativeString() )

	def testEmptyPath( self ) :

		p = Gaffer.FileSystemPath()
		self.assertEqual( str( p ), "" )
		self.assertEqual( p.nativeString(), "" )
		self.assertTrue( p.isEmpty() )
		self.assertFalse( p.isValid() )

	def testRelativePath( self ) :

		os.chdir( self.temporaryDirectory() )

		with open( os.path.join( self.temporaryDirectory(), "a" ), "w" ) as f :
			f.write( "AAAA" )

		p = Gaffer.FileSystemPath( "a" )

		self.assertEqual( str( p ), "a" )
		self.assertEqual( p.nativeString(), "a" )
		self.assertFalse( p.isEmpty() )
		self.assertTrue( p.isValid() )

		p2 = Gaffer.FileSystemPath( "nonexistent" )

		self.assertEqual( str( p2 ), "nonexistent" )
		self.assertEqual( p2.nativeString(), "nonexistent" )
		self.assertFalse( p2.isEmpty() )
		self.assertFalse( p2.isValid() )

	def testDriveLetterPath( self ) :
		p = Gaffer.FileSystemPath( r"C:\this\path\does\not\exist.ext" )

		if os.name == "nt" :
			self.assertEqual( p.root(), "C:/" )
			self.assertEqual( str( p ), "C:/this/path/does/not/exist.ext" )
			self.assertEqual( list( p ), [ "this", "path", "does", "not", "exist.ext" ] )
			self.assertEqual( p.nativeString(), r"C:\this\path\does\not\exist.ext")
		else :
			self.assertEqual( p.root(), "" )
			self.assertEqual( str( p ), r"C:\this\path\does\not\exist.ext" )
			self.assertEqual( list( p ), [ r"C:\this\path\does\not\exist.ext" ] )
			self.assertEqual( p.nativeString(), str( p ) )
		self.assertFalse( p.isEmpty() )
		self.assertFalse( p.isValid() )

		p = Gaffer.FileSystemPath( "/C:/leading/slash/should/be/removed/on/windows" )
		if os.name == "nt" :
			self.assertEqual( p.root(), "C:/" )
			self.assertEqual( str( p ), "C:/leading/slash/should/be/removed/on/windows" )
			self.assertEqual( list( p ), [ "leading", "slash", "should", "be", "removed", "on", "windows" ] )
		else :
			self.assertEqual( p.root(), "/" )
			self.assertEqual( str( p ), "/C:/leading/slash/should/be/removed/on/windows" )
			self.assertEqual( list( p ), [ "C:", "leading", "slash", "should", "be", "removed", "on", "windows" ] )

	def testUNCPath( self ) :
		p = Gaffer.FileSystemPath( r"//this.server/share/does/not/exist.ext" )

		if os.name == "nt" :
			self.assertEqual( list( p ), [ "share", "does", "not", "exist.ext" ] )
			self.assertEqual( p.root(), "//this.server/" )
			self.assertEqual( str( p ), "//this.server/share/does/not/exist.ext" )
			self.assertEqual( p.nativeString(), r"\\this.server\share\does\not\exist.ext")
		else :
			self.assertEqual( list( p ), [ "this.server", "share", "does", "not", "exist.ext" ] )
			self.assertEqual( p.root(), "/" )
			self.assertEqual( str( p ), "/this.server/share/does/not/exist.ext" )
			self.assertEqual( p.nativeString(), str( p ) )
		self.assertFalse( p.isEmpty() )
		self.assertFalse( p.isValid() )

		p = Gaffer.FileSystemPath( r"\\this.server\share\does\not\exist.ext" )

		if os.name == "nt" :
			self.assertEqual( p.root(), "//this.server/" )
			self.assertEqual( str( p ), "//this.server/share/does/not/exist.ext" )
			self.assertEqual( list( p ), [ "share", "does", "not", "exist.ext" ] )
			self.assertEqual( p.nativeString(), r"\\this.server\share\does\not\exist.ext")
		else :
			self.assertEqual( p.root(), "" )
			self.assertEqual( str( p ), r"\\this.server\share\does\not\exist.ext" )
			self.assertEqual( list( p ), [ r"\\this.server\share\does\not\exist.ext" ] )
			self.assertEqual( p.nativeString(), r"\\this.server\share\does\not\exist.ext" )
		self.assertFalse( p.isEmpty() )
		self.assertFalse( p.isValid() )

	def testPosixPath( self ) :
		p = Gaffer.FileSystemPath( "/this/path/does/not/exist.ext" )

		self.assertEqual( p.root(), "/")
		self.assertEqual( str( p ), "/this/path/does/not/exist.ext" )
		self.assertEqual( list( p ), [ "this", "path", "does", "not", "exist.ext" ] )

		if os.name == "nt" :
			self.assertEqual( p.nativeString(), r"\this\path\does\not\exist.ext" )
		else :
			self.assertEqual( p.nativeString(), "/this/path/does/not/exist.ext")

		self.assertFalse( p.isEmpty() )
		self.assertFalse( p.isValid() )

	def testMixedSlashes( self ) :
		p = Gaffer.FileSystemPath( r"oh\my/what/a\mess" )
		self.assertEqual( p.root(), "" )
		if os.name == "nt" :
			self.assertEqual( str( p ), "oh/my/what/a/mess" )
			self.assertEqual( list( p ), [ "oh", "my", "what", "a", "mess" ] )
			self.assertEqual( p.nativeString(), r"oh\my\what\a\mess" )
		else :
			self.assertEqual( str( p ), r"oh\my/what/a\mess" )
			self.assertEqual( list( p ), [ r"oh\my", r"what", r"a\mess" ] )
			self.assertEqual( p.nativeString(), r"oh\my/what/a\mess" )

		p = Gaffer.FileSystemPath( r"C:\not/a\drive/letter\too" )
		if os.name == "nt" :
			self.assertEqual( p.root(), "C:/" )
			self.assertEqual( str( p ), "C:/not/a/drive/letter/too" )
			self.assertEqual( list( p ), [ "not", "a", "drive", "letter", "too" ] )
			self.assertEqual( p.nativeString(), r"C:\not\a\drive\letter\too" )
		else :
			self.assertEqual( p.root(), "" )
			self.assertEqual( str( p ), r"C:\not/a\drive/letter\too" )
			self.assertEqual( list( p ), [ r"C:\not", r"a\drive", r"letter\too" ] )
			self.assertEqual( p.nativeString(), r"C:\not/a\drive/letter\too" )

		# The inclusion of `\t` in the path is used to avoid the warning
		# "invalid escape sequence" written to the terminal, which can
		# cause some tests to fail.
		p = Gaffer.FileSystemPath( r"//unc\tshare/must\twork" )
		if os.name == "nt" :
			self.assertEqual( p.root(), "//unc/" )
			self.assertEqual( str( p ), "//unc/tshare/must/twork" )
			self.assertEqual( list( p ), [ "tshare", "must", "twork" ] )
			self.assertEqual( p.nativeString(), r"\\unc\tshare\must\twork" )
		else :
			self.assertEqual( p.root(), "/" )
			self.assertEqual( str( p ), r"/unc\tshare/must\twork" )
			self.assertEqual( list( p ), [ r"unc\tshare", r"must\twork" ] )
			self.assertEqual( p.nativeString(), r"/unc\tshare/must\twork")

	def testSetFromStrings( self ) :

		p = Gaffer.FileSystemPath( r"C:\this\path\does\not\exist" )

		p.setFromString( "make/it/relative" )

		self.assertEqual( p.root(), "" )
		self.assertEqual( str( p ), "make/it/relative" )
		if os.name == "nt" :
			self.assertEqual( p.nativeString(), r"make\it\relative" )
		else :
			self.assertEqual( p.nativeString(), str( p ) )

		p.setFromString( r"C:\try\drive\again" )
		if os.name == "nt" :
			self.assertEqual( p.root(), "C:/" )
			self.assertEqual( str( p ), "C:/try/drive/again" )
			self.assertEqual( p.nativeString(), r"C:\try\drive\again" )
		else :
			self.assertEqual( p.root(), "" )
			self.assertEqual( str( p ), r"C:\try\drive\again" )
			self.assertEqual( p.nativeString(), str( p ) )


	def testRelativePathChildren( self ) :

		os.chdir( self.temporaryDirectory() )
		os.mkdir( "dir" )
		with open( os.path.join( self.temporaryDirectory(), "dir", "a" ), "w" ) as f :
			f.write( "AAAA" )

		p = Gaffer.FileSystemPath( "dir" )

		c = p.children()
		self.assertEqual( len( c ), 1 )
		self.assertEqual( str( c[0] ), "dir/a" )
		if os.name == "nt" :
			self.assertEqual( c[0].nativeString(), "dir\\a" )
		else:
			self.assertEqual( c[0].nativeString(), "dir/a" )

		self.assertTrue( c[0].isValid() )

	def testChildrenOfFile( self ) :

		p = Gaffer.FileSystemPath( __file__ )
		self.assertEqual( p.children(), [] )

	def testModificationTimes( self ) :

		p = Gaffer.FileSystemPath( self.temporaryDirectory() )
		p.append( "t" )

		with open( p.nativeString(), "w" ) as f :
			f.write( "AAAA" )

		mt = p.property( "fileSystem:modificationTime" )
		self.assertTrue( isinstance( mt, datetime.datetime ) )
		self.assertLess( (datetime.datetime.utcnow() - mt).total_seconds(), 2 )

		time.sleep( 1 )

		with open( p.nativeString(), "w" ) as f :
			f.write( "BBBB" )

		mt = p.property( "fileSystem:modificationTime" )
		self.assertTrue( isinstance( mt, datetime.datetime ) )
		self.assertLess( (datetime.datetime.utcnow() - mt).total_seconds(), 2 )

	def testOwner( self ) :

		p = Gaffer.FileSystemPath( self.temporaryDirectory() )
		p.append( "t" )

		with open( p.nativeString(), "w" ) as f :
			f.write( "AAAA" )

		o = p.property( "fileSystem:owner" )
		self.assertTrue( isinstance( o, str ) )

		self.assertEqual( o, self.getFileOwner( p.nativeString() ) )

	def testGroup( self ) :

		p = Gaffer.FileSystemPath( self.temporaryDirectory() )
		p.append( "t" )

		with open( p.nativeString(), "w" ) as f :
			f.write( "AAAA" )

		g = p.property( "fileSystem:group" )
		self.assertTrue( isinstance( g, str ) )
		self.assertEqual( g, self.getFileGroup( p.nativeString() ) )

	def testPropertyNames( self ) :

		p = Gaffer.FileSystemPath( self.temporaryDirectory() )

		a = p.propertyNames()
		self.assertTrue( isinstance( a, list ) )

		self.assertTrue( "fileSystem:group" in a )
		self.assertTrue( "fileSystem:owner" in a )
		self.assertTrue( "fileSystem:modificationTime" in a )
		self.assertTrue( "fileSystem:size" in a )

		self.assertTrue( "fileSystem:frameRange" not in a )
		p = Gaffer.FileSystemPath( self.temporaryDirectory(), includeSequences = True )
		self.assertTrue( "fileSystem:frameRange" in p.propertyNames() )

	def testSequences( self ) :

		os.mkdir( os.path.join( self.temporaryDirectory(), "dir" ) )
		for n in [ "singleFile.txt", "a.001.txt", "a.002.txt", "a.004.txt", "b.003.txt" ] :
			with open( os.path.join( self.temporaryDirectory(), n ), "w" ) as f :
				f.write( "AAAA" )

		p = Gaffer.FileSystemPath( self.temporaryDirectory(), includeSequences = True )
		self.assertTrue( p.getIncludeSequences() )

		c = p.children()
		self.assertEqual( len( c ), 8 )

		s = sorted( c, key=str )
		self.assertEqual( str(s[0]), self.temporaryDirectory().replace( "\\", "/" ) + "/a.###.txt" )
		self.assertEqual( s[0].nativeString(), os.path.join( self.temporaryDirectory(), "a.###.txt" ) )
		self.assertEqual( str(s[1]), self.temporaryDirectory().replace( "\\", "/" ) + "/a.001.txt" )
		self.assertEqual( s[1].nativeString(), os.path.join( self.temporaryDirectory(), "a.001.txt" ) )
		self.assertEqual( str(s[2]), self.temporaryDirectory().replace( "\\", "/" ) + "/a.002.txt" )
		self.assertEqual( s[2].nativeString(), os.path.join( self.temporaryDirectory(), "a.002.txt" ) )
		self.assertEqual( str(s[3]), self.temporaryDirectory().replace( "\\", "/" ) + "/a.004.txt" )
		self.assertEqual( s[3].nativeString(), os.path.join( self.temporaryDirectory(), "a.004.txt" ) )
		self.assertEqual( str(s[4]), self.temporaryDirectory().replace( "\\", "/" ) + "/b.###.txt" )
		self.assertEqual( s[4].nativeString(), os.path.join( self.temporaryDirectory(), "b.###.txt" ) )
		self.assertEqual( str(s[5]), self.temporaryDirectory().replace( "\\", "/" ) + "/b.003.txt" )
		self.assertEqual( s[5].nativeString(), os.path.join( self.temporaryDirectory(), "b.003.txt" ) )
		self.assertEqual( str(s[6]), self.temporaryDirectory().replace( "\\", "/" ) + "/dir" )
		self.assertEqual( s[6].nativeString(), os.path.join( self.temporaryDirectory(), "dir" ) )
		self.assertEqual( str(s[7]), self.temporaryDirectory().replace( "\\", "/" ) + "/singleFile.txt" )
		self.assertEqual( s[7].nativeString(), os.path.join( self.temporaryDirectory(), "singleFile.txt" ) )

		for x in s :

			self.assertTrue( x.isValid() )
			if not os.path.isdir( x.nativeString() ) :
				self.assertTrue( x.isLeaf() )

			self.assertEqual( x.property( "fileSystem:owner" ), self.getFileOwner( p.nativeString() ) )
			self.assertEqual( x.property( "fileSystem:group" ), self.getFileGroup( p.nativeString() ) )
			self.assertLess( (datetime.datetime.utcnow() - x.property( "fileSystem:modificationTime" )).total_seconds(), 2 )
			if "###" not in str( x ) :
				self.assertFalse( x.isFileSequence() )
				self.assertEqual( x.fileSequence(), None )
				self.assertEqual( x.property( "fileSystem:frameRange" ), "" )
				if os.path.isdir( x.nativeString() ) :
					self.assertEqual( x.property( "fileSystem:size" ), 0 )
				else :
					self.assertEqual( x.property( "fileSystem:size" ), 4 )

		self.assertEqual( s[0].property( "fileSystem:frameRange" ), "1-2,4" )
		self.assertTrue( s[0].isFileSequence() )
		self.assertTrue( isinstance( s[0].fileSequence(), IECore.FileSequence ) )
		self.assertEqual( s[0].fileSequence(), IECore.FileSequence( s[0].nativeString(), IECore.frameListFromList( [ 1, 2, 4 ] ) ) )
		self.assertEqual( s[0].property( "fileSystem:size" ), 4 * 3 )

		self.assertEqual( s[4].property( "fileSystem:frameRange" ), "3" )
		self.assertTrue( s[4].isFileSequence() )
		self.assertTrue( isinstance( s[4].fileSequence(), IECore.FileSequence ) )
		self.assertEqual( s[4].fileSequence(), IECore.FileSequence( s[4].nativeString(), IECore.frameListFromList( [ 3 ] ) ) )
		self.assertEqual( s[4].property( "fileSystem:size" ), 4 )

		# make sure we can copy
		p2 = p.copy()
		self.assertTrue( p2.getIncludeSequences() )
		self.assertEqual( len( p2.children() ), 8 )

		# make sure we can still exclude the sequences
		p = Gaffer.FileSystemPath( self.temporaryDirectory(), includeSequences = False )
		self.assertFalse( p.getIncludeSequences() )

		c = p.children()
		self.assertEqual( len( c ), 6 )

		s = sorted( c, key=str )
		self.assertEqual( str(s[0]), self.temporaryDirectory().replace( "\\", "/" ) + "/a.001.txt" )
		self.assertEqual( s[0].nativeString(), os.path.join( self.temporaryDirectory(), "a.001.txt" ) )
		self.assertEqual( str(s[1]), self.temporaryDirectory().replace( "\\", "/" ) + "/a.002.txt" )
		self.assertEqual( s[1].nativeString(), os.path.join( self.temporaryDirectory(), "a.002.txt" ) )
		self.assertEqual( str(s[2]), self.temporaryDirectory().replace( "\\", "/" ) + "/a.004.txt" )
		self.assertEqual( s[2].nativeString(), os.path.join( self.temporaryDirectory(), "a.004.txt" ) )
		self.assertEqual( str(s[3]), self.temporaryDirectory().replace( "\\", "/" ) + "/b.003.txt" )
		self.assertEqual( s[3].nativeString(), os.path.join( self.temporaryDirectory(), "b.003.txt" ) )
		self.assertEqual( str(s[4]), self.temporaryDirectory().replace( "\\", "/" ) + "/dir" )
		self.assertEqual( s[4].nativeString(), os.path.join( self.temporaryDirectory(), "dir" ) )
		self.assertEqual( str(s[5]), self.temporaryDirectory().replace( "\\", "/" ) + "/singleFile.txt" )
		self.assertEqual( s[5].nativeString(), os.path.join( self.temporaryDirectory(), "singleFile.txt" ) )

		# and we can include them again
		p.setIncludeSequences( True )
		self.assertTrue( p.getIncludeSequences() )

		c = p.children()
		self.assertEqual( len( c ), 8 )

	def testCancellation( self ) :

		p = Gaffer.FileSystemPath( os.path.dirname( __file__ ) )

		# Children

		c = IECore.Canceller()
		c.cancel()

		with self.assertRaises( IECore.Cancelled ) :
			p.children( c )

		# Sequence properties

		for f in range( 0, 100 ) :
			with open( os.path.join( self.temporaryDirectory(), "{}.txt".format( f ) ), "w" ) as f :
				f.write( "x" )

		p = Gaffer.FileSystemPath( os.path.join( self.temporaryDirectory(), "#.txt" ), includeSequences = True )

		with self.assertRaises( IECore.Cancelled ) :
			p.property( "fileSystem:owner", c )

		with self.assertRaises( IECore.Cancelled ) :
			p.property( "fileSystem:group", c )

		with self.assertRaises( IECore.Cancelled ) :
			p.property( "fileSystem:size", c )

		with self.assertRaises( IECore.Cancelled ) :
			p.property( "fileSystem:modificationTime", c )

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__originalCWD = os.getcwd()

	def tearDown( self ) :

		os.chdir( self.__originalCWD )

		GafferTest.TestCase.tearDown( self )

	def getFileOwner( self, filePath ):

		if os.name is not "nt" :
			return pwd.getpwuid( os.stat( filePath ).st_uid ).pw_name
		else :
			securityDescriptor = GafferTest._WindowsUtils.getFileSecurity( filePath )
			owner, domain = securityDescriptor.owner()
			return owner

	def getFileGroup( self, filePath ) :

		if os.name is not "nt" :
			return grp.getgrgid( os.stat( filePath ).st_gid ).gr_name
		else :
			securityDescriptor = GafferTest._WindowsUtils.getFileSecurity( filePath )
			group, domain = securityDescriptor.group()
			return group

if __name__ == "__main__":
	unittest.main()
