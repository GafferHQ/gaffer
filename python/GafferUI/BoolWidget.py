##########################################################################
#  
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

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

class BoolWidget( GafferUI.Widget ) :

	DisplayMode = IECore.Enum.create( "CheckBox", "Switch" )

	def __init__( self, text="", checked=False, displayMode=DisplayMode.CheckBox, **kw ) :
	
		GafferUI.Widget.__init__( self, QtGui.QCheckBox( text ), **kw )
		
		self.setState( checked )
		
		self.__stateChangedSignal = GafferUI.WidgetSignal()
		
		self._qtWidget().stateChanged.connect( Gaffer.WeakMethod( self.__stateChanged ) )
	
		if displayMode == self.DisplayMode.Switch :
			self._qtWidget().setObjectName( "gafferBoolWidgetSwitch" )
	
	def setText( self, text ) :
	
		self._qtWidget().setText( text )
	
	def getText( self ) :
	
		return str( self._qtWidget().text() )
	
	def setState( self, checked ) :
	
		self._qtWidget().setCheckState( QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked )
		
	def getState( self ) :
	
		return self._qtWidget().checkState() == QtCore.Qt.Checked

	def stateChangedSignal( self ) :
	
		return self.__stateChangedSignal
	
	def __stateChanged( self, state ) :
	
		self.__stateChangedSignal( self )

## \todo Backwards compatibility - remove for version 1.0
CheckBox = BoolWidget
