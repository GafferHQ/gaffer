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
import os

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class SelectViewTest( GafferImageTest.ImageTestCase ) :

	__rgbFilePath = Gaffer.rootPath() / "python" / "GafferImageTest" / "images" / "rgb.100x100.exr"

	def test( self ) :


		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( self.__rgbFilePath )
		constant1 = GafferImage.Constant()
		constant1["color"].setValue( imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )
		constant1["format"]["displayWindow"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 512 ) ) )
		constant2 = GafferImage.Constant()
		constant2["color"].setValue( imath.Color4f( 0.3, 0.4, 0.5, 0.6 ) )
		constant2["format"]["displayWindow"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 100 ) ) )

		createViews = GafferImage.CreateViews()

		createViews["views"].addChild( Gaffer.NameValuePlug( "left", GafferImage.ImagePlug(), True, "view0", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		createViews["views"].addChild( Gaffer.NameValuePlug( "right", GafferImage.ImagePlug(), True, "view1", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		createViews["views"].addChild( Gaffer.NameValuePlug( "default", GafferImage.ImagePlug(), True, "view2", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		createViews["views"]["view0"]["value"].setInput( reader["out"] )
		createViews["views"]["view1"]["value"].setInput( constant1["out"] )
		createViews["views"]["view2"]["value"].setInput( constant2["out"] )

		createViews["views"]["view2"]["enabled"].setValue( False )

		selectView = GafferImage.SelectView()
		selectView["in"].setInput( createViews["out"] )


		self.assertEqual( selectView["out"].viewNames(), IECore.StringVectorData( [ "default" ] ) )
		self.assertEqual(
			GafferImage.ImageAlgo.image( selectView["out"], "default" ),
			GafferImage.ImageAlgo.image( reader["out"], "default" )
		)

		selectView["view"].setValue( "right" )
		self.assertEqual(
			GafferImage.ImageAlgo.image( selectView["out"], "default" ),
			GafferImage.ImageAlgo.image( constant1["out"], "default" )
		)

		selectView["view"].setValue( "undeclared" )
		with self.assertRaisesRegex( Gaffer.ProcessException, ".*View does not exist \"undeclared\""):
			selectView["out"].format()

		createViews["views"]["view2"]["enabled"].setValue( True )

		self.assertEqual( selectView["out"].viewNames(), IECore.StringVectorData( [ "default" ] ) )
		selectView["view"].setValue( "left" )
		self.assertEqual(
			GafferImage.ImageAlgo.image( selectView["out"], "default" ),
			GafferImage.ImageAlgo.image( reader["out"], "default" )
		)

		selectView["view"].setValue( "right" )
		self.assertEqual(
			GafferImage.ImageAlgo.image( selectView["out"], "default" ),
			GafferImage.ImageAlgo.image( constant1["out"], "default" )
		)

		selectView["view"].setValue( "default" )
		self.assertEqual(
			GafferImage.ImageAlgo.image( selectView["out"], "default" ),
			GafferImage.ImageAlgo.image( constant2["out"], "default" )
		)

		selectView["view"].setValue( "undeclared" )
		self.assertEqual(
			GafferImage.ImageAlgo.image( selectView["out"], "default" ),
			GafferImage.ImageAlgo.image( constant2["out"], "default" )
		)


if __name__ == "__main__":
	unittest.main()
