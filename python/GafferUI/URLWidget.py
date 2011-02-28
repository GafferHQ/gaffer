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

import gtk

import IECore

import GafferUI

class URLWidget( GafferUI.Widget ) :

	def __init__( self, url="", label=None, font={}, alignment=IECore.V2f( 0.5, 0.5 ) ) :
	
		GafferUI.Widget.__init__( self, gtk.EventBox() )

		self.__label = gtk.Label()
		self.__label.show()

		self.gtkWidget().add_events( gtk.gdk.BUTTON_PRESS_MASK )
		self.gtkWidget().add_events( gtk.gdk.ENTER_NOTIFY_MASK )
		self.gtkWidget().add_events( gtk.gdk.LEAVE_NOTIFY_MASK )
		self.gtkWidget().connect( "button-press-event", self.__buttonPress )
		self.gtkWidget().connect( "enter-notify-event", self.__enterNotify )
		self.gtkWidget().connect( "leave-notify-event", self.__leaveNotify )

		self.gtkWidget().add( self.__label )
		
		self.__url = url
		self.__labelText = label
		self.__font = font
		self.__updateMarkup()
		self.setAlignment( alignment )

	def setAlignment( self, alignment ) :
	
		self.__label.set_alignment( alignment[0], alignment[1] )
		
	def getAlignment( self ) :
	
		return IECore.V2f( *self.__label.get_alignment() )

	def setFont( self, **kw ) :
	
		self.__font = kw
		self.__updateMarkup()
		
	def getFont( self ) :
	
		return self.__font

	def getURL( self ) :
	
		return self.__url

	def setURL( self, url ) :
	
		self.__url = url
		self.__updateMarkup()

	def getLabel( self ) :
	
		return self.__labelText
		
	def setLabel( self, label ) :
	
		self.__labelText = label
		self.__updateMarkup()

	def __buttonPress( self, widget, event ) :
	
		GafferUI.showURL( self.getURL() )
		
	def __enterNotify( self, widget, event ) :
	
		self.__label.set_state( gtk.STATE_PRELIGHT )
		self.__updateMarkup()
	
	def __leaveNotify( self, widget, event ) :
	
		self.__label.set_state( gtk.STATE_NORMAL )
		self.__updateMarkup()
		
	def __updateMarkup( self ) :
	
		text = self.getLabel() or self.getURL()
		font = self._pangoFont( **self.__font )
		if self.__label.state==gtk.STATE_PRELIGHT :
			self.__label.set_markup( "<span underline='double' underline_color='#FF0000' " + font + ">" + text + "</span>" )
		else :
			self.__label.set_markup( "<span underline='single' " + font + ">" + text + "</span>" )

