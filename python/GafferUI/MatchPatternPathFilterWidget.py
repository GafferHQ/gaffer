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

class MatchPatternPathFilterWidget( GafferUI.PathFilterWidget ) :

	def __init__( self, pathFilter, **kw ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=2, borderWidth=0 )

		GafferUI.PathFilterWidget.__init__( self, self.__row, pathFilter, **kw )

		with self.__row :

			self.__enabledWidget = GafferUI.BoolWidget()
			self.__enabledWidget.stateChangedSignal().connect( Gaffer.WeakMethod( self.__enabledStateChanged ), scoped = False )

			self.__propertyButton = GafferUI.MenuButton(
				image = "collapsibleArrowDown.png",
				hasFrame = False,
				menu = GafferUI.Menu( Gaffer.WeakMethod( self.__propertyMenuDefinition ) ),
			)

			self.__patternWidget = GafferUI.TextWidget()

			if hasattr( self.__patternWidget._qtWidget(), "setPlaceholderText" ) :
				# setPlaceHolderText appeared in qt 4.7, nuke (6.3 at time of writing) is stuck on 4.6.
				self.__patternWidget._qtWidget().setPlaceholderText( "Filter..." )

			self.__patternWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__patternEditingFinished ), scoped = False )
			self.__patternWidget.textChangedSignal().connect( Gaffer.WeakMethod( self.__patternTextChanged ), scoped = False )

		self._updateFromPathFilter()

	def _updateFromPathFilter( self ) :

		editable = False
		with IECore.IgnoredExceptions( KeyError ) :
			editable = self.pathFilter().userData()["UI"]["editable"].value

		self.__enabledWidget.setVisible( not editable )
		self.__propertyButton.setVisible( editable )
		self.__patternWidget.setVisible( editable )

		label = str( self.pathFilter() )
		with IECore.IgnoredExceptions( KeyError ) :
			label = self.pathFilter().userData()["UI"]["label"].value
		self.__enabledWidget.setText( label )

		invertEnabled = False
		with IECore.IgnoredExceptions( KeyError ) :
			invertEnabled = self.pathFilter().userData()["UI"]["invertEnabled"].value

		self.__enabledWidget.setState( self.pathFilter().getEnabled() is not invertEnabled )
		self.__patternWidget.setText( " ".join( self.pathFilter().getMatchPatterns() ) )

	def __enabledStateChanged( self, widget ) :

		assert( widget is self.__enabledWidget )

		invertEnabled = False
		with IECore.IgnoredExceptions( KeyError ) :
			invertEnabled = self.pathFilter().userData()["UI"]["invertEnabled"].value

		with Gaffer.Signals.BlockedConnection( self._pathFilterChangedConnection() ) :
			self.pathFilter().setEnabled( widget.getState() is not invertEnabled )

	def __patternEditingFinished( self, textWidget ) :

		assert( textWidget is self.__patternWidget )

		self.__updateFilterMatchPatterns()

	def __patternTextChanged( self, textWidget ) :

		assert( textWidget is self.__patternWidget )

		if self.__patternWidget.getText()=="" :
			self.__updateFilterMatchPatterns()

	def __updateFilterMatchPatterns( self ) :

		t = self.__patternWidget.getText()

		patterns = []
		for pattern in t.split() :
			if "*" not in pattern :
				pattern = "*" + pattern + "*"
			patterns.append( pattern )

		with Gaffer.Signals.BlockedConnection( self._pathFilterChangedConnection() ) :
			self.pathFilter().setMatchPatterns( patterns )
			self.pathFilter().setEnabled( len( patterns ) )

	def __propertyMenuDefinition( self ) :

		## \todo Make this configurable
		propertiesAndLabels = (
			( "name", "Name" ),
			( "fileSystem:owner", "Owner" ),
		)

		menuDefinition = IECore.MenuDefinition()
		for property, label in propertiesAndLabels :
			menuDefinition.append(
				"/" + label,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setPropertyName ), property ),
					"checkBox" : property == self.pathFilter().getPropertyName()
				}
			)

		return menuDefinition

	def __setPropertyName( self, property, checked ) :

		with Gaffer.Signals.BlockedConnection( self._pathFilterChangedConnection() ) :
			self.pathFilter().setPropertyName( property )

GafferUI.PathFilterWidget.registerType( Gaffer.MatchPatternPathFilter, MatchPatternPathFilterWidget )
