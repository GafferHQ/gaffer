##########################################################################
#  
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI

class BrowserEditor( GafferUI.EditorWidget ) :

	def __init__( self, scriptNode=None, **kw ) :
	
		self.__column = GafferUI.ListContainer( borderWidth = 8, spacing = 6 )
		
		GafferUI.EditorWidget.__init__( self, self.__column, scriptNode, **kw )
		
		with self.__column :
		
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 6 ) :
			
				GafferUI.Label( "Location" )
			
				modeMenu = GafferUI.SelectionMenu()
				for mode in self.__modes :
					modeMenu.addItem( mode[0] )
				self.__modeChangedConnection = modeMenu.currentIndexChangedSignal().connect( Gaffer.WeakMethod( self.__modeChanged ) )
		
			self.__pathChooser = GafferUI.PathChooserWidget( Gaffer.DictPath( {}, "/" ), previewTypes=GafferUI.PathPreviewWidget.types() )
			self.__pathChooser.pathWidget().setVisible( False )
		
		self.__modeInstances = {}
		self.__currentModeInstance = None
		self.__modeChanged( modeMenu )
	
	## Returns the PathChooserWidget which forms the majority of this ui.
	def pathChooser( self ) :
	
		return self.__pathChooser
	
	def __repr__( self ) :

		return "GafferUI.BrowserEditor()"
		
	def __modeChanged( self, modeMenu ) :
	
		label = modeMenu.getCurrentItem()
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
						
		def disconnect( self ) :
	
			self.__directoryPath[:] = self.browser().pathChooser().directoryPathWidget().getPath()[:]
			self.__displayMode = self.browser().pathChooser().pathListingWidget().getDisplayMode()
	
		## Must be implemented by derived classes to return the initial directory path to be viewed.
		def _initialPath( self ) :
		
			raise NotImplementedError
		
		## May be reimplemented by derived classes to change the initial display mode of the path listing
		def _initialDisplayMode( self ) :
		
			return GafferUI.PathListingWidget.DisplayMode.List
			
		def _initialColumns( self ) :
		
			raise NotImplementedError
	
	__modes = []
	@classmethod
	def registerMode( cls, label, modeCreator ) :
	
		cls.__modes.append( ( label, modeCreator ) )

GafferUI.EditorWidget.registerType( "Browser", BrowserEditor )	

class FileSystemMode( BrowserEditor.Mode ) :

	def __init__( self, browser ) :
		
		BrowserEditor.Mode.__init__( self, browser )

	def _initialPath( self ) :
	
		return Gaffer.FileSystemPath(
			os.getcwd(),
			filter = Gaffer.CompoundPathFilter(
			
				filters = [
				
					Gaffer.FileNamePathFilter(
						[ re.compile( "^[^.].*" ) ],
						leafOnly=False,
						userData = {
							"UI" : {
								"label" : "Show hidden files",
								"invertEnabled" : True,
							}
						}
					),
					
					Gaffer.InfoPathFilter(
						infoKey = "name",
						matcher = None, # the ui will fill this in
						leafOnly = False,
					),
					
				],
			
			),
		)
		
	def _initialColumns( self ) :
	
		return GafferUI.PathListingWidget.defaultFileSystemColumns
			
BrowserEditor.registerMode( "Files", FileSystemMode )
	
class FileSequenceMode( BrowserEditor.Mode ) :

	def __init__( self, browser ) :
		
		BrowserEditor.Mode.__init__( self, browser )
	
	def _initialPath( self ) :
	
	
		return Gaffer.SequencePath(
			Gaffer.FileSystemPath( os.getcwd() ),
			filter = Gaffer.CompoundPathFilter(
				
				filters = [
				
					Gaffer.FileNamePathFilter(
						[ re.compile( "^[^.].*" ) ],
						leafOnly=False,
						userData = {
							"UI" : {
								"label" : "Show hidden files",
								"invertEnabled" : True,
							}
						}
					),
					
					Gaffer.InfoPathFilter(
						infoKey = "name",
						matcher = None, # the ui will fill this in
						leafOnly = False,
					),
					
				],
			
			),
		)

	def _initialColumns( self ) :
	
		return GafferUI.PathListingWidget.defaultFileSystemColumns
		
BrowserEditor.registerMode( "File Sequences", FileSequenceMode )

class OpMode( BrowserEditor.Mode ) :

	def __init__( self, browser ) :
	
		BrowserEditor.Mode.__init__( self, browser )
				
	def connect( self ) :
	
		BrowserEditor.Mode.connect( self )
		
		self.__pathSelectedConnection = self.browser().pathChooser().pathListingWidget().pathSelectedSignal().connect( Gaffer.WeakMethod( self.__pathSelected ) )
		
	def disconnect( self ) :
	
		BrowserEditor.Mode.disconnect( self )

		self.__pathSelectedConnection = None
	
	def _initialPath( self ) :
	
		return Gaffer.ClassLoaderPath( IECore.ClassLoader.defaultOpLoader(), "/" )
		
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
