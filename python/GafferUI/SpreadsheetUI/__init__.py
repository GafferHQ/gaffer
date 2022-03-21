##########################################################################
#
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

from . import _Metadata
from . import _Menus

from ._CellPlugValueWidget import _CellPlugValueWidget
from ._PlugTableModel import _PlugTableModel
from ._RowsPlugValueWidget import _RowsPlugValueWidget

# Value Formatting
# ================

from ._Formatting import registerValueFormatter, formatValue

# Editing
# =======
#
# By default, `PlugValueWidget.create( cell["value"] )` is used to create
# a widget for editing cells in the spreadsheet, but custom editors may be
# provided for specific plug types.

# Registers a function to return a PlugValueWidget for editing cell
# value plugs of the specified type.
def registerValueWidget( plugType, plugValueWidgetCreator ) :

	_CellPlugValueWidget.registerValueWidget( plugType, plugValueWidgetCreator )

# Decorations
# ===========

## Registers a function to return a decoration to be shown
# alongside the formatted value. Currently the only supported
# return type is `Color3f`.
def registerDecoration( plugType, decorator ) :

	_PlugTableModel.registerDecoration( plugType, decorator )

## Returns the decoration for the specified plug.
def decoration( plug ) :

	return _PlugTableModel.decoration( plug )

# Signals
# =======

def addRowButtonMenuSignal() :

	return _RowsPlugValueWidget.addRowButtonMenuSignal()

## Signal emitted when the "add column" button is pressed. Slots
# may be connected to customise the menu that is shown, and are
# called with the following arguments :
#
# - `menuDefinition` : The `IECore.MenuDefinition` to be edited.
# - `widget` : The PlugValueWidget for the spreadsheet. Access
#   the `RowsPlug` itself via `widget.getPlug()`.
#
# Example :
#
# ```
# def customAddColumnMenu( menuDefinition, widget ) :
#
# 	def addColumn( rowsPlug ) :
#
# 		with Gaffer.UndoScope( rowsPlug.ancestor( Gaffer.ScriptNode ) ) :
# 			rowsPlug.addColumn( Gaffer.StringPlug( "custom", defaultValue = "custom" ) )
#
# 	menuDefinition.append( "/CustomDivider", { "divider" : True } )
# 	menuDefinition.append( "/Custom", { "command" : functools.partial( addColumn, widget.getPlug() ) } )
#
# GafferUI.SpreadsheetUI.addColumnButtonMenuSignal().connect( customAddColumnMenu, scoped = False )
# ```
#
# > Tip : The `menuDefinition` will already contain a set of default
# > menu items. These may be removed by calling `menuDefinition.clear()`.
def addColumnButtonMenuSignal() :

	return _RowsPlugValueWidget.addColumnButtonMenuSignal()
