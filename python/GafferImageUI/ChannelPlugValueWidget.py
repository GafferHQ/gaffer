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

import functools

import IECore

import Gaffer
import GafferUI

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

	def __init__( self, plug, **kw ) :

		self.__menuButton = GafferUI.MenuButton( menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )

		GafferUI.PlugValueWidget.__init__( self, self.__menuButton, plug, **kw )

		imagePlugName = Gaffer.Metadata.value( self.getPlug(), "channelPlugValueWidget:imagePlugName" )
		if imagePlugName :
			self.__imagePlug = plug.node().descendant( imagePlugName )
		else :
			self.__imagePlug = plug.node()["in"]

		assert( isinstance( self.__imagePlug, GafferImage.ImagePlug ) )

		self._updateFromPlug()

	def _updateFromPlug( self ) :

		value = None
		if self.getPlug() is not None :
			with self.getContext() :
				try :
					value = self.getPlug().getValue()
				except :
					# Leave it to other parts of the UI
					# to display the error.
					pass

		self.__menuButton.setText( self.__channelLabel( value ) )
		self.__menuButton.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		with self.getContext() :
			selectedChannel = ""
			availableChannels = []
			with IECore.IgnoredExceptions( Exception ):
				selectedChannel = self.getPlug().getValue()
				availableChannels = self.__imagePlug["channelNames"].getValue()


		if Gaffer.Metadata.value( self.getPlug(), "channelPlugValueWidget:allowNewChannels" ):
			for channel in ( "R", "G", "B", "A" ) :
				if channel not in availableChannels :
					availableChannels.append( channel )

		availableChannels = GafferImage.ImageAlgo.sortedChannelNames( availableChannels )

		extraChannels = Gaffer.Metadata.value( self.getPlug(), "channelPlugValueWidget:extraChannels" )
		if extraChannels:
			availableChannels.append( "___DIVIDER___" )
			availableChannels.extend( extraChannels )

		result = IECore.MenuDefinition()
		for channel in availableChannels :

			if channel == "___DIVIDER___" :
				result.append( "/__Divider", { "divider" : True } )
			else:
				result.append(
					"/" + self.__channelLabel( channel ).replace( ".", "/" ),
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value = channel ),
						"checkBox" : selectedChannel == channel,
					}
				)

		return result

	def __setValue( self, unused, value ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().setValue( value )

	def __channelLabel( self, channelName ) :

		if not channelName :
			return "None"

		extraChannels = Gaffer.Metadata.value( self.getPlug(), "channelPlugValueWidget:extraChannels" )
		extraChannelLabels = Gaffer.Metadata.value( self.getPlug(), "channelPlugValueWidget:extraChannelLabels" )
		if extraChannels and extraChannelLabels:
			for label, value in zip( extraChannelLabels, extraChannels ):
				if channelName == value:
					return label

		return channelName
