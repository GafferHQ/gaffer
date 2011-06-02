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

import os

import IECore

import GafferUI

QtGui = GafferUI._qtImport( "QtGui" )

## The Collapsible container provides an easy means of controlling the
# visibility of a child Widget. A labelled heading is always visible
# and clicking on it reveals or hides the child below.
class Collapsible( GafferUI.ContainerWidget ) :

	def __init__( self, label="", child=None, collapsed=False ) :
	
		GafferUI.ContainerWidget.__init__( self, QtGui.QWidget() )
		
		layout = _VBoxLayout()
		self._qtWidget().setLayout( layout )
		layout.setSizeConstraint( QtGui.QLayout.SetMinAndMaxSize )
		
		self.__toggle = QtGui.QRadioButton()
		self.__toggle.setObjectName( "gafferCollapsibleToggle" )
		layout.addWidget( self.__toggle )
		
		self.__stateChangedSignal = GafferUI.WidgetSignal()
		self.__toggle.toggled.connect( self.__toggled )
		
		self.__child = None
		self.setChild( child )
		
		self.setLabel( label )
		self.setCollapsed( collapsed )
		
	def removeChild( self, child ) :
	
		assert( child is self.__child )
		
		child._qtWidget().setParent( None )
		self.__child = None
		
	def setChild( self, child ) :
	
		if self.__child is not None :
			self.removeChild( self.__child )
		
		if child is not None :
			self._qtWidget().layout().addWidget( child._qtWidget() )
			child.setVisible( not self.getCollapsed() )
			self.__child = child

	def getChild( self ) :
	
		return self.__child
	
	def setLabel( self, label ) :
				
		self.__toggle.setText( label )
		
	def getLabel( self ) :
	
		return self.__toggle.text()
	
	def setCollapsed( self, state ) :
		
		self.__toggle.setChecked( state )
				
	def getCollapsed( self ) :
	
		return self.__toggle.isChecked()
	
	## A signal emitted whenever the ui is collapsed or
	# expanded.
	def stateChangedSignal( self ) :
	
		return self.__stateChangedSignal
		
	def __toggled( self, value ) :
		
		if self.__child is not None :
			self.__child.setVisible( not value )
			
		self.stateChangedSignal()( self )

class _VBoxLayout( QtGui.QVBoxLayout ) :

	def __init__( self ) :
	
		QtGui.QVBoxLayout.__init__( self )
		
	## Reimplemented so that requested width takes account of the
	# width of child items even if they are currently hidden. That
	# way the width doesn't change when the child is shown.
	def sizeHint( self ) :
		
		s = QtGui.QVBoxLayout.sizeHint( self )
		
		maxWidth = 0
		for i in range( 0, self.count() ) :
			maxWidth = max( maxWidth, self.itemAt( i ).widget().sizeHint().width() )
		
		margins = self.contentsMargins()
			
		s.setWidth( maxWidth + margins.left() + margins.right() )
		return s
