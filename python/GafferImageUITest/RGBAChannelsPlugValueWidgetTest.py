##########################################################################
#
#  Copyright (c) 2026, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferUI
import GafferUITest
import GafferImage
import GafferImageUI

class RGBAChannelsPlugValueWidgetTest( GafferUITest.TestCase ) :

	@staticmethod
	def __script( layers ) :

		script = Gaffer.ScriptNode()
		script["constant"] = GafferImage.Constant()

		script["shuffle"] = GafferImage.Shuffle()
		script["shuffle"]["in"].setInput( script["constant"]["out"] )
		for layer in layers :
			for channel in "RGBA" :
				script["shuffle"]["shuffles"].addChild( Gaffer.ShufflePlug( channel, f"{layer}.{channel}" ) )

		script["stats"] = GafferImage.ImageStats()
		script["stats"]["in"].setInput( script["shuffle"]["out"] )

		return script

	def testSearchable( self ) :

		script = self.__script( [] )

		widget = GafferImageUI.RGBAChannelsPlugValueWidget( script["stats"]["channels"] )
		self.assertTrue( widget._RGBAChannelsPlugValueWidget__menuButton.getMenu().searchable() )

		Gaffer.Metadata.registerValue( script["stats"]["channels"], "rgbaChannelsPlugValueWidget:searchable", False )
		widget = GafferImageUI.RGBAChannelsPlugValueWidget( script["stats"]["channels"] )
		self.assertFalse( widget._RGBAChannelsPlugValueWidget__menuButton.getMenu().searchable() )

	def testSearchTextIsFullLayerName( self ) :

		script = self.__script( [ "diffuse", "diffuse.direct", "specular.indirect" ] )

		widget = GafferImageUI.RGBAChannelsPlugValueWidget( script["stats"]["channels"] )
		GafferUITest.PlugValueWidgetTest.waitForUpdate( widget )

		searchTexts = {
			path : item.searchText
			for path, item in widget._menuDefinition().items()
		}

		self.assertEqual(
			searchTexts,
			{
				"/RGBA" : "RGBA",
				"/diffuse" : "diffuse",
				"/diffuse/direct" : "diffuse.direct",
				"/specular/indirect" : "specular.indirect",
			}
		)

	def testNoChannelsItemIsNotSearchable( self ) :

		script = Gaffer.ScriptNode()
		script["stats"] = GafferImage.ImageStats()

		widget = GafferImageUI.RGBAChannelsPlugValueWidget( script["stats"]["channels"] )
		GafferUITest.PlugValueWidgetTest.waitForUpdate( widget )

		items = widget._menuDefinition().items()
		self.assertEqual( [ path for path, item in items ], [ "/No channels available" ] )
		self.assertIs( items[0][1].searchable, False )

if __name__ == "__main__":
	unittest.main()
