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

# Value Formatting
# ================

## Returns the value of the plug as it will be formatted in a Spreadsheet.
def formatValue( plug, forToolTip = False ) :

	return _PlugTableModel.formatValue( plug, forToolTip )

## Registers a custom formatter for the specified `plugType`.
# `formatter` must have the same signature as `formatValue()`.
def registerValueFormatter( plugType, formatter ) :

	_PlugTableModel.registerValueFormatter( plugType, formatter )

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
