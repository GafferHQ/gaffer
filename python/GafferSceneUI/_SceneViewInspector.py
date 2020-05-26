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
import traceback

import imath

import IECore
import IECoreScene

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

__all__ = [ "_SceneViewInspector", "_ParameterInspector" ]

## \todo Add registration mechanism to determine which parameters are shown,
# and make sure we support Appleseed/3Delight lights out of the box.
_parameters = [ "exposure", "color", "radius", "cone_angle", "penumbra_angle", "spread" ]

# Conceptually this is an embedded context-sensitive SceneInspector for
# the SceneView. In practice it is implemented completely separately from
# the SceneInspector though, because the SceneInspector doesn't yet support
# editing and/or EditScopes. Our intention is to unify the two so that the
# SceneInspector gains editing features and this can become just a thin
# wrapper to do the configuration and embedding for the Viewer. We also
# intend to move many of the components into GafferUI, so that they can
# be used in the development of an ImageInspector too.
#
# Future development should consider the following :
#
# - It may be better for the inspector classes to track their
#   own dirtiness, rather than rely on the outer code for that.
#   And it may be better for each `_ParameterWidget/DiffRow` to manage
#   its own background updates based on inspector dirtiness.
#   This would allow individual widgets to be used standalone in
#   any other UI.
# - Moving tracking and updates to individual widgets/inspectors
#   would make it harder to share work. All parameter inspectors
#   need the same `AttributeHistory` to work from, and we don't
#   want to compute that more than once. The SceneInspector uses
#   an inspector hierarchy, so maybe this would allow us to cache
#   shared values on a parent inspector?
# - We want to extend our inspection/editing features into the
#   HierarchyView and a new LightEditor panel. This will likely
#   mean coupling inspectors with PathListingWidget somehow. Or
#   perhaps we should be using Path properties to provide values
#   for all UIs, and the editing functionality should be provided
#   separately?
# - It's not clear how the SceneInspector's `Target` class fits
#   into a general scheme that could include images, because it
#   contains scene-specific data. Perhaps we should ditch
#   `Target` entirely, and instead say that inspectors always
#   operate on the plug they are constructed with and in the
#   Context they are invoked in.
#
class _SceneViewInspector( GafferUI.Widget ) :

	def __init__( self, sceneView ) :

		self.__frame = GafferUI.Frame()
		GafferUI.Widget.__init__( self, self.__frame )

		self.__sceneView = sceneView

		with self.__frame :

			with GafferUI.ListContainer( spacing = 8 ) :

				with GafferUI.ListContainer(
					orientation = GafferUI.ListContainer.Orientation.Horizontal,
					spacing = 4
				) :
					GafferUI.Label( "<h4>Inspector</h4>" )
					GafferUI.Spacer( imath.V2i( 1 ) )
					self.__busyWidget = GafferUI.BusyWidget( size = 20, busy = False )

				GafferUI.Divider()

				with GafferUI.Collapsible( "Arnold Lights" ) as self.__arnoldLightsCollapsible :
					with GafferUI.ListContainer( spacing = 4 ) :
						self.__parameterWidgets = {}
						for parameter in _parameters :
							self.__parameterWidgets[parameter] = _ParameterWidget( parameter )

		self.__frame.setVisible( False )

		sceneView.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ), scoped = False )
		sceneView.getContext().changedSignal().connect( Gaffer.WeakMethod( self.__contextChanged ), scoped = False )

	def __plugDirtied( self, plug ) :

		if plug in ( self.__sceneView["in"]["attributes"], self.__sceneView["editScope"] ) :
			self.__updateLazily()

	def __contextChanged( self, context, name ) :

		if GafferSceneUI.ContextAlgo.affectsSelectedPaths( name ) or not name.startswith( "ui:" ) :
			self.__updateLazily()

	@GafferUI.LazyMethod()
	def __updateLazily( self ) :

		with self.__sceneView.getContext() :
			self.__backgroundUpdate()

	@GafferUI.BackgroundMethod()
	def __backgroundUpdate( self ) :

		try :

			selectedPaths = GafferSceneUI.ContextAlgo.getSelectedPaths( Gaffer.Context.current() )
			parameters = {}

			for path in selectedPaths.paths() :
				if not self.__sceneView["in"].exists( path ) :
					continue
				history = GafferScene.SceneAlgo.history( self.__sceneView["in"]["attributes"], path )
				attributeHistory = GafferScene.SceneAlgo.attributeHistory( history, "ai:light" )
				if attributeHistory is not None :
					for parameter in _parameters :
						parameters.setdefault( parameter, [] ).append(
							_ParameterInspector( attributeHistory, parameter, self.__sceneView.editScope() )
						)

			return parameters

		except :
			import traceback
			import sys
			traceback.print_tb( sys.exc_info()[2] )
			raise

	@__backgroundUpdate.plug
	def __backgroundUpdatePlug( self ) :

		return self.__sceneView["in"]

	@__backgroundUpdate.preCall
	def __backgroundUpdatePreCall( self ) :

		self.__busyWidget.setBusy( True )

	@__backgroundUpdate.postCall
	def __backgroundUpdatePostCall( self, backgroundResult ) :

		if isinstance( backgroundResult, IECore.Cancelled ) or backgroundResult is None :
			self.__updateLazily()
		elif isinstance( backgroundResult, Gaffer.ProcessException ) :
			# Computation error. Rest of the UI can deal with
			# displaying this.
			self.__frame.setVisible( False )
		elif isinstance( backgroundResult, Exception ) :
			# Possible error in our code.
			IECore.msg(
				IECore.Msg.Level.Error, "_SceneViewInspector",
				"".join( traceback.format_exception_only( type( backgroundResult ), backgroundResult ) )
			)
		else :
			# Success.
			numLights = 0
			for parameter, widget in self.__parameterWidgets.items() :
				inspectors = backgroundResult.get( parameter, [] )
				numLights = max( numLights, len( [ i for i in inspectors if i.value() is not None ] ) )
				widget.update( inspectors )

			self.__arnoldLightsCollapsible.setLabel( "{} Arnold Light{}".format( numLights, "s" if numLights != 1 else "" ) )
			self.__frame.setVisible( numLights > 0 )

		self.__busyWidget.setBusy( False )

## \todo Figure out how this relates to the inspectors in
# the SceneInspector.
class _ParameterInspector( object ) :

	def __init__( self, attributeHistory, parameter, editScope ) :

		self.__parameter = parameter
		self.__errorMessage = None
		self.__warningMessage = None

		shader = attributeHistory.attributeValue.outputShader()
		self.__value = shader.parameters.get( parameter )
		if self.__value is not None :
			if hasattr( self.__value, "value" ) :
				self.__value = self.__value.value
			self.__editFunction, self.__hasEditFunction = self.__makeEditFunction( attributeHistory, editScope )
		else :
			self.__editFunction = None
			self.__hasEditFunction = None

	def value( self ) :

		return self.__value

	def editable( self ) :

		return self.__editFunction is not None

	def acquireEdit( self ) :

		return self.__editFunction() if self.__editFunction is not None else None

	def hasEdit( self ) :

		return self.__hasEditFunction() if self.__hasEditFunction is not None else False

	def warningMessage( self ) :

		return self.__warningMessage

	def errorMessage( self ) :

		return self.__errorMessage

	def __editFunctionFromSceneNode( self, attributeHistory ) :

		node = attributeHistory.scene.node()
		if not isinstance( node, ( GafferScene.ShaderTweaks, GafferScene.Light ) ) :
			return None, None

		if attributeHistory.scene != node["out"] :
			return None, None

		## \todo Find source plug for the plugs we find here. Even if its a spreadsheet cell.
		# TransformTool has a private `spreadsheetAwareSource()` that seems to do this - should
		# it just go in PlugAlgo?
		if isinstance( node, GafferScene.Light ) :
			return ( lambda : node["parameters"][self.__parameter], lambda : True )
		elif isinstance( node, GafferScene.ShaderTweaks ) :
			with attributeHistory.context :
				if not node["filter"].getValue() & IECore.PathMatcher.Result.ExactMatch :
					return None, None
				for tweak in node["tweaks"] :
					if tweak["name"].getValue() == self.__parameter :
						self.__errorMessage = None
						return ( lambda : tweak, lambda : True )

		return None, None

	def __makeEditFunction( self, attributeHistory, editScope ) :

		if editScope is not None :
			scriptNode = editScope.ancestor( Gaffer.ScriptNode )
			with scriptNode.context() if scriptNode is not None else Gaffer.Context() :
				if not editScope["enabled"].getValue() :
					self.__errorMessage = "Target EditScope is disabled"
					return None, None

		node = attributeHistory.scene.node()
		if isinstance( node, Gaffer.EditScope ) and attributeHistory.scene == node["out"] :

			if node == editScope :

				def editScopeEdit( attributeHistory, parameter ) :

					with attributeHistory.context :
						return GafferScene.EditScopeAlgo.acquireParameterEdit(
							attributeHistory.scene.node(),
							attributeHistory.context["scene:path"],
							attributeHistory.attributeName,
							IECoreScene.ShaderNetwork.Parameter( "", parameter ),
						)

				def editScopeHasEdit( attributeHistory, parameter ) :

					with attributeHistory.context :
						hasEdit = GafferScene.EditScopeAlgo.hasParameterEdit(
							attributeHistory.scene.node(),
							attributeHistory.context["scene:path"],
							attributeHistory.attributeName,
							IECoreScene.ShaderNetwork.Parameter( "", parameter ),
						)
						if not hasEdit :
							return False

						tweak = GafferScene.EditScopeAlgo.acquireParameterEdit(
							attributeHistory.scene.node(),
							attributeHistory.context["scene:path"],
							attributeHistory.attributeName,
							IECoreScene.ShaderNetwork.Parameter( "", parameter ),
						)
						return  tweak["enabled"].getValue()

				editFn = functools.partial( editScopeEdit, attributeHistory, self.__parameter )
				hasEditFn = functools.partial( editScopeHasEdit, attributeHistory, self.__parameter )

				self.__errorMessage = None
				return editFn, hasEditFn

			elif editScope is None :

				# We have encountered an EditScope node, but have not been told to use
				# one. We could continue our search upstream, but we take the position that
				# if EditScopes are present, we shouldn't make any edits outside of one.
				self.__errorMessage = "EditScopes in graph but none targeted for edit"
				return None, None

		else :

			e, h = self.__editFunctionFromSceneNode( attributeHistory )
			if e is not None :
				if editScope is None or editScope.isAncestorOf( attributeHistory.scene ) :
					return e, h
				elif editScope is not None :
					# We could edit this node, but it's downstream of the EditScope we've been
					# asked to use
					self.__warningMessage = "Edits in this scope may be overriden downstream"

		for p in attributeHistory.predecessors :
			e, h = self.__makeEditFunction( p, editScope )
			if e is not None :
				return e, h

		if editScope is not None and not self.__errorMessage:
			self.__errorMessage = "Target EditScope is not in the scene history"

		return None, None

## \todo Figure out how this relates to the DiffRow in the SceneInspector.
class _ParameterWidget( GafferUI.Widget ) :

	def __init__( self, parameter ) :

		self.__parameter = parameter

		grid = GafferUI.GridContainer( spacing = 4 )
		GafferUI.Widget.__init__( self, grid )

		self.__inspectors = []

		with grid :

			GafferUI.Label(
				## \todo Prettify label text (remove snake case)
				text = "<h5>" + IECore.CamelCase.toSpaced( parameter ) + "</h5>",
				parenting = { "index" : ( slice( 0, 4 ), 0 ) }
			)

			with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal, parenting = { "index" : ( 0, 1 ), "alignment" : ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Center ) } ) :

				self.__errorBadge = GafferUI.Image( "errorSmall.png" )

				self.__editButton = GafferUI.Button( image = "editOff.png", hasFrame = False )
				self.__editButton.clickedSignal().connect( Gaffer.WeakMethod( self.__editButtonClicked ), scoped = False )

			self.__valueWidget = _ValueWidget( parenting = { "index" : ( 2, 1 ) } )
			self.__valueWidget.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__valueWidgetClicked ), scoped = False )

			self.__warningBadge = GafferUI.Image( "warningSmall.png", parenting = { "index" : ( 3, 1 ) } )


		self.update( [] )

	def update( self, inspectors ) :

		inspectors = [ i for i in inspectors if i.value() is not None ]

		self.setVisible( inspectors )

		self.__valueWidget.setValues( [ i.value() for i in inspectors ] )

		editable = bool( inspectors ) and all( i.editable() for i in inspectors )
		hasEdit = bool( inspectors ) and all( i.hasEdit() for i in inspectors )

		image = "editDisabled.png"
		if editable :
			image = "editOn.png" if hasEdit else "editOff.png"

		errors = [ i.errorMessage() for i in inspectors if i.errorMessage() ]
		errorStr = "\n".join( errors )
		self.__errorBadge.setVisible( errors )
		self.__errorBadge.setToolTip( errorStr )

		warnings = [ i.warningMessage() for i in inspectors if i.warningMessage() ]
		warningStr = "\n".join( warnings )
		self.__warningBadge.setToolTip( warningStr )
		self.__warningBadge.setVisible( warnings and not errors )

		self.__editButton.setToolTip( "Click to edit" if hasEdit else "Click to add an edit" )
		self.__editButton.setImage( image )
		self.__editButton.setEnabled( editable )
		self.__editButton.setVisible( not errors )

		self.__valueWidget.setToolTip( errorStr if errors else ( "Click to Edit" if hasEdit else "" ) )

		self.__inspectors = inspectors

	def __editButtonClicked( self, button ) :

		self.__edit()

	def __valueWidgetClicked( self, *unused ) :

		if bool( self.__inspectors ) and all( i.hasEdit() for i in self.__inspectors ) :
			self.__edit	()

	def __edit( self ) :

		plugs = [ v.acquireEdit() for v in self.__inspectors ]
		self.__editWindow = _EditWindow( plugs )
		self.__editWindow.popup( self.bound().center() + imath.V2i( 0, 45 ) )

## \todo How does this relate to PopupWindow and SpreadsheetUI._EditWindow?
class _EditWindow( GafferUI.Window ) :

	def __init__( self, plugs, **kw ) :

		container = GafferUI.ListContainer( spacing = 4 )
		GafferUI.Window.__init__( self, "", child = container, borderWidth = 8, sizeMode=GafferUI.Window.SizeMode.Automatic, **kw )

		for p in plugs :
			## \todo Figure out when/if this is about to happen, and disable
			# editing beforehand.
			assert( isinstance( p, plugs[0].__class__ ) )

		self._qtWidget().setWindowFlags( QtCore.Qt.Popup )
		self._qtWidget().setAttribute( QtCore.Qt.WA_TranslucentBackground )
		self._qtWidget().paintEvent = Gaffer.WeakMethod( self.__paintEvent )

		with container :

			# Label to tell folks what they're editing.

			labels = { self.__plugLabel( p ) for p in plugs }
			label = GafferUI.Label()
			if len( labels ) == 1 :
				label.setText( "<h4>{}</h4>".format( next( iter( labels ) ) ) )
			else :
				label.setText( "<h4>{} plugs</h4>".format( len( labels ) ) )
				label.setToolTip(
					"\n".join( "- " + l for l in labels )
				)

			# Widget for editing plugs

			plugValueWidget = GafferUI.PlugValueWidget.create( plugs )
			if isinstance( plugValueWidget, GafferSceneUI.TweakPlugValueWidget ) :
				## \todo We have this same hack in SpreadsheetUI. Should we instead
				# do something with metadata when we add the column to the spreadsheet?
				plugValueWidget.setNameVisible( False )

		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )

	def popup( self, position ) :

		size = self._qtWidget().sizeHint()
		self.setPosition( position - imath.V2i( size.width() / 2, size.height() / 2 ) )
		self.setVisible( True )

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

	def __plugLabel( self, plug ) :

		editScope = plug.ancestor( Gaffer.EditScope )
		if editScope is not None :
			return editScope.relativeName( editScope.ancestor( Gaffer.ScriptNode ) )
		else :
			return plug.relativeName( plug.ancestor( Gaffer.ScriptNode ) )

# Widget for displaying any value type.
## \todo Figure out relationship with SceneInspector's Diff widgets.
# It seems like they may all be subclasses of the same abstract base?
class _ValueWidget( GafferUI.Widget ) :

	def __init__( self, values = [], **kw ) :

		GafferUI.Widget.__init__( self, QtWidgets.QLabel(), **kw )

		self._qtWidget().setMinimumHeight( 20 )
		self._qtWidget().setMinimumWidth( 140 )

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

		if isinstance( value, ( int, float ) ) :
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
