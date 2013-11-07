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

from __future__ import with_statement

import sys
import threading

import IECore

import Gaffer
import GafferUI

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
	PostExecuteBehaviour = IECore.Enum.create( "FromUserData", "None", "Close", "DisplayResult", "DisplayResultAndClose", "NoneByDefault", "CloseByDefault" )

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
		**kw
	) :

		# sort out our op and op holder
		
		if isinstance( opInstanceOrOpHolderInstance, IECore.Op ) :
			opInstance = opInstanceOrOpHolderInstance
			self.__node = Gaffer.ParameterisedHolderNode()
			self.__node.setParameterised( opInstance )
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
			
			center = { "horizontalAlignment" : GafferUI.HorizontalAlignment.Center }
			
			GafferUI.Spacer( IECore.V2i( 1 ), parenting = { "expand" : True } )
			
			self.__progressIconFrame = GafferUI.Frame(
				borderStyle = GafferUI.Frame.BorderStyle.None,
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
			
			GafferUI.Spacer( IECore.V2i( 1 ), expand=True )
			
			with GafferUI.Collapsible( "Details", collapsed = True ) :
			
				self.__messageWidget = GafferUI.MessageWidget()
				
		# add buttons. our buttons mean different things depending on our current state,
		# but they equate roughly to going forwards or going backwards.
		
		self.__backButton = self._addButton( "Back" )
		self.__forwardButton = self._addButton( "Forward" )
		
		self.__opExecutedSignal = Gaffer.Signal1()
		
		self.__initiateParameterEditing()
					
	## A signal called when the user has pressed the execute button
	# and the Op has been successfully executed. This is passed the
	# result of the execution.
	def opExecutedSignal( self ) :
	
		return self.__opExecutedSignal
	
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
		self.__backButtonClickedConnection = self.__backButton.clickedSignal().connect( 0, Gaffer.WeakMethod( self.__close ) )
		
		executeLabel = "OK"
		with IECore.IgnoredExceptions( KeyError ) :
			executeLabel = self.__node.getParameterised()[0].userData()["UI"]["buttonLabel"].value
		
		self.__forwardButton.setText( executeLabel )
		self.__forwardButton.setEnabled( True )
		self.__forwardButton.setVisible( True )
		self.__forwardButtonClickedConnection = self.__forwardButton.clickedSignal().connect( 0, Gaffer.WeakMethod( self.__initiateExecution ) )
		
		self.__frame.setChild( self.__parameterEditingUI )

		self.__forwardButton._qtWidget().setFocus()
		
		self.__state = self.__State.ParameterEditing
	
	def __close( self, *unused ) :
	
		self.__state = self.__State.ParameterEditing
		self.close()
				
	def __initiateExecution( self, *unused ) :
		
		self.__progressIconFrame.setChild( GafferUI.BusyWidget() )
		self.__progressLabel.setText( "<h3>Processing...</h3>" )
		self.__backButton.setEnabled( False )
		self.__forwardButton.setEnabled( False )
		self.__messageWidget.textWidget().setText( "" )
		
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
									
		except Exception, e :

			result = sys.exc_info()
			
		GafferUI.EventLoop.executeOnUIThread( IECore.curry( self.__finishExecution, result ) )
		
	def __finishExecution( self, result ) :
	
		if isinstance( result, IECore.Object ) :
		
			if self.getModal() :
				self.__resultOfWait = result
		
			if self.__postExecuteBehaviour == self.PostExecuteBehaviour.Close :
				self.__close()
			elif self.__postExecuteBehaviour == self.PostExecuteBehaviour.None :
				self.__initiateParameterEditing()
			else :
				self.__initiateResultDisplay( result )

 			self.opExecutedSignal()( result )
 			
		else :
		
			self.__initiateErrorDisplay( result )
			
	def __initiateErrorDisplay( self, exceptionInfo ) :
		
		self.__progressIconFrame.setChild( GafferUI.Image( "opDialogueFailure.png" ) )
		self.__progressLabel.setText( "<h3>" + str( exceptionInfo[1] ) + "</h3>" )
	
		self.__backButton.setText( "Cancel" )
		self.__backButton.setEnabled( True )
		self.__backButtonClickedConnection = self.__backButton.clickedSignal().connect( Gaffer.WeakMethod( self.__close ) )
	
		self.__forwardButton.setText( "Retry" )
		self.__forwardButton.setEnabled( True )
		self.__forwardButtonClickedConnection = self.__forwardButton.clickedSignal().connect( Gaffer.WeakMethod( self.__initiateParameterEditing ) )
		
		self.__messageWidget.appendException( exceptionInfo )
		
		self.__frame.setChild( self.__progressUI )

		self.__forwardButton._qtWidget().setFocus()

		self.__state = self.__State.ErrorDisplay
	
	def __initiateResultDisplay( self, result ) :
	
		self.__progressIconFrame.setChild( GafferUI.Image( "opDialogueSuccess.png" ) )
		self.__progressLabel.setText( "<h3>Completed</h3>" )

		self.__messageWidget.appendMessage( IECore.Msg.Level.Info, "Result", str( result ) )

		self.__backButton.setText( "Close" )
		self.__backButton.setEnabled( True )
		self.__backButtonClickedConnection = self.__backButton.clickedSignal().connect( Gaffer.WeakMethod( self.__close ) )
		
		self.__forwardButton.setText( "Again!" )
		self.__forwardButton.setEnabled( True )
		self.__forwardButtonClickedConnection = self.__forwardButton.clickedSignal().connect( Gaffer.WeakMethod( self.__initiateParameterEditing ) )
		
		if self.__postExecuteBehaviour == self.PostExecuteBehaviour.DisplayResultAndClose :
			self.__forwardButton.setVisible( False )

		self.__frame.setChild( self.__progressUI )
			
		self.__backButton._qtWidget().setFocus()

		self.__state = self.__State.ResultDisplay
