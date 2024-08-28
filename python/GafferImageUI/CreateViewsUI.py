###########################################################################
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

import Gaffer
import GafferImage
import GafferUI
import imath

## A function suitable as the postCreator in a NodeMenu.append() call. It
# sets up the default "left" and "right" views
def postCreate( node, menu ) :

	node["views"].resize( 2 )
	node["views"][0]["name"].setValue( "left" )
	node["views"][1]["name"].setValue( "right" )

Gaffer.Metadata.registerNode(

	GafferImage.CreateViews,

	"description",
	"""
	Creates a multi-view image by combining multiple input images.
	""",

	plugs = {

		"views" : [
			"description",
			"Views to add.  In the case of multiple views with the same name, the last one will override.",

			"nodule:type", "GafferUI::CompoundNodule",
			"noduleLayout:spacing", 2.0,
			"noduleLayout:customGadget:addButton:gadgetType", "",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:customWidget:footer:widgetType", "GafferImageUI.CreateViewsUI._ViewsFooter",
			"layout:customWidget:footer:index", -1,

		],

		"views.*" : [

			"nodule:type", "GafferUI::CompoundNodule",
			"deletable", True,

		],

		"views.*.name" : [
			"description",
			"""
			The name of the view to be created from this input. Usually "left" or "right" for a
			stereo workflow, but can be any name, allowing arbitrary numbers of views to be created
			in a single image stream.
			""",

			"nodule:type", "",

		],

		"views.*.enabled" : [
			"description",
			"""
			Enables this view.
			""",

			"nodule:type", "",

		],

		"views.*.value" : [
			"description",
			"""
			Provides the image to be used to create this view. The connected image should not itself
			be a multi-view image.
			""",

			"plugValueWidget:type", "GafferUI.ConnectionPlugValueWidget",
			"noduleLayout:label", lambda plug : plug.parent()["name"].getValue(),

		],

	}

)

class _ViewsFooter( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.PlugValueWidget.__init__( self, row, plug )

		with row :

			GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

			self.__button = GafferUI.Button( image = "plus.png", hasFrame = False )
			self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ), scoped = False )

			GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

	def _updateFromEditable( self ) :

		self.__button.setEnabled( self._editable() )

	def __buttonClicked( self, widget ) :

		plug = Gaffer.NameValuePlug( "custom", GafferImage.ImagePlug(), True, "view0", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().addChild( plug )
