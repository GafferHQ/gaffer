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

import IECore

import Gaffer
import GafferUI

class PresetsPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		cont = GafferUI.ListContainer(
			GafferUI.ListContainer.Orientation.Vertical, spacing=4, borderWidth=0,
		)

		GafferUI.PlugValueWidget.__init__( self, cont, plug, **kw )

		self.__menuButton = GafferUI.MenuButton( "", menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )
		cont.addChild( self.__menuButton )

		self.__customValuePlugWidget = GafferUI.PlugValueWidget.create( plug, useTypeOnly=True )
		cont.addChild( self.__customValuePlugWidget )

		self._addPopupMenu( self.__menuButton )
		self._updateFromPlug()

	def menu( self ) :

		return self.__menuButton.getMenu()

	def _updateFromPlug( self ) :

		self.__menuButton.setEnabled( self._editable() )

		text = ""
		allowCustom = False
		isCustom = False
		if self.getPlug() is not None :
			allowCustom = Gaffer.Metadata.value( self.getPlug(), "presetsPlugValueWidget:allowCustom" )
			isCustom = Gaffer.Metadata.value( self.getPlug(), "presetsPlugValueWidget:isCustom" )

			with self.getContext() :
				presetName = Gaffer.NodeAlgo.currentPreset( self.getPlug() )

			if allowCustom:
				if isCustom or not presetName:
					isCustom = True
					text = "Custom"
				else:
					text = presetName or "Invalid"
			else:
				text = presetName or "Invalid"

		self.__menuButton.setText( text )
		self.__customValuePlugWidget.setVisible( isCustom )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()
		if self.getPlug() is None :
			return result

		currentPreset = Gaffer.NodeAlgo.currentPreset( self.getPlug() )
		allowCustom = Gaffer.Metadata.value( self.getPlug(), "presetsPlugValueWidget:allowCustom" )
		isCustom = Gaffer.Metadata.value( self.getPlug(), "presetsPlugValueWidget:isCustom" )
		for n in Gaffer.NodeAlgo.presets( self.getPlug() ) :
			menuPath = n if n.startswith( "/" ) else "/" + n
			result.append(
				menuPath,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__applyPreset ), preset = n ),
					"checkBox" : n == currentPreset and not isCustom,
				}
			)

		if allowCustom:
			result.append( "/CustomDivider", { "divider" : True } )
			result.append(
				"/Custom",
				{
					"command" : Gaffer.WeakMethod( self.__applyCustomPreset ),
					"checkBox" : isCustom or not currentPreset,
				}
			)

		return result

	def __applyPreset( self, unused, preset ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			Gaffer.Metadata.deregisterValue( self.getPlug(), "presetsPlugValueWidget:isCustom" )
			Gaffer.NodeAlgo.applyPreset( self.getPlug(), preset )

	def __applyCustomPreset( self, unused ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			# When we first switch to custom mode, the current value will
			# actually be one of the registered presets. So we use this
			# metadata value to keep track of the user's desire to be in
			# custom mode despite of this fact. We use metadata rather than
			# a member variable so that undo will take us back to the non-custom
			# state automatically.
			Gaffer.Metadata.registerValue( self.getPlug(), "presetsPlugValueWidget:isCustom", True )
