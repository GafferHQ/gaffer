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
QtCore = GafferUI._qtImport( "QtCore" )

class Label( GafferUI.Widget ) :

	HorizontalAlignment = IECore.Enum.create( "Left", "Right", "Center" )
	VerticalAlignment = IECore.Enum.create( "Top", "Bottom", "Center" )
	
	def __init__( self, text="", horizontalAlignment=HorizontalAlignment.Left, verticalAlignment=VerticalAlignment.Center, **kw ) :
	
		GafferUI.Widget.__init__( self, QtGui.QLabel( text ), **kw )

		# by default the widget would accept both shrinking and growing, but we'd rather it just stubbornly stayed
		# the same size. it's particularly important that it doesn't accept growth vertically as then vertical ListContainers
		# don't shrink properly when a child is hidden or shrunk - instead the container would distribute the extra height
		# among all the labels.
		self._qtWidget().setSizePolicy( QtGui.QSizePolicy( QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed ) )

		self.setAlignment( horizontalAlignment, verticalAlignment )

	def setText( self, text ) :
	
		self._qtWidget().setText( text )

	def getText( self ) :
	
		return str( self._qtWidget().text() )
	
	def setAlignment( self, horizontalAlignment, verticalAlignment ) :
		
		self._qtWidget().setAlignment(
			QtCore.Qt.AlignRight | 
			QtCore.Qt.AlignTop
		)
				
	def getAlignment( self ) :
	
		a = self._qtWidget().alignment()
		return (
			self.__qtAlignmentToGaffer[int(a & QtCore.Qt.AlignHorizontal_Mask)],
			self.__qtAlignmentToGaffer[int(a & QtCore.Qt.AlignVertical_Mask)],
		)
		
	__qtAlignmentToGaffer = {
		int( QtCore.Qt.AlignLeft ) : HorizontalAlignment.Left,
		int( QtCore.Qt.AlignRight ) : HorizontalAlignment.Right,
		int( QtCore.Qt.AlignHCenter ) : HorizontalAlignment.Center,
		int( QtCore.Qt.AlignTop ) : VerticalAlignment.Top,
		int( QtCore.Qt.AlignBottom ) : VerticalAlignment.Bottom,
		int( QtCore.Qt.AlignVCenter ) : VerticalAlignment.Center,
	}
	
	__gafferAlignmentToQt = {
		HorizontalAlignment.Left : QtCore.Qt.AlignLeft,
		HorizontalAlignment.Right : QtCore.Qt.AlignRight,
		HorizontalAlignment.Center : QtCore.Qt.AlignHCenter,
		VerticalAlignment.Top : QtCore.Qt.AlignTop,
		VerticalAlignment.Bottom : QtCore.Qt.AlignBottom,
		VerticalAlignment.Center : QtCore.Qt.AlignVCenter,
	}
