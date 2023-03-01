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
import IECoreScene

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

from GafferUI.PlugValueWidget import sole

Gaffer.Metadata.registerNode(

	GafferScene.ShaderTweaks,

	"description",
	"""
	Makes modifications to shader parameter values.
	""",

	plugs = {

		"shader" : [

			"description",
			"""
			The type of shader to modify. This is actually the name
			of an attribute which contains the shader network.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"presetsPlugValueWidget:allowCustom", True,

			"preset:None", "",

			"layout:index", 0

		],

		"localise" : [

			"description",
			"""
			Turn on to allow location-specific tweaks to be made to inherited
			shaders. Shaders will be localised to locations matching the
			node's filter prior to tweaking. The original inherited shader will
			remain untouched.
			""",

			"layout:index", 1
		],

		"ignoreMissing" : [

			"description",
			"""
			Ignores tweaks targeting missing parameters. When off, missing parameters
			cause the node to error.
			""",

			"layout:index", 2

		],

		"tweaks" : [

			"description",
			"""
			The tweaks to be made to the parameters of the shader.
			Arbitrary numbers of user defined tweaks may be
			added as children of this plug via the user
			interface, or using the ShaderTweaks API via python.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:customWidget:footer:widgetType", "GafferSceneUI.ShaderTweaksUI._TweaksFooter",
			"layout:customWidget:footer:index", -1,

			"nodule:type", "GafferUI::CompoundNodule",
			"noduleLayout:section", "left",
			"noduleLayout:spacing", 0.2,

			# Add + button for showing and hiding parameters in the GraphEditor
			"noduleLayout:customGadget:addButton:gadgetType", "GafferSceneUI.ShaderTweaksUI.PlugAdder",

		],

		"tweaks.*" : [

			"noduleLayout:visible", False, # Can be shown individually using PlugAdder above
			"tweakPlugValueWidget:allowCreate", True,
			"tweakPlugValueWidget:allowRemove", True,

		],

	}

)

##########################################################################
# Internal utilities
##########################################################################

def _shaderTweaksNode( plugValueWidget ) :

	# The plug may not belong to a ShaderTweaks node
	# directly. Instead it may have been promoted
	# elsewhere and be driving a target plug on a
	# ShaderTweaks node.

	return Gaffer.PlugAlgo.findDestination(
		plugValueWidget.getPlug(),
		lambda plug : plug.node() if isinstance( plug.node(), GafferScene.ShaderTweaks ) else None,
	)

def _pathsFromAffected( plugValueWidget ) :

	node = _shaderTweaksNode( plugValueWidget )
	if node is None :
		return []

	pathMatcher = IECore.PathMatcher()
	with plugValueWidget.getContext() :
		GafferScene.SceneAlgo.matchingPaths( node["filter"], node["in"], pathMatcher )

	return pathMatcher.paths()

def _pathsFromSelection( plugValueWidget ) :

	node = _shaderTweaksNode( plugValueWidget )
	if node is None :
		return []

	paths = GafferSceneUI.ContextAlgo.getSelectedPaths( plugValueWidget.getContext() )
	paths = paths.paths() if paths else []

	with plugValueWidget.getContext() :
		paths = [ p for p in paths if node["in"].exists( p ) ]

	return paths

def _shaderAttributes( plugValueWidget, paths, affectedOnly ) :

	result = {}
	node = _shaderTweaksNode( plugValueWidget )
	if node is None :
		return result

	with plugValueWidget.getContext() :
		useFullAttr = node["localise"].getValue()
		attributeNamePatterns = node["shader"].getValue() if affectedOnly else "*"
		for path in paths :
			attributes = node["in"].fullAttributes( path ) if useFullAttr else node["in"].attributes( path )
			for name, attribute in attributes.items() :
				if not IECore.StringAlgo.matchMultiple( name, attributeNamePatterns ) :
					continue
				if not isinstance( attribute, IECoreScene.ShaderNetwork ) or not len( attribute ) :
					continue
				result.setdefault( path, {} )[name] = attribute

	return result

##########################################################################
# _TweaksFooter
##########################################################################

class _TweaksFooter( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.PlugValueWidget.__init__( self, row, plug )

		with row :

				GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

				self.__button = GafferUI.MenuButton(
					image = "plus.png",
					hasFrame = False,
					menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) )
				)

				GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

	def _updateFromEditable( self ) :

		# Not using `_editable()` as it considers the whole plug to be non-editable if
		# any child has an input connection, but that shouldn't prevent us adding a new
		# tweak.
		self.__button.setEnabled( self.getPlug().getInput() is None and not Gaffer.MetadataAlgo.readOnly( self.getPlug() ) )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		result.append(
			"/From Affected...",
			{
				"command" : Gaffer.WeakMethod( self.__browseAffectedShaders )
			}
		)

		result.append(
			"/From Selection...",
			{
				"command" : Gaffer.WeakMethod( self.__browseSelectedShaders )
			}
		)

		result.append( "/FromPathsDivider", { "divider" : True } )

		# TODO - would be nice to share these default options with other users of TweakPlug
		for item in [
			Gaffer.BoolPlug,
			Gaffer.FloatPlug,
			Gaffer.IntPlug,
			"NumericDivider",
			Gaffer.StringPlug,
			"StringDivider",
			Gaffer.V2iPlug,
			Gaffer.V3iPlug,
			Gaffer.V2fPlug,
			Gaffer.V3fPlug,
			"VectorDivider",
			Gaffer.Color3fPlug,
			Gaffer.Color4fPlug
		] :

			if isinstance( item, str ) :
				result.append( "/" + item, { "divider" : True } )
			else :
				result.append(
					"/" + item.__name__.replace( "Plug", "" ),
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__addTweak ), "", item ),
					}
				)

		return result

	def __browseAffectedShaders( self ) :

		self.__browseShaders( _pathsFromAffected( self ), "Affected Shaders" )

	def __browseSelectedShaders( self ) :

		self.__browseShaders( _pathsFromSelection( self ), "Selected Shaders" )

	def __browseShaders( self, paths, title ) :

		shaderAttributes = _shaderAttributes( self, paths, affectedOnly = True )

		uniqueNetworks = { n.hash(): n for a in shaderAttributes.values() for n in a.values() }

		browser = GafferSceneUI.ShaderUI._ShaderParameterDialogue( uniqueNetworks.values(), title )

		shaderTweaks = browser.waitForParameters( parentWindow = self.ancestor( GafferUI.ScriptWindow ) )

		if shaderTweaks is not None :
			for shaderName, parameter in shaderTweaks :
				tweaks = {}
				for network in uniqueNetworks.values() :
					if shaderName in network.shaders() and parameter in network.shaders()[shaderName].parameters :
						tweakName = shaderName + "." + parameter if network.getOutput().shader != shaderName else parameter
						if tweakName not in tweaks :
							tweaks[tweakName] = network.shaders()[shaderName].parameters[parameter]

				tweakName = sole( tweaks.keys() )
				if tweakName is None :
					self.__addTweak( shaderName + "." + parameter, list( tweaks.values() )[0] )
				else :
					self.__addTweak( tweakName, tweaks[tweakName] )

	def __addTweak( self, name, plugTypeOrValue ) :

		if isinstance( plugTypeOrValue, IECore.Data ) :
			plug = Gaffer.TweakPlug( name, plugTypeOrValue )
		else :
			plug = Gaffer.TweakPlug( name, plugTypeOrValue() )

		if name :
			for i in ( ".", ":", ) :
				name = name.replace( i, "_" )
			plug.setName( name )

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().addChild( plug )

##########################################################################
# PlugValueWidget context menu
##########################################################################

def __setShaderFromAffectedMenuDefinition( menu ) :

	plugValueWidget = menu.ancestor( GafferUI.PlugValueWidget )
	return __setShaderFromPathsMenuDefinition( plugValueWidget, _pathsFromAffected( plugValueWidget ) )

def __setShaderFromSelectionMenuDefinition( menu ) :

	plugValueWidget = menu.ancestor( GafferUI.PlugValueWidget )
	return __setShaderFromPathsMenuDefinition( plugValueWidget, _pathsFromSelection( plugValueWidget ) )

def __setShader( plug, value ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.setValue( value )

def __setShaderFromPathsMenuDefinition( plugValueWidget, paths ) :

	shaderAttributes = _shaderAttributes( plugValueWidget, paths, affectedOnly = False )
	names = set().union( *[ set( a.keys() ) for a in shaderAttributes.values() ] )

	result = IECore.MenuDefinition()
	for name in sorted( names ) :
		result.append(
			"/" + name,
			{
				"command" : functools.partial( __setShader, plugValueWidget.getPlug(), name ),
				"active" : not Gaffer.MetadataAlgo.readOnly( plugValueWidget.getPlug() ),
			}
		)

	return result

def __plugPopupMenu( menuDefinition, plugValueWidget ) :

	if plugValueWidget.getPlug() is None :
		return

	if Gaffer.PlugAlgo.findDestination(
		plugValueWidget.getPlug(),
		lambda plug : plug if isinstance( plug.parent(), GafferScene.ShaderTweaks ) and plug.getName() == "shader" else None
	) :

		menuDefinition.prepend( "/ShaderTweaksDivider/", { "divider" : True } )
		menuDefinition.prepend( "/From Selection/", { "subMenu" : __setShaderFromSelectionMenuDefinition } )
		menuDefinition.prepend( "/From Affected/", { "subMenu" : __setShaderFromAffectedMenuDefinition } )

GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu, scoped = False )

##########################################################################
# Nodule context menu
##########################################################################

def __setPlugMetadata( plug, key, value ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		Gaffer.Metadata.registerValue( plug, key, value )

def __graphEditorPlugContextMenu( graphEditor, plug, menuDefinition ) :

	if not isinstance( plug.node(), GafferScene.ShaderTweaks ) :
		return

	tweakPlug = plug.parent()
	if not isinstance( tweakPlug, Gaffer.TweakPlug ) :
		return False

	if tweakPlug.parent() != plug.node()["tweaks"] :
		return

	if len( menuDefinition.items() ) :
		menuDefinition.append( "/HideDivider", { "divider" : True } )

	menuDefinition.append(

		"/Hide",
		{
			"command" : functools.partial( __setPlugMetadata, tweakPlug, "noduleLayout:visible", False ),
			"active" : plug.getInput() is None and not Gaffer.MetadataAlgo.readOnly( tweakPlug ),
		}

	)

GafferUI.GraphEditor.plugContextMenuSignal().connect( __graphEditorPlugContextMenu, scoped = False )
