##########################################################################
#  
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

import IECore

import GafferUI

QtGui = GafferUI._qtImport( "QtGui" )

## The GridContainer holds a series of Widgets in a grid format. Widgets
# may span more than one grid cell.
class GridContainer( GafferUI.ContainerWidget ) :

	def __init__( self, spacing=0, borderWidth=0 ) :
	
		GafferUI.ContainerWidget.__init__( self, QtGui.QWidget() )
	
		self.__qtLayout = QtGui.QGridLayout( self._qtWidget() )
		self.__qtLayout.setSpacing( spacing )
		self.__qtLayout.setContentsMargins( borderWidth, borderWidth, borderWidth, borderWidth )
		self.__qtLayout.setSizeConstraint( QtGui.QLayout.SetMinAndMaxSize )
		
		self.__widgets = set()
		
		# although it shrinks in terms of appearance if outlying widgets are
		# removed, the QLayout doesn't report a smaller columnCount() or rowCount().
		# so we keep a track of the true dimensions (largest coordinate any widget
		# currently has) ourselves. this is so we can implement gridSize() to return
		# what we really want.
		self.__maxCoordinate = IECore.V2i( -1 )
	
	def gridSize( self ) :
	
		if self.__maxCoordinate is None :
			self.__maxCoordinate = IECore.V2i( -1 )
			for x in range( 0, self.__qtLayout.columnCount() ) :
				for y in range( 0, self.__qtLayout.rowCount() ) :
					if self.__qtLayout.itemAtPosition( y, x ) is not None :
						self.__maxCoordinate.x = max( self.__maxCoordinate.x, x )
						self.__maxCoordinate.y = max( self.__maxCoordinate.y, y )
						
		return self.__maxCoordinate + IECore.V2i( 1 )
	
	def __setitem__( self, index, child ) :
	
		self.__validateIndex( index )
	
		oldParent = child.parent()
		if oldParent is not None :
			oldParent.removeChild( child )
					
		self.__widgets.add( child )
		self.__qtLayout.addWidget( child._qtWidget(), index[1], index[0] )
		
		if self.__maxCoordinate is not None :
			self.__maxCoordinate.x = max( self.__maxCoordinate[0], index[0] )
			self.__maxCoordinate.y = max( self.__maxCoordinate[1], index[1] )
			
	def __getitem__( self, index ) :
	
		self.__validateIndex( index )
	
		qLayoutItem = self.__qtLayout.itemAtPosition( index[1], index[0] )
		if qLayoutItem is None :
			return None
			
		return GafferUI.Widget._owner( qLayoutItem.widget() )
	
	def __delitem__( self, index ) :
	
		self.__validateIndex( index )
				
		child = self.__getitem__( index )
		if child is not None :
			self.removeChild( child )
		
	def __validateIndex( self, index ) :
	
		assert( len( index ) == 2 )
		assert( isinstance( index[0], int ) )
		assert( isinstance( index[1], int ) )
		
	def removeChild( self, child ) :

		assert( child in self.__widgets )
	
		self.__widgets.remove( child )
		child._qtWidget().setParent( None )

		# force recomputation of gridSize()
		self.__maxCoordinate = None

	## Removes a whole row at the specified y coordinate.
	# Unlike the del operator, this doesn't leave holes,
	# and will shuffle the following rows up to fill the
	# gap, both physically in the layout and logically
	# in terms of the indices.
	def removeRow( self, rowIndex ) :
	
		self.__removeLine( 1, rowIndex )
		
	## Removes a whole column at the specified x coordinate.
	# Unlike the del operator, this doesn't leave holes,
	# and will shuffle the following columns left to fill the
	# gap, both physically in the layout and logically
	# in terms of the indices.
	def removeColumn( self, columnIndex ) :
	
		self.__removeLine( 0, columnIndex )	
	
	def __removeLine( self, axis, index ) :
	
		size = self.gridSize()
		
		assert( index < size[axis] )
		
		otherAxis = 1 if axis == 0 else 0
				
		# remove the line
		for v in range( 0, size[otherAxis] ) :
			c = [index,v] if axis == 0 else [v,index]
			del self[c]
			
		# shuffle everything into the hole
		for u in range( index + 1, size[axis] ) :
			for v in range( 0, size[otherAxis] ) :
				c = [u,v] if axis == 0 else [v,u]
				w = self[c]
				if w is not None :
					c[axis] -= 1
					self[c] = w
					
		self.__maxCoordinate = size - IECore.V2i( 1 )
		self.__maxCoordinate[axis] = self.__maxCoordinate[axis] - 1
