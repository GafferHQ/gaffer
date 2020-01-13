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
import inspect
import unittest
import imath

import IECore

import Gaffer
import GafferImage
import GafferImageTest

class GradeTest( GafferImageTest.ImageTestCase ) :

	checkerFile = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker.exr" )

	# Test that when gamma == 0 that the coresponding channel isn't modified.
	def testChannelEnable( self ) :
		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.checkerFile )

		# Create a grade node and save the hash of a tile from each channel.
		grade = GafferImage.Grade()
		grade["in"].setInput(i["out"])
		grade["gain"].setValue( imath.Color3f( 2., 2., 2. ) )
		hashRed = grade["out"].channelData( "R", imath.V2i( 0 ) ).hash()
		hashGreen = grade["out"].channelData( "G", imath.V2i( 0 ) ).hash()
		hashBlue = grade["out"].channelData( "B", imath.V2i( 0 ) ).hash()

		# Now we set the gamma on the green channel to 0 which should disable it's output.
		# The red and blue channels should still be graded as before.
		grade["gamma"].setValue( imath.Color3f( 1., 0., 1. ) )
		hashRed2 = grade["out"].channelData( "R", imath.V2i( 0 ) ).hash()
		hashGreen2 = grade["out"].channelData( "G", imath.V2i( 0 ) ).hash()
		hashBlue2 = grade["out"].channelData( "B", imath.V2i( 0 ) ).hash()

		self.assertEqual( hashRed, hashRed2 )
		self.assertNotEqual( hashGreen, hashGreen2 )
		self.assertEqual( hashBlue, hashBlue2 )

	def testChannelDataHashes( self ) :
		# Create a grade node and save the hash of a tile from each channel.
		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.checkerFile )

		grade = GafferImage.Grade()
		grade["in"].setInput(i["out"])
		grade["gain"].setValue( imath.Color3f( 2., 2., 2. ) )

		h1 = grade["out"].channelData( "R", imath.V2i( 0 ) ).hash()
		h2 = grade["out"].channelData( "R", imath.V2i( GafferImage.ImagePlug().tileSize() ) ).hash()
		self.assertNotEqual( h1, h2 )

		# Test that two tiles within the same image have the same hash when disabled.
		grade["enabled"].setValue(False)
		h1 = grade["out"].channelData( "R", imath.V2i( 0 ) ).hash()
		h2 = grade["out"].channelData( "R", imath.V2i( GafferImage.ImagePlug().tileSize() ) ).hash()
		self.assertNotEqual( h1, h2 )

	def testEnableBehaviour( self ) :

		g = GafferImage.Grade()
		self.assertTrue( g.enabledPlug().isSame( g["enabled"] ) )
		self.assertTrue( g.correspondingInput( g["out"] ).isSame( g["in"] ) )
		self.assertEqual( g.correspondingInput( g["in"] ), None )
		self.assertEqual( g.correspondingInput( g["enabled"] ), None )
		self.assertEqual( g.correspondingInput( g["gain"] ), None )

	def testPassThrough( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.checkerFile )

		g = GafferImage.Grade()
		g["in"].setInput( i["out"] )
		g["gain"].setValue( imath.Color3f( 2., 2., 2. ) )

		self.assertEqual( i["out"]["format"].hash(), g["out"]["format"].hash() )
		self.assertEqual( i["out"]["dataWindow"].hash(), g["out"]["dataWindow"].hash() )
		self.assertEqual( i["out"]["metadata"].hash(), g["out"]["metadata"].hash() )
		self.assertEqual( i["out"]["channelNames"].hash(), g["out"]["channelNames"].hash() )

		self.assertEqual( i["out"]["format"].getValue(), g["out"]["format"].getValue() )
		self.assertEqual( i["out"]["dataWindow"].getValue(), g["out"]["dataWindow"].getValue() )
		self.assertEqual( i["out"]["metadata"].getValue(), g["out"]["metadata"].getValue() )
		self.assertEqual( i["out"]["channelNames"].getValue(), g["out"]["channelNames"].getValue() )

	def testChannelDataHashesAreIndependent( self ) :

		# changing only one channel of any of the grading plugs should not
		# affect the hash of any of the other channels.

		s = Gaffer.ScriptNode()
		s["c"] = GafferImage.Constant()
		s["g"] = GafferImage.Grade()
		s["g"]["in"].setInput( s["c"]["out"] )

		channelNames = ( "R", "G", "B" )
		for channelIndex, channelName in enumerate( channelNames ) :
			for plugName in ( "blackPoint", "whitePoint", "lift", "gain", "multiply", "offset", "gamma" ) :
				oldChannelHashes = [ s["g"]["out"].channelDataHash( c, imath.V2i( 0 ) ) for c in channelNames ]
				s["g"][plugName][channelIndex].setValue( s["g"][plugName][channelIndex].getValue() + 0.01 )
				newChannelHashes = [ s["g"]["out"].channelDataHash( c, imath.V2i( 0 ) ) for c in channelNames ]
				for hashChannelIndex in range( 0, 3 ) :
					if channelIndex == hashChannelIndex :
						self.assertNotEqual( oldChannelHashes[hashChannelIndex], newChannelHashes[hashChannelIndex] )
					else :
						self.assertEqual( oldChannelHashes[hashChannelIndex], newChannelHashes[hashChannelIndex] )

	def testChannelPassThrough( self ) :

		# we should get a perfect pass-through without cache duplication when
		# all the colour plugs are at their defaults and clamping is disabled

		s = Gaffer.ScriptNode()
		s["c"] = GafferImage.Constant()
		s["g"] = GafferImage.Grade()
		s["g"]["blackClamp"].setValue( False )
		s["g"]["in"].setInput( s["c"]["out"] )

		for channelName in ( "R", "G", "B", "A" ) :
			self.assertEqual(
				s["g"]["out"].channelDataHash( channelName, imath.V2i( 0 ) ),
				s["c"]["out"].channelDataHash( channelName, imath.V2i( 0 ) ),
			)

			c = Gaffer.Context( s.context() )
			c["image:channelName"] = channelName
			c["image:tileOrigin"] = imath.V2i( 0 )
			with c :
				self.assertTrue(
					s["g"]["out"]["channelData"].getValue( _copy=False ).isSame(
						s["c"]["out"]["channelData"].getValue( _copy=False )
					)
				)

	def testAllChannels( self ):
		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( 50, 50, 1.0 ) )
		c["color"].setValue( imath.Color4f( 0.125, 0.25, 0.5, 0.75 ) )

		s = GafferImage.Shuffle()
		s["channels"].addChild( GafferImage.Shuffle.ChannelPlug( 'customChannel', '__white' ) )
		s["in"].setInput( c["out"] )

		g = GafferImage.Grade()
		g["in"].setInput( s["out"] )

		def sample( x, y ) :
			redSampler = GafferImage.Sampler( g["out"], "R", g["out"]["format"].getValue().getDisplayWindow() )
			greenSampler = GafferImage.Sampler( g["out"], "G", g["out"]["format"].getValue().getDisplayWindow() )
			blueSampler = GafferImage.Sampler( g["out"], "B", g["out"]["format"].getValue().getDisplayWindow() )
			alphaSampler = GafferImage.Sampler( g["out"], "A", g["out"]["format"].getValue().getDisplayWindow() )
			customSampler = GafferImage.Sampler( g["out"], "customChannel", g["out"]["format"].getValue().getDisplayWindow() )

			return [
				redSampler.sample( x, y ),
				greenSampler.sample( x, y ),
				blueSampler.sample( x, y ),
				alphaSampler.sample( x, y ),
				customSampler.sample( x, y )
			]

		self.assertEqual( sample( 25, 25 ), [ 0.125, 0.25, 0.5, 0.75, 1.0 ] )

		g["offset"].setValue( imath.Color4f( 3, 3, 3, 3 ) )
		self.assertEqual( sample( 25, 25 ), [ 3.125, 3.25, 3.5, 0.75, 1.0 ] )

		g["channels"].setValue( IECore.StringVectorData( [ "A" ] ) )
		self.assertEqual( sample( 25, 25 ), [ 0.125, 0.25, 0.5, 3.75, 1.0 ] )

		g["channels"].setValue( IECore.StringVectorData( [ "customChannel" ] ) )
		self.assertEqual( sample( 25, 25 ), [ 0.125, 0.25, 0.5, 0.75, 4.0 ] )

		g["channels"].setValue( IECore.StringVectorData( [ "R", "G", "B", "A", "customChannel" ] ) )
		self.assertEqual( sample( 25, 25 ), [ 3.125, 3.25, 3.5, 3.75, 4.0 ] )

	def testPerLayerExpression( self ) :

		script = Gaffer.ScriptNode()

		script["c1"] = GafferImage.Constant()
		script["c1"]["color"].setValue( imath.Color4f( 1 ) )

		script["c2"] = GafferImage.Constant()
		script["c2"]["color"].setValue( imath.Color4f( 1 ) )
		script["c2"]["layer"].setValue( "B" )

		script["copyChannels"] = GafferImage.CopyChannels()
		script["copyChannels"]["in"][0].setInput( script["c1"]["out"] )
		script["copyChannels"]["in"][1].setInput( script["c2"]["out"] )
		script["copyChannels"]["channels"].setValue( "*" )

		script["grade"] = GafferImage.Grade()
		script["grade"]["in"].setInput( script["copyChannels"]["out"] )
		script["grade"]["channels"].setValue( "*" )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			import GafferImage
			layerName = GafferImage.ImageAlgo.layerName( context["image:channelName" ] )
			parent["grade"]["gain"] = imath.Color4f( 1 if layerName == "B" else 0.5 )
			"""
		) )

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( script["grade"]["out"] )
		sampler["pixel"].setValue( imath.V2f( 10.5 ) )

		sampler["channels"].setValue( IECore.StringVectorData( [ "R", "G", "B", "A" ] ) )
		self.assertEqual( sampler["color"].getValue(), imath.Color4f( 0.5 ) )

		sampler["channels"].setValue( IECore.StringVectorData( [ "B.R", "B.G", "B.B", "B.A" ] ) )
		self.assertEqual( sampler["color"].getValue(), imath.Color4f( 1 ) )

	def testUnpremultiplied( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.checkerFile )

		shuffleAlpha = GafferImage.Shuffle()
		shuffleAlpha["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "channel" ) )
		shuffleAlpha["in"].setInput( i["out"] )
		shuffleAlpha["channels"]["channel"]["out"].setValue( 'A' )
		shuffleAlpha["channels"]["channel"]["in"].setValue( 'R' )

		gradeAlpha = GafferImage.Grade()
		gradeAlpha["in"].setInput( shuffleAlpha["out"] )
		gradeAlpha["channels"].setValue( '[RGBA]' )
		gradeAlpha["offset"].setValue( imath.Color4f( 0, 0, 0, 0.1 ) )

		unpremultipliedGrade = GafferImage.Grade()
		unpremultipliedGrade["in"].setInput( gradeAlpha["out"] )
		unpremultipliedGrade["processUnpremultiplied"].setValue( True )
		unpremultipliedGrade["gamma"].setValue( imath.Color4f( 2, 2, 2, 1.0 ) )

		unpremultiply = GafferImage.Unpremultiply()
		unpremultiply["in"].setInput( gradeAlpha["out"] )

		bareGrade = GafferImage.Grade()
		bareGrade["in"].setInput( unpremultiply["out"] )
		bareGrade["gamma"].setValue( imath.Color4f( 2, 2, 2, 1.0 ) )

		premultiply = GafferImage.Premultiply()
		premultiply["in"].setInput( bareGrade["out"] )

		# Assert that with a non-zero alpha, processUnpremultiplied is identical to:
		# unpremult, grade, and premult
		self.assertImagesEqual( unpremultipliedGrade["out"], premultiply["out"] )


		# Assert that grading alpha to 0 inside the grade still premults at the end correctly
		unpremultipliedGrade["channels"].setValue( '[RGBA]' )
		unpremultipliedGrade["multiply"].setValue( imath.Color4f( 1, 1, 1, 0 ) )

		zeroGrade = GafferImage.Grade()
		zeroGrade["channels"].setValue( '[RGBA]' )
		zeroGrade["in"].setInput( gradeAlpha["out"] )
		zeroGrade["multiply"].setValue( imath.Color4f( 0, 0, 0, 0 ) )

		self.assertImagesEqual( unpremultipliedGrade["out"], zeroGrade["out"] )

		unpremultipliedGrade["multiply"].setValue( imath.Color4f( 1, 1, 1, 1 ) )

		# Assert that when input alpha is zero, processUnpremultiplied doesn't affect the result

		gradeAlpha["multiply"].setValue( imath.Color4f( 1, 1, 1, 0.0 ) )
		gradeAlpha["offset"].setValue( imath.Color4f( 0, 0, 0, 0.0 ) )

		defaultGrade = GafferImage.Grade()
		defaultGrade["in"].setInput( gradeAlpha["out"] )
		defaultGrade["gamma"].setValue( imath.Color4f( 2, 2, 2, 1.0 ) )

		self.assertImagesEqual( unpremultipliedGrade["out"], defaultGrade["out"] )

