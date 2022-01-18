##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

import warnings

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtWidgets

## The PlugWidget combines a LabelPlugValueWidget with a second PlugValueWidget
## suitable for editing the plug.
## \todo This could provide functionality for arbitrary Widgets to be placed
## on the right, which combined with the ability to find a
## PlugWidget given a Plug could be quite useful for many things.
## \todo Remove deprecated label and description capabilities.
class PlugWidget( GafferUI.Widget ) :

	def __init__( self, plugOrWidget, label=None, description=None, **kw ) :

		GafferUI.Widget.__init__( self, QtWidgets.QWidget(), **kw )

		layout = QtWidgets.QHBoxLayout()
		layout.setContentsMargins( 0, 0, 0, 0 )
		layout.setSpacing( 4 )
		layout.setSizeConstraint( QtWidgets.QLayout.SetMinAndMaxSize )
		self._qtWidget().setLayout( layout )

		if isinstance( plugOrWidget, Gaffer.Plug ) :
			self.__valueWidget = GafferUI.PlugValueWidget.create( plugOrWidget )
			plug = plugOrWidget
		else :
			assert( isinstance( plugOrWidget, GafferUI.PlugValueWidget ) or hasattr( plugOrWidget, "plugValueWidget" ) )
			self.__valueWidget = plugOrWidget
			plug = self.plugValueWidget().getPlug()

		self.__label = GafferUI.LabelPlugValueWidget(
			plug,
			horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right,
		)

		## \todo Decide how we allow this sort of tweak using the public
		# interface. Perhaps we should have a SizeableContainer or something?
		self.__label.label()._qtWidget().setFixedWidth( self.labelWidth() )

		if label is not None :
			warnings.warn(
				"The PlugWidget label parameter is deprecated. Use Metadata instead.",
				DeprecationWarning,
				2
			)
			self.__label.label().setText( label )

		if description is not None :
			warnings.warn(
				"The PlugWidget description parameter is deprecated. Use Metadata instead.",
				DeprecationWarning,
				2
			)
			self.__label.label().setToolTip( description )

		layout.addWidget( self.__label._qtWidget(), alignment = QtCore.Qt.AlignTop )
		layout.addWidget( self.__valueWidget._qtWidget() )

		# The plugValueWidget() may have smarter drop behaviour than the labelPlugValueWidget(),
		# because it has specialised PlugValueWidget._convertValue(). It's also more meaningful to the
		# user if we highlight the plugValueWidget() on dragEnter rather than the label. So we
		# forward the dragEnter/dragLeave/drop signals from the labelPlugValueWidget() to the plugValueWidget().
		self.__label.dragEnterSignal().connectFront( Gaffer.WeakMethod( self.__labelDragEnter ), scoped = False )
		self.__label.dragLeaveSignal().connectFront( Gaffer.WeakMethod( self.__labelDragLeave ), scoped = False )
		self.__label.dropSignal().connectFront( Gaffer.WeakMethod( self.__labelDrop ), scoped = False )

	def plugValueWidget( self ) :

		if isinstance( self.__valueWidget, GafferUI.PlugValueWidget ) :
			return self.__valueWidget
		else :
			return self.__valueWidget.plugValueWidget()

	def labelPlugValueWidget( self ) :

		return self.__label

	@staticmethod
	def labelWidth() :

		return 150

	## Ensures that the specified plug has a visible PlugWidget,
	# creating one if necessary.
	@classmethod
	def acquire( cls, plug ) :

		plugValueWidget = GafferUI.PlugValueWidget.acquire( plug )
		if not plugValueWidget :
			return None

		plugWidget = plugValueWidget.ancestor( GafferUI.PlugWidget )
		if not plugWidget :
			return None

		plugWidget.reveal()

		return plugWidget

	def __labelDragEnter( self, label, event ) :

		return self.plugValueWidget().dragEnterSignal()( self.plugValueWidget(), event )

	def __labelDragLeave( self, label, event ) :

		return self.plugValueWidget().dragLeaveSignal()( self.plugValueWidget(), event )

	def __labelDrop( self, label, event ) :

		return self.plugValueWidget().dropSignal()( self.plugValueWidget(), event )
