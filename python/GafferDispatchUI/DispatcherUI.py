##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferUI
import GafferDispatch

from Qt import QtCore

Gaffer.Metadata.registerNode(

	GafferDispatch.Dispatcher,

	"description",
	"""
	Used to schedule the execution of a network
	of TaskNodes.
	""",

	"layout:activator:framesModeIsCustomRange", lambda node : node["framesMode"].getValue() == GafferDispatch.Dispatcher.FramesMode.CustomRange,

	plugs = {

		"user" : (

			"plugValueWidget:type", "",

		),

		"framesMode" : (

			"description",
			"""
			Determines the active frame range to be dispatched as
			follows :

			  - CurrentFrame uses the current timeline frame only.
			  - FullRange uses the outer handles of the timeline
			    (i.e. the full range of the script).
			  - CustomRange uses a user defined range, as specified by
			    the frameRange plug.
			""",

			"preset:Current Frame", GafferDispatch.Dispatcher.FramesMode.CurrentFrame,
			"preset:Full Range", GafferDispatch.Dispatcher.FramesMode.FullRange,
			"preset:Custom Range", GafferDispatch.Dispatcher.FramesMode.CustomRange,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		),

		"frameRange" : (

			"description",
			"""
			The frame range to be used when framesMode is "CustomRange".
			""",

			"layout:visibilityActivator", "framesModeIsCustomRange",

		),

		"jobName" : (

			"description",
			"""
			A descriptive name for the job.
			"""

		),

		"jobsDirectory" : (

			"description",
			"""
			A directory to store temporary files used by the dispatcher.
			""",

			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"path:leaf", False,

		),

	}

)

##########################################################################
# Additional Metadata for TaskNode
##########################################################################

Gaffer.Metadata.registerNode(

	GafferDispatch.TaskNode,

	"layout:customWidget:dispatchButton:widgetType", "GafferDispatchUI.DispatcherUI._DispatchButton",

	plugs = {

		"dispatcher.batchSize" : (

			"description",
			"""
			Maximum number of frames to batch together when dispatching tasks.
			""",

		),

		"dispatcher.immediate" : (

			"description",
			"""
			Causes this node to be executed immediately upon dispatch,
			rather than have its execution be scheduled normally by
			the dispatcher. For instance, when using the LocalDispatcher,
			the node will be executed immediately in the dispatching process
			and not in a background process as usual.

			When a node is made immediate, all upstream nodes are automatically
			considered to be immediate too, regardless of their settings.
			"""

		)

	}

)

##########################################################################
# Public functions
##########################################################################

def appendMenuDefinitions( menuDefinition, prefix="" ) :

	menuDefinition.append( prefix + "/Execute Selected", { "command" : executeSelected, "shortCut" : "Ctrl+E", "active" : selectionAvailable } )
	menuDefinition.append( prefix + "/Repeat Previous", { "command" : repeatPrevious, "shortCut" : "Ctrl+R", "active" : previousAvailable } )

def appendNodeContextMenuDefinitions( graphEditor, node, menuDefinition ) :

	if not hasattr( node, "execute" ) :
		return

	menuDefinition.append( "/ExecuteDivider", { "divider" : True } )
	menuDefinition.append( "/Execute", { "command" : functools.partial( _showDispatcherWindow, [ node ] ) } )

def executeSelected( menu ) :
	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	_showDispatcherWindow( selectedNodes( script ) )

def repeatPrevious( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	_dispatch( __previous( script ) )

##################################################################################
# Dispatcher Window
##################################################################################

class DispatcherWindow( GafferUI.Window ) :

	def __init__( self, **kw ) :

		GafferUI.Window.__init__( self, **kw )

		self.__dispatchers = {}
		for dispatcherType in GafferDispatch.Dispatcher.registeredDispatchers() :
			dispatcher = GafferDispatch.Dispatcher.create( dispatcherType )
			Gaffer.NodeAlgo.applyUserDefaults( dispatcher )
			self.__dispatchers[dispatcherType] = dispatcher

		defaultType = GafferDispatch.Dispatcher.getDefaultDispatcherType()
		self.__currentDispatcher = self.__dispatchers[ defaultType ]
		self.__nodes = []

		with self :

			with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Vertical, spacing = 2, borderWidth = 6 ) :

				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
					GafferUI.Label( "Dispatcher" )
					self.__dispatchersMenu = GafferUI.MultiSelectionMenu( allowMultipleSelection = False, allowEmptySelection = False )
					self.__dispatchersMenu.append( list( self.__dispatchers.keys() ) )
					self.__dispatchersMenu.setSelection( [ defaultType ] )
					self.__dispatchersMenu.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__dispatcherChanged ), scoped = False )

				self.__frame = GafferUI.Frame( borderStyle=GafferUI.Frame.BorderStyle.None_, borderWidth=0 )
				self.__dispatchButton = GafferUI.Button( "Dispatch" )
				self.__dispatchButton.clickedSignal().connect( Gaffer.WeakMethod( self.__dispatchClicked ), scoped = False )

		self.__update( resizeToFit = True )

	def setVisible( self, visible ) :

		GafferUI.Window.setVisible( self, visible )

		if visible :
			self.__dispatchButton._qtWidget().setFocus( QtCore.Qt.OtherFocusReason )

	def addDispatcher( self, label, dispatcher ) :

		if label not in self.__dispatchers.keys() :
			self.__dispatchersMenu.append( label )

		self.__dispatchers[label] = dispatcher

	def removeDispatcher( self, label ) :

		if label in self.__dispatchers.keys() :
			toRemove = self.__dispatchers.get( label, None )
			if toRemove and self.__currentDispatcher.isSame( toRemove ) :
				if len(self.__dispatchers.items()) < 2 :
					raise RuntimeError( "DispatcherWindow: " + label + " is the only dispatcher, so it cannot be removed." )
				self.setCurrentDispatcher( self.__dispatchers.values()[0] )

			del self.__dispatchers[label]
			self.__dispatchersMenu.remove( label )

	def dispatcher( self, label ) :

		return self.__dispatchers.get( label, None )

	def getCurrentDispatcher( self ) :

		return self.__currentDispatcher

	def setCurrentDispatcher( self, dispatcher ) :

		dispatcherLabel = ""
		for label, d in self.__dispatchers.items() :
			if d.isSame( dispatcher ) :
				dispatcherLabel = label
				break

		if not dispatcherLabel :
			raise RuntimeError( "DispatcherWindow: The current dispatcher must be added first. Use DispatcherWindow.addDispatcher( label, dispatcher )" )

		self.__currentDispatcher = dispatcher
		self.__dispatchersMenu.setSelection( [ dispatcherLabel ] )
		self.__update()

	def setNodesToDispatch( self, nodes ) :

		self.__nodes = nodes
		self.__updateTitle()

	## Acquires the DispatcherWindow for the specified application.
	@staticmethod
	def acquire( applicationOrApplicationRoot ) :

		if isinstance( applicationOrApplicationRoot, Gaffer.Application ) :
			applicationRoot = applicationOrApplicationRoot.root()
		else :
			assert( isinstance( applicationOrApplicationRoot, Gaffer.ApplicationRoot ) )
			applicationRoot = applicationOrApplicationRoot

		window = getattr( applicationRoot, "_dispatcherWindow", None )
		if window is not None and window() :
			return window()

		window = DispatcherWindow()

		applicationRoot._dispatcherWindow = weakref.ref( window )

		return window

	def __update( self, resizeToFit = False ) :

		nodeUI = GafferUI.NodeUI.create( self.__currentDispatcher )
		self.__frame.setChild( nodeUI )
		self.__updateTitle()

		if resizeToFit :
			self.resizeToFitChild()

	def __updateTitle( self ) :

		title = "Dispatching"
		if len(self.__nodes) :
			title += ": " + ", ".join( [ x.getName() for x in self.__nodes ] )

		self.setTitle( title )

	def __dispatchClicked( self, button ) :

		if _dispatch( self.__nodes ) :
			self.close()

	def __dispatcherChanged( self, menu ) :

		self.__currentDispatcher = self.__dispatchers[ menu.getSelection()[0] ]
		self.__update()

##################################################################################
# Button for dispatching - this forms the header for the TaskNode ui.
##################################################################################

class _DispatchButton( GafferUI.Button ) :

	def __init__( self, node, **kw ) :

		GafferUI.Button.__init__( self, "Execute", **kw )

		self.__node = node
		self.clickedSignal().connect( Gaffer.WeakMethod( self.__clicked ), scoped = False )

	def __clicked( self, button ) :

		_showDispatcherWindow( [ self.__node ] )

##########################################################################
# Implementation Details
##########################################################################

def _dispatch( nodes ) :

	script = nodes[0].scriptNode()
	with script.context() :
		success = False
		with GafferUI.ErrorDialogue.ErrorHandler( title = "Dispatch Error" ) :
			__dispatcherWindow( script ).getCurrentDispatcher().dispatch( nodes )
			success = True

	if success :
		scriptWindow = GafferUI.ScriptWindow.acquire( script )
		scriptWindow._lastDispatch = [ weakref.ref( node ) for node in nodes ]

	return success

def __dispatcherWindow( script ) :

	window = DispatcherWindow.acquire( script.applicationRoot() )
	scriptWindow = GafferUI.ScriptWindow.acquire( script )
	scriptWindow.addChildWindow( window )

	return window

def _showDispatcherWindow( nodes ) :

	window = __dispatcherWindow( nodes[0].scriptNode() )
	window.setNodesToDispatch( nodes )
	window.setVisible( True )

def selectedNodes( script ) :
	result = []
	for n in script.selection() :
		if isinstance( n, GafferDispatch.TaskNode ) :
			result.append( n )
		elif isinstance( n, Gaffer.SubGraph ) :
			for p in GafferDispatch.TaskNode.TaskPlug.RecursiveOutputRange( n ) :
				if isinstance( p.source().node(), GafferDispatch.TaskNode ) :
					result.append( n )
					break

	return result

def selectionAvailable( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	return bool( selectedNodes( script ) )

def __previous( script ) :

	scriptWindow = GafferUI.ScriptWindow.acquire( script )
	nodes = getattr( scriptWindow, "_lastDispatch", [] )
	return [ w() for w in nodes if w() is not None and script.isSame( w().scriptNode() ) ]

def previousAvailable( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	return bool( __previous( script ) )
