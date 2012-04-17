##########################################################################
#  
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

import GafferUI

import GafferScene

__all__ = []

## The Viewer currently wants to be given a Renderable, which the SceneProcedural is not.
# So we wrap it in this class so we can give it to the Viewer. This should all change when
# the Viewer becomes more elaborate and we actually implement a SceneView class.
class __WrappingProcedural( IECore.ParameterisedProcedural ) :

	def __init__( self, procedural ) :
	
		IECore.ParameterisedProcedural.__init__( self, "" )
		
		self.__procedural = procedural
		
	def doBound( self, args ) :
	
		return self.__procedural.bound()
		
	def doRender( self, renderer, args ) :
	
		renderer.procedural( self.__procedural )
		
def __sceneViewCreator( plug, context ) :

	pathsToExpand = IECore.StringVectorData( [ "/" ] )
	with IECore.IgnoredExceptions( Exception ) :
		pathsToExpand = context.get( "ui:scene:expandedPaths" )

	return __WrappingProcedural( GafferScene.SceneProcedural( plug, context, "/", pathsToExpand ) )
	
GafferUI.Viewer.registerView( GafferScene.ScenePlug.staticTypeId(), __sceneViewCreator )