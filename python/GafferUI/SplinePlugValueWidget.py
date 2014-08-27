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

		if isinstance( plug, Gaffer.SplinefColor3fPlug ) :
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
				self.__splineWidget.setSpline( plug.getValue() )

	def __buttonPress( self, button, event ) :

		if event.buttons & event.Buttons.Left :

			if self.__editorWindow is None or self.__editorWindow() is None :

				## \todo This could perhaps be improved if it derived from a PlugValueDialogue
				# base class shared with the _ColorPlugValueDialogue.
				window = GafferUI.Window(
					title = self.getPlug().relativeName( self.getPlug().ancestor( Gaffer.ScriptNode ) ),
					borderWidth = 8,
				)
				window.setChild( GafferUI.RampPlugValueWidget( self.getPlug() ) )

				self.ancestor( GafferUI.Window ).addChildWindow( window )
				self.__editorWindow = weakref.ref( window )

			self.__editorWindow().setVisible( True )

GafferUI.PlugValueWidget.registerType( Gaffer.SplineffPlug, SplinePlugValueWidget )
GafferUI.PlugValueWidget.registerType( Gaffer.SplinefColor3fPlug, SplinePlugValueWidget )
