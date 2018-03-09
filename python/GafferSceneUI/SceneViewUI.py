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

		"lookThrough" : [

			"plugValueWidget:type", "GafferSceneUI.SceneViewUI._LookThroughPlugValueWidget",
			"toolbarLayout:divider", True,
			"toolbarLayout:label", "",

		],

		"lookThrough.enabled" : [

			"description",
			"""
			When enabled, locks the view to look through a specific camera in the scene.
			By default, the current render camera is used, but this can be changed using the lookThrough.camera
			setting.
			""",
		],

		"lookThrough.camera" : [

			"description",
			"""
			Specifies the camera to look through when lookThrough.enabled is on. The default value
			means that the current render camera will be used - the paths to other cameras may be specified
			to choose another camera."
			""",
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
# _LookThroughPlugValueWidget
##########################################################################

class _LookThroughPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		menuButton = GafferUI.MenuButton(
			image = "camera.png",
			menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ), title="Camera" ),
			hasFrame = False,
		)

		GafferUI.PlugValueWidget.__init__( self, menuButton, plug, **kw )

	def _updateFromPlug( self ) :

		pass

	def __menuDefinition( self ) :

		m = IECore.MenuDefinition()

		if self.getPlug()["enabled"].getValue() :
			currentLookThrough = self.getPlug()["camera"].getValue()
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
			for path in sorted( sets[setName].value.paths() ) :
				m.append(
					"/{}{}".format( setName[2:-1].title(), path ),
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

		return m

	def __lookThrough( self, path, *unused ) :

		self.getPlug()["enabled"].setValue( path is not None )
		self.getPlug()["camera"].setValue( path or "" )

	def __browse( self ) :

		w = GafferSceneUI.ScenePathPlugValueWidget(
			self.getPlug()["camera"],
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
