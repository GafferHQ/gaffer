##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferTest
import GafferImage

class ImageTestCase( GafferTest.TestCase ) :

	class DeepImage( GafferImage.ImageNode ) :
		def __init__( self, name = "DeepImage" ) :
			GafferImage.ImageNode.__init__( self, name )
			self.addChild( Gaffer.IntPlug( "deepState", Gaffer.Plug.Direction.In, GafferImage.ImagePlug.DeepState.Messy ) )
			self.addChild( GafferImage.FormatPlug( "format", Gaffer.Plug.Direction.In ) )

			self["__empty"] = GafferImage.Empty()
			self["__empty"]["format"].setInput( self["format"] )

			self["__imageState"] = GafferImage.ImageState()
			self["__imageState"]["in"].setInput( self["__empty"]["out"] )
			self["__imageState"]["deepState"].setInput( self["deepState"] )

			self["out"].setInput( self["__imageState"]["out"] )

	IECore.registerRunTimeTyped( DeepImage )

	def assertImageHashesEqual( self, imageA, imageB ) :

		self.assertEqual( imageA["format"].hash(), imageB["format"].hash() )
		self.assertEqual( imageA["dataWindow"].hash(), imageB["dataWindow"].hash() )
		self.assertEqual( imageA["metadata"].hash(), imageB["metadata"].hash() )
		self.assertEqual( imageA["channelNames"].hash(), imageB["channelNames"].hash() )

		dataWindow = imageA["dataWindow"].getValue()
		self.assertEqual( dataWindow, imageB["dataWindow"].getValue() )

		channelNames = imageA["channelNames"].getValue()
		self.assertEqual( channelNames, imageB["channelNames"].getValue() )

		tileOrigin = GafferImage.ImagePlug.tileOrigin( dataWindow.min )
		while tileOrigin.y < dataWindow.max.y :
			tileOrigin.x = GafferImage.ImagePlug.tileOrigin( dataWindow.min ).x
			while tileOrigin.x < dataWindow.max.x :
				for channelName in channelNames :
					self.assertEqual(
						imageA.channelDataHash( channelName, tileOrigin ),
						imageB.channelDataHash( channelName, tileOrigin )
					)
				tileOrigin.x += GafferImage.ImagePlug.tileSize()
			tileOrigin.y += GafferImage.ImagePlug.tileSize()

	def assertImagesEqual( self, imageA, imageB, maxDifference = 0.0, ignoreMetadata = False, ignoreDataWindow = False ) :

		self.assertEqual( imageA["format"].getValue(), imageB["format"].getValue() )
		if not ignoreDataWindow :
			self.assertEqual( imageA["dataWindow"].getValue(), imageB["dataWindow"].getValue() )
		if not ignoreMetadata :
			self.assertEqual( imageA["metadata"].getValue(), imageB["metadata"].getValue() )
		self.assertEqual( imageA["channelNames"].getValue(), imageB["channelNames"].getValue() )

		for channelName in imageA["channelNames"].getValue() :
			## \todo Lift this restriction
			self.assertTrue( channelName in "RGBA" )

		difference = GafferImage.Merge()
		difference["in"][0].setInput( imageA )
		difference["in"][1].setInput( imageB )
		difference["operation"].setValue( GafferImage.Merge.Operation.Difference )

		stats = GafferImage.ImageStats()
		stats["in"].setInput( difference["out"] )
		stats["regionOfInterest"].setValue( imageA["format"].getValue().getDisplayWindow() )
		stats["channels"].setValue( IECore.StringVectorData( [ "R", "G", "B", "A" ] ) )

		if "R" in imageA["channelNames"].getValue() :
			self.assertLessEqual( stats["max"]["r"].getValue(), maxDifference )

		if "G" in imageA["channelNames"].getValue() :
			self.assertLessEqual( stats["max"]["g"].getValue(), maxDifference )

		if "B" in imageA["channelNames"].getValue() :
			self.assertLessEqual( stats["max"]["b"].getValue(), maxDifference )

		if "A" in imageA["channelNames"].getValue() :
			self.assertLessEqual( stats["max"]["a"].getValue(), maxDifference )

	## Returns an image node with an empty data window. This is useful in
	# verifying that nodes deal correctly with such inputs.
	def emptyImage( self ) :

		image = IECore.ImagePrimitive( IECore.Box2i(), IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 100 ) ) )
		image["R"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Varying, IECore.FloatVectorData() )
		image["G"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Varying, IECore.FloatVectorData() )
		image["B"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Varying, IECore.FloatVectorData() )
		image["A"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Varying, IECore.FloatVectorData() )

		result = GafferImage.ObjectToImage()
		result["object"].setValue( image )

		self.assertEqual( result["out"]["dataWindow"].getValue(), IECore.Box2i() )

		return result

	def deepImage( self, fmt=None ) :

		deep = self.DeepImage()
		if fmt :
			deep["format"].setValue( fmt )

		return deep

	def _testNonFlatHashPassThrough( self, node ) :

		deep = self.deepImage()

		node["in"].setInput( deep["out"] )

		self.assertEqual( deep["out"].imageHash(), node["out"].imageHash() )
		deep["deepState"].setValue( GafferImage.ImagePlug.DeepState.Flat )
		self.assertNotEqual( deep["out"].imageHash(), node["out"].imageHash() )
