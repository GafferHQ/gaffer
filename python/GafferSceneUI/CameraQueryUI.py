##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

import IECore

import Gaffer
import GafferUI
import GafferScene

from GafferUI.PlugValueWidget import sole

##########################################################################
# Internal utilities
##########################################################################

def __getLabel( plug ) :

	n = plug.node()
	queryPlug = n.queryPlug( plug )
	prefix = queryPlug.getValue() or "none"

	return prefix + "." + plug.relativeName( n.outPlugFromQuery( queryPlug ) )

##########################################################################
# Query widget
##########################################################################

class _QueryWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, childPlug, **kw ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__row, childPlug )

		nameWidget = GafferUI.StringPlugValueWidget( self.getPlugs() )
		nameWidget.textWidget()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )
		self.__row.append(
			nameWidget,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		sourceLabelWidget = GafferUI.LabelPlugValueWidget(
			{ plug.node().sourcePlugFromQuery( plug ) for plug in self.getPlugs() },
			horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right
		)
		sourceLabelWidget.label()._qtWidget().setFixedWidth( 40 )
		self.__row.append(
			sourceLabelWidget,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		self.__row.append(
			_SourcePlugValueWidget( { plug.node().sourcePlugFromQuery( plug ) for plug in self.getPlugs() } ),
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		valueLabelWidget = GafferUI.LabelPlugValueWidget(
			{ plug.node().valuePlugFromQuery( plug ) for plug in self.getPlugs() },
			horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right
		)
		valueLabelWidget.label()._qtWidget().setFixedWidth( 40 )
		self.__row.append(
			valueLabelWidget,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		self.__row.append(
			GafferUI.PlugValueWidget.create( { plug.node().valuePlugFromQuery( plug ) for plug in self.getPlugs() } )
		)

		self.dropSignal().connectFront( Gaffer.WeakMethod( self.__drop ) )

	def setPlugs( self, plugs ) :

		GafferUI.PlugValueWidget.setPlugs( self, plugs )

		self.__row[0].setPlugs( plugs )
		self.__row[1].setPlugs( { plug.node().sourcePlugFromQuery( plug ) for plug in plugs } )
		self.__row[2].setPlugs( { plug.node().sourcePlugFromQuery( plug ) for plug in plugs } )
		self.__row[3].setPlugs( { plug.node().valuePlugFromQuery( plug ) for plug in plugs } )
		self.__row[4].setPlugs( { plug.node().valuePlugFromQuery( plug ) for plug in plugs } )

	def hasLabel( self ) :

		return True

	def childPlugValueWidget( self, childPlug ) :

		for w in self.__row :
			if childPlug in w.getPlugs() :
				return w

		return None

	def __drop( self, widget, event ) :

		# We dont want to accept plugs or values dropped onto the query row
		# as that would attempt to set the row's query plug, so we always
		# return `True` to block the PlugValueWidget drop handler.
		return True

class _SourcePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, childPlug, **kw ) :

		self.__textWidget = GafferUI.TextWidget( editable = False )
		self.__textWidget._qtWidget().setFixedWidth( 60 )

		GafferUI.PlugValueWidget.__init__( self, self.__textWidget, childPlug )

	def hasLabel( self ) :

		return True

	def _updateFromValues( self, values, exception ) :

		value = sole( values )
		if value is None :
			self.__textWidget.setText( "---" )
		else :
			self.__textWidget.setText(
				GafferScene.CameraQuery.Source.values[ value ].name if value > 0 else "None"
			)

		self.__textWidget.setErrored( exception is not None )

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.CameraQuery,

	"description",
	"""
	Queries parameters from a camera, creating an output for each query.
	""",

	"layout:activator:cameraModeIsLocation", lambda node : node["cameraMode"].getValue() == int( GafferScene.CameraQuery.CameraMode.Location ),

	"layout:section:Settings.Queries:collapsed", False,

	plugs = {

		"scene" : {

			"description" :
			"""
			The scene to query the camera from.
			""",

		},

		"cameraMode" : {

			"description" :
			"""
			How the camera to be queried is specified.

			- Render Camera : Uses the value of the `render:camera` option in the scene globals.
			- Location : Uses the camera specified on the `location` plug.
			""",

			"preset:Render Camera" : GafferScene.CameraQuery.CameraMode.RenderCamera,
			"preset:Location" : GafferScene.CameraQuery.CameraMode.Location,

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"nodule:type" : "",

		},

		"location" : {

			"description" :
			"""
			The location within the scene containing a camera to query.
			> Note : If the location does not exist then the query will not be
			> performed and all outputs will be set to their default values with
			> each output `source` plug set to "None" (`0`).
			""",

			"plugValueWidget:type" : "GafferSceneUI.ScenePathPlugValueWidget",
			"scenePathPlugValueWidget:scene" : "scene",
			"nodule:type" : "",
			"scenePathPlugValueWidget:setNames" : IECore.StringVectorData( [ "__cameras" ] ),
			"scenePathPlugValueWidget:setsLabel" : "Show only cameras",

			"layout:visibilityActivator" : "cameraModeIsLocation",

		},

		"queries" : {

			"description" :
			"""
			The camera parameters to be queried - arbitrary numbers of queries may
			be added as children of this plug via the user interface, or via python.
			Each child is a `StringPlug` whose value is the parameter to query.

			> Note : While a query typically returns the value of a parameter,
			> a few special inbuilt queries return values not represented by a
			> parameter but which are instead computed from the camera.
			> - `apertureAspectRatio` : `aperture.x` / `aperture.y`.
			> - `fieldOfView` : The horizontal field of view in degrees, based
			> on `focalLength` and `aperture`.
			> - `frustum` : The screen window at a distance of 1 unit from the camera, taking
			> into account `filmFit`, `resolution`, and `pixelAspectRatio` render overrides
			> on the camera or values from the scene globals.
			""",

			"plugValueWidget:type" : "GafferUI.LayoutPlugValueWidget",
			"layout:section" : "Settings.Queries",

			"layout:customWidget:footer:widgetType" : "GafferSceneUI.CameraQueryUI._CameraQueryFooter",
			"layout:customWidget:footer:index" : -1,

			"nodule:type" : "",

		},

		"queries.*" : {

			"description" :
			"""
			The name of the parameter to query.
			""",

			"layout:label" : "",

			"plugValueWidget:type" : "GafferSceneUI.CameraQueryUI._QueryWidget",

		},

		"out" : {

			"description" :
			"""
			The parent plug of the query outputs. The order of outputs corresponds
			to the order of children of `queries`.
			""",

			"plugValueWidget:type" : "",

			"nodule:type" : "GafferUI::CompoundNodule",
			"noduleLayout:spacing" : 0.4,
			"noduleLayout:customGadget:addButton:gadgetType" : "",

		},

		"out.*" : {

			"description" :
			"""
			The result of the query.
			""",

			"nodule:type" : "GafferUI::CompoundNodule",

		},

		"out.*.source" : {

			"description" :
			"""
			Outputs the source of the value returned by the query.

			- None (`0`) : No source was found. Either the parameter does not exist and has no default value, or the camera does not exist.
			- Camera (`1`) : The camera.
			- Globals (`2`) : An option in the scene globals.
			- Fallback (`3`) : The query did not find a result and fell back to returning the default value of the parameter.
			""",

			"nodule:type" : "",

		},

		"out.*.value" : {

			"description" :
			"""
			Outputs the value returned by the query.
			""",

		},

		"out.*.value..." : {

			"noduleLayout:label" : __getLabel,

		},

	}
)

##########################################################################
# _CameraQueryFooter
##########################################################################

## \todo Replace with PlugCreationWidget. Introduce `ui:scene:acceptsCameraParameters`
# metadata to trigger the creation of menu items for all registered parameters.
class _CameraQueryFooter( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.PlugValueWidget.__init__( self, row, plug )

		with row :

			GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

			self.__menuButton = GafferUI.MenuButton(
				image = "plus.png",
				hasFrame = False,
				menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) )
			)

			GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand": True } )

		plug.node().plugSetSignal().connect(
			Gaffer.WeakMethod( self.__updateQueryMetadata )
		)

	def _updateFromEditable( self ) :

		self.__menuButton.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		node = self.getPlug().node()
		assert( isinstance( node, GafferScene.CameraQuery ) )

		with self.context() :
			existingQueries = { query.getValue() for query in node["queries"] }

		## \todo It would be worthwhile migrating CameraTweaksUI to also use this metadata
		for target in Gaffer.Metadata.targetsWithMetadata( "camera:parameter:*", "defaultValue" ) :
			name = target[17:]
			label = Gaffer.Metadata.value( target, "label" ) or IECore.CamelCase.toSpaced( name )
			category = Gaffer.Metadata.value( target, "layout:section" ) or "Standard"
			value = Gaffer.Metadata.value( target, "defaultValue" )
			valueType = type( value )
			if issubclass( valueType, IECore.Data ) :
				dataType = valueType
			elif valueType is float :
				# Special case as dataTypeFromElementType( float ) returns DoubleData
				dataType = IECore.FloatData
			else :
				dataType = IECore.DataTraits.dataTypeFromElementType( valueType )
			## \todo Support Splineff in PlugAlgo::createPlugFromData()
			if isinstance( value, IECore.Splineff ) :
				plugCreator = functools.partial( Gaffer.ObjectPlug, defaultValue = IECore.NullObject.defaultNullObject() )
			else :
				plugCreator = functools.partial(
					Gaffer.PlugAlgo.createPlugFromData, "value", Gaffer.Plug.Direction.In, Gaffer.Plug.Flags.Default, dataType()
				)

			result.append(
				"/{}/{}".format( category, label ),
				{
					"command" : functools.partial(
						Gaffer.WeakMethod( self.__addQuery ), name, plugCreator
					),
					"active" : name not in existingQueries
				}
			)

		result.append( "/StandardDivider", { "divider" : True } )

		result.append(
			"/Frustum",
			{
				"command" : functools.partial(
					Gaffer.WeakMethod( self.__addQuery ), "frustum", functools.partial( Gaffer.Box2fPlug, defaultValue = imath.Box2f( imath.V2f( 0.0 ) ) )
				),
				"active" : "frustum" not in existingQueries,
				"description" : "The screen window at a distance of 1 unit from the camera.",
			}
		)

		result.append( "/FrustumDivider", { "divider" : True } )

		for label, plugCreator in [
			( "Bool", Gaffer.BoolPlug ),
			( "Float", Gaffer.FloatPlug ),
			( "Int", Gaffer.IntPlug ),
			( "NumericDivider", None ),
			( "String", Gaffer.StringPlug ),
			( "StringDivider", None ),
			( "V2i", Gaffer.V2iPlug ),
			( "V3i", Gaffer.V3iPlug ),
			( "V2f", Gaffer.V2fPlug ),
			( "V3f", Gaffer.V3fPlug ),
			( "VectorDivider", None ),
			( "Color3f", Gaffer.Color3fPlug ),
			( "Color4f", Gaffer.Color4fPlug ),
			( "BoxDivider", None ),
			( "Box2i", functools.partial( Gaffer.Box2iPlug, defaultValue = imath.Box2i( imath.V2i( 0 ) ) ) ),
			( "Box2f", functools.partial( Gaffer.Box2fPlug, defaultValue = imath.Box2f( imath.V2f( 0.0 ) ) ) ),
			( "Box3i", functools.partial( Gaffer.Box3iPlug, defaultValue = imath.Box3i( imath.V3i( 0 ) ) ) ),
			( "Box3f", functools.partial( Gaffer.Box3fPlug, defaultValue = imath.Box3f( imath.V3f( 0.0 ) ) ) ),
			( "ObjectDivider", None ),
			( "Object", functools.partial( Gaffer.ObjectPlug, defaultValue = IECore.NullObject.defaultNullObject() ) ),
			( "ArrayDivider", None ),
			( "Array/Float", Gaffer.FloatVectorDataPlug ),
			( "Array/Int", Gaffer.IntVectorDataPlug ),
			( "Array/StringDivider", None ),
			( "Array/String", Gaffer.StringVectorDataPlug ),
		] :
			if plugCreator is None :
				result.append( f"/Custom/{label}", { "divider": True } )
			else :
				result.append(
					f"/Custom/{label}",
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__addQuery ), "", plugCreator ),
					}
				)

		return result

	def __addQuery( self, name, plugCreator ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :

			node = self.getPlug().node()
			node.addQuery( plugCreator(), name )

	def __updateQueryMetadata( self, plug ) :

		node = plug.node()

		if plug.parent() == node["queries"] :

			Gaffer.Metadata.plugValueChangedSignal( node )(
				node.outPlugFromQuery( plug ),
				"label",
				Gaffer.Metadata.ValueChangedReason.StaticRegistration
			)

##########################################################################
# Delete Plug
##########################################################################

def __plugPopupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	if plug is not None and isinstance( plug.node(), GafferScene.CameraQuery ) and plug.node()["queries"].isAncestorOf( plug ) :

		if len( menuDefinition.items() ) :
			menuDefinition.append( "/DeleteDivider", { "divider" : True } )

		menuDefinition.append( "/Delete", { "command" : functools.partial( __deletePlug, plug ), "active" : not Gaffer.MetadataAlgo.readOnly( plug.node()["queries"] ) } )

def __deletePlug( plug ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.node().removeQuery( plug )

GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu )
