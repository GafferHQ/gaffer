##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import Gaffer
import GafferUI

from Qt import QtWidgets
from Qt import QtCore

class Label( GafferUI.Widget ) :

	## \todo Remove these and just reference them directly
	HorizontalAlignment = GafferUI.HorizontalAlignment
	VerticalAlignment = GafferUI.VerticalAlignment

	def __init__( self, text="", horizontalAlignment=HorizontalAlignment.Left, verticalAlignment=VerticalAlignment.Center, textSelectable = False, **kw ) :

		GafferUI.Widget.__init__( self, QtWidgets.QLabel( text ), **kw )

		# by default the widget would accept both shrinking and growing, but we'd rather it just stubbornly stayed
		# the same size. it's particularly important that it doesn't accept growth vertically as then vertical ListContainers
		# don't shrink properly when a child is hidden or shrunk - instead the container would distribute the extra height
		# among all the labels.
		self._qtWidget().setSizePolicy( QtWidgets.QSizePolicy( QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed ) )

		self.setAlignment( horizontalAlignment, verticalAlignment )
		if textSelectable :
			self.setTextSelectable( True )

	def setText( self, text ) :

		self._qtWidget().setText( text )

	def getText( self ) :

		return str( self._qtWidget().text() )

	def setAlignment( self, horizontalAlignment, verticalAlignment ) :

		self._qtWidget().setAlignment(
			GafferUI.HorizontalAlignment._toQt( horizontalAlignment ) |
			GafferUI.VerticalAlignment._toQt( verticalAlignment )
		)

	def getAlignment( self ) :

		a = self._qtWidget().alignment()
		return (
			GafferUI.HorizontalAlignment._fromQt( a ),
			GafferUI.VerticalAlignment._fromQt( a ),
		)

	def setTextSelectable( self, selectable ) :

		flags = self._qtWidget().textInteractionFlags()
		flags &= ~QtCore.Qt.TextSelectableByMouse
		if selectable :
			flags |= QtCore.Qt.TextSelectableByMouse

		self._qtWidget().setTextInteractionFlags( flags )

	def getTextSelectable( self ) :

		return bool( self._qtWidget().textInteractionFlags() & QtCore.Qt.TextSelectableByMouse )

	def linkActivatedSignal( self ) :

		try :
			return self.__linkActivatedSignal
		except :
			self.__linkActivatedSignal = GafferUI.WidgetEventSignal()
			self._qtWidget().linkActivated.connect( Gaffer.WeakMethod( self.__linkActivated ) )

		return self.__linkActivatedSignal

	def __linkActivated( self, link ) :

		self.__linkActivatedSignal( self, str( link ) )
