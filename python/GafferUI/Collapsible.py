##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

import os

import IECore

import Gaffer
import GafferUI

QtGui = GafferUI._qtImport( "QtGui" )

## The Collapsible container provides an easy means of controlling the
# visibility of a child Widget. A labelled heading is always visible
# and clicking on it reveals or hides the child below. A corner widget
# may be provided to add additional functionality to the header.
class Collapsible( GafferUI.ContainerWidget ) :

	def __init__( self, label="", child=None, collapsed=False, borderWidth=0, cornerWidget=None, cornerWidgetExpanded=False, **kw ) :

		GafferUI.ContainerWidget.__init__( self, QtGui.QWidget(), **kw )

		layout = _VBoxLayout()
		self._qtWidget().setLayout( layout )
		layout.setSizeConstraint( QtGui.QLayout.SetMinAndMaxSize )
		layout.setContentsMargins( borderWidth, borderWidth, borderWidth, borderWidth )

		self.__headerLayout = QtGui.QHBoxLayout()
		self.__headerLayout.setSizeConstraint( QtGui.QLayout.SetMinAndMaxSize )
		self.__headerLayout.setContentsMargins( 0, 0, 0, 0 )
		self.__headerLayout.setSpacing(0)

		self.__toggle = QtGui.QCheckBox()
		self.__toggle.setObjectName( "gafferCollapsibleToggle" )
		self.__headerLayout.addWidget( self.__toggle)

		self.__headerLayout.addStretch( 1 )

		layout.addLayout( self.__headerLayout )

		self.__stateChangedSignal = GafferUI.WidgetSignal()
		self.__toggle.stateChanged.connect( Gaffer.WeakMethod( self.__toggled ) )

		self.__child = None
		self.setChild( child )

		self.__cornerWidget = None
		self.setCornerWidget( cornerWidget, cornerWidgetExpanded )

		self.setLabel( label )
		self.setCollapsed( collapsed )

	def addChild( self, child ) :

		if self.getChild() is not None :
			raise Exception( "Collapsible can only hold one child" )

		self.setChild( child )

	def removeChild( self, childOrCornerWidget ) :

		assert( childOrCornerWidget is self.__child or childOrCornerWidget is self.__cornerWidget )

		childOrCornerWidget._qtWidget().setParent( None )
		childOrCornerWidget._applyVisibility()
		if childOrCornerWidget is self.__child :
			self.__child = None
		else :
			self.__cornerWidget = None

	def setChild( self, child ) :

		if self.__child is not None :
			self.removeChild( self.__child )

		if child is not None :

			oldParent = child.parent()
			if oldParent is not None :
				oldParent.removeChild( child )

			self._qtWidget().layout().addWidget( child._qtWidget() )
			child.setVisible( not self.getCollapsed() )
			self.__child = child

	def getChild( self ) :

		return self.__child

	def setLabel( self, label ) :

		self.__toggle.setText( label )

	def getLabel( self ) :

		return self.__toggle.text()

	def setCollapsed( self, state ) :

		self.__toggle.setChecked( state )

	def getCollapsed( self ) :

		return self.__toggle.isChecked()

	def setCornerWidget( self, cornerWidget, cornerWidgetExpanded=False ) :

		if self.__cornerWidget is not None :
			self.removeChild( self.__cornerWidget )

		if cornerWidget is not None :
			if cornerWidgetExpanded and self.__headerLayout.stretch(1) == 1:
				self.__headerLayout.setStretch(1, 0)

			elif self.__headerLayout.stretch(1) == 0:
				self.__headerLayout.setStretch(1, 1)

			stretch = 1 if cornerWidgetExpanded else 0

			self.__headerLayout.addWidget( cornerWidget._qtWidget(), stretch )
			self.__cornerWidget = cornerWidget
			self.__cornerWidget._applyVisibility()

	def getCornerWidget( self ) :

		return self.__cornerWidget

	## A signal emitted whenever the ui is collapsed or
	# expanded.
	def stateChangedSignal( self ) :

		return self.__stateChangedSignal

	def __toggled( self, value ) :

		if self.__child is not None :
			self.__child.setVisible( not value )

		self.stateChangedSignal()( self )

class _VBoxLayout( QtGui.QVBoxLayout ) :

	def __init__( self ) :

		QtGui.QVBoxLayout.__init__( self )

	## Reimplemented so that requested width takes account of the
	# width of child items even if they are currently hidden. That
	# way the width doesn't change when the child is shown.
	def sizeHint( self ) :

		s = QtGui.QVBoxLayout.sizeHint( self )

		maxWidth = 0
		for i in range( 0, self.count() ) :
			maxWidth = max( maxWidth, self.itemAt( i ).sizeHint().width() )

		margins = self.contentsMargins()

		s.setWidth( maxWidth + margins.left() + margins.right() )
		return s
