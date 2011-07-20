##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

QtGui = GafferUI._qtImport( "QtGui" )

class Button( GafferUI.Widget ) :

	__palette = None

	def __init__( self, text="", image=None ) :
	
		GafferUI.Widget.__init__( self, QtGui.QPushButton() )
		
		self.setText( text )
		self.setImage( image )
		
		# using a WeakMethod to avoid circular references which would otherwise
		# never be broken.		
		self._qtWidget().clicked.connect( Gaffer.WeakMethod( self.__clicked ) )
		
		self.__clickedSignal = GafferUI.WidgetSignal()
	
		# buttons appear to totally ignore the etch-disabled-text stylesheet option,
		# and we really don't like the etching. the only effective way of disabling it
		# seems to be to apply this palette which makes the etched text transparent.
		if Button.__palette is None :
			Button.__palette = QtGui.QPalette( QtGui.QApplication.instance().palette() )
			Button.__palette.setColor( QtGui.QPalette.Disabled, QtGui.QPalette.Light, QtGui.QColor( 0, 0, 0, 0 ) )

		self._qtWidget().setPalette( Button.__palette )

	def setText( self, text ) :
	
		assert( isinstance( text, basestring ) )
	
		self._qtWidget().setText( text )
		
	def getText( self ) :
	
		return self._qtWidget().text()
		
	def setImage( self, imageOrImageFileName ) :
	
		assert( isinstance( imageOrImageFileName, ( basestring, GafferUI.Image, type( None ) ) ) )
		
		if isinstance( imageOrImageFileName, basestring ) :
			self.__image = GafferUI.Image( imageOrImageFileName )
		else :
			self.__image = imageOrImageFileName
		
		if self.__image is not None :
		
			self._qtWidget().setIcon( QtGui.QIcon( self.__image._qtPixmap() ) )
			self._qtWidget().setIconSize( self.__image._qtPixmap().size() )
		
		else : 
		
			self._qtWidget().setIcon( QtGui.QIcon() )
	
	def getImage( self ) :
	
		return self.__image
		
	def clickedSignal( self ) :
	
		return self.__clickedSignal
		
	def __clicked( self, *unusedArgs ) : # currently PyQt passes a "checked" argument and PySide doesn't
				
		self.clickedSignal()( self )	
