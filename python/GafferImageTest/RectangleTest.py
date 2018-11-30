##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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
import GafferImage
import GafferImageTest

class RectangleTest( GafferImageTest.ImageTestCase ) :

	def testDataWindow( self ) :

		a = imath.Box2f( imath.V2f( 10 ), imath.V2f( 100 ) )

		r = GafferImage.Rectangle()
		r["area"].setValue( a )
		r["lineWidth"].setValue( 10 )

		dw = r["out"]["dataWindow"].getValue()
		self.assertEqual( dw.min(), imath.V2i( a.min() ) - imath.V2i( 5 ) )
		self.assertEqual( dw.max(), imath.V2i( a.max() ) + imath.V2i( 5 ) )

	def testChannelData( self ) :

		a = imath.Box2f( imath.V2f( 0.5 ), imath.V2f( 49.5 ) )

		r = GafferImage.Rectangle()
		r["area"].setValue( a )
		r["lineWidth"].setValue( 1 )

		w = r["out"]["dataWindow"].getValue()
		s = GafferImage.Sampler( r["out"], "R", w )

		for y in range( w.min().y, w.max().y ) :
			for x in range( w.min().x, w.max().x ) :
				v = s.sample( x, y )
				if x == 0 or x == 49 or y == 0 or y == 49 :
					self.assertEqual( v, 1 )
				else :
					self.assertEqual( v, 0 )

if __name__ == "__main__":
	unittest.main()
