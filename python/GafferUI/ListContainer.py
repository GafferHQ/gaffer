##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

import imath

import IECore
import GafferUI

from Qt import QtWidgets
from Qt import QtCore

## The ListContainer holds a series of Widgets either in a column or a row.
# It attempts to provide a list like interface for manipulation of the widgets.
class ListContainer( GafferUI.ContainerWidget ) :

	Orientation = enum.Enum( "Orientation", [ "Vertical", "Horizontal" ] )
	HorizontalAlignment = GafferUI.Enums.HorizontalAlignment
	VerticalAlignment = GafferUI.Enums.VerticalAlignment

	def __init__( self, orientation=Orientation.Vertical, spacing=0, borderWidth=0, **kw ) :

		GafferUI.ContainerWidget.__init__( self, QtWidgets.QWidget(), **kw )

		if orientation==self.Orientation.Vertical :
			self.__qtLayout = QtWidgets.QVBoxLayout()
		else :
			self.__qtLayout = QtWidgets.QHBoxLayout()

		self.__qtLayout.setSpacing( spacing )
		self.__qtLayout.setContentsMargins( borderWidth, borderWidth, borderWidth, borderWidth )
		self.__qtLayout.setSizeConstraint( QtWidgets.QLayout.SetMinAndMaxSize )

		self._qtWidget().setLayout( self.__qtLayout )

		self.__orientation = orientation
		self.__widgets = []

	def orientation( self ) :

		return self.__orientation

	def append( self, child, expand=False, horizontalAlignment=None, verticalAlignment=None ) :

		assert( isinstance( child, GafferUI.Widget ) )

		oldParent = child.parent()
		if oldParent is not None :
			oldParent.removeChild( child )

		self.__widgets.append( child )

		stretch = 1 if expand else 0
		self.__qtLayout.addWidget( child._qtWidget(), stretch, self.__convertToQtAlignment( horizontalAlignment, verticalAlignment ) )
		child._applyVisibility()

	def remove( self, child ) :

		self.removeChild( child )

	def insert( self, index, child, expand=False, horizontalAlignment=None, verticalAlignment=None ) :

		l = len( self.__widgets )
		if index > l :
			index = l

		oldParent = child.parent()
		if oldParent is not None :
			oldParent.removeChild( child )

		self.__widgets.insert( index, child )

		stretch = 1 if expand else 0
		self.__qtLayout.insertWidget( index, child._qtWidget(), stretch, self.__convertToQtAlignment( horizontalAlignment, verticalAlignment ) )
		child._applyVisibility()

	def index( self, child ) :

		return self.__widgets.index( child )

	def __setitem__( self, index, child ) :

		# Shortcut if there would be no change. Rearranging
		# things in Qt is extremely costly and this test is
		# trivial in comparison, so this is well worth doing.
		if self.__widgets[index] == child :
			return

		if isinstance( index, slice ) :
			assert( isinstance( child, list ) )
			children = child
			insertionIndex = index.start if index.start is not None else 0
		else :
			children = [ child ]
			insertionIndex = index

		expands = []
		for i in range( insertionIndex, insertionIndex + len( children ) ) :
			if i < len( self ) :
				expands.append( self.__qtLayout.stretch( i ) > 0 )
			else :
				expands.append( False )

		del self[index]

		# It's very important that we insert widgets in the order in which
		# they are to appear visually, because qt will define the tab-focus
		# chain order based on order of insertion, and not based on the order
		# of visual appearance. It's still possible to make several calls to
		# __setitem__ out of sequence and end up with bad focus orders, but
		# at least this way a slice set at one time will be in the correct order.
		#
		# Investigation into a method of achieving perfect ordering all the
		# time didn't yield anything better than this. One attempt called
		# setTabOrder() for every child, starting with the last child - this
		# worked when the children of the ListContainer where childless,
		# but not when they had children. Another possibility was to reimplement
		# QWidget.focusNextPrevChild() at the GafferUI.Window level, iterating
		# through the focus chain as for QApplicationPrivate::focusNextPrevChild_helper(),
		# but using knowledge of Container order to override the sequence where
		# necessary. This seemed like it might have promise, but is not straightforward.
		for i in range( 0, len( children ) ) :
			self.insert( insertionIndex + i, children[i], expands[i] )

	def __getitem__( self, index ) :

		return self.__widgets[index]

	def __delitem__( self, index ) :

		if isinstance( index, slice ) :
			indices = range( *(index.indices( len( self ) )) )
			for i in indices :
				self[i]._qtWidget().setParent( None )
				self[i]._applyVisibility()
			del self.__widgets[index]
		else :
			self.__widgets[index]._qtWidget().setParent( None )
			self.__widgets[index]._applyVisibility()
			del self.__widgets[index]

	def __len__( self ) :

		return len( self.__widgets )

	def __convertToQtAlignment( self, horizontalAlignment, verticalAlignment):

		if not horizontalAlignment and not verticalAlignment:
			return QtCore.Qt.Alignment( 0 )

		if verticalAlignment:
			qtVerticalAlignment = GafferUI.VerticalAlignment._toQt( verticalAlignment )
		else:
			qtVerticalAlignment = QtCore.Qt.Alignment( 0 )

		if horizontalAlignment:
			qtHorizontalAlignment = GafferUI.HorizontalAlignment._toQt( horizontalAlignment )
		else:
			qtHorizontalAlignment = QtCore.Qt.Alignment( 0 )

		return qtHorizontalAlignment | qtVerticalAlignment

	def addSpacer( self, width=0, height=0, expand=False, horizontalAlignment=None, verticalAlignment=None):

		self.append( GafferUI.Spacer( imath.V2i( width, height ) ), expand=expand, horizontalAlignment=horizontalAlignment, verticalAlignment=verticalAlignment )

	def addChild( self, child, expand=False, horizontalAlignment=None, verticalAlignment=None ) :

		self.append( child, expand=expand, horizontalAlignment=horizontalAlignment, verticalAlignment=verticalAlignment )

	def removeChild( self, child ) :

		self.__widgets.remove( child )
		child._qtWidget().setParent( None )
		child._applyVisibility()

	def setExpand( self, child, expand ) :

		self.__qtLayout.setStretchFactor( child._qtWidget(), 1 if expand else 0 )

	def getExpand( self, child ) :

		stretch = self.__qtLayout.stretch( self.index( child ) )
		return stretch > 0
