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

import IECore

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )

## The NodeSetEditor is a base class for all Editors which focus their
# editing on a subset of nodes beneath a ScriptNode. This set defaults
# to the ScriptNode.selection() but can be modified to be any Set of nodes.
class NodeSetEditor( GafferUI.EditorWidget ) :

	def __init__( self, topLevelWidget, scriptNode, **kw ) :
	
		self.__nodeSet = Gaffer.StandardSet()
		self.__nodeSetChangedSignal = GafferUI.WidgetSignal()

		GafferUI.EditorWidget.__init__( self, topLevelWidget, scriptNode, **kw )
		
		self.__titleFormat = None
		
		self.__updateScheduled = False
		# allow derived classes to call _updateFromSet() themselves after construction,
		# to avoid being called when they're only half constructed.
		self.__setNodeSetInternal( self.scriptNode().selection(), callUpdateFromSet=False )
	
	## Sets the nodes that will be displayed by this editor. As members are
	# added to and removed from the set, the UI will be updated automatically
	# to show them. If the set is not scriptNode.selection(), then an OrphanRemover
	# will be applied automatically to the set so that deleted nodes are not
	# visible in the UI.
	# \todo Although the OrphanRemover behaviour is convenient for our current use cases
	# where it prevents the callers of setNodeSet() from having to worry about nodes
	# being deleted, it might not be ideal in all cases. For instance the same set may be
	# reused across multiple NodeSetEditors and end up with multiple OrphanRemovers applied.
	# We might like to consider an API where the behaviours applied to a given object can be
	# queried, or we could make it the responsibility of the caller to apply an OrphanRemover
	# explicitly where appropriate.
	def setNodeSet( self, nodeSet ) :
	
		self.__setNodeSetInternal( nodeSet, callUpdateFromSet=True )
		
	def getNodeSet( self ) :
	
		return self.__nodeSet
	
	def nodeSetChangedSignal( self ) :
	
		return self.__nodeSetChangedSignal
	
	## Overridden to display the names of the nodes being edited.
	# Derived classes should override _titleFormat() rather than
	# reimplement this again.
	def getTitle( self ) :
		
		t = GafferUI.EditorWidget.getTitle( self )
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
			if isinstance( t, basestring ) :
				result += t
			else :
				result += t.getName()
				
		return result
		
	## Ensures that the specified node has a visible editor of this class type editing
	# it, creating one if necessary.
	## \todo User preferences for whether these are made floating, embedded, whether
	# they are reused etc. This class should provide the behaviour, but the code for
	# linking it to preferences should be in a startup file.
	## \todo Consider how this relates to draggable editor tabs and editor floating
	# once we implement that in CompoundEditor - perhaps acquire will become a method
	# on CompoundEditor instead at this point.
	@classmethod
	def acquire( cls, node ) :
	
		if isinstance( node, Gaffer.ScriptNode ) :
			script = node
		else :
			script = node.scriptNode()
		
		scriptWindow = GafferUI.ScriptWindow.acquire( script )
		
		for editor in scriptWindow.getLayout().editors( type = cls ) :
			if node.isSame( editor._lastAddedNode() ) :
				editor.reveal()
				return editor
		
		childWindows = scriptWindow.childWindows()
		for window in childWindows :
			if isinstance( window, _EditorWindow ) :
				if isinstance( window.getChild(), cls ) and node in window.getChild().getNodeSet() :
					window.setVisible( True )
					return window.getChild()
		
		editor = cls( script )
		editor.setNodeSet( Gaffer.StandardSet( [ node ] ) )						
		
		window = _EditorWindow( scriptWindow, editor )
		window.setVisible( True )

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
	
		# flush information needed for making the title -
		# we'll update it lazily in getTitle().
		self.__nameChangedConnections = []
		self.__titleFormat = None
	
		self.titleChangedSignal()( self )
	
	# May be called to ensure that _updateFromSet() is called
	# immediately if a lazy update has been scheduled but not
	# yet performed.
	def _doPendingUpdate( self ) :
	
		self.__updateTimeout()
		
	## May be reimplemented by derived classes to specify a combination of
	# strings and node names to use in building the title. The NodeSetEditor
	# will take care of updating the title appropriately as the nodes are renamed.
	def _titleFormat( self, _prefix = None, _maxNodes = 2, _reverseNodes = False, _ellipsis = True ) :
	
		if _prefix is None :
			result = [ IECore.CamelCase.toSpaced( self.__class__.__name__ ) ]
		else :
			result = [ _prefix ]
			
		numNames = min( _maxNodes, len( self.__nodeSet ) )
		if numNames :
			
			result.append( " : " )
			
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
				
		return result
		
	def __setNodeSetInternal( self, nodeSet, callUpdateFromSet ) :
	
		if self.__nodeSet.isSame( nodeSet ) :
			return
	
		prevSet = self.__nodeSet
		self.__nodeSet = nodeSet
		self.__memberAddedConnection = self.__nodeSet.memberAddedSignal().connect( Gaffer.WeakMethod( self.__membersChanged ) )
		self.__memberRemovedConnection = self.__nodeSet.memberRemovedSignal().connect( Gaffer.WeakMethod( self.__membersChanged ) )
		
		if not self.__nodeSet.isSame( self.scriptNode().selection() ) :
			self.__orphanRemover = Gaffer.Behaviours.OrphanRemover( self.__nodeSet )
		else :
			self.__orphanRemover = None
		
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
		
		if self.__updateScheduled :
			return
		
		QtCore.QTimer.singleShot( 0, self.__updateTimeout )
		self.__updateScheduled = True
	
	def __updateTimeout( self ) :
		
		if self.__updateScheduled :
			self.__updateScheduled = False
			self._updateFromSet()

class _EditorWindow( GafferUI.Window ) :

	def __init__( self, parentWindow, editor, **kw ) :
	
		GafferUI.Window.__init__( self, borderWidth = 8, **kw )
		
		self.setChild( editor )

		self.__titleChangedConnection = editor.titleChangedSignal().connect( Gaffer.WeakMethod( self.__updateTitle ) )
		self.__nodeSetMemberRemovedConnection = editor.getNodeSet().memberRemovedSignal().connect( Gaffer.WeakMethod( self.__nodeSetMemberRemoved ) )
		self.__closedConnection = self.closedSignal().connect( Gaffer.WeakMethod( self.__closed ) )

		parentWindow.addChildWindow( self )

		self.__updateTitle()

	def __updateTitle( self, *unused ) :
	
		self.setTitle( self.getChild().getTitle() )

	def __nodeSetMemberRemoved( self, set, node ) :
	
		if not len( set ) :
			self.parent().removeChild( self )

	def __closed( self, window ) :
	
		assert( window is self )
		
		self.parent().removeChild( self )
