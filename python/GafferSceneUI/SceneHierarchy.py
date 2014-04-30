##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import GafferScene
import GafferUI

class SceneHierarchy( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode, **kw ) :
	
		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 8 )
		
		GafferUI.NodeSetEditor.__init__( self, column, scriptNode, **kw )
		
		with column :
		
			self.__pathListing = GafferUI.PathListingWidget(
				Gaffer.DictPath( {}, "/" ), # temp till we make a ScenePath
				columns = [ GafferUI.PathListingWidget.defaultNameColumn ],
				allowMultipleSelection = True,
				displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
			)
			self.__pathListing.setDragPointer( "objects.png" )
			
			self.__selectionChangedConnection = self.__pathListing.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__selectionChanged ) )
			self.__expansionChangedConnection = self.__pathListing.expansionChangedSignal().connect( Gaffer.WeakMethod( self.__expansionChanged ) )
		
		self.__plug = None
		self.__playback = None
		self._updateFromSet()
				
	def __repr__( self ) :

		return "GafferSceneUI.SceneHierarchy( scriptNode )"

	def _updateFromSet( self ) :

		# first of all decide what plug we're viewing.
		self.__plug = None
		self.__plugParentChangedConnection = None
		node = self._lastAddedNode()
		if node is not None :
			outputScenePlugs = [ p for p in node.children( GafferScene.ScenePlug.staticTypeId() ) if p.direction() == Gaffer.Plug.Direction.Out ]
			if len( outputScenePlugs ) :
				self.__plug = outputScenePlugs[0]
				self.__plugParentChangedConnection = self.__plug.parentChangedSignal().connect( Gaffer.WeakMethod( self.__plugParentChanged ) )
		
		# call base class update - this will trigger a call to _titleFormat(),
		# hence the need for already figuring out the plug.
		GafferUI.NodeSetEditor._updateFromSet( self )
		
		# update our view of the hierarchy
		self.__setPathListingPath()
				
	def _updateFromContext( self, modifiedItems ) :
		
		if self.__playback is None or not self.__playback.context().isSame( self.getContext() ) :
			self.__playback = GafferUI.Playback.acquire( self.getContext() )
			self.__playbackStateChangedConnection = self.__playback.stateChangedSignal().connect( Gaffer.WeakMethod( self.__playbackStateChanged ) )
	
		if "ui:scene:selectedPaths" in modifiedItems :
			self.__transferSelectionFromContext()
		elif "ui:scene:expandedPaths" in modifiedItems :
			self.__transferExpansionFromContext()
			
		if self.__playback.getState() == GafferUI.Playback.State.Stopped :
			# When the context has changed, the hierarchy of the scene may
			# have too so we should update our PathListingWidget. One of the
			# most common causes of Context changes is animation playback though,
			# and in this scenario our update would greatly slow down playback,
			# and be exceedingly unlikely to display anything of interest. For
			# this reason, we don't update during playback. We can also avoid
			# updating if the only entries which have changed are "ui:" prefixed
			# as those shouldn't affect the result.
			for item in modifiedItems :
				if not item.startswith( "ui:" ) :
					self.__setPathListingPath()
					break
			
	def _titleFormat( self ) :
	
		return GafferUI.NodeSetEditor._titleFormat(
			self,
			_maxNodes = 1 if self.__plug is not None else 0,
			_reverseNodes = True,
			_ellipsis = False
		)
	
	def __plugParentChanged( self, plug, oldParent ) :
	
		# the plug we were viewing has been deleted or moved - find
		# another one to view.
		self._updateFromSet()
	
	def __setPathListingPath( self ) :
	
		if self.__plug is not None :
			# Note that we take a static copy of our current context for use in the ScenePath - this prevents the
			# PathListing from updating automatically when the original context changes, and allows us to have finer
			# grained control of the update in our _updateFromContext() method.
			self.__pathListing.setPath( GafferScene.ScenePath( self.__plug, Gaffer.Context( self.getContext() ), "/" ) )
			self.__transferExpansionFromContext()
			self.__transferSelectionFromContext()
		else :
			self.__pathListing.setPath( Gaffer.DictPath( {}, "/" ) )

	def __expansionChanged( self, pathListing ) :
	
		assert( pathListing is self.__pathListing )
		
		paths = pathListing.getExpandedPaths()
		paths = IECore.StringVectorData( [ "/" ] + [ str( path ) for path in paths ] )
		pathMatcherData = GafferScene.PathMatcherData()
		pathMatcherData.value.init( paths )
		with Gaffer.BlockedConnection( self._contextChangedConnection() ) :
			self.getContext().set( "ui:scene:expandedPaths", pathMatcherData )
	
	def __selectionChanged( self, pathListing ) :
	
		assert( pathListing is self.__pathListing )

		paths = pathListing.getSelectedPaths()
		paths = IECore.StringVectorData( [ str( path ) for path in paths ] )
		with Gaffer.BlockedConnection( self._contextChangedConnection() ) :
			self.getContext().set( "ui:scene:selectedPaths", paths )
	
	def __transferExpansionFromContext( self ) :
	
		expandedPaths = self.getContext().get( "ui:scene:expandedPaths", None )
		if expandedPaths is None :
			return
			
		p = self.__pathListing.getPath()
		expandedPaths = [ p.copy().setFromString( s ) for s in expandedPaths.value.paths() ]
		with Gaffer.BlockedConnection( self.__expansionChangedConnection ) :
			self.__pathListing.setExpandedPaths( expandedPaths )
	
	def __transferSelectionFromContext( self ) :
	
		selection = self.getContext()["ui:scene:selectedPaths"]
		with Gaffer.BlockedConnection( self.__selectionChangedConnection ) :
			## \todo Qt is dog slow with large non-contiguous selections,
			# so we're only mirroring single selections currently. Rewrite
			# PathListingWidget so it manages selection itself using a PathMatcher
			# and we can refer to the same data structure everywhere, and reenable
			# mirroring of multi-selection.
			if len( selection ) == 1 :
				p = self.__pathListing.getPath()
				selection = [ p.copy().setFromString( s ) for s in selection ]
				self.__pathListing.setSelectedPaths( selection, scrollToFirst=True, expandNonLeaf=False )
			else :
				self.__pathListing.setSelectedPaths( [] )
	
	def __playbackStateChanged( self, playback ) :
	
		assert( playback is self.__playback )
		
		if playback.getState() == playback.State.Stopped :
			# because we disable update during playback, we need to
			# perform a final update when playback stops.
			self.__setPathListingPath()
		
GafferUI.EditorWidget.registerType( "SceneHierarchy", SceneHierarchy )
