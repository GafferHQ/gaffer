##########################################################################
#  
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

class op( Gaffer.Application ) :

	def __init__( self ) :
	
		Gaffer.Application.__init__( self )
		
		self.parameters().addParameters(
		
			[
			
				IECore.StringParameter(
					name = "op",
					description = "The name of the op to run.",
					defaultValue = ""
				),
				
				IECore.IntParameter(
					name = "version",
					description = "The version of the op to run.",
					defaultValue = -1,
				),
				
				IECore.BoolParameter(
					name = "gui",
					description = "If this is true, then a gui is presented for the op. Otherwise "
						"the op is run directly.",
					defaultValue = False,
				),
				
				IECore.StringVectorParameter(
					name = "arguments",
					description = "The arguments to be passed to the op. This should be the last "
						"command line argument passed.",
					defaultValue = IECore.StringVectorData( [] ),
					userData = {
						"parser" : {
							"acceptFlags" : IECore.BoolData( True ),
						},
					},
				),
				
			]
			
		)
		
		self.parameters().userData()["parser"] = IECore.CompoundObject(
			{
				"flagless" : IECore.StringVectorData( [ "op", "version" ] )
			}
		)
		
	def doRun( self, args ) :
		
		classLoader = IECore.ClassLoader.defaultOpLoader()
		
		matchingOpNames = classLoader.classNames( "*" + args["op"].value )
		if not len( matchingOpNames ) :
			IECore.msg( IECore.Msg.Level.Error, "op", "Op \"%s\" does not exist" % args["op"].value )
			return 1
		elif len( matchingOpNames ) > 1 :
			IECore.msg(
				IECore.Msg.Level.Error, "op",
				"Op name \"%s\" is ambiguous - could be any of the following : \n\n\t%s" % (
					args["op"].value,
					"\n\t".join( matchingOpNames ),
				)
			)
			return 1
		else :
			opName = matchingOpNames[0]
		
		opVersion = args["version"].value
		if opVersion >= 0 :
			if opVersion not in classLoader.versions( opName ) :
				IECore.msg( IECore.Msg.Level.Error, "op", "Version %d of op \"%s\" does not exist" % ( opVersion, args["op"].value ) )
				return 1
		else :
			opVersion = None # let loader choose default	
		
		op = classLoader.load( opName, opVersion )()
		IECore.ParameterParser().parse( list( args["arguments"] ), op.parameters() )
		
		if args["gui"].value :
			import GafferUI # delay import to improve startup times for non-gui case
			self.__dialogue = GafferUI.OpDialogue( op )
			self.__dialogueClosedConnection = self.__dialogue.closedSignal().connect( self.__dialogueClosed )
			self.__dialogue.setVisible( True )
			GafferUI.EventLoop.mainEventLoop().start()
		else :
			op()
			
		return 0

	def __dialogueClosed( self, dialogue ) :
	
		import GafferUI # delay import to improve startup times for non-gui case
		GafferUI.EventLoop.mainEventLoop().stop()

IECore.registerRunTimeTyped( op )
