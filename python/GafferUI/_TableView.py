##########################################################################
#
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

from Qt import QtCore
from Qt import QtWidgets

# A QTableView derived class with custom size behaviours we want for
# GafferUI. This is not part of the public API.
#
# - Always requests enough space to show all cells if possible.
# - Optionally refuses to shrink below a certain number of visible rows.
class _TableView( QtWidgets.QTableView ) :

	def __init__( self, minimumVisibleRows = 0 ) :

		QtWidgets.QTableView.__init__( self )

		self.__minimumVisibleRows = minimumVisibleRows
		self.horizontalHeader().sectionResized.connect( self.__sizeShouldChange )

	def setModel( self, model ) :

		prevModel = self.model()
		if prevModel :
			prevModel.rowsInserted.disconnect( self.__sizeShouldChange )
			prevModel.rowsRemoved.disconnect( self.__sizeShouldChange )
			prevModel.columnsInserted.disconnect( self.__sizeShouldChange )
			prevModel.columnsRemoved.disconnect( self.__sizeShouldChange )
			prevModel.dataChanged.disconnect( self.__sizeShouldChange )
			prevModel.modelReset.disconnect( self.__sizeShouldChange )

		QtWidgets.QTableView.setModel( self, model )

		if model :
			model.rowsInserted.connect( self.__sizeShouldChange )
			model.rowsRemoved.connect( self.__sizeShouldChange )
			model.columnsInserted.connect( self.__sizeShouldChange )
			model.columnsRemoved.connect( self.__sizeShouldChange )
			model.dataChanged.connect( self.__sizeShouldChange )
			model.modelReset.connect( self.__sizeShouldChange )

	def setHorizontalHeader( self, header ) :

		if header == self.horizontalHeader() :
			return

		self.horizontalHeader().sectionResized.disconnect( self.__sizeShouldChange )
		QtWidgets.QTableView.setHorizontalHeader( self, header )
		self.horizontalHeader().sectionResized.connect( self.__sizeShouldChange )

	def minimumSizeHint( self ) :

		# compute the minimum height to be the size of the header plus
		# a minimum number of rows specified in self.__minimumVisibleRows

		margins = self.contentsMargins()
		minimumHeight = margins.top() + margins.bottom()

		if not self.horizontalHeader().isHidden() :
			minimumHeight += self.horizontalHeader().sizeHint().height()
		# allow room for a visible horizontal scrollbar to prevent it overlapping
		# the last row.
		if self.horizontalScrollBarPolicy() != QtCore.Qt.ScrollBarAlwaysOff and not self.horizontalScrollBar().isHidden() :
			minimumHeight += self.horizontalScrollBar().sizeHint().height()

		numRows = self.verticalHeader().count()
		if numRows :
			minimumHeight += self.verticalHeader().sectionSize( 0 ) * min( numRows, self.__minimumVisibleRows )

		# horizontal direction doesn't matter, as we don't allow shrinking
		# in that direction anyway.

		return QtCore.QSize( 1, minimumHeight )

	def sizeHint( self ) :

		# this seems to be necessary to nudge the header into calculating
		# the correct size - otherwise the length() below comes out wrong
		# sometimes. in other words it's a hack.
		for i in range( 0, self.horizontalHeader().count() ) :
			self.horizontalHeader().sectionSize( i )

		margins = self.contentsMargins()

		w = self.horizontalHeader().length() + margins.left() + margins.right()
		if not self.verticalHeader().isHidden() :
			w += self.verticalHeader().sizeHint().width()
		# always allow room for a scrollbar even though we don't always need one. we
		# make sure the background in the stylesheet is transparent so that when the
		# scrollbar is hidden we don't draw an empty gap where it otherwise would be.
		if self.horizontalScrollBarPolicy() != QtCore.Qt.ScrollBarAlwaysOff :
			w += self.verticalScrollBar().sizeHint().width()

		h = self.verticalHeader().length() + margins.top() + margins.bottom()
		if not self.horizontalHeader().isHidden() :
			h += self.horizontalHeader().sizeHint().height()
		# allow room for a visible horizontal scrollbar to prevent it overlapping
		# the last row.
		if self.horizontalScrollBarPolicy() != QtCore.Qt.ScrollBarAlwaysOff and not self.horizontalScrollBar().isHidden() :
			h += self.horizontalScrollBar().sizeHint().height()

		return QtCore.QSize( w, h )

	def __sizeShouldChange( self, *unusedArgs ) :

		self.updateGeometry()
