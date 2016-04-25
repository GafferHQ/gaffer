##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2014, John Haddon. All rights reserved.
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

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

Gaffer.Metadata.registerNode(

	GafferSceneUI.SceneView,

	plugs = {

		"shadingMode" : [

			"toolbarLayout:index", 2,
			"toolbarLayout:divider", True,
			"plugValueWidget:type", "GafferSceneUI.SceneViewToolbar._ShadingModePlugValueWidget",

		],

		"minimumExpansionDepth" : [

			"plugValueWidget:type", "GafferSceneUI.SceneViewToolbar._ExpansionPlugValueWidget",
			"toolbarLayout:divider", True,

		],

		"lookThrough" : [

			"plugValueWidget:type", "GafferSceneUI.SceneViewToolbar._LookThroughPlugValueWidget",
			"toolbarLayout:divider", True,
			"toolbarLayout:label", "",

		],

		"lookThrough.enabled" : [

			"description",
			"""
			When enabled, locks the view to look through a specific camera in the scene.
			By default, the current render camera is used, but this can be changed using the lookThrough.camera
			setting.
			""",
		],

		"lookThrough.camera" : [

			"description",
			"""
			Specifies the camera to look through when lookThrough.enabled is on. The default value
			means that the current render camera will be used - the paths to other cameras may be specified
			to choose another camera."
			""",
		],

		"grid" : [

			"plugValueWidget:type", "GafferSceneUI.SceneViewToolbar._GridPlugValueWidget",

		],

		"gnomon" : [

			"plugValueWidget:type", "",

		],

	}

)

##########################################################################
# _ShadingModePlugValueWidget
##########################################################################

class _ShadingModePlugValueWidget( GafferUI.PlugValueWidget ) :

		def __init__( self, plug, parenting = None ) :

			menuButton = GafferUI.MenuButton(
				image = "shading.png",
				menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ),
				hasFrame = False,
			)

			GafferUI.PlugValueWidget.__init__( self, menuButton, plug, parenting = parenting )

		def hasLabel( self ) :

			return True

		def _updateFromPlug( self ) :

			pass

		def __menuDefinition( self ) :

			m = IECore.MenuDefinition()

			currentName = self.getPlug().getValue()
			for name in [ "" ] + GafferSceneUI.SceneView.registeredShadingModes() :
				m.append(
					"/" + name if name else "Default",
					{
						"checkBox" : name == currentName,
						"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), name if name != currentName else "" ),
					}
				)

				if not name :
					m.append( "/DefaultDivider", { "divider" : True } )

			return m

		def __setValue( self, value, *unused ) :

			self.getPlug().setValue( value )

##########################################################################
# _ExpansionPlugValueWidget
##########################################################################

class _ExpansionPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, parenting = None ) :

		menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) )
		menuButton = GafferUI.MenuButton( menu=menu, image = "expansion.png", hasFrame=False )

		GafferUI.PlugValueWidget.__init__( self, menuButton, plug, parenting = parenting )

	def hasLabel( self ) :

		return True

	def _updateFromPlug( self ) :

		pass

	def __menuDefinition( self ) :

		expandAll = bool( self.getPlug().getValue() )

		m = IECore.MenuDefinition()
		m.append( "/Expand Selection", { "command" : self.getPlug().node().expandSelection, "active" : not expandAll, "shortCut" : "Down" } )
		m.append( "/Expand Selection Fully", { "command" : IECore.curry( self.getPlug().node().expandSelection, depth = 999 ), "active" : not expandAll, "shortCut" : "Shift+Down" } )
		m.append( "/Collapse Selection", { "command" : self.getPlug().node().collapseSelection, "active" : not expandAll, "shortCut" : "Up" } )
		m.append( "/Expand All Divider", { "divider" : True } )
		m.append( "/Expand All", { "checkBox" : expandAll, "command" : Gaffer.WeakMethod( self.__toggleMinimumExpansionDepth ) } )

		return m

	def __toggleMinimumExpansionDepth( self, *unused ) :

		self.getPlug().setValue( 0 if self.getPlug().getValue() else 999 )

##########################################################################
# _LookThroughPlugValueWidget
##########################################################################

class _LookThroughPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, parenting = None ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.PlugValueWidget.__init__( self, row, plug, parenting = parenting )

		with row :
			self.__enabledWidget = GafferUI.BoolPlugValueWidget( plug["enabled"], displayMode=GafferUI.BoolWidget.DisplayMode.Switch )
			self.__cameraWidget = GafferSceneUI.ScenePathPlugValueWidget(
				plug["camera"],
				path = GafferScene.ScenePath(
					plug.node()["in"],
					plug.node().getContext(),
					"/",
					filter = GafferScene.ScenePath.createStandardFilter( [ "__cameras" ], "Show only cameras" )
				),
			)
			self.__cameraWidget.pathWidget().setFixedCharacterWidth( 13 )
			if hasattr( self.__cameraWidget.pathWidget()._qtWidget(), "setPlaceholderText" ) :
				self.__cameraWidget.pathWidget()._qtWidget().setPlaceholderText( "Render Camera" )

		self._updateFromPlug()

	def _updateFromPlug( self ) :

		with self.getContext() :
			self.__cameraWidget.setEnabled( self.getPlug()["enabled"].getValue() )

##########################################################################
# _GridPlugValueWidget
##########################################################################

class _GridPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, parenting = None ) :

		menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) )
		menuButton = GafferUI.MenuButton( menu=menu, image = "grid.png", hasFrame=False )

		GafferUI.PlugValueWidget.__init__( self, menuButton, plug, parenting = parenting )

	def hasLabel( self ) :

		return True

	def _updateFromPlug( self ) :

		pass

	def __menuDefinition( self ) :

		m = IECore.MenuDefinition()
		m.append(
			"/Show Grid",
			{
				"checkBox" : self.getPlug()["visible"].getValue(),
				"command" : self.getPlug()["visible"].setValue,
			}
		)

		m.append(
			"/Show Gnomon",
			{
				"checkBox" : self.getPlug().node()["gnomon"]["visible"].getValue(),
				"command" : self.getPlug().node()["gnomon"]["visible"].setValue,
			}
		)

		return m
