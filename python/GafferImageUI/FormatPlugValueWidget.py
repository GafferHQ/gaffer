##########################################################################
#
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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
import imath

import IECore
import Gaffer
import GafferUI
import GafferImage

from GafferUI.PlugValueWidget import sole

class FormatPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		grid = GafferUI.GridContainer( spacing = 4 )
		GafferUI.PlugValueWidget.__init__( self, grid, plugs, **kw )

		self.__menuButton = GafferUI.MenuButton( menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )
		grid[0:2,0] = self.__menuButton

		self.__minLabel = GafferUI.Label( "Min" )
		grid.addChild( self.__minLabel, index = ( 0, 1 ), alignment = ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Center ) )

		self.__minWidget = GafferUI.CompoundNumericPlugValueWidget( plugs = [] )
		grid[1,1] = self.__minWidget

		self.__maxLabel = GafferUI.Label( "Max" )
		grid.addChild( self.__maxLabel, index = ( 0, 2 ), alignment = ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Center ) )

		self.__maxWidget = GafferUI.CompoundNumericPlugValueWidget( plugs = [] )
		grid[1,2] = self.__maxWidget

		self.__pixelAspectLabel = GafferUI.Label( "Pixel Aspect" )
		grid.addChild( self.__pixelAspectLabel, index = ( 0, 3 ), alignment = ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Center ) )

		self.__pixelAspectWidget = GafferUI.NumericPlugValueWidget( plugs = [] )
		grid[1,3] = self.__pixelAspectWidget

		self._addPopupMenu( self.__menuButton )

		self.__currentFormat = None
		self.__attachChildPlugValueWidgets()

	def setPlugs( self, plugs ) :

		GafferUI.PlugValueWidget.setPlugs( self, plugs )
		self.__attachChildPlugValueWidgets()

	def _updateFromValues( self, values, exception ) :

		self.__currentFormat = sole( values )
		custom = any( Gaffer.Metadata.value( p, "formatPlugValueWidget:mode" ) == "custom" for p in self.getPlugs() )

		if self.__currentFormat is not None :
			if self.__currentFormat == GafferImage.Format() :
				# The empty display window of the default format is
				# confusing to look at, so turn off custom mode.
				custom = False
			elif not GafferImage.Format.name( self.__currentFormat ) :
				# If the chosen format hasn't been registered,
				# force custom mode even if it hasn't been
				# asked for explicitly.
				custom = True

		self.__menuButton.setText(
			"Custom" if custom
			else
			( _formatLabel( self.__currentFormat, self.context() ) if self.__currentFormat is not None else "---" )
		)

		nonZeroOrigin = any( v.getDisplayWindow().min() != imath.V2i( 0 ) for v in values )
		for widget in ( self.__minLabel, self.__minWidget ) :
			widget.setVisible( custom and nonZeroOrigin )

		for widget in ( self.__maxLabel, self.__maxWidget, self.__pixelAspectLabel, self.__pixelAspectWidget ) :
			widget.setVisible( custom )

		self.__maxLabel.setText( "Max" if nonZeroOrigin else "Size" )

		self.__menuButton.setErrored( exception is not None )

	def _valuesDependOnContext( self ) :

		# We use the context in `_updateFromValues()`, so must return True
		# here so that it is called when the context changes.
		return True

	def _updateFromMetadata( self ) :

		# Account for query to "formatPlugValueWidget:mode"
		# in `_updateFromValues()`.
		self._requestUpdateFromValues()

	def _updateFromEditable( self ) :

		self.__menuButton.setEnabled( self._editable() )

	def __attachChildPlugValueWidgets( self ) :

		self.__minWidget.setPlugs( [ p["displayWindow"]["min"] for p in self.getPlugs() ] )
		self.__maxWidget.setPlugs( [ p["displayWindow"]["max"] for p in self.getPlugs() ] )
		self.__pixelAspectWidget.setPlugs( [ p["pixelAspect"] for p in self.getPlugs() ] )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()
		if not self.getPlugs() :
			return result

		formats = [ GafferImage.Format.format( n ) for n in GafferImage.Format.registeredFormats() ]
		if not any( p.ancestor( Gaffer.ScriptNode ).isSame( p.node() ) for p in self.getPlugs() ) :
			formats.insert( 0, GafferImage.Format() )

		modeIsCustom = any( Gaffer.Metadata.value( p, "formatPlugValueWidget:mode" ) == "custom" for p in self.getPlugs() )
		for fmt in formats :
			result.append(
				"/" + _formatLabel( fmt, self.context() ),
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__applyFormat ), fmt = fmt ),
					"checkBox" : fmt == self.__currentFormat and not modeIsCustom,
				}
			)

		result.append( "/CustomDivider", { "divider" : True } )

		result.append(
			"/Custom",
			{
				"command" : Gaffer.WeakMethod( self.__applyCustomFormat ),
				"checkBox" : modeIsCustom or self.__currentFormat not in formats,
			}
		)

		return result

	def __applyFormat( self, unused, fmt ) :

		with Gaffer.UndoScope( self.scriptNode() ) :
			for plug in self.getPlugs() :
				Gaffer.Metadata.registerValue( plug, "formatPlugValueWidget:mode", "standard" )
				plug.setValue( fmt )

	def __applyCustomFormat( self, unused ) :

		with Gaffer.UndoScope( self.scriptNode() ) :

			if self.__currentFormat == GafferImage.Format() :
				# Format is empty. It's kindof confusing to display that
				# to the user in the custom fields, so take the default
				# format and set it explicitly as a starting point for
				# editing.
				for p in self.getPlugs() :
					p.setValue( GafferImage.FormatPlug.getDefaultFormat( self.context() ) )

			# When we first switch to custom mode, the current value will
			# actually be one of the registered formats. So we use this
			# metadata value to keep track of the user's desire to be in
			# custom mode despite of this fact. We use metadata rather than
			# a member variable so that undo will take us back to the non-custom
			# state automatically.
			for p in self.getPlugs() :
				Gaffer.Metadata.registerValue( p, "formatPlugValueWidget:mode", "custom" )

GafferUI.PlugValueWidget.registerType( GafferImage.FormatPlug, FormatPlugValueWidget )

def _formatLabel( fmt, context ) :

	if fmt == GafferImage.Format() :
		return "Default ( {} )".format( GafferImage.FormatPlug.getDefaultFormat( context ) )
	else :
		return "{} ( {} )".format(
			GafferImage.Format.name( fmt ) or "Custom",
			fmt
		)

def __spreadsheetFormatter( plug, forToolTip ) :

	return _formatLabel( plug.getValue(), Gaffer.Context.current() )

GafferUI.SpreadsheetUI.registerValueFormatter( GafferImage.FormatPlug, __spreadsheetFormatter )
