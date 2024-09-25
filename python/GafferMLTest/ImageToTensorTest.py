##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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
import GafferImage
import GafferML

class ImageToTensorTest( GafferTest.TestCase ) :

	def testMissingChannels( self ) :

		checker = GafferImage.Checkerboard()
		tensor = GafferML.ImageToTensor()
		tensor["image"].setInput( checker["out"] )
		tensor["channels"].setValue( IECore.StringVectorData( [ "Y" ] ) )

		with self.assertRaisesRegex( Gaffer.ProcessException, 'Channel "Y" does not exist' ) :
			tensor["tensor"].getValue()

	def testShufflingChannelsChangesHash( self ) :

		checker = GafferImage.Checkerboard()
		tensor = GafferML.ImageToTensor()
		tensor["image"].setInput( checker["out"] )

		self.assertEqual( tensor["channels"].getValue(), IECore.StringVectorData( [ "R", "G", "B" ] ) )
		h1 = tensor["tensor"].hash()

		tensor["channels"].setValue( IECore.StringVectorData( [ "B", "G", "R" ] ) )
		self.assertNotEqual( tensor["tensor"].hash(), h1 )

if __name__ == "__main__":
	unittest.main()