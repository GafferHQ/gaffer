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
import pwd
import grp
import os

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

	def testEmptyPath( self ) :

		p = Gaffer.FileSystemPath()
		self.assertEqual( str( p ), "" )
		self.assertTrue( p.isEmpty() )
		self.assertFalse( p.isValid() )

	def testRelativePath( self ) :

		os.chdir( self.temporaryDirectory() )

		with open( self.temporaryDirectory() + "/a", "w" ) as f :
			f.write( "AAAA" )

		p = Gaffer.FileSystemPath( "a" )

		self.assertEqual( str( p ), "a" )
		self.assertFalse( p.isEmpty() )
		self.assertTrue( p.isValid() )

		p2 = Gaffer.FileSystemPath( "nonexistent" )

		self.assertEqual( str( p2 ), "nonexistent" )
		self.assertFalse( p2.isEmpty() )
		self.assertFalse( p2.isValid() )

	def testRelativePathChildren( self ) :

		os.chdir( self.temporaryDirectory() )
		os.mkdir( "dir" )
		with open( self.temporaryDirectory() + "/dir/a", "w" ) as f :
			f.write( "AAAA" )

		p = Gaffer.FileSystemPath( "dir" )

		c = p.children()
		self.assertEqual( len( c ), 1 )
		self.assertEqual( str( c[0] ), "dir/a" )
		self.assertTrue( c[0].isValid() )

	def testChildrenOfFile( self ) :

		p = Gaffer.FileSystemPath( __file__ )
		self.assertEqual( p.children(), [] )

	def testModificationTimes( self ) :

		p = Gaffer.FileSystemPath( self.temporaryDirectory() )
		p.append( "t" )

		with open( str( p ), "w" ) as f :
			f.write( "AAAA" )

		mt = p.property( "fileSystem:modificationTime" )
		self.assertTrue( isinstance( mt, datetime.datetime ) )
		self.assertLess( (datetime.datetime.utcnow() - mt).total_seconds(), 2 )

		time.sleep( 1 )

		with open( str( p ), "w" ) as f :
			f.write( "BBBB" )

		mt = p.property( "fileSystem:modificationTime" )
		self.assertTrue( isinstance( mt, datetime.datetime ) )
		self.assertLess( (datetime.datetime.utcnow() - mt).total_seconds(), 2 )

	def testOwner( self ) :

		p = Gaffer.FileSystemPath( self.temporaryDirectory() )
		p.append( "t" )

		with open( str( p ), "w" ) as f :
			f.write( "AAAA" )

		o = p.property( "fileSystem:owner" )
		self.assertTrue( isinstance( o, str ) )
		self.assertEqual( o, pwd.getpwuid( os.stat( str( p ) ).st_uid ).pw_name )

	def testGroup( self ) :

		p = Gaffer.FileSystemPath( self.temporaryDirectory() )
		p.append( "t" )

		with open( str( p ), "w" ) as f :
			f.write( "AAAA" )

		g = p.property( "fileSystem:group" )
		self.assertTrue( isinstance( g, str ) )
		self.assertEqual( g, grp.getgrgid( os.stat( str( p ) ).st_gid ).gr_name )

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

		os.mkdir( self.temporaryDirectory() + "/dir" )
		for n in [ "singleFile.txt", "a.001.txt", "a.002.txt", "a.004.txt", "b.003.txt" ] :
			with open( self.temporaryDirectory() + "/" + n, "w" ) as f :
				f.write( "AAAA" )

		p = Gaffer.FileSystemPath( self.temporaryDirectory(), includeSequences = True )
		self.assertTrue( p.getIncludeSequences() )

		c = p.children()
		self.assertEqual( len( c ), 8 )

		s = sorted( c, key=str )
		self.assertEqual( str(s[0]), self.temporaryDirectory() + "/a.###.txt" )
		self.assertEqual( str(s[1]), self.temporaryDirectory() + "/a.001.txt" )
		self.assertEqual( str(s[2]), self.temporaryDirectory() + "/a.002.txt" )
		self.assertEqual( str(s[3]), self.temporaryDirectory() + "/a.004.txt" )
		self.assertEqual( str(s[4]), self.temporaryDirectory() + "/b.###.txt" )
		self.assertEqual( str(s[5]), self.temporaryDirectory() + "/b.003.txt" )
		self.assertEqual( str(s[6]), self.temporaryDirectory() + "/dir" )
		self.assertEqual( str(s[7]), self.temporaryDirectory() + "/singleFile.txt" )

		for x in s :

			self.assertTrue( x.isValid() )
			if not os.path.isdir( str(x) ) :
				self.assertTrue( x.isLeaf() )

			self.assertEqual( x.property( "fileSystem:owner" ), pwd.getpwuid( os.stat( str( p ) ).st_uid ).pw_name )
			self.assertEqual( x.property( "fileSystem:group" ), grp.getgrgid( os.stat( str( p ) ).st_gid ).gr_name )
			self.assertLess( (datetime.datetime.utcnow() - x.property( "fileSystem:modificationTime" )).total_seconds(), 2 )
			if "###" not in str(x) :
				self.assertFalse( x.isFileSequence() )
				self.assertEqual( x.fileSequence(), None )
				self.assertEqual( x.property( "fileSystem:frameRange" ), "" )
				if os.path.isdir( str(x) ) :
					self.assertEqual( x.property( "fileSystem:size" ), 0 )
				else :
					self.assertEqual( x.property( "fileSystem:size" ), 4 )

		self.assertEqual( s[0].property( "fileSystem:frameRange" ), "1-2,4" )
		self.assertTrue( s[0].isFileSequence() )
		self.assertTrue( isinstance( s[0].fileSequence(), IECore.FileSequence ) )
		self.assertEqual( s[0].fileSequence(), IECore.FileSequence( str(s[0]), IECore.frameListFromList( [ 1, 2, 4 ] ) ) )
		self.assertEqual( s[0].property( "fileSystem:size" ), 4 * 3 )

		self.assertEqual( s[4].property( "fileSystem:frameRange" ), "3" )
		self.assertTrue( s[4].isFileSequence() )
		self.assertTrue( isinstance( s[4].fileSequence(), IECore.FileSequence ) )
		self.assertEqual( s[4].fileSequence(), IECore.FileSequence( str(s[4]), IECore.frameListFromList( [ 3 ] ) ) )
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
		self.assertEqual( str(s[0]), self.temporaryDirectory() + "/a.001.txt" )
		self.assertEqual( str(s[1]), self.temporaryDirectory() + "/a.002.txt" )
		self.assertEqual( str(s[2]), self.temporaryDirectory() + "/a.004.txt" )
		self.assertEqual( str(s[3]), self.temporaryDirectory() + "/b.003.txt" )
		self.assertEqual( str(s[4]), self.temporaryDirectory() + "/dir" )
		self.assertEqual( str(s[5]), self.temporaryDirectory() + "/singleFile.txt" )

		# and we can include them again
		p.setIncludeSequences( True )
		self.assertTrue( p.getIncludeSequences() )

		c = p.children()
		self.assertEqual( len( c ), 8 )

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__originalCWD = os.getcwd()

	def tearDown( self ) :

		GafferTest.TestCase.tearDown( self )

		os.chdir( self.__originalCWD )

if __name__ == "__main__":
	unittest.main()
