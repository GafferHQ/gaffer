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
		self.__pendingUpdate = False

		self._updateFromSet()
	
	def __repr__( self ) :

		return "GafferUI.Viewer( scriptNode )"

	def _updateFromSet( self ) :
		
		GafferUI.NodeSetEditor._updateFromSet( self )
		
		self.__currentView = None
		self.__updateRequestConnection = None
		needToUpdate = False
		
		node = self._lastAddedNode()
		if node :	
			for plug in node.children( Gaffer.Plug.staticTypeId() ) :
				if isinstance( plug, Gaffer.Plug ) and plug.direction() == Gaffer.Plug.Direction.Out :
					# try to reuse an existing view
					for view in self.__views :
						if view["in"].acceptsInput( plug ) :
							self.__currentView = view
							viewInput = self.__currentView["in"].getInput()
							if not viewInput or not viewInput.isSame( plug ) :
								self.__currentView["in"].setInput( plug )
								needToUpdate = True
							break
					# if that failed then make a new one
					if self.__currentView is None :
						self.__currentView = GafferUI.View.create( plug )
						if self.__currentView is not None:
							self.__views.append( self.__currentView )
							needToUpdate = True
							break
										
		if self.__currentView is not None :	
			self.__gadgetWidget.setViewportGadget( self.__currentView.viewportGadget() )
			self.__updateRequestConnection = self.__currentView.updateRequestSignal().connect( Gaffer.WeakMethod( self.__updateRequest ) )
			if needToUpdate :
				self.__update()
		else :
			self.__gadgetWidget.setViewportGadget( GafferUI.ViewportGadget() )
				
	def _titleFormat( self ) :
	
		return GafferUI.NodeSetEditor._titleFormat( self, _maxNodes = 1, _reverseNodes = True, _ellipsis = False )

	def __update( self ) :
	
		self.__pendingUpdate = False
	
		if self.__currentView is None :
			return
			
		if not self.__currentView.getContext().isSame( self.getContext() ) :
			self.__currentView.setContext( self.getContext() )
		
		self.__currentView._update()
	
	def __updateRequest( self, view ) :
	
		assert( view.isSame( self.__currentView ) )
		
		# Ideally we might want the view to be doing the update automatically whenever it
		# wants, rather than using updateRequestSignal() to request a call back in to update().
		# Currently we can't do that because the Views are implemented in C++ and might spawn
		# threads which need to call back into Python - leading to deadlock if the GIL hasn't
		# been released previously. The binding for View._update() releases the GIL for
		# us to work around that problem - another solution might be to release the GIL in all
		# bindings which might eventually trigger a viewer update, but that could
		# be nearly anything.
		if not self.__pendingUpdate :
			self.__pendingUpdate = True
			GafferUI.EventLoop.executeOnUIThread( self.__update )
			
GafferUI.EditorWidget.registerType( "Viewer", Viewer )
