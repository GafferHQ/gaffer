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
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ImageTimeWarpTest( GafferImageTest.ImageTestCase ) :

	def testEnabledPlug( self ) :

		t = Gaffer.TimeWarp()
		t.setup( GafferImage.ImagePlug() )
		self.assertTrue( isinstance( t["enabled"], Gaffer.BoolPlug ) )
		self.assertTrue( t["enabled"].isSame( t.enabledPlug() ) )
		self.assertFalse( "enabled1" in t )

	def testAffects( self ) :

		timeWarp = Gaffer.TimeWarp()
		timeWarp.setup( GafferImage.ImagePlug() )

		for n in [ "format", "dataWindow", "metadata", "deep", "sampleOffsets", "channelNames", "channelData" ] :
			a = timeWarp.affects( timeWarp["in"][n] )
			self.assertEqual( len( a ), 1 )
			self.assertTrue( a[0].isSame( timeWarp["out"][n] ) )

		for n in [ "enabled", "offset", "speed" ] :
			a = set( [ plug.relativeName( plug.node() ) for plug in timeWarp.affects( timeWarp[n] ) ] )
			self.assertEqual(
				a,
				set( [
					"out.viewNames", "out.format", "out.dataWindow", "out.metadata", "out.deep", "out.sampleOffsets", "out.channelNames", "out.channelData",
				] ),
			)

	def testTimeWarping( self ) :

		script = Gaffer.ScriptNode()

		script["constant"] = GafferImage.Constant()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( 'parent["constant"]["color"]["r"] = context["frame"]' )

		script["timeWarp"] = Gaffer.TimeWarp()
		script["timeWarp"].setup( GafferImage.ImagePlug() )
		script["timeWarp"]["offset"].setValue( 1 )
		script["timeWarp"]["in"].setInput( script["constant"]["out"] )

		for f in range( 0, 10 ) :
			with script.context() :

				script.context().setFrame( f )
				c0 = GafferImage.ImageAlgo.image( script["constant"]["out"], viewName = "default" )
				c0Hash = GafferImage.ImageAlgo.imageHash( script["constant"]["out"], viewName = "default" )
				t = GafferImage.ImageAlgo.image( script["timeWarp"]["out"], viewName = "default" )
				tHash = GafferImage.ImageAlgo.imageHash( script["timeWarp"]["out"], viewName = "default" )

				script.context().setFrame( f + 1 )
				c1 = GafferImage.ImageAlgo.image( script["constant"]["out"], viewName = "default" )
				c1Hash = GafferImage.ImageAlgo.imageHash( script["constant"]["out"], viewName = "default" )

			self.assertEqual( c1, t )
			self.assertEqual( c1Hash, tHash )
			self.assertNotEqual( c0, c1 )
			self.assertNotEqual( c0Hash, c1Hash )

	def testTimeContext( self ) :

		script = Gaffer.ScriptNode()
		script["constant"] = GafferImage.Constant()
		script["constant"]["format"].setValue( GafferImage.Format( 1, 1, 1.0 ) )

		script["e"] = Gaffer.Expression()
		script["e"].setExpression( 'parent["constant"]["color"] = imath.Color4f( context["frame"] )' )

		script["timeWarp"] = Gaffer.TimeWarp()
		script["timeWarp"].setup( GafferImage.ImagePlug() )
		script["timeWarp"]["in"].setInput( script["constant"]["out"] )
		script["timeWarp"]["speed"].setValue( 0 )
		script["timeWarp"]["offset"].setValue( 3 )

		script["sampler"] = GafferImage.ImageSampler()
		script["sampler"]["pixel"].setValue( imath.V2f( 0.5, 0.5 ) )
		script["sampler"]["image"].setInput( script["timeWarp"]["out"] )

		self.assertEqual( script["sampler"]["color"].getValue(), imath.Color4f( 3 ) )

		script["e2"] = Gaffer.Expression()
		script["e2"].setExpression( inspect.cleandoc(
			"""
			assert( context.get( "image:channelName", None ) is None )
			assert( context.get( "image:tileOrigin", None ) is None )
			parent["timeWarp"]["offset"] = 5
			"""
		) )

		self.assertEqual( script["sampler"]["color"].getValue(), imath.Color4f( 5 ) )

	def testDisabling( self ) :

		script = Gaffer.ScriptNode()

		script["constant"] = GafferImage.Constant()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( 'parent["constant"]["color"]["r"] = context["frame"]' )

		script["timeWarp"] = Gaffer.TimeWarp()
		script["timeWarp"].setup( GafferImage.ImagePlug() )

		script["timeWarp"]["offset"].setValue( 1 )
		script["timeWarp"]["in"].setInput( script["constant"]["out"] )

		with script.context() :

			c = GafferImage.ImageAlgo.image( script["constant"]["out"], viewName = "default" )
			cHash = GafferImage.ImageAlgo.imageHash( script["constant"]["out"], viewName = "default" )
			t = GafferImage.ImageAlgo.image( script["timeWarp"]["out"], viewName = "default" )
			tHash = GafferImage.ImageAlgo.imageHash( script["timeWarp"]["out"], viewName = "default" )

		self.assertNotEqual( c, t )
		self.assertNotEqual( cHash, tHash )

		script["timeWarp"]["enabled"].setValue( False )

		with script.context() :

			c = GafferImage.ImageAlgo.image( script["constant"]["out"], viewName = "default" )
			cHash = GafferImage.ImageAlgo.imageHash( script["constant"]["out"], viewName = "default" )
			t = GafferImage.ImageAlgo.image( script["timeWarp"]["out"], viewName = "default" )
			tHash = GafferImage.ImageAlgo.imageHash( script["timeWarp"]["out"], viewName = "default" )

		self.assertEqual( c, t )
		self.assertEqual( cHash, tHash )

if __name__ == "__main__":
	unittest.main()
