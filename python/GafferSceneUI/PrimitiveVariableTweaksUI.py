##########################################################################
#
#  Copyright (c) 2024, Image Engine Design Inc. All rights reserved.
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

import imath
import functools
import collections

import IECore
import IECoreScene

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

def __primVarTweaksSelectionModeEnabled( node ):
	return not node["interpolation"].getValue() in [
		IECoreScene.PrimitiveVariable.Interpolation.Invalid, IECoreScene.PrimitiveVariable.Interpolation.Constant
	]


Gaffer.Metadata.registerNode(

	GafferScene.PrimitiveVariableTweaks,

	"description",
	"""
	Modify primitive variable values. Supports modifying values just for specific elements of the
	primitive.
	""",

	"layout:activator:selectionModeEnabled", lambda node : __primVarTweaksSelectionModeEnabled( node ),
	"layout:activator:idListExplicitVisible", lambda node : __primVarTweaksSelectionModeEnabled( node ) and node["selectionMode"].getValue() == GafferScene.PrimitiveVariableTweaks.SelectionMode.IdList,
	"layout:activator:idListVarVisible", lambda node : __primVarTweaksSelectionModeEnabled( node ) and node["selectionMode"].getValue() == GafferScene.PrimitiveVariableTweaks.SelectionMode.IdListPrimitiveVariable,
	"layout:activator:idListVisible", lambda node : __primVarTweaksSelectionModeEnabled( node ) and node["selectionMode"].getValue() in [ GafferScene.PrimitiveVariableTweaks.SelectionMode.IdList, GafferScene.PrimitiveVariableTweaks.SelectionMode.IdListPrimitiveVariable ],
	"layout:activator:maskVarVisible", lambda node : __primVarTweaksSelectionModeEnabled( node ) and node["selectionMode"].getValue() == GafferScene.PrimitiveVariableTweaks.SelectionMode.MaskPrimitiveVariable,

	"layout:section:Settings.Tweaks:collapsed", False,

	plugs = {

		"interpolation" : [

			"description",
			"""
			The interpolation of the target primitive variables. Using "Any" allows you to
			operate on any primitive variable, but if you know your target, using a more
			specific interpolation offers benefits: you can specify an idList to operate
			on specific elements, and you can use "Create" mode to create new primitive
			variables.
			""",

			"preset:Any", IECoreScene.PrimitiveVariable.Interpolation.Invalid,
			"preset:Constant", IECoreScene.PrimitiveVariable.Interpolation.Constant,
			"preset:Uniform", IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			"preset:Vertex", IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			"preset:Varying", IECoreScene.PrimitiveVariable.Interpolation.Varying,
			"preset:FaceVarying", IECoreScene.PrimitiveVariable.Interpolation.FaceVarying,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"selectionMode" : [

			"description",
			"""
			Chooses how to select which elements are affected. Only takes effect if you
			choose an interpolation other than "Any" or "Constant". "Id List" shows a
			list plug to manually select ids. "Id List Primitive Variable" takes
			the name of a constant array primitive variable containing a list of ids.
			"Mask Primitive Variable" takes the name of a primvar that must match the
			selected interpolation - the tweak will apply to all elements where the primitive
			variable is non-zero.
			""",

			"preset:All", GafferScene.PrimitiveVariableTweaks.SelectionMode.All,
			"preset:Id List", GafferScene.PrimitiveVariableTweaks.SelectionMode.IdList,
			"preset:Id List Primitive Variable", GafferScene.PrimitiveVariableTweaks.SelectionMode.IdListPrimitiveVariable,
			"preset:Mask Primitive Variable", GafferScene.PrimitiveVariableTweaks.SelectionMode.MaskPrimitiveVariable,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

			"layout:activator", "selectionModeEnabled",

		],

		"idList" : [

			"description",
			"""
			A list of ids for the elements to affect, corresponding to the current interpolation. For
			example, if you choose "Vertex" interpolation, these will be vertex ids. By default, ids
			are based on the index, but if you specify an id primitive variable below, the ids in
			this list will match the id primitive variable.
			""",

			"layout:visibilityActivator", "idListExplicitVisible",

		],

		"idListVariable" : [

			"description",
			"""
			The name of a constant primitive variable containing a list of ids for the elements to affect,
			corresponding to the current interpolation. For example, if you choose "Vertex" interpolation,
			these will be vertex ids. By default, ids are based on the index, but if you specify an id
			primitive variable below, the ids in this list will match the id primitive variable.
			""",

			"layout:visibilityActivator", "idListVarVisible",

		],

		"id" : [

			"description",
			"""
			The name of the primitive variable to use as ids. Affects which elements are selected by the idList.
			""",

			"layout:visibilityActivator", "idListVisible",

		],

		"maskVariable" : [

			"description",
			"""
			The name of a primitive variable containing a mask. The variable must match the specified interpolation.
			Any elements where the mask variable is non-zero will be tweaked.
			""",

			"layout:visibilityActivator", "maskVarVisible",

		],

		"ignoreMissing" : [

			"description",
			"""
			Ignores tweaks targeting missing primitive variables. When off, missing primitive variables
			cause the node to error.
			""",

		],

		"tweaks" : [

			"description",
			"""
			The tweaks to be made to the primitive variables. Arbitrary numbers of user defined
			tweaks may be added as children of this plug.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:customWidget:footer:widgetType", "GafferSceneUI.PrimitiveVariableTweaksUI._TweaksFooter",
			"layout:customWidget:footer:index", -1,

			"nodule:type", "",
			"layout:section", "Settings.Tweaks",

		],

		"tweaks.*" : [

			"tweakPlugValueWidget:propertyType", "primitive variable",

		],

		"tweaks.*.value" : [
			"description",
			"""
			For a constant primitive variable, this is just the value of the primitive variable. For
			non-constant primitive variables, this is the value for each element.
			""",
		]
	}
)

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

		for subMenu, items in [
			( "", [
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
				Gaffer.Color4fPlug,
				"BoxDivider",
				IECore.Box2iData( imath.Box2i( imath.V2i( 0 ), imath.V2i( 1 ) ) ),
				IECore.Box2fData( imath.Box2f( imath.V2f( 0 ), imath.V2f( 1 ) ) ),
				IECore.Box3iData( imath.Box3i( imath.V3i( 0 ), imath.V3i( 1 ) ) ),
				IECore.Box3fData( imath.Box3f( imath.V3f( 0 ), imath.V3f( 1 ) ) ),
				"ArrayDivider"
			] ),
			( "Array", [
				IECore.FloatVectorData(),
				IECore.IntVectorData(),
				IECore.Int64VectorData(),
				"StringVectorDivider",
				IECore.StringVectorData()
			] )
		]:
			for item in items:
				prefix = "/" + subMenu if subMenu else ""

				if isinstance( item, str ) :
					result.append( prefix + "/" + item, { "divider" : True } )
				else :
					itemName = item.typeName() if isinstance( item, IECore.Data ) else item.__name__
					itemName = itemName.replace( "Plug", "" ).replace( "Data", "" ).replace( "Vector", "" )

					if hasattr( item, "getInterpretation" ):
						itemName += " (" + str( item.getInterpretation() ) + ")"

					result.append(
						prefix + "/" + itemName,
						{
							"command" : functools.partial( Gaffer.WeakMethod( self.__addTweak ), "", item ),
						}
					)

		return result

	def __addFromAffectedMenuDefinition( self ) :

		node = self.getPlug().node()
		assert( isinstance( node, GafferScene.PrimitiveVariableTweaks ) )

		pathMatcher = IECore.PathMatcher()
		with self.context() :
			GafferScene.SceneAlgo.matchingPaths( node["filter"], node["in"], pathMatcher )

		return self.__addFromPathsMenuDefinition( pathMatcher.paths() )

	def __addFromSelectedMenuDefinition( self ) :

		return self.__addFromPathsMenuDefinition(
			GafferSceneUI.ScriptNodeAlgo.getSelectedPaths( self.scriptNode() ).paths()
		)

	def __addFromPathsMenuDefinition( self, paths ) :

		result = IECore.MenuDefinition()

		node = self.getPlug().node()
		assert( isinstance( node, GafferScene.PrimitiveVariableTweaks ) )

		possibilities = {}
		with self.context() :
			for path in paths :
				obj = node["in"].object( path )
				for name in obj.keys():
					d = obj[name].data
					newType = type( d )
					if obj[name].interpolation != IECoreScene.PrimitiveVariable.Interpolation.Constant:
						# Convert to element type ( ie V3fVectorData to V3fData ).
						# When tweaking non-constant primvars, the tweak must match each element.
						newType = IECore.DataTraits.dataTypeFromElementType( IECore.DataTraits.valueTypeFromSequenceType( newType ) )
					newData = newType()
					if hasattr( d, "getInterpretation" ):
						newData.setInterpretation( d.getInterpretation() )

					possibilities[name] = newData

			existingTweaks = { tweak["name"].getValue() for tweak in node["tweaks"] }

		possibilities = collections.OrderedDict( sorted( possibilities.items() ) )

		for key, value in possibilities.items() :
			result.append(
				"/" + key,
				{
					"command" : functools.partial(
						Gaffer.WeakMethod( self.__addTweak ),
						key,
						value
					),
					"active" : key not in existingTweaks
				}
			)

		if not len( result.items() ) :
			result.append(
				"/No Primitive Variables Found", { "active" : False }
			)
			return result

		return result

	def __addTweak( self, privVarName, plugTypeOrValue ) :

		if isinstance( plugTypeOrValue, IECore.Data ) :
			plug = Gaffer.TweakPlug( privVarName, plugTypeOrValue )
		else :
			plug = Gaffer.TweakPlug( privVarName, plugTypeOrValue() )

		plug.setName( "tweak0" )

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().addChild( plug )
