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
import GafferScene
import GafferSceneUI

Gaffer.Metadata.registerNode(

	GafferScene.LightTweaks,

	"description",
	"""
	Makes modifications to light parameter values.
	""",

	plugs = {

		"type" : [

			"description",
			"""
			The type of light to modify. This is actually the name
			of an attribute which contains the light shader
			network.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:All", "light *:light",
			"preset:Appleseed", "as:light",
			"preset:Arnold", "ai:light",

		],

		"tweaks" : [

			"description",
			"""
			The tweaks to be made to the parameters of the light.
			Arbitrary numbers of user defined tweaks may be
			added as children of this plug via the user
			interface, or using the LightTweaks API via python.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:customWidget:footer:widgetType", "GafferSceneUI.LightTweaksUI._TweaksFooter",
			"layout:customWidget:footer:index", -1,

		],

		"tweaks.*.name" : [

			"description",
			"""
			The name of the parameter to apply the tweak to.
			"""

		],

		"tweaks.*.mode" : [

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Replace", GafferScene.LightTweaks.TweakPlug.Mode.Replace,
			"preset:Add", GafferScene.LightTweaks.TweakPlug.Mode.Add,
			"preset:Subtract", GafferScene.LightTweaks.TweakPlug.Mode.Subtract,
			"preset:Multiply", GafferScene.LightTweaks.TweakPlug.Mode.Multiply,

		],

	}

)

class _TweakPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, childPlug ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__row, childPlug )


		nameWidget = GafferUI.StringPlugValueWidget( childPlug["name"] )
		nameWidget.textWidget()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )

		self.__row.append( nameWidget,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		self.__row.append(
			GafferUI.BoolPlugValueWidget(
				childPlug["enabled"],
				displayMode = GafferUI.BoolWidget.DisplayMode.Switch
			),
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top,
		)

		self.__row.append( GafferUI.PlugValueWidget.create( childPlug["mode"] ) )
		self.__row.append( GafferUI.PlugValueWidget.create( childPlug["value"] ), expand = True )

		self._updateFromPlug()

	def setPlug( self, plug ) :

		GafferUI.PlugValueWidget.setPlug( self, plug )

		self.__row[0].setPlug( plug["name"] )
		self.__row[1].setPlug( plug["enabled"] )
		self.__row[2].setPlug( plug["mode"] )
		self.__row[3].setPlug( plug["value"] )

	def hasLabel( self ) :

		return True

	def childPlugValueWidget( self, childPlug, lazy=True ) :

		for w in self.__row :
			if w.getPlug().isSame( childPlug ) :
				return w

		return None

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )

		for w in self.__row :
			w.setReadOnly( readOnly )

	def _updateFromPlug( self ) :

		with self.getContext() :
			enabled = self.getPlug()["enabled"].getValue()

		for i in ( 0, 2, 3 ) :
			self.__row[i].setEnabled( enabled )


def __deletePlug( plug ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.parent().removeChild( plug )

def __plugPopupMenu( menuDefinition, plugValueWidget ):

	plug = plugValueWidget.getPlug()
	parent = plug.parent()
	node = plug.node()

	if not isinstance( node, GafferScene.LightTweaks ) or not parent.parent().isSame( node["tweaks"] ) :
		return

	menuDefinition.append( "/DeleteDivider", { "divider" : True } )
	menuDefinition.append(
		"/Delete",
		{
			"command" : functools.partial( __deletePlug, parent ),
			"active" : not plugValueWidget.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( parent )
		}
	)

__plugPopupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu )

GafferUI.PlugValueWidget.registerType( GafferScene.LightTweaks.TweakPlug, _TweakPlugValueWidget )

class _TweaksFooter( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.PlugValueWidget.__init__( self, row, plug )

		with row :

				GafferUI.Spacer( IECore.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

				GafferUI.MenuButton(
					image = "plus.png",
					hasFrame = False,
					menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) )
				)

				GafferUI.Spacer( IECore.V2i( 1 ), IECore.V2i( 999999, 1 ), parenting = { "expand" : True } )

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

		paths = []
		node = self.__lightTweaksNode()
		if node is not None :
			pathMatcher = GafferScene.PathMatcher()
			with self.getContext() :
				GafferScene.SceneAlgo.matchingPaths( node["filter"], node["in"], pathMatcher )
				paths = pathMatcher.paths()

		return self.__addFromPathsMenuDefinition( paths )

	def __addFromSelectedMenuDefinition( self ) :

		paths = []
		node = self.__lightTweaksNode()
		if node is not None :
			paths = GafferSceneUI.ContextAlgo.getSelectedPaths( self.getContext() )
			paths = paths.paths() if paths else []
			paths = [ p for p in paths if GafferScene.SceneAlgo.exists( node["in"], p ) ]

		return self.__addFromPathsMenuDefinition( paths )

	def __addFromPathsMenuDefinition( self, paths ) :

		result = IECore.MenuDefinition()

		node = self.__lightTweaksNode()
		if node is None :
			result.append(
				"/No Scene Found", { "active" : False }
			)
			return result

		parameters = {}
		with self.getContext() :
			attributeNamePatterns = node["type"].getValue()
			for path in paths :
				attributes = node["in"].attributes( path )
				for name, network in attributes.items() :
					if not Gaffer.StringAlgo.matchMultiple( name, attributeNamePatterns ) :
						continue
					if not isinstance( network, IECore.ObjectVector ) or not len( network ):
						continue
					if not isinstance( network[-1], IECore.Shader ) :
						continue
					shader = network[-1]
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

	def __lightTweaksNode( self ) :

		# Our plug may not belong to a LightTweaks node
		# directly. Instead it may have been promoted
		# elsewhere and be driving a target plug on a
		# LightTweaksNode.

		def walkOutputs( plug ) :

			if isinstance( plug.node(), GafferScene.LightTweaks ) :
				return plug.node()

			for output in plug.outputs() :
				node = walkOutputs( output )
				if node is not None :
					return node

		return walkOutputs( self.getPlug() )

	def __addTweak( self, name, plugTypeOrValue ) :

		if isinstance( plugTypeOrValue, IECore.Data ) :
			plug = GafferScene.LightTweaks.TweakPlug( name, plugTypeOrValue )
		else :
			plug = GafferScene.LightTweaks.TweakPlug( name, plugTypeOrValue() )

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().addChild( plug )
