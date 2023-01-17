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
import GafferImage

from GafferUI.PlugValueWidget import sole

class RGBAChannelsPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__menuButton = GafferUI.MenuButton( menu = GafferUI.Menu( Gaffer.WeakMethod( self._menuDefinition ) ) )
		self.__menuButton._qtWidget().setMinimumWidth( 150 )

		GafferUI.PlugValueWidget.__init__( self, self.__menuButton, plugs, **kw )

		self.__availableChannels = set()
		self.__currentValue = None

	def _auxiliaryPlugs( self, plug ) :

		firstInputImage = next( GafferImage.ImagePlug.RecursiveInputRange( plug.node() ), None )
		return [ firstInputImage ] if firstInputImage is not None else []

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		result = []

		for plug, imagePlugs in zip( plugs, auxiliaryPlugs ) :

			availableChannels = set()
			for viewName in imagePlugs[0].viewNames() :
				availableChannels.update( imagePlugs[0].channelNames( viewName = viewName ) )

			result.append( { "value" : plug.getValue(), "availableChannels" : availableChannels } )

		return result

	def _updateFromValues( self, values, exception ) :

		self.__availableChannels = set().union( *[ v["availableChannels"] for v in values ] )
		self.__currentValue = sole( v["value"] for v in values )

		if self.__currentValue is None :
			self.__menuButton.setText( "---" )
			return

		layers = [ GafferImage.ImageAlgo.layerName( x ) for x in self.__currentValue ]
		channels = [ GafferImage.ImageAlgo.baseName( x ) for x in self.__currentValue ]

		# Figure out a good label for the current list of channels.
		# Start out with "Custom" to represent something arbitrary
		# chosen via scripting, and then assign more descriptive labels
		# to anything that can be chosen via the menu.
		# > Note : We don't use `_rgbaChannels()` to generate
		# > our label because it depends on the currently available
		# > channels. We need a label even if the channels don't
		# > currently exist.
		text = "Custom"
		if len( set( layers ) ) == 1 :
			prefix = layers[0] + "." if layers[0] else ""
			if channels == [ "R", "G", "B", "A" ] :
				text = prefix + "RGBA"
			elif len( set( channels ) ) == 1 :
				text = prefix + channels[0]

		self.__menuButton.setText( text )
		self.__menuButton.setErrored( exception is not None )

	def _updateFromEditable( self ) :

		self.__menuButton.setEnabled( self._editable() )

	# Returns a dictionary mapping from display name to sets of `[ R, G, B, A ]`
	# channels. Maybe belongs in ImageAlgo.h?
	def _rgbaChannels( self ) :

		result = collections.OrderedDict()

		nonStandardLayers = {
			GafferImage.ImageAlgo.layerName( c ) for c in self.__availableChannels
			if GafferImage.ImageAlgo.baseName( c ) not in [ "R", "G", "B", "A" ]
		}

		for channelName in GafferImage.ImageAlgo.sortedChannelNames( self.__availableChannels ) :

			if GafferImage.ImageAlgo.baseName( channelName ) in [ "R", "G", "B", "A" ] :
				layerName = GafferImage.ImageAlgo.layerName( channelName )
				prefix = layerName + "." if layerName else ""
				text = prefix + "RGBA"
				value = IECore.StringVectorData( [ prefix + x for x in [ "R", "G", "B", "A" ] ] )
			else :
				text = channelName
				value = IECore.StringVectorData( [ channelName ] * 4 )

			if not GafferImage.ImageAlgo.layerName( text ) in nonStandardLayers :
				# If there are only standard channels, we don't need to differentiate
				# them from non-standard channels.
				text = text.replace( ".RGBA", "" )

			if text in result :
				continue

			result[text] = value

		return result

	def _menuDefinition( self ) :

		rgbaChannels = self._rgbaChannels()

		result = IECore.MenuDefinition()
		if not rgbaChannels :
			result.append( "/No channels available", { "active" : False } )
			return result

		for text, value in rgbaChannels.items() :

			result.append(
				"/" + text.replace( ".", "/" ),
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value = value ),
					"checkBox" : value == self.__currentValue,
				}
			)

		return result

	def __setValue( self, unused, value ) :

		with Gaffer.UndoScope( next( iter( self.getPlugs() ) ).ancestor( Gaffer.ScriptNode ) ) :
			for plug in self.getPlugs() :
				plug.setValue( value )
