##########################################################################
#
#  Copyright (c) 2011-2013, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

from GafferUI.PlugValueWidget import sole

# Supported metadata :
#
#	- "ui:visibleDimensions" controls how many dimensions are actually shown.
#     For instance, a value of 2 can be used to make a V3fPlug appear like a
#     V2fPlug.
class CompoundNumericPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=4 )
		GafferUI.PlugValueWidget.__init__( self, self.__row, plugs, **kw )

		self.__ensureChildPlugValueWidgets()
		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )

	def setPlugs( self, plugs ) :

		GafferUI.PlugValueWidget.setPlugs( self, plugs )
		self.__ensureChildPlugValueWidgets()

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )

		for w in self.__row :
			if isinstance( w, GafferUI.NumericPlugValueWidget ) :
				w.setHighlighted( highlighted )
			else :
				# End widgets managed by a subclass.
				break

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )

		for w in self.__row :
			if isinstance( w, GafferUI.PlugValueWidget ) :
				w.setReadOnly( readOnly )

	def childPlugValueWidget( self, childPlug ) :

		for widget in self.__row :
			if isinstance( widget, GafferUI.PlugValueWidget ) :
				if childPlug in widget.getPlugs() :
					return widget

		return None

	## Returns the ListContainer used as the main layout for this Widget.
	# Derived classes may use it to add to the layout.
	def _row( self ) :

		return self.__row

	# Reimplemented to perform casting between vector and color types,
	# including types with different dimensions. In this case we preserve
	# the current values for any additional dimensions not provided by the
	# incoming `value`.
	def _convertValue( self, value ) :

		result = GafferUI.PlugValueWidget._convertValue( self, value )
		if result is not None :
			return result

		if isinstance( value, IECore.Data ) and hasattr( value, "value" ) :
			value = value.value
			if hasattr( value, "dimensions" ) and isinstance( value.dimensions(), int ) :
				with self.getContext() :
					result = sole( p.getValue() for p in self.getPlugs() )
				if result is None :
					return None
				componentType = type( result[0] )
				for i in range( 0, min( result.dimensions(), value.dimensions() ) ) :
					result[i] = componentType( value[i] )
				return result

		return None

	def __keyPress( self, widget, event ) :

		if event.key == "G" and event.modifiers & event.Modifiers.Control :

			if not all( hasattr( p, "isGanged" ) for p in self.getPlugs() ) :
				return False

			if all( p.isGanged() for p in self.getPlugs() ) :
				self.__ungang()
			else :
				self.__gang()

			return True

		return False

	def __gang( self ) :

		with Gaffer.UndoScope( next( iter( self.getPlugs() ) ).ancestor( Gaffer.ScriptNode ) ) :
			for plug in self.getPlugs() :
				plug.gang()

	def __ungang( self ) :

		with Gaffer.UndoScope( next( iter( self.getPlugs() ) ).ancestor( Gaffer.ScriptNode ) ) :
			for plug in self.getPlugs() :
				plug.ungang()

	@staticmethod
	def _popupMenu( menuDefinition, plugValueWidget ) :

		compoundNumericPlugValueWidget = None
		if isinstance( plugValueWidget, GafferUI.CompoundNumericPlugValueWidget ) :
			compoundNumericPlugValueWidget = plugValueWidget
		else :
			plugWidget = plugValueWidget.ancestor( GafferUI.PlugWidget )
			if plugWidget is not None and isinstance( plugWidget.plugValueWidget(), GafferUI.CompoundNumericPlugValueWidget ) :
				compoundNumericPlugValueWidget = plugWidget.plugValueWidget()

		if compoundNumericPlugValueWidget is None :
			return

		plugs = compoundNumericPlugValueWidget.getPlugs()
		if not all( hasattr( p, "isGanged" ) for p in plugs ) :
			return

		readOnly = plugValueWidget.getReadOnly() or any( Gaffer.MetadataAlgo.readOnly( p ) for p in plugs )

		if all( p.isGanged() for p in plugs ) :
			menuDefinition.append( "/GangDivider", { "divider" : True } )
			menuDefinition.append( "/Ungang", {
				"command" : Gaffer.WeakMethod( compoundNumericPlugValueWidget.__ungang ),
				"shortCut" : "Ctrl+G",
				"active" : not readOnly,
			} )
		else :
			menuDefinition.append( "/GangDivider", { "divider" : True } )
			menuDefinition.append( "/Gang", {
				"command" : Gaffer.WeakMethod( compoundNumericPlugValueWidget.__gang ),
				"shortCut" : "Ctrl+G",
				"active" : not readOnly and all( p.canGang() for p in plugs ),
			} )

	def __ensureChildPlugValueWidgets( self ) :

		# Adjust our layout to include the right number of widgets.
		# Because we expose `row_()`, derived classes may have added
		# additional widgets on the end, which we must leave alone.

		numericWidgets = []
		additionalWidgets = []
		for i, w in enumerate( self.__row ) :
			if isinstance( w, GafferUI.NumericPlugValueWidget ) :
				numericWidgets.append( w )
			else :
				additionalWidgets = self.__row[i:]
				break

		dimensions = min( len( p ) for p in self.getPlugs() )
		if dimensions > len( numericWidgets ) :
			for i in range( 0, dimensions - len( numericWidgets ) ) :
				numericWidgets.append( GafferUI.NumericPlugValueWidget( plugs = [] ) )
		else :
			del numericWidgets[dimensions:]

		self.__row[:] = numericWidgets + additionalWidgets

		# Call `setPlugs()` for each numeric widget and apply widget
		# visibility according to metadata.

		visibleDimensions = dimensions
		for plug in self.getPlugs() :
			d = Gaffer.Metadata.value( plug, "ui:visibleDimensions" )
			if d is not None :
				visibleDimensions = min( visibleDimensions, d )

		for i, w in enumerate( numericWidgets ) :
			w.setPlugs( { p[i] for p in self.getPlugs() } )
			w.setVisible( i < visibleDimensions )

GafferUI.PlugValueWidget.popupMenuSignal().connect( CompoundNumericPlugValueWidget._popupMenu, scoped = False )

GafferUI.PlugValueWidget.registerType( Gaffer.V2fPlug, CompoundNumericPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.V3fPlug, CompoundNumericPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.V2iPlug, CompoundNumericPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.V3iPlug, CompoundNumericPlugValueWidget )
