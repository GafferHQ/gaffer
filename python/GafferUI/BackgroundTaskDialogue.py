##########################################################################
#
#  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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
import functools
import traceback

import imath

import IECore

import Gaffer
import GafferUI

from Qt import QtCore

class BackgroundTaskDialogue( GafferUI.Dialogue ) :

	def __init__( self, title, **kw ) :

		GafferUI.Dialogue.__init__( self, title, **kw )

		# Build UI. We have widgets for two states - busy and error - and manage
		# widget visibility to switch between those states.

		with GafferUI.ListContainer( spacing = 4 ) as column :

			GafferUI.Spacer( imath.V2i( 250, 20 ) )

			self.__busyWidget = GafferUI.BusyWidget(
				parenting = {
					"horizontalAlignment" : GafferUI.ListContainer.HorizontalAlignment.Center
				}
			)

			self.__errorImage = GafferUI.Image(
				"failure.png",
				parenting = {
					"horizontalAlignment" : GafferUI.HorizontalAlignment.Center,
					"expand" : True,
				}
			)

			self.__label = GafferUI.Label(
				parenting = { "horizontalAlignment" : GafferUI.ListContainer.HorizontalAlignment.Center }
			)

			GafferUI.Spacer( imath.V2i( 250, 20 ) )

			self.__messageWidget = GafferUI.MessageWidget( toolbars = True )

		self._setWidget( column )

		self.__continueButton = self._addButton( "Continue" )
		self.__cancelButton = self._addButton( "Cancel" )
		# Make it impossible to accidentally cancel by hitting `Enter`.
		self.__cancelButton._qtWidget().setFocusPolicy( QtCore.Qt.NoFocus )
		self.__cancelButton.clickedSignal().connect( Gaffer.WeakMethod( self.__cancelClicked ) )

		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )

		self.__backgroundTask = None
		self.__messageHandler = IECore.CapturingMessageHandler()

	## Enters a modal state and waits for the result of calling `ParallelAlgo.callOnBackgroundThread()`.
	# Any errors which occur while running `function` are reported within the dialogue before exiting.
	def waitForBackgroundTask( self, function, parentWindow = None ) :

		# Put UI in "busy" mode.

		self.__label.setText( self.getTitle() )
		self.__busyWidget.setVisible( True )
		self.__errorImage.setVisible( False )
		self.__messageWidget.setVisible( False )
		self.__continueButton.setVisible( False )
		self.__cancelButton.setText( "Cancel" )
		self.__cancelButton.setVisible( True )
		self.__cancelButton.setEnabled( True )

		# Queue up an event that will launch the background task
		# as soon as we've entered our modal state.

		QtCore.QTimer.singleShot( 1, functools.partial( self.__launchBackgroundTask, function ) )

		# Enter modal state. This will return when the background task completes
		# and calls `setModal( False )`. We block UI thread execution while our
		# background task executes because ui thread calls may make graph edits
		# which would cancel our task unexpectedly.

		with GafferUI.EventLoop.BlockedUIThreadExecution() :
			self.setModal( True, parentWindow )
			self.__backgroundTask = None

		# Deal with cancellation.

		if isinstance( self.__backgroundResult, IECore.Cancelled ) :
			if self.__cancelButton.getText() == "Cancelling..." :
				return self.__backgroundResult
			else :
				# Unexpected cancellation. This means a bug somewhere.
				# Capture an error message that we'll display below.
				self.__messageHandler.handle(
					IECore.Msg.Level.Error, "Unexpected cancellation", "Please report this as a bug."
				)

		# If there was an error or warning, then we enter a second modal state
		# to display it.

		self.__messageWidget.setMessages( self.__messageHandler.messages )
		errors = self.__messageWidget.messageCount( IECore.Msg.Level.Error )
		warnings = self.__messageWidget.messageCount( IECore.Msg.Level.Warning )
		if warnings or errors :
			self.__label.setText( "<b>Error</b>" if errors else "<b>Warning</b>" )
			self.__busyWidget.setVisible( False )
			self.__errorImage.setVisible( True )
			self.__messageWidget.setVisible( True )
			self.__cancelButton.setVisible( False )
			self.__continueButton.setVisible( True )
			self.waitForButton()

		# And finally we can return to the caller.

		return self.__backgroundResult

	def _acceptsClose( self ) :

		return self.__backgroundTask is None

	def __launchBackgroundTask( self, function ) :

		del self.__messageHandler.messages[:]
		self.__backgroundTask = Gaffer.ParallelAlgo.callOnBackgroundThread(
			None, functools.partial(
				self.__backgroundFunction, function = function
			)
		)

	def __backgroundFunction( self, function ) :

		with self.__messageHandler :
			try :
				result = function()
			except :
				result = sys.exc_info()[1]
				if not isinstance( result, IECore.Cancelled ) :
					IECore.msg( IECore.Msg.Level.Error, str( result ), traceback.format_exc() )
				# Avoid circular references that would prevent this
				# stack frame (and therefore `self`) from dying.
				result.__traceback__ = None

		self.__backgroundResult = result
		self.setModal( False )

	def __cancel( self ) :

		self.__backgroundTask.cancel()
		self.__cancelButton.setText( "Cancelling..." )
		self.__cancelButton.setEnabled( False )

	def __cancelClicked( self, *unused ) :

		self.__cancel()

	def __keyPress( self, widget, event ) :

		if event.key == "Escape" and self.__backgroundTask is not None :
			self.__cancel()
			return True

		return False
