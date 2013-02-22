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

import IECore
import GafferImage
import os

class MergeTest( unittest.TestCase ) :

	checkerFile = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/checker.exr" )
	radialFile = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/radial.exr" )
	radialOverCheckerFile = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/radialOverChecker.exr" )

	# Create two read nodes and connect them with a merge node.
	# Test that the "over" operation is what we expect.
	def testOverOperation( self ) :
	
		background = GafferImage.ImageReader()
		background["fileName"].setValue( self.checkerFile )		
		
		foreground = GafferImage.ImageReader()
		foreground["fileName"].setValue( self.radialFile )		

		merge = GafferImage.Merge()
		merge["operation"].setValue(8) # 8 is the Enum value of the over operation.
		merge["in"].setInput(foreground["out"])
		merge["in1"].setInput(background["out"])
			
		image = merge["out"].image()
		image2 = IECore.Reader.create( self.radialOverCheckerFile ).read()
		
		image.blindData().clear()
		image2.blindData().clear()
		
		self.assertEqual( image, image2 )

	# Test that the output hash changes when the inputs are switched.
	def testHashChanged( self ) :
	
		background = GafferImage.ImageReader()
		background["fileName"].setValue( self.checkerFile )		
		
		foreground = GafferImage.ImageReader()
		foreground["fileName"].setValue( self.radialFile )		

		merge = GafferImage.Merge()
		merge["operation"].setValue(8) # 8 is the Enum value of the over operation.
		merge["in"].setInput(foreground["out"])
		merge["in1"].setInput(background["out"])
		h1 = merge["out"].image().hash()
		
		merge["in1"].setInput(foreground["out"])
		merge["in"].setInput(background["out"])
		h2 = merge["out"].image().hash()

		self.assertNotEqual( h1, h2 )

if __name__ == "__main__":
	unittest.main()
