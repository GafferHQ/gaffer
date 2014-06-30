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
import threading
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
	_execute( __previous( script ) )

##################################################################################
# Dispatcher Window 
##################################################################################

class _DispatcherWindow( GafferUI.Window ) :
	
	def __init__( self, **kw ) :
		
		GafferUI.Window.__init__( self, **kw )
		
		self.__dispatcher = Gaffer.Dispatcher.dispatcher( "local" )
		self.__nodes = []
		
		with self :
			
			with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Vertical, spacing = 2, borderWidth = 4 ) :
				
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
					GafferUI.Label( "Dispatcher" )
					dispatchersMenu = GafferUI.MultiSelectionMenu( allowMultipleSelection = False, allowEmptySelection = False )
					dispatchersMenu.append( [ IECore.CamelCase.toSpaced( x ) for x in Gaffer.Dispatcher.dispatcherNames() ] )
					dispatchersMenu.setSelection( [ "Local" ] )
					self.__dispatchersMenuSelectionChangedConnection = dispatchersMenu.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__dispatcherChanged ) )
				
				self.__frame = GafferUI.Frame( borderStyle=GafferUI.Frame.BorderStyle.None, borderWidth=0 )
				self.__dispatchButton = GafferUI.Button( "Dispatch" )
				self.__dispatchClickedConnection = self.__dispatchButton.clickedSignal().connect( Gaffer.WeakMethod( self.__dispatchClicked ) )
		
		self.__update()
	
	def setVisible( self, visible ) :
		
		GafferUI.Window.setVisible( self, visible )
		
		if visible :
			self.__dispatchButton._qtWidget().setFocus( QtCore.Qt.OtherFocusReason )
	
	def dispatcher( self ) :
	
		return self.__dispatcher
	
	def setNodesToDispatch( self, nodes ) :
		
		self.__nodes = nodes
		self.__updateTitle()
	
	def __update( self ) :
		
		self.__frame.setChild( GafferUI.NodeUI.create( self.__dispatcher ) )
		self.__updateTitle()
	
	def __updateTitle( self ) :
		
		title = "Dispatching"
		if len(self.__nodes) :
			title += ": " + ", ".join( [ x.getName() for x in self.__nodes ] )
		
		self.setTitle( title )
	
	def __dispatchClicked( self, button ) :
		
		threading.Thread( target = self.__dispatch ).start()
		self.close()
	
	def __dispatch( self ) :
		
		with self.parent().scriptNode().context() :
			self.__dispatcher.dispatch( self.__nodes )
		## \todo: update _executeUILastExecuted
	
	def __dispatcherChanged( self, menu ) :
		
		self.__dispatcher = Gaffer.Dispatcher.dispatcher( IECore.CamelCase.fromSpaced( menu.getSelection()[0], IECore.CamelCase.Caps.AllExceptFirst ) )
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


#################################
# PlugValueWidget for framesMode
#################################

## \todo: This can be removed once we have enums and activators driven by metadata.
class __FramesModePlugValueWidget( GafferUI.EnumPlugValueWidget ) :

	def __init__( self, plug ) :
		
		GafferUI.EnumPlugValueWidget.__init__(
			self, plug,
			labelsAndValues = (
				( "CurrentFrame", Gaffer.Dispatcher.FramesMode.CurrentFrame ),
				( "ScriptRange", Gaffer.Dispatcher.FramesMode.ScriptRange ),
				( "CustomRange", Gaffer.Dispatcher.FramesMode.CustomRange ),
			)
		)
	
	def _updateFromPlug( self ) :
		
		GafferUI.EnumPlugValueWidget._updateFromPlug( self )
		
		if self.getPlug() is None :
			return
		
		with self.getContext() :
			framesMode = self.getPlug().getValue()
		
		nodeUI = self.ancestor( GafferUI.NodeUI )
		if nodeUI :
			frameRangeWidget = nodeUI.plugValueWidget( self.getPlug().node()["frameRange"], lazy = False )
			if frameRangeWidget :
				frameRangeWidget.setEnabled( framesMode == Gaffer.Dispatcher.FramesMode.CustomRange )

##########################################################################
# Metadata, PlugValueWidgets and Nodules
##########################################################################

Gaffer.Metadata.registerPlugValue( Gaffer.ExecutableNode, "requirement", "nodeUI:section", "header" )
Gaffer.Metadata.registerPlugValue( Gaffer.ExecutableNode, "dispatcher", "nodeUI:section", "Dispatcher" )
Gaffer.Metadata.registerPlugDescription( Gaffer.Dispatcher, "framesMode", "Determines the active frame range for dispatching." )
Gaffer.Metadata.registerPlugDescription( Gaffer.Dispatcher, "frameRange", "The frame range to be used when framesMode is set to CustomRange." )
Gaffer.Metadata.registerPlugDescription( Gaffer.Dispatcher, "jobDirectory", "A directory to store temporary files used by the dispatcher." )

GafferUI.PlugValueWidget.registerCreator(
	Gaffer.Dispatcher,
	"jobDirectory",
	lambda plug : GafferUI.PathPlugValueWidget( plug,
		path = Gaffer.FileSystemPath( "/", filter = Gaffer.FileSystemPath.createStandardFilter( [ "gfr" ] ) ),
		pathChooserDialogueKeywords = {
			"leaf" : False,
		},
	)
)

GafferUI.PlugValueWidget.registerCreator( Gaffer.Dispatcher, "user", None )
GafferUI.PlugValueWidget.registerCreator( Gaffer.Dispatcher, "framesMode", __FramesModePlugValueWidget )
GafferUI.PlugValueWidget.registerCreator( Gaffer.ExecutableNode, "requirement", __RequirementPlugValueWidget )
GafferUI.PlugValueWidget.registerCreator( Gaffer.ExecutableNode, "dispatcher", GafferUI.CompoundPlugValueWidget, collapsed = None )

GafferUI.Nodule.registerNodule( Gaffer.Dispatcher, fnmatch.translate( "*" ), lambda plug : None )
GafferUI.Nodule.registerNodule( Gaffer.ExecutableNode, "dispatcher", lambda plug : None )

##########################################################################
# Implementation Details
##########################################################################

def _execute( nodes ) :

	script = nodes[0].scriptNode()
	script._executeUILastExecuted = []
	
	with script.context() :
		__dispatcherWindow( script ).dispatcher().dispatch( nodes )
	
	script._executeUILastExecuted = [ weakref.ref( node ) for node in nodes ]

__dispatcherWindowInstance = None
def __dispatcherWindow( script ) :
	
	global __dispatcherWindowInstance
	
	if __dispatcherWindowInstance is not None and __dispatcherWindowInstance() :
		window = __dispatcherWindowInstance()
	else :
		window = _DispatcherWindow()
		__dispatcherWindowInstance = weakref.ref( window )
	
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

	if not hasattr( script, "_executeUILastExecuted" ) :
		return []
	
	result = []	
	for w in script._executeUILastExecuted :
		n = w()
		if n is not None :
			s = n.scriptNode()
			if s is not None and s.isSame( script ) :
				result.append( n )
		
	return result
	
def __previousAvailable( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	return bool( __previous( script ) )
