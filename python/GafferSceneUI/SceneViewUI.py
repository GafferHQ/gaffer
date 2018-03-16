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

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

Gaffer.Metadata.registerNode(

	GafferSceneUI.SceneView,

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
			plug = self.getPlug()[n]["enabled"]
			m.append(
				"/" + IECore.CamelCase.toSpaced( n ),
				{
					"command" : plug.setValue,
					"checkBox" : plug.getValue(),
				}
			)

		m.append( "/ComponentsDivider", { "divider" : True } )

		for n in ( "useGLLines", "interpolate" ) :
			plug = self.getPlug()["curves"][n]["enabled"]
			m.append(
				"/Curves/" + IECore.CamelCase.toSpaced( n ),
				{
					"command" : plug.setValue,
					"checkBox" : plug.getValue(),
				}
			)

		return m

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
		m.append( "/Expand Selection Fully", { "command" : IECore.curry( self.getPlug().node().expandSelection, depth = 999 ), "active" : not expandAll, "shortCut" : "Shift+Down" } )
		m.append( "/Collapse Selection", { "command" : self.getPlug().node().collapseSelection, "active" : not expandAll, "shortCut" : "Up" } )
		m.append( "/Expand All Divider", { "divider" : True } )
		m.append( "/Expand All", { "checkBox" : expandAll, "command" : Gaffer.WeakMethod( self.__toggleMinimumExpansionDepth ) } )

		return m

	def __toggleMinimumExpansionDepth( self, *unused ) :

		self.getPlug().setValue( 0 if self.getPlug().getValue() else 999 )

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
		self.__dragEnterConnection = self.dragEnterSignal().connect( 0, Gaffer.WeakMethod( self.__dragEnter ) )
		self.__dropConnection = self.dropSignal().connect( 0, Gaffer.WeakMethod( self.__drop ) )

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

		sets = {}
		with IECore.IgnoredExceptions( Exception ) :
			with self.getContext() :
				sets = GafferScene.SceneAlgo.sets( self.getPlug().node()["in"], ( "__cameras", "__lights" ) )

		for setName in sorted( sets.keys() ) :
			for abbreviatedPath, path in self.__abbreviatedPaths( sets[setName].value ) :
				m.append(
					"/{}{}".format( setName[2:-1].title(), abbreviatedPath ),
					{
						"checkBox" : currentLookThrough == path,
						"command" : functools.partial( Gaffer.WeakMethod( self.__lookThrough ), path )
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

		sets = {}
		with IECore.IgnoredExceptions( Exception ) :
			with self.getContext() :
				sets = GafferScene.SceneAlgo.sets( self.getPlug().node()["in"], ( "__cameras", "__lights" ) )

		if not any(
			s.value.match( event.data[0] ) & IECore.PathMatcher.Result.ExactMatch
			for s in sets.values()
		) :
			return False

		self.setHighlighted( True )
		return True

	def __drop( self, widget, event ) :

		self.setHighlighted( False )
		self.__lookThrough( event.data[0] )
		return True

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
