##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

import functools
import imath

import IECore

import Gaffer
import GafferUI

class PathChooserWidget( GafferUI.Widget ) :

	def __init__( self, path, previewTypes=[], allowMultipleSelection=False, bookmarks=None, **kw ) :

		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=8 )

		GafferUI.Widget.__init__( self, self.__column, **kw )

		# we use this temporary path for our child widgets while constructing, and then call
		# self.setPath() to replace it with the real thing. this lets us avoid duplicating the
		# logic we need in setPath().
		tmpPath = Gaffer.DictPath( {}, "/" )
		with self.__column :

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 ) as browserFrame :

				# Override this so we can customise the appearance of only this list container
				browserFrame._qtWidget().setObjectName( "gafferPathListingContainer" )

				# row for manipulating current directory
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4, borderWidth = 8 ) :

					self.__displayModeButton = GafferUI.Button( image = "pathListingTree.png", hasFrame=False )
					self.__displayModeButton.setToolTip( "Toggle between list and tree views" )
					self.__displayModeButton.clickedSignal().connect( Gaffer.WeakMethod( self.__displayModeButtonClicked ) )

					self.__bookmarksButton = GafferUI.MenuButton(
						image = "bookmarks.png",
						hasFrame=False,
						menu = GafferUI.Menu( Gaffer.WeakMethod( self.__bookmarksMenuDefinition ) ),
					)
					self.__bookmarksButton.setToolTip( "Bookmarks" )
					self.__bookmarksButton.dragEnterSignal().connect( Gaffer.WeakMethod( self.__bookmarksButtonDragEnter ) )
					self.__bookmarksButton.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__bookmarksButtonDragLeave ) )
					self.__bookmarksButton.dropSignal().connect( Gaffer.WeakMethod( self.__bookmarksButtonDrop ) )

					reloadButton = GafferUI.Button( image = "refresh.png", hasFrame=False )
					reloadButton.setToolTip( "Refresh view" )
					reloadButton.clickedSignal().connect( Gaffer.WeakMethod( self.__reloadButtonClicked ) )

					upButton = GafferUI.Button( image = "pathUpArrow.png", hasFrame=False )
					upButton.setToolTip( "Up one level" )
					upButton.clickedSignal().connect( Gaffer.WeakMethod( self.__upButtonClicked ) )

					GafferUI.Spacer( imath.V2i( 2, 2 ) )

					self.__dirPathWidget = GafferUI.PathWidget( tmpPath )

				# directory listing and preview widget
				with GafferUI.SplitContainer(
					GafferUI.SplitContainer.Orientation.Horizontal,
					parenting = { "expand" : True }
				) as splitContainer :

					self.__directoryListing = GafferUI.PathListingWidget(
						tmpPath,
						selectionMode = GafferUI.PathListingWidget.SelectionMode.Rows if allowMultipleSelection else GafferUI.PathListingWidget.SelectionMode.Row
					)
					self.__directoryListing.displayModeChangedSignal().connect( Gaffer.WeakMethod( self.__displayModeChanged ) )
					if len( previewTypes ) :
						self.__previewWidget = GafferUI.CompoundPathPreview( tmpPath, childTypes=previewTypes )
					else :
						self.__previewWidget = None

				if len( splitContainer ) > 1 :
					splitContainer.setSizes( [ 2, 1 ] ) # give priority to the listing over the preview

				# filter section
				self.__filterFrame = GafferUI.Frame( borderWidth=4, borderStyle=GafferUI.Frame.BorderStyle.None_ )
				self.__filter = None

			# path
			self.__pathWidget = GafferUI.PathWidget( tmpPath )
			self.__pathWidget.setVisible( allowMultipleSelection == False )

		self.__pathSelectedSignal = GafferUI.WidgetSignal()

		self.__directoryListing.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__listingSelectionChanged ) )
		self.__directoryListing.pathSelectedSignal().connect( Gaffer.WeakMethod( self.__pathSelected ) )
		self.__pathWidget.activatedSignal().connect( Gaffer.WeakMethod( self.__pathSelected ) )

		self.__path = None
		self.setPath( path )
		self.setBookmarks( bookmarks )

	def getPath( self ) :

		return self.__path

	def setPath( self, path ) :

		if path.isSame( self.__path ) :
			return

		self.__path = path

		# the path bar at the top of the window uses a modified path to make sure it can
		# only display directories and never be used to choose leaf files. we apply the necessary filter
		# to achieve that in __updateFilter. we don't worry about getting the contents of this path correct
		# immediately - we'll do that in __pathChanged() at the end of this method.
		self.__dirPath = self.__path.copy()
		self.__dirPathWidget.setPath( self.__dirPath )

		# the listing also uses a modified path of it's own.
		self.__listingPath = self.__path.copy()
		self.__directoryListing.setPath( self.__listingPath )

		# the main path widget is actually allowed to edit the real path
		self.__pathWidget.setPath( self.__path )

		# and the preview widget must also use the real path
		if self.__previewWidget is not None :
			self.__previewWidget.setPath( self.__path )

		# set up the signals we need to keep everything glued together
		self.__pathChangedConnection = self.__path.pathChangedSignal().connect(
			Gaffer.WeakMethod( self.__pathChanged ), scoped = True
		)
		self.__dirPathChangedConnection = self.__dirPath.pathChangedSignal().connect(
			Gaffer.WeakMethod( self.__dirPathChanged ), scoped = True
		)
		self.__listingPathChangedConnection = self.__listingPath.pathChangedSignal().connect(
			Gaffer.WeakMethod( self.__listingPathChanged ), scoped = True
		)

		self.__updateFilter()
		self.__pathChanged( self.__path )

	def getBookmarks( self ) :

		return self.__bookmarks

	def setBookmarks( self, bookmarks ) :

		self.__bookmarks = bookmarks
		self.__bookmarksButton.setVisible( self.__bookmarks is not None )

	## Returns the PathWidget used for text-based path entry. Note that this Widget is hidden when multiple
	# selection is enabled.
	def pathWidget( self ) :

		return self.__pathWidget

	## Returns the PathListingWidget used for displaying the paths to choose from.
	def pathListingWidget( self ) :

		return self.__directoryListing

	## Returns the PathWidget used for displaying and editing the current directory.
	def directoryPathWidget( self ) :

		return self.__dirPathWidget

	## This signal is emitted when the user has selected a path.
	def pathSelectedSignal( self ) :

		return self.__pathSelectedSignal

	def __listingSelectionChanged( self, widget ) :

		assert( widget is self.__directoryListing )

		selection = self.__directoryListing.getSelection()
		if selection.isEmpty() :
			return

		with Gaffer.Signals.BlockedConnection( self.__pathChangedConnection ) :
			self.__path.setFromString( selection.paths()[0] )

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
		if self.__filter is not None and self.__filter.isSame( newFilter ) :
			return

		# update the directory path filter to include
		# the new filter, but with the additional removal
		# of leaf paths. block the signal because otherwise
		# we'd end up truncating the main path in __dirPathChanged.
		with Gaffer.Signals.BlockedConnection( self.__dirPathChangedConnection ) :
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
			with Gaffer.Signals.BlockedConnection( ( self.__dirPathChangedConnection, self.__listingPathChangedConnection ) ) :
				self.__dirPath.setFromPath( pathCopy )
				self.__listingPath.setFromPath( pathCopy )
		else :
			# if we're in tree mode then we instead scroll to display the new path
			self.__directoryListing.scrollToPath( path )

		# and update the selection in the listing
		if path.isLeaf() :
			self.__directoryListing.setSelection( IECore.PathMatcher( [ str( path ) ] ) )
		else :
			self.__directoryListing.setSelection( IECore.PathMatcher() )

	def __dirPathChanged( self, dirPath ) :

		# update the main path and the listing path
		dirPathCopy = dirPath.copy()
		dirPathCopy.truncateUntilValid()
		with Gaffer.Signals.BlockedConnection( ( self.__pathChangedConnection, self.__listingPathChangedConnection ) ) :
			self.__path.setFromPath( dirPathCopy )
			self.__listingPath.setFromPath( dirPathCopy )

	def __listingPathChanged( self, listingPath ) :

		assert( listingPath.isSame( self.__listingPath ) )

		# update the directory path and the main path
		with Gaffer.Signals.BlockedConnection( ( self.__pathChangedConnection, self.__dirPathChangedConnection ) ) :
			self.__dirPath[:] = listingPath[:]
			self.__path[:] = listingPath[:]

	def __displayModeButtonClicked( self, button ) :

		mode = self.__directoryListing.getDisplayMode()
		if mode == GafferUI.PathListingWidget.DisplayMode.List :
			mode = GafferUI.PathListingWidget.DisplayMode.Tree
		else :
			mode = GafferUI.PathListingWidget.DisplayMode.List

		self.__directoryListing.setDisplayMode( mode )

		# if we're going back to list mode, then we need to update the directory and listing paths,
		# because they're not changed as we navigate in tree mode.
		if mode == GafferUI.PathListingWidget.DisplayMode.List :
			self.__pathChanged( self.__path )

	def __displayModeChanged( self, pathListing ) :

		assert( pathListing is self.__directoryListing )

		if pathListing.getDisplayMode() == GafferUI.PathListingWidget.DisplayMode.List :
			buttonImage = "pathListingTree.png"
		else :
			buttonImage = "pathListingList.png"

		self.__displayModeButton.setImage( buttonImage )

	def __bookmarksMenuDefinition( self ) :

		m = IECore.MenuDefinition()

		unbookmarkableLocations = set()
		testPath = self.__dirPath.copy()
		for name in self.__bookmarks.names() :
			bookmark = self.__bookmarks.get( name, forWidget=self )
			testPath.setFromString( bookmark )
			m.append(
				"/" + name,
				{
					"command" : functools.partial( self.__path.setFromString, bookmark ),
					"active" : testPath.isValid(),
					"description" : bookmark,
				}
			)
			unbookmarkableLocations.add( bookmark )

		recents = self.__bookmarks.recents()
		if recents :
			m.append( "/RecentDivider", { "divider" : True } )
			for i, bookmark in enumerate( reversed( recents ) ) :
				testPath.setFromString( bookmark )
				m.append(
					"/Recent/%d" % i,
					{
						"command" : functools.partial( self.__path.setFromString, bookmark ),
						"active" : testPath.isValid(),
						"description" : bookmark,
						"label" : bookmark,
					}
				)

		m.append( "/SaveDeleteDivider", { "divider" : True } )

		for name in self.__bookmarks.names( persistent=True ) :
			m.append( "/Delete/" + name, { "command" : functools.partial( self.__bookmarks.remove, name ) } )

		m.append( "/Add Bookmark...", {
			"command" : Gaffer.WeakMethod( self.__saveBookmark ),
			"active" : self.__dirPath.isValid() and str( self.__dirPath ) not in unbookmarkableLocations,
		} )

		return m

	def __bookmarksButtonDropPath( self, event ) :

		string = None
		if isinstance( event.data, IECore.StringData ) :
			string = event.data.value
		elif isinstance( event.data, IECore.StringVectorData ) and len( event.data ) == 1 :
			string = event.data[0]

		if string is None :
			return None

		for name in self.__bookmarks.names() :
			if string == self.__bookmarks.get( name ) :
				return None

		testPath = self.__path.copy()
		testPath.setFromString( string )
		if not testPath.isValid() :
			return None

		return testPath

	def __bookmarksButtonDragEnter( self, button, event ) :

		if self.__bookmarksButtonDropPath( event ) is None :
			return False

		button.setHighlighted( True )
		return True

	def __bookmarksButtonDragLeave( self, button, event ) :

		button.setHighlighted( False )
		return True

	def __bookmarksButtonDrop( self, button, event ) :

		GafferUI.Pointer.setCurrent( None )
		self.__saveBookmark( self.__bookmarksButtonDropPath( event ) )
		button.setHighlighted( False )

	def __saveBookmark( self, path = None ) :

		if path is None :
			path = self.__dirPath

		name = path[-1] if len( path ) else "Root"
		d = GafferUI.TextInputDialogue( initialText=name, title="Save Bookmark", confirmLabel="Save" )
		name = d.waitForText( parentWindow = self.ancestor( GafferUI.Window ) )

		if name is not None :
			self.__bookmarks.add( name, str( path ), persistent=True )
