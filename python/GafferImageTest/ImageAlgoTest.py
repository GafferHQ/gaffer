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

import unittest
import imath
import itertools
import re

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ImageAlgoTest( GafferImageTest.ImageTestCase ) :

	def testLayerName( self ) :

		for channelName, layerName in [
			( "R", "" ),
			( "A", "" ),
			( "Z", "" ),
			( "myFunkyChannel", "" ),
			( "left.R", "left" ),
			( "right.myFunkyChannel", "right" ),
			( "diffuse.left.R", "diffuse.left" ),
		] :
			self.assertEqual( GafferImage.ImageAlgo.layerName( channelName ), layerName )

	def testBaseName( self ) :

		for channelName, baseName in [
			( "R", "R" ),
			( "A", "A" ),
			( "Z", "Z" ),
			( "myFunkyChannel", "myFunkyChannel" ),
			( "left.R", "R" ),
			( "right.myFunkyChannel", "myFunkyChannel" ),
			( "diffuse.left.R", "R" ),
		] :
			self.assertEqual( GafferImage.ImageAlgo.baseName( channelName ), baseName )

	def testChannelName( self ) :

		for layerName, baseName, channelName in [
			( "", "R", "R" ),
			( "", "G", "G" ),
			( "", "myFunkyChannel", "myFunkyChannel" ),
			( "left", "R", "left.R" ),
			( "right", "myFunkyChannel", "right.myFunkyChannel" ),
			( "diffuse.left", "R", "diffuse.left.R" ),
		] :
			self.assertEqual( GafferImage.ImageAlgo.channelName( layerName, baseName ), channelName )

	def testColorIndex( self ) :

		for channelName, index in [
			( "R", 0 ),
			( "G", 1 ),
			( "B", 2 ),
			( "A", 3 ),
			( "Z", -1 ),
			( "myFunkyChannel", -1 ),
			( "left.R", 0 ),
			( "left.G", 1 ),
			( "left.B", 2 ),
			( "left.A", 3 ),
			( "left.Z", -1 ),
			( "right.myFunkyChannel", -1 ),
			( "diffuse.left.R", 0 ),
			( "diffuse.left.G", 1 ),
			( "diffuse.left.B", 2 ),
			( "diffuse.left.A", 3 ),
			( "diffuse.left.Z", -1 ),
		] :
			self.assertEqual( GafferImage.ImageAlgo.colorIndex( channelName ), index )

	def testChannelExists( self ) :

		c = GafferImage.Constant()

		d = GafferImage.DeleteChannels()
		d["in"].setInput( c["out"] )
		d["mode"].setValue( GafferImage.DeleteChannels.Mode.Delete )
		d["channels"].setValue( "" )

		self.assertTrue( GafferImage.ImageAlgo.channelExists( d["out"], "R" ) )
		self.assertTrue( GafferImage.ImageAlgo.channelExists( d["out"], "G" ) )
		self.assertTrue( GafferImage.ImageAlgo.channelExists( d["out"], "B" ) )
		self.assertTrue( GafferImage.ImageAlgo.channelExists( d["out"], "A" ) )

		for chan in [ "R", "G", "B", "A" ] :
			d["channels"].setValue( chan )
			self.assertFalse( GafferImage.ImageAlgo.channelExists( d["out"], chan ) )

	def testChannelExistsBindings( self ) :

		# Test that both forms of binding to channelExists return the same
		# value

		c = GafferImage.Constant()

		d = GafferImage.DeleteChannels()
		d["in"].setInput( c["out"] )
		d["mode"].setValue( GafferImage.DeleteChannels.Mode.Delete )
		d["channels"].setValue( "R A" )

		for chan in [ "R", "G", "B", "A" ] :
			self.assertEqual( GafferImage.ImageAlgo.channelExists( d["out"], chan ), GafferImage.ImageAlgo.channelExists( d["out"]["channelNames"].getValue(), chan ) )

	def testParallelProcessEmptyDataWindow( self ) :

		d = GafferImage.Display()
		self.assertEqual( d["out"]["dataWindow"].getValue(), imath.Box2i() )

		GafferImageTest.processTiles( d["out"] )
		GafferImage.ImageAlgo.image( d["out"] )
		GafferImage.ImageAlgo.imageHash( d["out"] )

	def testLayerNames( self ) :

		self.assertEqual(
			GafferImage.ImageAlgo.layerNames( [ "R", "G", "B" ] ),
			[ "" ]
		)

		self.assertEqual(
			GafferImage.ImageAlgo.layerNames( [ "Z", "A" ] ),
			[ "" ]
		)

		self.assertEqual(
			GafferImage.ImageAlgo.layerNames( [ "R", "G", "B", "diffuse.R", "diffuse.G", "diffuse.B" ] ),
			[ "", "diffuse" ]
		)

		self.assertEqual(
			GafferImage.ImageAlgo.layerNames( [ "R", "G", "B", "foreground.diffuse.R", "foreground.diffuse.G", "foreground.diffuse.B" ] ),
			[ "", "foreground.diffuse" ]
		)

	def testParallelGatherTileOrder( self ) :

		c = GafferImage.Constant()

		tileOrigins = []
		channelTileOrigins = []

		def tileFunctor( *args ) :

			pass

		def gatherFunctor( image, tileOrigin, tile ) :

			tileOrigins.append( tileOrigin )

		def channelGatherFunctor( image, channelName, tileOrigin, tile ) :

			channelTileOrigins.append( tileOrigin )

		for window in [
			# Window not aligned to tile boundaries
			imath.Box2i( imath.V2i( 2 ), GafferImage.ImagePlug.tileSize() * imath.V2i( 20, 8 ) - imath.V2i( 2 ) ),
			# Window aligned to tile boundaries
			imath.Box2i( imath.V2i( 0 ), GafferImage.ImagePlug.tileSize() * imath.V2i( 6, 7 ) ),
			# Negative origin
			imath.Box2i( imath.V2i( -GafferImage.ImagePlug.tileSize() ), GafferImage.ImagePlug.tileSize() * imath.V2i( 4, 6 ) )
		] :

			size = GafferImage.ImagePlug.tileIndex( window.max() - imath.V2i( 1 ) ) - GafferImage.ImagePlug.tileIndex( window.min() ) + imath.V2i( 1 )
			numTiles = size.x * size.y

			for order in GafferImage.ImageAlgo.TileOrder.values.values() :

				del tileOrigins[:]
				del channelTileOrigins[:]

				GafferImage.ImageAlgo.parallelGatherTiles(
					c["out"],
					tileFunctor,
					gatherFunctor,
					window = window,
					tileOrder = order
				)

				GafferImage.ImageAlgo.parallelGatherTiles(
					c["out"],
					[ "R" ],
					tileFunctor,
					channelGatherFunctor,
					window = window,
					tileOrder = order
				)

				self.assertEqual( len( tileOrigins ), numTiles )
				self.assertEqual( len( channelTileOrigins ), numTiles )

				for i in range( 1, len( tileOrigins ) ) :

					if order == GafferImage.ImageAlgo.TileOrder.TopToBottom :
						self.assertGreaterEqual( tileOrigins[i-1].y, tileOrigins[i].y )
					elif order == GafferImage.ImageAlgo.TileOrder.BottomToTop :
						self.assertLessEqual( tileOrigins[i-1].y, tileOrigins[i].y )

					if order != GafferImage.ImageAlgo.TileOrder.Unordered :
						self.assertEqual( channelTileOrigins[i], tileOrigins[i] )

	def testParallelGatherTileLifetime( self ) :

		constant = GafferImage.Constant()
		constant["color"].setValue( imath.Color4f( 1 ) )

		def computeTile( image, channelName, tileOrigin ) :

			return image["channelData"].getValue()

		def gatherTile( image, channelName, tileOrigin, tile ) :

			self.assertIsInstance( tile, IECore.FloatVectorData )

		GafferImage.ImageAlgo.parallelGatherTiles( constant["out"], [ "R", "G", "B", "A" ], computeTile, gatherTile )

	def testMonitorParallelProcessTiles( self ) :

		numTilesX = 50
		numTilesY = 50

		c = GafferImage.Checkerboard()
		c["format"].setValue(
			GafferImage.Format(
				numTilesX * GafferImage.ImagePlug.tileSize(),
				numTilesY * GafferImage.ImagePlug.tileSize(),
			)
		)

		with Gaffer.PerformanceMonitor() as m :
			GafferImageTest.processTiles( c["out"] )

		self.assertEqual(
			m.plugStatistics( c["out"]["channelData"] ).computeCount,
			numTilesX * numTilesY * 4
		)

	def testSortChannelNames( self ):

		# Sort RGBA
		self.assertEqual( GafferImage.ImageAlgo.sortChannelNames( [ "R", "A", "B", "G" ] ), [ "R", "G", "B", "A" ] )

		# Sort RGBA	before other channels
		self.assertEqual( GafferImage.ImageAlgo.sortChannelNames( [ "A", "Arc", "Z", "ZSomethingElse", "H", "Bark", "G", "ZBack", "custom", "F", "R", "B" ] ), [ "R", "G", "B", "A", "Arc", "Bark", "F", "H", "Z", "ZBack", "ZSomethingElse", "custom" ] )

		# Sort default layer before named layers
		self.assertEqual( GafferImage.ImageAlgo.sortChannelNames( [ "A", "G", "A.G", "B.B", "A.R", "B.R", "B", "R", "A.B", "B.G" ] ), [ "R", "G", "B", "A", "A.R", "A.G", "A.B", "B.R", "B.G", "B.B" ] )

		# Sort hierarchical layers
		self.assertEqual( GafferImage.ImageAlgo.sortChannelNames( [ "Y.X.Y", "Y.X.X", "Y", "X", "X.X", "X.Y" ] ), [ "X", "Y", "X.X", "X.Y", "Y.X.X", "Y.X.Y" ] )

		# Default alphabetical sort puts capital letters before lowercase ( dunno if this is good or not, but
		# worth documenting )
		self.assertEqual( GafferImage.ImageAlgo.sortChannelNames( [ "x", "X", "x.x", "X.X", "X.x", "x.X" ] ), ["X", "x", "X.X", "X.x", "x.X", "x.x"] )

		# Test that our natural sort handles numbers
		self.assertEqual(
			GafferImage.ImageAlgo.sortChannelNames( [ "12", "4", "1", "14", "2", "3", "13", "99" ] ),
			[ "1", "2", "3", "4", "12", "13", "14", "99" ]
		)

		self.assertEqual(
			GafferImage.ImageAlgo.sortChannelNames( [ str( 999 - i ) for i in range( 1000 ) ] ),
			[ str( i ) for i in range( 1000 ) ]
		)

		# And numbers with varying padding
		self.assertEqual(
			GafferImage.ImageAlgo.sortChannelNames( [ "03", "00012", "4", "01", "0000014", "2", "00003", "13", "3", "99" ] ),
			[ "01", "2", "3", "03", "00003", "4", "00012", "13", "0000014", "99" ]
		)

		# Test large numbers ( larger than the size of an integer )
		largeNums = [ str( ( i % 9 ) + 1 ) + "0" * i for i in range( 30 ) ]
		self.assertEqual( GafferImage.ImageAlgo.sortChannelNames( largeNums ), largeNums )

		# Test something like how we see this being used in production
		realistic = [ "channel0", "channel1", "channel2", "channel2alt", "channel2alt2", "channel2alt13", "channel04", "channel13" ]
		self.assertEqual( GafferImage.ImageAlgo.sortChannelNames( realistic ), realistic )

		# And test every length 4 possibility for alternating letters and digits
		permutations = [ "".join( i ) for j in [1,2,3,4 ] for i in itertools.product( *["012acC"] * j ) ]
		permutationsGaffer = GafferImage.ImageAlgo.sortChannelNames( permutations )


		# The most debatable order here is between "00C0" and "0C00", which conceptually mean the same thing, and
		# are the same length.  Our ordering is consistent, which is all that matters in this corner case.
		self.assertEqual( permutationsGaffer[:10], ['0', '00', '000', '0000', '0C', '00C', '000C', '0C0', '00C0', '0C00'] )
		self.assertEqual( permutationsGaffer[-10:], ['ccaC', 'ccaa', 'ccac', 'ccc', 'ccc0', 'ccc1', 'ccc2', 'cccC', 'ccca', 'cccc'] )

		# We don't want to check all of these manually, so just make sure we agree with an independent
		# implementation of a basic Python natural sort ( as long as we stay away from "." and RGBA which
		# have a special meaning for channel names )
		pythonRegex = re.compile('([0-9]+)')
		def pythonNaturalSortKey( s ):
			return [int(text) if text.isdigit() else text for text in pythonRegex.split(s)]
		permutationsPython = sorted( permutations, key = pythonNaturalSortKey )
		self.assertEqual( permutationsGaffer, permutationsPython )


if __name__ == "__main__":
	unittest.main()
