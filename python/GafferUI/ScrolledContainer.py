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

class ScrolledContainer( GafferUI.ContainerWidget ) :

	ScrollMode = IECore.Enum.create( "Never", "Always", "Automatic" )

	def __init__( self, horizontalMode=ScrollMode.Automatic, verticalMode=ScrollMode.Automatic, borderWidth=0 ) :
	
		GafferUI.ContainerWidget.__init__( self, gtk.ScrolledWindow() )
		
		self.gtkWidget().set_property( "border-width", borderWidth )
		self.setHorizontalMode( horizontalMode )
		self.setVerticalMode( verticalMode )
		
		self.__child = None
		
	def removeChild( self, child ) :
	
		assert( child is self.__child )
		self.gtkWidget().remove( self.__child.gtkWidget() )
		self.__child = None
		
	def setChild( self, child ) :
	
		if self.__child :
			self.removeChild( self.__child )
		
		needsViewport = True
		try :
			child.gtkWidget().get_property( "hadjustment" )
			needsViewport = False
		except :
			pass
			
		if needsViewport :
			self.gtkWidget().add_with_viewport( child.gtkWidget() )
		else :
			self.gtkWidget().add( child.gtkWidget() )
		
		self.__child = child
	
	def getChild( self ) :
	
		return self.__child
	
	__modesToPolicies = {
		ScrollMode.Never : gtk.POLICY_NEVER,
		ScrollMode.Always : gtk.POLICY_ALWAYS,
		ScrollMode.Automatic : gtk.POLICY_AUTOMATIC,
	}

	__policiesToModes = {
		gtk.POLICY_NEVER : ScrollMode.Never,
		gtk.POLICY_ALWAYS : ScrollMode.Always,
		gtk.POLICY_AUTOMATIC : ScrollMode.Automatic,
	}
		
	def setHorizontalMode( self, mode ) :
	
		p = self.gtkWidget().get_policy()
		self.gtkWidget().set_policy( self.__modesToPolicies[mode], p[1] )

	def getHorizontalMode( self ) :
	
		p = self.gtkWidget().get_policy()
		return self.__policiesToModes[p[0]]
		
	def setVerticalMode( self, mode ) :
	
		p = self.gtkWidget().get_policy()
		self.gtkWidget().set_policy( p[0], self.__modesToPolicies[mode] )

	def getVerticalMode( self ) :
	
		p = self.gtkWidget().get_policy()
		return self.__policiesToModes[p[1]]
		
GafferUI.Widget._parseRCStyle(

	"""
	style "gafferScrollbar"
	{
		GtkScrollbar::slider-width = 12
		GtkScrollbar::has-backward-stepper = 0
		GtkScrollbar::has-secondary-backward-stepper = 1
		bg[ACTIVE] = $dull
		bg[PRELIGHT] = $bright
		bg[SELECTED] = $bright
	}

	widget_class "*<GtkScrollbar>*" style "gafferScrollbar"
	""",
	
	{
		"dull" : GafferUI.Widget._gtkRCColor( IECore.Color3f( 0.05 ) ),
		"bright" : GafferUI.Widget._gtkRCColor( IECore.Color3f( 0.1 ) ),
	}

)
		
