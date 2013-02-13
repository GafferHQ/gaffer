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
import IECoreRI

import Gaffer
import GafferScene

class RenderManRender( GafferScene.Render ) :

	def __init__( self, name="RenderManRender" ) :
	
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
				"ribFileName",
			)
		)
				
	def _createRenderer( self ) :
	
		renderer = IECoreRI.Renderer( self.__fileName() )
		return renderer
		
	def _outputProcedural( self, procedural, bound, renderer ) :
	
		assert( isinstance( procedural, GafferScene.ScriptProcedural ) )	
		
		serialisedParameters = str( IECore.ParameterParser().serialise( procedural.parameters() ) )
		pythonString = "IECoreRI.executeProcedural( 'gaffer/script', 1, %s )" % serialisedParameters
		
		dynamicLoadCommand = "Procedural \"DynamicLoad\" [ \"iePython\" \"%s\" ] [ %f %f %f %f %f %f ]\n" % \
			(
				pythonString,
				bound.min.x, bound.max.x,
				bound.min.y, bound.max.y,
				bound.min.z, bound.max.z,
			)
				
		renderer.command(
			"ri:archiveRecord",
			{
				"type" : "verbatim",	
				"record" : dynamicLoadCommand
			}
		)
		
	def _commandAndArgs( self ) :
		
		mode = self["mode"].getValue()
		if mode == "render" :
			return [ "renderdl", self.__fileName() ]
		else :
			return []
			
	def __fileName( self ) : 
	
		result = self["ribFileName"].getValue()
		# because execute() isn't called inside a compute(), we
		# don't get string expansions automatically, and have to
		# do them ourselves.
		## \todo Can we improve this situation?
		result = Gaffer.Context.current().substitute( result )
		return result

IECore.registerRunTimeTyped( RenderManRender )
