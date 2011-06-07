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

import IECore

import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )
	
class ScrolledContainer( GafferUI.ContainerWidget ) :

	ScrollMode = IECore.Enum.create( "Never", "Always", "Automatic" )

	def __init__( self, horizontalMode=ScrollMode.Automatic, verticalMode=ScrollMode.Automatic, borderWidth=0 ) :
	
		GafferUI.ContainerWidget.__init__( self, _ScrollArea() )
				
		self._qtWidget().setViewportMargins( borderWidth, borderWidth, borderWidth, borderWidth )
		self._qtWidget().setWidgetResizable( True )
		
		self.setHorizontalMode( horizontalMode )
		self.setVerticalMode( verticalMode )
						
		self.__child = None
		
	def removeChild( self, child ) :
	
		assert( child is self.__child )
		
		child.setParent( None )
		self.__child = None
		
	def setChild( self, child ) :
	
		if self.__child :
			self.removeChild( self.__child )
		
		self._qtWidget().setWidget( child._qtWidget() )
		self.__child = child
		
	def getChild( self ) :
	
		return self.__child
	
	__modesToPolicies = {
		ScrollMode.Never : QtCore.Qt.ScrollBarAlwaysOff,
		ScrollMode.Always : QtCore.Qt.ScrollBarAlwaysOn,
		ScrollMode.Automatic : QtCore.Qt.ScrollBarAsNeeded,
	}

	__policiesToModes = {
		QtCore.Qt.ScrollBarAlwaysOff : ScrollMode.Never,
		QtCore.Qt.ScrollBarAlwaysOn : ScrollMode.Always,
		QtCore.Qt.ScrollBarAsNeeded : ScrollMode.Automatic,
	}
		
	def setHorizontalMode( self, mode ) :
	
		self._qtWidget().setHorizontalScrollBarPolicy( self.__modesToPolicies[mode] )

	def getHorizontalMode( self ) :
	
		p = self._qtWidget().horizontalScrollBarPolicy()
		return self.__policiesToModes[p[0]]
		
	def setVerticalMode( self, mode ) :
	
		self._qtWidget().setVerticalScrollBarPolicy( self.__modesToPolicies[mode] )

	def getVerticalMode( self ) :
	
		p = self._qtWidget().verticalScrollBarPolicy()
		return self.__policiesToModes[p[1]]

# Private implementation - a QScrollArea derived class which is a bit more
# forceful aboout claiming size when the scrollbars are off in a particular 
# direction.
class _ScrollArea( QtGui.QScrollArea ) :

	def __init__( self ) :
	
		QtGui.QScrollArea.__init__( self )
	
		self.__marginLeft = 0
		self.__marginRight = 0
		self.__marginTop = 0
		self.__marginBottom = 0
	
	def setWidget( self, widget ) :
	
		QtGui.QScrollArea.setWidget( self, widget )
		widget.installEventFilter( self )
		
	def setViewportMargins( self, left, top, right, bottom ) :
	
		QtGui.QScrollArea.setViewportMargins( self, left, top, right, bottom )
		
		self.__marginLeft = left
		self.__marginRight = right
		self.__marginTop = top
		self.__marginBottom = bottom
				
	def sizeHint( self ) :
			
		result = QtGui.QScrollArea.sizeHint( self )
		
		w = self.widget()
		if w :
		
			wSize = w.sizeHint()
			if self.horizontalScrollBarPolicy()==QtCore.Qt.ScrollBarAlwaysOff :
				result.setWidth(
					self.__marginLeft +
					self.__marginRight +
					wSize.width() +
					self.verticalScrollBar().sizeHint().width()
				)

			if self.verticalScrollBarPolicy()==QtCore.Qt.ScrollBarAlwaysOff :
				result.setHeight(
					self.__marginTop +
					self.__marginBottom +
					wSize.height() +
					self.horizontalScrollBar().sizeHint().width()
				)
				
		return result
	
	def eventFilter( self, widget, event ) :
	
		if widget is self.widget() and isinstance( event, QtGui.QResizeEvent ) :
			self.updateGeometry()
		
		return False
