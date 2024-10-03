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

import re
import copy
import functools
import collections

import IECore

import Gaffer
import GafferImage
import GafferUI

from GafferUI.PlugValueWidget import sole

class ChannelMaskPlugValueWidget( GafferUI.PlugValueWidget ) :

	__customMetadataName = "channelMaskPlugValueWidget:custom"

	def __init__( self, plugs, **kw ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, column, plugs, **kw )

		with column :
			self.__menuButton = GafferUI.MenuButton( menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )
			self.__stringPlugValueWidget = GafferUI.StringPlugValueWidget( plugs )

		self.__availableChannels = set()
		self.__currentValue = None

	def _auxiliaryPlugs( self, plug ) :

		result = []
		for imagePlug in GafferImage.ImagePlug.RecursiveInputRange( plug.node() ) :
			result.extend( [ imagePlug["viewNames"], imagePlug["channelNames"] ] )
		return result

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		result = []

		for plug, imagePlugs in zip( plugs, auxiliaryPlugs ) :

			availableChannels = set()
			for viewNamesPlug, channelNamesPlug in [ ( imagePlugs[i], imagePlugs[i+1] ) for i in range( 0, len( imagePlugs ), 2 ) ] :
				for viewName in viewNamesPlug.getValue() :
					availableChannels.update( channelNamesPlug.parent().channelNames( viewName = viewName ) )

			result.append( { "value" : plug.getValue(), "availableChannels" : availableChannels } )

		return result

	def _updateFromValues( self, values, exception ) :

		self.__availableChannels = set().union( *[ v["availableChannels"] for v in values ] )
		self.__currentValue = sole( v["value"] for v in values )

		custom = any( Gaffer.Metadata.value( p, self.__customMetadataName ) for p in self.getPlugs() )
		self.__stringPlugValueWidget.setVisible( custom )

		if custom :
			self.__menuButton.setText( "Custom" )
		elif self.__currentValue is None :
			self.__menuButton.setText( "---" )
		else :
			labels = _CanonicalValue( self.__currentValue ).matchPatterns()
			# Replace match expressions the menu can create
			# with friendlier descriptions.
			for i, label in enumerate( labels ) :

				label = "All" if label == "*" else label
				# Replace preceeding .* with "All "
				label = re.sub( r"^\*\.", "All ", label )
				# Replace trailing .* with " All"
				label = re.sub( r"\.\*$", " All", label )
				# Remove brackets from [RGBAZ] channel lists
				label = re.sub( "(\\[)([RGBAZ]+)(\\])$", lambda m : m.group( 2 ), label )

				labels[i] = label

			if labels :
				self.__menuButton.setText( ", ".join( labels ) )
			else :
				self.__menuButton.setText( "None" )

		self.__menuButton.setErrored( exception is not None )

	def _updateFromMetadata( self ) :

		# Because the button text is determined by a combination of
		# values and metadata.
		self._requestUpdateFromValues()

	def _updateFromEditable( self ) :

		self.__menuButton.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		value = _CanonicalValue( self.__currentValue )
		matchPatterns = value.matchPatterns()
		availableChannels = _CanonicalValue( self.__availableChannels )

		def menuItem( matchPattern ) :

			if matchPattern is not None :
				newValue = copy.deepcopy( value )
				if matchPattern in newValue :
					newValue.remove( matchPattern )
					checkBox = True
				else :
					newValue.add( matchPattern )
					checkBox = False
			else :
				newValue = _CanonicalValue()
				checkBox = not matchPatterns

			newMatchPatterns = newValue.matchPatterns()

			return {
				"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value = " ".join( newMatchPatterns ) ),
				"active" : newMatchPatterns != matchPatterns,
				"checkBox" : checkBox,
			}

		result = IECore.MenuDefinition()

		result.append( "/All", menuItem( "*" ) )
		result.append( "/None", menuItem( None ) )

		for i, layerName in enumerate( sorted( availableChannels.layers.keys() ) ) :

			result.append( "/LayerDivider{0}".format( i ), { "divider" : True } )

			layer = availableChannels.layers[layerName]
			if set( "RGBA" ) & layer.baseNames :

				prefix = "/" + layerName if layerName else "/RGBA"

				result.append( prefix + "/RGB", menuItem( GafferImage.ImageAlgo.channelName( layerName, "[RGB]" ) ) )
				result.append( prefix + "/RGBA", menuItem( GafferImage.ImageAlgo.channelName( layerName, "[RGBA]" ) ) )
				result.append( prefix + "/Divider", { "divider" : True } )
				result.append( prefix + "/R", menuItem( GafferImage.ImageAlgo.channelName( layerName, "R" ) ) )
				result.append( prefix + "/G", menuItem( GafferImage.ImageAlgo.channelName( layerName, "G" ) ) )
				result.append( prefix + "/B", menuItem( GafferImage.ImageAlgo.channelName( layerName, "B" ) ) )
				result.append( prefix + "/A", menuItem( GafferImage.ImageAlgo.channelName( layerName, "A" ) ) )

				layerHasRGBA = True

			auxiliaryBaseNames = sorted( layer.baseNames - set( "RGBA" ) )
			if auxiliaryBaseNames :

				prefix = "/" + layerName if layerName else ""
				if layerName and ( set( "RGBA" ) & layer.baseNames ) :
					result.append( prefix + "/AuxiliaryDivider", { "divider" : True } )

				for baseName in auxiliaryBaseNames :
					result.append( prefix + "/" + baseName, menuItem( GafferImage.ImageAlgo.channelName( layerName, baseName ) ) )

		result.append( "/CustomDivider", { "divider" : True } )
		result.append(
			"/Custom",
			{
				"command" : Gaffer.WeakMethod( self.__toggleCustom ),
				"checkBox" : any( Gaffer.Metadata.value( p, self.__customMetadataName ) for p in self.getPlugs() ),
			}
		)

		return result

	def __setValue( self, unused, value ) :

		with Gaffer.UndoScope( self.scriptNode() ) :
			for plug in self.getPlugs() :
				plug.setValue( value )

	def __toggleCustom( self, checked ) :

		with Gaffer.UndoScope( self.scriptNode() ) :
			for plug in self.getPlugs() :
				if not checked :
					Gaffer.Metadata.deregisterValue( plug, self.__customMetadataName )
				else :
					Gaffer.Metadata.registerValue( plug, self.__customMetadataName, True )

# Because channel masks can contain arbitary match patterns,
# there are multiple ways of expressing the same thing - for
# instance, "R G B" is equivalent to "[RGB]". The _CanonicalValue
# class normalises such patterns for ease of editing.
class _CanonicalValue( object ) :

	class Layer( object ) :

		def __init__( self ) :

			self.baseNames = set()

		def add( self, baseNameMatchPattern ) :

			for n in self.__canonicalBaseNames( baseNameMatchPattern ) :
				self.baseNames.add( n )

		def remove( self, baseNameMatchPattern ) :

			for n in self.__canonicalBaseNames( baseNameMatchPattern ) :
				self.baseNames.remove( n )

		@staticmethod
		def __canonicalBaseNames( baseNameMatchPattern ) :

			m = re.match( "\\[([RGBAZ]+)\\]", baseNameMatchPattern )
			if m :
				return list( m.group( 1 ) )
			else :
				return [ baseNameMatchPattern ]

		def __contains__( self, baseNameMatchPattern ) :

			for baseName in self.__canonicalBaseNames( baseNameMatchPattern ) :
				if baseName not in self.baseNames :
					return False

			return True

		def __deepcopy__( self, memo ) :

			c = _CanonicalValue.Layer()
			c.baseNames = copy.deepcopy( self.baseNames, memo )
			return c

	def __init__( self, value = None ) :

		self.layers = collections.defaultdict( self.Layer )

		if value is not None :
			if isinstance( value, str ) :
				value = value.split()
			for v in value :
				self.add( v )

	def add( self, channelNameMatchPattern ) :

		layerName = GafferImage.ImageAlgo.layerName( channelNameMatchPattern )
		self.layers[layerName].add( GafferImage.ImageAlgo.baseName( channelNameMatchPattern ) )

	def remove( self, channelNameMatchPattern ) :

		layerName = GafferImage.ImageAlgo.layerName( channelNameMatchPattern )
		self.layers[layerName].remove( GafferImage.ImageAlgo.baseName( channelNameMatchPattern ) )

	# Returns a minimal set of match patterns needed
	# for this value. For instance, if it contains "*",
	# then no other pattern will be returned.
	def matchPatterns( self ) :

		if "*" in self :
			return [ "*" ]

		result = []
		for layerName in sorted( self.layers.keys() ) :

			layer = self.layers[layerName]

			if "*" in layer.baseNames :
				# Matches everything, so no need to consider anything else
				result.append( GafferImage.ImageAlgo.channelName( layerName, "*" ) )
				continue

			# Format RGBAZ into a single character class
			rgbaz = [ c for c in "RGBAZ" if c in layer.baseNames ]
			if rgbaz :
				result.append(
					GafferImage.ImageAlgo.channelName(
						layerName,
						"[{0}]".format( "".join( rgbaz ) ),
					)
				)

			# Format the rest as additional strings
			for baseName in layer.baseNames.difference( set( "RGBAZ" ) ) :
				result.append(  GafferImage.ImageAlgo.channelName( layerName, baseName ) )

		return result

	def __contains__( self, channelNameMatchPattern ) :

		layerName = GafferImage.ImageAlgo.layerName( channelNameMatchPattern )
		baseName = GafferImage.ImageAlgo.baseName( channelNameMatchPattern )
		return baseName in self.layers[layerName]

	def __deepcopy__( self, memo ) :

			c = _CanonicalValue()
			c.layers = copy.deepcopy( self.layers, memo )
			return c
