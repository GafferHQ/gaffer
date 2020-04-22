##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import math

import IECore

import Gaffer
import GafferUI

from Qt import QtGui

## The NumericSlider extends the slider class to provide a mapping between the positions
# and a range defined by a minimum and maximum value.
class NumericSlider( GafferUI.Slider ) :

	## The type of value (int or float) determines the type of the slider.
	# The min and max arguments define the numeric values at the ends of the slider.
	# By default, values outside this range will be clamped, but hardMin and hardMax
	# may be specified to move the point at which the clamping happens outside of the
	# slider itself.
	def __init__( self, value=None, min=0, max=1, hardMin=None, hardMax=None, values=None, **kw ) :

		GafferUI.Slider.__init__( self, **kw )

		assert( ( value is None ) or ( values is None) )

		self.__min = min
		self.__max = max
		self.__hardMin = hardMin if hardMin is not None else self.__min
		self.__hardMax = hardMax if hardMax is not None else self.__max

		# It would be nice to not store the values, but always infer them from
		# the positions. This isn't possible though, as the range may be 0 length
		# and then we would lose the values.
		self.__values = []
		if values is not None :
			self.__setValuesInternal( values, self.PositionChangedReason.SetPositions )
		else :
			self.__setValuesInternal( [ 0 if value is None else value ], self.PositionChangedReason.SetPositions )

	## Convenience function to call setValues( [ value ] )
	def setValue( self, value ) :

		self.setValues( [ value ] )

	## Convenience function returning getValues()[0] if there
	# is only one value, and raising ValueError if not.
	def getValue( self ) :

		if len( self.__values ) != 1 :
			raise ValueError

		return self.__values[0]

	def setValues( self, values ) :

		self.__setValuesInternal( values, self.PositionChangedReason.SetPositions )

	def getValues( self ) :

		return self.__values

	def setRange( self, min, max, hardMin=None, hardMax=None ) :

		if hardMin is None :
			hardMin = min
		if hardMax is None :
			hardMax = max

		if min==self.__min and max==self.__max and hardMin==self.__hardMin and hardMax==self.__hardMax :
			return

		self.__min = min
		self.__max = max
		self.__hardMin = hardMin
		self.__hardMax = hardMax

		self.__setValuesInternal( self.__values, self.PositionChangedReason.Invalid ) # reclamps the values to the range if necessary
		# __setValuesInternal() won't trigger an update if the position is the same - if
		# the position is at one end of the range, and that end is the same as before.
		self._qtWidget().update()

	def getRange( self ) :

		return self.__min, self.__max, self.__hardMin, self.__hardMax

	def valueChangedSignal( self ) :

		try :
			return self.__valueChangedSignal
		except :
			self.__valueChangedSignal = Gaffer.Signal2()

		return self.__valueChangedSignal

	def _setPositionsInternal( self, positions, reason ) :

		# change it into a __setValuesInternal call so we can apply clamping etc.
		# __setValuesInternal will call Slider._setPositionsInternal for us.
		self.__setValuesInternal(
			[ self.__min + x * ( self.__max - self.__min ) for x in positions ],
			reason
		)

	def __setValuesInternal( self, values, reason ) :

		# clamp values
		values = [ max( self.__hardMin, min( self.__hardMax, x ) ) for x in values ]

		# convert them to positions
		range = self.__max - self.__min
		if range == 0 :
			positions = [ 0 ] * len( values )
		else :
			positions = [ float( x - self.__min ) / range for x in values ]

		# store values. we do this before storing positions so they'll
		# be in sync when the position change is signalled.
		dragBeginOrEnd = reason in ( self.PositionChangedReason.DragBegin, self.PositionChangedReason.DragEnd )
		valueChangedSignal = None
		if values != self.__values or dragBeginOrEnd :
			self.__values = values
			with IECore.IgnoredExceptions( AttributeError ) :
				valueChangedSignal = self.__valueChangedSignal

		# store positions.
		GafferUI.Slider._setPositionsInternal( self, positions, reason )

		# signal value change if necessary. we do this after storing
		# positions so that the positions are in sync.
		if valueChangedSignal is not None :
			valueChangedSignal( self, reason )

	def _drawBackground( self, painter ) :

		size = self.size()
		valueRange = self.__max - self.__min
		if valueRange == 0 :
			return

		idealSpacing = 10
		idealNumTicks = float( size.x ) / idealSpacing
		tickStep = valueRange / idealNumTicks

		logTickStep = math.log10( tickStep )
		flooredLogTickStep = math.floor( logTickStep )
		tickStep = math.pow( 10, flooredLogTickStep )
		blend = (logTickStep - flooredLogTickStep)

		tickValue = math.floor( self.__min / tickStep ) * tickStep
		i = 0
		while tickValue <= self.__max :
			x = size.x * ( tickValue - self.__min ) / valueRange
			if i % 100 == 0 :
				height0 = height1 = 0.75
				alpha0 = alpha1 = 1
			elif i % 50 == 0 :
				height0 = 0.75
				height1 = 0.5
				alpha0 = alpha1 = 1
			elif i % 10 == 0 :
				height0 = 0.75
				height1 = 0.25
				alpha0 = alpha1 = 1
			elif i % 5 == 0 :
				height0 = 0.5
				height1 = 0
				alpha0 = 1
				alpha1 = 0
			else :
				height0 = 0.25
				height1 = 0
				alpha0 = 1
				alpha1 = 0

			alpha = alpha0 + (alpha1 - alpha0) * blend
			height = height0 + (height1 - height0) * blend

			pen = QtGui.QPen()
			pen.setWidth( 0 )
			pen.setColor( QtGui.QColor( 0, 0, 0, alpha * 255 ) )
			painter.setPen( pen )

			painter.drawLine( x, size.y, x, size.y * ( 1 - height ) )
			tickValue += tickStep
			i += 1
