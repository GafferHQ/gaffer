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

import GafferUI
from PlugValueWidget import PlugValueWidget
import CamelCase

## \todo Make tooltips work
## \todo Useful popup menu on label - connect, disconnect, expressions etc
## Or does that belong on the PlugValueWidget?
class PlugWidget( GafferUI.Widget ) :

	def __init__( self, plugOrPlugValueWidget, label=None, description=None ) :
	
		GafferUI.Widget.__init__( self, QtGui.QWidget() )

		layout = QtGui.QHBoxLayout()
		layout.setContentsMargins( 0, 0, 0, 0 )
		layout.setSpacing( 4 )
		self._qtWidget().setLayout( layout )

		if isinstance( plugOrPlugValueWidget, PlugValueWidget ) :
			self.__valueWidget = plugOrPlugValueWidget
			plug = self.__valueWidget.getPlug()
		else :
			self.__valueWidget = PlugValueWidget.create( plugOrPlugValueWidget )
			plug = plugOrPlugValueWidget

		self.__label = GafferUI.Label( label or CamelCase.toSpaced( plug.getName() ) )
		
		layout.addWidget( self.__label._qtWidget() )
		layout.addWidget( self.__valueWidget._qtWidget() )
		
		#label.set_width_chars( 15 )
		#label.set_alignment( 1, 0.5 )

		#labelEventBox = gtk.EventBox()
		#labelEventBox.add( label )
		
		#self.__gtkHBox.pack_start( labelEventBox, False )			
		#if self.__valueWidget :
		#	self.__gtkHBox.pack_start( self.__valueWidget.gtkWidget() )

		#if description :
		#	self.__tooltips = gtk.Tooltips()
		#	self.__tooltips.set_tip( labelEventBox, "hi there" )		
		
