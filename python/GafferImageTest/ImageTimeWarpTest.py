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

import unittest
import inspect

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ImageTimeWarpTest( GafferImageTest.ImageTestCase ) :

	def testDefaultName( self ) :

		t = GafferImage.ImageTimeWarp()
		self.assertEqual( t.getName(), "ImageTimeWarp" )

	def testEnabledPlug( self ) :

		t = GafferImage.ImageTimeWarp()
		self.assertTrue( isinstance( t["enabled"], Gaffer.BoolPlug ) )
		self.assertTrue( t["enabled"].isSame( t.enabledPlug() ) )
		self.assertFalse( "enabled1" in t )

	def testAffects( self ) :

		timeWarp = GafferImage.ImageTimeWarp()

		for n in [ "format", "dataWindow", "metadata", "channelNames", "channelData" ] :
			a = timeWarp.affects( timeWarp["in"][n] )
			self.assertEqual( len( a ), 1 )
			self.assertTrue( a[0].isSame( timeWarp["out"][n] ) )

		for n in [ "enabled", "offset", "speed" ] :
			a = set( [ plug.relativeName( plug.node() ) for plug in timeWarp.affects( timeWarp[n] ) ] )
			self.assertEqual(
				a,
				set( [
					"out.format", "out.dataWindow", "out.metadata", "out.channelNames", "out.channelData",
				] ),
			)

	def testTimeWarping( self ) :

		script = Gaffer.ScriptNode()

		script["constant"] = GafferImage.Constant()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( 'parent["constant"]["color"]["r"] = context["frame"]' )

		script["timeWarp"] = GafferImage.ImageTimeWarp()
		script["timeWarp"]["offset"].setValue( 1 )
		script["timeWarp"]["in"].setInput( script["constant"]["out"] )

		for f in range( 0, 10 ) :
			with script.context() :

				script.context().setFrame( f )
				c0 = script["constant"]["out"].image()
				c0Hash = script["constant"]["out"].imageHash()
				t = script["timeWarp"]["out"].image()
				tHash = script["timeWarp"]["out"].imageHash()

				script.context().setFrame( f + 1 )
				c1 = script["constant"]["out"].image()
				c1Hash = script["constant"]["out"].imageHash()

			self.assertEqual( c1, t )
			self.assertEqual( c1Hash, tHash )
			self.assertNotEqual( c0, c1 )
			self.assertNotEqual( c0Hash, c1Hash )

	def testTimeContext( self ) :
		script = Gaffer.ScriptNode()
		script["constant"] = GafferImage.Constant()
		script["constant"]["format"].setValue( GafferImage.Format( 1, 1, 1.0 ) )
		
		script["e"] = Gaffer.Expression()
		script["e"].setExpression( 'parent["constant"]["color"] = IECore.Color4f( context["frame"] )' )

		script["timeWarp"] = GafferImage.ImageTimeWarp()
		script["timeWarp"]["in"].setInput( script["constant"]["out"] )
		script["timeWarp"]["speed"].setValue( 0 )
		script["timeWarp"]["offset"].setValue( 3 )

		script["sampler"] = GafferImage.ImageSampler()
		script["sampler"]["pixel"].setValue( IECore.V2f( 0.5, 0.5 ) )
		script["sampler"]["image"].setInput( script["timeWarp"]["out"] )

		self.assertEqual( script["sampler"]["color"].getValue(), IECore.Color4f( 3 ) )

		script["e2"] = Gaffer.Expression()
		script["e2"].setExpression( inspect.cleandoc(
			"""
			assert( context.get( "image:channelName", None ) is None )
			assert( context.get( "image:tileOrigin", None ) is None )
			parent["timeWarp"]["offset"] = 5
			"""
		) )

		self.assertEqual( script["sampler"]["color"].getValue(), IECore.Color4f( 5 ) )

	def testDisabling( self ) :

		script = Gaffer.ScriptNode()

		script["constant"] = GafferImage.Constant()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( 'parent["constant"]["color"]["r"] = context["frame"]' )

		script["timeWarp"] = GafferImage.ImageTimeWarp()
		script["timeWarp"]["offset"].setValue( 1 )
		script["timeWarp"]["in"].setInput( script["constant"]["out"] )

		with script.context() :

			c = script["constant"]["out"].image()
			cHash = script["constant"]["out"].imageHash()
			t = script["timeWarp"]["out"].image()
			tHash = script["timeWarp"]["out"].imageHash()

		self.assertNotEqual( c, t )
		self.assertNotEqual( cHash, tHash )

		script["timeWarp"]["enabled"].setValue( False )

		with script.context() :

			c = script["constant"]["out"].image()
			cHash = script["constant"]["out"].imageHash()
			t = script["timeWarp"]["out"].image()
			tHash = script["timeWarp"]["out"].imageHash()

		self.assertEqual( c, t )
		self.assertEqual( cHash, tHash )

if __name__ == "__main__":
	unittest.main()
