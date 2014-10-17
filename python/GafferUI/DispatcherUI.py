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

import fnmatch
import weakref

import IECore

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )

##########################################################################
# Public functions
##########################################################################

def appendMenuDefinitions( menuDefinition, prefix="" ) :

	menuDefinition.append( prefix + "/Execute Selected", { "command" : executeSelected, "shortCut" : "Ctrl+E", "active" : __selectionAvailable } )
	menuDefinition.append( prefix + "/Repeat Previous", { "command" : repeatPrevious, "shortCut" : "Ctrl+R", "active" : __previousAvailable } )

def appendNodeContextMenuDefinitions( nodeGraph, node, menuDefinition ) :

	if not hasattr( node, "execute" ) :
		return

	menuDefinition.append( "/ExecuteDivider", { "divider" : True } )
	menuDefinition.append( "/Execute", { "command" : IECore.curry( _showDispatcherWindow, [ node ] ) } )

def executeSelected( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	_showDispatcherWindow( __selectedNodes( script ) )

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
		for dispatcherType in Gaffer.Dispatcher.registeredDispatchers() :
			dispatcher = Gaffer.Dispatcher.create( dispatcherType )
			Gaffer.NodeAlgo.applyUserDefaults( dispatcher )
			self.__dispatchers[dispatcherType] = dispatcher
		
		self.__currentDispatcher = self.__dispatchers["Local"]
		self.__nodes = []

		with self :

			with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Vertical, spacing = 2, borderWidth = 4 ) :

				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
					GafferUI.Label( "Dispatcher" )
					self.__dispatchersMenu = GafferUI.MultiSelectionMenu( allowMultipleSelection = False, allowEmptySelection = False )
					self.__dispatchersMenu.append( self.__dispatchers.keys() )
					self.__dispatchersMenu.setSelection( [ "Local" ] )
					self.__dispatchersMenuSelectionChangedConnection = self.__dispatchersMenu.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__dispatcherChanged ) )

				self.__frame = GafferUI.Frame( borderStyle=GafferUI.Frame.BorderStyle.None, borderWidth=0 )
				self.__dispatchButton = GafferUI.Button( "Dispatch" )
				self.__dispatchClickedConnection = self.__dispatchButton.clickedSignal().connect( Gaffer.WeakMethod( self.__dispatchClicked ) )

		self.__update()

	def setVisible( self, visible ) :

		GafferUI.Window.setVisible( self, visible )

		if visible :
			self.__dispatchButton._qtWidget().setFocus( QtCore.Qt.OtherFocusReason )

	def getDispatcher( self, dispatcherType ) :

		return self.__dispatchers.get( dispatcherType, None )

	def setDispatcher( self, dispatcherType, dispatcher ) :
		
		if dispatcherType not in self.__dispatchers.keys() :
			self.__dispatchersMenu.append( dispatcherType )
		
		self.__currentDispatcher = dispatcher
		self.__dispatchers[dispatcherType] = dispatcher
		
		self.__dispatchersMenu.setSelection( [ dispatcherType ] )
		self.__update()
	
	def currentDispatcher( self ) :
		
		return self.__currentDispatcher
	
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
		if window :
			return window
		
		window = DispatcherWindow()
		applicationRoot._dispatcherWindow = window
		
		return window
	
	def __update( self ) :
		
		nodeUI = GafferUI.NodeUI.create( self.__currentDispatcher )
		self.__frame.setChild( nodeUI )
		self.__updateTitle()

	def __updateTitle( self ) :

		title = "Dispatching"
		if len(self.__nodes) :
			title += ": " + ", ".join( [ x.getName() for x in self.__nodes ] )

		self.setTitle( title )

	def __dispatchClicked( self, button ) :

		_dispatch( self.__nodes )
		self.close()

	def __dispatcherChanged( self, menu ) :

		self.__currentDispatcher = self.__dispatchers[ menu.getSelection()[0] ]
		self.__update()

##################################################################################
# PlugValueWidget for execution - this forms the header for the ExecutableNode ui.
##################################################################################

class __RequirementPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.PlugValueWidget.__init__( self, row, plug, **kw )

		with row :

			executeButton = GafferUI.Button( "Execute" )
			executeButton.setToolTip( "Execute" )
			self.__executeClickedConnection = executeButton.clickedSignal().connect( Gaffer.WeakMethod( self.__executeClicked ) )

	def hasLabel( self ) :

		return True

	def _updateFromPlug( self ) :

		pass

	def __executeClicked( self, button ) :

		_showDispatcherWindow( [ self.getPlug().node() ] )


########################################
# PlugValueWidgets for frame range plugs
########################################

# Much of this is copied from EnumPlugValueWidget, but we're not deriving because we
# want the ability to add in menu items that don't correspond to plug values directly.
class __FramesModePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :
		
		self.__selectionMenu = GafferUI.MultiSelectionMenu( allowMultipleSelection = False, allowEmptySelection = False )
		GafferUI.PlugValueWidget.__init__( self, self.__selectionMenu, plug, **kw )
		
		self.__labelsAndValues = (
			( "CurrentFrame", Gaffer.Dispatcher.FramesMode.CurrentFrame ),
			( "FullRange", Gaffer.Dispatcher.FramesMode.FullRange ),
			( "PlaybackRange", Gaffer.Dispatcher.FramesMode.CustomRange ),
			( "CustomRange", Gaffer.Dispatcher.FramesMode.CustomRange ),
		)
		
		for label, value in self.__labelsAndValues :
			self.__selectionMenu.append( label )
		
		self.__updateFrameRangeConnection = None
		self.__visibilityChangedConnection = self.visibilityChangedSignal().connect( Gaffer.WeakMethod( self.__visibilityChanged ) )
		self.__selectionChangedConnection = self.__selectionMenu.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__selectionChanged ) )
		
		self._addPopupMenu( self.__selectionMenu )
		
		# save the metadata in case the frameRange plug is set prior to enabling CustomRange mode
		self.__customFrameRangeChanged( self.getPlug().node()["frameRange"] )
		
		self._updateFromPlug()
	
	def selectionMenu( self ) :

		return self.__selectionMenu

	def _updateFromPlug( self ) :
		
		self.__selectionMenu.setEnabled( self._editable() )
		
		if self.getPlug() is None :
			return
		
		with self.getContext() :
			plugValue = self.getPlug().getValue()
		
		for labelAndValue in self.__labelsAndValues :
			if labelAndValue[1] == plugValue :
				with Gaffer.BlockedConnection( self.__selectionChangedConnection ) :
					self.__selectionMenu.setSelection( labelAndValue[0] )
				break
	
	def __frameRangeWidget( self ) :
		
		nodeUI = self.ancestor( GafferUI.NodeUI )
		if nodeUI :
			return nodeUI.plugValueWidget( self.getPlug().node()["frameRange"], lazy = False )
		
		return None
	
	def __selectionChanged( self, selectionMenu ) :
		
		label = selectionMenu.getSelection()[0]
		value = self.__labelsAndValues[ selectionMenu.index( label ) ][1]
		
		with Gaffer.BlockedConnection( self._plugConnections() ) :
			self.getPlug().setValue( value )
		
		frameRangeWidget = self.__frameRangeWidget()
		if frameRangeWidget :
			## \todo: This should be managed by activator metadata once we've ported
			# that functionality out of RenderManShaderUI and into PlugLayout.
			frameRangeWidget.setReadOnly( label in [ "CurrentFrame", "FullRange", "PlaybackRange" ] )
		
		self.__updateFrameRangeConnection = None
		
		window = self.ancestor( GafferUI.ScriptWindow )
		if not window :
			return
		
		script = window.scriptNode()
		context = script.context()
		
		if label == "CurrentFrame" :
			self.__updateFrameRangeConnection = context.changedSignal().connect( Gaffer.WeakMethod( self.__contextChanged ) )
			self.__contextChanged( context, "frame" )
		elif label == "FullRange" :
			self.__updateFrameRangeConnection = script.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__scriptPlugDirtied ) )
			self.__scriptPlugDirtied( script["frameRange"] )
		elif label == "PlaybackRange" :
			playback = GafferUI.Playback.acquire( context )
			self.__updateFrameRangeConnection = playback.frameRangeChangedSignal().connect( Gaffer.WeakMethod( self.__playbackFrameRangeChanged ) )
			self.__playbackFrameRangeChanged( playback )
		else :
			frameRange = Gaffer.Metadata.plugValue( self.getPlug(), "dispatcherWindow:frameRange", inherit=False )
			if frameRange is not None :
				self.getPlug().node()["frameRange"].setValue( frameRange )
			self.__updateFrameRangeConnection = self.getPlug().node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__customFrameRangeChanged ) )
	
	def __visibilityChanged( self, widget ) :
		
		if self.visible() :
			self.__selectionChanged( self.__selectionMenu )
		else :
			self.__updateFrameRangeConnection = None
	
	def __contextChanged( self, context, key ) :
		
		if key == "frame" :
			frameRangeWidget = self.__frameRangeWidget()
			if frameRangeWidget :
				frameRangeWidget.textWidget().setText( str(int(context.getFrame())) )
	
	def __playbackFrameRangeChanged( self, playback ) :
		
		frameRange = playback.getFrameRange()
		frameRange = str(IECore.frameListFromList( range(frameRange[0], frameRange[1]+1) ))
		self.getPlug().node()["frameRange"].setValue( frameRange )
	
	def __scriptPlugDirtied( self, plug ) :
		
		script = plug.ancestor( Gaffer.ScriptNode )
		if script and plug.isSame( script["frameRange"] ) or plug.parent().isSame( script["frameRange"] ) :
			frameRangeWidget = self.__frameRangeWidget()
			if frameRangeWidget :
				frameRangeWidget.textWidget().setText( str(IECore.FrameRange( script["frameRange"]["start"].getValue(), script["frameRange"]["end"].getValue() )) )
	
	def __customFrameRangeChanged( self, plug ) :
		
		if plug.isSame( self.getPlug().node()["frameRange"] ) :
			with self.getContext() :
				Gaffer.Metadata.registerPlugValue( self.getPlug(), "dispatcherWindow:frameRange", plug.getValue() )

class __FrameRangePlugValueWidget( GafferUI.StringPlugValueWidget ) :
	
	def _updateFromPlug( self ) :
		
		with self.getContext() :
			framesMode = self.getPlug().node()["framesMode"].getValue()
		
		# we need to disable the normal update in CurrentFrame and FullRange modes
		if framesMode == Gaffer.Dispatcher.FramesMode.CustomRange :
			GafferUI.StringPlugValueWidget._updateFromPlug( self )
		
		self.textWidget().setEditable( self._editable() )

##########################################################################
# Metadata, PlugValueWidgets and Nodules
##########################################################################

Gaffer.Metadata.registerPlugValue( Gaffer.ExecutableNode, "requirement", "nodeUI:section", "header" )
Gaffer.Metadata.registerPlugValue( Gaffer.ExecutableNode, "dispatcher", "nodeUI:section", "Dispatcher" )
Gaffer.Metadata.registerPlugDescription( Gaffer.ExecutableNode, "dispatcher.batchSize", "Maximum number of frames to batch together when dispatching execution tasks." )

Gaffer.Metadata.registerPlugDescription( Gaffer.Dispatcher, "framesMode",
	"Determines the active frame range for dispatching. " +
	"\"CurrentFrame\" uses the current timeline frame only. " +
	"\"FullRange\" uses the outer handles of the timeline (i.e. the full range of the script). " +
	"\"CustomRange\" uses a user defined range, as specified by the string plug below."
)
Gaffer.Metadata.registerPlugDescription( Gaffer.Dispatcher, "frameRange", "The frame range to be used when framesMode is set to \"CustomRange\"." )
Gaffer.Metadata.registerPlugDescription( Gaffer.Dispatcher, "jobsDirectory", "A directory to store temporary files used by the dispatcher." )

GafferUI.PlugValueWidget.registerCreator(
	Gaffer.Dispatcher,
	"jobsDirectory",
	lambda plug : GafferUI.PathPlugValueWidget( plug,
		path = Gaffer.FileSystemPath( "/", filter = Gaffer.FileSystemPath.createStandardFilter( [ "gfr" ] ) ),
		pathChooserDialogueKeywords = {
			"leaf" : False,
		},
	)
)

GafferUI.PlugValueWidget.registerCreator( Gaffer.Dispatcher, "user", None )
GafferUI.PlugValueWidget.registerCreator( Gaffer.Dispatcher, "framesMode", __FramesModePlugValueWidget )
GafferUI.PlugValueWidget.registerCreator( Gaffer.Dispatcher, "frameRange", __FrameRangePlugValueWidget )
GafferUI.PlugValueWidget.registerCreator( Gaffer.ExecutableNode, "requirement", __RequirementPlugValueWidget )
GafferUI.PlugValueWidget.registerCreator( Gaffer.ExecutableNode, "dispatcher", GafferUI.CompoundPlugValueWidget, collapsed = None )

GafferUI.Nodule.registerNodule( Gaffer.Dispatcher, fnmatch.translate( "*" ), lambda plug : None )
GafferUI.Nodule.registerNodule( Gaffer.ExecutableNode, "dispatcher", lambda plug : None )

##########################################################################
# Implementation Details
##########################################################################

def _dispatch( nodes ) :

	script = nodes[0].scriptNode()
	with script.context() :
		__dispatcherWindow( script ).currentDispatcher().dispatch( nodes )

	scriptWindow = GafferUI.ScriptWindow.acquire( script )
	scriptWindow._lastDispatch = [ weakref.ref( node ) for node in nodes ]

def __dispatcherWindow( script ) :
	
	window = DispatcherWindow.acquire( script.applicationRoot() )
	scriptWindow = GafferUI.ScriptWindow.acquire( script )
	scriptWindow.addChildWindow( window )
	
	return window

def _showDispatcherWindow( nodes ) :

	window = __dispatcherWindow( nodes[0].scriptNode() )
	window.setNodesToDispatch( nodes )
	window.setVisible( True )

def __selectedNodes( script ) :

	result = []
	for n in script.selection() :
		if hasattr( n, "execute" ) :
			result.append( n )

	return result

def __selectionAvailable( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	return bool( __selectedNodes( script ) )

def __previous( script ) :

	scriptWindow = GafferUI.ScriptWindow.acquire( script )
	nodes = getattr( scriptWindow, "_lastDispatch", [] )
	return [ w() for w in nodes if w() is not None and script.isSame( w().scriptNode() ) ]

def __previousAvailable( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	return bool( __previous( script ) )
