##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
import GafferUI
import GafferScene

class ScenePathPlugValueWidget( GafferUI.PathPlugValueWidget ) :

	def __init__( self, plug, path = None, **kw ) :

		if path is None :

			filter = None
			sets = Gaffer.Metadata.value( plug, "scenePathPlugValueWidget:setNames" )
			if sets :
				filter = GafferScene.ScenePath.createStandardFilter(
					list( sets ),
					Gaffer.Metadata.value( plug, "scenePathPlugValueWidget:setsLabel" )
				)

			path = GafferScene.ScenePath(
				self.__scenePlug( plug ),
				plug.node().scriptNode().context(),
				"/",
				filter = filter
			)

		GafferUI.PathPlugValueWidget.__init__( self, plug, path, **kw )

		plug.ancestor( Gaffer.ScriptNode ).focusChangedSignal().connect( Gaffer.WeakMethod( self.__focusChanged ), scoped = False )

	def _pathChooserDialogue( self ) :

		dialogue = GafferUI.PathPlugValueWidget._pathChooserDialogue( self )

		# Unsorted tree view with only a name column - like the HierarchyView.
		dialogue.pathChooserWidget().pathListingWidget().setDisplayMode( GafferUI.PathListingWidget.DisplayMode.Tree )
		dialogue.pathChooserWidget().pathListingWidget().setColumns( ( GafferUI.PathListingWidget.defaultNameColumn, ) )
		dialogue.pathChooserWidget().pathListingWidget().setSortable( False )

		# View relative to the root, rather than the current location.
		## \todo The save/restore of pathNames is to work around the PathChooserWidget
		# truncating the path when the root directory changes. I don't think that
		# behaviour makes sense in tree view mode, so we should probably fix it there.
		dirPath = dialogue.pathChooserWidget().directoryPathWidget().getPath()
		if len( dirPath ) :
			path = dialogue.pathChooserWidget().pathWidget().getPath()
			pathNames = path[:]
			del dirPath[:]
			path[:] = pathNames

		return dialogue

	def __scenePlug( self, plug ) :

		# Search for a suitable ScenePlug input on the same node as this plug,
		# or on the node of another plug being driven by this plug.

		def predicate( plug ) :

			scenePlugName = Gaffer.Metadata.value( plug, "scenePathPlugValueWidget:scene" ) or "in"
			scenePlug = plug.node().descendant( scenePlugName )
			if scenePlug and isinstance( scenePlug, GafferScene.ScenePlug ) :
				return scenePlug

		scenePlug = Gaffer.PlugAlgo.findDestination( plug, predicate )
		if scenePlug is not None :
			return scenePlug

		# The above doesn't work well for ShaderNodes, since they don't have
		# ScenePlug inputs. We _could_ traverse outputs from the shader looking
		# for a ShaderAssignment node to get a ScenePlug from. But this wouldn't
		# be useful if the scene hierarchy was manipulated downstream of the
		# ShaderAssignment as shaders need the final paths as seen by the
		# renderer. So instead use the focus node, as it is more likely to
		# be pointed at the final render node.

		focusNode = plug.ancestor( Gaffer.ScriptNode ).getFocus()
		if focusNode is not None :
			return next( GafferScene.ScenePlug.RecursiveOutputRange( focusNode ), None )

	def __focusChanged( self, scriptNode, node ) :

		scenePlug = self.__scenePlug( self.getPlug() )
		if scenePlug is not None :
			self.path().setScene( scenePlug )
