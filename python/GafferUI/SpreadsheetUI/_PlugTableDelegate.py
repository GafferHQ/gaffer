##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

from ._PlugTableModel import _PlugTableModel

class _PlugTableDelegate( QtWidgets.QStyledItemDelegate ) :

	def __init__( self, parent = None ) :

		QtWidgets.QStyledItemDelegate.__init__( self, parent )

	def paint( self, painter, option, index ) :

		QtWidgets.QStyledItemDelegate.paint( self, painter, option, index )

		flags = index.flags()
		enabled = flags & QtCore.Qt.ItemIsEnabled and flags & QtCore.Qt.ItemIsEditable
		cellPlugEnabled = index.data( _PlugTableModel.CellPlugEnabledRole )

		if option.state & QtWidgets.QStyle.State_HasFocus :

			if option.state & QtWidgets.QStyle.State_Selected :
				focusColour = QtGui.QColor( QtCore.Qt.white )
			else :
				focusColour = option.palette.color( QtGui.QPalette.Highlight )

			focusColour.setAlpha( 30 )
			painter.fillRect( option.rect, focusColour )

		if index.data( _PlugTableModel.ActiveRole ) :
			pen = QtGui.QPen( QtGui.QColor( 240, 220, 40, 150 ) )
			pen.setWidth( 2 )
			painter.setPen( pen )
			painter.drawLine( option.rect.bottomLeft(), option.rect.bottomRight() )

		if enabled and cellPlugEnabled :
			return

		painter.save()

		painter.setRenderHint( QtGui.QPainter.Antialiasing )

		overlayAlpha = 100 if option.state & QtWidgets.QStyle.State_Selected else 200
		overlayColor = QtGui.QColor( 40, 40, 40, overlayAlpha )

		if not cellPlugEnabled :

			painter.fillRect( option.rect, overlayColor )

			pen = QtGui.QPen( QtGui.QColor( 20, 20, 20, 150 ) )
			pen.setWidth( 2 )
			painter.setPen( pen )
			painter.drawLine( option.rect.bottomLeft(), option.rect.topRight() )

		if not enabled :

			painter.fillRect( option.rect, overlayColor )

		painter.restore()

	__filteredEvents = ( QtCore.QEvent.MouseButtonPress, QtCore.QEvent.MouseButtonRelease )

	def editorEvent( self, event, model, option, index ) :

		if event.type() in self.__filteredEvents and bool( index.flags() & QtCore.Qt.ItemIsUserCheckable ) :
			# Prevent checkable items from being editable via single click
			return False
		else :
			return super( _PlugTableDelegate, self ).editorEvent( event, model, option, index )
