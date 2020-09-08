##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import os
import time
import imath

import six

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

from Qt import QtGui

class screengrab( Gaffer.Application ) :

	def __init__( self ) :

		Gaffer.Application.__init__( self, "A tool to generate documentation screengrabs." )

		self.parameters().addParameters(

			[
				IECore.FileNameParameter(
					name = "script",
					description = "The gfr script to load",
					defaultValue = "",
					extensions = "gfr",
					allowEmptyString = True,
					check = IECore.FileNameParameter.CheckType.MustExist,
				),

				IECore.FileNameParameter(
					name = "image",
					description = "Where to save the resulting image",
					defaultValue = "",
					extensions = "png",
					allowEmptyString = True,
				),

				IECore.StringVectorParameter(
					name = "selection",
					description = "A list of nodes to select.",
					defaultValue = IECore.StringVectorData(),
				),

				IECore.StringParameter(
					name = "editor",
					description = "The name of an editor to screengrab. If not specified, the whole window will be grabbed.",
					defaultValue = "",
				),

				IECore.BoolParameter(
					name = "panel",
					description = "Whether to the panel surrounding an editor, or just the editor contents itself.",
					defaultValue = False,
				),

				IECore.CompoundParameter(
					name = "nodeEditor",
					description = "Parameters that configure NodeEditors.",
					members = [
						IECore.StringVectorParameter(
							name = "reveal",
							description = "The names of plugs to reveal in the NodeEditor.",
							defaultValue = IECore.StringVectorData(),
						),
						IECore.StringParameter(
							name = "grab",
							description = "The name of a plug to grab from the NodeEditor.",
							defaultValue = "",
						),
					],
				),

				IECore.CompoundParameter(
					name = "pythonEditor",
					description = "Parameters that configure PythonEditors.",
					members = [
						IECore.StringParameter(
							name = "execute",
							description = "Some python code to execute in the editor.",
							defaultValue = "",
						),
					]
				),

				IECore.CompoundParameter(
					name = "viewer",
					description = "Parameters that configure Viewers.",
					members = [
						IECore.IntParameter(
							name = "minimumExpansionDepth",
							description = "The minimum expansion depth in the viewer.",
							defaultValue = 0,
							minValue = 0,
						),
						IECore.StringVectorParameter(
							name = "framedObjects",
							description = "The names of objects to frame in the Viewer.",
							defaultValue = IECore.StringVectorData(),
						),
						IECore.V3fParameter(
							name = "viewDirection",
							description = "The direction to view the framed objects in.",
							defaultValue = imath.V3f( -0.64, -0.422, -0.64 ),
						),
					]
				),

				IECore.CompoundParameter(
					name = "graphEditor",
					description = "Parameters that configure GraphEditors.",
					members = [
						IECore.StringVectorParameter(
							name = "frame",
							description = "The names of nodes to frame in the GraphEditor.",
							defaultValue = IECore.StringVectorData(),
						),
					],
				),

				IECore.CompoundParameter(
					name = "scene",
					description = "Parameters that configure the scene.",
					members = [
						IECore.StringVectorParameter(
							name = "expandedPaths",
							description = "A list of locations to expand in the Viewer and HierarchyView.",
							defaultValue = IECore.StringVectorData(),
						),
						IECore.StringVectorParameter(
							name = "fullyExpandedPaths",
							description = "A list of locations to expand fully in the Viewer and HierarchyView.",
							defaultValue = IECore.StringVectorData(),
						),
						IECore.StringVectorParameter(
							name = "selectedPaths",
							description = "A list of locations to select in the Viewer and HierarchyView.",
							defaultValue = IECore.StringVectorData(),
						),
					]
				),

				IECore.StringParameter(
					name = "command",
					description = "Command to execute after session is launched. A 'script' variable provides access to the root ScriptNode.",
					defaultValue = "",
				),

				IECore.StringParameter(
					name = "commandFile",
					description = "File containing sequence of commands to execute after session is launched.",
					defaultValue = "",
				),

				IECore.FloatParameter(
					name = "delay",
					description = "A delay between setting up the script and grabbing the image.",
					defaultValue = 0,
				),

			]

		)

		self.parameters().userData()["parser"] = IECore.CompoundObject( {
			"flagless" : IECore.StringVectorData( [ "script" ] )
		} )

	def setGrabWidget( self, widget ) :

		self.__grabWidget = widget

	def getGrabWidget( self ) :

		return self.__grabWidget

	def _run( self, args ) :

		# Run the gui startup files so the images we grab are representative
		# of the layouts and configuration of the gui app.
		self._executeStartupFiles( "gui" )

		GafferUI.ScriptWindow.connect( self.root() )

		# Load the specified gfr file.
		script = Gaffer.ScriptNode()
		if args["script"].value :
			script["fileName"].setValue( os.path.abspath( args["script"].value ) )
			script.load()
		self.root()["scripts"].addChild( script )

		# Choose the widget we'll grab by default. This can be overridden
		# by the command files below by calling `application.setGrabWidget()`.

		scriptWindow = GafferUI.ScriptWindow.acquire( script )
		self.setGrabWidget( scriptWindow )

		# Execute any commands we've been asked to, exposing the application
		# and script as variables.

		GafferUI.EventLoop.waitForIdle()

		d = {
			"application" 	: self,
			"script"		: script,
		}

		if args["command"].value :
			exec( args["command"].value, d, d )
		if args["commandFile"].value :
			commandFile = args["commandFile"].value
			with open( commandFile ) as f :
				six.exec_( compile( f.read(), commandFile, "exec" ), d, d )

		# Select any nodes we've been asked to.
		for name in args["selection"] :
			script.selection().add( script.descendant( name ) )

		# Override the default grab widget if requested by
		# the editor command line flag.

		if args["editor"].value :

			editor = args["editor"].value
			if "." not in editor :
				editor = "GafferUI." + editor
			editorPartition = editor.rpartition( "." )
			editor = getattr( __import__( editorPartition[0] ), editorPartition[2] )

			editors = scriptWindow.getLayout().editors( editor )
			if not editors :
				IECore.msg( IECore.Msg.Level.Error, "screengrab", "Unable to find an editor of type \"%s\"" % editor )
				return 1

			if args["panel"].value :
				self.setGrabWidget( editors[0].parent() )
			else :
				self.setGrabWidget( editors[0] )

			editors[0].reveal()

		# Set up some default framing for the node graphs.

		GafferUI.EventLoop.waitForIdle()

		for graphEditor in scriptWindow.getLayout().editors( GafferUI.GraphEditor ) :
			if args["graphEditor"]["frame"] :
				graphEditor.frame( [ script.descendant( n ) for n in args["graphEditor"]["frame"] ] )
			else :
				graphEditor.frame( script.children( Gaffer.Node ) )

		# Set up the NodeEditors as requested.

		for nodeEditor in scriptWindow.getLayout().editors( GafferUI.NodeEditor ) :

			for name in args["nodeEditor"]["reveal"] :
				GafferUI.PlugValueWidget.acquire( script.descendant( name ) )

			if args["nodeEditor"]["grab"].value :
				grabWidget = GafferUI.PlugWidget.acquire( script.descendant( args["nodeEditor"]["grab"].value ) )
				if not grabWidget :
					grabWidget = GafferUI.PlugValueWidget.acquire( script.descendant( args["nodeEditor"]["grab"].value ) )
				self.setGrabWidget( grabWidget )

		# Set up the PythonEditors as requested.

		for pythonEditor in scriptWindow.getLayout().editors( GafferUI.PythonEditor ) :

			if args["pythonEditor"]["execute"].value :
				pythonEditor.inputWidget().setText( args["pythonEditor"]["execute"].value )
				pythonEditor.inputWidget()._qtWidget().selectAll()
				pythonEditor.execute()

		# Set up the Viewers as requested.

		pathsToFrame = IECore.PathMatcher( list( args["viewer"]["framedObjects"] ) )
		for viewer in scriptWindow.getLayout().editors( GafferUI.Viewer ) :
			if isinstance( viewer.view(), GafferSceneUI.SceneView ) :
				viewer.view()["minimumExpansionDepth"].setValue( args["viewer"]["minimumExpansionDepth"].value )
				if args["viewer"]["framedObjects"] :
					viewer.view().frame( pathsToFrame, args["viewer"]["viewDirection"].value.normalized() )

		del viewer

		# Set up the scene expansion and selection.

		GafferSceneUI.ContextAlgo.clearExpansion( script.context() )

		pathsToExpand = IECore.PathMatcher( list( args["scene"]["fullyExpandedPaths"] ) + list( args["scene"]["expandedPaths"] ) )
		GafferSceneUI.ContextAlgo.expand( script.context(), pathsToExpand )

		pathsToFullyExpand = IECore.PathMatcher( list( args["scene"]["fullyExpandedPaths"] ) )

		with script.context() :
			for node in script.selection() :
				for scenePlug in [ p for p in node.children( GafferScene.ScenePlug ) if p.direction() == Gaffer.Plug.Direction.Out ] :
					GafferSceneUI.ContextAlgo.expandDescendants( script.context(), pathsToFullyExpand, scenePlug )

		GafferSceneUI.ContextAlgo.setSelectedPaths( script.context(), IECore.PathMatcher( args["scene"]["selectedPaths"] ) )

		# Add a delay.

		t = time.time() + args["delay"].value
		while time.time() < t :
			GafferUI.EventLoop.waitForIdle( 1 )

		# Write the image, creating a directory for it if necessary.

		if args["image"].value :
			IECore.msg( IECore.Msg.Level.Info, "screengrab", "Writing image [ %s ]" % args["image"].value )
			GafferUI.WidgetAlgo.grab( widget = self.getGrabWidget(), imagePath = args["image"].value )

		# Remove the script and any reference to the grab widget up so
		# we can shut down cleanly.
		self.root()["scripts"].clearChildren()
		self.setGrabWidget( None )

		return 0

IECore.registerRunTimeTyped( screengrab )
