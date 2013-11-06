##########################################################################
#  
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import sys
import traceback
import weakref

import IECore

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

## The MessageWidget class displays a log of messages in the format specified by
# IECore MessageHandlers.
class MessageWidget( GafferUI.Widget ) :

	def __init__( self, **kw ) :
		
		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=4 )
		GafferUI.Widget.__init__( self, row, **kw )
		
		with row :
		
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
			self.__textChangedConnection = self.__text.textChangedSignal().connect( Gaffer.WeakMethod( self.__textChanged ) )
	
		self.__messageHandler = _MessageHandler( self )
	
	## Returns the MultiLineTextWidget used internally for displaying the messages.
	# This can be manipulated directly to clear the output or to interleave the messages
	# with text from another source.
	def textWidget( self ) :
	
		return self.__text
	
	## Returns a MessageHandler which will output to this Widget.
	## \threading It is safe to use the handler on threads other than the main thread.
	def messageHandler( self ) :
	
		return self.__messageHandler
	
	## May be called to append a message manually.
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
		
		with Gaffer.BlockedConnection( self.__textChangedConnection ) :
			self.__text._qtWidget().appendHtml( formatted )

		# update the gui so messages are output as they occur, rather than all getting queued
		# up till the end.
		QtGui.QApplication.instance().processEvents( QtCore.QEventLoop.ExcludeUserInputEvents )
	
	## May be called to append a message describing an exception. By default the currently handled exception is displayed
	# but another exception can be displayed by specifying exceptionInfo in the same format as returned by sys.exc_info().
	def appendException( self, exceptionInfo=None ) :
	
		if exceptionInfo is None :
			exceptionInfo = sys.exc_info()
	
		if exceptionInfo[0] is None :
			return

		self.appendMessage(
			IECore.Msg.Level.Error,
			str( exceptionInfo[1] ),
			"".join( traceback.format_exception( *exceptionInfo ) )
		)
		
	def __buttonClicked( self, button ) :
		
		## \todo Decide how we allow this to be achieved directly using the public
		# interface of MultiLineTextWidget.
		toFind = IECore.Msg.levelAsString( button.__level ) + " : "
		if not self.__text._qtWidget().find( toFind ) :
			self.__text._qtWidget().moveCursor( QtGui.QTextCursor.Start )
			self.__text._qtWidget().find( toFind )

	def __textChanged( self, widget ) :
	
		assert( widget is self.__text )
		
		# if someone else has changed the text behind our backs, then we need to
		# update our button visibility based on the contents.
		t = self.__text.getText()
		for level, button in self.__levelButtons.items() :
			button.setVisible( IECore.Msg.levelAsString( button.__level ) + " : " in t )

class _MessageHandler( IECore.MessageHandler ) :

	def __init__( self, messageWidget ) :
	
		IECore.MessageHandler.__init__( self )	
		
		# using a weak reference because we're owned by the MessageWidget,
		# so we mustn't have a reference back.	
		self.__messageWidget = weakref.ref( messageWidget )
		
	def handle( self, level, context, msg ) :
		
		w = self.__messageWidget()
		
		if w :
			GafferUI.EventLoop.executeOnUIThread( IECore.curry( w.appendMessage, level, context, msg ) )
		else :
			# the widget has died. bad things are probably afoot so its best
			# that we output the messages somewhere to aid in debugging.
			IECore.MessageHandler.getDefaultHandler().handle( level, context, msg )
