##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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
import sys
import traceback

import imath

from collections import OrderedDict, namedtuple

import IECore
import IECoreScene

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

from Qt import QtWidgets

# Conceptually this is an embedded context-sensitive SceneInspector for the
# SceneView. In practice it is implemented completely separately from the
# SceneInspector though, because the SceneInspector doesn't yet support editing
# and/or EditScopes. Our intention is to unify the two by refactoring the
# SceneInspector to use the same Inspector framework used here and in the
# LightEditor. We also intend to move many of the components into GafferUI, so
# that they can be used in the development of an ImageInspector too.

# \todo Create a central renderer/attribute registry that we can
# query for this information, this is also duplicated in EditScopeAlgo.cpp
_rendererAttributePrefixes = {
	"ai" : "Arnold",
	"dl" : "Delight",
	"as" : "Appleseed",
	"gl" : "OpenGL",
	"osl" : "OSL",
	"cycles" : "Cycles"
};

__registeredShaderParameters = OrderedDict()

##########################################################################
# Shader Parameter Registration API
##########################################################################

def registerShaderParameter( attribute, parameter ) :

	__registeredShaderParameters.setdefault( attribute, [] ).append( parameter )

def deregisterShaderParameter( attribute, parameter ) :

	try :
		__registeredShaderParameters[ attribute ].remove( parameter )
	except :
		pass

def _registeredShaderAttributes() :

	return [ a for a in __registeredShaderParameters.keys() if __registeredShaderParameters[ a ] ]

def _registeredShaderParameters( attribute ) :

	return __registeredShaderParameters[ attribute ]

##########################################################################
# _SceneViewInspector
##########################################################################

class _SceneViewInspector( GafferUI.Widget ) :

	def __init__( self, sceneView ) :

		self.__frame = GafferUI.Frame( borderWidth = 4 )
		GafferUI.Widget.__init__( self, self.__frame )

		self.__attachToView( sceneView )

		self.__pendingUpdates = set()
		with self.__frame :

			with GafferUI.ListContainer( spacing = 8 ) :

				with GafferUI.ListContainer(
					orientation = GafferUI.ListContainer.Orientation.Horizontal,
					spacing = 8
				) :
					GafferUI.Label( "<h4 style=\"color: rgba( 255, 255, 255, 120 );\">Inspector</h4>" )
					GafferUI.Spacer( imath.V2i( 1 ) )
					self.__busyWidget = GafferUI.BusyWidget( size = 20, busy = False )
					hideButton = GafferUI.Button( image="deleteSmall.png", hasFrame=False )
					hideButton.clickedSignal().connect( Gaffer.WeakMethod( self.__closeButtonClicked ), scoped = False )

				with GafferUI.ScrolledContainer( horizontalMode = GafferUI.ScrollMode.Never ) :
					with GafferUI.ListContainer( spacing = 20 ) as self.__sections :
						for a in _registeredShaderAttributes() :
							_InspectorSection(
								self.__attributeLabel( a ),
								[
									GafferSceneUI.Private.ParameterInspector( sceneView["in"], sceneView["editScope"], a, ( "", p ) )
									for p in _registeredShaderParameters( a )
								],
								sceneView.getContext()
							)

		# We want to hide ourselves when we have nothing to show, and then show
		# ourselves again when an update discovers something relevant. But
		# `__updateLazily()` won't run if `self` is hidden, so we instead hide
		# this frame which holds all our contents.
		self.__frame.setVisible( False )

		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False)

	def _scheduleUpdate( self, inspectorWidget ) :

		if inspectorWidget not in self.__pendingUpdates :
			self.__pendingUpdates.add( inspectorWidget )
			self.__updateLazily()

	def __attachToView( self, sceneView ) :

		# Add a plug used to manage our visibility from an activator in SceneViewUI.py.
		sceneView.addChild( Gaffer.ValuePlug( "inspector" ) )
		sceneView["inspector"].addChild( Gaffer.BoolPlug( "visible", Gaffer.Plug.Direction.In, True ) )
		Gaffer.NodeAlgo.applyUserDefaults( sceneView["inspector"] )

		sceneView.viewportGadget().keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )

		self.__sceneView = sceneView

	def __closeButtonClicked( self, *unused ) :

		self.__sceneView["inspector"]["visible"].setValue( False )

	def __keyPress( self, gadget, event ) :

		if event.key == "I" and event.modifiers == GafferUI.ModifiableEvent.Modifiers.None_ :
			visible = self.__sceneView["inspector"]["visible"].getValue()
			self.__sceneView["inspector"]["visible"].setValue( not visible )
			return True

		return False

	@staticmethod
	def __attributeLabel( attribute ) :

		prefix, name = attribute.split( ":", 1 )
		prefix = _rendererAttributePrefixes.get( prefix, prefix )
		name = " ".join( [ IECore.CamelCase.toSpaced( n ) for n in name.split( ":" ) ] )
		return "{} {}".format( prefix, name )

	@GafferUI.LazyMethod()
	def __updateLazily( self ) :

		widgets = self.__pendingUpdates
		self.__pendingUpdates = set()

		# We copy the contexts so they can be safely used in
		# the background thread without fear of them being
		# modified on the foreground thread.
		self.__backgroundUpdate( {
			w : Gaffer.Context( w.context() )
			for w in widgets
		} )

	@GafferUI.BackgroundMethod()
	def __backgroundUpdate( self, pendingUpdates ) :

		canceller = Gaffer.Context.current().canceller()
		result = {}
		for widget, context in pendingUpdates.items() :
			try :
				with Gaffer.Context( context, canceller ) :
					widgetResult = widget._backgroundUpdate()
			except Exception as e :
				widgetResult = sys.exc_info()[1]
				# Avoid circular references that would prevent this
				# stack frame (and therefore `widget`) from dying.
				widgetResult.__traceback__ = None
			result[widget] = widgetResult

		return result

	@__backgroundUpdate.plug
	def __backgroundUpdatePlug( self ) :

		return self.__sceneView["in"]

	@__backgroundUpdate.preCall
	def __backgroundUpdatePreCall( self ) :

		self.__busyWidget.setBusy( True )

	@__backgroundUpdate.postCall
	def __backgroundUpdatePostCall( self, backgroundResult ) :

		# Pass results to individual inspector widgets.

		for widget, widgetResult in backgroundResult.items() :
			widget._backgroundUpdatePostCall( widgetResult )

		self.__busyWidget.setBusy( False )

		# Hide sections that have nothing to show, and hide
		# ourselves if no sections are visible.

		for section in self.__sections :
			section.update()

		self.__frame.setVisible( any( s.getVisible() for s in self.__sections ) )

# \todo Check how this relates to DiffColumn in the SceneInspector
class _InspectorSection( GafferUI.ListContainer ) :

	def __init__( self, label, inspectors, context, **kwargs ) :

		GafferUI.ListContainer.__init__( self, spacing = 4, **kwargs )

		with self :

			self.__labelText = label
			self.__label = GafferUI.Label()
			GafferUI.Divider()

			self.__inspectorWidgets = [
				_InspectorWidget( inspector, context )
				for inspector in inspectors
			]

	# Called by _SceneViewInspector to update our label and
	# visibility after the _InspectorWidgets are updated.
	def update( self ) :

		numValues = max( len( w.valueWidget().getValues() ) for w in self.__inspectorWidgets )
		visible = numValues > 0

		self.setVisible( visible )
		if visible :
			self.__label.setText( "{} {}{}".format(
				numValues,
				self.__labelText,
				"s" if numValues != 1 else ""
			) )

## \todo Figure out how this relates to the DiffRow in the SceneInspector.
class _InspectorWidget( GafferUI.Widget ) :

	def __init__( self, inspector, context ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 2 )
		GafferUI.Widget.__init__( self, column )

		self.__inspector = inspector
		self.__context = context
		self.__locations = []

		with column :

			name = self.__inspector.name()
			if "_" in name :
				name = IECore.CamelCase.fromSpaced( name.replace( "_", " " ) )
			name = IECore.CamelCase.toSpaced( name )

			label = GafferUI.Label( text = "<h5>{}</h5>".format( name ) )
			label._qtWidget().setMaximumWidth( 140 )

			self.__valueWidget = _ValueWidget()
			self.__valueWidget.buttonDoubleClickSignal().connect( Gaffer.WeakMethod( self.__valueDoubleClick ), scoped = False )

		self.__inspectorResults = []
		self.__context.changedSignal().connect( Gaffer.WeakMethod( self.__contextChanged ), scoped = False )
		self.__inspector.dirtiedSignal().connect( Gaffer.WeakMethod( self.__inspectorDirtied ), scoped = False )

	def context( self ) :

		return self.__context

	def valueWidget( self ) :

		return self.__valueWidget

	def _backgroundUpdate( self ) :

		inspectorResults = []

		with Gaffer.Context( Gaffer.Context.current() ) as context :
			for path in GafferSceneUI.ContextAlgo.getSelectedPaths( context ).paths() :
				context.set( "scene:path", IECore.InternedStringVectorData( path[1:].split( "/" ) ) )
				inspectorResult = self.__inspector.inspect()
				if inspectorResult is not None :
					inspectorResults.append( inspectorResult )

		return inspectorResults

	def _backgroundUpdatePostCall( self, backgroundResult ) :

		if isinstance( backgroundResult, IECore.Cancelled ) :
			# Cancellation - schedule a later update.
			self.__scheduleUpdate()
		elif isinstance( backgroundResult, Gaffer.ProcessException ) :
			# Computation error. Rest of the UI can deal with
			# displaying this.
			self.setVisible( False )
		elif isinstance( backgroundResult, Exception ) :
			# Possible error in our code.
			IECore.msg(
				IECore.Msg.Level.Error, "_InspectorWidget",
				"".join( traceback.format_exception_only( type( backgroundResult ), backgroundResult ) )
			)
		else :
			# Success.
			self.__inspectorResults = backgroundResult
			self.__valueWidget.setValues( [ r.value() for r in self.__inspectorResults ] )
			# Set background to reflect the source type for each of the inspector results.
			sourceTypes = { r.sourceType() for r in self.__inspectorResults }
			if GafferSceneUI.Private.Inspector.Result.SourceType.Other in sourceTypes :
				# We don't draw any visual distinction between Upstream and Other.
				sourceTypes.add( GafferSceneUI.Private.Inspector.Result.SourceType.Upstream )
				sourceTypes.remove( GafferSceneUI.Private.Inspector.Result.SourceType.Other )

			self.__valueWidget._qtWidget().setProperty( "gafferInspectorSourceType", "|".join( sorted( str( s ) for s in sourceTypes ) ) )
			self.__valueWidget._repolish()
			self.setVisible( len( self.__inspectorResults ) > 0 )

	def __contextChanged( self, context, variableName ) :

		if variableName.startswith( "ui:" ) and not GafferSceneUI.ContextAlgo.affectsSelectedPaths( variableName ) :
			return

		self.__scheduleUpdate()

	def __inspectorDirtied( self, inspector ) :

		self.__scheduleUpdate()

	def __scheduleUpdate( self ) :

		# Avoid `Internal C++ object (PySide2.QtWidgets.QWidget) already deleted`
		# warnings when Gaffer is closed while we are in `_backgroundUpdate()`.
		# In this case, the main UI has been deleted, but we have been kept alive
		# by the BackgroundMethod.
		if not GafferUI._qtObjectIsValid( self._qtWidget() ) :
			return

		# Ideally, _InspectorWidget would be a completely standalone component
		# that managed its own updates internally via a BackgroundMethod. But
		# if many _InspectorWidgets launched their own background updates
		# concurrently, all but one would end up spinning while one thread
		# computed the cached attribute history that was needed by all. So for
		# now we coordinate updates centrally via the _SceneViewInspector so
		# that they are all performed together on the same thread.
		#
		# \todo Improve this situation. Possibilities include :
		#
		# - Using `tbb::task::suspend` to free threads that would otherwise
		#   have to wait for the cached history.
		# - Using a different `task_arena` to limit the concurrency of the
		#   background updates.

		self.ancestor( _SceneViewInspector )._scheduleUpdate( self )

	def __valueDoubleClick( self, widget, event ) :

		if event.button != event.Buttons.Left :
			return False

		if not self.__inspectorResults :
			return False

		if all( r.editable() for r in self.__inspectorResults ) :

			self.__popup = GafferUI.PlugPopup(
				list( { r.acquireEdit() for r in self.__inspectorResults } ),
				warning = self.__formatWarnings(
					[ r.editWarning() for r in self.__inspectorResults ]
				)
			)
			if isinstance( self.__popup.plugValueWidget(), GafferUI.TweakPlugValueWidget ) :
				self.__popup.plugValueWidget().setNameVisible( False )
			self.__popup.popup()

		else :

			with GafferUI.PopupWindow() as self.__popup :
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
					GafferUI.Image( "warningSmall.png" )
					GafferUI.Label( "<h4>{}</h4>".format(
						self.__formatWarnings( [ r.nonEditableReason() for r in self.__inspectorResults ] )
					) )

			self.__popup.popup()

		return True

	@staticmethod
	def __formatWarnings( strings ) :

		strings = { s for s in strings if s }
		if len( strings ) > 1 :
			return "\n".join( [ "- {}".format( w ) for s in strings ] )
		elif len( strings ) == 1 :
			return next( iter( strings ) )
		else :
			return ""

# Widget for displaying any value type.
## \todo Figure out relationship with SceneInspector's Diff widgets.
# It seems like they may all be subclasses of the same abstract base?
class _ValueWidget( GafferUI.Widget ) :

	def __init__( self, values = [], **kw ) :

		GafferUI.Widget.__init__( self, QtWidgets.QLabel(), **kw )

		self._qtWidget().setFixedHeight( 20 )
		self._qtWidget().setFixedWidth( 140 )

		self._qtWidget().setStyleSheet( "padding-left: 4px; padding-right: 4px;" )

		self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
		self.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ), scoped = False )
		self.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ), scoped = False )
		GafferUI.DisplayTransform.changedSignal().connect( Gaffer.WeakMethod( self.__updateLabel ), scoped = False )

		self.__values = []
		self.setValues( values )

	def setValues( self, values ) :

		if self.__values == values :
			return

		self.__values = values
		self.__updateLabel()

	def getValues( self ) :

		return self.__values

	def getToolTip( self ) :

		result = GafferUI.Widget.getToolTip( self )
		if result :
			return result

		if not self.__values or all( v == self.__values[0] for v in self.__values ) :
			# No values, or values all the same. No need for a tooltip.
			return ""

		return "\n".join(
			self.__formatValue( v ) for v in self.__values
		)

	def __updateLabel( self ) :

		if not len( self.__values ) :
			self._qtWidget().setText( "" )
			return

		if any( v != self.__values[0] for v in self.__values ) :
			# Mixed values
			self._qtWidget().setText( "---" )
			return

		# All values the same
		self._qtWidget().setText( self.__formatValue( self.__values[0] ) )

	@classmethod
	def __formatValue( cls, value ) :

		if isinstance( value, IECore.Data ) and hasattr( value, "value" ) :
			return cls.__formatValue( value.value )
		elif isinstance( value, ( int, float ) ) :
			return GafferUI.NumericWidget.valueToString( value )
		elif isinstance( value, imath.Color3f ) :
			color = GafferUI.Widget._qtColor( GafferUI.DisplayTransform.get()( value ) ).name()
			return "<table><tr><td bgcolor={} style=\"padding-right:12px\"></td><td style=\"padding-left:4px\">{}</td></tr></table>".format(
				color,
				cls.__formatValue( imath.V3f( value ) )
			)
		elif isinstance( value, ( imath.V3f, imath.V2f, imath.V3i, imath.V2i ) ) :
			return " ".join( GafferUI.NumericWidget.valueToString( x ) for x in value )
		elif value is None :
			return ""
		else :
			return str( value )

	def __dragData( self ) :

		if not self.__values :
			return None

		if all( v == self.__values[0] for v in self.__values ) :
			return self.__values[0]

		## \todo Where all values are of the same type, pack them
		# into `IECore.VectorData`.
		return None

	def __buttonPress( self, widget, event ) :

		return self.__dragData() is not None and event.buttons == event.Buttons.Left

	def __dragBegin( self, widget, event ) :

		if event.buttons != event.Buttons.Left :
			return None

		data = self.__dragData()
		if data is None :
			return None

		GafferUI.Pointer.setCurrent( "values" )
		return data

	def __dragEnd( self, widget, event ) :

		GafferUI.Pointer.setCurrent( None )
