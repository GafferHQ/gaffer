##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import Gaffer
import GafferScene
import GafferUI

class SceneEditor( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode=None, **kw ) :
	
		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		
		GafferUI.NodeSetEditor.__init__( self, column, scriptNode, **kw )
		
		with column :
		
			self.__pathListing = GafferUI.PathListingWidget(
				Gaffer.DictPath( {}, "/" ), # temp till we make a ScenePath
				columns = [ GafferUI.PathListingWidget.defaultNameColumn ],
				allowMultipleSelection = True,
				displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
			)
		
		self.__plug = None		
		self._updateFromSet()
				
	def __repr__( self ) :

		return "GafferSceneUI.SceneEditor()"

	def _updateFromSet( self ) :
		
		if not hasattr( self, "_SceneEditor__plug" ) :
			# we're being called during construction
			return
			
		self.__plug = None
		node = self._lastAddedNode()
		if not node or not isinstance( node, GafferScene.SceneNode ) :
			self.__plugDirtiedConnection = None
		else :			
			self.__plug = node["out"]
			self.__plugDirtiedConnection = node.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ) )
			
		self.__update()
	
	def _updateFromContext( self ) :
	
		self.__update()
	
	def __update( self ) :
		
		if self.__plug is not None :
			self.__pathListing.setPath( GafferScene.ScenePath( self.__plug, "/" ) )
		else :
			self.__pathListing.setPath( Gaffer.DictPath( {}, "/" ) )
	
	def __plugDirtied( self, plug ) :
	
		if plug.isSame( self.__plug ) :
			self.__update()
	
GafferUI.EditorWidget.registerType( "SceneEditor", SceneEditor )
