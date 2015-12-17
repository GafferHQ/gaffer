##########################################################################
#
#  Copyright (c) 2015, John Haddon. All rights reserved.
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
import GafferImage
import GafferImageTest

class BlurTest( GafferImageTest.ImageTestCase ) :

	def testPassThrough( self ) :

		c = GafferImage.Constant()

		b = GafferImage.Blur()
		b["in"].setInput( c["out"] )
		b["radius"].setValue( IECore.V2f( 0 ) )

		self.assertEqual( c["out"].imageHash(), b["out"].imageHash() )
		self.assertEqual( c["out"].image(), b["out"].image() )

	def testNonFlatHashPassThrough( self ) :

		blur = GafferImage.Blur()
		blur["radius"].setValue( IECore.V2f( 1 ) )

		self._testNonFlatHashPassThrough( blur )

	def testExpandDataWindow( self ) :

		c = GafferImage.Constant()

		b = GafferImage.Blur()
		b["in"].setInput( c["out"] )
		b["radius"].setValue( IECore.V2f( 1 ) )

		self.assertEqual( b["out"]["dataWindow"].getValue(), c["out"]["dataWindow"].getValue() )

		b["expandDataWindow"].setValue( True )

		self.assertEqual( b["out"]["dataWindow"].getValue().min, c["out"]["dataWindow"].getValue().min - IECore.V2i( 2 ) )
		self.assertEqual( b["out"]["dataWindow"].getValue().max, c["out"]["dataWindow"].getValue().max + IECore.V2i( 2 ) )

	def testOnePixelBlur( self ) :

		constant = GafferImage.Constant()
		constant["color"].setValue( IECore.Color4f( 1 ) )

		crop = GafferImage.Crop()
		crop["in"].setInput( constant["out"] )
		crop["area"].setValue( IECore.Box2i( IECore.V2i( 10 ), IECore.V2i( 11 ) ) )
		crop["affectDisplayWindow"].setValue( False )

		blur = GafferImage.Blur()
		blur["in"].setInput( crop["out"] )
		blur["radius"].setValue( IECore.V2f( 1 ) )
		blur["expandDataWindow"].setValue( True )

		sampler = GafferImage.Sampler( blur["out"], "R", IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 20 ) ) )

		# Centre is brightest
		self.assertGreater( sampler.sample( 10, 10 ), sampler.sample( 11, 10 ) )

		# Corners are least bright
		self.assertGreater( sampler.sample( 11, 10 ), sampler.sample( 11, 11 ) )
		self.assertGreater( sampler.sample( 11, 11 ), 0 )

		# Shape is symmetrical
		self.assertEqual( sampler.sample( 11, 10 ), sampler.sample( 9, 10 ) )
		self.assertEqual( sampler.sample( 10, 11 ), sampler.sample( 10, 9 ) )
		self.assertEqual( sampler.sample( 10, 11 ), sampler.sample( 10, 9 ) )

		self.assertEqual( sampler.sample( 9, 9 ), sampler.sample( 11, 9 ) )
		self.assertEqual( sampler.sample( 9, 9 ), sampler.sample( 11, 11 ) )
		self.assertEqual( sampler.sample( 9, 9 ), sampler.sample( 9, 11 ) )

	def testEnergyPreservation( self ) :

		constant = GafferImage.Constant()
		constant["color"].setValue( IECore.Color4f( 1 ) )

		crop = GafferImage.Crop()
		crop["in"].setInput( constant["out"] )
		crop["area"].setValue( IECore.Box2i( IECore.V2i( 10 ), IECore.V2i( 11 ) ) )
		crop["affectDisplayWindow"].setValue( False )

		blur = GafferImage.Blur()
		blur["in"].setInput( crop["out"] )
		blur["expandDataWindow"].setValue( True )

		stats = GafferImage.ImageStats()
		stats["in"].setInput( blur["out"] )
		stats["regionOfInterest"].setValue( IECore.Box2i( IECore.V2i( 5 ), IECore.V2i( 15 ) ) )

		for i in range( 0, 10 ) :

			blur["radius"].setValue( IECore.V2f( i * 0.5 ) )
			self.assertAlmostEqual( stats["average"]["r"].getValue(), 1 / 100., delta = 0.0001 )

if __name__ == "__main__":
	unittest.main()
