##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import unittest

import IECore
import Gaffer
import GafferTest
import GafferImage

class ImagePlugTest( GafferTest.TestCase ) :

	def testTileOrigin( self ) :

		ts = GafferImage.ImagePlug.tileSize()
		
		testCases = [
			( IECore.V2i( ts-1, ts-1 ), IECore.V2i( 0, 0 ) ),
			( IECore.V2i( ts, ts-1 ), IECore.V2i( ts, 0 ) ),
			( IECore.V2i( ts, ts ), IECore.V2i( ts, ts ) ),
			( IECore.V2i( ts*3-1, ts+5 ), IECore.V2i( ts*2, ts ) ),
			( IECore.V2i( ts*3, ts-5 ), IECore.V2i( ts*3, 0 ) ),
			( IECore.V2i( -ts+ts/2, 0 ), IECore.V2i( -ts, 0 ) ),
			( IECore.V2i( ts*5+ts/3, -ts*4 ), IECore.V2i( ts*5, -ts*4 ) ),
			( IECore.V2i( -ts+1, -ts-1 ), IECore.V2i( -ts, -ts*2 ) )
		]

		for input, expectedResult in testCases :
			self.assertEqual(
				GafferImage.ImagePlug.tileOrigin( input ),
				expectedResult
			)

	def testTileStaticMethod( self ) :
	
		tileSize = GafferImage.ImagePlug.tileSize()
	
		self.assertEqual(
			GafferImage.ImagePlug.tileBound( IECore.V2i( 0 ) ),
			IECore.Box2i(
				IECore.V2i( 0, 0 ),
				IECore.V2i( tileSize - 1, tileSize - 1 )
			)
		)
		
		self.assertEqual(
			GafferImage.ImagePlug.tileBound( IECore.V2i( 0, 1 ) ),
			IECore.Box2i(
				IECore.V2i( 0, tileSize ),
				IECore.V2i( tileSize - 1, tileSize * 2 - 1 )
			)
		)
		
	def testDefaultChannelNamesMethod( self ) :
	
		channelNames = GafferImage.ImagePlug()['channelNames'].defaultValue()
		self.assertTrue( 'R' in channelNames )
		self.assertTrue( 'G' in channelNames )
		self.assertTrue( 'B' in channelNames )
	
	def testCreateCounterpart( self ) :
	
		p = GafferImage.ImagePlug()
		p2 = p.createCounterpart( "a", Gaffer.Plug.Direction.Out )
		
		self.assertEqual( p2.getName(), "a" )
		self.assertEqual( p2.direction(), Gaffer.Plug.Direction.Out )
		self.assertEqual( p2.getFlags(), p.getFlags() )
	
	def testDynamicSerialisation( self ) :
	
		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = GafferImage.ImagePlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		ss = s.serialise()
		
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.assertTrue( isinstance( s["n"]["p"], GafferImage.ImagePlug ) )
		self.assertEqual( s["n"]["p"].getFlags(), Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

	def testTypeNamePrefixes( self ) :
	
		self.assertTypeNamesArePrefixed( GafferImage, namesToIgnore = set( ( "IECore::FormatData", ) ) )

	def testDefaultNames( self ) :
	
		self.assertDefaultNamesAreCorrect( GafferImage )
	
if __name__ == "__main__":
	unittest.main()
