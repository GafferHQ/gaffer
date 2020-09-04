##########################################################################
#
#  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

from Qt import QtWidgets

## A simple PlugValueWidget which just displays the name of the plug,
# with the popup action menu for the plug.
#
# Supported plug metadata :
#
#  - "renameable"
class LabelPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, horizontalAlignment=GafferUI.Label.HorizontalAlignment.Left, verticalAlignment=GafferUI.Label.VerticalAlignment.Center, **kw ) :

		GafferUI.PlugValueWidget.__init__( self, QtWidgets.QWidget(), plug, **kw )

		layout = QtWidgets.QHBoxLayout()
		layout.setContentsMargins( 0, 0, 0, 0 )
		layout.setSizeConstraint( QtWidgets.QLayout.SetMinAndMaxSize )
		self._qtWidget().setLayout( layout )

		self.__label = GafferUI.NameLabel(
			plug,
			horizontalAlignment = horizontalAlignment,
			verticalAlignment = verticalAlignment,
			formatter = self.__formatter,
		)
		self.__label._qtWidget().setObjectName( "gafferPlugLabel" )
		layout.addWidget( self.__label._qtWidget() )

		self.__editableLabel = None # we'll make this lazily as needed

		# connecting at group 0 so we're called before the slots
		# connected by the NameLabel class.
		self.__label.dragBeginSignal().connect( 0, Gaffer.WeakMethod( self.__dragBegin ), scoped = False )
		self.__label.dragEndSignal().connect( 0, Gaffer.WeakMethod( self.__dragEnd ), scoped = False )

		Gaffer.Metadata.plugValueChangedSignal().connect( Gaffer.WeakMethod( self.__plugMetadataChanged ), scoped = False )

		self._addPopupMenu( self.__label )

		self.setPlug( plug )

	def label( self ) :

		return self.__label

	def setPlug( self, plug ) :

		GafferUI.PlugValueWidget.setPlug( self, plug )

		self.__label.setGraphComponent( plug )
		if self.__editableLabel is not None :
			self.__editableLabel.setGraphComponent( plug )

		self.__updateDoubleClickConnection()

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )

		self.__label.setHighlighted( highlighted )

	def getToolTip( self ) :

		result = GafferUI.PlugValueWidget.getToolTip( self )

		if self.getPlug() is not None :
			if result :
				result += "\n"
			result += "## Actions\n\n"
			result += "- Left drag to connect\n"
			if hasattr( self.getPlug(), "getValue" ) :
				result += "- Shift+left or middle drag to transfer value"

		return result

	def _updateFromPlug( self ) :

		plug = self.getPlug()

		valueChanged = plug.getInput() is not None
		if not valueChanged and isinstance( plug, Gaffer.ValuePlug ) :
			if Gaffer.NodeAlgo.hasUserDefault( plug ) :
				valueChanged = not Gaffer.NodeAlgo.isSetToUserDefault( plug )
			else :
				valueChanged = not plug.isSetToDefault()
		self.__setValueChanged( valueChanged )

	# Sets whether or not the label be rendered in a ValueChanged state.
	def __setValueChanged( self, valueChanged ) :

		if valueChanged == self.__getValueChanged() :
			return

		self.__label._qtWidget().setProperty( "gafferValueChanged", GafferUI._Variant.toVariant( valueChanged ) )
		self.__label._repolish()

	def __getValueChanged( self ) :

		if "gafferValueChanged" not in self.__label._qtWidget().dynamicPropertyNames() :
			return False

		return GafferUI._Variant.fromVariant( self.__label._qtWidget().property( "gafferValueChanged" ) )

	def __dragBegin( self, widget, event ) :

		# initiate a drag containing the value of the plug
		# for shift-left drag or a middle drag. initiate a
		# drag containing the plug for a straight left-drag.

		shift = event.modifiers & event.Modifiers.Shift
		left = event.buttons == event.Buttons.Left
		middle = event.buttons == event.Buttons.Middle
		if ( shift and left ) or middle :
			if not hasattr( self.getPlug(), "getValue" ) :
				return None
			GafferUI.Pointer.setCurrent( "values" )
			with self.getContext() :
				return self.getPlug().getValue()
		elif left :
			GafferUI.Pointer.setCurrent( "plug" )
			return self.getPlug()

	def __dragEnd( self, widget, event ) :

		GafferUI.Pointer.setCurrent( None )

	def __updateDoubleClickConnection( self ) :

		self.__labelDoubleClickConnection = None
		if self.getPlug() is None :
			return

		# First try the official metadata.
		renameable = Gaffer.Metadata.value( self.getPlug(), "renameable" )
		if renameable is None :
			# Then try the old metadata that we are phasing out.
			renameable = Gaffer.Metadata.value( self.getPlug(), "labelPlugValueWidget:renameable" )

		if renameable != True :
			return

		self.__labelDoubleClickConnection = self.__label.buttonDoubleClickSignal().connect( Gaffer.WeakMethod( self.__labelDoubleClicked ) )

	def __labelDoubleClicked( self, label, event ) :

		assert( label is self.__label )

		if Gaffer.MetadataAlgo.readOnly( self.getPlug() ) :
			return

		if self.__editableLabel is None :
			self.__editableLabel = GafferUI.NameWidget( self.getPlug() )
			self.__editableLabel._qtWidget().setMinimumSize( self.label()._qtWidget().minimumSize() )
			self.__editableLabel._qtWidget().setMaximumSize( self.label()._qtWidget().maximumSize() )
			# Connect at group 0 so we're called before the NameWidget's own slots.
			self.__labelEditingFinishedConnection = self.__editableLabel.editingFinishedSignal().connect( 0, Gaffer.WeakMethod( self.__labelEditingFinished ) )
			self._qtWidget().layout().insertWidget( 0, self.__editableLabel._qtWidget() )

		self.__label.setVisible( False )
		self.__editableLabel.setVisible( True )
		self.__editableLabel.setSelection( 0, len( self.__editableLabel.getText() ) )
		self.__editableLabel.grabFocus()

	def __labelEditingFinished( self, nameWidget ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			# Do what the NameWidget would have done for us anyway, so we
			# can group it with the metadata deregistration in the undo queue.
			self.getPlug().setName( nameWidget.getText() )
			# Remove any metadata label which would mask the name - if a user
			# has gone to the trouble of setting a sensible name, then it should
			# take precedence.
			Gaffer.Metadata.deregisterValue( self.getPlug(), "label" )

		self.__label.setVisible( True )
		self.__editableLabel.setVisible( False )

		# Return True so that the NameWidget's handler isn't run, since we
		# did all the work ourselves.
		return True

	def __plugMetadataChanged( self, nodeTypeId, plugPath, key, plug ) :

		if self.getPlug() is None :
			return

		if key=="label" and Gaffer.MetadataAlgo.affectedByChange( self.getPlug(), nodeTypeId, plugPath, plug ) :
			# The NameLabel doesn't know that our formatter is sensitive
			# to the metadata, so give it a little kick.
			self.__label.setFormatter( self.__formatter )

	@staticmethod
	def __formatter( graphComponents ) :

		if graphComponents :
			label = Gaffer.Metadata.value( graphComponents[-1], "label" )
			if label is not None :
				return label

		return GafferUI.NameLabel.defaultFormatter( graphComponents )
