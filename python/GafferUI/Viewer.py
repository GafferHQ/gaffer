##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

import copy 
import functools

import gtk

import IECore
import IECoreGL

import Gaffer
import GafferUI

class Viewer( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode=None ) :
	
		GafferUI.NodeSetEditor.__init__( self, gtk.EventBox(), scriptNode )

		self.__renderableGadget = GafferUI.RenderableGadget( None )
		self.__gadgetWidget = GafferUI.GadgetWidget( self.__renderableGadget, bufferOptions=set( ( GafferUI.GLWidget.BufferOptions.Depth, ) ), cameraMode=GafferUI.GadgetWidget.CameraMode.Mode3D )
		self.__gadgetWidget.gtkWidget().connect( "button-press-event", self.__buttonPress )
		self.__gadgetWidget.baseState().add( IECoreGL.Primitive.DrawWireframe( True ) )
		
		self.gtkWidget().add( self.__gadgetWidget.gtkWidget() )
		
		self._updateFromSet()
	
	## Returns an IECore.MenuDefinition which is used to define the right click menu for all Viewers.
	# This can be edited at any time to modify the menu - typically this would be done from a startup
	# script.
	@staticmethod
	def menuDefinition() :
	
		return Viewer.__menuDefinition

	__menuDefinition = IECore.MenuDefinition()
		
	def __repr__( self ) :

		return "GafferUI.Viewer()"

	def _updateFromSet( self ) :
	
		if not hasattr( self, "_Viewer__renderableGadget" ) :
			# we're being called during construction
			return
		
		node = self.getNodeSet().lastAdded()
		if node :
			self.__plugDirtiedConnection = node.plugDirtiedSignal().connect( self.__plugDirtied )
		else :
			self.__plugDirtiedConnection = None
			
		self.__update()	
		
	def __update( self ) :
	
		renderable = None			
		node = self.getNodeSet().lastAdded()
		if node and "output" in node :
			renderable = node["output"].getValue()
				
		self.__renderableGadget.setRenderable( renderable )
		self.__gadgetWidget.setGadget( self.__renderableGadget )
	
	def __plugDirtied( self, plug ) :
	
		if plug.getName()=="output" :
			self.__update()
			
	def __buttonPress( self, widget, event ) :
	
		if event.button==3 :
		
			# right click menu
			menuDefinition = copy.deepcopy( self.menuDefinition() )
			menuDefinition.append( "/Style/Wireframe", { "checkBox" : IECore.curry( self.__baseState, componentType=IECoreGL.Primitive.DrawWireframe ), "command" : IECore.curry( self.__toggleBaseState, componentType=IECoreGL.Primitive.DrawWireframe ) } )
			menuDefinition.append( "/Style/Solid", { "checkBox" : IECore.curry( self.__baseState, componentType=IECoreGL.Primitive.DrawSolid ), "command" : IECore.curry( self.__toggleBaseState, componentType=IECoreGL.Primitive.DrawSolid ) } )
			menuDefinition.append( "/Style/Points", { "checkBox" : IECore.curry( self.__baseState, componentType=IECoreGL.Primitive.DrawPoints ), "command" : IECore.curry( self.__toggleBaseState, componentType=IECoreGL.Primitive.DrawPoints ) } )
			menuDefinition.append( "/Style/Bound", { "checkBox" : IECore.curry( self.__baseState, componentType=IECoreGL.Primitive.DrawBound ), "command" : IECore.curry( self.__toggleBaseState, componentType=IECoreGL.Primitive.DrawBound ) } )
			
			self.__m = GafferUI.Menu( menuDefinition )
			self.__m.popup( self ) 
			
			return True
		
		return False
	
	def __baseState( self, componentType=None ) :
	
		return self.__gadgetWidget.baseState().get( componentType.staticTypeId() ).value
		
	def __toggleBaseState( self, checkBox, componentType=None ) :
	
		self.__gadgetWidget.baseState().add( componentType( checkBox ) )
		
GafferUI.EditorWidget.registerType( "Viewer", Viewer )
