##########################################################################
#
#  Copyright (c) 2013-2014, John Haddon. All rights reserved.
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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
import IECoreScene
import Gaffer
import GafferUI

import GafferOSL

import imath
import functools

_primitiveVariableNamesOptions = {
	"P" : IECore.V3fData( imath.V3f(0), IECore.GeometricData.Interpretation.Point ),
	"Pref" : IECore.V3fData( imath.V3f(0), IECore.GeometricData.Interpretation.Point ),
	"N" : IECore.V3fData( imath.V3f(0), IECore.GeometricData.Interpretation.Normal ),
	"velocity" : IECore.V3fData( imath.V3f(0), IECore.GeometricData.Interpretation.Vector ),
	"uv" : IECore.V3fData( imath.V3f(0), IECore.GeometricData.Interpretation.UV ),
	"scale" : IECore.V3fData( imath.V3f(1) ),
	"width" : IECore.FloatData(),
	"prototypeIndex" : IECore.IntData(),
	"Cs" : IECore.Color3fData(),
	"customInt" : IECore.IntData(),
	"customFloat" : IECore.FloatData(),
	"customVector" : IECore.V3fData( imath.V3f(0), IECore.GeometricData.Interpretation.Vector ),
	"customNormal" : IECore.V3fData( imath.V3f(0), IECore.GeometricData.Interpretation.Normal ),
	"customPoint" : IECore.V3fData( imath.V3f(0), IECore.GeometricData.Interpretation.Point ),
	"customUV" : IECore.V3fData( imath.V3f(0), IECore.GeometricData.Interpretation.UV ),
	"customColor" : IECore.Color3fData(),
	"customMatrix" : IECore.M44fData(),
	"customString" : IECore.StringData(),
	"closure" : None,
}

##########################################################################
# _PrimitiveVariablesFooter
##########################################################################

class _PrimitiveVariablesFooter( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.PlugValueWidget.__init__( self, row, plug )

		with row :

				GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

				menuButton = GafferUI.MenuButton(
					image = "plus.png",
					hasFrame = False,
					menu = GafferUI.Menu(
						Gaffer.WeakMethod( self.__menuDefinition ),
						title = "Add Input"
					),
					toolTip = "Add Input"
				)
				menuButton.setEnabled( not Gaffer.MetadataAlgo.readOnly( plug ) )

				GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

	def _updateFromPlug( self ) :

		self.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()
		usedNames = set()
		for p in self.getPlug().children():
			if not Gaffer.PlugAlgo.dependsOnCompute( p ) :
				usedNames.add( p["name"].getValue() )

		categories = { "Standard" : [], "Custom" : [], "Advanced" : [] }
		for label, defaultData in sorted( _primitiveVariableNamesOptions.items() ):
			if label.startswith( "custom" ):
				primVarName = label
				if primVarName in usedNames:
					suffix = 2
					while True:
						primVarName = label + str( suffix )
						if not primVarName in usedNames:
							break
						suffix += 1
				categories["Custom"].append( ( label[6:], primVarName, defaultData ) )
			elif label == "closure":
				categories["Advanced"].append( ( label, label, defaultData ) )
			else:
				if label in usedNames:
					continue
				categories["Standard"].append( ( label, label, defaultData ) )


		for category in [ "Standard", "Custom", "Advanced" ]:
			for ( menuLabel, primVarName, defaultData ) in categories[category]:
				result.append(
					"/" + category + "/" + menuLabel,
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), primVarName, defaultData ),
					}
				)

		return result

	def __addPlug( self, name, defaultData ) :

		if defaultData == None:
			plugName = "closure"
			name = ""
			valuePlug = GafferOSL.ClosurePlug( "value" )
		else:
			plugName = "primitiveVariable"
			valuePlug = Gaffer.PlugAlgo.createPlugFromData( "value", Gaffer.Plug.Direction.In, Gaffer.Plug.Flags.Default, defaultData )

		plug = Gaffer.NameValuePlug( name, valuePlug, True, plugName, Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().addChild( plug )

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferOSL.OSLObject,

	"description",
	"""
	Executes OSL shaders to perform object processing. Use the shaders from
	the OSL/ObjectProcessing menu to read primitive variables from the input
	object and then write primitive variables back to it.
	""",

	"plugAdderOptions", IECore.CompoundData( _primitiveVariableNamesOptions ),

	plugs = {

		"adjustBounds" : [

			"layout:index", -2,

		],

		"primitiveVariables" : [

			"description",
			"""
			Define primitive varibles to output by adding child plugs and connecting
			corresponding OSL shaders.  Supported plug types are :

			- FloatPlug
			- IntPlug
			- ColorPlug
			- V3fPlug ( outputting vector, normal or point )
			- M44fPlug
			- StringPlug

			If you want to add multiple outputs at once, you can also add a closure plug,
			which can accept a connection from an OSLCode with a combined output closure.
			""",
			"layout:customWidget:footer:widgetType", "GafferOSLUI.OSLObjectUI._PrimitiveVariablesFooter",
			"layout:customWidget:footer:index", -1,
			"nodule:type", "GafferUI::CompoundNodule",
			"noduleLayout:section", "left",
			"noduleLayout:spacing", 0.2,
			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",

			# Add + button for showing and hiding parameters in the GraphEditor
			"noduleLayout:customGadget:addButton:gadgetType", "GafferOSLUI.OSLObjectUI.PlugAdder",

			"layout:index", -1,

		],
		"primitiveVariables.*" : [

			"deletable", True,
			# Although the parameters plug is positioned
			# as we want above, we must also register
			# appropriate values for each individual parameter,
			# for the case where they get promoted to a box
			# individually.
			"noduleLayout:section", "left",
			"nodule:type", "GafferUI::CompoundNodule",
			"nameValuePlugPlugValueWidget:ignoreNamePlug", lambda plug : isinstance( plug["value"], GafferOSL.ClosurePlug ),
		],
		"primitiveVariables.*.name" : [
			"nodule:type", "",
		],
		"primitiveVariables.*.enabled" : [
			"nodule:type", "",
		],
		"primitiveVariables.*.value" : [

			# Although the parameters plug is positioned
			# as we want above, we must also register
			# appropriate values for each individual parameter,
			# for the case where they get promoted to a box
			# individually.
			"noduleLayout:section", "left",
			"noduleLayout:label", lambda plug : plug.parent().getName() if plug.typeId() == GafferOSL.ClosurePlug.staticTypeId() else plug.parent()["name"].getValue(),
			"ui:visibleDimensions", lambda plug : 2 if hasattr( plug, "interpretation" ) and plug.interpretation() == IECore.GeometricData.Interpretation.UV else None,
		],

		"interpolation" : [

			"description",
			"""
			The interpolation type of the primitive variables created by this node.
			For instance, Uniform interpolation means that the shader is run once per face on a mesh, allowing it to output primitive variables with a value per face.
			All non-constant input primitive variables are resampled to match the selected interpolation so that they can be accessed from the shader.
			""",

			"preset:Uniform", IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			"preset:Vertex", IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			"preset:FaceVarying", IECoreScene.PrimitiveVariable.Interpolation.FaceVarying,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",


		],

		"useTransform" : [

			"description",
			"""
			Makes the object's transform available to OSL, so that you can use OSL functions that convert
			from object to world space.
			""",

		],

		"useAttributes" : [

			"description",
			"""
			Makes the Gaffer attributes at the object's location available to OSL through the getattribute
			function.  Once this is on, you can use OSL nodes such as InFloat or InString to retrieve the
			attribute values.
			""",

		],

	}

)
