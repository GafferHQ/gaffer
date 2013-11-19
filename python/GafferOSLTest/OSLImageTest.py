##########################################################################
#  
#  Copyright (c) 2013, John Haddon. All rights reserved.
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

import Gaffer
import GafferTest
import GafferImage
import GafferOSL
import GafferOSLTest

class OSLImageTest( GafferOSLTest.OSLTestCase ) :

	def test( self ) :
	
		getRed = GafferOSL.OSLShader()
		getRed.loadShader( "imageProcessing/getChannel" )
		getRed["parameters"]["channelName"].setValue( "R" )
		
		getGreen = GafferOSL.OSLShader()
		getGreen.loadShader( "imageProcessing/getChannel" )
		getGreen["parameters"]["channelName"].setValue( "G" )
		
		getBlue = GafferOSL.OSLShader()
		getBlue.loadShader( "imageProcessing/getChannel" )
		getBlue["parameters"]["channelName"].setValue( "B" )
		
		buildColor = GafferOSL.OSLShader()
		buildColor.loadShader( "utility/buildColor" )
		buildColor["parameters"]["r"].setInput( getBlue["out"]["channelValue"] )
		buildColor["parameters"]["g"].setInput( getGreen["out"]["channelValue"] )
		buildColor["parameters"]["b"].setInput( getRed["out"]["channelValue"] )
		
		constant = GafferOSL.OSLShader()
		constant.loadShader( "surface/constant" )
		constant["parameters"]["Cs"].setInput( buildColor["out"]["c"] )
		
		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/rgb.100x100.exr" ) )
		
		image = GafferOSL.OSLImage()
		image["in"].setInput( reader["out"] )
		
		# we haven't connected the shader yet, so the node should act as a pass through
		
		self.assertEqual( image["out"].image(), reader["out"].image() )
		self.assertEqual( image["out"].imageHash(), reader["out"].imageHash() )

		# that should all change when we hook up a shader
		
		cs = GafferTest.CapturingSlot( image.plugDirtiedSignal() )
		image["shader"].setInput( constant["out"] )
		
		self.assertEqual( len( cs ), 4 )
		self.assertTrue( cs[0][0].isSame( image["shader"] ) )
		self.assertTrue( cs[1][0].isSame( image["__shading"] ) )
		self.assertTrue( cs[2][0].isSame( image["out"]["channelData"] ) )
		self.assertTrue( cs[3][0].isSame( image["out"] ) )
		
		inputImage = reader["out"].image()
		outputImage = image["out"].image()
		
		self.assertNotEqual( inputImage, outputImage )
		self.assertEqual( outputImage["R"].data, inputImage["B"].data )
		self.assertEqual( outputImage["G"].data, inputImage["G"].data )
		self.assertEqual( outputImage["B"].data, inputImage["R"].data )
		
		# changes in the shader network should signal more dirtiness
		
		del cs[:]
		
		getGreen["parameters"]["channelName"].setValue( "R" )
		
		self.assertEqual( len( cs ), 4 )
		self.assertTrue( cs[0][0].isSame( image["shader"] ) )
		self.assertTrue( cs[1][0].isSame( image["__shading"] ) )
		self.assertTrue( cs[2][0].isSame( image["out"]["channelData"] ) )
		self.assertTrue( cs[3][0].isSame( image["out"] ) )
		
		del cs[:]
	
		buildColor["parameters"]["r"].setInput( getRed["out"]["channelValue"] )
		
		self.assertEqual( len( cs ), 4 )
		self.assertTrue( cs[0][0].isSame( image["shader"] ) )
		self.assertTrue( cs[1][0].isSame( image["__shading"] ) )
		self.assertTrue( cs[2][0].isSame( image["out"]["channelData"] ) )
		self.assertTrue( cs[3][0].isSame( image["out"] ) )

		inputImage = reader["out"].image()
		outputImage = image["out"].image()
		
		self.assertEqual( outputImage["R"].data, inputImage["R"].data )
		self.assertEqual( outputImage["G"].data, inputImage["R"].data )
		self.assertEqual( outputImage["B"].data, inputImage["R"].data )
		
if __name__ == "__main__":
	unittest.main()
