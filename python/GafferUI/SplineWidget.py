##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

import sys

import gtk
import cairo

import IECore

import GafferUI

## This Widget simply displays an IECore.Spline object. For representation and editing
# of SplinePlugs use a SplineEditor instead.
class SplineWidget( GafferUI.Widget ) :

	DrawMode = IECore.Enum.create( "Invalid", "Ramp", "Splines" )

	def __init__( self, spline=None, drawMode=DrawMode.Splines, **kw ) :
	
		GafferUI.Widget.__init__( self, gtk.DrawingArea(), **kw )
				
		self.gtkWidget().connect( "expose-event", self.__expose )		

		self.gtkWidget().set_size_request( 20, 20 )

		self.setDrawMode( drawMode )

		if spline==None :
			spline = IECore.Splineff(
				IECore.CubicBasisf.catmullRom(),
				(
					( 0, 0 ),
					( 0, 0 ),
					( 1, 1 ),
					( 1, 1 ),
				)
			)
			
		self.setSpline( spline )

	def setSpline( self, spline ) :
	
		try :
			if spline==self.__spline :
				return
		except :
			pass
					
		self.__spline = spline
		self.__splinesToDraw = None
		self.gtkWidget().queue_draw()
		
	def getSpline( self ) :
	
		return self.__spline
		
	def setDrawMode( self, drawMode ) :
	
		try :
			if drawMode==self.__drawMode :
				return
		except :
			pass
			
		self.__drawMode = drawMode
		self.gtkWidget().queue_draw()		

	def __expose( self, gtkWidget, event ) :
	
		context = gtkWidget.window.cairo_create()
		context.rectangle( event.area.x, event.area.y, event.area.width, event.area.height )
		context.clip()
		
		if self.__drawMode==self.DrawMode.Ramp :
			self.__drawRamp( context )
		elif self.__drawMode==self.DrawMode.Splines :
			self.__drawSplines( context )
		
	def __drawRamp( self, context ) :
	
		allocation = self.gtkWidget().get_allocation()
		width = allocation.width
		height = allocation.height

		grad = cairo.LinearGradient( 0, 0, width, 0 )

		numStops = 50
		for i in range( 0, numStops ) :
			t = float( i ) / ( numStops - 1 )
			c = self.__spline( t )
			if isinstance( c, float ) :
				grad.add_color_stop_rgb( t, c, c, c )
			elif isinstance( t, c, IECore.Color3f ) :
				grad.add_color_stop_rgb( c[0], c[1], c[2] )
			elif isinstance( t, c, IECore.Color43f ) :
				grad.add_color_stop_rgba( t, c[0], c[1], c[2], c[3] )	
		
		context.set_source( grad )
		
		context.rectangle( 0, 0, width, height )
		context.fill()
				
	def __drawSplines( self, context ) :
	
		# update the evaluation of our splines if necessary
		numPoints = 50
		if not self.__splinesToDraw :
			yMin = sys.float_info.max
			yMax = sys.float_info.min
			self.__splinesToDraw = []
			interval = self.__spline.interval()
			if isinstance( self.__spline, IECore.Splineff ) :
				spline = IECore.Struct()
				spline.color = IECore.Color3f( 1 )
				spline.points = []
				for i in range( 0, numPoints ) :
					t = float( i ) / ( numPoints - 1 )
					tt = interval[0] + (interval[1] - interval[0]) * t
					c = self.__spline( tt )
					yMin = min( c, yMin )
					yMax = max( c, yMax )
					spline.points.append( IECore.V2f( t, c ) )
				self.__splinesToDraw.append( spline )
			else :
				for i in range( 0, self.__spline( 0 ).dimensions() ) :
					spline = IECore.Struct()
					if i==3 :
						spline.color = IECore.Color3f( 1 )
					else :
						c = IECore.Color3f( 0 )
						c[i] = 1
						spline.color = c
					spline.points = []
					self.__splinesToDraw.append( spline )

				for i in range( 0, numPoints ) :
					t = float( i ) / ( numPoints - 1 )
					tt = interval[0] + (interval[1] - interval[0]) * t
					c = self.__spline( tt )
					for i in range( 0, self.__spline( 0 ).dimensions() ) :
						yMin = min( yMin, c[i] )
						yMax = max( yMax, c[i] )
						splines[i].points.append( IECore.V2f( t, c[i] ) )
				
			# scale and translate into 0-1 range in y 
			yScale = 1.0 / ( yMax - yMin )
			for s in self.__splinesToDraw :
				for i in range( 0, len( s.points ) ) :
					s.points[i].y = 1.0 - (s.points[i].y - yMin) * yScale
		
		# draw the splines		
		allocation = self.gtkWidget().get_allocation()
		width = allocation.width
		height = allocation.height

		context.set_line_width( 1.0 )
		for s in self.__splinesToDraw :
			context.set_source_rgb( s.color[0], s.color[1], s.color[2] )	
			for p in s.points :
				context.line_to( p[0] * width, p[1] * height )
			context.stroke()
