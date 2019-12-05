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

		self.__titleChangedSignal = GafferUI.WidgetEventSignal()

		GafferUI.Window.__init__( self, **kw )

		self.__script = script

		self.__titleBehaviour = _WindowTitleBehaviour( self, script )

		self.__listContainer = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 0 )

		menuDefinition = self.menuDefinition( script.applicationRoot() ) if script.applicationRoot() else IECore.MenuDefinition()
		self.__listContainer.append( GafferUI.MenuBar( menuDefinition ) )

		applicationRoot = self.__script.ancestor( Gaffer.ApplicationRoot )
		layouts = GafferUI.Layouts.acquire( applicationRoot ) if applicationRoot is not None else None
		if layouts is not None :
			self.setLayout( layouts.createDefault( script ) )
		else :
			self.setLayout( GafferUI.CompoundEditor( script ) )

		self.setChild( self.__listContainer )

		self.closedSignal().connect( Gaffer.WeakMethod( self.__closed ), scoped = False )

		ScriptWindow.__instances.append( weakref.ref( self ) )

	def menuBar( self ) :

		return self.__listContainer[0]

	def scriptNode( self ) :

		return self.__script

	def setLayout( self, compoundEditor ) :

		if len( self.__listContainer ) > 1 :
			del self.__listContainer[1]

		assert( compoundEditor.scriptNode().isSame( self.scriptNode() ) )
		self.__listContainer.append( compoundEditor, expand=True )

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

		dialogue = GafferUI.ConfirmationDialogue(
			"Discard Unsaved Changes?",
			"The file %s has unsaved changes. Do you want to discard them?" % f,
			confirmLabel = "Discard"
		)
		return dialogue.waitForConfirmation( parentWindow=self )

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

		applicationRoot["scripts"].childAddedSignal().connect( 0, ScriptWindow.__scriptAdded, scoped = False )
		applicationRoot["scripts"].childRemovedSignal().connect( ScriptWindow.__staticScriptRemoved, scoped = False )

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


class _WindowTitleBehaviour :

	def __init__( self, window, script ) :

		self.__window = weakref.ref( window )
		self.__script = weakref.ref( script )

		self.__scriptPlugSetConnection = script.plugSetSignal().connect( Gaffer.WeakMethod( self.__scriptPlugChanged ) )
		self.__metadataChangedConnection = Gaffer.Metadata.nodeValueChangedSignal().connect( Gaffer.WeakMethod( self.__metadataChanged ) )

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

