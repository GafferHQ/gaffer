##########################################################################
#
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI
import GafferCortexUI

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

class DateTimeParameterValueWidget( GafferCortexUI.ParameterValueWidget ) :

	def __init__( self, parameterHandler, **kw ) :

		GafferCortexUI.ParameterValueWidget.__init__( self, _DateTimePlugValueWidget( parameterHandler.plug() ), parameterHandler, **kw )

GafferCortexUI.ParameterValueWidget.registerType( IECore.DateTimeParameter, DateTimeParameterValueWidget )

class _DateTimePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		GafferUI.PlugValueWidget.__init__( self, QtWidgets.QDateTimeEdit(), plug, **kw )

		self._qtWidget().setCalendarPopup( True )
		self._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed )
		self._qtWidget().calendarWidget().setGridVisible( True )

		headerFormat = QtGui.QTextCharFormat()
		headerFormat.setFontWeight( 100 )
		self._qtWidget().calendarWidget().setHeaderTextFormat( headerFormat )

		# remove weekday text format overrides so the stylesheet gets to do what it wants
		self._qtWidget().calendarWidget().setWeekdayTextFormat( QtCore.Qt.Saturday, QtGui.QTextCharFormat() )
		self._qtWidget().calendarWidget().setWeekdayTextFormat( QtCore.Qt.Sunday, QtGui.QTextCharFormat() )

		self._qtWidget().dateTimeChanged.connect( Gaffer.WeakMethod( self.__dateTimeChanged ) )

		self._addPopupMenu()

		self._updateFromPlug()

	def _updateFromPlug( self ) :

		# convert from the undelimited form boost likes (and the DateTimeParameterHandler uses)
		# to the delimited form qt likes
		undelimited = self.getPlug().getValue()
		delimited = "%s-%s-%sT%s:%s:%s" % (
			undelimited[0:4],
			undelimited[4:6],
			undelimited[6:8],
			undelimited[9:11],
			undelimited[11:13],
			undelimited[13:15],
		)

		qDateTime = QtCore.QDateTime.fromString( delimited, QtCore.Qt.ISODate )
		self._qtWidget().blockSignals( True )
		self._qtWidget().setDateTime( qDateTime )
		self._qtWidget().blockSignals( False )

		self._qtWidget().setReadOnly( not self._editable() )

	def __dateTimeChanged( self, qDateTime ) :

		delimited = str( qDateTime.toString( QtCore.Qt.ISODate ) )
		undelimited = "%s%s%sT%s%s%s" % (
			delimited[0:4],
			delimited[5:7],
			delimited[8:10],
			delimited[11:13],
			delimited[14:16],
			delimited[17:19],
		)

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().setValue( undelimited )
