##########################################################################
#  
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

QtGui = GafferUI._qtImport( "QtGui" )

class NotificationMessageHandler( IECore.MessageHandler ) :

	# we want to keep the windows we create alive beyond
	# the lifetime of the handler itself, so they can remain
	# on screen until the user is done with them, so we keep
	# them in this set. they're removed when the user closes the
	# window
	__windows = set()

	def __init__( self, windowTitle = "Notifications" ) :
	
		IECore.MessageHandler.__init__( self )	
				
		self.__window = None
		self.__windowTitle = windowTitle
		
	def handle( self, level, context, msg ) :
		
		if self.__window is None :
			self.__window = _Window( self.__windowTitle )
			self.__window.__closedConnection = self.__window.closedSignal().connect( NotificationMessageHandler.__windowClosed )
			NotificationMessageHandler.__windows.add( self.__window )
			
		self.__window.appendMessage( level, context, msg )
	
	def __exit__( self, type, value, traceBack ) :
		
		IECore.MessageHandler.__exit__( self, type, value, traceBack )
		if self.__window :
			self.__window.setVisible( True )	
	
	@classmethod
	def __windowClosed( cls, window ) :
	
		cls.__windows.remove( window )
	
class _Window( GafferUI.Window ) :

	__levelsToColors = {
		IECore.Msg.Level.Error : "#ff5555",
		IECore.Msg.Level.Warning : "#ffb655",
		IECore.Msg.Level.Info : "#80b3ff",
		IECore.Msg.Level.Debug : "#aaffcc",
	}

	def __init__( self, title ) :
	
		GafferUI.Window.__init__( self, title, borderWidth = 8 )
		
		with self :
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=4 ) :
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=6 ) :
					
					buttonSpecs = [
						( IECore.Msg.Level.Error, "Errors. These may chill you to your very core. Click to scroll to the next one (if you can stomach it)." ),
						( IECore.Msg.Level.Warning, "Warnings. These may give you pause for thought. Click to scroll to the next thinking point." ),
						( IECore.Msg.Level.Info, "Information. You may find this edifying. Click to scroll to the next enlightening nugget." ),
						( IECore.Msg.Level.Debug, "Debug information. You may find this very dull. Click to scroll to the next item." ),
					]
					self.__levelButtons = {}
					self.__buttonClickedConnections = []
					for buttonSpec in buttonSpecs :
						button = GafferUI.Button(
							image = IECore.Msg.levelAsString( buttonSpec[0] ).lower() + "Notification.png",
							hasFrame = False,
						)
						button.__level = buttonSpec[0]
						self.__levelButtons[buttonSpec[0]] = button
						self.__buttonClickedConnections.append( button.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) ) )
						button.setVisible( False )
						button.setToolTip( buttonSpec[1] )
					
					GafferUI.Spacer( IECore.V2i( 10 ) )
				
				self.__text = GafferUI.MultiLineTextWidget( editable=False )
				## \todo This should come from the Style when we get Styles applied to Widgets
				# (and not just Gadgets as we have currently).
				self.__text._qtWidget().document().setDefaultStyleSheet( 
					"""
					h1 { font-weight : bold; font-size : large; }
					h1[class="ERROR"] { color : #ff5555 }
					h1[class="WARNING"] { color : #ffb655 }
					h1[class="INFO"] { color : #80b3ff }
					h1[class="DEBUG"] { color : #aaffcc }
					body { color : red }
					span[class="message"] { color : #999999 }
					"""
				)
		
		self.setResizeable( True )
		
	def appendMessage( self, level, context, message ) :
	
		# make sure relevant button is shown
		self.__levelButtons[level].setVisible( True )
		
		# append message text
		formatted = "<h1 class='%s'>%s : %s </h1><span class='message'>%s</span><br>" % ( 
			IECore.Msg.levelAsString( level ),
			IECore.Msg.levelAsString( level ),
			context,
			message.replace( "\n", "<br>" )
		)
		## \todo Decide how we allow formatting to be specified in the public interface
		# for MultiLineTextWidget.
		self.__text._qtWidget().appendHtml( formatted )
		
	def __buttonClicked( self, button ) :
		
		## \todo Decide how we allow this to be achieved directly using the public
		# interface of MultiLineTextWidget.
		toFind = IECore.Msg.levelAsString( button.__level ) + " : "
		if not self.__text._qtWidget().find( toFind ) :
			self.__text._qtWidget().moveCursor( QtGui.QTextCursor.Start )
			self.__text._qtWidget().find( toFind )