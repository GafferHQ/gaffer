##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import re
import fnmatch

import IECore

import Gaffer
import GafferUI

class PlugValueWidget( GafferUI.Widget ) :

	def __init__( self, topLevelWidget, plug, **kw ) :
	
		GafferUI.Widget.__init__( self, topLevelWidget, **kw )
	
		# we don't want to call _updateFromPlug yet because the derived
		# classes haven't constructed yet. they can call it themselves
		# upon completing construction.
		self.__setPlugInternal( plug, callUpdateFromPlug=False )

		self.__popupMenuConnections = []
		
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
	
	## Should be reimplemented to return True if this widget includes
	# some sort of labelling for the plug. This is used to prevent
	# extra labels being created in the NodeUI when they're not necessary.
	def hasLabel( self ) :
	
		return False
			
	## Must be implemented by subclasses so that the widget reflects the current
	# status of the plug.	
	def _updateFromPlug( self ) :
	
		raise NotImplementedError
	
	## Returns True if the plug value is editable - that is the plug
	# is an input plug and it has no incoming connection.
	def _editable( self ) :
	
		plug = self.getPlug()
		
		if plug is None :
			return False
		
		if plug.direction()==Gaffer.Plug.Direction.Out :
			return False
		if plug.getInput() :
			return False
		
		return True
	
	## Adds a useful popup menu to the specified widget, providing useful functions that
	# operate on the plug. The menu is populated with the result of _popupMenuDefinition(),
	# and may also be customised by external code using the popupMenuSignal().
	def _addPopupMenu( self, widget = None, buttons = GafferUI.ButtonEvent.Buttons.Right ) :
	
		if widget is None :
			widget = self
			
		self.__popupMenuConnections.append(
			widget.buttonPressSignal().connect( IECore.curry( Gaffer.WeakMethod( self.__buttonPress ), buttonMask = buttons & ~GafferUI.ButtonEvent.Buttons.Right ) )
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
		
		if hasattr( self.getPlug(), "defaultValue" ) :
			menuDefinition.append( "/Default", { "command" : IECore.curry( Gaffer.WeakMethod( self.__setValue ), self.getPlug().defaultValue() ) } )
		
		self.popupMenuSignal()( menuDefinition, self.getPlug() )
		
		return menuDefinition
	
	__popupMenuSignal = Gaffer.Signal2()
	## This signal is emitted whenever a popup menu for a plug is about
	# to be shown. This provides an opportunity to customise the menu from
	# external code. The signature for slots is ( menuDefinition, plug ),
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
			creator = cls.__plugTypesToCreators.get( plugTypeId )
			if creator is not None :
				return creator( plug )
		
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
		
	def __plugSet( self, plug ) :
	
		if plug.isSame( self.__plug ) :
		
			self._updateFromPlug()	

	def __plugDirtied( self, plug ) :
	
		if plug.isSame( self.__plug ) :
		
			self._updateFromPlug()	

	def __plugInputChanged( self, plug ) :
	
		if plug.isSame( self.__plug ) :
			self.__updateContextConnection()
			self._updateFromPlug()
			
	def __contextChanged( self, context, key ) :
	
		self._updateFromPlug()

	def __setPlugInternal( self, plug, callUpdateFromPlug ) :
	
		self.__plug = plug
		
		context = self.__fallbackContext
		
		if self.__plug is not None :
			self.__plugSetConnection = plug.node().plugSetSignal().connect( Gaffer.WeakMethod( self.__plugSet ) )
			self.__plugDirtiedConnection = plug.node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ) )
			self.__plugInputChangedConnection = plug.node().plugInputChangedSignal().connect( Gaffer.WeakMethod( self.__plugInputChanged ) )
			scriptNode = self.__plug.ancestor( Gaffer.ScriptNode.staticTypeId() )
			if scriptNode is not None :
				context = scriptNode.context()
		else :
			self.__plugSetConnection = None
			self.__plugDirtiedConnection = None
			self.__plugInputChangedConnection = None

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
			
		menuDefinition = self._popupMenuDefinition()
		if not len( menuDefinition.items() ) :
			return False
		
		self.__popupMenu = GafferUI.Menu( menuDefinition )
		self.__popupMenu.popup()
		
		return True

	def __setValue( self, value ) :
			
		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
			self.getPlug().setValue( value )
	