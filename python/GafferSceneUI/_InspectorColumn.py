##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

import enum
import functools

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

from GafferUI.PlugValueWidget import sole
from GafferSceneUI._HistoryWindow import _HistoryWindow

# This file extends the C++ functionality of InspectorColumn with functionality
# that is easier to implement in Python. This should all be considered as one
# component.

def __toggleBoolean( pathListing, inspections ) :

	# Make sure all the inspections contain and accept BoolData
	if not all(
		isinstance( i.value(), IECore.BoolData ) and i.canEdit( IECore.BoolData( True ) )
		for i in inspections
	) :
		return False

	# Default to `True` if values differ.
	newValue = not sole( [ i.value().value for i in inspections ] )

	with Gaffer.UndoScope( pathListing.ancestor( GafferUI.Editor ).scriptNode() ) :
		for inspection in inspections :
			inspection.edit( IECore.BoolData( newValue ) )

	return True

def __editSelectedCells( pathListing, quickBoolean = True, ensureEnabled = False ) :

	global __inspectorColumnPopup

	inspections = []

	path = pathListing.getPath().copy()
	for selection, column in zip( pathListing.getSelection(), pathListing.getColumns() ) :
		for pathString in selection.paths() :
			path.setFromString( pathString )
			inspectionContext = path.inspectionContext()
			if inspectionContext is None :
				continue

			with inspectionContext :
				inspection = column.inspector().inspect()

				if inspection is not None :
					inspections.append( inspection )

	if len( inspections ) == 0 :
		with GafferUI.PopupWindow() as __inspectorColumnPopup :
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
				GafferUI.Image( "warningSmall.png" )
				GafferUI.Label( "<h4>The selected cells cannot be edited in the current Edit Scope</h4>" )

		__inspectorColumnPopup.popup( parent = pathListing )

		return

	nonEditable = [ i for i in inspections if not i.editable() ]

	if len( nonEditable ) == 0 :
		if not quickBoolean or not __toggleBoolean( pathListing, inspections ) :
			edits = [ i.acquireEdit() for i in inspections ]
			warnings = "\n".join( [ i.editWarning() for i in inspections if i.editWarning() != "" ] )

			if ensureEnabled :
				with Gaffer.UndoScope( pathListing.ancestor( GafferUI.Editor ).scriptNode() ) :
					for edit in edits :
						if isinstance( edit, ( Gaffer.NameValuePlug, Gaffer.OptionalValuePlug, Gaffer.TweakPlug ) ) :
							edit["enabled"].setValue( True )

			# The plugs are either not boolean, boolean with mixed values,
			# or attributes that don't exist and are not boolean. Show the popup.
			__inspectorColumnPopup = GafferUI.PlugPopup( edits, warning = warnings )

			if isinstance( __inspectorColumnPopup.plugValueWidget(), GafferUI.TweakPlugValueWidget ) :
				__inspectorColumnPopup.plugValueWidget().setNameVisible( False )

			__inspectorColumnPopup.popup( parent = pathListing )

	else :
		with GafferUI.PopupWindow() as __inspectorColumnPopup :
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
				GafferUI.Image( "warningSmall.png" )
				GafferUI.Label( "<h4>{}</h4>".format( nonEditable[0].nonEditableReason() ) )

		__inspectorColumnPopup.popup( parent = pathListing )

def __toggleableInspections( pathListing ) :

	inspections = []
	nonEditableReason = ""
	toggleShouldDisable = True

	path = pathListing.getPath().copy()
	for columnSelection, column in zip( pathListing.getSelection(), pathListing.getColumns() ) :
		for pathString in columnSelection.paths() :
			path.setFromString( pathString )
			inspectionContext = path.inspectionContext()
			if inspectionContext is None :
				continue

			with inspectionContext :
				inspection = column.inspector().inspect()
				if inspection is None :
					continue

				canReenableEdit = False
				if not inspection.canDisableEdit() and inspection.editable() :
					edit = inspection.acquireEdit( createIfNecessary = False )
					canReenableEdit = isinstance( edit, ( Gaffer.NameValuePlug, Gaffer.OptionalValuePlug, Gaffer.TweakPlug ) ) and Gaffer.Metadata.value( edit, "inspector:disabledEdit" )
					if canReenableEdit :
						toggleShouldDisable = False

				if canReenableEdit or inspection.canDisableEdit() :
					inspections.append( inspection )
				elif nonEditableReason == "" :
					# Prefix reason with the column header to disambiguate when more than one column has selection
					nonEditableReason = "{} : ".format( column.headerData().value ) if len( [ x for x in pathListing.getSelection() if not x.isEmpty() ] ) > 1 else ""
					nonEditableReason += inspection.nonDisableableReason() if toggleShouldDisable else inspection.nonEditableReason()

	return inspections, nonEditableReason, toggleShouldDisable

def __toggleEditEnabled( pathListing ) :

	global __inspectorColumnPopup

	inspections, nonEditableReason, shouldDisable = __toggleableInspections( pathListing )

	if nonEditableReason != "" :
		with GafferUI.PopupWindow() as __inspectorColumnPopup :
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
				GafferUI.Image( "warningSmall.png" )
				GafferUI.Label( "<h4>{}</h4>".format( nonEditableReason ) )

			__inspectorColumnPopup.popup( parent = pathListing )

		return

	with Gaffer.UndoScope( pathListing.ancestor( GafferUI.Editor ).scriptNode() ) :
		for inspection in inspections :
			if shouldDisable :
				inspection.disableEdit()
				# We register non-persistent metadata on disabled edits to later determine
				# whether the disabled edit is a suitable candidate for enabling. This allows
				# investigative toggling of edits in the current session while avoiding enabling
				# edits the user may not expect to exist, such as previously unedited spreadsheet
				# cells in EditScope processors.
				Gaffer.Metadata.registerValue( inspection.source(), "inspector:disabledEdit", True, persistent = False )
			else :
				edit = inspection.acquireEdit( createIfNecessary = False )
				edit["enabled"].setValue( True )
				Gaffer.Metadata.deregisterValue( edit, "inspector:disabledEdit" )

def __removableAttributeInspections( pathListing ) :

	inspections = []

	path = pathListing.getPath().copy()
	for columnSelection, column in zip( pathListing.getSelection(), pathListing.getColumns() ) :
		if not columnSelection.isEmpty() and type( column.inspector() ) != GafferSceneUI.Private.AttributeInspector :
			return []
		for pathString in columnSelection.paths() :
			path.setFromString( pathString )
			inspectionContext = path.inspectionContext()
			if inspectionContext is None :
				continue

			with inspectionContext :
				inspection = column.inspector().inspect()
				if inspection is not None and inspection.editable() :
					source = inspection.source()
					if (
						( isinstance( source, Gaffer.TweakPlug ) and source["mode"].getValue() != Gaffer.TweakPlug.Mode.Remove ) or
						( isinstance( source, Gaffer.ValuePlug ) and len( source.children() ) == 2 and "Added" in source and "Removed" in source ) or
						inspection.editScope() is not None
					) :
						inspections.append( inspection )
					else :
						return []
				else :
					return []

	return inspections

def __removeAttributes( pathListing ) :

	inspections = __removableAttributeInspections( pathListing )

	with Gaffer.UndoScope( pathListing.ancestor( GafferUI.Editor ).scriptNode() ) :
		for inspection in inspections :
			tweak = inspection.acquireEdit()
			tweak["enabled"].setValue( True )
			tweak["mode"].setValue( Gaffer.TweakPlug.Mode.Remove )

def __selectedSetExpressions( pathListing ) :

	# A dictionary of the form :
	# { path1 : set( setExpression1, setExpression2 ), path2 : set( setExpression1 ), ... }
	result = {}

	# Map of Inspectors to metadata prefixes.
	prefixMap = {
		GafferSceneUI.Private.OptionInspector : "option:",
		GafferSceneUI.Private.AttributeInspector : "attribute:"
	}

	path = pathListing.getPath().copy()
	for columnSelection, column in zip( pathListing.getSelection(), pathListing.getColumns() ) :
		if (
			not columnSelection.isEmpty() and (
				type( column.inspector() ) not in prefixMap.keys() or
				not (
					Gaffer.Metadata.value( prefixMap.get( type( column.inspector() ) ) + column.inspector().name(), "ui:scene:acceptsSetName" ) or
					Gaffer.Metadata.value( prefixMap.get( type( column.inspector() ) ) + column.inspector().name(), "ui:scene:acceptsSetNames" ) or
					Gaffer.Metadata.value( prefixMap.get( type( column.inspector() ) ) + column.inspector().name(), "ui:scene:acceptsSetExpression" )
				)
			)
		) :
			# We only return set expressions if all selected paths are in
			# columns that accept set names or set expressions.
			return {}

		for pathString in columnSelection.paths() :
			path.setFromString( pathString )
			cellValue = column.cellData( path ).value
			if cellValue is not None :
				result.setdefault( pathString, set() ).add( cellValue )
			else :
				# We only return set expressions if all selected paths have values.
				return {}

	return result

def __selectAffected( pathListing ) :

	result = IECore.PathMatcher()

	editor = pathListing.ancestor( GafferUI.Editor )
	path = pathListing.getPath().copy()

	for pathString, setExpressions in __selectedSetExpressions( pathListing ).items() :
		# Evaluate set expressions within their path's inspection context
		# as set membership could vary based on the context.
		path.setFromString( pathString )
		with path.inspectionContext() :
			for setExpression in setExpressions :
				result.addPaths( GafferScene.SetAlgo.evaluateSetExpression( setExpression, editor.settings()["in"] ) )

	GafferSceneUI.ScriptNodeAlgo.setSelectedPaths( editor.scriptNode(), result )

def __showHistory( pathListing ) :

	columns = pathListing.getColumns()
	selection = pathListing.getSelection()

	for i, column in enumerate( columns ) :
		for pathString in selection[i].paths() :
			path = pathListing.getPath().copy()
			path.setFromString( pathString )
			if path.inspectionContext() is None :
				continue
			window = _HistoryWindow(
				column.inspector(),
				path,
				"History : {} : {}".format( pathString, column.headerData().value )
			)
			pathListing.ancestor( GafferUI.Window ).addChildWindow( window, removeOnClose = True )
			window.setVisible( True )

def __validateSelection( pathListing ) :

	selection = pathListing.getSelection()
	# We only operate on PathListingWidgets
	# with `Cell` or `Cells` selection modes.
	if not isinstance( selection, list ) :
		return False

	if all( [ x.isEmpty() for x in selection ] ) :
		return False

	for columnSelection, column in zip( selection, pathListing.getColumns() ) :
		if not columnSelection.isEmpty() and not isinstance( column, GafferSceneUI.Private.InspectorColumn ) :
			return False

	return True

def __buttonDoubleClick( path, pathListing, event ) :

	# We only support doubleClick events when all of the selected
	# cells are in InspectorColumns.
	if not __validateSelection( pathListing ) :
		return False

	if event.button == event.Buttons.Left :
		__editSelectedCells( pathListing )
		return True

	return False

def __contextMenu( column, pathListing, menuDefinition ) :

	# We only add context menu items when all of the selected
	# cells are in InspectorColumns.
	if not __validateSelection( pathListing ) :
		return

	menuDefinition.append(
		"Show History...",
		{
			"command" : functools.partial( __showHistory, pathListing )
		}
	)

	toggleOnly = isinstance( column.inspector(), GafferSceneUI.Private.SetMembershipInspector )
	menuDefinition.append(
		"Toggle" if toggleOnly else "Edit...",
		{
			"command" : functools.partial( __editSelectedCells, pathListing, toggleOnly ),
		}
	)
	inspections, nonEditableReason, disable = __toggleableInspections( pathListing )
	menuDefinition.append(
		"{} Edit{}".format( "Disable" if disable else "Reenable", "s" if len( inspections ) > 1 else "" ),
		{
			"command" : functools.partial( __toggleEditEnabled, pathListing ),
			"active" : len( inspections ) > 0 and nonEditableReason == "",
			"shortCut" : "D",
			"description" : nonEditableReason,
		}
	)

	if len( __removableAttributeInspections( pathListing ) ) > 0 :
		menuDefinition.append(
			"Remove Attribute",
			{
				"command" : functools.partial( __removeAttributes, pathListing ),
				"shortCut" : "Backspace, Delete",
			}
		)

	if len( __selectedSetExpressions( pathListing ) ) > 0 :
		menuDefinition.append(
			"SelectAffectedObjectsDivider", { "divider" : True }
		)
		menuDefinition.append(
			"Select Affected Objects",
			{
				"command" : functools.partial( __selectAffected, pathListing ),
			}
		)

def __keyPress( column, pathListing, event ) :

	# We only support keyPress events when all of the selected
	# cells are in InspectorColumns.
	if not __validateSelection( pathListing ) :
		return

	if event.key in ( "Return", "Enter" ) and event.modifiers in ( event.Modifiers.None_, event.modifiers.Control ):
		__editSelectedCells( pathListing, ensureEnabled = event.modifiers == event.modifiers.Control )
		return True

	if event.modifiers == event.Modifiers.None_ :

		if event.key == "D" :
			inspections, nonEditableReason, _ = __toggleableInspections( pathListing )
			# We allow toggling when there is a nonEditableReason to let __toggleEditEnabled
			# present the reason to the user via a popup.
			if len( inspections ) > 0 or nonEditableReason != "" :
				__toggleEditEnabled( pathListing )
			return True

		if event.key in ( "Backspace", "Delete" ) :
			if len( __removableAttributeInspections( pathListing ) ) > 0 :
				__removeAttributes( pathListing )
			return True

	return False

__originalDragPointer = None
__DropMode = enum.Enum( "__DropMode", [ "Add", "Remove", "Replace", "NotEditable" ] )

def __dragEnter( column, path, pathListing, event ) :

	global __originalDragPointer
	if __originalDragPointer is None :
		__originalDragPointer = GafferUI.Pointer.getCurrent()

	if path is None :
		return False

	inspectionContext = path.inspectionContext()
	if inspectionContext is None :
		return False

	with inspectionContext :
		inspection = column.inspector().inspect()
		if inspection is None :
			return False

		__updatePointer( column, inspection, event )

	return True

def __dragLeave( column, path, pathListing, event ) :

	global __originalDragPointer
	if __originalDragPointer is None :
		return False

	GafferUI.Pointer.setCurrent( __originalDragPointer )
	__originalDragPointer = None

	return True

def __dragMove( column, path, pathListing, event ) :

	if path is None :
		return False

	inspectionContext = path.inspectionContext()
	if inspectionContext is None :
		return False

	with inspectionContext :
		inspection = column.inspector().inspect()
		if inspection is None :
			return False

		__updatePointer( column, inspection, event )

	return True

def __updatePointer( column, inspection, event ) :

	dropMode = __dropMode( column, inspection, event )
	if dropMode == __DropMode.Add :
		GafferUI.Pointer.setCurrent( "add" )
	elif dropMode == __DropMode.Remove :
		GafferUI.Pointer.setCurrent( "remove" )
	elif dropMode == __DropMode.NotEditable :
		GafferUI.Pointer.setCurrent( "notEditable" )
	else :
		GafferUI.Pointer.setCurrent( __originalDragPointer )

def __dropMode( column, inspection, event ) :

	if isinstance( inspection.value(), IECore.StringData ) and (
		__columnMetadata( column, "ui:scene:acceptsSetNames" ) or __columnMetadata( column, "ui:scene:acceptsSetExpression" )
	)  :
		if event.modifiers == event.Modifiers.Shift :
			return __DropMode.Add if __updatable( inspection ) else __DropMode.NotEditable
		elif event.modifiers == event.Modifiers.Control :
			return __DropMode.Remove if __updatable( inspection ) else __DropMode.NotEditable
	elif isinstance( inspection.value(), IECore.StringVectorData ) :
		if event.modifiers == event.Modifiers.Shift :
			return __DropMode.Add
		elif event.modifiers == event.Modifiers.Control :
			return __DropMode.Remove

	return __DropMode.Replace

def __updatable( inspection ) :

	if isinstance( inspection.value(), IECore.StringData ) :
		if any( i in inspection.value().value for i in [ "(", ")", "|", "-", "&" ] ) :
			return False

		plugTokens = inspection.value().value.split( " " )
		if any( i in plugTokens for i in [ "in", "containing" ] ) :
			return False

	return True

def __drop( column, path, pathListing, event ) :

	if path is None :
		return False

	inspectionContext = path.inspectionContext()
	if inspectionContext is None :
		return False

	global __originalDragPointer
	if __originalDragPointer is not None :
		GafferUI.Pointer.setCurrent( __originalDragPointer )
		__originalDragPointer = None

	with inspectionContext :
		inspection = column.inspector().inspect()
		if inspection is None :
			return True

		if __dropMode( column, inspection, event ) == __DropMode.NotEditable :
			__warningPopup( pathListing, "Cannot modify set expressions containing operators with drag and drop." )
			return True

		data = __dropData( column, inspection, event )
		if not inspection.canEdit( data ) :
			__warningPopup( pathListing, inspection.nonEditableReason( data ) or "Unable to edit." )
			return True

		with Gaffer.UndoScope( pathListing.ancestor( GafferUI.Editor ).scriptNode() ) :
			inspection.edit( data )

	return True

def __dropData( column, inspection, event ) :

	if isinstance( event.data, IECore.StringVectorData ) and isinstance( inspection.value(), IECore.StringData ) :
		data = IECore.StringData( " ".join( event.data ) )
	elif isinstance( event.data, IECore.StringData ) and isinstance( inspection.value(), IECore.StringVectorData ) :
		data = IECore.StringVectorData( event.data.value.split( " " ) )
	else :
		data = event.data

	mode = __dropMode( column, inspection, event )
	if mode == __DropMode.Replace or not isinstance( inspection.value(), ( IECore.StringData, IECore.StringVectorData ) ) :
		return data

	strings = set( inspection.value().value.split( " " ) if isinstance( inspection.value(), IECore.StringData ) else inspection.value() )
	updateData = event.data.value.split( " " ) if isinstance( event.data, IECore.StringData ) else event.data

	if mode == __DropMode.Add :
		strings.update( updateData )
	elif mode == __DropMode.Remove :
		strings.difference_update( updateData )
	else :
		return data

	if isinstance( inspection.value(), IECore.StringData ) :
		return IECore.StringData( " ".join( sorted( strings ) ) )
	else :
		return IECore.StringVectorData( sorted( strings ) )

def __warningPopup( parent, message ) :

	global __inspectorColumnPopup

	with GafferUI.PopupWindow() as __inspectorColumnPopup :
		with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
			GafferUI.Image( "warningSmall.png" )
			GafferUI.Label( "<h4>{}</h4>".format( message ) )

	__inspectorColumnPopup.popup( parent = parent )

def __columnMetadata( column, metadataKey ) :

	# Map of Inspectors to metadata prefixes.
	prefixMap = {
		GafferSceneUI.Private.OptionInspector : "option:",
		GafferSceneUI.Private.AttributeInspector : "attribute:"
	}

	if type( column.inspector() ) not in prefixMap.keys() :
		return None

	return Gaffer.Metadata.value( prefixMap.get( type( column.inspector() ) ) + column.inspector().name(), metadataKey )

def __inspectorColumnCreated( column ) :

	if isinstance( column, GafferSceneUI.Private.InspectorColumn ) :
		column.buttonDoubleClickSignal().connectFront( __buttonDoubleClick )
		column.contextMenuSignal().connectFront( __contextMenu )
		column.keyPressSignal().connectFront( __keyPress )
		column.dragEnterSignal().connectFront( __dragEnter )
		column.dragMoveSignal().connectFront( __dragMove )
		column.dragLeaveSignal().connectFront( __dragLeave )
		column.dropSignal().connectFront( __drop )

GafferSceneUI.Private.InspectorColumn.instanceCreatedSignal().connect( __inspectorColumnCreated )
