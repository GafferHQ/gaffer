##########################################################################
#
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI

## This class forms the base class for all uis which manipulate PathFilters.
class PathFilterWidget( GafferUI.Widget ) :

	def __init__( self, topLevelWidget, pathFilter, **kw ) :

		GafferUI.Widget.__init__( self, topLevelWidget, **kw )

		self.__pathFilter = pathFilter
		self.__pathFilterChangedConnection = self.__pathFilter.changedSignal().connect( Gaffer.WeakMethod( self.__pathFilterChanged ), scoped = False )

	## Returns the PathFilter object this UI represents.
	def pathFilter( self ) :

		return self.__pathFilter

	## Must be implemented by subclasses to update the UI when the filter
	# changes in some way. To temporarily suspend calls to this function, use
	# Gaffer.Signals.BlockedConnection( self._pathFilterChangedConnection() ).
	def _updateFromPathFilter( self ) :

		raise NotImplementedError

	## Returns the connection
	def _pathFilterChangedConnection( self ) :

		return self.__pathFilterChangedConnection

	def __pathFilterChanged( self, pathFilter ) :

		assert( pathFilter.isSame( self.__pathFilter ) )

		self._updateFromPathFilter()

	## Creates a PathFilterWidget instance for the specified pathFilter. Returns None
	# if no suitable widget exists.
	@classmethod
	def create( cls, pathFilter ) :

		visible = True
		with IECore.IgnoredExceptions( KeyError ) :
			visible = pathFilter.userData()["UI"]["visible"].value

		if not visible :
			return None

		c = pathFilter.__class__
		while c is not None :

			creator = cls.__typesToCreators.get( c, None )
			if creator is not None :
				return creator( pathFilter )

			c = c.__bases__[0] if c.__bases__ else None

		return None

	## Registers a subclass of PathFilterWidget to be used with a specific pathFilter type.
	@classmethod
	def registerType( cls, pathFilterClass, widgetCreationFunction ) :

		cls.__typesToCreators[pathFilterClass] = widgetCreationFunction

	__typesToCreators = {}

class BasicPathFilterWidget( PathFilterWidget ) :

	def __init__( self, pathFilter ) :

		self.__checkBox = GafferUI.BoolWidget( str( pathFilter ) )

		PathFilterWidget.__init__( self, self.__checkBox, pathFilter )

		self.__checkBox.stateChangedSignal().connect( Gaffer.WeakMethod( self.__stateChanged ), scoped = False )

		self._updateFromPathFilter()

	def _updateFromPathFilter( self ) :

		label = str( self.pathFilter() )
		with IECore.IgnoredExceptions( KeyError ) :
			label = self.pathFilter().userData()["UI"]["label"].value
		self.__checkBox.setText( label )

		invertEnabled = False
		with IECore.IgnoredExceptions( KeyError ) :
			invertEnabled = self.pathFilter().userData()["UI"]["invertEnabled"].value
		self.__checkBox.setState( self.pathFilter().getEnabled() is not invertEnabled )

	def __stateChanged( self, checkBox ) :

		invertEnabled = False
		with IECore.IgnoredExceptions( KeyError ) :
			invertEnabled = self.pathFilter().userData()["UI"]["invertEnabled"].value
		self.pathFilter().setEnabled( checkBox.getState() is not invertEnabled )

PathFilterWidget.registerType( Gaffer.PathFilter, BasicPathFilterWidget )
