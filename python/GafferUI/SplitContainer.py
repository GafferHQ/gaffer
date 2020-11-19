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

import IECore

import GafferUI

from Qt import QtCore
from Qt import QtWidgets

## \todo Support other list operations for child access
class SplitContainer( GafferUI.ContainerWidget ) :

	Orientation = IECore.Enum.create( "Vertical", "Horizontal" )

	def __init__( self, orientation=Orientation.Vertical, borderWidth=0, **kw ) :

		GafferUI.ContainerWidget.__init__( self, _Splitter(), **kw )

		self.__widgets = []
		self.__handleWidgets = {}

		self._qtWidget().setContentsMargins( borderWidth, borderWidth, borderWidth, borderWidth )

		self.setOrientation( orientation )

	def getOrientation( self ) :

		o = self._qtWidget().orientation()
		if o == QtCore.Qt.Horizontal :
			return self.Orientation.Horizontal
		else :
			return self.Orientation.Vertical

	def setOrientation( self, orientation ) :

		v = QtCore.Qt.Horizontal if orientation == self.Orientation.Horizontal else QtCore.Qt.Vertical
		self._qtWidget().setOrientation( QtCore.Qt.Orientation( v ) )

	def append( self, child ) :

		oldParent = child.parent()
		if oldParent is not None :
			oldParent.removeChild( child )

		self.__applySizePolicy( child )
		self.__widgets.append( child )
		self._qtWidget().addWidget( child._qtWidget() )
		child._applyVisibility()
		assert( child._qtWidget().parent() is self._qtWidget() )

		self.__updateStyles()

	def remove( self, child ) :

		self.removeChild( child )

	def insert( self, index, child ) :

		assert( child not in self.__widgets )

		oldParent = child.parent()
		if oldParent :
			oldParent.removeChild( child )

		self.__applySizePolicy( child )
		self.__widgets.insert( index, child )
		self._qtWidget().insertWidget( index,  child._qtWidget() )
		child._applyVisibility()
		assert( child._qtWidget().parent() is self._qtWidget() )

		self.__updateStyles()

	def index( self, child ) :

		return self.__widgets.index( child )

	def addChild( self, child ) :

		self.append( child )

	def removeChild( self, child ) :

		assert( child in self.__widgets )
		child._qtWidget().setSizePolicy( child.__originalSizePolicy )
		child._qtWidget().setParent( None )
		child._applyVisibility()
		self.__widgets.remove( child )

	## Returns a list of actual pixel sizes for each of the children.
	# These do not include the space taken up by the handles.
	def getSizes( self ) :

		return self._qtWidget().sizes()

	## Sets the sizes of the children. Note that this will not change
	# the overall size of the SplitContainer - instead the sizes are
	# adjusted to take up all the space available. Therefore it is only
	# the relative differences in sizes which are important.
	def setSizes( self, sizes ) :

		assert( len( sizes ) == len( self ) )

		if self.getOrientation() == self.Orientation.Vertical :
			availableSize = self.size().y
		else :
			availableSize = self.size().x

		if len( self ) > 1 :
			availableSize -= (len( self ) - 1) * self._qtWidget().handleWidth()

		scaleFactor = availableSize / sum( sizes )
		sizes = [ scaleFactor * x for x in sizes ]

		self._qtWidget().setSizes( sizes )

	## Returns the handle to the right/bottom of the specified child index.
	# Note that you should not attempt to reparent the handles, and you will
	# be unable to access them after the SplitContainer itself has been destroyed.
	def handle( self, index ) :

		if index < 0 or index >= len( self ) - 1 :
			raise IndexError()

		qtHandle = self._qtWidget().handle( index + 1 )
		assert( qtHandle.parent() is self._qtWidget() )
		handle = self.__handleWidgets.get( qtHandle, None )
		if handle is None :
			handle = GafferUI.Widget( qtHandle )
			self.__handleWidgets[qtHandle] = handle

		return handle

	def __getitem__( self, index ) :

		return self.__widgets[index]

	def __delitem__( self, index ) :

		if isinstance( index, slice ) :
			indices = range( *(index.indices( len( self ) )) )
			toRemove = []
			for i in indices :
				toRemove.append( self[i] )
			for c in toRemove :
				self.removeChild( c )
		else :
			self.removeChild( self[index] )

	def __len__( self ) :

		return len( self.__widgets )

	def __applySizePolicy( self, widget ) :

		# this size policy allows the children to be cropped to any size - otherwise some stubbornly
		# stay at a minimum size and then suddenly collapse to nothing when moving the splitter all
		# the way. we store the original size policy on the widget and reapply it in removeChild().
		widget.__originalSizePolicy = widget._qtWidget().sizePolicy()
		widget._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored )

	def __updateStyles( self ) :

		# Had issues using ints
		self._qtWidget().setProperty( "gafferNumChildren", GafferUI._Variant.toVariant( "%d" % len(self) ) )
		self._repolish()

# We inherit from QSplitter purely so that the handles can be created
# in Python rather than C++. This seems to help PyQt and PySide in tracking
# the lifetimes of the splitter and handles.
class _Splitter( QtWidgets.QSplitter ) :

	def __init__( self ) :

		QtWidgets.QSplitter.__init__( self )

		# There seems to be an odd interaction between this and the stylesheet, and
		# setting this to the desired size and then using the stylesheet to divide it into
		# margins seems the only reliable way of sizing the handle.
		## \todo This should come from the style once we've unified the Gadget and Widget
		# styling.
		self.setHandleWidth( 6 )

	def createHandle( self ) :

		return QtWidgets.QSplitterHandle( self.orientation(), self )
