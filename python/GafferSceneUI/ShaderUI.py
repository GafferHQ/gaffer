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

def __parameterUserDefault( plug ) :

	shader = plug.node()
	return Gaffer.Metadata.value(
		shader["type"].getValue() + ":" + shader["name"].getValue() + ":" + plug.relativeName( shader["parameters"] ),
		"userDefault"
	)

Gaffer.Metadata.registerNode(

	GafferScene.Shader,

	"description",
	"""
	The base type for all nodes which create shaders. Use the
	ShaderAssignment node to assign them to objects in the scene.
	""",

	"nodeGadget:minWidth", 0.0,
	"nodeGadget:color", functools.partial( __shaderMetadata, key = "nodeGadget:color" ),

	plugs = {

		"name" : [

			"description",
			"""
			The name of the shader being represented. This should
			be considered read-only. Use the `Shader.loadShader()`
			method to load a shader.
			""",

			"label", "Shader",
			"readOnly", True,
			"layout:section", "",
			"nodule:type", "",
			"plugValueWidget:type", "GafferSceneUI.ShaderUI._ShaderNamePlugValueWidget",

		],

		"type" : [

			"description",
			"""
			The type of the shader being represented. This should
			be considered read-only. Use the `Shader.loadShader()`
			method to load a shader.
			""",

			"readOnly", True,
			"layout:section", "",
			"nodule:type", "",
			"plugValueWidget:type", "",

		],

		"parameters" : [

			"description",
			"""
			Where the parameters for the shader are represented.
			""",

			"nodule:type", "GafferUI::CompoundNodule",
			"noduleLayout:section", "left",
			"noduleLayout:spacing", 0.2,
			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",

			# Add + button for showing and hiding parameters in the GraphEditor
			"noduleLayout:customGadget:addButton:gadgetType", "GafferSceneUI.ShaderUI.PlugAdder",

		],

		"parameters..." : [

			# Although the parameters plug is positioned
			# as we want above, we must also register
			# appropriate values for each individual parameter,
			# for the case where they get promoted to a box
			# individually.
			"noduleLayout:section", "left",

			"userDefault", __parameterUserDefault,

		],

		"out" : [

			"description",
			"""
			The output from the shader.
			""",

			"noduleLayout:section", "right",
			"plugValueWidget:type", "",

			# Add + button for showing and hiding parameters in the GraphEditor
			"noduleLayout:customGadget:addButton:gadgetType", "GafferSceneUI.ShaderUI.PlugAdder",

		],

		"out.*" : [

			"noduleLayout:section", "right",

		],

		"attributeSuffix" : [

			"description",
			"""
			Suffix for the attribute used for shader assignment.
			""",

			"nodule:type", "",
			"plugValueWidget:type", "",
			"layout:section", "",

		],

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
			self.__reloadButton.clickedSignal().connect( Gaffer.WeakMethod( self.__reloadButtonClicked ), scoped = False )

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

GafferUI.GraphEditor.plugContextMenuSignal().connect( __graphEditorPlugContextMenu, scoped = False )


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
			data.toolTip = (
				("Shader" if len( path ) == 1 else "Parameter" ) +
				" occurs in multiple " +
				( "networks." if len( path ) == 1 else "shaders." )
			)

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
					data.value = inputs.pop()

					data.toolTip = "Select and scroll to parameter input."

		return data

	def headerData( self, canceller = None ) :

		return self.CellData( self.__title )

# A Path pointing to a shader or shader parameter belonging to one or more
# IECore::ShaderNetworks. Shaders with identical names are merged
# into a single location.

class _ShaderPath( Gaffer.Path ) :

	def __init__( self, shaderNetworks, path, root = "/", filter = None, connectedParametersOnly = False ) :

		Gaffer.Path.__init__( self, path, root, filter )

		self.__connectedParametersOnly = connectedParametersOnly

		assert( all( [ isinstance( n, IECoreScene.ShaderNetwork ) for n in shaderNetworks ] ) )

		self.__shaderNetworks = shaderNetworks

	def isValid( self ) :

		if len( self ) > 0 and self.__shaders() is None :
			return False

		if len( self ) > 1 and self[1] not in self.__parameters():
			return False

		if len( self ) > 2 :
			return False

		return True

	def isLeaf( self, canceller = None ) :

		return self.__isParameter()

	def propertyNames( self, canceller = None ) :

		commonProperties = [
			"shader:instances"
		]

		if self.__isParameter() :
			return Gaffer.Path.propertyNames( self ) + [
				"shader:value",
				"shader:inputs",
			] + commonProperties

		elif self.__isShader() :
			return Gaffer.Path.propertyNames( self ) + [
				"shader:type",
			] + commonProperties

	def property( self, name, canceller = None ) :

		if self.__isParameter() :
			if name == "shader:instances" :
				return self.__parameters().count( self[1] )

			if name == "shader:value" :
				value = sole( self.__parameterValues() )
				return value if value is not None else "---"

			if name == "shader:inputs" :

				connections = {
					c.source.shader for n in self.__shaderNetworks if (
						n.getShader( self[0] ) is not None
					) for c in n.inputConnections( self[0] ) if (
						c.destination.name.split( '.' )[0] == self[1]
					)
				}

				return connections

		elif self.__isShader() :
			if name == "shader:instances" :
				return len( self.__shaders() )

			if name == "shader:type" :
				shaders = self.__shaders()

				shader = sole( [ s.name for s in self.__shaders() ] )

				return shader if shader is not None else "---"

		return Gaffer.Path.property( self, name )

	def copy( self ) :

		return _ShaderPath( self.__shaderNetworks, self[:], self.root(), self.getFilter(), self.__connectedParametersOnly )

	def _children( self, canceller ) :

		if self.isLeaf() :
			return []

		result = []

		# Shaders, ordered by depth from the output shader
		if len( self ) == 0 :
			shaders = set()
			visited = set()

			stack = deque(
				sorted(
					[ ( n, n.getOutput().shader ) for n in self.__shaderNetworks ],
					key = lambda k : k[1]
				)
			)

			while stack :
				shaderNetwork, shaderHandle = stack.popleft()

				h = shaderNetwork.hash().append( shaderHandle )

				if h not in visited :
					visited.add( h )

					if shaderHandle not in shaders :
						shaders.add( shaderHandle )
						result.append(
							_ShaderPath(
								self.__shaderNetworks,
								self[:] + [shaderHandle],
								self.root(),
								self.getFilter(),
								self.__connectedParametersOnly
							)
						)

					stack.extend(
						[ ( shaderNetwork, i.source.shader ) for i in shaderNetwork.inputConnections( shaderHandle ) ]
					)

		# Parameters
		elif self.__isShader() :
			parameterNames = sorted( set( self.__parameters() ) )
			for p in parameterNames :
				result.append(
					_ShaderPath(
						self.__shaderNetworks,
						self[:] + [p],
						self.root(),
						self.getFilter(),
						self.__connectedParametersOnly
					)
				)

		return result

	# Returns a list of all parameters that belong to the path's shaders.
	# This will mix parameters from different types of shaders into a single list
	# if multiple shaders in the networks have the same name but different type.
	def __parameters( self ) :

		if len( self ) == 0 :
			return []

		if self.__connectedParametersOnly :
			connectedParams = set()
			for n in self.__shaderNetworks :
				if n.getShader( self[0] ) is not None :
					for c in n.inputConnections( self[0] ) :
						connectedParams.add( c.destination.name )
			return list( connectedParams )

		return [ p for s in self.__shaders() for p in s.parameters.keys() ]

	# Returns a list of all shaders with a name matching the path's shader name.
	def __shaders( self ) :

		if len( self ) > 0 :

			uniqueShaders = {}
			for network in self.__shaderNetworks :
				shader = network.getShader( self[0] )
				if shader is not None :
					uniqueShaders[shader.hash()] = shader

			return list( uniqueShaders.values() )

		return None

	def __isShader( self ) :

		return len( self ) == 1 and self.isValid()

	def __isParameter( self ) :

		return len( self ) == 2 and self.isValid()

	# Returns a list of values for the path's parameter.
	def __parameterValues( self ) :

		if self.__isParameter() :
			return [ s.parameters[ self[1] ] for s in self.__shaders() if self[1] in s.parameters ]

		return None

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

		rootPath.pathChangedSignal().connect( Gaffer.WeakMethod( self.__rootPathChanged ), scoped = False )

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
		self.__cancelled = False

		self.__shaderNetworks = shaderNetworks

		self.__path = _ShaderPath( self.__shaderNetworks, path = "/", connectedParametersOnly = not self.__selectParameters )

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

		self.__pathListingWidget.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__updateButtonState ), scoped = False )
		self.__pathListingWidget.buttonReleaseSignal().connectFront( Gaffer.WeakMethod( self.__buttonRelease ), scoped = False )
		self.__pathListingWidget.pathSelectedSignal().connect( Gaffer.WeakMethod( self.__pathSelected ), scoped = False )

		self._addButton( "Cancel" )
		self.__confirmButton = self._addButton( "OK" )
		self.__confirmButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ), scoped = False )

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
			inputRootPath = path.parent().parent()
			inputs = path.property( "shader:inputs" )

			if inputs is None :
				return False

			if len( inputs ) == 0 :
				return False

			inputPaths = [ inputRootPath.copy().append( i ) for i in inputs ]

			if all( [ i.isValid() for i in inputPaths ] ) :
				self.__pathListingWidget.setSelection( IECore.PathMatcher( [ str( i ) for i in inputPaths ] ) )

			return True

		return False

	def __result( self ) :

		resultPaths = self.__pathListingWidget.getSelection()

		if not self.__selectParameters:
			if not resultPaths.paths() or resultPaths.paths()[0].rfind( "/" ) > 0:
				return None

			return resultPaths.paths()[0].strip( "/" )

		resultPaths = [ self.__path.copy().setFromString( x ) for x in resultPaths.paths() ]

		for p in resultPaths :
			if len( p ) < 2 :
				return []
		return [ ( p[0], p[1] ) for p in resultPaths ]

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
