##########################################################################
#  
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

import os
import re
import weakref
import threading

import IECore

import Gaffer
import GafferUI

class BrowserEditor( GafferUI.EditorWidget ) :

	def __init__( self, scriptNode, **kw ) :
	
		self.__column = GafferUI.ListContainer( borderWidth = 8, spacing = 6 )
		
		GafferUI.EditorWidget.__init__( self, self.__column, scriptNode, **kw )
		
		with self.__column :
		
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 6 ) :
			
				GafferUI.Label( "Location" )
			
				modeMenu = GafferUI.MultiSelectionMenu(
					allowMultipleSelection = False,
					allowEmptySelection = False,
				)
				for mode in self.__modes :
					modeMenu.append( mode[0] )
				self.__modeChangedConnection = modeMenu.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__modeChanged ) )
		
			self.__pathChooser = GafferUI.PathChooserWidget( Gaffer.DictPath( {}, "/" ), previewTypes=GafferUI.PathPreviewWidget.types() )
			self.__pathChooser.pathWidget().setVisible( False )
		
		self.__modeInstances = {}
		self.__currentModeInstance = None
		modeMenu.setSelection( [ self.__modes[0][0] ] )
	
	## Returns the PathChooserWidget which forms the majority of this ui.
	def pathChooser( self ) :
	
		return self.__pathChooser
	
	def __repr__( self ) :

		return "GafferUI.BrowserEditor( scriptNode )"
		
	def __modeChanged( self, modeMenu ) :
	
		label = modeMenu.getSelection()[0]
		if label not in self.__modeInstances :
			for mode in self.__modes :
				if mode[0] == label :
					self.__modeInstances[label] = mode[1]( self )
					break

		if self.__currentModeInstance is not None :
			self.__currentModeInstance.disconnect()
		
		self.__currentModeInstance = self.__modeInstances[label]
		self.__currentModeInstance.connect()
		
	class Mode( object ) :
	
		def __init__( self, browser ) :
		
			self.__browser = weakref.ref( browser ) # avoid circular references
			self.__directoryPath = None
			self.__displayMode = None
			
			# create the op matcher on a separate thread, as it may take a while to trawl
			# through all the available ops.
			self.__opMatcher = None
			threading.Thread( target = self.__createOpMatcher ).start()
			
		def browser( self ) :
		
			return self.__browser()
		
		def connect( self ) :
		
			if self.__directoryPath is None :
				self.__directoryPath = self._initialPath()
				self.__displayMode = self._initialDisplayMode()
				self.__columns = self._initialColumns()
				
			# we need a little bit of jiggery pokery, because the PathChooserWidget edits
			# the main path as a leaf path, and we're more interested in setting the current
			# directory.
			pathElements = self.__directoryPath[:]
			self.browser().pathChooser().setPath( self.__directoryPath )
			self.browser().pathChooser().directoryPathWidget().getPath()[:] = pathElements
			
			self.browser().pathChooser().pathListingWidget().setDisplayMode( self.__displayMode )
			self.browser().pathChooser().pathListingWidget().setColumns( self.__columns )
			
			# we've potentially changed to an entirely different type of path, so we must make
			# sure that the bookmarks we use are suitable for that. we do this here in the base
			# class to make sure that the path and bookmarks never get out of sync, but derived
			# classes can still modify the bookmarks if they know better.
			self.browser().pathChooser().setBookmarks(
				GafferUI.Bookmarks.acquire(
					self.browser().scriptNode().ancestor( Gaffer.ApplicationRoot.staticTypeId() ),
					pathType = self.__directoryPath.__class__
				)
			)
			
			self.__contextMenuConnection = self.browser().pathChooser().pathListingWidget().contextMenuSignal().connect( Gaffer.WeakMethod( self.__contextMenu ) )
						
		def disconnect( self ) :
	
			self.__directoryPath[:] = self.browser().pathChooser().directoryPathWidget().getPath()[:]
			self.__displayMode = self.browser().pathChooser().pathListingWidget().getDisplayMode()
	
			self.__contextMenuConnection = None
	
		## Must be implemented by derived classes to return the initial directory path to be viewed.
		def _initialPath( self ) :
		
			raise NotImplementedError
		
		## May be reimplemented by derived classes to change the initial display mode of the path listing
		def _initialDisplayMode( self ) :
		
			return GafferUI.PathListingWidget.DisplayMode.List
		
		## Must be reimplemented by derived classes to specify the columns to be displayed in the PathListingWidget.
		def _initialColumns( self ) :
		
			raise NotImplementedError
		
		## May be reimplemented by derived classes to return a custom OpMatcher to be used
		# to provide action menu items for the ui.
		def _createOpMatcher( self ) :
		
			return Gaffer.OpMatcher.defaultInstance()
			
		def __contextMenu( self, pathListing ) :
		
			menuDefinition = IECore.MenuDefinition()
		
			if self.__opMatcher is not None :
			
				selectedPaths = pathListing.getSelectedPaths()
				if len( selectedPaths ) == 1 :
					parameterValue = selectedPaths[0]
				else :
					parameterValue = selectedPaths
			
				menuDefinition.append( "/Actions", { "subMenu" : IECore.curry( Gaffer.WeakMethod( self.__actionsSubMenu ), parameterValue ) } )
					
			else :
			
				menuDefinition.append( "/Loading actions...", { "active" : False } )
					
			self.__menu = GafferUI.Menu( menuDefinition )
			if len( menuDefinition.items() ) :
				self.__menu.popup( parent = pathListing.ancestor( GafferUI.Window ) )
			
			return True
		
		def __actionsSubMenu( self, parameterValue ) :
		
			menuDefinition = IECore.MenuDefinition()
				
			ops = self.__opMatcher.matches( parameterValue )
			if len( ops ) :
				for op, parameter in ops :
					menuDefinition.append( "/%s (%s)" % ( op.typeName(), parameter.name ), { "command" : self.__opDialogueCommand( op ) } )
			else :
				menuDefinition.append( "/None available", { "active" : False } )
				
			return menuDefinition
				
		def __createOpMatcher( self ) :
		
			self.__opMatcher = self._createOpMatcher()
			
		def __opDialogueCommand( self, op ) :
		
			def showDialogue( menu ) :
			
				dialogue = GafferUI.OpDialogue(
					op,
					postExecuteBehaviour = GafferUI.OpDialogue.PostExecuteBehaviour.Close,
					executeInBackground=True
				)
				dialogue.waitForResult( parentWindow = menu.ancestor( GafferUI.Window ) )
				
			return showDialogue
			
	__modes = []
	@classmethod
	def registerMode( cls, label, modeCreator ) :
	
		# first remove any existing modes of the same label
		cls.__modes = [ m for m in cls.__modes if m[0] != label ]
		
		cls.__modes.append( ( label, modeCreator ) )

GafferUI.EditorWidget.registerType( "Browser", BrowserEditor )	

class FileSystemMode( BrowserEditor.Mode ) :

	def __init__( self, browser ) :
		
		BrowserEditor.Mode.__init__( self, browser )

	def connect( self ) :
		
		currentPath = self.browser().pathChooser().getPath()
		
		BrowserEditor.Mode.connect( self )
		
		if isinstance( currentPath, ( Gaffer.FileSystemPath, Gaffer.SequencePath ) ) :
			dirPath = currentPath.parent() if currentPath.isLeaf() else currentPath
			self.browser().pathChooser().getPath().setFromPath( Gaffer.FileSystemPath( str(dirPath) ) )
	
	def _initialPath( self ) :
	
		return Gaffer.FileSystemPath(
			os.getcwd(),
			filter = Gaffer.FileSystemPath.createStandardFilter(),
		)
		
	def _initialColumns( self ) :
	
		return list( GafferUI.PathListingWidget.defaultFileSystemColumns )
			
BrowserEditor.registerMode( "Files", FileSystemMode )
BrowserEditor.FileSystemMode = FileSystemMode
	
class FileSequenceMode( BrowserEditor.Mode ) :

	def __init__( self, browser ) :
		
		BrowserEditor.Mode.__init__( self, browser )
	
	def connect( self ) :
		
		currentPath = self.browser().pathChooser().getPath()
		
		BrowserEditor.Mode.connect( self )
		
		if isinstance( currentPath, ( Gaffer.FileSystemPath, Gaffer.SequencePath ) ) :
			dirPath = currentPath.parent() if currentPath.isLeaf() else currentPath
			self.browser().pathChooser().getPath().setFromPath( Gaffer.SequencePath( str(dirPath) ) )
		
		# we want to share our bookmarks with the non-sequence filesystem paths
		self.browser().pathChooser().setBookmarks(
			GafferUI.Bookmarks.acquire(
				self.browser().scriptNode().ancestor( Gaffer.ApplicationRoot.staticTypeId() ),
				pathType = Gaffer.FileSystemPath
			)
		)
			
	def _initialPath( self ) :
	
		return Gaffer.SequencePath(
			Gaffer.FileSystemPath( os.getcwd() ),
			filter = Gaffer.FileSystemPath.createStandardFilter(),
		)

	def _initialColumns( self ) :
	
		return list( GafferUI.PathListingWidget.defaultFileSystemColumns )
		
BrowserEditor.registerMode( "File Sequences", FileSequenceMode )
BrowserEditor.FileSequenceMode = FileSequenceMode

class OpMode( BrowserEditor.Mode ) :

	def __init__( self, browser, classLoader=None ) :
	
		BrowserEditor.Mode.__init__( self, browser )
		
		if classLoader is not None :
			self.__classLoader = classLoader
		else :
			self.__classLoader = IECore.ClassLoader.defaultOpLoader()
				
	def connect( self ) :
	
		BrowserEditor.Mode.connect( self )
		
		self.__pathSelectedConnection = self.browser().pathChooser().pathListingWidget().pathSelectedSignal().connect( Gaffer.WeakMethod( self.__pathSelected ) )
		
	def disconnect( self ) :
	
		BrowserEditor.Mode.disconnect( self )

		self.__pathSelectedConnection = None
	
	def _initialPath( self ) :
	
		return Gaffer.ClassLoaderPath( self.__classLoader, "/" )
		
	def _initialDisplayMode( self ) :
	
		return GafferUI.PathListingWidget.DisplayMode.Tree
	
	def _initialColumns( self ) :
	
		return [ GafferUI.PathListingWidget.defaultNameColumn ]
	
	def __pathSelected( self, pathListing ) :
	
		selectedPaths = pathListing.getSelectedPaths()
		if not len( selectedPaths ) :
			return
			
		op = selectedPaths[0].classLoader().load( str( selectedPaths[0] )[1:] )()
		opDialogue = GafferUI.OpDialogue( op )
		pathListing.ancestor( GafferUI.Window ).addChildWindow( opDialogue )
		opDialogue.setVisible( True )

BrowserEditor.registerMode( "Ops", OpMode )
BrowserEditor.OpMode = OpMode
