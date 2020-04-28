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

import IECore

import Gaffer
import GafferTest

class SequencePathTest( GafferTest.TestCase ) :

	def __dictPath( self ) :

		dict = {}
		dict["dir"] = {}
		for f in IECore.FileSequence( "a.#.exr 1-10" ).fileNames() :
			dict["dir"][f] = 1
		for f in IECore.FileSequence( "b.####.tiff 20-200x2" ).fileNames() :
			dict["dir"][f] = 1

		return Gaffer.DictPath( dict, "/" )

	def test( self ) :

		path = Gaffer.SequencePath( self.__dictPath() )

		self.assertTrue( path.isValid() )
		self.assertFalse( path.isLeaf() )

		path.append( "dir" )
		self.assertTrue( path.isValid() )
		self.assertFalse( path.isLeaf() )

		path[0] = "oops!"
		self.assertFalse( path.isValid() )
		self.assertFalse( path.isLeaf() )

		path[:] = [ "dir" ]
		children = path.children()
		for child in children :
			self.assertIsInstance( child, Gaffer.SequencePath )

		self.assertEqual( len( children ), 2 )
		childrenStrings = [ str( c ) for c in children ]
		self.assertIn( "/dir/a.#.exr 1-10", childrenStrings )
		self.assertIn( "/dir/b.####.tiff 20-200x2", childrenStrings )

	def testNonLeafChildren( self ) :

		path = Gaffer.SequencePath( self.__dictPath() )
		children = path.children()
		for child in children :
			self.assertIsInstance( child, Gaffer.SequencePath )
		self.assertEqual( len( children ), 1 )
		self.assertEqual( str( children[0] ), "/dir" )

	def testCopy( self ) :

		path = Gaffer.SequencePath( self.__dictPath() )
		path.append( "dir" )

		path2 = path.copy()
		self.assertIsInstance( path2, Gaffer.SequencePath )

		self.assertEqual( path[:], path2[:] )
		self.assertTrue( path.getFilter() is path2.getFilter() )

		c = [ str( p ) for p in path.children() ]
		c2 = [ str( p ) for p in path2.children() ]

		self.assertEqual( c, c2 )

	def testInfo( self ) :

		dictPath = self.__dictPath()
		path = Gaffer.SequencePath( dictPath )

		self.assertEqual( dictPath.info(), path.info() )

	def testInfoOfInvalidPath( self ) :

		fp = Gaffer.FileSystemPath( "/iSurelyDontExist" )
		self.assertEqual( fp.isValid(), False )
		self.assertEqual( fp.info(), None )

		sp = Gaffer.SequencePath( fp )
		self.assertEqual( sp.isValid(), False )
		self.assertEqual( sp.info(), None )

	def testFilter( self ) :

		dictPath = self.__dictPath()
		path = Gaffer.SequencePath( dictPath )

	def testIsEmpty( self ) :

		dictPath = self.__dictPath()
		path = Gaffer.SequencePath( dictPath )

		path.setFromString( "" )
		self.assertTrue( path.isEmpty() )

		path2 = path.copy()
		self.assertTrue( path2.isEmpty() )

	def testProperties( self ) :

		dictPath = self.__dictPath()
		path = Gaffer.SequencePath( dictPath )

		self.assertEqual( dictPath.propertyNames(), path.propertyNames() )
		self.assertEqual( dictPath.property( "dict:value" ), path.property( "dict:value" ) )

if __name__ == "__main__":
	unittest.main()
