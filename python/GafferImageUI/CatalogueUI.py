##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2019, Cinesite VFX Limited. All rights reserved.
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
import GafferImage
import GafferImageUI

## \todo
## Ideally Catalogue reordering wouldn't just be managed the UI layer, but
## the scope of changing this is somewhat large. When we need to do folders,
## then this will probably force us to sort this out. For now, is at least
## contained within just this file...

Gaffer.Metadata.registerNode(

	GafferImage.Catalogue,

	"description",
	"""
	Stores a catalogue of images to be browsed. Images can either be loaded
	from files or rendered directly into the catalogue.

	To send a live render to a Catalogue, an "ieDisplay" output definition
	should be used with the following parameters :

	- driverType : "ClientDisplayDriver"
	- displayHost : host name ("localhost" is sufficient for local renders)
	- displayPort : `GafferImage.Catalogue.displayDriverServer().portNumber()`
	- remoteDisplayType : "GafferImage::GafferDisplayDriver"
	- catalogue:name : The name of the catalogue to render to (optional)
	""",

	plugs = {

		"images" : [

			"description",
			"""
			Specifies the list of images currently
			stored in the catalogue.

			Either add images interactively
			using the UI, or use the API to construct
			Catalogue.Image plugs and parent them
			here.
			""",

			"plugValueWidget:type", "",

		],

		"imageIndex" : [

			"description",
			"""
			Specifies the index of the currently
			selected image. This forms the output
			from the catalogue node.
			""",

			"plugValueWidget:type", "GafferImageUI.CatalogueUI._ImageListing",
			"label", "",
			"layout:section", "Images",

		],

		"name" : [

			"description",
			"""
			Used to distinguish between catalogues, so that when
			multiple catalogues exist, it is possible to send a
			render to just one of them. Renders are matched
			to catalogues by comparing the "catalogue:name" parameter
			from the renderer output with the value of this plug.
			""",

		],

		"directory" : [

			"description",
			"""
			The directory where completed renders
			are saved. This allows them to remain
			in the catalogue for the next session.
			""",

			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"path:leaf", False,

		],

	},

)


##########################################################################
# Viewer hot-keys
##########################################################################

def addCatalogueHotkeys( editor ) :

	if not isinstance( editor, GafferUI.Viewer ) :
		return

	editor.keyPressSignal().connect( __viewerKeyPress, scoped = False )

def __viewerKeyPress( viewer, event ) :

	# Up/Down arrows need to walk upstream of the viewer input and look for
	# a Catalogue node and increment/decrement its active index

	if event.key not in ( "Down", "Up" ) :
		return False

	if not isinstance( viewer.view(), GafferImageUI.ImageView ) :
		return False

	catalogue = __findCatalogue( viewer.view() )
	if catalogue is None :
		return False

	__incrementImageIndex( catalogue, event.key )

	return True

def __findCatalogue( node ) :

	catalogue = node.ancestor( GafferImage.Catalogue )
	if catalogue is not None :
		return catalogue
	else :
		for inPlug in GafferImage.ImagePlug.RecursiveInputRange( node ) :
			upstreamPlug = inPlug.source()
			if upstreamPlug == inPlug or upstreamPlug.node() == node :
				continue
			catalogue = __findCatalogue( upstreamPlug.node() )
			if catalogue is not None :
				return catalogue

	return None

def __incrementImageIndex( catalogue, direction ) :

	indexPlug = catalogue["imageIndex"].source()

	if Gaffer.MetadataAlgo.readOnly( indexPlug ) or not indexPlug.settable() :
		return

	# Match the UI's top-to-bottom order instead of 'up is a larger number'
	increment = -1 if direction == "Up" else 1

	# The Catalog UI re-orders images internally using metadata, rather than by
	# shuffling plugs. As such, we can't just set imageIndex. We don't want to
	# be poking into the specifics of how this works, so for now we re-use
	# _ImagesPath as it knows all that logic.

	images = catalogue["images"].source().children()
	if len( images ) == 0 :
		return

	maxIndex = len( images ) - 1
	orderedImages = _ImagesPath( catalogue["images"].source(), [] )._orderedImages()

	# There are times when this can be out of sync with the number of images.
	# Generally when the UI hasn't been opened.
	currentPlugIndex = min( indexPlug.getValue(), maxIndex )

	catalogueIndex = orderedImages.index( images[currentPlugIndex] )
	nextIndex = max( min( catalogueIndex + increment, maxIndex ), 0 )
	nextPlugIndex = images.index( orderedImages[nextIndex] )

	if nextPlugIndex != currentPlugIndex :
		indexPlug.setValue( nextPlugIndex )

##########################################################################
# _CataloguePath
##########################################################################

class _ImagesPath( Gaffer.Path ) :

	indexMetadataName = 'image:index'

	def __init__( self, images, path, root = "/", filter = None ) :

		Gaffer.Path.__init__( self, path, root, filter )

		self.__images = images

	def copy( self ) :

		return self.__class__( self.__images, self[:], self.root(), self.getFilter() )

	def isLeaf( self ) :

		return len( self ) > 0

	def _orderedImages( self ) :

		# Avoid repeat lookups for plugs with no logical index by first getting all
		# images with their plug indices, then updating those with any metadata
		imageAndIndices = [ [ image, plugIndex ] for plugIndex, image in enumerate( self.__images.children() ) ]
		for imageAndIndex in imageAndIndices :
			logicalIndex = Gaffer.Metadata.value( imageAndIndex[0], _ImagesPath.indexMetadataName )
			if logicalIndex is not None :
				imageAndIndex[1] = logicalIndex

		return [ i[0] for i in sorted( imageAndIndices, key = lambda i : i[1] ) ]

	def _children( self ) :

		if len( self ) != 0 :
			return []

		return [
			self.__class__( self.__images, [ image.getName() ], self.root(), self.getFilter() )
			for image in self._orderedImages()
		]

	def _pathChangedSignalCreated( self ) :

		Gaffer.Path._pathChangedSignalCreated( self )

		# Connect to all the signals we need to in order
		# to emit pathChangedSignal at the appropriate times.

		self.__childAddedConnection = self.__images.childAddedSignal().connect( Gaffer.WeakMethod( self.__childAdded ) )
		self.__childRemovedConnection = self.__images.childRemovedSignal().connect( Gaffer.WeakMethod( self.__childRemoved ) )
		self.__nameChangedConnections = {
			image : image.nameChangedSignal().connect( Gaffer.WeakMethod( self.__nameChanged ) )
			for image in self.__images
		}

	def __childAdded( self, parent, child ) :

		assert( parent.isSame( self.__images ) )
		self.__nameChangedConnections[child] = child.nameChangedSignal().connect( Gaffer.WeakMethod( self.__nameChanged ) )
		self._emitPathChanged()

	def __childRemoved( self, parent, child ) :

		assert( parent.isSame( self.__images ) )
		del self.__nameChangedConnections[child]
		self._emitPathChanged()

	def __nameChanged( self, child ) :

		self._emitPathChanged()

##########################################################################
# _ImageListing
##########################################################################

class _ImageListing( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__column = GafferUI.ListContainer( spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__column, plug, **kw )

		with self.__column :

			self.__pathListing = GafferUI.PathListingWidget(
				_ImagesPath( self.__images(), [] ),
				columns = ( GafferUI.PathListingWidget.defaultNameColumn, ),
				allowMultipleSelection = True
			)
			self.__pathListing.setDragPointer( "" )
			self.__pathListing.setSortable( False )
			self.__pathListing.setHeaderVisible( False )
			self.__pathListing.selectionChangedSignal().connect(
				Gaffer.WeakMethod( self.__pathListingSelectionChanged ), scoped = False
			)
			self.__pathListing.dragEnterSignal().connect(
				Gaffer.WeakMethod( self.__pathListingDragEnter ), scoped = False
			)
			self.__pathListing.dragLeaveSignal().connect(
				Gaffer.WeakMethod( self.__pathListingDragLeave ), scoped = False
			)
			self.__pathListing.dragMoveSignal().connect(
				Gaffer.WeakMethod( self.__pathListingDragMove ), scoped = False
			)
			self.__pathListing.dropSignal().connect(
				Gaffer.WeakMethod( self.__pathListingDrop ), scoped = False
			)
			self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				addButton = GafferUI.Button( image = "pathChooser.png", hasFrame = False, toolTip = "Load image" )
				addButton.clickedSignal().connect( Gaffer.WeakMethod( self.__addClicked ), scoped = False )

				self.__duplicateButton = GafferUI.Button( image = "duplicate.png", hasFrame = False, toolTip = "Duplicate selected image" )
				self.__duplicateButton.setEnabled( False )
				self.__duplicateButton.clickedSignal().connect( Gaffer.WeakMethod( self.__duplicateClicked ), scoped = False )

				self.__exportButton = GafferUI.Button( image = "export.png", hasFrame = False, toolTip = "Export selected image" )
				self.__exportButton.setEnabled( False )
				self.__exportButton.clickedSignal().connect( Gaffer.WeakMethod( self.__exportClicked ), scoped = False )

				self.__extractButton = GafferUI.Button( image = "extract.png", hasFrame = False, toolTip = "Create CatalogueSelect node for selected image" )
				self.__extractButton.setEnabled( False )
				self.__extractButton.clickedSignal().connect( Gaffer.WeakMethod( self.__extractClicked ), scoped = False )

				GafferUI.Spacer( imath.V2i( 0 ), parenting = { "expand" : True } )

				self.__removeButton = GafferUI.Button( image = "delete.png", hasFrame = False, toolTip = "Remove selected image" )
				self.__removeButton.setEnabled( False )
				self.__removeButton.clickedSignal().connect( Gaffer.WeakMethod( self.__removeClicked ), scoped = False )

			GafferUI.Divider()

			with GafferUI.Collapsible( label = "Image Properties", collapsed = False ) :

				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 ) :

					with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
						GafferUI.Label( "Name" )
						self.__nameWidget = GafferUI.NameWidget( graphComponent = None )

					GafferUI.Label( "Description" )
					self.__descriptionWidget = GafferUI.MultiLineStringPlugValueWidget( plug = None )

		self._updateFromPlug()

	def _updateFromPlug( self ) :

		with self.getContext() :
			index = self.getPlug().getValue()

		images = self.__images()
		if len( images ) :
			image = images[index % len( images )]
			indices = self.__indicesFromSelection()
			if index not in indices :
				self.__pathListing.setSelection( IECore.PathMatcher( [ "/" + image.getName() ] ) )
			self.__descriptionWidget.setPlug( image["description"] )
			self.__nameWidget.setGraphComponent( image )
		else :
			self.__descriptionWidget.setPlug( None )
			self.__nameWidget.setGraphComponent( None )

		self.__column.setEnabled( self._editable() )

	def __catalogue( self ) :

		def walk( plug ) :

			if isinstance( plug.parent(), GafferImage.Catalogue ) :
				return plug.parent()

			for output in plug.outputs() :
				r = walk( output )
				if r is not None :
					return r

			return None

		return walk( self.getPlug() )

	def __images( self ) :

		return self.__catalogue()["images"].source()

	def __indicesFromSelection( self ) :
		indices = []
		selection = self.__pathListing.getSelection()
		for i, image in enumerate( self.__images() ) :
			if selection.match( "/" + image.getName() ) & selection.Result.ExactMatch :
				indices.append( i )

		return indices

	def __pathListingSelectionChanged( self, pathListing ) :

		indices = self.__indicesFromSelection()

		self.__removeButton.setEnabled( bool( indices ) )
		self.__extractButton.setEnabled( bool( indices ) )
		self.__exportButton.setEnabled( len( indices ) == 1 )
		self.__duplicateButton.setEnabled( bool( indices ) )

		if not indices :
			# No selection. This happens when the user renames
			# an image, because the selection is name based.
			# Calling _updateFromPlug() causes us to reselect
			# the correct image based on the value of the index
			# plug.
			self._updateFromPlug()
		else :
			# Deliberately not using an UndoScope as the user thinks
			# of this as making a selection, not changing a plug value.
			if self._editable() :
				if self.getPlug().getValue() not in indices :
					self.getPlug().setValue( indices[0] )

	def __addClicked( self, *unused ) :

		bookmarks = GafferUI.Bookmarks.acquire( self, category="image" )
		path = Gaffer.FileSystemPath( bookmarks.getDefault( self ) )
		path.setIncludeSequences( True )

		path.setFilter(
			Gaffer.FileSystemPath.createStandardFilter(
				GafferImage.ImageReader.supportedExtensions(),
				"Show only image files",
				includeSequenceFilter = True,
			)
		)

		dialogue = GafferUI.PathChooserDialogue( path, title = "Add image", confirmLabel = "Add", valid = True, leaf = True, bookmarks = bookmarks )
		dialogue.pathChooserWidget().pathListingWidget().setColumns(
			dialogue.pathChooserWidget().pathListingWidget().getColumns() +
			[ GafferUI.PathListingWidget.StandardColumn( "Frame Range", "fileSystem:frameRange" )  ]
		)

		path = dialogue.waitForPath( parentWindow = self.ancestor( GafferUI.Window ) )
		if not path :
			return

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.__images().addChild( GafferImage.Catalogue.Image.load( str( path ) ) )
			self.getPlug().setValue( len( self.__images() ) - 1 )

	def __metadataIndexToGraphComponentIndex( self, index ) :
		for i, image in enumerate( self.__images() ) :
			if index == Gaffer.Metadata.value( image, _ImagesPath.indexMetadataName ) :
				return i

	def __removeClicked( self, *unused ) :

		indices = self.__indicesFromSelection()

		# If the user repeatedly clicks the delete button, we might end up in a
		# state, where selection hasn't been restored yet. In that case we
		# can't delete anything and will ignore the request.
		if not indices :
			return

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			for index in reversed( sorted( indices ) ) :
				metadataIndex = Gaffer.Metadata.value( self.__images()[index], _ImagesPath.indexMetadataName )
				self.__images().removeChild( self.__images()[index] )

			# Figure out new selection
			if not metadataIndex :
				selectionIndex = index - 1
			else:
				selectionIndex = self.__metadataIndexToGraphComponentIndex( metadataIndex - 1 )

			self.getPlug().setValue( max( 0, selectionIndex ) )

	def __extractClicked( self, *unused ) :

		node = self.getPlug().node()
		catalogue = self.__catalogue()
		outPlug = next( p for p in node.children( GafferImage.ImagePlug ) if catalogue.isAncestorOf( p.source() ) )

		for index in self.__indicesFromSelection() :
			image = self.__images()[index]

			extractNode = GafferImage.CatalogueSelect()
			extractNode["in"].setInput( outPlug )
			extractNode["imageName"].setValue( image.getName() )

			node.parent().addChild( extractNode )

	def __exportClicked( self, *unused ) :

		bookmarks = GafferUI.Bookmarks.acquire( self, category="image" )
		path = Gaffer.FileSystemPath( bookmarks.getDefault( self ) )

		path.setFilter(
			Gaffer.FileSystemPath.createStandardFilter(
				GafferImage.ImageReader.supportedExtensions(),
				"Show only image files",
				includeSequenceFilter = True,
			)
		)

		dialogue = GafferUI.PathChooserDialogue( path, title = "Export image", confirmLabel = "Export", leaf = True, bookmarks = bookmarks )

		path = dialogue.waitForPath( parentWindow = self.ancestor( GafferUI.Window ) )
		if not path :
			return

		index = self.__indicesFromSelection()[0]  # button is disabled unless exactly one image is selected
		with GafferUI.ErrorDialogue.ErrorHandler( parentWindow = self.ancestor( GafferUI.Window ) ) :
			self.__images()[index].save( str( path ) )

	def __duplicateClicked( self, *unused ) :

		indices = self.__indicesFromSelection()

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			for index in indices :
				image = self.__images()[index]
				imageCopy = GafferImage.Catalogue.Image( image.getName() + "Copy",  flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
				self.__images().addChild( imageCopy )
				imageCopy.copyFrom( image )

			self.getPlug().setValue( len( self.__images() ) - 1 )

	def __dropImage( self, eventData ) :

		if not self.__catalogue()["directory"].getValue() :
			return None

		if isinstance( eventData, GafferImage.ImagePlug ) :
			return eventData
		elif isinstance( eventData, Gaffer.Node ) :
			return next( iter( eventData.children( GafferImage.ImagePlug ) ), None )
		elif isinstance( eventData, Gaffer.Set ) and len( eventData ) == 1 :
			return self.__dropImage( eventData[0] )
		else :
			return None

	def __pathListingDragEnter( self, widget, event ) :

		if isinstance( event.data, IECore.StringVectorData ) :
			# Allow reordering of images
			self.__moveToPath = None
			return True

		if self.__dropImage( event.data ) is None :
			return False

		self.__pathListing.setHighlighted( True )
		GafferUI.Pointer.setCurrent( "plus" )

		return True

	def __pathListingDragLeave( self, widget, event ) :

		self.__pathListing.setHighlighted( False )
		GafferUI.Pointer.setCurrent( None )
		return True

	def __pathListingDragMove( self, listing, event ) :

		if not event.data or not isinstance( event.data, IECore.StringVectorData ) :
			return

		targetPath = self.__pathListing.pathAt( event.line.p0 )
		if targetPath and targetPath == self.__moveToPath :
			# We have done the work already, the mouse is just still over the same path
			return
		self.__moveToPath = targetPath

		images = _ImagesPath( self.__images(), [] )._orderedImages()
		imagesToMove = [image for image in images if '/'+image.getName() in event.data]

		# Because of multi-selection it's possible to move the mouse over a selected image.
		# That's not a valid image we want to replace with the current selection - do nothing.
		if str( targetPath )[1:] in [image.getName() for image in imagesToMove] :
			return

		imageToReplace = None

		if targetPath is not None :
			targetName = str( targetPath )[1:]
			for image in images :
				if not image.getName() == targetName :
					continue

				imageToReplace = image
				break
		else :
			# Drag has gone above or below all listed items. Use closest image.
			imageToReplace = images[0] if event.line.p0.y < 1 else images[-1]

		if not imageToReplace or imageToReplace in imagesToMove :
			return

		# Reorder images and reassign indices accordingly.
		previous = None
		for image in imagesToMove :

			currentIndex = images.index( image )
			images[currentIndex] = None  # Add placeholder so we don't mess with indices

			if previous :
				# Just insert after previous image to preserve odering of selected images
				newIndex = images.index( previous ) + 1
			else :
				newIndex = images.index( imageToReplace )
				if currentIndex < newIndex :  # Make up for the placeholder
					newIndex += 1

			images.insert( newIndex, image )
			previous = image

		for idx, image in enumerate( [image for image in images if image ] ) :
			Gaffer.Metadata.registerValue( image, _ImagesPath.indexMetadataName, idx )

		self.__pathListing.getPath().pathChangedSignal()( self.__pathListing.getPath() )

	def __pathListingDrop( self, widget, event ) :

		image = self.__dropImage( event.data )
		if image is None :
			return False

		with self.getContext() :
			fileName = self.__catalogue().generateFileName( image )
			imageWriter = GafferImage.ImageWriter()
			imageWriter["in"].setInput( image )
			imageWriter["fileName"].setValue( fileName )
			imageWriter["task"].execute()

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			loadedImage = GafferImage.Catalogue.Image.load( fileName )
			loadedImage.setName( image.node().getName() )
			self.__images().addChild( loadedImage )
			self.getPlug().setValue( len( self.__images() ) - 1 )

		self.__pathListing.setHighlighted( False )
		GafferUI.Pointer.setCurrent( None )

		return True

	def __keyPress( self, imageListing, keyEvent ) :

		if keyEvent.key in ['Delete', 'Backspace'] :
			self.__removeClicked()
			return True

		return False

GafferUI.Pointer.registerPointer( "plus", GafferUI.Pointer( "plus.png" ) )
