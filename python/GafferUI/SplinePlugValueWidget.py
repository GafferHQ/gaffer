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

import weakref

import Gaffer
import GafferUI

class SplinePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__splineWidget = GafferUI.SplineWidget()

		GafferUI.PlugValueWidget.__init__( self, self.__splineWidget, plug, **kw )

		self.__splineWidget._qtWidget().setFixedHeight( 20 )

		self.__buttonPressConnection = self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )

		self.__editorWindow = None

		self.setPlug( plug )

	def splineWidget( self ) :

		return self.__splineWidget

	def setPlug( self, plug ) :

		GafferUI.PlugValueWidget.setPlug( self, plug )

		if isinstance( plug, ( Gaffer.SplinefColor3fPlug, Gaffer.SplinefColor4fPlug ) ) :
			self.__splineWidget.setDrawMode( GafferUI.SplineWidget.DrawMode.Ramp )
		else :
			self.__splineWidget.setDrawMode( GafferUI.SplineWidget.DrawMode.Splines )

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )

		self.splineWidget().setHighlighted( highlighted )

	def _updateFromPlug( self ) :

		plug = self.getPlug()
		if plug is not None :
			with self.getContext() :
				self.__splineWidget.setSpline( plug.getValue().spline() )

	def __buttonPress( self, button, event ) :

		if event.buttons & event.Buttons.Left :

			if not self._editable() :
				return False

			_SplinePlugValueDialogue.acquire( self.getPlug() )
			return True

GafferUI.PlugValueWidget.registerType( Gaffer.SplineffPlug, SplinePlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.SplinefColor3fPlug, SplinePlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.SplinefColor4fPlug, SplinePlugValueWidget )

## \todo See comments for `ColorSwatchPlugValueWidget._ColorPlugValueDialogue`.
# I think the best approach is probably to move the `acquire()` mechanism to the
# main layout class when we do an overhaul of that system.
class _SplinePlugValueDialogue( GafferUI.Dialogue ) :

	def __init__( self, plug ) :

		GafferUI.Dialogue.__init__(
			self,
			plug.relativeName( plug.ancestor( Gaffer.ScriptNode ) )
		)

		self.__plug = plug
		self.setChild( GafferUI.RampPlugValueWidget( plug ) )

		## \todo Perhaps if `acquire()` were to be a shared central
		# mechanism, this handling should be done in `acquire()`
		# instead of in each of the individual dialogues? Perhaps
		# `acquire()` should even be responsible for building the
		# dialogues, so it's able to build a dialogue around any
		# PlugValueWidget?
		self.__plugParentChangedConnection = plug.parentChangedSignal().connect( Gaffer.WeakMethod( self.__destroy ) )
		self.__nodeParentChangedConnection = plug.node().parentChangedSignal().connect( Gaffer.WeakMethod( self.__destroy ) )

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
