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
import GafferScene

##########################################################################
# Metadata
##########################################################################

GafferUI.Metadata.registerNodeDescription(

GafferScene.Shader,

"""The base type for all nodes which create shaders. Use the ShaderAssignment node to assign them to objects in the scene.""",

"name",
{
	"description" :
	"""The name of the shader being represented. This should be considered read-only. Use the Shader.loadShader() method to load a shader.""",
	"nodeUI:section" : "header",
},

"parameters",
"""Where the parameters for the shader are represented.""",

)

##########################################################################
# PlugValueWidgets
##########################################################################

class __ShaderNamePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :
	
		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
	
		GafferUI.PlugValueWidget.__init__( self, row, plug, **kw )
		
		with row :
		
			self.__label = GafferUI.Label( "" )
					
			GafferUI.Spacer( IECore.V2i( 1 ), expand=True )
			
			self.__button = GafferUI.Button( "Reload" )
			self.__buttonClickedConnection = self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )
			
		self._updateFromPlug()
	
	def hasLabel( self ) :
	
		return True
		
	def _updateFromPlug( self ) :
	
		with self.getContext() :
			shaderName = self.getPlug().getValue()
			self.__label.setText( "<h3>Shader : " + shaderName + "</h3>" )
			## \todo Disable the RenderMan check once we've got all the shader types implementing reloading properly.
			self.__button.setEnabled( shaderName and "RenderMan" in self.getPlug().node().typeName() )
			
	def __buttonClicked( self, button ) :
	
		node = self.getPlug().node()
		node.shaderLoader().clear()
		
		with Gaffer.UndoContext( node.ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
			node.loadShader( node["name"].getValue(), keepExistingValues = True )

GafferUI.PlugValueWidget.registerCreator( GafferScene.Shader.staticTypeId(), "name", __ShaderNamePlugValueWidget )

GafferUI.PlugValueWidget.registerCreator( GafferScene.Shader.staticTypeId(), "parameters", GafferUI.CompoundPlugValueWidget, collapsed=None )
GafferUI.PlugValueWidget.registerCreator( GafferScene.Shader.staticTypeId(), "out", None )
GafferUI.PlugValueWidget.registerCreator( GafferScene.Shader.staticTypeId(), "type", None )
GafferUI.PlugValueWidget.registerCreator( GafferScene.Shader.staticTypeId(), "enabled", None )

##########################################################################
# NodeGadgets and Nodules
##########################################################################

def __nodeGadgetCreator( node ) :

	return GafferUI.StandardNodeGadget( node, GafferUI.LinearContainer.Orientation.Y )

GafferUI.NodeGadget.registerNodeGadget( GafferScene.Shader.staticTypeId(), __nodeGadgetCreator )

def __parametersNoduleCreator( plug ) :

	return GafferUI.CompoundNodule( plug, GafferUI.LinearContainer.Orientation.Y, spacing = 0.2 )

GafferUI.Nodule.registerNodule( GafferScene.Shader.staticTypeId(), "parameters", __parametersNoduleCreator )
GafferUI.Nodule.registerNodule( GafferScene.Shader.staticTypeId(), "name", lambda plug : None )
GafferUI.Nodule.registerNodule( GafferScene.Shader.staticTypeId(), "type", lambda plug : None )
GafferUI.Nodule.registerNodule( GafferScene.Shader.staticTypeId(), "enabled", lambda plug : None )

# we leave it to the derived class uis to register creators for the parameters.* plugs, because only the derived classes know whether
# or not networkability makes sense in each case.
