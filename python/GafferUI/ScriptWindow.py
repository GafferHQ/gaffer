##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

class ScriptWindow( GafferUI.Window ) :

	def __init__( self, script, **kw ) :
	
		GafferUI.Window.__init__( self, **kw )

		self.__script = script
		
		self.__listContainer = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 2 )
		
		menuDefinition = self.menuDefinition( script.applicationRoot() ) if script.applicationRoot() else IECore.MenuDefinition()
		self.__listContainer.append( GafferUI.MenuBar( menuDefinition ) )
		
		applicationRoot = self.__script.ancestor( Gaffer.ApplicationRoot.staticTypeId() )
		layouts = GafferUI.Layouts.acquire( applicationRoot ) if applicationRoot is not None else None
		if layouts is not None and "Default" in layouts.names() :
			self.setLayout( layouts.create( "Default", script ) )
		else :
			self.setLayout( GafferUI.CompoundEditor( script ) )
		
		self.setChild( self.__listContainer )
		
		self.__closedConnection = self.closedSignal().connect( Gaffer.WeakMethod( self.__closed ) )

		self.__scriptPlugSetConnection = script.plugSetSignal().connect( Gaffer.WeakMethod( self.__scriptPlugChanged ) )
	
		self.__updateTitle()

		ScriptWindow.__instances.append( weakref.ref( self ) )
		
	def scriptNode( self ) :
	
		return self.__script

	def setLayout( self, compoundEditor ) :
	
		if len( self.__listContainer ) > 1 :
			del self.__listContainer[1]
	
		assert( compoundEditor.scriptNode().isSame( self.scriptNode() ) )
		self.__listContainer.append( compoundEditor, expand=True )
		
	def getLayout( self ) :
	
		return self.__listContainer[1] 

	def _acceptsClose( self ) :
	
		if not self.__script["unsavedChanges"].getValue() :
			return True
		
		f = self.__script["fileName"].getValue()
		f = f.rpartition( "/" )[2] if f else "untitled"
					
		dialogue = GafferUI.ConfirmationDialogue(
			"Discard Unsaved Changes?",
			"The file %s has unsaved changes. Do you want to discard them?" % f,
			confirmLabel = "Discard"
		)
		return dialogue.waitForConfirmation()

	def __closed( self, widget ) :
		
		scriptParent = self.__script.parent()
		if scriptParent is not None :
			scriptParent.removeChild( self.__script )

	def __scriptPlugChanged( self, plug ) :
	
		if plug.isSame( self.__script["fileName"] ) or plug.isSame( self.__script["unsavedChanges"] ) :
			self.__updateTitle()
	
	def __updateTitle( self ) :
	
		f = self.__script["fileName"].getValue()
		if not f :
			f = "untitled"
			d = ""
		else :
			d, n, f = f.rpartition( "/" )
			d = " - " + d
		
		u = " *" if self.__script["unsavedChanges"].getValue() else ""
		
		self.setTitle( "Gaffer : %s%s%s" % ( f, u, d ) )

	__instances = [] # weak references to all instances - used by acquire()
	## Returns the ScriptWindow for the specified script, creating one
	# if necessary.
	@staticmethod
	def acquire( script ) :
	
		for w in ScriptWindow.__instances :
			scriptWindow = w()
			if scriptWindow is not None and scriptWindow.scriptNode().isSame( script ) :
				return scriptWindow
		
		return ScriptWindow( script )

	## Returns an IECore.MenuDefinition which is used to define the menu bars for all ScriptWindows
	# created as part of the specified application. This can be edited at any time to modify subsequently
	# created ScriptWindows - typically editing would be done as part of gaffer startup.
	@staticmethod
	def menuDefinition( applicationOrApplicationRoot ) :
	
		if isinstance( applicationOrApplicationRoot, Gaffer.Application ) :
			applicationRoot = applicationOrApplicationRoot.root()
		else :
			assert( isinstance( applicationOrApplicationRoot, Gaffer.ApplicationRoot ) )
			applicationRoot = applicationOrApplicationRoot
			
		menuDefinition = getattr( applicationRoot, "_scriptWindowMenuDefinition", None )
		if menuDefinition :
			return menuDefinition
			
		menuDefinition = IECore.MenuDefinition()
		applicationRoot._scriptWindowMenuDefinition = menuDefinition
		
		return menuDefinition
	
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

	__automaticallyCreatedInstances = [] # strong references to instances made by __scriptAdded()
	@staticmethod
	def __scriptAdded( scriptContainer, script ) :
	
		w = ScriptWindow( script )
		w.setVisible( True )
		ScriptWindow.__automaticallyCreatedInstances.append( w )
		
	@staticmethod
	def __staticScriptRemoved( scriptContainer, script ) :
	
		for w in ScriptWindow.__automaticallyCreatedInstances :
			if w.scriptNode().isSame( script ) :
				ScriptWindow.__automaticallyCreatedInstances.remove( w )
	
		if not len( scriptContainer.children() ) :
			GafferUI.EventLoop.mainEventLoop().stop()
