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

import imath

import IECore

import Gaffer
import GafferUI

Gaffer.Metadata.registerNode(

	Gaffer.NameSwitch,

	"description",
	"""
	Switches between multiple input connections, passing through the
	chosen input to the output. Each input has a "name" as well
	as a value, and switching is performed by comparing the names against
	the value of `selector` as follows :

	- Matching starts with the second input and considers all subsequent
	  inputs one by one until a match is found. The first matching input
	  is the one that is chosen.
	- Matching is performed using Gaffer's standard wildcard matching.
	  Each "name" may contain several individual patterns each separated
	  by spaces.
	- The first input is used as a default, and is chosen only if no other
	  input matches.
	""",

	plugs = {

		"selector" : [

			"description",
			"""
			The value that the input names will be matched against.
			Typically this will refer to a Context Variable using
			the `${variableName}` syntax.
			""",

			"nodule:type", "",
			"divider", True,

		],

		"in" : [

			"plugValueWidget:type", "GafferUI.NameSwitchUI._InPlugValueWidget",
			"noduleLayout:customGadget:addButton:gadgetType", "GafferUI.NameSwitchUI.PlugAdder",

		],

		"in.in0" : [

			"deletable", False,

		],

		"in.in0.value" : [

			"noduleLayout:label", "default",

		],

		"in.*" : [

			"nodule:type", "GafferUI::CompoundNodule",
			"plugValueWidget:type", "GafferUI.NameSwitchUI._RowPlugValueWidget",
			"deletable", True,

		],

		"in.*.name" : [

			"nodule:type", "",

		],

		"in.*.enabled" : [

			"nodule:type", "",

		],

		"in.*.value" : [

			"plugValueWidget:type", "GafferUI.ConnectionPlugValueWidget",
			"noduleLayout:label", lambda plug : plug.parent()["name"].getValue(),

		],

		"out" : [

			"nodule:type", "GafferUI::CompoundNodule",

		],

		"out.name" : [

			"nodule:type", "",

		],

		"out.enabled" : [

			"nodule:type", "",

		],

		"out.value" : [

			"noduleLayout:label", "out",

		],

	}

)

# Equivalent to LayoutPlugValueWidget, but with a little footer with a button
# for adding new inputs.
class _InPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		column = GafferUI.ListContainer( spacing = 4 )
		GafferUI.PlugValueWidget.__init__( self, column, plug )

		with column :
			self.__plugLayout = GafferUI.PlugLayout( plug )
			self.__addButton = GafferUI.Button( image = "plus.png", hasFrame = False )

		self.__addButton.clickedSignal().connect( Gaffer.WeakMethod( self.__addButtonClicked ), scoped = False )

		self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ), scoped = False )
		self.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ), scoped = False )
		self.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ), scoped = False )
		self.dropSignal().connect( 0, Gaffer.WeakMethod( self.__drop ), scoped = False )

		self.__currentDragTarget = None

	def hasLabel( self ) :

		return True

	def setReadOnly( self, readOnly ) :

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )
		self.__plugLayout.setReadOnly( readOnly )

	def childPlugValueWidget( self, childPlug, lazy=True ) :

		return self.__plugLayout.plugValueWidget( childPlug, lazy )

	def _updateFromPlug( self ) :

		self.__addButton.setEnabled( self._editable() )

	def __addButtonClicked( self, button ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().resize( len( self.getPlug() ) + 1 )
			parent = self.getPlug().parent()
			if not isinstance( parent, Gaffer.NameSwitch ) or self.getPlug() != parent["in"] :
				## See comments in `NameSwitchPlugAdder::createConnection()`
				Gaffer.MetadataAlgo.copy( self.getPlug()[-2], self.getPlug()[-1] )

	def __dragEnter( self, widget, event ) :

		return self.__sourcePlug( event ) is not None

	def __dragMove( self, widget, event ) :

		dragTarget = self.__destinationDivider( event )
		if dragTarget is self.__currentDragTarget :
			return True

		if self.__currentDragTarget is not None :
			self.__currentDragTarget.setHighlighted( False )

		self.__currentDragTarget = dragTarget
		self.__currentDragTarget.setHighlighted( True )

		return True

	def __dragLeave( self, widget, event ) :

		self.__currentDragTarget.setHighlighted( False )
		self.__currentDragTarget = None

	def __drop( self, widget, event ) :

		srcPlug = self.__sourcePlug( event )
		dstPlug = self.__currentDragTarget.ancestor( _RowPlugValueWidget ).getPlug()
		parent = dstPlug.parent()
		assert( srcPlug.parent() == parent )

		srcIndex = parent.children().index( srcPlug )
		dstIndex = parent.children().index( dstPlug )

		# Reordering the plugs themselves is problematic, so
		# we reorder their values and connections instead.

		assert( srcIndex != 0 )

		if dstIndex > srcIndex :
			with Gaffer.UndoScope( srcPlug.ancestor( Gaffer.ScriptNode ) ) :
				srcState = self.__getValuesAndInputs( srcPlug )
				for i in range( srcIndex, dstIndex ) :
					self.__setValuesAndInputs( parent[i], self.__getValuesAndInputs( parent[i+1] ) )
				self.__setValuesAndInputs( parent[dstIndex], srcState )
		elif dstIndex < srcIndex - 1 :
			with Gaffer.UndoScope( srcPlug.ancestor( Gaffer.ScriptNode ) ) :
				srcState = self.__getValuesAndInputs( srcPlug )
				for i in range( srcIndex, dstIndex + 1, -1 ) :
					self.__setValuesAndInputs( parent[i], self.__getValuesAndInputs( parent[i-1] ) )
				self.__setValuesAndInputs( parent[dstIndex + 1], srcState )

		self.__currentDragTarget.setHighlighted( False )
		self.__currentDragTarget = None

		return True

	def __sourcePlug( self, dragEvent ) :

		if not isinstance( dragEvent.sourceWidget, _DragHandle ) :
			return None

		if dragEvent.data != IECore.NullObject.defaultNullObject() :
			return None

		sourcePlug = dragEvent.sourceWidget.ancestor( _RowPlugValueWidget ).getPlug()
		if sourcePlug.parent() == self.getPlug() :
			return sourcePlug

		return None

	def __destinationDivider( self, dragEvent ) :

		for plug in reversed( self.getPlug().children() ) :
			row = self.childPlugValueWidget( plug )
			yMin = row.bound( relativeTo = self ).min().y
			yMax = row._dragDivider().bound( relativeTo = self ).min().y - 4
			yCenter = (yMin + yMax) / 2.0
			if dragEvent.line.p0.y > yCenter or plug == self.getPlug()[0] :
				return row._dragDivider()

	@staticmethod
	def __getValuesAndInputs( plug ) :

		result = []
		for child in Gaffer.Plug.Range( plug ) :
			if child.getInput() is not None :
				result.append( child.getInput() )
			elif hasattr( child, "getValue" ) :
				result.append( child.getValue() )
			else :
				result.append( None )

		return result

	@staticmethod
	def __setValuesAndInputs( plug, valuesAndInputs ) :

		for i, valueOrInput in enumerate( valuesAndInputs ) :
			if isinstance( valueOrInput, Gaffer.Plug ) :
				plug[i].setInput( valueOrInput )
			else :
				plug[i].setInput( None )
				if valueOrInput is not None :
					plug[i].setValue( valueOrInput )

class _DragHandle( GafferUI.Image ) :

	def __init__( self, **kw ) :

		GafferUI.Image.__init__( self, "reorderVertically.png", **kw )

		self.enterSignal().connect( Gaffer.WeakMethod( self.__enter ), scoped = False )
		self.leaveSignal().connect( Gaffer.WeakMethod( self.__leave ), scoped = False )
		self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
		self.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ), scoped = False )

	def __enter( self, widget ) :

		GafferUI.Pointer.setCurrent( "moveVertically" )

	def __leave( self, widget ) :

		GafferUI.Pointer.setCurrent( None )

	def __buttonPress( self, widget, event ) :

		return event.buttons == event.Buttons.Left

	def __dragBegin( self, widget, event ) :

		if event.buttons == event.Buttons.Left :
			# NullObject is the convention for data for private drags.
			return IECore.NullObject().defaultNullObject()

# Widget for an individual input.
class _RowPlugValueWidget( GafferUI.PlugValueWidget ) :

	__labelWidth = 200

	def __init__( self, plug ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, column, plug )

		with column :

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				self.__dragHandle = _DragHandle()
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) as self.__defaultLabel :
					# Spacers on default row occupy the space taken by PlugValueWidgets on
					# non-default rows. This keeps the ConnectionPlugValueWidgets in alignment.
					GafferUI.Spacer( imath.V2i( 11, 1 ) )
					label = GafferUI.Label( "Default", horizontalAlignment = GafferUI.HorizontalAlignment.Left )
					label._qtWidget().setFixedWidth( self.__labelWidth )
					GafferUI.Spacer( imath.V2i( 25, 1 ) )

				self.__plugValueWidgets = []
				self.__plugValueWidgets.append( GafferUI.StringPlugValueWidget( plug["name"] ) )
				self.__plugValueWidgets.append( GafferUI.BoolPlugValueWidget( plug["enabled"], displayMode = GafferUI.BoolWidget.DisplayMode.Switch ) )
				self.__plugValueWidgets.append( GafferUI.PlugValueWidget.create( plug["value"] ) )

				self.__plugValueWidgets[0].textWidget()._qtWidget().setFixedWidth( self.__labelWidth )

			self.__dragDivider = GafferUI.Divider()

		self.__updateWidgetVisibility()
		self._updateFromPlug()

	def setPlug( self, plug ) :

		GafferUI.PlugValueWidget.setPlug( self, plug )

		self.__plugValueWidgets[0].setPlug( plug["name"] )
		self.__plugValueWidgets[1].setPlug( plug["enabled"] )
		self.__plugValueWidgets[2].setPlug( plug["value"] )

		self.__updateWidgetVisibility()

	def hasLabel( self ) :

		return True

	def childPlugValueWidget( self, childPlug, lazy=True ) :

		for w in self.__plugValueWidgets :
			if w.getPlug().isSame( childPlug ) :
				return w

		return None

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )

		for w in self.__plugValueWidgets :
			w.setReadOnly( readOnly )

	def _updateFromPlug( self ) :

		enabled = False
		with self.getContext() :
			with IECore.IgnoredExceptions( Gaffer.ProcessException ) :
				enabled = self.getPlug()["enabled"].getValue()

		self.__plugValueWidgets[0].setEnabled( enabled )
		self.__plugValueWidgets[2].setEnabled( enabled )

		self.__dragHandle.setEnabled(
			not self.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( self.getPlug() )
		)

	def __updateWidgetVisibility( self ) :

		default = False
		if self.getPlug() is not None :
			default = self.getPlug().parent().children().index( self.getPlug() ) == 0

		self.__defaultLabel.setVisible( default )
		self.__dragHandle.setVisible( not default )
		self.__plugValueWidgets[0].setVisible( not default )
		self.__plugValueWidgets[1].setVisible( not default )

	# Exposed only for use by _InPlugValueWidget. Really, it would be better if we could
	# move all the drag handling to _InPlugValueWidget, including the creation
	# of the drag handles and dividers. Currently this doesn't seem possible without duplicating
	# much of the code from _PlugLayout, so for now we use a compromise where _RowPlugValueWidget
	# manages the widgets and _InPlugValueWidget implements the behaviour.
	def _dragDivider( self ) :

		return self.__dragDivider