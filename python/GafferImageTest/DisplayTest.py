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

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__dataReceivedSemaphore = threading.Semaphore( 0 )
		self.__dataReceivedConnection = GafferImage.Display.dataReceivedSignal().connect( Gaffer.WeakMethod( self.__dataReceived ) )

		self.__imageReceivedSemaphore = threading.Semaphore( 0 )
		self.__imageReceivedConnection = GafferImage.Display.imageReceivedSignal().connect( Gaffer.WeakMethod( self.__imageReceived ) )

	def __dataReceived( self, plug ) :

		# Emulate the DisplayUI code which increments a plug when data is received, to
		# trigger correct recomputation.
		plug.node()["__updateCount"].setValue( plug.node()["__updateCount"].getValue() + 1 )
		self.__dataReceivedSemaphore.release()

	def __imageReceived( self, plug ) :

		plug.node()["__updateCount"].setValue( plug.node()["__updateCount"].getValue() + 1 )
		self.__imageReceivedSemaphore.release()

	def testDefaultFormat( self ) :

		d = GafferImage.Display()

		with Gaffer.Context() as c :
			self.assertEqual( d["out"]["format"].getValue(), GafferImage.FormatPlug.getDefaultFormat( c ) )
			GafferImage.FormatPlug.setDefaultFormat( c, GafferImage.Format( 200, 150, 1. ) )
			self.assertEqual( d["out"]["format"].getValue(), GafferImage.FormatPlug.getDefaultFormat( c ) )

	def testDeepState( self ) :

		d = GafferImage.Display()
		self.assertEqual( d["out"]["deepState"].getValue(), GafferImage.ImagePlug.DeepState.Flat )

	def testTileHashes( self ) :

		node = GafferImage.Display()
		node["port"].setValue( 2500 )

		gafferDisplayWindow = IECore.Box2i( IECore.V2i( -100, -200 ), IECore.V2i( 303, 557 ) )
		gafferFormat = GafferImage.Format( gafferDisplayWindow, 1.0 )

		externalDisplayWindow = gafferFormat.toEXRSpace( gafferDisplayWindow )

		externalDataWindow = externalDisplayWindow
		gafferDataWindow = gafferDisplayWindow
		driver = IECore.ClientDisplayDriver(
			externalDisplayWindow,
			externalDataWindow,
			[ "Y" ],
			{
				"displayHost" : "localHost",
				"displayPort" : "2500",
				"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
			}
		)

		for i in range( 0, 1000 ) :

			h1 = self.__tileHashes( node, "Y" )
			t1 = self.__tiles( node, "Y" )

			externalBucketWindow = IECore.Box2i()
			for j in range( 0, 2 ) :
				externalBucketWindow.extendBy(
					IECore.V2i(
						int( random.uniform( externalDisplayWindow.min.x, externalDisplayWindow.max.x ) ),
						int( random.uniform( externalDisplayWindow.min.y, externalDisplayWindow.max.y ) ),
					)
				)

			numPixels = ( externalBucketWindow.size().x + 1 ) * ( externalBucketWindow.size().y + 1 )
			bucketData = IECore.FloatVectorData()
			bucketData.resize( numPixels, i + 1 )
			driver.imageData( externalBucketWindow, bucketData )

			self.__dataReceivedSemaphore.acquire()

			h2 = self.__tileHashes( node, "Y" )
			t2 = self.__tiles( node, "Y" )

			gafferBucketWindow = gafferFormat.fromEXRSpace( externalBucketWindow )

			self.__assertTilesChangedInRegion( t1, t2, gafferBucketWindow )
			self.__assertTilesChangedInRegion( h1, h2, gafferBucketWindow )

		driver.imageClose()

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

	def __testTransferImage( self, fileName ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( os.path.expandvars( fileName ) )

		node = GafferImage.Display()
		node["port"].setValue( 2500 )

		externalDisplayWindow = gafferDisplayWindow = imageReader["out"]["format"].getValue().getDisplayWindow()
		externalDisplayWindow.max -= IECore.V2i( 1 )

		gafferDataWindow = imageReader["out"]["dataWindow"].getValue()
		externalDataWindow = imageReader["out"]["format"].getValue().toEXRSpace( gafferDataWindow )

		driver = IECore.ClientDisplayDriver(
			externalDisplayWindow,
			externalDataWindow,
			list( imageReader["out"]["channelNames"].getValue() ),
			{
				"displayHost" : "localHost",
				"displayPort" : "2500",
				"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
			}
		)

		tileSize = GafferImage.ImagePlug.tileSize()
		minTileOrigin = GafferImage.ImagePlug.tileOrigin( gafferDataWindow.min )
		maxTileOrigin = GafferImage.ImagePlug.tileOrigin( gafferDataWindow.max - IECore.V2i( 1 ) )
		for y in range( minTileOrigin.y, maxTileOrigin.y + 1, tileSize ) :
			for x in range( minTileOrigin.x, maxTileOrigin.x + 1, tileSize ) :
				tileOrigin = IECore.V2i( x, y )
				channelData = []
				for channelName in imageReader["out"]["channelNames"].getValue() :
					channelData.append( imageReader["out"].channelData( channelName, tileOrigin ) )
				bucketData = IECore.FloatVectorData()
				for by in range( tileSize - 1, -1, -1 ) :
					for bx in range( 0, tileSize ) :
						i = by * tileSize + bx
						for c in channelData :
							bucketData.append( c[i] )

				bucketBound = IECore.Box2i( tileOrigin, tileOrigin + IECore.V2i( GafferImage.ImagePlug.tileSize() ) )
				bucketBound = imageReader["out"]["format"].getValue().toEXRSpace( bucketBound )
				driver.imageData( bucketBound, bucketData )

		driver.imageClose()

		self.__imageReceivedSemaphore.acquire()

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
				self.assertNotEqual( t1[tileOriginTuple], t2[tileOriginTuple], "REMOVE BEFORE RELEASE" )
			else :
				self.assertEqual( t1[tileOriginTuple], t2[tileOriginTuple], "REMOVE BEFORE RELEASE" )

if __name__ == "__main__":
	unittest.main()
