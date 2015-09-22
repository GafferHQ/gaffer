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

import inspect
import unittest
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ImageSwitchTest( GafferImageTest.ImageTestCase ) :

	def testEnabledPlug( self ) :

		s = Gaffer.Switch()
		s.setup( GafferImage.ImagePlug() )
		self.assertTrue( isinstance( s["enabled"], Gaffer.BoolPlug ) )
		self.assertTrue( s["enabled"].isSame( s.enabledPlug() ) )
		self.assertFalse( "enabled1" in s )

	def testAffects( self ) :

		in0 = GafferImage.Constant()
		in1 = GafferImage.Constant()

		switch = Gaffer.Switch()
		switch.setup( GafferImage.ImagePlug() )
		switch["in"][0].setInput( in0["out"] )
		switch["in"][1].setInput( in1["out"] )

		add = GafferTest.AddNode()
		switch["index"].setInput( add["sum"] )

		for p in [ switch["in"][0], switch["in"][1] ] :
			for n in [ "format", "dataWindow", "metadata", "deep", "sampleOffsets", "channelNames", "channelData" ] :
				a = switch.affects( p[n] )
				self.assertEqual( len( a ), 1 )
				self.assertTrue( a[0].isSame( switch["out"][n] ) )

		a = set( [ plug.relativeName( plug.node() ) for plug in switch.affects( switch["enabled"] ) ] )
		self.assertEqual(
			a,
			set( [
				"out.format", "out.dataWindow", "out.metadata", "out.deep", "out.sampleOffsets", "out.channelNames", "out.channelData",
			] ),
		)

		a = set( [ plug.relativeName( plug.node() ) for plug in switch.affects( switch["index"] ) ] )
		self.assertEqual(
			a,
			set( [
				"out.format", "out.dataWindow", "out.metadata", "out.deep", "out.sampleOffsets", "out.channelNames", "out.channelData",
			] ),
		)

	def testSwitching( self ) :

		in0 = GafferImage.Constant()
		in0["format"].setValue( GafferImage.Format( 100, 100, 1.0 ) )
		in0["color"].setValue( imath.Color4f( 1, 0, 0, 1 ) )
		in1 = GafferImage.Constant()
		in1["format"].setValue( GafferImage.Format( 100, 100, 1.0 ) )
		in0["color"].setValue( imath.Color4f( 0, 1, 0, 1 ) )

		switch = Gaffer.Switch()
		switch.setup( GafferImage.ImagePlug() )
		switch["in"][0].setInput( in0["out"] )
		switch["in"][1].setInput( in1["out"] )

		self.assertImageHashesEqual( switch["out"], in0["out"] )
		self.assertImagesEqual( switch["out"], in0["out"] )

		switch["index"].setValue( 1 )

		self.assertImageHashesEqual( switch["out"], in1["out"] )
		self.assertImagesEqual( switch["out"], in1["out"] )

		switch["enabled"].setValue( False )

		self.assertImageHashesEqual( switch["out"], in0["out"] )
		self.assertImagesEqual( switch["out"], in0["out"] )

	def testSerialisation( self ) :

		script = Gaffer.ScriptNode()

		script["switch"] = Gaffer.Switch()
		script["switch"].setup( GafferImage.ImagePlug() )
		script["in0"] = GafferImage.Constant()
		script["in1"] = GafferImage.Constant()

		script["switch"]["in"][0].setInput( script["in0"]["out"] )
		script["switch"]["in"][1].setInput( script["in1"]["out"] )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		self.assertTrue( script2["switch"]["in"][0].getInput().isSame( script2["in0"]["out"] ) )
		self.assertTrue( script2["switch"]["in"][1].getInput().isSame( script2["in1"]["out"] ) )
		self.assertTrue( script2["switch"]["in"][2].getInput() is None )

	def testTileNotAvailableInContextExpressions( self ) :

		# We don't want expressions on the index to be sensitive
		# to the image:tileOrigin or image:channelName context entries,
		# because then an invalid image could result from splicing together
		# different images, even requesting tiles outside the data window.

		script = Gaffer.ScriptNode()

		script["switch"] = Gaffer.Switch()
		script["switch"].setup( GafferImage.ImagePlug() )
		script["in0"] = GafferImage.Constant()
		script["in0"]["color"].setValue( imath.Color4f( 1, 1, 1, 1 ) )
		script["in1"] = GafferImage.Constant()
		script["in0"]["color"].setValue( imath.Color4f( 0, 0, 0, 0 ) )

		script["switch"]["in"][0].setInput( script["in0"]["out"] )
		script["switch"]["in"][1].setInput( script["in1"]["out"] )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			assert( context.get( "image:channelName", None ) is None )
			assert( context.get( "image:tileOrigin", None ) is None )
			parent["switch"]["index"] = 1
			"""
		) )

		self.assertEqual( script["switch"]["out"].channelData( "R", imath.V2i( 0 ) )[0], 0 )

if __name__ == "__main__":
	unittest.main()
