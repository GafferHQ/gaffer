##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

from __future__ import with_statement

import Gaffer
import GafferImage
import GafferUI
import GafferImageUI
from IECore import StringVectorData

class ChannelMaskPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, inputImagePlug, **kw ) :

		self.__multiSelectionMenu = GafferUI.MultiSelectionMenu( allowMultipleSelection = True, alwaysHaveASelection=False )
		GafferUI.PlugValueWidget.__init__( self, self.__multiSelectionMenu, plug, **kw )
		self.__selectionChangedConnection = self.__multiSelectionMenu.selectionChangedSignal().connect( Gaffer.WeakMethod( self._updateFromSelection ) )
		self.__inputPlug = None

		if inputImagePlug != None :
			p = plug.node()[inputImagePlug]
			if p.direction() != Gaffer.Plug.Direction.In :
				raise RuntimeError("Image plug is not an input. Please connect an input image plug.")
			else:
				self.__inputPlug = p
				self.__inputChangedConnection = self.__inputPlug.node().plugInputChangedSignal().connect( Gaffer.WeakMethod( self._updateFromImagePlug ) )
				self._updateFromImagePlug( self.__inputPlug )
		else :
			raise RuntimeError("Failed to find an input image plug. Please ensure that one has been assigned in the ChannelMaskPlugValueWidget's constructor.")

		self._updateFromPlug()

	def _displayText( self ) :

		selected = self.__multiSelectionMenu.getSelection()
		nSelected = len( selected )
		nEntries = len( self.__multiSelectionMenu )

		if nEntries == 0 :
			return "none"
		elif nSelected == nEntries :
			return "all"
		elif nSelected == 0 :
			return "none"

		text = ""
		for i in range( 0, nSelected ) :
			if i < 4 :
				text = text + selected[i][-1]
			elif i == 4 :
				text = text + "..."
				break

		return text

	def _updateFromSelection( self, widget ) :

		plug = self.getPlug()
		if plug is not None :
			with Gaffer.UndoContext( plug.ancestor( Gaffer.ScriptNode ) ) :
				selection = StringVectorData( self.__multiSelectionMenu.getSelection() )
				self.__multiSelectionMenu.setText( self._displayText() )
				selection = [ channel.replace( "/", "." ) for channel in selection ]
				plug.setValue( StringVectorData( selection ) )

	def _updateFromPlug( self ) :

		# Get the value from the plug and select those channels from the menu.
		plug = self.getPlug()
		if plug is not None :
			with self.getContext() :
				plugValue = plug.getValue()
				if plugValue is None :
					plugValue = plug.ValueType()
				else :
					plugValue = [ channel.replace( ".", "/" ) for channel in plugValue ]
				self.__multiSelectionMenu.setSelection( plugValue )
		self.__multiSelectionMenu.setEnabled( True )

	## Populates the menu with the channels found on the inputPlug.
	## When populating the menu, if the current plug value is trying to mask a
	## channel which doesn't exist on the input, it is disabled (but still displayed).
	def _updateFromImagePlug( self, inputPlug ) :

		if not inputPlug.isSame( self.__inputPlug ) and not self.__inputPlug == None :
			return

		input = self.__inputPlug

		# Get the new channels from the input plug.
		channels = list( input['channelNames'].getValue() )
		channels = [ channel.replace( ".", "/" ) for channel in channels ]

		# Get the currently selected channels from the input plug.
		plug = self.getPlug()
		if plug is not None :
			with self.getContext() :
				plugValue = plug.getValue()

		selected = []
		for item in plugValue :
			selected.append( item )

		# Merge the selected channels and the input's channels.
		# We do this by creating a list of unique channels which are also ordered so that
		# any channels that were selected but don't belong to the input's channels are
		# appended to the end.
		seen = set()
		seen_add = seen.add
		newChannels = [ x for x in channels + selected if x not in seen and not seen_add(x)]
		self.__multiSelectionMenu[:] = newChannels

		# Now disable the channels that don't exist on the input.
		disabled = set( selected ) - set( channels )

		self.__multiSelectionMenu.setSelection( selected )
		if len( disabled ) > 0 :
			enabled = set(self.__multiSelectionMenu.getEnabledItems()) - disabled
			self.__multiSelectionMenu.setEnabledItems( enabled )

GafferUI.PlugValueWidget.registerType( GafferImage.ChannelMaskPlug, ChannelMaskPlugValueWidget )

