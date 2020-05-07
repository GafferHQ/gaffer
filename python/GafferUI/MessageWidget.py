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

import weakref
import functools
import imath

import IECore

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

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
				for buttonSpec in buttonSpecs :
					button = GafferUI.Button(
						image = IECore.Msg.levelAsString( buttonSpec[0] ).lower() + "Notification.png",
						hasFrame = False,
					)
					button.__level = buttonSpec[0]
					self.__levelButtons[buttonSpec[0]] = button
					button.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ), scoped = False )
					button.setVisible( False )
					button.setToolTip( buttonSpec[1] )

				GafferUI.Spacer( imath.V2i( 10 ) )

			self.__text = GafferUI.MultiLineTextWidget( editable=False )

		self.__messageLevel = IECore.Msg.Level.Info
		self.__messageHandler = _MessageHandler( self )
		self.__messages = []
		self.__processingEvents = False

	## Returns a MessageHandler which will output to this Widget.
	## \threading It is safe to use the handler on threads other than the main thread.
	def messageHandler( self ) :

		return self.__messageHandler

	## It can be useful to forward messages captured by this widget
	# on to other message handlers - for instance to perform centralised
	# logging in addition to local display. This method returns a
	# CompoundMessageHandler which can be used for such forwarding -
	# simply add a handler with forwardingMessageHandler().addHandler().
	def forwardingMessageHandler( self ) :

		return self.__messageHandler._forwarder

	## Sets an IECore.MessageHandler.Level specifying which
	# type of messages will be visible to the user - levels above
	# that specified will be invisible. Note that the invisible
	# messages are still stored, so they can be made visible at a later
	# time by a suitable call to setMessageLevel(). This can be useful
	# for revealing debug messages only after a warning or error has
	# alerted the user to a problem.
	def setMessageLevel( self, messageLevel ) :

		assert( isinstance( messageLevel, IECore.MessageHandler.Level ) )

		if messageLevel == self.__messageLevel :
			return

		self.__messageLevel = messageLevel
		self.__text.setText( "" )
		for message in self.__messages :
			self.__appendMessageToText( *message )

	def getMessageLevel( self ) :

		return self.__messageLevel

	## May be called to append a message manually.
	# \note Because these are not real messages, they are not
	# passed to the forwardingMessageHandler().
	# \deprecated.
	def appendMessage( self, level, context, message ) :

		self.__levelButtons[level].setVisible( True )
		self.__messages.append( ( level, context, message ) )
		if self.__appendMessageToText( level, context, message ) :

			# Update the gui so messages are output as they occur, rather than all getting queued
			# up till the end. We have to be careful to avoid recursion when doing this - another
			# thread may be queuing up loads of messages using self.messageHandler(), and those
			# will get processed by processEvents(), resulting in a recursive call to appendMessage().
			# If the other thread supplies messages fast enough and we don't guard against recursion
			# then we can end up exceeding Python's stack limit very quickly.
			if not self.__processingEvents :
				try :
					self.__processingEvents = True
					# Calling processEvents can cause almost anything to be executed,
					# including idle callbacks that might build UIs. We must push an
					# empty parent so that any widgets created will not be inadvertently
					# parented to the wrong thing.
					## \todo Calling `processEvents()` has also caused problems in the
					# past where a simple error message has then led to idle callbacks
					# being triggered which in turn triggered a graph evaluation. Having
					# a message handler lead to arbitarary code execution is not good! Is
					# there some way we can update the UI without triggering arbitrary
					# code evaluation?
					self._pushParent( None )
					QtWidgets.QApplication.instance().processEvents( QtCore.QEventLoop.ExcludeUserInputEvents )
					self._popParent()
				finally :
					self.__processingEvents = False

	## Returns the number of messages being displayed, optionally
	# restricted to the specified level.
	def messageCount( self, level = None ) :

		if level is not None :
			return sum( y[0] == level for y in self.__messages )
		else :
			return sum(
				[
					self.messageCount( IECore.Msg.Level.Debug ),
					self.messageCount( IECore.Msg.Level.Info ),
					self.messageCount( IECore.Msg.Level.Warning ),
					self.messageCount( IECore.Msg.Level.Error ),
				]
			)

	## Clears all the displayed messages.
	def clear( self ) :

		self.__text.setText( "" )
		self.__messages = []
		for button in self.__levelButtons.values() :
			button.setVisible( False )

	def __buttonClicked( self, button ) :

		# make sure messages of this level are being displayed
		if button.__level > self.__messageLevel :
			self.setMessageLevel( button.__level )

		# scroll to the next one
		toFind = IECore.Msg.levelAsString( button.__level ) + " : "

		def find( widget, text ) :

			# Really we just want to call `widget.find( text )`
			# but that is utterly broken in PySide - it is marked
			# as a static method so receives a null self and promptly
			# crashes. So instead we reproduce the work that
			# `widget.find()` does internally.

			search = widget.document().find( text, widget.textCursor() )
			if search :
				widget.setTextCursor( search )

			return search

		if not find( self.__text._qtWidget(), toFind ) :
			self.__text._qtWidget().moveCursor( QtGui.QTextCursor.Start )
			find( self.__text._qtWidget(), toFind )

	def __appendMessageToText( self, level, context, message ) :

		if level > self.__messageLevel :
			return False

		formatted = "<h1 class='%s'>%s : %s </h1><pre class='message'>%s</pre><br>" % (
			IECore.Msg.levelAsString( level ),
			IECore.Msg.levelAsString( level ),
			context,
			message
		)

		self.__text.appendHTML( formatted )

		return True

class _MessageHandler( IECore.MessageHandler ) :

	def __init__( self, messageWidget ) :

		IECore.MessageHandler.__init__( self )

		self._forwarder = IECore.CompoundMessageHandler()

		# using a weak reference because we're owned by the MessageWidget,
		# so we mustn't have a reference back.
		self.__messageWidget = weakref.ref( messageWidget )

	def handle( self, level, context, msg ) :

		self._forwarder.handle( level, context, msg )

		w = self.__messageWidget()

		if w :
			GafferUI.EventLoop.executeOnUIThread( functools.partial( w.appendMessage, level, context, msg ) )
		else :
			# the widget has died. bad things are probably afoot so its best
			# that we output the messages somewhere to aid in debugging.
			IECore.MessageHandler.getDefaultHandler().handle( level, context, msg )
