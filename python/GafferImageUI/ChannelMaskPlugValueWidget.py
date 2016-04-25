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

import functools

import IECore

import Gaffer
import GafferImage
import GafferUI

class ChannelMaskPlugValueWidget( GafferUI.PlugValueWidget ) :

	# The imagePlug provides the available channel names which are
	# presented in the UI. The default value causes the "in" plug
	# from the same node as the main plug to be used.
	def __init__( self, plug, imagePlug = None, parenting = None ) :

		self.__menuButton = GafferUI.MenuButton( menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )

		GafferUI.PlugValueWidget.__init__( self, self.__menuButton, plug, parenting = parenting )

		if imagePlug is not None :
			self.__imagePlug = imagePlug
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

		text = ""
		if value is not None :
			if not len( value ) :
				text = "None"
			else :
				## \todo Improve display for when we have long
				# channel names.
				text = "".join( value )

		self.__menuButton.setText( text )
		self.__menuButton.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		with self.getContext() :
			try :
				selectedChannels = self.getPlug().getValue()
			except :
				selectedChannels = IECore.StringVectorData()
			try :
				availableChannels = self.__imagePlug["channelNames"].getValue()
			except :
				availableChannels = IECore.StringVectorData()

		result = IECore.MenuDefinition()
		for channel in availableChannels :

			channelSelected = channel in selectedChannels
			if channelSelected :
				newValue = IECore.StringVectorData( [ c for c in selectedChannels if c != channel ] )
			else :
				newValue = IECore.StringVectorData( [ c for c in availableChannels if c in selectedChannels or c == channel ] )

			result.append(
				"/" + channel.replace( ".", "/" ),
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value = newValue ),
					"checkBox" : channelSelected,
				}
			)

		return result

	def __setValue( self, unused, value ) :

		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().setValue( value )

GafferUI.PlugValueWidget.registerType( GafferImage.ChannelMaskPlug, ChannelMaskPlugValueWidget )
