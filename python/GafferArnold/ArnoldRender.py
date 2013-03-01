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

import os

import IECore
import IECoreArnold

import Gaffer
import GafferScene

class ArnoldRender( GafferScene.Render ) :

	def __init__( self, name="ArnoldRender" ) :
	
		GafferScene.Render.__init__( self, name )
	
		self.addChild(
			Gaffer.StringPlug(
				"mode",
				Gaffer.Plug.Direction.In,
				"render",
			)
		)
	
		self.addChild(
			Gaffer.StringPlug( 
				"fileName",
			)
		)
				
		self.addChild(
			Gaffer.IntPlug(
				"verbosity",
				Gaffer.Plug.Direction.In,
				2
			)
		)
				
	def _createRenderer( self ) :
	
		renderer = IECoreArnold.Renderer( self.__fileName() )
		renderer.setOption( "ai:procedural_searchpath", os.path.expandvars( "$GAFFER_ROOT/arnold/procedurals" ) )
		
		return renderer
		
	def _outputProcedural( self, procedural, bound, renderer ) :
		import arnold
	
		assert( isinstance( procedural, GafferScene.ScriptProcedural ) )
	
		node = arnold.AiNode( "procedural" )
		arnold.AiNodeSetStr( node, "dso", os.path.expandvars( "ieProcedural.so" ) )
		
		arnold.AiNodeSetPnt( node, "min", bound.min.x, bound.min.y, bound.min.z );
		arnold.AiNodeSetPnt( node, "max", bound.max.x, bound.max.y, bound.max.z );
			
		arnold.AiNodeDeclare( node, "className", "constant STRING" )
		arnold.AiNodeDeclare( node, "classVersion", "constant INT" )
		arnold.AiNodeDeclare( node, "parameterValues", "constant ARRAY STRING" )
		
		arnold.AiNodeSetStr( node, "className", "gaffer/script" )
		arnold.AiNodeSetInt( node, "classVersion", 1 )
		
		serialised = IECore.ParameterParser().serialise( procedural.parameters() )
		stringArray = arnold.AiArrayAllocate( len( serialised ), 1, arnold.AI_TYPE_STRING )
		for i in range( 0, len( serialised ) ) :
			arnold.AiArraySetStr( stringArray, i, serialised[i] )
		arnold.AiNodeSetArray( node, "parameterValues", stringArray )
	
	def _commandAndArgs( self ) :
		
		mode = self["mode"].getValue()
		if mode == "render" :
			return [ "kick", "-dp",  "-dw", "-v", str( self["verbosity"].getValue() ), self.__fileName() ]
		elif mode == "expand" :
			return [ "kick", "-v", str( self["verbosity"].getValue() ), "-resaveop", self.__fileName(), self.__fileName() ]
		
		return []
		
	def __fileName( self ) : 
	
		result = self["fileName"].getValue()
		# because execute() isn't called inside a compute(), we
		# don't get string expansions automatically, and have to
		# do them ourselves.
		## \todo Can we improve this situation?
		result = Gaffer.Context.current().substitute( result )
		return result
		
IECore.registerRunTimeTyped( ArnoldRender )
