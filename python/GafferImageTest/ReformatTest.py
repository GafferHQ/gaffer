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

import IECore
import Gaffer
import GafferImage
import os

class ReformatTest( unittest.TestCase ) :

	path = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/" )

	# Test a reformat on an image with a data window that is different to the display window.
	def testDataWindow( self ) :

		read = GafferImage.ImageReader()
		read["fileName"].setValue( os.path.join( self.path, "blueWithDataWindow.100x100.exr" ) )
		readWindow = read["out"]["dataWindow"].getValue()
		
		# Resize the image and check the size of the output data window.
		reformat = GafferImage.Reformat()
		reformat["format"].setValue( GafferImage.Format( 150, 125, 1. ) )
		reformat["in"].setInput( read["out"] )
		reformatWindow = reformat["out"]["dataWindow"].getValue()
		self.assertEqual( reformatWindow, IECore.Box2i( IECore.V2i( 45, 25 ), IECore.V2i( 119, 99 )  ) )
		
	# Test that when the input and output format are the same that the hash is passed through.
	def testHashPassThrough( self ) :

		read = GafferImage.ImageReader()
		read["fileName"].setValue( os.path.join( self.path, "checkerboard.100x100.exr" ) )
		readFormat = read["out"]["format"].getValue()
		
		# Set the reformat node's format plug to be the same as the read node.
		reformat = GafferImage.Reformat()
		reformat["in"].setInput( read["out"] )
		reformat["format"].setValue( readFormat )
		
		# Check that it passes through the hash for the channel data.
		h1 = read["out"].channelData( "G", IECore.V2i( 0 ) ).hash()
		h2 = reformat["out"].channelData( "G", IECore.V2i( 0 ) ).hash()
		self.assertEqual( h1, h2 )
		
		# Now assert that the hash changes when set to something else.
		reformat["format"].setValue( GafferImage.Format( 128, 256, 1. ) )
		
		h2 = reformat["out"].channelData( "G", IECore.V2i( 0 ) ).hash()
		self.assertNotEqual( h1, h2 )

	# Tests all filters against images of their expected result.
	def testFilters( self ) :
		
		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( os.path.join( self.path, "checkerboard.100x100.exr" ) )

		reformat = GafferImage.Reformat()
		reformat["format"].setValue( GafferImage.Format( 200, 150, 1. ) )
		reformat["in"].setInput( reader["out"] )
		
		expectedOutput = GafferImage.ImageReader()

		# Test all of the registered filters.	
		filters = GafferImage.FilterPlug.filters()	
		for filter in filters:
			file = "checker" + filter + ".200x100.exr"
			expectedOutput["fileName"].setValue( os.path.join( self.path, file ) )
			reformat["filter"].setValue( filter )

			op = IECore.ImageDiffOp()
			res = op(
				imageA = expectedOutput["out"].image(),
				imageB = reformat["out"].image()
			)
			
			self.assertFalse( res.value )	
		

