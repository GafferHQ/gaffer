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

from GafferUI.PlugValueWidget import sole

from . import _Algo

class _CellPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugOrPlugs, **kw ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		GafferUI.PlugValueWidget.__init__( self, self.__row, plugOrPlugs )

		plugs = self.getPlugs()

		# If all cells have enabled plugs, we need to add a switch for them.
		# If cells adopt the enabled plug from their value plug, we rely on the
		# PlugValueWidget drawing the switch for us.
		# However, in cases where the widget for the value plug doesn't support
		# multiple plugs, we don't show a value, and so need to add our own
		# switch so people can at least edit enabled state the cells.

		cellEnabledPlugs = { p["enabled"] for p in plugs if "enabled" in p }
		valuePlugs = { p["value"] for p in plugs }

		addCellEnabledSwitch = len( cellEnabledPlugs ) == len( valuePlugs )

		if self.canEdit( plugs ) :

			plugValueWidget = self.__createValueWidget( valuePlugs )
			if plugValueWidget is not None :
				# Apply some fixed widths for some widgets, otherwise they're
				# a bit too eager to grow. \todo Should we change the underlying
				# behaviour of the widgets themselves?
				self.__applyFixedWidths( plugValueWidget )
				self.__row.append( plugValueWidget )
			else :
				self.__row.append( GafferUI.Label( "Unable to edit multiple plugs of this type" ) )
				addCellEnabledSwitch = True

		else :
			self.__row.append( GafferUI.Label( "Unable to edit plugs with mixed types" ) )
			addCellEnabledSwitch = True

		if addCellEnabledSwitch :
			self.__enabledPlugValueWidget = GafferUI.BoolPlugValueWidget(
				[ p.enabledPlug() for p in plugs ],
				displayMode=GafferUI.BoolWidget.DisplayMode.Switch
			)
			self.__enabledPlugValueWidget.setEnabled( _Algo.cellsCanBeDisabled( plugs ) )
			self.__row.insert( 0, self.__enabledPlugValueWidget, verticalAlignment=GafferUI.VerticalAlignment.Top )
		else :
			self.__enabledPlugValueWidget = None

	def childPlugValueWidget( self, childPlug ) :

		for widget in self.__row :
			if not isinstance( widget, GafferUI.PlugValueWidget ) :
				continue
			if childPlug in widget.getPlugs() :
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

	@classmethod
	def canEdit( cls, cellPlugs ) :

		if not cellPlugs :
			return False

		if len( cellPlugs ) == 1 :
			return True

		def plugStructure( cell ) :
			return [ p.__class__ for p in Gaffer.Plug.RecursiveRange( cell ) ]

		if sole( [ plugStructure( c ) for c in cellPlugs ] ) is None :
			return False

		return True

	def __createValueWidget( self, plugs ) :

		creator = self.__plugValueWidgetCreators.get(
			next( iter( plugs ) ).__class__,
			GafferUI.PlugValueWidget.create
		)

		# Not all value widgets support multiple plugs yet,
		# so we need to be a little careful here.
		if len( plugs ) == 1 :
			# Ensure maximum compatability
			w = creator( next( iter( plugs ) ) )
		else :
			try :
				w = creator( plugs )
			except :
				return None

		assert( isinstance( w, GafferUI.PlugValueWidget ) )
		return w

	__plugValueWidgetCreators = {}

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		return [ p.enabledPlug().getValue() for p in plugs ]

	def _updateFromValues( self, values, exception ) :

		if self.__enabledPlugValueWidget is None :
			return

		self.__row[-1].setEnabled( sole( values ) is True )

	__numericFieldWidth = 60

	@classmethod
	def __applyFixedWidths( cls, plugValueWidget ) :

		def walk( widget ) :

			if isinstance( widget, GafferUI.NumericPlugValueWidget ) :
				widget._qtWidget().setFixedWidth( cls.__numericFieldWidth )
				widget._qtWidget().layout().setSizeConstraint( QtWidgets.QLayout.SetNoConstraint )

			for childPlug in Gaffer.Plug.Range( next( iter( widget.getPlugs() ) ) ) :
				childWidget = widget.childPlugValueWidget( childPlug )
				if childWidget is not None :
					walk( childWidget )

		if isinstance( plugValueWidget, ( GafferUI.VectorDataPlugValueWidget, GafferUI.StringPlugValueWidget ) ) :
			# It's pretty common to make wide spreadsheet columns to accommodate
			# lists of long scene locations. When that is the case, we want
			# to make sure the editor is equally wide, so that it shows at least
			# as much content as the spreadsheet itself.
			columnWidth = Gaffer.Metadata.value( plugValueWidget.getPlug().parent(), "spreadsheet:columnWidth" ) or 0
			plugValueWidget._qtWidget().setFixedWidth( max( columnWidth, 250 ) )
			if isinstance( plugValueWidget, GafferUI.StringPlugValueWidget ) :
				plugValueWidget._qtWidget().layout().setSizeConstraint( QtWidgets.QLayout.SetNoConstraint )
				plugValueWidget.textWidget().setFixedCharacterWidth( None )
		else :
			walk( plugValueWidget )

GafferUI.PlugValueWidget.registerType( Gaffer.Spreadsheet.CellPlug, _CellPlugValueWidget )
