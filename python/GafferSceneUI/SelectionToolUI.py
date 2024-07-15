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

import functools
import imath

import IECore

import Gaffer
import GafferUI
import GafferSceneUI

Gaffer.Metadata.registerNode(

	GafferSceneUI.SelectionTool,

	"description",
	"""
	Tool for selecting objects.

	- Click or drag to set selection
	- Shift-click or shift-drag to add to selection
	- Drag and drop selected objects
		- Drag to Python Editor to get their names
		- Drag to PathFilter or Set node to add/remove their paths
	""",

	"nodeToolbar:bottom:type", "GafferUI.StandardNodeToolbar.bottom",

	"viewer:shortCut", "Q",
	"order", 0,

	# So we don't obscure the corner gnomon
	"toolbarLayout:customWidget:LeftSpacer:widgetType", "GafferSceneUI.SelectionToolUI._LeftSpacer",
	"toolbarLayout:customWidget:LeftSpacer:section", "Bottom",
	"toolbarLayout:customWidget:LeftSpacer:index", 0,

	# So our layout doesn't jump around too much when our selection widget changes size
	"toolbarLayout:customWidget:RightSpacer:widgetType", "GafferSceneUI.SelectionToolUI._RightSpacer",
	"toolbarLayout:customWidget:RightSpacer:section", "Bottom",
	"toolbarLayout:customWidget:RightSpacer:index", -1,

	plugs = {

		"selectMode" : [

			"description",
			"""
			Determines the scene location that is ultimately selected or deselected,
			which may differ from what is originally selected.
			""",

			"plugValueWidget:type", "GafferSceneUI.SelectionToolUI.SelectModePlugValueWidget",

			"label", "Select",

			"toolbarLayout:section", "Bottom",
			"toolbarLayout:width", 150,

		],
	},

)

class _LeftSpacer( GafferUI.Spacer ) :

	def __init__( self, imageView, **kw ) :

		GafferUI.Spacer.__init__( self, size = imath.V2i( 40, 1 ), maximumSize = imath.V2i( 40, 1 ) )

class _RightSpacer( GafferUI.Spacer ) :

	def __init__( self, imageView, **kw ) :

		GafferUI.Spacer.__init__( self, size = imath.V2i( 0, 0 ) )

class SelectModePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__menuButton = GafferUI.MenuButton( "", menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )

		GafferUI.PlugValueWidget.__init__( self, self.__menuButton, plugs, **kw )

	def _updateFromValues( self, values, exception ) :

		if exception is not None :
			self.__menuButton.setText( "" )
		else :
			modes = GafferSceneUI.SelectionTool.registeredSelectModes()

			assert( len( values ) == 1 )

			if values[0] in modes :
				self.__menuButton.setText( values[0].partition( "/" )[-1] )
			else :
				self.__menuButton.setText( "Invalid" )

		self.__menuButton.setErrored( exception is not None )

	def _updateFromEditable( self ) :

		self.__menuButton.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		modes = GafferSceneUI.SelectionTool.registeredSelectModes()

		# dict mapping category names to the last inserted menu item for that category
		# so we know where to insert the next item for the category.
		modifiedCategories = {}

		with self.context() :
			currentValue = self.getPlug().getValue()

		for mode in modes :
			category, sep, label = mode.partition( "/" )

			if category != "" and category not in modifiedCategories.keys() :
				dividerPath = f"/__{category}Dividier"
				result.append( dividerPath, { "divider" : True, "label" : category } )
				modifiedCategories[category] = dividerPath

			itemPath = f"/{label}"
			itemDefinition = {
				"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), mode ),
				"checkBox" : mode == currentValue
			}

			if category in modifiedCategories.keys() :
				result.insertAfter( itemPath, itemDefinition, modifiedCategories[category] )
			else :
				result.append( itemPath, itemDefinition )

			modifiedCategories[category] = itemPath

		return result

	def __setValue( self, modifier, *unused ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().setValue( modifier )
