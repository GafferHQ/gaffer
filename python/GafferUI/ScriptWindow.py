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

import imath

import IECore

import Gaffer
import GafferUI

class ScriptWindow( GafferUI.Window ) :

	def __init__( self, script, **kw ) :

		self.__titleChangedSignal = GafferUI.WidgetEventSignal()

		GafferUI.Window.__init__( self, **kw )

		self.__script = script

		self.__titleBehaviour = _WindowTitleBehaviour( self, script )

		self.__listContainer = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 0 )

		self.__menuContainer = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		self.__listContainer.append( self.__menuContainer )

		menuDefinition = self.menuDefinition( script.applicationRoot() ) if script.applicationRoot() else IECore.MenuDefinition()
		self.__menuBar = GafferUI.MenuBar( menuDefinition )
		self.__menuBar.addShortcutTarget( self )
		self.__menuContainer.append( self.__menuBar )
		self.__menuContainer._qtWidget().setObjectName( "gafferMenuBarWidgetContainer" )
		# Must parent `__listContainer` to the window before setting the layout,
		# because `CompoundEditor.__parentChanged` needs to find the ancestor
		# ScriptWindow.
		self.setChild( self.__listContainer )

		applicationRoot = self.__script.ancestor( Gaffer.ApplicationRoot )
		layouts = GafferUI.Layouts.acquire( applicationRoot ) if applicationRoot is not None else None
		if layouts is not None :
			self.setLayout( layouts.createDefault( script ) )
		else :
			self.setLayout( GafferUI.CompoundEditor( script ) )

		self.closedSignal().connect( Gaffer.WeakMethod( self.__closed ) )

		ScriptWindow.__instances.append( weakref.ref( self ) )

	def menuBar( self ) :

		return self.__menuContainer[0]

	def scriptNode( self ) :

		return self.__script

	def setLayout( self, compoundEditor ) :

		# When changing layout we need to manually transfer the edit scope
		# from an existing CompoundEditor to the new one.
		currentEditScope = None
		if len( self.__listContainer ) > 1 :
			currentEditScope = self.getLayout().settings()["editScope"].getInput()
			del self.__listContainer[1]

		assert( compoundEditor.scriptNode().isSame( self.scriptNode() ) )
		self.__listContainer.append( compoundEditor, expand=True )

		if len( self.__menuContainer ) > 1 :
			del self.__menuContainer[1:]

		if currentEditScope is not None :
			compoundEditor.settings()["editScope"].setInput( currentEditScope )
		self.__menuContainer.append(
			GafferUI.PlugLayout(
				compoundEditor.settings(),
				orientation = GafferUI.ListContainer.Orientation.Horizontal,
				rootSection = "Settings"
			)
		)
		self.__menuContainer.append( GafferUI.Spacer( imath.V2i( 0 ) ) )

	def getLayout( self ) :

		return self.__listContainer[1]

	# Calling this will disable automatic title updates when the script state
	# changes name/dirty state.
	def setTitle( self, title ) :

		self.__titleBehaviour = None
		self._setTitle( title )

	def _setTitle( self, title ) :

		GafferUI.Window.setTitle( self, title )
		self.__titleChangedSignal( self, title )

	def titleChangedSignal( self ) :

		return self.__titleChangedSignal

	def _acceptsClose( self ) :

		if not self.__script["unsavedChanges"].getValue() :
			return True

		f = self.__script["fileName"].getValue()
		f = f.rpartition( "/" )[2] if f else "untitled"

		dialogue = _ChoiceDialogue(
			"Discard Unsaved Changes?",
			f"The file \"{f}\" has unsaved changes. Do you want to discard them?",
			choices = [ "Cancel", "Save", "Discard" ]
		)
		choice = dialogue.waitForChoice( parentWindow=self )

		if choice == "Discard" :
			return True
		elif choice == "Save" :
			## \todo Is it a bit odd that ScriptWindow should depend on FileMenu
			# like this? Should the code be moved somewhere else?
			GafferUI.FileMenu.save( self.menuBar() )
			return True
		else :
			return False

	def __closed( self, widget ) :

		scriptParent = self.__script.parent()
		if scriptParent is not None :
			scriptParent.removeChild( self.__script )

	__instances = [] # weak references to all instances - used by acquire()
	## Returns the ScriptWindow for the specified script, creating one
	# if necessary.
	@staticmethod
	def acquire( script, createIfNecessary=True ) :

		for w in ScriptWindow.__instances :
			scriptWindow = w()
			if scriptWindow is not None and scriptWindow.scriptNode().isSame( script ) :
				return scriptWindow

		return ScriptWindow( script ) if createIfNecessary else None

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
	@classmethod
	def connect( cls, applicationRoot ) :

		applicationRoot["scripts"].childAddedSignal().connectFront( ScriptWindow.__scriptAdded )
		applicationRoot["scripts"].childRemovedSignal().connect( ScriptWindow.__staticScriptRemoved )

	__automaticallyCreatedInstances = [] # strong references to instances made by __scriptAdded()
	@staticmethod
	def __scriptAdded( scriptContainer, script ) :

		w = ScriptWindow( script )
		w.setVisible( True )
		w.getLayout().restoreWindowState()
		ScriptWindow.__automaticallyCreatedInstances.append( w )

	@staticmethod
	def __staticScriptRemoved( scriptContainer, script ) :

		for w in ScriptWindow.__automaticallyCreatedInstances :
			if w.scriptNode().isSame( script ) :
				ScriptWindow.__automaticallyCreatedInstances.remove( w )

		if not len( scriptContainer.children() ) and GafferUI.EventLoop.mainEventLoop().running() :
			GafferUI.EventLoop.mainEventLoop().stop()

## \todo Would this be worthy of inclusion in GafferUI?
class _ChoiceDialogue( GafferUI.Dialogue ) :

	def __init__( self, title, message, choices, **kw ) :

		GafferUI.Dialogue.__init__( self, title, sizeMode=GafferUI.Window.SizeMode.Automatic, **kw )

		with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 8 ) as column :

			GafferUI.Label( message )

		self._setWidget( column )

		for choice in choices :
			self.__lastButton = self._addButton( choice )

	def waitForChoice( self, **kw ) :

		self.__lastButton._qtWidget().setFocus()
		button = self.waitForButton( **kw )

		if button is None :
			return None
		else :
			return button.getText()

class _WindowTitleBehaviour :

	def __init__( self, window, script ) :

		self.__window = weakref.ref( window )
		self.__script = weakref.ref( script )

		self.__scriptPlugSetConnection = script.plugSetSignal().connect( Gaffer.WeakMethod( self.__scriptPlugChanged ), scoped = True )
		self.__metadataChangedConnection = Gaffer.Metadata.nodeValueChangedSignal().connect( Gaffer.WeakMethod( self.__metadataChanged ), scoped = True )

		self.__updateTitle()

	def __updateTitle( self ) :

		w = self.__window()
		if not w :
			return

		f = self.__script()["fileName"].getValue()
		if not f :
			f = "untitled"
			d = ""
		else :
			d, n, f = f.rpartition( "/" )
			d = " - " + d

		u = " *" if self.__script()["unsavedChanges"].getValue() else ""
		ro = " (read only) " if Gaffer.MetadataAlgo.readOnly( self.__script() ) else ""

		w._setTitle( "Gaffer %s : %s%s%s%s" % ( Gaffer.About.versionString(), f, ro, u, d ) )

	def __scriptPlugChanged( self, plug ) :

		if plug.isSame( self.__script()["fileName"] ) or plug.isSame( self.__script()["unsavedChanges"] ) :
			self.__updateTitle()

	def __metadataChanged( self, nodeTypeId, key, node ) :

		if Gaffer.MetadataAlgo.readOnlyAffectedByChange( self.__script(), nodeTypeId, key, node ) :
			self.__updateTitle()
