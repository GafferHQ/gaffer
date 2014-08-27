##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

QtGui = GafferUI._qtImport( "QtGui" )

## A simple PlugValueWidget which just displays the name of the plug,
# with the popup action menu for the plug.
class LabelPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, horizontalAlignment=GafferUI.Label.HorizontalAlignment.Left, verticalAlignment=GafferUI.Label.VerticalAlignment.Center, **kw ) :

		GafferUI.PlugValueWidget.__init__( self, QtGui.QWidget(), plug, **kw )

		layout = QtGui.QHBoxLayout()
		layout.setContentsMargins( 0, 0, 0, 0 )
		layout.setSizeConstraint( QtGui.QLayout.SetMinAndMaxSize )
		self._qtWidget().setLayout( layout )

		self.__label = GafferUI.NameLabel(
			plug,
			horizontalAlignment = horizontalAlignment,
			verticalAlignment = verticalAlignment,
		)
		layout.addWidget( self.__label._qtWidget() )

		self.__editableLabel = None # we'll make this lazily as needed

		# connecting at group 0 so we're called before the slots
		# connected by the NameLabel class.
		self.__dragBeginConnection = self.__label.dragBeginSignal().connect( 0, Gaffer.WeakMethod( self.__dragBegin ) )
		self.__dragEndConnection = self.__label.dragEndSignal().connect( 0, Gaffer.WeakMethod( self.__dragEnd ) )

		self._addPopupMenu( self.__label )

		self.setPlug( plug )

	def label( self ) :

		return self.__label

	def setPlug( self, plug ) :

		GafferUI.PlugValueWidget.setPlug( self, plug )

		self.__label.setGraphComponent( plug )
		if self.__editableLabel is not None :
			self.__editableLabel.setGraphComponent( plug )

		label = Gaffer.Metadata.plugValue( plug, "label" ) if plug is not None else None
		if label is not None :
			self.__label.setText( label )

		# if the plug is a user plug, then set things up so it can be renamed
		# by double clicking on the label. currently we only accept plugs immediately
		# parented to the user plug, so as to avoid allowing the renaming of child
		# plugs inside SplinePlugs and the like, where plug names have specific meanings.
		if plug is not None and plug.node()["user"].isSame( plug.parent() ) :
			self.__labelDoubleClickConnection = self.__label.buttonDoubleClickSignal().connect( Gaffer.WeakMethod( self.__labelDoubleClicked ) )
		else :
			self.__labelDoubleClickConnection = None

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )

		self.__label.setHighlighted( highlighted )

	def getToolTip( self ) :

		result = GafferUI.PlugValueWidget.getToolTip( self )

		if self.getPlug() is not None :
			result += "<ul>"
			result += "<li>Left drag to connect</li>"
			if hasattr( self.getPlug(), "getValue" ) :
				result += "<li>Shift-left or middle drag to transfer value</li>"
			result += "<ul>"

		return result

	def _updateFromPlug( self ) :

		self.__label.setEnabled(
			self.getPlug() is not None and
			not self.getPlug().getFlags( Gaffer.Plug.Flags.ReadOnly )
		)

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

	def __labelDoubleClicked( self, label, event ) :

		assert( label is self.__label )

		if self.__editableLabel is None :
			self.__editableLabel = GafferUI.NameWidget( self.getPlug() )
			self.__editableLabel._qtWidget().setMinimumSize( self.label()._qtWidget().minimumSize() )
			self.__editableLabel._qtWidget().setMaximumSize( self.label()._qtWidget().maximumSize() )
			self.__labelEditingFinishedConnection = self.__editableLabel.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__labelEditingFinished ) )
			self._qtWidget().layout().insertWidget( 0, self.__editableLabel._qtWidget() )

		self.__label.setVisible( False )
		self.__editableLabel.setVisible( True )
		self.__editableLabel.setSelection( 0, len( self.__editableLabel.getText() ) )
		self.__editableLabel.grabFocus()

	def __labelEditingFinished( self, label ) :

		self.__label.setVisible( True )
		self.__editableLabel.setVisible( False )

