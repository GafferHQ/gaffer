##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

import imath

import Gaffer
import GafferUI
import GafferSceneUI

Gaffer.Metadata.registerNode(

	GafferSceneUI.ImageSelectionTool,

	"description",
	"""
	Tool for selecting objects based on image data.  Requires one of the following :

	- An `id` image layer with associated render manifest (enabled using the StandardOptions node).
	- An ObjectID Cryptomatte image.
	- An `instanceID` image layer.

	Supports the same interactions as the 3D scene selection tool:

	- Click or drag to set selection
	- Shift-click or shift-drag to add to selection
	- Drag and drop selected objects
		- Drag to Python Editor to get their names
		- Drag to PathFilter or Set node to add/remove their paths
	""",

	"viewer:shortCut", "Q",
	"order", 1,
	"viewer:shouldAutoActivate", False,

	"nodeToolbar:bottom:type", "GafferUI.StandardNodeToolbar.bottom",

	"toolbarLayout:customWidget:SelectionWidget:widgetType", "GafferSceneUI.ImageSelectionToolUI._StatusWidget",
	"toolbarLayout:customWidget:SelectionWidget:section", "Bottom",

	"toolbarLayout:customWidget:LeftSpacer:widgetType", "GafferSceneUI.ImageSelectionToolUI._ToolOverlayInsetSpacer",
	"toolbarLayout:customWidget:LeftSpacer:section", "Bottom",
	"toolbarLayout:customWidget:LeftSpacer:index", 0,

	"toolbarLayout:customWidget:RightSpacer:widgetType", "GafferSceneUI.ImageSelectionToolUI._ToolOverlayInsetSpacer",
	"toolbarLayout:customWidget:RightSpacer:section", "Bottom",
	"toolbarLayout:customWidget:RightSpacer:index", -1,

	plugs = {

		"active" : {

			"boolPlugValueWidget:image" : "gafferSceneUISelectionTool.png"

		},

		"selectMode" : {

			"description" :
			"""
			The standard mode selects locations based on an `id` layer with a corresponding manifest.
			`Instance` mode instead picks instance ids based on an `instanceID` layer ( this will only
			contain information for encapsulated instancers, which don't pass multiple locations to the
			renderer, but do set up special instance id information ).
			""",

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"preset:Standard" : "standard",
			"preset:Instance" : "instance",

			"label" : "Select",

			"toolbarLayout:section" : "Bottom",
			"toolbarLayout:width" : 80,

		},

	}

)

class _ToolOverlayInsetSpacer( GafferUI.Spacer ) :

	def __init__( self, imageView, **kw ) :

		GafferUI.Spacer.__init__( self, size = imath.V2i( 40, 0 ), maximumSize = imath.V2i( 40, 0 ) )

class _StatusWidget( GafferUI.Frame ) :

	def __init__( self, tool, **kw ) :

		GafferUI.Frame.__init__( self, borderWidth = 0, **kw )

		self.__tool = tool

		with self :
			with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal, borderWidth = 0 ) :

				self.__infoIcon = GafferUI.Image( "infoSmall.png" )
				self.__errorIcon = GafferUI.Image( "errorSmall.png" )
				self.__warningIcon = GafferUI.Image( "warningSmall.png" )
				GafferUI.Spacer( size = imath.V2i( 4 ), maximumSize = imath.V2i( 4 ) )
				self.__label = GafferUI.Label( "" )
				self.__label.setTextSelectable( True )
				GafferUI.Spacer( size = imath.V2i( 0 ) )

		self.__tool.statusChangedSignal().connect( Gaffer.WeakMethod( self.__update, fallbackResult = None ) )

		self.__update()

	def scriptNode( self ) : # For LazyMethod's `deferUntilPlaybackStops`

		return self.__tool.ancestor( GafferUI.View ).scriptNode()

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __update( self, *unused ) :
		if not self.__tool["active"].getValue() :
			# We're about to be made invisible so all our update
			# would do is cause unnecessary flickering in Qt's
			# redraw.
			return

		status = self.__tool.status()

		state, _, message = status.partition( ":" )

		self.__label.setText( message )

		info = warn = error = False
		if state == "error":
			error = True
		elif state == "warning":
			warn = True
		else:
			info = True

		self.__infoIcon.setVisible( info )
		self.__warningIcon.setVisible( warn )
		self.__errorIcon.setVisible( error )
