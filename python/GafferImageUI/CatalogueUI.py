##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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
## - Could up/down in the Viewer cycle through the image list?

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
# _CataloguePath
##########################################################################

class _ImagesPath( Gaffer.Path ) :

	def __init__( self, images, path, root = "/", filter = None ) :

		Gaffer.Path.__init__( self, path, root, filter )

		self.__images = images

	def copy( self ) :

		return self.__class__( self.__images, self[:], self.root(), self.getFilter() )

	def isLeaf( self ) :

		return len( self ) > 0

	def _children( self ) :

		if len( self ) != 0 :
			return []

		return [
			self.__class__( self.__images, [ image.getName() ], self.root(), self.getFilter() )
			for image in self.__images
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
			self.__pathListing.setSortable( False )
			self.__pathListing.setHeaderVisible( False )
			self.__pathListingSelectionChangedConnection = self.__pathListing.selectionChangedSignal().connect(
				Gaffer.WeakMethod( self.__pathListingSelectionChanged )
			)
			self.__pathListingDragEnterConnection = self.__pathListing.dragEnterSignal().connect(
				Gaffer.WeakMethod( self.__pathListingDragEnter )
			)
			self.__pathListingDragLeaveConnection = self.__pathListing.dragLeaveSignal().connect(
				Gaffer.WeakMethod( self.__pathListingDragLeave )
			)
			self.__pathListingDropConnection = self.__pathListing.dropSignal().connect(
				Gaffer.WeakMethod( self.__pathListingDrop )
			)
			self.__pathListingKeyPressConnection = self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				addButton = GafferUI.Button( image = "pathChooser.png", hasFrame = False, toolTip = "Load image" )
				self.__addClickedConnection = addButton.clickedSignal().connect(
					Gaffer.WeakMethod( self.__addClicked )
				)

				self.__duplicateButton = GafferUI.Button( image = "duplicate.png", hasFrame = False, toolTip = "Duplicate selected image" )
				self.__duplicateButton.setEnabled( False )
				self.__duplicateButtonClickedConnection = self.__duplicateButton.clickedSignal().connect(
					Gaffer.WeakMethod( self.__duplicateClicked )
				)

				self.__exportButton = GafferUI.Button( image = "export.png", hasFrame = False, toolTip = "Export selected image" )
				self.__exportButton.setEnabled( False )
				self.__exportButtonClickedConnection = self.__exportButton.clickedSignal().connect(
					Gaffer.WeakMethod( self.__exportClicked )
				)

				self.__extractButton = GafferUI.Button( image = "extract.png", hasFrame = False, toolTip = "Create CatalogueSelect node for selected image" )
				self.__extractButton.setEnabled( False )
				self.__extractButtonClickedConnection = self.__extractButton.clickedSignal().connect(
					Gaffer.WeakMethod( self.__extractClicked )
				)

				GafferUI.Spacer( imath.V2i( 0 ), parenting = { "expand" : True } )

				self.__removeButton = GafferUI.Button( image = "delete.png", hasFrame = False, toolTip = "Remove selected image" )
				self.__removeButton.setEnabled( False )
				self.__removeClickedConnection = self.__removeButton.clickedSignal().connect(
					Gaffer.WeakMethod( self.__removeClicked )
				)

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

	def __removeClicked( self, *unused ) :

		indices = self.__indicesFromSelection()

		# If the user repeatedly clicks the delete button, we might end up in a
		# state, where selection hasn't been restored yet. In that case we
		# can't delete anything and will ignore the request.
		if not indices :
			return

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			for i, index in enumerate( reversed( sorted( indices ) ) ) :
				self.__images().removeChild( self.__images()[index] )
			self.getPlug().setValue( max( 0, index-1 ) )

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

		if self.__dropImage( event.data ) is None :
			return False

		self.__pathListing.setHighlighted( True )
		GafferUI.Pointer.setCurrent( "plus" )

		return True

	def __pathListingDragLeave( self, widget, event ) :

		self.__pathListing.setHighlighted( False )
		GafferUI.Pointer.setCurrent( None )
		return True

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
