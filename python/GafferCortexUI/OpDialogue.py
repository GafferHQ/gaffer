##########################################################################
#
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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
import threading
import traceback
import imath

import IECore

import Gaffer
import GafferUI
import GafferCortex

## A dialogue which allows a user to edit the parameters of an
# IECore.Op instance and then execute it.
class OpDialogue( GafferUI.Dialogue ) :

	## Defines what happens when the op has been successfully executed :
	#
	# FromUserData : Get behaviour from ["UI"]["postExecuteBehaviour"] userData, which should
	#	contain a string value specifying one of the other Enum values. If no userData is found,
	#	it defaults to DisplayResult.
	#
	# None : Do nothing. The dialogue returns to the parameter editing state.
	#
	# Close : The dialogue is closed immediately.
	#
	# DisplayResult : The result is displayed, with a button for returning to the parameter editing state.
	#
	# DisplayResultAndClose : The result is displayed, with a button for closing the dialogue.
	#
	# NoneByDefault : deprecated - the same as DisplayResult
	# CloseByDefault : deprecated - the same as DisplayResult
	PostExecuteBehaviour = IECore.Enum.create( "FromUserData", "None_", "Close", "DisplayResult", "DisplayResultAndClose", "NoneByDefault", "CloseByDefault" )

	## Defines which button has the focus when the op is displayed for editing.
	#
	# FromUserData : Gets the default button from ["UI"]["defaultButton"] userData, which
	#	should contain a string value specifying one of the other Enum values. If no userData is found,
	#	it defaults to OK.
	#
	# None : Neither button has the focus.
	#
	# OK : The OK button has the focus.
	#
	# Cancel : The cancel button has the focus.
	DefaultButton = IECore.Enum.create( "FromUserData", "None_", "OK", "Cancel" )

	# If executeInBackground is True, then the Op will be executed on another
	# thread, allowing the UI to remain responsive during execution. This is
	# the preferred method of operation, but it is currently not the default
	# in case certain clients are relying on running the Op on the main thread.
	def __init__(
		self,
		opInstanceOrOpHolderInstance,
		title=None,
		sizeMode=GafferUI.Window.SizeMode.Manual,
		postExecuteBehaviour = PostExecuteBehaviour.FromUserData,
		executeInBackground = False,
		defaultButton = DefaultButton.FromUserData,
		executeImmediately = False,
		**kw
	) :

		# sort out our op and op holder

		if isinstance( opInstanceOrOpHolderInstance, IECore.Op ) :
			opInstance = opInstanceOrOpHolderInstance
			self.__node = GafferCortex.ParameterisedHolderNode()
			self.__node.setParameterised( opInstance )
			# set the current plug values as userDefaults to provide
			# a clean NodeUI based on the initial settings of the Op.
			# we assume that if an OpHolder was passed directly then
			# the metadata has already been setup as preferred.
			self.__setUserDefaults( self.__node )
		else :
			self.__node = opInstanceOrOpHolderInstance
			opInstance = self.__node.getParameterised()[0]

		# initialise the dialogue

		if title is None :
			title = IECore.CamelCase.toSpaced( opInstance.typeName() )

		GafferUI.Dialogue.__init__( self, title, sizeMode=sizeMode, **kw )

		# decide what we'll do after execution.

		if postExecuteBehaviour == self.PostExecuteBehaviour.FromUserData :

			postExecuteBehaviour = self.PostExecuteBehaviour.DisplayResult

			d = None
			with IECore.IgnoredExceptions( KeyError ) :
				d = opInstance.userData()["UI"]["postExecuteBehaviour"]
			if d is not None :
				for v in self.PostExecuteBehaviour.values() :
					if str( v ).lower() == d.value.lower() :
						postExecuteBehaviour = v
						break
			else :
				# backwards compatibility with batata
				with IECore.IgnoredExceptions( KeyError ) :
					d = opInstance.userData()["UI"]["closeAfterExecution"]
				if d is not None :
					postExecuteBehaviour = self.PostExecuteBehaviour.Close if d.value else self.PostExecuteBehaviour.DisplayResult

		self.__postExecuteBehaviour = postExecuteBehaviour
		self.__executeInBackground = executeInBackground
		self.__defaultButton = defaultButton

		# make a frame to contain our main ui element. this will
		# contain different elements depending on our state.

		self.__frame = GafferUI.Frame()
		self._setWidget( self.__frame )

		# get the ui for the op - we'll use this when we want
		# the user to edit parameters.

		self.__parameterEditingUI = GafferUI.NodeUI.create( self.__node )

		# build a ui element for progress feedback and suchlike.
		# we'll use this when executing and displaying the result.

		with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 ) as self.__progressUI :

			GafferUI.Spacer( imath.V2i( 1 ), preferredSize = imath.V2i( 1, 1 ) )

			self.__progressIconFrame = GafferUI.Frame(
				borderStyle = GafferUI.Frame.BorderStyle.None_,
				parenting = {
					"horizontalAlignment" : GafferUI.HorizontalAlignment.Center
				}
			)

			self.__progressLabel = GafferUI.Label(
				parenting = {
					"expand" : True,
					"horizontalAlignment" : GafferUI.HorizontalAlignment.Center,
				}
			)

			GafferUI.Spacer( imath.V2i( 250, 1 ), preferredSize = imath.V2i( 250, 1 ) )

			with GafferUI.Collapsible( "Details", collapsed = True ) as self.__messageCollapsible :

				self.__messageWidget = GafferUI.MessageWidget( toolbars = True )

				# connect to the collapsible state change so we can increase the window
				# size when the details pane is first shown.
				self.__messageCollapsibleStateChangedConnection = self.__messageCollapsible.stateChangedSignal().connect(
					Gaffer.WeakMethod( self.__messageCollapsibleStateChanged )
				)

		# add buttons. our buttons mean different things depending on our current state,
		# but they equate roughly to going forwards or going backwards.

		self.__backButton = self._addButton( "Back" )
		self.__forwardButton = self._addButton( "Forward" )

		self.__preExecuteSignal = GafferUI.WidgetSignal()
		self.__postExecuteSignal = Gaffer.Signal2()
		self.__opExecutedSignal = Gaffer.Signal1()
		self.__haveResizedToFitParameters = False

		if executeImmediately :
			self.__initiateExecution()
		else :
			self.__initiateParameterEditing()

	## Returns the ParameterisedHolder used to store the Op.
	# This may be used to edit parameter values.
	def parameterisedHolder( self ) :

		return self.__node

	## Signal emitted before executing the Op.
	# Slots should have the signature `bool slot( opDialogue )`,
	# and may return True to cancel execution, or False to
	# allow it to continue.
	def preExecuteSignal( self ) :

		return self.__preExecuteSignal

	## Signal emitted after executing the Op.
	# Slots should have the signature `slot( opDialogue, result )`.
	def postExecuteSignal( self ) :

		return self.__postExecuteSignal

	## A signal called when the user has pressed the execute button
	# and the Op has been successfully executed. This is passed the
	# result of the execution.
	## \deprecated Use postExecuteSignal() instead.
	def opExecutedSignal( self ) :

		return self.__opExecutedSignal

	## Returns the internal MessageWidget used for displaying messages
	# output by the Op.
	def messageWidget( self ) :

		return self.__messageWidget

	## Causes the dialogue to enter a modal state, returning the result
	# of executing the Op, or None if the user cancelled the operation. Any
	# validation or execution errors will be reported to the user and return
	# to the dialogue for them to cancel or try again.
	def waitForResult( self, **kw ) :

		self.__resultOfWait = None
		self.setModal( True, **kw ) # will return when the dialogue is closed
		return self.__resultOfWait

	def _acceptsClose( self ) :

		# we mustn't allow the window to be closed while
		# the op is running in the background.
		return self.__state != self.__State.Execution

	__State = IECore.Enum.create( "ParameterEditing", "Execution", "ErrorDisplay", "ResultDisplay" )

	def __initiateParameterEditing( self, *unused ) :

		self.__backButton.setText( "Cancel" )
		self.__backButton.setEnabled( True )
		self.__backButton.setVisible( True )
		self.__backButtonClickedConnection = self.__backButton.clickedSignal().connectFront( Gaffer.WeakMethod( self.__close ) )

		executeLabel = "OK"
		with IECore.IgnoredExceptions( KeyError ) :
			executeLabel = self.__node.getParameterised()[0].userData()["UI"]["buttonLabel"].value

		self.__forwardButton.setText( executeLabel )
		self.__forwardButton.setEnabled( True )
		self.__forwardButton.setVisible( True )
		self.__forwardButtonClickedConnection = self.__forwardButton.clickedSignal().connectFront( Gaffer.WeakMethod( self.__initiateExecution ) )

		self.__frame.setChild( self.__parameterEditingUI )

		self.__focusDefaultButton()

		self.__state = self.__State.ParameterEditing

		# when we first display our parameters, we want to ensure that the window
		# is big enough to fit them nicely. we don't do this the next time we show
		# the parameters, because the user may have deliberately resized the window.
		if not self.__haveResizedToFitParameters :
			self.resizeToFitChild( shrink = False )
			self.__haveResizedToFitParameters = True

	def __close( self, *unused ) :

		self.__state = self.__State.ParameterEditing
		self.close()

	def __initiateExecution( self, *unused ) :

		if self.preExecuteSignal()( self ) :
			return

		self.__progressIconFrame.setChild( GafferUI.BusyWidget() )
		self.__progressLabel.setText( "<h3>Processing...</h3>" )
		self.__backButton.setEnabled( False )
		self.__backButton.setText( "Cancel" )
		self.__forwardButton.setVisible( False )
		self.__messageWidget.clear()
		self.__messageCollapsible.setCollapsed( True )

		self.__state = self.__State.Execution

		if self.__executeInBackground :
			self.__frame.setChild( self.__progressUI )
			threading.Thread( target = self.__execute ).start()
		else :
			# we don't display progress when we're not threaded,
			# because we have no way of updating it.
			self.__execute()

	def __execute( self ) :

		try :

			self.__node.setParameterisedValues()

			with self.__messageWidget.messageHandler() :
				result = self.__node.getParameterised()[0]()

		except Exception as e :

			result = sys.exc_info()

		if self.__executeInBackground :
			GafferUI.EventLoop.executeOnUIThread( IECore.curry( self.__finishExecution, result ) )
		else :
			# We're being called on the main gui thread, most likely from a button click on
			# the forward button. If we called __finishExecution() immediately, it would add
			# new slots to the button click signal, and these would be executed immediately
			# for the _current_ click - this is not what we want! So we defer __finishExecution
			# to the next idle event, when the current click is a thing of the past.
			## \todo The documentation for boost::signals2 seems to imply that it has a different
			# behaviour, and that slots added during signal emission are ignored until the next
			# emission. If we move to using signals2, we may be able to revert this change.
			GafferUI.EventLoop.addIdleCallback( IECore.curry( self.__finishExecution, result ) )

	def __finishExecution( self, result ) :

		if isinstance( result, IECore.Object ) :

			if self.getModal() :
				self.__resultOfWait = result

			self.__initiateResultDisplay( result )

			self.opExecutedSignal()( result )
			self.postExecuteSignal()( self, result )

		else :

			self.__initiateErrorDisplay( result )

		return False # remove idle callback

	def __initiateErrorDisplay( self, exceptionInfo ) :

		self.__progressIconFrame.setChild( GafferUI.Image( "failure.png" ) )
		self.__progressLabel.setText( "<h3>Failed</h3>" )

		self.__messageCollapsible.setCollapsed( False )

		self.__backButton.setVisible( True )
		self.__backButton.setText( "Cancel" )
		self.__backButton.setEnabled( True )
		self.__backButtonClickedConnection = self.__backButton.clickedSignal().connect( Gaffer.WeakMethod( self.__close ) )

		self.__forwardButton.setVisible( True )
		self.__forwardButton.setText( "Retry" )
		self.__forwardButton.setEnabled( True )
		self.__forwardButtonClickedConnection = self.__forwardButton.clickedSignal().connect( Gaffer.WeakMethod( self.__initiateParameterEditing ) )

		self.__messageWidget.messageHandler().handle(
			IECore.Msg.Level.Debug,
			"Python Traceback",
			"".join( traceback.format_exception( *exceptionInfo ) )
		)

		self.__messageWidget.messageHandler().handle(
			IECore.Msg.Level.Error,
			"Problem Executing {opName}".format( opName=self.__node.getParameterised()[0].typeName() ),
			str( exceptionInfo[1] ),
		)

		self.__frame.setChild( self.__progressUI )

		self.__forwardButton._qtWidget().setFocus()

		self.__state = self.__State.ErrorDisplay

	def __initiateResultDisplay( self, result ) :

		# Although we computed a result successfully, there may still be minor problems
		# indicated by messages the Op emitted - check for those.
		problems = []
		for level in ( IECore.Msg.Level.Error, IECore.Msg.Level.Warning ) :
			count = self.__messageWidget.messageCount( level )
			if count :
				problems.append( "%d %s%s" % ( count, IECore.Msg.levelAsString( level ).capitalize(), "s" if count > 1 else "" ) )

		if not problems :
			# If there were no problems, then our post execute behaviour may
			# indicate that we don't need to display anything - deal with
			# those cases.
			if self.__postExecuteBehaviour == self.PostExecuteBehaviour.Close :
				self.__close()
				return
			elif self.__postExecuteBehaviour == self.PostExecuteBehaviour.None_ :
				self.__initiateParameterEditing()
				return

		# Either the post execute behaviour says we should display the result, or we're
		# going to anyway, because we don't want the problems to go unnoticed.

		self.__progressIconFrame.setChild(
			GafferUI.Image( "successWarning.png" if problems else "success.png" )
		)

		completionMessage = "Completed"
		if problems :
			completionMessage += " with " + " and ".join( problems )
			self.__messageCollapsible.setCollapsed( False )

		self.__progressLabel.setText( "<h3>" + completionMessage + "</h3>" )

		self.__messageWidget.messageHandler().handle( IECore.Msg.Level.Info, "Result", str( result ) )

		self.__backButton.setText( "Close" )
		self.__backButton.setEnabled( True )
		self.__backButton.setVisible( True )
		self.__backButtonClickedConnection = self.__backButton.clickedSignal().connect( Gaffer.WeakMethod( self.__close ) )

		self.__forwardButton.setText( "Again!" )
		self.__forwardButton.setEnabled( True )
		self.__forwardButton.setVisible( True )
		self.__forwardButtonClickedConnection = self.__forwardButton.clickedSignal().connect( Gaffer.WeakMethod( self.__initiateParameterEditing ) )

		if self.__postExecuteBehaviour in ( self.PostExecuteBehaviour.DisplayResultAndClose, self.PostExecuteBehaviour.Close ) :
			self.__forwardButton.setVisible( False )

		self.__frame.setChild( self.__progressUI )

		self.__backButton._qtWidget().setFocus()

		self.__state = self.__State.ResultDisplay

	def __focusDefaultButton( self ) :

		defaultButton = self.__defaultButton
		if defaultButton == self.DefaultButton.FromUserData :
			defaultButton = self.DefaultButton.OK
			d = None
			with IECore.IgnoredExceptions( KeyError ) :
				d = self.__node.getParameterised()[0].userData()["UI"]["defaultButton"]
			if d is not None :
				for v in self.DefaultButton.values() :
					if str( v ).lower() == d.value.lower() :
						defaultButton = v
						break

		if defaultButton == self.DefaultButton.None_ :
			self._qtWidget().setFocus()
		elif defaultButton == self.DefaultButton.Cancel :
			self.__backButton._qtWidget().setFocus()
		else :
			self.__forwardButton._qtWidget().setFocus()

	def __messageCollapsibleStateChanged( self, collapsible ) :

		if not collapsible.getCollapsed() :
			# make the window bigger to better fit the messages, but don't make
			# it any smaller than it currently is.
			self.resizeToFitChild( shrink = False )
			# remove our connection - we only want to resize the first time we
			# show the messages. after this we assume that if the window is smaller
			# it is because the user has made it so, and wishes it to remain so.
			self.__messageCollapsibleStateChangedConnection = None

	def __setUserDefaults( self, graphComponent ) :

		if isinstance( graphComponent, Gaffer.Plug ) and hasattr( graphComponent, "getValue" ) :
			with IECore.IgnoredExceptions( Exception ) :
				Gaffer.Metadata.registerValue( graphComponent, "userDefault", graphComponent.getValue() )

		for child in graphComponent.children() :
			self.__setUserDefaults( child )
