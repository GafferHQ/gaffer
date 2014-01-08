##########################################################################
#  
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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
import random

import IECore
import Gaffer

import GafferImage

class FormatTest( unittest.TestCase ) :
	def testAddRemoveFormat( self ) :
		# Get any existing format names
		existingFormatNames = GafferImage.Format.formatNames()
		
		# Assert that our test format is in not in the list of formats
		self.assertFalse( self.__testFormatName() in existingFormatNames )
		
		# Add a test format
		GafferImage.Format.registerFormat( self.__testFormatValue(), self.__testFormatName() )
		
		# Get the new list of format names and test that it contains our new format
		self.assertTrue( self.__testFormatName() in GafferImage.Format.formatNames() )
		
		# Attempt to get the format we added by name and check to see if the results are what we expect
		testFormat = GafferImage.Format.getFormat( self.__testFormatName() )
		self.__assertTestFormat( testFormat )
		
		# Now remove it by name.
		GafferImage.Format.removeFormat( self.__testFormatName() )
		
		# Get the new list of format names and check that it is the same as the old list
		self.assertEqual( set( existingFormatNames ), set( GafferImage.Format.formatNames() ) )
		
	def testDefaultFormatPlugExists( self ) :
		# Create a node to make sure that we have a default format...
		s = Gaffer.ScriptNode()
		n = GafferImage.Grade()
		s.addChild( n )

		try:
			# Now assert that the default format plug exists. If it doesn't then an exception is raised.
			s["defaultFormat"]
		except:
			self.assertTrue(False)
	
	def testOffsetDisplayWindow( self ) :
		box = IECore.Box2i( IECore.V2i( 6, -4 ), IECore.V2i( 49, 149 ) )
		f = GafferImage.Format( box, 1.1 )
		self.assertEqual( f.getDisplayWindow(), box )
		self.assertEqual( f.width(), 44 )
		self.assertEqual( f.height(), 154 )
		self.assertEqual( f.getPixelAspect(), 1.1 )
	
	def testBoxAspectConstructor( self ) :
		f = GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 49, 149 ) ), 1.3 )
		self.assertEqual( f.width(), 50 )
		self.assertEqual( f.height(), 150 )
		self.assertEqual( f.getPixelAspect(), 1.3 )
		
	def testWH( self ) :
		f = GafferImage.Format( 101, 102, 1. )
		self.assertEqual( f.width(), 101 )
		self.assertEqual( f.height(), 102 )
		
		f = GafferImage.Format( 0, 0, 1. )
		self.assertEqual( f.width(), 0 )
		self.assertEqual( f.height(), 0 )
		
	def testDefaultFormatContext( self ) :
		# Create a node to make sure that we have a default format...
		s = Gaffer.ScriptNode()
		n = GafferImage.Grade()
		s.addChild( n )
		s.context().get("image:defaultFormat")
	
	def testHashChanged( self ) :
		# Create a grade node and check that the format changes if it is unconnected.
		n = GafferImage.Grade()
		s = Gaffer.ScriptNode()
		s.addChild( n )
		
		h1 = n["out"]["format"].hash()
		
		# Change the default format.
		GafferImage.Format.registerFormat( self.__testFormatValue(), self.__testFormatName() )
		GafferImage.Format.setDefaultFormat( s, self.__testFormatValue() )
		
		# Check that the hash has changed.
		h2 = n["out"]["format"].hash()
		
		self.assertNotEqual( h1, h2 )
		
	def testDefaultFormatChanged( self ) :
		# Create a grade node and check that the format changes if it is unconnected.
		n = GafferImage.Grade()
		s = Gaffer.ScriptNode()
		s.addChild( n )
		
		p = GafferImage.ImagePlug( "test", GafferImage.ImagePlug.Direction.In )
		p.setInput( n["out"] )
		
		with s.context() :
			f1 = p["format"].getValue()

			# Change the default format.
			GafferImage.Format.registerFormat( self.__testFormatValue(), self.__testFormatName() )
			GafferImage.Format.setDefaultFormat( s, self.__testFormatValue() )
		
			# Check that the hash has changed.
			f2 = p["format"].getValue()
		
			self.assertNotEqual( f1, f2 )
		
	def testAddRemoveFormatByValue( self ) :
		# Get any existing format names
		existingFormatNames = GafferImage.Format.formatNames()
		
		# Assert that our test format is in not in the list of formats
		self.assertFalse( self.__testFormatName() in existingFormatNames )
		
		# Add a test format by value only
		GafferImage.Format.registerFormat( self.__testFormatValue() )
		
		# Get the new list of format names and test that it contains our new format name
		self.assertTrue( self.__testFormatName() in GafferImage.Format.formatNames() )
		
		# Attempt to get the format we added by name and check to see if the results are what we expect
		testFormat = GafferImage.Format.getFormat( self.__testFormatName() )
		self.__assertTestFormat( testFormat )
		
		# Now remove it by value.
		GafferImage.Format.removeFormat( self.__testFormatValue() )
		
		# Get the new list of format names and check that it is the same as the old list
		self.assertEqual( set( existingFormatNames ), set( GafferImage.Format.formatNames() ) )
	
	def testCoordinateSystemTransforms( self ) :
	
		f = GafferImage.Format( IECore.Box2i( IECore.V2i( -100, -200 ), IECore.V2i( 500, 300 ) ), 1 )
		
		self.assertEqual( f.yDownToFormatSpace( IECore.V2i( -100, -200 ) ), IECore.V2i( -100, 300 ) )
		self.assertEqual( f.yDownToFormatSpace( IECore.V2i( -100, 300 ) ), IECore.V2i( -100, -200 ) )

		self.assertEqual( f.formatToYDownSpace( IECore.V2i( -100, -200 ) ), IECore.V2i( -100, 300 ) )
		self.assertEqual( f.formatToYDownSpace( IECore.V2i( -100, 300 ) ), IECore.V2i( -100, -200 ) )
	
		for i in range( 0, 1000 ) :
		
			p = IECore.V2i( int( random.uniform( -500, 500 ) ), int( random.uniform( -500, 500 ) ) )
			pDown = f.formatToYDownSpace( p )
			self.assertEqual( f.yDownToFormatSpace( pDown ), p )
	
	def __assertTestFormat( self, testFormat ):
		self.assertEqual( testFormat.getPixelAspect(), 1.4 )
		self.assertEqual( testFormat.width(), 1234 )
		self.assertEqual( testFormat.height(), 5678 )
		self.assertEqual( testFormat.getDisplayWindow(), IECore.Box2i( IECore.V2i( 0, 0 ), IECore.V2i( 1233, 5677 ) ) )
		
	def __testFormatValue( self ) :
		return GafferImage.Format( 1234, 5678, 1.4 )
		
	def __testFormatName( self ) :
		return '1234x5678 1.400'
		

if __name__ == "__main__":
	unittest.main()
