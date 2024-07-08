##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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
import inspect

import imath
import PyOpenColorIO

import IECore

import Gaffer
import GafferUI
import GafferImage
import GafferImageUI

# General OpenColorIOConfigPlug UI metadata

Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "plugValueWidget:type", "GafferUI.LayoutPlugValueWidget" )
Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "layout:section:Variables:collapsed", False )

Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "config", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )
Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "config", "preset:$OCIO", "" )
Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "config", "preset:ACES 1.3 - CG Config", "ocio://cg-config-v1.0.0_aces-v1.3_ocio-v2.1" )
Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "config", "preset:ACES 1.3 - Studio Config", "ocio://studio-config-v1.0.0_aces-v1.3_ocio-v2.1" )
Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "config", "preset:Legacy (Gaffer 1.2)", "${GAFFER_ROOT}/openColorIO/config.ocio" )

Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "config", "presetsPlugValueWidget:allowCustom", True )
Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "config", "presetsPlugValueWidget:customWidgetType", "GafferUI.FileSystemPathPlugValueWidget" )
Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "config", "fileSystemPath:extensions", "ocio" )
Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "config", "path:leaf", True )
Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "config", "path:valid", True )
Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "config", "path:bookmarks", "openColorIOConfig" )

Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "workingSpace", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )
Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "workingSpace", "presetNames", GafferImageUI.OpenColorIOTransformUI.colorSpacePresetNames )
Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "workingSpace", "presetValues", GafferImageUI.OpenColorIOTransformUI.colorSpacePresetValues )
Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "workingSpace", "openColorIO:categories", "working-space" )
Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "workingSpace", "openColorIO:includeRoles", True )

Gaffer.Metadata.registerValue( Gaffer.ScriptNode, "openColorIO.displayTransform", "plugValueWidget:type", "GafferImageUI.OpenColorIOConfigPlugUI.DisplayTransformPlugValueWidget" )

Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "variables", "layout:section", "Variables" )
Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "variables", "plugValueWidget:type", "GafferUI.LayoutPlugValueWidget" )
Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "variables", "layout:customWidget:footer:widgetType", "GafferImageUI.OpenColorIOContextUI._VariablesFooter" )
Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "variables", "layout:customWidget:footer:index", -1 )
Gaffer.Metadata.registerValue( GafferImage.OpenColorIOConfigPlug, "variables.*", "deletable", True )

# Metadata for the ScriptNode's default ConfigPlug

Gaffer.Metadata.registerNode(

	Gaffer.ScriptNode,

	plugs = {

		"openColorIO" : [

			"layout:section", "OpenColorIO",

		],

		"openColorIO.config" : [

			"description",
			"""
			The OpenColorIO config to use.

			> Note : An OpenColorIOContext node can be used to override the config within specific parts
			of the node graph, or to perform wedging across several contexts.
			""",

		],

		"openColorIO.workingSpace" : [

			"description",
			"""
			The color space in which Gaffer performs image processing. ImageReaders will automatically load
			images into this space, and ImageWriters will automatically convert images from this space.
			""",

		],

		"openColorIO.variables" : [

			"description",
			"""
			Variables used to customise the default
			[OpenColorIO context](https://opencolorio.readthedocs.io/en/latest/guides/authoring/overview.html#environment).
			OpenColorIO refers to these variously as "string vars", "context vars" or
			"environment vars".

			> Note : An OpenColorIOContext node can be used to define variables within specific parts
			of the node graph, or to perform wedging across several variable values.
			""",

		],

		"openColorIO.displayTransform" : [

			"label", "UI Display Transform",
			"description",
			"""
			The colour transform used for showing colours in the UI - in swatches and colour pickers etc.
			This is a combination of an OpenColorIO Display and an OpenColorIO View.

			> Note : The Viewer has its own display transform configured in the Viewer itself.
			""",

		],

	}

)

# DisplayTransformPlugValueWidget

class DisplayTransformPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__menuButton = GafferUI.MenuButton( "", menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )
		GafferUI.PlugValueWidget.__init__( self, self.__menuButton, plugs, **kw )

		self.context().changedSignal().connect( Gaffer.WeakMethod( self.__contextChanged ), scoped = True )
		self.__ensureValidValue()

	def _updateFromValues( self, values, exception ) :

		if exception is not None :
			self.__menuButton.setText( "" )
		else :
			assert( len( values ) == 1 )
			# Only show the View name, because the Display name is more of
			# a "set once and forget" affair. The menu shows both for when
			# you need to check.
			self.__menuButton.setText( values[0].partition( "/" )[-1] )

		self.__menuButton.setErrored( exception is not None )

	def _updateFromEditable( self ) :

		self.__menuButton.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		activeViews = Gaffer.Metadata.value( self.getPlug(), "openColorIO:activeViews" ) or "*"
		with self.getContext() :

			try :
				config = GafferImage.OpenColorIOAlgo.currentConfig()
			except :
				result.append( "/Invalid Config", { "active" : False } )
				return result

			currentDisplay, currentView = self.getPlug().getValue().split( "/" )

		# View section

		result.append( "/__ViewDivider__", { "divider" : True, "label" : "View" } )

		for view in config.getViews( currentDisplay ) :
			if not IECore.StringAlgo.matchMultiple( view, activeViews ) :
				continue
			result.append(
				f"/{view}", {
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), currentDisplay, view ),
					"checkBox" : view == currentView
				}
			)

		# Display section

		result.append( "/__DisplayDivider__", { "divider" : True, "label" : "Display" } )

		for display in config.getDisplays() :
			view = currentView if currentView in config.getViews( display ) else config.getDefaultView( display )
			result.append(
				f"/{display}", {
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), display, view ),
					"checkBox" : display == currentDisplay
				}
			)

		return result

	def __setValue( self, display, view, *unused ) :

		GafferUI.View.DisplayTransform.registerDisplayTransform(
			f"{display}/{view}",
			functools.partial( _viewDisplayTransformCreator, display, view )
		)

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().setValue( f"{display}/{view}" )

	def __contextChanged( self, context, key ) :

		if key.startswith( "ocio:" ) :
			# OCIO config may have changed, and the new config might
			# not provide the display transform that we want.
			self.__ensureValidValue()

	def __ensureValidValue( self ) :

		with self.getContext() :
			try :
				config = GafferImage.OpenColorIOAlgo.currentConfig()
			except :
				return
			elements = self.getPlug().getValue().split( "/" )

		if len( elements ) == 2 :
			display, view = elements[0], elements[1]
		else :
			display = config.getDefaultDisplay()
			view = config.getDefaultView( display )

		if display not in config.getDisplays() :
			display = config.getDefaultDisplay()

		if view not in config.getViews( display ) :
			view = config.getDefaultView( display )

		self.__setValue( display, view )

# Connection between default script config and Widget and View display transforms.
# Calling `connect()` from an application startup file is what makes the UI OpenColorIO-aware.

def connect( script ) :

	hadPlug = GafferImage.OpenColorIOConfigPlug.acquireDefaultConfigPlug( script, createIfNecessary = False )
	plug = GafferImage.OpenColorIOConfigPlug.acquireDefaultConfigPlug( script )
	if not hadPlug :
		Gaffer.NodeAlgo.applyUserDefaults( plug )

	script.plugDirtiedSignal().connect( __scriptPlugDirtied, scoped = False )
	__scriptPlugDirtied( plug )

def __displayTransformProcessor( config, context, workingSpace, display, view ) :

	transform = PyOpenColorIO.DisplayViewTransform()
	transform.setSrc( workingSpace )
	transform.setDisplay( display )
	transform.setView( view )

	return config.getProcessor( transform = transform, context = context, direction = PyOpenColorIO.TRANSFORM_DIR_FORWARD )

def _viewDisplayTransformCreator( display, view ) :

	config, context = GafferImage.OpenColorIOAlgo.currentConfigAndContext()
	workingSpace = GafferImage.OpenColorIOAlgo.getWorkingSpace( Gaffer.Context.current() )
	processor = __displayTransformProcessor( config, context, workingSpace, display, view )
	return GafferImageUI.OpenColorIOAlgo.displayTransformToFramebufferShader( processor )

def __widgetDisplayTransform( config, context, workingSpace, display, view ) :

	try :
		processor = __displayTransformProcessor( config, context, workingSpace, display, view ).getDefaultCPUProcessor()
	except Exception as e :
		IECore.msg( IECore.Msg.Level.Error, "OpenColorIO", str( e ) )
		processor = None

	def f( c ) :
		if processor is not None :
			cc = processor.applyRGB( [ c.r, c.g, c.b ] )
			return imath.Color3f( *cc )
		else :
			# Error colour
			return imath.Color3f( 1, 0.33, 0.33 )

	return f

def __scriptPlugDirtied( plug ) :

	if plug.getName() != "openColorIO" :
		return

	with plug.parent().context() :
		try :
			config, context = GafferImage.OpenColorIOAlgo.currentConfigAndContext()
		except :
			return

	for display in config.getDisplays() :
		for view in config.getViews( display ) :
			GafferUI.View.DisplayTransform.registerDisplayTransform(
				f"{display}/{view}",
				functools.partial( _viewDisplayTransformCreator, display, view )
			)

	displayTransform = plug["displayTransform"].getValue()
	if displayTransform :
		display, view = displayTransform.split( "/" )
	else :
		display = config.getDefaultDisplay()
		view = config.getDefaultView( display )

	workingSpace = GafferImage.OpenColorIOAlgo.getWorkingSpace( plug.parent().context() )

	scriptWindow = GafferUI.ScriptWindow.acquire( plug.parent(), createIfNecessary = False )
	if scriptWindow is not None :
		scriptWindow.setDisplayTransform( __widgetDisplayTransform( config, context, workingSpace, display, view ) )
