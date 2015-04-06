##########################################################################
#
#  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

import IECore

import GafferTest
import GafferImage

class MergeTest( GafferTest.TestCase ) :

	rPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/redWithDataWindow.100x100.exr" )
	gPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/greenWithDataWindow.100x100.exr" )
	bPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/blueWithDataWindow.100x100.exr" )
	checkerPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/checkerboard.100x100.exr" )
	checkerRGBPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/rgbOverChecker.100x100.exr" )
	rgbPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/rgb.100x100.exr" )

	# Do several tests to check the cache is working correctly:
	def testHashes( self ) :

		r1 = GafferImage.ImageReader()
		r1["fileName"].setValue( self.checkerPath )

		r2 = GafferImage.ImageReader()
		r2["fileName"].setValue( self.gPath )

		##########################################
		# Test to see if the hash changes.
		##########################################
		merge = GafferImage.Merge()
		merge["operation"].setValue( GafferImage.Merge.Operation.Over )

		merge["in"].setInput(r1["out"])
		merge["in1"].setInput(r2["out"])
		h1 = merge["out"].image().hash()

		# Switch the inputs.
		merge["in1"].setInput(r1["out"])
		merge["in"].setInput(r2["out"])
		h2 = merge["out"].image().hash()

		self.assertNotEqual( h1, h2 )

		##########################################
		# Test to see if the hash remains the same
		# when the output should be the same but the
		# input plugs used are not.
		##########################################
		merge = GafferImage.Merge()
		merge["operation"].setValue( GafferImage.Merge.Operation.Over )

		expectedHash = h1

		# Connect up a load of inputs ...
		merge["in"].setInput(r1["out"])
		merge["in1"].setInput(r1["out"])
		merge["in2"].setInput(r1["out"])
		merge["in3"].setInput(r2["out"])

		# but then disconnect two so that the result should still be the same...
		merge["in1"].setInput( None )
		merge["in2"].setInput( None )
		h1 = merge["out"].image().hash()

		self.assertEqual( h1, expectedHash )

	def testHashPassThrough( self ) :

		r1 = GafferImage.ImageReader()
		r1["fileName"].setValue( self.checkerPath )

		##########################################
		# Test to see if the input has is always passed
		# through if only the first input is connected.
		##########################################
		merge = GafferImage.Merge()
		merge["operation"].setValue( GafferImage.Merge.Operation.Over )

		expectedHash = r1["out"].image().hash()
		merge["in"].setInput(r1["out"])
		h1 = merge["out"].image().hash()

		self.assertEqual( h1, expectedHash )

		##########################################
		# Test that if we disable the node the hash gets passed through.
		##########################################
		merge["enabled"].setValue(False)
		h1 = merge["out"].image().hash()

		self.assertEqual( h1, expectedHash )


	# Overlay a red, green and blue tile of different data window sizes and check the data window is expanded on the result and looks as we expect.
	def testOverRGBA( self ) :
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.rPath )

		g = GafferImage.ImageReader()
		g["fileName"].setValue( self.gPath )

		b = GafferImage.ImageReader()
		b["fileName"].setValue( self.bPath )

		merge = GafferImage.Merge()
		merge["operation"].setValue( GafferImage.Merge.Operation.Over )
		merge["in"].setInput(r["out"])
		merge["in1"].setInput(g["out"])
		merge["in2"].setInput(b["out"])

		mergeResult = merge["out"].image()
		expected = IECore.Reader.create( self.rgbPath ).read()

		self.assertTrue( not IECore.ImageDiffOp()( imageA = expected, imageB = mergeResult, skipMissingChannels = False, maxError = 0.001 ).value )

	# Overlay a red, green and blue tile of different data window sizes and check the data window is expanded on the result and looks as we expect.
	def testOverRGBAonRGB( self ) :

		c = GafferImage.ImageReader()
		c["fileName"].setValue( self.checkerPath )

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.rPath )

		g = GafferImage.ImageReader()
		g["fileName"].setValue( self.gPath )

		b = GafferImage.ImageReader()
		b["fileName"].setValue( self.bPath )

		merge = GafferImage.Merge()
		merge["operation"].setValue( GafferImage.Merge.Operation.Over )
		merge["in"].setInput(c["out"])
		merge["in1"].setInput(r["out"])
		merge["in2"].setInput(g["out"])
		merge["in3"].setInput(b["out"])

		mergeResult = merge["out"].image()
		expected = IECore.Reader.create( self.checkerRGBPath ).read()

		self.assertTrue( not IECore.ImageDiffOp()( imageA = expected, imageB = mergeResult, skipMissingChannels = False, maxError = 0.001 ).value )

	def testAffects( self ) :

		c1 = GafferImage.Constant()
		c2 = GafferImage.Constant()

		m = GafferImage.Merge()
		m["in"].setInput( c1["out"] )
		m["in1"].setInput( c2["out"] )

		cs = GafferTest.CapturingSlot( m.plugDirtiedSignal() )

		c1["color"]["r"].setValue( 0.1 )

		self.assertEqual( len( cs ), 4 )
		self.assertTrue( cs[0][0].isSame( m["in"]["channelData"] ) )
		self.assertTrue( cs[1][0].isSame( m["in"] ) )
		self.assertTrue( cs[2][0].isSame( m["out"]["channelData"] ) )
		self.assertTrue( cs[3][0].isSame( m["out"] ) )

		del cs[:]

		c2["color"]["g"].setValue( 0.2 )

		self.assertEqual( len( cs ), 4 )
		self.assertTrue( cs[0][0].isSame( m["in1"]["channelData"] ) )
		self.assertTrue( cs[1][0].isSame( m["in1"] ) )
		self.assertTrue( cs[2][0].isSame( m["out"]["channelData"] ) )
		self.assertTrue( cs[3][0].isSame( m["out"] ) )

	def testEnabledAffects( self ) :

		m = GafferImage.Merge()

		affected = m.affects( m["enabled"] )
		self.assertTrue( m["out"]["channelData"] in affected )

	def testPassThrough( self ) :

		c = GafferImage.Constant()
		f = GafferImage.Reformat()
		f["in"].setInput( c["out"] )
		f["format"].setValue( GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 10 ) ), 1 ) )
		d = GafferImage.ImageMetadata()
		d["metadata"].addMember( "comment", IECore.StringData( "reformated and metadata updated" ) )
		d["in"].setInput( f["out"] )
		
		m = GafferImage.Merge()
		m["in"].setInput( c["out"] )
		m["in1"].setInput( d["out"] )

		self.assertEqual( m["out"]["format"].hash(), c["out"]["format"].hash() )
		self.assertEqual( m["out"]["metadata"].hash(), c["out"]["metadata"].hash() )
		
		self.assertEqual( m["out"]["format"].getValue(), c["out"]["format"].getValue() )
		self.assertEqual( m["out"]["metadata"].getValue(), c["out"]["metadata"].getValue() )
		
		m["in"].setInput( d["out"] )
		m["in1"].setInput( c["out"] )
		
		self.assertEqual( m["out"]["format"].hash(), d["out"]["format"].hash() )
		self.assertEqual( m["out"]["metadata"].hash(), d["out"]["metadata"].hash() )
		
		self.assertEqual( m["out"]["format"].getValue(), d["out"]["format"].getValue() )
		self.assertEqual( m["out"]["metadata"].getValue(), d["out"]["metadata"].getValue() )

if __name__ == "__main__":
	unittest.main()
