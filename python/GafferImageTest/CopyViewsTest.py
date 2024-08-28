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

class CopyViewsTest( GafferImageTest.ImageTestCase ) :

	def test( self ) :

		createViews = []

		for i in range(3):
			createViews.append( GafferImage.CreateViews() )
			for j in range(5):
				constant = GafferImage.Constant()
				constant["color"].setValue( imath.Color4f( 0.1 * i, 0.1 * j, 0, 0 ) )
				constant["format"]["displayWindow"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 10 * i, 10 * j) ) )
				name = ""
				if j == 0:
					name = "a"
				elif j == 4:
					name = "b"
				else:
					name = "source%iview%i" % ( i, j )

				createViews[i].addChild( constant )
				view = createViews[i]["views"].next()
				view["name"].setValue( name )
				view["value"].setInput( constant["out"] )

		copyViews = GafferImage.CopyViews()
		copyViews["in"][0].setInput( createViews[0]["out"] )
		copyViews["in"][1].setInput( createViews[1]["out"] )
		copyViews["in"][2].setInput( createViews[2]["out"] )

		self.assertEqual( copyViews["out"].viewNames(), IECore.StringVectorData( [
			"a", "source0view1", "source0view2", "source0view3", "b",
			"source1view1", "source1view2", "source1view3",
			"source2view1", "source2view2", "source2view3"
		] ) )

		self.assertEqual( copyViews["out"].dataWindow( "a" ).max(), imath.V2i( 20, 0 ) )
		self.assertEqual( copyViews["out"].dataWindow( "b" ).max(), imath.V2i( 20, 40 ) )
		self.assertEqual( copyViews["out"].dataWindow( "source0view1" ).max(), imath.V2i( 0, 10 ) )
		self.assertEqual( copyViews["out"].dataWindow( "source1view2" ).max(), imath.V2i( 10, 20 ) )
		self.assertEqual( copyViews["out"].dataWindow( "source2view3" ).max(), imath.V2i( 20, 30 ) )

		copyViews["views"].setValue( "*view2" )

		self.assertEqual( copyViews["out"].viewNames(), IECore.StringVectorData( [
			"a", "source0view1", "source0view2", "source0view3", "b",
			"source1view2", "source2view2",
		] ) )

		copyViews["views"].setValue( "source2*" )

		self.assertEqual( copyViews["out"].viewNames(), IECore.StringVectorData( [
			"a", "source0view1", "source0view2", "source0view3", "b",
			"source2view1", "source2view2", "source2view3"
		] ) )

		copyViews["views"].setValue( "*" )

		createViews[1]["views"][3]["name"].setValue( "default" )
		self.assertEqual( copyViews["out"].viewNames(), IECore.StringVectorData( [
			"a", "source0view1", "source0view2", "source0view3", "b",
			"source1view1", "source1view2", "default",
			"source2view1", "source2view2", "source2view3"
		] ) )

		self.assertEqual( copyViews["out"].dataWindow( "undeclared" ).max(), imath.V2i( 10, 30 ) )

		createViews[2]["views"][2]["name"].setValue( "default" )
		self.assertEqual( copyViews["out"].viewNames(), IECore.StringVectorData( [
			"a", "source0view1", "source0view2", "source0view3", "b",
			"source1view1", "source1view2", "default",
			"source2view1", "source2view3"
		] ) )

		self.assertEqual( copyViews["out"].dataWindow( "undeclared" ).max(), imath.V2i( 20, 20 ) )

		createViews[0]["views"][1]["name"].setValue( "default" )
		self.assertEqual( copyViews["out"].viewNames(), IECore.StringVectorData( [
			"a", "default", "source0view2", "source0view3", "b",
			"source1view1", "source1view2",
			"source2view1", "source2view3"
		] ) )
		self.assertEqual( copyViews["out"].dataWindow( "undeclared" ).max(), imath.V2i( 20, 20 ) )

		copyViews["views"].setValue( "*view*" )
		self.assertEqual( copyViews["out"].viewNames(), IECore.StringVectorData( [
			"a", "default", "source0view2", "source0view3", "b",
			"source1view1", "source1view2",
			"source2view1", "source2view3"
		] ) )
		self.assertEqual( copyViews["out"].dataWindow( "undeclared" ).max(), imath.V2i( 0, 10 ) )

if __name__ == "__main__":
	unittest.main()
