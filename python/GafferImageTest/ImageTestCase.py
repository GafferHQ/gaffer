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

import imath

import IECore
import IECoreImage

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ImageTestCase( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		sanitiser = GafferImageTest.ContextSanitiser()
		sanitiser.__enter__()
		self.addCleanup( sanitiser.__exit__, None, None, None )

	def assertImageHashesEqual( self, imageA, imageB ) :

		self.assertEqual( imageA.viewNamesHash(), imageB.viewNamesHash() )

		for view in imageA.viewNames():

			with Gaffer.Context( Gaffer.Context.current() ) as context :
				context["image:viewName"] = view

				self.assertEqual( imageA["format"].hash(), imageB["format"].hash() )
				self.assertEqual( imageA["dataWindow"].hash(), imageB["dataWindow"].hash() )
				self.assertEqual( imageA["metadata"].hash(), imageB["metadata"].hash() )
				self.assertEqual( imageA["channelNames"].hash(), imageB["channelNames"].hash() )

				dataWindow = imageA["dataWindow"].getValue()
				self.assertEqual( dataWindow, imageB["dataWindow"].getValue() )

				channelNames = imageA["channelNames"].getValue()
				self.assertEqual( channelNames, imageB["channelNames"].getValue() )

				tileOrigin = GafferImage.ImagePlug.tileOrigin( dataWindow.min() )
				while tileOrigin.y < dataWindow.max().y :
					tileOrigin.x = GafferImage.ImagePlug.tileOrigin( dataWindow.min() ).x
					while tileOrigin.x < dataWindow.max().x :
						for channelName in channelNames :
							self.assertEqual(
								imageA.channelDataHash( channelName, tileOrigin ),
								imageB.channelDataHash( channelName, tileOrigin )
							)
						tileOrigin.x += GafferImage.ImagePlug.tileSize()
					tileOrigin.y += GafferImage.ImagePlug.tileSize()

	def assertImagesEqual( self, imageA, imageB, maxDifference = 0.0, ignoreMetadata = False, ignoreDataWindow = False, ignoreChannelNamesOrder = False, ignoreViewNamesOrder = False, metadataBlacklist = [] ) :

		self.longMessage = True

		if not ignoreViewNamesOrder :
			self.assertEqual( list( imageA.viewNames() ), list( imageB.viewNames() ) )
		else :
			self.assertEqual( set( imageA.viewNames() ), set( imageB.viewNames() ) )

		for view in imageA.viewNames():

			with Gaffer.Context( Gaffer.Context.current() ) as context :
				context["image:viewName"] = view

				self.assertEqual( imageA["format"].getValue(), imageB["format"].getValue() )
				dataWindowA = imageA["dataWindow"].getValue()
				dataWindowB = imageB["dataWindow"].getValue()
				if not ignoreDataWindow :
					self.assertEqual( dataWindowA, dataWindowB )
				if not ignoreMetadata :
					# Converting to dict allows us to remove some items, and also gives a more informative
					# exception if they don't match, since assertEqual has a special case for dicts
					metaA = dict( imageA["metadata"].getValue() )
					metaB = dict( imageB["metadata"].getValue() )
					for i in metadataBlacklist:
						metaA.pop( i, None )
						metaB.pop( i, None )

					self.assertEqual( metaA, metaB )

				if not ignoreChannelNamesOrder :
					self.assertEqual( list( imageA["channelNames"].getValue() ), list( imageB["channelNames"].getValue() ) )
				else :
					self.assertEqual( set( imageA["channelNames"].getValue() ), set( imageB["channelNames"].getValue() ) )

				deep = imageA["deep"].getValue()
				self.assertEqual( deep, imageB["deep"].getValue() )

				if not deep:

					difference = GafferImage.Merge()
					difference["in"][0].setInput( imageA )
					difference["in"][1].setInput( imageB )
					difference["operation"].setValue( GafferImage.Merge.Operation.Difference )

					unionDataWindow = imath.Box2i( dataWindowA )
					unionDataWindow.extendBy( dataWindowB )
					stats = GafferImage.ImageStats()
					stats["view"].setValue( view )
					stats["in"].setInput( difference["out"] )
					stats["area"].setValue( unionDataWindow )

					for channelName in imageA["channelNames"].getValue() :

						stats["channels"].setValue( IECore.StringVectorData( [ channelName ] * 4 ) )
						self.assertLessEqual( stats["max"]["r"].getValue(), maxDifference, "Channel {0}".format( channelName ) )
					# Access the tiles, because this will throw an error if the sample offsets are bogus
					GafferImage.ImageAlgo.tiles( imageA )
					GafferImage.ImageAlgo.tiles( imageB )
				else:
					pixelDataA = GafferImage.ImageAlgo.tiles( imageA )
					pixelDataB = GafferImage.ImageAlgo.tiles( imageB )
					if pixelDataA != pixelDataB:
						self.assertEqual( pixelDataA.keys(), pixelDataB.keys() )
						self.assertEqual( pixelDataA["tileOrigins"], pixelDataB["tileOrigins"] )
						for k in pixelDataA.keys():
							if k == "tileOrigins":
								continue
							for i in range( len( pixelDataA[k] ) ):
								if pixelDataA[k][i] != pixelDataB[k][i]:
									tileStr = str( pixelDataA["tileOrigins"][i] )
									self.assertEqual( len( pixelDataA[k][i] ), len( pixelDataB[k][i] ), " while checking pixel data %s : %s" % ( k, tileStr ) )
									for j in range( len( pixelDataA[k][i] ) ):
										self.assertEqual( pixelDataA[k][i][j], pixelDataB[k][i][j] , " while checking pixel data %s : %s at index %i" % ( k, tileStr, j ) )

	## Returns an image node with an empty data window. This is useful in
	# verifying that nodes deal correctly with such inputs.
	def emptyImage( self ) :

		emptyCrop = GafferImage.Crop( "Crop" )
		emptyCrop["Constant"] = GafferImage.Constant()
		emptyCrop["Constant"]["format"].setValue( GafferImage.Format( 100, 100, 1.000 ) )
		emptyCrop["in"].setInput( emptyCrop["Constant"]["out"] )
		emptyCrop["area"].setValue( imath.Box2i() )
		emptyCrop["affectDisplayWindow"].setValue( False )

		self.assertEqual( emptyCrop["out"]["dataWindow"].getValue(), imath.Box2i() )

		return emptyCrop

	def deepImage( self ):
		return self.DeepImage()

	## Returns an image node with a set of channels that is good for testing read/write
	def channelTestImage( self ) :

		channelTestImage = GafferImage.CollectImages()
		channelTestImage["Constant"] = GafferImage.Constant()
		channelTestImage["Constant"]["format"].setValue( GafferImage.Format( 16, 16, 1.000 ) )
		channelTestImage["Constant"]["Expression"] = Gaffer.Expression()
		channelTestImage["Constant"]["Expression"].setExpression( """
import imath
parent["color"] = imath.Color4f( 0.5, 0.6, 0.7, 0.8 ) if context.get( "collect:layerName", "" ) != "" else imath.Color4f( 0.1, 0.2, 0.3, 0.4 )
""" )

		channelTestImage["Shuffle"] = GafferImage.Shuffle()
		channelTestImage["Shuffle"]["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "Z", "R" ) )
		channelTestImage["Shuffle"]["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "ZBack", "G" ) )
		channelTestImage["Shuffle"]["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "custom", "A" ) )
		channelTestImage["Shuffle"]["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "mask", "B" ) )
		channelTestImage["Shuffle"]["in"].setInput( channelTestImage["Constant"]["out"] )

		channelTestImage["in"].setInput( channelTestImage["Shuffle"]["out"] )
		channelTestImage["rootLayers"].setValue( IECore.StringVectorData( [ '', 'character' ] ) )

		return channelTestImage

	## Convert the test image to a stereo test
	def channelTestImageMultiView( self ) :

		channelTestImageMultiView = GafferImage.CreateViews()
		channelTestImageMultiView["views"].addChild( Gaffer.NameValuePlug( "left", GafferImage.ImagePlug(), True, "view0", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		channelTestImageMultiView["views"].addChild( Gaffer.NameValuePlug( "right", GafferImage.ImagePlug(), True, "view1", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		channelTestImageMultiView["TestImage"] = self.channelTestImage()

		channelTestImageMultiView["DeleteChannels"] = GafferImage.DeleteChannels()
		channelTestImageMultiView["DeleteChannels"]["in"].setInput( channelTestImageMultiView["TestImage"]["out"] )
		channelTestImageMultiView["DeleteChannels"]["channels"].setValue( 'custom character.custom' )

		channelTestImageMultiView["ImageTransform"] = GafferImage.ImageTransform()
		channelTestImageMultiView["ImageTransform"]["in"].setInput( channelTestImageMultiView["TestImage"]["out"] )
		channelTestImageMultiView["ImageTransform"]["transform"]["translate"]["x"].setValue( -10 )

		channelTestImageMultiView["views"][0]["value"].setInput( channelTestImageMultiView["DeleteChannels"]["out"] )
		channelTestImageMultiView["views"][1]["value"].setInput( channelTestImageMultiView["ImageTransform"]["out"] )

		return channelTestImageMultiView

	def assertRaisesDeepNotSupported( self, node ) :

		flat = GafferImage.Constant()
		node["in"].setInput( flat["out"] )

		self.assertNotEqual( GafferImage.ImageAlgo.imageHash( flat["out"] ), GafferImage.ImageAlgo.imageHash( node["out"] ) )

		deep = GafferImage.Empty()
		node["in"].setInput( deep["out"] )
		self.assertRaisesRegex( RuntimeError, 'Deep data not supported in input "in*', GafferImage.ImageAlgo.image, node["out"] )
