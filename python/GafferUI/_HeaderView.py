##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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
from ._StyleSheet import _styleColors

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets
import Qt

# A QHeaderView derived class with custom behaviours we want for
# GafferUI. This is not part of the public API.
#
# - Adds `blockingSectionPressedSignal()`, which can block Qt's mousePressEvent, useful for preventing changes to sort order when clicking.
# - Improves visual feedback when interactively moving sections by highlighting the section divider where the dropped section would be inserted.
# - Supports changing header icons on mouse hover, via PathColumn's { "state:normal" : "normal.png", "state:highlighted" : "highlighted.png" } icon format.
class _HeaderView( QtWidgets.QHeaderView ) :

	def __init__( self, orientation = QtCore.Qt.Horizontal, parent = None ) :

		QtWidgets.QHeaderView.__init__( self, orientation, parent )

		self.setMouseTracking( True )
		if orientation == QtCore.Qt.Horizontal :
			self.setDefaultAlignment( QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter )

		self.__blockingSectionPressedSignal = None

		self.__highlightedSectionDivider = None
		self.__hoveredSection = None
		self.__pressedSection = None
		self.__firstMovableSection = 0

	def setHighlightedSectionDivider( self, index ) :

		self.__highlightedSectionDivider = index
		self.viewport().update()

	## \todo It may be better to make movability a property of each PathColumn
	# rather than set this on the HeaderView, though this would require an ABI break.
	def setFirstMovableSection( self, index ) :

		self.__firstMovableSection = index

	## A signal emitted whenever a section header is pressed. Slots can
	# return `True` to block the Qt mousePressEvent.
	def blockingSectionPressedSignal( self ) :

		def signalCombiner( slotResults ) :
			for result in slotResults :
				if result :
					return result

		if self.__blockingSectionPressedSignal is None :
			self.__blockingSectionPressedSignal = Gaffer.Signals.Signal1( signalCombiner )
		return self.__blockingSectionPressedSignal

	def mousePressEvent( self, event ) :

		if not self.__eventOverSectionResizeHandle( event ) :
			section = self.logicalIndexAt( event.position().toPoint() if Qt.__binding__ == "PySide6" else event.pos() )
			if self.__blockingSectionPressedSignal is not None :
				if self.blockingSectionPressedSignal()( section ) :
					# Slot has requested to block Qt's mousePressEvent.
					return

			if self.sectionsMovable() and event.button() == QtCore.Qt.MouseButton.LeftButton :
				self.__pressedSection = section

		QtWidgets.QHeaderView.mousePressEvent( self, event )

	def mouseReleaseEvent( self, event ) :

		if event.button() == QtCore.Qt.MouseButton.LeftButton and self.__pressedSection is not None :
			self.__pressedSection = None
			self.__highlightedSectionDivider = None
			self.viewport().update()

		QtWidgets.QHeaderView.mouseReleaseEvent( self, event )

	def mouseMoveEvent( self, event ) :

		updateRequired = False

		position = event.position().toPoint() if Qt.__binding__ == "PySide6" else event.pos()
		section = self.logicalIndexAt( position )

		if self.__pressedSection is not None :

			if self.__pressedSection < self.__firstMovableSection :
				return

			if position.x() >= self.sectionViewportPosition( section ) + self.sectionSize( section ) // 2 :
				section = self.__nextVisibleSection( section )

			if section is not None :
				section = max( self.__firstMovableSection, section )

			if section != self.__highlightedSectionDivider :
				self.__highlightedSectionDivider = section
				updateRequired = True

		elif self.__eventOverSectionResizeHandle( event ) :
			if self.__hoveredSection is not None :
				self.__hoveredSection = None
				updateRequired = True

		elif section != self.__hoveredSection :
			self.__hoveredSection = section
			updateRequired = True

		if updateRequired :
			self.viewport().update()

		QtWidgets.QHeaderView.mouseMoveEvent( self, event )

	def leaveEvent( self, event ) :

		update = False
		if self.__hoveredSection is not None :
			self.__hoveredSection = None
			update = True

		if self.__highlightedSectionDivider is not None :
			self.__highlightedSectionDivider = None
			update = True

		if update :
			self.viewport().update()

		QtWidgets.QHeaderView.leaveEvent( self, event )

	def initStyleOptionForIndex( self, option, logicalIndex ) :

		QtWidgets.QHeaderView.initStyleOptionForIndex( self, option, logicalIndex )

		if logicalIndex == self.__hoveredSection and isinstance( option.icon, QtGui.QIcon ) :
			iconSize = self.style().pixelMetric( QtWidgets.QStyle.PM_SmallIconSize )
			option.icon = option.icon.pixmap( QtCore.QSize( iconSize, iconSize ), QtGui.QIcon.Active )

	def paintEvent( self, event ) :

		QtWidgets.QHeaderView.paintEvent( self, event )

		if self.__highlightedSectionDivider is not None :
			painter = QtGui.QPainter( self.viewport() )
			pen = QtGui.QPen( QtGui.QColor( *(_styleColors["brightColor"]) ) )
			pen.setWidth( 2 )
			painter.setPen( pen )
			if self.__highlightedSectionDivider >= self.count() :
				x = self.length() - 1
			else :
				x = max( 1, self.sectionViewportPosition( self.__highlightedSectionDivider ) - 1 )
			painter.drawLine( x, 0, x, self.height() )

	def __eventOverSectionResizeHandle( self, event ) :

		position = event.position().toPoint() if Qt.__binding__ == "PySide6" else event.pos()
		section = self.logicalIndexAt( position )
		relativePosition = position.x() - self.sectionViewportPosition( section )
		handleMargin = self.style().pixelMetric( QtWidgets.QStyle.PM_HeaderGripMargin )

		if relativePosition < handleMargin or relativePosition > self.sectionSize( section ) - handleMargin :
			return True

		return False

	def __nextVisibleSection( self, logicalIndex ) :

		visualIndex = self.visualIndex( logicalIndex )
		if visualIndex < 0 :
			return None

		for v in range( visualIndex + 1, self.count() ) :
			l = self.logicalIndex( v )
			if not self.isSectionHidden( l ) :
				return l

		return self.count()
