##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

import re

import IECore

import Gaffer
import GafferUI

class ScriptWindow( GafferUI.Window ) :

	def __init__( self, script ) :
	
		GafferUI.Window.__init__( self )

		self.__script = script
		
		self.__listContainer = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		
		m = GafferUI.MenuBar( self.menuDefinition() )
		
		self.__listContainer.append( m )
		
		if "Default" in GafferUI.Layouts.names() :
			self.setLayout( GafferUI.Layouts.create( "Default" ) )
		else :
			self.setLayout( GafferUI.CompoundEditor() )
		
		self.setChild( self.__listContainer )
		
		scriptParent = script.parent()
		if scriptParent :
			self.__scriptRemovedConnection = scriptParent.childRemovedSignal().connect( Gaffer.WeakMethod( self.__scriptRemoved ) )

		self.__closedConnection = self.closedSignal().connect( Gaffer.WeakMethod( self.__closed ) )

		self.__scriptPlugSetConnection = script.plugSetSignal().connect( Gaffer.WeakMethod( self.__scriptPlugChanged ) )
		self.__scriptPlugDirtiedConnection = script.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__scriptPlugChanged ) )
	
		self.__updateTitle()

		ScriptWindow.__instances.append( self )
		
	## \todo Implement setScript() - and decide on naming so it matches the Editor method (getScriptNode)
	def getScript( self ) :
	
		return self.__script

	def setLayout( self, compoundEditor ) :
	
		if len( self.__listContainer ) > 1 :
			del self.__listContainer[1]
	
		compoundEditor.setScriptNode( self.__script )
		self.__listContainer.append( compoundEditor, expand=True )
		
	def getLayout( self ) :
	
		return self.__listContainer[1] 

	def __closed( self, widget ) :
		
		scriptParent = self.__script.parent()
		if scriptParent :
			scriptParent.removeChild( self.__script )
			
	def __scriptRemoved( self, scriptContainer, script ) :
	
		if script.isSame( self.__script ) :
			ScriptWindow.__instances.remove( self )

	def __scriptPlugChanged( self, plug ) :
	
		if plug.isSame( self.__script["fileName"] ) :
			self.__updateTitle()
	
	def __updateTitle( self ) :
	
		f = self.__script["fileName"].getValue()
		if not f :
			f = "untitled"
			d = ""
		else :
			d, n, f = f.rpartition( "/" )
			d = " - " + d
			
		self.setTitle( "Gaffer : %s %s" % ( f, d ) )

	## Returns the ScriptWindow for the specified script, creating one
	# if necessary.
	@staticmethod
	def acquire( script ) :
	
		for i in ScriptWindow.__instances :
			if i.getScript().isSame( script ) :
				return i
				
		return ScriptWindow( script )

	## Returns an IECore.MenuDefinition which is used to define the menu bars for all ScriptWindows.
	# This can be edited at any time to modify subsequently created ScriptWindows - typically editing
	# would be done as part of gaffer startup.
	@staticmethod
	def menuDefinition() :
	
		return ScriptWindow.__menuDefinition
	
	__menuDefinition = IECore.MenuDefinition()	

	## This function provides the top level functionality for instantiating
	# the UI. Once called, new ScriptWindows will be instantiated for each
	# script added to the application, and EventLoop.mainEventLoop().stop() will
	# be called when the last script is removed.
	__scriptAddedConnections = []
	__scriptRemovedConnections = []
	@classmethod
	def connect( cls, applicationRoot ) :
	
		cls.__scriptAddedConnections.append( applicationRoot["scripts"].childAddedSignal().connect( ScriptWindow.__scriptAdded ) )
		cls.__scriptRemovedConnections.append( applicationRoot["scripts"].childRemovedSignal().connect( ScriptWindow.__staticScriptRemoved ) )

	__instances = []
	@staticmethod
	def __scriptAdded( scriptContainer, script ) :
	
		ScriptWindow( script ).setVisible( True )
		
	@staticmethod
	def __staticScriptRemoved( scriptContainer, script ) :
	
		if not len( scriptContainer.children() ) :
			
			GafferUI.EventLoop.mainEventLoop().stop()
