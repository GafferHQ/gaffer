##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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
import os

class gui( Gaffer.Application ) :

	def __init__( self ) :
	
		Gaffer.Application.__init__(
			self,
			"This application provides a graphical user interface for editing node graphs."
		)
		
		self.parameters().addParameters(
		
			[
				IECore.StringVectorParameter(
					name = "scripts",
					description = "A list of scripts to edit.",
					defaultValue = IECore.StringVectorData(),
				),
				
				IECore.BoolParameter(
					name = "fullScreen",
					description = "Opens the UI in full screen mode.",
					defaultValue = False,
				),
			]
			
		)
		
		self.parameters().userData()["parser"] = IECore.CompoundObject(
			{
				"flagless" : IECore.StringVectorData( [ "scripts" ] )
			}
		)
		
	def doRun( self, args ) :
	
		# we must make the application root a member variable because we need to
		# make sure it stays alive for as long as the ui is alive.
		# normally it would be fine to have it as a local variable because
		# GafferUI.EventLoop.mainEventLoop().start() won't return until the
		# user has closed all the script windows, after which we don't need
		# the application root any longer. however, when we run embedded in maya,
		# GafferUI.EventLoop.mainEventLoop().start() returns immediately.
		# we therefore hold onto our application root, and assume that the
		# invoker of the application will hold a reference to us to keep it
		# alive.
		self.__application = Gaffer.ApplicationRoot( "gui" )

		self._executeStartupFiles( [ "gui" ], { "application" : self.__application } )
	
		GafferUI.ScriptWindow.connect( self.__application )
		
		if len( args["scripts"] ) :
			for fileName in args["scripts"] :
				scriptNode = Gaffer.ScriptNode( os.path.splitext( os.path.basename( fileName ) )[0] )
				scriptNode["fileName"].setValue( os.path.abspath( fileName ) )
				scriptNode.load()
				self.__application["scripts"].addChild( scriptNode )
		else :
			self.__application["scripts"]["script1"] = Gaffer.ScriptNode()
		
		if args["fullScreen"].value :
			primaryScript = self.__application["scripts"][-1]
			primaryWindow = GafferUI.ScriptWindow.acquire( primaryScript )
			primaryWindow.setFullScreen( True )
			
		GafferUI.EventLoop.mainEventLoop().start()		
				
		return 0

IECore.registerRunTimeTyped( gui )

