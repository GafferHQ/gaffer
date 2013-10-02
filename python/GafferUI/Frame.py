##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

import IECore

import GafferUI

QtGui = GafferUI._qtImport( "QtGui" )

class Frame( GafferUI.ContainerWidget ) :

	## \todo Raised and Inset?
	BorderStyle = IECore.Enum.create( "None", "Flat" )

	def __init__( self, child=None, borderWidth=8, borderStyle=BorderStyle.Flat, **kw ) :
	
		GafferUI.ContainerWidget.__init__( self, QtGui.QFrame(), **kw )
		
		self._qtWidget().setLayout( QtGui.QGridLayout() )
		self._qtWidget().layout().setContentsMargins( borderWidth, borderWidth, borderWidth, borderWidth )
		self._qtWidget().layout().setSizeConstraint( QtGui.QLayout.SetMinAndMaxSize )
		
		self.__child = None
		self.setChild( child )
		
		self.setBorderStyle( borderStyle )
	
	def setBorderStyle( self, borderStyle ) :
		
		self._qtWidget().setObjectName( "borderStyle" + str( borderStyle ) )
	
	def getBorderStyle( self ) :
	
		n = IECore.CamelCase.split( str( self._qtWidget().objectName() ) )[-1]
		return getattr( self.BorderStyle, n )
		
	def removeChild( self, child ) :
	
		assert( child is self.__child )
		
		child._qtWidget().setParent( None )
		child._applyVisibility()
		self.__child = None

	def addChild( self, child ) :
	
		if self.getChild() is not None :
			raise Exception( "Frame can only hold one child" )
			
		self.setChild( child )
		
	def setChild( self, child ) :
	
		if self.__child is not None :
			self.removeChild( self.__child )
		
		if child is not None :
			
			oldParent = child.parent()
			if oldParent is not None :
				oldParent.removeChild( child )
			
			self._qtWidget().layout().addWidget( child._qtWidget(), 0, 0 )
			child._applyVisibility()
					
		self.__child = child	

	def getChild( self ) :
	
		return self.__child
