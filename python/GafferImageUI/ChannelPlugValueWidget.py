##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

import GafferImage

## Supported plug metadata :
#
# - "channelPlugValueWidget:extraChannels", a list of extra channel names to always support.
#   Can be used to provide special functionality such as the reserved White/Black channels on Shuffle
# - "channelPlugValueWidget:extraChannelLabels", if you are using extraChannels, you may specify a
#   matching list of the same length of what label to use for each extra channel
# - "channelPlugValueWidget:imagePlugName", the image plug to choose a channel from
#   Will be passed to node().descendant.  Defaults to "in"
# - "channelPlugValueWidget:allowNewChannels", allow choosing channels that don't exist on the imagePlug.
#   This currently allows only the channels RGBA to be created.
#   \todo - can we allow creating arbitrary custom new channels?  Should this be controlled by the same
#           metadata or different?
class ChannelPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		column = GafferUI.ListContainer( spacing = 4 )
		GafferUI.PlugValueWidget.__init__( self, column, plugs, **kw )

		with column :

			self.__menuButton = GafferUI.MenuButton( menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )
			self._addPopupMenu( self.__menuButton )
			self.__customValueWidget = GafferUI.StringPlugValueWidget( plugs )

		self.__availableChannels = set()
		self.__currentChannel = None

		self.__customValueWidget.setVisible( self.__isCustom() )

	def _auxiliaryPlugs( self, plug ) :

		name = Gaffer.Metadata.value( plug, "channelPlugValueWidget:imagePlugName" ) or "in"
		imagePlug = plug.node().descendant( name )
		return [ imagePlug["viewNames"], imagePlug["channelNames"] ]

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		result = []

		for plug, ( viewNamesPlug, channelNamesPlug ) in zip( plugs, auxiliaryPlugs ) :

			availableChannels = set()
			for viewName in viewNamesPlug.getValue() :
				availableChannels.update( channelNamesPlug.parent().channelNames( viewName = viewName ) )

			result.append( { "value" : plug.getValue(), "availableChannels" : availableChannels } )

		return result

	def _updateFromValues( self, values, exception ) :

		self.__availableChannels = set().union( *[ v["availableChannels"] for v in values ] )
		self.__currentChannel = sole( v["value"] for v in values )

		isCustom = self.__isCustom()
		self.__customValueWidget.setVisible( isCustom )

		if isCustom :
			label = "Custom"
		else :
			label = self.__extraChannels().get( self.__currentChannel, self.__currentChannel )

		self.__menuButton.setText(
			label if label is not None else "---"
		)

		self.__menuButton.setErrored( exception is not None )

	def _updateFromMetadata( self ) :

		self._requestUpdateFromValues()

	def _updateFromEditable( self ) :

		self.__menuButton.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		availableChannels = self.__availableChannels.copy()
		if all( Gaffer.Metadata.value( plug, "channelPlugValueWidget:allowNewChannels" ) for plug in self.getPlugs() ) :
			for channel in ( "R", "G", "B", "A" ) :
				if channel not in availableChannels :
					availableChannels.add( channel )

		isCustom = self.__isCustom()

		result = IECore.MenuDefinition()
		for channel in GafferImage.ImageAlgo.sortedChannelNames( availableChannels ) :
			result.append(
				"/{}".format( channel.replace( ".", "/" ) ),
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value = channel ),
					"checkBox" : not isCustom and channel == self.__currentChannel,
				}
			)

		extraChannels = self.__extraChannels()
		if extraChannels :
			result.append( "__ExtraChannelsDivider", { "divider" : True } )
			for channel, label in extraChannels.items() :
				result.append(
					f"/{label}",
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value = channel ),
						"checkBox" : channel == self.__currentChannel,
					}
				)

		if not result.items() :
			result.append( "/No Channels Available", { "active" : False } )

		result.append( "/CustomDivider", { "divider" : True } )
		result.append(
			"/Custom",
			{
				"command" : Gaffer.WeakMethod( self.__applyCustom ),
				"checkBox" : isCustom,
			}
		)

		return result

	def __setValue( self, unused, value ) :

		with Gaffer.UndoScope( self.scriptNode() ) :
			for plug in self.getPlugs() :
				plug.setValue( value )
				Gaffer.Metadata.deregisterValue( plug, "channelPlugValueWidget:isCustom" )

	def __applyCustom( self, unused ) :

		with Gaffer.UndoScope( self.scriptNode() ) :
			for plug in self.getPlugs() :
				Gaffer.Metadata.registerValue( plug, "channelPlugValueWidget:isCustom", True )

	def __isCustom( self ) :

		return any( Gaffer.Metadata.value( p, "channelPlugValueWidget:isCustom" ) for p in self.getPlugs() )

	def __extraChannels( self ) :

		# Intersection of the extra channels defined by each individual plug.

		if not self.getPlugs() :
			return {}

		result = None
		for plug in self.getPlugs() :
			extraChannels = Gaffer.Metadata.value( plug, "channelPlugValueWidget:extraChannels" ) or []
			extraChannelLabels = Gaffer.Metadata.value( plug, "channelPlugValueWidget:extraChannelLabels" ) or []
			if result is None :
				result = collections.OrderedDict( zip( extraChannels, extraChannelLabels ) )
			else :
				for channel, label in zip( extraChannels, extraChannelLabels ) :
					if result.get( channel, None ) != label :
						del result[channel]

		return result
