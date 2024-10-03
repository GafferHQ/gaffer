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
import GafferTest
import GafferUI
import GafferUITest
import GafferImage
import GafferImageUI

class ImageViewTest( GafferUITest.TestCase ) :

	def testFactory( self ) :

		script = Gaffer.ScriptNode()
		script["image"] = GafferImage.Constant()
		view = GafferUI.View.create( script["image"]["out"] )

		self.assertTrue( isinstance( view, GafferImageUI.ImageView ) )
		self.assertTrue( view["in"].getInput().isSame( script["image"]["out"] ) )

	def testDeriving( self ) :

		class MyView( GafferImageUI.ImageView ) :

			def __init__( self, scriptNode ) :

				GafferImageUI.ImageView.__init__( self, scriptNode )

				converter = Gaffer.Node()
				converter["in"] = Gaffer.StringPlug()
				converter["out"] = GafferImage.ImagePlug( direction = Gaffer.Plug.Direction.Out )
				converter["text"] = GafferImage.Text()
				converter["text"]["text"].setInput( converter["in"] )
				converter["out"].setInput( converter["text"]["out"] )

				self._insertConverter( converter )

		GafferUI.View.registerView( GafferTest.StringInOutNode, "out", MyView )

		script = Gaffer.ScriptNode()
		script["string"] = GafferTest.StringInOutNode()

		view = GafferUI.View.create( script["string"]["out"] )
		self.assertTrue( isinstance( view, MyView ) )
		self.assertTrue( view["in"].getInput().isSame( script["string"]["out"] ) )
		self.assertTrue( isinstance( view["in"], Gaffer.StringPlug ) )
		view["displayTransform"]["exposure"].setValue( 1 )
		view["displayTransform"]["gamma"].setValue( 0.5 )

	def testImageGadget( self ) :

		script = Gaffer.ScriptNode()
		view = GafferImageUI.ImageView( script )
		self.assertIsInstance( view.imageGadget(), GafferImageUI.ImageGadget )
		self.assertTrue( view.viewportGadget().isAncestorOf( view.imageGadget() ) )

if __name__ == "__main__":
	unittest.main()
