##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

## \todo Add buttons for removing existing ChannelPlugs, and for adding
# extras. This is probably best done as part of a concerted effort to
# support layers everywhere (we can already compute arbitrary numbers of
# named channels, we just need a convention and a UI for presenting this
# as layers).

Gaffer.Metadata.registerNode(

	GafferImage.Shuffle,

	"description",
	"""
	Shuffles data between image channels, for instance by copying R
	into G or a constant white into A.
	""",

	plugs = {

		"channels" : [

			"description",
			"""
			The definition of the shuffling to be performed - an
			arbitrary number of channel edits can be made by adding
			Shuffle.ChannelPlugs as children of this plug.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",

		],

		"channels.*.out" : [

			"plugValueWidget:type", "GafferImageUI.ShuffleUI._ChannelPlugValueWidget"

		],

		"channels.*.in" : [

			"plugValueWidget:type", "GafferImageUI.ShuffleUI._ChannelPlugValueWidget"

		],

	}

)

def nodeMenuCreateCommand() :

	result = GafferImage.Shuffle()
	for channel in ( "R", "G", "B", "A" ) :
		result["channels"].addChild( result.ChannelPlug( channel, channel ) )

	return result

class _ShuffleChannelPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, parenting = None ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		GafferUI.PlugValueWidget.__init__( self, self.__row, plug, parenting = parenting )

		with self.__row :

			GafferUI.PlugValueWidget.create( plug["out"] )

			GafferUI.Image( "shuffleArrow.png" )

			GafferUI.PlugValueWidget.create( plug["in"] )

	def setPlug( self, plug ) :

		GafferUI.PlugValueWidget.setPlug( self, plug )

		self.__row[0].setPlug( plug[0] )
		self.__row[2].setPlug( plug[1] )

	def childPlugValueWidget( self, childPlug, lazy=True ) :

		for w in self.__row[0], self.__row[2] :
			if childPlug.isSame( w.getPlug() ) :
				return w

		return None

	def hasLabel( self ) :

		return True

	def _updateFromPlug( self ) :

		pass

GafferUI.PlugValueWidget.registerType( GafferImage.Shuffle.ChannelPlug, _ShuffleChannelPlugValueWidget )

## \todo This probably makes sense as a public part of GafferImageUI
# so it can be used by other nodes which want to select individual channels.
# When doing this we'll need to drive the extra White/Black fields and
# whether or not new channels can be created using metadata.
class _ChannelPlugValueWidget( GafferUI.PlugValueWidget ) :

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

		self.__menuButton.setText( self.__channelLabel( value ) )
		self.__menuButton.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		with self.getContext() :
			try :
				selectedChannel = self.getPlug().getValue()
			except :
				selectedChannels = ""
			try :
				availableChannels = self.__imagePlug["channelNames"].getValue()
			except :
				availableChannels = []

		if self.getPlug().getName() == "in" :
			availableChannels.extend( [ "__white", "__black" ] )
		else :
			for channel in ( "R", "G", "B", "A" ) :
				if channel not in availableChannels :
					availableChannels.append( channel )

		result = IECore.MenuDefinition()
		for channel in availableChannels :

			if channel == "__white" :
				result.append( "/__Divider", { "divider" : True } )

			result.append(
				"/" + self.__channelLabel( channel ).replace( ".", "/" ),
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value = channel ),
					"checkBox" : selectedChannel == channel,
				}
			)

		return result

	def __setValue( self, unused, value ) :

		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().setValue( value )

	def __channelLabel( self, channelName ) :

		if not channelName :
			return "None"
		elif channelName == "__white" :
			return "White"
		elif channelName == "__black" :
			return "Black"
		else :
			return channelName
