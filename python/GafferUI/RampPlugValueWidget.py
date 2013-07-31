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

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

class RampPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :
		
		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 )
		
		GafferUI.PlugValueWidget.__init__( self, column, plug, **kw )

		with column :
			
			self.__splineWidget = GafferUI.SplineWidget()
			self.__splineWidget.setDrawMode( self.__splineWidget.DrawMode.Ramp )
			self.__splineWidget._qtWidget().setMinimumHeight( 50 )
			
			self.__slider = GafferUI.Slider()
			self.__slider.setSizeEditable( True )
			self.__slider.setMinimumSize( 2 )
			self.__positionsChangedConnection = self.__slider.positionChangedSignal().connect( Gaffer.WeakMethod( self.__positionsChanged ) )
			self.__indexRemovedConnection = self.__slider.indexRemovedSignal().connect( Gaffer.WeakMethod( self.__indexRemoved ) )
			self.__selectedIndexChangedConnection = self.__slider.selectedIndexChangedSignal().connect( Gaffer.WeakMethod( self.__selectedIndexChanged ) )

			self.__lastPositionChangedReason = None
			self.__positionsMergeGroupId = 0

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
			
				self.__positionLabel = GafferUI.LabelPlugValueWidget( plug.pointXPlug( 0 ) )
				self.__positionField = GafferUI.NumericPlugValueWidget( plug.pointXPlug( 0 ) )
				
				self.__valueLabel = GafferUI.LabelPlugValueWidget( plug.pointYPlug( 0 ) )
				self.__valueField = GafferUI.ColorPlugValueWidget( plug.pointYPlug( 0 ) )
						
		self.setPlug( plug )

	def setPlug( self, plug ) :
		
		GafferUI.PlugValueWidget.setPlug( self, plug )
		
		self.__slider.setSelectedIndex( 0 )	

	def getToolTip( self ) :
	
		result = GafferUI.PlugValueWidget.getToolTip( self )
		
		if self.getPlug() is not None :
			result += "<ul>"
			result += "<li>Click empty space in slider to add handle"
			result += "<li>Click handle to select"
			result += "<li>Delete to remove selected handle"
			result += "<li>Cursor left/right to nudge selected handle"
			result += "<ul>"

		return result
	
	def _updateFromPlug( self ) :
	
		plug = self.getPlug()
		with self.getContext() :
			
			self.__splineWidget.setSpline( plug.getValue() )
			
			positions = []
			for i in range( 0, plug.numPoints() ) :
				positions.append( plug.pointXPlug( i ).getValue() )
			
			with Gaffer.BlockedConnection( self.__positionsChangedConnection ) :
				self.__slider.setPositions( positions )
	
	def __positionsChanged( self, slider, reason ) :
		
		if not slider.changesShouldBeMerged( self.__lastPositionChangedReason, reason ) :
			self.__positionsMergeGroupId += 1
		self.__lastPositionChangedReason = reason
		
		plug = self.getPlug()
		with Gaffer.UndoContext(
			plug.ancestor( Gaffer.ScriptNode.staticTypeId() ),
			mergeGroup = "RampPlugValudWidget%d%d" % ( id( self, ), self.__positionsMergeGroupId )
		) :
		
			if len( slider.getPositions() ) == plug.numPoints() :
				# the user has moved an existing point on the slider
				for index, position in enumerate( slider.getPositions() ) :
					plug.pointXPlug( index ).setValue( position )			
			else :
				# a new position was added on the end by the user clicking
				# on an empty area of the slider.
				numPoints = plug.numPoints()
				assert( len( slider.getPositions() ) == numPoints + 1 )
				spline = plug.getValue()
				position = slider.getPositions()[numPoints]
				plug.addPoint()
				plug.pointXPlug( numPoints ).setValue( position )
				plug.pointYPlug( numPoints ).setValue( spline( position ) )	
	
	def __indexRemoved( self, slider, index ) :
	
		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
			self.getPlug().removePoint( index )			
	
	def __selectedIndexChanged( self, slider ) :
	
		index = slider.getSelectedIndex()
		if self.getPlug() is not None and index is not None :
			pointPlug = self.getPlug().pointPlug( index )
			self.__positionLabel.setPlug( pointPlug["x"] )
			self.__positionField.setPlug( pointPlug["x"] )
			self.__valueLabel.setPlug( pointPlug["y"] )
			self.__valueField.setPlug( pointPlug["y"] )
			
		else :
			self.__positionLabel.setPlug( None )
			self.__positionField.setPlug( None )
			self.__valueLabel.setPlug( None )
			self.__valueField.setPlug( None )
			
		self.__positionLabel.label().setText( "Position" )
		self.__valueLabel.label().setText( "Value" )
			
# we don't register this automatically for any plugs, as it takes up a lot of room
# in the node editor. this means the SplinePlugValueWidget will be used instead, and
# that will launch a dialogue containing a RampPlugValueWidget when appropriate. for
# nodes which want a large editor directly in the node editor, the RampPlugValueWidget
# can be registered directly for specific plugs.
