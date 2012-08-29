##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

from __future__ import with_statement

import unittest
import shutil
import os

import IECore

import Gaffer

class FileSystemPathTest( unittest.TestCase ) :

	__dir = "/tmp/gafferFileSystemPathTest"
	
	def test( self ) :
	
		p = Gaffer.FileSystemPath( __file__ )
		
		self.assert_( p.isValid() )
		self.assert_( p.isLeaf() )
	
		while len( p ) :
		
			del p[-1]
			self.assert_( p.isValid() )
			self.assert_( not p.isLeaf() )
			
	def testIsLeaf( self ) :
	
		path = Gaffer.FileSystemPath( "/this/path/doesnt/exist" )
		self.assert_( not path.isLeaf() )
		
	def testConstructWithFilter( self ) :
	
		p = Gaffer.FileSystemPath( __file__ )
		self.failUnless( p.getFilter() is None )
		
		f = Gaffer.FileNamePathFilter( [ "*.exr" ] )
		p = Gaffer.FileSystemPath( __file__, filter = f )
		self.failUnless( p.getFilter() is f )
		
	def testBrokenSymbolicLinks( self ) :
	
		os.symlink( self.__dir + "/nonExistent", self.__dir + "/broken" )
	
		# we do want symlinks to appear in children, even if they're broken
		d = Gaffer.FileSystemPath( self.__dir )
		c = d.children()
		self.assertEqual( len( c ), 1 )
		
		l = c[0]
		self.assertEqual( str( l ), self.__dir + "/broken" )
		
		# we also want broken symlinks to report themselves as "valid",
		# because having a path return a child and then claim the child
		# is invalid seems rather useless. admittedly this is a bit of
		# a compromise.
		self.assertEqual( l.isValid(), True )
	
		# since we said it was valid, it ought to have some info
		info = l.info()
		self.failUnless( info is not None )
		
	def testSymLinkInfo( self ) :
	
		with open( self.__dir + "/a", "w" ) as f :
			f.write( "AAAA" )
	
		os.symlink( self.__dir + "/a", self.__dir + "/l" )
		
		# symlinks should report the info for the file
		# they point to.
		a = Gaffer.FileSystemPath( self.__dir + "/a" )
		l = Gaffer.FileSystemPath( self.__dir + "/l" )
		aInfo = a.info()
		self.assertEqual( aInfo["fileSystem:size"], l.info()["fileSystem:size"] )
		# unless they're broken
		os.remove( str( a ) )
		self.assertNotEqual( aInfo["fileSystem:size"], l.info()["fileSystem:size"] )
		
	def setUp( self ) :
		
		# clear out old files and make empty directory
		# to work in
		if os.path.exists( self.__dir ) :
			shutil.rmtree( self.__dir )
		os.mkdir( self.__dir )
		
if __name__ == "__main__":
	unittest.main()
	
