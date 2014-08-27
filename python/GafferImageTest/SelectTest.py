##########################################################################
#
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
import os
import IECore
import GafferImage

class SelectTest( unittest.TestCase ) :

	rPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/redWithDataWindow.100x100.exr" )
	gPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/greenWithDataWindow.100x100.exr" )
	bPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/blueWithDataWindow.100x100.exr" )

	# Do several tests to check the cache is working correctly:
	def testHashPassThrough( self ) :

		r1 = GafferImage.ImageReader()
		r1["fileName"].setValue( self.rPath )

		r2 = GafferImage.ImageReader()
		r2["fileName"].setValue( self.gPath )

		r3 = GafferImage.ImageReader()
		r3["fileName"].setValue( self.bPath )

		##########################################
		# Test to see if the hash changes when we set the select plug.
		##########################################
		s = GafferImage.Select()
		s["select"].setValue(1)
		s["in"].setInput(r1["out"])
		s["in1"].setInput(r2["out"])
		s["in2"].setInput(r3["out"])

		h1 = s["out"].image().hash()
		h2 = r2["out"].image().hash()
		self.assertEqual( h1, h2 )

		s["select"].setValue(0)
		h1 = s["out"].image().hash()
		h2 = r1["out"].image().hash()
		self.assertEqual( h1, h2 )

		s["select"].setValue(2)
		h1 = s["out"].image().hash()
		h2 = r3["out"].image().hash()
		self.assertEqual( h1, h2 )

if __name__ == "__main__":
	unittest.main()
