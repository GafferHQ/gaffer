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

	"layout:section:Settings.Tweaks:collapsed", False,

	plugs = {

		"shader" : {

			"description" :
			"""
			The type of shader to modify. This is actually the name
			of an attribute which contains the shader network.
			""",

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"presetsPlugValueWidget:allowCustom" : True,

			"preset:None" : "",

			"layout:index" : 0

		},

		"localise" : {

			"description" :
			"""
			Turn on to allow location-specific tweaks to be made to inherited
			shaders. Shaders will be localised to locations matching the
			node's filter prior to tweaking. The original inherited shader will
			remain untouched.
			""",

			"layout:index" : 1
		},

		"ignoreMissing" : {

			"description" :
			"""
			Ignores tweaks targeting missing parameters. When off, missing parameters
			cause the node to error.
			""",

			"layout:index" : 2

		},

		"tweaks" : {

			"description" :
			"""
			The tweaks to be made to the parameters of the shader.
			Arbitrary numbers of user defined tweaks may be
			added as children of this plug via the user
			interface, or using the ShaderTweaks API via python.
			""",

			"layout:section" : "Settings.Tweaks",
			"plugValueWidget:type" : "GafferUI.LayoutPlugValueWidget",
			"layout:customWidget:footer:widgetType" : "GafferUI.PlugCreationWidget",
			"layout:customWidget:footer:index" : -1,
			"plugCreationWidget:excludedTypes" : "Gaffer.Box*Plug Gaffer.ObjectPlug",
			"ui:scene:acceptsShaderParameters" : True,

			"nodule:type" : "GafferUI::CompoundNodule",
			"noduleLayout:section" : "left",
			"noduleLayout:spacing" : 0.2,

			# Add + button for showing and hiding parameters in the GraphEditor
			"noduleLayout:customGadget:addButton:gadgetType" : "GafferSceneUI.ShaderTweaksUI.PlugAdder",

		},

		"tweaks.*" : {

			# ClosurePlugs are visible by default, because the only thing you can do with them is make
			# connections. Other plugs can be shown individually using PlugAdder above.
			"noduleLayout:visible" : lambda plug : isinstance( plug["value"], GafferScene.ClosurePlug ),
			"tweakPlugValueWidget:propertyType" : "parameter",
			"plugValueWidget:type" : "GafferSceneUI.ShaderTweaksUI._ShaderTweakPlugValueWidget",

		},

	}

)

##########################################################################
# Internal utilities
##########################################################################

def _shaderTweaksNode( plug ) :

	# The plug may not belong to a ShaderTweaks node
	# directly. Instead it may have been promoted
	# elsewhere and be driving a target plug on a
	# ShaderTweaks node.

	return Gaffer.PlugAlgo.findDestination(
		plug,
		lambda plug : plug.node() if isinstance( plug.node(), GafferScene.ShaderTweaks ) else None,
	)

def _pathsFromAffected( plug ) :

	node = _shaderTweaksNode( plug )
	if node is None :
		return []

	pathMatcher = IECore.PathMatcher()
	GafferScene.SceneAlgo.matchingPaths( node["filter"], node["in"], pathMatcher )

	return pathMatcher.paths()

def _pathsFromSelection( plug ) :

	node = _shaderTweaksNode( plug )
	if node is None :
		return []

	paths = GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( plug.ancestor( Gaffer.ScriptNode ) )
	paths = paths.paths() if paths else []

	return [ p for p in paths if node["in"].exists( p ) ]

def _shaderAttributes( plug, paths, affectedOnly ) :

	result = {}
	node = _shaderTweaksNode( plug )
	if node is None :
		return result

	useFullAttr = node["localise"].getValue()
	attributeNamePatterns = node["shader"].getValue() if affectedOnly else "*"
	for path in paths :
		attributes = node["in"].fullAttributes( path, withGlobalAttributes = True ) if useFullAttr else node["in"].attributes( path )
		for name, attribute in attributes.items() :
			if not IECore.StringAlgo.matchMultiple( name, attributeNamePatterns ) :
				continue
			if not isinstance( attribute, IECoreScene.ShaderNetwork ) or not len( attribute ) :
				continue
			result.setdefault( path, {} )[name] = attribute

	return result

##########################################################################
# PlugCreationWidget menu extensions
##########################################################################

def __browseAffectedShaders( menu ) :

	plugCreationWidget = menu.ancestor( GafferUI.PlugCreationWidget )
	__browseShaders( plugCreationWidget, _pathsFromAffected( plugCreationWidget.plugParent() ), "Affected Shaders" )

def __browseSelectedShaders( menu ) :

	plugCreationWidget = menu.ancestor( GafferUI.PlugCreationWidget )
	__browseShaders( plugCreationWidget, _pathsFromSelection( plugCreationWidget.plugParent() ), "Selected Shaders" )

def __browseShaders( plugCreationWidget, paths, title ) :

	shaderAttributes = _shaderAttributes( plugCreationWidget.plugParent(), paths, affectedOnly = True )

	uniqueNetworks = { n.hash(): n for a in shaderAttributes.values() for n in a.values() }

	browser = GafferSceneUI.ShaderUI._ShaderParameterDialogue( uniqueNetworks.values(), title )

	shaderTweaks = browser.waitForParameters( parentWindow = plugCreationWidget.ancestor( GafferUI.ScriptWindow ) )

	if shaderTweaks is not None :
		for shaderName, parameter in shaderTweaks :
			tweaks = {}
			for network in uniqueNetworks.values() :
				if shaderName in network.shaders() and parameter in network.shaders()[shaderName].parameters :
					tweakName = shaderName + "." + parameter if network.getOutput().shader != shaderName else parameter
					if tweakName not in tweaks :
						tweaks[tweakName] = network.shaders()[shaderName].parameters[parameter]

			plugCreationWidget.createPlug(
				Gaffer.PlugAlgo.createPlugFromData( "value", Gaffer.Plug.Direction.In, Gaffer.Plug.Flags.Default, next( iter( tweaks.values() ) ) ),
				name = sole( tweaks.keys() )
			)

def __plugCreationMenu( menuDefinition, widget ) :

	if not Gaffer.Metadata.value( widget.plugParent(), "ui:scene:acceptsShaderParameters" ) :
		return

	menuDefinition.prepend( "/FromPathsDivider", { "divider" : True } )

	menuDefinition.prepend(
		"/From Selection...",
		{
			"command" : __browseSelectedShaders
		}
	)

	menuDefinition.prepend(
		"/From Affected...",
		{
			"command" : __browseAffectedShaders
		}
	)

GafferUI.PlugCreationWidget.plugCreationMenuSignal().connect( __plugCreationMenu )

##########################################################################
# PlugCreationWidget drag & drop extension
##########################################################################

def __filteredParameters( widget, dragDropEvent ) :

	parameters = GafferSceneUI.SceneInspector.draggedParameters( dragDropEvent )
	if not parameters :
		return None

	existingNames = { plug["name"].getValue() for plug in widget.plugParent() }
	return {
		k : v for k, v in parameters.items()
		if k not in existingNames
	}

def __parametersDropHandler( widget, dragDropEvent ) :

	parameters = __filteredParameters( widget, dragDropEvent )
	if not parameters :
		GafferUI.PopupWindow.showWarning( "Parameters added already", parent = widget )

	toCreate = {}
	for name, value in parameters.items() :
		try :
			toCreate[name] = Gaffer.PlugAlgo.createPlugFromData( "value", Gaffer.Plug.Direction.In, Gaffer.Plug.Flags.Default, value )
		except :
			# If we can't handle a parameter, then warn and exit without handling any
			# others. It's confusing if we show a warning but still make some tweaks.
			GafferUI.PopupWindow.showWarning( "Unsupported data type", parent = widget )
			return

	with Gaffer.UndoScope( widget.plugParent().ancestor( Gaffer.ScriptNode ) ) :
		for name, plug in toCreate.items() :
			widget.createPlug( plug, name = name )

def __plugCreationDragEnter( widget, dragDropEvent ) :

	if not Gaffer.Metadata.value( widget.plugParent(), "ui:scene:acceptsShaderParameters" ) :
		return

	if __filteredParameters( widget, dragDropEvent ) is not None :
		return __parametersDropHandler

	return None

GafferUI.PlugCreationWidget.plugCreationDragEnterSignal().connect( __plugCreationDragEnter )

##########################################################################
# _ShaderTweakPlugValueWidget
##########################################################################

class _ShaderTweakPlugValueWidget( GafferUI.TweakPlugValueWidget ) :

	def __init__( self, plugs ):

		GafferUI.TweakPlugValueWidget.__init__( self, plugs )

		with self._TweakPlugValueWidget__row :

			self.__proxyButton = GafferUI.MenuButton(
				image="shaderTweakProxyIcon.png",
				hasFrame=False,
				menu=GafferUI.Menu( Gaffer.WeakMethod( self.__createProxyMenuDefinition ), title = "Create Proxy" ),
				toolTip = "Proxies allow making connections from the outputs of nodes in the input network."
			)

		self.__updateButtonVisibility()

	def setPlugs( self, plugs ) :

		GafferUI.TweakPlugValueWidget.setPlugs( self, plugs )
		self.__updateButtonVisibility()

	def _updateFromEditable( self ) :

		self.__proxyButton.setEnabled(
			not any( Gaffer.MetadataAlgo.readOnly( p["value"] ) for p in self.getPlugs() )
		)

	def __createProxyMenuDefinition( self ) :

		return GafferSceneUI.ShaderTweakProxyUI._plugContextMenu( self.getPlug()["value"], self.getPlug().node() )

	def __updateButtonVisibility( self ) :

		self.__proxyButton.setVisible(
			len( self.getPlugs() ) == 1 and isinstance( self.getPlug().node(), GafferScene.ShaderTweaks )
		)

##########################################################################
# PlugValueWidget context menu
##########################################################################

def __setShaderFromAffectedMenuDefinition( menu ) :

	plug = menu.ancestor( GafferUI.PlugValueWidget ).getPlug()
	return __setShaderFromPathsMenuDefinition( plug, _pathsFromAffected( plug ) )

def __setShaderFromSelectionMenuDefinition( menu ) :

	plug = menu.ancestor( GafferUI.PlugValueWidget ).getPlug()
	return __setShaderFromPathsMenuDefinition( plug, _pathsFromSelection( plug ) )

def __setShader( plug, value ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.setValue( value )

def __setShaderFromPathsMenuDefinition( plug, paths ) :

	shaderAttributes = _shaderAttributes( plug, paths, affectedOnly = False )
	names = set().union( *[ set( a.keys() ) for a in shaderAttributes.values() ] )

	result = IECore.MenuDefinition()
	for name in sorted( names ) :
		result.append(
			"/" + name,
			{
				"command" : functools.partial( __setShader, plug, name ),
				"active" : not Gaffer.MetadataAlgo.readOnly( plug ),
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

GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu )

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

GafferUI.GraphEditor.plugContextMenuSignal().connect( __graphEditorPlugContextMenu )
