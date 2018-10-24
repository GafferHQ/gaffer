##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
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
from Qt import QtGui
from Qt import QtWidgets

class ScrolledContainer( GafferUI.ContainerWidget ) :

	ScrollMode = GafferUI.Enums.ScrollMode

	def __init__( self, horizontalMode=GafferUI.ScrollMode.Automatic, verticalMode=GafferUI.ScrollMode.Automatic, borderWidth=0, **kw ) :

		GafferUI.ContainerWidget.__init__( self, _ScrollArea(), **kw )

		self._qtWidget().setViewportMargins( borderWidth, borderWidth, borderWidth, borderWidth )
		self._qtWidget().setWidgetResizable( True )

		self.setHorizontalMode( horizontalMode )
		self.setVerticalMode( verticalMode )

		self.__child = None

	def addChild( self, child ) :

		if self.getChild() is not None :
			raise Exception( "ScrolledContainer can only hold one child" )

		self.setChild( child )

	def removeChild( self, child ) :

		assert( child is self.__child )

		child._qtWidget().setParent( None )
		child._applyVisibility()
		self.__child = None

	def setChild( self, child ) :

		if self.__child :
			self.removeChild( self.__child )

		if child is not None :

			oldParent = child.parent()
			if oldParent is not None :
				oldParent.removeChild( child )

			self._qtWidget().setWidget( child._qtWidget() )
			child._applyVisibility()
			self.__child = child

	def getChild( self ) :

		return self.__child

	def setHorizontalMode( self, mode ) :

		self._qtWidget().setHorizontalScrollBarPolicy( GafferUI.ScrollMode._toQt( mode ) )

	def getHorizontalMode( self ) :

		p = self._qtWidget().horizontalScrollBarPolicy()
		return GafferUI.ScrollMode._fromQt( p[0] )

	def setVerticalMode( self, mode ) :

		self._qtWidget().setVerticalScrollBarPolicy( GafferUI.ScrollMode._toQt( mode ) )

	def getVerticalMode( self ) :

		p = self._qtWidget().verticalScrollBarPolicy()
		return GafferUI.ScrollMode._fromQt( p[1] )

	def _revealDescendant( self, descendant ) :

		self._qtWidget().ensureWidgetVisible( descendant._qtWidget() )

# Private implementation - a QScrollArea derived class which is a bit more
# forceful about claiming size - it always asks for enough to completely show
# the contained widget.
class _ScrollArea( QtWidgets.QScrollArea ) :

	def __init__( self ) :

		QtWidgets.QScrollArea.__init__( self )

		self.__marginLeft = 0
		self.__marginRight = 0
		self.__marginTop = 0
		self.__marginBottom = 0

	def setWidget( self, widget ) :

		QtWidgets.QScrollArea.setWidget( self, widget )
		widget.installEventFilter( self )

	def setViewportMargins( self, left, top, right, bottom ) :

		QtWidgets.QScrollArea.setViewportMargins( self, left, top, right, bottom )

		self.__marginLeft = left
		self.__marginRight = right
		self.__marginTop = top
		self.__marginBottom = bottom

	def sizeHint( self ) :

		w = self.widget()
		if not w :
			return QtWidgets.QScrollArea.sizeHint( self )

		wSize = w.sizeHint()

		width = self.__marginLeft + self.__marginRight + wSize.width()
		if self.verticalScrollBarPolicy()==QtCore.Qt.ScrollBarAlwaysOn :
			width += self.verticalScrollBar().sizeHint().width()

		height = self.__marginTop + self.__marginBottom + wSize.height()
		if self.horizontalScrollBarPolicy()==QtCore.Qt.ScrollBarAlwaysOn :
			height += self.horizontalScrollBar().sizeHint().height()

		return QtCore.QSize( width, height )

	def eventFilter( self, widget, event ) :

		if widget is self.widget() and isinstance( event, QtGui.QResizeEvent ) :
			# Ask for our geometry to be recalculated if possible. This allows
			# us to expand and contract with our child.
			self.updateGeometry()

			# I don't know why this is necessary. If it's removed then when the
			# child widget resizes and the ScrolledContainer is resized up to fit,
			# the scroll bar flickers on and off briefly. This can be seen in the
			# OpDialogue with any op with collapsible parameter sections. Ideally
			# we would find a better fix, or at least understand this one.
			while widget is not None :
				if widget.layout() is not None :
					widget.layout().invalidate()
				widget = widget.parent()


		return False
