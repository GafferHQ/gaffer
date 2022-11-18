##########################################################################
#
#  Copyright (c) 2020, Image Engine Design Inc. All rights reserved.
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

import functools

import imath

import IECore

import Gaffer
import GafferUI

##########################################################################
# ShufflePlug Widget
##########################################################################

# Widget for ShufflePlug, which is used to build shuffle nodes
# such as ShuffleAttributes and ShufflePrimitiveVariables.
class ShufflePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__row, plug )

		sourceWidget = GafferUI.StringPlugValueWidget( plug["source"] )
		sourceWidget.textWidget()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )
		self.__row.append( sourceWidget, verticalAlignment = GafferUI.Label.VerticalAlignment.Top )

		self.__row.append(
			GafferUI.BoolPlugValueWidget( plug["enabled"], displayMode = GafferUI.BoolWidget.DisplayMode.Switch ),
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top,
		)

		destinationWidget = GafferUI.StringPlugValueWidget( plug["destination"] )
		destinationWidget.textWidget()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )
		self.__row.append( destinationWidget, verticalAlignment = GafferUI.Label.VerticalAlignment.Top )

		deleteSourceWidget = GafferUI.PlugValueWidget.create( plug["deleteSource"] )
		deleteSourceWidget.boolWidget()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() - 40 )
		self.__row.append( deleteSourceWidget )
		self.__row.append( GafferUI.PlugValueWidget.create( plug["replaceDestination"] ), expand = True )

		self._updateFromPlug()

	def setPlug( self, plug ) :

		GafferUI.PlugValueWidget.setPlug( self, plug )

		self.__row[0].setPlug( plug["source"] )
		self.__row[1].setPlug( plug["enabled"] )
		self.__row[2].setPlug( plug["destination"] )
		self.__row[3].setPlug( plug["deleteSource"] )
		self.__row[4].setPlug( plug["replaceDestination"] )

	def hasLabel( self ) :

		return True

	def childPlugValueWidget( self, childPlug ) :

		for w in self.__row :
			if w.getPlug().isSame( childPlug ) :
				return w

		return None

	def _updateFromPlug( self ) :

		with self.getContext() :
			enabled = self.getPlug()["enabled"].getValue()

		for i in ( 0, 2, 3, 4 ) :
			self.__row[i].setEnabled( enabled )

GafferUI.PlugValueWidget.registerType( Gaffer.ShufflePlug, ShufflePlugValueWidget )

##########################################################################
# ShufflePlug Metadata
##########################################################################

Gaffer.Metadata.registerValue( Gaffer.ShufflePlug, "source", "description", "The name(s) of the source data to be shuffled. Accepts standard matching syntax (eg \"a*b\")." )
Gaffer.Metadata.registerValue( Gaffer.ShufflePlug,
	"destination",
	"description",
	"""
	The name of the destination data to be created. Use `${source}` to insert
	the name of the source data. For example, to prepend `prefix:` set the
	destination to `prefix:${source}`.
	"""
)
Gaffer.Metadata.registerValue( Gaffer.ShufflePlug, "deleteSource", "description", "Enable to delete the source data after shuffling to the destination(s)." )
Gaffer.Metadata.registerValue( Gaffer.ShufflePlug, "replaceDestination", "description", "Enable to replace already written destination data with the same name as destination(s)." )
Gaffer.Metadata.registerValue( Gaffer.ShufflePlug, "enabled", "description", "Used to enable/disable this shuffle operation." )
Gaffer.Metadata.registerValue( Gaffer.ShufflePlug, "nodule:type", "" )
Gaffer.Metadata.registerValue( Gaffer.ShufflePlug, "*", "nodule:type", "" )

##########################################################################
# ShufflesPlug Widget
##########################################################################

## \todo: Much of this widget is reused in several places (eg CompoundDataPlugValueWidget, CameraTweaksUI, NameSwitchUI, etc).
## Can we add more flexibility to LayoutPlugValueWidget (ie. header and footer options) and remove these other widgets?
class ShufflesPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		column = GafferUI.ListContainer( spacing = 4 )
		GafferUI.PlugValueWidget.__init__( self, column, plug )

		with column :
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
				GafferUI.Label( "<h4><b>Source</b></h4>" )._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )
				GafferUI.Spacer( imath.V2i( 25, 2 ) ) # approximate width of a BoolWidget Switch
				GafferUI.Label( "<h4><b>Destination</b></h4>" )._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )
				GafferUI.Label( "<h4><b>Delete Source</b></h4>" )._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() - 40 )
				GafferUI.Label( "<h4><b>Replace</b></h4>" )._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )

			self.__plugLayout = GafferUI.PlugLayout( plug )
			self.__addButton = GafferUI.Button( image = "plus.png", hasFrame = False )

		self.__addButton.clickedSignal().connect( Gaffer.WeakMethod( self.__addButtonClicked ), scoped = False )

	def hasLabel( self ) :

		return True

	def childPlugValueWidget( self, childPlug ) :

		return self.__plugLayout.plugValueWidget( childPlug )

	def _updateFromPlug( self ) :

		self.__addButton.setEnabled( self._editable() )

	def __addButtonClicked( self, button ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().addChild(
				Gaffer.ShufflePlug(
					name = "shuffle{}".format( len(self.getPlug().children()) ),
					flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic,
				)
			)

GafferUI.PlugValueWidget.registerType( Gaffer.ShufflesPlug, ShufflesPlugValueWidget )

##########################################################################
# ShufflesPlug Metadata
##########################################################################

Gaffer.Metadata.registerValue( Gaffer.ShufflesPlug, "*", "deletable", lambda plug : plug.getFlags( Gaffer.Plug.Flags.Dynamic ) )
Gaffer.Metadata.registerValue( Gaffer.ShufflesPlug, "nodule:type", "" )
