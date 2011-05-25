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

import IECore

import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

## \todo Support other list operations for child access
## \todo Can this share things with ListContainer?
class SplitContainer( GafferUI.ContainerWidget ) :
	
	Orientation = IECore.Enum.create( "Vertical", "Horizontal" )
	
	def __init__( self, orientation=Orientation.Vertical ) :
		
		GafferUI.ContainerWidget.__init__( self, QtGui.QSplitter() )
		
		self.__widgets = []
		
		self.setOrientation( orientation )
	
	def getOrientation( self ) :
	
		o = self._qtWidget().orientation()
		if o == QtCore.Qt.Horizontal :
			return self.Orientation.Horizontal
		else :
			return self.Orientation.Vertical
		
	def setOrientation( self, orientation ) :
	
		v = QtCore.Qt.Horizontal if orientation == self.Orientation.Horizontal else QtCore.Qt.Vertical
		self._qtWidget().setOrientation( QtCore.Qt.Orientation( v ) )
			
	def append( self, child ) :
			
		oldParent = child.parent()
		if oldParent is not None :
			oldParent.removeChild( child )
			
		self.__widgets.append( child )
		self._qtWidget().addWidget( child._qtWidget() )
	
	def remove( self, child ) :
		
		self.removeChild( child )
		
	def insert( self, index, child ) :
	
		assert( child not in self.__widgets )
		
		oldParent = child.parent()
		if oldParent :
			oldParent.removeChild( child )
			
		self._qtWidget().insertWidget( index,  child._qtWidget() )
		self.__widgets.insert( index, child )
	
	def index( self, child ) :
	
		return self.__widgets.index( child )
	
	def removeChild( self, child ) :
	
		assert( child in self.__widgets )
		child._qtWidget().setParent( None )
		self.__widgets.remove( child )
	
	def __getitem__( self, index ) :
	
		return self.__widgets[index]
	
	def __delitem__( self, index ) :
	
		if isinstance( index, slice ) :
			indices = range( *(index.indices( len( self ) )) )
			toRemove = []
			for i in indices :
				toRemove.append( self[i] )
			for c in toRemove :
				self.removeChild( c )			
		else :
			self.removeChild( self[index] )
	
	def __len__( self ) :
		
		return len( self.__widgets )
			
	
