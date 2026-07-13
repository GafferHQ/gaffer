##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

import Gaffer

from Qt import QtCore

from ._PlugTableModelBase import _PlugTableModelBase

## A model providing data for the Results TableView in the SpreadsheetUI.
# Data is sourced from the values of a Spreadsheet's `out` plug.
class _OutPlugTableModel( _PlugTableModelBase ) :

	def __init__( self, outPlug, rowsPlug, parent = None ) :

		_PlugTableModelBase.__init__( self, outPlug, parent )

		self.__outPlug = outPlug
		self.__rowsPlug = rowsPlug

		self.__plugDirtiedConnection = self.__outPlug.node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ), scoped = True )
		self.__columnAddedConnection = self.__outPlug.childAddedSignal().connect( Gaffer.WeakMethod( self.__columnsChanged ), scoped = True )
		self.__columnRemovedConnection = self.__outPlug.childRemovedSignal().connect( Gaffer.WeakMethod( self.__columnsChanged ), scoped = True )

	# Methods of our own
	# ------------------

	def rowsPlug( self ) :

		return self.__rowsPlug

	def plugForIndex( self, index ) :

		if not index.isValid() or index.column() >= len( self.__outPlug ) :
			return None

		return self.__outPlug[ index.column() ]

	def valuePlugForIndex( self, index ) :

		return self.plugForIndex( index )

	def indexForPlug( self, plug ) :

		for column, outChild in enumerate( self.__outPlug ) :
			if plug == outChild or outChild.isAncestorOf( plug ) :
				return self.index( 0, column )

		return QtCore.QModelIndex()

	# Overrides for methods inherited from QAbstractTableModel
	# --------------------------------------------------------

	def rowCount( self, parent = QtCore.QModelIndex() ) :

		if parent.isValid() :
			return 0

		return 1

	def columnCount( self, parent = QtCore.QModelIndex() ) :

		if parent.isValid() :
			return 0

		return len( self.__outPlug )

	def headerData( self, section, orientation, role ) :

		# The Results table header is always hidden, so we provide no header data (see _PlugTableView).
		return None

	def flags( self, index ) :

		# Always selectable and enabled, but never editable.
		return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

	def presentsCheckstate( self, index ) :

		return isinstance( self.valuePlugForIndex( index ), Gaffer.BoolPlug )

	def _cellPlugEnabledData( self, index ) :

		plug = self.plugForIndex( index )

		enabled = True
		if isinstance( plug, ( Gaffer.NameValuePlug, Gaffer.OptionalValuePlug, Gaffer.TweakPlug ) ) :
			with self._context() :
				try :
					enabled = plug["enabled"].getValue()
				except :
					return None

		return enabled

	# Methods of our own
	# ------------------

	def __plugDirtied( self, plug ) :

		index = self.indexForPlug( plug )
		if index.isValid() :
			self.dataChanged.emit( index, index )

	def __columnsChanged( self, outPlug, childPlug ) :

		self._emitModelReset()
