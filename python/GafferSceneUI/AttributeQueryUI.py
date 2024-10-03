#########################################################################
#
#  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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
import GafferScene
import GafferUI
import imath

from GafferSceneUI._GafferSceneUI import __showSetupMenu as showSetupMenu

class _SetupButton( GafferUI.Widget ) :

	def __init__( self, node ) :

		self.__node = node
		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.Widget.__init__( self, self.__row )

		with self.__row :

				GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

				menuButton = GafferUI.Button( image = "plus.png", hasFrame = False )
				menuButton.clickedSignal().connect( Gaffer.WeakMethod( self.__showMenu ) )

				GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

		node.childAddedSignal().connect( Gaffer.WeakMethod( self.__updateVisibility ) )
		node.childRemovedSignal().connect( Gaffer.WeakMethod( self.__updateVisibility ) )

		self.__updateVisibility()

	def __showMenu( self, *args, **kwargs ):

		showSetupMenu( self.__node )

	def __updateVisibility( self, *args, **kwargs ) :

		# We can't use `self.setVisible()` because PlugLayout uses it to implement visibility activators
		self.__row.setVisible( not ( self.__node.isSetup() ) )

Gaffer.Metadata.registerNode(

	GafferScene.AttributeQuery,

	"description",
	"""
	Query a particular location in a scene and outputs attribute.
	""",

	"layout:customWidget:setupButton:widgetType", "GafferSceneUI.AttributeQueryUI._SetupButton",
	"layout:customWidget:setupButton:section", "Settings",
	"layout:customWidget:setupButton:index", -1,

	"noduleLayout:customGadget:setupButton:gadgetType", "GafferSceneUI.AttributeQueryUI.PlugAdder",
	"noduleLayout:customGadget:setupButton:section", "bottom",

	plugs = {

		"scene" : [

			"description",
			"""
			The scene to query the attribute for.
			"""

		],

		"location" : [

			"description",
			"""
			The location within the scene to query the attribute at.
			> Note : If the location does not exist then the query will not be
			> performed and all outputs will be set to their default values.
			""",

			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",
			"scenePathPlugValueWidget:scene", "scene",
			"nodule:type", ""

		],

		"attribute" : [

			"description",
			"""
			The name of the attribute to query.
			> Note : If the attribute does not exist then the query will not be
			> performed and all outputs will be set to their default values.
			""",

			"nodule:type", ""

		],

		"inherit" : [

			"description",
			"""
			Should inherited attributes or be considered or not.
			""",

			"nodule:type", ""

		],

		"default" : [

			"description",
			"""
			Default value to use if attribute or location does not exist.
			"""

		],

		"exists" : [

			"description",
			"""
			Outputs true if both attribute and location exist, otherwise false.
			""",

			"layout:section", "Settings.Outputs"

		],

		"value" : [

			"description",
			"""
			Outputs the value of the specified attribute.
			""",

			"layout:section", "Settings.Outputs"

		],

	}
)
