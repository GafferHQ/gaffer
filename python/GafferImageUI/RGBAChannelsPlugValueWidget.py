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

class RGBAChannelsPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__menuButton = GafferUI.MenuButton( menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )
		self.__menuButton._qtWidget().setMinimumWidth( 150 )

		GafferUI.PlugValueWidget.__init__( self, self.__menuButton, plug, **kw )

		self._updateFromPlug()

	def _updateFromPlug( self ) :

		with self.getContext() :
			value = self.getPlug().getValue()

		assert( len( value ) == 4 )

		layers = [ GafferImage.ImageAlgo.layerName( x ) for x in value ]
		channels = [ GafferImage.ImageAlgo.baseName( x ) for x in value ]

		# Figure out a good label for the current list of channels.
		# Start out with "Custom" to represent something arbitrary
		# chosen via scripting, and then assign more descriptive labels
		# to anything that can be chosen via the menu.
		text = "Custom"
		if len( set( layers ) ) == 1 :
			prefix = layers[0] + "." if layers[0] else ""
			if channels == [ "R", "G", "B", "A" ] :
				text = prefix + "RGBA"
			elif len( set( channels ) ) == 1 :
				text = prefix + channels[0]

		self.__menuButton.setText( text )
		self.__menuButton.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		image = next( iter( self.getPlug().node().children( GafferImage.ImagePlug ) ) )
		channelNames = []
		with self.getContext() :
			with IECore.IgnoredExceptions( Exception ) :
				channelNames = image["channelNames"].getValue()

		result = IECore.MenuDefinition()
		if not channelNames :
			result.append( "/No channels available", { "active" : False } )
			return result

		added = set()
		nonStandardLayers = set( [ GafferImage.ImageAlgo.layerName( x ) for x in channelNames
			if GafferImage.ImageAlgo.baseName( x ) not in [ "R", "G", "B", "A" ] ] )

		for channelName in sorted( channelNames, key = GafferImage.ImageAlgo.layerName ) :

			if GafferImage.ImageAlgo.baseName( channelName ) in [ "R", "G", "B", "A" ] :
				layerName = GafferImage.ImageAlgo.layerName( channelName )
				prefix = layerName + "." if layerName else ""
				text = prefix + "RGBA"
				value = [ prefix + x for x in [ "R", "G", "B", "A" ] ]
			else :
				text = channelName
				value = [ channelName ] * 4

			if text in added :
				continue

			added.add( text )

			if not GafferImage.ImageAlgo.layerName( text ) in nonStandardLayers:
				# If there are only the standard channels, we don't need a submenu
				text = text.replace( ".RGBA", "" )

			result.append(
				"/" + text.replace( ".", "/" ),
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value = value ),
					"checkBox" : text == self.__menuButton.getText(),
				}
			)

		return result

	def __setValue( self, unused, value ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().setValue( IECore.StringVectorData( value ) )

