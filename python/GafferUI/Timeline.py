##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )

## The Timeline presents a time slider which edits the frame
# entry of a context.
class Timeline( GafferUI.EditorWidget ) :

	def __init__( self, scriptNode, **kw ) :
	
		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, borderWidth = 4, spacing = 2 )
	
		GafferUI.EditorWidget.__init__( self, self.__row, scriptNode, **kw )
		
		self.__playTimer = QtCore.QTimer()
		self.__playTimer.timeout.connect( Gaffer.WeakMethod( self.__playTimeout ) )
							
		with self.__row :
			
			self.__visibilityButton = GafferUI.Button( image="timeline3.png", hasFrame=False )
			self.__visibilityButtonClickedConnection = self.__visibilityButton.clickedSignal().connect( Gaffer.WeakMethod( self.__visibilityButtonClicked ) )
			
			self.__scriptRangeStart = GafferUI.NumericPlugValueWidget( scriptNode["frameRange"]["start"] )
			self.__scriptRangeStart.numericWidget().setCharacterWidth( 4 )
			self.__scriptRangeStart.setToolTip( self.__scriptRangeStart.getPlug().fullName() )

			self.__sliderRangeStart = GafferUI.NumericWidget( scriptNode["frameRange"]["start"].getValue() )
			self.__sliderRangeStart.setCharacterWidth( 4 )
			self.__sliderRangeStart.setToolTip( "Slider minimum" )
			self.__sliderRangeStartChangedConnection = self.__sliderRangeStart.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__sliderRangeChanged ) )
			
			self.__slider = GafferUI.NumericSlider(
				value = self.getContext().getFrame(),
				min = float( scriptNode["frameRange"]["start"].getValue() ),
				max = float( scriptNode["frameRange"]["end"].getValue() ),
				expand = 1
			)
			self.__sliderValueChangedConnection = self.__slider.valueChangedSignal().connect( Gaffer.WeakMethod( self.__sliderChanged ) )

			self.__startButton = GafferUI.Button( image = "timelineStart.png", hasFrame=False )
			self.__startButtonClickedConnection = self.__startButton.clickedSignal().connect( Gaffer.WeakMethod( self.__startOrEndButtonClicked ) )
			
			self.__playPause = GafferUI.Button( image = "timelinePlay.png", hasFrame=False )
			self.__playPauseClickedConnection = self.__playPause.clickedSignal().connect( Gaffer.WeakMethod( self.__playPauseClicked ) )

			self.__endButton = GafferUI.Button( image = "timelineEnd.png", hasFrame=False )
			self.__endButtonClickedConnection = self.__endButton.clickedSignal().connect( Gaffer.WeakMethod( self.__startOrEndButtonClicked ) )
			
			self.__frame = GafferUI.NumericWidget( self.getContext().getFrame() )
			self.__frame.setCharacterWidth( 5 )
			self.__frame.setToolTip( "Current frame" )
			self.__frameChangedConnection = self.__frame.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__frameChanged ) )
			
			self.__sliderRangeEnd = GafferUI.NumericWidget( scriptNode["frameRange"]["end"].getValue() )
			self.__sliderRangeEnd.setCharacterWidth( 4 )
			self.__sliderRangeEnd.setToolTip( "Slider maximum" )
			self.__sliderRangeEndChangedConnection = self.__sliderRangeEnd.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__sliderRangeChanged ) )

			self.__scriptRangeEnd = GafferUI.NumericPlugValueWidget( scriptNode["frameRange"]["end"] )	
			self.__scriptRangeEnd.numericWidget().setCharacterWidth( 4 )
			self.__scriptRangeEnd.setToolTip( self.__scriptRangeEnd.getPlug().fullName() )
	
		self.__scriptNodePlugSetConnection = scriptNode.plugSetSignal().connect( Gaffer.WeakMethod( self.__scriptNodePlugSet ) )
	
	def _updateFromContext( self, modifiedItems ) :
		
		if "frame" not in modifiedItems :
			return
		
		# update the frame counter and slider position
		with Gaffer.BlockedConnection( [ self.__frameChangedConnection, self.__sliderValueChangedConnection ] ) :
			self.__frame.setValue( self.getContext().getFrame() )
			self.__slider.setValue( self.getContext().getFrame() )
	
	def __sliderRangeChanged( self, widget ) :
			
		assert( widget is self.__sliderRangeStart or widget is self.__sliderRangeEnd )
		
		# clamp value within range specified by script
		value = widget.getValue()
		value = max( self.scriptNode()["frameRange"]["start"].getValue(), value )
		value = min( self.scriptNode()["frameRange"]["end"].getValue(), value )
		
		# move the other end of the range if necessary
		if widget is self.__sliderRangeStart :
			minValue = value
			maxValue = max( value, self.__sliderRangeEnd.getValue() )
		else :
			maxValue = value
			minValue = min( value, self.__sliderRangeStart.getValue() )

		self.__slider.setRange( minValue, maxValue )
		self.__sliderRangeStart.setValue( minValue )
		self.__sliderRangeEnd.setValue( maxValue )
	
	def __frameChanged( self, widget ) :
		
		assert( widget is self.__frame )
				
		frame = widget.getValue()
		frame = max( frame, self.scriptNode()["frameRange"]["start"].getValue() )
		frame = min( frame, self.scriptNode()["frameRange"]["end"].getValue() )
		
		self.__frame.setValue( frame )
		self.getContext().setFrame( frame )
	
	def __sliderChanged( self, slider, reason ) :
		
		assert( slider is self.__slider )
		## \todo Have the rounding come from NumericSlider, and allow the shift
		# modifier to choose fractional frame values.
		frame = int( self.__slider.getValue() )

		frame = max( frame, self.scriptNode()["frameRange"]["start"].getValue() )
		frame = min( frame, self.scriptNode()["frameRange"]["end"].getValue() )
		
		self.getContext().setFrame( frame )
		
	def __scriptNodePlugSet( self, plug ) :
	
		combineFunction = None
		if plug.isSame( self.scriptNode()["frameRange"]["start"] ) :
			combineFunction = max
		elif plug.isSame( self.scriptNode()["frameRange"]["end"] ) :
			combineFunction = min
		
		if combineFunction is not None :
			self.__sliderRangeStart.setValue( combineFunction( plug.getValue(), self.__sliderRangeStart.getValue() ) )
			self.__sliderRangeEnd.setValue( combineFunction( plug.getValue(), self.__sliderRangeEnd.getValue() ) )
			self.__slider.setRange( self.__sliderRangeStart.getValue(), self.__sliderRangeEnd.getValue() )
			self.getContext().setFrame( combineFunction( plug.getValue(), self.getContext().getFrame() ) )
			
	def __visibilityButtonClicked( self, button ) :
	
		assert( button is self.__visibilityButton )
		
		if self.__scriptRangeStart.getVisible() :
			self.__scriptRangeStart.setVisible( False )
			self.__scriptRangeEnd.setVisible( False )
			self.__visibilityButton.setImage( "timeline2.png" )
		elif self.__sliderRangeStart.getVisible() :
			self.__sliderRangeStart.setVisible( False )
			self.__sliderRangeEnd.setVisible( False )
			self.__visibilityButton.setImage( "timeline1.png" )
		else :
			self.__scriptRangeStart.setVisible( True )
			self.__scriptRangeEnd.setVisible( True )
			self.__sliderRangeStart.setVisible( True )
			self.__sliderRangeEnd.setVisible( True )
			self.__visibilityButton.setImage( "timeline3.png" )
	
	def __playPauseClicked( self, button ) :
	
		assert( button is self.__playPause )
		
		if self.__playTimer.isActive() :
			# we want to pause
			self.__playTimer.stop()
			button.setImage( "timelinePlay.png" )
		else :
			self.__playTimer.start()
			button.setImage( "timelinePause.png" )
			
	def __startOrEndButtonClicked( self, button ) :
		
		self.__playTimer.stop()
		self.__playPause.setImage( "timelinePlay.png" )
		
		if button is self.__startButton :
			self.getContext().setFrame( self.__sliderRangeStart.getValue() )
		else :
			self.getContext().setFrame( self.__sliderRangeEnd.getValue() )			
			
	def __playTimeout( self ) :
	
		frame = self.getContext().getFrame()
		frame += 1
		if frame > self.__sliderRangeEnd.getValue() :	
			frame = self.__sliderRangeStart.getValue()
			
		self.getContext().setFrame( frame )
	
	def __repr__( self ) :

		return "GafferUI.Timeline( scriptNode )"
	
GafferUI.EditorWidget.registerType( "Timeline", Timeline )
