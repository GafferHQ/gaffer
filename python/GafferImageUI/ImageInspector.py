##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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
import GafferImage
import GafferImageUI

class ImageInspector( GafferUI.NodeSetEditor ) :

	# Used to hold settings and internal processing network
	# for the ImageInspector.
	## \todo Eventually we want `GafferUI.Editor` to derive from Node itself,
	# in which case we wouldn't need a separate settings object.
	class Settings( GafferUI.Editor.Settings ) :

		def __init__( self, script ) :

			GafferUI.Editor.Settings.__init__( self, "ImageInspectorSettings", script )

			self["in"] = GafferImage.ImagePlug()
			self["view"] = Gaffer.StringPlug( defaultValue = "default" )

			self["__selectView"] = GafferImage.SelectView()
			self["__selectView"]["in"].setInput( self["in"] )
			self["__selectView"]["view"].setInput( self["view"] )

			self["__contextQuery"] = Gaffer.ContextQuery()
			self["__contextQuery"].addQuery(
				Gaffer.StringVectorDataPlug( defaultValue = IECore.StringVectorData() ), "imageInspector:statsChannels"
			)

			self["__deleteContextVariables"] = Gaffer.DeleteContextVariables()
			self["__deleteContextVariables"].setup( self["__selectView"]["out"] )
			self["__deleteContextVariables"]["in"].setInput( self["__selectView"]["out"] )
			self["__deleteContextVariables"]["variables"].setValue( "imageInspector:statsChannels" )

			self["__formatQuery"] = GafferImage.FormatQuery()
			self["__formatQuery"]["image"].setInput( self["__deleteContextVariables"]["out"] )

			self["__imageStats"] = GafferImage.ImageStats()
			self["__imageStats"]["in"].setInput(  self["__deleteContextVariables"]["out"] )
			self["__imageStats"]["area"].setInput( self["__formatQuery"]["format"]["displayWindow"] )
			self["__imageStats"]["channels"].setInput( self["__contextQuery"]["out"][0]["value"] )

			self["__sampleCounts"] = GafferImage.DeepSampleCounts()
			self["__sampleCounts"]["in"].setInput( self["__deleteContextVariables"]["out"] )

			self["__sampleStats"] = GafferImage.ImageStats()
			self["__sampleStats"]["in"].setInput( self["__sampleCounts"]["out"] )
			self["__sampleStats"]["area"].setInput( self["__formatQuery"]["format"]["displayWindow"] )

	IECore.registerRunTimeTyped( Settings, typeName = "GafferImageUI::ImageInspector::Settings" )

	def __init__( self, scriptNode, **kw ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 4 )

		GafferUI.NodeSetEditor.__init__( self, column, scriptNode, nodeSet = scriptNode.focusSet(), **kw )

		self.__settingsNode = self.Settings( scriptNode )
		Gaffer.NodeAlgo.applyUserDefaults( self.__settingsNode )

		with column :

			GafferUI.PlugLayout(
				self.__settingsNode,
				rootSection = "Settings"
			)

			with GafferUI.TabbedContainer() :

				self.__imagePathListing = GafferUI.PathListingWidget(
					Gaffer.DictPath( {}, "/" ), # Placeholder, updated in `__setPathListingPaths()``
					columns = [
						GafferUI.PathListingWidget.defaultNameColumn,
						GafferUI.StandardPathColumn( "Value", "image:value", sizeMode = GafferUI.PathColumn.SizeMode.Stretch )
					],
					displayMode = GafferUI.PathListingWidget.DisplayMode.List,
					selectionMode = GafferUI.PathListingWidget.SelectionMode.Cell,
					horizontalScrollMode = GafferUI.ScrollMode.Automatic,
					sortable = False,
					parenting = {
						"label" : "Image"
					}
				)

				self.__channelsPathListing = GafferUI.PathListingWidget(
					Gaffer.DictPath( {}, "/" ),
					columns = [
						GafferUI.PathListingWidget.defaultNameColumn,
						GafferUI.StandardPathColumn( "Min", "stats:min", sizeMode = GafferUI.PathColumn.SizeMode.Stretch ),
						GafferUI.StandardPathColumn( "Max", "stats:max", sizeMode = GafferUI.PathColumn.SizeMode.Stretch ),
						GafferUI.StandardPathColumn( "Average", "stats:average", sizeMode = GafferUI.PathColumn.SizeMode.Stretch ),
					],
					displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
					selectionMode = GafferUI.PathListingWidget.SelectionMode.Cell,
					sortable = False,
					horizontalScrollMode = GafferUI.ScrollMode.Automatic,
					parenting = {
						"label" : "Channels"
					}
				)

				self.__metadataPathListing = GafferUI.PathListingWidget(
					Gaffer.DictPath( {}, "/" ),
					columns = [
						GafferUI.PathListingWidget.defaultNameColumn,
						GafferUI.StandardPathColumn( "Value", "metadata:value", sizeMode = GafferUI.PathColumn.SizeMode.Stretch )
					],
					displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
					selectionMode = GafferUI.PathListingWidget.SelectionMode.Cell,
					horizontalScrollMode = GafferUI.ScrollMode.Automatic,
					sortable = False,
					parenting = {
						"label" : "Metadata"
					}
				)

		self._updateFromSet()
		self.__setPathListingPaths()

	def __repr__( self ) :

		return "GafferImageUI.ImageInspector( scriptNode )"

	def _updateFromSet( self ) :

		# Decide what image we're viewing.
		plug = None
		self.__plugParentChangedConnection = None
		node = self._lastAddedNode()
		if node is not None :
			plug = next( GafferImage.ImagePlug.RecursiveOutputRange( node ), None )
			if plug is not None :
				self.__plugParentChangedConnection = plug.parentChangedSignal().connect( Gaffer.WeakMethod( self.__plugParentChanged ), scoped = True )

		self.__settingsNode["in"].setInput( plug )

		# Call base class update - this will trigger a call to _titleFormat(),
		# hence the need for already figuring out the image being viewed.
		GafferUI.NodeSetEditor._updateFromSet( self )

	def _updateFromContext( self, modifiedItems ) :

		for item in modifiedItems :
			if not item.startswith( "ui:" ) :
				self.__setPathListingPaths()
				break

	def _titleFormat( self ) :

		return GafferUI.NodeSetEditor._titleFormat(
			self,
			_maxNodes = 1 if self.__settingsNode["in"].getInput() is not None else 0,
			_reverseNodes = True,
			_ellipsis = False
		)

	def __plugParentChanged( self, plug, oldParent ) :

		# The plug we were viewing has been deleted or moved - find
		# another one to view.
		self._updateFromSet()

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __setPathListingPaths( self ) :

		# We take a static copy of our current context for use in the paths. This
		# lets us defer updates until playback stops, and also provides important
		# thread-safety, because the PathListingWidget will access the context
		# on a background thread.
		context = Gaffer.Context( self.getContext() )
		self.__imagePathListing.setPath(
			_ImagePath( self.scriptNode(), self.__settingsNode["__sampleStats"]["in"], context, "/" ),
		)
		self.__channelsPathListing.setPath(
			_ChannelPath( self.scriptNode(), self.__settingsNode["__imageStats"]["in"], context, "/" ),
		)
		self.__metadataPathListing.setPath(
			_MetadataPath( self.scriptNode(), self.__settingsNode["__selectView"]["out"], context, "/" ),
		)

GafferUI.Editor.registerType( "ImageInspector", ImageInspector )

##########################################################################
# Metadata controlling the settings UI
##########################################################################

Gaffer.Metadata.registerNode(

	ImageInspector.Settings,

	plugs = {

		"view" : [

			"plugValueWidget:type", "GafferImageUI.ViewPlugValueWidget",
			"description", "The view to inspect",

		],

	}

)

##########################################################################
# _ImagePathBase
##########################################################################

class _ImagePathBase( Gaffer.Path ) :

	def __init__( self, scriptNode, image, context, path, root = "/", filter = None ) :

		Gaffer.Path.__init__( self, path, root, filter )

		self.__scriptNode = scriptNode
		self._context = context
		self._image = image
		self.__imagePlugDirtiedConnection = self._image.node().plugDirtiedSignal().connect(
			Gaffer.WeakMethod( self.__imagePlugDirtied, fallbackResult = None ), scoped = True
		)

	def copy( self ) :

		return self.__class__( self.__scriptNode, self._image, self._context, self[:], self.root(), self.getFilter() )

	def cancellationSubject( self ) :

		return self._image

	def _children( self, canceller ) :

		return [
			self.__class__( self.__scriptNode, self._image, self._context, self[:] + [ name ], self.root(), self.getFilter() )
			for name in self._childNames( canceller )
		]

	def _childNames( self, canceller ) :

		raise NotImplementedError

	def _imagePlugAffectsPath( self, plug ) :

		raise NotImplementedError

	def __imagePlugDirtied( self, plug ) :

		if plug.parent() == self._image and self._imagePlugAffectsPath( plug ) :
			self._emitPathChanged()

##########################################################################
# _ImagePath
##########################################################################

class _ImagePath( _ImagePathBase ) :

	def __init__( self, scriptNode, image, context, path, root = "/", filter = None ) :

		_ImagePathBase.__init__( self, scriptNode, image, context, path, root, filter )

		assert( isinstance( image.node(), GafferImage.ImageStats ) )

	def propertyNames( self, canceller = None ) :

		return Gaffer.Path.propertyNames( self ) + [ "image:value" ]

	def property( self, name, canceller = None ) :

		if name != "image:value" :
			return Gaffer.Path.property( self, name, canceller )

		if len( self ) != 1 :
			return None

		with Gaffer.Context( self._context, canceller ) :

			# Our `_image` has been through a DeepSampleCounts node, and
			# several of our properties need to be retrieved from the
			# original input image.
			originalImage = self._image.getInput().node()["in"]

			if not originalImage.channelNames() :
				# Heuristic for detecting lack of input image.
				return "---"

			if self[0] == "Format" :
				return GafferImage.Format.name( self._image.format() ) or "---"
			elif self[0] == "Resolution" :
				size = self._image.format().getDisplayWindow().size()
				return f"{size.x} x {size.y}"
			elif self[0] == "Pixel Aspect" :
				return self._image.format().getPixelAspect()
			elif self[0] == "Display Window Min" :
				return self._image.format().getDisplayWindow().min()
			elif self[0] == "Display Window Max" :
				return self._image.format().getDisplayWindow().max()
			elif self[0] == "Data Window Size" :
				size = self._image.dataWindow().size()
				return f"{size.x} x {size.y}"
			elif self[0] == "Data Window Min" :
				return self._image.dataWindow().min()
			elif self[0] == "Data Window Max" :
				return self._image.dataWindow().max()
			elif self[0] == "Type" :
				return "Deep" if self._image.getInput().node()["in"].deep() else "Flat"
			elif self[0] == "Min Samples Per Pixel" :
				return self._image.node()["min"][0].getValue() if originalImage.deep() else "---"
			elif self[0] == "Max Samples Per Pixel" :
				return self._image.node()["max"][0].getValue() if originalImage.deep() else "---"
			elif self[0] == "Average Samples Per Pixel" :
				return self._image.node()["average"][0].getValue() if originalImage.deep() else "---"

	def _childNames( self, canceller ) :

		if len( self ) :
			return []

		return [
			"Format",
			"Resolution",
			"Pixel Aspect",
			"Display Window Min",
			"Display Window Max",
			"Data Window Size",
			"Data Window Min",
			"Data Window Max",
			"Type",
			"Min Samples Per Pixel",
			"Max Samples Per Pixel",
			"Average Samples Per Pixel",
		]

	def _imagePlugAffectsPath( self, plug ) :

		return plug in [ self._image["format"], self._image["dataWindow"], self._image["channelNames"], self._image["channelData"] ]

##########################################################################
# _MetadataPath
##########################################################################

class _MetadataPath( _ImagePathBase ) :

	def __init__( self, scriptNode, image, context, path, root = "/", filter = None ) :

		_ImagePathBase.__init__( self, scriptNode, image, context, path, root, filter )

	def propertyNames( self, canceller = None ) :

		return Gaffer.Path.propertyNames( self ) + [ "metadata:value" ]

	def property( self, name, canceller = None ) :

		if name == "metadata:value" :
			return self.__metadata( canceller ).get(
				str( self )[1:]
			)

		return Gaffer.Path.property( self, name, canceller )

	def _childNames( self, canceller ) :

		metadata = self.__metadata( canceller )
		selfNames = self[:]

		result = []
		visited = set()
		for key in sorted( metadata.keys() ) :
			names = key.split( "/" )
			if len( names ) <= len( selfNames ) or names[:len(selfNames)] != selfNames :
				continue
			name = names[len(selfNames)]
			if name not in visited :
				result.append( name )
				visited.add( name )

		return result

	def _imagePlugAffectsPath( self, plug ) :

		return plug.isSame( self._image["metadata"] )

	def __metadata( self, canceller ) :

		with Gaffer.Context( self._context, canceller ) :
			return self._image.metadata()

##########################################################################
# _ChannelPath
##########################################################################

class _ChannelPath( _ImagePathBase ) :

	def __init__( self, scriptNode, image, context, path, root = "/", filter = None ) :

		_ImagePathBase.__init__( self, scriptNode, image, context, path, root, filter )

		assert( isinstance( image.node(), GafferImage.ImageStats ) )

	def propertyNames( self, canceller = None ) :

		return Gaffer.Path.propertyNames( self ) + [ "stats:min", "stats:max", "stats:average" ]

	def property( self, name, canceller = None ) :

		if name in [ "stats:min", "stats:max", "stats:average" ] :

			statsPlug = self._image.node()[name.replace( "stats:", "" )]

			with Gaffer.Context( self._context, canceller ) as context :

				channelName = str( self )[1:].replace( "/", "." )
				if channelName == "RGBA" :
					channelName = ""
				elif channelName.startswith( "RGBA." ) :
					channelName = channelName[5:]

				# Note : `channelName` may actually be a layer name.
				# If it is, early out.

				for c in self._channelNames( canceller ) :
					if GafferImage.ImageAlgo.layerName( c ) == channelName :
						return None
					elif c.startswith( f"{channelName}." ) :
						# Doubly nested, like `{channelName}.subLayerName.baseName`
						return None

				# Use the stats node to query the property.

				context["imageInspector:statsChannels"] = IECore.StringVectorData( [ channelName ] )
				return statsPlug[0].getValue()

		return Gaffer.Path.property( self, name, canceller )

	def _childNames( self, canceller ) :

		selfNames = self[:]

		result = []
		visited = set()
		for channelName in self._channelNames( canceller ) :
			layerName = GafferImage.ImageAlgo.layerName( channelName ) or "RGBA"
			names = layerName.split( "." ) + [ GafferImage.ImageAlgo.baseName( channelName ) ]
			if len( names ) <= len( selfNames ) or names[:len(selfNames)] != selfNames :
				continue
			name = names[len(selfNames)]
			if name not in visited :
				result.append( name )
				visited.add( name )

		return result

	def _imagePlugAffectsPath( self, plug ) :

		return plug in [ self._image["channelNames"], self._image["channelData" ] ]

	def _channelNames( self, canceller ) :

		with Gaffer.Context( self._context, canceller ) :
			return GafferImage.ImageAlgo.sortedChannelNames( self._image.channelNames() )
