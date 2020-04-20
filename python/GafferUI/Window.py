##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import six
import sys
import warnings
import imath

import IECore

import GafferUI
import Gaffer

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets
import Qt

class Window( GafferUI.ContainerWidget ) :

	SizeMode = IECore.Enum.create( "Fixed", "Manual", "Automatic" )

	## \todo Remove the deprecated resizable argument
	def __init__( self, title="GafferUI.Window", borderWidth=0, resizeable=None, child=None, sizeMode=SizeMode.Manual, icon="GafferLogoMini.png", **kw ) :

		GafferUI.ContainerWidget.__init__(
			self, QtWidgets.QWidget( None, QtCore.Qt.WindowFlags( QtCore.Qt.Window ), **kw )
		)

		self.__child = None
		self.__childWindows = set()
		self.__qtLayout = QtWidgets.QGridLayout()
		self.__qtLayout.setContentsMargins( borderWidth, borderWidth, borderWidth, borderWidth )
		self.__qtLayout.setSizeConstraint( QtWidgets.QLayout.SetMinAndMaxSize )

		# The initial size of a widget in qt "depends on the user's platform and screen geometry".
		# In other words, it is useless. We use this flag to determine whether or not our size is
		# this meaningless initial size, or whether it has been set appropriately. This is needed in
		# resizeToFitChild().
		self.__sizeValid = False

		if len( self.__caughtKeys() ):
			# set up a key press handler, so we can catch various key presses and stop them being handled by the
			# host application
			self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )


		# \todo Does this hurt performance? Maybe keyPressSignal() should set this up when it's called?
		self._qtWidget().setFocusPolicy( QtCore.Qt.ClickFocus )

		self._qtWidget().setLayout( self.__qtLayout )

		self._qtWidget().installEventFilter( _windowEventFilter )

		self._setStyleSheet()

		self.setTitle( title )
		self.setIcon( icon )

		if resizeable is not None :
			self.setResizeable( resizeable )
		else :
			self.setSizeMode( sizeMode )

		self.__closedSignal = GafferUI.WidgetSignal()

		self.setChild( child )

	def setTitle( self, title ) :

		self._qtWidget().setWindowTitle( title )

	def getTitle( self ) :

		return self._qtWidget().windowTitle()

	## Overridden from the base class to ensure that
	# window.setVisible( True ) also raises and unminimizes
	# the window.
	def setVisible( self, visible ) :

		GafferUI.Widget.setVisible( self, visible )

		if self.visible() :
			if self._qtWidget().isMinimized() :
				self._qtWidget().showNormal()
			self._qtWidget().raise_()

	def removeChild( self, child ) :

		assert( child is self.__child or child in self.__childWindows )
		child._qtWidget().setParent( None )
		child._applyVisibility()
		if child is self.__child :
			self.__child = None
		else :
			self.__childWindows.remove( child )

	def addChild( self, child ) :

		if isinstance( child, Window ) :
			self.addChildWindow( child )
		else :
			if self.getChild() is not None :
				raise Exception( "Window can only hold one child" )
			self.setChild( child )

	def setChild( self, child ) :

		oldChild = self.getChild()
		if oldChild is not None :
			self.removeChild( oldChild )

		if child is not None :

			oldParent = child.parent()
			if oldParent is not None :
				oldParent.removeChild( child )

			self.__child = child
			self.__qtLayout.addWidget( child._qtWidget(), 0, 0 )
			child._applyVisibility()

	def getChild( self ) :

		return self.__child

	## Adding a child window causes the child to stay
	# on top of the parent at all times. This is useful for
	# preventing dialogues and the like from disappearing behind
	# the main window. Note that the parent will keep the child
	# window alive until it is removed using removeChild() -
	# passing removeOnClose=True provides a convenient mechanism
	# for removing it automatically when it is closed.
	def addChildWindow( self, childWindow, removeOnClose=False ) :

		assert( isinstance( childWindow, Window ) )

		oldParent = childWindow.parent()
		if oldParent is self :
			return

		if oldParent is not None :
			oldParent.removeChild( childWindow )

		self.__childWindows.add( childWindow )

		# We have the following criteria for child windows :
		#
		#	- they must always stay on top of their parent
		#		- even when the parent is fullscreen
		#	- they must open somewhere sensible by default
		#		- ideally centered on the parent
		#	- they must take focus nicely when asked (by PathChooserDialogue for instance)
		#
		# On OS X, the Tool window type does an excellent job
		# of all of that, as well as looking pretty. But if we use
		# the Dialog window type, they disappear behind full screen
		# windows.
		#
		# On Linux, the Tool window type does a poor job, opening
		# in arbitrary places, and displaying various focus problems.
		# The Dialog type on the other hand does a much better job. Of
		# course, this being X11, different window managers will do different
		# things, but on the whole the Dialog type seems best for X11.
		childWindowType = QtCore.Qt.Tool if sys.platform == "darwin" else QtCore.Qt.Dialog
		childWindowFlags = ( childWindow._qtWidget().windowFlags() & ~QtCore.Qt.WindowType_Mask ) | childWindowType

		if sys.platform == "darwin" and Qt.__binding__ in ( "PySide2", "PyQt5" ) :
			# Alternative order of operations to work around crashes
			# on OSX with Qt5.
			childWindow._qtWidget().setParent( self._qtWidget() )
			childWindow._applyVisibility()
			childWindow._qtWidget().setWindowFlags( childWindowFlags )
		else :
			childWindow._qtWidget().setParent( self._qtWidget(), childWindowFlags )
			childWindow._applyVisibility()

		if removeOnClose :
			childWindow.closedSignal().connect( lambda w : w.parent().removeChild( w ), scoped = False )

	## Returns a list of all the windows parented to this one.
	def childWindows( self ) :

		return list( self.__childWindows )

	## \deprecated
	def setResizeable( self, resizeable ) :

		warnings.warn( "Window.setResizeable() is deprecated, use Window.setSizeMode() instead.", DeprecationWarning, 2 )
		if resizeable :
			self.setSizeMode( self.SizeMode.Manual )
		else :
			self.setSizeMode( self.SizeMode.Fixed )

	## \deprecated
	def getResizeable( self ) :

		warnings.warn( "Window.getResizeable() is deprecated, use Window.getSizeMode() instead.", DeprecationWarning, 2 )
		return self.getSizeMode() == self.SizeMode.Manual

	def setSizeMode( self, sizeMode ) :

		self.__sizeMode = sizeMode
		if sizeMode == self.SizeMode.Manual :
			self.__qtLayout.setSizeConstraint( QtWidgets.QLayout.SetDefaultConstraint )
		else :
			self.__qtLayout.setSizeConstraint( QtWidgets.QLayout.SetFixedSize )

	def getSizeMode( self ) :

		return self.__sizeMode

	## Resizes the window to fit the requirements of the current child.
	# The shrink or expand arguments may be set to False to prevent the
	# window becoming smaller or larger than its current size if that is
	# not desired.
	def resizeToFitChild( self, shrink=True, expand=True ) :

		s = self._qtWidget().size()
		sizeHint = self._qtWidget().sizeHint()

		if expand or not self.__sizeValid :
			s = s.expandedTo( sizeHint )
		if shrink or not self.__sizeValid :
			s = s.boundedTo( sizeHint )

		self._qtWidget().resize( s )

	def setPosition( self, position ) :

		self._qtWidget().move( position.x, position.y )

	def getPosition( self ) :

		return imath.V2i( self._qtWidget().x(), self._qtWidget().y() )

	def setFullScreen( self, fullScreen ) :

		if fullScreen :
			self._qtWidget().showFullScreen()
		else :
			self._qtWidget().showNormal()

	def getFullScreen( self ) :

		return self._qtWidget().isFullScreen()

	def setIcon( self, imageOrImageFileName ) :

		if isinstance( imageOrImageFileName, six.string_types ) :
			self.__image = GafferUI.Image( imageOrImageFileName )
		else :
			self.__image = imageOrImageFileName

		self._qtWidget().setWindowIcon( QtGui.QIcon( self.__image._qtPixmap() ) )

	def getIcon( self ) :

		return self.__image

	## Requests that this window be closed - this function may either be called
	# directly or in response to the user attempting to close the window.
	# If successful, setVisible( False ) will be called on the window and True will
	# be returned. However, the window may choose to deny the request in which case
	# the window will remain visible and False will be returned. The latter possibility
	# is to allow windows to take appropriate action when closing a window would mean a
	# user losing work. If a window is not visible on entry to this function then no
	# action is taken and False is returned.
	def close( self ) :

		if not self.getVisible() :
			return False

		if self._acceptsClose() :
			self.setVisible( False )
			self.closedSignal()( self )
			return True
		else :
			return False

	## Subclasses may override this to deny the closing of a window triggered
	# either by user action or by a call to close(). Simply return False to
	# prevent the closing.
	def _acceptsClose( self ) :

		return True

	## A signal emitted when the window has been closed successfully, either through
	# user action or a call to close()
	def closedSignal( self ) :

		return self.__closedSignal

	__caughtKeysSet = None
	@classmethod
	def __caughtKeys( cls ):

		if cls.__caughtKeysSet is None:

			try:
				# are we in maya? If so, we need to catch the ctrl and shift key presses to prevent
				# maya from handling them and doing crazy focus stealing stuff
				import maya
				cls.__caughtKeysSet = set( ["Control", "Shift"] )
			except ImportError:
				cls.__caughtKeysSet = set()

		return cls.__caughtKeysSet

	def __keyPress( self, widget, event ):

		return event.key in self.__caughtKeys()

class _WindowEventFilter( QtCore.QObject ) :

	def __init__( self ) :

		QtCore.QObject.__init__( self )

	def eventFilter( self, qObject, qEvent ) :

		type = qEvent.type()

		if type==QtCore.QEvent.Close :
			widget = GafferUI.Widget._owner( qObject )
			closed = widget.close()
			if closed :
				qEvent.accept()
			else :
				qEvent.ignore()
			return True
		elif type==QtCore.QEvent.LayoutRequest :
			widget = GafferUI.Widget._owner( qObject )
			if widget.getSizeMode() == widget.SizeMode.Automatic :
				widget.resizeToFitChild()
				return True
		elif type==QtCore.QEvent.Resize :
			widget = GafferUI.Widget._owner( qObject )
			widget._Window__sizeValid = True

		return False

# this single instance is used by all window widgets
_windowEventFilter = _WindowEventFilter()
