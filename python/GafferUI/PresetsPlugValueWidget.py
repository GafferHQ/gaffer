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

import collections
import functools

import IECore

import Gaffer
import GafferUI

from GafferUI.PlugValueWidget import sole

class PresetsPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		cont = GafferUI.ListContainer(
			GafferUI.ListContainer.Orientation.Vertical, spacing=4, borderWidth=0,
		)

		GafferUI.PlugValueWidget.__init__( self, cont, plugs, **kw )

		self.__menuButton = GafferUI.MenuButton( "", menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )
		cont.addChild( self.__menuButton )

		self.__customValuePlugWidget = GafferUI.PlugValueWidget.create( plugs, typeMetadata = "presetsPlugValueWidget:customWidgetType" )

		cont.addChild( self.__customValuePlugWidget )

		self._addPopupMenu( self.__menuButton )

		# Possible states :
		#
		# - None : Multiple plugs, and they have different values.
		# - "<presetName>" : All plugs have value matching `<presetName>`.
		# - "" : All plugs have a value that isn't a preset.
		self.__currentPreset = None
		# We do this again when `_updateFromValues()` is called, but doing it
		# from the constructor first avoids layout flicker by getting the
		# visibility correct before the widget is shown.
		self.__customValuePlugWidget.setVisible( self.__isCustom() )

	def menu( self ) :

		return self.__menuButton.getMenu()

	def menuButton( self ) :

		return self.__menuButton

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		return [ Gaffer.NodeAlgo.currentPreset( p ) or "" for p in plugs ]

	def _updateFromValues( self, values, exception ) :

		self.__currentPreset = sole( values )
		isCustom = self.__isCustom()

		self.__customValuePlugWidget.setVisible( isCustom )

		if exception is not None :
			self.__menuButton.setText( "" )
		elif isCustom :
			self.__menuButton.setText( "Custom" )
		elif self.__currentPreset :
			self.__menuButton.setText( self.__currentPreset )
		elif self.__currentPreset is None :
			self.__menuButton.setText( "---" )
		else :
			self.__menuButton.setText( "Invalid" )

		self.__menuButton.setErrored( exception is not None )

	def _valuesDependOnContext( self ) :

		# We allow the presets metadata to be context-sensitive, so must
		# update whenever the context changes.
		return True

	def _updateFromMetadata( self ) :

		self._requestUpdateFromValues()

	def _updateFromEditable( self ) :

		self.__menuButton.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()
		if not self.getPlugs() :
			return result

		# Required for context-sensitive dynamic presets
		with self.getContext():

			# Find the union of the presets across all plugs,
			# and count how many times they occur.
			presets = []
			presetCounts = collections.Counter()
			for plug in self.getPlugs() :
				for preset in Gaffer.NodeAlgo.presets( plug ) :
					if not presetCounts[preset] :
						presets.append( preset )
					presetCounts[preset] += 1

		# Build menu. We'll list every preset we found, but disable
		# any which aren't available for all plugs.
		isCustom = self.__isCustom()
		readOnly = any( Gaffer.MetadataAlgo.readOnly( p ) for p in self.getPlugs() )
		for preset in presets :

			menuPath = preset if preset.startswith( "/" ) else "/" + preset
			result.append(
				menuPath,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__applyPreset ), preset = preset ),
					"checkBox" : preset == self.__currentPreset and not isCustom,
					"active" : ( presetCounts[preset] == len( self.getPlugs() ) ) and not readOnly
				}
			)

		allowCustom = sole( ( Gaffer.Metadata.value( p, "presetsPlugValueWidget:allowCustom" ) for p in self.getPlugs() ) )
		if allowCustom :
			result.append( "/CustomDivider", { "divider" : True } )
			result.append(
				"/Custom",
				{
					"command" : Gaffer.WeakMethod( self.__applyCustomPreset ),
					"checkBox" : isCustom,
					"active" : not readOnly,
				}
			)

		return result

	def __isCustom( self ) :

		allowCustom = sole( ( Gaffer.Metadata.value( p, "presetsPlugValueWidget:allowCustom" ) for p in self.getPlugs() ) )
		isCustom = any( Gaffer.Metadata.value( p, "presetsPlugValueWidget:isCustom" ) for p in self.getPlugs() )
		return allowCustom and ( isCustom or self.__currentPreset == "" )

	def __applyPreset( self, unused, preset ) :

		# Required for context-sensitive dynamic presets
		with self.getContext() :
			with Gaffer.UndoScope( next( iter( self.getPlugs() ) ).ancestor( Gaffer.ScriptNode ) ) :
				for plug in self.getPlugs() :
					Gaffer.Metadata.deregisterValue( plug, "presetsPlugValueWidget:isCustom" )
					Gaffer.NodeAlgo.applyPreset( plug, preset )

	def __applyCustomPreset( self, unused ) :

		with Gaffer.UndoScope( next( iter( self.getPlugs() ) ).ancestor( Gaffer.ScriptNode ) ) :
			for plug in self.getPlugs() :
				# When we first switch to custom mode, the current value will
				# actually be one of the registered presets. So we use this
				# metadata value to keep track of the user's desire to be in
				# custom mode despite of this fact. We use metadata rather than
				# a member variable so that undo will take us back to the non-custom
				# state automatically.
				Gaffer.Metadata.registerValue( plug, "presetsPlugValueWidget:isCustom", True )
