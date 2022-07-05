##########################################################################
#
#  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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

import imath

import Gaffer
import GafferUI

from GafferUI.PlugValueWidget import sole

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

## \todo Replace `GafferUI.PopupWindow` with this. It isn't used anywhere in Gaffer,
# and it has various unwanted behaviours.
class _PopupWindow( GafferUI.Window ) :

	def __init__( self, title = "GafferUI.Window", borderWidth = 8, child = None, **kw ) :

		GafferUI.Window.__init__( self, title, borderWidth, child = child, sizeMode = GafferUI.Window.SizeMode.Automatic, **kw )

		self._qtWidget().setWindowFlags( QtCore.Qt.Popup )
		self._qtWidget().setAttribute( QtCore.Qt.WA_TranslucentBackground )
		self._qtWidget().paintEvent = Gaffer.WeakMethod( self.__paintEvent )

		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )

	def popup( self, center = None ) :

		if center is None :
			center = GafferUI.Widget.mousePosition()

		self.setVisible( True )
		size = self._qtWidget().sizeHint()
		self.setPosition( center - imath.V2i( size.width() / 2, size.height() / 2 ) )

	def __paintEvent( self, event ) :

		painter = QtGui.QPainter( self._qtWidget() )
		painter.setRenderHint( QtGui.QPainter.Antialiasing )

		painter.setBrush( QtGui.QColor( 35, 35, 35 ) )
		painter.setPen( QtGui.QColor( 0, 0, 0, 0 ) )

		radius = self._qtWidget().layout().contentsMargins().left()
		size = self.size()
		painter.drawRoundedRect( QtCore.QRectF( 0, 0, size.x, size.y ), radius, radius )

	def __keyPress( self, widget, event ) :

		if event.key == "Return" :
			self.close()

class PlugPopup( _PopupWindow ) :

	def __init__( self, plugs, title = None, warning = None, **kw ) :

		assert( len( plugs ) )
		script = sole( p.ancestor( Gaffer.ScriptNode ) for p in plugs )
		assert( script is not None )

		column = GafferUI.ListContainer( spacing = 4 )
		_PopupWindow.__init__( self, "", child = column, **kw )

		with column :

			# Title

			if title is None :

				# Make default title

				if len( plugs ) == 1 :
					title = plugs[0].relativeName( script )
				else :
					nodes = { plug.node() for plug in plugs }
					title = "{} plugs{}".format(
						len( plugs ),
						" on {} nodes".format( len( nodes ) ) if len( nodes ) > 1 else ""
					)

					commonNode = plugs[0].node()
					for plug in plugs :
						if not commonNode.isAncestorOf( plug ) :
							commonNode = commonNode.commonAncestor( plug.node() )

					if commonNode != script :
						title = "{} ({})".format(
							commonNode.relativeName( script ),
							title
						)

			if title :

				titleWidget = GafferUI.Label( "<h4>{}</h4>".format( title ) )
				titleWidget.setToolTip(
					"\n".join( "- " + p.relativeName( script ) for p in plugs )
				)

			# Widget row

			with GafferUI.ListContainer( spacing = 4, orientation = GafferUI.ListContainer.Orientation.Horizontal ) :

				# Warning

				if warning :
					warningBadge = GafferUI.Image( "warningSmall.png" )
					warningBadge.setToolTip( warning )

				# PlugValueWidget, or label explaining why we can't show one
				try :
					self.__plugValueWidget = GafferUI.PlugValueWidget.create( plugs )
				except (
					GafferUI.PlugValueWidget.MultipleWidgetCreatorsError,
					GafferUI.PlugValueWidget.MultiplePlugTypesError
				) as e :
					self.__plugValueWidget = None
					GafferUI.Label( "Unable to edit plugs with mixed types" )
					e.__traceback__ = None

		# If we have a ColorPlugValueWidget, expand it to show the chooser.
		colorPlugValueWidget = self.__colorPlugValueWidget( self.__plugValueWidget )
		if colorPlugValueWidget is not None :
			colorPlugValueWidget.setColorChooserVisible( True )

		self.visibilityChangedSignal().connect( Gaffer.WeakMethod( self.__visibilityChanged ), scoped = False )

	def popup( self, center = None ) :

		_PopupWindow.popup( self, center )

		# Attempt to focus the first text widget. This is done after making
		# the window visible, as we check child widget visibility to avoid
		# attempting to focus hidden widgets.

		textWidget = self.__firstTextWidget( self.__plugValueWidget )
		if textWidget is not None :
			if isinstance( textWidget, GafferUI.TextWidget ) :
				textWidget.grabFocus()
				textWidget.setSelection( 0, len( textWidget.getText() ) )
			else :
				textWidget.setFocussed( True )
			textWidget._qtWidget().activateWindow()

	def plugValueWidget( self ) :

		return self.__plugValueWidget

	def __visibilityChanged( self, unused ) :

		if self.visible() :
			return

		# It appears that Qt will sometimes fail to remove focus from
		# our window when it is hidden. This can cause edits to be lost,
		# because change of focus is the trigger for things like
		# `TextWidget.editingFinishedSignal()`. Remove the focus manually
		# if necessary.
		focusWidget = QtWidgets.QApplication.focusWidget()
		if focusWidget is not None :
			gafferWidget = GafferUI.Widget._owner( focusWidget )
			if gafferWidget is not None and self.isAncestorOf( gafferWidget ) :
				gafferWidget._qtWidget().clearFocus()

	@classmethod
	def __firstTextWidget( cls, plugValueWidget ) :

		if plugValueWidget is None :
			return None

		def widgetUsable( w ) :
			return w.visible() and w.enabled() and w.getEditable()

		widget = None

		if isinstance( plugValueWidget, GafferUI.StringPlugValueWidget ) :
			widget = plugValueWidget.textWidget()
		elif isinstance( plugValueWidget, GafferUI.NumericPlugValueWidget ) :
			widget = plugValueWidget.numericWidget()
		elif isinstance( plugValueWidget, GafferUI.PathPlugValueWidget ) :
			widget = plugValueWidget.pathWidget()
		elif isinstance( plugValueWidget, GafferUI.MultiLineStringPlugValueWidget ) :
			widget = plugValueWidget.textWidget()

		if widget is not None and widgetUsable( widget ) :
			return widget

		for childPlug in Gaffer.Plug.Range( next( iter( plugValueWidget.getPlugs() ) ) ) :
			childWidget = plugValueWidget.childPlugValueWidget( childPlug )
			if childWidget is not None :
				childTextWidget = cls.__firstTextWidget( childWidget )
				if childTextWidget is not None :
					return childTextWidget

		return None

	@classmethod
	def __colorPlugValueWidget( cls, plugValueWidget ) :

		if plugValueWidget is None :
			return None

		if isinstance( plugValueWidget, GafferUI.ColorPlugValueWidget ) :
			return plugValueWidget

		for childPlug in Gaffer.Plug.Range( next( iter( plugValueWidget.getPlugs() ) ) ) :
			childWidget = cls.__colorPlugValueWidget(
				plugValueWidget.childPlugValueWidget( childPlug )
			)
			if childWidget is not None :
				return childWidget

		return None
