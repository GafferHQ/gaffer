##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

from __future__ import with_statement

import IECore

import Gaffer
import GafferScene

class ScriptProcedural( IECore.ParameterisedProcedural ) :

	def __init__( self ) :
	
		IECore.ParameterisedProcedural.__init__( self, "Generates geometry from a node within a .gfr script." )
	
		self.parameters().addParameters(
			
			[
				
				IECore.FileNameParameter(
					name = "fileName",
					description = "The gaffer script which contains a scene to generate geometry from.",
					allowEmptyString = False,
					check = IECore.FileNameParameter.CheckType.MustExist,
					extensions = "gfr",
				),
				
				IECore.StringParameter(
					name = "node",
					description = "The node to generate geometry from.",
					defaultValue = "",
				),
				
				IECore.FloatParameter(
					name = "frame",
					description = "The frame to generate geometry at.",
					defaultValue = 1,
				),
				
			]
			
		)
	
		self.__currentFileName = None
	
	def doBound( self, args ) :
	
		plug, context = self.__plugAndContext( args )
		if plug is  None :
			return IECore.Box3f()
	
		sceneProcedural = GafferScene.SceneProcedural( plug, context, "/" )
		return sceneProcedural.bound()

	def doRender( self, renderer, args ) :
	
		plug, context = self.__plugAndContext( args )
		if plug is None :
			return
			
		sceneProcedural = GafferScene.SceneProcedural( plug, context, "/" )
		renderer.procedural( sceneProcedural )
		
	def __plugAndContext( self, args ) :
	
		if args["fileName"].value != self.__currentFileName :
		
			if args["fileName"].value == "" :
				self.__scriptNode = None
			else :
				self.__scriptNode = Gaffer.ScriptNode()
				self.__scriptNode["fileName"].setValue( args["fileName"].value )
				self.__scriptNode.load()
				self.__currentFileName = args["fileName"].value
			
		if self.__scriptNode is None :
			return None, None
		
		if not args["node"].value :
			return None, None
		
		node = self.__scriptNode.descendant( args["node"].value )
		
		context = Gaffer.Context( self.__scriptNode.context() )
		context.setFrame( args["frame"].value )
		
		return node["out"], context

IECore.registerRunTimeTyped( ScriptProcedural, typeName = "GafferScene::ScriptProcedural" )
