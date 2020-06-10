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

import functools
import warnings

import IECore

import Gaffer
import GafferUI

## \todo Potential optimisation.
# Currently every PlugValueWidget instance connects to the various plug signals
# on the node, and tests to see if the plug is of interest when signalled. When many
# PlugValueWidgets are instantiated for a node this might prove a little slow. In this
# eventuality perhaps we can optimise things by having PlugLayout be responsible for
# updating only the correct child, so the children don't need to be connected themselves.
# PlugValueWidget would need to maintain the ability to do things itself when used alone,
# but this might give a good speedup for the most common case.
class PlugValueWidget( GafferUI.Widget ) :

	def __init__( self, topLevelWidget, plug, **kw ) :

		GafferUI.Widget.__init__( self, topLevelWidget, **kw )
		self._qtWidget().setProperty( "gafferPlugValueWidget", True )

		# we don't want to call _updateFromPlug yet because the derived
		# classes haven't constructed yet. they can call it themselves
		# upon completing construction.
		self.__setPlugInternal( plug, callUpdateFromPlug=False )

		self.__readOnly = False

		self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ), scoped = False )
		self.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ), scoped = False )
		self.dropSignal().connect( Gaffer.WeakMethod( self.__drop ), scoped = False )

		Gaffer.Metadata.nodeValueChangedSignal().connect(
			Gaffer.WeakMethod( self.__nodeMetadataChanged ),
			scoped = False
		)

	## Note that it is acceptable to pass None to setPlug() (and to the constructor)
	# and that derived classes should be implemented to cope with this eventuality.
	def setPlug( self, plug ) :

		self.__setPlugInternal( plug, callUpdateFromPlug=True )

	def getPlug( self ) :

		return self.__plug

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
		self._updateFromPlug()

	def getContext( self ) :

		return self.__context

	## \deprecated
	def setReadOnly( self, readOnly ) :

		assert( isinstance( readOnly, bool ) )
		if readOnly == self.__readOnly :
			return

		self.__readOnly = readOnly
		self._updateFromPlug()

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
	# status of the plug. To temporarily suspend calls to this function, use
	# Gaffer.BlockedConnection( self._plugConnections() ).
	def _updateFromPlug( self ) :

		raise NotImplementedError

	def _plugConnections( self ) :

		return [
			self.__plugDirtiedConnection,
			self.__plugInputChangedConnection,
			self.__plugMetadataChangedConnection,
		]

	## Returns True if the plug value is editable as far as this ui is concerned
	# - that plug.settable() is True and self.getReadOnly() is False. By default,
	# an animated plug is considered to be non-editable because it has an input
	# connection. Subclasses which support animation editing may pass
	# `canEditAnimation = True` to have animated plugs considered as editable.
	def _editable( self, canEditAnimation = False ) :

		plug = self.getPlug()

		if plug is None :
			return False

		if self.__readOnly :
			return False

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

	__popupMenuSignal = Gaffer.Signal2()
	## This signal is emitted whenever a popup menu for a plug is about
	# to be shown. This provides an opportunity to customise the menu from
	# external code. The signature for slots is ( menuDefinition, plugValueWidget ),
	# and slots should just modify the menu definition in place.
	@classmethod
	def popupMenuSignal( cls ) :

		return cls.__popupMenuSignal

	## Returns a PlugValueWidget suitable for representing the specified plug.
	# The type of plug returned may be customised on a per-widget basis by a
	# "plugValueWidget:type" metadata value, specifying the fully qualified
	# python type name for a widget class. To suppress the creation of a widget,
	# a value of "" may be registered - in this case None will be returned from
	# create(). If useTypeOnly is True, then the metadata will be ignored and
	# only the plug type will be taken into account in creating a PlugValueWidget.
	@classmethod
	def create( cls, plug, useTypeOnly=False ) :

		# first try to create one using a creator registered for the specific plug
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
				return widgetClass( plug )

		# if that failed, then just create something based on the type of the plug
		typeId = plug.typeId()
		for plugTypeId in [ plug.typeId() ] + IECore.RunTimeTyped.baseTypeIds( plug.typeId() ) :
			if plugTypeId in cls.__plugTypesToCreators :
				creator = cls.__plugTypesToCreators[plugTypeId]
				if creator is not None :
					return creator( plug )
				else :
					return None

		return None

	## Registers a PlugValueWidget type for a specific Plug type.
	@classmethod
	def registerType( cls, plugClassOrTypeId, creator ) :

		if isinstance( plugClassOrTypeId, IECore.TypeId ) :
			plugTypeId = plugClassOrTypeId
		else :
			plugTypeId = plugClassOrTypeId.staticTypeId()

		cls.__plugTypesToCreators[plugTypeId] = creator

	__plugTypesToCreators = {}

	def __plugDirtied( self, plug ) :

		if plug.isSame( self.__plug ) :

			self._updateFromPlug()

	def __plugInputChanged( self, plug ) :

		if plug.isSame( self.__plug ) :
			self.__updateContextConnection()
			self._updateFromPlug()

	def __plugMetadataChanged( self, nodeTypeId, plugPath, key, plug ) :

		if self.__plug is None :
			return

		if (
			Gaffer.MetadataAlgo.affectedByChange( self.__plug, nodeTypeId, plugPath, plug ) or
			Gaffer.MetadataAlgo.readOnlyAffectedByChange( self.__plug, nodeTypeId, plugPath, key, plug )
		) :
			self._updateFromPlug()

	def __nodeMetadataChanged( self, nodeTypeId, key, node ) :

		if self.__plug is None :
			return

		if Gaffer.MetadataAlgo.readOnlyAffectedByChange( self.__plug, nodeTypeId, key, node ) :
			self._updateFromPlug()

	def __contextChanged( self, context, key ) :

		self._updateFromPlug()

	def __setPlugInternal( self, plug, callUpdateFromPlug ) :

		self.__plug = plug

		context = self.__fallbackContext

		if self.__plug is not None :
			self.__plugDirtiedConnection = plug.node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ) )
			self.__plugInputChangedConnection = plug.node().plugInputChangedSignal().connect( Gaffer.WeakMethod( self.__plugInputChanged ) )
			self.__plugMetadataChangedConnection = Gaffer.Metadata.plugValueChangedSignal().connect( Gaffer.WeakMethod( self.__plugMetadataChanged ) )
			scriptNode = self.__plug.ancestor( Gaffer.ScriptNode )
			if scriptNode is not None :
				context = scriptNode.context()
		else :
			self.__plugDirtiedConnection = None
			self.__plugInputChangedConnection = None
			self.__plugMetadataChangedConnection = None

		self.__context = context
		self.__updateContextConnection()

		if callUpdateFromPlug :
			self._updateFromPlug()

	def __updateContextConnection( self ) :

		# we only want to be notified of context changes if we have a plug and that
		# plug has an incoming connection. otherwise context changes are irrelevant
		# and we'd just be slowing things down by asking for notifications.

		context = self.__context
		plug = self.getPlug()
		if plug is None or ( plug.getInput() is None and plug.direction() == Gaffer.Plug.Direction.In ):
			context = None

		if context is not None :
			self.__contextChangedConnection = context.changedSignal().connect( Gaffer.WeakMethod( self.__contextChanged ) )
		else :
			self.__contextChangedConnection = None

	# we use this when the plug being viewed doesn't have a ScriptNode ancestor
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
