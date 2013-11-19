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

##########################################################################
# Viewer implementation
##########################################################################

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

		self.__toolbarFrame = GafferUI.Frame( borderWidth = 4, borderStyle=GafferUI.Frame.BorderStyle.None )
		self.__gadgetWidget.addOverlay( self.__toolbarFrame )
		
		self.__views = []
		self.__currentView = None

		self._updateFromSet()
	
	def __repr__( self ) :

		return "GafferUI.Viewer( scriptNode )"

	def _updateFromSet( self ) :
		
		GafferUI.NodeSetEditor._updateFromSet( self )
		
		self.__currentView = None
		
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
								self.__currentView.__pendingUpdate = True
								self.__currentView["in"].setInput( plug )
							break # break out of view loop
					# if that failed then try to make a new one
					if self.__currentView is None :
						self.__currentView = GafferUI.View.create( plug )
						if self.__currentView is not None:
							self.__currentView.__updateRequestConnection = self.__currentView.updateRequestSignal().connect( Gaffer.WeakMethod( self.__updateRequest ) )
							self.__currentView.__pendingUpdate = True
							self.__currentView.__toolbar = _ViewToolbar( self.__currentView )
							self.__views.append( self.__currentView )
					# if we succeeded in getting a suitable view, then
					# don't bother checking the other plugs
					if self.__currentView is not None :
						break
										
		if self.__currentView is not None :	
			self.__gadgetWidget.setViewportGadget( self.__currentView.viewportGadget() )
			self.__toolbarFrame.setChild( self.__currentView.__toolbar )
			if self.__currentView.__pendingUpdate :
				self.__update()
		else :
			self.__gadgetWidget.setViewportGadget( GafferUI.ViewportGadget() )
			self.__toolbarFrame.setChild( None )
			
	def _titleFormat( self ) :
	
		return GafferUI.NodeSetEditor._titleFormat( self, _maxNodes = 1, _reverseNodes = True, _ellipsis = False )

	def __update( self ) :
		
		if self.__currentView is None :
			return
		
		self.__currentView.__pendingUpdate = False
		
		if not self.__currentView.getContext().isSame( self.getContext() ) :
			self.__currentView.setContext( self.getContext() )
				
		self.__currentView._update()
	
	def __updateRequest( self, view ) :
		
		# due to problems with object identity in boost::python, the view we are passed might
		# be a different python instance than the ones we stored in self.__views. find the original
		# python instance so we can access view.__pendingUpdate on it.
		view, = [ v for v in self.__views if v.isSame( view ) ]
			
		# Ideally we might want the view to be doing the update automatically whenever it
		# wants, rather than using updateRequestSignal() to request a call back in to update().
		# Currently we can't do that because the Views are implemented in C++ and might spawn
		# threads which need to call back into Python - leading to deadlock if the GIL hasn't
		# been released previously. The binding for View._update() releases the GIL for
		# us to work around that problem - another solution might be to release the GIL in all
		# bindings which might eventually trigger a viewer update, but that could
		# be nearly anything.
		if not view.__pendingUpdate :
			view.__pendingUpdate = True
			if view.isSame( self.__currentView ) :
				GafferUI.EventLoop.executeOnUIThread( self.__update )
			
GafferUI.EditorWidget.registerType( "Viewer", Viewer )

##########################################################################
# Toolbar implementation
##########################################################################

## \todo We could turn this into a general class useable for all nodes and
# not just views. Then we could use it to create useful toolbars for the node
# being viewed too. If we do that we should have a pure abstract class called
# NodeToolbar and then a derived class called StandardToolbar which does the
# job 90% of the time, as we do with NodeUI and StandardNodeUI.
class _ViewToolbar( GafferUI.Widget ) :

	def __init__( self, view, **kw ) :
	
		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		
		GafferUI.Widget.__init__( self, self.__row, **kw )
		
		for plug in view.children( Gaffer.Plug.staticTypeId() ) :
			
			if plug.getName().startswith( "__" ) :
				continue
			
			widget = GafferUI.PlugValueWidget.create( plug )
			if widget is None :
				continue
							
			if ( isinstance( widget, GafferUI.PlugValueWidget )
			     and not widget.hasLabel()
			     and GafferUI.Metadata.plugValue( plug, "label" ) != ""
			) :
				widget = GafferUI.PlugWidget( widget )
				
			self.__row.append( widget )
		
		self.__row.insert( 0, GafferUI.Spacer( IECore.V2i( 1, 1 ) ), expand = True )

GafferUI.PlugValueWidget.registerCreator( GafferUI.View.staticTypeId(), "in", None )
GafferUI.PlugValueWidget.registerCreator( GafferUI.View.staticTypeId(), "user", None )
