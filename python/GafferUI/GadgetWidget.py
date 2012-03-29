##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

from __future__ import with_statement

import IECore

import Gaffer
import GafferUI
from GLWidget import GLWidget
from _GafferUI import ButtonEvent, ModifiableEvent, ContainerGadget, DragDropEvent, KeyEvent

# import lazily to improve startup of apps which don't use GL functionality
GL = Gaffer.lazyImport( "OpenGL.GL" )
IECoreGL = Gaffer.lazyImport( "IECoreGL" )

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

## The GadgetWidget class provides a means of
# hosting a Gadget within a Widget based interface.
#
# Camera motion is achieved by holding down Alt and clicking
# and dragging. Use the left button for tumbling, the middle mouse button
# for tracking and the right mouse button for dollying.
#
## \todo The camera movement should be coming from somewhere else - some kind
# of ViewportGadget or summink?
class GadgetWidget( GafferUI.GLWidget ) :

	CameraMode = IECore.Enum.create( "None", "Mode2D", "Mode3D" )

	def __init__( self, gadget=None, bufferOptions=set(), cameraMode=CameraMode.Mode2D, **kw ) :
		
		GLWidget.__init__( self, bufferOptions, **kw )

		# Force the IECoreGL lazy loading to kick in /now/. Otherwise we can get IECoreGL objects
		# being returned from the GafferUIBindings without the appropriate boost::python converters
		# having been registered first.
		IECoreGL.Renderer
		
		## \todo Decide if/how this goes in the public API
		self._qtWidget().setMouseTracking( True )		
		
		self.__requestedDepthBuffer = self.BufferOptions.Depth in bufferOptions

		self.__keyPressConnection = self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )
		self.__keyReleaseConnection = self.keyReleaseSignal().connect( Gaffer.WeakMethod( self.__keyRelease ) )
		self.__buttonPressConnection = self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.__buttonReleaseConnection = self.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ) )
		self.__buttonDoubleClickConnection = self.buttonDoubleClickSignal().connect( Gaffer.WeakMethod( self.__buttonDoubleClick ) )
		self.__mouseMoveConnection = self.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__mouseMove ) )
		self.__wheelConnection = self.wheelSignal().connect( Gaffer.WeakMethod( self.__wheel ) )
		
		self.__camera = IECore.Camera()
		self.__cameraController = IECore.CameraController( self.__camera )
		self.__cameraInMotion = False
				
		self.setCameraMode( cameraMode )
		self.setBackgroundColor( IECore.Color3f( 0 ) )
		self.setGadget( gadget )
						
		self._qtWidget().installEventFilter( _eventFilter )
		
	def setGadget( self, gadget ) :
	
		self.__gadget = gadget
		self.__lastButtonPressGadget = None
		self.__lastButtonPressEvent = None
		self.__dragDropEvent = None
		self.__enteredGadgets = []
		self.__dragEnteredGadgets = []
		
		if self.__gadget :
			self.__renderRequestConnection = self.__gadget.renderRequestSignal().connect( Gaffer.WeakMethod( self.__renderRequest ) )
		else :
			self.__renderRequestConnection = None
			
		framingBound = self._framingBound()
		if not framingBound.isEmpty() :
			self.__cameraController.frame( framingBound )
			
		self._redraw()
		
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
	# Yep. It should be in the Style class, and there should be no methods
	# like this on any Widgets at all.
	def setBackgroundColor( self, color ) :
	
		self.__backgroundColor = color
	
	def getBackgroundColor( self ) :
	
		return self.__backgroundColor
	
	## Returns a list of Gadgets below the specified position.
	# The first Gadget in the list will be the frontmost, determined either by the
	# depth buffer if it exists or the drawing order if it doesn't.
	def gadgetsAt( self, position ) :
	
		assert( isinstance( position, ( IECore.V2f, IECore.V2i ) ) )
	
		return self.__select( position )
	
	## Frames the specified bounding box so it is entirely visible in the Widget.
	# \todo I think the entire camera management needs to be shifted to a ViewportGadget.
	def frame( self, bound, viewDirection=None, upVector=IECore.V3f( 0, 1, 0 ) ) :
	
		if viewDirection is not None :
			self.__cameraController.frame( bound, viewDirection, upVector )		
		else :
			self.__cameraController.frame( bound )
		
		self._redraw()
		
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
		GL.glClearColor( bg[0], bg[1], bg[2], 0.0 )
		GL.glClearDepth( 1.0 )
		GL.glClear( GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT )
			  
		IECoreGL.ToGLCameraConverter( self.__camera ).convert().render( None )
		IECoreGL.State.bindBaseState()
		IECoreGL.State.defaultState().bind()
		self.__gadget.render()
			
	def __renderRequest( self, gadget ) :
	
		# the gadget we're holding has requested to be rerendered.
		self._redraw()
			
	def __buttonPress( self, widget, event ) :
					
		if event.modifiers & ModifiableEvent.Modifiers.Alt :
			return self.__cameraButtonPress( event );

		gadgets = self.__select( event )
		self.__eventToGadgetSpace( event )
				
		gadget, result = self.__dispatchEvent( gadgets, "buttonPressSignal", event )
		if result :
			self.__lastButtonPressGadget = gadget
			self.__lastButtonPressEvent = event
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
			self.__dispatchEnterLeaveEvents( gadgets, self.__dragDropEvent )
			self.__dispatchEnterLeaveEvents( gadgets, event )	
			self.__dragDropEvent = None
			
		elif self.__lastButtonPressGadget :
			
			self.__dispatchEvent( self.__lastButtonPressGadget, "buttonReleaseSignal", event, dispatchToAncestors=False )
			self.__lastButtonPressGadget = None
			
		return True
		
	def __buttonDoubleClick( self, widget, event ) :
				
		gadgets = self.__select( event )
		self.__eventToGadgetSpace( event )
				
		gadget, result = self.__dispatchEvent( gadgets, "buttonDoubleClickSignal", event )
		return result
		
	def __mouseMove( self, widget, event ) :
	
		if not self.__gadget :
			return True
				
		if self.__cameraInMotion :
			return self.__cameraMotion( event );

		gadgets = self.__select( event )
		self.__eventToGadgetSpace( event )

		if self.__lastButtonPressGadget and not self.__dragDropEvent :
						
			# try to start a new drag. we do this using the position at which the button was initially pressed rather
			# than the current position. if starting the drag succeeds then we'll immediately send a drag update
			# with the current position.
			dragDropEvent = DragDropEvent( event.buttons, self.__lastButtonPressEvent.line, event.modifiers )
			dragDropEvent.source = self.__lastButtonPressGadget
			g, d = self.__dispatchEvent( self.__lastButtonPressGadget, "dragBeginSignal", dragDropEvent, dispatchToAncestors=False )
			if d :
				dragDropEvent.data = d
				self.__dragDropEvent = dragDropEvent
				
			self.__lastButtonPressGadget = None
			self.__lastButtonPressEvent = None
			
		if self.__dragDropEvent :
		
			# update an existing drag
			
			self.__dragDropEvent.line = event.line
			self.__dragDropEvent.buttons = event.buttons
			self.__dragDropEvent.modifiers = event.modifiers
			self.__dispatchEvent( self.__dragDropEvent.source, "dragUpdateSignal", self.__dragDropEvent, dispatchToAncestors=False )
			self.__dispatchEnterLeaveEvents( gadgets, self.__dragDropEvent )
		
		else :
		
			self.__dispatchEnterLeaveEvents( gadgets, event )			
		
		return True
		
	def __keyPress( self, widget, event ) :
		
		if not self.__gadget :
			return True
		
		# "F" for framing	
		if event.key=="F" :
			bound = self._framingBound()
			if not bound.isEmpty() :
				self.frame( bound )
			return True
				
		# pass the key to the gadget
		result = self.__dispatchEvent( self.getGadget(), "keyPressSignal", event )
		
		return True if result[1] else False

	def __keyRelease( self, widget, event ) :
		
		if not self.__gadget :
			return True
		
		# pass the key to the gadget - we really need a focus model for gadgets so
		# we can be smarter here
		result = self.__dispatchEvent( self.getGadget(), "keyReleaseSignal", event )
		
		return True if result[1] else False
	
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
			for a in self.__ancestors( gadget ) :
				
				handler, result = self.__dispatchEvent( a, signalName, gadgetEvent, dispatchToAncestors=False, _leafGadget=gadget )
				if result :
					return handler, result
					
			return None, None
		
		## Otherwise it's just a single Gadget to despatch directly to.
		
		gadget = gadgetOrGadgets
		
		if hasattr( gadgetEvent, "line" ) :
				
			# Transform into Gadget space
			untransformedLine = IECore.LineSegment3f( gadgetEvent.line )
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

	def __dispatchEnterLeaveEvents( self, gadgets, event ) :
		
		if isinstance( event, GafferUI.DragDropEvent ) :
			enteredGadgets = self.__dragEnteredGadgets
			enterSignal = "dragEnterSignal"
			leaveSignal = "dragLeaveSignal"
		else :
			enteredGadgets = self.__enteredGadgets
			enterSignal = "enterSignal"
			leaveSignal = "leaveSignal"
		
		gadget = gadgets[0] if gadgets else None
				
		# emit leave signals for anything previously entered and now no longer
		# in the hierarchy of the current gadget.
		for g in reversed( enteredGadgets ) :
			if not ( g.isSame( gadget ) or g.isAncestorOf( gadget ) ) :
				self.__dispatchEvent( g, leaveSignal, event, dispatchToAncestors=False )
		
		# emit enter signals for anything in the current hierarchy which hasn't
		# received an enter event yet.
		ancestors = self.__ancestors( gadget )
		for ancestor in ancestors :
			enteredAlready = False
			for g in enteredGadgets :
				if g.isSame( ancestor ) :
					enteredAlready = True
					break
			if not enteredAlready :
				self.__dispatchEvent( ancestor, enterSignal, event, dispatchToAncestors=False )
		
		# remember what we've entered
		enteredGadgets[:] = ancestors
		
	def __ancestors( self, gadget ) :
	
		## \todo It'd be nice to bind an ancestors() method so we get this list more easily. It might
		# be nice to implement custom iterators on the c++ side to make it easy to traverse the graph too - can
		# we use boost::graph stuff to help with that?
		ancestors = []
		while gadget :
			ancestors.insert( 0, gadget )
			gadget = gadget.parent()
		
		return ancestors
		
	## Returns a list of Gadgets under the screen x,y position specified by eventOrPosition.
	# The first Gadget in the list will be the frontmost, determined either by the
	# depth buffer if it exists or the drawing order if it doesn't.
	def __select( self, eventOrPosition ) :
	
		if self.__gadget is None:
			return []
				
		self._qtWidget().context().makeCurrent()
				
		viewportSize = IECore.V2f( self._qtWidget().width(), self._qtWidget().height() )
		if isinstance( eventOrPosition, GafferUI.Event ) :
			regionCentre = IECore.V2f( eventOrPosition.line.p1.x, eventOrPosition.line.p1.y ) / viewportSize
		else :
			regionCentre = IECore.V2f( eventOrPosition[0], eventOrPosition[1] ) / viewportSize
		regionSize = IECore.V2f( 2 ) / viewportSize
		
		region = IECore.Box2f( regionCentre - regionSize/2, regionCentre + regionSize/2 )
		
		IECoreGL.ToGLCameraConverter( self.__camera ).convert().render( None )

		selector = IECoreGL.Selector()		
		selector.begin( region )

		GL.glClearColor( 0.0, 0.0, 0.0, 0.0 );
		GL.glClearDepth( 1.0 )
		GL.glClear( GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT );
		
		self.__gadget.render()
		
		selection = selector.end()
		
		if not len( selection ) :
			# This causes events to be sent to the top level gadget even when they
			# don't really hit any particular child gadget.
			return [ self.getGadget() ]
		
		if self.__requestedDepthBuffer :
			selection.sort()
		else :
			selection.reverse()
				
		gadgets = [ GafferUI.Gadget.select( s.name.value() ) for s in selection ]
		return [ g for g in gadgets if g is not None ]
	
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
		
	def __wheel( self, widget, event ) :
	
		position = IECore.V2i( int( event.line.p0.x ), int( event.line.p0.y ) )
		self.__cameraController.motionStart( IECore.CameraController.MotionType.Dolly, position )

		position.x += int( event.wheelRotation * self.size().x / 200.0  )
		
		self.__cameraController.motionUpdate( position )

		self.__cameraController.motionEnd( position )
		
		self._redraw()

	## Converts event coordinates from Qt space into Gadget space
	def __eventToGadgetSpace( self, event ) :
		
		event.line.p0, event.line.p1 = self.__cameraController.unproject( IECore.V2i( int( event.line.p0.x ), int( event.line.p0.y ) ) )
		
## Used to make the tooltips dependent on which gadget is under the mouse
class _EventFilter( QtCore.QObject ) :

	def __init__( self ) :
	
		QtCore.QObject.__init__( self )
		
	def eventFilter( self, qObject, qEvent ) :
	
		if qEvent.type()==QtCore.QEvent.ToolTip :
		
			widget = GafferUI.Widget._owner( qObject )
			
			assert( isinstance( widget, GadgetWidget ) )
			
			event = GafferUI.ButtonEvent(
				GafferUI.ButtonEvent.Buttons.Left,
				IECore.LineSegment3f(
				IECore.V3f( qEvent.x(), qEvent.y(), 1 ),
					IECore.V3f( qEvent.x(), qEvent.y(), 0 )
				),
				0.0,
				GafferUI.ButtonEvent.Modifiers.None,
			)
			
			gadgets = widget._GadgetWidget__select( event )
			
			toolTip = None
			for g in gadgets :
				while g is not None :
					toolTip = g.getToolTip()
					if toolTip :
						break
					g = g.parent()
				if toolTip :
					break
						
			QtGui.QToolTip.showText( qEvent.globalPos(), toolTip if toolTip is not None else "", qObject )

			return True
			
		return False

# this single instance is used by all widgets
_eventFilter = _EventFilter()
