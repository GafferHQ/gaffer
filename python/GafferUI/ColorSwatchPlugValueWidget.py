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

import Gaffer
import GafferUI

class ColorSwatchPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__swatch = GafferUI.ColorSwatch()

		GafferUI.PlugValueWidget.__init__( self, self.__swatch, plugs, **kw )

		## \todo How do set maximum height with a public API?
		self.__swatch._qtWidget().setMaximumHeight( 20 )

		self._addPopupMenu( self.__swatch )

		self.__swatch.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
		self.__swatch.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ), scoped = False )
		self.__swatch.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ), scoped = False )
		self.__swatch.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ), scoped = False )

		self._updateFromPlugs()

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )

		self.__swatch.setHighlighted( highlighted )

	def _updateFromPlugs( self ) :

		with self.getContext() :
			value = _colorFromPlugs( self.getPlugs() )

		self.__swatch.setColor( value )

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

		_ColorPlugValueDialogue.acquire( self.getPlugs() )

		return True

def _colorFromPlugs( plugs ) :

	if not len( plugs ) :
		return imath.Color4f( 0 )

	# ColorSwatch only supports one colour, and doesn't have
	# an "indeterminate" state, so when we have multiple plugs
	# the best we can do is take an average.
	return sum( p.getValue() for p in plugs ) / len( plugs )

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

		self.__colorChangedConnection = self.colorChooser().colorChangedSignal().connect( Gaffer.WeakMethod( self.__colorChanged ), scoped = False )
		self.confirmButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ), scoped = False )
		self.cancelButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ), scoped = False )

		self.__plugs = plugs
		self.__initialValues = { p : p.getValue() for p in self.__plugs }

		nodes = { p.node() for p in self.__plugs }
		self.__plugSetConnections = [ n.plugSetSignal().connect( Gaffer.WeakMethod( self.__plugSet ), scoped = False ) for n in nodes ]
		for node in nodes :
			node.parentChangedSignal().connect( Gaffer.WeakMethod( self.__destroy ), scoped = False )

		plug = next( iter( self.__plugs ) )
		if len( self.__plugs ) == 1 :
			self.setTitle( plug.relativeName( plug.ancestor( Gaffer.ScriptNode ) ) )
		else :
			self.setTitle( "{} plugs".format( len( self.__plugs ) ) )

		self.__plugSet( plug )

		parentWindow.addChildWindow( self, removeOnClose = True )

	@classmethod
	def acquire( cls, plugs ) :

		plug = next( iter( plugs ) )

		script = plug.node().scriptNode()
		scriptWindow = GafferUI.ScriptWindow.acquire( script )

		for window in scriptWindow.childWindows() :
			if isinstance( window, cls ) and window.__plugs == plugs :
				window.setVisible( True )
				return window

		window = _ColorPlugValueDialogue( plugs, scriptWindow )
		window.setVisible( True )
		return False

	def __plugSet( self, plug ) :

		if plug in self.__plugs :
			with Gaffer.BlockedConnection( self.__colorChangedConnection ) :
				self.colorChooser().setColor( _colorFromPlugs( self.__plugs ) )

	def __colorChanged( self, colorChooser, reason ) :

		if not GafferUI.ColorChooser.changesShouldBeMerged( self.__lastChangedReason, reason ) :
			self.__mergeGroupId += 1
		self.__lastChangedReason = reason

		with Gaffer.UndoScope(
			next( iter( self.__plugs ) ).ancestor( Gaffer.ScriptNode ),
			mergeGroup = "ColorPlugValueDialogue%d%d" % ( id( self, ), self.__mergeGroupId )
		) :

			with Gaffer.BlockedConnection( self.__plugSetConnections ) :
				for plug in self.__plugs :
					plug.setValue( self.colorChooser().getColor() )

	def __buttonClicked( self, button ) :

		if button is self.cancelButton :
			with Gaffer.UndoScope( next( iter( self.__plugs ) ).ancestor( Gaffer.ScriptNode ) ) :
				for p, v in self.__initialValues.items() :
					p.setValue( v )

		# ideally we'd just remove ourselves from our parent immediately, but that would
		# trigger this bug :
		#
		# 	https://bugreports.qt-project.org/browse/QTBUG-26761
		#
		# so instead we destroy ourselves on the next idle event.

		GafferUI.EventLoop.addIdleCallback( self.__destroy )

	def __destroy( self, *unused ) :

		self.parent().removeChild( self )
		return False # to remove idle callback
