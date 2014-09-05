##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

class execute( Gaffer.Application ) :

	def __init__( self ) :
	
		Gaffer.Application.__init__( self )
		
		self.parameters().addParameters(
		
			[
				IECore.FileNameParameter(
					name = "script",
					description = "The script to execute.",
					defaultValue = "",
					allowEmptyString = False,
					extensions = "gfr",
					check = IECore.FileNameParameter.CheckType.MustExist,
				),
				
				IECore.StringVectorParameter(
					name = "nodes",
					description = "The names of the nodes to execute. If not specified "
						"then all executable nodes will be found automatically.",
					defaultValue = IECore.StringVectorData( [] ),
				),
				
				IECore.FrameListParameter(
					name = "frames",
					description = "The frames to execute.",
					defaultValue = "1",
					allowEmptyList = False,
				),
				
				IECore.StringVectorParameter(
					name = "context",
					description = "The context used during execution. Note that the frames "
						"parameter will be used to vary the context frame entry.",
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
				"flagless" : IECore.StringVectorData( [ "script" ] )
			}
		)
		
	def _run( self, args ) :
			
		scriptNode = Gaffer.ScriptNode( os.path.splitext( os.path.basename( args["script"].value ) )[0] )
		scriptNode["fileName"].setValue( os.path.abspath( args["script"].value ) )
		scriptNode.load()
		self.root()["scripts"].addChild( scriptNode )
		
		nodes = []
		if len( args["nodes"] ) :
			for nodeName in args["nodes"] :
				node = scriptNode.descendant( nodeName )
				if node is None :
					IECore.msg( IECore.Msg.Level.Error, "gaffer execute", "Node \"%s\" does not exist" % nodeName )
					return 1
				if not hasattr( node, "execute" ) :
					IECore.msg( IECore.Msg.Level.Error, "gaffer execute", "Node \"%s\" is not executable" % nodeName )
					return 1
				nodes.append( node )
		else :
			for node in scriptNode.children() :
				if hasattr( node, "execute" ) :
					nodes.append( node )
			if not nodes :
				IECore.msg( IECore.Msg.Level.Error, "gaffer execute", "Script has no executable nodes" )
				return 1
		
		if len(args["context"]) % 2 :
			IECore.msg( IECore.Msg.Level.Error, "gaffer execute", "Context parameter must have matching entry/value pairs" )
			return 1
		
		context = Gaffer.Context( scriptNode.context() )
		for i in range( 0, len(args["context"]), 2 ) :
			entry = args["context"][i].lstrip( "-" )
			context[entry] = eval( args["context"][i+1] )
		
		frames = self.parameters()["frames"].getFrameListValue().asList()
		
		with context :
			for node in nodes :
				node.executeSequence( frames )
		
		return 0

IECore.registerRunTimeTyped( execute )

