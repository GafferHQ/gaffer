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

import imath

import IECore
import IECoreScene

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

Gaffer.Metadata.registerNode(

	GafferSceneUI.SceneView,

	"toolbarLayout:customWidget:LeftSpacer:widgetType", "GafferSceneUI.SceneViewUI._Spacer",
	"toolbarLayout:customWidget:LeftSpacer:section", "Top",
	"toolbarLayout:customWidget:LeftSpacer:index", 0,

	"toolbarLayout:customWidget:RightSpacer:widgetType", "GafferSceneUI.SceneViewUI._Spacer",
	"toolbarLayout:customWidget:RightSpacer:section", "Top",
	"toolbarLayout:customWidget:RightSpacer:index", -2,

	"toolbarLayout:customWidget:StateWidget:widgetType", "GafferSceneUI.SceneViewUI._StateWidget",
	"toolbarLayout:customWidget:StateWidget:section", "Top",
	"toolbarLayout:customWidget:StateWidget:index", -1,

	plugs = {

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

		],

		"camera.fieldOfView" : [

			"description",
			"""
			The field of view for the viewport's default perspective camera.
			""",

		],

		"camera.clippingPlanes" : [

			"description",
			"""
			The near and far clipping planes for the viewport's default perspective camera.
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

		],

		"gnomon" : [

			"plugValueWidget:type", "",

		],

	}

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

	def _updateFromPlug( self ) :

		pass

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

		lightDrawingModePlug = self.getPlug()["light"]["drawingMode"]
		for mode in ( "wireframe", "color", "texture" ) :
			m.append(
				"/Lights/" + IECore.CamelCase.toSpaced( mode ),
				{
					"command" : functools.partial( lambda m, _ : lightDrawingModePlug.setValue( m ), mode ),
					"checkBox" : lightDrawingModePlug.getValue() == mode
				}
			)

		m.append( "/Lights/__optionsDivider__", { "divider" : True } )

		lightProjectionPlug = self.getPlug()["light"]["projection"]
		m.append(
			"/Lights/Show Projection",
			{
				"command" : lightProjectionPlug.setValue,
				"checkBox" : lightProjectionPlug.getValue()
			}
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

		m.append( "/__visualiserDivider__", { "divider" : True } )

		visScaleIsOther = True
		visScalePlug = self.getPlug()["visualiserOrnamentScale"]
		for scale in ( 1, 10, 100 ) :
			isSelected = visScalePlug.getValue() == scale
			if isSelected :
				visScaleIsOther = False
			m.append(
				"/Visualiser Scale/%d" % scale,
				{
					"command" : functools.partial( lambda s, _ : visScalePlug.setValue( s ), scale ),
					"checkBox" : isSelected
				}
			)

		m.append( "/Visualiser Scale/__divider__", { "divider" : True } )
		m.append(
			"/Visualiser Scale/Other...",
			{
				"command" : functools.partial(  Gaffer.WeakMethod( self.__popupPlugWidget ), visScalePlug, "Other Scale" ),
				"checkBox" : visScaleIsOther
			}
		)

		return m

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

		def _updateFromPlug( self ) :

			pass

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

	def _updateFromPlug( self ) :

		pass

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
	if derivedTypes :
		return set().union( *[ _leafTypes( t ) for t in derivedTypes ] )
	else :
		return { IECore.RunTimeTyped.typeNameFromTypeId( typeId ) }

class _SelectionMaskPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ), title="Selection Mask" )
		self.__menuButton = GafferUI.MenuButton( menu=menu, image = "selectionMaskOff.png", hasFrame=False )

		GafferUI.PlugValueWidget.__init__( self, self.__menuButton, plug, **kw )

		self._updateFromPlug()

	def hasLabel( self ) :

		return True

	def _updateFromPlug( self ) :

		allTypes = set().union( *[ x[1] for x in self.__menuItems() if x[1] and not x[2] ] )
		currentTypes = set().union( *[ _leafTypes( t ) for t in self.getPlug().getValue() ] )

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

		# Must connect with group 0 so we get called before PlugValueWidget's default handlers
		self.dragEnterSignal().connect( 0, Gaffer.WeakMethod( self.__dragEnter ), scoped = False )
		self.dropSignal().connect( 0, Gaffer.WeakMethod( self.__drop ), scoped = False )

		self._updateFromPlug()

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )

		self.__menuButton.setHighlighted( highlighted )

	def _updateFromPlug( self ) :

		self.__menuButton.setImage(
			"cameraOn.png" if self.getPlug()["lookThroughEnabled"].getValue() else "cameraOff.png"
		)

	def __menuDefinition( self ) :

		m = IECore.MenuDefinition()

		if self.getPlug()["lookThroughEnabled"].getValue() :
			currentLookThrough = self.getPlug()["lookThroughCamera"].getValue()
		else :
			currentLookThrough = None

		m.append(
			"/Default",
			{
				"checkBox" : currentLookThrough is None,
				"command" : functools.partial( Gaffer.WeakMethod( self.__lookThrough ), None )
			}
		)

		m.append(
			"/Render Camera",
			{
				"checkBox" : currentLookThrough is "",
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

	def __lookThrough( self, path, *unused ) :

		self.getPlug()["lookThroughEnabled"].setValue( path is not None )
		self.getPlug()["lookThroughCamera"].setValue( path or "" )

	def __browse( self ) :

		w = GafferSceneUI.ScenePathPlugValueWidget(
			self.getPlug()["lookThroughCamera"],
			path = GafferScene.ScenePath(
				self.getPlug().node()["in"],
				self.getPlug().node().getContext(),
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
					with GafferUI.Frame( borderStyle = GafferUI.Frame.BorderStyle.None, borderWidth = 4 ) :
						layout = GafferUI.PlugLayout( self.getPlug() )
					GafferUI.Spacer( imath.V2i( 0 ), parenting = { "expand" : True } )

			self.ancestor( GafferUI.Window ).addChildWindow( self.__settingsWindow )

			# Force layout to build immediately, so we can then match
			# the window size to it.
			layout.plugValueWidget( self.getPlug()["fieldOfView"], lazy = False )
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
			with self.getContext() :
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

	def _updateFromPlug( self ) :

		pass

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

		return m

##########################################################################
# Context menu
##########################################################################

def __fitClippingPlanes( view, toSelection = False ) :

	viewportGadget = view.viewportGadget()
	sceneGadget = viewportGadget.getPrimaryChild()
	viewportGadget.fitClippingPlanes(
		sceneGadget.bound() if not toSelection else sceneGadget.selectionBound()
	)

def __appendClippingPlaneMenuItems( menuDefinition, prefix, view, parentWidget ) :

	sceneGadget = view.viewportGadget().getPrimaryChild()

	if isinstance( parentWidget, GafferUI.Viewer ) :
		editable = view.viewportGadget().getCameraEditable()
	else :
		editable = not parentWidget.getReadOnly()

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

def __viewContextMenu( viewer, view, menuDefinition ) :

	if not isinstance( view, GafferSceneUI.SceneView ) :
		return False

	__appendClippingPlaneMenuItems( menuDefinition, "/Clipping Planes", view, viewer )

GafferUI.Viewer.viewContextMenuSignal().connect( __viewContextMenu, scoped = False )

def __plugValueWidgetContextMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	node = plug.node()
	if not isinstance( node, GafferSceneUI.SceneView ) :
		return
	if plug != node["camera"]["clippingPlanes"] :
		return

	menuDefinition.append( "/FitDivider", { "divider" : True } )

	__appendClippingPlaneMenuItems( menuDefinition, "", node, plugValueWidget )

GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugValueWidgetContextMenu, scoped = False )

##########################################################################
# _StateWidget
##########################################################################

class _Spacer( GafferUI.Spacer ) :

	def __init__( self, sceneView, **kw ) :

		GafferUI.Spacer.__init__( self, size = imath.V2i( 0 ) )

## \todo This widget is basically the same as the UVView and ImageView ones. Perhaps the
# View base class should provide standard functionality for pausing and state, and we could
# use one standard widget for everything.
class _StateWidget( GafferUI.Widget ) :

	def __init__( self, sceneView, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		GafferUI.Widget.__init__( self, row, **kw )

		with row :

			self.__busyWidget = GafferUI.BusyWidget( size = 20 )
			self.__button = GafferUI.Button( hasFrame = False )

		self.__sceneGadget = sceneView.viewportGadget().getPrimaryChild()

		self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClick ), scoped = False )
		self.__sceneGadget.stateChangedSignal().connect( Gaffer.WeakMethod( self.__stateChanged ), scoped = False )

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
