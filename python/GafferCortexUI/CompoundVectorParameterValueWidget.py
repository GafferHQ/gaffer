##########################################################################
#
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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
import GafferCortexUI

## Supported userData entries :
#
# ["UI"]["sizeEditable"]
# ["UI"]["showIndices"]
#
# Supported child parameter userData entries :
#
# ["UI"]["editable"]
# ["UI"]["elementPresets"] ObjectVector containing presets of the following form :
#
#	IECore.CompoundData(
#		{  "label" : StringData() , "value" : Data() }
#	)
#
# ["UI"]["elementPresetsOnly"] BoolData.
class CompoundVectorParameterValueWidget( GafferCortexUI.CompoundParameterValueWidget ) :

	def __init__( self, parameterHandler, collapsible=None, **kw ) :

		GafferCortexUI.CompoundParameterValueWidget.__init__( self, parameterHandler, collapsible, _plugValueWidgetClass=_PlugValueWidget, **kw )

class _PlugValueWidget( GafferCortexUI.CompoundParameterValueWidget._PlugValueWidget ) :

	def __init__( self, parameterHandler, collapsed ) :

		GafferCortexUI.CompoundParameterValueWidget._PlugValueWidget.__init__( self, parameterHandler, collapsed )

		self.__vectorDataWidget = None

	def _headerWidget( self ) :

		if self.__vectorDataWidget is not None :
			return self.__vectorDataWidget

		header = [ IECore.CamelCase.toSpaced( x ) for x in self._parameter().keys() ]
		columnToolTips = [ self._parameterToolTip( self._parameterHandler().childParameterHandler( x ) ) for x in self._parameter().values() ]

		showIndices = True
		with IECore.IgnoredExceptions( KeyError ) :
			showIndices = self._parameterHandler().parameter().userData()["UI"]["showIndices"].value

		sizeEditable = True
		with IECore.IgnoredExceptions( KeyError ) :
			sizeEditable = self._parameterHandler().parameter().userData()["UI"]["sizeEditable"].value

		self.__vectorDataWidget = _VectorDataWidget(
			header = header,
			columnToolTips = columnToolTips,
			showIndices = showIndices,
			sizeEditable = sizeEditable,
		)

		self.__vectorDataWidget.editSignal().connect( Gaffer.WeakMethod( self.__edit ), scoped = False )
		self.__vectorDataWidget.dataChangedSignal().connect( Gaffer.WeakMethod( self.__dataChanged ), scoped = False )

		self._updateFromPlug()

		return self.__vectorDataWidget

	def _childPlugs( self ) :

		# because we represent everything in the header we don't
		# need any plug widgets made by the base class.
		return []

	def _updateFromPlug( self ) :

		GafferCortexUI.CompoundParameterValueWidget._PlugValueWidget._updateFromPlug( self )

		if self.__vectorDataWidget is None:
			return

		data = []
		for plug in self._parameterHandler().plug().children() :
			plugData = plug.getValue()
			if len( data ) and len( plugData ) != len( data[0] ) :
				# in __dataChanged we have to update the child plug values
				# one at a time. when adding or removing rows, this means that the
				# columns will have differing lengths until the last plug
				# has been set. in this case we shortcut ourselves, and wait
				# for the final plug to be set before updating the VectorDataWidget.
				# \todo Now dirty propagation is batched via the UndoScope,
				# we should remove this workaround, since _updateFromPlug()
				# will only be called when the plug is in a valid state.
				return
			data.append( plugData )

		self.__vectorDataWidget.setData( data )
		self.__vectorDataWidget.setEditable( self._editable() )

		for columnIndex, childParameter in enumerate( self._parameter().values() ) :

			columnVisible = True
			with IECore.IgnoredExceptions( KeyError ) :
				columnVisible = childParameter.userData()["UI"]["visible"].value
			self.__vectorDataWidget.setColumnVisible( columnIndex, columnVisible )

			columnEditable = True
			with IECore.IgnoredExceptions( KeyError ) :
				columnEditable = childParameter.userData()["UI"]["editable"].value
			self.__vectorDataWidget.setColumnEditable( columnIndex, columnEditable )

	def __edit( self, vectorDataWidget, column, row ) :

		dataIndex, componentIndex = vectorDataWidget.columnToDataIndex( column )
		childParameter = self._parameter().values()[dataIndex]

		presetsOnly = False
		with IECore.IgnoredExceptions( KeyError ) :
			presetsOnly = childParameter.userData()["UI"]["elementPresetsOnly"].value

		if not presetsOnly :
			return None

		return _PresetEditor( childParameter )

	def __dataChanged( self, vectorDataWidget ) :

		data = vectorDataWidget.getData()

		with Gaffer.Signals.BlockedConnection( self._plugConnections() ) :
			with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
				for d, p in zip( data, self._parameterHandler().plug().children() ) :
					p.setValue( d )

GafferCortexUI.ParameterValueWidget.registerType( IECore.CompoundVectorParameter, CompoundVectorParameterValueWidget )

# Deriving from ListContainer and not adding any children, so that we're
# entirely see-through, allowing the underlying cell value to remain visible.
class _PresetEditor( GafferUI.ListContainer ) :

	def __init__( self, parameter ) :

		GafferUI.ListContainer.__init__( self )

		self.__parameter = parameter
		self.__menu = None

	def setValue( self, value ) :

		self.__value = value

		# show the menu on the first setValue() call, as
		# in the constructor we don't yet have a parent or
		# a position on screen.
		self.__showMenu()

	def getValue( self ) :

		return self.__value

	def __showMenu( self ) :

		if self.__menu is not None :
			return

		m = IECore.MenuDefinition()
		for preset in self.__parameter.userData()["UI"]["elementPresets"] :
			m.append(
				"/" + preset["label"].value,
				{
					"command" : IECore.curry( Gaffer.WeakMethod( self.__setPreset ), preset["value"].value ),
				},
			)

		self.__menu = GafferUI.Menu( m )

		bound = self.bound()
		self.__menu.popup( parent = self, position = imath.V2i( bound.min().x, bound.max().y ) )

		# necessary because the qt edit action tries to give us the focus, and we don't want it -
		# we want the menu to have it so it can be navigated with the cursor keys.
		self._qtWidget().setFocusProxy( self.__menu._qtWidget() )

	def __setPreset( self, presetValue ) :

		self.setValue( presetValue )
		self.setVisible( False ) # finish editing

class _VectorDataWidget( GafferUI.VectorDataWidget ) :

	def __init__( self, header, columnToolTips, showIndices, sizeEditable ) :

		GafferUI.VectorDataWidget.__init__(
			self,
			header = header,
			columnToolTips = columnToolTips,
			showIndices = showIndices,
			sizeEditable = sizeEditable,
		)

	# Reimplemented to tie the ParameterValueWidget.popupMenuSignal()
	# into the menu creation process.
	## \todo I feel that we should be able to unify everything much better, perhaps
	# to the point where everything is driven directly by Widget.contextMenuSignal().
	# See issue #217.
	def _contextMenuDefinition( self, selectedRows ) :

		m = GafferUI.VectorDataWidget._contextMenuDefinition( self, selectedRows )
		GafferCortexUI.ParameterValueWidget.popupMenuSignal()( m, self.ancestor( GafferCortexUI.ParameterValueWidget ) )
		return m

##########################################################################
# Parameter popup menu for per-element presets
##########################################################################

def __applyPreset( columnParameterHandler, indices, elementValue ) :

	value = columnParameterHandler.parameter().getValue()
	for index in indices :
		value[index] = elementValue

	with Gaffer.UndoScope( columnParameterHandler.plug().ancestor( Gaffer.ScriptNode ) ) :
		columnParameterHandler.setPlugValue()

def __parameterPopupMenu( menuDefinition, parameterValueWidget ) :

	if not isinstance( parameterValueWidget, CompoundVectorParameterValueWidget ) :
		return

	vectorDataWidget = parameterValueWidget.plugValueWidget()._headerWidget()
	if not vectorDataWidget.getEditable() :
		return

	selectedIndices = vectorDataWidget.selectedIndices()
	if not selectedIndices :
		return

	column = selectedIndices[0][0]
	for index in selectedIndices :
		if index[0] != column :
			# not all in the same column
			return

	parameter = parameterValueWidget.parameter()
	columnParameter = parameter.values()[vectorDataWidget.columnToDataIndex( column )[0]]

	with IECore.IgnoredExceptions( KeyError ) :
		if columnParameter.userData()["UI"]["editable"].value == False :
			return

	presets = None
	with IECore.IgnoredExceptions( KeyError ) :
		presets = columnParameter.userData()["UI"]["elementPresets"]

	if presets is None :
		return

	menuDefinition.prepend( "/PresetsDivider", { "divider" : True } )
	for preset in reversed( presets ) :
		menuDefinition.prepend(
			"/Apply Preset To Selection/" + preset["label"].value,
			{
				"command" : IECore.curry(
					__applyPreset,
					parameterValueWidget.parameterHandler().childParameterHandler( columnParameter ),
					[ index[1] for index in selectedIndices ],
					preset["value"].value,
				)
			},
		)

GafferCortexUI.ParameterValueWidget.popupMenuSignal().connect( __parameterPopupMenu, scoped = False )
