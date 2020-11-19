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


			"plugValueWidget:type", "GafferImageUI.ChannelPlugValueWidget",
			"channelPlugValueWidget:allowNewChannels", True,

		],

		"channels.*.in" : [

			"plugValueWidget:type", "GafferImageUI.ChannelPlugValueWidget",
			"channelPlugValueWidget:extraChannels", IECore.StringVectorData( [ "__white", "__black" ] ),
			"channelPlugValueWidget:extraChannelLabels", IECore.StringVectorData( [ "White", "Black" ] ),

		],

	}

)

def nodeMenuCreateCommand() :

	result = GafferImage.Shuffle()
	for channel in ( "R", "G", "B", "A" ) :
		result["channels"].addChild( result.ChannelPlug( channel, channel ) )

	return result

class _ShuffleChannelPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		GafferUI.PlugValueWidget.__init__( self, self.__row, plug, **kw )

		with self.__row :

			GafferUI.PlugValueWidget.create( plug["out"] )

			GafferUI.Image( "shuffleArrow.png" )

			GafferUI.PlugValueWidget.create( plug["in"] )

	def setPlug( self, plug ) :

		GafferUI.PlugValueWidget.setPlug( self, plug )

		self.__row[0].setPlug( plug[0] )
		self.__row[2].setPlug( plug[1] )

	def childPlugValueWidget( self, childPlug ) :

		for w in self.__row[0], self.__row[2] :
			if childPlug.isSame( w.getPlug() ) :
				return w

		return None

	def hasLabel( self ) :

		return True

	def _updateFromPlug( self ) :

		pass

GafferUI.PlugValueWidget.registerType( GafferImage.Shuffle.ChannelPlug, _ShuffleChannelPlugValueWidget )
