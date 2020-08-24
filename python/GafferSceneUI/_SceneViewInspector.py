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

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

__all__ = [ "_SceneViewInspector", "_ParameterInspector" ]

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

# \todo Create a central renderer/attribute registry that we can
# query for this information, this is also duplicated in EditScopeAlgo.cpp
_rendererAttributePrefixes = {
	"ai" : "Arnold",
	"dl" : "Delight",
	"as" : "Appleseed",
	"gl" : "OpenGL",
	"osl" : "OSL",
	"ccl" : "Cycles"
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

		with self.__frame :

			with GafferUI.ListContainer( spacing = 8 ) :

				with GafferUI.ListContainer(
					orientation = GafferUI.ListContainer.Orientation.Horizontal,
					spacing = 8
				) :
					GafferUI.Spacer( imath.V2i( 12 ), imath.V2i( 12 ) ) # hideButton
					GafferUI.Spacer( imath.V2i( 20 ), imath.V2i( 20 ) ) # BusyWidget
					GafferUI.Spacer( imath.V2i( 1 ) )
					GafferUI.Label( "<h4 style=\"color: rgba( 255, 255, 255, 120 );\">Inspector</h4>" )
					GafferUI.Spacer( imath.V2i( 1 ) )
					self.__busyWidget = GafferUI.BusyWidget( size = 20, busy = False )
					hideButton = GafferUI.Button( image="deleteSmall.png", hasFrame=False )
					hideButton.clickedSignal().connect( Gaffer.WeakMethod( self.__closeButtonClicked ), scoped = False )

				with GafferUI.ScrolledContainer( horizontalMode = GafferUI.ScrollMode.Never ) :
					with GafferUI.ListContainer( spacing = 20 ) :
						self.__groups = { a : _ParameterGroup(a) for a in _registeredShaderAttributes() }

		# The on/off state of the Inspector is managed by setVisible, which also disables lazy updates when
		# we're turned off. We desire to hide ourselves when we have nothing to show, but still need background
		# updates so we can re-appear as needed. We achieve this by managing the visibility of our frame,
		# independently of the widget.
		self.__frame.setVisible( False )

		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False)

		Gaffer.Metadata.nodeValueChangedSignal().connect( Gaffer.WeakMethod( self.__nodeMetadataChanged ), scoped = False )
		Gaffer.Metadata.plugValueChangedSignal().connect( Gaffer.WeakMethod( self.__plugMetadataChanged ), scoped = False )

	def setVisible( self, visible ) :

		# The view.inspector.visible plug is the authority on whether the
		# inspector should be visible. setVisible may be called by our parent
		# layout as its visibility changes. We need to ensure we don't appear
		# if the user has disabled us. Considering the plug state here allows
		# allows us to take advantage of @lazymethod deferring updates whilst
		# we have been turned off.
		if visible == self.__sceneView["inspector"]["visible"].getValue() :
			GafferUI.Widget.setVisible( self, visible )
			if visible :
				self.__updateLazily()
		else :
			GafferUI.Widget.setVisible( self, False )

	def __attachToView( self, sceneView ) :

		# We add plugs to manage our visibility as per grid/gnomon. This plug is the
		# authoritative source for visibility, and is checked in setVisible.
		sceneView.addChild( Gaffer.ValuePlug( "inspector" ) )
		sceneView["inspector"].addChild( Gaffer.BoolPlug( "visible", Gaffer.Plug.Direction.In, True ) )
		Gaffer.NodeAlgo.applyUserDefaults( sceneView["inspector"] )

		sceneView.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ), scoped = False )
		sceneView.getContext().changedSignal().connect( Gaffer.WeakMethod( self.__contextChanged ), scoped = False )
		sceneView.viewportGadget().keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )

		self.__sceneView = sceneView

	def __closeButtonClicked( self, *unused ) :

		self.__sceneView["inspector"]["visible"].setValue( False )

	def __plugDirtied( self, plug ) :

		if plug in ( self.__sceneView["in"]["attributes"], self.__sceneView["editScope"] ) :
			self.__updateLazily()
		elif plug.isSame( self.__sceneView["inspector"]["visible"] ) :
			self.setVisible( plug.getValue() )

	def __contextChanged( self, context, name ) :

		if GafferSceneUI.ContextAlgo.affectsSelectedPaths( name ) or not name.startswith( "ui:" ) :
			self.__updateLazily()

	def __plugMetadataChanged( self, typeId, plugPath, key, plug  ) :

		# As we don't fully understand which nodes/plugs affect our ability to edit (as the network
		# inside the edit scope is effectively opaque to us), we only need to know if the plugs
		# node was affected.
		self.__nodeMetadataChanged( typeId, key, plug.node() if plug is not None else None )

	def __nodeMetadataChanged( self, typeId, key, node ) :

		# Early out with an easy comparison if we can
		if not Gaffer.MetadataAlgo.readOnlyAffectedByChange( key ) :
			return

		scope = self.__sceneView.editScope()
		if scope is None :
			# The ability to add an edit is only enabled if we have an edit scope, in all other
			# cases we always show plugs, whether they're read only or not.
			return

		if Gaffer.MetadataAlgo.readOnlyAffectedByChange( scope, typeId, key, node ) or scope.isAncestorOf( node ) :
			self.__updateLazily()

	def __keyPress( self, gadget, event ) :

		if event.key == "I" and event.modifiers == GafferUI.ModifiableEvent.Modifiers.None_ :
			visible = self.__sceneView["inspector"]["visible"].getValue()
			self.__sceneView["inspector"]["visible"].setValue( not visible )
			return True

		return False

	@GafferUI.LazyMethod()
	def __updateLazily( self ) :

		with self.__sceneView.getContext() :
			self.__backgroundUpdate()

	@GafferUI.BackgroundMethod()
	def __backgroundUpdate( self ) :

		selectedPaths = GafferSceneUI.ContextAlgo.getSelectedPaths( Gaffer.Context.current() )

		parameterInspectors = {}

		for path in selectedPaths.paths() :
			if not self.__sceneView["in"].exists( path ) :
				continue
			history = GafferScene.SceneAlgo.history( self.__sceneView["in"]["attributes"], path )
			for attribute, group in self.__groups.items() :
				attributeHistory = GafferScene.SceneAlgo.attributeHistory( history, attribute )
				if attributeHistory is not None :
					for parameter in group.parameters() :
						parameterInspectors.setdefault( attribute, {} ).setdefault( parameter, [] ).append(
							_ParameterInspector( attributeHistory, parameter, self.__sceneView.editScope() )
						)

		return parameterInspectors

	@__backgroundUpdate.plug
	def __backgroundUpdatePlug( self ) :

		return self.__sceneView["in"]

	@__backgroundUpdate.preCall
	def __backgroundUpdatePreCall( self ) :

		self.__busyWidget.setBusy( True )

	@__backgroundUpdate.postCall
	def __backgroundUpdatePostCall( self, backgroundResult ) :

		if isinstance( backgroundResult, IECore.Cancelled ) or backgroundResult is None :
			# Cancellation or some other exception
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
			visible = False
			for attribute, group in self.__groups.items() :
				visible = group.update( backgroundResult.get( attribute, {} ) ) or visible
			self.__frame.setVisible( visible )

		self.__busyWidget.setBusy( False )


# \todo Check how this relates to DiffColumn in the SceneInspector
class _ParameterGroup( GafferUI.ListContainer ) :

	def __init__( self, attribute, **kwargs ) :

		GafferUI.ListContainer.__init__( self, spacing = 8, **kwargs )
		self.__attribute = attribute
		self.__widgets = {}

		with self :

			self.__label = GafferUI.Label( self.__attributeLabel( attribute ) )

			GafferUI.Divider()

			for parameter in _registeredShaderParameters( self.__attribute ) :
				self.__widgets[ parameter ] = _ParameterWidget( parameter )

	def parameters( self ) :

		return self.__widgets.keys()

	def update( self, parameterInspectors ) :

		numValues = 0

		for parameter, inspectors in parameterInspectors.items() :
			self.__widgets[ parameter ].update( inspectors )
			numValues = max( numValues, len( [ i for i in inspectors if i.value() is not None ] ) )

		visible = numValues > 0

		self.setVisible( visible )
		if visible :
			self.__label.setText( "{} {}{}".format(
				numValues,
				self.__attributeLabel( self.__attribute ),
				"s" if numValues != 1 else ""
			) )

		return visible

	def __attributeLabel( self, attribute ) :

		prefix, name = attribute.split( ":", 1 )
		prefix = _rendererAttributePrefixes.get( prefix, prefix )
		name = " ".join( [ IECore.CamelCase.toSpaced( n ) for n in name.split( ":" ) ] )
		return "{} {}".format( prefix, name )

# EditType defines discrete parameter edit types. The inspector UI assumes that all
# locations with the same edit type can be edited simultaneously using a single
# PlugValueWidget set to hold all applicable plugs.
_EditType = IECore.Enum.create( "Source", "Tweak" )

# Defines a (potential) edit for a single location.
#  - acquireEdit [callable] will return the plug that performs the edit, creating it if necessary.
#  - editType [_EditType] the type of edit (or potential edit if one doesn't exist yet) facilitated by the plug.
#  - inEditScope [Bool] True if the node affecting the edit is a child of an EditScope.
#  - hasEdit [Bool] True if the plugs for the edit already exist, and in the case of tweaks,
#       if they are enabled.
_EditInfo = namedtuple( "_EditInfo", [ "acquireEdit", "editType", "inEditScope", "hasEdit" ] )

## \todo Figure out how this relates to the inspectors in the SceneInspector.
## \see _EditInfo for the meaning of the various accessors.
class _ParameterInspector( object ) :

	def __init__( self, attributeHistory, parameter, editScope ) :

		self.__parameter = parameter
		self.__errorMessage = None
		self.__warningMessages = []

		shader = attributeHistory.attributeValue.outputShader()
		self.__value = shader.parameters.get( parameter )
		if self.__value is not None :
			if hasattr( self.__value, "value" ) :
				self.__value = self.__value.value
			self.__editInfo = self.__findEdit( attributeHistory, editScope )
		else :
			self.__editInfo = None

	def value( self ) :

		return self.__value

	def editable( self ) :

		return self.__editInfo is not None

	def acquireEdit( self ) :

		return self.__editInfo.acquireEdit() if self.__editInfo else None

	def editType( self ) :

		return self.__editInfo.editType  if self.__editInfo else None

	def hasEdit( self ) :

		return self.__editInfo.hasEdit if self.__editInfo else None

	def inEditScope( self ) :

		return self.__editInfo.inEditScope if self.__editInfo else False

	def warningMessage( self ) :

		return "\n".join( self.__warningMessages )

	def errorMessage( self ) :

		return self.__errorMessage if self.__errorMessage is not None else ""

	## \todo This is a modified copy of TransformTool::spreadsheetAwareSource,
	# and is eerily similar to Dispatcher::computedSource and others. This needs
	# factoring out into some general contextAwareSource method that can be
	# shared by all these.
	# In this case, we also need to make sure we never return an output plug,
	# such as when it is connected to an anim curve.
	def __spreadsheetAwareSource( self, plug ) :

		source = plug.source()
		spreadsheet = source.node()

		if not isinstance( spreadsheet, Gaffer.Spreadsheet ) :
			return sourceInput( plug )

		if not spreadsheet["out"].isAncestorOf( source ) :
			return sourceInput( plug )

		valuePlug = spreadsheet.activeInPlug( source )
		if valuePlug.ancestor( Gaffer.Spreadsheet.RowPlug ).isSame( spreadsheet["rows"].defaultRow() ) :
			return None

		return sourceInput( valuePlug )

	def __sourceShader( self, plug ) :

		node = plug.source().node()
		if isinstance( node, Gaffer.Switch ) :
			node = node.activeInPlug().source().node()
		return node if isinstance( node, GafferScene.Shader ) else None

	def __editFromSceneNode( self, attributeHistory ) :

		node = attributeHistory.scene.node()
		if not isinstance( node, ( GafferScene.ShaderTweaks, GafferScene.Light, GafferScene.LightFilter, GafferScene.ShaderAssignment ) ) :
			return None

		if attributeHistory.scene != node["out"] :
			return None

		with attributeHistory.context :

			if not node["enabled"].getValue() :
				return None

			if "filter" in node and not ( node["filter"].getValue() & IECore.PathMatcher.Result.ExactMatch ) :
				return None

			if isinstance( node, ( GafferScene.Light, GafferScene.LightFilter ) ) :

				plug = self.__spreadsheetAwareSource( node["parameters"][ self.__parameter ] )
				if plug is not None :
					return _EditInfo(
						acquireEdit = lambda : plug,
						editType = _EditType.Source,
						inEditScope = node.ancestor( Gaffer.EditScope ) is not None,
						hasEdit = True
					)
				return None

			elif isinstance( node, GafferScene.ShaderAssignment ) :

				# \todo use `computedSource` or similar when we have it to consider switches, etc...
				shader = self.__sourceShader( node["shader"] )
				if shader is not None :
					plug = shader["parameters"].getChild( self.__parameter )
					if plug is not None :
						return _EditInfo(
							acquireEdit = lambda : plug,
							editType = _EditType.Source,
							inEditScope = node.ancestor( Gaffer.EditScope ) is not None,
							hasEdit = True
						)
				return None

			elif isinstance( node, GafferScene.ShaderTweaks ) :

				for tweak in node["tweaks"] :
					if tweak["name"].getValue() == self.__parameter :
						tweak = self.__spreadsheetAwareSource( tweak )
						if tweak is not None :
							return _EditInfo(
								acquireEdit = lambda : tweak,
								editType = _EditType.Tweak,
								inEditScope = node.ancestor( Gaffer.EditScope ) is not None,
								hasEdit = tweak["enabled"].getValue()
							)
						return None

		return None

	def __editFromEditScope( self, attributeHistory ) :

		editScope = attributeHistory.scene.node()

		# \todo This misses cases where the processor has been disabled.
		# Migrate to EditScopeAlgo functionality once it's available.
		with attributeHistory.context :

			if not editScope["enabled"].getValue() :
				self.__error( "The target Edit Scope '{}' is disabled.", editScope )
				return None

			readOnlyReason = GafferScene.EditScopeAlgo.parameterEditReadOnlyReason(
				editScope,
				attributeHistory.context["scene:path"],
				attributeHistory.attributeName,
				IECoreScene.ShaderNetwork.Parameter( "", self.__parameter )
			)
			if readOnlyReason is not None :
				# If we don't have an edit and the scope is locked, we error,
				# as we can't add an edit. Other cases where we already _have_
				# an edit will have been found by _editFromSceneNode).
				self.__error( "'{}' is locked.", readOnlyReason )
				return None

		def editScopeEdit( attributeHistory, parameter ) :

			with attributeHistory.context :
				return GafferScene.EditScopeAlgo.acquireParameterEdit(
					editScope,
					attributeHistory.context["scene:path"],
					attributeHistory.attributeName,
					IECoreScene.ShaderNetwork.Parameter( "", parameter )
				)

		return _EditInfo(
			acquireEdit = functools.partial( editScopeEdit, attributeHistory, self.__parameter ),
			editType = _EditType.Tweak,
			inEditScope = True,
			hasEdit = self.__editScopeHasEdit( attributeHistory )
		)

	def __editScopeHasEdit( self, attributeHistory ) :

		with attributeHistory.context :

			tweak = GafferScene.EditScopeAlgo.acquireParameterEdit(
				attributeHistory.scene.node(),
				attributeHistory.context["scene:path"],
				attributeHistory.attributeName,
				IECoreScene.ShaderNetwork.Parameter( "", self.__parameter ),
				createIfNecessary = False
			)

			if tweak is None :
				return False

			return tweak["enabled"].getValue()

	def __findEdit( self, attributeHistory, editScope ) :

		# Walk through the attributeHistory, looking for a suitable edit, based on the user's chosen editScope.

		node = attributeHistory.scene.node()

		if isinstance( node, Gaffer.EditScope ) and attributeHistory.scene == node["in"] :

			# We are leaving an EditScope. We consider EditScopes on the way out to allow other
			# nodes within the scope to take precedence. An existing edit in the scope will
			# be picked up via __editFromSceneNode, which is spreadsheet aware.
			if node.isSame( editScope ) :
				return self.__editFromEditScope( attributeHistory )

		else :

			# Some other node affecting a change, see if we understand it.

			edit = self.__editFromSceneNode( attributeHistory )
			if edit is not None :

				# We can potentially make use of this node

				# Check the first parent scope of the edit, as they may be nested
				parentEditScope = attributeHistory.scene.ancestor( Gaffer.EditScope )

				if edit.hasEdit and ( editScope is None or editScope.isSame( parentEditScope ) ) :
					# If no editScope has been specified, or we're inside the target edit scope,
					# then we can safely use this edit if we have one.
					# The hasEdit check is deliberate to ensure that we don't include 'potential' targets, such
					# as disabled tweak nodes. Our semantics for editScope == None is that we only consider nodes
					# actually making a change to the scene at the time.
					if edit.hasEdit and isinstance( node, GafferScene.ShaderAssignment ) :
						self.__warn( "Edits to '{}' may affect other locations in the scene.", edit.acquireEdit().node() )
					return edit

				elif edit.hasEdit and editScope is not None :
					# If an edit scope has been specified, but we're not inside of it, then we shouldn't
					# use this node. We are downstream of any potential edit though, so do however need
					# to warn people that any edits they do make may be overridden by this node.
					displayNode = node.ancestor( Gaffer.EditScope ) or node
					self.__warn( "Parameter has edits downstream in '{}'.", displayNode )

		# If we haven't found an edit here, walk up the history
		for p in attributeHistory.predecessors :
			edit = self.__findEdit( p, editScope )
			if edit is not None :
				return edit

		if editScope is not None and not self.__errorMessage:
			# If we've not been able to find an edit, and we have a scope
			# specified, then we musn't have passed through the edit scope
			self.__error( "The target Edit Scope '{}' is not in the scene history.", editScope )

		return None

	def __warn( self, message, node ) :

		self.__warningMessages.append( message.format( self.__displayName( node ) ) )

	def __error( self, message, node ) :

		self.__errorMessage = message.format( self.__displayName( node ) )
		# We clear out the warnings in the case of an error to prevent confusion in the UI
		self.__warningMessages = []

	@staticmethod
	def __displayName( node ) :

		return node.relativeName( node.ancestor( Gaffer.ScriptNode ) )

## \todo Figure out how this relates to the DiffRow in the SceneInspector.
class _ParameterWidget( GafferUI.Widget ) :

	def __init__( self, parameter ) :

		self.__parameter = parameter

		grid = GafferUI.GridContainer( spacing = 2 )
		GafferUI.Widget.__init__( self, grid )

		self.__inspectors = []

		with grid :

			GafferUI.Label(
				## \todo Prettify label text (remove snake case)
				text = "<h5>" + IECore.CamelCase.toSpaced( parameter ) + "</h5>",
				parenting = { "index" : ( slice( 0, 2 ), 0 ) }
			)

			self.__editButton = GafferUI.Button( image = "editOff.png", hasFrame = False,
				parenting = {
					"index" : ( 0, 1 ),
					"alignment" : ( GafferUI.HorizontalAlignment.Center, GafferUI.VerticalAlignment.Center )
				}
			)
			self.__editButton.clickedSignal().connect( Gaffer.WeakMethod( self.__editButtonClicked ), scoped = False )

			self.__valueWidget = _ValueWidget( parenting = { "index" : ( 1, 1 ) } )
			self.__valueWidget.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__valueWidgetClicked ), scoped = False )

		self.update( [] )

	def update( self, inspectors ) :

		# The somewhat intricate logic here attempts to determine whether we should present the user
		# with an edit button for the parameter for the selected locations. This needs to consider:
		#
		# - Is the whole selection editable, we deliberately don't allow any edits, if any locations aren't.
		# - Is there only on type of edit. We can't concurrently edit tweaks and standard numeric node plugs.
		# - Do all locations currently have edits. We allow editing in this case, but only if we can create the edits.
		# - In 'Automatic' Edit Scope mode, is an existing edit in a scope or not.
		#
		# Based on this, we update the styling of the UI to attempt to clue the user into the current state.

		inspectors = [ i for i in inspectors if i.value() is not None ]

		# Only show something if we have any inspectors for this parameter
		self.setVisible( inspectors )

		# Display the current values
		self.__valueWidget.setValues( [ i.value() for i in inspectors ] )

		# We can only edit if all of them are editable
		self.__editable = bool( inspectors ) and all( i.editable() for i in inspectors )

		errors = [ i.errorMessage() for i in inspectors if i.errorMessage() ]
		warnings = [ i.warningMessage() for i in inspectors if i.warningMessage() ]

		# Ensure we aren't trying to present multiple types of edit
		editType = sole( i.editType() for i in inspectors if i.editable() )
		if self.__editable and editType is None :
			# None implies there are multiple edit types, disable editing.
			errors.append( "Selected locations have mixed Tweak and Source edits, the Inspector can only edit one kind at once." )
			self.__editable = False

		# Will be None if there are a mixture of edited and unedited locations. We won't be visible if there are none.
		hasEdit = sole( i.hasEdit() for i in inspectors )

		warningStr = "\n" + "\n".join( warnings ) if warnings and not errors else ""

		if self.__editable:
			self.__editButton.setToolTip( ( "Click to edit" if hasEdit else "Click to add an edit" ) + warningStr )
		else :
			self.__editButton.setToolTip( "\n".join( errors ) if errors else "" )

		# We don't disable the button, as we need more control over the disabled icon.
		# We just don't do anything when clicked if we're not editable.
		image = "editDisabled.png"
		if self.__editable :
			image = "editOn.png" if hasEdit else "editOff.png"
		self.__editButton.setImage( image )

		self.__valueWidget.setToolTip( "\n".join( errors ) if errors else ( ( "Click to Edit" if hasEdit else "The current value" ) + warningStr )  )

		# Determine the logical state of the UI element, so we can apply appropriate styling
		valueState = "Uneditable"
		if self.__editable :
			if hasEdit is None :
				# A mix of edited and unedited.
				# We can only make edits for the user if we are using an EditScope, so self.__editable will be
				# False for any unedited locations when Automatic is set. As such we'll only get here if there
				# the user has chosen EditScope, so we show a mixed state of Editable + EditScopeEdit decoration.
				valueState = "SomeEdited"
			elif hasEdit == False :
				valueState = "Editable"
			else :
				# Every location has edits, but they may be a mixture of GenericEdits and EditScopeEdits
				allInEditScopes = sole( i.inEditScope() for i in inspectors )
				valueState = "MixedEdits" if allInEditScopes is None else "{}Edit".format( "EditScope" if allInEditScopes else "Generic" )

		self.__valueWidget._qtWidget().setProperty( "inspectorValueState", valueState )
		self.__valueWidget._qtWidget().setProperty( "inspectorValueHasWarnings", warnings and not errors )
		self.__valueWidget._repolish()

		self.__inspectors = inspectors

	def __editButtonClicked( self, button ) :

		if self.__editable :
			self.__edit()

	def __valueWidgetClicked( self, *unused ) :

		# Only edit via the value label all locations already have edits to help avoid accidental edit creation
		if self.__editable and bool( self.__inspectors ) and all( i.hasEdit() for i in self.__inspectors ) :
			self.__edit()

	def __edit( self ) :

		plugs = [ i.acquireEdit() for i in self.__inspectors ]
		warnings = [ i.warningMessage() for i in self.__inspectors if i.warningMessage() ]

		for p in plugs :
			r = Gaffer.MetadataAlgo.readOnlyReason( p )
			if r is not None :
				# We still allow viewing of read-only plugs to people can inspect the nature of an edit
				warnings.append( "'{}' is locked.".format( r.relativeName( r.ancestor( Gaffer.ScriptNode ) ) ) )

		self.__editWindow = _EditWindow( plugs, warning = "\n".join( warnings ) )
		self.__editWindow.resizeToFitChild()
		self.__editWindow.popup( self.bound().center() + imath.V2i( 0, 45 ) )

## \todo How does this relate to PopupWindow and SpreadsheetUI._EditWindow?
class _EditWindow( GafferUI.Window ) :

	def __init__( self, plugs, warning=None, **kw ) :

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

			with GafferUI.ListContainer( spacing = 4, orientation = GafferUI.ListContainer.Orientation.Horizontal ) :

				# An alert (if required)

				if warning :
					warningBadge = GafferUI.Image( "warningSmall.png" )
					warningBadge.setToolTip( warning )

				# Widget for editing plugs

				self.__plugValueWidget = GafferUI.PlugValueWidget.create( plugs )
				if isinstance( self.__plugValueWidget, GafferSceneUI.TweakPlugValueWidget ) :
					## \todo We have this same hack in SpreadsheetUI. Should we instead
					# do something with metadata when we add the column to the spreadsheet?
					self.__plugValueWidget.setNameVisible( False )

		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )

	def popup( self, position ) :

		self.setVisible( True )

		# Attempt to focus the first text widget. This is done after making
		# the window visible, as we check child widget visibility to avoid
		# attempting to focus upon hidden widgets.

		size = self._qtWidget().sizeHint()
		self.setPosition( position - imath.V2i( size.width() / 2, size.height() / 2 ) )

		textWidget = self.__textWidget( self.__plugValueWidget )
		if textWidget is not None :
			if isinstance( textWidget, GafferUI.TextWidget ) :
				textWidget.grabFocus()
				textWidget.setSelection( 0, len( textWidget.getText() ) )
			else :
				textWidget.setFocussed( True )


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

	# \todo This is duplicated from SpreadsheetUI, is this something we can generalise?
	@classmethod
	def __textWidget( cls, plugValueWidget ) :

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

		for childPlug in Gaffer.Plug.Range( plugValueWidget.getPlug() ) :
			childWidget = plugValueWidget.childPlugValueWidget( childPlug )
			if childWidget is not None :
				childTextWidget = cls.__textWidget( childWidget )
				if childTextWidget is not None :
					return childTextWidget

		return None

# Widget for displaying any value type.
## \todo Figure out relationship with SceneInspector's Diff widgets.
# It seems like they may all be subclasses of the same abstract base?
class _ValueWidget( GafferUI.Widget ) :

	def __init__( self, values = [], **kw ) :

		GafferUI.Widget.__init__( self, QtWidgets.QLabel(), **kw )

		self._qtWidget().setFixedHeight( 20 )
		self._qtWidget().setMinimumWidth( 140 )

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

# Determines the source _input_ to an input plug. Plug.source() may give us an
# output in the case of an animation node, etc.
## \todo Factor in when implementing contextAwareSource.
def sourceInput( plug ) :

	result = plug
	while plug is not None :
		if plug.direction() is Gaffer.Plug.Direction.In :
			result = plug
		plug = plug.getInput()
	return result

# Utility in the spirit of `all()` and `any()`. If all values in `sequence`
# are equal, returns that value, otherwise returns `None`.
## \todo Copied from Gaffer.PlugValueWidget. Is there somewhere more sensible we can put this? Cortex perhaps?
def sole( sequence ) :

	result = None
	for i, v in enumerate( sequence ) :
		if i == 0 :
			result = v
		elif v != result :
			return None

	return result
