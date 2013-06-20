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
		self._updateFromSet()
				
	def __repr__( self ) :

		return "GafferSceneUI.SceneHierarchy( scriptNode )"

	def _updateFromSet( self ) :

		# first of all decide what plug we're viewing.
		self.__plug = None
		node = self._lastAddedNode()
		if node and "out" in node and isinstance( node["out"], GafferScene.ScenePlug ) :
			self.__plug = node["out"]
		
		# call base class update - this will trigger a call to _titleFormat(),
		# hence the need for already figuring out the plug.
		GafferUI.NodeSetEditor._updateFromSet( self )
		
		# finish our update
		if self.__plug is not None :		
			self.__pathListing.setPath( GafferScene.ScenePath( self.__plug, self.getContext(), "/" ) )
			self.__transferExpansionFromContext()
			self.__transferSelectionFromContext()
		else :
			self.__pathListing.setPath( Gaffer.DictPath( {}, "/" ) )
		
	def _updateFromContext( self, modifiedItems ) :
	
		if "ui:scene:selectedPaths" in modifiedItems :
			self.__transferSelectionFromContext()
		elif "ui:scene:expandedPaths" in modifiedItems :
			self.__transferExpansionFromContext()
			
	def _titleFormat( self ) :
	
		return GafferUI.NodeSetEditor._titleFormat(
			self,
			_maxNodes = 1 if self.__plug is not None else 0,
			_reverseNodes = True,
			_ellipsis = False
		)
		
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
		
GafferUI.EditorWidget.registerType( "SceneHierarchy", SceneHierarchy )
