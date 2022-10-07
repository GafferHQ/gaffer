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
	class MultipleWidgetCreatorsError( ValueError ) : pass
	class MultiplePlugTypesError( ValueError ) : pass

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

		if not self.getPlugs() :
			return ""

		# Name

		if len( self.getPlugs() ) == 1 :
			result = "# " + self.getPlug().relativeName( self.getPlug().node() )
		else :
			result = "# {} plugs".format( len( self.getPlugs() ) )

		# Input

		if len( self.getPlugs() ) == 1 :
			input = self.getPlug().getInput()
			if input is not None :
				result += "\n\nInput : {}".format( input.relativeName( input.commonAncestor( self.getPlug() ) ) )

		# Description

		description = sole( Gaffer.Metadata.value( p, "description" ) for p in self.getPlugs() )
		if description :
			result += "\n\n" + description

		return result

	## Because Plugs may have child Plugs, so too PlugValueWidgets may
	# have child PlugValueWidgets to represent the children of their plug.
	# This method should be reimplemented to return such children, or `None`
	# if no appropriate child exists.
	def childPlugValueWidget( self, childPlug ) :

		return None

	__popupMenuSignal = None
	## This signal is emitted whenever a popup menu for a plug is about
	# to be shown. This provides an opportunity to customise the menu from
	# external code. The signature for slots is ( menuDefinition, plugValueWidget ),
	# and slots should just modify the menu definition in place.
	@classmethod
	def popupMenuSignal( cls ) :

		if cls.__popupMenuSignal is None :
			cls.__popupMenuSignal = _PopupMenuSignal()

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
			# Not all PlugValueWidgets support multiple plugs, and some
			# except in their constructors if passed a sequence type.
			# Unwrap where possible.
			if len( plugs ) == 1 :
				plugs = next( iter( plugs ) )

		if len( creators ) > 1 :
			raise cls.MultipleWidgetCreatorsError()

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
	# `Gaffer.Signals.BlockedConnection( self._plugConnections() )`.
	def _updateFromPlugs( self ) :

		# Default implementation falls back to legacy update for a single plug.
		updateFromPlug = getattr( self, "_updateFromPlug", None )
		if updateFromPlug is not None :
			updateFromPlug()

	def _plugConnections( self ) :

		return (
			self.__plugDirtiedConnections +
			self.__plugInputChangedConnections +
			self.__plugMetadataChangedConnections
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

		plugValueType = sole(
			type( p.defaultValue() ) if hasattr( p, "defaultValue" ) else None
			for p in self.getPlugs()
		)
		if plugValueType is None :
			return None

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

		if all( hasattr( p, "getValue" ) for p in self.getPlugs() ) :

			applicationRoot = sole( p.ancestor( Gaffer.ApplicationRoot ) for p in self.getPlugs() )
			menuDefinition.append(
				"/Copy Value", {
					"command" : Gaffer.WeakMethod( self.__copyValue ),
					"active" : len( self.getPlugs() ) == 1 and applicationRoot is not None
				}
			)

			pasteValue = None
			if applicationRoot is not None :
				pasteValue = self._convertValue( applicationRoot.getClipboardContents() )

			menuDefinition.append(
				"/Paste Value", {
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValues ), pasteValue ),
					"active" : self._editable() and pasteValue is not None
				}
			)

			menuDefinition.append( "/CopyPasteDivider", { "divider" : True } )

		if any( p.getInput() is not None for p in self.getPlugs() ) :
			menuDefinition.append( "/Edit input...", { "command" : Gaffer.WeakMethod( self.__editInputs ) } )
			menuDefinition.append( "/EditInputDivider", { "divider" : True } )
			menuDefinition.append(
				"/Remove input", {
					"command" : Gaffer.WeakMethod( self.__removeInputs ),
					"active" : not self.getReadOnly() and all( p.acceptsInput( None ) and not Gaffer.MetadataAlgo.readOnly( p ) for p in self.getPlugs() ),
				}
			)
		if all( hasattr( p, "defaultValue" ) and p.direction() == Gaffer.Plug.Direction.In for p in self.getPlugs() ) :
			menuDefinition.append(
				"/Default", {
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValues ), [ p.defaultValue() for p in self.getPlugs() ] ),
					"active" : self._editable()
				}
			)

		if all( Gaffer.NodeAlgo.hasUserDefault( p ) and p.direction() == Gaffer.Plug.Direction.In for p in self.getPlugs() ) :
			menuDefinition.append(
				"/User Default", {
					"command" : Gaffer.WeakMethod( self.__applyUserDefaults ),
					"active" : self._editable()
				}
			)

		with self.getContext() :
			if any( Gaffer.NodeAlgo.presets( p ) for p in self.getPlugs() ) :
				menuDefinition.append(
					"/Preset", {
						"subMenu" : Gaffer.WeakMethod( self.__presetsSubMenu ),
						"active" : self._editable()
					}
				)

		if len( menuDefinition.items() ) :
			menuDefinition.append( "/LockDivider", { "divider" : True } )

		readOnly = any( Gaffer.MetadataAlgo.getReadOnly( p ) for p in self.getPlugs() )
		menuDefinition.append(
			"/Unlock" if readOnly else "/Lock",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__applyReadOnly ), not readOnly ),
				"active" : not self.getReadOnly() and not any( Gaffer.MetadataAlgo.readOnly( p.parent() ) for p in self.getPlugs() ),
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

	def __plugMetadataChanged( self, plug, key, reason ) :

		for p in self.__plugs :
			if (
				p == plug or p.isAncestorOf( plug ) or
				Gaffer.MetadataAlgo.readOnlyAffectedByChange( p, plug, key )
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
			raise self.MultiplePlugTypesError()

		nodes = set()
		scriptNodes = set()
		for plug in plugs :
			nodes.add( plug.node() )
			scriptNodes.add( plug.ancestor( Gaffer.ScriptNode ) )

		assert( len( scriptNodes ) <= 1 )

		self.__plugs = plugs

		self.__plugDirtiedConnections = [
			node.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ), scoped = True )
			for node in nodes
		]
		self.__plugInputChangedConnections = [
			node.plugInputChangedSignal().connect( Gaffer.WeakMethod( self.__plugInputChanged ), scoped = True )
			for node in nodes
		]
		self.__plugMetadataChangedConnections = [
			Gaffer.Metadata.plugValueChangedSignal( node ).connect( Gaffer.WeakMethod( self.__plugMetadataChanged ), scoped = True )
			for node in nodes
		]

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
			self.__contextChangedConnection = context.changedSignal().connect( Gaffer.WeakMethod( self.__contextChanged ), scoped = True )
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

		if not self.getPlugs() :
			return False

		menuDefinition = self._popupMenuDefinition()
		if not len( menuDefinition.items() ) :
			return False

		if len( self.getPlugs() ) == 1 :
			title = self.getPlug().relativeName( self.getPlug().node() )
			title = ".".join( [ IECore.CamelCase.join( IECore.CamelCase.split( x ) ) for x in title.split( "." ) ] )
		else :
			title = "{} plugs".format( len( self.getPlugs() ) )

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

	def __setValues( self, values ) :

		if not isinstance( values, list ) :
			values = itertools.repeat( values, len( self.getPlugs() ) )

		with Gaffer.UndoScope( next( iter( self.getPlugs() ) ).ancestor( Gaffer.ScriptNode ) ) :
			for plug, value in zip( self.getPlugs(), values ) :
				plug.setValue( value )

	def __editInputs( self ) :

		# We may have multiple inputs from the same node.
		# Choose one input plug per node to reveal.
		nodesToPlugs = {}
		for p in self.getPlugs() :
			i = p.getInput()
			if i is not None :
				nodesToPlugs[i.node()] = i

		# Acquire a NodeEditor for each node, and reveal the
		# chosen plug.
		for node, plug in nodesToPlugs.items() :

			nodeEditor = GafferUI.NodeEditor.acquire( node )
			if nodeEditor is None :
				continue

			plugValueWidget = nodeEditor.nodeUI().plugValueWidget( plug )
			if plugValueWidget is not None :
				plugValueWidget.reveal()

	def __removeInputs( self ) :

		with Gaffer.UndoScope( next( iter( self.getPlugs() ) ).ancestor( Gaffer.ScriptNode ) ) :
			for p in self.getPlugs() :
				p.setInput( None )

	def __applyUserDefaults( self ) :

		with Gaffer.UndoScope( next( iter( self.getPlugs() ) ).ancestor( Gaffer.ScriptNode ) ) :
			for p in self.getPlugs() :
				Gaffer.NodeAlgo.applyUserDefault( p )

	def __presetsSubMenu( self ) :

		with self.getContext() :

			currentPreset = sole( ( Gaffer.NodeAlgo.currentPreset( p ) or "" for p in self.getPlugs() ) )

			# Find the union of the presets across all plugs,
			# and count how many times they occur.
			presets = []
			presetCounts = collections.Counter()
			for plug in self.getPlugs() :
				for preset in Gaffer.NodeAlgo.presets( plug ) :
					if not presetCounts[preset] :
						presets.append( preset )
					presetCounts[preset] += 1

		# Build menu. We'll list every preset we found, but disable
		# any which aren't available for all plugs.
		result = IECore.MenuDefinition()
		for presetName in presets :
			menuPath = presetName if presetName.startswith( "/" ) else "/" + presetName
			result.append(
				menuPath, {
					"command" : functools.partial( Gaffer.WeakMethod( self.__applyPreset ), presetName ),
					"active" : self._editable() and presetCounts[preset] == len( self.getPlugs() ),
					"checkBox" : presetName == currentPreset,
				}
			)

		return result

	def __applyPreset( self, presetName, *unused ) :

		with self.getContext() :
			with Gaffer.UndoScope( next( iter( self.getPlugs() ) ).ancestor( Gaffer.ScriptNode ) ) :
				for p in self.getPlugs() :
					Gaffer.NodeAlgo.applyPreset( p, presetName )

	def __applyReadOnly( self, readOnly ) :

		with Gaffer.UndoScope( next( iter( self.getPlugs() ) ).ancestor( Gaffer.ScriptNode ) ) :
			for p in self.getPlugs() :
				Gaffer.MetadataAlgo.setReadOnly( p, readOnly )

	# drag and drop stuff

	def __dragEnter( self, widget, event ) :

		if self.getReadOnly() or any( Gaffer.MetadataAlgo.readOnly( p ) for p in self.getPlugs() ) :
			return False

		if isinstance( event.sourceWidget, GafferUI.PlugValueWidget ) :
			sourcePlugValueWidget = event.sourceWidget
		else :
			sourcePlugValueWidget = event.sourceWidget.ancestor( GafferUI.PlugValueWidget )

		if sourcePlugValueWidget is not None and sourcePlugValueWidget.getPlugs() & self.getPlugs() :
			return False

		if isinstance( event.data, Gaffer.Plug ) :
			if all( p.direction() == Gaffer.Plug.Direction.In and p.acceptsInput( event.data ) for p in self.getPlugs() ) :
				self.setHighlighted( True )
				return True
		elif all( hasattr( p, "setValue" ) for p in self.getPlugs() ) and self._convertValue( event.data ) is not None :
			if all( p.settable() for p in self.getPlugs() ) :
				self.setHighlighted( True )
				return True

		return False

	def __dragLeave( self, widget, event ) :

		self.setHighlighted( False )

	def __drop( self, widget, event ) :

		self.setHighlighted( False )

		with Gaffer.UndoScope( next( iter( self.getPlugs() ) ).node().scriptNode() ) :
			if isinstance( event.data, Gaffer.Plug ) :
				for p in self.getPlugs() :
					p.setInput( event.data )
			else :
				v = self._convertValue( event.data )
				for p in self.getPlugs() :
					p.setValue( v )

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

# Signal with custom result combiner to prevent bad slots blocking the
# execution of others, and to ease the transition from single plug to multiple
# plug support.
class _PopupMenuSignal( Gaffer.Signals.Signal2 ) :

	def __init__( self ) :

		Gaffer.Signals.Signal2.__init__( self, self.__combiner )

	@staticmethod
	def __combiner( results ) :

		while True :
			try :
				next( results )
			except StopIteration :
				return
			except Exception as e :
				# Print message but continue to execute other slots
				IECore.msg(
					# Demote MultiplePlugsError to a debug message, to give the multitude of custom plug menus
					# a grace period to adjust to PlugValueWidget's new multi-plug capabilities.
					IECore.Msg.Level.Error if "MultiplePlugsError" not in str( e ) else IECore.Msg.Level.Debug,
					"Plug menu", traceback.format_exc()
				)
				# Remove circular references that would keep the widget in limbo.
				e.__traceback__ = None
