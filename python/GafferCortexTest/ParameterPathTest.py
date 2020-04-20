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
import GafferCortex

class ParameterPathTest( GafferTest.TestCase ) :

	def __parameters( self ) :

		return IECore.CompoundParameter(

			"p",
			"",

			members = [

				IECore.IntParameter(
					"a",
					"",
					1
				),

				IECore.FloatParameter(
					"b",
					"",
					1
				),

				IECore.CompoundParameter(

					"c",
					"",

					members = [

						IECore.IntParameter(
							"d",
							"",
							1
						),

						IECore.FloatParameter(
							"e",
							"",
							1
						),

					]

				),

				IECore.CompoundVectorParameter(

					"cv",
					"",
					members = [

						IECore.StringVectorParameter(
							"s",
							"",
							IECore.StringVectorData(),
						),

						IECore.BoolVectorParameter(
							"b",
							"",
							IECore.BoolVectorData(),
						)

					]

				),

			],

		)

	def test( self ) :

		p = self.__parameters()

		p = GafferCortex.ParameterPath( p, "/" )

		self.assertTrue( p.isValid() )
		self.assertFalse( p.isLeaf() )

		children = p.children()
		self.assertEqual( len( children ), 4 )
		for child in children :
			self.assertIsInstance( child, GafferCortex.ParameterPath )
			if child[-1] in ( "c", "cv" ) :
				self.assertFalse( child.isLeaf() )
			else :
				self.assertTrue( child.isLeaf() )
			self.assertEqual( child[-1], child.info()["parameter:parameter"].name )

	def testChildOrdering( self ) :

		p = GafferCortex.ParameterPath( self.__parameters(), "/" )

		self.assertEqual(
			[ str( c ) for c in p.children() ],
			[ "/a", "/b", "/c", "/cv" ]
		)

		p = GafferCortex.ParameterPath( self.__parameters(), "/c" )
		self.assertEqual(
			[ str( c ) for c in p.children() ],
			[ "/c/d", "/c/e" ]
		)

	def testCopy( self ) :

		p = GafferCortex.ParameterPath( self.__parameters(), "/c" )

		pp = p.copy()
		self.assertEqual( str( pp ), str( p ) )
		self.assertEqual( pp, p )
		self.assertFalse( p != p )

		del pp[-1]
		self.assertNotEqual( str( pp ), str( p ) )
		self.assertNotEqual( pp, p )
		self.assertTrue( pp != p )

	def testRepr( self ) :

		p = GafferCortex.ParameterPath( self.__parameters(), "/c" )

		self.assertEqual( repr( p ), "ParameterPath( '/c' )" )

	def testForcedLeafTypes( self ) :

		p = GafferCortex.ParameterPath( self.__parameters(), "/c" )

		self.assertEqual( GafferCortex.ParameterPath( self.__parameters(), "/" ).isLeaf(), False )
		self.assertEqual( GafferCortex.ParameterPath( self.__parameters(), "/a" ).isLeaf(), True )
		self.assertEqual( GafferCortex.ParameterPath( self.__parameters(), "/b" ).isLeaf(), True )
		self.assertEqual( GafferCortex.ParameterPath( self.__parameters(), "/c" ).isLeaf(), False )
		self.assertEqual( GafferCortex.ParameterPath( self.__parameters(), "/c/d" ).isLeaf(), True )
		self.assertEqual( GafferCortex.ParameterPath( self.__parameters(), "/c/e" ).isLeaf(), True )
		self.assertEqual( GafferCortex.ParameterPath( self.__parameters(), "/cv" ).isLeaf(), False )
		self.assertEqual( GafferCortex.ParameterPath( self.__parameters(), "/cv/s" ).isLeaf(), True )
		self.assertEqual( GafferCortex.ParameterPath( self.__parameters(), "/cv/b" ).isLeaf(), True )

		kw = { "forcedLeafTypes" : ( IECore.CompoundVectorParameter, ) }

		self.assertEqual( GafferCortex.ParameterPath( self.__parameters(), "/", **kw ).isLeaf(), False )
		self.assertEqual( GafferCortex.ParameterPath( self.__parameters(), "/a", **kw ).isLeaf(), True )
		self.assertEqual( GafferCortex.ParameterPath( self.__parameters(), "/b", **kw ).isLeaf(), True )
		self.assertEqual( GafferCortex.ParameterPath( self.__parameters(), "/c", **kw ).isLeaf(), False )
		self.assertEqual( GafferCortex.ParameterPath( self.__parameters(), "/c/d", **kw ).isLeaf(), True )
		self.assertEqual( GafferCortex.ParameterPath( self.__parameters(), "/c/e", **kw ).isLeaf(), True )
		self.assertEqual( GafferCortex.ParameterPath( self.__parameters(), "/cv", **kw ).isLeaf(), True )

		self.assertEqual( GafferCortex.ParameterPath( self.__parameters(), "/cv", **kw ).children(), [] )

	def testForcedLeafTypesCopy( self ) :

		p = GafferCortex.ParameterPath( self.__parameters(), "/cv", forcedLeafTypes = ( IECore.CompoundVectorParameter, ) )
		self.assertEqual( p.isLeaf(), True )

		pp = p.copy()
		self.assertEqual( pp.isLeaf(), True )

	def testChildForcedLeafTypes( self ) :

		p = GafferCortex.ParameterPath( self.__parameters(), "/", forcedLeafTypes = ( IECore.CompoundVectorParameter, ) )

		c = p.children()[3]
		self.assertEqual( str( c ), "/cv" )
		self.assertEqual( c.isLeaf(), True )

	def testRelative( self ) :

		p = GafferCortex.ParameterPath( self.__parameters(), "c", forcedLeafTypes = ( IECore.CompoundVectorParameter, ) )

		self.assertEqual( str( p ), "c" )
		self.assertTrue( "c/d" in [ str( c ) for c in p.children() ] )
		self.assertTrue( "c/e" in [ str( c ) for c in p.children() ] )

		p2 = p.copy()
		self.assertEqual( str( p2 ), "c" )
		self.assertTrue( "c/d" in [ str( c ) for c in p2.children() ] )
		self.assertTrue( "c/e" in [ str( c ) for c in p2.children() ] )

if __name__ == "__main__":
	unittest.main()
