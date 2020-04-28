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

class DictPathTest( GafferTest.TestCase ) :

	def test( self ) :

		d = {
			"one" : 1,
			"two" : 2,
			"three" : "three",
			"d" : {
				"e" : {
					"four" : 4,
				},
				"five" : 5,
			},
			"f" : {},
		}

		p = Gaffer.DictPath( d, "/" )

		self.assertTrue( p.isValid() )
		self.assertFalse( p.isLeaf() )

		children = p.children()
		self.assertEqual( len( children ), 5 )
		for child in children :
			self.assertIsInstance( child, Gaffer.DictPath )
			if child[-1] in ( "d", "f" ) :
				self.assertFalse( child.isLeaf() )
				self.assertNotIn( "value", child.info() )
			else :
				self.assertTrue( child.isLeaf() )
				self.assertTrue( "dict:value" in child.info() )

		p.setFromString( "/d/e/four" )
		self.assertEqual( p.info()["dict:value"], 4 )

		p.setFromString( "/d/e/fourfdsfsd" )
		self.assertFalse( p.isValid() )

	def testCopy( self ) :

		d = {
			"one" : 1,
			"two" : 2,
		}

		p = Gaffer.DictPath( d, "/one" )

		pp = p.copy()
		self.assertEqual( str( pp ), str( p ) )
		self.assertEqual( pp, p )
		self.assertFalse( p != p )

		del pp[-1]
		self.assertNotEqual( str( pp ), str( p ) )
		self.assertNotEqual( pp, p )
		self.assertTrue( pp != p )

	def testRepr( self ) :

		d = {
			"one" : 1,
			"two" : 2,
		}

		p = Gaffer.DictPath( d, "/one" )

		self.assertEqual( repr( p ), "DictPath( '/one' )" )

	def testDictTypes( self ) :

		d = {
			"a" : IECore.CompoundObject( {
				"b" : IECore.IntData( 10 ),
			} ),
			"c" : IECore.CompoundData( {
				"d" : IECore.StringData( "e" ),
			} ),
		}

		self.assertEqual( Gaffer.DictPath( d, "/" ).isLeaf(), False )
		self.assertEqual( Gaffer.DictPath( d, "/a" ).isLeaf(), False )
		self.assertEqual( Gaffer.DictPath( d, "/a/b" ).isLeaf(), True )
		self.assertEqual( Gaffer.DictPath( d, "/c" ).isLeaf(), False )
		self.assertEqual( Gaffer.DictPath( d, "/c/d" ).isLeaf(), True )

		self.assertEqual( Gaffer.DictPath( d, "/", dictTypes=( dict, IECore.CompoundData ) ).isLeaf(), False )
		self.assertEqual( Gaffer.DictPath( d, "/a", dictTypes=( dict, IECore.CompoundData ) ).isLeaf(), True )
		self.assertEqual( Gaffer.DictPath( d, "/a/b" ).isLeaf(), True )
		self.assertEqual( Gaffer.DictPath( d, "/c" ).isLeaf(), False )
		self.assertEqual( Gaffer.DictPath( d, "/c/d" ).isLeaf(), True )

	def testDictTypesCopy( self ) :

		d = {
			"a" : IECore.CompoundObject( {
				"b" : IECore.IntData( 10 ),
			} ),
			"c" : IECore.CompoundData( {
				"d" : IECore.StringData( "e" ),
			} ),
		}

		p = Gaffer.DictPath( d, "/a", dictTypes=( dict, IECore.CompoundData ) )
		self.assertEqual( p.isLeaf(), True )

		pp = p.copy()
		self.assertEqual( pp.isLeaf(), True )

	def testChildDictTypes( self ) :

		d = {
			"a" : IECore.CompoundObject()
		}

		p = Gaffer.DictPath( d, "/" )
		c = p.children()[0]
		self.assertEqual( c.isLeaf(), False )

		p = Gaffer.DictPath( d, "/", dictTypes = ( dict, ) )
		c = p.children()[0]
		self.assertEqual( c.isLeaf(), True )

	def testRelative( self ) :

		d = {
			"one" : 1,
			"two" : 2,
			"three" : "three",
			"d" : {
				"e" : {
					"four" : 4,
				},
				"five" : 5,
			},
			"f" : {},
		}

		p = Gaffer.DictPath( d, "d" )
		self.assertEqual( str( p ), "d" )
		self.assertTrue( "d/e" in [ str( c ) for c in p.children() ] )
		self.assertTrue( "d/five" in [ str( c ) for c in p.children() ] )

		p2 = p.copy()
		self.assertEqual( str( p2 ), "d" )
		self.assertTrue( "d/e" in [ str( c ) for c in p2.children() ] )
		self.assertTrue( "d/five" in [ str( c ) for c in p2.children() ] )

	def testProperties( self ) :

		d = {
			"one" : 1,
			"d" : {
				"two" : 2,
			},
		}

		p = Gaffer.DictPath( d, "/one" )
		self.assertTrue( "dict:value" in p.propertyNames() )
		self.assertEqual( p.property( "dict:value"), 1 )

		p = Gaffer.DictPath( d, "/d" )
		self.assertEqual( p.property( "dict:value"), None )

		p = Gaffer.DictPath( d, "/ invalid" )
		self.assertEqual( p.property( "dict:value"), None )

if __name__ == "__main__":
	unittest.main()
