##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

## The Viewer provides the primary means of visualising the output
# of Nodes. It defers responsibility for the generation of content to
# the View classes, which are registered against specific types of
# Plug.
## \todo Support split screening two Views together and overlaying
# them etc. Hopefully we can support that entirely within the Viewer
# without modifying the Views themselves.
class Viewer( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode, **kw ) :
	
		self.__gadgetWidget = GafferUI.GadgetWidget(
			bufferOptions = set( (
				GafferUI.GLWidget.BufferOptions.Depth,
				GafferUI.GLWidget.BufferOptions.Double )
			),					
		)
		
		GafferUI.NodeSetEditor.__init__( self, self.__gadgetWidget, scriptNode, **kw )

		self.__views = []
		self.__currentView = None

		self._updateFromSet()
	
	def __repr__( self ) :

		return "GafferUI.Viewer( scriptNode )"

	def _updateFromSet( self ) :
			
		node = self._lastAddedNode()
		
		self.__currentView = None
		self.__plugDirtiedConnection = None
		if node :	
			for plug in node.children() :
				if isinstance( plug, Gaffer.Plug ) and plug.direction() == Gaffer.Plug.Direction.Out :
					for view in self.__views :
						if view["in"].acceptsInput( plug ) :
							self.__currentView = view
							self.__currentView["in"].setInput( plug )
							break
					if self.__currentView is None :
						self.__currentView = GafferUI.View.create( plug )
						if self.__currentView :
							self.__views.append( self.__currentView )
					if self.__currentView is not None :
						break
						
		if self.__currentView is not None :	
			self.__plugDirtiedConnection = self.__currentView.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ) )
			self.__gadgetWidget.setViewportGadget( self.__currentView.viewportGadget() )
			self.__update()
		else :
			self.__gadgetWidget.setViewportGadget( GafferUI.ViewportGadget() )
				
	def _updateFromContext( self ) :
	
		self.__update()
	
	def __update( self ) :
	
		if self.__currentView is None :
			return
			
		self.__currentView.setContext( self.getContext() )	
		self.__currentView._updateFromPlug()
		
	def __plugDirtied( self, plug ) :
	
		# Ideally we might want the view to be doing the update automatically on dirty,
		# rather than for to call _updateFromPlug ourselves. Currently we can't do that
		# because the Views are implemented in C++ and might spawn threads which need
		# to call back into Python - leading to deadlock if the GIL hasn't been released
		# previously. The binding for View.updateFromPlug() releases the GIL for us to
		# work around that problem - another solution might be to release the GIL in all
		# bindings which might eventually trigger a plug dirtied signal, but that could
		# be nearly anything.
		if plug.isSame( self.__currentView["in"] ) :
			self.__update()	

GafferUI.EditorWidget.registerType( "Viewer", Viewer )
