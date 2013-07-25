##########################################################################
#  
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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
import os

import IECore

import Gaffer

class IndexedIOPathTest( unittest.TestCase ) :

	__fileName = "/tmp/test.fio"

	def setUp( self ) :
	
		f = IECore.FileIndexedIO( self.__fileName, IECore.IndexedIO.OpenMode.Write )
		d1 = f.subdirectory( "d1", IECore.FileIndexedIO.MissingBehaviour.CreateIfMissing )
		d2 = d1.subdirectory( "d2", IECore.FileIndexedIO.MissingBehaviour.CreateIfMissing )
		d2.write( "a", 1 )
		d2.write( "b", 2 )
		d2.write( "c", "three" )
		d2.write( "d", IECore.IntVectorData( [ 1, 2, 3 ] ) )
		f.subdirectory( "d3", IECore.FileIndexedIO.MissingBehaviour.CreateIfMissing )

	def testConstructFromFileName( self ) :
	
		p = Gaffer.IndexedIOPath( self.__fileName, "/" )
		self.failUnless( p.isValid() )
		
		p.append( "d1" )
		self.failUnless( p.isValid() )
		
		p.append( "notHere" )
		self.failIf( p.isValid() )
		
	def testConstructFromIndexedIO( self ) :
	
		p = Gaffer.IndexedIOPath( IECore.FileIndexedIO( self.__fileName, IECore.IndexedIO.OpenMode.Read ), "/" )
		self.failUnless( p.isValid() )
		
		p.append( "d1" )
		self.failUnless( p.isValid() )
		
		p.append( "notHere" )
		self.failIf( p.isValid() )
		
	def testChildren( self ) :
	
		p = Gaffer.IndexedIOPath( self.__fileName, "/" )

		c = p.children()		
		self.assertEqual( len( c ), 2 )
		
		cs = [ str( x ) for x in c ]
		self.failUnless( "/d1" in cs )
		self.failUnless( "/d3" in cs )
		
	def testInfo( self ) :
	
		p = Gaffer.IndexedIOPath( self.__fileName, "/d1/d2/c" )
		i = p.info()
		
		self.assertEqual( i["indexedIO:entryType"], IECore.IndexedIO.EntryType.File )		
		self.assertEqual( i["indexedIO:dataType"], IECore.IndexedIO.DataType.String )
		
		p = Gaffer.IndexedIOPath( self.__fileName, "/d1/d2/d" )
		i = p.info()
		
		self.assertEqual( i["indexedIO:entryType"], IECore.IndexedIO.EntryType.File )		
		self.assertEqual( i["indexedIO:dataType"], IECore.IndexedIO.DataType.IntArray )
		self.assertEqual( i["indexedIO:arrayLength"], 3 )
		
		p = Gaffer.IndexedIOPath( self.__fileName, "/d1/d2" )
		i = p.info()
		self.assertEqual( i["indexedIO:entryType"], IECore.IndexedIO.EntryType.Directory )		
	
	def testData( self ) :
	
		p = Gaffer.IndexedIOPath( self.__fileName, "/d1/d2/c" )
		self.assertEqual( p.data(), IECore.StringData( "three" ) )
		
	def testRelative( self ) :

		p = Gaffer.IndexedIOPath( self.__fileName, "d1/d2" )
		self.assertEqual( str( p ), "d1/d2" )
		self.assertEqual( p.root(), "" )
		self.assertTrue( "d1/d2/a" in [ str( c ) for c in p.children() ] )
		
		p2 = p.copy()
		self.assertEqual( str( p2 ), "d1/d2" )
		self.assertEqual( p2.root(), "" )
		self.assertTrue( "d1/d2/a" in [ str( c ) for c in p2.children() ] )
			
	def tearDown( self ) :
	
		if os.path.exists( self.__fileName ) :
			os.remove( self.__fileName )
	
if __name__ == "__main__":
	unittest.main()
	
