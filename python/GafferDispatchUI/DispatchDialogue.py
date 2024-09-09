##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

import enum
import functools
import sys
import threading
import traceback

import IECore

import Gaffer
import GafferDispatch

import GafferUI

## A dialogue which can be used to dispatch tasks
class DispatchDialogue( GafferUI.Dialogue ) :

	## Defines what happens when the tasks have been successfully dispatched :
	#
	# Close : The dialogue is closed immediately.
	#
	# Confirm : The dialogue remains open confirming success, with a button for returning to the editing state.
	PostDispatchBehaviour = enum.Enum( "PostDispatchBehaviour", [ "Close", "Confirm" ] )

	__dispatchDialogueMenuDefinition = None

	def __init__( self, tasks, dispatchers, nodesToShow, postDispatchBehaviour=PostDispatchBehaviour.Confirm, title="Dispatch Tasks", sizeMode=GafferUI.Window.SizeMode.Manual, **kw ) :

		GafferUI.Dialogue.__init__( self, title, sizeMode=sizeMode, **kw )

		self._getWidget().setBorderStyle( GafferUI.Frame.BorderStyle.None_ )

		self.__dispatchers = dispatchers
		self.__tasks = tasks
		self.__nodesToShow = nodesToShow
		self.__script = tasks[0].scriptNode()
		# hold a reference to the script window so plugs which launch child windows work properly.
		# this is necessary for PlugValueWidgets like color swatches and ramps. Ideally those widgets
		# wouldn't rely on the existence of a ScriptWindow and we could drop this acquisition.
		self.__scriptWindow = GafferUI.ScriptWindow.acquire( self.__script )

		self.__postDispatchBehaviour = postDispatchBehaviour

		# Hide bits of the dispatcher UIs that don't make sense in this context.
		for dispatcher in self.__dispatchers :
			Gaffer.Metadata.registerValue( dispatcher, "layout:customWidget:dispatchButton:visibilityActivator", False )
			Gaffer.Metadata.registerValue( dispatcher["dispatcher"], "layout:visibilityActivator", False )
			Gaffer.Metadata.registerValue( dispatcher["user"], "layout:visibilityActivator", False )

		# build tabs for all the node, dispatcher, and context settings
		with GafferUI.ListContainer() as self.__settings :

			mainMenu = GafferUI.MenuBar( self.menuDefinition() )
			mainMenu.setVisible( False )

			with GafferUI.TabbedContainer() as self.__tabs :

				for node in self.__nodesToShow :
					nodeFrame = GafferUI.Frame( borderStyle=GafferUI.Frame.BorderStyle.None_, borderWidth=0 )
					nodeFrame.addChild( self.__nodeEditor( node ) )
					# remove the per-node execute button
					Gaffer.Metadata.registerValue( node, "layout:customWidget:dispatchButton:widgetType", "", persistent = False )
					self.__tabs.setLabel( nodeFrame, node.relativeName( self.__script ) )

				with GafferUI.ListContainer() as dispatcherTab :

					with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=2, borderWidth=4 ) as dispatcherMenuColumn :
						GafferUI.Label( "<h4>Dispatcher</h4>" )
						self.__dispatchersMenu = GafferUI.MultiSelectionMenu( allowMultipleSelection = False, allowEmptySelection = False )
						self.__dispatchersMenu.append( [ x.getName() for x in self.__dispatchers ] )
						self.__dispatchersMenu.setSelection( [ self.__dispatchers[0].getName() ] )
						self.__dispatchersMenu.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__dispatcherChanged ) )
						dispatcherMenuColumn.setVisible( len(self.__dispatchers) > 1 )

					self.__dispatcherFrame = GafferUI.Frame( borderStyle=GafferUI.Frame.BorderStyle.None_, borderWidth=0 )
					self.__tabs.setLabel( dispatcherTab, "Dispatcher" )

				with GafferUI.Frame( borderStyle=GafferUI.Frame.BorderStyle.None_, borderWidth=4 ) as contextTab :
					GafferUI.PlugValueWidget.create( self.__script["variables"] )
					self.__tabs.setLabel( contextTab, "Context Variables" )

		# build a ui element for progress feedback and messages
		with GafferUI.ListContainer( spacing = 4 ) as self.__progressUI :

			with GafferUI.ListContainer( parenting = { "horizontalAlignment" : GafferUI.HorizontalAlignment.Center, "verticalAlignment" : GafferUI.VerticalAlignment.Center } ) :
				self.__progressIconFrame = GafferUI.Frame( borderStyle = GafferUI.Frame.BorderStyle.None_, parenting = { "horizontalAlignment" : GafferUI.HorizontalAlignment.Center } )
				self.__progressLabel = GafferUI.Label( parenting = { "horizontalAlignment" : GafferUI.HorizontalAlignment.Center } )

			with GafferUI.Collapsible( "Details", collapsed = True, parenting = { "expand" : True } ) as self.__messageCollapsible :
				self.__messageWidget = GafferUI.MessageWidget( toolbars = True )
				# connect to the collapsible state change so we can increase the window
				# size when the details pane is first shown.
				self.__messageCollapsibleConnection = self.__messageCollapsible.stateChangedSignal().connect( Gaffer.WeakMethod( self.__messageCollapsibleChanged ) )

		self.__backButton = self._addButton( "Back" )
		self.__backButton.clickedSignal().connectFront( Gaffer.WeakMethod( self.__initiateSettings ) )

		self.__primaryButton = self._addButton( "Dispatch" )

		self.__setDispatcher( dispatchers[0] )

		self.__initiateSettings( self.__primaryButton )

	@staticmethod
	def createWithDefaultDispatchers( tasks, nodesToShow, defaultDispatcherType=None, postDispatchBehaviour=PostDispatchBehaviour.Confirm, title="Dispatch Tasks", sizeMode=GafferUI.Window.SizeMode.Manual, **kw ) :

		defaultType = defaultDispatcherType if defaultDispatcherType else GafferDispatch.Dispatcher.getDefaultDispatcherType()
		dispatcherTypes = list(GafferDispatch.Dispatcher.registeredDispatchers())
		if defaultType and defaultType in dispatcherTypes :
			dispatcherTypes.remove( defaultType )
			dispatcherTypes.insert( 0, defaultType )

		dispatchers = []
		for key in dispatcherTypes :
			dispatcher = GafferDispatch.Dispatcher.create( key )
			Gaffer.NodeAlgo.applyUserDefaults( dispatcher )
			dispatchers.append( dispatcher )

		return DispatchDialogue( tasks, dispatchers, nodesToShow, postDispatchBehaviour=postDispatchBehaviour, title = title, sizeMode = sizeMode, **kw )

	def scriptNode( self ) :

		return self.__script

	def setVisible( self, visible ) :

		if visible :
			# See comment in `GafferUI.NodeSetEditor.acquire()`
			self._qtWidget().resize( 400, 400 )

		GafferUI.Window.setVisible( self, visible )

	## Returns an IECore.MenuDefinition which is used to define the keyboard shortcuts for all DispatchDialogues.
	# This can be edited at any time to modify subsequently created DispatchDialogues.
	# Typically editing would be done as part of gaffer startup. Note that this menu is never shown to users,
	# but we need it in order to register keyboard shortcuts.
	@classmethod
	def menuDefinition( cls ) :

		if cls.__dispatchDialogueMenuDefinition is None :
			cls.__dispatchDialogueMenuDefinition = IECore.MenuDefinition()

		return cls.__dispatchDialogueMenuDefinition

	def __nodeEditor( self, node ) :

		editor = GafferUI.NodeEditor( self.__script )
		editor.setNodeSet( Gaffer.StandardSet( [ node ] ) )
		## \todo: Expose public API for the NodeEditor's NameWidget visibility
		editor._NodeEditor__nameWidget.setVisible( False )
		editor._NodeEditor__nameWidget.parent()[0].setVisible( False )

		return editor

	def __setDispatcher( self, dispatcher ) :

		self.__currentDispatcher = dispatcher
		self.__dispatcherFrame.setChild( self.__nodeEditor( self.__currentDispatcher ) )

	def __dispatcherChanged( self, menu ) :

		for dispatcher in self.__dispatchers :
			if dispatcher.getName() == menu.getSelection()[0] :
				self.__setDispatcher( dispatcher )
				return

	def __initiateSettings( self, button ) :

		self.__backButton.setEnabled( False )
		self.__backButton.setVisible( False )

		self.__primaryButton.setText( "Dispatch" )
		self.__primaryButton.setEnabled( True )
		self.__primaryButton.setVisible( True )
		self.__primaryButtonConnection = self.__primaryButton.clickedSignal().connectFront( Gaffer.WeakMethod( self.__initiateDispatch ), scoped = True )

		self.__tabs.setCurrent( self.__tabs[0] )
		self._getWidget().setChild( self.__settings )

	def __initiateDispatch( self, button ) :

		self.__progressIconFrame.setChild( GafferUI.BusyWidget() )
		self.__progressLabel.setText( "<h3>Dispatching...</h3>" )

		self.__backButton.setVisible( False )
		self.__backButton.setEnabled( False )

		self.__primaryButton.setVisible( False )
		self.__primaryButton.setEnabled( False )

		self.__messageWidget.clear()
		self.__messageCollapsible.setCollapsed( True )

		self._getWidget().setChild( self.__progressUI )

		threading.Thread( target = self.__dispatch ).start()

	def __dispatch( self ) :

		try :

			with self.__messageWidget.messageHandler() :
				with self.__script.context() :
					self.__currentDispatcher.dispatch( self.__tasks )
					result = 0

		except Exception as e :

			result = sys.exc_info()

		GafferUI.EventLoop.executeOnUIThread( functools.partial( self.__finish, result ) )

	def __finish( self, result ) :

		if result == 0 :
			self.__initiateResultDisplay()
		else :
			self.__initiateErrorDisplay( result )

	def __initiateErrorDisplay( self, exceptionInfo ) :

		self.__progressIconFrame.setChild( GafferUI.Image( "failure.png" ) )
		self.__progressLabel.setText( "<h3>Failed</h3>" )

		self.__messageCollapsible.setCollapsed( False )

		self.__messageWidget.messageHandler().handle(
			IECore.Msg.Level.Debug,
			"Python Traceback",
			"".join( traceback.format_exception( *exceptionInfo ) )
		)

		excType, excValue, excTrace = exceptionInfo
		if excValue and hasattr( excValue, "message" ) and excValue.message :
			userFriendlyException = excValue.message.strip( "\n" ).split( "\n" )[-1]
		else:
			userFriendlyException = str( excType.__name__ )
		userFriendlyException += "\nSee DEBUG messages for more information."
		self.__messageWidget.messageHandler().handle(
			IECore.Msg.Level.Error,
			"Problem Dispatching {nodes}".format( nodes = str( [ task.relativeName( self.__script ) for task in self.__tasks ] ) ),
			userFriendlyException,
		)

		self.__backButton.setEnabled( True )
		self.__backButton.setVisible( True )
		self.__backButton._qtWidget().setFocus()

		self.__primaryButton.setText( "Quit" )
		self.__primaryButton.setEnabled( True )
		self.__primaryButton.setVisible( True )
		self.__primaryButtonConnection = self.__primaryButton.clickedSignal().connect( Gaffer.WeakMethod( self.__close ), scoped = True )

	def __initiateResultDisplay( self ) :

		# Although we computed a result successfully, there may still be minor problems
		# indicated by messages emitted - check for those.
		problems = []
		for level in ( IECore.Msg.Level.Error, IECore.Msg.Level.Warning ) :
			count = self.__messageWidget.messageCount( level )
			if count :
				problems.append( "%d %s%s" % ( count, IECore.Msg.levelAsString( level ).capitalize(), "s" if count > 1 else "" ) )

		if not problems and self.__postDispatchBehaviour == self.PostDispatchBehaviour.Close :
			self.close()
			return

		self.__progressIconFrame.setChild(
			GafferUI.Image( "successWarning.png" if problems else "success.png" )
		)

		completionMessage = "Completed"
		if problems :
			completionMessage += " with " + " and ".join( problems )
			self.__messageCollapsible.setCollapsed( False )

		self.__progressLabel.setText( "<h3>" + completionMessage + "</h3>" )

		self.__messageCollapsible.setVisible( self.__messageWidget.messageCount() )

		self.__backButton.setEnabled( True )
		self.__backButton.setVisible( True )

		self.__primaryButton.setText( "Close" )
		self.__primaryButton.setEnabled( True )
		self.__primaryButton.setVisible( True )
		self.__primaryButtonConnection = self.__primaryButton.clickedSignal().connect( Gaffer.WeakMethod( self.__close ), scoped = True )
		self.__primaryButton._qtWidget().setFocus()

	def __close( self, *unused ) :

		self.close()

	def __messageCollapsibleChanged( self, collapsible ) :

		if not collapsible.getCollapsed() :
			# make the window bigger to better fit the messages, but don't make
			# it any smaller than it currently is.
			self.resizeToFitChild( shrink = False )
			# remove our connection - we only want to resize the first time we
			# show the messages. after this we assume that if the window is smaller
			# it is because the user has made it so, and wishes it to remain so.
			self.__messageCollapsibleConnection.disconnect()
