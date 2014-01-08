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

import re
import fnmatch

import IECore

import Gaffer
import GafferUI

## \todo Potential optimisation.
# Currently every PlugValueWidget instance connects to the various plug signals
# on the node, and tests to see if the plug is of interest when signalled. When many
# PlugValueWidgets are instantiated for a node this might prove a little slow. In this
# eventuality perhaps we can optimise things by having CompoundPlugValueWidget be
# responsible for updating only the correct child, so the children don't need to be
# connected themselves. PlugValueWidget would need to maintain the ability to do things
# itself when used alone, but this might give a good speedup for the most common case.
class PlugValueWidget( GafferUI.Widget ) :

	def __init__( self, topLevelWidget, plug, **kw ) :
	
		GafferUI.Widget.__init__( self, topLevelWidget, **kw )
	
		# we don't want to call _updateFromPlug yet because the derived
		# classes haven't constructed yet. they can call it themselves
		# upon completing construction.
		self.__setPlugInternal( plug, callUpdateFromPlug=False )

		self.__popupMenuConnections = []
		self.__readOnly = False
		
		self.__dragEnterConnection = self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )
		self.__dragLeaveConnection = self.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ) )
		self.__dropConnection = self.dropSignal().connect( Gaffer.WeakMethod( self.__drop ) )
		
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
	
	## This method allows editing of the plug value
	# to be disabled for this ui. Note that even when getReadOnly()
	# is False, the ui may not allow editing due to the plug
	# itself being read only for other reasons.
	def setReadOnly( self, readOnly ) :
	
		assert( isinstance( readOnly, bool ) )
		if readOnly == self.__readOnly :
			return
			
		self.__readOnly = readOnly
		self._updateFromPlug()
		
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
			inputText = " &lt;- " + input.relativeName( input.commonAncestor( plug, Gaffer.GraphComponent.staticTypeId() ) )
		
		result = "<h3>" + plug.relativeName( plug.node() ) + inputText + "</h3>"
		description = Gaffer.Metadata.plugDescription( plug )
		if description :
			result += "\n\n" + description
			
		return result
			
	## Must be implemented by subclasses so that the widget reflects the current
	# status of the plug. To temporarily suspend calls to this function, use
	# Gaffer.BlockedConnection( self._plugConnections() ).
	def _updateFromPlug( self ) :
	
		raise NotImplementedError
		
	def _plugConnections( self ) :
	
		return [ 
			self.__plugDirtiedConnection,
			self.__plugInputChangedConnection,
			self.__plugFlagsChangedConnection
		]

	## Returns True if the plug value is editable as far as this ui is concerned
	# - that plug.settable() is True and self.getReadOnly() is False.
	def _editable( self ) :
	
		plug = self.getPlug()
		
		if plug is None :
			return False
		
		if hasattr(plug, 'settable') and not plug.settable():
			return False
		
		if self.__readOnly :
			return False
		
		return True
		
	## Adds a useful popup menu to the specified widget, providing useful functions that
	# operate on the plug. The menu is populated with the result of _popupMenuDefinition(),
	# and may also be customised by external code using the popupMenuSignal().
	def _addPopupMenu( self, widget = None, buttons = GafferUI.ButtonEvent.Buttons.Right ) :
	
		if widget is None :
			widget = self

		# it's unclear under what circumstances we get given a right-click vs a context menu event,
		# but we try to cover all our bases by connecting to both.

		self.__popupMenuConnections.append(
			widget.buttonPressSignal().connect( IECore.curry( Gaffer.WeakMethod( self.__buttonPress ), buttonMask = buttons ) )
		)

		if buttons & GafferUI.ButtonEvent.Buttons.Right :
			self.__popupMenuConnections.append(
				widget.contextMenuSignal().connect( IECore.curry( Gaffer.WeakMethod( self.__contextMenu ) ) )
			)
	
	## Returns a definition for the popup menu - this is called each time the menu is displayed
	# to allow for dynamic menus. Subclasses may override this method to customise the menu, but
	# should call the base class implementation first.
	def _popupMenuDefinition( self ) :
	
		menuDefinition = IECore.MenuDefinition()
		
		if self.getPlug().getInput() is not None :
			menuDefinition.append( "/Edit input...", { "command" : Gaffer.WeakMethod( self.__editInput ) } )
			menuDefinition.append( "/EditInputDivider", { "divider" : True } )
			menuDefinition.append(
				"/Remove input", {
					"command" : Gaffer.WeakMethod( self.__removeInput ),
					"active" : self.getPlug().acceptsInput( None ) and not self.getReadOnly(),
				}
			)
		if hasattr( self.getPlug(), "defaultValue" ) and self.getPlug().direction() == Gaffer.Plug.Direction.In :
			menuDefinition.append(
				"/Default", {
					"command" : IECore.curry( Gaffer.WeakMethod( self.__setValue ), self.getPlug().defaultValue() ),
					"active" : self._editable()
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

	## Returns a PlugValueWidget suitable for representing the specified plug. If
	# useTypeOnly is True, then custom registrations made by registerCreator() will
	# be ignored and only the plug type will be taken into account in creating a
	# PlugValueWidget.		
	@classmethod
	def create( cls, plug, useTypeOnly=False ) :

		# first try to create one using a creator registered for the specific plug
		if not useTypeOnly :
			node = plug.node()
			if node is not None :
				plugPath = plug.relativeName( node )
				nodeHierarchy = IECore.RunTimeTyped.baseTypeIds( node.typeId() )
				for nodeTypeId in [ node.typeId() ] + nodeHierarchy :	
					creators = cls.__nodeTypesToCreators.get( nodeTypeId, None )
					if creators :
						for creator in creators :
							if creator.plugPathMatcher.match( plugPath ) :
								if creator.creator is not None :
									return creator.creator( plug, **(creator.creatorKeywordArgs) )
								else :
									return None
		
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
	
	## Registers a PlugValueWidget type for a specific Plug type. Note
	# that the registerCreator function below provides the
	# opportunity to further customise the type of Widget used for specific
	# plug instances based on the node type and plug name.
	@classmethod
	def registerType( cls, plugTypeId, creator ) :
	
		cls.__plugTypesToCreators[plugTypeId] = creator
		
	## Registers a function to create a PlugWidget. None may be passed as creator, to
	# disable the creation of uis for specific plugs.
	@classmethod
	def registerCreator( cls, nodeTypeId, plugPath, creator, **creatorKeywordArgs ) :
	
		if isinstance( plugPath, basestring ) :
			plugPath = re.compile( fnmatch.translate( plugPath ) )
		else :
			assert( type( plugPath ) is type( re.compile( "" ) ) )
		
		creators = cls.__nodeTypesToCreators.setdefault( nodeTypeId, [] )
		
		creator = IECore.Struct(
			plugPathMatcher = plugPath,
			creator = creator,
			creatorKeywordArgs = creatorKeywordArgs,
		)
		
		creators.insert( 0, creator )

	__plugTypesToCreators = {}
	__nodeTypesToCreators = {}
	
	def __plugDirtied( self, plug ) :
	
		if plug.isSame( self.__plug ) :
		
			self._updateFromPlug()	

	def __plugInputChanged( self, plug ) :
	
		if plug.isSame( self.__plug ) :
			self.__updateContextConnection()
			self._updateFromPlug()
	
	def __plugFlagsChanged( self, plug ) :
	
		if plug.isSame( self.__plug ) :
			self._updateFromPlug()			
		
	def __contextChanged( self, context, key ) :
	
		self._updateFromPlug()

	def __setPlugInternal( self, plug, callUpdateFromPlug ) :
	
		self.__plug = plug
		
		context = self.__fallbackContext
		
		if self.__plug is not None :
			self.__plugDirtiedConnection = plug.node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ) )
			self.__plugInputChangedConnection = plug.node().plugInputChangedSignal().connect( Gaffer.WeakMethod( self.__plugInputChanged ) )
			self.__plugFlagsChangedConnection = plug.node().plugFlagsChangedSignal().connect( Gaffer.WeakMethod( self.__plugFlagsChanged ) )
			scriptNode = self.__plug.ancestor( Gaffer.ScriptNode.staticTypeId() )
			if scriptNode is not None :
				context = scriptNode.context()
		else :
			self.__plugDirtiedConnection = None
			self.__plugInputChangedConnection = None
			self.__plugFlagsChangedConnection = None
			
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
		if plug is None or plug.getInput() is None :
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
		self.__popupMenu.popup()
		
		return True

	def __setValue( self, value ) :
			
		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
			self.getPlug().setValue( value )
	
	def __editInput( self ) :
	
		GafferUI.NodeEditor.acquire( self.getPlug().getInput().node() )

	def __removeInput( self ) :
	
		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
			self.getPlug().setInput( None )
	
	# drag and drop stuff
	
	def __dragEnter( self, widget, event ) :

		if self.getReadOnly() :
			return False

		if isinstance( event.sourceWidget, GafferUI.PlugValueWidget ) :
			sourcePlugValueWidget = event.sourceWidget
		else :
			sourcePlugValueWidget = event.sourceWidget.ancestor( GafferUI.PlugValueWidget )

		if sourcePlugValueWidget is not None and sourcePlugValueWidget.getPlug().isSame( self.getPlug() ) :
			return False
		
		if isinstance( event.data, Gaffer.Plug ) :
			if self.getPlug().acceptsInput( event.data ) :
				self.setHighlighted( True )
				return True
		elif hasattr( self.getPlug(), "setValue" ) and self._dropValue( event ) is not None :
			if self.getPlug().settable() :
				self.setHighlighted( True )
				return True		
			
		return False

	def __dragLeave( self, widget, event ) :

		self.setHighlighted( False )

	def __drop( self, widget, event ) :

		self.setHighlighted( False )

		with Gaffer.UndoContext( self.getPlug().node().scriptNode() ) :
			if isinstance( event.data, Gaffer.Plug ) :
				self.getPlug().setInput( event.data )
			else :
				self.getPlug().setValue( self._dropValue( event ) )
			
		return True
			
	## Called from a dragEnter slot to see if the drag data can
	# be converted to a value suitable for a plug.setValue() call.
	# If this returns a non-None value then the drag will be accepted
	# and plug.setValue() will be called in the drop event. May be
	# reimplemented by derived classes to provide conversions of the
	# drag data to the type needed for setValue().
	def _dropValue( self, dragDropEvent ) :
	
		if not hasattr( self.getPlug(), "defaultValue" ) :
			return None
			
		plugValueType = type( self.getPlug().defaultValue() )
		if isinstance( dragDropEvent.data, plugValueType ) :
			return dragDropEvent.data
		elif isinstance( dragDropEvent.data, IECore.Data ) :
		
			dataValue = None
			if hasattr( dragDropEvent.data, "value" ) :
				dataValue = dragDropEvent.data.value
			else :
				with IECore.IgnoredExceptions( Exception ) :
					if len( dragDropEvent.data ) == 1 :
						dataValue = dragDropEvent.data[0]
			
			if dataValue is None :
				return None
			elif isinstance( dataValue, plugValueType ) :
				return dataValue
			else :
				with IECore.IgnoredExceptions( Exception ) :
					return plugValueType( dataValue )
		
		return None
