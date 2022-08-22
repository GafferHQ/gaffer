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

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

class _OperationIconColumn( GafferUI.PathColumn ) :

	def __init__( self, title, property ) :

		GafferUI.PathColumn.__init__( self )

		self.__title = title
		self.__property = property

	def cellData( self, path, canceller = None ) :

		cellValue = path.property( self.__property )

		data = self.CellData()

		data.icon = {
			Gaffer.TweakPlug.Mode.Replace : "replaceSmall.png",
			Gaffer.TweakPlug.Mode.Add : "plusSmall.png",
			Gaffer.TweakPlug.Mode.Subtract : "minusSmall.png",
			Gaffer.TweakPlug.Mode.Multiply : "multiplySmall.png",
			Gaffer.TweakPlug.Mode.Remove : "removeSmall.png",
			Gaffer.TweakPlug.Mode.Create : "createSmall.png",
			Gaffer.TweakPlug.Mode.Min : "lessThanSmall.png",
			Gaffer.TweakPlug.Mode.Max : "greaterThanSmall.png",
			Gaffer.TweakPlug.Mode.ListAppend : "listAppendSmall.png",
			Gaffer.TweakPlug.Mode.ListPrepend : "listPrependSmall.png",
			Gaffer.TweakPlug.Mode.ListRemove : "listRemoveSmall.png",
		}.get( cellValue, "errorSmall.png" )

		return data

	def headerData( self, canceller = None ) :

		return self.CellData( self.__title )

class _NodeNameColumn( GafferUI.PathColumn ) :

	def __init__( self, title, property, scriptNode ) :

		GafferUI.PathColumn.__init__( self )

		self.__title = title
		self.__property = property
		self.__scriptNode = scriptNode

	def cellData( self, path, canceller = None ) :

		cellValue = path.property( self.__property )

		data = self.CellData( cellValue.relativeName( self.__scriptNode ) )

		return data

	def headerData( self, canceller = None ) :

		return self.CellData( self.__title )

class _HistoryWindow( GafferUI.Window ) :

	def __init__( self, inspector, scenePath, context, scriptNode, title=None, **kw ) :

		assert( isinstance( scriptNode, Gaffer.ScriptNode ) )

		if title is None :
			title = "History"

		GafferUI.Window.__init__( self, title, **kw )

		self.__inspector = inspector
		self.__scenePath = scenePath
		self.__scriptNode = scriptNode

		with self :
			self.__pathListingWidget = GafferUI.PathListingWidget(
				Gaffer.DictPath( {}, "/" ),
				columns = (
					_NodeNameColumn( "Node", "history:node", self.__scriptNode ),
					GafferUI.PathListingWidget.StandardColumn( "Value", "history:value" ),
					_OperationIconColumn( "Operation", "history:operation" ),
				),
				sortable = False,
				horizontalScrollMode = GafferUI.ScrollMode.Automatic,
				selectionMode = GafferUI.PathListingWidget.SelectionMode.Cell
			)

		self.__pathListingWidget.setDragPointer( "values" )

		self.__nameColumnIndex = 0
		self.__valueColumnIndex = 1
		self.__operationColumnIndex = 2

		self.__pathListingWidget.buttonDoubleClickSignal().connectFront( Gaffer.WeakMethod( self.__buttonDoubleClick ), scoped = False )
		self.__pathListingWidget.keyPressSignal().connectFront( Gaffer.WeakMethod( self.__keyPress ), scoped = False )
		self.__pathListingWidget.dragBeginSignal().connectFront( Gaffer.WeakMethod( self.__dragBegin ), scoped = False )
		self.__pathListingWidget.updateFinishedSignal().connectFront( Gaffer.WeakMethod( self.__updateFinished ), scoped = False )

		inspector.dirtiedSignal().connect( Gaffer.WeakMethod( self.__inspectorDirtied ), scoped = False )

		context.changedSignal().connect( Gaffer.WeakMethod( self.__contextChanged ), scoped = False )

		self.__updatePath( context )

	def __updatePath( self, newContext ) :

		with Gaffer.Context( newContext ) as context :
			context["scene:path"] = GafferScene.ScenePlug.stringToPath( self.__scenePath )
			self.__path = self.__inspector.historyPath()
			self.__pathChangedConnection = self.__path.pathChangedSignal().connect( Gaffer.WeakMethod( self.__pathChanged ), scoped = True )

		self.__pathListingWidget.setPath( self.__path )

	def __pathChanged( self, path ) :

		if len( path.children() ) == 0 :
			self.close()

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
		elif selectedColumn == self.__valueColumnIndex or selectedColumn == self.__operationColumnIndex :
			editPlug = selectedPath.property( "history:source" )
			self.__popup = GafferUI.PlugPopup(
				[ editPlug ], warning = selectedPath.property( "history:editWarning" )
			)
			if isinstance( self.__popup.plugValueWidget(), GafferUI.TweakPlugValueWidget ) :
				self.__popup.plugValueWidget().setNameVisible( False )

			self.__popup.popup()

	def __dragBegin( self, pathListing, event ) :

		selection = pathListing.getSelection()

		selectedPath, selectedColumn = self.__selectionData( selection )

		if selectedColumn == self.__nameColumnIndex :
			GafferUI.Pointer.setCurrent( "nodes" )

			return selectedPath.property( "history:node" )

		elif selectedColumn == self.__operationColumnIndex :
			GafferUI.Pointer.setCurrent( "values" )

			return selectedPath.property( "history:operation" )

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

	def __inspectorDirtied( self, inspector ) :

		self.__path._emitPathChanged()

	def __contextChanged( self, context, key ) :

		self.__updatePath( context )

	def __updateFinished( self, pathListing ) :

		self.__nodeNameChangedSignals = []

		for path in self.__path.children() :
			node = path.property( "history:node" )

			# The node and all of its parents up to the script node
			# contribute to the path name.

			while node is not self.__scriptNode and node is not None :
				self.__nodeNameChangedSignals.append(
					node.nameChangedSignal().connect(
						Gaffer.WeakMethod( self.__nodeNameChanged ),
						scoped = True
					)
				)

				node = node.parent()

	def __nodeNameChanged( self, node ) :

		self.__path._emitPathChanged()
