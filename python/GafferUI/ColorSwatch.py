##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

from PySide import QtGui
from PySide import QtCore

import IECore

import Gaffer
import GafferUI

## \todo Worry about colourspace (including not doing the alpha compositing in the wrong space)
class ColorSwatch( GafferUI.Widget ) :

	def __init__( self, color=IECore.Color4f( 1 ) ) :
	
		GafferUI.Widget.__init__( self, QtGui.QWidget() )
	
		self.__color = color
		
		## \todo Should this be an option? Should it be an option for all Widgets?
		self._qtWidget().setMinimumSize( 12, 12 )
		self._qtWidget().paintEvent = Gaffer.WeakMethod( self.__paintEvent )

	def setColor( self, color ) :
	
		if color!=self.__color :
			self.__color = color
			self._qtWidget().update()
		
	def getColor( self ) :
	
		return self.__color

	def __paintEvent( self, event ) :
	
		painter = QtGui.QPainter( self._qtWidget() )
		rect = event.rect()
		
		# draw checkerboard background if necessary
		if self.__color.dimensions()==4 and self.__color.a < 1 :
			
			checkSize = 6
						
			min = IECore.V2i( rect.x() / checkSize, rect.y() / checkSize )
			max = IECore.V2i( (rect.x() + rect.width()) / checkSize, (rect.y() + rect.height()) / checkSize )
			
			checkColor = QtGui.QColor( 100, 100, 100 )
			
			for x in range( min.x, max.x ) :
				for y in range( min.y, max.y ) :
					if ( x + y ) % 2 :
						painter.fillRect( QtCore.QRectF( x * checkSize, y * checkSize, checkSize, checkSize ), checkColor )

		# draw colour
		
		qColor = self._qtColor( self.__color )
		if self.__color.dimensions()==4 :
			qColor.setAlphaF( self.__color.a )
		painter.fillRect( QtCore.QRectF( rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height() ), qColor )
		
		return True
