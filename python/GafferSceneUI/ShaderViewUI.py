##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

	GafferSceneUI.ShaderView,

	plugs = {

		"scene" : [

			"description",
			"""
			Defines the scene used for the shader preview.
			""",
			"plugValueWidget:type", "GafferSceneUI.ShaderViewUI._ScenePlugValueWidget",
		],

		"lutGPU" : [
			"divider", True
		],

	}

)

##########################################################################
# _ScenePlugValueWidget
##########################################################################

class _ScenePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ), title = "Shader Preview Scene" )
		menuButton = GafferUI.MenuButton( menu=menu, image = "scene.png", hasFrame=False )

		GafferUI.PlugValueWidget.__init__( self, menuButton, plug, **kw )

		self.__settingsWindow = None

	def hasLabel( self ) :

		return True

	def _updateFromPlug( self ) :

		pass

	def __menuDefinition( self ) :

		m = IECore.MenuDefinition()

		view = self.getPlug().node()
		currentScene = self.getPlug().getValue()
		for scene in view.registeredScenes( view.shaderPrefix() ) :
			m.append(
				"/" + scene,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__changeScene ), scene ),
					"checkBox" : scene == currentScene
				}
			)

		m.append( "/SettingsDivider", { "divider" : True } )

		m.append( "/Settings...", { "command" : Gaffer.WeakMethod( self.__showSettings ) } )

		return m

	def __changeScene( self, scene, *unused ) :

		self.getPlug().setValue( scene )

	def __showSettings( self, menu ) :

		if self.__settingsWindow is None :
			self.__settingsWindow = _SettingsWindow( self.getPlug().node() )
			self.ancestor( GafferUI.Window ).addChildWindow( self.__settingsWindow )

		self.__settingsWindow.setVisible( True )

class _SettingsWindow( GafferUI.Window ) :

	def __init__( self, shaderView ) :

		GafferUI.Window.__init__( self, "ShaderView Settings" )

		with self :
			with GafferUI.ListContainer() :
				self.__frame = GafferUI.Frame( borderStyle = GafferUI.Frame.BorderStyle.None_, borderWidth = 4 )
				GafferUI.Spacer( imath.V2i( 0 ), parenting = { "expand" : True } )

		self.__shaderView = shaderView
		shaderView.sceneChangedSignal().connect( Gaffer.WeakMethod( self.__sceneChanged ), scoped = False )
		self.__updateNodeUI()

	def __updateNodeUI( self ) :

		plugLayout = None
		if self.__shaderView.scene() is not None :
			Gaffer.Metadata.registerValue( self.__shaderView.scene()["shader"], "plugValueWidget:type", "" )
			plugLayout = GafferUI.PlugLayout( self.__shaderView.scene(), rootSection = "Settings" )

		self.__frame.setChild( plugLayout )

	def __sceneChanged( self, shaderView ) :

		self.__updateNodeUI()
