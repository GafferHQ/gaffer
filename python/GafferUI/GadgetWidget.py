##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

from __future__ import with_statement

from OpenGL.GL import *

import IECore
import IECoreGL

import GafferUI
from GLWidget import GLWidget
from _GafferUI import ButtonEvent, ModifiableEvent, ContainerGadget, DragDropEvent, KeyEvent

## The GadgetWidget class provides a means of
# hosting a Gadget within a Widget based interface.
# Widgets are UI elements implemented using GTK, whereas
# Gadgets are implemented on top of the Cortex infrastructure.
#
# Camera motion is achieved by holding down Alt and clicking
# and dragging. Use the left button for tumbling, the middle mouse button
# for tracking and the right mouse button for dollying.
#
## \todo It feels like this could be split into two classes - one that just
# takes gtk events and turns them into GafferUI events, and one that takes
# those events and forwards them to the Gadgets appropriately, maintaining
# current drag state etc. The latter class could then be used if implementing
# other hosts.
## \todo The camera movement should be coming from somewhere else - some kind
# of ViewportGadget or summink?
class GadgetWidget( GafferUI.GLWidget ) :

	CameraMode = IECore.Enum.create( "None", "Mode2D", "Mode3D" )

	def __init__( self, gadget=None, bufferOptions=set(), cameraMode=CameraMode.Mode2D ) :
		
		GLWidget.__init__( self, bufferOptions )
				
## \todo
#		self.gtkWidget().connect( "scroll_event", self.__scroll )

		self.__requestedDepthBuffer = self.BufferOptions.Depth in bufferOptions

		self.__keyPressConnection = self.keyPressSignal().connect( self.__keyPress )
		self.__buttonPressConnection = self.buttonPressSignal().connect( self.__buttonPress )
		self.__buttonReleaseConnection = self.buttonReleaseSignal().connect( self.__buttonRelease )
		self.__mouseMoveConnection = self.mouseMoveSignal().connect( self.__mouseMove )
	
		self.__camera = IECore.Camera()
		self.__cameraController = IECore.CameraController( self.__camera )
				
		self.setCameraMode( cameraMode )
		self.setBackgroundColor( IECore.Color3f( 0 ) )
		self.setGadget( gadget )
		
		self.__lastButtonPressGadget = None
		self.__dragDropEvent = None
		
		self.__cameraInMotion = False
		
		self.__baseState = IECoreGL.State( True )
		
	def setGadget( self, gadget ) :
	
		self.__gadget = gadget
		self.__scene = None
		
		if self.__gadget :
			self.__renderRequestConnection = self.__gadget.renderRequestSignal().connect( self.__renderRequest )
		else :
			self.__renderRequestConnection = None
			
		framingBound = self._framingBound()
		if not framingBound.isEmpty() :
			self.__cameraController.frame( framingBound )
		
	def getGadget( self ) :
	
		return self.__gadget
	
	def setCameraMode( self, cameraMode ) :
	
		self.__cameraMode = cameraMode
		if cameraMode==self.CameraMode.Mode2D :
			self.__camera.parameters()["projection"] = IECore.StringData( "orthographic" )
		else :
			self.__camera.parameters()["projection"] = IECore.StringData( "perspective" )
		
		# force the controller to update
		self.__cameraController.setCamera( self.__camera )
				
	def getCameraMode( self ) :
	
		return self.__cameraMode
	
	## \todo Should there be a standard way of setting colors for all Widgets?	
	def setBackgroundColor( self, color ) :
	
		self.__backgroundColor = color
	
	def getBackgroundColor( self ) :
	
		return self.__backgroundColor
	
	## Returns the bounding box which will be framed when "f" is pressed. This
	# may be overridden in derived classes to implement more intelligent framing.
	def _framingBound( self ) :
	
		if self.__gadget :
			return self.__gadget.bound()
		else :
			return IECore.Box3f()
	
	def _resize( self, size ) :
		
		GafferUI.GLWidget._resize( self, size )
		if size.x and size.y :
			# avoid resizing if resolution has hit 0, as then
			# the reframing maths breaks down
			self.__cameraController.setResolution( size )
	
	def _draw( self ) :
	
		## \todo bg = self.__backgroundColor.linearToSRGB()
		bg = IECore.Color3f( 0.3, 0.3, 0.3 )
		glClearColor( bg[0], bg[1], bg[2], 0.0 )
		glClearDepth( 1.0 )
		glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT )
			  
		self.__updateScene()
		if self.__scene :
			
			self.__scene.setCamera( IECoreGL.ToGLCameraConverter( self.__camera ).convert() )
			self.__scene.render( self.__baseState )
	
	## Returns the IECoreGL.State object used as the base display style for the
	# rendering of the held Gadget. This may be modified freely to
	# change the display style.
	def baseState( self ) :
	
		return self.__baseState
	
	def __renderRequest( self, gadget ) :
	
		# the gadget we're holding has requested to be rerendered.
		# destroy our scene so we'll have to rebuild it, and ask
		# that we're redrawn.
		self.__scene = None
		self._redraw()
			
	def __updateScene( self ) :
	
		if not self.__gadget :
			self.__scene = None
			return
			
		if self.__scene :
			return
			
		renderer = IECoreGL.Renderer()
		renderer.setOption( "gl:mode", IECore.StringData( "deferred" ) )

		with IECore.WorldBlock( renderer ) :
		
			self.__gadget.render( renderer )

		self.__scene = renderer.scene()

	def __buttonPress( self, widget, event ) :
					
		if event.modifiers & ModifiableEvent.Modifiers.Alt :
			return self.__cameraButtonPress( event );

		gadgets = self.__select( event )
		self.__eventToGadgetSpace( event )
		
		gadget, result = self.__dispatchEvent( gadgets, "buttonPressSignal", event )
		if result :
			self.__lastButtonPressGadget = gadget
			return True
		else :
			self.__lastButtonPressGadget = None
			return False

	def __buttonRelease( self, widget, event ) :
		
		if not self.__gadget :
			return True

		if self.__cameraInMotion :
			return self.__cameraButtonRelease( event );
		
		gadgets = self.__select( event )
		self.__eventToGadgetSpace( event )
		
		if self.__dragDropEvent :
		
			self.__dragDropEvent.line = event.line
			self.__dragDropEvent.buttons = event.buttons
			self.__dragDropEvent.modifiers = event.modifiers
			
			dropGadget, result = self.__dispatchEvent( gadgets, "dropSignal", self.__dragDropEvent )
			self.__dragDropEvent.destination = dropGadget
			self.__dragDropEvent.dropResult = result
			self.__dispatchEvent( self.__dragDropEvent.source, "dragEndSignal", self.__dragDropEvent, dispatchToAncestors=False )
			self.__dragDropEvent = None
			
		elif self.__lastButtonPressGadget :
			
			self.__dispatchEvent( self.__lastButtonPressGadget, "buttonReleaseSignal", event, dispatchToAncestors=False )
			self.__lastButtonPressGadget = None
			
		return True

	def __mouseMove( self, widget, event ) :
	
		if not self.__gadget :
			return True
		
		if self.__cameraInMotion :
			return self.__cameraMotion( event );

		self.__eventToGadgetSpace( event )

		if self.__lastButtonPressGadget and not self.__dragDropEvent :
						
			# try to start a new drag
			dragDropEvent = DragDropEvent( event.buttons, event.line, event.modifiers )
			dragDropEvent.source = self.__lastButtonPressGadget
			g, d = self.__dispatchEvent( self.__lastButtonPressGadget, "dragBeginSignal", dragDropEvent, dispatchToAncestors=False )
			if d :
				dragDropEvent.data = d
				self.__dragDropEvent = dragDropEvent
				
			self.__lastButtonPressGadget = None
			
		elif self.__dragDropEvent :
		
			# update an existing drag
			
			self.__dragDropEvent.line = event.line
			self.__dragDropEvent.buttons = event.buttons
			self.__dragDropEvent.modifiers = event.modifiers
			self.__dispatchEvent( self.__dragDropEvent.source, "dragUpdateSignal", self.__dragDropEvent, dispatchToAncestors=False )
		
		return True
		
	def __keyPress( self, widget, event ) :
		
		if not self.__gadget :
			return True
		
		# "F" for framing	
		if event.key=="F" :
			bound = self._framingBound()
			if not bound.isEmpty() :
				self.__cameraController.frame( bound )
				self._redraw()
			return True
				
		# pass the key to the gadget
		self.__dispatchEvent( self.getGadget(), "keyPressSignal", event )
		
		return True
	
	## Dispatches an event to a named signal on a Gadget, returning a tuple containing the
	# gadget that handled the event and the return value from the handler. A list of Gadgets
	# may be passed, in which case the event will be dispatched to them in order until it is
	# handled by one of them. If dispatchToAncestors is True, then the event will be despatched
	# to all the Gadgets from the root to the target Gadget, with the despatch terminating if
	# one of these ancestors handles the signal. Returns the gadget that handled the event and
	# the event result.
	def __dispatchEvent( self, gadgetOrGadgets, signalName, gadgetEvent, dispatchToAncestors=True, _leafGadget=None ) :
		
		## If it's a list of Gadgets call ourselves again for each element.		
		if isinstance( gadgetOrGadgets, list ) :
		
			for g in gadgetOrGadgets :
			
				handler, result = self.__dispatchEvent( g, signalName, gadgetEvent, dispatchToAncestors )
				if result :
					return handler, result
					
			return None, None
				
		## Or if we've been asked to despatch to the ancestors of a single gadget then do that.
		if dispatchToAncestors :
		
			gadget = gadgetOrGadgets
			
			## \todo It'd be nice to bind an ancestors() method so we get this list more easily. It might
			# be nice to implement custom iterators on the c++ side to make it easy to traverse the graph too - can
			# we use boost::graph stuff to help with that?
			ancestors = []
			a = gadget
			while a :
				ancestors.insert( 0, a )
				a = a.parent()
				
			for a in ancestors :
				
				handler, result = self.__dispatchEvent( a, signalName, gadgetEvent, dispatchToAncestors=False, _leafGadget=gadget )
				if result :
					return handler, result
					
			return None, None
		
		## Otherwise it's just a single Gadget to despatch directly to.
		
		gadget = gadgetOrGadgets
		
		if hasattr( gadgetEvent, "line" ) :
				
			# Transform into Gadget space
			untransformedLine = gadgetEvent.line
			m = gadget.fullTransform()
			m.invert( True )
			gadgetEvent.line *= m
		
		else :
		
			untransformedLine = None
				
		signal = getattr( gadget, signalName )()
		result = signal( _leafGadget or gadget, gadgetEvent )

		gadgetEvent.line = untransformedLine
		
		if result :
		
			return gadget, result
				
		return None, None

	## Returns a list of Gadgets under the screen x,y position specified by event.
	# The first Gadget in the list will be the frontmost, determined either by the
	# depth buffer if it exists or the drawing order if it doesn't.
	def __select( self, event ) :
	
		if not self.__scene :
			return []
		
		self._qtWidget().context().makeCurrent()
				
		viewportSize = IECore.V2f( self._qtWidget().width(), self._qtWidget().height() )
		regionCentre = IECore.V2f( event.line.p1.x, event.line.p1.y ) / viewportSize
		regionSize = IECore.V2f( 2 ) / viewportSize
		
		region = IECore.Box2f( regionCentre - regionSize/2, regionCentre + regionSize/2 )
		
		glClearColor( 0.0, 0.0, 0.0, 0.0 );
		glClearDepth( 1.0 )
		glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT );
		selection = self.__scene.select( region )
		
		if not len( selection ) :
			# This causes events to be sent to the top level gadget even when they
			# don't really hit any particular child gadget.
			return [ self.getGadget() ]
		
		if self.__requestedDepthBuffer :
			selection.sort()
		else :
			selection.reverse()
				
		result = []
		for s in selection :
			
			name = s.name.value()
			nameComponents = name.split( "." )
			g = self.__gadget
			assert( g.getName() == nameComponents[0] )
			for i in range( 1, len( nameComponents ) ) :
				g = g.getChild( nameComponents[i] )
				
			result.append( g )
				
		return result
	
	#########################################################################################################
	# stuff for controlling the camera
	#########################################################################################################
	
	def __cameraButtonPress( self, event ) :
								
		motionType = IECore.CameraController.MotionType.None
		if event.buttons==GafferUI.ButtonEvent.Buttons.Left :
			motionType = IECore.CameraController.MotionType.Tumble
		elif event.buttons==GafferUI.ButtonEvent.Buttons.Middle :
			motionType = IECore.CameraController.MotionType.Track
		elif event.buttons==GafferUI.ButtonEvent.Buttons.Right :
			motionType = IECore.CameraController.MotionType.Dolly
				
		if motionType==IECore.CameraController.MotionType.Tumble and self.__cameraMode==self.CameraMode.Mode2D :
			motionType = IECore.CameraController.MotionType.Track
				
		if motionType :
			self.__cameraController.motionStart( motionType, IECore.V2i( int( event.line.p1.x ), int( event.line.p1.y ) ) )
			self.__cameraInMotion = True
			
		return True
	
	def __cameraMotion( self, event ) :
		
		self.__cameraController.motionUpdate( IECore.V2i( int( event.line.p1.x ), int( event.line.p1.y ) ) )
		self._redraw()

		return True
		
	def __cameraButtonRelease( self, event ) :

		self.__cameraController.motionEnd( IECore.V2i( int( event.line.p1.x ), int( event.line.p1.y ) ) )
		self._redraw()
		self.__cameraInMotion = False
		return True
		
	def __scroll( self, widget, event ) :
	
		if event.direction in (gtk.gdk.SCROLL_UP, gtk.gdk.SCROLL_DOWN) :
		
			position = IECore.V2i( int(event.x), int(event.y) )
			self.__cameraController.motionStart( IECore.CameraController.MotionType.Dolly, position )
			
			if event.direction==gtk.gdk.SCROLL_UP :
				position.x += 20
			else :
				position.x -= 20
			self.__cameraController.motionUpdate( position )
			
			self.__cameraController.motionEnd( position )
			self.gtkWidget().queue_draw()
	
	## Converts event coordinates from Qt space into Gadget space
	def __eventToGadgetSpace( self, event ) :
		
		event.line.p0, event.line.p1 = self.__cameraController.unproject( IECore.V2i( int( event.line.p0.x ), int( event.line.p0.y ) ) )
		
