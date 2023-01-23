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

import functools

import Gaffer
import GafferUI

## A simple PlugValueWidget which just displays the node connected
# to a Plug.
class ConnectionPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__frame = GafferUI.Frame( borderWidth = 2 )

		GafferUI.PlugValueWidget.__init__( self, self.__frame, plug, **kw )

		self.__inputLabel = GafferUI.NameLabel(
			None,
			horizontalAlignment = GafferUI.HorizontalAlignment.Center,
			formatter=self.__labelFormatter,
			numComponents=2,
		)

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )
		row.append( self.__inputLabel, horizontalAlignment = GafferUI.HorizontalAlignment.Center, expand = True )
		self.__frame.setChild( row )

		self.__frame.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ), scoped = False )
		self.__inputLabel.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ), scoped = False )
		self.__frame.enterSignal().connect( functools.partial( GafferUI.Frame.setHighlighted, highlighted=True ), scoped = False )
		self.__frame.leaveSignal().connect( functools.partial( GafferUI.Frame.setHighlighted, highlighted=False ), scoped = False )

		self._addPopupMenu( self.__frame )

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )
		self.__frame.setHighlighted( highlighted )

	def getToolTip( self ) :

		result = GafferUI.PlugValueWidget.getToolTip( self )

		srcNode = None
		if self.getPlug() is not None :
			input = self.getPlug().getInput()
			if input is not None :
				srcNode = input.node()

		if srcNode is not None :
			if result :
				result += "\n"
			result += "## Actions\n\n"
			result += " - Left drag to drag source plug\n"
			result += " - Left click to edit source node\n"

		return result

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		# Avoid unnecessary overhead of computing values, since
		# we don't use them in `_updateFromValues()`.
		return [ None for p in plugs ]

	# We don't actually display values, but this is also called whenever the
	# input changes, which is when we need to update.
	def _updateFromValues( self, values, exception ) :

		input = self.getPlug().getInput()
		self.__inputLabel.setGraphComponent( input )
		if input is not None :
			self.__inputLabel.setNumComponents( input.relativeName( input.node() ).count( "." ) + 2 )

	def __buttonRelease( self, widget, event ) :

		if event.button == event.Buttons.Left :
			if self.getPlug().getInput() is not None :
				GafferUI.NodeEditor.acquire( self.getPlug().getInput().node() )
				return True

		return False

	@staticmethod
	def __labelFormatter( graphComponents ) :

		if graphComponents :
			return "<b>" + ".".join( [ g.getName() for g in graphComponents ] ) + "</b>"
		else :
			return "<b><i>None</i></b>"

GafferUI.PlugValueWidget.registerType( Gaffer.Plug, ConnectionPlugValueWidget )
