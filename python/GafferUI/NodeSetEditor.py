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

import six

import IECore

import Gaffer
import GafferUI

from Qt import QtCore

import weakref

## The NodeSetEditor is a base class for all Editors which focus their
# editing on a subset of nodes beneath a ScriptNode. This set defaults
# to the ScriptNode.selection() but can be modified to be any Set of nodes.
#
# The node set for any given editor can be optionally driven by that of some
# other editor, such that they don't need to be independently maintained. The
# default mode simply ensures they have the same node set. Custom modes can be
# registered for extended functionality.
class NodeSetEditor( GafferUI.Editor ) :

	DriverModeNodeSet = "NodeSet"

	__nodeSetDriverModes = {}

	def __init__( self, topLevelWidget, scriptNode, **kw ) :

		self.__nodeSet = Gaffer.StandardSet()
		self.__nodeSetChangedSignal = GafferUI.WidgetSignal()

		self.__nodeSetDriver = {}
		self.__nodeSetDriverChangedSignal = GafferUI.WidgetSignal()
		self.__drivenNodeSets = {}
		self.__drivenNodeSetsChangedSignal = GafferUI.WidgetSignal()

		GafferUI.Editor.__init__( self, topLevelWidget, scriptNode, **kw )

		self.__titleFormat = None

		# Allow derived classes to call `_updateFromSet()`` themselves after construction,
		# to avoid being called when they're only half constructed.
		## \todo Should we call `__lazyUpdate()` instead, so `_updateFromSet()` is called
		# when the editor becomes visible? Then derived classes shouldn't need to call
		# `updateFromSet()` in their constructors at all.
		self.__setNodeSetInternal( self.scriptNode().selection(), callUpdateFromSet=False )

	## Sets the nodes that will be displayed by this editor. As members are
	# added to and removed from the set, the UI will be updated automatically
	# to show them. This also calls `nodeSet.setRemoveOrphans( True )` so that
	# deleted nodes are not visible in the UI.
	#
	# This will break any editor links, if set.
	#
	# The driver will be updated *after* the node set, such that calling
	# `getNodeSetDriver` in the nodeSetChangedSignal will return the departing
	# driver. TODO: We need to work out a sensible way to signal once state has
	# stabilised
	def setNodeSet( self, nodeSet ) :

		self.__setNodeSetInternal( nodeSet, callUpdateFromSet=True )
		# We do this after setting the node set, so that when the driver changed
		# signal is emitted, we will have the new node set. Otherwise the editor
		# looks like it has the old drivers node set still despite not having a
		# driver...
		self.setNodeSetDriver( None )

	def getNodeSet( self ) :

		return self.__nodeSet

	## Called before nodeSetDriverChangedSignal in the event that setNodeSet breaks a driver link.
	def nodeSetChangedSignal( self ) :

		return self.__nodeSetChangedSignal

	## Links the nodeSet for this editor to that of the supplied drivingEditor.
	# The default mode results in a simple mirroring of the driver's node set
	# to this editor. Other modes may be registered by other Gaffer modules.
	# If drivingEditor is None, any existing links will be broken.
	def setNodeSetDriver( self, drivingEditor, mode = DriverModeNodeSet ) :

		if drivingEditor is not None :
			assert( isinstance( drivingEditor, GafferUI.NodeSetEditor ) )
			# We also need to stop people creating infinite loops
			if self.drivesNodeSet( drivingEditor ) :
				raise ValueError( "The supplied driver is already driven by this editor" )

		if self.__nodeSetDriver :
			previousDriver = self.__nodeSetDriver["weakDriver"]()
			# It may have been deleted, we'll still have link data but the ref will be dead
			if previousDriver is not None :
				if drivingEditor is previousDriver and mode == self.__nodeSetDriver["mode"] :
					return
				else :
					previousDriver.__unregisterDrivenEditor( self )

		self.__nodeSetDriver = {}

		if drivingEditor :

			drivingEditor.__registerDrivenEditor( self, mode )

			weakSelf = weakref.ref( self )

			# We need to unlink ourselves if the driver goes away
			def disconnect( _ ) :
				if weakSelf() is not None:
					weakSelf().setNodeSetDriver( None )

			weakDriver = weakref.ref( drivingEditor, disconnect )

			changeCallback = self.__nodeSetDriverModes[ mode ]

			def updateFromDriver( _ ) :
				if weakDriver() is not None and weakSelf() is not None :
					nodeSet = weakDriver().getNodeSet()
					if changeCallback :
						nodeSet = changeCallback( weakSelf(), weakDriver() )
					weakSelf().__setNodeSetInternal( nodeSet, callUpdateFromSet=True )

			self.__nodeSetDriver = {
				"mode" : mode,
				"weakDriver" : weakDriver,
				"driverNodeSetChangedConnection" : drivingEditor.nodeSetChangedSignal().connect( updateFromDriver ),
			}
			updateFromDriver( drivingEditor )

		self.__nodeSetDriverChangedSignal( self )
		self.__dirtyTitle()

	## Returns a tuple of the drivingEditor and the drive mode.
	# When there is no driver ( None, "" ) will be returned.
	def getNodeSetDriver( self ) :

		if self.__nodeSetDriver :
			return ( self.__nodeSetDriver["weakDriver"](), self.__nodeSetDriver["mode"] )

		return ( None, "" )

	## Called whenever the editor's driving node set changes.
	# Note: This is called after nodeSetChangedSignal in the event that
	# the setNodeSet call breaks an existing driver link.
	def nodeSetDriverChangedSignal( self ) :

		return self.__nodeSetDriverChangedSignal

	## Returns a dict of { editor : mode } that are driven by this editor.
	# If recurse is true, the link chain will be followed recursively to
	# also include editors that indirectly driven by this one.
	def drivenNodeSets( self, recurse = False ) :

		# Unwrap the weak refs
		driven = { w(): m for w,m in self.__drivenNodeSets.items() if w() is not None }

		if recurse :
			for editor in list( driven.keys() ) :
				driven.update( editor.drivenNodeSets( recurse = True ) )

		return driven

	def drivenNodeSetsChangedSignal( self ) :

		return self.__drivenNodeSetsChangedSignal

	## Does this editor ultimately drive otherEditor
	def drivesNodeSet( self, otherEditor ) :

		assert( isinstance( otherEditor, GafferUI.NodeSetEditor ) )

		driver = otherEditor
		while True :
			if driver is None :
				break
			if driver is self :
				return True
			driver, _ = driver.getNodeSetDriver()

		return False

	## Returns the editor that ultimately drives this editor. If this editor
	# is not driven, None is returned.
	def drivingEditor( self ) :

		driver = None

		upstreamEditor = self
		while True :
			upstreamEditor, _ = upstreamEditor.getNodeSetDriver()
			if upstreamEditor :
				driver = upstreamEditor
			else :
				break

		return driver

	def __registerDrivenEditor( self, drivenEditor, mode ) :

		if drivenEditor in self.drivenNodeSets() :
			return

		self.__drivenNodeSets[ weakref.ref( drivenEditor ) ] = mode
		self.__drivenNodeSetsChangedSignal( self )

	def __unregisterDrivenEditor( self, drivenEditor ) :

		for weakEditor in self.__drivenNodeSets :
			if weakEditor() is drivenEditor :
				del self.__drivenNodeSets[ weakEditor ]
				self.__drivenNodeSetsChangedSignal( self )
				break

	## Call to register a new DriverMode that can be used with setNodeSetDriver.
	# The supplied callback will be called with ( thisEditor, drivingEditor ) and
	# must return a derivative of Gaffer.Set that represents the nodesSet to be
	# set in the driven editor.
	# If provided, 'description' should be a sensible message to describe the
	# nature of the user-observed behaviour, '{editor}' will be replaced with
	# the name of the driving editor. eg:
	#   "Following the source node for the scene selection of {editor}"
	@classmethod
	def registerNodeSetDriverMode( cls, mode, changeCallback, description = "Following {editor}." ) :

		cls.__nodeSetDriverModes[ mode ] = changeCallback
		# TODO: Move to the NodeSetEditor class once they are GraphComponents
		Gaffer.Metadata.registerValue( "NodeSetEditor", "nodeSetDriverMode:%s:description" % mode, description )

	@staticmethod
	def nodeSetDriverModeDescription( mode ) :

		return Gaffer.Metadata.value( "NodeSetEditor", "nodeSetDriverMode:%s:description" % mode )

	## Overridden to display the names of the nodes being edited.
	# Derived classes should override _titleFormat() rather than
	# reimplement this again.
	def getTitle( self ) :

		t = GafferUI.Editor.getTitle( self )
		if t :
			return t

		if self.__titleFormat is None :
			self.__titleFormat = self._titleFormat()
			self.__nameChangedConnections = []
			for n in self.__titleFormat :
				if isinstance( n, Gaffer.GraphComponent ) :
					self.__nameChangedConnections.append( n.nameChangedSignal().connect( Gaffer.WeakMethod( self.__nameChanged ) ) )

		result = ""
		for t in self.__titleFormat :
			if isinstance( t, six.string_types ) :
				result += t
			else :
				result += t.getName()

		return result

	## Ensures that the specified node has a visible editor of this class type editing
	# it, creating one if necessary. The `floating` argument may be passed a value of
	# `True` or `False`, to force the acquisition of a panel that is either floating or
	# docked respectively.
	## \todo Consider how this relates to draggable editor tabs and editor floating
	# once we implement that in CompoundEditor - perhaps acquire will become a method
	# on CompoundEditor instead at this point.
	@classmethod
	def acquire( cls, node, floating = None ) :

		if isinstance( node, Gaffer.ScriptNode ) :
			script = node
		else :
			script = node.scriptNode()

		scriptWindow = GafferUI.ScriptWindow.acquire( script )

		if floating in ( None, False ) :
			for editor in scriptWindow.getLayout().editors( type = cls ) :
				if node.isSame( editor._lastAddedNode() ) :
					editor.reveal()
					return editor

		if floating in ( None, True ) :
			childWindows = scriptWindow.childWindows()
			for window in childWindows :
				if isinstance( window, _EditorWindow ) :
					if isinstance( window.getChild(), cls ) and node in window.getChild().getNodeSet() :
						window.setVisible( True )
						return window.getChild()

		editor = cls( script )
		editor.setNodeSet( Gaffer.StandardSet( [ node ] ) )

		if floating is False :
			scriptWindow.getLayout().addEditor( editor )
		else :
			window = _EditorWindow( scriptWindow, editor )
			# Ensure keyboard shortcuts are relayed to the main menu bar
			scriptWindow.menuBar().addShortcutTarget( window )
			window.setVisible( True )

			if isinstance( editor, GafferUI.NodeEditor ) :
				# The window will have opened at the perfect size for the
				# contained widgets. But some NodeEditors have expanding
				# sections and buttons to add new widgets, and for that
				# reason, a minimum height of 400px has been deemed more
				# suitable.
				size = window._qtWidget().size()
				if size.height() < 400 :
					size.setHeight( 400 )
					window._qtWidget().resize( size )

		return editor

	def _lastAddedNode( self ) :

		if len( self.__nodeSet ) :
			return self.__nodeSet[-1]

		return None

	## Called when the contents of getNodeSet() have changed and need to be
	# reflected in the UI - so must be implemented by derived classes to update
	# their UI appropriately. Updates are performed lazily to avoid unecessary
	# work, but any pending updates can be performed immediately by calling
	# _doPendingUpdate().
	#
	# All implementations must first call the base class implementation.
	def _updateFromSet( self ) :

		self.__dirtyTitle()

	# May be called to ensure that _updateFromSet() is called
	# immediately if a lazy update has been scheduled but not
	# yet performed.
	def _doPendingUpdate( self ) :

		self.__lazyUpdate.flush( self )

	## May be reimplemented by derived classes to specify a combination of
	# strings and node names to use in building the title. The NodeSetEditor
	# will take care of updating the title appropriately as the nodes are renamed.
	def _titleFormat( self, _prefix = None, _maxNodes = 2, _reverseNodes = False, _ellipsis = True ) :

		if _prefix is None :
			result = [ IECore.CamelCase.toSpaced( self.__class__.__name__ ) ]
		else :
			result = [ _prefix ]

		# Only add node names if we're pinned in some way shape or form
		if not self.__nodeSetIsScriptSelection() :

			result.append( " [" )

			numNames = min( _maxNodes, len( self.__nodeSet ) )
			if numNames :

				if _reverseNodes :
					nodes = self.__nodeSet[len(self.__nodeSet)-numNames:]
					nodes.reverse()
				else :
					nodes = self.__nodeSet[:numNames]

				for i, node in enumerate( nodes ) :
					result.append( node )
					if i < numNames - 1 :
						result.append( ", " )

				if _ellipsis and len( self.__nodeSet ) > _maxNodes :
					result.append( "..." )

			result.append( "]" )

		return result

	def __dirtyTitle( self ) :

		# flush information needed for making the title -
		# we'll update it lazily in getTitle().
		self.__nameChangedConnections = []
		self.__titleFormat = None

		self.titleChangedSignal()( self )

	def __nodeSetIsScriptSelection( self ) :

		driver = self.drivingEditor() or self
		return driver.getNodeSet() == self.scriptNode().selection()

	def __setNodeSetInternal( self, nodeSet, callUpdateFromSet ) :

		if self.__nodeSet.isSame( nodeSet ) :
			return

		prevSet = self.__nodeSet
		self.__nodeSet = nodeSet
		self.__memberAddedConnection = self.__nodeSet.memberAddedSignal().connect( Gaffer.WeakMethod( self.__membersChanged ) )
		self.__memberRemovedConnection = self.__nodeSet.memberRemovedSignal().connect( Gaffer.WeakMethod( self.__membersChanged ) )
		self.__dirtyTitle()

		if isinstance( nodeSet, Gaffer.StandardSet ) :
			nodeSet.setRemoveOrphans( True )

		if callUpdateFromSet :
			# only update if the nodes being held have actually changed,
			# so we don't get unnecessary flicker in any of the uis.
			needsUpdate = len( prevSet ) != len( self.__nodeSet )
			if not needsUpdate :
				for i in range( 0, len( prevSet ) ) :
					if not prevSet[i].isSame( self.__nodeSet[i] ) :
						needsUpdate = True
						break
			if needsUpdate :
				self._updateFromSet()

		self.__nodeSetChangedSignal( self )

	def __nameChanged( self, node ) :

		self.titleChangedSignal()( self )

	def __membersChanged( self, set, member ) :

		self.__lazyUpdate()

	@GafferUI.LazyMethod()
	def __lazyUpdate( self ) :

		self._updateFromSet()

class _EditorWindow( GafferUI.Window ) :

	def __init__( self, parentWindow, editor, **kw ) :

		GafferUI.Window.__init__( self, borderWidth = 8, **kw )

		self.setChild( editor )

		editor.titleChangedSignal().connect( Gaffer.WeakMethod( self.__updateTitle ), scoped = False )
		editor.getNodeSet().memberRemovedSignal().connect( Gaffer.WeakMethod( self.__nodeSetMemberRemoved ), scoped = False )

		parentWindow.addChildWindow( self, removeOnClose=True )

		self.__updateTitle()

	def __updateTitle( self, *unused ) :

		self.setTitle( self.getChild().getTitle() )

	def __nodeSetMemberRemoved( self, set, node ) :

		if not len( set ) :
			self.parent().removeChild( self )


NodeSetEditor.registerNodeSetDriverMode(
	NodeSetEditor.DriverModeNodeSet, None,
	"Following {editor}."
)
