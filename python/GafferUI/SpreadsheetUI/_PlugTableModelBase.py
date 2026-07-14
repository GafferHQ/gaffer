##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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
import imath

import Gaffer
import GafferUI

from Qt import QtCore

from . import _Formatting

## Base class for models that provide data for SpreadsheetUI TableViews.
class _PlugTableModelBase( QtCore.QAbstractTableModel ) :

	CellPlugEnabledRole = QtCore.Qt.UserRole
	ActiveRole = CellPlugEnabledRole + 1

	def __init__( self, plug, parent = None ) :

		QtCore.QAbstractTableModel.__init__( self, parent )

		self.__plug = plug

		self.__contextTracker = GafferUI.ContextTracker.acquireForFocus( plug )
		self.__contextTrackerChangedConnection = self.__contextTracker.changedSignal().connect( Gaffer.WeakMethod( self.__contextTrackerChanged ), scoped = True )
		self.__context = None
		self.__contextTrackerChanged( self.__contextTracker )

	## Must be implemented by subclasses to return the value plug
	# for the provided index.
	def valuePlugForIndex( self, index ) :

		raise NotImplementedError

	# Decorations
	# ===========

	## Returns the decoration for the specified plug.
	@classmethod
	def decoration( cls, plug ) :

		decorator = cls.__valueDecorators.get( plug.__class__ )
		return decorator( plug ) if decorator is not None else None

	## Registers a function to return a decoration to be shown
	# alongside the formatted value. Currently the only supported
	# return type is `Color3f`.
	@classmethod
	def registerDecoration( cls, plugType, decorator ) :

		cls.__valueDecorators[plugType] = decorator

	__valueDecorators = {}

	def data( self, index, role ) :

		if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole :

			return self._formatValue( index )

		elif role == QtCore.Qt.DecorationRole :

			return self._decorationData( index )

		elif role == QtCore.Qt.CheckStateRole :

			return self._checkStateData( index )

		elif role == QtCore.Qt.ToolTipRole :

			return self._formatValue( index, forToolTip = True )

		elif role == self.CellPlugEnabledRole :

			return self._cellPlugEnabledData( index )

		elif role == self.ActiveRole :

			return self._activeData( index )

		return None

	# `data()` helpers. Can be overridden by subclasses to customise behaviour.

	def _formatValue( self, index, forToolTip = False ) :

		plug = self.valuePlugForIndex( index )

		if not forToolTip and isinstance( plug, Gaffer.BoolPlug ) :
			# Dealt with via CheckStateRole
			return None

		try :
			with self.__context :
				return _Formatting.formatValue( plug, forToolTip )
		except :
			return None

	def _decorationData( self, index ) :

		plug = self.valuePlugForIndex( index )
		with self.__context :
			try :
				value = self.decoration( plug )
			except :
				return None

		if value is None :
			return None
		elif isinstance( value, imath.Color3f ) :
			displayTransform = GafferUI.Widget._owner( self.parent() ).displayTransform()
			return GafferUI.Widget._qtColor( displayTransform( value ) )
		else :
			IECore.msg( IECore.Msg.Level.Error, "Spreadsheet Decoration", "Unsupported type {}".format( type( value ) ) )
			return None

	def _checkStateData( self, index ) :

		plug = self.valuePlugForIndex( index )
		if not isinstance( plug, Gaffer.BoolPlug ) :
			return None

		with self.__context :
			try :
				value = plug.getValue()
			except :
				return None

		return QtCore.Qt.Checked if value else QtCore.Qt.Unchecked

	def _cellPlugEnabledData( self, index ) :

		return True

	def _activeData( self, index ) :

		return None

	def _emitModelReset( self ) :

		self.beginResetModel()
		self.endResetModel()

	def _context( self ) :

		return self.__context

	def __contextTrackerChanged( self, contextTracker ) :

		context = self.__contextTracker.context( self.__plug )
		if self.__context is None or self.__context.hash() != context.hash() :
			self.__context = context
			self._emitModelReset()

# Plug decorators
# ---------------

def __colorPlugDecorator( plug ) :

	return plug.getValue()

_PlugTableModelBase.registerDecoration( Gaffer.Color3fPlug, __colorPlugDecorator )
