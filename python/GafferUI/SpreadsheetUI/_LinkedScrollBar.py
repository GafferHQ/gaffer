##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

from Qt import QtCore
from Qt import QtWidgets

# ScrolledContainer linking
# =========================
#
# To keep the row and column names and default cells visible at all times, we
# need to house them in separate table views from the main one. But we
# want to link the scrolling of them all, so they still act as a unit. We achieve
# this using the _LinkedScrollBar widget, which provides two-way coupling between
# the scrollbars of each container.

class _LinkedScrollBar( GafferUI.Widget ) :

	def __init__( self, orientation, scrolledContainers, **kw ) :

		GafferUI.Widget.__init__(
			self,
			_StepsChangedScrollBar(
				QtCore.Qt.Orientation.Horizontal if orientation == GafferUI.ListContainer.Orientation.Horizontal else QtCore.Qt.Orientation.Vertical
			),
			**kw
		)

		self.__scrollBars = [ self._qtWidget() ]
		for container in scrolledContainers :
			if orientation == GafferUI.ListContainer.Orientation.Horizontal :
				if not isinstance( container._qtWidget().horizontalScrollBar(), _StepsChangedScrollBar ) :
					container._qtWidget().setHorizontalScrollBar( _StepsChangedScrollBar( QtCore.Qt.Orientation.Horizontal ) )
				self.__scrollBars.append( container._qtWidget().horizontalScrollBar() )
			else :
				if not isinstance( container._qtWidget().verticalScrollBar(), _StepsChangedScrollBar ) :
					container._qtWidget().setVerticalScrollBar( _StepsChangedScrollBar( QtCore.Qt.Orientation.Vertical ) )
				self.__scrollBars.append( container._qtWidget().verticalScrollBar() )

		# Set size policy to `Ignored` in the direction of scrolling, so sizing is determined entirely
		# by the `scrolledContainers`. Otherwise, showing the scrollbar in `__rangeChanged` can lead to
		# another change of range, making an infinite loop where the scrollbar flickers on and off.
		if orientation == GafferUI.ListContainer.Orientation.Vertical :
			self._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Ignored )
		else :
			self._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed )

		self._qtWidget().setValue( self.__scrollBars[1].value() )
		self._qtWidget().setRange( self.__scrollBars[1].minimum(), self.__scrollBars[1].maximum() )
		self._qtWidget().setPageStep( self.__scrollBars[1].pageStep() )
		self._qtWidget().setSingleStep( self.__scrollBars[1].singleStep() )
		self.setVisible( self._qtWidget().minimum() != self._qtWidget().maximum() )

		for scrollBar in self.__scrollBars :
			scrollBar.valueChanged.connect( Gaffer.WeakMethod( self.__valueChanged ) )
			scrollBar.rangeChanged.connect( Gaffer.WeakMethod( self.__rangeChanged ) )
			scrollBar.stepsChanged.connect( Gaffer.WeakMethod( self.__stepsChanged ) )

		self.__isUpdating = False

	def __valueChanged( self, value ) :

		if self.__isUpdating :
			return

		try :
			self.__isUpdating = True
			for scrollBar in self.__scrollBars :
				scrollBar.setValue( value )
		finally :
			self.__isUpdating = False

	def __rangeChanged( self, min, max ) :

		if self.__isUpdating :
			return

		try :
			self.__isUpdating = True
			for scrollBar in self.__scrollBars :
				scrollBar.setRange( min, max )
			self.setVisible( min != max )
		finally :
			self.__isUpdating = False

	def __stepsChanged( self, page, single ) :

		if self.__isUpdating :
			return

		try :
			self.__isUpdating = True
			for scrollBar in self.__scrollBars :
				scrollBar.setPageStep( page )
				scrollBar.setSingleStep( single )
		finally :
			self.__isUpdating = False

# QScrollBar provides signals for when the value and range are changed,
# but not for when the page step is changed. This subclass adds the missing
# signal.
class _StepsChangedScrollBar( QtWidgets.QScrollBar ) :

	stepsChanged = QtCore.Signal( int, int )

	def __init__( self, orientation, parent = None ) :

		QtWidgets.QScrollBar.__init__( self, orientation, parent )

	def sliderChange( self, change ) :

		QtWidgets.QScrollBar.sliderChange( self, change )

		if change == QtWidgets.QAbstractSlider.SliderStepsChange :
			self.stepsChanged.emit( self.pageStep(), self.singleStep() )
