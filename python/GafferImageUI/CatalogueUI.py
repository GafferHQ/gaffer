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
import six
import imath

from collections import namedtuple, OrderedDict

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

##########################################################################
# Column Configuration
#
# All of the Catalogue's columns are configurable. Gaffer provides a default
# set of columns that can be extended or replaced via the registration of new
# names or re-registration of existing ones.
#
# The columns displayed by a Catalogue are controlled by the
# "catalogue:columns" [StringVectorData] metadata on its `imageIndex` plug.
# Default columns are stored via a class registration, ie:
#
#   Gaffer.Metadata.registerValue(
#       GafferImage.Catalogue, "imageIndex",
#       "catalogue:columns", [ ... ]
#   )
#
# This should consist of an ordered list of the `names` of columns registered
# via the `CatalogueUI.registerColumns` method.
##########################################################################

__registeredColumns = OrderedDict()
_columnsMetadataKey = "catalogue:columns"

## The Column class extends the PathColumn class to simplify the process of
# creating a custom column for the Catalogue. Subclasses must implement
# `_imageCellData()`.
class Column( GafferUI.PathColumn ) :

	def __init__( self, title ) :

		GafferUI.PathColumn.__init__( self )

		self.__title = IECore.StringData( title )

	def title( self ) :

		return self.__title.value

	## Calls `_imageCellData()`.
	def cellData( self, path, canceller ) :

		image = path.property( "catalogue:image" )
		catalogue = path.property( "catalogue" )

		# Suppress error. The GraphEditor will be displaying the
		# error anyway, as will the standard type column, and we're
		# not in a position to do anything more helpful.
		with IECore.IgnoredExceptions( Gaffer.ProcessException ) :

			# Call `_imageCellData()` in a context which causes the Catalogue
			# to output the image of interest.
			with Gaffer.Context( catalogue.scriptNode().context() ) as context :
				context["catalogue:imageName"] = image.getName()
				try :
					return self._imageCellData( image, catalogue )
				except NotImplementedError :
					# Backwards compatibility for deprecated API.
					if isinstance( self, IconColumn ) :
						return self.CellData( icon = self.value( image, catalogue ) + ".png" )
					else :
						return self.CellData( value = self.value( image, catalogue ) )

		return self.CellData()

	def headerData( self, canceller ) :

		return self.CellData( value = self.__title )

	## Called to generate a cell from an image in
	# the Catalogue. Must be implemented by derived classes to return
	# `PathColumn.CellData`.
	# Arguments :
	#
	# - `image` : The `GafferImage.Catalogue.Image` plug for the cell
	#   (not to be confused with a standard ImagePlug).
	# - `catalogue` : The `GafferImage.Catalogue` being displayed.
	#
	# Called in a context where `catalogue["out"]` provides the
	# correct image for the cell.
	def _imageCellData( self, image, catalogue ) :

		raise NotImplementedError

# Registers a new column or overwrites an existing column. Registered columns
# appear in the Catalogue header context menu, and can be set as default
# columns in the "catalogue:columns" metadata on Catalogue's `imageIndex` plug.
# The registered name is used for the menu path when presenting available columns
# to the user. As such, it can contain `/` for sub-menus and should be formatted
# with appropriate case/spaces.
def registerColumn( name, column ) :

	__registeredColumns[ name ] = column

# Removes a column. It will no longer show up in the Catalogue UI and can't be
# set as a default column.
def deregisterColumn( name ) :

	if name in __registeredColumns :
		del __registeredColumns[ name ]

# Returns the instance of a Column class registered for `name` or
# None if no column has been registered.
def column( name ) :

	return __registeredColumns.get( name, None )

# Returns all registered column names
def registeredColumns() :

	return __registeredColumns.keys()

# Convenience Column subclasses
# =============================

## \deprecated. Derive from Column and implement `_imageCellData()`
# instead.
class IconColumn( Column ) :

	pass

# Convenience class for simple columns that derive the cell value
# from a callable. e.g.
#
#   `SimpleColumn( "Name", lambda image, catalogue : image.getName() ) )`
#
class SimpleColumn( Column ) :

	def __init__( self, title, valueProvider ) :

		Column.__init__( self, title )
		self.__valueProvider = valueProvider

	def _imageCellData( self, image, catalogue ) :

		return self.CellData( value = self.__valueProvider( image, catalogue ) )

# A Columns class that retrieves its value from the catalogue item's image
# metadata. If multiple names are provided, the first one present will be used,
# allowing a single column to support several source names depending on the
# image's origin.
class ImageMetadataColumn( Column ) :

	def __init__( self, title, nameOrNames, defaultValue = None ) :

		Column.__init__( self, title )

		if isinstance( nameOrNames, six.string_types ) :
			nameOrNames = [ nameOrNames, ]

		self.__names = nameOrNames
		self.__defaultValue = defaultValue

	def _imageCellData( self, image, catalogue ) :

		value = self.__defaultValue

		metadata = catalogue["out"].metadata()
		for name in self.__names :
			metadataValue = metadata.get( name, None )
			if metadataValue is not None :
				value = metadataValue
				break

		return self.CellData( value = value )

# A Column class that retrieves its value from render-time context variable
# values passed through the catalogue item's image metadata.  If multiple names
# are provided, the first present context entry will be used. Note: Not all
# context variables are available via image metadata, the exact list is renderer
# dependent, but it is generally limited to basic value types
class ContextVariableColumn( ImageMetadataColumn ) :

	def __init__( self, title, nameOrNames, defaultValue = None ) :

		if isinstance( nameOrNames, six.string_types ) :
			nameOrNames = [ nameOrNames, ]

		names = [ "gaffer:context:%s" % name for name in nameOrNames ]
		ImageMetadataColumn.__init__( self, title, names, defaultValue )

# Standard Columns
# ================

class __StatusIconColumn( Column ) :

	def __init__( self ) :

		Column.__init__( self, "" )

	def _imageCellData( self, image, catalogue ) :

		icon = "catalogueStatusDisplay.png"
		toolTip = None

		fileName = image["fileName"].getValue()
		if fileName :
			icon = "catalogueStatusDisk.png"
			# Attempt to read the metadata to check the image is loadable. Given other columns
			# are going to do this anyway, we're not adding too much overhead here.
			try :
				catalogue["out"].metadata()
			except Gaffer.ProcessException as e :
				icon = "errorSmall.png"
				toolTip = str( e )

		return self.CellData( icon = icon, toolTip = toolTip )

registerColumn( "Status", __StatusIconColumn() )
registerColumn( "Name", GafferUI.PathListingWidget.defaultNameColumn )
registerColumn( "Frame", ContextVariableColumn( "Frame", "frame" ) )
registerColumn( "Description", ImageMetadataColumn( "Description", "ImageDescription" ) )

# Image properties

def __resolutionColumnValueProvider( image, catalogue ) :

	format_ = catalogue["out"].format()
	return "%d x %d" % ( format_.width(), format_.height() )

def __formatBox( box ) :

	return "(%d %d) - (%d, %d)" % ( box.min().x, box.min().y, box.max().x, box.max().y )

registerColumn(
	"Image/Resolution",
	SimpleColumn( "Resolution", __resolutionColumnValueProvider )
)
registerColumn(
	"Image/Channels",
	SimpleColumn( "Channels", lambda _, c : ", ".join( c["out"].channelNames() ) )
)
registerColumn(
	"Image/Type",
	SimpleColumn( "Image Type", lambda _, c : "Deep" if c["out"].deep() else "Flat" )
)
registerColumn(
	"Image/Pixel Aspect Ratio",
	SimpleColumn( "P. Aspect", lambda _, c : c["out"].format().getPixelAspect() )
)
registerColumn(
	"Image/Data Window",
	SimpleColumn( "Data Window", lambda _, c : __formatBox( c["out"].dataWindow() ) )
)
registerColumn(
	"Image/Display Window",
	SimpleColumn( "Display Window", lambda _, c : __formatBox( c["out"].format().getDisplayWindow() ) )
)

# Default visible column set

Gaffer.Metadata.registerValue(
	GafferImage.Catalogue, "imageIndex", _columnsMetadataKey,
	IECore.StringVectorData( [ "Status", "Name" ] )
)

##########################################################################
# Node registration
##########################################################################

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

Gaffer.Metadata.registerValue( GafferImage.Catalogue.Image, "renameable", True )

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

	if event.key not in ( "Down", "Up", "D" ) :
		return False

	if not isinstance( viewer.view(), GafferImageUI.ImageView ) :
		return False

	catalogue = Gaffer.NodeAlgo.findUpstream(
		viewer.view(),
		lambda node : isinstance( node, GafferImage.Catalogue ),
		order = Gaffer.NodeAlgo.VisitOrder.DepthFirst
	)

	if catalogue is None :
		return False

	if event.key in ( "Down", "Up" ) :
		__incrementImageIndex( catalogue, event.key )
		return True
	elif event.key == "D" and event.modifiers == event.Modifiers.Control :
		__duplicateCurrentImage( catalogue )
		return True

	return False

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

def __duplicateCurrentImage( catalogue ) :

	currentIndex = catalogue["imageIndex"].getValue()
	with Gaffer.UndoScope( catalogue.ancestor( Gaffer.ScriptNode ) ) :
		_duplicateImages( catalogue, currentIndex )

##########################################################################
# Shared utility functions, these would ideally form a more public API for
# manipulating a catalogue
##########################################################################

# Duplicates images at the specified plug-based indices, returning a list of
# plug indices that were inserted.
def _duplicateImages( catalogue, plugIndices ) :

	if not isinstance( plugIndices, ( list, tuple ) ) :
		plugIndices = ( plugIndices, )

	images = catalogue["images"].source()
	# As we may be inserting more than one image, keep a copy of the original
	# list so the selection indices remain valid
	sourceImages = [ i for i in images.children() ]
	# We need to insert the duplicate before the source, as it's usually
	# used to snapshot in-progress renders.
	orderedImages = _ImagesPath( images, [] )._orderedImages()

	insertions = []

	for index in plugIndices :
		image = sourceImages[ index ]
		suffix = "Copy" if image["fileName"].getValue() else "Snapshot1"
		uiInsertionIndex = orderedImages.index( image )
		imageCopy = GafferImage.Catalogue.Image( image.getName() + suffix, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		images.addChild( imageCopy )
		imageCopy.copyFrom( image )
		orderedImages.insert( uiInsertionIndex, imageCopy )
		insertions.append( len(images) - 1 )

	_ImagesPath._updateUIIndices( orderedImages )

	return insertions

##########################################################################
# _CataloguePath
##########################################################################

def _findSourceCatalogue( imagesPlug ) :

	def walk( plug ) :

		if isinstance( plug.parent(), GafferImage.Catalogue ) :
			return plug.parent()

		for output in plug.outputs() :
			r = walk( output )
			if r is not None :
				return r

		return None

	return walk( imagesPlug )

class _ImagesPath( Gaffer.Path ) :

	indexMetadataName = 'image:index'

	def __init__( self, images, path, root = "/", filter = None ) :

		Gaffer.Path.__init__( self, path, root, filter )

		self.__images = images
		self.__catalogue = _findSourceCatalogue( images )

	def copy( self ) :

		return self.__class__( self.__images, self[:], self.root(), self.getFilter() )

	def isLeaf( self, canceller = None ) :

		return len( self ) > 0

	def propertyNames( self, canceller = None ) :

		return Gaffer.Path.propertyNames( self ) + [ "catalogue", "catalogue:image" ]

	def property( self, name, canceller = None ) :

		if name == "catalogue" :
			return self.__catalogue
		elif name == "catalogue:image" :
			return self.__images[self[-1]]
		else :
			return Gaffer.Path.property( self, name )

	def cancellationSubject( self ) :

		return self.__images

	def _orderedImages( self ) :

		# Avoid repeat lookups for plugs with no ui index by first getting all
		# images with their plug indices, then updating those with any metadata
		imageAndIndices = [ [ image, plugIndex ] for plugIndex, image in enumerate( self.__images.children() ) ]
		for imageAndIndex in imageAndIndices :
			uiIndex = Gaffer.Metadata.value( imageAndIndex[0], _ImagesPath.indexMetadataName )
			if uiIndex is not None :
				imageAndIndex[1] = uiIndex

		return [ i[0] for i in sorted( imageAndIndices, key = lambda i : i[1] ) ]

	def _children( self, canceller ) :

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

		self.__childAddedConnection = self.__images.childAddedSignal().connect( Gaffer.WeakMethod( self.__childAdded ), scoped = True )
		self.__childRemovedConnection = self.__images.childRemovedSignal().connect( Gaffer.WeakMethod( self.__childRemoved ), scoped = True )
		self.__cataloguePlugDirtiedConnection = self.__catalogue.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__cataloguePlugDirtied ), scoped = True )
		self.__nameChangedConnections = {
			image : image.nameChangedSignal().connect( Gaffer.WeakMethod( self.__nameChanged ), scoped = True )
			for image in self.__images
		}

	@staticmethod
	def _updateUIIndices( orderedImages ) :

		for i, image in enumerate( orderedImages ) :
			Gaffer.Metadata.registerValue( image, _ImagesPath.indexMetadataName, i )

	def __childAdded( self, parent, child ) :

		assert( parent.isSame( self.__images ) )
		self.__nameChangedConnections[child] = child.nameChangedSignal().connect( Gaffer.WeakMethod( self.__nameChanged ), scoped = True )
		self._emitPathChanged()

	def __childRemoved( self, parent, child ) :

		assert( parent.isSame( self.__images ) )
		del self.__nameChangedConnections[child]
		self._emitPathChanged()

	def __nameChanged( self, child ) :

		self._emitPathChanged()

	def __cataloguePlugDirtied( self, plug ):

		if plug.ancestor( GafferImage.Catalogue.Image ) :
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
				columns = self.__listingColumns(),
				selectionMode = GafferUI.PathListingWidget.SelectionMode.Rows,
				sortable = False,
				horizontalScrollMode = GafferUI.ScrollMode.Automatic
			)
			self.__pathListing.setDragPointer( "" )
			self.__pathListing.setHeaderVisible( True )
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

				self.__duplicateButton = GafferUI.Button( image = "duplicate.png", hasFrame = False, toolTip = "Duplicate selected image, hold <kbd>alt</kbd> to view copy. [<kbd>Ctrl-D</kbd>]" )
				self.__duplicateButton.setEnabled( False )
				self.__duplicateButton.clickedSignal().connect( Gaffer.WeakMethod( self.__duplicateClicked ), scoped = False )

				self.__exportButton = GafferUI.Button( image = "export.png", hasFrame = False, toolTip = "Export selected image" )
				self.__exportButton.setEnabled( False )
				self.__exportButton.clickedSignal().connect( Gaffer.WeakMethod( self.__exportClicked ), scoped = False )

				self.__extractButton = GafferUI.Button( image = "extract.png", hasFrame = False, toolTip = "Create CatalogueSelect node for selected image" )
				self.__extractButton.setEnabled( False )
				self.__extractButton.clickedSignal().connect( Gaffer.WeakMethod( self.__extractClicked ), scoped = False )

				GafferUI.Spacer( imath.V2i( 0 ), parenting = { "expand" : True } )

				self.__removeButton = GafferUI.Button( image = "delete.png", hasFrame = False, toolTip = "Remove selected image [<kbd>Delete</kbd>]" )
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

		Gaffer.Metadata.plugValueChangedSignal( plug.node() ).connect( Gaffer.WeakMethod( self.__plugMetadataValueChanged ), scoped = False )

		self.contextMenuSignal().connect( Gaffer.WeakMethod( self.__contextMenu ), scoped = False )

		self._updateFromPlug()

	def getToolTip( self ) :

		# Suppress the default imageIndex tool-tip until we can do something
		# more intelligent. We can't use setToolTip as PlugValueWidget defaults
		# to the plug description for 'falsy' values.
		return None

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

	def __plugMetadataValueChanged( self, plug, key, reason ) :

		if key == _columnsMetadataKey and plug == self.getPlug() :
			self.__pathListing.setColumns( self.__listingColumns() )

	def __getColumns( self ) :

		# Support for promoted plugs.
		# The plug data may have been reset, or it may have been promoted in a
		# previous version of gaffer. As such, we can't assume there is a
		# registered class value for our plug. Fall back on the Catalogue nodes
		# plug's value as this will consider the class default columns value.
		## \todo Refactor when we get metadata delegation for promoted plugs
		return Gaffer.Metadata.value( self.getPlug(), _columnsMetadataKey ) \
			or Gaffer.Metadata.value( self.__catalogue()["imageIndex"], _columnsMetadataKey )

	def __setColumns( self, columns ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			Gaffer.Metadata.registerValue( self.getPlug(), _columnsMetadataKey, IECore.StringVectorData( columns ) )

	def __resetColumns( self, *unused ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			Gaffer.Metadata.deregisterValue( self.getPlug(), _columnsMetadataKey )

	def __toggleColumn( self, column, visible ) :

		columns = list( self.__getColumns() )
		if visible :
			columns.append( column )
		else :
			columns.remove( column )

		self.__setColumns( columns )

	def __listingColumns( self ) :

		columns = []

		for name in self.__getColumns() :

			c = column( name )
			if c is not None :
				columns.append( c )
			else :
				IECore.msg(
					IECore.Msg.Level.Error,
					"GafferImageUI.CatalogueUI", "No column registered with name '%s'" % name
				)

		return columns

	def __catalogue( self ) :

		return _findSourceCatalogue( self.getPlug() )

	def __images( self ) :

		return self.__catalogue()["images"].source()

	def __orderedImages( self ) :

		return _ImagesPath( self.__images(), [] )._orderedImages()

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

	def __uiIndexToIndex( self, index ) :

		target = self.__orderedImages()[ index ]

		for i, image in enumerate( self.__images() ) :
			if image.isSame( target ) :
				return i

	def __removeClicked( self, *unused ) :

		indices = self.__indicesFromSelection()

		# If the user repeatedly clicks the delete button, we might end up in a
		# state, where selection hasn't been restored yet. In that case we
		# can't delete anything and will ignore the request.
		if not indices :
			return

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :

			orderedImages = self.__orderedImages()
			reselectionIndex = len( orderedImages )

			for index in reversed( sorted( indices ) ) :
				image = self.__images()[ index ]
				uiIndex = orderedImages.index( image )
				reselectionIndex = min( max( 0, uiIndex - 1 ), reselectionIndex )
				self.__images().removeChild( image )
				orderedImages.remove( image )

			_ImagesPath._updateUIIndices( orderedImages )

			# Figure out new selection
			if orderedImages :
				selectionIndex = self.__uiIndexToIndex( reselectionIndex )
				self.getPlug().setValue( selectionIndex )

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

		# These are plug indices, rather than ui indices, so need to be
		# used directly with self.__images() without remapping.
		indices = self.__indicesFromSelection()
		if not indices :
			return

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			insertions = _duplicateImages( self.__catalogue(), indices )
			# Only switch to the last duplicate if alt is held
			altHeld = GafferUI.Widget.currentModifiers() & GafferUI.ModifiableEvent.Modifiers.Alt
			if altHeld :
				self.getPlug().setValue( insertions[-1] )

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

		images = self.__orderedImages()
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

		_ImagesPath._updateUIIndices( [image for image in images if image ] )

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
		elif keyEvent.key == "D" and keyEvent.modifiers == keyEvent.Modifiers.Control :
			self.__duplicateClicked()
			return True

		return False

	def __columnContextMenuDefinition( self ) :

		columns = self.__getColumns()
		allColumnsSorted = sorted( registeredColumns() )

		menu = IECore.MenuDefinition()
		menu.append( "/Reset", { "command" : Gaffer.WeakMethod( self.__resetColumns ) } )
		menu.append( "/__resetDivider__", { "divider" : True } )

		for column in allColumnsSorted :

			menu.append( "/%s" % column, {
				"checkBox" : column in columns,
				"command" : functools.partial( Gaffer.WeakMethod( self.__toggleColumn ), column ),
				# Prevent the last column being removed
				"active": False if column in columns and len(columns) == 1 else True
			} )

		return menu

	def __contextMenu( self, *unused ) :

		if self.getPlug() is None :
			return False

		# This signal is called anywhere in the listing, check we're over the header.
		mousePosition = GafferUI.Widget.mousePosition( relativeTo = self.__pathListing )
		headerRect = self.__pathListing._qtWidget().header().rect()
		if not headerRect.contains( mousePosition[0], mousePosition[1] ) :
			return False

		self.__popupMenu = GafferUI.Menu( self.__columnContextMenuDefinition(), "Columns" )
		self.__popupMenu.popup( parent = self )

		return True

GafferUI.Pointer.registerPointer( "plus", GafferUI.Pointer( "plus.png" ) )
