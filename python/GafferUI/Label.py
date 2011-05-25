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

QtGui = GafferUI._qtImport( "QtGui" )

class Label( GafferUI.Widget ) :

	def __init__( self, text="", font={}, alignment=IECore.V2f( 0.5, 0.5 ) ) :
	
		GafferUI.Widget.__init__( self, QtGui.QLabel( text ) )

		## \todo ??
		#self.setFont( **font )
		#self.setAlignment( alignment )

	#def setAlignment( self, alignment ) :
#	
#		self.gtkWidget().set_alignment( alignment[0], alignment[1] )
#		
#	def getAlignment( self ) :
#	
#		return IECore.V2f( *self.gtkWidget().get_alignment() )
#
#	def setFont( self, **kw ) :
#	
#		text = self.gtkWidget().get_text()
#		font = self._pangoFont( **kw )
#		self.gtkWidget().set_markup( "<span %s>%s</span>" % ( font, text ) )
#		self.__font = font
#		
#	def getFont( self, **kw ) :
#	
#		return self.__font
