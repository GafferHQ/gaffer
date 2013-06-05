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

import IECore
import Gaffer
import GafferUI

QtGui = GafferUI._qtImport( "QtGui" )

import os


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
					name = "cmd",
					description = "Command(s) to execute after session is launched. 'script' node is available to interact with script contents",
					defaultValue = "",
				),
			]
			
		)
		
		#dirty hack - pretend we are the gui app so that we can load all of its startup files.
		self.root().setName("gui") ## these startup files are required to initialise layouts, menus etc 

	
	def _run( self, args ) :
		
		GafferUI.ScriptWindow.connect( self.root() )
		
		#load the specified gfr file
		fileName = str(args["script"])
		script = Gaffer.ScriptNode( os.path.splitext( os.path.basename( fileName ) )[0] )
		script["fileName"].setValue( os.path.abspath( fileName ) )
		script.load()
		self.root()["scripts"].addChild( script )
		
		#get a hook into the target window
		self.__primaryWindow = GafferUI.ScriptWindow.acquire( script )
		
		#set up target to write to
		self.__image = str(args["image"])
		#create path if missing
		targetdir = os.path.dirname(self.__image)
		if not os.path.exists(targetdir):
			IECore.msg( IECore.Msg.Level.Info, "screengrab", "Creating target directory [ %s ]" % (targetdir) )
			os.makedirs(targetdir)
		
		#execute any commands passed as arguments prior to doing the screengrab
		exec(str(args["cmd"]))
		
		#register the function to run when the app is idle.
		self.__idleCount = 0
		GafferUI.EventLoop.addIdleCallback( self.__grabAndQuit )
		GafferUI.EventLoop.mainEventLoop().start()
		
		return 0

	def __grabAndQuit( self ) :
		
		
		self.__idleCount += 1
		if self.__idleCount == 100 : #put a little wait in to give gaffer a chance to draw the ui
			
			#do some dirty rummaging to get the id of the resulting window
			## this should replaced by gaffer api methods in future
			winhandle = self.__primaryWindow._qtWidget().winId()
			
			#use QPixmap to snapshot the window
			pm = QtGui.QPixmap.grabWindow( winhandle )
			
			#save that file out
			IECore.msg( IECore.Msg.Level.Info, "screengrab", "Writing image [ %s ]" % (self.__image) )
			pm.save( self.__image )
			
			#exit the application once we've done the screen grab
			GafferUI.EventLoop.mainEventLoop().stop()
		
		return True

IECore.registerRunTimeTyped( screengrab )
