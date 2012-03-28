##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

import IECore

import Gaffer
import GafferUI

class PathChooserWidget( GafferUI.Widget ) :

	def __init__( self, path, previewTypes=[], **kw ) :
	
		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=8 )
		
		GafferUI.Widget.__init__( self, self.__column, **kw )
		
		# we edit this path directly
		self.__path = path
		
		with self.__column :
		
			# row for manipulating current directory
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 0 ) :
				
				displayModeButton = GafferUI.Button( image = "pathListingTree.png", hasFrame=False )
				displayModeButton.setToolTip( "Toggle between list and tree views" )
				self.__displayModeButtonClickedConnection = displayModeButton.clickedSignal().connect( Gaffer.WeakMethod( self.__displayModeButtonClicked ) )
				
				reloadButton = GafferUI.Button( image = "refresh.png", hasFrame=False )
				reloadButton.setToolTip( "Refresh view" )
				self.__reloadButtonClickedConnection = reloadButton.clickedSignal().connect( Gaffer.WeakMethod( self.__reloadButtonClicked ) )
				
				upButton = GafferUI.Button( image = "pathUpArrow.png", hasFrame=False )
				upButton.setToolTip( "Up one level" )
				self.__upButtonClickedConnection = upButton.clickedSignal().connect( Gaffer.WeakMethod( self.__upButtonClicked ) )
				
				GafferUI.Spacer( IECore.V2i( 4, 4 ) )
				
				# make the path bar at the top of the window. this uses a modified path to make sure it can
				# only display directories and never be used to choose leaf files. we apply the necessary filter
				# to achieve that in __updateFilter.
				self.__dirPath = self.__path.copy()
				if len( self.__dirPath ) :
					del self.__dirPath[-1]

				GafferUI.PathWidget( self.__dirPath )
			
			# directory listing and preview widget
			with GafferUI.SplitContainer( GafferUI.SplitContainer.Orientation.Horizontal, expand=True ) as splitContainer :
			
				# the listing also uses a modified path of it's own.
				self.__listingPath = self.__path.copy()
				self.__directoryListing = GafferUI.PathListingWidget( self.__listingPath )
			
				if len( previewTypes ) :
					GafferUI.CompoundPathPreview( self.__path, childTypes=previewTypes )
				
			if len( splitContainer ) > 1 :
				splitContainer.setSizes( [ 2, 1 ] ) # give priority to the listing over the preview
		
			# filter section
			self.__filterFrame = GafferUI.Frame( borderWidth=0, borderStyle=GafferUI.Frame.BorderStyle.None )
			self.__filter = None
			self.__updateFilter()
				
			# path
			self.__pathWidget = GafferUI.PathWidget( self.__path )
		
		self.__pathSelectedSignal = GafferUI.WidgetSignal()

		self.__listingSelectionChangedConnection = self.__directoryListing.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__listingSelectionChanged ) )
		self.__listingSelectedConnection = self.__directoryListing.pathSelectedSignal().connect( Gaffer.WeakMethod( self.__pathSelected ) )
		self.__pathWidgetSelectedConnection = self.__pathWidget.activatedSignal().connect( Gaffer.WeakMethod( self.__pathSelected ) )
		
		self.__pathChangedConnection = self.__path.pathChangedSignal().connect( Gaffer.WeakMethod( self.__pathChanged ) )
		self.__dirPathChangedConnection = self.__dirPath.pathChangedSignal().connect( Gaffer.WeakMethod( self.__dirPathChanged ) )
		self.__listingPathChangedConnection = self.__listingPath.pathChangedSignal().connect( Gaffer.WeakMethod( self.__listingPathChanged ) )
		
	## Returns the PathWidget used for text-based path entry.
	def pathWidget( self ) :
	
		return self.__pathWidget

	## This signal is emitted when the user has selected a path.
	def pathSelectedSignal( self ) :
	
		return self.__pathSelectedSignal

	def __listingSelectionChanged( self, widget ) :
	
		assert( widget is self.__directoryListing )
		
		selection = self.__directoryListing.getSelectedPaths()
		for path in selection :
			if path.isLeaf() :
				with Gaffer.BlockedConnection( self.__pathChangedConnection ) :
					self.__path[:] = path[:]
					break

	# This slot is connected to the pathSelectedSignals of the children and just forwards
	# them to our own pathSelectedSignal.
	def __pathSelected( self, childWidget ) :
		
		self.pathSelectedSignal()( self )

	def __upButtonClicked( self, button ) :
	
		if not len( self.__dirPath ) :
			return
	
		del self.__dirPath[-1]

	def __reloadButtonClicked( self, button ) :
	
		self.__listingPath.pathChangedSignal()( self.__listingPath )
	
	def __updateFilter( self ) :
	
		newFilter = self.__path.getFilter()
		if self.__filter is newFilter :
			return
		
		# update the directory path filter to include
		# the new filter, but with the additional removal
		# of leaf paths.
		if newFilter is not None :
			self.__dirPath.setFilter(
				Gaffer.CompoundPathFilter( 
					[
						Gaffer.LeafPathFilter(),
						newFilter,
					]
				)
			)
		else :
			self.__dirPath.setFilter( Gaffer.LeafPathFilter() )
		
		# update ui for displaying the filter
		newFilterUI = None
		if newFilter is not None :
			newFilterUI = GafferUI.PathFilterWidget.create( newFilter )
		
		self.__filterFrame.setChild( newFilterUI )
		self.__filterFrame.setVisible( newFilterUI is not None )
			
		self.__filter = newFilter
	
	def __pathChanged( self, path ) :
	
		self.__updateFilter()
		
		# update the directory path and the listing path, but only if we're
		# in list mode rather than tree mode.
		if self.__directoryListing.getDisplayMode() == GafferUI.PathListingWidget.DisplayMode.List :
			pathCopy = path.copy()
			if pathCopy.isLeaf() :
				del pathCopy[-1]
			pathCopy.truncateUntilValid()
			with Gaffer.BlockedConnection( ( self.__dirPathChangedConnection, self.__listingPathChangedConnection ) ) :
				self.__dirPath[:] = pathCopy[:]
				self.__listingPath[:] = pathCopy[:]
		else :
			# if we're in tree mode then we instead scroll to display the new path
			self.__directoryListing.scrollToPath( path )
		
		# and update the selection in the listing
		if path.isLeaf() :
			self.__directoryListing.setSelectedPaths( [ path ] )
		else :
			self.__directoryListing.setSelectedPaths( [] )
			
	def __dirPathChanged( self, dirPath ) :
	
		# update the main path and the listing path
		dirPathCopy = dirPath.copy()
		dirPathCopy.truncateUntilValid()
		with Gaffer.BlockedConnection( ( self.__pathChangedConnection, self.__listingPathChangedConnection ) ) :
			self.__path[:] = dirPathCopy[:]
			self.__listingPath[:] = dirPathCopy[:]
		
	def __listingPathChanged( self, listingPath ) :
	
		assert( listingPath is self.__listingPath )
	
		# update the directory path and the main path
		with Gaffer.BlockedConnection( ( self.__pathChangedConnection, self.__dirPathChangedConnection ) ) :
			self.__dirPath[:] = listingPath[:]
			self.__path[:] = listingPath[:]
		
	def __displayModeButtonClicked( self, button ) :
	
		mode = self.__directoryListing.getDisplayMode()
		if mode == GafferUI.PathListingWidget.DisplayMode.List :
			mode = GafferUI.PathListingWidget.DisplayMode.Tree
			buttonImage = "pathListingList.png"
		else :
			mode = GafferUI.PathListingWidget.DisplayMode.List
			buttonImage = "pathListingTree.png"
			
		self.__directoryListing.setDisplayMode( mode )
		button.setImage( buttonImage )
		
		# if we're going back to list mode, then we need to update the directory and listing paths,
		# because they're not changed as we navigate in tree mode.
		if mode == GafferUI.PathListingWidget.DisplayMode.List :
			self.__pathChanged( self.__path )
		