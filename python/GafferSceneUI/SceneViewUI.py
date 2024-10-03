##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2014, John Haddon. All rights reserved.
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
import datetime
import pathlib

import imath

import IECore
import IECoreScene

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI
import GafferImage

from ._SceneViewInspector import _SceneViewInspector

def __rendererPlugActivator( plug ) :

	if plug.getName() == "name" :
		return True

	# Plug is the parent for some renderer-specific
	# settings. Only show it if has some worthwhile settings
	# and it is for the current renderer.

	if plug.keys() == [ "enabled" ] :
		return False

	return plug.parent()["name"].getValue().lower() == plug.getName().lower()

Gaffer.Metadata.registerNode(

	GafferSceneUI.SceneView,

	"toolbarLayout:customWidget:StateWidget:widgetType", "GafferSceneUI.SceneViewUI._StateWidget",
	"toolbarLayout:customWidget:StateWidget:section", "Top",
	"toolbarLayout:customWidget:StateWidget:index", 0,

	"toolbarLayout:customWidget:EditScopeBalancingSpacer:widgetType", "GafferSceneUI.SceneViewUI._EditScopeBalancingSpacer",
	"toolbarLayout:customWidget:EditScopeBalancingSpacer:section", "Top",
	"toolbarLayout:customWidget:EditScopeBalancingSpacer:index", 1,

	"toolbarLayout:customWidget:CenterLeftSpacer:widgetType", "GafferSceneUI.SceneViewUI._Spacer",
	"toolbarLayout:customWidget:CenterLeftSpacer:section", "Top",
	"toolbarLayout:customWidget:CenterLeftSpacer:index", 1,

	"toolbarLayout:customWidget:CenterRightSpacer:widgetType", "GafferSceneUI.SceneViewUI._Spacer",
	"toolbarLayout:customWidget:CenterRightSpacer:section", "Top",
	"toolbarLayout:customWidget:CenterRightSpacer:index", -2,

	"nodeToolbar:right:type", "GafferUI.StandardNodeToolbar.right",

	"toolbarLayout:customWidget:InspectorTopSpacer:widgetType", "GafferSceneUI.SceneViewUI._InspectorTopSpacer",
	"toolbarLayout:customWidget:InspectorTopSpacer:section", "Right",

	"toolbarLayout:activator:inspectorVisible", lambda node : node["inspector"]["visible"].getValue(),
	"toolbarLayout:customWidget:Inspector:widgetType", "GafferSceneUI.SceneViewUI._SceneViewInspector",
	"toolbarLayout:customWidget:Inspector:section", "Right",
	"toolbarLayout:customWidget:Inspector:visibilityActivator", "inspectorVisible",

	"toolbarLayout:customWidget:InspectorBottomSpacer:widgetType", "GafferSceneUI.SceneViewUI._InspectorBottomSpacer",
	"toolbarLayout:customWidget:InspectorBottomSpacer:section", "Right",

	plugs = {

		"editScope" : [

			"plugValueWidget:type", "GafferUI.EditScopeUI.EditScopePlugValueWidget",
			"toolbarLayout:index", -1,
			"toolbarLayout:width", 225,

		],

		"renderer" : [

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layoutPlugValueWidget:orientation", "horizontal",
			"toolbarLayout:index", 1,
			"toolbarLayout:label", "",
			"toolbarLayout:width", 100,

		],

		"renderer.name" : [

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"layout:label", "",
			"presetNames", lambda plug : IECore.StringVectorData( GafferSceneUI.SceneView.registeredRenderers() ),
			"presetValues", lambda plug : IECore.StringVectorData( GafferSceneUI.SceneView.registeredRenderers() ),

		],

		"renderer.*" : [

			"plugValueWidget:type", "GafferSceneUI.SceneViewUI._RendererSettingsPlugValueWidget",
			"layout:visibilityActivator", __rendererPlugActivator,
			"layout:label", "",

		],

		"drawingMode" : [

			"description",
			"""
			Defines how the scene is drawn in the viewport.
			""",
			"plugValueWidget:type", "GafferSceneUI.SceneViewUI._DrawingModePlugValueWidget",

		],

		"shadingMode" : [

			"description",
			"""
			Defines how the scene is shaded in the viewport.
			""",
			"toolbarLayout:divider", True,
			"plugValueWidget:type", "GafferSceneUI.SceneViewUI._ShadingModePlugValueWidget",

		],

		"minimumExpansionDepth" : [

			"plugValueWidget:type", "GafferSceneUI.SceneViewUI._ExpansionPlugValueWidget",

		],

		"selectionMask" : [

			"description",
			"""
			Defines what types of objects are selectable in the viewport.
			""",
			"plugValueWidget:type", "GafferSceneUI.SceneViewUI._SelectionMaskPlugValueWidget",

			"toolbarLayout:divider", True,

		],

		"camera" : [

			"description",
			"""
			Defines the camera used to view the scene.
			""",

			"plugValueWidget:type", "GafferSceneUI.SceneViewUI._CameraPlugValueWidget",
			"toolbarLayout:divider", True,
			"toolbarLayout:label", "",
			"layout:activator:hidden", lambda plug : False,
			"layout:activator:lookThroughEnabled", lambda plug : plug["lookThroughEnabled"].getValue(),
			"layout:activator:lookThroughDisabled", lambda plug : not plug["lookThroughEnabled"].getValue(),
			"layout:activator:cameraIsFreePerspective", lambda plug : not plug["lookThroughEnabled"].getValue() and plug["freeCamera"].getValue() == "perspective",
			"layout:section:Free Camera:collapsed", False,
			"layout:section:Light Look Through:collapsed", False,

		],

		"camera.freeCamera" : [

			"description",
			"""
			Chooses the default camera to be used when `camera.lookThroughEnabled` is off.
			""",

			"layout:visibilityActivator", "hidden"

		],

		"camera.fieldOfView" : [

			"description",
			"""
			The field of view for the viewport's default perspective camera.
			""",

			"layout:section", "Free Camera",
			"layout:activator", "cameraIsFreePerspective",

		],

		"camera.clippingPlanes" : [

			"description",
			"""
			The near and far clipping planes for the viewport's default perspective camera.
			""",

			"layout:section", "Free Camera",
			"layout:activator", "lookThroughDisabled",

		],

		"camera.lightLookThroughDefaultDistantAperture" : [
			"layout:section", "Light Look Through",
			"layout:activator", "lookThroughEnabled",
			"label", "Default Distant Aperture",
			"description",
			"""
			The orthographic aperture used when converting distant lights
			( which are theoretically infinite in extent ).  May be overridden
			by the visualisation setting on the light.
			""",
		],

		"camera.lightLookThroughDefaultClippingPlanes" : [
			"layout:section", "Light Look Through",
			"layout:activator", "lookThroughEnabled",
			"label", "Default Clipping Planes",
			"description",
			"""
			Clipping planes for cameras implied by lights.  When creating a perspective camera, a near clip
			<= 0 is invalid, and will be replaced with 0.01.  Also, certain lights only start casting
			light at some distance - if near clip is less than this, it will be increased.  May be overridden
			by the visualisation setting on the light.
			""",
		],

		"camera.lookThroughEnabled" : [

			"description",
			"""
			When enabled, locks the view to look through a specific camera in the scene.
			By default, the current render camera is used, but this can be changed using the camera.lookThroughCamera
			setting.
			""",

			"layout:visibilityActivator", "hidden"

		],

		"camera.lookThroughCamera" : [

			"description",
			"""
			Specifies the camera to look through when lookThrough.enabled is on. The default value
			means that the current render camera will be used - the paths to other cameras may be specified
			to choose another camera."
			""",

			"layout:visibilityActivator", "hidden"

		],

		"grid" : [

			"plugValueWidget:type", "GafferSceneUI.SceneViewUI._GridPlugValueWidget",
			"toolbarLayout:divider", True,

		],

		"gnomon" : [

			"plugValueWidget:type", "",

		],

		"inspector" : [

			"plugValueWidget:type", "",

		],

		"fps" : [

			"plugValueWidget:type", "",

		],

		"displayTransform.soloChannel" : [

			# The `RGBAL`` shortcuts conflict with shortcuts used for
			# Tools, so we disable them.
			"view:displayTransform:useShortcuts", False,

		],

	}

)

##########################################################################
# _RendererSettingsPlugValueWidget
##########################################################################

class _RendererSettingsPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		button = GafferUI.Button( image = "tabScrollMenu.png", hasFrame = False )
		GafferUI.PlugValueWidget.__init__( self, button, plug, **kw )

		self.__window = None

		button.clickedSignal().connect( Gaffer.WeakMethod( self.__clicked ) )

	def __clicked( self, button ) :

		if self.__window is None :
			with GafferUI.PopupWindow( IECore.CamelCase.toSpaced( self.getPlug().getName() + "Settings" ) ) as self.__window :
				GafferUI.PlugLayout( self.getPlug(), rootSection = "Settings" )
			self.__window.resizeToFitChild()

		bound = self.bound()
		self.__window.popup(
			center = imath.V2i(
				bound.center().x,
				bound.max().y + self.__window.bound().size().y / 2 + 8,
			),
			parent = self
		)

##########################################################################
# _DrawingModePlugValueWidget
##########################################################################

class _DrawingModePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ), title="Drawing" )
		menuButton = GafferUI.MenuButton( menu=menu, image = "drawingStyles.png", hasFrame=False )

		GafferUI.PlugValueWidget.__init__( self, menuButton, plug, **kw )

	def hasLabel( self ) :

		return True

	def __menuDefinition( self ) :

		m = IECore.MenuDefinition()

		for n in ( "solid", "wireframe", "points" ) :
			plug = self.getPlug()[n]
			m.append(
				"/" + IECore.CamelCase.toSpaced( n ),
				{
					"command" : plug.setValue,
					"checkBox" : plug.getValue(),
				}
			)

		m.append( "/ComponentsDivider", { "divider" : True } )

		includedPurposes = self.getPlug()["includedPurposes"]["value"].getValue()
		includedPurposesEnabled = self.getPlug()["includedPurposes"]["enabled"].getValue()
		allPurposes = [ "default", "render", "proxy", "guide" ]
		for purpose in allPurposes :
			newPurposes = IECore.StringVectorData( [
				p for p in allPurposes
				if
				( p != purpose and p in includedPurposes ) or ( p == purpose and p not in includedPurposes )
			] )
			m.append(
				"/Purposes/{}".format( purpose.capitalize() ),
				{
					"checkBox" : purpose in includedPurposes,
					"active" : includedPurposesEnabled,
					"command" : functools.partial( self.getPlug()["includedPurposes"]["value"].setValue, newPurposes ),
				}
			)
			m.append( "/Purposes/SceneDivider", { "divider" : True } )
			m.append(
				"/Purposes/From Scene",
				{
					"checkBox" : not includedPurposesEnabled,
					"command" : lambda checked : self.getPlug()["includedPurposes"]["enabled"].setValue( not checked ),
				}
			)

		m.append( "/PurposesDivider", { "divider" : True } )

		lightDrawingModePlug = self.getPlug()["light"]["drawingMode"]
		for mode in ( "wireframe", "color", "texture" ) :
			m.append(
				"/Lights/" + IECore.CamelCase.toSpaced( mode ),
				{
					"command" : functools.partial( lambda m, _ : lightDrawingModePlug.setValue( m ), mode ),
					"checkBox" : lightDrawingModePlug.getValue() == mode
				}
			)

		m.append( "/Lights/OptionsDivider", { "divider" : True } )

		self.__appendValuePresetMenu(
			m, self.getPlug()["light"]["frustumScale"],
			"/Lights/Frustum Scale", ( 1, 10, 100 ), "Other Scale"
		)

		for n in ( "useGLLines", "interpolate" ) :
			plug = self.getPlug()["curvesPrimitive"][n]
			m.append(
				"/Curves Primitives/" + IECore.CamelCase.toSpaced( n ),
				{
					"command" : plug.setValue,
					"checkBox" : plug.getValue(),
				}
			)

		useGLPointsPlug = self.getPlug()["pointsPrimitive"]["useGLPoints"]
		m.append(
			"/Points Primitives/Use GL Points",
			{
				"command" : useGLPointsPlug.setValue,
				"checkBox" : useGLPointsPlug.getValue()
			}
		)

		m.append( "/VisualisersDivider", { "divider" : True } )

		frustumPlug = self.getPlug()["visualiser"]["frustum"]
		for mode in ( "off", "whenSelected", "on" ) :
			m.append(
				"/Visualisers/Frustum/" + IECore.CamelCase.toSpaced( mode ),
				{
					"command" : functools.partial( lambda m, _ : frustumPlug.setValue( m ), mode ),
					"checkBox" : frustumPlug.getValue() == mode
				}
			)

		self.__appendValuePresetMenu(
			m, self.getPlug()["visualiser"]["scale"],
			"/Visualisers/Scale", ( 1, 10, 100 ), "Other Scale"
		)

		return m

	def __appendValuePresetMenu( self, menu, plug, title, presets, otherDialogTitle = None  ) :

		if not otherDialogTitle :
			otherDialogTitle = title

		valueIsOther = True
		for preset in presets :
			isSelected = plug.getValue() == preset
			if isSelected :
				valueIsOther = False
			menu.append(
				"%s/%s" % ( title, preset ),
				{
					"command" : functools.partial( lambda s, _ : plug.setValue( s ), preset ),
					"checkBox" : isSelected
				}
			)

		menu.append( "%s/__divider__" % title, { "divider" : True } )

		menu.append(
			"%s/Other..." % title,
			{
				"command" : functools.partial(  Gaffer.WeakMethod( self.__popupPlugWidget ), plug, otherDialogTitle ),
				"checkBox" : valueIsOther
			}
		)

	def __popupPlugWidget( self, plug, title, *unused ) :

		_PlugWidgetDialogue( plug, title ).waitForClose( parentWindow = self.ancestor( GafferUI.Window ) )

class _PlugWidgetDialogue( GafferUI.Dialogue ) :

	def __init__( self, plug, title="", **kw ) :

		self.__initialValue = plug.getValue()

		if not title :
			title = IECore.CamelCase.toSpaced( plug.getName() )

		GafferUI.Dialogue.__init__( self, title, sizeMode=GafferUI.Window.SizeMode.Fixed, **kw )

		self.__plugWidget = GafferUI.PlugValueWidget.create( plug )
		self._setWidget( self.__plugWidget )

		self.__cancelButton = self._addButton( "Cancel" )
		self.__confirmButton = self._addButton( "OK" )

	def waitForClose( self, **kw ) :

		button = self.waitForButton( **kw )
		if button is self.__cancelButton :
			self.__plugWidget.getPlug().setValue( self.__initialValue )
			return False
		else :
			return True

##########################################################################
# _ShadingModePlugValueWidget
##########################################################################

class _ShadingModePlugValueWidget( GafferUI.PlugValueWidget ) :

		def __init__( self, plug, **kw ) :

			menuButton = GafferUI.MenuButton(
				image = "shading.png",
				menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ), title="Shading" ),
				hasFrame = False,
			)

			GafferUI.PlugValueWidget.__init__( self, menuButton, plug, **kw )

		def hasLabel( self ) :

			return True

		def __menuDefinition( self ) :

			m = IECore.MenuDefinition()

			currentName = self.getPlug().getValue()
			for name in [ "" ] + GafferSceneUI.SceneView.registeredShadingModes() :
				m.append(
					"/" + name if name else "Default",
					{
						"checkBox" : name == currentName,
						"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), name if name != currentName else "" ),
					}
				)

				if not name :
					m.append( "/DefaultDivider", { "divider" : True } )

			return m

		def __setValue( self, value, *unused ) :

			self.getPlug().setValue( value )

##########################################################################
# _ExpansionPlugValueWidget
##########################################################################

class _ExpansionPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ), title="Expansion" )
		menuButton = GafferUI.MenuButton( menu=menu, image = "expansion.png", hasFrame=False )

		GafferUI.PlugValueWidget.__init__( self, menuButton, plug, **kw )

	def hasLabel( self ) :

		return True

	def __menuDefinition( self ) :

		expandAll = bool( self.getPlug().getValue() )

		m = IECore.MenuDefinition()
		m.append( "/Expand Selection", { "command" : self.getPlug().node().expandSelection, "active" : not expandAll, "shortCut" : "Down" } )
		m.append( "/Expand Selection Fully", { "command" : functools.partial( self.getPlug().node().expandSelection, depth = 999 ), "active" : not expandAll, "shortCut" : "Shift+Down" } )
		m.append( "/Collapse Selection", { "command" : self.getPlug().node().collapseSelection, "active" : not expandAll, "shortCut" : "Up" } )
		m.append( "/Expand All Divider", { "divider" : True } )
		m.append( "/Expand All", { "checkBox" : expandAll, "command" : Gaffer.WeakMethod( self.__toggleMinimumExpansionDepth ) } )

		return m

	def __toggleMinimumExpansionDepth( self, *unused ) :

		self.getPlug().setValue( 0 if self.getPlug().getValue() else 999 )

##########################################################################
# _SelectionMaskPlugValueWidget
##########################################################################

def _leafTypes( typeId ) :

	if isinstance( typeId, str ) :
		typeId = IECore.RunTimeTyped.typeIdFromTypeName( typeId )

	derivedTypes = IECore.RunTimeTyped.derivedTypeIds( typeId )

	# By "leaf" we really mean "derived enough to appear in the Selection Mask
	# menu". So we must pretend that the private InstancerCapsule subclass of
	# Capsule doesn't exist.
	## \todo No doubt this could be expressed more naturally somehow, perhaps
	# just with a set union of `derivedTypes` and `typesWeUseInTheMenu`.
	instancerCapsuleTypeId = IECore.RunTimeTyped.typeIdFromTypeName( "InstancerCapsule" )
	derivedTypes = [ t for t in derivedTypes if t != instancerCapsuleTypeId ]

	if derivedTypes :
		return set().union( *[ _leafTypes( t ) for t in derivedTypes ] )
	else :
		return { IECore.RunTimeTyped.typeNameFromTypeId( typeId ) }

class _SelectionMaskPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ), title="Selection Mask" )
		self.__menuButton = GafferUI.MenuButton( menu=menu, image = "selectionMaskOff.png", hasFrame=False )

		GafferUI.PlugValueWidget.__init__( self, self.__menuButton, plug, **kw )

	def hasLabel( self ) :

		return True

	def _updateFromValues( self, values, exception ) :

		allTypes = set().union( *[ x[1] for x in self.__menuItems() if x[1] and not x[2] ] )
		currentTypes = set().union( *[ _leafTypes( t ) for t in values[0] ] )

		self.__menuButton.setImage(
			"selectionMaskOff.png" if currentTypes.issuperset( allTypes ) else "selectionMaskOn.png"
		)

	@staticmethod
	def __menuItems() :

		geometryTypes = _leafTypes( IECoreScene.VisibleRenderable.staticTypeId() )

		result = [

			# Label, types, invert

			( "/Cameras", { "Camera" }, False ),
			( "/Lights", { "NullObject" }, False ),
			( "/Geometry/All", geometryTypes, False ),
			( "/Geometry/None", geometryTypes, True ),
			( "/Geometry/Divider", None, None ),
			( "/Geometry/Meshes", { "MeshPrimitive" }, False ),
			( "/Geometry/Curves", { "CurvesPrimitive" }, False ),
			( "/Geometry/Points", { "PointsPrimitive" }, False ),
			( "/Geometry/Volumes", { "IECoreVDB::VDBObject" }, False ),
			( "/Geometry/Capsules", { "GafferScene::Capsule" }, False ),
			( "/Geometry/Procedurals", { "ExternalProcedural" }, False ),
			( "/Other/Coordinate Systems", { "CoordinateSystem" }, False ),
			( "/Other/Clipping Planes", { "ClippingPlane" }, False ),

		]

		allTypes = set().union( *[ x[1] for x in result if x[1] and not x[2] ] )
		result = [
			( "/All", allTypes, False ),
			( "/None", allTypes, True ),
			( "/AllDivider", None, None ),
		] + result

		return result

	def __menuDefinition( self ) :

		currentTypes = set().union( *[ _leafTypes( t ) for t in self.getPlug().getValue() ] )
		defaultTypes = set().union( *[ _leafTypes( t ) for t in self.getPlug().defaultValue() ] )

		result = IECore.MenuDefinition()
		for label, types, invert in self.__menuItems() :

			if types is None :
				result.append( label, { "divider" : True } )
			else :
				if invert :
					checked = not currentTypes.intersection( types )
					newTypes = currentTypes - types
				else :
					checked = currentTypes.issuperset( types )
					newTypes = currentTypes | types if not checked else currentTypes - types

				if newTypes == defaultTypes :
					# We generate `newTypes` using leaf typeIds, because it makes
					# addition and removal easier. But when `newTypes` is equivalent
					# to the default value (which uses base types), we want to collapse
					# them back to the default value. This results in a call to
					# `SceneGadget.setSelectionMask( nullptr )`, which puts us on the
					# fast path where we don't use a mask at all.
					newTypes = self.getPlug().defaultValue()

				result.append(
					label,
					{
						"command" : functools.partial(
							self.getPlug().setValue,
							IECore.StringVectorData( newTypes )
						),
						"checkBox" : checked
					}
				)

		return result

##########################################################################
# _CameraPlugValueWidget
##########################################################################

class _CameraPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__menuButton = GafferUI.MenuButton(
			menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ), title="Camera" ),
			hasFrame = False,
		)

		GafferUI.PlugValueWidget.__init__( self, self.__menuButton, plug, **kw )

		self.__settingsWindow = None

		# Must connect at front so we get called before PlugValueWidget's default handlers
		self.dragEnterSignal().connectFront( Gaffer.WeakMethod( self.__dragEnter ) )
		self.dropSignal().connectFront( Gaffer.WeakMethod( self.__drop ) )

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )

		self.__menuButton.setHighlighted( highlighted )

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		return [ p["lookThroughEnabled"].getValue() for p in plugs ]

	def _updateFromValues( self, values, exception ) :

		self.__menuButton.setImage(
			"cameraOn.png" if all( values ) else "cameraOff.png"
		)

	def __menuDefinition( self ) :

		m = IECore.MenuDefinition()

		if self.getPlug()["lookThroughEnabled"].getValue() :
			currentFree = None
			currentLookThrough = self.getPlug()["lookThroughCamera"].getValue()
		else :
			currentFree = self.getPlug()["freeCamera"].getValue()
			currentLookThrough = None

		for freeCamera in [
			"perspective",
			"top",
			"front",
			"side"
		] :

			m.append(
				"/" + freeCamera.title(),
				{
					"checkBox" : freeCamera == currentFree,
					"command" : functools.partial( Gaffer.WeakMethod( self.__free ), freeCamera )
				}
			)

		m.append( "/FreeCameraDivider", { "divider" : True } )

		m.append(
			"/Render Camera",
			{
				"checkBox" : currentLookThrough == "",
				"command" : functools.partial( Gaffer.WeakMethod( self.__lookThrough ), "" )
			}
		)

		for setName in ( "__cameras", "__lights" ) :
			m.append(
				"/{}".format( setName[2:-1].title() ),
				{
					"subMenu" : functools.partial( Gaffer.WeakMethod( self.__setMenu ), setName, currentLookThrough ),
				}
			)

		m.append( "/BrowseDivider", { "divider" : True } )

		m.append(
			"/Browse...",
			{
				"command" : Gaffer.WeakMethod( self.__browse ),
			}
		)

		m.append(
			"/SettingsDivider",
			{
				"divider" : True,
			}
		)

		m.append(
			"/Settings...",
			{
				"command" : Gaffer.WeakMethod( self.__showSettings ),
			}
		)

		return m

	def __free( self, freeCamera, *unused ) :

		self.getPlug()["lookThroughEnabled"].setValue( False )
		self.getPlug()["freeCamera"].setValue( freeCamera )

	def __lookThrough( self, path, *unused ) :

		self.getPlug()["lookThroughEnabled"].setValue( True )
		self.getPlug()["lookThroughCamera"].setValue( path )

	def __browse( self ) :

		w = GafferSceneUI.ScenePathPlugValueWidget(
			self.getPlug()["lookThroughCamera"],
			path = GafferScene.ScenePath(
				self.getPlug().node()["in"],
				self.getPlug().node().context(),
				"/",
				filter = self.__pathFilter()
			),
		)
		## \todo We're making a ScenePathPlugValueWidget just
		# to get its dialogue, because it customises it for
		# browsing scenes. Perhaps we should expose this
		# functionality somewhere more officially.
		dialogue = w._pathChooserDialogue()

		path = dialogue.waitForPath( parentWindow = self.ancestor( GafferUI.Window ) )
		if path is not None :
			self.__lookThrough( str( path ) )

	def __showSettings( self, menu ) :

		if self.__settingsWindow is None :

			self.__settingsWindow = GafferUI.Window( title = "Camera Settings" )
			with self.__settingsWindow :
				with GafferUI.ListContainer() :
					with GafferUI.Frame( borderStyle = GafferUI.Frame.BorderStyle.None_, borderWidth = 4 ) :
						layout = GafferUI.PlugLayout( self.getPlug() )
					GafferUI.Spacer( imath.V2i( 0 ), parenting = { "expand" : True } )

			self.ancestor( GafferUI.Window ).addChildWindow( self.__settingsWindow )
			self.__settingsWindow.resizeToFitChild()

		self.__settingsWindow.setVisible( True )

	@staticmethod
	def __pathFilter() :

		# First make a filter that strips the scene down to
		# only things it is valid to look through - the union
		# of lights and cameras.

		validFilter = GafferScene.UnionFilter()

		# Must parent this filter to validFilter so it remains alive
		# after returning from this method.
		validFilter["__camerasFilter"] = GafferScene.SetFilter()
		validFilter["__camerasFilter"]["setExpression"].setValue( "__cameras" )

		validFilter["__lightsFilter"] = GafferScene.SetFilter()
		validFilter["__lightsFilter"]["setExpression"].setValue( "__lights" )

		validFilter["in"][0].setInput( validFilter["__camerasFilter"]["out"] )
		validFilter["in"][1].setInput( validFilter["__lightsFilter"]["out"] )

		validPathFilter = GafferScene.SceneFilterPathFilter( validFilter )
		validPathFilter.userData()["UI"] = { "visible" : False }

		# Now intersect that with a filter to show only cameras.
		# By turning this second filter on and off, we can give the
		# user a "Show Lights" toggle.

		camerasPathFilter = GafferScene.SceneFilterPathFilter( validFilter["__camerasFilter"] )
		camerasPathFilter.userData()["UI"] = { "label" : "Show Lights", "invertEnabled" : True }

		return Gaffer.CompoundPathFilter( [ validPathFilter, camerasPathFilter ] )

	def __dragEnter( self, widget, event ) :

		if not isinstance( event.data, IECore.StringVectorData ) :
			return False

		if len( event.data ) != 1 :
			return False

		self.setHighlighted( True )
		return True

	def __drop( self, widget, event ) :

		self.setHighlighted( False )
		self.__lookThrough( event.data[0] )
		return True

	def __setMenu( self, setName, currentLookThrough ) :

		m = IECore.MenuDefinition()

		try :
			with self.context() :
				set = self.getPlug().node()["in"].set( setName )
		except :
			return m

		for abbreviatedPath, path in self.__abbreviatedPaths( set.value ) :
			m.append(
				abbreviatedPath,
				{
					"checkBox" : currentLookThrough == path,
					"command" : functools.partial( Gaffer.WeakMethod( self.__lookThrough ), path )
				}
			)

		return m

	## \todo Would this be useful as PathMatcherAlgo
	# somewhere (implemented in C++ using iterators)?
	@staticmethod
	def __abbreviatedPaths( pathMatcher ) :

		class Node( dict ) :
			fullPath = None
			def __missing__( self, key ) :
				n = Node()
				self[key] = n
				return n

		# Build tree of dicts equivalent to the
		# PathMatcher.
		root = Node()
		for path in pathMatcher.paths() :
			node = root
			for name in path[1:].split( "/" ) :
				node = node[name]
			node.fullPath = path

		# Walk the tree, building the abbreviated
		# paths. We abbreviate by omitting the names
		# of nodes which have no siblings.
		result = []
		def walk( node, abbreviatedPath ) :

			for key in node.keys() :
				abbreviatedChildPath = abbreviatedPath
				if len( node ) > 1 or node[key].fullPath :
					abbreviatedChildPath += "/" + key
				walk( node[key], abbreviatedChildPath )

			if node.fullPath :
				result.append( ( abbreviatedPath, node.fullPath ) )

		walk( root, "" )

		return sorted( result )

##########################################################################
# _GridPlugValueWidget
##########################################################################

class _GridPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ), title="Gadgets" )
		menuButton = GafferUI.MenuButton( menu=menu, image = "grid.png", hasFrame=False )

		GafferUI.PlugValueWidget.__init__( self, menuButton, plug, **kw )

	def hasLabel( self ) :

		return True

	def __menuDefinition( self ) :

		m = IECore.MenuDefinition()
		m.append(
			"/Show Grid",
			{
				"checkBox" : self.getPlug()["visible"].getValue(),
				"command" : self.getPlug()["visible"].setValue,
			}
		)

		m.append(
			"/Show Gnomon",
			{
				"checkBox" : self.getPlug().node()["gnomon"]["visible"].getValue(),
				"command" : self.getPlug().node()["gnomon"]["visible"].setValue,
			}
		)

		m.append(
			"/Show Inspector",
			{
				"checkBox" : self.getPlug().node()["inspector"]["visible"].getValue(),
				"command" : self.getPlug().node()["inspector"]["visible"].setValue,
				"shortCut" : "I"
			}
		)

		m.append(
			"/Show FPS",
			{
				"checkBox" : self.getPlug().node()["fps"]["visible"].getValue(),
				"command" : self.getPlug().node()["fps"]["visible"].setValue,
			}
		)

		return m

##########################################################################
# Context menu
##########################################################################

def __fitClippingPlanes( view, toSelection = False ) :

	viewportGadget = view.viewportGadget()
	sceneGadget = viewportGadget.getPrimaryChild()
	viewportGadget.fitClippingPlanes( sceneGadget.bound( toSelection ) )

def __appendClippingPlaneMenuItems( menuDefinition, prefix, view, parentWidget ) :

	sceneGadget = view.viewportGadget().getPrimaryChild()

	if isinstance( parentWidget, GafferUI.Viewer ) :
		editable = view.viewportGadget().getCameraEditable()
	else :
		editable = True

	menuDefinition.append(
		prefix + "/Fit To Selection",
		{
			"active" : editable and not sceneGadget.getSelection().isEmpty(),
			"command" : functools.partial( __fitClippingPlanes, view, toSelection = True ),
			"shortCut" : "Ctrl+K" if isinstance( parentWidget, GafferUI.Viewer ) else "",
		}
	)

	menuDefinition.append(
		prefix + "/Fit To Scene",
		{
			"active" : editable,
			"command" : functools.partial( __fitClippingPlanes, view ),
		}
	)

	if isinstance( parentWidget, GafferUI.Viewer ) :

		# No need to add this one when parentWidget is a PlugValueWidget,
		# because there's already a menu item for that.

		menuDefinition.append(
			prefix + "/Default",
			{
				"active" : editable,
				"command" : view["camera"]["clippingPlanes"].setToDefault,
			}
		)

def __snapshotDescription( view ) :

	sceneGadget = view.viewportGadget().getPrimaryChild()
	if sceneGadget.getRenderer() == "OpenGL" :
		return "Viewport snapshots are only available for rendered (non-OpenGL) previews."

	return "Snapshot viewport and send to catalogue."

def __snapshotToCatalogue( catalogue, view ) :

	timeStamp = str( datetime.datetime.now() )

	scriptRoot = view["in"].getInput().ancestor( Gaffer.ScriptNode )

	fileName = pathlib.Path(
		scriptRoot.context().substitute( catalogue["directory"].getValue() )
	) / ( f"viewerSnapshot-{ timeStamp.replace( ':', '-' ).replace(' ', '_'  ) }.exr" )

	resolutionGate = imath.Box3f()
	if isinstance( view, GafferSceneUI.SceneView ) :
		resolutionGate = view.resolutionGate()

	metadata = IECore.CompoundData(
		{
			"gaffer:sourceScene" : view["in"].getInput().relativeName( scriptRoot ),
			"gaffer:context:frame" : view.context().getFrame()
		}
	)

	sceneGadget = view.viewportGadget().getPrimaryChild()
	sceneGadget.snapshotToFile( fileName, resolutionGate, metadata )

	image = GafferImage.Catalogue.Image( "Snapshot1", Gaffer.Plug.Direction.In, Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
	image["fileName"].setValue( fileName )

	image["description"].setValue(
		"Snapshot of {} at frame {} taken at {}".format(
			metadata["gaffer:sourceScene"],
			metadata["gaffer:context:frame"], timeStamp[:-6]  # Remove trailing microseconds
		)
	)

	catalogue["images"].source().addChild( image )
	catalogue["imageIndex"].source().setValue( len( catalogue["images"].source().children() ) - 1 )

def __snapshotCataloguesSubMenu( view, scriptNode ) :

	menuDefinition = IECore.MenuDefinition()

	catalogueList = list( GafferImage.Catalogue.RecursiveRange( scriptNode ) )

	if len( catalogueList ) == 0 :
		menuDefinition.append(
			"/No Catalogues Available",
			{
				"active" : False,
			}
		)

	else :
		commonDescription = __snapshotDescription( view )
		commonActive = view["renderer"]["name"].getValue() != "OpenGL"

		for c in catalogueList :

			cName = c["name"].getValue()
			nName = c["imageIndex"].source().node().relativeName( scriptNode )

			snapshotActive = (
				commonActive and
				not Gaffer.MetadataAlgo.readOnly( c["images"].source() ) and
				not Gaffer.MetadataAlgo.readOnly( c["imageIndex"].source() )
			)

			snapshotDescription = commonDescription
			if Gaffer.MetadataAlgo.readOnly( c["images"].source() ) :
				snapshotDescription = "\"images\" plug is read-only"
			if Gaffer.MetadataAlgo.readOnly( c["imageIndex"].source() ) :
				snapshotDescription = "\"imageIndex\" plug is read-only"

			menuDefinition.append(
				"/" + ( nName + ( " ({})".format( cName ) if cName else "" ) ),
				{
					"active" : snapshotActive,
					"command" : functools.partial( __snapshotToCatalogue, c, view ),
					"description" : snapshotDescription
				}
			)

	return menuDefinition


def __viewContextMenu( viewer, view, menuDefinition ) :

	if not isinstance( view, GafferSceneUI.SceneView ) :
		return False

	__appendClippingPlaneMenuItems( menuDefinition, "/Clipping Planes", view, viewer )

	scriptNode = view["in"].getInput().ancestor( Gaffer.ScriptNode )

	menuDefinition.append(
		"/Snapshot to Catalogue",
		{
			"subMenu" : functools.partial(
				__snapshotCataloguesSubMenu,
				view,
				scriptNode
			)
		}
	)


GafferUI.Viewer.viewContextMenuSignal().connect( __viewContextMenu )

def __plugValueWidgetContextMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	node = plug.node()
	if not isinstance( node, GafferSceneUI.SceneView ) :
		return
	if plug != node["camera"]["clippingPlanes"] :
		return

	menuDefinition.append( "/FitDivider", { "divider" : True } )

	__appendClippingPlaneMenuItems( menuDefinition, "", node, plugValueWidget )

GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugValueWidgetContextMenu )

##########################################################################
# _Spacers
##########################################################################

class _EditScopeBalancingSpacer( GafferUI.Spacer ) :

	def __init__( self, sceneView, **kw ) :

		# EditScope width - pause button - spacer - spinner - renderer
		width = 200 - 25 - 4 - 20 - 100

		GafferUI.Spacer.__init__(
			self,
			imath.V2i( 0 ), # Minimum
			preferredSize = imath.V2i( width, 1 ),
			maximumSize = imath.V2i( width, 1 )
		)

class _Spacer( GafferUI.Spacer ) :

	def __init__( self, sceneView, **kw ) :

		GafferUI.Spacer.__init__( self, imath.V2i( 0 ) )

class _InspectorTopSpacer( GafferUI.Spacer ) :

	def __init__( self, sceneView, **kw ) :

		GafferUI.Spacer.__init__( self, imath.V2i( 1, 26 ) )

class _InspectorBottomSpacer( GafferUI.Spacer ) :

	def __init__( self, sceneView, **kw ) :

		GafferUI.Spacer.__init__(
			self,
			imath.V2i( 0 ), # Minimum
			preferredSize = imath.V2i( 1, 30 )
		)

##########################################################################
# _StateWidget
##########################################################################

## \todo This widget is basically the same as the UVView and ImageView ones. Perhaps the
# View base class should provide standard functionality for pausing and state, and we could
# use one standard widget for everything.
class _StateWidget( GafferUI.Widget ) :

	def __init__( self, sceneView, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		GafferUI.Widget.__init__( self, row, **kw )

		with row :

			self.__button = GafferUI.Button( hasFrame = False )
			self.__busyWidget = GafferUI.BusyWidget( size = 20 )

		self.__sceneGadget = sceneView.viewportGadget().getPrimaryChild()

		self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClick ) )
		self.__sceneGadget.stateChangedSignal().connect( Gaffer.WeakMethod( self.__stateChanged ) )

		self.__update()

	def __stateChanged( self, sceneGadget ) :

		self.__update()

	def __buttonClick( self, button ) :

		self.__sceneGadget.setPaused( not self.__sceneGadget.getPaused() )
		self.__update()

	def __update( self ) :

		paused = self.__sceneGadget.getPaused()
		self.__button.setImage( "viewPause.png" if not paused else "viewPaused.png" )
		self.__busyWidget.setBusy( self.__sceneGadget.state() == self.__sceneGadget.State.Running )
		self.__button.setToolTip( "Viewer updates suspended, click to resume" if paused else "Click to suspend viewer updates [esc]" )
