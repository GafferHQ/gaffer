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

import gtk

import Gaffer
import GafferUI

class SplinePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :
	
		self.__splineWidget = GafferUI.SplineWidget()
		
		GafferUI.PlugValueWidget.__init__( self, self.__splineWidget.gtkWidget(), plug, **kw )

		self.__splineWidget.gtkWidget().connect( "button-press-event", self.__buttonPress )
		self.__splineWidget.gtkWidget().add_events( gtk.gdk.BUTTON_PRESS_MASK )

		self.__editorWindow = None

	def updateFromPlug( self ) :
	
		plug = self.getPlug()
		s = plug.getValue()
		self.__splineWidget.setSpline( s )
		
	def __buttonPress( self, widget, event ) :
	
		if event.button==1 :
						
			if not self.__editorWindow :
			
				self.__editorWindow = GafferUI.Window()
				self.__editor = GafferUI.SplineEditor( None )
				self.__editorWindow.setChild( self.__editor )
				self.__editorWindowClosedConnection = self.__editorWindow.closedSignal().connect( Gaffer.WeakMethod( self.__editorWindowClosed ) )
			
			scriptNode = self.getPlug().ancestor( Gaffer.ScriptNode.staticTypeId() )
				
			self.ancestor( GafferUI.Window ).addChildWindow( self.__editorWindow )
			self.__editorWindow.setTitle( self.getPlug().relativeName( scriptNode ) )
			self.__editor.splines().clear()
			self.__editor.splines().add( self.getPlug() )
			
			self.__editorWindow.show()
				
	def __editorWindowClosed( self, window ) :
	
		self.__editorWindow = None

GafferUI.PlugValueWidget.registerType( Gaffer.SplineffPlug.staticTypeId(), SplinePlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.SplinefColor3fPlug.staticTypeId(), SplinePlugValueWidget )
