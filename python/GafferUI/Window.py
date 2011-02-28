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

from PySide import QtCore
from PySide import QtGui

import GafferUI

class Window( GafferUI.ContainerWidget ) :

	def __init__( self, title="GafferUI.Window", borderWidth=0, resizeable=True ) :
	
		GafferUI.ContainerWidget.__init__(
			self, QtGui.QWidget( None, QtCore.Qt.WindowFlags( QtCore.Qt.Window ) )
		)
		
		self.__child = None
		self.__qtLayout = QtGui.QGridLayout()
		self.__qtLayout.setContentsMargins( borderWidth, borderWidth, borderWidth, borderWidth )
		
		self._qtWidget().setLayout( self.__qtLayout )

		self._qtWidget().installEventFilter( _windowEventFilter )
		
		self.setTitle( title )
		
		self.setResizeable( resizeable )

		self.__closeSignal = GafferUI.WidgetSignal()
				
	def setTitle( self, title ) :
	
		self._qtWidget().setWindowTitle( title )
		
	def getTitle( self ) :
	
		return self._qtWidget().windowTitle()
	
	def removeChild( self, child ) :
	
		assert( child is self.__child )
		child._qtWidget().setParent( None )
		self.__child = None
		
	def setChild( self, child ) :
	
		oldChild = self.getChild()
		if oldChild is not None :
			self.removeChild( oldChild )
			
		if child is not None :
			
			oldParent = child.parent()
			if oldParent is not None :
				oldParent.removeChild( child )
							
			self.__child = child
			self.__qtLayout.addWidget( child._qtWidget(), 0, 0 )

	def getChild( self ) :
	
		return self.__child
	
	## Adding a child window causes the child to stay
	# on top of the parent at all times. This is useful for
	# preventing dialogues and the like from disappearing behind
	# the main window.
	# \todo
	def addChildWindow( self, childWindow ) :

		return
#	
#		assert( isinstance( childWindow, Window ) )
#		
#		childWindow.gtkWidget().set_transient_for( self.gtkWidget() )
		
	def setResizeable( self, resizeable ) :
	
		self.__qtLayout.setSizeConstraint( QtGui.QLayout.SetDefaultConstraint if resizeable else QtGui.QLayout.SetFixedSize );
		
	def getResizeable( self ) :
	
		return self.__qtLayout.sizeConstraint() == QtGui.QLayout.SetDefaultConstraint

	def closeSignal( self ) :
	
		return self.__closeSignal

class _WindowEventFilter( QtCore.QObject ) :

	def __init__( self ) :
	
		QtCore.QObject.__init__( self )
		
	def eventFilter( self, qObject, qEvent ) :
	
		if qEvent.type()==QtCore.QEvent.Close :
			widget = GafferUI.Widget._owner( qObject )
			return widget.closeSignal()( widget )

		return False

# this single instance is used by all window widgets
_windowEventFilter = _WindowEventFilter()
