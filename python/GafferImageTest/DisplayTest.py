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
import subprocess32 as subprocess

import IECore

import Gaffer
import GafferTest
import GafferDispatch
import GafferImage
import GafferImageTest

class DisplayTest( GafferImageTest.ImageTestCase ) :

	# Utility class for sending images to Display nodes.
	# This does a couple of important things :
	#
	# - Abstracts away the different image orientations between
	#   Gaffer and Cortex. All Driver methods expect data with the
	#   usual Gaffer conventions.
	# - Emulates the DisplayUI's connection to Display.executeOnUIThreadSignal().
	class Driver( object ) :

		def __init__( self, format, dataWindow, channelNames, port, extraParameters = {}  ) :

			self.__executeOnUIThreadConnection = GafferImage.Display.executeOnUIThreadSignal().connect( Gaffer.WeakMethod( self.__executeOnUIThread ) )
			self.__executeOnUIThreadCondition = threading.Condition()
			self.__executeOnUIThreadCondition.toExecute = None

			self.__format = format

			parameters = {
				"displayHost" : "localHost",
				"displayPort" : str( port ),
				"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
			}
			parameters.update( extraParameters )

			self.__driver = IECore.ClientDisplayDriver(
				self.__format.toEXRSpace( self.__format.getDisplayWindow() ),
				self.__format.toEXRSpace( dataWindow ),
				list( channelNames ),
				parameters,
			)

			# Wait for UI thread execution used to emit Display::driverCreatedSignal()
			self.performExpectedUIThreadExecution()

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

			self.__driver.imageData(
				self.__format.toEXRSpace( bucketWindow ),
				bucketData
			)

			# Wait for UI thread execution used to increment updateCount plug
			self.performExpectedUIThreadExecution()

		def close( self ) :

			self.__driver.imageClose()

			# Wait for UI thread execution used to emit Display::imageReceivedSignal()
			self.performExpectedUIThreadExecution()

		def performExpectedUIThreadExecution( self ) :

			with self.__executeOnUIThreadCondition :

				while self.__executeOnUIThreadCondition.toExecute is None :
					self.__executeOnUIThreadCondition.wait()

				self.__executeOnUIThreadCondition.toExecute()
				self.__executeOnUIThreadCondition.toExecute = None

		@classmethod
		def sendImage( cls, image, port, extraParameters = {} ) :

			dataWindow = image["dataWindow"].getValue()
			channelNames = image["channelNames"].getValue()

			driver = DisplayTest.Driver(
				image["format"].getValue(),
				dataWindow,
				channelNames,
				port, extraParameters
			)

			tileSize = GafferImage.ImagePlug.tileSize()
			minTileOrigin = GafferImage.ImagePlug.tileOrigin( dataWindow.min )
			maxTileOrigin = GafferImage.ImagePlug.tileOrigin( dataWindow.max - IECore.V2i( 1 ) )
			for y in range( minTileOrigin.y, maxTileOrigin.y + 1, tileSize ) :
				for x in range( minTileOrigin.x, maxTileOrigin.x + 1, tileSize ) :
					tileOrigin = IECore.V2i( x, y )
					channelData = []
					for channelName in channelNames :
						channelData.append( image.channelData( channelName, tileOrigin ) )
					driver.sendBucket( IECore.Box2i( tileOrigin, tileOrigin + IECore.V2i( tileSize ) ), channelData )

			driver.close()

			return driver

		def __executeOnUIThread( self, f ) :

			with self.__executeOnUIThreadCondition :

				self.__executeOnUIThreadCondition.toExecute = f
				self.__executeOnUIThreadCondition.notify()

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		# We just make this connection to force the display nodes to create servers,
		# because if no connections exist they assume they're in a batch render and do
		# nothing. The real UI thread execution is performed in the Driver class.
		## \todo We can remove this when we remove all the server management from
		# the Display node.
		self.__executeOnUIThreadConnection = GafferImage.Display.executeOnUIThreadSignal().connect( lambda f : None )

	def tearDown( self ) :

		self.__executeOnUIThreadConnection.disconnect()

	def testDefaultFormat( self ) :

		d = GafferImage.Display()

		with Gaffer.Context() as c :
			self.assertEqual( d["out"]["format"].getValue(), GafferImage.FormatPlug.getDefaultFormat( c ) )
			GafferImage.FormatPlug.setDefaultFormat( c, GafferImage.Format( 200, 150, 1. ) )
			self.assertEqual( d["out"]["format"].getValue(), GafferImage.FormatPlug.getDefaultFormat( c ) )

	def testTileHashes( self ) :

		node = GafferImage.Display()
		node["port"].setValue( 2500 )

		dataWindow = IECore.Box2i( IECore.V2i( -100, -200 ), IECore.V2i( 303, 557 ) )
		driver = self.Driver(
			GafferImage.Format( dataWindow ),
			dataWindow,
			[ "Y" ],
			port = 2500,
		)

		for i in range( 0, 1000 ) :

			h1 = self.__tileHashes( node, "Y" )
			t1 = self.__tiles( node, "Y" )

			bucketWindow = IECore.Box2i()
			while GafferImage.BufferAlgo.empty( bucketWindow ) :
				bucketWindow.extendBy(
					IECore.V2i(
						int( random.uniform( dataWindow.min.x, dataWindow.max.x ) ),
						int( random.uniform( dataWindow.min.y, dataWindow.max.y ) ),
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

		self.__testTransferImage( "$GAFFER_ROOT/python/GafferImageTest/images/checker.exr" )

	def testTransferWithDataWindow( self ) :

		self.__testTransferImage( "$GAFFER_ROOT/python/GafferImageTest/images/checkerWithNegativeDataWindow.200x150.exr" )

	def testAccessOutsideDataWindow( self ) :

		node = self.__testTransferImage( "$GAFFER_ROOT/python/GafferImageTest/images/checker.exr" )

		blackTile = IECore.FloatVectorData( [ 0 ] * GafferImage.ImagePlug.tileSize() * GafferImage.ImagePlug.tileSize() )

		self.assertEqual(
			node["out"].channelData( "R", -IECore.V2i( GafferImage.ImagePlug.tileSize() ) ),
			blackTile
		)

		self.assertEqual(
			node["out"].channelData( "R", 10 * IECore.V2i( GafferImage.ImagePlug.tileSize() ) ),
			blackTile
		)

	def testNoErrorOnBackgroundDispatch( self ) :

		s = Gaffer.ScriptNode()

		s["d"] = GafferImage.Display()
		s["d"]["port"].setValue( 2500 )

		s["p"] = GafferDispatch.PythonCommand()
		s["p"]["command"].setValue( "pass" )

		s["fileName"].setValue( self.temporaryDirectory() + "test.gfr" )
		s.save()

		output = subprocess.check_output( [ "gaffer", "execute", self.temporaryDirectory() + "test.gfr", "-nodes", "p" ], stderr = subprocess.STDOUT )
		self.assertEqual( output, "" )

	def testSetDriver( self ) :

		driversCreated = GafferTest.CapturingSlot( GafferImage.Display.driverCreatedSignal() )

		server = IECore.DisplayDriverServer()
		dataWindow = IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 100 ) )

		driver = self.Driver(
			GafferImage.Format( dataWindow ),
			dataWindow,
			[ "Y" ],
			port = server.portNumber()
		)

		self.assertTrue( len( driversCreated ), 1 )

		display = GafferImage.Display()
		self.assertTrue( display.getDriver() is None )

		display.setDriver( driversCreated[0][0] )
		self.assertTrue( display.getDriver().isSame( driversCreated[0][0] ) )

		driver.sendBucket( dataWindow, [ IECore.FloatVectorData( [ 0.5 ] * dataWindow.size().x * dataWindow.size().y ) ] )

		self.assertEqual( display["out"]["format"].getValue().getDisplayWindow(), dataWindow )
		self.assertEqual( display["out"]["dataWindow"].getValue(), dataWindow )
		self.assertEqual( display["out"]["channelNames"].getValue(), IECore.StringVectorData( [ "Y" ] ) )
		self.assertEqual(
			display["out"].channelData( "Y", IECore.V2i( 0 ) ),
			IECore.FloatVectorData( [ 0.5 ] * GafferImage.ImagePlug.tileSize() * GafferImage.ImagePlug.tileSize() )
		)

		display2 = GafferImage.Display()
		display2.setDriver( display.getDriver(), copy = True )

		self.assertImagesEqual( display["out"], display2["out"] )

		driver.sendBucket( dataWindow, [ IECore.FloatVectorData( [ 1 ] * dataWindow.size().x * dataWindow.size().y ) ] )

		self.assertEqual(
			display["out"].channelData( "Y", IECore.V2i( 0 ) ),
			IECore.FloatVectorData( [ 1 ] * GafferImage.ImagePlug.tileSize() * GafferImage.ImagePlug.tileSize() )
		)

		self.assertEqual(
			display2["out"].channelData( "Y", IECore.V2i( 0 ) ),
			IECore.FloatVectorData( [ 0.5 ] * GafferImage.ImagePlug.tileSize() * GafferImage.ImagePlug.tileSize() )
		)

		driver.close()

	def __testTransferImage( self, fileName ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( os.path.expandvars( fileName ) )

		node = GafferImage.Display()
		node["port"].setValue( 2500 )

		self.Driver.sendImage( imageReader["out"], port = 2500 )

		# Display doesn't handle image metadata, so we must erase it before comparing the images
		inImage = imageReader["out"].image()
		inImage.blindData().clear()

		self.assertEqual( inImage, node["out"].image() )

		return node

	def __tiles( self, node, channelName ) :

		dataWindow = node["out"]["dataWindow"].getValue()

		minTileOrigin = GafferImage.ImagePlug.tileOrigin( dataWindow.min )
		maxTileOrigin = GafferImage.ImagePlug.tileOrigin( dataWindow.max )

		tiles = {}
		for y in range( minTileOrigin.y, maxTileOrigin.y, GafferImage.ImagePlug.tileSize() ) :
			for x in range( minTileOrigin.x, maxTileOrigin.x, GafferImage.ImagePlug.tileSize() ) :
				tiles[( x, y )] = node["out"].channelData( channelName, IECore.V2i( x, y ) )

		return tiles

	def __tileHashes( self, node, channelName ) :

		dataWindow = node["out"]["dataWindow"].getValue()

		minTileOrigin = GafferImage.ImagePlug.tileOrigin( dataWindow.min )
		maxTileOrigin = GafferImage.ImagePlug.tileOrigin( dataWindow.max )

		hashes = {}
		for y in range( minTileOrigin.y, maxTileOrigin.y, GafferImage.ImagePlug.tileSize() ) :
			for x in range( minTileOrigin.x, maxTileOrigin.x, GafferImage.ImagePlug.tileSize() ) :
				hashes[( x, y )] = node["out"].channelDataHash( channelName, IECore.V2i( x, y ) )

		return hashes

	def __assertTilesChangedInRegion( self, t1, t2, region ) :

		# Box2i.intersect assumes inclusive bounds, so make region inclusive
		inclusiveRegion = IECore.Box2i( region.min, region.max - IECore.V2i( 1 ) )

		for tileOriginTuple in t1.keys() :
			tileOrigin = IECore.V2i( *tileOriginTuple )
			tileRegion = IECore.Box2i( tileOrigin, tileOrigin + IECore.V2i( GafferImage.ImagePlug.tileSize() - 1 ) )

			if tileRegion.intersects( inclusiveRegion ) :
				self.assertNotEqual( t1[tileOriginTuple], t2[tileOriginTuple] )
			else :
				self.assertEqual( t1[tileOriginTuple], t2[tileOriginTuple] )

if __name__ == "__main__":
	unittest.main()
