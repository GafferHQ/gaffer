##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

from __future__ import with_statement

import operator
import time

import IECore

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

class PathListingWidget( GafferUI.Widget ) :

	## This simple class defines the content of a column.
	class Column( object ) :
	
		__slots__ = ( "infoField", "label", "displayFunction", "lessThanFunction" )
		
		def __init__( self, infoField, label, displayFunction=str, lessThanFunction=operator.lt ) :
		
			self.infoField = infoField
			self.label = label
			self.displayFunction = displayFunction
			self.lessThanFunction = lessThanFunction
	
	## A sensible set of columns to display for FileSystemPaths
	defaultFileSystemColumns = (
		Column( infoField = "name", label = "Name" ),
		Column( infoField = "fileSystem:owner", label = "Owner" ),
		Column( infoField = "fileSystem:modificationTime", label = "Modified", displayFunction = time.ctime ),
	)

	def __init__( self, path, columns = defaultFileSystemColumns, allowMultipleSelection=False ) :
	
		GafferUI.Widget.__init__( self, _TreeView() )
		
		self.__itemModel = QtGui.QStandardItemModel()
		
		self._qtWidget().setAlternatingRowColors( True )
		self._qtWidget().setModel( self.__itemModel )
		self._qtWidget().setEditTriggers( QtGui.QTreeView.NoEditTriggers )
		self._qtWidget().activated.connect( Gaffer.WeakMethod( self.__activated ) )
		self._qtWidget().selectionModel().selectionChanged.connect( Gaffer.WeakMethod( self.__selectionChanged ) )
		self._qtWidget().header().setMovable( False )
		self._qtWidget().header().setResizeMode( QtGui.QHeaderView.ResizeToContents )
		
		if allowMultipleSelection :
			self._qtWidget().setSelectionMode( QtGui.QAbstractItemView.ExtendedSelection )			
				
		self.__path = path
		self.__pathChangedConnection = self.__path.pathChangedSignal().connect( Gaffer.WeakMethod( self.__pathChanged ) )
				
		self.__currentDir = None
		self.__currentPath = ""
		self.__columns = columns
		self.__pathsToItems = {}
		self.__update()
		
		self._qtWidget().header().setSortIndicator( 0, QtCore.Qt.AscendingOrder )
	
		self.__pathSelectedSignal = GafferUI.WidgetSignal()
	
	## Returns a list of all currently selected paths.
	def selectedPaths( self ) :
	
		result = []
		selectedRows = self._qtWidget().selectionModel().selectedRows()
				
		for k, v in self.__pathsToItems.items() :
			if v.index() in selectedRows :
				p = self.__path.copy()
				p.setFromString( k )
				result.append( p )
				
		return result
	
	## This signal is emitted when the user double clicks on a leaf path.
	def pathSelectedSignal( self ) :
	
		return self.__pathSelectedSignal
			
	def __update( self ) :
				
		# update the listing if necessary. when the path itself changes, we only
		# want to update if the directory being viewed has changed. if the path
		# hasn't changed at all then we assume that the filter has changed and
		# we therefore have to update the listing anyway.
		# \todo Add an argument to Path.pathChangedSignal() to specify whether it
		# is the path or the filtering that has changed, and remove self.__currentPath
				
		dirPath = self.__dirPath()
		if self.__currentDir!=dirPath or str( self.__path )==self.__currentPath :
						
			children = dirPath.children()
			self.__pathsToItems.clear()
			self.__itemModel.clear()

			# qt manual suggests its best to edit the model with sorting disabled
			# for performance reasons.
			self._qtWidget().setSortingEnabled( False )
			sortingColumn = self._qtWidget().header().sortIndicatorSection()
			sortingOrder = self._qtWidget().header().sortIndicatorOrder()
			
			for index, column in enumerate( self.__columns ) :
				self.__itemModel.setHorizontalHeaderItem( index, QtGui.QStandardItem( column.label ) )

			for child in children :

				info = child.info() or {}

				row = []
				for column in self.__columns :
					value = info.get( column.infoField, None )
					row.append( _Item( value, column.displayFunction, column.lessThanFunction ) )
				
				self.__itemModel.appendRow( row )
				
				self.__pathsToItems[str(child)] = row[0]

			self._qtWidget().setSortingEnabled( True )
			self._qtWidget().header().setSortIndicator( sortingColumn, sortingOrder )

			self.__currentDir = dirPath
		
		self.__currentPath = str( self.__path )
				
		# update the selection
			
		sm = self._qtWidget().selectionModel()
		itemToSelect = self.__pathsToItems.get( str(self.__path), None )
		if itemToSelect is not None :
			sm.select( itemToSelect.index(), sm.ClearAndSelect | sm.Rows )
			self._qtWidget().scrollTo( itemToSelect.index(), self._qtWidget().EnsureVisible )
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
					
		currentlySelectedRows = self._qtWidget().selectionModel().selectedRows( 0 )
		if len( currentlySelectedRows )==1 and self.__appendedPath( currentlySelectedRows[0] ).isLeaf() :
			# we only have a single selected item, and it's a leaf. update the path
			# to reflect this selection.
			self.__path[:] = self.__appendedPath( currentlySelectedRows[0] )[:]
		else :
			# either we have a multiple selection, a single selection of a non-leaf node
			# or no selection at all. set the path back to be the current directory only,
			# and do this without calling __update() so the current selection isn't
			# destroyed.
			with Gaffer.BlockedConnection( self.__pathChangedConnection ) :
				self.__path[:] = self.__dirPath()[:]	
			
		return True
	
	def __appendedPath( self, modelIndexToAppend ) :
	
		path = self.__dirPath()
	
		name = self.__itemModel.data( self.__itemModel.index( modelIndexToAppend.row(), 0 ) )
		name = GafferUI._Variant.fromVariant( name )
		
		path.append( name )
		
		return path
		
	def __pathChanged( self, path ) :
		
		self.__update()

# Private implementation - a QTreeView with some specific size behaviour
class _TreeView( QtGui.QTreeView ) :

	def __init__( self ) :
	
		QtGui.QTreeView.__init__( self )
		
		self.setHorizontalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
		self.header().geometriesChanged.connect( self.updateGeometry )
		
	def sizeHint( self ) :
	
		result = QtGui.QTreeView.sizeHint( self )
		
		margins = self.contentsMargins()
		result.setWidth( self.header().length() + margins.left() + margins.right() )

		result.setHeight( max( result.width() * .5, result.height() ) )
		
		return result

# Private implementation - the items being displayed
class _Item( QtGui.QStandardItem ) :

	def __init__( self, value, displayFunction, lessThanFunction ) :
	
		QtGui.QStandardItem.__init__( self, displayFunction( value ) )
		
		self.__value = value
		self.__lessThanFunction = lessThanFunction
		
	def __lt__( self, other ) :
		
		return self.__lessThanFunction( self.__value, other.__value )
