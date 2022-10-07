##########################################################################
#
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

import warnings

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

## \todo Support cascading menus using "/" in labels. Rework API to
# better match the rest of GafferUI - ditch index based methods, and
# just have setCurrent(), getCurrent() passing strings, and a
# currentChangedSignal(). Maybe use list style methods for managing
# entries (append [] del etc).
class SelectionMenu( GafferUI.Widget ) :

	__palette = None

	def __init__( self, **kw ) :

		warnings.warn( "GafferUI.SelectionMenu is deprecated, use MultiSelectionMenu instead.", DeprecationWarning, 2 )

		GafferUI.Widget.__init__( self, QtWidgets.QComboBox(), **kw )

		self._qtWidget().currentIndexChanged.connect( Gaffer.WeakMethod( self.__changed ) )
		self._qtWidget().activated.connect( Gaffer.WeakMethod( self.__selected ) )
		self.__currentIndexChangedSignal = GafferUI.WidgetSignal()
		self.__selectedSignal = GafferUI.WidgetSignal()

		# combo boxes appear to totally ignore the etch-disabled-text stylesheet option,
		# and we really don't like the etching. the only effective way of disabling it
		# seems to be to apply this palette which makes the etched text transparent.
		## \todo When we extend the Style classes to deal with Widgets, this should be
		# done there. The same code exists in the Button class too.
		if SelectionMenu.__palette is None :
			SelectionMenu.__palette = QtGui.QPalette( QtWidgets.QApplication.instance().palette( self._qtWidget() ) )
			SelectionMenu.__palette.setColor( QtGui.QPalette.Disabled, QtGui.QPalette.Light, QtGui.QColor( 0, 0, 0, 0 ) )

		self._qtWidget().setPalette( SelectionMenu.__palette )

		self._qtWidget().setView( QtWidgets.QListView() )

	def selectedSignal( self ):
		return self.__selectedSignal

	def currentIndexChangedSignal( self ):
		return self.__currentIndexChangedSignal

	def __changed( self, index ):
		self.currentIndexChangedSignal()( self )

	def __selected( self, index ):
		self.selectedSignal()( self )

	def addItem( self, itemName, imageOrImageFileName=None ):
		self._qtWidget().addItem(itemName)

		if not imageOrImageFileName is None:
			self.setIcon( self.getTotal()-1, imageOrImageFileName )

	def insertItem( self, index, itemName, imageOrImageFileName=None ):
		self._qtWidget().insertItem( index, itemName )

		if not imageOrImageFileName is None:
			self.setIcon( index, imageOrImageFileName )

	def setIcon( self, index, imageOrImageFileName ):
		icon = None

		assert( isinstance( imageOrImageFileName, ( str, GafferUI.Image, type( None ) ) ) )

		if isinstance( imageOrImageFileName, str ) :
			icon = GafferUI.Image( imageOrImageFileName )
		else :
			icon = imageOrImageFileName

		if icon is not None :
			self._qtWidget().setItemIcon( index, QtGui.QIcon(icon._qtPixmap() ) )
			self._qtWidget().setIconSize( icon._qtPixmap().size() )


	def getIcon( self, index ):
		return self._qtWidget().itemIcon( index )

	def getCurrentIndex( self ):
		return self._qtWidget().currentIndex()

	def getCurrentItem( self ):
		return str( self._qtWidget().currentText() )

	def getTotal( self ):
		return self._qtWidget().count()

	def setCurrentIndex( self, index ):
		self._qtWidget().setCurrentIndex( index )

	def getItem( self, index ):
		return str( self._qtWidget().itemText( index ) )

	def removeIndex( self, index ):
		self._qtWidget().removeItem( index )

	def insertSeparator( self, index ):
		self._qtWidget().insertSeparator( index )
