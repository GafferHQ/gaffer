##########################################################################
#
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

import os
import unittest
import imath

import IECore
import IECoreImage

import GafferUI
import GafferUITest

class ImageGadgetTest( GafferUITest.TestCase ) :

	def testConstructFromImagePrimitive( self ) :

		window = imath.Box2i( imath.V2i( 0 ), imath.V2i( 255 ) )
		imagePrimitive = IECoreImage.ImagePrimitive.createRGBFloat( imath.Color3f( 0.25, .5, .75 ), window, window )

		i = GafferUI.ImageGadget( imagePrimitive )
		self.assertEqual( i.bound(), imath.Box3f( imath.V3f( -128, -128, 0 ), imath.V3f( 128, 128, 0 ) ) )

	def testConstructFromFile( self ) :

		i = GafferUI.ImageGadget( "arrowRight10.png" )

		self.assertEqual( i.bound(), imath.Box3f( imath.V3f( -5, -5, 0 ), imath.V3f( 5, 5, 0 ) ) )

	def testMissingFiles( self ) :

		self.assertRaises( Exception, GafferUI.ImageGadget, "iDonNotExist" )

	def testTextureLoader( self ) :

		# must access an attribute from IECoreGL to force import
		# before calling textureLoader(), because it is imported
		# lazily by GafferUI.
		import IECoreGL
		IECoreGL.TextureLoader

		l = GafferUI.ImageGadget.textureLoader()
		self.assertTrue( isinstance( l, IECoreGL.TextureLoader ) )

if __name__ == "__main__":
	unittest.main()
