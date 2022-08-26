##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
import os
import sys
import six

import GafferUI

import Qt
from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

def joinEdges( widgets, orientation = None ) :

	if isinstance( widgets, GafferUI.ListContainer ) :
		assert( orientation is None )
		orientation = widgets.orientation()
	else :
		assert( orientation is not None )

	if orientation == GafferUI.ListContainer.Orientation.Horizontal :
		lowProperty = "gafferAdjoinedLeft"
		highProperty = "gafferAdjoinedRight"
	else :
		lowProperty = "gafferAdjoinedTop"
		highProperty = "gafferAdjoinedBottom"

	joinableTypes = ( QtWidgets.QAbstractButton, QtWidgets.QFrame )

	visibleWidgets = [ w for w in widgets if w.getVisible() ]
	l = len( visibleWidgets )
	for i, widget in enumerate( visibleWidgets ) :

		qtWidget = widget._qtWidget()
		# The top-level `QWidget` may be a non-drawable container that
		# doesn't respond to styling - one common example is when
		# `GafferUI.Widget.__init__` wraps a `GafferUI.Widget` in a `QWidget``.
		# In this case, search for a child that does accept styling,
		# and style that instead.
		while not isinstance( qtWidget, joinableTypes ) :
			children = [ c for c in qtWidget.children() if isinstance( c, QtWidgets.QWidget ) ]
			if len( children ) == 1 :
				qtWidget = children[0]
			else :
				break

		qtWidget.setProperty( lowProperty, i > 0 )
		qtWidget.setProperty( highProperty, i < l - 1 )
		widget._repolish()

def grab( widget, imagePath ) :

	if not GafferUI.EventLoop.mainEventLoop().running() :
		# This is a hack to try to give Qt time to
		# finish processing any events needed to get
		# the widget ready for capture. Really we need
		# a rock solid way that _guarantees_ this, and which
		# we can also use when the event loop is running.
		GafferUI.EventLoop.waitForIdle()

	imageDir = os.path.dirname( imagePath )
	if imageDir and not os.path.isdir( imageDir ) :
		os.makedirs( imageDir )

	if Qt.__binding__ in ( "PySide2", "PyQt5" ) :
		# Qt 5
		screen = QtWidgets.QApplication.primaryScreen()
		windowHandle = widget._qtWidget().windowHandle()
		if windowHandle :
			screen = windowHandle.screen()

		qtVersion = [ int( x ) for x in Qt.__qt_version__.split( "." ) ]
		if qtVersion >= [ 5, 12 ] or six.PY3 :
			pixmap = screen.grabWindow( widget._qtWidget().winId() )
		else :
			pixmap = screen.grabWindow( long( widget._qtWidget().winId() ) )

		if sys.platform == "darwin" and pixmap.size() == screen.size() * screen.devicePixelRatio() :
			# A bug means that the entire screen will have been captured,
			# not just the widget we requested. Copy out just the widget.
			topLeft = widget._qtWidget().mapToGlobal( QtCore.QPoint( 0, 0 ) )
			bottomRight = widget._qtWidget().mapToGlobal( QtCore.QPoint( widget._qtWidget().width(), widget._qtWidget().height() ) )
			size = bottomRight - topLeft
			pixmap = pixmap.copy(
				QtCore.QRect(
					topLeft * screen.devicePixelRatio(),
					QtCore.QSize( size.x(), size.y() ) * screen.devicePixelRatio()
				)
			)

	else :
		# Qt 4
		pixmap = QtGui.QPixmap.grabWindow( long( widget._qtWidget().winId() ) )

	pixmap.save( imagePath )

## Useful as a workaround when you want to dispose of a GafferUI.Widget immediately,
# but Qt bugs prevent you from doing so.
def keepUntilIdle( widget ) :

	def keep( o ) :

		return False # Removes idle callback

	GafferUI.EventLoop.addIdleCallback( functools.partial( keep, widget ) )
