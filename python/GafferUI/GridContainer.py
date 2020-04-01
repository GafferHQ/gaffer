##########################################################################
#
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

import imath

import IECore

import GafferUI

from Qt import QtCore
from Qt import QtWidgets

## The GridContainer holds a series of Widgets in a grid format, and provides
# indexing using python's multidimensional array syntax to complement the list
# syntax used by ListContainer. Indexing starts from 0,0 at the top left of the
# container.
#
# g = GafferUI.GridContainer()
# g[0,0] = GafferUI.Button() # add a button at cell 0,0
# g[1:3, 0] = GafferUI.Button() # add a button spanning two cells in the x direction
# g[0:3, 1:3] = GafferUI.Button() # add a button spanning a 3x2 area below the other buttons
#
# g[2,2] # reference the button in the specified cell (even though it spans several others too)
#
# del[0,0] # delete the button in the top left corner.
# del[2,0:2] # delete all children intersecting the specified area (both the remaining buttons in this case).
class GridContainer( GafferUI.ContainerWidget ) :

	def __init__( self, spacing=0, borderWidth=0, **kw ) :

		GafferUI.ContainerWidget.__init__( self, QtWidgets.QWidget(), **kw )

		self.__qtLayout = _GridLayout( self._qtWidget() )
		self.__qtLayout.setSpacing( spacing )
		self.__qtLayout.setContentsMargins( borderWidth, borderWidth, borderWidth, borderWidth )
		self.__qtLayout.setSizeConstraint( QtWidgets.QLayout.SetMinAndMaxSize )

		self.__widgets = set()

		# although it shrinks in terms of appearance if outlying widgets are
		# removed, the QLayout doesn't report a smaller columnCount() or rowCount().
		# so we keep a track of the true dimensions (largest coordinate any widget
		# currently has) ourselves. this is so we can implement gridSize() to return
		# what we really want.
		self.__maxCoordinate = imath.V2i( -1 )

	def gridSize( self ) :

		if self.__maxCoordinate is None :
			self.__maxCoordinate = imath.V2i( -1 )
			for x in range( 0, self.__qtLayout.columnCount() ) :
				for y in range( 0, self.__qtLayout.rowCount() ) :
					if self.__qtLayout.itemAtPosition( y, x ) is not None :
						self.__maxCoordinate.x = max( self.__maxCoordinate.x, x )
						self.__maxCoordinate.y = max( self.__maxCoordinate.y, y )

		return self.__maxCoordinate + imath.V2i( 1 )

	def __setitem__( self, index, child ) :

		self.addChild( child, index )

	def __getitem__( self, index ) :

		assert( len( index ) == 2 )
		assert( isinstance( index[0], int ) )
		assert( isinstance( index[1], int ) )
		assert( index[0] >= 0 )
		assert( index[1] >= 0 )

		qLayoutItem = self.__qtLayout.itemAtPosition( index[1], index[0] )
		if qLayoutItem is None :
			return None

		return GafferUI.Widget._owner( qLayoutItem.widget() )

	def __delitem__( self, index ) :

		ranges = self.__indexToRanges( index )
		self.__removeRanges( ranges )

	def __indexToRanges( self, index ) :

		assert( len( index ) == 2 )

		assert( isinstance( index[0], ( int, slice ) ) )
		assert( isinstance( index[1], ( int, slice ) ) )
		if isinstance( index[0], slice ) :
			assert( index[0].start >= 0 )
			assert( index[0].stop >= 0 )
			assert( index[0].stop > index[0].start )
		if isinstance( index[1], slice ) :
			assert( index[1].start >= 0 )
			assert( index[1].stop >= 0 )
			assert( index[1].stop > index[1].start )

		if isinstance( index[0], slice ) :
			xRange = index[0].start, index[0].stop
		else :
			xRange = index[0], index[0] + 1

		if isinstance( index[1], slice ) :
			yRange = index[1].start, index[1].stop
		else :
			yRange = index[1], index[1] + 1

		return xRange, yRange

	def addChild( self, child, index=( 1, 1 ), alignment = ( GafferUI.HorizontalAlignment.None_, GafferUI.VerticalAlignment.None_ ) ) :

		ranges = self.__indexToRanges( index )
		self.__removeRanges( ranges )

		oldParent = child.parent()
		if oldParent is not None :
			oldParent.removeChild( child )

		self.__widgets.add( child )
		self.__qtLayout.addWidget(
			child._qtWidget(),
			ranges[1][0],
			ranges[0][0],
			ranges[1][1] - ranges[1][0],
			ranges[0][1] - ranges[0][0],
			GafferUI.HorizontalAlignment._toQt( alignment[0] ) |
			GafferUI.VerticalAlignment._toQt( alignment[1] )
		)
		child._applyVisibility()

		if self.__maxCoordinate is not None :
			self.__maxCoordinate.x = max( self.__maxCoordinate[0], ranges[0][1] - 1 )
			self.__maxCoordinate.y = max( self.__maxCoordinate[1], ranges[1][1] - 1 )

	def removeChild( self, child ) :

		assert( child in self.__widgets )

		self.__widgets.remove( child )
		child._qtWidget().setParent( None )
		child._applyVisibility()

		# force recomputation of gridSize()
		self.__maxCoordinate = None

	## Removes a whole row at the specified y coordinate.
	# Unlike the del operator, this doesn't leave holes,
	# and will shuffle the following rows up to fill the
	# gap, both physically in the layout and logically
	# in terms of the indices. If a multicell child intersects
	# the row being removed then it will be removed too,
	# even though it existed partly outside the row.
	def removeRow( self, rowIndex ) :

		self.__removeLine( 1, rowIndex )

	## Removes a whole column at the specified x coordinate.
	# Unlike the del operator, this doesn't leave holes,
	# and will shuffle the following columns left to fill the
	# gap, both physically in the layout and logically
	# in terms of the indices. If a multicell child intersects
	# the column being removed then it will be removed too,
	# even though it existed partly outside the column.
	def removeColumn( self, columnIndex ) :

		self.__removeLine( 0, columnIndex )

	def __removeLine( self, axis, index ) :

		size = self.gridSize()

		assert( index < size[axis] )

		# remove the line
		if axis == 0 :
			self.__removeRanges( ( ( index, index + 1 ), ( 0, size[1] ) ) )
		else :
			self.__removeRanges( ( ( 0, size[0] ), ( index, index + 1 ) ) )

		# shuffle everything into the hole
		otherAxis = 1 if axis == 0 else 0
		for u in range( index + 1, size[axis] ) :
			for v in range( 0, size[otherAxis] ) :
				c = [u,v] if axis == 0 else [v,u]
				w = self[c]
				if w is not None :
					c[axis] -= 1
					self[c] = w

	def __removeRanges( self, ranges ) :

		for x in range( *ranges[0] ) :
			for y in range( *ranges[1] ) :
				child = self[x,y]
				if child is not None :
					self.removeChild( child )

# Private implementation. A QGridLayout derived class which fixes problems
# whereby maximumSize() would come out less than sizeHint().
class _GridLayout( QtWidgets.QGridLayout ) :

	def __init__( self, parent ) :

		QtWidgets.QGridLayout.__init__( self, parent )

	def maximumSize( self ) :

		ms = QtWidgets.QGridLayout.maximumSize( self )
		sh = QtWidgets.QGridLayout.sizeHint( self )

		return QtCore.QSize( max( ms.width(), sh.width() ), max( ms.height(), sh.height() ) )
