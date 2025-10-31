##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import dataclasses
import os
import re
import string
import fnmatch
import functools
import imath
from collections import deque

import IECore
import IECoreScene

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

from GafferUI.PlugValueWidget import sole

##########################################################################
# Metadata
##########################################################################

def __shaderMetadata( node, key ) :

	return Gaffer.Metadata.value(
		node["type"].getValue() + ":" + node["name"].getValue(), key
	)

def __nodeDescriptionMetadata( node ) :

	description =__shaderMetadata( node, "description" )
	if description :
		return description

	renderer = node.typeName().rpartition( ":" )[-1].replace( "Shader", "" )
	return f"Loads {renderer} shaders. Use a ShaderAssignment node to assign the shader to objects in the scene."

def __parameterMetadata( plug, key, shaderFallbackKey = None ) :

	shader = plug.node()
	result = Gaffer.Metadata.value(
		shader["type"].getValue() + ":" + shader["name"].getValue() + ":" + plug.relativeName( shader["parameters"] ),
		key
	)

	if result is not None :
		return result

	return __shaderMetadata( shader, shaderFallbackKey ) if shaderFallbackKey is not None else None

def __parameterComponentNoduleLabel( plug ) :

	parameterPlug = plug.parent()
	label = Gaffer.Metadata.value( parameterPlug, "label" ) or parameterPlug.getName()
	return label + "." + plug.getName()

Gaffer.Metadata.registerNode(

	GafferScene.Shader,

	"description", __nodeDescriptionMetadata,

	"nodeGadget:minWidth", 0.0,
	"nodeGadget:color", functools.partial( __shaderMetadata, key = "nodeGadget:color" ),

	plugs = {

		"name" : {

			"description" :
			"""
			The name of the shader being represented. This should
			be considered read-only. Use the `Shader.loadShader()`
			method to load a shader.
			""",

			"label" : "Shader",
			"readOnly" : True,
			"layout:section" : "",
			"nodule:type" : "",
			"plugValueWidget:type" : "GafferSceneUI.ShaderUI._ShaderNamePlugValueWidget",

		},

		"type" : {

			"description" :
			"""
			The type of the shader being represented. This should
			be considered read-only. Use the `Shader.loadShader()`
			method to load a shader.
			""",

			"readOnly" : True,
			"layout:section" : "",
			"nodule:type" : "",
			"plugValueWidget:type" : "",

		},

		"parameters" : {

			"description" :
			"""
			Where the parameters for the shader are represented.
			""",

			"nodule:type" : "GafferUI::CompoundNodule",
			"noduleLayout:section" : "left",
			"noduleLayout:spacing" : 0.2,
			"plugValueWidget:type" : "GafferUI.LayoutPlugValueWidget",

			# Add + button for showing and hiding parameters in the GraphEditor
			"noduleLayout:customGadget:addButton:gadgetType" : "GafferSceneUI.ShaderUI.PlugAdder",

		},

		"parameters.*" : {

			"label" : functools.partial( __parameterMetadata, key = "label" ),
			"description" : functools.partial( __parameterMetadata, key = "description" ),
			"layout:section" : functools.partial( __parameterMetadata, key = "layout:section" ),
			"layout:accessory" : functools.partial( __parameterMetadata, key = "layout:accessory" ),
			"layout:divider" : functools.partial( __parameterMetadata, key = "layout:divider" ),
			"plugValueWidget:type" : functools.partial( __parameterMetadata, key = "plugValueWidget:type" ),
			"presetNames" : functools.partial( __parameterMetadata, key = "presetNames" ),
			"presetValues" : functools.partial( __parameterMetadata, key = "presetValues" ),
			"nodule:type" : functools.partial( __parameterMetadata, key = "nodule:type" ),
			"noduleLayout:visible" : functools.partial( __parameterMetadata, key = "noduleLayout:visible", shaderFallbackKey = "noduleLayout:defaultVisibility" ),

		},

		"parameters.*.[rgbxyz]" : {

			"noduleLayout:label" : __parameterComponentNoduleLabel,

		},

		"parameters.*..." : {

			# Although the parameters plug is positioned
			# as we want above, we must also register
			# appropriate values for each individual parameter,
			# for the case where they get promoted to a box
			# individually.
			"noduleLayout:section" : "left",

			"userDefault" : functools.partial( __parameterMetadata, key = "userDefault" ),

		},

		"out" : {

			"description" :
			"""
			The output from the shader.
			""",

			"noduleLayout:section" : "right",
			"plugValueWidget:type" : "",

			# Add + button for showing and hiding parameters in the GraphEditor
			"noduleLayout:customGadget:addButton:gadgetType" : "GafferSceneUI.ShaderUI.PlugAdder",

		},

		"out.*" : {

			"noduleLayout:section" : "right",

		},

		"attributeSuffix" : {

			"description" :
			"""
			Suffix for the attribute used for shader assignment.
			""",

			"nodule:type" : "",
			"plugValueWidget:type" : "",
			"layout:section" : "",

		},

	}

)

##########################################################################
# PlugValueWidgets
##########################################################################

class _ShaderNamePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, row, plugs, **kw )

		with row :

			self.__stringPlugValueWidget = GafferUI.StringPlugValueWidget( plugs )
			self.__reloadButton = GafferUI.Button( image = "refresh.png", hasFrame = False, toolTip = "Click to reload shader" )
			self.__reloadButton.clickedSignal().connect( Gaffer.WeakMethod( self.__reloadButtonClicked ) )

	def setPlugs( self, plugs ) :

		GafferUI.PlugValueWidget.setPlugs( self, plugs )
		self.__stringPlugValueWidget.setPlugs( plugs )

	def _updateFromEditable( self ) :

		self.__reloadButton.setEnabled(
			# The plug will always be read-only because we don't want the user to edit it.
			# But we do want to allow reloading, as long as the parent node isn't read-only.
			not any( Gaffer.MetadataAlgo.readOnly( p.node() ) for p in self.getPlugs() )
		)

	def __reloadButtonClicked( self, button ) :

		with Gaffer.UndoScope( self.scriptNode() ) :
			for plug in self.getPlugs() :
				plug.node().reloadShader()

##########################################################################
# NodeFinderDialogue mode
##########################################################################

def __shaderNameExtractor( node ) :

	if isinstance( node, GafferScene.Shader ) :
		return node["name"].getValue()
	else :
		return ""

GafferUI.NodeFinderDialogue.registerMode( "Shader Names", __shaderNameExtractor )

##########################################################################
# Shader menu
##########################################################################

## Appends menu items for the creation of all shaders found on some searchpaths.
def appendShaders( menuDefinition, prefix, searchPaths, extensions, nodeCreator, matchExpression = "*", searchTextPrefix = "" ) :

	menuDefinition.append( prefix, { "subMenu" : functools.partial( __shaderSubMenu, searchPaths, extensions, nodeCreator, matchExpression, searchTextPrefix ) } )

__hiddenShadersPathMatcher = IECore.PathMatcher()
## Hides shaders from the menu created by `appendShaders()`.
# The `pathMatcher` is an `IECore.PathMatcher()` that will be used
# to match searchpath-relative shader filenames.
def hideShaders( pathMatcher ) :

	global __hiddenShadersPathMatcher
	__hiddenShadersPathMatcher.addPaths( pathMatcher )

def __nodeName( shaderName ) :

	nodeName = os.path.split( shaderName )[-1]
	nodeName = nodeName.translate( str.maketrans( ".-", "__" ) )

	return nodeName

def __loadFromFile( menu, extensions, nodeCreator ) :

	bookmarks = GafferUI.Bookmarks.acquire( menu, category = "shader" )
	path = Gaffer.FileSystemPath( bookmarks.getDefault( menu ) )
	path.setFilter( Gaffer.FileSystemPath.createStandardFilter( extensions ) )

	dialogue = GafferUI.PathChooserDialogue( path, title="Load Shader", confirmLabel = "Load", valid=True, leaf=True, bookmarks = bookmarks )
	path = dialogue.waitForPath( parentWindow = menu.ancestor( GafferUI.ScriptWindow ) )

	if not path :
		return None

	shaderName = os.path.splitext( str( path ) )[0]

	return nodeCreator( __nodeName( shaderName ), shaderName )

def __shaderSubMenu( searchPaths, extensions, nodeCreator, matchExpression, searchTextPrefix ) :

	global __hiddenShadersPathMatcher

	if isinstance( matchExpression, str ) :
		matchExpression = re.compile( fnmatch.translate( matchExpression ) )

	shaders = set()
	pathsVisited = set()
	for path in searchPaths :

		if path in pathsVisited :
			continue

		for root, dirs, files in os.walk( path ) :
			for file in files :
				if os.path.splitext( file )[1][1:] in extensions :
					shaderPath = os.path.join( root, file ).partition( path )[-1].lstrip( os.path.sep )
					shaderPath = shaderPath.replace( "\\", "/" )
					if __hiddenShadersPathMatcher.match( shaderPath ) & IECore.PathMatcher.Result.ExactMatch :
						continue
					if shaderPath not in shaders and matchExpression.match( shaderPath ) :
						shaders.add( os.path.splitext( shaderPath )[0] )

		pathsVisited.add( path )

	shaders = sorted( list( shaders ) )
	categorisedShaders = [ x for x in shaders if "/" in x ]
	uncategorisedShaders = [ x for x in shaders if "/" not in x ]

	shadersAndMenuPaths = []
	for shader in categorisedShaders :
		shadersAndMenuPaths.append( ( shader, "/" + shader ) )

	for shader in uncategorisedShaders :
		if not categorisedShaders :
			shadersAndMenuPaths.append( ( shader, "/" + shader ) )
		else :
			shadersAndMenuPaths.append( ( shader, "/Other/" + shader ) )

	result = IECore.MenuDefinition()
	for shader, menuPath in shadersAndMenuPaths :
		menuPath = "/".join( [ IECore.CamelCase.toSpaced( x ) for x in menuPath.split( "/" ) ] )
		result.append(
			menuPath,
			{
				"command" : GafferUI.NodeMenu.nodeCreatorWrapper( functools.partial( nodeCreator, __nodeName( shader ), shader ) ),
				"searchText" : searchTextPrefix + menuPath.rpartition( "/" )[-1].replace( " ", "" ),
			},
		)

	result.append( "/LoadDivider", { "divider" : True } )
	result.append( "/Load...", { "command" : GafferUI.NodeMenu.nodeCreatorWrapper( lambda menu : __loadFromFile( menu, extensions, nodeCreator ) ) } )

	return result

##########################################################################
# Interaction with ShaderNodeGadget
##########################################################################

def __setPlugMetadata( plug, key, value ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		Gaffer.Metadata.registerValue( plug, key, value )

def __graphEditorPlugContextMenu( graphEditor, plug, menuDefinition ) :

	if not isinstance( plug.node(), GafferScene.Shader ) :
		return

	if not (
		plug.node()["parameters"].isAncestorOf( plug ) or
		plug.node()["out"].isAncestorOf( plug )
	) :
		return

	if len( menuDefinition.items() ) :
		menuDefinition.append( "/HideDivider", { "divider" : True } )

	if plug.direction() == plug.Direction.In :
		numConnections = 1 if plug.getInput() else 0
	else :
		numConnections = len( plug.outputs() )

	menuDefinition.append(

		"/Hide",
		{
			"command" : functools.partial( __setPlugMetadata, plug, "noduleLayout:visible", False ),
			"active" : numConnections == 0 and not Gaffer.MetadataAlgo.readOnly( plug ),
		}

	)

GafferUI.GraphEditor.plugContextMenuSignal().connect( __graphEditorPlugContextMenu )


##########################################################################
# ShaderParameterDialog
##########################################################################

class _DuplicateIconColumn ( GafferUI.PathColumn ) :

	def __init__( self, title, property ) :

		GafferUI.PathColumn.__init__( self )

		self.__title = title
		self.__property = property

	def cellData( self, path, canceller = None ) :

		cellValue = path.property( self.__property )
		# \todo : Remove this check when Arnold lights don't use `__shader`
		# as the name of the internal shader.
		if cellValue == "__shader" :
			cellValue = "Light"

		data = self.CellData( cellValue )

		if "shader:instances" in path.propertyNames() and path.property( "shader:instances" ) > 1 :
			data.icon = "duplicate.png"
			data.toolTip = "Shader occurs in multiple networks."
		elif len( path.property( "shader:parameterValues" ) ) > 1 :
			data.icon = "duplicate.png"
			data.toolTip = "Parameter occurs in multiple shaders."

		return data

	def headerData( self, canceller = None ) :

		return self.CellData( self.__title )

class _ShaderInputColumn ( GafferUI.PathColumn ) :

	def __init__( self, title ) :

		GafferUI.PathColumn.__init__( self )

		self.__title = title

	def cellData( self, path, canceller = None ) :

		data = self.CellData()

		if "shader:inputs" in path.propertyNames() :

			inputs = path.property( "shader:inputs" )

			if len( inputs ) > 0 :
				data.icon = "navigationArrow.png"

				if len( inputs ) > 1 :
					data.value = "---"

					data.toolTip = "Select parameter inputs and scroll to first.\n\nInputs :\n"
					for i in inputs :
						data.toolTip += "- {}\n".format( i )
				else :
					data.value = next( iter( inputs ) )
					data.toolTip = "Select and scroll to parameter input."

		return data

	def headerData( self, canceller = None ) :

		return self.CellData( self.__title )

# A Path pointing to a shader or shader parameter belonging to one or more
# IECore::ShaderNetworks. Shaders with identical names are merged
# into a single location.
#
# See comments on InspectorTree in SceneInspectorBinding.cpp for the rationale
# behind the _ShaderTree/_ShaderPath factoring.
class _ShaderTree :

	@dataclasses.dataclass
	class Node :

		# Maps from hash to `IECore.Shader`, so we only store unique shaders.
		shaderInstances : dict = dataclasses.field( default_factory = dict )
		parameterValues : list = dataclasses.field( default_factory = list )
		parameterInputs : set = dataclasses.field( default_factory = set )
		children : dict = dataclasses.field( default_factory = dict )

	def __init__( self, shaderNetworks, connectedParametersOnly = False ) :

		assert( all( [ isinstance( n, IECoreScene.ShaderNetwork ) for n in shaderNetworks ] ) )
		self.__root = self.Node()

		# Build an internal tree of Nodes by visiting all shaders, ordered by
		# depth from the output shader.

		queue = deque(
			sorted(
				[ ( n, n.getOutput().shader ) for n in shaderNetworks ],
				key = lambda k : k[1]
			)
		)
		visited = set()

		while queue :

			shaderNetwork, shaderHandle = queue.popleft()

			h = shaderNetwork.hash().append( shaderHandle )
			if h in visited :
				continue

			visited.add( h )

			shaderNode = self.__node( shaderHandle.split( "/" ), createIfMissing = True )

			shader = shaderNetwork.getShader( shaderHandle )
			shaderHash = shader.hash()
			if shaderHash not in shaderNode.shaderInstances :
				shaderNode.shaderInstances[shaderHash] = shader
				if not connectedParametersOnly :
					for parameter in sorted( shader.parameters.keys() ) :
						parameterNode = shaderNode.children.setdefault( parameter, self.Node() )
						parameterNode.parameterValues.append( shader.parameters[parameter] )

			for connection in shaderNetwork.inputConnections( shaderHandle ) :
				parameterNode = shaderNode.children.setdefault( connection.destination.name.partition( "." )[0], self.Node() )
				parameterNode.parameterInputs.add( connection.source.shader )

			queue.extend(
				[ ( shaderNetwork, c.source.shader ) for c in shaderNetwork.inputConnections( shaderHandle ) ]
			)

	def _isValid( self, pathNames ) :

		return self.__node( pathNames ) is not None

	def _isLeaf( self, pathNames ) :

		node = self.__node( pathNames )
		return node is not None and not len( node.children )

	def _propertyNames( self, pathNames ) :

		node = self.__node( pathNames )
		if node is None :
			return []

		result = [ "shader:instances" ]
		if node.parameterValues :
			result.append( "shader:value" )
			result.append( "shader:parameterValues" )
		if node.parameterInputs :
			result.append( "shader:inputs" )
		if node.shaderInstances :
			result.append( "shader:type" )

		return result

	def _property( self, pathNames, propertyName ) :

		node = self.__node( pathNames )
		if node is None :
			return None

		match propertyName :
			case "shader:instances" :
				return len( node.shaderInstances )
			case "shader:value" :
				if node.parameterValues :
					value = sole( node.parameterValues )
					return value if value is not None else "---"
				else :
					return None
			case "shader:parameterValues" :
				return node.parameterValues
			case "shader:inputs" :
				return node.parameterInputs
			case "shader:type" :
				if node.shaderInstances :
					return sole( [ s.name for s in node.shaderInstances.values() ] ) or "---"
				else :
					return None

	def _childNames( self, pathNames ) :

		node = self.__node( pathNames )
		return node.children.keys() if node is not None else []

	def __node( self, pathNames, createIfMissing = False ) :

		node = self.__root
		for name in pathNames :
			if createIfMissing :
				node = node.children.setdefault( name, self.Node() )
			else :
				node = node.children.get( name )
				if node is None :
					return None

		return node

class _ShaderPath( Gaffer.Path ) :

	def __init__( self, shaderNetworks, path, root = "/", filter = None ) :

		Gaffer.Path.__init__( self, path, root, filter )
		if isinstance( shaderNetworks, _ShaderTree ) :
			self.__tree = shaderNetworks
		else :
			self.__tree = _ShaderTree( shaderNetworks )

	def isValid( self ) :

		return self.__tree._isValid( self[:] )

	def isLeaf( self, canceller = None ) :

		return self.__tree._isLeaf( self[:] )

	def propertyNames( self, canceller = None ) :

		return self.__tree._propertyNames( self[:] )

	def property( self, name, canceller = None ) :

		result = self.__tree._property( self[:], name )
		return result if result is not None else Gaffer.Path.property( self, name )

	def copy( self ) :

		return _ShaderPath( self.__tree, self[:], self.root(), self.getFilter() )

	def _children( self, canceller ) :

		return [
			_ShaderPath( self.__tree, self[:] + [ name ], self.root(), self.getFilter() )
			for name in self.__tree._childNames( self[:] )
		]

# A path filter that keeps a path if it, any of its ancestors or any of its descendants have a
# property `propertyName` that matches `patterns`.

class _PathMatcherPathFilter( Gaffer.PathFilter ) :

	def __init__( self, patterns, rootPath = None, propertyName = "name", userData = {} ) :

		Gaffer.PathFilter.__init__( self, userData )

		self.__patterns = patterns
		self.__rootPath = rootPath
		self.__propertyName = propertyName

		self.__pathMatcherDirty = True
		self.__pathMatcher = IECore.PathMatcher()

		rootPath.pathChangedSignal().connect( Gaffer.WeakMethod( self.__rootPathChanged ) )

	def setMatchPatterns( self, patterns ) :

		if self.__patterns == patterns :
			return

		self.__patterns = patterns
		self.__pathMatcherDirty = True
		self.changedSignal()( self )

	def getMatchPatterns( self ) :

		return self.__patterns

	def setPropertyName( self, propertyName ) :

		if( self.__propertyName == propertyName ) :
			return

		self.__propertyName = propertyName
		self.__pathMatcherDirty = True
		self.changedSignal()( self )

	def getPropertyName( self ) :

		return self.__propertyName

	def _filter( self, paths, canceller ) :

		if len( paths ) == 0 :
			return []

		self.__updatePathMatcher()

		if self.__pathMatcher.isEmpty() :
			return []

		result = [ p for p in paths if self.__pathMatcher.match( str( p ) ) ]

		return result

	def __updatePathMatcher( self ) :

		if not self.__pathMatcherDirty :
			return

		newPathMatcher = IECore.PathMatcher()
		self.__pathMatcherDirty = False

		for p in self.__paths() :
			property = p.property( self.__propertyName )
			if property is None :
				continue

			for pattern in self.__patterns :
				if IECore.StringAlgo.match( property, pattern ) :
					newPathMatcher.addPath( str( p ) )
					break

		if self.__pathMatcher == newPathMatcher :
			return

		self.__pathMatcher = newPathMatcher

	def __paths( self ) :

		def collectPaths( parentPath ) :
			result = []
			for p in parentPath.children() :
				result.append( p )
				result += collectPaths( p )

			return result

		return collectPaths( self.__rootPath )

	def __rootPathChanged( self, path ) :

		self.__pathMatcherDirty = True

GafferUI.PathFilterWidget.registerType( _PathMatcherPathFilter, GafferUI.MatchPatternPathFilterWidget )

class _ShaderDialogueBase( GafferUI.Dialogue ) :

	def __init__( self, shaderNetworks, title, selectParameters, **kw ) :

		GafferUI.Dialogue.__init__( self, title, **kw )

		self.__selectParameters = selectParameters

		tree = _ShaderTree( shaderNetworks, connectedParametersOnly = not self.__selectParameters )
		self.__path = _ShaderPath( tree, path = "/" )

		self.__filter = _PathMatcherPathFilter( [ "" ], self.__path.copy() )
		self.__filter.setEnabled( False )
		self.__filter.userData()["UI"] = {
			"editable" : True,
			"label" : "Filter",
			"propertyFilters" : { "name": "Name", "shader:type": "Type" }
		}

		self.__path.setFilter( self.__filter )

		with GafferUI.ListContainer( spacing = 4 ) as mainColumn :
			self.__pathListingWidget = GafferUI.PathListingWidget(
				self.__path,
				columns = (
					_DuplicateIconColumn( "Name", "name" ),
					GafferUI.PathListingWidget.StandardColumn( "Type", "shader:type" ),
					GafferUI.PathListingWidget.StandardColumn( "Value", "shader:value" ),
					_ShaderInputColumn( "Input" ),
				),
				allowMultipleSelection = self.__selectParameters,
				displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
				sortable = False,
				horizontalScrollMode = GafferUI.ScrollMode.Automatic
			)

			GafferUI.PathFilterWidget.create( self.__filter )

		self.__inputNavigateColumn = self.__pathListingWidget.getColumns()[3]

		self._setWidget( mainColumn )

		self.__pathListingWidget.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__updateButtonState ) )
		self.__pathListingWidget.buttonReleaseSignal().connectFront( Gaffer.WeakMethod( self.__buttonRelease ) )
		self.__pathListingWidget.pathSelectedSignal().connect( Gaffer.WeakMethod( self.__pathSelected ) )

		self._addButton( "Cancel" )
		self.__confirmButton = self._addButton( "OK" )
		self.__confirmButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )

		self.__selectedSignal = Gaffer.Signal1()

		self.__updateButtonState()

	def _resultSelectedSignal( self ) :

		return self.__selectedSignal

	def _waitForResult( self, **kw ) :
		if len( self.__path.children() ) == 0 :
			dialogue = GafferUI.ConfirmationDialogue(
				"Shader Browser",
				"No shaders to browse."
			)
			dialogue.waitForConfirmation( **kw )

		else :
			button = self.waitForButton( **kw )
			if button is self.__confirmButton :
				return self.__result()

		return None

	def __buttonClicked( self, button ) :

		if button is self.__confirmButton :
			self._resultSelectedSignal()( self.__result() )

	def __pathSelected( self, pathListing ) :

		if self.__confirmButton.getEnabled() :
			self.__confirmButton.clickedSignal()( self.__confirmButton )

	def __buttonRelease( self, pathListing, event ) :

		if event.button != event.Buttons.Left :
			return False

		path = pathListing.pathAt( event.line.p0 )
		if path is None :
			return False

		column = pathListing.columnAt( event.line.p0 )
		if column == self.__inputNavigateColumn :

			inputs = path.property( "shader:inputs" )
			if not inputs :
				return False

			self.__pathListingWidget.setSelection(
				IECore.PathMatcher( [ f"/{input}" for input in inputs ] )
			)

			return True

		return False

	def __result( self ) :

		selection = self.__pathListingWidget.getSelection()

		if not self.__selectParameters :
			if selection.isEmpty() :
				return None
			assert( selection.size() == 1 )
			path = self.__pathListingWidget.getPath().copy().setFromString( selection.paths()[0] )
			if path.property( "shader:instances" ) :
				return str( path ).strip( "/" )
			return None

		result = []
		for pathString in selection.paths() :
			path = self.__pathListingWidget.getPath().copy().setFromString( pathString )
			if path.property( "shader:value" ) or path.property( "shader:input" ) :
				result.append(
					( "/".join( path[:-1] ), path[-1] )
				)

		return result

	def __updateButtonState( self, *unused ) :
		self.__confirmButton.setEnabled( bool( self.__result() ) )

class _ShaderParameterDialogue( _ShaderDialogueBase ) :

	def __init__( self, shaderNetworks, title = None, **kw ) :

		if title is None :
			title = "Select Shader Parameters"

		_ShaderDialogueBase.__init__( self, shaderNetworks, title, True, **kw )

	# Causes the dialogue to enter a modal state, returning the selected shader parameters
	# once they have been selected by the user. Returns None if the dialogue is cancelled.
	# Parameters are returned as a list of tuples of the form
	# [ ( "shaderName", "parameterName" ), ... ]
	def waitForParameters( self, **kw ) :
		return self._waitForResult( **kw )

	def parametersSelectedSignal( self ) :
		return self._resultSelectedSignal()



class _ShaderDialogue( _ShaderDialogueBase ) :

	def __init__( self, shaderNetworks, title = None, **kw ) :

		if title is None :
			title = "Select Shader"

		_ShaderDialogueBase.__init__( self, shaderNetworks, title, False, **kw )

	# Causes the dialogue to enter a modal state, returning the handle of the selected shader once it
	# has been selected by the user. Returns None if the dialogue is cancelled.
	def waitForShader( self, **kw ) :
		return self._waitForResult( **kw )

	def shaderSelectedSignal( self ) :
		return self._resultSelectedSignal()

##########################################################################
# Conditional parameter visibility
##########################################################################

# Evaluates conditional visibility as it is defined in third-party `.args`
# files. `queryFunction` is called to look up metadata values for keys such as
# `conditionalVisOp` etc.
#
## \todo Define a standard Gaffer mechanism for shader parameter visibility
#  that closely matches our general-purpose plug visibility mechanism, and
#  then hook `.args` files into that. That might look something like this :
#
# - Allow `layout:activator:{name}` metadata to be registered to `{shaderType}:{shaderName}`
#   shader targets, and forward these to the `Shader.parameters` plug. The difficulty here
#   is forwarding targets whose names are not known in advance - our Metadata API doesn't
#   currently support that. And the value would need to be a Python expression which we
#   `eval()`, which isn't ideal.
# - Allow `layout:visibilityActivator` metadata to be registered to `{shaderType}:{shaderName}:{parameterName}
#   parameter targest, with values referencing the names of activators registered above. Forward
#   this to `Shader.parameters.*` plugs.
# - Convert `.args` conditional visibility into expressions suitable for use in the above and
#   register them as metadata.
# - Likewise convert our OSL visibility metadata into expressions suitable for use in the
#   above.
def _evaluateConditionalVisibility( parametersPlug, queryFunction ) :

	return __evaluateConditionalOp( parametersPlug, queryFunction, "conditionalVis", defaultValue = True )

def _evaluateConditionalLock( parametersPlug, queryFunction ) :

	return __evaluateConditionalOp( parametersPlug, queryFunction, "conditionalLock", defaultValue = False )

def __evaluateConditionalOp( parametersPlug, queryFunction, prefix, defaultValue = None ) :

	op = queryFunction( f"{prefix}Op" )
	if op is None :
		if defaultValue is not None :
			return defaultValue
		IECore.msg( IECore.Msg.Level.Warning, "ShaderUI", f"`{prefix}Op` is missing" )
		return True

	if op in ( "and", "or" ) :

		left = __queryOrWarn( queryFunction, f"{prefix}Left" )
		right = __queryOrWarn( queryFunction, f"{prefix}Right" )

		if left is None or right is None :
			return True

		operand1 = __evaluateConditionalOp( parametersPlug, queryFunction, left )
		operand2 = __evaluateConditionalOp( parametersPlug, queryFunction, right )

	else :

		path = __queryOrWarn( queryFunction, f"{prefix}Path" )
		value = __queryOrWarn( queryFunction, f"{prefix}Value" )

		if path is None or value is None :
			return True

		plugName = path.rpartition( "/" )[2]
		pathPlug = parametersPlug.getChild( plugName )
		if pathPlug is None :
			IECore.msg( IECore.Msg.Level.Warning, "ShaderUI", f"`{path}` not found" )
			return True

		operand1 = pathPlug.getValue()
		operand2 = operand1.__class__( value )

	match op :
		case "equalTo" :
			return operand1 == operand2
		case "notEqualTo" :
			return operand1 != operand2
		case "greaterThan" :
			return operand1 > operand2
		case "lessThan" :
			return operand1 < operand2
		case "greaterThanOrEqualTo" :
			return operand1 >= operand2
		case "lessThanOrEqualTo" :
			return operand1 <= operand2
		case "or" :
			return operand1 or operand2
		case "and" :
			return operand1 and operand2
		case _ :
			IECore.msg( IECore.Msg.Level.Warning, "ShaderUI", f"Unknown operation `{op}`" )
			return True

def __queryOrWarn( query, key ) :

	result = query( key )
	if result is None :
		IECore.msg( IECore.Msg.Level.Warning, "ShaderUI", f"`{key}` is missing" )

	return result
