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

import imath
import IECore

import Gaffer
import GafferUI

class RampPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__rampWidget = GafferUI.RampWidget()

		GafferUI.PlugValueWidget.__init__( self, self.__rampWidget, plug, **kw )

		self.__rampWidget._qtWidget().setFixedHeight( 20 )

		self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )

		self.__editorWindow = None

		self.setPlug( plug )

	def setPlug( self, plug ) :

		GafferUI.PlugValueWidget.setPlug( self, plug )

		if isinstance( plug, ( Gaffer.RampfColor3fPlug, Gaffer.RampfColor4fPlug ) ) :
			self.__rampWidget.setDrawMode( GafferUI.RampWidget.DrawMode.Ramp )
		else :
			self.__rampWidget.setDrawMode( GafferUI.RampWidget.DrawMode.Splines )

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )

		self.__rampWidget.setHighlighted( highlighted )

	def _updateFromValues( self, values, exception ) :

		if values :
			assert( len( values ) == 1 )
			self.__rampWidget.setRamp( values[0] )
		else :
			self.__rampWidget.setRamp(
				IECore.Rampff( [ ( 0, 0.3 ), ( 1, 0.3 ) ], IECore.RampInterpolation.Linear ),
			)

	def __buttonPress( self, button, event ) :

		if event.buttons & event.Buttons.Left :

			_RampPlugValueDialogue.acquire( self.getPlug() )
			return True

for plugType in ( Gaffer.RampffPlug, Gaffer.RampfColor3fPlug, Gaffer.RampfColor4fPlug ) :

	GafferUI.PlugValueWidget.registerType( plugType, RampPlugValueWidget )
	Gaffer.Metadata.registerValue( plugType, "interpolation", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )
	for name, value in sorted( IECore.RampInterpolation.names.items() ):
		Gaffer.Metadata.registerValue( plugType, "interpolation", "preset:" + name, value )
	Gaffer.Metadata.registerValue( plugType, "p[0-9]*.x", "labelPlugValueWidget:showValueChangedIndicator", False )
	Gaffer.Metadata.registerValue( plugType, "p[0-9]*.y", "labelPlugValueWidget:showValueChangedIndicator", False )

## \todo See comments for `ColorSwatchPlugValueWidget._ColorPlugValueDialogue`.
# I think the best approach is probably to move the `acquire()` mechanism to the
# main layout class when we do an overhaul of that system.
class _RampPlugValueDialogue( GafferUI.Dialogue ) :

	def __init__( self, plug ) :

		GafferUI.Dialogue.__init__(
			self,
			plug.relativeName( plug.ancestor( Gaffer.ScriptNode ) )
		)

		self.__plug = plug
		self.setChild( _RampPlugEditValueWidget( plug ) )

		## \todo Perhaps if `acquire()` were to be a shared central
		# mechanism, this handling should be done in `acquire()`
		# instead of in each of the individual dialogues? Perhaps
		# `acquire()` should even be responsible for building the
		# dialogues, so it's able to build a dialogue around any
		# PlugValueWidget?
		plug.parentChangedSignal().connect( Gaffer.WeakMethod( self.__destroy ) )
		plug.node().parentChangedSignal().connect( Gaffer.WeakMethod( self.__destroy ) )

	@classmethod
	def acquire( cls, plug ) :

		script = plug.node().scriptNode()
		scriptWindow = GafferUI.ScriptWindow.acquire( script )

		for window in scriptWindow.childWindows() :
			if isinstance( window, cls ) and window.__plug == plug :
				window.setVisible( True )
				return window

		window = cls( plug )
		scriptWindow.addChildWindow( window, removeOnClose = True )
		window.setVisible( True )

		return window

	def __destroy( self, *unused ) :

		self.parent().removeChild( self )

# Private widget class that we open in a popup window when we need to edit a ramp.
class _RampPlugEditValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, column, plug, **kw )

		with column :
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
				GafferUI.Label( "Display Mode" )
				drawModeWidget = GafferUI.MultiSelectionMenu( allowMultipleSelection = False, allowEmptySelection = False )
				drawModeWidget.append( "Ramp" )
				drawModeWidget.append( "Curves" )
				drawModeWidget.setSelection( "Ramp" )
				drawModeWidget.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__drawModeChanged ) )

				GafferUI.Spacer( imath.V2i( 0 ), parenting = { "expand" : True } )
				GafferUI.PlugWidget( GafferUI.PlugValueWidget.create( plug["interpolation"] ) )

			self.__rampWidget = GafferUI.RampWidget()
			if isinstance( plug, ( Gaffer.RampfColor3fPlug, Gaffer.RampfColor4fPlug ) ) :
				self.__rampWidget.setDrawMode( self.__rampWidget.DrawMode.Ramp )
			else:
				self.__rampWidget.setDrawMode( self.__rampWidget.DrawMode.Splines )
			self.__rampWidget._qtWidget().setMinimumHeight( 50 )

			self.__slider = GafferUI.Slider()
			self.__slider.setMinimumSize( 2 )
			self.__positionsChangedConnection = self.__slider.valueChangedSignal().connect( Gaffer.WeakMethod( self.__positionsChanged ) )
			self.__slider.indexRemovedSignal().connect( Gaffer.WeakMethod( self.__indexRemoved ) )
			self.__slider.selectedIndexChangedSignal().connect( Gaffer.WeakMethod( self.__selectedIndexChanged ) )

			self.__lastPositionChangedReason = None
			self.__positionsMergeGroupId = 0

			with GafferUI.ListContainer(
				orientation = GafferUI.ListContainer.Orientation.Horizontal if isinstance( plug.pointYPlug( 0 ), Gaffer.FloatPlug ) else GafferUI.ListContainer.Orientation.Vertical,
				spacing = 4
			) :

				self.__positionLabel = GafferUI.LabelPlugValueWidget(
					plug.pointXPlug( 0 ),
					parenting = { "verticalAlignment" : GafferUI.VerticalAlignment.Top }
				)
				self.__positionField = GafferUI.NumericPlugValueWidget(
					plug.pointXPlug( 0 ),
					parenting = { "verticalAlignment" : GafferUI.VerticalAlignment.Top }
				)

				self.__valueLabel = GafferUI.LabelPlugValueWidget(
					plug.pointYPlug( 0 ),
					parenting = { "verticalAlignment" : GafferUI.VerticalAlignment.Top }
				)
				if isinstance( plug.pointYPlug( 0 ), Gaffer.FloatPlug ):
					self.__valueField = GafferUI.NumericPlugValueWidget(
						plug.pointYPlug( 0 ),
						parenting = { "verticalAlignment" : GafferUI.VerticalAlignment.Top }
					)
				else:
					self.__valueField = GafferUI.ColorPlugValueWidget(
						plug.pointYPlug( 0 ),
						parenting = { "verticalAlignment" : GafferUI.VerticalAlignment.Top }
					)
					self.__valueField.setColorChooserVisible( True )

		self.setPlug( plug )

	def __drawModeChanged( self, drawModeWidget ) :
		name = drawModeWidget.getSelection()[0]
		self.__rampWidget.setDrawMode( self.__rampWidget.DrawMode.Ramp if name == "Ramp" else self.__rampWidget.DrawMode.Splines )

	def setPlug( self, plug ) :

		GafferUI.PlugValueWidget.setPlug( self, plug )

		self.__slider.setSelectedIndex( 0 )

	def getToolTip( self ) :

		result = GafferUI.PlugValueWidget.getToolTip( self )

		if self.getPlug() is not None :
			if result :
				result += "\n\n"
			result += "## Actions\n\n"
			result += "- Click empty space in slider to add handle\n"
			result += "- Click handle to select\n"
			result += "- Delete to remove selected handle\n"
			result += "- Cursor left/right to nudge selected handle\n"

		return result

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		return [
			{
				"ramp" : p.getValue(),
				# We can't get these positions from `spline`, because we need
				# them to have the same order as the point plugs.
				"positions" : [ p.pointXPlug( i ).getValue() for i in range( 0, p.numPoints() ) ],
			}
			for p in plugs
		]

	def _updateFromValues( self, values, exception ) :

		assert( len( values ) < 2 )
		if len( values ) :
			self.__rampWidget.setRamp( values[0]["ramp"] )
			with Gaffer.Signals.BlockedConnection( self.__positionsChangedConnection ) :
				self.__slider.setValues( values[0]["positions"] )

	def _updateFromEditable( self ) :

		plug = self.getPlug()
		self.__slider.setSizeEditable( not ( plug.getInput() or
			plug.direction() == Gaffer.Plug.Direction.Out or Gaffer.MetadataAlgo.readOnly( plug )
		) )

	def __positionsChanged( self, slider, reason ) :

		if not slider.changesShouldBeMerged( self.__lastPositionChangedReason, reason ) :
			self.__positionsMergeGroupId += 1
		self.__lastPositionChangedReason = reason

		plug = self.getPlug()
		with Gaffer.UndoScope(
			plug.ancestor( Gaffer.ScriptNode ),
			mergeGroup = "RampPlugValudWidget%d%d" % ( id( self, ), self.__positionsMergeGroupId )
		) :

			if len( slider.getValues() ) == plug.numPoints() :
				rejected = False
				# the user has moved an existing point on the slider
				for index, position in enumerate( slider.getValues() ) :
					if plug.pointXPlug( index ).getValue() != position :
						curPlug = plug.pointXPlug( index )
						if curPlug.settable() and not Gaffer.MetadataAlgo.readOnly( curPlug ):
							curPlug.setValue( position )
						else:
							rejected = True

				if rejected :
					# Do immediate (non-lazy) update to get slider position back
					# to where it should be, without any flickering.
					self._requestUpdateFromValues( lazy = False )
			else :
				# a new position was added on the end by the user clicking
				# on an empty area of the slider.
				numPoints = plug.numPoints()
				assert( len( slider.getValues() ) == numPoints + 1 )
				evaluator = plug.getValue().evaluator()
				position = slider.getValues()[numPoints]
				plug.addPoint()
				plug.pointXPlug( numPoints ).setValue( position )
				plug.pointYPlug( numPoints ).setValue( evaluator( position ) )

	def __indexRemoved( self, slider, index ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
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
