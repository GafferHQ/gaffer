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

import functools
import sys
import threading
import traceback

import imath

import IECore

import Gaffer
import GafferDispatch

import GafferUI

## A dialogue which can be used to dispatch tasks
class DispatchDialogue( GafferUI.Dialogue ) :

	def __init__( self, script, tasks, dispatcherType, applyUserDefaults=False, title="Dispatch Tasks", sizeMode=GafferUI.Window.SizeMode.Manual, **kw ) :

		GafferUI.Dialogue.__init__( self, title, sizeMode=sizeMode, **kw )

		self._getWidget().setBorderStyle( GafferUI.Frame.BorderStyle.None )

		# build tabs for all the node, dispatcher, and context settings
		with GafferUI.ListContainer() as self.__settings :

			mainMenu = GafferUI.MenuBar( self.menuDefinition( script.applicationRoot() ) )
			mainMenu.setVisible( False )

			with GafferUI.TabbedContainer() as self.__tabs :

				with GafferUI.ListContainer( borderWidth=3 ) as dispatcherTab :
					with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=2, borderWidth=2 ) :
						GafferUI.Label( "<h4>Current Dispatcher</h4>" )
						self.__dispatchersMenu = GafferUI.MultiSelectionMenu( allowMultipleSelection = False, allowEmptySelection = False )
						self.__dispatchersMenu.append( list(GafferDispatch.Dispatcher.registeredDispatchers()) )
						self.__dispatchersMenu.setSelection( [ dispatcherType ] )
						self.__dispatchersMenuChanged = self.__dispatchersMenu.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__dispatcherChanged ) )

					self.__dispatcherFrame = GafferUI.Frame( borderWidth=2 )
					self.__tabs.setLabel( dispatcherTab, "Dispatcher" )

				with GafferUI.Frame( borderStyle=GafferUI.Frame.BorderStyle.None, borderWidth=2 ) as contextTab :
					GafferUI.PlugValueWidget.create( script["variables"] )
					self.__tabs.setLabel( contextTab, "Context Variables" )

		# build a ui element for progress feedback and messages
		with GafferUI.ListContainer( spacing = 4 ) as self.__progressUI :

			with GafferUI.ListContainer( parenting = { "horizontalAlignment" : GafferUI.HorizontalAlignment.Center, "verticalAlignment" : GafferUI.VerticalAlignment.Center } ) :
				self.__progressIconFrame = GafferUI.Frame( borderStyle = GafferUI.Frame.BorderStyle.None, parenting = { "horizontalAlignment" : GafferUI.HorizontalAlignment.Center } )
				self.__progressLabel = GafferUI.Label( parenting = { "horizontalAlignment" : GafferUI.HorizontalAlignment.Center } )

			with GafferUI.Collapsible( "Details", collapsed = True, parenting = { "expand" : True } ) as self.__messageCollapsible :
				self.__messageWidget = GafferUI.MessageWidget()
				# connect to the collapsible state change so we can increase the window
				# size when the details pane is first shown.
				self.__messageCollapsibleConneciton = self.__messageCollapsible.stateChangedSignal().connect( Gaffer.WeakMethod( self.__messageCollapsibleChanged ) )

		self.__button = self._addButton( "Dispatch" )

		self.__script = script
		# hold a reference to the script window so plugs which launch child windows work properly
		self.__scriptWindow = GafferUI.ScriptWindow.acquire( script )

		self.__applyUserDefaults = applyUserDefaults
		self.__dispatchers = {}
		self.setDispatcher( dispatcherType )
		self.setTasks( tasks )

		self.__initiateSettings( self.__button )

	def __initiateSettings( self, button ) :

		button.setText( "Dispatch" )
		self.__buttonConnection = button.clickedSignal().connect( 0, Gaffer.WeakMethod( self.__initiateDispatch ) )
		self.__tabs.setCurrent( self.__tabs[0] )
		self._getWidget().setChild( self.__settings )

	def setTasks( self, tasks ) :

		self.__tasks = tasks

		# remove the task tabs but leave the dispatcher and context variables
		del self.__tabs[:-2]

		for task in reversed( self.__tasks ) :
			editor = self.__nodeEditor( task )
			# remove the per-node execute button
			Gaffer.Metadata.registerValue( task, "layout:customWidget:dispatchButton:widgetType", "", persistent = False )
			self.__tabs.insert( 0, editor, label = task.relativeName( self.__script ) )

	def setDispatcher( self, dispatcherType ) :

		if dispatcherType not in self.__dispatchers.keys() :
			self.__dispatchers[dispatcherType] = GafferDispatch.Dispatcher.create( dispatcherType )
			if self.__applyUserDefaults :
				Gaffer.NodeAlgo.applyUserDefaults( self.__dispatchers[dispatcherType] )

		self.__currentDispatcher = self.__dispatchers[dispatcherType]
		self.__dispatcherFrame.setChild( self.__nodeEditor( self.__currentDispatcher ) )

	def getDispatcher( self ) :

		return self.__currentDispatcher

	def scriptNode( self ) :

		return self.__script

	def setVisible( self, visible ) :

		if visible :
			# See comment in `GafferUI.NodeSetEditor.acquire()`
			self._qtWidget().resize( 400, 400 )

		GafferUI.Window.setVisible( self, visible )

	## Returns an IECore.MenuDefinition which is used to define the keyboard shortcuts for all DispatchDialogues
	# created as part of the specified application. This can be edited at any time to modify subsequently
	# created DispatchDialogues - typically editing would be done as part of gaffer startup. Note that
	# this menu is never shown to users, but we need it in order to register keyboard shortcuts.
	@staticmethod
	def menuDefinition( applicationOrApplicationRoot ) :

		if isinstance( applicationOrApplicationRoot, Gaffer.Application ) :
			applicationRoot = applicationOrApplicationRoot.root()
		else :
			assert( isinstance( applicationOrApplicationRoot, Gaffer.ApplicationRoot ) )
			applicationRoot = applicationOrApplicationRoot

		menuDefinition = getattr( applicationRoot, "_dispatchDialogueMenuDefinition", None )
		if menuDefinition :
			return menuDefinition

		menuDefinition = IECore.MenuDefinition()
		applicationRoot._dispatchDialogueMenuDefinition = menuDefinition

		return menuDefinition

	def __nodeEditor( self, node ) :

		editor = GafferUI.NodeEditor( self.__script )
		editor.setNodeSet( Gaffer.StandardSet( [ node ] ) )
		## \todo: Expose public API for the NodeEditor's NameWidget visibility
		editor._NodeEditor__nameWidget.setVisible( False )
		editor._NodeEditor__nameWidget.parent()[0].setVisible( False )

		return editor

	def __dispatcherChanged( self, menu ) :

		self.setDispatcher( menu.getSelection()[0] )

	def __initiateDispatch( self, button ) :

		self.__progressIconFrame.setChild( GafferUI.BusyWidget() )
		self.__progressLabel.setText( "<h3>Dispatching...</h3>" )

		self.__button.setVisible( False )
		self.__button.setEnabled( False )
		self.__buttonConnection = None

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

		except Exception, e :

			result = sys.exc_info()

		GafferUI.EventLoop.executeOnUIThread( functools.partial( self.__finish, result ) )

	def __finish( self, result ) :

		if result == 0 :
			self.__initiateResultDisplay( result )
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

		# this works for RuntimeError, but is this safe for all exceptions?
		userFriendlyException = exceptionInfo[1].args[0].strip( "\n" ).split( "\n" )[-1]
		userFriendlyException += "\nSee DEBUG messages for more information."
		self.__messageWidget.messageHandler().handle(
			IECore.Msg.Level.Error,
			"Problem Dispatching {nodes}".format( nodes = str( [ task.relativeName( self.__script ) for task in self.__tasks ] ) ),
			userFriendlyException,
		)

		self.__button.setText( "Retry" )
		self.__button.setEnabled( True )
		self.__button.setVisible( True )
		self.__buttonConnection = self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.__initiateSettings ) )
		self.__button._qtWidget().setFocus()

	def __initiateResultDisplay( self, result ) :

		# Although we computed a result successfully, there may still be minor problems
		# indicated by messages emitted - check for those.
		problems = []
		for level in ( IECore.Msg.Level.Error, IECore.Msg.Level.Warning ) :
			count = self.__messageWidget.messageCount( level )
			if count :
				problems.append( "%d %s%s" % ( count, IECore.Msg.levelAsString( level ).capitalize(), "s" if count > 1 else "" ) )

		if not problems :
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

		self.__messageWidget.messageHandler().handle( IECore.Msg.Level.Info, "Result", str( result ) )

		self.__button.setText( "Ok" )
		self.__button.setEnabled( True )
		self.__button.setVisible( True )
		self.__buttonClickedConnection = self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.close ) )
		self.__button._qtWidget().setFocus()

	def __messageCollapsibleChanged( self, collapsible ) :

		if not collapsible.getCollapsed() :
			# make the window bigger to better fit the messages, but don't make
			# it any smaller than it currently is.
			self.resizeToFitChild( shrink = False )
			# remove our connection - we only want to resize the first time we
			# show the messages. after this we assume that if the window is smaller
			# it is because the user has made it so, and wishes it to remain so.
			self.__messageCollapsibleConneciton = None
