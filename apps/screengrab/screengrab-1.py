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

import IECore

import Gaffer
import GafferUI

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
					allowEmptyString = False,
					check = IECore.FileNameParameter.CheckType.MustExist,
				),

				IECore.FileNameParameter(
					name = "image",
					description = "Where to save the resulting image",
					defaultValue = "",
					extensions = "png",
					allowEmptyString = False,
				),

				IECore.StringParameter(
					name = "editor",
					description = "The name of an editor to screengrab. If not specified, the whole window will be grabbed.",
					defaultValue = "",
				),

				IECore.StringParameter(
					name = "cmd",
					description = "Command(s) to execute after session is launched. 'script' node is available to interact with script contents",
					defaultValue = "",
				),

				IECore.StringParameter(
					name = "cmdfile",
					description = "File containing sequence of commands to execute after session is launched.",
					defaultValue = "",
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
		script["fileName"].setValue( os.path.abspath( args["script"].value ) )
		script.load()
		self.root()["scripts"].addChild( script )

		# Choose the widget we'll grab by default. This can be overridden
		# by the command files below by calling `application.setGrabWidget()`.

		scriptWindow = GafferUI.ScriptWindow.acquire( script )
		self.setGrabWidget( scriptWindow )

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

			self.setGrabWidget( editors[0] )

		# Set up some default framing for the node graphs.

		self.__waitForIdle()

		for nodeGraph in scriptWindow.getLayout().editors( GafferUI.NodeGraph ) :
			nodeGraph.frame( script.children( Gaffer.Node ) )

		# Execute any commands we've been asked to, exposing the application
		# and script as variables.

		self.__waitForIdle()

		d = {
			"application" 	: self,
			"script"		: script,
		}

		if args["cmd"].value :
			exec( args["cmd"].value, d, d )
		if args["cmdfile"].value :
			execfile( args["cmdfile"].value, d, d )

		# Write the image, creating a directory for it if necessary.

		self.__waitForIdle()

		imageDir = os.path.dirname( args["image"].value )
		if imageDir and not os.path.isdir( imageDir ) :
			IECore.msg( IECore.Msg.Level.Info, "screengrab", "Creating target directory [ %s ]" % imageDir )
			os.makedirs( imageDir )

		pixmap = QtGui.QPixmap.grabWindow( self.getGrabWidget()._qtWidget().winId() )
		IECore.msg( IECore.Msg.Level.Info, "screengrab", "Writing image [ %s ]" % args["image"].value )
		pixmap.save( args["image"].value )

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
