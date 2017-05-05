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
			)
			self.__pathListing.setSortable( False )
			self.__pathListing.setHeaderVisible( False )
			self.__pathListingSelectionChangedConnection = self.__pathListing.selectionChangedSignal().connect(
				Gaffer.WeakMethod( self.__pathListingSelectionChanged )
			)

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

				GafferUI.Spacer( IECore.V2i( 0 ), parenting = { "expand" : True } )

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

		imagePaths = self.__pathListing.getPath().children()
		if imagePaths :
			index = index % len( imagePaths )
			self.__pathListing.setSelectedPaths( imagePaths[index] )
			self.__descriptionWidget.setPlug( self.__images()[index]["description"] )
			self.__nameWidget.setGraphComponent( self.__images()[index] )
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

	def __indexFromSelection( self ) :

		paths = self.__pathListing.getSelectedPaths()
		if len( paths ) != 1 :
			return None

		for i, image in enumerate( self.__images() ) :
			if image.getName() == paths[0][-1] :
				return i

		return None

	def __pathListingSelectionChanged( self, pathListing ) :

		index = self.__indexFromSelection()
		self.__removeButton.setEnabled( index is not None )
		self.__exportButton.setEnabled( index is not None )
		self.__duplicateButton.setEnabled( index is not None )
		# Deliberately not using an UndoScope as the user thinks
		# of this as making a selection, not changing a plug value.
		if self._editable() :
			self.getPlug().setValue( index if index is not None else 0 )

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

		index = self.__indexFromSelection()
		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.__images().removeChild( self.__images()[index] )
			self.getPlug().setValue( max( 0, index - 1 ) )

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

		index = self.__indexFromSelection()
		with GafferUI.ErrorDialogue.ErrorHandler( parentWindow = self.ancestor( GafferUI.Window ) ) :
			self.__images()[index].save( str( path ) )

	def __duplicateClicked( self, *unused ) :

		index = self.__indexFromSelection()
		image = self.__images()[index]

		with self.getContext() :
			fileName = image["fileName"].getValue()
			directory = self.__catalogue()["directory"].getValue()
			directory = self.getContext().substitute( directory )

		if not fileName :
			# It's a render
			fileName = self.__catalogue().generateFileName( image )
			image.save( fileName )

		duplicateImage = GafferImage.Catalogue.Image.load( fileName )
		duplicateImage.setName( image.getName() + "Copy" )

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.__images().addChild( duplicateImage )
			self.getPlug().setValue( len( self.__images() ) - 1 )

##########################################################################
# Display server management. This would all be in Catalogue.cpp if it
# were not for the need to operate on the UI thread.
##########################################################################

def __driverCreated( driver, parameters ) :

	# The driverCreatedSignal() is emitted on the server thread,
	# but we can only make node graph edits from the UI thread,
	# so we must use `executeOnUIThread()`.
	GafferUI.EventLoop.executeOnUIThread( functools.partial( __driverCreatedUI, driver, parameters ) )

def __driverCreatedUI( driver, parameters ) :

	GafferImage.Catalogue.driverCreated( driver, parameters )

def __imageReceived( plug ) :

	GafferUI.EventLoop.executeOnUIThread( functools.partial( __imageReceivedUI, plug ) )

def __imageReceivedUI( plug ) :

	GafferImage.Catalogue.imageReceived( plug )

GafferImage.Display.driverCreatedSignal().connect( functools.partial( __driverCreated ), scoped = False )
GafferImage.Display.imageReceivedSignal().connect( functools.partial( __imageReceived ), scoped = False )
