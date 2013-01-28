##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI

# import lazily to improve startup of apps which don't use GL functionality
IECoreGL = Gaffer.lazyImport( "IECoreGL" )

## The Viewer provides the primary means for the user to look at the output
# of Nodes.
class Viewer( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode, **kw ) :
	
		self.__renderableGadget = GafferUI.RenderableGadget( None )
		self.__gadgetWidget = GafferUI.GadgetWidget(
			
			self.__renderableGadget,
			
			bufferOptions = set( (
				GafferUI.GLWidget.BufferOptions.Depth,
				GafferUI.GLWidget.BufferOptions.Double )
			),
					
		)
		
		GafferUI.NodeSetEditor.__init__( self, self.__gadgetWidget, scriptNode, **kw )

		self.__renderableGadget.baseState().add( IECoreGL.Primitive.DrawWireframe( True ) )
		self.__gadgetWidget.getViewportGadget().setCamera(
			IECore.Camera( parameters = { "projection" : IECore.StringData( "perspective" ) } )
		)
		
		self.__buttonPressConnection = self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.__keyPressConnection = self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )
		
		self.__viewedPlug = None		
		self.__viewCreator = None

		self._updateFromSet()
	
	## Returns an IECore.MenuDefinition which is used to define the right click menu for all Viewers.
	# This can be edited at any time to modify the menu - typically this would be done from a startup
	# script.
	@staticmethod
	def menuDefinition() :
	
		return Viewer.__menuDefinition

	__menuDefinition = IECore.MenuDefinition()
	
	## Registers a function which can extract a VisibleRenderable from
	# a plug of a given type for viewing.
	## \todo This will need to become much more complex to support incremental
	# update, on screen editing handles etc. At that point we should probably
	# define a new View class which the creator should return instances of.
	@classmethod
	def registerView( cls, plugTypeId, creator ) :
	
		cls.__typesToCreators[plugTypeId] = creator
		
	__typesToCreators = {}
	
	def __repr__( self ) :

		return "GafferUI.Viewer( scriptNode )"

	def _updateFromSet( self ) :
		
		GafferUI.NodeSetEditor._updateFromSet( self )
			
		node = self._lastAddedNode()
		
		self.__viewedPlug = None
		self.__viewCreator = None
		self.__plugDirtiedConnection = None
		if node :
		
			for plug in node.children( Gaffer.Plug.staticTypeId() ) :
				if plug.direction() == Gaffer.Plug.Direction.Out and plug.typeId() in self.__typesToCreators :
					self.__viewedPlug = plug
					self.__viewCreator = self.__typesToCreators[plug.typeId()]
					break
			
			if self.__viewedPlug is not None :
				self.__plugDirtiedConnection = node.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ) )

		self.__update()	
	
	def _updateFromContext( self ) :
	
		self.__update()

	def _titleFormat( self ) :
	
		return GafferUI.NodeSetEditor._titleFormat( self, _maxNodes = 1, _reverseNodes = True, _ellipsis = False )

	def __update( self ) :

		renderable = None	
		if self.__viewedPlug is not None :
			renderable = self.__viewCreator( self.__viewedPlug, self.getContext() )
			renderable = renderable if isinstance( renderable, IECore.Renderable ) else None
			
		self.__renderableGadget.setRenderable( renderable )
	
	def __plugDirtied( self, plug ) :
	
		if plug.isSame( self.__viewedPlug ) :
			self.__update()
			
	def __buttonPress( self, widget, event ) :
	
		if event.buttons & GafferUI.ButtonEvent.Buttons.Right :
		
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
	
	def __keyPress( self, widget, event ) :
	
		if event.key == "F" :
			self.__gadgetWidget.getViewportGadget().frame( self.__renderableGadget.bound() )
			return True
		
		return False
	
	def __baseState( self, componentType=None ) :
	
		return self.__renderableGadget.baseState().get( componentType.staticTypeId() ).value
		
	def __toggleBaseState( self, checkBox, componentType=None ) :
	
		self.__renderableGadget.baseState().add( componentType( checkBox ) )
		self.__renderableGadget.renderRequestSignal()( self.__renderableGadget )
		
GafferUI.EditorWidget.registerType( "Viewer", Viewer )

def __objectPlugViewCreator( plug, context ) :

	with context :
		return plug.getValue( _copy=False )
	
Viewer.registerView( Gaffer.ObjectPlug.staticTypeId(), __objectPlugViewCreator )
