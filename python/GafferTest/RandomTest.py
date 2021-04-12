##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import imath

import IECore

import Gaffer
import GafferTest

class RandomTest( GafferTest.TestCase ) :

	def testHashes( self ) :

		r = Gaffer.Random()
		self.assertHashesValid( r, inputsToIgnore = [ r["contextEntry"], ] )

	def testOutFloat( self ) :

		r = Gaffer.Random()
		v1 = r["outFloat"].getValue()

		r["seed"].setValue( 1 )
		v2 = r["outFloat"].getValue()

		self.assertNotEqual( v1, v2 )

		r["floatRange"].setValue( imath.V2f( 2, 3 ) )
		v3 = r["outFloat"].getValue()

		self.assertNotEqual( v2, v3 )

	def testOutFloatRange( self ) :

		r = Gaffer.Random()
		r["floatRange"].setValue( imath.V2f( 10, 11 ) )

		for s in range( 0, 1000 ) :

			r["seed"].setValue( s )
			v = r["outFloat"].getValue()
			self.assertGreaterEqual( v, r["floatRange"].getValue()[0] )
			self.assertLessEqual( v, r["floatRange"].getValue()[1] )

	def testContext( self ) :

		r = Gaffer.Random()
		r["contextEntry"].setValue( "frame" )

		c = Gaffer.Context()

		c.setFrame( 1 )
		with c :
			v1 = r["outFloat"].getValue()

		c.setFrame( 2 )
		with c :
			v2 = r["outFloat"].getValue()

		self.assertNotEqual( v1, v2 )

	def testColor( self ) :

		r = Gaffer.Random()
		r["seed"].setValue( 1 )

		r["baseColor"].setValue( imath.Color3f( 0.25, 0.5, 0 ) )

		c1 = r["outColor"].getValue()
		c2 = r.randomColor( 1 )

		self.assertEqual( c1, c2 )

	def testMissingContextDoesntError( self ) :

		# when randomising things based on scene:path etc,
		# the required context entry may well not exist when
		# the ui is evaluating the value to be displayed in
		# a PlugValueWidget. we therefore need the Random
		# node to not be too fussy and just ignore missing context
		# items.

		r = Gaffer.Random()

		f1 = r["outFloat"].getValue()

		r["contextEntry"].setValue( "frame" )
		self.assertNotEqual( f1, r["outFloat"].getValue() )

		r["contextEntry"].setValue( "oops!" )
		self.assertEqual( f1, r["outFloat"].getValue() )

	def testAffects( self ) :

		r = Gaffer.Random()

		o = [ x.relativeName( r ) for x in r.affects( r["seed"] ) ]

		self.assertEqual( len( o ), 4 )
		self.assertTrue( "outColor.r" in o )
		self.assertTrue( "outColor.g" in o )
		self.assertTrue( "outColor.b" in o )
		self.assertTrue( "outFloat" in o )

		o = [ x.relativeName( r ) for x in r.affects( r["saturation"] ) ]

		self.assertEqual( len( o ), 3 )
		self.assertTrue( "outColor.r" in o )
		self.assertTrue( "outColor.g" in o )
		self.assertTrue( "outColor.b" in o )

		o = [ x.relativeName( r ) for x in r.affects( r["floatRange"][0] ) ]

		self.assertEqual( o, [ "outFloat" ] )

	def testNegativeSeeds( self ) :

		r = Gaffer.Random()
		r["seed"].setValue( -1 )
		self.assertEqual( r["seed"].getValue(), 0 )
		r["baseColor"].setValue( imath.Color3f( 0.25, 0.5, 0 ) )
		c1 = r["outColor"].getValue()
		c2 = r.randomColor( 0 )

		self.assertEqual( c1, c2 )

		r["seed"].setValue( -5 )
		c3 = r["outColor"].getValue()
		c4 = r.randomColor( -5 )

		self.assertEqual( c3, c4 )
		self.assertEqual( c3, c2 )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testRandomPerf( self ) :

		GafferTest.testRandomPerf()

if __name__ == "__main__":
	unittest.main()
