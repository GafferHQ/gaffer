##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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
import IECoreScene

import Gaffer
import GafferUI
import GafferSceneUI

from GafferUI.PlugValueWidget import sole

Gaffer.Metadata.registerNode(

	GafferSceneUI.VisualiserTool,

	"description",
	"""
	Tool for displaying object data.
	""",

	"viewer:shortCut", "L",
	"viewer:shouldAutoActivate", False,
	"order", 8,
	"tool:exclusive", False,

	"toolbarLayout:activator:modeIsColor", lambda node : node["mode"].getValue() == GafferSceneUI.VisualiserTool.Mode.Color,
	"toolbarLayout:activator:modeIsAuto", lambda node : node["mode"].getValue() == GafferSceneUI.VisualiserTool.Mode.Auto,

	plugs = {

		"dataName" : [

			"description",
			"""
			The name of the data to visualise. Primitive variable names must be
			prefixed by `primitiveVariable:`. For example, `primitiveVariable:uv`
			would display the `uv` primitive variable. Primitive variables of
			type int, float, V2f, Color3f or V3f can be visualised.

			To visualise vertex indices instead of a primitive variable, use the
			value `vertex:index`.
			""",

			"toolbarLayout:section", "Bottom",
			"toolbarLayout:width", 150,

			"plugValueWidget:type", "GafferSceneUI.VisualiserToolUI._DataNameChooser",

		],
		"opacity" : [

			"description",
			"""
			The amount the visualiser will occlude the scene locations being visualised.
			""",

			"toolbarLayout:section", "Bottom",
			"toolbarLayout:width", 45,

		],
		"mode" : [

			"description",
			"""
			The method for displaying the data.

			- Auto : Chooses the most appropriate mode based on the data and primitive type.
			- Color : Values are remapped from the range `[valueMin, valueMax]` to `[0, 1]`.
			- Color (Auto Range) : Float, integer, V2f and color data is displayed without
			modification. Vector data is remapped from `[-1, 1]` to `[0, 1]`.
			""",

			"preset:Auto", GafferSceneUI.VisualiserTool.Mode.Auto,
			"preset:Color", GafferSceneUI.VisualiserTool.Mode.Color,
			"preset:Color (Auto Range)", GafferSceneUI.VisualiserTool.Mode.ColorAutoRange,
			"preset:Vertex Label", GafferSceneUI.VisualiserTool.Mode.VertexLabel,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

			"toolbarLayout:section", "Bottom",
			"toolbarLayout:width", 150,

		],
		"valueMin" : [

			"description",
			"""
			The minimum data channel value that will be mapped to 0.

			For float data only the first channel is used. For V2f data only the first
			and second channels are used. For V3f data all three channels are used.
			""",

			"toolbarLayout:section", "Bottom",
			"toolbarLayout:width", 175,

			"toolbarLayout:visibilityActivator", "modeIsColor",

		],
		"valueMax" : [

			"description",
			"""
			The maximum data channel value that will be mapped to 1.

			For float data only the first channel is used. For V2f data only the first
			and second channels are used. For V3f data all three channels are used.
			""",

			"toolbarLayout:section", "Bottom",
			"toolbarLayout:width", 175,

			"toolbarLayout:visibilityActivator", "modeIsColor",

		],
		"size": [

			"description",
			"""
			Specifies the size of the displayed text.
			""",

			"plugValueWidget:type", ""

		],
		"vectorScale" : [

			"description",
			"""
			The scale factor to apply to vectors.
			""",

			"toolbarLayout:section", "Bottom",
			"toolbarLayout:width", 45,

			"toolbarLayout:visibilityActivator", "modeIsAuto",

		],

		"vectorColor" : [

			"description",
			"""
			The colour to use for drawing vectors.
			""",

			"toolbarLayout:section", "Bottom",
			"toolbarLayout:width", 175,

			"toolbarLayout:visibilityActivator", "modeIsAuto",
			"colorPlugValueWidget:colorChooserButtonVisible", False,

			"plugValueWidget:type", "GafferSceneUI.VisualiserToolUI._UntransformedColorWidget",

		],

	},
)

class _UntransformedColorWidget( GafferUI.ColorPlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		GafferUI.ColorPlugValueWidget.__init__( self, plugs, **kw )

		self.setDisplayTransform( GafferUI.Widget.identityDisplayTransform )

class _DataNameChooser( GafferUI.PlugValueWidget ) :

	__primitiveVariablePrefix = "primitiveVariable:"
	__primitiveVariablePrefixSize = len( __primitiveVariablePrefix )
	__vertexIndexDataName = "vertex:index"

	def __init__( self, plug, **kw ) :

		self.__menuButton = GafferUI.MenuButton(
			menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) )
		)

		GafferUI.PlugValueWidget.__init__( self, self.__menuButton, plug, **kw )

	def _updateFromValues( self, values, exception ) :

		singleValue = sole( values )
		text = "None"
		if singleValue is not None :
			text = "Vertex Index" if singleValue == self.__vertexIndexDataName else self.__primitiveVariableFromDataName( singleValue )

		self.__menuButton.setText( text )

	def __menuDefinition( self ) :

		menuDefinition = IECore.MenuDefinition()

		node = self.getPlug().node()
		if not isinstance( node, GafferSceneUI.VisualiserTool ) :
			return
		if self.getPlug() != node["dataName"] :
			return

		scenePlug = node.view()["in"].getInput()
		scriptNode = node.view().scriptNode()
		with node.view().context() :
			selection = GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( scriptNode )

			primitiveVariables = set()

			for path in selection.paths() :
				if not scenePlug.exists( path ) :
					continue

				primitive = scenePlug.object( path )
				if not isinstance( primitive, IECoreScene.Primitive ) :
					continue

				for v in primitive.keys() :
					if primitive[v].interpolation not in [
						IECoreScene.PrimitiveVariable.Interpolation.FaceVarying,
						IECoreScene.PrimitiveVariable.Interpolation.Uniform,
						IECoreScene.PrimitiveVariable.Interpolation.Vertex,
					] :
						continue

					if not isinstance(
						primitive[v].data,
						(
							IECore.IntVectorData,
							IECore.FloatVectorData,
							IECore.V2fVectorData,
							IECore.Color3fVectorData,
							IECore.V3fVectorData,
							IECore.QuatfVectorData,
						)
					) :
						continue

					primitiveVariables.add( v )

		if len( primitiveVariables ) == 0 :
			menuDefinition.append( "/None Available", { "active" : False } )

		else :
			for v in reversed( sorted( primitiveVariables ) ) :
				menuDefinition.prepend(
					"/" + v,
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__setDataName ), self.__primitiveVariablePrefix + v ),
						"checkBox" : self.__primitiveVariableFromDataName( self.getPlug().getValue() ) == v,
					}
				)

		menuDefinition.prepend( "/PrimitiveVariableDivider", { "divider" : True, "label" : "Primitive Variables" } )

		menuDefinition.append( "/Other", { "divider" : True, "label" : "Other" } )
		menuDefinition.append(
			"/Vertex Index",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__setDataName ), self.__vertexIndexDataName ),
				"checkBox" : self.getPlug().getValue() == self.__vertexIndexDataName,
			}
		)

		return menuDefinition

	def __setDataName( self, value, *unused ) :

		self.getPlug().setValue( value )

	def __primitiveVariableFromDataName( self, name ) :

		return name[self.__primitiveVariablePrefixSize:] if (
			name.startswith( self.__primitiveVariablePrefix ) ) else ""
