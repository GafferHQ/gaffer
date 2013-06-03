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
		self.assertEqual( len( dirtiedPlugs ), 1 )
		self.assertTrue( "__scaledFormat" in dirtiedPlugs )

	# Check that the hash is the same for all integer translations.
	# As the ImagePlug::image() method renders the data window of the plug with tiles
	# that have an origin relative to the data window, we can assume that the data
	# in a tile with origin (0,0) that has a data window origin of (0,0) is the same as
	# the same tile translated to (1, 1) if the data window is also (1, 1).
	# Therefore, a translation of 1.5 and 4.5 should produce the same channel data
	# but with a translated data window. As a result, the channel data hashes should also be the same.
	# We test this by comparing the results of several translations that have identical floating point
	# parts but different integer parts. As the ImagePlug::image() method renders the
	# data window of the plug with tiles that have an origin relative to the data window, we can assume
	# that the data in a tile with origin (0,0) that has a data window origin of (0,0) is the same as
	# the same tile translated to (1, 1) if the data window is also (1,1).
	def testTranslateHash( self ) :	

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.fileName )		

		t = GafferImage.ImageTransform()
		t["in"].setInput( r["out"] )
		
		tileSize = GafferImage.ImagePlug.tileSize()
		v1 = IECore.V2f( 1.5, 0.0 )
		v2 = IECore.V2f( 4.5, 0.0 )
		for i in range( 0, 30 ) :
			t["transform"]["translate"].setValue( v1 + IECore.V2f( i ) )
			h1 = t["out"].channelDataHash( "R", t["out"]["dataWindow"].getValue().min )
			t["transform"]["translate"].setValue( v2 + IECore.V2f( i ) )
			h2 = t["out"].channelDataHash( "R", t["out"]["dataWindow"].getValue().min )
			self.assertEqual( h1, h2 )

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

if __name__ == "__main__":
	unittest.main()


