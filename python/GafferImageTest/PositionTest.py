##########################################################################
#  
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2014, Luke Goddard. All rights reserved.
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
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES LOSS OF USE, DATA, OR
#  PROFITS OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#  
##########################################################################

import unittest

import IECore
import Gaffer
import GafferTest
import GafferImage
import os

class PositionTest( unittest.TestCase ) :

	path = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/" )

	def testPosition( self ) :

		read = GafferImage.ImageReader()
		read["fileName"].setValue( os.path.join( self.path, "checkerBox.200x150.exr" ) )

		position = GafferImage.Position()
		position["in"].setInput( read["out"] )
		position["offset"].setValue( IECore.V2i( 0, 0 ) )
	
		self.assertEqual( position["out"]["dataWindow"].getValue(), IECore.Box2i( IECore.V2i( 0, 0 ), IECore.V2i( 199, 149 )  ) )

		d = IECore.Box2i( IECore.V2i( 0, 0 ), IECore.V2i( 199, 149 )  )		
		for j in range( 0, 10 ) :	
			for i in range( 0, 10 ) :
				offset = IECore.V2i( i * 10 - 50, j * 10 - 50 )
				position["offset"].setValue( offset )
				self.assertEqual( position["out"]["dataWindow"].getValue(), IECore.Box2i( d.min + offset, d.max + offset  ) )

	def testEnabled( self ) :
		
		read = GafferImage.ImageReader()
		read["fileName"].setValue( os.path.join( self.path, "blueWithDataWindow.100x100.exr" ) )
		position = GafferImage.Position()
		position["in"].setInput( read["out"] )
		position["offset"].setValue( IECore.V2i( 0, 0 ) )

		context = Gaffer.Context()
		context["image:channelName"] = "B"
		context["image:tileOrigin"] = IECore.V2i( GafferImage.ImagePlug.tileSize() )

		with context :
			self.assertEqual( position["in"]["format"].hash(), position["out"]["format"].hash() )
			self.assertEqual( position["in"]["channelNames"].hash(), position["out"]["channelNames"].hash() )
			self.assertEqual( position["in"]["dataWindow"].hash(), position["out"]["dataWindow"].hash() )
			self.assertEqual( position["in"]["channelData"].hash(), position["out"]["channelData"].hash() )
		
			position["enabled"].setValue( False )
			self.assertEqual( position["in"]["dataWindow"].hash(), position["out"]["dataWindow"].hash() )
			
			position["enabled"].setValue( True )
			position["offset"].setValue( IECore.V2i( 12, 1 ) )
			self.assertNotEqual( position["in"]["dataWindow"].hash(), position["out"]["dataWindow"].hash() )
			
			position["enabled"].setValue( False )
			self.assertEqual( position["in"]["dataWindow"].hash(), position["out"]["dataWindow"].hash() )

	def testHashPassThrough( self ) :
		
		read = GafferImage.ImageReader()
		read["fileName"].setValue( os.path.join( self.path, "checkerBox.200x150.exr" ) )
		position = GafferImage.Position()
		position["in"].setInput( read["out"] )
		
		context = Gaffer.Context()
		context["image:channelName"] = "B"
		context["image:tileOrigin"] = IECore.V2i( GafferImage.ImagePlug.tileSize() )

		# Sanity check...
		self.assertEqual( read["out"]["dataWindow"].getValue().min, IECore.V2i( 0 ) )
		
		# Gather the hashes of several tiles in a grid.	
		tileHashes = []
		for y in range( 0, 5 ) :
			tileHashes.append( [] )
			for x in range( 0, 5 ) :
				context["image:tileOrigin"] = IECore.V2i( x * GafferImage.ImagePlug.tileSize(), y * GafferImage.ImagePlug.tileSize() )
				with context :
					tileHashes[y].append( position["in"]["channelData"].hash() )

		# Here we test that the hashes are reused when the image is offset by a multiple of the tile size.
		for originY in range( 0, 5 ) :
			for originX in range( 0, 5 ) :
		
				for y in range( 0, 5 ) :
					for x in range( 0, 5 ) :
		
						offset = IECore.V2i( x * GafferImage.ImagePlug.tileSize(), y * GafferImage.ImagePlug.tileSize() )
						
						tileOriginToTest = IECore.V2i(
							originX * GafferImage.ImagePlug.tileSize() + offset.x,
							originY * GafferImage.ImagePlug.tileSize() + offset.y
						)
						
						context["image:tileOrigin"] = GafferImage.ImagePlug.tileOrigin( tileOriginToTest )

						with context :
							position["offset"].setValue( offset )
							self.assertEqual( position["out"]["channelData"].hash(), tileHashes[originY][originX] )

	def testDirtyPropagation( self ) :

		read = GafferImage.ImageReader()
		read["fileName"].setValue( os.path.join( self.path, "blueWithDataWindow.100x100.exr" ) )
		position = GafferImage.Position()
		position["in"].setInput( read["out"] )

		context = Gaffer.Context()
		context["image:channelName"] = "B"
		context["image:tileOrigin"] = IECore.V2i( 0 )

		with context :
			cs = GafferTest.CapturingSlot( position.plugDirtiedSignal() )
			position["offset"].setValue( IECore.V2i( 44, 1 ) )	

			dirtiedPlugs = set( [ x[0].relativeName( x[0].node() ) for x in cs ] )
			self.assertEqual( len( dirtiedPlugs ), 6 )
			self.assertTrue( "offset" in dirtiedPlugs )
			self.assertTrue( "offset.x" in dirtiedPlugs )
			self.assertTrue( "offset.y" in dirtiedPlugs )
			self.assertTrue( "out.channelData" in dirtiedPlugs )
			self.assertTrue( "out" in dirtiedPlugs )
			self.assertTrue( "out.dataWindow" in dirtiedPlugs )

