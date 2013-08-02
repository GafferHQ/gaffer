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

import unittest

import IECore
import Gaffer
import GafferImage
import GafferTest
import os

class ClampTest( unittest.TestCase ) :
	
	def testClamp( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/colorbars_half_max.exr" ) )
		
		clamp = GafferImage.Clamp()
		clamp["in"].setInput(i["out"])
		clamp["maximum"].setValue( IECore.Color4f( .5, .5, .5, .5 ) )	

		self.assertEqual(i['out'].image().hash(), clamp['out'].image().hash())

	def testPerChannelHash( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/colorbars_half_max.exr" ) )
		
		clamp = GafferImage.Clamp()
		clamp["in"].setInput(i["out"])

		clamp["maximum"].setValue( IECore.Color4f( 1., 1., 1., 1. ) )

		redHash = clamp["out"].channelData( "R", IECore.V2i( 0 ) ).hash()
		greenHash = clamp["out"].channelData( "G", IECore.V2i( 0 ) ).hash()
		blueHash = clamp["out"].channelData( "B", IECore.V2i( 0 ) ).hash()		

		clamp["maximum"].setValue( IECore.Color4f( .25, 1., 1., 1. ) )

		redHash2 = clamp["out"].channelData( "R", IECore.V2i( 0 ) ).hash()
		greenHash2 = clamp["out"].channelData( "G", IECore.V2i( 0 ) ).hash()
		blueHash2 = clamp["out"].channelData( "B", IECore.V2i( 0 ) ).hash()	

		self.assertNotEqual(redHash, redHash2)
		self.assertEqual(greenHash, greenHash2)
		self.assertEqual(blueHash, blueHash2)

	def testDisconnectedDirty( self ) :
		
		r = GafferImage.ImageReader()
		r["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/colorbars_half_max.exr" ) )	
		clamp = GafferImage.Clamp()
		clamp["in"].setInput( r["out"] )

		cs = GafferTest.CapturingSlot( clamp.plugDirtiedSignal() )
		clamp["maximum"].setValue( IECore.Color4f( .25, 1., 1., 1. ) )
		
		dirtiedPlugs = set( [ x[0].relativeName( x[0].node() ) for x in cs ] )

		expectedPlugs = [
			'out.channelData',
			'out'
		]

		for plug in expectedPlugs :
			self.assertTrue( plug in dirtiedPlugs )

	def testClampWithMaxTo( self ) : 

		i = GafferImage.ImageReader()
		i["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/colorbars_max_clamp.exr" ) )
		
		clamp = GafferImage.Clamp()
		clamp["in"].setInput(i["out"])
		clamp["minimum"].setValue( IECore.Color4f( .0, .0, .0, .0 ) )
		clamp["maximum"].setValue( IECore.Color4f( .0, .25, .25, .25 ) )	
		clamp["minClampTo"].setValue( IECore.Color4f( .0, .0, .0, .0 ) )
		clamp["maxClampTo"].setValue( IECore.Color4f( 1., .5, .25, 1. ) )
		clamp["minimumEnabled"].setValue( True )
		clamp["maximumEnabled"].setValue( True )
		clamp["minClampToEnabled"].setValue( False )
		clamp["maxClampToEnabled"].setValue( True )

		self.assertEqual(i['out'].image().hash(), clamp['out'].image().hash())

	def testDefaultState( self ) :

		clamp = GafferImage.Clamp()
	
		self.assertTrue( clamp['minimumEnabled'].getValue() )
		self.assertTrue( clamp['maximumEnabled'].getValue() )
		self.assertFalse( clamp['minClampToEnabled'].getValue() )
		self.assertFalse( clamp['maxClampToEnabled'].getValue() )

	def testEnabledBypass( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/colorbars_half_max.exr" ) )
		
		clamp = GafferImage.Clamp()
		clamp["in"].setInput(i["out"])
		clamp["minimumEnabled"].setValue( False )
		clamp["maximumEnabled"].setValue( False )

		self.assertEqual(i['out'].image().hash(), clamp['out'].image().hash())

	def testEnableBehaviour( self ) :
		
		clamp = GafferImage.Clamp()

		self.assertTrue( clamp.enabledPlug().isSame( clamp["enabled"] ) )
		self.assertTrue( clamp.correspondingInput( clamp["out"] ).isSame( clamp["in"] ) )
		self.assertEqual( clamp.correspondingInput( clamp["in"] ), None )
		self.assertEqual( clamp.correspondingInput( clamp["enabled"] ), None )
		self.assertEqual( clamp.correspondingInput( clamp["minimum"] ), None )

if __name__ == "__main__":
	unittest.main()
