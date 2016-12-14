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

import IECore

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

QtGui = GafferUI._qtImport( "QtGui" )

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
					allowEmptyString = False,
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
					name = "scriptEditor",
					description = "Parameters that configure ScriptEditors.",
					members = [
						IECore.StringParameter(
							name = "execute",
							description = "Some python code to execute in the script editor.",
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
							defaultValue = IECore.V3f( -0.64, -0.422, -0.64 ),
						),
					]
				),

				IECore.CompoundParameter(
					name = "nodeGraph",
					description = "Parameters that configure NodeGraphs.",
					members = [
						IECore.StringVectorParameter(
							name = "frame",
							description = "The names of nodes to frame in the NodeGraph.",
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
							description = "A list of locations to expand in the Viewer and SceneHierarchy.",
							defaultValue = IECore.StringVectorData(),
						),
						IECore.StringVectorParameter(
							name = "fullyExpandedPaths",
							description = "A list of locations to expand fully in the Viewer and SceneHierarchy.",
							defaultValue = IECore.StringVectorData(),
						),
						IECore.StringVectorParameter(
							name = "selectedPaths",
							description = "A list of locations to select in the Viewer and SceneHierarchy.",
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

		self.__waitForIdle()

		d = {
			"application" 	: self,
			"script"		: script,
		}

		if args["command"].value :
			exec( args["command"].value, d, d )
		if args["commandFile"].value :
			execfile( args["commandFile"].value, d, d )

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

		self.__waitForIdle()

		for nodeGraph in scriptWindow.getLayout().editors( GafferUI.NodeGraph ) :
			if args["nodeGraph"]["frame"] :
				nodeGraph.frame( [ script.descendant( n ) for n in args["nodeGraph"]["frame"] ] )
			else :
				nodeGraph.frame( script.children( Gaffer.Node ) )

		# Set up the NodeEditors as requested.

		for nodeEditor in scriptWindow.getLayout().editors( GafferUI.NodeEditor ) :

			for name in args["nodeEditor"]["reveal"] :
				plugValueWidget = nodeEditor.nodeUI().plugValueWidget( script.descendant( name ) )
				plugValueWidget.reveal()

			if args["nodeEditor"]["grab"].value :
				grabWidget = nodeEditor.nodeUI().plugValueWidget( script.descendant( args["nodeEditor"]["grab"].value ) )
				grabWidget = grabWidget.ancestor( GafferUI.PlugWidget ) or grabWidget
				grabWidget.reveal()
				self.setGrabWidget( grabWidget )

		# Set up the ScriptEditors as requested.

		for scriptEditor in scriptWindow.getLayout().editors( GafferUI.ScriptEditor ) :

			if args["scriptEditor"]["execute"].value :
				scriptEditor.inputWidget().setText( args["scriptEditor"]["execute"].value )
				scriptEditor.inputWidget()._qtWidget().selectAll()
				scriptEditor.execute()

		# Set up the Viewers as requested.

		for viewer in scriptWindow.getLayout().editors( GafferUI.Viewer ) :
			if isinstance( viewer.view(), GafferSceneUI.SceneView ) :
				viewer.view()["minimumExpansionDepth"].setValue( args["viewer"]["minimumExpansionDepth"].value )
				if args["viewer"]["framedObjects"] :
					bound = IECore.Box3f()
					for path in args["viewer"]["framedObjects"] :
						objectBound = viewer.view()["in"].bound( path )
						objectFullTransform = viewer.view()["in"].fullTransform( path )
						bound.extendBy( objectBound.transform( objectFullTransform ) )
					viewer.view().viewportGadget().frame( bound, args["viewer"]["viewDirection"].value.normalized() )

		del viewer

		# Set up the scene expansion and selection.

		pathsToExpand = GafferScene.PathMatcher()

		for path in list( args["scene"]["fullyExpandedPaths"] ) + list( args["scene"]["expandedPaths"] ) :
			# Add paths and all their ancestors.
			while path :
				pathsToExpand.addPath( path )
				path = path.rpartition( "/" )[0]

		fullyExpandedPathsFilter = GafferScene.PathFilter()
		fullyExpandedPathsFilter["paths"].setValue(
			IECore.StringVectorData( [ path + "/..." for path in args["scene"]["fullyExpandedPaths"] ] )
		)
		for node in script.selection() :
			for scenePlug in [ p for p in node.children( GafferScene.ScenePlug ) if p.direction() == Gaffer.Plug.Direction.Out ] :
				GafferScene.SceneAlgo.matchingPaths( fullyExpandedPathsFilter, scenePlug, pathsToExpand )

		script.context()["ui:scene:expandedPaths"] = GafferScene.PathMatcherData( pathsToExpand )
		script.context()["ui:scene:selectedPaths"] = args["scene"]["selectedPaths"]

		# Add a delay.

		t = time.time() + args["delay"].value
		while time.time() < t :
			self.__waitForIdle( 1 )

		# Write the image, creating a directory for it if necessary.

		self.__waitForIdle()

		imageDir = os.path.dirname( args["image"].value )
		if imageDir and not os.path.isdir( imageDir ) :
			IECore.msg( IECore.Msg.Level.Info, "screengrab", "Creating target directory [ %s ]" % imageDir )
			os.makedirs( imageDir )

		pixmap = QtGui.QPixmap.grabWindow( self.getGrabWidget()._qtWidget().winId() )
		IECore.msg( IECore.Msg.Level.Info, "screengrab", "Writing image [ %s ]" % args["image"].value )
		pixmap.save( args["image"].value )

		# Remove the script and any reference to the grab widget up so
		# we can shut down cleanly.
		self.root()["scripts"].clearChildren()
		self.setGrabWidget( None )

		return 0

	def __waitForIdle( self, count = 1000 ) :

		self.__idleCount = 0
		def f() :

			self.__idleCount += 1

			if self.__idleCount >= count :
				GafferUI.EventLoop.mainEventLoop().stop()
				return False

			return True

		GafferUI.EventLoop.addIdleCallback( f )
		GafferUI.EventLoop.mainEventLoop().start()

IECore.registerRunTimeTyped( screengrab )
