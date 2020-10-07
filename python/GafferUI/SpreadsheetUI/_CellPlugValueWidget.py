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

import Gaffer
import GafferUI

import IECore

from Qt import QtWidgets

class _CellPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		GafferUI.PlugValueWidget.__init__( self, self.__row, plug )

		rowPlug = plug.ancestor( Gaffer.Spreadsheet.RowPlug )
		if "enabled" in plug and rowPlug != rowPlug.parent().defaultRow() :
			enabledPlugValueWidget = GafferUI.BoolPlugValueWidget(
				plug["enabled"],
				displayMode=GafferUI.BoolWidget.DisplayMode.Switch
			)
			self.__row.append( enabledPlugValueWidget, verticalAlignment=GafferUI.VerticalAlignment.Top )

		plugValueWidget = self.__createValueWidget( plug["value"] )

		# Apply some fixed widths for some widgets, otherwise they're
		# a bit too eager to grow. \todo Should we change the underlying
		# behaviour of the widgets themselves?
		self.__applyFixedWidths( plugValueWidget )

		self.__row.append( plugValueWidget )

		self._updateFromPlug()

	def childPlugValueWidget( self, childPlug ) :

		for widget in self.__row :
			if widget.getPlug() == childPlug :
				return widget

		return None

	# By default, `PlugValueWidget.create( cell["value"] )` is used to create
	# a widget for editing cells in the spreadsheet, but custom editors may be
	# provided for specific plug types.

	# Registers a function to return a PlugValueWidget for editing cell
	# value plugs of the specified type.
	@classmethod
	def registerValueWidget( cls, plugType, plugValueWidgetCreator ) :

		cls.__plugValueWidgetCreators[plugType] = plugValueWidgetCreator

	def __createValueWidget( self, plug ) :

		creator = self.__plugValueWidgetCreators.get(
			plug.__class__,
			GafferUI.PlugValueWidget.create
		)

		w = creator( plug )
		assert( isinstance( w, GafferUI.PlugValueWidget ) )
		return w

	__plugValueWidgetCreators = {}

	def _updateFromPlug( self ) :

		if "enabled" in self.getPlug() :
			enabled = False
			with self.getContext() :
				with IECore.IgnoredExceptions( Exception ) :
					enabled = self.getPlug()["enabled"].getValue()
			self.__row[-1].setEnabled( enabled )

	__numericFieldWidth = 60

	@classmethod
	def __applyFixedWidths( cls, plugValueWidget ) :

		def walk( widget ) :

			if isinstance( widget, GafferUI.NumericPlugValueWidget ) :
				widget._qtWidget().setFixedWidth( cls.__numericFieldWidth )
				widget._qtWidget().layout().setSizeConstraint( QtWidgets.QLayout.SetNoConstraint )

			for childPlug in Gaffer.Plug.Range( widget.getPlug() ) :
				childWidget = widget.childPlugValueWidget( childPlug )
				if childWidget is not None :
					walk( childWidget )

		if isinstance( plugValueWidget, GafferUI.VectorDataPlugValueWidget ) :
			plugValueWidget._qtWidget().setFixedWidth( 250 )
		else :
			walk( plugValueWidget )

GafferUI.PlugValueWidget.registerType( Gaffer.Spreadsheet.CellPlug, _CellPlugValueWidget )
