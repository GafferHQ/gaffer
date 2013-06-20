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

import os
import unittest
import IECore
import Gaffer
import GafferImage
import GafferTest
import sys
import math

class ImageStatsTest( unittest.TestCase ) :
	
	__rgbFilePath = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/rgb.100x100.exr" )
	
	def testHash( self ) :
		pass	
		
	# Test that the outputs change when different channels are selected.
	def testChannels( self ) :
		
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath )
		
		s = GafferImage.ImageStats()
		s["in"].setInput( r["out"] )
		
		s["channels"].setValue( IECore.StringVectorData( [ "G", "B" ] ) )
		self.__assertColour( s["average"].getValue(), IECore.Color4f( 0., 0.0744, 0.1250, 1. ) )
		self.__assertColour( s["min"].getValue(), IECore.Color4f( 0, 0, 0, 1. ) )
		self.__assertColour( s["max"].getValue(), IECore.Color4f( 0, 0.5, 0.5, 1. ) )
		
		s["channels"].setValue( IECore.StringVectorData( [ "R", "B" ] ) )
		self.__assertColour( s["average"].getValue(), IECore.Color4f( 0.0544, 0, 0.1250, 1. ) )
		self.__assertColour( s["min"].getValue(), IECore.Color4f( 0, 0, 0, 1. ) )
		self.__assertColour( s["max"].getValue(), IECore.Color4f( 0.5, 0, 0.5, 1. ) )

	def testDisconnectedDirty( self ) :
		
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath )	
		s = GafferImage.ImageStats()
		s["in"].setInput( r["out"] )
		s["in"].setInput( None )

		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )
		s["in"].setInput( r["out"] )
		
		dirtiedPlugs = set( [ x[0].relativeName( x[0].node() ) for x in cs ] )
			
		expectedPlugs = [
			'min',
			'min.r',
			'min.g',
			'min.b',
			'min.a',
			'max',
			'max.r',
			'max.g',
			'max.b',
			'max.a',
			'average',
			'average.r',
			'average.g',
			'average.b',
			'average.a',
			'in',
			'in.dataWindow',
			'in.channelNames',
			'in.format',
			'in.channelData'
		]

		for plug in expectedPlugs :
			self.assertTrue( plug in dirtiedPlugs )
	
	def testDisconnectHash( self ) :	
		
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath )	
		s = GafferImage.ImageStats()
		s["in"].setInput( r["out"] )

		# Get the hashes of the outputs when there is no input.
		s["in"].setInput( None )
		minHash = s["min"].hash()
		maxHash = s["max"].hash()
		averageHash = s["average"].hash()

		# Check that they are not equal to the hashes when we have an input. 
		s["in"].setInput( r["out"] )
		self.assertNotEqual( minHash, s["min"].hash() )
		self.assertNotEqual( maxHash, s["max"].hash() )
		self.assertNotEqual( averageHash, s["average"].hash() )
		
	def testImageDisconnectValue( self ) :
		
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath )	
		s = GafferImage.ImageStats()

		# Connect.
		s["in"].setInput( r["out"] )
		self.__assertColour( s["average"].getValue(), IECore.Color4f( 0.0544, 0.0744, 0.1250, 1. ) )
		self.__assertColour( s["min"].getValue(), IECore.Color4f( 0, 0, 0, 1. ) )
		self.__assertColour( s["max"].getValue(), IECore.Color4f( 0.5, 0.5, 0.5, 1. ) )

		# Disconnect.
		s["in"].setInput( None )
		self.__assertColour( s["average"].getValue(), IECore.Color4f( 0, 0, 0, 1 ) )
		self.__assertColour( s["min"].getValue(), IECore.Color4f( 0, 0, 0, 1 ) )
		self.__assertColour( s["max"].getValue(), IECore.Color4f( 0, 0, 0, 1 ) )

		# Connect again.
		s["in"].setInput( r["out"] )
		self.__assertColour( s["average"].getValue(), IECore.Color4f( 0.0544, 0.0744, 0.1250, 1. ) )
		self.__assertColour( s["min"].getValue(), IECore.Color4f( 0, 0, 0, 1. ) )
		self.__assertColour( s["max"].getValue(), IECore.Color4f( 0.5, 0.5, 0.5, 1. ) ) 
	
	def testRoiDefault( self ) :
		
		reader = GafferImage.ImageReader()
		script = Gaffer.ScriptNode()
		stats = GafferImage.ImageStats()
		script.addChild( reader )
		script.addChild( stats )
		
		with script.context() :
			reader["fileName"].setValue( self.__rgbFilePath )
			stats["in"].setInput( reader["out"] )
			self.assertEqual( stats["regionOfInterest"].getValue(), reader["out"]["format"].getValue().getDisplayWindow() )

	def testStats( self ) :
		
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath )
		
		s = GafferImage.ImageStats()
		s["in"].setInput( r["out"] )
		s["channels"].setValue( IECore.StringVectorData( [ "R", "G", "B", "A" ] ) )
		
		s["regionOfInterest"].setValue( r["out"]["format"].getValue().getDisplayWindow() )
		self.__assertColour( s["average"].getValue(), IECore.Color4f( 0.0544, 0.0744, 0.1250, 0.2537 ) )
		self.__assertColour( s["min"].getValue(), IECore.Color4f( 0, 0, 0, 0 ) )
		self.__assertColour( s["max"].getValue(), IECore.Color4f( 0.5, 0.5, 0.5, 0.875 ) )
	
	# Test that we can change the ROI and the outputs are correct.
	def testROI( self ) :
		
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath )
		
		s = GafferImage.ImageStats()
		s["in"].setInput( r["out"] )
		s["channels"].setValue( IECore.StringVectorData( [ "R", "G", "B", "A" ] ) )
		
		s["regionOfInterest"].setValue( IECore.Box2i( IECore.V2i( 20, 20 ), IECore.V2i( 24, 24 ) ) )
		self.__assertColour( s["average"].getValue(), IECore.Color4f( 0.5, 0, 0, 0.5 ) )
		self.__assertColour( s["max"].getValue(), IECore.Color4f( 0.5, 0, 0, 0.5 ) )
		self.__assertColour( s["min"].getValue(), IECore.Color4f( 0.5, 0, 0, 0.5 ) )
		
		s["regionOfInterest"].setValue( IECore.Box2i( IECore.V2i( 20, 20 ), IECore.V2i( 40, 29 ) ) )
		self.__assertColour( s["average"].getValue(), IECore.Color4f( 0.4048, 0.1905, 0, 0.5952 ) )
		self.__assertColour( s["min"].getValue(), IECore.Color4f( 0.25, 0, 0, 0.5 ) )
		self.__assertColour( s["max"].getValue(), IECore.Color4f( 0.5, 0.5, 0, 0.75 ) )

	def __assertColour( self, colour1, colour2 ) :
		for i in range( 0, 4 ):
			self.assertEqual( "%.4f" % colour2[i], "%.4f" % colour1[i] )

if __name__ == "__main__":
	unittest.main()

