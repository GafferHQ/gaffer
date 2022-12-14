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
import random
import threading
import subprocess
import imath

import IECore
import IECoreImage

import Gaffer
import GafferTest
import GafferDispatch
import GafferImage
import GafferImageTest

class DisplayTest( GafferImageTest.ImageTestCase ) :

	# Utility class for sending images to Display nodes.
	# This abstracts away the different image orientations between
	# Gaffer and Cortex. All Driver methods expect data with the
	# usual Gaffer conventions.
	class Driver( object ) :

		def __init__( self, format, dataWindow, channelNames, port, extraParameters = {}  ) :

			self.__format = format

			parameters = {
				"displayHost" : "localHost",
				"displayPort" : str( port ),
				"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
			}
			parameters.update( extraParameters )

			with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as h :

				self.__driver = IECoreImage.ClientDisplayDriver(
					self.__format.toEXRSpace( self.__format.getDisplayWindow() ),
					self.__format.toEXRSpace( dataWindow ),
					list( channelNames ),
					parameters,
				)

				# Expect UI thread call used to emit Display::driverCreatedSignal()
				h.assertCalled()
				h.assertDone()

		# The channelData argument is a list of FloatVectorData
		# per channel.
		def sendBucket( self, bucketWindow, channelData ) :

			bucketSize = bucketWindow.size()
			bucketData = IECore.FloatVectorData()
			for by in range( bucketSize.y - 1, -1, -1 ) :
				for bx in range( 0, bucketSize.x ) :
					i = by * bucketSize.x + bx
					for c in channelData :
						bucketData.append( c[i] )

			with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as h :

				self.__driver.imageData(
					self.__format.toEXRSpace( bucketWindow ),
					bucketData
				)

				# Expect UI thread call used to increment updateCount plug
				h.assertCalled()
				h.assertDone()

		def close( self ) :

			with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as h :
				self.__driver.imageClose()
				# Expect UI thread call used to emit Display::imageReceivedSignal()
				h.assertCalled()
				h.assertDone()

		@classmethod
		def sendImage( cls, image, port, extraParameters = {}, close = True ) :

			dataWindow = image["dataWindow"].getValue()
			channelNames = image["channelNames"].getValue()

			parameters = IECore.CompoundData()
			parameters.update( { "header:" + k : v for k, v in image["metadata"].getValue().items() } )
			parameters.update( extraParameters )

			driver = DisplayTest.Driver(
				image["format"].getValue(),
				dataWindow,
				channelNames,
				port, parameters
			)

			tileSize = GafferImage.ImagePlug.tileSize()
			minTileOrigin = GafferImage.ImagePlug.tileOrigin( dataWindow.min() )
			maxTileOrigin = GafferImage.ImagePlug.tileOrigin( dataWindow.max() - imath.V2i( 1 ) )
			for y in range( minTileOrigin.y, maxTileOrigin.y + 1, tileSize ) :
				for x in range( minTileOrigin.x, maxTileOrigin.x + 1, tileSize ) :
					tileOrigin = imath.V2i( x, y )
					channelData = []
					for channelName in channelNames :
						channelData.append( image.channelData( channelName, tileOrigin ) )
					driver.sendBucket( imath.Box2i( tileOrigin, tileOrigin + imath.V2i( tileSize ) ), channelData )

			if close :
				driver.close()

			return driver

	def testDefaultFormat( self ) :

		d = GafferImage.Display()

		with Gaffer.Context() as c :
			self.assertEqual( d["out"]["format"].getValue(), GafferImage.FormatPlug.getDefaultFormat( c ) )
			GafferImage.FormatPlug.setDefaultFormat( c, GafferImage.Format( 200, 150, 1. ) )
			self.assertEqual( d["out"]["format"].getValue(), GafferImage.FormatPlug.getDefaultFormat( c ) )

	def testDeep( self ) :

		d = GafferImage.Display()
		self.assertEqual( d["out"]["deep"].getValue(), False )

	def testTileHashes( self ) :

		node = GafferImage.Display()
		server = IECoreImage.DisplayDriverServer()
		driverCreatedConnection = GafferImage.Display.driverCreatedSignal().connect( lambda driver, parameters : node.setDriver( driver ), scoped = True )

		dataWindow = imath.Box2i( imath.V2i( -100, -200 ), imath.V2i( 303, 557 ) )
		driver = self.Driver(
			GafferImage.Format( dataWindow ),
			dataWindow,
			[ "Y" ],
			port = server.portNumber(),
		)

		for i in range( 0, 100 ) :

			h1 = self.__tileHashes( node, "Y" )
			t1 = self.__tiles( node, "Y" )

			bucketWindow = imath.Box2i()
			while GafferImage.BufferAlgo.empty( bucketWindow ) :
				bucketWindow.extendBy(
					imath.V2i(
						int( random.uniform( dataWindow.min().x, dataWindow.max().x ) ),
						int( random.uniform( dataWindow.min().y, dataWindow.max().y ) ),
					)
				)

			numPixels = ( bucketWindow.size().x + 1 ) * ( bucketWindow.size().y + 1 )
			bucketData = IECore.FloatVectorData()
			bucketData.resize( numPixels, i + 1 )

			driver.sendBucket( bucketWindow, [ bucketData ] )

			h2 = self.__tileHashes( node, "Y" )
			t2 = self.__tiles( node, "Y" )

			self.__assertTilesChangedInRegion( t1, t2, bucketWindow )
			self.__assertTilesChangedInRegion( h1, h2, bucketWindow )

		driver.close()

	def testTransferChecker( self ) :

		self.__testTransferImage( Gaffer.rootPath() / "python" / "GafferImageTest" / "images" / "checker.exr" )

	def testTransferWithDataWindow( self ) :

		self.__testTransferImage( Gaffer.rootPath() / "python" / "GafferImageTest" / "images" / "checkerWithNegativeDataWindow.200x150.exr" )

	def testAccessOutsideDataWindow( self ) :

		node = self.__testTransferImage( Gaffer.rootPath() / "python" / "GafferImageTest" / "images" / "checker.exr" )

		blackTile = IECore.FloatVectorData( [ 0 ] * GafferImage.ImagePlug.tileSize() * GafferImage.ImagePlug.tileSize() )

		self.assertEqual(
			node["out"].channelData( "R", -imath.V2i( GafferImage.ImagePlug.tileSize() ) ),
			blackTile
		)

		self.assertEqual(
			node["out"].channelData( "R", 10 * imath.V2i( GafferImage.ImagePlug.tileSize() ) ),
			blackTile
		)

	def testNoErrorOnBackgroundDispatch( self ) :

		s = Gaffer.ScriptNode()

		s["d"] = GafferImage.Display()

		s["p"] = GafferDispatch.PythonCommand()
		s["p"]["command"].setValue( "pass" )

		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )
		s.save()

		output = subprocess.check_output(
			[ str( Gaffer.executablePath() ), "execute", self.temporaryDirectory() / "test.gfr", "-nodes", "p" ],
			stderr = subprocess.STDOUT, universal_newlines = True
		)
		self.assertEqual( output, "" )

	def testSetDriver( self ) :

		driversCreated = GafferTest.CapturingSlot( GafferImage.Display.driverCreatedSignal() )

		server = IECoreImage.DisplayDriverServer()
		dataWindow = imath.Box2i( imath.V2i( 0 ), imath.V2i( GafferImage.ImagePlug.tileSize() ) )

		driver = self.Driver(
			GafferImage.Format( dataWindow ),
			dataWindow,
			[ "Y" ],
			port = server.portNumber()
		)

		try:

			self.assertTrue( len( driversCreated ), 1 )

			display = GafferImage.Display()
			self.assertTrue( display.getDriver() is None )

			dirtiedPlugs = GafferTest.CapturingSlot( display.plugDirtiedSignal() )

			display.setDriver( driversCreated[0][0] )
			self.assertTrue( display.getDriver().isSame( driversCreated[0][0] ) )

			# Ensure all the output plugs have been dirtied
			expectedDirty = { "__driverCount", "__channelDataCount", "out" }.union( { c.getName() for c in display["out"].children() } )
			self.assertEqual( expectedDirty, set( e[0].getName() for e in dirtiedPlugs ) )

			del dirtiedPlugs[:]

			driver.sendBucket( dataWindow, [ IECore.FloatVectorData( [ 0.5 ] * dataWindow.size().x * dataWindow.size().y ) ] )

			self.assertEqual( display["out"]["format"].getValue().getDisplayWindow(), dataWindow )
			self.assertEqual( display["out"]["dataWindow"].getValue(), dataWindow )
			self.assertEqual( display["out"]["channelNames"].getValue(), IECore.StringVectorData( [ "Y" ] ) )
			self.assertEqual(
				display["out"].channelData( "Y", imath.V2i( 0 ) ),
				IECore.FloatVectorData( [ 0.5 ] * GafferImage.ImagePlug.tileSize() * GafferImage.ImagePlug.tileSize() )
			)

			# Ensure only channel data has been dirtied
			expectedDirty = { "channelData", "__channelDataCount", "out" }
			self.assertEqual( set( e[0].getName() for e in dirtiedPlugs ), expectedDirty )

			display2 = GafferImage.Display()
			display2.setDriver( display.getDriver(), copy = True )

			self.assertImagesEqual( display["out"], display2["out"] )

			driver.sendBucket( dataWindow, [ IECore.FloatVectorData( [ 1 ] * dataWindow.size().x * dataWindow.size().y ) ] )

			self.assertEqual(
				display["out"].channelData( "Y", imath.V2i( 0 ) ),
				IECore.FloatVectorData( [ 1 ] * GafferImage.ImagePlug.tileSize() * GafferImage.ImagePlug.tileSize() )
			)

			self.assertEqual(
				display2["out"].channelData( "Y", imath.V2i( 0 ) ),
				IECore.FloatVectorData( [ 0.5 ] * GafferImage.ImagePlug.tileSize() * GafferImage.ImagePlug.tileSize() )
			)
		finally:
			driver.close()

	def __testTransferImage( self, fileName ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( os.path.expandvars( fileName ) )

		imagesReceived = GafferTest.CapturingSlot( GafferImage.Display.imageReceivedSignal() )

		node = GafferImage.Display()
		server = IECoreImage.DisplayDriverServer()
		driverCreatedConnection = GafferImage.Display.driverCreatedSignal().connect( lambda driver, parameters : node.setDriver( driver ), scoped = True )

		self.assertEqual( len( imagesReceived ), 0 )

		self.Driver.sendImage( imageReader["out"], port = server.portNumber() )

		self.assertImagesEqual( imageReader["out"], node["out"] )

		self.assertEqual( len( imagesReceived ), 1 )
		self.assertEqual( imagesReceived[0][0], node["out"] )

		return node

	def __tiles( self, node, channelName ) :

		dataWindow = node["out"]["dataWindow"].getValue()

		minTileOrigin = GafferImage.ImagePlug.tileOrigin( dataWindow.min() )
		maxTileOrigin = GafferImage.ImagePlug.tileOrigin( dataWindow.max() )

		tiles = {}
		for y in range( minTileOrigin.y, maxTileOrigin.y, GafferImage.ImagePlug.tileSize() ) :
			for x in range( minTileOrigin.x, maxTileOrigin.x, GafferImage.ImagePlug.tileSize() ) :
				tiles[( x, y )] = node["out"].channelData( channelName, imath.V2i( x, y ) )

		return tiles

	def __tileHashes( self, node, channelName ) :

		dataWindow = node["out"]["dataWindow"].getValue()

		minTileOrigin = GafferImage.ImagePlug.tileOrigin( dataWindow.min() )
		maxTileOrigin = GafferImage.ImagePlug.tileOrigin( dataWindow.max() )

		hashes = {}
		for y in range( minTileOrigin.y, maxTileOrigin.y, GafferImage.ImagePlug.tileSize() ) :
			for x in range( minTileOrigin.x, maxTileOrigin.x, GafferImage.ImagePlug.tileSize() ) :
				hashes[( x, y )] = node["out"].channelDataHash( channelName, imath.V2i( x, y ) )

		return hashes

	def __assertTilesChangedInRegion( self, t1, t2, region ) :

		for tileOriginTuple in t1.keys() :
			tileOrigin = imath.V2i( *tileOriginTuple )
			tileRegion = imath.Box2i( tileOrigin, tileOrigin + imath.V2i( GafferImage.ImagePlug.tileSize() ) )

			if GafferImage.BufferAlgo.intersects( tileRegion, region ) :
				self.assertNotEqual( t1[tileOriginTuple], t2[tileOriginTuple] )
			else :
				self.assertEqual( t1[tileOriginTuple], t2[tileOriginTuple] )

if __name__ == "__main__":
	unittest.main()
