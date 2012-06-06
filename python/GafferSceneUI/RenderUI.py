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

import fnmatch

import Gaffer
import GafferScene
import GafferUI

class RenderUI( GafferUI.NodeUI ) :

	def __init__( self, node, **kw ) :
	
		GafferUI.NodeUI.__init__( self, node, **kw )
		
	def _build( self ) :
	
		GafferUI.NodeUI._build( self )
		
		executeButton = GafferUI.Button( "Execute" )
		self.__executeButtonConnection = executeButton.clickedSignal().connect( Gaffer.WeakMethod( self.__executeClicked ) )
		
		self._addWidget( executeButton )
		
	def __executeClicked( self, button ) :
	
		self._node().execute()

def __createParameterWidget( plug ) :

	return GafferUI.CompoundParameterValueWidget( plug.node().parameterHandler(), collapsible=False )

GafferUI.NodeUI.registerNodeUI( GafferScene.Render.staticTypeId(), RenderUI )
GafferUI.NodeUI.registerPlugValueWidget( GafferScene.Render.staticTypeId(), "in", None )

GafferUI.Nodule.registerNodule( GafferScene.Render.staticTypeId(), fnmatch.translate( "*" ), lambda plug : None )
GafferUI.Nodule.registerNodule( GafferScene.Render.staticTypeId(), "in", GafferUI.StandardNodule )
