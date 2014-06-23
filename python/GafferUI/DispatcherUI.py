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

import IECore

import Gaffer
import GafferUI

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
	menuDefinition.append( "/Execute", { "command" : IECore.curry( _execute, [ node ] ) } )
	
def executeSelected( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	_execute( __selectedNodes( script ) )

def repeatPrevious( menu ) :

	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()
	_execute( __previous( script ) )

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
	
		_execute( [ self.getPlug().node() ] )

##########################################################################
# Metadata, PlugValueWidgets and Nodules
##########################################################################

Gaffer.Metadata.registerPlugValue( Gaffer.ExecutableNode, "requirement", "nodeUI:section", "header" )
Gaffer.Metadata.registerPlugValue( Gaffer.ExecutableNode, "dispatcher", "nodeUI:section", "Dispatcher" )

GafferUI.PlugValueWidget.registerCreator( Gaffer.ExecutableNode, "requirement", __RequirementPlugValueWidget )
GafferUI.PlugValueWidget.registerCreator( Gaffer.ExecutableNode, "dispatcher", GafferUI.CompoundPlugValueWidget, collapsed = None )

GafferUI.Nodule.registerNodule( Gaffer.ExecutableNode, "dispatcher", lambda plug : None )

##########################################################################
# Implementation Details
##########################################################################

def _execute( nodes ) :

	script = nodes[0].scriptNode()
	script._executeUILastExecuted = []
	
	for node in nodes :
		node.execute( [ script.context() ] )
		script._executeUILastExecuted.append( weakref.ref( node ) )

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
