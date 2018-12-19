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

	def walkOutputs( plug ) :

		if isinstance( plug.node(), GafferScene.ShaderTweaks ) :
			return plug.node()

		for output in plug.outputs() :
			node = walkOutputs( output )
			if node is not None :
				return node

	return walkOutputs( plugValueWidget.getPlug() )

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
		paths = [ p for p in paths if GafferScene.SceneAlgo.exists( node["in"], p ) ]

	return paths

def _shaderAttributes( plugValueWidget, paths, affectedOnly ) :

	result = {}
	node = _shaderTweaksNode( plugValueWidget )
	if node is None :
		return result

	with plugValueWidget.getContext() :
		attributeNamePatterns = node["shader"].getValue() if affectedOnly else "*"
		for path in paths :
			attributes = node["in"].attributes( path )
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

				GafferUI.MenuButton(
					image = "plus.png",
					hasFrame = False,
					menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) )
				)

				GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

	def _updateFromPlug( self ) :

		self.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		result.append(
			"/From Affected",
			{
				"subMenu" : Gaffer.WeakMethod( self.__addFromAffectedMenuDefinition )
			}
		)

		result.append(
			"/From Selection",
			{
				"subMenu" : Gaffer.WeakMethod( self.__addFromSelectedMenuDefinition )
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

			if isinstance( item, basestring ) :
				result.append( "/" + item, { "divider" : True } )
			else :
				result.append(
					"/" + item.__name__.replace( "Plug", "" ),
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__addTweak ), "", item ),
					}
				)

		return result

	def __addFromAffectedMenuDefinition( self ) :

		return self.__addFromPathsMenuDefinition( _pathsFromAffected( self ) )

	def __addFromSelectedMenuDefinition( self ) :

		return self.__addFromPathsMenuDefinition( _pathsFromSelection( self ) )

	def __addFromPathsMenuDefinition( self, paths ) :

		result = IECore.MenuDefinition()

		shaderAttributes = _shaderAttributes( self, paths, affectedOnly = True )
		if not len( shaderAttributes ) :
			result.append(
				"/No Shaders Found", { "active" : False }
			)
			return result

		parameters = {}
		for attributes in shaderAttributes.values() :
			for name, network in attributes.items() :
				shader = network.outputShader()
				for parameterName, parameterValue in shader.parameters.items() :
					if parameterName.startswith( "__" ) :
						continue
					parameters[parameterName] = parameterValue

		if not len( parameters ) :
			result.append(
				"/No Parameters Found", { "active" : False }
			)
			return result

		for parameterName in sorted( parameters.keys() ) :
			result.append(
				"/" + parameterName,
				{
					"command" :	functools.partial(
						Gaffer.WeakMethod( self.__addTweak ),
						parameterName, parameters[parameterName]
					)
				}
			)

		return result

	def __addTweak( self, name, plugTypeOrValue ) :

		if isinstance( plugTypeOrValue, IECore.Data ) :
			plug = GafferScene.TweakPlug( name, plugTypeOrValue )
		else :
			plug = GafferScene.TweakPlug( name, plugTypeOrValue() )

		if name:
			plug.setName( "tweak_" + name )

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
				"active" : not plugValueWidget.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( plugValueWidget.getPlug() ),
			}
		)

	return result

def __plugPopupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	if plug is None :
		return

	node = plug.node()
	if not isinstance( node, GafferScene.ShaderTweaks ) :
		return

	if plug != node["shader"] :
		return

	menuDefinition.prepend( "/ShaderTweaksDivider/", { "divider" : True } )
	menuDefinition.prepend( "/From Selection/", { "subMenu" : __setShaderFromSelectionMenuDefinition } )
	menuDefinition.prepend( "/From Affected/", { "subMenu" : __setShaderFromAffectedMenuDefinition } )

GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu, scoped = False )
