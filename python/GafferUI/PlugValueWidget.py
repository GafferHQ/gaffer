##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import collections
import functools
import itertools
import traceback
import warnings
import six

import IECore

import Gaffer
import GafferUI

## Base class for widgets which can display and optionally edit one or
# more ValuePlugs. Subclasses must override `_updateFromPlugs()` to
# update the UI to reflect the current state of the plugs, and may also
# override `setPlugs()` to perform any book-keeping needed when the plugs
# being displayed are changed.
#
# > Note : PlugValueWidgets could originally only display a single plug
# > at a time, using overrides for `_updateFromPlug()` and `setPlug()`
# > (note the singular). For backwards compatibility we still support
# > subclasses which override these old methods, but over time will phase
# > this out and require the plural form.
class PlugValueWidget( GafferUI.Widget ) :

	class MultiplePlugsError( ValueError ) : pass

	def __init__( self, topLevelWidget, plugs, **kw ) :

		GafferUI.Widget.__init__( self, topLevelWidget, **kw )
		self._qtWidget().setProperty( "gafferPlugValueWidget", True )

		if isinstance( plugs, Gaffer.Plug ) :
			plugs = { plugs }
		elif plugs is None :
			plugs = set()
		elif not isinstance( plugs, set ) :
			plugs = set( plugs )

		# We don't want to call `_updateFromPlugs()` yet because the derived
		# classes haven't constructed. They can call it themselves
		# upon completing construction.
		self.__setPlugsInternal( plugs, callUpdateFromPlugs=False )

		self.__readOnly = False

		self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ), scoped = False )
		self.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ), scoped = False )
		self.dropSignal().connect( Gaffer.WeakMethod( self.__drop ), scoped = False )

		Gaffer.Metadata.nodeValueChangedSignal().connect(
			Gaffer.WeakMethod( self.__nodeMetadataChanged ),
			scoped = False
		)

	## Changes the plugs displayed by this widget. May be overridden by derived classes,
	# but all implementations must call the base class version first. Note that it is
	# acceptable for `plugs` to be empty, so derived classes should be implemented with
	# this in mind.
	def setPlugs( self, plugs ) :

		if not isinstance( plugs, set ) :
			plugs = set( plugs )

		if self.setPlug.__code__ is not PlugValueWidget.setPlug.__code__ :
			# Legacy subclass has overridden `setPlug()`. Implement via
			# that so that it can do whatever it needs to do.
			if len( plugs ) <= 1 :
				self.setPlug( next( iter( plugs ), None ) )
			else :
				raise Exception( "{} does not support multiple plugs".format( self.__class__.__name__ ) )
		else :
			self.__setPlugsInternal( plugs, callUpdateFromPlugs=True )

	def getPlugs( self ) :

		return self.__plugs

	## Convenience function that calls `setPlugs()`. Note that
	# `plug` may be `None`.
	def setPlug( self, plug ) :

		if self.setPlug.__code__ is not PlugValueWidget.setPlug.__code__ :
			# Legacy subclass has overridden `setPlug()`. Do work internally
			# to avoid recursion.
			self.__setPlugsInternal( { plug } if plug is not None else set(), callUpdateFromPlugs=True )
		else :
			# Implement via `setPlugs()` so that new classes may
			# override it.
			self.setPlugs( { plug } if plug is not None else set() )

	## Convenience function. Raises MultiplePlugsError if more than one plug is
	# being displayed.
	def getPlug( self ) :

		if len( self.__plugs ) > 1 :
			raise self.MultiplePlugsError()

		return next( iter( self.__plugs ), None )

	## By default, PlugValueWidgets operate in the main context held by the script node
	# for the script the plug belongs to. This function allows an alternative context
	# to be provided, making it possible to view a plug at a custom frame (or with any
	# other context modification).
	def setContext( self, context ) :

		assert( isinstance( context, Gaffer.Context ) )
		if context is self.__context :
			return

		self.__context = context
		self.__updateContextConnection()
		self._updateFromPlugs()

	def getContext( self ) :

		return self.__context

	## \deprecated
	def setReadOnly( self, readOnly ) :

		assert( isinstance( readOnly, bool ) )
		if readOnly == self.__readOnly :
			return

		self.__readOnly = readOnly
		self._updateFromPlugs()

	## \deprecated
	def getReadOnly( self ) :

		return self.__readOnly

	## Should be reimplemented to return True if this widget includes
	# some sort of labelling for the plug. This is used to prevent
	# extra labels being created in the NodeUI when they're not necessary.
	def hasLabel( self ) :

		return False

	## Implemented to return a tooltip containing the plug name and description.
	def getToolTip( self ) :

		result = GafferUI.Widget.getToolTip( self )
		if result :
			return result

		plug = self.getPlug()
		if plug is None :
			return ""

		input = plug.getInput()

		inputText = ""
		if input is not None :
			inputText = " <- " + input.relativeName( input.commonAncestor( plug, Gaffer.GraphComponent ) )

		result = "# " + plug.relativeName( plug.node() ) + inputText
		description = Gaffer.Metadata.value( plug, "description" )
		if description :
			result += "\n\n" + description

		return result

	## Because Plugs may have child Plugs, so too PlugValueWidgets may
	# have child PlugValueWidgets to represent the children of their plug.
	# This method should be reimplemented to return such children, or `None`
	# if no appropriate child exists.
	def childPlugValueWidget( self, childPlug ) :

		return None

	__popupMenuSignal = Gaffer.Signal2()
	## This signal is emitted whenever a popup menu for a plug is about
	# to be shown. This provides an opportunity to customise the menu from
	# external code. The signature for slots is ( menuDefinition, plugValueWidget ),
	# and slots should just modify the menu definition in place.
	@classmethod
	def popupMenuSignal( cls ) :

		return cls.__popupMenuSignal

	## Returns a PlugValueWidget suitable for representing the specified plugs.
	# The type of widget returned may be customised on a per-plug basis by a
	# "plugValueWidget:type" metadata value, specifying the fully qualified
	# python type name for a widget class. To suppress the creation of a widget,
	# a value of "" may be registered - in this case None will be returned from
	# create(). If useTypeOnly is True, then the metadata will be ignored and
	# only the plug type will be taken into account in creating a PlugValueWidget.
	@classmethod
	def create( cls, plugs, useTypeOnly=False ) :

		if isinstance( plugs, Gaffer.Plug ) :
			creators = { cls.__creator( plugs, useTypeOnly ) }
		else :
			creators = { cls.__creator( p, useTypeOnly ) for p in plugs }

		if len( creators ) > 1 :
			raise Exception( "Multiple widget creators" )

		creator = next( iter( creators ) )
		if creator is not None :
			return creator( plugs )

		return None

	## Registers a PlugValueWidget type for a specific Plug type.
	@classmethod
	def registerType( cls, plugClassOrTypeId, creator ) :

		if isinstance( plugClassOrTypeId, IECore.TypeId ) :
			plugTypeId = plugClassOrTypeId
		else :
			plugTypeId = plugClassOrTypeId.staticTypeId()

		cls.__plugTypesToCreators[plugTypeId] = creator

	## Ensures that the specified plug has a visible PlugValueWidget,
	# creating one if necessary.
	@classmethod
	def acquire( cls, plug ) :

		editor = GafferUI.NodeEditor.acquire( plug.node() )

		plugValueWidget = editor.nodeUI().plugValueWidget( plug )
		if not plugValueWidget :
			return None

		plugValueWidget.reveal()

		return plugValueWidget

	## Must be implemented by subclasses so that the widget reflects the current
	# status of the plugs. To temporarily suspend calls to this function, use
	# `Gaffer.BlockedConnection( self._plugConnections() )`.
	def _updateFromPlugs( self ) :

		# Default implementation falls back to legacy update for a single plug.
		updateFromPlug = getattr( self, "_updateFromPlug", None )
		if updateFromPlug is not None :
			updateFromPlug()

	def _plugConnections( self ) :

		return (
			self.__plugDirtiedConnections +
			self.__plugInputChangedConnections +
			[ self.__plugMetadataChangedConnection ]
		)

	## Returns True if the plug's values are editable as far as this UI is concerned
	# - that `plug.settable()` is True for all plugs and `self.getReadOnly()` is
	# False. By default, an animated plug is considered to be non-editable because
	# it has an input connection. Subclasses which support animation editing may pass
	# `canEditAnimation = True` to have animated plugs considered as editable.
	def _editable( self, canEditAnimation = False ) :

		if self.__readOnly or not self.getPlugs() :
			return False

		for plug in self.getPlugs() :

			if hasattr( plug, "settable" ) and not plug.settable() :
				if not canEditAnimation or not Gaffer.Animation.isAnimated( plug ) :
					return False

			if Gaffer.MetadataAlgo.readOnly( plug ) :
				return False

		return True

	## Called to convert the specified value into something
	# suitable for passing to a plug.setValue() call. Returns
	# None if no such conversion is necessary. May be reimplemented
	# by derived classes to provide more complex conversions than
	# the standard. The base class uses this method to accept drag/drop
	# and copy/paste data.
	def _convertValue( self, value ) :

		if not hasattr( self.getPlug(), "defaultValue" ) :
			return None

		plugValueType = type( self.getPlug().defaultValue() )
		if isinstance( value, plugValueType ) :
			return value
		elif isinstance( value, IECore.Data ) :

			dataValue = None
			if hasattr( value, "value" ) :
				dataValue = value.value
			else :
				with IECore.IgnoredExceptions( Exception ) :
					if len( value ) == 1 :
						dataValue = value[0]

			if dataValue is None :
				return None
			elif isinstance( dataValue, plugValueType ) :
				return dataValue
			else :
				with IECore.IgnoredExceptions( Exception ) :
					return plugValueType( dataValue )

		return None

	## Adds a useful popup menu to the specified widget, providing useful functions that
	# operate on the plug. The menu is populated with the result of _popupMenuDefinition(),
	# and may also be customised by external code using the popupMenuSignal().
	def _addPopupMenu( self, widget = None, buttons = GafferUI.ButtonEvent.Buttons.Right ) :

		if widget is None :
			widget = self

		# it's unclear under what circumstances we get given a right-click vs a context menu event,
		# but we try to cover all our bases by connecting to both.

		widget.buttonPressSignal().connect( functools.partial( Gaffer.WeakMethod( self.__buttonPress ), buttonMask = buttons ), scoped = False )

		if buttons & GafferUI.ButtonEvent.Buttons.Right :
			widget.contextMenuSignal().connect( functools.partial( Gaffer.WeakMethod( self.__contextMenu ) ), scoped = False )

	## Returns a definition for the popup menu - this is called each time the menu is displayed
	# to allow for dynamic menus. Subclasses may override this method to customise the menu, but
	# should call the base class implementation first.
	def _popupMenuDefinition( self ) :

		menuDefinition = IECore.MenuDefinition()

		if hasattr( self.getPlug(), "getValue" ) :

			applicationRoot = self.getPlug().ancestor( Gaffer.ApplicationRoot )
			menuDefinition.append(
				"/Copy Value", {
					"command" : Gaffer.WeakMethod( self.__copyValue ),
					"active" : applicationRoot is not None
				}
			)

			pasteValue = None
			if applicationRoot is not None :
				pasteValue = self._convertValue( applicationRoot.getClipboardContents() )

			menuDefinition.append(
				"/Paste Value", {
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), pasteValue ),
					"active" : self._editable() and pasteValue is not None
				}
			)

			menuDefinition.append( "/CopyPasteDivider", { "divider" : True } )

		if self.getPlug().getInput() is not None :
			menuDefinition.append( "/Edit input...", { "command" : Gaffer.WeakMethod( self.__editInput ) } )
			menuDefinition.append( "/EditInputDivider", { "divider" : True } )
			menuDefinition.append(
				"/Remove input", {
					"command" : Gaffer.WeakMethod( self.__removeInput ),
					"active" : self.getPlug().acceptsInput( None ) and not self.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( self.getPlug() ),
				}
			)
		if hasattr( self.getPlug(), "defaultValue" ) and self.getPlug().direction() == Gaffer.Plug.Direction.In :
			menuDefinition.append(
				"/Default", {
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), self.getPlug().defaultValue() ),
					"active" : self._editable()
				}
			)

		if Gaffer.NodeAlgo.hasUserDefault( self.getPlug() ) and self.getPlug().direction() == Gaffer.Plug.Direction.In :
			menuDefinition.append(
				"/User Default", {
					"command" : Gaffer.WeakMethod( self.__applyUserDefault ),
					"active" : self._editable()
				}
			)

		if Gaffer.NodeAlgo.presets( self.getPlug() ) :
			menuDefinition.append(
				"/Preset", {
					"subMenu" : Gaffer.WeakMethod( self.__presetsSubMenu ),
					"active" : self._editable()
				}
			)

		if len( menuDefinition.items() ) :
			menuDefinition.append( "/LockDivider", { "divider" : True } )

		readOnly = Gaffer.MetadataAlgo.getReadOnly( self.getPlug() )
		menuDefinition.append(
			"/Unlock" if readOnly else "/Lock",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__applyReadOnly ), not readOnly ),
				"active" : not self.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( self.getPlug().parent() ),
			}
		)

		self.popupMenuSignal()( menuDefinition, self )

		return menuDefinition

	def __plugDirtied( self, plug ) :

		if plug in self.__plugs :
			self._updateFromPlugs()

	def __plugInputChanged( self, plug ) :

		if plug in self.__plugs :
			self.__updateContextConnection()
			self._updateFromPlugs()

	def __plugMetadataChanged( self, nodeTypeId, plugPath, key, plug ) :

		for p in self.__plugs :
			if (
				Gaffer.MetadataAlgo.affectedByChange( p, nodeTypeId, plugPath, plug ) or
				Gaffer.MetadataAlgo.readOnlyAffectedByChange( p, nodeTypeId, plugPath, key, plug )
			) :
				self._updateFromPlugs()
				return

	def __nodeMetadataChanged( self, nodeTypeId, key, node ) :

		for p in self.__plugs :
			if Gaffer.MetadataAlgo.readOnlyAffectedByChange( p, nodeTypeId, key, node ) :
				self._updateFromPlugs()
				return

	def __contextChanged( self, context, key ) :

		self._updateFromPlugs()

	def __setPlugsInternal( self, plugs, callUpdateFromPlugs ) :

		assert( isinstance( plugs, set ) )
		if len( plugs ) and sole( p.__class__ for p in plugs ) is None :
			raise ValueError( "Plugs have different types" )

		nodes = set()
		scriptNodes = set()
		for plug in plugs :
			nodes.add( plug.node() )
			scriptNodes.add( plug.ancestor( Gaffer.ScriptNode ) )

		assert( len( scriptNodes ) <= 1 )

		self.__plugs = plugs

		self.__plugDirtiedConnections = [
			node.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ) )
			for node in nodes
		]
		self.__plugInputChangedConnections = [
			node.plugInputChangedSignal().connect( Gaffer.WeakMethod( self.__plugInputChanged ) )
			for node in nodes
		]

		if self.__plugs :
			self.__plugMetadataChangedConnection = Gaffer.Metadata.plugValueChangedSignal().connect( Gaffer.WeakMethod( self.__plugMetadataChanged ) )
		else :
			self.__plugMetadataChangedConnection = None

		scriptNode = next( iter( scriptNodes ), None )
		self.__context = scriptNode.context() if scriptNode is not None else self.__fallbackContext
		self.__updateContextConnection()

		if callUpdateFromPlugs :
			self._updateFromPlugs()

	def __updateContextConnection( self ) :

		# We only want to be notified of context changes for plugs whose values are
		# computed.

		context = self.__context
		if all( p.source().direction() == Gaffer.Plug.Direction.In for p in self.getPlugs() ) :
			context = None

		if context is not None :
			self.__contextChangedConnection = context.changedSignal().connect( Gaffer.WeakMethod( self.__contextChanged ) )
		else :
			self.__contextChangedConnection = None

	# we use this when the plugs being viewed doesn't have a ScriptNode ancestor
	# to provide a context.
	__fallbackContext = Gaffer.Context()

	def __buttonPress( self, widget, event, buttonMask ) :

		if event.buttons & buttonMask :
			return self.__contextMenu()

		return False

	def __contextMenu( self, *unused ) :

		if self.getPlug() is None :
			return False

		menuDefinition = self._popupMenuDefinition()
		if not len( menuDefinition.items() ) :
			return False

		title = self.getPlug().relativeName( self.getPlug().node() )
		title = ".".join( [ IECore.CamelCase.join( IECore.CamelCase.split( x ) ) for x in title.split( "." ) ] )

		self.__popupMenu = GafferUI.Menu( menuDefinition, title = title )
		self.__popupMenu.popup( parent = self )

		return True

	def __copyValue( self ) :

		with self.getContext() :
			value = self.getPlug().getValue()

		if not isinstance( value, IECore.Object ) :
			# Trick to get Data from a simple type - put
			# it in a CompoundData (which will convert to
			# Data automatically) and then get it back out.
			value = IECore.CompoundData( { "v" : value } )["v"]

		self.getPlug().ancestor( Gaffer.ApplicationRoot ).setClipboardContents( value )

	def __setValue( self, value ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().setValue( value )

	def __editInput( self ) :

		nodeEditor = GafferUI.NodeEditor.acquire( self.getPlug().getInput().node() )
		if nodeEditor is None :
			return

		plugValueWidget = nodeEditor.nodeUI().plugValueWidget( self.getPlug().getInput() )
		if plugValueWidget is None :
			return

		plugValueWidget.reveal()

	def __removeInput( self ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().setInput( None )

	def __applyUserDefault( self ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			Gaffer.NodeAlgo.applyUserDefault( self.getPlug() )

	def __presetsSubMenu( self ) :

		with self.getContext() :
			currentPreset = Gaffer.NodeAlgo.currentPreset( self.getPlug() )

		result = IECore.MenuDefinition()
		for presetName in Gaffer.NodeAlgo.presets( self.getPlug() ) :
			menuPath = presetName if presetName.startswith( "/" ) else "/" + presetName
			result.append(
				menuPath, {
					"command" : functools.partial( Gaffer.WeakMethod( self.__applyPreset ), presetName ),
					"active" : self._editable(),
					"checkBox" : presetName == currentPreset,
				}
			)

		return result

	def __applyPreset( self, presetName, *unused ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			Gaffer.NodeAlgo.applyPreset( self.getPlug(), presetName )

	def __applyReadOnly( self, readOnly ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			Gaffer.MetadataAlgo.setReadOnly( self.getPlug(), readOnly )

	# drag and drop stuff

	def __dragEnter( self, widget, event ) :

		if self.getReadOnly() or Gaffer.MetadataAlgo.readOnly( self.getPlug() ):
			return False

		if isinstance( event.sourceWidget, GafferUI.PlugValueWidget ) :
			sourcePlugValueWidget = event.sourceWidget
		else :
			sourcePlugValueWidget = event.sourceWidget.ancestor( GafferUI.PlugValueWidget )

		if sourcePlugValueWidget is not None and sourcePlugValueWidget.getPlug().isSame( self.getPlug() ) :
			return False

		if isinstance( event.data, Gaffer.Plug ) :
			if self.getPlug().direction() == Gaffer.Plug.Direction.In and self.getPlug().acceptsInput( event.data ) :
				self.setHighlighted( True )
				return True
		elif hasattr( self.getPlug(), "setValue" ) and self._convertValue( event.data ) is not None :
			if self.getPlug().settable() :
				self.setHighlighted( True )
				return True

		return False

	def __dragLeave( self, widget, event ) :

		self.setHighlighted( False )

	def __drop( self, widget, event ) :

		self.setHighlighted( False )

		with Gaffer.UndoScope( self.getPlug().node().scriptNode() ) :
			if isinstance( event.data, Gaffer.Plug ) :
				self.getPlug().setInput( event.data )
			else :
				self.getPlug().setValue( self._convertValue( event.data ) )

		return True

	# Type registry internals

	@classmethod
	def __creator( cls, plug, useTypeOnly ) :

		# First try to create one using a creator registered for the specific plug.
		if not useTypeOnly :

			widgetType = Gaffer.Metadata.value( plug, "plugValueWidget:type" )
			if widgetType is None :
				widgetType = Gaffer.Metadata.value( plug, "layout:widgetType" )
				if widgetType is not None :
					warnings.warn( "The \"layout:widgetType\" metadata entry is deprecated, use \"plugValueWidget:type\" instead.", DeprecationWarning )
					if widgetType == "None" :
						return None

			if widgetType is not None :
				if widgetType == "" :
					return None
				path = widgetType.split( "." )
				widgetClass = __import__( path[0] )
				for n in path[1:] :
					widgetClass = getattr( widgetClass, n )
				return widgetClass

		# If that failed, then just create something based on the type of the plug.
		typeId = plug.typeId()
		for plugTypeId in [ plug.typeId() ] + IECore.RunTimeTyped.baseTypeIds( plug.typeId() ) :
			if plugTypeId in cls.__plugTypesToCreators :
				creator = cls.__plugTypesToCreators[plugTypeId]
				if creator is not None :
					return creator
				else :
					return None

		return None

	__plugTypesToCreators = {}

# Utility in the spirit of `all()` and `any()`. If all values in `sequence`
# are equal, returns that value, otherwise returns `None`.
## \todo Is there somewhere more sensible we can put this? Cortex perhaps?
def sole( sequence ) :

	result = None
	for i, v in enumerate( sequence ) :
		if i == 0 :
			result = v
		elif v != result :
			return None

	return result
