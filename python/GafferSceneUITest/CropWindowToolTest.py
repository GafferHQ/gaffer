##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Cinesite VFX Ltd nor the names of
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

import Gaffer
import GafferImage
import GafferScene
import GafferUI
import GafferUITest
import GafferSceneUI

class CropWindowToolTest( GafferUITest.TestCase ) :

	def testSceneViewStatus( self ) :

		camera = GafferScene.Camera()

		view = GafferUI.View.create( camera["out"] )

		tool = GafferSceneUI.CropWindowTool( view )
		tool["active"].setValue( True )

		# Presently, crop window tool updates are coupled to `preRender`, so we
		# need to actually show the View before we can verify our behaviour.

		with GafferUI.Window() as window :
			GafferUI.GadgetWidget( view.viewportGadget() )
		window.setVisible( True )

		# View camera isn't a real camera

		self.waitForIdle( 1 )
		self.assertEqual( tool.status(), "Error: No applicable crop window for this view" )

		# Working camera, no node to edit

		view["camera"]["lookThroughCamera"].setValue( "/camera" )
		view["camera"]["lookThroughEnabled"].setValue( True )

		self.waitForIdle( 1 )
		self.assertEqual( tool.status(), "Error: No crop window found. Insert a <b>StandardOptions</b> node." )

		# Editable

		options = GafferScene.StandardOptions()
		options["in"].setInput( camera["out"] )
		view["in"].setInput( options["out"] )

		self.waitForIdle( 1 )
		self.assertEqual( tool.status(), "Info: Editing <b>StandardOptions.options.renderCropWindow.value</b>" )

		# Locked value plug

		Gaffer.MetadataAlgo.setReadOnly( options["options"]["renderCropWindow"]["value"], True )

		self.waitForIdle( 1 )
		self.assertEqual( tool.status(), "Warning: <b>StandardOptions.options.renderCropWindow.value</b> is locked" )

		# Locked/off enabled plug

		Gaffer.MetadataAlgo.setReadOnly( options["options"]["renderCropWindow"]["value"], False )
		options["options"]["renderCropWindow"]["enabled"].setValue( False )
		Gaffer.MetadataAlgo.setReadOnly( options["options"]["renderCropWindow"]["enabled"], True )

		self.waitForIdle( 1 )
		self.assertEqual( tool.status(), "Warning: <b>StandardOptions.options.renderCropWindow.value</b> isn't editable" )

		# Check status across visible/invisible overlay transitions (this is
		# really testing one of the gnarly parts of the status implementation
		# that has caused trouble before, until we can properly refactor the tool).

		view["camera"]["lookThroughEnabled"].setValue( False )

		self.waitForIdle( 1 )
		self.assertEqual( tool.status(), "Error: No applicable crop window for this view" )

		view["camera"]["lookThroughEnabled"].setValue( True )

		self.waitForIdle( 1 )
		self.assertEqual( tool.status(), "Warning: <b>StandardOptions.options.renderCropWindow.value</b> isn't editable" )

	def testImageViewStatus( self ) :

		script = Gaffer.ScriptNode()
		script["image"] = GafferImage.ImageReader()

		view = GafferUI.View.create( script["image"]["out"] )

		tool = GafferSceneUI.CropWindowTool( view )
		tool["active"].setValue( True )

		# Presently, crop window tool updates are coupled to `preRender`, so we
		# need to actually show the View before we can verify our behaviour.

		with GafferUI.Window() as window :
			GafferUI.GadgetWidget( view.viewportGadget() )
		window.setVisible( True )

		# Check process exceptions

		script["image"]["fileName"].setValue( "/i/do/not/exist.exr" )

		self.waitForIdle( 1 )
		self.assertEqual( tool.status(), "Error: image.__oiioReader.out.format : OpenImageIOReader : Could not create ImageInput : Could not open file \"/i/do/not/exist.exr\"" )

		# Missing metadata

		script["image"]["fileName"].setValue( "${GAFFER_ROOT}/resources/images/macaw.exr" )

		self.waitForIdle( 1 )
		self.assertEqual( tool.status(), "Error: No <b>gaffer:sourceScene</b> metadata in image" )

		script["meta"] = GafferImage.ImageMetadata()
		script["meta"]["metadata"].addChild( Gaffer.NameValuePlug( "gaffer:sourceScene", "options.out", True, "member1" ) )
		script["meta"]["in"].setInput( script["image"]["out"] )

		script["options"] = GafferScene.StandardOptions()

		view["in"].setInput( script["meta"]["out"] )

		# Valid options path

		self.waitForIdle( 1 )
		self.assertEqual( tool.status(), "Info: Editing <b>options.options.renderCropWindow.value</b>" )


if __name__ == "__main__":
	unittest.main()
