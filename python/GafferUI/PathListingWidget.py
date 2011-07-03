##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

import time

import IECore

import Gaffer
import GafferUI

QtGui = GafferUI._qtImport( "QtGui" )

## \todo Make columns configurable.
class PathListingWidget( GafferUI.Widget ) :

	def __init__( self, path ) :
	
		GafferUI.Widget.__init__( self, _TreeView() )
		
		self.__itemModel = QtGui.QStandardItemModel()
		
		self._qtWidget().setAlternatingRowColors( True )
		self._qtWidget().setModel( self.__itemModel )
		self._qtWidget().setEditTriggers( QtGui.QTreeView.NoEditTriggers )
		self._qtWidget().activated.connect( Gaffer.WeakMethod( self.__activated ) )
		self._qtWidget().selectionModel().selectionChanged.connect( Gaffer.WeakMethod( self.__selectionChanged ) )
		self._qtWidget().header().setMovable( False )
		self._qtWidget().header().setResizeMode( QtGui.QHeaderView.ResizeToContents )
				
		self.__path = path
		self.__pathChangedConnection = self.__path.pathChangedSignal().connect( Gaffer.WeakMethod( self.__pathChanged ) )
				
		self.__currentDir = None
		self.__update()
	
		self.__pathSelectedSignal = GafferUI.WidgetSignal()
	
	## This signal is emitted when the user double clicks on a leaf path.
	def pathSelectedSignal( self ) :
	
		return self.__pathSelectedSignal
			
	def __update( self ) :
		
		# update the listing if necessary
				
		dirPath = self.__dirPath()
		if self.__currentDir!=dirPath :
						
			children = dirPath.children()
			self.__itemModel.clear()

			self.__itemModel.setHorizontalHeaderItem( 0, QtGui.QStandardItem( "Name" ) )
			self.__itemModel.setHorizontalHeaderItem( 1, QtGui.QStandardItem( "Owner" ) )
			self.__itemModel.setHorizontalHeaderItem( 2, QtGui.QStandardItem( "Modified" ) )

			for child in children :

				info = child.info() or {}

				row = []
				row.append( QtGui.QStandardItem( child[-1] ) )
				row.append( QtGui.QStandardItem( info.get( "fileSystem:owner", "" ) ) )

				mTime = info.get( "fileSystem:modificationTime", 0 )
				row.append( QtGui.QStandardItem( time.ctime( mTime ) ) )

				self.__itemModel.appendRow( row )

			self.__currentDir = dirPath
		
		# update the selection
			
		rowIndex = None
		with IECore.IgnoredExceptions( ValueError ) :
			rowIndex = dirPath.children().index( self.__path )
		
		sm = self._qtWidget().selectionModel()
		if rowIndex is not None :
			sm.select( self.__itemModel.index( rowIndex, 0 ), sm.Select | sm.Rows )
		else :
			sm.clear()
			
	def __dirPath( self ) :
	
		p = self.__path.copy()
		if p.isLeaf() :
			# if it's a leaf then take the parent
			del p[-1]
		else :
			# it's not a leaf.
			if not p.isValid() :
				# it's not valid. if we can make it
				# valid by trimming the last element
				# then do that
				pp = p.copy()
				del pp[-1]
				if pp.isValid() :
					p = pp
			else :
				# it's valid and not a leaf, and
				# that's what we want.
				pass
						
		return p

	def __activated( self, modelIndex ) :
				
		activatedPath = self.__appendedPath( modelIndex )
		self.__path[:] = activatedPath[:]
				
		if self.__path.isLeaf() :
			self.pathSelectedSignal()( self )
			
		return True
		
	def __selectionChanged( self, selected, deselected ) :
			
		selectedIndices = selected.indexes()
		if len( selectedIndices ) :
			selectedPath = self.__appendedPath( selectedIndices[0] )
			if selectedPath.isLeaf() :
				self.__path[:] = selectedPath[:]			
			
		return True
	
	def __appendedPath( self, modelIndexToAppend ) :
	
		path = self.__dirPath()
	
		name = self.__itemModel.data( self.__itemModel.index( modelIndexToAppend.row(), 0 ) )
		name = GafferUI._Variant.fromVariant( name )
		
		path.append( name )
		
		return path
		
	def __pathChanged( self, path ) :
		
		self.__update()

## Private implementation - a QTreeView with some specific size behaviour
class _TreeView( QtGui.QTreeView ) :

	def __init__( self ) :
	
		QtGui.QTreeView.__init__( self )
		
		self.header().geometriesChanged.connect( self.updateGeometry )
		
	def sizeHint( self ) :
	
		result = QtGui.QTreeView.sizeHint( self )
		
		margins = self.contentsMargins()
		result.setWidth( self.header().length() + margins.left() + margins.right() )

		result.setHeight( max( result.width() * .5, result.height() ) )
		
		return result
