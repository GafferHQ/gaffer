##########################################################################
#
#  Copyright (c) 2022, Image Engine Design Inc. All rights reserved.
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
import inspect
import os

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class CreateViewsTest( GafferImageTest.ImageTestCase ) :

	__rgbFilePath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/rgb.100x100.exr" )
	__stereoFilePath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/channelTestMultiViewPartPerView.exr" )

	def test( self ) :

		script = Gaffer.ScriptNode()
		createViews = GafferImage.CreateViews()
		script.addChild( createViews )

		# Default views added by the UI
		createViews["views"].addChild( Gaffer.NameValuePlug( "left", GafferImage.ImagePlug(), True, "view0", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		createViews["views"].addChild( Gaffer.NameValuePlug( "right", GafferImage.ImagePlug(), True, "view1", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		reader = GafferImage.ImageReader()
		script.addChild( reader )
		reader["fileName"].setValue( self.__rgbFilePath )
		constant1 = GafferImage.Constant()
		script.addChild( constant1 )
		constant1["color"].setValue( imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )
		constant1["format"]["displayWindow"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 512 ) ) )
		constant2 = GafferImage.Constant()
		script.addChild( constant2 )
		constant2["color"].setValue( imath.Color4f( 0.3, 0.4, 0.5, 0.6 ) )
		constant2["format"]["displayWindow"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 100 ) ) )

		createViews["views"]["view0"]["value"].setInput( reader["out"] )
		createViews["views"]["view1"]["value"].setInput( constant1["out"] )

		self.assertEqual( createViews["out"].viewNames(), IECore.StringVectorData( [ "left", "right" ] ) )
		self.assertEqual(
			GafferImage.ImageAlgo.image( createViews["out"], "left" ),
			GafferImage.ImageAlgo.image( reader["out"], "default" )
		)
		self.assertEqual(
			GafferImage.ImageAlgo.image( createViews["out"], "right" ),
			GafferImage.ImageAlgo.image( constant1["out"], "default" )
		)

		serialised = script.serialise()
		deserialise = Gaffer.ScriptNode()
		deserialise.execute( serialised )

		self.assertImagesEqual( createViews["out"], deserialise["CreateViews"]["out"] )


		createViews["views"].addChild( Gaffer.NameValuePlug( "custom", GafferImage.ImagePlug(), True, "view1", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		createViews["views"]["view2"]["name"].setValue( "blah" )
		createViews["views"]["view2"]["value"].setInput( constant2["out"] )

		self.assertEqual( createViews["out"].viewNames(), IECore.StringVectorData( [ "left", "right", "blah" ] ) )
		self.assertEqual(
			GafferImage.ImageAlgo.image( createViews["out"], "left" ),
			GafferImage.ImageAlgo.image( reader["out"], "default" )
		)
		self.assertEqual(
			GafferImage.ImageAlgo.image( createViews["out"], "right" ),
			GafferImage.ImageAlgo.image( constant1["out"], "default" )
		)
		self.assertEqual(
			GafferImage.ImageAlgo.image( createViews["out"], "blah" ),
			GafferImage.ImageAlgo.image( constant2["out"], "default" )
		)

		serialised = script.serialise()
		deserialise = Gaffer.ScriptNode()
		deserialise.execute( serialised )

		self.assertImagesEqual( createViews["out"], deserialise["CreateViews"]["out"] )

		# Test enable/disable
		createViews["views"]["view0"]["enabled"].setValue( False )
		self.assertEqual( createViews["out"].viewNames(), IECore.StringVectorData( [ "right", "blah" ] ) )
		with self.assertRaisesRegex( Gaffer.ProcessException, ".*CreateViews : Not outputting view \"left\"."):
			createViews["out"].format( "left" )
		createViews["views"]["view0"]["enabled"].setValue( True )
		self.assertEqual( createViews["out"].viewNames(), IECore.StringVectorData( [ "left", "right", "blah" ] ) )

		# Test duplicate names
		self.assertEqual(
			GafferImage.ImageAlgo.image( createViews["out"], "left" ),
			GafferImage.ImageAlgo.image( reader["out"], "default" )
		)
		createViews["views"]["view2"]["name"].setValue( "left" )
		self.assertEqual(
			GafferImage.ImageAlgo.image( createViews["out"], "left" ),
			GafferImage.ImageAlgo.image( constant2["out"], "default" )
		)
		self.assertEqual( createViews["out"].viewNames(), IECore.StringVectorData( [ "left", "right" ] ) )

		# Test default view supplies defaults
		createViews["views"]["view0"]["name"].setValue( "default" )
		self.assertEqual( createViews["out"].viewNames(), IECore.StringVectorData( [ "default", "right", "left" ] ) )
		self.assertEqual(
			GafferImage.ImageAlgo.image( createViews["out"], "default" ),
			GafferImage.ImageAlgo.image( reader["out"], "default" )
		)
		self.assertEqual(
			GafferImage.ImageAlgo.image( createViews["out"], "undeclared" ),
			GafferImage.ImageAlgo.image( reader["out"], "default" )
		)
		createViews["views"]["view2"]["name"].setValue( "default" )
		self.assertEqual(
			GafferImage.ImageAlgo.image( createViews["out"], "undeclared" ),
			GafferImage.ImageAlgo.image( constant2["out"], "default" )
		)
		createViews["views"]["view2"]["name"].setValue( "blah" )

		# Test removing view
		del createViews["views"]["view0"]
		self.assertEqual( createViews["out"].viewNames(), IECore.StringVectorData( [ "right", "blah" ] ) )
		self.assertEqual(
			GafferImage.ImageAlgo.image( createViews["out"], "right" ),
			GafferImage.ImageAlgo.image( constant1["out"], "default" )
		)
		self.assertEqual(
			GafferImage.ImageAlgo.image( createViews["out"], "blah" ),
			GafferImage.ImageAlgo.image( constant2["out"], "default" )
		)

		serialised = script.serialise()
		deserialise = Gaffer.ScriptNode()
		deserialise.execute( serialised )

		self.assertImagesEqual( createViews["out"], deserialise["CreateViews"]["out"] )

		# Test error for multiview inputs
		stereoReader = GafferImage.ImageReader()
		script.addChild( stereoReader )
		stereoReader["fileName"].setValue( self.__stereoFilePath )
		createViews["views"][0]["value"].setInput( stereoReader["out"] )

		with self.assertRaisesRegex( Gaffer.ProcessException, ".*CreateViews : Inputs must have just a default view."):
			createViews["out"].format( "right" )

	def testInputToExpressionDrivingEnabledPlug( self ) :

		# This is a distilled version of a production node network in which the
		# `enabled` plug on one ImageNode was driven by an expression querying
		# the existence of channels in another image.

		script = Gaffer.ScriptNode()

		script["checkerboard"] = GafferImage.Checkerboard()

		# `default` view with RGBA channels, and `notDefault` view with no channels
		script["createViews"] = GafferImage.CreateViews()
		script["createViews"]["views"].addChild( Gaffer.NameValuePlug( "default", GafferImage.ImagePlug(), True, "view0", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		script["createViews"]["views"].addChild( Gaffer.NameValuePlug( "notDefault", GafferImage.ImagePlug(), True, "view1", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		script["createViews"]["views"][0]["value"].setInput( script["checkerboard"]["out"] )
		self.assertEqual( script["createViews"]["out"].channelNames( "default" ), IECore.StringVectorData( [ "R", "G", "B", "A" ] ) )
		self.assertEqual( script["createViews"]["out"].channelNames( "notDefault" ), IECore.StringVectorData() )

		script["constant"] = GafferImage.Constant()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			parent["constant"]["enabled"] = bool( parent["createViews"]["out"]["channelNames"] )
			"""
		) )

		# The `viewNames()` call removes `image:viewName` from the context, and the `enabled` plug
		# is used as part of the subsequent compute. This means that `createViews.out.channelNames`
		# will be queried by the expression in a context without `image:viewName`. For backwards
		# compatibility, we want this to fall back to querying the default view.
		self.assertEqual( script["constant"]["out"].viewNames(), GafferImage.ImagePlug.defaultViewNames() )
		self.assertTrue( script["constant"]["enabled"].getValue() )

		with Gaffer.Context() as c :
			# It's irrelevant if we specify the view explicitly, because again `image:viewName` is removed.
			c["image:viewName"] = "notDefault"
			self.assertEqual( script["constant"]["out"].viewNames(), GafferImage.ImagePlug.defaultViewNames() )
			# Although the `enabled` plug itself does see the new context, so the node is disabled
			# for this particular view.
			self.assertFalse( script["constant"]["enabled"].getValue() )

if __name__ == "__main__":
	unittest.main()
