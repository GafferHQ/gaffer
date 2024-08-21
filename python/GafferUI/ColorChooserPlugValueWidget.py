##########################################################################
#
#  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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
from GafferUI.PlugValueWidget import sole

class ColorChooserPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__colorChooser = GafferUI.ColorChooser()

		GafferUI.PlugValueWidget.__init__( self, self.__colorChooser, plugs, **kw )

		self.__colorChooser.setSwatchesVisible( False )

		options = self.__colorChooserOptions()

		if "visibleComponents" in options :
			self.__colorChooser.setVisibleComponents( options["visibleComponents"].value )

		if "staticComponent" in options :
			self.__colorChooser.setColorFieldStaticComponent( options["staticComponent"].value )

		if "colorFieldVisible" in options :
			self.__colorChooser.setColorFieldVisible( options["colorFieldVisible"].value )

		self.__colorChangedConnection = self.__colorChooser.colorChangedSignal().connect(
			Gaffer.WeakMethod( self.__colorChanged ), scoped = False
		)

		self.__colorChooser.visibleComponentsChangedSignal().connect(
			functools.partial( Gaffer.WeakMethod( self.__colorChooserVisibleComponentsChanged ) ),
			scoped = False
		)
		self.__colorChooser.staticComponentChangedSignal().connect(
			functools.partial( Gaffer.WeakMethod( self.__colorChooserStaticComponentChanged ) ),
			scoped = False
		)
		self.__colorChooser.colorFieldVisibleChangedSignal().connect(
			functools.partial( Gaffer.WeakMethod( self.__colorChooserColorFieldVisibleChanged ) ),
			scoped = False
		)

		self.__lastChangedReason = None
		self.__mergeGroupId = 0

	def _updateFromValues( self, values, exception ) :

		# ColorChooser only supports one colour, and doesn't have
		# an "indeterminate" state, so when we have multiple plugs
		# the best we can do is take an average.
		if len( values ) :
			color = sum( values ) / len( values )
		else :
			color = imath.Color4f( 0 )

		with Gaffer.Signals.BlockedConnection( self.__colorChangedConnection ) :
			self.__colorChooser.setColor( color )
			self.__colorChooser.setErrored( exception is not None )

	def _updateFromEditable( self ) :

		self.__colorChooser.setEnabled( self.__allComponentsEditable() )

	def __colorChanged( self, colorChooser, reason ) :

		if not GafferUI.ColorChooser.changesShouldBeMerged( self.__lastChangedReason, reason ) :
			self.__mergeGroupId += 1
		self.__lastChangedReason = reason

		with Gaffer.UndoScope(
			next( iter( self.getPlugs() ) ).ancestor( Gaffer.ScriptNode ),
			mergeGroup = "ColorPlugValueWidget%d%d" % ( id( self, ), self.__mergeGroupId )
		) :

			with self._blockedUpdateFromValues() :
				for plug in self.getPlugs() :
					plug.setValue( self.__colorChooser.getColor() )

	def __colorChooserOptionChanged( self, value, key ) :

		if Gaffer.Metadata.value( "colorChooser:inlineOptions", "userDefault" ) is None :
			sessionOptions = Gaffer.Metadata.value( "colorChooser:inlineOptions", "sessionDefault" )
			if sessionOptions is None :
				sessionOptions = IECore.CompoundData()
				Gaffer.Metadata.registerValue( "colorChooser:inlineOptions", "sessionDefault", sessionOptions )

			sessionOptions.update( { key: value } )

		for p in self.getPlugs() :
			plugOptions = Gaffer.Metadata.value( p, "colorChooser:inlineOptions" )
			if plugOptions is None :
				plugOptions = IECore.CompoundData()
				Gaffer.Metadata.registerValue( p, "colorChooser:inlineOptions", plugOptions, persistent = False )

			plugOptions.update( { key: value } )

	def __colorChooserVisibleComponentsChanged( self, colorChooser ) :

		self.__colorChooserOptionChanged( colorChooser.getVisibleComponents(), "visibleComponents" )

	def __colorChooserStaticComponentChanged( self, colorChooser ) :

		self.__colorChooserOptionChanged( colorChooser.getColorFieldStaticComponent(), "staticComponent" )

	def __colorChooserColorFieldVisibleChanged( self, colorChooser ) :

		self.__colorChooserOptionChanged( colorChooser.getColorFieldVisible(), "colorFieldVisible" )

	def __colorChooserOptions( self ) :

		v = sole( Gaffer.Metadata.value( p, "colorChooser:inlineOptions" ) for p in self.getPlugs() )
		if v is None :
			v  = Gaffer.Metadata.value( "colorChooser:inlineOptions", "userDefault" )
			if v is None :
				v = Gaffer.Metadata.value( "colorChooser:inlineOptions", "sessionDefault" ) or IECore.CompoundData()

		return v

	def __allComponentsEditable( self ) :

		if not self._editable() :
			return False

		# The base class `_editable()` call doesn't consider that
		# child plugs might be read only, so check for that.
		## \todo Should the base class be doing this for us?
		for plug in self.getPlugs() :
			for child in Gaffer.Plug.Range( plug ) :
				if Gaffer.MetadataAlgo.readOnly( child ) :
					return False

		return True
