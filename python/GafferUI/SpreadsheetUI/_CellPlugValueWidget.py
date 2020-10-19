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

class _CellPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		if not isinstance( plugs, set ) :
			plugs = { plugs }

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		GafferUI.PlugValueWidget.__init__( self, self.__row, plugs )

		enabledPlugs = { p["enabled"] for p in plugs if "enabled" in p }
		valuePlugs = { p["value"] for p in plugs }

		rowPlug = next( iter( plugs ) ).ancestor( Gaffer.Spreadsheet.RowPlug )
		if enabledPlugs and len(enabledPlugs) == len(plugs) and rowPlug != rowPlug.parent().defaultRow() :
			enabledPlugValueWidget = GafferUI.BoolPlugValueWidget(
				enabledPlugs,
				displayMode=GafferUI.BoolWidget.DisplayMode.Switch
			)
			self.__row.append( enabledPlugValueWidget, verticalAlignment=GafferUI.VerticalAlignment.Top )

		if self.canEdit( plugs ) :

			plugValueWidget = self.__createValueWidget( valuePlugs )
			if plugValueWidget is not None :
				# Apply some fixed widths for some widgets, otherwise they're
				# a bit too eager to grow. \todo Should we change the underlying
				# behaviour of the widgets themselves?
				self.__applyFixedWidths( plugValueWidget )
				self.__row.append( plugValueWidget )
			else :
				self.__row.append( GafferUI.Label( "Unable to multi-edit values of this type" ) )

		else :
			self.__row.append( GafferUI.Label( "Unable to multi-edit values with mixed types" ) )


		self._updateFromPlugs()

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

		if len( cellPlugs ) == 0 :
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

	def _updateFromPlugs( self ) :

		enabledPlugs = [ p["enabled"] for p in self.getPlugs() if "enabled" in p ]

		if enabledPlugs :
			assert( len(enabledPlugs) == len(self.getPlugs()) )
			enabled = False
			with self.getContext() :
				with IECore.IgnoredExceptions( Exception ) :
					enabled = sole( [ p.getValue() for p in enabledPlugs ] )
			self.__row[-1].setEnabled( enabled is True )

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

		if isinstance( plugValueWidget, GafferUI.VectorDataPlugValueWidget ) :
			plugValueWidget._qtWidget().setFixedWidth( 250 )
		else :
			walk( plugValueWidget )

GafferUI.PlugValueWidget.registerType( Gaffer.Spreadsheet.CellPlug, _CellPlugValueWidget )
