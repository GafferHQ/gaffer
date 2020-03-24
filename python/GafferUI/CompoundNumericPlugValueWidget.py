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

# Supported metadata :
#
#	- "ui:visibleDimensions" controls how many dimensions are actually shown.
#     For instance, a value of 2 can be used to make a V3fPlug appear like a
#     V2fPlug.
class CompoundNumericPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=4 )

		GafferUI.PlugValueWidget.__init__( self, self.__row, plug, **kw )

		componentPlugs = plug.children()
		for p in componentPlugs :
			w = GafferUI.NumericPlugValueWidget( p )
			self.__row.append( w )

		self.__applyVisibleDimensions()

		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )

	def setPlug( self, plug ) :

		assert( len( plug ) == len( self.getPlug() ) )

		GafferUI.PlugValueWidget.setPlug( self, plug )

		for index, plug in enumerate( plug.children() ) :
			self.__row[index].setPlug( plug )

		self.__applyVisibleDimensions()

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )

		for i in range( 0, len( self.getPlug() ) ) :
			self.__row[i].setHighlighted( highlighted )

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )

		for w in self.__row :
			if isinstance( w, GafferUI.PlugValueWidget ) :
				w.setReadOnly( readOnly )

	def childPlugValueWidget( self, childPlug ) :

		for i, p in enumerate( self.getPlug().children() ) :
			if p.isSame( childPlug ) :
				return self.__row[i]

		return None

	def _updateFromPlug( self ) :

		pass

	## Returns the ListContainer used as the main layout for this Widget.
	# Derived classes may use it to add to the layout.
	def _row( self ) :

		return self.__row

	# Reimplemented to perform casting between vector and color types.
	def _convertValue( self, value ) :

		result = GafferUI.PlugValueWidget._convertValue( self, value )
		if result is not None :
			return result

		if isinstance( value, IECore.Data ) and hasattr( value, "value" ) :
			value = value.value
			if hasattr( value, "dimensions" ) and isinstance( value.dimensions(), int ) :
				with self.getContext() :
					result = self.getPlug().getValue()
				componentType = type( result[0] )
				for i in range( 0, min( result.dimensions(), value.dimensions() ) ) :
					result[i] = componentType( value[i] )
				return result

		return None

	def __keyPress( self, widget, event ) :

		if event.key == "G" and event.modifiers & event.Modifiers.Control :
			if self.getPlug().isGanged() :
				self.__ungang()
			elif self.getPlug().canGang() :
				self.__gang()

			return True

		return False

	def __gang( self ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().gang()

	def __ungang( self ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().ungang()

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

		if compoundNumericPlugValueWidget.getPlug().isGanged() :
			menuDefinition.append( "/GangDivider", { "divider" : True } )
			menuDefinition.append( "/Ungang", {
				"command" : Gaffer.WeakMethod( compoundNumericPlugValueWidget.__ungang ),
				"shortCut" : "Ctrl+G",
				"active" : not plugValueWidget.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( compoundNumericPlugValueWidget.getPlug() ),
			} )
		elif compoundNumericPlugValueWidget.getPlug().canGang() :
			menuDefinition.append( "/GangDivider", { "divider" : True } )
			menuDefinition.append( "/Gang", {
				"command" : Gaffer.WeakMethod( compoundNumericPlugValueWidget.__gang ),
				"shortCut" : "Ctrl+G",
				"active" : not plugValueWidget.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( compoundNumericPlugValueWidget.getPlug() ),
			} )

	def __applyVisibleDimensions( self ) :

		actualDimensions = len( self.getPlug() )
		visibleDimensions = Gaffer.Metadata.value( self.getPlug(), "ui:visibleDimensions" )
		visibleDimensions = visibleDimensions if visibleDimensions is not None else actualDimensions

		for i in range( 0, actualDimensions ) :
			self.__row[i].setVisible( i < visibleDimensions )

GafferUI.PlugValueWidget.popupMenuSignal().connect( CompoundNumericPlugValueWidget._popupMenu, scoped = False )

GafferUI.PlugValueWidget.registerType( Gaffer.V2fPlug, CompoundNumericPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.V3fPlug, CompoundNumericPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.V2iPlug, CompoundNumericPlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.V3iPlug, CompoundNumericPlugValueWidget )
