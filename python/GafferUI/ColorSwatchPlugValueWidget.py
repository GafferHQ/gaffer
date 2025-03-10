##########################################################################
#
#  Copyright (c) 2013, John Haddon. All rights reserved.
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

import weakref
import imath
import functools

import IECore

import Gaffer
import GafferUI
from GafferUI.PlugValueWidget import sole
from GafferUI.ColorChooserPlugValueWidget import saveDefaultOptions

class ColorSwatchPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__swatch = GafferUI.ColorSwatch()

		GafferUI.PlugValueWidget.__init__( self, self.__swatch, plugs, **kw )

		## \todo How do set maximum height with a public API?
		self.__swatch._qtWidget().setMaximumHeight( 20 )
		self.__swatch._qtWidget().setFixedWidth( 40 )

		self._addPopupMenu( self.__swatch )

		self.__swatch.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.__swatch.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ) )
		self.__swatch.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ) )
		self.__swatch.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ) )

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )

		self.__swatch.setHighlighted( highlighted )

	def _updateFromValues( self, values, exception ) :

		self.__swatch.setErrored( exception is not None )
		self.__swatch.setColor( _averageColor( values ) )

	def __buttonPress( self, widget, event ) :

		if event.buttons == event.Buttons.Left :
			return True

		return False

	def __dragBegin( self, widget, event ) :

		GafferUI.Pointer.setCurrent( "rgba" )

		return self.__swatch.getColor()

	def __dragEnd( self, widget, event ) :

		GafferUI.Pointer.setCurrent( None )

	def __buttonRelease( self, widget, event ) :

		if event.button != event.Buttons.Left :
			return False

		if not self._editable() :
			return False

		dialogue = _ColorPlugValueDialogue.acquire( self.getPlugs() )
		if dialogue.displayTransform() is not self.displayTransform() :
			# If we have been given a specific transform, then transfer it to
			# the dialogue. This is currently only necessary for `VisualiserToolUI._UntransformedColorWidget`.
			## \todo It might be better if we used plug metadata to
			# opt out of the display transform instead.
			dialogue.setDisplayTransform( self.displayTransform() )
		else :
			# The dialogue has the same display transform as us. Don't call
			# `setDisplayTransform()` because that would bake the transform in,
			# preventing updates when the transform on an ancestor is changed
			# (typically we manage display transforms at the top level on the
			# ScriptWindow).
			pass

		return True

def _averageColor( colors ) :

	if not len( colors ) :
		return imath.Color4f( 0 )

	return sum( colors ) / len( colors )

def _colorFromPlugs( plugs ) :

	# ColorSwatch only supports one colour, and doesn't have
	# an "indeterminate" state, so when we have multiple plugs
	# the best we can do is take an average.
	return _averageColor( [ p.getValue() for p in plugs ] )

## \todo Perhaps we could make this a part of the public API? Perhaps we could also make a
# PlugValueDialogue base class to share some of the work with the dialogue made by the
# SplinePlugValueWidget. Or perhaps the `acquire()` here and `NodeSetEditor.acquire()` should
# actually be functionality of CompoundEditor?
class _ColorPlugValueDialogue( GafferUI.ColorChooserDialogue ) :

	def __init__( self, plugs, parentWindow ) :

		GafferUI.ColorChooserDialogue.__init__(
			self,
			color = _colorFromPlugs( plugs )
		)

		# we use these to decide which actions to merge into a single undo
		self.__lastChangedReason = None
		self.__mergeGroupId = 0

		self.__colorChangedConnection = self.colorChooser().colorChangedSignal().connect( Gaffer.WeakMethod( self.__colorChanged ) )

		self.colorChooser().visibleComponentsChangedSignal().connect(
			functools.partial( Gaffer.WeakMethod( self.__colorChooserVisibleComponentsChanged ) )
		)
		self.colorChooser().staticComponentChangedSignal().connect(
			functools.partial( Gaffer.WeakMethod( self.__colorChooserStaticComponentChanged ) )
		)
		self.colorChooser().colorFieldVisibleChangedSignal().connect(
			functools.partial( Gaffer.WeakMethod( self.__colorChooserColorFieldVisibleChanged ) )
		)
		self.colorChooser().dynamicSliderBackgroundsChangedSignal().connect(
			functools.partial( Gaffer.WeakMethod( self.__dynamicSliderBackgroundsChanged ) )
		)
		self.colorChooser().optionsMenuSignal().connect(
			functools.partial( Gaffer.WeakMethod( self.__colorChooserOptionsMenu ) )
		)

		self.confirmButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )
		self.cancelButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )

		self.__plugs = plugs
		self.__initialValues = { p : p.getValue() for p in self.__plugs }

		nodes = { p.node() for p in self.__plugs }
		self.__plugSetConnections = [ n.plugSetSignal().connect( Gaffer.WeakMethod( self.__plugSet ) ) for n in nodes ]
		for node in nodes :
			node.parentChangedSignal().connect( Gaffer.WeakMethod( self.__destroy ) )

		plug = next( iter( self.__plugs ) )
		if len( self.__plugs ) == 1 :
			self.setTitle( plug.relativeName( plug.ancestor( Gaffer.ScriptNode ) ) )
		else :
			self.setTitle( "{} plugs".format( len( self.__plugs ) ) )

		self.__plugSet( plug )

		visibleComponents = self.__colorChooserOption( "visibleComponents" )
		if visibleComponents is not None :
			self.colorChooser().setVisibleComponents( visibleComponents )

		staticComponent = self.__colorChooserOption( "staticComponent" )
		if staticComponent is not None :
			self.colorChooser().setColorFieldStaticComponent( staticComponent )

		colorFieldVisible = self.__colorChooserOption( "colorFieldVisible" )
		if colorFieldVisible is not None :
			self.colorChooser().setColorFieldVisible( colorFieldVisible )

		dynamicSliderBackgrounds = self.__colorChooserOption( "dynamicSliderBackgrounds" )
		if dynamicSliderBackgrounds is not None :
			self.colorChooser().setDynamicSliderBackgrounds( dynamicSliderBackgrounds )

		parentWindow.addChildWindow( self, removeOnClose = True )

	@classmethod
	def acquire( cls, plugs ) :

		plug = next( iter( plugs ) )

		script = plug.node().scriptNode()
		if script is None :
			# Plug might be part of the UI rather than the node graph (e.g. a
			# Tool or View setting). Find the script.
			view = plug.ancestor( GafferUI.View )
			if view is not None :
				script = view["in"].getInput().node().scriptNode()

		assert( script is not None )
		scriptWindow = GafferUI.ScriptWindow.acquire( script )

		for window in scriptWindow.childWindows() :
			if isinstance( window, cls ) and window.__plugs == plugs :
				window.setVisible( True )
				return window

		window = _ColorPlugValueDialogue( plugs, scriptWindow )
		window.setVisible( True )

		return window

	def __plugSet( self, plug ) :

		if plug in self.__plugs :
			with Gaffer.Signals.BlockedConnection( self.__colorChangedConnection ) :
				self.colorChooser().setColor( _colorFromPlugs( self.__plugs ) )

	def __colorChanged( self, colorChooser, reason ) :

		if not GafferUI.ColorChooser.changesShouldBeMerged( self.__lastChangedReason, reason ) :
			self.__mergeGroupId += 1
		self.__lastChangedReason = reason

		with Gaffer.UndoScope(
			next( iter( self.__plugs ) ).ancestor( Gaffer.ScriptNode ),
			mergeGroup = "ColorPlugValueDialogue%d%d" % ( id( self, ), self.__mergeGroupId )
		) :

			with Gaffer.Signals.BlockedConnection( self.__plugSetConnections ) :
				for plug in self.__plugs :
					plug.setValue( self.colorChooser().getColor() )

	def __buttonClicked( self, button ) :

		if button is self.cancelButton :
			with Gaffer.UndoScope( next( iter( self.__plugs ) ).ancestor( Gaffer.ScriptNode ) ) :
				for p, v in self.__initialValues.items() :
					p.setValue( v )

		self.parent().removeChild( self )
		# Workaround for https://bugreports.qt-project.org/browse/QTBUG-26761.
		assert( not self.visible() )
		GafferUI.WidgetAlgo.keepUntilIdle( self )

	def __colorChooserOptionsMenu( self, colorChooser, menuDefinition ) :

		menuDefinition.append( "/__saveDefaultOptions__", { "divider": True, "label": "Defaults" } )

		menuDefinition.append(
			"/Save Default Dialogue Layout",
			{
				"command": functools.partial(
					saveDefaultOptions,
					colorChooser,
					"colorChooser:dialogue:",
					self.ancestor( GafferUI.ScriptWindow ).scriptNode().applicationRoot().preferencesLocation() / "__colorChooser.py"
				)
			}
		)

	def __destroy( self, *unused ) :

		self.parent().removeChild( self )

	# \todo Extract these two methods to share with `ColorChooserPlugValueWidget` which has
	# an almost identical implementation.

	def __colorChooserOptionChanged( self, keySuffix, value ) :

		for p in self.__plugs :
			Gaffer.Metadata.deregisterValue( p, "colorChooser:dialogue:" + keySuffix )
			Gaffer.Metadata.registerValue( p, "colorChooser:dialogue:" + keySuffix, value, persistent = False )

	def __colorChooserOption( self, keySuffix ) :

		return sole( Gaffer.Metadata.value( p, "colorChooser:dialogue:" + keySuffix ) for p in self.__plugs )

	def __colorChooserVisibleComponentsChanged( self, colorChooser ) :

		self.__colorChooserOptionChanged( "visibleComponents", colorChooser.getVisibleComponents() )

	def __colorChooserStaticComponentChanged( self, colorChooser ) :

		self.__colorChooserOptionChanged( "staticComponent", colorChooser.getColorFieldStaticComponent() )

	def __colorChooserColorFieldVisibleChanged( self, colorChooser ) :

		self.__colorChooserOptionChanged( "colorFieldVisible", colorChooser.getColorFieldVisible() )

	def __dynamicSliderBackgroundsChanged( self, colorChooser ) :

		self.__colorChooserOptionChanged( "dynamicSliderBackgrounds", colorChooser.getDynamicSliderBackgrounds() )
