##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

import IECore

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtWidgets

# A `QtCore.Object` for capturing all mouse clicks before any UI elements
# get the click event so we can identify the widget clicked on.
class _ButtonPressFilter( QtCore.QObject ) :

	def __init__( self ) :

		QtCore.QObject.__init__( self )

		self.__widgetPickedSignal = Gaffer.Signals.Signal1()

	def eventFilter( self, obj, event ) :

		if event.type() == QtCore.QEvent.MouseButtonPress :
			widget = GafferUI.Widget.widgetAt( GafferUI.Widget.mousePosition() )

			if widget is not None :
				self.__widgetPickedSignal( widget )

			return True

		return False

	# A signal emitted whenver a widget is picked. Slots should have the
	# signature slot( widget ).
	def widgetPickedSignal( self ) :

		return self.__widgetPickedSignal


class WidgetPath( Gaffer.Path ) :
	# A `Gaffer.Path` to a `GafferUI.Widget` rooted at `rootWidget`. Path
	# entries are string representations of the integer index into the parent
	# widget's children for the widget, or the name of the parent's member variable
	# for the widget.

	def __init__( self, scriptNode, path = None, root = "/", filter = None ) :

		Gaffer.Path.__init__( self, path = path, root = root, filter = filter )

		self.__scriptNode = scriptNode

	def copy( self ) :

		return self.__class__( self.__scriptNode, self[:], self.root(), self.getFilter() )

	def isValid( self, canceller = None ) :

		return self.widget() is not None

	def isLeaf( self, canceller = None ) :

		return self.isValid() and len( self.__childWidgets( self.widget() ) ) == 0

	def propertyNames( self ) :

		return Gaffer.Path.propertyNames() + [
			"widgetEditor:name",
			"widgetEditor:widget",
			"widgetEditor:widgetType",
		]

	def property( self, name, canceller = None ) :

		result = Gaffer.Path.property( self, name )

		if result is not None :
			return result

		widget = self.widget()
		if widget is None :
			return None

		if name == "widgetEditor:name" :
			return self[-1]
		elif name == "widgetEditor:widget" :
			return widget
		elif name == "widgetEditor:widgetType" :
			return type( widget ).__name__

	def widget( self ) :
		# Returns the `GafferUI.Widget` for this path.

		if self.__scriptNode is None :
			return None

		widget = GafferUI.ScriptWindow.acquire( self.__scriptNode )
		assert( widget is not None )
		# A path with a single element is the top level `ScriptWindow`, start looking below that.
		for i in self[1:] :
			childWidgets = self.__childWidgets( widget )
			if i.isnumeric():
				widget = widget[ int( i ) ]
			else :
				widget = childWidgets[i]

		return widget

	def scriptNode( self ) :

		return self.__scriptNode

	def _children( self, canceller ) :

		if not self.isValid() or self.isLeaf() :
			return []

		if len( self ) == 0 :
			return [ WidgetPath( self.__scriptNode, self[:] + ["scriptWindow"], self.root(), self.getFilter() ) ]

		childWidgets = self.__childWidgets( self.widget() )
		return [
			WidgetPath( self.__scriptNode, self[:] + [ k ], self.root(), self.getFilter() )
			for k in childWidgets.keys()
		]

	def __repr__( self ) :

		result = "GafferUI.ScriptWindow.acquire(root)"
		for p in self[1:] :
			if p.isnumeric() :
				result += f"[{p}]"
			else :
				result += "." + p

		return result

	def __isAggregate( self, widget ) :

		return hasattr( widget, "__getitem__" ) and hasattr( widget, "__len__" )

	def __childWidgets( self, widget ) :

		result = {}

		visited = set()

		if self.__isAggregate( widget ) :
			for i in range( 0, len( widget ) ) :
				if isinstance( widget[i], GafferUI.Widget ) and widget[i] not in visited :
					result[str( i )] = widget[i]
					visited.add( widget[i] )

		for a in dir( widget ) :
			if isinstance( getattr( widget, a ), GafferUI.Widget ) and getattr( widget, a ) not in visited :
				result[a] = getattr( widget, a )
				visited.add( getattr( widget, a ) )

		return result

class WidgetEditor( GafferUI.Editor ) :

	def __init__( self, scriptNode, **kw ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 4 )
		GafferUI.Editor.__init__( self, column, scriptNode, **kw )

		self.__scriptNode = scriptNode

		with column :

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				self.__pickButton = GafferUI.Button( "Pick Widget" )
				self.__pickButton.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__pickButtonReleased ) )
				self.__pickButton._qtWidget().setMaximumWidth( 150 )

				self.__delayedPickButton = GafferUI.Button( "Pick Widget (3 sec delay)" )
				self.__delayedPickButton.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__delayedPickButtonReleased ) )
				self.__delayedPickButton._qtWidget().setMaximumWidth( 150 )

				self.__timerWidget = GafferUI.BusyWidget( size = 25, busy = False )

			self.__widgetNameColumn = GafferUI.PathListingWidget.StandardColumn( "Name", "widgetEditor:name" )

			self.__widgetListingWidget = GafferUI.PathListingWidget(
				WidgetPath( None ),  # temp until we make a WidgetPath
				columns = (
					self.__widgetNameColumn,
					GafferUI.PathListingWidget.StandardColumn( "Type", "widgetEditor:widgetType" ),
				),
				selectionMode = GafferUI.PathListingWidget.SelectionMode.Row,
				displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
			)

			self.__widgetListingWidget.dragBeginSignal().connectFront( Gaffer.WeakMethod( self.__dragBegin ) )

		self.visibilityChangedSignal().connect( Gaffer.WeakMethod( self.__visibilityChanged ) )

		self.__buttonPressFilter = _ButtonPressFilter()
		self.__buttonPressFilter.widgetPickedSignal().connect( Gaffer.WeakMethod( self.__widgetPicked ) )

	def __repr__( self ) :

		return "GafferUI.WidgetEditor( scriptNode )"

	def __dragBegin( self, widget, event ) :

		path = self.__widgetListingWidget.pathAt( imath.V2f( event.line.p0.x, event.line.p0.y ) )

		column = self.__widgetListingWidget.columnAt( imath.V2f( event.line.p0.x, event.line.p0.y ) )

		if column == self.__widgetNameColumn :
			GafferUI.Pointer.setCurrent( "nodes" )
			return path

	def __installEventFilter( self ) :

		self.__timerWidget.setBusy( False )
		QtWidgets.QApplication.instance().installEventFilter( self.__buttonPressFilter )

	def __pickButtonReleased( self, *unused ) :

		self.__installEventFilter()

	def __delayedPickButtonReleased( self, *unused ) :

		self.__timerWidget.setBusy( True )
		QtCore.QTimer.singleShot( 3000, self.__installEventFilter )

	def __visibilityChanged( self, widget ) :

		if widget.visible() and self.__widgetListingWidget.getPath().scriptNode() is None :
			self.__widgetListingWidget.setPath( WidgetPath( self.__scriptNode ) )

	def __widgetPathWalk( self, path, targetWidget ) :

		for c in path.children() :
			widget = c.property( "widgetEditor:widget" )
			if widget == targetWidget :
				return c
			elif widget.isAncestorOf( targetWidget ) :
				return self.__widgetPathWalk( c, targetWidget )

	def __widgetPicked( self, widget ) :

		path = self.__widgetPathWalk( self.__widgetListingWidget.getPath(), widget )
		pm = IECore.PathMatcher()
		pm.addPath( str( path ) )
		self.__widgetListingWidget.setSelection( pm, True )
		QtWidgets.QApplication.instance().removeEventFilter( self.__buttonPressFilter )


GafferUI.Editor.registerType( "WidgetEditor", WidgetEditor )