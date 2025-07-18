##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

class _OperationIconColumn( GafferUI.PathColumn ) :

	def __init__( self ) :

		GafferUI.PathColumn.__init__( self )

	def cellData( self, path, canceller = None ) :

		cellValue = path.property( "history:operation", canceller )

		data = self.CellData()

		data.icon = {
			Gaffer.TweakPlug.Mode.Replace : "replaceSmall.png",
			Gaffer.TweakPlug.Mode.Add : "plusSmall.png",
			Gaffer.TweakPlug.Mode.Subtract : "minusSmall.png",
			Gaffer.TweakPlug.Mode.Multiply : "multiplySmall.png",
			Gaffer.TweakPlug.Mode.Remove : "removeSmall.png",
			Gaffer.TweakPlug.Mode.Create : "createSmall.png",
			Gaffer.TweakPlug.Mode.CreateIfMissing : "createIfMissingSmall.png",
			Gaffer.TweakPlug.Mode.Min : "lessThanSmall.png",
			Gaffer.TweakPlug.Mode.Max : "greaterThanSmall.png",
			Gaffer.TweakPlug.Mode.ListAppend : "listAppendSmall.png",
			Gaffer.TweakPlug.Mode.ListPrepend : "listPrependSmall.png",
			Gaffer.TweakPlug.Mode.ListRemove : "listRemoveSmall.png",
		}.get( cellValue )

		return data

	def headerData( self, canceller = None ) :

		return self.CellData( "Operation" )

class _NodeNameColumn( GafferUI.PathColumn ) :

	def __init__( self ) :

		GafferUI.PathColumn.__init__( self )

	def cellData( self, path, canceller = None ) :

		node = path.property( "history:node", canceller )
		return self.CellData( node.relativeName( node.scriptNode() ) )

	def headerData( self, canceller = None ) :

		return self.CellData( "Node" )

# \todo This duplicates logic from (in this case) `_GafferSceneUI._LightEditorInspectorColumn`.
# Refactor to allow calling `_GafferSceneUI.InspectorColumn.cellData()` from `_HistoryWindow` to
# remove this duplication for columns that customize their value presentation.
class _ValueColumn( GafferUI.PathColumn ) :

	def __init__( self ) :

		GafferUI.PathColumn.__init__( self )

	def cellData( self, path, canceller = None ) :

		cellValue = path.property( "history:value", canceller )
		fallbackValue = path.property( "history:fallbackValue", canceller )

		data = self.CellData()

		if cellValue is not None :
			data.value = cellValue
		elif fallbackValue is not None :
			data.value = fallbackValue
			data.foreground = imath.Color4f( 0.64, 0.64, 0.64, 1.0 )

		if isinstance( data.value, ( imath.Color3f, imath.Color4f ) ) :
			data.icon = data.value

		return data

	def headerData( self, canceller = None ) :

		return self.CellData( "Value" )

class _HistoryWindow( GafferUI.Window ) :

	def __init__( self, inspectorColumn, inspectionRootPath, inspectionPathString, title=None, **kw ) :

		if title is None :
			title = "History"

		GafferUI.Window.__init__( self, title, **kw )

		self.__inspectorColumn = inspectorColumn
		self.__inspectionRootPath = inspectionRootPath
		self.__inspectionPathString = inspectionPathString

		with self :
			self.__pathListingWidget = GafferUI.PathListingWidget(
				Gaffer.DictPath( {}, "/" ),
				columns = (
					_NodeNameColumn(),
					_ValueColumn(),
					_OperationIconColumn(),
				),
				sortable = False,
				horizontalScrollMode = GafferUI.ScrollMode.Automatic,
				selectionMode = GafferUI.PathListingWidget.SelectionMode.Cell
			)

		self.__pathListingWidget.setDragPointer( "values" )

		self.__nameColumnIndex = 0
		self.__valueColumnIndex = 1
		self.__operationColumnIndex = 2

		self.__pathListingWidget.buttonDoubleClickSignal().connectFront( Gaffer.WeakMethod( self.__buttonDoubleClick ) )
		self.__pathListingWidget.keyPressSignal().connectFront( Gaffer.WeakMethod( self.__keyPress ) )
		self.__pathListingWidget.dragBeginSignal().connectFront( Gaffer.WeakMethod( self.__dragBegin ) )
		self.__pathListingWidget.updateFinishedSignal().connectFront( Gaffer.WeakMethod( self.__updateFinished ) )

		self.__inspectorColumn.changedSignal().connect( Gaffer.WeakMethod( self.__inspectorColumnChanged ) )
		self.__inspectionRootPath.pathChangedSignal().connect( Gaffer.WeakMethod( self.__inspectionRootPathChanged ) )

		self.__updatePath()

	def __updatePath( self ) :

		inspectionPath = self.__inspectionRootPath.copy()
		inspectionPath.setFromString( self.__inspectionPathString )
		self.__path = self.__inspectorColumn.historyPath( inspectionPath )
		if self.__path is None :
			self.close()
			return

		self.__pathListingWidget.setPath( self.__path )

	def __buttonDoubleClick( self, pathListing, event ) :

		if pathListing.pathAt( event.line.p0 ) is None :
			return False

		if event.buttons == event.Buttons.Left :
			self.__editSelectedCell( pathListing )

			return True

		return False

	def __keyPress( self, pathListing, event ) :

		if event.key == "Return" or event.key == "Enter" :
			self.__editSelectedCell( pathListing )

			return True

		return False

	def __editSelectedCell( self, pathListing ) :

		selection = pathListing.getSelection()

		selectedPath, selectedColumn = self.__selectionData( selection )

		if selectedColumn == self.__nameColumnIndex :
			GafferUI.NodeEditor.acquire(
				selectedPath.property( "history:node" ),
				floating = True
			)
		elif (
			( selectedColumn == self.__valueColumnIndex or selectedColumn == self.__operationColumnIndex ) and
			not isinstance( self.__inspector, GafferSceneUI.Private.SetMembershipInspector )
		) :
			editPlug = selectedPath.property( "history:source" )
			if editPlug is not None :
				self.__popup = GafferUI.PlugPopup(
					[ editPlug ], warning = selectedPath.property( "history:editWarning" )
				)
				if isinstance( self.__popup.plugValueWidget(), GafferUI.TweakPlugValueWidget ) :
					self.__popup.plugValueWidget().setNameVisible( False )

				self.__popup.popup( parent = self )

	def __dragBegin( self, pathListing, event ) :

		selection = pathListing.getSelection()

		selectedPath, selectedColumn = self.__selectionData( selection )

		if selectedColumn == self.__nameColumnIndex :
			GafferUI.Pointer.setCurrent( "nodes" )
			return selectedPath.property( "history:node" )

		elif selectedColumn == self.__operationColumnIndex :
			operation = selectedPath.property( "history:operation" )
			if operation is not None :
				GafferUI.Pointer.setCurrent( "values" )
				return operation

		# Value column works by default

	def __selectionData( self, selection ) :

		# Return a tuple of (selectedPath, selectedColumnIndex )

		columnIndex = None

		for i in range( 0, len( selection ) ) :
			if selection[i].size() > 0 :
				selectedPathString = selection[i].paths()[0]
				columnIndex = i

		for path in self.__path.children() :
			if str( path ) == selectedPathString :
				return (path, columnIndex )

		return None

	def __inspectorColumnChanged( self, inspectorColumn ) :

		self.__updatePath()

	def __inspectionRootPathChanged( self, contextTracker ) :

		self.__updatePath()

	def __updateFinished( self, pathListing ) :

		# Note : Now the update is finished, we know our HistoryPath has
		# computed and cached everything internally. So we can call `children()`
		# without fear of blocking the UI waiting for it to compute.

		# Close window if there's no longer anything to show.

		if len( self.__path.children() ) == 0 :
			# History is empty, for example because the scene location no
			# longer exists.
			self.close()
			return

		# Arrange to signal changes for the node name
		# column if any nodes are renamed.

		self.__nodeNameChangedSignals = {}
		for path in self.__path.children() :

			# The node and all of its parents up to the script node
			# contribute to the path name.

			node = path.property( "history:node" )
			while node is not None and not isinstance( node, Gaffer.ScriptNode ) :
				if node not in self.__nodeNameChangedSignals :
					self.__nodeNameChangedSignals[node] = node.nameChangedSignal().connect(
						Gaffer.WeakMethod( self.__nodeNameChanged ),
						scoped = True
					)

				node = node.parent()

	def __nodeNameChanged( self, node, oldName ) :

		nameColumn = self.__pathListingWidget.getColumns()[0]
		nameColumn.changedSignal()( nameColumn )
