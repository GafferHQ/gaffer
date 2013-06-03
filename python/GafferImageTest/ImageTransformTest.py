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
import os
import Gaffer
import GafferTest
import GafferImage

class ImageTransformTest( unittest.TestCase ) :

	fileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/checker.exr" )
	path = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/" )

	def testIdentityHash( self ) :
		
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.fileName )		

		t = GafferImage.ImageTransform()
		t["in"].setInput( r["out"] )
		
		c = Gaffer.Context()
		c["image:channelName"] = "R"
		c["image:tileOrigin"] = IECore.V2i( 0 )
		with c :
			h1 = t["out"].hash();	
			h2 = r["out"].hash();	
			self.assertEqual( h1, h2 )	
		
	def testScaleHash( self ) :
		
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.fileName )		

		t = GafferImage.ImageTransform()
		t["in"].setInput( r["out"] )

		h1 = t["__scaledFormat"].hash();	
		t["transform"]["scale"].setValue( IECore.V2f( 2., 2. ) );	
		h2 = t["__scaledFormat"].hash();	
		self.assertNotEqual( h1, h2 )	
		
	def testDirtyPropagation( self ) :
	
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.fileName )		

		t = GafferImage.ImageTransform()
		t["in"].setInput( r["out"] )
		
		cs = GafferTest.CapturingSlot( t.plugDirtiedSignal() )
		t["transform"]["scale"].setValue( IECore.V2f( 2., 2. ) );	
		
		dirtiedPlugs = set( [ x[0].relativeName( x[0].node() ) for x in cs ] )
		self.assertEqual( len( dirtiedPlugs ), 4 )
		self.assertTrue( "out" in dirtiedPlugs )
		self.assertTrue( "out.channelData" in dirtiedPlugs )
		self.assertTrue( "out.dataWindow" in dirtiedPlugs )
		self.assertTrue( "__scaledFormat" in dirtiedPlugs )

	def testOutputFormat( self ) :
	
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.fileName )		

		t = GafferImage.ImageTransform()
		t["in"].setInput( r["out"] )
		t["transform"]["translate"].setValue( IECore.V2f( 2., 2. ) );	
		
		c = Gaffer.Context()
		c["image:channelName"] = "R"
		c["image:tileOrigin"] = IECore.V2i( 0 )
		with c :
			self.assertEqual( t["out"]["format"].hash(), r["out"]["format"].hash() )

	def testHashPassThrough( self ) :
	
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.fileName )		

		t = GafferImage.ImageTransform()
		t["in"].setInput( r["out"] )
		
		c = Gaffer.Context()
		c["image:channelName"] = "R"
		c["image:tileOrigin"] = IECore.V2i( 0 )
		t["enabled"].setValue( True )
		with c :
			self.assertEqual( r["out"].hash(), t["out"].hash() )
		
			t["transform"]["translate"].setValue( IECore.V2f( 20., 20.5 ) );	
			self.assertNotEqual( r["out"].hash(), t["out"].hash() )
	
	def testDisabled( self ) :
	
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.fileName )		

		t = GafferImage.ImageTransform()
		t["in"].setInput( r["out"] )
		
		c = Gaffer.Context()
		c["image:channelName"] = "R"
		c["image:tileOrigin"] = IECore.V2i( 0 )
		with c:
			cs = GafferTest.CapturingSlot( t.plugDirtiedSignal() )
			t["transform"]["translate"].setValue( IECore.V2f( 2., 2. ) );	
			t["transform"]["rotate"].setValue( 90 );	
			t["enabled"].setValue( True )
			self.assertNotEqual( r["out"].hash(), t["out"].hash() )
		
			t["enabled"].setValue( False )
			self.assertEqual( r["out"].hash(), t["out"].hash() )

	def testBoxFilter( self ) :
		self.__testFilter( "Box" )

	def testBSplineFilter( self ) :
		self.__testFilter( "BSpline" )

	def testBilinearFilter( self ) :
		self.__testFilter( "Bilinear" )

	def testCatmullRomFilter( self ) :
		self.__testFilter( "CatmullRom" )

	def testCubicFilter( self ) :
		self.__testFilter( "Cubic" )

	def testHermiteFilter( self ) :
		self.__testFilter( "Hermite" )

	def testLanczosFilter( self ) :
		self.__testFilter( "Lanczos" )
		
	def testMitchellFilter( self ) :
		self.__testFilter( "Mitchell" )

	def testSincFilter( self ) :
		self.__testFilter( "Sinc" )

	def __testFilter( self, filter ) :
		
		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( os.path.join( self.path, "checkerWithNegativeDataWindow.200x150.exr" ) )

		t = GafferImage.ImageTransform()
		t["transform"]["translate"].setValue( IECore.V2f( 20, -10 ) )
		t["transform"]["scale"].setValue( IECore.V2f( .75, 1.1 ) )
		t["transform"]["rotate"].setValue( 40 )
		t["transform"]["pivot"].setValue( IECore.V2f( 50, 30 ) )
		t["in"].setInput( reader["out"] ) 
		
		expectedOutput = GafferImage.ImageReader()

		file = "transformedChecker" + filter + ".200x150.exr"
		expectedOutput["fileName"].setValue( os.path.join( self.path, file ) )
		t["filter"].setValue( filter )
		
		op = IECore.ImageDiffOp()
		res = op(
			imageA = expectedOutput["out"].image(),
			imageB = t["out"].image()
		)
		
		self.assertFalse( res.value )

if __name__ == "__main__":
	unittest.main()


