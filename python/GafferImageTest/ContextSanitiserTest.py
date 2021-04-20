##########################################################################
#
#  Copyright (c) 2021, Image Engine Design Inc. All rights reserved.
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

import imath
import six

import IECore

import Gaffer
import GafferImage
import GafferImageTest

class ContextSanitiserTest( GafferImageTest.ImageTestCase ) :

	def test( self ) :

		constant = GafferImage.Constant()

		# A ContextSanitiser is automatically hooked up by ImageTestCase.setUp, so
		# we don't need to explicitly set one up
		with IECore.CapturingMessageHandler() as mh :
			with Gaffer.Context() as c :

				c["image:channelName"] = IECore.StringData( "R" )
				c["image:tileOrigin"] = IECore.V2iData( imath.V2i( 0, 0 ) )

				constant["out"]["metadata"].getValue()
				constant["out"]["sampleOffsets"].getValue()
				constant["out"]["channelData"].getValue()

				c["image:channelName"] = IECore.IntData( 5 )

				with six.assertRaisesRegex( self, IECore.Exception, 'Context variable is not of type "StringData"' ) :
					constant["out"]["metadata"].getValue()

		for message in mh.messages :
			self.assertEqual( message.level, mh.Level.Warning )
			self.assertEqual( message.context, "ContextSanitiser" )

		self.assertEqual(
			[ m.message for m in mh.messages ],
			[
				'image:channelName in context for Constant.out.metadata computeNode:hash',
				'image:tileOrigin in context for Constant.out.metadata computeNode:hash',
				'image:channelName in context for Constant.out.sampleOffsets computeNode:compute'
			]
		)

if __name__ == "__main__":
	unittest.main()
